from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
from ..tts import get_engine, get_engines_info
from ..utils.emotion_recognizer import get_emotion_recognizer
from ..tts.emotion_adapter import EmotionAdapter

router = APIRouter(prefix="/tts", tags=["TTS"])


@router.get("/engines")
async def get_engines():
    return get_engines_info()


@router.post("/synthesize")
async def synthesize(
        text: str = Form(...),
        voice: str = Form(...),
        engine: str = Form(...),
        reference_audio: Optional[UploadFile] = File(None),
        emotion: Optional[str] = Form(None),
        emotion_intensity: Optional[float] = Form(None),
        prompt_text: Optional[str] = Form(None)  # 新增
):
    """
    TTS 语音合成
    """
    try:
        print("\n" + "=" * 60)
        print(f"[TTS请求] engine={engine}, voice={voice}")
        print(f"[TTS请求] text={text[:100]}..." if len(text) > 100 else f"[TTS请求] text={text}")
        if prompt_text:
            print(f"[TTS请求] prompt_text={prompt_text[:50]}...")
        if reference_audio:
            print(f"[TTS请求] 参考音频: {reference_audio.filename}, 大小: {reference_audio.size} bytes")

        # ========== 情感识别 ==========
        if emotion is None:
            # 自动识别情感
            recognizer = get_emotion_recognizer()
            emotion_result = recognizer.analyze(text)
            detected_emotion = emotion_result["emotion"]
            detected_intensity = emotion_result["intensity"]
            confidence = emotion_result.get("confidence", 0.5)

            # 打印情感识别结果
            print("-" * 40)
            print("[情感识别] 输入文本:", text[:80] + "..." if len(text) > 80 else text)
            print(f"[情感识别] 识别结果: {detected_emotion} (强度: {detected_intensity:.2f}, 置信度: {confidence:.2f})")
            if "all_emotions" in emotion_result:
                print(f"[情感识别] 全部情感分布: {emotion_result['all_emotions']}")
        else:
            # 使用前端指定的情感
            detected_emotion = emotion
            detected_intensity = emotion_intensity if emotion_intensity is not None else 0.5
            print("-" * 40)
            print(f"[情感识别] 使用前端指定情感: {detected_emotion} (强度: {detected_intensity:.2f})")
        # =================================

        # ========== 获取引擎并转换情感参数 ==========
        tts_engine = get_engine(engine)

        # 打印各模型的情感参数转换结果
        if detected_emotion:
            emotion_params = EmotionAdapter.convert(engine, detected_emotion, detected_intensity)
            print(f"[情感适配] 引擎: {engine}")
            print(f"[情感适配] 转换后参数: {emotion_params}")
        # ===========================================

        # 读取参考音频数据
        reference_audio_data = None
        if reference_audio:
            reference_audio_data = await reference_audio.read()
            print(f"[参考音频] 已读取 {len(reference_audio_data)} bytes")

        # 调用引擎合成（根据引擎决定是否传递 prompt_text）
        print("-" * 40)
        print("[TTS合成] 开始调用引擎...")

        # 方案2：只有 voxcpm 传递 prompt_text
        if engine == "voxcpm" and prompt_text:
            audio_data = await tts_engine.synthesize(
                text=text,
                voice=voice,
                reference_audio=reference_audio_data,
                emotion=detected_emotion,
                emotion_intensity=detected_intensity,
                prompt_text=prompt_text
            )
        else:
            audio_data = await tts_engine.synthesize(
                text=text,
                voice=voice,
                reference_audio=reference_audio_data,
                emotion=detected_emotion,
                emotion_intensity=detected_intensity
            )

        print(f"[TTS合成] 合成成功，音频大小: {len(audio_data)} bytes")
        print("=" * 60 + "\n")

        audio_format = tts_engine.get_audio_format()
        media_type = "audio/mpeg" if audio_format == "mp3" else "audio/wav"

        return StreamingResponse(
            iter([audio_data]),
            media_type=media_type,
            headers={
                "X-Engine": engine,
                "X-Voice": voice,
                "X-Format": audio_format,
                "X-Emotion": detected_emotion,
                "X-Emotion-Intensity": str(detected_intensity)
            }
        )

    except ValueError as e:
        print(f"[错误] ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_full = traceback.format_exc()
        print(f"[错误] TTS 合成失败: {error_full}")
        raise HTTPException(status_code=500, detail=str(e) + "\n" + error_full)