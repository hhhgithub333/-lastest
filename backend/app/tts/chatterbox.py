import os
import asyncio
import json
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor
from .base import BaseTTSEngine
from ..tts.emotion_adapter import EmotionAdapter

CONDA_BASE = r"E:\miniconda3"
PYTHON_PATH = os.path.join(CONDA_BASE, "envs", "chatterbox", "python.exe")

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "chatterbox_worker.py"
)
SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)

DEFAULT_REFERENCE_AUDIO = r"D:\Python\Project\tts_test_output\vibevoice.wav"

_executor = ThreadPoolExecutor(max_workers=2)


class ChatterBoxEngine(BaseTTSEngine):
    def __init__(self):
        super().__init__()

    def get_voices(self) -> list:
        return []

    def get_audio_format(self) -> str:
        return "mp3"

    async def synthesize(
            self,
            text: str,
            voice: str = None,
            reference_audio: bytes = None,
            emotion: str = None,
            emotion_intensity: float = 0.5
    ) -> bytes:
        """
        ChatterBox 合成

        优先级：
        1. 用户上传的 reference_audio
        2. emotion 参数对应的预设参考音频
        3. 默认参考音频 DEFAULT_REFERENCE_AUDIO

        Args:
            text: 要合成的文本
            voice: 音色参数（保留兼容）
            reference_audio: 参考音频数据（bytes）
            emotion: 情感标签
            emotion_intensity: 情感强度
        """

        def _sync_synthesize():
            reference_audio_path = None
            temp_voice_path = None

            try:
                # ========== 1. 决定参考音频（优先级） ==========
                if reference_audio:
                    # 优先级1：用户上传的参考音频
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(reference_audio)
                        temp_voice_path = tmp.name
                    reference_audio_path = temp_voice_path
                    print(f"✅ 使用用户上传的参考音频，长度: {len(reference_audio)} bytes")

                elif emotion:
                    # 优先级2：根据 emotion 选择预设参考音频（复用 XTTS_CONFIG）
                    from ..config.model_emotion_config import XTTS_CONFIG
                    preset_audio = XTTS_CONFIG["reference_audio_map"].get(emotion)

                    if preset_audio and os.path.exists(preset_audio):
                        reference_audio_path = preset_audio
                        print(f"✅ 使用情感预设参考音频: {preset_audio} (情感: {emotion}, 强度: {emotion_intensity})")
                    else:
                        print(f"⚠️ 情感预设参考音频不存在: {preset_audio}，使用默认")
                        reference_audio_path = DEFAULT_REFERENCE_AUDIO
                else:
                    # 优先级3：默认参考音频
                    reference_audio_path = DEFAULT_REFERENCE_AUDIO
                    print(f"⚠️ 没有参考音频和情感参数，使用默认: {DEFAULT_REFERENCE_AUDIO}")

                # 检查参考音频是否存在
                if not os.path.exists(reference_audio_path):
                    raise Exception(f"参考音频不存在: {reference_audio_path}")

                # ========== 2. 情感参数处理 ==========
                cb_params = {}
                if emotion:
                    cb_params = EmotionAdapter.convert("chatterbox", emotion, emotion_intensity)
                    print(f"ChatterBox 情感参数: {cb_params}")
                # =================================

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    output_path = tmp.name

                cmd = [
                    PYTHON_PATH,
                    SCRIPT_PATH,
                    "--text", text,
                    "--output", output_path,
                    "--voice_file", reference_audio_path
                ]

                # 添加情感参数
                if cb_params:
                    if "exaggeration" in cb_params:
                        cmd.extend(["--exaggeration", str(cb_params["exaggeration"])])
                        print(f"  - exaggeration: {cb_params['exaggeration']}")
                    if "cfg_weight" in cb_params:
                        cmd.extend(["--cfg_weight", str(cb_params["cfg_weight"])])
                        print(f"  - cfg_weight: {cb_params['cfg_weight']}")
                    if "temperature" in cb_params:
                        cmd.extend(["--temperature", str(cb_params["temperature"])])
                        print(f"  - temperature: {cb_params['temperature']}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                try:
                    for line in result.stdout.split("\n"):
                        if line.strip().startswith("{"):
                            res = json.loads(line)
                            if res.get("success"):
                                with open(output_path, "rb") as f:
                                    audio_data = f.read()
                                os.unlink(output_path)
                                return audio_data
                            else:
                                raise Exception(res.get("error", "未知错误"))
                except json.JSONDecodeError:
                    pass

                if os.path.exists(output_path):
                    os.unlink(output_path)

                raise Exception(f"ChatterBox 合成失败: {result.stderr}")

            finally:
                # 只删除临时文件，不删除预设音频
                if temp_voice_path and os.path.exists(temp_voice_path):
                    try:
                        os.unlink(temp_voice_path)
                    except:
                        pass

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _sync_synthesize)