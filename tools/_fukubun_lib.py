# -*- coding: utf-8 -*-
"""SAA-C03/AIF-C01 複文率調整の共通処理（読み込み・書式保持保存・計測）"""
import glob, json, re, statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "資料" / "生成"


def sent(t):
    return [s for s in re.split(r"(?<=[。？！])", t or "") if s.strip()]


WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+|[ァ-ヶー]{3,}|[一-龥]{2,}")


def overlap(q):
    ss = [set(WORD.findall(o.get("text", ""))) for o in q["options"] if o.get("text")]
    ss = [s for s in ss if s]
    pr = [len(ss[i] & ss[j]) / len(ss[i] | ss[j]) for i in range(len(ss))
          for j in range(i + 1, len(ss)) if (ss[i] | ss[j])]
    return statistics.mean(pr) if pr else 0


def detect_fmt(raw):
    """既存ファイルの書式(indent/改行/末尾改行)を推定する。
    指示された indent=2 + CRLF + 末尾改行に合わない既存ファイルが3つあるため、
    無改変ラウンドトリップがバイト一致する書式をファイルごとに使う。"""
    txt = raw.decode("utf-8")
    data = json.loads(txt)
    nl = "\r\n" if b"\r\n" in raw else "\n"
    for ind in (2, 1, 3, 4):
        for tail in ("\n", ""):
            s = (json.dumps(data, ensure_ascii=False, indent=ind) + tail).replace("\n", nl).encode("utf-8")
            if s == raw:
                return data, (ind, nl, tail)
    raise SystemExit("書式を特定できません（ラウンドトリップ不一致）")


def load(exam):
    """{path: (data, fmt)} と {id: (path, q)} を返す"""
    files, index = {}, {}
    for f in sorted(glob.glob(str(GEN / ("%s_orig*.json" % exam)))):
        raw = Path(f).read_bytes()
        data, fmt = detect_fmt(raw)
        files[f] = [data, fmt]
        for q in data:
            if q.get("exam") == exam:
                index[q["id"]] = (f, q)
    return files, index


def save(files, touched):
    for f in touched:
        data, (ind, nl, tail) = files[f]
        s = (json.dumps(data, ensure_ascii=False, indent=ind) + tail).replace("\n", nl)
        Path(f).write_bytes(s.encode("utf-8"))
