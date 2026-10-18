// 音声モード(ハンズフリー)を検証する。読み上げと音声認識は偽物に差し替え、
// 「読み上げが終わったら聞き取り → 認識結果で回答・次へ」の流れが回るかを見る。
// 実行: node tests/test_voice.js   (QUIZ_URL で開く URL を、PW_CHANNEL / PW_EXE でブラウザを変えられる)
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const errors = [];
  const ch = process.env.PW_CHANNEL ?? (process.platform === 'win32' ? 'msedge' : undefined);
  const browser = await chromium.launch(process.env.PW_EXE ? { executablePath: process.env.PW_EXE, headless: true }
    : ch ? { channel: ch, headless: true } : { headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
  page.on('pageerror', e => errors.push(e.message));
  page.on('dialog', async d => { await d.accept(); });

  // 偽の speechSynthesis / SpeechRecognition。話した内容は window.__spoken に積む。
  // 認識結果は window.__say に積んだ順に1つずつ返す(空なら無音=no-speech で終わる)
  await page.addInitScript(() => {
    window.__spoken = []; window.__say = []; window.__recStarts = 0;
    const synth = {
      speak(u) { window.__spoken.push(u.text); setTimeout(() => u.onend && u.onend(), 5); },
      cancel() {}, getVoices() { return []; }, onvoiceschanged: null,
    };
    Object.defineProperty(window, 'speechSynthesis', { value: synth, configurable: true });
    window.SpeechSynthesisUtterance = function (t) { this.text = t; };
    class FakeRec {
      start() {
        window.__recStarts++;
        setTimeout(() => {
          const t = window.__say.shift();
          if (t !== undefined) {
            const alt = [{ transcript: t }];
            this.onresult && this.onresult({ results: [alt] });
          } else {
            this.onerror && this.onerror({ error: 'no-speech' });
          }
          this.onend && this.onend();
        }, 30);
      }
      abort() {}
    }
    window.SpeechRecognition = FakeRec;
  });

  const url = process.env.QUIZ_URL ||
    'file:///' + path.resolve('C:/Users/na7sh/Works/95_work/aws/01_projects/cert_quiz_app/index.html').replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('.examcard');
  await page.locator('.examcard', { hasText: 'Generative AI Developer' }).first().click();
  await page.waitForSelector('#v-home.on');
  await page.evaluate(() => { SETTINGS.sessionLen = '5'; });

  const results = [];
  const check = (name, ok, extra = '') => { results.push(ok); console.log((ok ? 'OK  ' : 'NG  ') + name + (extra ? ' — ' + extra : '')); };
  const wait = ms => page.waitForTimeout(ms);
  const waitPhase = async (p, ms = 4000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { if (await page.evaluate(x => VOICE.phase === x, p)) return true; await wait(50); }
    return false;
  };

  await page.locator('button:has-text("音声で解く")').click();
  await page.waitForSelector('#q-card .qtext');
  check('音声バーが出る', await page.locator('#voicebar').isVisible());
  check('出題を読み上げる', await waitPhase('ask'));
  await wait(500);
  const spoken1 = await page.evaluate(() => window.__spoken.join(''));
  const q1 = await page.evaluate(() => ({ id: cur.id, type: cur.type, need: cur.n_correct || 1, letters: dispLetters(cur) }));
  check('問題文と選択肢を読む', /選択肢。エー。/.test(spoken1), spoken1.slice(0,200));
  check('選択式の問題だけが出る', q1.type === 'choice');

  // 「もう一回」で読み直す
  let n0 = await page.evaluate(() => window.__spoken.length);
  await page.evaluate(() => window.__say.push('もう一回'));
  await wait(800);
  check('「もう一回」で読み直す', await page.evaluate(n => window.__spoken.length > n, n0));

  // 正解を声で答える(複数選択なら「エーとシー」の形で)
  const LN = { A: 'エー', B: 'ビー', C: 'シー', D: 'ディー', E: 'イー', F: 'エフ' };
  const sayAns = letters => letters.map(l => LN[l]).join('と') + 'です';
  await page.evaluate(s => window.__say.push(s), sayAns(q1.letters));
  check('回答後に結果を読み上げる', await waitPhase('result'));
  const last = await page.evaluate(() => sessionLog[sessionLog.length - 1]);
  check('正解として記録される', last && last.ok === true, JSON.stringify(last));
  check('「正解です」と読む', await page.evaluate(() => window.__spoken.some(t => /正解です/.test(t))));
  check('画面にも結果が出る', await page.locator('#q-card .resultbanner').count() > 0);

  // 「解説」→ 全肢の解説を読む
  n0 = await page.evaluate(() => window.__spoken.length);
  await page.evaluate(() => window.__say.push('解説'));
  await wait(800);
  check('「解説」で全肢の解説を読む', await page.evaluate(n => window.__spoken.slice(n).join('').includes('は不正解'), n0));

  // 「次」→ 次の問題
  await page.evaluate(() => window.__say.push('次'));
  await wait(400);
  check('「次」で次の問題に進む', await waitPhase('ask') && await page.evaluate(id => cur.id !== id, q1.id));

  // 言いよどみ「えーと」を A と取り違えないか / 聞き取れないときは聞き直す
  const q2 = await page.evaluate(() => ({ id: cur.id, letters: dispLetters(cur), avail: displayOpts(cur).map(o => o.letter), need: cur.n_correct || 1 }));
  await page.evaluate(() => window.__say.push('えーと'));
  await wait(600);
  check('「えーと」は回答にしない', await page.evaluate(id => VOICE.phase === 'ask' && cur.id === id, q2.id));

  // 間違えた答え
  const wrong = q2.avail.filter(l => !q2.letters.includes(l)).slice(0, q2.need);
  await page.evaluate(s => window.__say.push(s), sayAns(wrong));
  check('誤答も結果に進む', await waitPhase('result'));
  const last2 = await page.evaluate(() => sessionLog[sessionLog.length - 1]);
  check('不正解として記録される', last2 && last2.ok === false);
  check('「不正解。正解は…」と読む', await page.evaluate(() => window.__spoken.join('').includes('不正解。正解は')));

  // 「わからない」は不正解として記録し正解を読む
  await page.evaluate(() => window.__say.push('次'));
  await waitPhase('ask');
  const q3 = await page.evaluate(() => cur.id);
  await page.evaluate(() => window.__say.push('わからない'));
  check('「わからない」で正解を聞ける', await waitPhase('result'));
  const last3 = await page.evaluate(() => sessionLog[sessionLog.length - 1]);
  check('「わからない」は不正解として記録', last3 && last3.id === q3 && last3.ok === false);

  // 残りを片付けてセット終了 → 「続ける」
  for (let i = 0; i < 6; i++) {
    const ph = await page.evaluate(() => VOICE.phase);
    if (ph === 'finish') break;
    if (ph === 'result') { await page.evaluate(() => window.__say.push('次')); await wait(500); continue; }
    if (ph === 'ask') {
      const l = await page.evaluate(() => dispLetters(cur));
      await page.evaluate(s => window.__say.push(s), sayAns(l));
      await waitPhase('result');
    }
  }
  check('セット終了をまとめて読む', await waitPhase('finish') && await page.evaluate(() => window.__spoken.some(t => /このセットは終了/.test(t))));
  await page.evaluate(() => window.__say.push('続ける'));
  const okc = await waitPhase('ask');
  check('「続ける」で次のセット', okc, okc ? '' : await page.evaluate(() => JSON.stringify({ph: VOICE.phase, n: sessionN, id: cur && cur.id, asked: VOICE.askedId, say: window.__say, last: window.__spoken.slice(-3)})));

  // 無音が続いても聞き直し続ける(ボタンを押させない)
  const s0 = await page.evaluate(() => window.__recStarts);
  await wait(1200);
  check('無音のあと自動で聞き直す', await page.evaluate(n => window.__recStarts > n + 2, s0));

  // 「終了」で止まる
  await page.evaluate(() => window.__say.push('終了'));
  await wait(400);
  check('「終了」で音声モードを止める', await page.evaluate(() => !VOICE.on) && !(await page.locator('#voicebar').isVisible()));

  // 模擬試験では使わない / タップでの操作は今までどおり
  await page.locator('nav button[data-v="home"]').click();
  await page.waitForSelector('#v-home.on');
  await page.locator('button:has-text("問題を解く(おまかせ)")').click();
  await page.waitForSelector('#q-card .opt');
  check('通常モードでは読み上げない', await page.evaluate(() => !VOICE.on));

  // 送り仮名つきの言い方もコマンドとして通るか
  const cmds = await page.evaluate(() => ['続けて','詳しく','進めて','終わり','止めて','繰り返して','分からない'].map(x => vCommand(vNorm(x))));
  check('送り仮名つきの言い方', JSON.stringify(cmds) === JSON.stringify(['cont','expl','next','stop','stop','repeat','pass']), JSON.stringify(cmds));
  const lt = await page.evaluate(() => [vLetters(vNorm('AとC'), ['A','B','C','D','E']), vLetters(vNorm('ビーです'), ['A','B','C','D']), vLetters(vNorm('3番'), ['A','B','C','D']), vLetters(vNorm('えーとディー'), ['A','B','C','D'])]);
  check('記号の聞き取り', JSON.stringify(lt) === JSON.stringify([['A','C'],['B'],['C'],['D']]), JSON.stringify(lt));
  check('ページのエラーなし', errors.length === 0, errors.join(' / '));
  const ng = results.filter(r => !r).length;
  console.log(ng ? `\n${ng}件NG` : '\n全項目OK');
  await browser.close();
  process.exit(ng ? 1 : 0);
})();
