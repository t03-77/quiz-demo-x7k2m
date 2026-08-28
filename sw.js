/* オフラインで問題演習を続けられるようにするService Worker。
   アプリ本体と問題データを最初の訪問でキャッシュし、以後はネットワークが無くても起動する。
   音声(audio/)は容量が大きいので自動キャッシュしない — 再生した分だけブラウザが保持する。 */

const VERSION = 'v3';   // 上げると古いキャッシュを破棄する。index.html を直したら必ず上げること
const CACHE = `certquiz-${VERSION}`;

// 起動に必要な最小構成。data/audio_tracks.js は無い環境もあるため別扱いにする
const CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon.svg',
  './data/exams.js',
  './data/glossary.js',
  './data/orig.js',
];
const OPTIONAL = ['./data/demo_audio.js', './data/audio_tracks.js'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(CORE);
    // 存在しないファイルで install 全体を失敗させない
    await Promise.all(OPTIONAL.map((u) => cache.add(u).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;                      // AI APIへのPOSTなどは素通し
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;       // 外部APIはキャッシュしない
  if (url.pathname.includes('/audio/')) return;          // 音声は大きいので対象外
  // デモ用キーは差し替えることがある。キャッシュを返すと古いキーのままになり、
  // 新しいパスワードで解錠できなくなる（実際にそれが起きた）
  if (url.pathname.endsWith('/data/demo_key.js')) return;

  // まずキャッシュを返して即座に起動し、裏で最新を取り込む
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, { ignoreSearch: true });
    const net = fetch(req).then((res) => {
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    }).catch(() => null);
    return hit || (await net) || new Response('オフラインのため読み込めませんでした', {
      status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' },
    });
  })());
});
