# -*- coding: utf-8 -*-
"""聞き流し用の音声(解説型 + 覚える用の要点)を VOICEVOX で作る(PC で実行する)

使い方:  tools\\make_listen_audio.bat をダブルクリック(または python tools/make_listen_audio.py)

何を読むかは tools/listen_plan.json で決める(回答記録の分析から作る。2026-11-01 初版)。
  items : 読む順に並べた論点。正答率の低い分野から、分野の中は 間違えた→未回答→1回だけ正解 の順
          id(元の問題) / domain / topic(論点の見出し) / point(覚える用の1〜3文) / narration(解説型の40〜70秒)
          point と narration は元の問題の解説だけから書き、別の担当が解説と照合したもの

問題文と選択肢はそのまま読まない(耳だけでは頭に入らないと利用者から指摘があったため)。
解説型は「場面 → 使うもの → 紛らわしい案がだめな理由 → 一言で」の順に、説明するように話す。

出力(すべて audio/*-orig_*.mp3 の形。.gitignore で公開を許しているのはこの形だけ):
  audio/aip-c01-orig_listen_<i>of<n>.mp3   聞き流し(解説型)。分野ごとに1本
  audio/aip-c01-orig_points_<i>of<n>.mp3   覚える用の要点
  data/audio_tracks_listen.js              アプリの「聞く」タブの一覧(チャプター付き)

途中で止めても、作り終えた論点は audio/_cache_listen/ に残り、次回はそこから続ける。
文面を直した論点だけが作り直される。
声は音声モードと同じ春日部つむぎ。英語の読みは tools/voice_yomi.json。
"""
import hashlib
import io
import json
import re
import sys
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_voice_audio as mv  # noqa: E402  VOICEVOX の起動・合成・読みの変換を共有する

BASE = Path(__file__).resolve().parent.parent
PLAN = BASE / "tools" / "listen_plan.json"
OUT_DIR = BASE / "audio"
CACHE = OUT_DIR / "_cache_listen"
TRACKS_JS = BASE / "data" / "audio_tracks_listen.js"
LOG = OUT_DIR / "_listen_progress.txt"
FORMAT_VER = "2"
N_POINT_FILES = 2
SHORT_DOM = {
    "テスト・検証・トラブルシューティング": "テスト・検証",
    "運用効率と最適化": "運用効率",
    "基盤モデル統合・データ管理・コンプライアンス": "基盤モデル統合",
    "AI安全性・セキュリティ・ガバナンス": "安全性・ガバナンス",
    "実装と統合": "実装と統合",
}


def log(msg):
    print(msg, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    except Exception:
        pass


def frames_of(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return w.getparams(), w.readframes(w.getnframes())


def cl(t):
    """読み上げ用に整える。「A」「B」と並んだ例が括弧を外すとつながってしまうので、先に読点を挟む"""
    return mv.clean(re.sub(r"」\s*「", "」、「", str(t or "")))


class Speaker:
    def __init__(self):
        mv.start_engine()
        self.sid = mv.speaker_id()
        p, _ = frames_of(mv.synth("あ", self.sid))
        self.params = p
        self.rate = p.framerate

    def say(self, text):
        text = re.sub(r"。{2,}", "。", cl(text)).strip("。 ")
        if not text:
            return b""
        _, fr = frames_of(mv.synth(text + "。", self.sid))
        return fr

    def pause(self, sec):
        return b"\x00" * (int(self.rate * sec) * self.params.sampwidth * self.params.nchannels)

    def sec(self, frames):
        return round(len(frames) / (self.rate * self.params.sampwidth * self.params.nchannels), 1)


def cached(kind, it, num, parts, make):
    key = hashlib.sha1("\u0001".join([FORMAT_VER, kind, str(num), *parts]).encode("utf-8")).hexdigest()[:10]
    path = CACHE / f"{kind}_{it['id']}_{key}.pcm"
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    fr = make()
    path.write_bytes(fr)
    return fr


def narration_frames(sp, it, num):
    return cached("n", it, num, [it["topic"], it["narration"]],
                  lambda: sp.say(f"{num}。{it['topic']}。") + sp.pause(0.6) + sp.say(it["narration"]) + sp.pause(2.0))


def point_frames(sp, it, num):
    return cached("p", it, num, [it["topic"], it["point"]],
                  lambda: sp.say(f"{num}。{it['topic']}。") + sp.pause(0.35) + sp.say(it["point"]) + sp.pause(1.6))


def write_mp3(sp, frames, out, ff):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setparams(sp.params)
        w.writeframes(frames)
    mv.to_mp3(buf.getvalue(), out, ff)


def main():
    LOG.write_text("", encoding="utf-8")
    items = json.loads(PLAN.read_text(encoding="utf-8"))["items"]
    mv._yomi.update(json.loads(mv.YOMI.read_text(encoding="utf-8")))
    OUT_DIR.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    ff = mv.ffmpeg_exe()
    sp = Speaker()
    t0 = time.time()
    listen, points = [], []

    # 1) 聞き流し(解説型)。分野ごとに1本
    doms = []
    for it in items:
        if it["domain"] not in doms:
            doms.append(it["domain"])
    for fi, dom in enumerate(doms):
        group = [it for it in items if it["domain"] == dom]
        name = SHORT_DOM.get(dom, dom)
        frames = sp.say(f"{name}の分野。{len(group)}の論点です。") + sp.pause(1.0)
        chapters = []
        for gi, it in enumerate(group):
            chapters.append({"t": f"{gi+1}. {it['topic']}", "s": sp.sec(frames)})
            frames += narration_frames(sp, it, gi + 1)
            log(f"[聞き流し {fi+1}/{len(doms)}] {it['id']} ({gi+1}/{len(group)}) 経過{(time.time()-t0)/60:.0f}分")
        out = OUT_DIR / f"aip-c01-orig_listen_{fi+1}of{len(doms)}.mp3"
        write_mp3(sp, frames, out, ff)
        listen.append({"exam": "AIP-C01", "kind": "listen",
                       "title": f"聞き流し {fi+1}/{len(doms)}：{name}（{len(group)}論点・約{round(sp.sec(frames)/60)}分）",
                       "src": f"audio/{out.name}", "chapters": chapters})
        log(f"聞き流し {fi+1}/{len(doms)} 書き出し ({out.stat().st_size//1024}KB)")

    # 2) 覚える用の要点(分野の切れ目でチャプター)
    per = (len(items) + N_POINT_FILES - 1) // N_POINT_FILES
    for fi in range(N_POINT_FILES):
        group = items[fi * per:(fi + 1) * per]
        frames, chapters, last = b"", [], None
        for gi, it in enumerate(group):
            name = SHORT_DOM.get(it["domain"], it["domain"])
            if name != last:
                chapters.append({"t": name, "s": sp.sec(frames)})
                frames += sp.say(f"{name}の分野。") + sp.pause(0.8)
                last = name
            frames += point_frames(sp, it, fi * per + gi + 1)
        out = OUT_DIR / f"aip-c01-orig_points_{fi+1}of{N_POINT_FILES}.mp3"
        write_mp3(sp, frames, out, ff)
        points.append({"exam": "AIP-C01", "kind": "points",
                       "title": f"覚える用の要点 {fi+1}/{N_POINT_FILES}（{len(group)}項目・約{round(sp.sec(frames)/60)}分）",
                       "src": f"audio/{out.name}", "chapters": chapters})
        log(f"要点 {fi+1}/{N_POINT_FILES} 書き出し ({out.stat().st_size//1024}KB) 経過{(time.time()-t0)/60:.0f}分")

    js = ("// 聞き流し用の音声(VOICEVOX:春日部つむぎ)。tools/make_listen_audio.py で生成\n"
          "// 回答記録をもとに、苦手な分野・間違えた問題の論点から並べている(tools/listen_plan.json)\n"
          "window.AUDIO_TRACKS = (window.AUDIO_TRACKS||[]).concat(" + json.dumps(listen + points, ensure_ascii=False) + ");\n")
    TRACKS_JS.write_text(js, encoding="utf-8")
    log(f"完了: {len(listen) + len(points)}本 / data/audio_tracks_listen.js 出力済み / 総所要 {(time.time()-t0)/60:.0f}分")


if __name__ == "__main__":
    main()
