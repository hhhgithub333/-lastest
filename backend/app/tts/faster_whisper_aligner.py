import tempfile
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
import logging
import subprocess
import threading

FFMPEG_DIR = r"F:\ffmpeg\ffmpeg-8.1-full_build\bin"
if FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

logger = logging.getLogger(__name__)

# 验证 ffmpeg
try:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    print("[Align] ffmpeg 就绪", flush=True)
except Exception as e:
    print(f"[Align] ffmpeg 不可用: {e}", flush=True)

# 模型缓存
_whisper_model = None
_align_models = {}          # {model_path: (model, metadata)}
_loading_lock = threading.Lock()
_model_loaded = False

# Whisper 模型路径（tiny 版本，本地缓存）
WHISPER_MODEL_PATH = r"E:\hf_cache\huggingface\hub\models--Systran--faster-whisper-tiny\snapshots\d90ca5fe260221311c53c58e660288d3deb8d356"

# 本地 wav2vec2 对齐模型路径
LOCAL_WAV2VEC2_PATH = r"F:\wav2vec2-chinese"


def warmup():
    """预热：提前加载 Whisper 模型 + wav2vec2 对齐模型"""
    global _model_loaded, _whisper_model
    print("[Align] 开始预热模型（Whisper ASR + wav2vec2 强制对齐）...", flush=True)

    try:
        from faster_whisper import WhisperModel
        import whisperx

        with _loading_lock:
            # 加载 Whisper ASR 模型
            if _whisper_model is None:
                _whisper_model = WhisperModel(
                    WHISPER_MODEL_PATH,
                    device="cpu",
                    compute_type="int8",
                    local_files_only=True
                )
                print("[Align] Whisper ASR 模型加载完成", flush=True)

            # 加载 wav2vec2 强制对齐模型（使用本地路径）
            if LOCAL_WAV2VEC2_PATH not in _align_models:
                print("[Align] 正在从本地加载wav2vec2对齐模型...", flush=True)
                align_model, metadata = whisperx.load_align_model(
                    language_code="zh",
                    model_name=LOCAL_WAV2VEC2_PATH,
                    device="cpu"
                )
                _align_models[LOCAL_WAV2VEC2_PATH] = (align_model, metadata)
                print("[Align] 对齐模型加载完成", flush=True)

            _model_loaded = True
            print("[Align] 所有模型预热完成", flush=True)
    except Exception as e:
        print(f"[Align] 预热失败: {e}", flush=True)
        _model_loaded = False


def is_model_ready() -> bool:
    """检查模型是否已加载完成"""
    return _model_loaded


def align_audio(audio_bytes: bytes, text: str, language: str = None) -> list:
    """
    使用 WhisperX 对 TTS 合成音频进行强制对齐，返回逐字时间戳。

    两步流程：
      1. faster-whisper transcribe：获取语音段（关闭 VAD，避免时间偏移）
      2. whisperx align：用 wav2vec2 模型做强制对齐，精细化到逐字级别

    Args:
        audio_bytes: 音频字节数据（WAV/MP3 均可）
        text: 原始文本（作为 initial_prompt 提升 ASR 识别准确度）
        language: 语言代码（如 "en"、"zh"），为 None 时默认 "zh"

    Returns:
        list of dict: [{"word": "你", "start": 0.12, "end": 0.35}, ...]
    """
    global _whisper_model, _align_models
    print("[Align] ========== 开始强制对齐 ==========", flush=True)
    print(f"[Align] 文本长度: {len(text)} 字符", flush=True)
    print(f"[Align] 音频大小: {len(audio_bytes)} 字节", flush=True)

    # 检测音频格式
    if audio_bytes[:3] == b"ID3" or (len(audio_bytes) > 4 and audio_bytes[:4].startswith(b"\xff\xfb")):
        suffix = ".mp3"
    else:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        audio_path = f.name
    print(f"[Align] 临时文件: {audio_path}", flush=True)

    try:
        from faster_whisper import WhisperModel
        import whisperx

        # ===== 确保 Whisper 模型已加载 =====
        if _whisper_model is None:
            warmup()
            if _whisper_model is None:
                raise RuntimeError("Whisper 模型加载失败")

        model = _whisper_model

        # ===== 第1步：ASR 转写 =====
        print(f"[Align] 第1步: ASR 转写，语言={language}", flush=True)

        # Windows + int8 可能死锁，设置单线程
        old_threads = os.environ.get("OMP_NUM_THREADS")
        os.environ["OMP_NUM_THREADS"] = "1"

        try:
            transcribe_kwargs = {
                "word_timestamps": True,
                "vad_filter": False,       # 关闭 VAD，避免时间偏移
                "suppress_blank": False,   # 不压制开头空白
            }

            transcribe_kwargs["language"] = language
            if text:
                transcribe_kwargs["initial_prompt"] = text  # 用原始文本提示 ASR，提升准确度

            segments, info = model.transcribe(audio_path, **transcribe_kwargs)
        finally:
            if old_threads is not None:
                os.environ["OMP_NUM_THREADS"] = old_threads
            else:
                os.environ.pop("OMP_NUM_THREADS", None)

        # 将 faster-whisper Segment 对象转为 whisperx 需要的 dict 格式
        result_segments = []
        for seg in segments:
            seg_dict = {
                "text": seg.text,
                "start": float(seg.start),
                "end": float(seg.end),
                "words": []
            }
            if seg.words:
                for w in seg.words:
                    seg_dict["words"].append({
                        "word": w.word.strip(),
                        "start": float(w.start),
                        "end": float(w.end),
                        "score": float(w.probability) if w.probability else 0.0
                    })
            result_segments.append(seg_dict)

        if not result_segments:
            raise ValueError("faster-whisper 转写未返回任何语音段")

        total_words = sum(len(s["words"]) for s in result_segments)
        print(f"[Align] 转写完成: {len(result_segments)} 个语音段, {total_words} 个词", flush=True)

        # ===== 第2步：确保对齐模型已加载 =====
        with _loading_lock:
            if LOCAL_WAV2VEC2_PATH not in _align_models:
                print("[Align] 正在从本地加载对齐模型...", flush=True)
                am, meta = whisperx.load_align_model(
                    language_code="zh",
                    model_name=LOCAL_WAV2VEC2_PATH,
                    device="cpu"
                )
                _align_models[LOCAL_WAV2VEC2_PATH] = (am, meta)
                print("[Align] 对齐模型加载完成", flush=True)

        align_model, metadata = _align_models[LOCAL_WAV2VEC2_PATH]

        # ===== 第3步：WhisperX 强制对齐 =====
        print("[Align] 第3步: WhisperX 强制对齐（wav2vec2）...", flush=True)

        result = whisperx.align(
            result_segments,
            align_model,
            metadata,
            audio_path,
            "cpu",
            return_char_alignments=True   # 返回逐字级别时间戳
        )

        # ===== 第4步：提取时间戳 =====
        word_timestamps = []
        has_char_alignments = False

        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                if "chars" in w and w["chars"]:
                    has_char_alignments = True
                    for c in w["chars"]:
                        char_text = c.get("char", "").strip()
                        start = c.get("start")
                        end = c.get("end")
                        if char_text and start is not None and end is not None:
                            word_timestamps.append({
                                "word": char_text,
                                "start": round(float(start), 3),
                                "end": round(float(end), 3)
                            })
                else:
                    word_text = w.get("word", "").strip()
                    start = w.get("start")
                    end = w.get("end")
                    if word_text and start is not None and end is not None:
                        word_timestamps.append({
                            "word": word_text,
                            "start": round(float(start), 3),
                            "end": round(float(end), 3)
                        })

        align_type = "逐字" if has_char_alignments else "逐词"
        print(f"[Align] 提取到 {len(word_timestamps)} 个{align_type}时间戳", flush=True)

        if len(word_timestamps) == 0:
            raise ValueError("WhisperX 强制对齐未返回任何时间戳")

        print("[Align] ========== 强制对齐完成 ==========", flush=True)
        return word_timestamps

    except Exception as e:
        print(f"[Align] 强制对齐失败: {e}", flush=True)
        raise

    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)
            print("[Align] 临时文件已删除", flush=True)
