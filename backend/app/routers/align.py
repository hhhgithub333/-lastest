from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
import json, os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["Align"])

@router.get("/ping")
async def ping():
    return {"status": "ok"}

@router.post("/align")
async def align_audio(
    audio: UploadFile = File(..., description="TTS 合成出的音频文件"),
    text: str = Form(..., description="原始文本，用于强制对齐"),
    language: str = Form(default=None),
):
    """
    强制对齐接口：用 Whisper 对音频 + 文本做对齐，返回逐词时间戳。

    返回格式：
    {
        "timestamps": [
            {"word": "你好", "start": 0.12, "end": 0.48},
            ...
        ]
    }
    """
    try:
        logger.info("[Align] 收到对齐请求，文本长度=%d，音频大小=%s bytes", len(text), audio.size)

        # 读取音频字节
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="音频文件为空")


        # 调用 faster-whisper 对齐
        from ..tts.faster_whisper_aligner import align_audio as do_align
        word_timestamps = do_align(audio_bytes, text, language)

        logger.info("[Align] 对齐完成，返回 %d 个词时间戳", len(word_timestamps))

        save_dir = r"F:\音频数据集\wenjian"
        os.makedirs(save_dir, exist_ok=True)  # 确保目录存在

        # 生成文件名：使用时间戳（精确到秒）
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 可选：从原音频文件名提取一部分，避免重名（这里仅用时间戳）
        safe_filename = f"align_{timestamp_str}.json"
        save_path = os.path.join(save_dir, safe_filename)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump({
                "text": text,
                "language": language,
                "timestamps": word_timestamps
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"[Align] 时间戳已保存至: {save_path}")
        return JSONResponse(content={"timestamps": word_timestamps})

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="faster-whisper 未安装，请运行：pip install faster-whisper"
        )
    except Exception as e:
        import traceback
        logger.exception("[Align] 对齐失败: %s", e)
        raise HTTPException(status_code=500, detail=f"对齐失败: {e}\n{traceback.format_exc()}")

