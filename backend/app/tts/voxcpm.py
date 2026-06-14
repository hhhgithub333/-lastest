import os
import asyncio
import json
import tempfile
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from .base import BaseTTSEngine
from ..tts.emotion_adapter import EmotionAdapter

CONDA_BASE = r"E:\miniconda3"
PYTHON_PATH = os.path.join(CONDA_BASE, "envs", "VoxCPM", "python.exe")
SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "voxcpm_worker.py"
)
SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)

# 默认参考音频（当用户不上传且没有 emotion 时使用）
DEFAULT_REFERENCE_AUDIO = r"D:\Python\Project\tts_test_output\reference_calm.wav"

_executor = ThreadPoolExecutor(max_workers=2)


class VoxCPMEngine(BaseTTSEngine):
    def __init__(self):
        super().__init__()

    def get_voices(self) -> list:
        return []

    def get_audio_format(self) -> str:
        return "wav"

    async def synthesize(
            self,
            text: str,
            voice: str = None,
            reference_audio: bytes = None,
            emotion: str = None,
            emotion_intensity: float = 0.5,
            prompt_text: str = None
    ) -> bytes:
        """
        VoxCPM 合成

        优先级：
        1. 用户上传的 reference_audio
        2. emotion 参数对应的预设参考音频
        3. 默认参考音频 DEFAULT_REFERENCE_AUDIO
        """
        temp_voice_path = None
        ref_audio_path = None

        # ========== 1. 决定参考音频（优先级） ==========
        if reference_audio:
            # 优先级1：用户上传的参考音频
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(reference_audio)
                temp_voice_path = tmp.name
            ref_audio_path = temp_voice_path
            print(f"✅ 使用用户上传的参考音频，长度: {len(reference_audio)} bytes")

        elif emotion:
            # 优先级2：根据 emotion 选择预设参考音频（复用 XTTS_CONFIG）
            from ..config.model_emotion_config import XTTS_CONFIG
            preset_audio = XTTS_CONFIG["reference_audio_map"].get(emotion)

            if preset_audio and os.path.exists(preset_audio):
                ref_audio_path = preset_audio
                print(f"✅ 使用情感预设参考音频: {preset_audio} (情感: {emotion}, 强度: {emotion_intensity})")
            else:
                print(f"⚠️ 情感预设参考音频不存在: {preset_audio}，使用默认")
                ref_audio_path = DEFAULT_REFERENCE_AUDIO
        else:
            # 优先级3：默认参考音频
            ref_audio_path = DEFAULT_REFERENCE_AUDIO
            print(f"⚠️ 没有参考音频和情感参数，使用默认: {DEFAULT_REFERENCE_AUDIO}")

        # 检查参考音频是否存在
        if not os.path.exists(ref_audio_path):
            raise ValueError(f"参考音频不存在: {ref_audio_path}")

        # ========== 2. 情感参数处理 ==========
        voxcpm_params = {}
        if emotion:
            voxcpm_params = EmotionAdapter.convert("voxcpm", emotion, emotion_intensity)
            print(f"VoxCPM 情感参数: {voxcpm_params}")
        # =================================

        try:
            if prompt_text:
                print(f"参考音频对应文本: {prompt_text[:50]}...")

            # ========== 3. 重试逻辑 ==========
            MAX_RETRIES = 1  # 最大重试次数（总共尝试 3 次）

            def _sync_synthesize_with_retry():
                last_error = None
                for attempt in range(MAX_RETRIES):
                    try:
                        print(f"尝试 {attempt + 1}/{MAX_RETRIES + 1}...")
                        return self._do_synthesize(
                            text, ref_audio_path, prompt_text,
                            emotion, emotion_intensity, voxcpm_params
                        )
                    except Exception as e:
                        last_error = e
                        if attempt < MAX_RETRIES:
                            print(f"合成失败 (attempt {attempt + 1})，重试中... 错误: {e}")
                            time.sleep(1)  # 等待1秒后重试
                        else:
                            print(f"合成失败，已达最大重试次数 {MAX_RETRIES + 1}")
                            raise last_error
                raise last_error

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(_executor, _sync_synthesize_with_retry)

        finally:
            # 只删除临时文件，不删除预设音频
            if temp_voice_path and os.path.exists(temp_voice_path):
                try:
                    os.unlink(temp_voice_path)
                except Exception:
                    pass

    def _do_synthesize(
            self,
            text: str,
            ref_audio_path: str,
            prompt_text: str,
            emotion: str,
            emotion_intensity: float,
            voxcpm_params: dict
    ) -> bytes:
        """实际的合成逻辑，抽出来方便重试"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        cmd = [
            PYTHON_PATH,
            SCRIPT_PATH,
            "--text", text,
            "--voice_file", ref_audio_path,
            "--output", output_path
        ]

        # 添加 prompt_text 参数
        if prompt_text:
            cmd.extend(["--prompt_text", prompt_text])

        # 添加情感参数
        if voxcpm_params:
            cmd.extend(["--emotion", emotion])
            cmd.extend(["--emotion_intensity", str(emotion_intensity)])

            if "cfg_value" in voxcpm_params:
                cmd.extend(["--cfg_value", str(voxcpm_params["cfg_value"])])
            if "inference_timesteps" in voxcpm_params:
                cmd.extend(["--timesteps", str(voxcpm_params["inference_timesteps"])])

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

        raise Exception(f"VoxCPM 合成失败: {result.stderr}")