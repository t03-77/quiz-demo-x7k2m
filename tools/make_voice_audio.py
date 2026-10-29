# -*- coding: utf-8 -*-
"""音声モード用の読み上げ音声を VOICEVOX で事前に作る(PC で実行する)

使い方:  tools\\make_voice_audio.bat をダブルクリック(または python tools/make_voice_audio.py)
- VOICEVOX が起動していなければ、エンジン(run.exe)を自動で起動する
- 1問につき3ファイル(問題+選択肢 / 正解の記号 / 正解の解説)を audio/ に mp3 で書き出す
- 途中で止めても、次回は作っていない問題から続ける(問題の文面が変わった問題は作り直す)
- 最後に data/voice_audio.js(どの問題の音声があるかの一覧)を書き出す

アプリ側は、問題の文面のハッシュが一覧と一致するときだけこの音声を使い、
一致しない(問題を直したのに音声を作り直していない)ときは端末の読み上げに戻る。
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import wave
import io
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ORIG = BASE / "data" / "orig.js"
OUT_DIR = BASE / "audio"
MANIFEST = BASE / "data" / "voice_audio.js"
YOMI = BASE / "tools" / "voice_yomi.json"
EXAMS = ["AIP-C01"]                      # 対象の資格
SPEAKER_NAME, STYLE_NAME = "春日部つむぎ", "ノーマル"
ENGINE = "http://127.0.0.1:50021"
LN = {"A": "エー", "B": "ビー", "C": "シー", "D": "ディー", "E": "イー", "F": "エフ"}
# 毎回同じ言い回しになる短い音声(アプリが組み合わせて使う)
COMMON = {
    "ok": "正解です。",
    "ng": "不正解。",
    "next": "「次」で進みます。",
    "nextlast": "「次」で、このセットの結果に進みます。",
    "prompt": "答えを記号で言ってください。",
    "again": "もう一度どうぞ。",
    "start": "音声モードを開始します。",
}


# ---------- アプリと同じ計算 ----------
def fnv_hex(s: str) -> str:
    """index.html の vHash と同じ FNV-1a(UTF-16 のコード単位ごと)"""
    h = 2166136261
    b = s.encode("utf-16-le")
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i + 1] << 8)
        h = (h * 16777619) & 0xFFFFFFFF
    return format(h, "08x")


def shuffled(arr, seed):
    """index.html の shuffled() を移植(選択肢の表示順を音声と画面でそろえる)"""
    s = 2166136261
    for c in seed:
        s ^= ord(c[0]) & 0xFFFF
        s = (s * 16777619) & 0xFFFFFFFF

    def rnd():
        nonlocal s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        s &= 0xFFFFFFFF
        return s / 4294967296

    a = list(arr)
    for i in range(len(a) - 1, 0, -1):
        j = int(rnd() * (i + 1))
        a[i], a[j] = a[j], a[i]
    return a


def qkey(q) -> str:
    """問題の文面のハッシュ。アプリの vAudioKey と同じ材料・順番"""
    parts = [q["question"], "\u0002".join(o["text"] for o in q["options"]),
             ",".join(o["letter"] for o in q["options"] if o["correct"]),
             "\u0002".join((o.get("explanation") or "") for o in q["options"] if o["correct"]),
             q.get("explanation") or ""]
    return fnv_hex("\u0001".join(parts))


# ---------- 読み上げ文 ----------
_yomi = {}
_tok = re.compile(r"[A-Za-z][A-Za-z0-9\.\-_/:+']*[A-Za-z0-9]|[A-Za-z]")


def yomi(t: str) -> str:
    return _tok.sub(lambda m: _yomi.get(m.group(0), m.group(0)), t)


def clean(t: str) -> str:
    t = str(t or "")
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"^(正解です|不正解です)。?", "", t)
    t = re.sub(r"[「」『』【】]", "", t)
    t = re.sub(r"\s*/\s*", "、", t)
    t = t.replace("→", "、")
    t = re.sub(r"\n+", "。", t)
    return yomi(t.strip())


def texts_for(q):
    opts = shuffled(q["options"], "opt:" + q["id"])
    letters = "ABCDEFGH"
    disp = [(letters[i], o) for i, o in enumerate(opts)]
    qt = clean(q["question"]) + "。選択肢。" + "".join(f"{LN[L]}。{clean(o['text'])}。" for L, o in disp)
    need = q.get("n_correct") or 1
    if need > 1:
        qt += f"{need}つ答えてください。"
    corr = [L for L, o in disp if o["correct"]]
    ct = "正解は" + "と".join(LN[L] for L in corr) + "です。"
    ex = "。".join(clean(o.get("explanation")) for o in q["options"] if o["correct"] and o.get("explanation"))
    at = ex or clean(q.get("explanation"))
    tidy = lambda x: re.sub(r"。{2,}", "。", re.sub(r"）。", "）", x))
    return {"q": tidy(qt), "c": ct, "a": tidy(at)}


# ---------- VOICEVOX ----------
def http(method, path, data=None, ctype=None, timeout=120):
    req = urllib.request.Request(ENGINE + path, data=data, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def engine_up():
    try:
        http("GET", "/version", timeout=3)
        return True
    except Exception:
        return False


def start_engine():
    if engine_up():
        return
    roots = [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "VOICEVOX", Path("C:/Program Files/VOICEVOX")]
    exe = None
    for r in roots:
        if r.exists():
            c = sorted(r.rglob("run.exe"))
            if c:
                exe = c[0]
                break
    if not exe:
        sys.exit("VOICEVOX が見つかりません。VOICEVOX を起動してからもう一度実行してください。")
    print("VOICEVOX のエンジンを起動します:", exe)
    subprocess.Popen([str(exe), "--use_gpu"], cwd=str(exe.parent), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(120):
        if engine_up():
            return
        time.sleep(1)
    sys.exit("VOICEVOX のエンジンが起動しませんでした。VOICEVOX を起動してからもう一度実行してください。")


def speaker_id():
    sp = json.loads(http("GET", "/speakers"))
    for s in sp:
        if s["name"] == SPEAKER_NAME:
            for st in s["styles"]:
                if st["name"] == STYLE_NAME:
                    return st["id"]
    sys.exit(f"{SPEAKER_NAME}（{STYLE_NAME}）が見つかりません")


def synth(text, sid):
    """長い文は句点で区切って合成し、つなげる(1回の合成が長すぎると遅くなるため)"""
    chunks, buf = [], ""
    for s in re.split(r"(?<=[。？！])", text):
        if not s.strip():
            continue
        if len(buf) + len(s) > 120 and buf:
            chunks.append(buf)
            buf = ""
        buf += s
    if buf:
        chunks.append(buf)
    frames, params = [], None
    for c in chunks:
        qs = urllib.parse.urlencode({"text": c, "speaker": sid})
        aq = json.loads(http("POST", "/audio_query?" + qs))
        aq["speedScale"] = 1.0
        aq["prePhonemeLength"] = 0.05
        aq["postPhonemeLength"] = 0.15
        wav = http("POST", f"/synthesis?speaker={sid}", json.dumps(aq).encode("utf-8"), "application/json", timeout=600)
        with wave.open(io.BytesIO(wav)) as w:
            params = w.getparams()
            frames.append(w.readframes(w.getnframes()))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setparams(params)
        for f in frames:
            w.writeframes(f)
    return out.getvalue()


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
    except ImportError:
        print("mp3 変換用の ffmpeg を用意します(初回のみ)…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"])
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def to_mp3(wav_bytes, path, ff):
    tmp = path.with_suffix(".tmp.wav")
    tmp.write_bytes(wav_bytes)
    subprocess.check_call([ff, "-y", "-loglevel", "error", "-i", str(tmp), "-ac", "1", "-b:a", "32k", str(path)])
    tmp.unlink()


def load_orig():
    s = ORIG.read_text(encoding="utf-8")
    return json.loads(s[s.index("["):s.rstrip().rstrip(";").rindex("]") + 1])


def fname(qid, part):
    # .gitignore で公開を許しているのは audio/*-orig_*.mp3 だけなので、その形にそろえる
    # 自作の別セット(例: AIP-C01_gap_001)も同じ形にそろえる。gap は番号を 9xx にして本番形式の番号と重ならないようにする
    exam, kind, num = re.match(r"^(.+?)_(orig|gap)_(\d+)$", qid).groups()
    if kind == "gap":
        num = "9" + num.zfill(2)[-2:]
    return f"{exam.lower()}-orig_{num}_{part}.mp3"


def main():
    global _yomi
    _yomi = json.loads(YOMI.read_text(encoding="utf-8")) if YOMI.exists() else {}
    OUT_DIR.mkdir(exist_ok=True)
    old = {}
    if MANIFEST.exists():
        t = MANIFEST.read_text(encoding="utf-8")
        try:
            old = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1]).get("items", {})
        except Exception:
            old = {}
    qs = [q for q in load_orig() if q["exam"] in EXAMS and q.get("type", "choice") == "choice"]
    if "--limit" in sys.argv:                       # 試しに数問だけ作る: --limit 3
        qs = qs[:int(sys.argv[sys.argv.index("--limit") + 1])]
    start_engine()
    sid = speaker_id()
    ff = ffmpeg_exe()
    print(f"{SPEAKER_NAME}（{STYLE_NAME}）で {len(qs)} 問ぶんの音声を作ります")
    for k, t in COMMON.items():
        p = OUT_DIR / f"{EXAMS[0].lower()}-orig_common_{k}.mp3"
        if not p.exists():
            to_mp3(synth(t, sid), p, ff)
    items = {}
    t0 = time.time()
    done = 0
    for i, q in enumerate(qs, 1):
        key = qkey(q)
        paths = {part: OUT_DIR / fname(q["id"], part) for part in ("q", "c", "a")}
        if old.get(q["id"]) == key and all(p.exists() for p in paths.values()):
            items[q["id"]] = key
            continue
        tx = texts_for(q)
        for part, p in paths.items():
            to_mp3(synth(tx[part], sid), p, ff)
        items[q["id"]] = key
        done += 1
        el = time.time() - t0
        rest = (len(qs) - i) * el / done
        print(f"[{i}/{len(qs)}] {q['id']}  残り約{int(rest // 60)}分")
        if done % 10 == 0:
            write_manifest(items, old)
    write_manifest(items, old)
    print("完了しました。GitHub Desktop でコミットして push すると、サイトで使われます。")


def write_manifest(items, old):
    allitems = dict(old)
    allitems.update(items)
    data = {"speaker": f"VOICEVOX:{SPEAKER_NAME}", "exams": EXAMS, "items": allitems}
    MANIFEST.write_text("// 音声モード用の事前生成音声の一覧(tools/make_voice_audio.py が書き出す)\n"
                        "window.VOICE_AUDIO = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
