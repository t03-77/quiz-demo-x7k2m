# -*- coding: utf-8 -*-
"""解説集HTML → 問題JSON変換スクリプト

資料/AWS認定_全問題解説集_*.html を仕様書§5.1スキーマ準拠のJSONに変換する。
出力: 資料/変換済み/questions_all.json (全問) + 資料/変換済み/summary.md (検証レポート)

問題タイプ:
- 複数選択 → type: "choice"  (options[].correct / explanation)
- マッチング → type: "matching" (statements[])
- 並び替え → type: "ordering" (order_answer[])
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC_DIR = BASE / "資料"
OUT_DIR = SRC_DIR / "変換済み"
PATCH_DIR = SRC_DIR / "補完"

SET_TYPE_MAP = {
    "問題集": ("qset", "Practice Question Set"),
    "模擬試験": ("exam", "Practice Exam"),
    "Pretest": ("pretest", "Pretest"),
}


def find_source_html():
    cands = sorted(SRC_DIR.glob("AWS認定_全問題解説集_*.html"))
    if not cands:
        sys.exit("ERROR: 資料/AWS認定_全問題解説集_*.html が見つかりません")
    return cands[0]


def split_sections(html):
    """[(exam_code, set_key, set_label, section_title, [pre_text, ...]), ...]"""
    sections = []
    for sec in re.finditer(
        r'<section id="s\d+"><h2>(.*?)<span class="n">.*?</h2>(.*?)</section>',
        html, re.S,
    ):
        title = re.sub(r"<[^>]+>", "", sec.group(1)).strip()
        # 例: "CLF-C02 — 問題集 (Practice Question Set)"
        m = re.match(r"([A-Z]{3}-C\d{2})\s*—\s*(問題集|模擬試験|Pretest)", title)
        if not m:
            sys.exit(f"ERROR: セクション見出しを解釈できません: {title}")
        exam, jp = m.group(1), m.group(2)
        set_key, set_label = SET_TYPE_MAP[jp]
        pres = [p.group(1) for p in re.finditer(r"<pre>(.*?)</pre>", sec.group(2), re.S)]
        sections.append((exam, set_key, set_label, title, pres))
    return sections


def unescape(text):
    return (text.replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace("&quot;", '"'))


def blocks(lines):
    """空行区切りの段落ブロックに分割"""
    out, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.rstrip())
        elif cur:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return out


def section_between(lines, start_marker, end_markers):
    """start_marker行の次から、end_markersのいずれかの行まで"""
    try:
        i = next(k for k, ln in enumerate(lines) if ln.strip() == start_marker)
    except StopIteration:
        return None
    out = []
    for ln in lines[i + 1:]:
        if ln.strip() in end_markers:
            break
        out.append(ln)
    return out


def parse_choice(text):
    lines = text.split("\n")
    q_lines = section_between(lines, "質問", {"回答オプション"})
    q_blocks = blocks(q_lines)
    question = "\n\n".join(q_blocks)

    # 回答オプション以降。ヘッダー行(オプション/正解/根拠)を読み飛ばす
    i = next(k for k, ln in enumerate(lines) if ln.strip() == "回答オプション")
    rest = [ln for ln in lines[i + 1:]]
    # 先頭のヘッダー語(オプション, 正解, 根拠)をスキップ
    j = 0
    while j < len(rest) and rest[j].strip() in {"", "オプション", "正解", "根拠"}:
        j += 1
    rest = rest[j:]

    # 選択肢は行頭 "A. " 〜 "F. " で始まる
    opt_starts = [k for k, ln in enumerate(rest) if re.match(r"^[A-F]\.\s", ln)]
    if not opt_starts:
        raise ValueError("選択肢が見つかりません")
    options = []
    for n, start in enumerate(opt_starts):
        end = opt_starts[n + 1] if n + 1 < len(opt_starts) else len(rest)
        chunk = rest[start:end]
        letter = chunk[0][0]
        bs = blocks(chunk)
        # 1ブロック目 = 選択肢本文(先頭 "A. " を除去)
        opt_text = re.sub(r"^[A-F]\.\s*", "", bs[0])
        correct = False
        expl_blocks = []
        for b in bs[1:]:
            if b.strip() == "正解":
                correct = True
            else:
                expl_blocks.append(b)
        explanation = "\n\n".join(expl_blocks)
        # 標記ゆれ対策: 説明文冒頭でも判定
        if explanation.startswith("正解です"):
            correct = True
        options.append({
            "letter": letter, "text": opt_text,
            "correct": correct, "explanation": explanation,
        })

    # 問題文に「n つ選択」の明記がある場合のみ整合チェックに使う。
    # 明記なしで正解が複数の問題も存在するため、その場合はマーク数を採用する。
    m = re.search(r"(\d+)\s*つ選択", question)
    stated = int(m.group(1)) if m else None
    n_marked = sum(1 for o in options if o["correct"])
    if stated is not None and stated != n_marked:
        raise ValueError(f"正解数不一致: 問題文={stated} マーク={n_marked}")
    return question, options, n_marked


def parse_matching(text):
    lines = text.split("\n")
    q_lines = section_between(lines, "質問", {"マッチング結果", "回答オプション"})
    question = "\n\n".join(blocks(q_lines))
    body = section_between(lines, "マッチング結果", {"根拠"})
    if body is None:
        body = section_between(lines, "回答オプション", {"根拠"})
    bs = blocks(body)
    # 先頭のヘッダー語を除去
    while bs and bs[0].strip() in {"ステートメント", "正解", "オプション"}:
        bs.pop(0)
    # 評価画面のバグで回答が記録されていない問題(SCS Pretest等)
    if len(bs) == 1 and "利用できるオプションはありません" in bs[0]:
        return question, [], extract_rationale(lines), True
    # (ステートメント, 正解, 受験時の選択) の3ブロック繰り返し。
    # 2列目が正解列(誤答した問題では3列目と異なるが、採用するのは正解列)
    if len(bs) % 3 != 0:
        raise ValueError(f"マッチングのブロック数が3の倍数でない: {len(bs)}")
    statements = []
    for k in range(0, len(bs), 3):
        statements.append({"statement": bs[k], "answer": bs[k + 1]})
    expl = extract_rationale(lines)
    return question, statements, expl, False


def parse_ordering(text):
    lines = text.split("\n")
    q_lines = section_between(lines, "質問", {"回答オプション"})
    question = "\n\n".join(blocks(q_lines))
    body = section_between(lines, "回答オプション", {"根拠"})
    bs = blocks(body)
    while bs and bs[0].strip() in {"オプション", "正解"}:
        bs.pop(0)
    # (選択 k, 正解, 受験時の選択) の3ブロック繰り返し。1列目が正解列
    # (誤答した問題では2列目と異なるが、採用するのは正解列)。
    # 末尾に (不正解の選択肢 n, 本文) のダミー選択肢が続く場合がある。
    # ラベルが「不正解の選択肢 NaN」+同一ペアの行は表示バグの回答行(要確認扱い)
    order, distractors = [], []
    needs_review = False
    k = 0
    while k < len(bs):
        if re.match(r"^選択\s*\d+", bs[k]):
            order.append(bs[k + 1])
            k += 3
        elif re.match(r"^不正解の選択肢\s*NaN", bs[k]):
            if k + 2 < len(bs) and bs[k + 1] == bs[k + 2]:
                order.append(bs[k + 1])
                needs_review = True
                k += 3
            else:
                distractors.append(bs[k + 1])
                needs_review = True
                k += 2
        elif re.match(r"^不正解の選択肢\s*\d+", bs[k]):
            distractors.append(bs[k + 1])
            k += 2
        else:
            raise ValueError(f"並び替えの構造が想定外: {bs[k]!r}")
    expl = extract_rationale(lines)
    return question, order, distractors, expl, needs_review


def extract_rationale(lines):
    try:
        i = next(k for k, ln in enumerate(lines) if ln.strip() == "根拠")
    except StopIteration:
        return ""
    return "\n\n".join(blocks(lines[i + 1:]))


def main():
    src = find_source_html()
    html = src.read_text(encoding="utf-8")
    sections = split_sections(html)

    all_questions = []
    errors = []
    counters = {}
    for exam, set_key, set_label, title, pres in sections:
        for idx, raw in enumerate(pres, start=1):
            text = unescape(raw)
            first_lines = [ln.strip() for ln in text.split("\n") if ln.strip()][:2]
            qtype_jp = first_lines[1] if len(first_lines) > 1 else "?"
            qid = f"{exam}_{set_key}_{idx:03d}"
            entry = {
                "id": qid,
                "source": title,
                "exam": exam,
                "set": set_key,
                "number": idx,
                "domain": "",
            }
            try:
                if qtype_jp == "複数選択":
                    q, opts, n = parse_choice(text)
                    n_marked = sum(1 for o in opts if o["correct"])
                    if n != n_marked:
                        raise ValueError(
                            f"正解数不一致: 問題文={n} マーク={n_marked}")
                    entry.update(type="choice", question=q,
                                 n_correct=n, options=opts)
                elif qtype_jp == "マッチング":
                    q, stmts, expl, review = parse_matching(text)
                    entry.update(type="matching", question=q,
                                 statements=stmts, explanation=expl)
                    if review:
                        entry["needs_review"] = True
                elif qtype_jp == "並び替え":
                    q, order, distractors, expl, review = parse_ordering(text)
                    entry.update(type="ordering", question=q,
                                 order_answer=order, distractors=distractors,
                                 explanation=expl)
                    if review:
                        entry["needs_review"] = True
                else:
                    raise ValueError(f"未知の問題タイプ: {qtype_jp}")
                all_questions.append(entry)
                counters[title] = counters.get(title, 0) + 1
            except Exception as e:
                errors.append(f"{qid}: {e}")

    # 補完パッチの適用(キャプチャ時のバグで欠損した問題の回答・解説を上書き)
    patched = []
    if PATCH_DIR.exists():
        by_id = {q["id"]: q for q in all_questions}
        for pf in sorted(PATCH_DIR.glob("*.json")):
            patches = json.load(open(pf, encoding="utf-8"))
            for qid, fields in patches.items():
                if qid not in by_id:
                    print(f"WARN: パッチ対象が見つかりません: {qid}")
                    continue
                by_id[qid].update(fields)
                if not by_id[qid].get("needs_review"):
                    by_id[qid].pop("needs_review", None)
                patched.append(qid)

    OUT_DIR.mkdir(exist_ok=True)
    out = {
        "meta": {
            "title": "AWS認定 Skill Builder公式問題 全問バンク",
            "source_file": src.name,
            "generated_by": "tools/convert_kaisetsu_html.py",
            "total": len(all_questions),
            "note": "AWS公式問題のためローカル読み込みセット扱い(サイト同梱不可)。仕様書§3.8参照",
        },
        "questions": all_questions,
    }
    (OUT_DIR / "questions_all.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    reviews = [q["id"] for q in all_questions if q.get("needs_review")]
    lines = ["# 変換レポート", "",
             f"- 変換元: {src.name}",
             f"- 変換成功: {len(all_questions)}問 / エラー: {len(errors)}件"
             f" / 要確認(キャプチャ時の表示バグで回答欠損): {len(reviews)}問"
             f" / 補完パッチ適用: {len(patched)}問", "",
             "## セクション別内訳", ""]
    for exam, set_key, set_label, title, pres in sections:
        ok = counters.get(title, 0)
        mark = "✅" if ok == len(pres) else "⚠️"
        lines.append(f"- {mark} {title}: {ok}/{len(pres)}")
    if reviews:
        lines += ["", "## 要確認の問題", ""] + [f"- {r}" for r in reviews]
    if errors:
        lines += ["", "## エラー", ""] + [f"- {e}" for e in errors]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"OK: {len(all_questions)} questions, {len(errors)} errors")
    for e in errors[:20]:
        print("ERR:", e)


if __name__ == "__main__":
    main()
