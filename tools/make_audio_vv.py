# -*- coding: utf-8 -*-
"""AIP-C01 公式95問の読み上げ音声を VOICEVOX(四国めたん)で生成する。

旧版(1.5倍速・4ファイル)からの改良:
- 等速(1.0x)で生成し、再生速度はアプリのプレイヤー側で調整する方式に変更
- 8ファイルに分割(1ファイル約12問・約50分)
- 問題ごとの開始秒を記録し、チャプター頭出し用の data/audio_tracks.js を出力
- カタカナ辞書はスペースなしの連続読み(v2の修正を踏襲)

構成は旧版と同じ: 問題+選択肢 → 4秒の間 → 正解 → 全選択肢の解説

使い方: python tools/make_audio_vv.py
(VOICEVOXエンジンは未起動なら自動起動する。生成には時間がかかる)
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import wave
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path(r"C:\Users\na7sh\Works\95_work\aws\06_lessons\genai_dev_pro\official\questions_official.json")
AUDIO_DIR = BASE / "audio"
CACHE_DIR = BASE / "audio" / "_cache"
TRACKS_JS = BASE / "data" / "audio_tracks.js"
ENGINE = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "VOICEVOX" / "vv-engine" / "run.exe"
API = "http://127.0.0.1:50021"
SPEAKER = 2          # 四国めたん(ノーマル)
N_FILES = 8
SAMPLE_RATE = 24000
PAUSE_SEC = 4.0

# カタカナ辞書(スペースなしの連続読み)。長い語から順に適用する
KATAKANA = {
    "Amazon OpenSearch Service": "アマゾンオープンサーチサービス",
    "OpenSearch Serverless": "オープンサーチサーバーレス",
    "Aurora PostgreSQL": "オーロラポストグレス",
    "Amazon Bedrock": "アマゾンベッドロック",
    "Amazon SageMaker": "アマゾンセージメーカー",
    "SageMaker JumpStart": "セージメーカージャンプスタート",
    "Step Functions": "ステップファンクションズ",
    "Secrets Manager": "シークレッツマネージャー",
    "Service Quotas": "サービスクォータス",
    "Knowledge Bases": "ナレッジベース",
    "Knowledge Base": "ナレッジベース",
    "CloudWatch Logs": "クラウドウォッチログス",
    "Model Monitor": "モデルモニター",
    "Ground Truth": "グラウンドトゥルース",
    "Amazon Kendra": "アマゾンケンドラ",
    "Amazon Titan": "アマゾンタイタン",
    "Amazon Nova": "アマゾンノヴァ",
    "Amazon Q": "アマゾンキュー",
    "EventBridge": "イベントブリッジ",
    "CloudFormation": "クラウドフォーメーション",
    "CloudWatch": "クラウドウォッチ",
    "CloudFront": "クラウドフロント",
    "CloudTrail": "クラウドトレイル",
    "OpenSearch": "オープンサーチ",
    "PostgreSQL": "ポストグレス",
    "DynamoDB": "ダイナモディービー",
    "AgentCore": "エージェントコア",
    "Guardrails": "ガードレール",
    "JumpStart": "ジャンプスタート",
    "QuickSight": "クイックサイト",
    "Rekognition": "レコグニション",
    "Personalize": "パーソナライズ",
    "Comprehend": "コンプリヘンド",
    "SageMaker": "セージメーカー",
    "Anthropic": "アンソロピック",
    "Transcribe": "トランスクライブ",
    "Translate": "トランスレイト",
    "Textract": "テキストラクト",
    "pgvector": "ピージーベクター",
    "Redshift": "レッドシフト",
    "Pinecone": "パインコーン",
    "Provisioned": "プロビジョンド",
    "Throughput": "スループット",
    "Fargate": "ファーゲート",
    "Bedrock": "ベッドロック",
    "Neptune": "ネプチューン",
    "Kinesis": "キネシス",
    "Clarify": "クラリファイ",
    "Mistral": "ミストラル",
    "Stability": "スタビリティ",
    "Forecast": "フォーキャスト",
    "Lambda": "ラムダ",
    "Aurora": "オーロラ",
    "Athena": "アテナ",
    "Claude": "クロード",
    "Cohere": "コヒア",
    "Titan": "タイタン",
    "X-Ray": "エックスレイ",
    "Llama": "ラマ",
    "Glue": "グルー",
    "Lex": "レックス",
    "Polly": "ポリー",
    "LoRA": "ローラ",
    "PEFT": "ペフト",
    "Agents": "エージェンツ",
    "Agent": "エージェント",
    "Amazon": "アマゾン",
    "k-NN": "ケーエヌエヌ",
    "TTFT": "ティーティーエフティー",
    "JSON": "ジェイソン",
    "YAML": "ヤムル",
    "HTTPS": "エイチティーティーピーエス",
    "HTTP": "エイチティーティーピー",
    "AWS": "エーダブリューエス",
    "API": "エーピーアイ",
    "IAM": "アイアム",
    "KMS": "ケーエムエス",
    "RAG": "ラグ",
    "VPC": "ブイピーシー",
    "EC2": "イーシーツー",
    "ECS": "イーシーエス",
    "EKS": "イーケーエス",
    "SQS": "エスキューエス",
    "SNS": "エスエヌエス",
    "SQL": "エスキューエル",
    "S3": "エススリー",
    "GPU": "ジーピーユー",
    "CPU": "シーピーユー",
    "PII": "ピーアイアイ",
    "LLM": "エルエルエム",
    "A2I": "エーツーアイ",
    "ML": "エムエル",
    "AI": "エーアイ",
    "FM": "エフエム",
    "ID": "アイディー",
}
_TERMS = sorted(KATAKANA.keys(), key=len, reverse=True)


def to_kana(text):
    for t in _TERMS:
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", KATAKANA[t], text)
    return text


def api(path, data=None, params=None, timeout=120):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method="POST" if path != "/version" else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ensure_engine():
    try:
        api("/version", timeout=3)
        return
    except Exception:
        pass
    print("VOICEVOXエンジンを起動中...")
    subprocess.Popen([str(ENGINE)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        time.sleep(2)
        try:
            api("/version", timeout=3)
            print("エンジン起動OK")
            return
        except Exception:
            continue
    sys.exit("ERROR: VOICEVOXエンジンが起動しません")


def synth_text(text):
    """1テキスト(〜200文字目安)を合成してWAVフレーム(bytes)を返す"""
    q = json.loads(api("/audio_query", params={"speaker": SPEAKER, "text": text}))
    q["speedScale"] = 1.0
    q["outputSamplingRate"] = SAMPLE_RATE
    q["outputStereo"] = False
    wav = api("/synthesis", data=json.dumps(q).encode(), params={"speaker": SPEAKER}, timeout=300)
    with wave.open(io.BytesIO(wav)) as w:
        return w.readframes(w.getnframes())


def sentences(text, limit=160):
    """句点・改行で分割し、limit文字以内のかたまりにまとめる"""
    parts = re.split(r"(?<=[。！？])|\n", text)
    out, cur = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(cur) + len(p) <= limit:
            cur += p
        else:
            if cur:
                out.append(cur)
            while len(p) > limit:  # 極端に長い一文は強制分割
                out.append(p[:limit])
                p = p[limit:]
            cur = p
    if cur:
        out.append(cur)
    return out


SILENCE = b"\x00\x00" * int(SAMPLE_RATE * PAUSE_SEC)
SHORT_PAUSE = b"\x00\x00" * int(SAMPLE_RATE * 0.7)


def question_audio(q, idx):
    """1問ぶんのWAVフレームを合成(キャッシュあり)"""
    cache = CACHE_DIR / f"{q['id']}.pcm"
    if cache.exists() and cache.stat().st_size > 0:
        return cache.read_bytes()
    texts = [f"問題、{idx}。{q['type']}。"] + sentences(q["question"])
    for o in q["options"]:
        texts += sentences(f"{o['letter']}。{o['text']}")
    frames = b""
    for t in texts:
        frames += synth_text(to_kana(t)) + SHORT_PAUSE
    frames += SILENCE  # 考える時間
    corrects = [o["letter"] for o in q["options"] if o.get("correct")]
    frames += synth_text(f"正解は、{'、と、'.join(corrects)}。" if corrects else "正解は、解説を参照してください。")
    frames += SHORT_PAUSE
    for o in q["options"]:
        for t in sentences(f"{o['letter']}。{o['explanation']}"):
            frames += synth_text(to_kana(t)) + SHORT_PAUSE
    frames += SILENCE
    cache.write_bytes(frames)
    return frames


def write_mp3(frames, out_path):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_wav = out_path.with_suffix(".tmp.wav")
    with wave.open(str(tmp_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(tmp_wav),
                    "-codec:a", "libmp3lame", "-b:a", "48k", str(out_path)], check=True)
    tmp_wav.unlink()


def main():
    qs = json.load(open(SRC, encoding="utf-8"))
    AUDIO_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    ensure_engine()

    per = (len(qs) + N_FILES - 1) // N_FILES
    tracks = []
    t0 = time.time()
    for fi in range(N_FILES):
        group = qs[fi * per:(fi + 1) * per]
        if not group:
            break
        out = AUDIO_DIR / f"aip-c01_{fi+1}of{N_FILES}.mp3"
        chapters = []
        if out.exists() and out.stat().st_size > 0:
            print(f"skip(生成済み): {out.name}")
            # チャプター情報はキャッシュから再計算
            frames_len = 0
            for gi, q in enumerate(group):
                chapters.append({"t": q["id"], "s": round(frames_len / 2 / SAMPLE_RATE, 1)})
                frames_len += len(question_audio(q, qs.index(q) + 1))
        else:
            frames = b""
            for gi, q in enumerate(group):
                chapters.append({"t": q["id"], "s": round(len(frames) / 2 / SAMPLE_RATE, 1)})
                qa = question_audio(q, qs.index(q) + 1)
                frames += qa
                el = time.time() - t0
                print(f"[{fi+1}/{N_FILES}] {q['id']} 完了 ({gi+1}/{len(group)}) 経過{el/60:.0f}分", flush=True)
            write_mp3(frames, out)
            print(f"書き出し: {out.name} ({out.stat().st_size//1024//1024}MB)")
        tracks.append({
            "exam": "AIP-C01",
            "title": f"AIP-C01 公式問題 読み上げ {fi+1}/{N_FILES} ({group[0]['id']}〜{group[-1]['id']})",
            "src": f"audio/{out.name}",
            "chapters": chapters,
        })

    js = "// AIP-C01 公式問題の読み上げ音声(VOICEVOX:四国めたん、等速)。tools/make_audio_vv.py で生成\n"
    js += "// 公式問題の読み上げのためサイトには同梱しない(.gitignore対象)\n"
    js += "window.AUDIO_TRACKS = " + json.dumps(tracks, ensure_ascii=False) + ";\n"
    TRACKS_JS.write_text(js, encoding="utf-8")
    print(f"完了: {len(tracks)}ファイル / audio_tracks.js 出力済み / 総所要 {(time.time()-t0)/60:.0f}分")


if __name__ == "__main__":
    main()
