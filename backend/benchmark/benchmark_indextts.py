"""
benchmark_indextts.py
IndexTTS 专项评测脚本（通过后端 API，含情感识别）

用法：
  python benchmark_indextts.py                       # 完整流程（中文）
  python benchmark_indextts.py --lang english        # 完整流程（英文）
  python benchmark_indextts.py --tts-only            # 仅生成音频
  python benchmark_indextts.py --stt-only            # 仅 STT 评估
"""

import os
import sys
import json
import time
import argparse
import wave
import io
import statistics
import re
from pathlib import Path
from datetime import datetime

import torch
import requests

# ─── 路径配置 ───────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
SCRIPT_DIR = Path(__file__).parent
BACKEND_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = BACKEND_ROOT / "outputs"
RESULTS_DIR = BACKEND_ROOT / "results"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 后端 API 地址
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# 参考音频（IndexTTS 需要参考音频）
DEFAULT_REF_AUDIO = r"D:\Python\Project\tts_test_output\reference_calm.wav"


# ─── 测试文本加载 ───────────────────────────────────────────────────────────

def load_chinese_texts() -> list:
    """加载中文测试文本"""
    path = SCRIPT_DIR / "texts" / "chinese.txt"
    texts = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            texts.append(line)
    return texts


def load_english_texts() -> list:
    """加载英文测试文本"""
    path = SCRIPT_DIR  / "texts" / "english.txt"
    texts = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            texts.append(line)
    return texts


# ─── 音频处理 ───────────────────────────────────────────────────────────────

def get_audio_duration(data: bytes) -> float:
    """获取音频时长（秒）"""
    try:
        bio = io.BytesIO(data)
        with wave.open(bio, 'rb') as wf:
            return wf.getnframes() / wf.getframerate()
    except Exception:
        return 0.0


def save_wav(data: bytes, path: str):
    """保存 WAV 文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def get_gpu_mb() -> float:
    """获取当前 GPU 显存占用（MB）"""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024 / 1024
    return 0.0


# ─── 通过后端 API 调用 TTS（含情感识别）─────────────────────────────────────

def call_tts_api(
    text: str,
    engine: str = "indextts",
    voice: str = "default",
    ref_audio_path: str = None
) -> dict:
    """
    调用后端 /tts/synthesize API
    """
    t0 = time.perf_counter()

    # 准备请求数据
    data = {
        "text": text,
        "voice": voice,
        "engine": engine,
    }

    files = {}
    if ref_audio_path and os.path.exists(ref_audio_path):
        files["reference_audio"] = ("reference_audio.wav", open(ref_audio_path, "rb"), "audio/wav")

    try:
        response = requests.post(
            f"{BACKEND_URL}/tts/synthesize",
            data=data,
            files=files,
            timeout=None
        )

        latency_ms = (time.perf_counter() - t0) * 1000

        if response.status_code != 200:
            return {
                "success": False,
                "engine": engine,
                "text": text,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }

        audio_data = response.content
        duration = get_audio_duration(audio_data)

        # 从响应头获取情感信息
        detected_emotion = response.headers.get("X-Emotion", "unknown")
        emotion_intensity = response.headers.get("X-Emotion-Intensity", "0")

        return {
            "success": True,
            "engine": engine,
            "text": text,
            "audio_data": audio_data,
            "latency_ms": round(latency_ms, 2),
            "audio_duration_s": round(duration, 4),
            "rtf": round((latency_ms / 1000) / duration, 4) if duration > 0 else 0,
            "detected_emotion": detected_emotion,
            "emotion_intensity": float(emotion_intensity),
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "engine": engine,
            "text": text,
            "error": "API 超时（600秒）",
        }
    except Exception as e:
        return {
            "success": False,
            "engine": engine,
            "text": text,
            "error": str(e),
        }
    finally:
        if "files" in locals() and "reference_audio" in files:
            files["reference_audio"][1].close()


def run_tts(texts: list, engine: str = "indextts", lang_label: str = "中文") -> list:
    """批量调用 TTS API 生成音频"""
    results = []
    engine_dir = OUTPUT_DIR / engine / ("chinese" if lang_label == "中文" else "english")
    os.makedirs(engine_dir, exist_ok=True)

    # 准备参考音频（IndexTTS 需要）
    ref_audio = DEFAULT_REF_AUDIO

    print(f"\n{'=' * 60}")
    print(f"[{engine}] 开始生成，共 {len(texts)} 条 {lang_label} 文本（含情感识别）")
    print(f"[{engine}] 参考音频: {ref_audio}")
    print(f"[{engine}] 后端地址: {BACKEND_URL}")
    print(f"{'=' * 60}")

    for i, text in enumerate(texts):
        safe = text.replace(" ", "_")[:40]
        safe = re.sub(r'[\\/*?:"<>|]', '', safe)
        if not safe:
            safe = f"text_{i + 1}"
        out_path = str(engine_dir / f"{i + 1:03d}_{safe}.wav")

        print(f"  [{i + 1}/{len(texts)}] {text[:30]}...", end=" ", flush=True)

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()
        gpu_before = get_gpu_mb()

        result = call_tts_api(text, engine=engine, ref_audio_path=ref_audio)

        gpu_peak = max(get_gpu_mb() - gpu_before, 0) if torch.cuda.is_available() else 0

        result["index"] = i
        result["lang"] = lang_label
        result["gpu_peak_mb"] = round(gpu_peak, 1)

        if result["success"]:
            save_wav(result.pop("audio_data"), out_path)
            result["output_path"] = out_path
            print(f"OK emotion={result['detected_emotion']} ({result['emotion_intensity']:.2f}) "
                  f"latency={result['latency_ms']}ms, rtf={result['rtf']}")
        else:
            print(f"FAIL: {result.get('error', 'unknown')}")

        results.append(result)

    out_file = RESULTS_DIR / f"tts_{engine}_{TIMESTAMP}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nTTS 结果已保存: {out_file}")
    return results


# ─── STT 评估 ───────────────────────────────────────────────────────────────

def run_stt(results: list, language: str = "zh") -> list:
    """Whisper STT 评估"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError("faster-whisper 未安装：pip install faster-whisper")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    lang_code = "zh" if language == "zh" else "en"
    model = WhisperModel("base", device=device, compute_type=compute_type)

    evaluated = []
    print(f"\n{'=' * 60}")
    print(f"[STT] 评估中... (语言: {lang_code})")

    for item in results:
        if not item.get("success"):
            evaluated.append({**item, "stt_transcript": "", "wer": None, "is_match": False})
            continue

        audio_path = item["output_path"]
        original = item["text"]

        try:
            segments, _ = model.transcribe(audio_path, language=lang_code, beam_size=5, vad_filter=True)
            transcript = "".join(s.text for s in segments)
        except Exception as e:
            transcript = ""
            print(f"  Warning: STT failed for {original[:20]}...: {e}")

        if lang_code == "zh":
            from utils import wer as wer_raw
            def wer_chinese(ref: str, hyp: str) -> float:
                ref_chars = list(ref.strip())
                hyp_chars = list(hyp.strip())
                return wer_raw("".join(ref_chars), "".join(hyp_chars))
            score = wer_chinese(original, transcript)
            is_match = original.strip() == transcript.strip()
        else:
            from utils import wer, normalize_english
            score = wer(original, transcript)
            is_match = normalize_english(original) == normalize_english(transcript)

        evaluated.append({
            **item,
            "stt_transcript": transcript,
            "wer": round(score, 6),
            "is_match": is_match,
        })

    out_file = RESULTS_DIR / f"stt_{results[0].get('engine', 'unknown')}_{TIMESTAMP}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(evaluated, f, ensure_ascii=False, indent=2)
    print(f"STT 结果已保存: {out_file}")
    return evaluated


# ─── 汇总报告 ───────────────────────────────────────────────────────────────

def build_report(results: list) -> dict:
    successful = [r for r in results if r.get("success")]
    matched = [r for r in successful if r.get("is_match")]

    def mean(lst): return round(statistics.mean(lst), 4) if lst else None
    def median(lst): return round(statistics.median(lst), 4) if lst else None

    wers = [r["wer"] for r in successful if r.get("wer") is not None]
    rtfs = [r["rtf"] for r in successful if "rtf" in r]
    latencies = [r["latency_ms"] for r in successful if "latency_ms" in r]
    gpu_peaks = [r["gpu_peak_mb"] for r in successful if "gpu_peak_mb" in r]
    emotions = [r["detected_emotion"] for r in successful if "detected_emotion" in r]

    emotion_counts = {}
    for e in emotions:
        emotion_counts[e] = emotion_counts.get(e, 0) + 1

    report = {
        "timestamp": TIMESTAMP,
        "engine": results[0].get("engine", "unknown") if results else "unknown",
        "lang": results[0].get("lang", "unknown") if results else "unknown",
        "total": len(results),
        "success_count": len(successful),
        "success_rate": round(len(successful) / len(results), 4) if results else 0,
        "match_count": len(matched),
        "avg_rtf": mean(rtfs),
        "median_rtf": median(rtfs),
        "avg_latency_ms": mean(latencies),
        "median_latency_ms": median(latencies),
        "avg_gpu_peak_mb": mean(gpu_peaks),
        "median_gpu_peak_mb": median(gpu_peaks),
        "avg_wer": mean(wers),
        "median_wer": median(wers),
        "emotion_distribution": emotion_counts,
        "details": results,
    }
    return report


def print_report(report: dict):
    r = report
    lang_name = "中文" if r.get("lang") == "中文" else "英文"
    print(f"\n{'=' * 70}")
    print(f"{r['engine']} {lang_name} 评测报告（含情感识别）")
    print(f"  时间: {r['timestamp']}")
    print(f"{'=' * 70}")
    print(f"  成功率:    {r['success_rate'] * 100:.1f}%   ({r['success_count']}/{r['total']})")
    print(f"  匹配数:    {r['match_count']}")
    print(f"  ── 质量 ──")
    print(f"  平均 WER:  {r['avg_wer']:.4f}" if r['avg_wer'] is not None else "  平均 WER:  N/A")
    print(f"  ── 速度 ──")
    print(f"  平均 RTF:  {r['avg_rtf']:.4f}" if r['avg_rtf'] is not None else "  平均 RTF:  N/A")
    print(f"  平均延迟:  {r['avg_latency_ms']:.1f} ms" if r['avg_latency_ms'] is not None else "  平均延迟:  N/A")
    print(f"  ── 资源 ──")
    print(f"  GPU 峰值:  {r['avg_gpu_peak_mb']:.0f} MB" if r['avg_gpu_peak_mb'] is not None else "  GPU 峰值:  N/A")
    print(f"  ── 情感识别 ──")
    if r.get('emotion_distribution'):
        for emotion, count in r['emotion_distribution'].items():
            print(f"    {emotion}: {count} 次")
    print(f"{'=' * 70}\n")


# ─── 主入口 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="IndexTTS 专项评测（含情感识别）")
    parser.add_argument("--tts-only", action="store_true", help="仅生成音频")
    parser.add_argument("--stt-only", action="store_true", help="仅 STT 评估")
    parser.add_argument("--lang", default="chinese", choices=["chinese", "english"], help="测试语言")
    parser.add_argument("--engine", default="indextts", help="TTS 引擎名称")
    parser.add_argument("--backend", default=None, help="后端 API 地址")
    args = parser.parse_args()

    # 设置后端地址
    global BACKEND_URL
    if args.backend:
        BACKEND_URL = args.backend

    # 加载测试文本
    if args.lang == "english":
        texts = load_english_texts()
        lang_label = "英文"
        stt_lang = "en"
    else:
        texts = load_chinese_texts()
        lang_label = "中文"
        stt_lang = "zh"

    print(f"{lang_label}测试集: {len(texts)} 句")
    print(f"后端地址: {BACKEND_URL}")
    print(f"引擎: {args.engine}")

    if args.stt_only:
        files = sorted(RESULTS_DIR.glob(f"tts_{args.engine}_*.json"))
        if not files:
            print(f"未找到 TTS 结果文件 (tts_{args.engine}_*.json)")
            return
        with open(files[-1], 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = run_tts(texts, engine=args.engine, lang_label=lang_label)
        if args.tts_only:
            return

    evaluated = run_stt(results, language=stt_lang)
    report = build_report(evaluated)

    report_path = RESULTS_DIR / f"report_{args.engine}_{TIMESTAMP}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print_report(report)
    print(f"报告已保存: {report_path}")


if __name__ == "__main__":
    main()