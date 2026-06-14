import os
import asyncio
import json
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from .base import BaseTTSEngine
from ..tts.emotion_adapter import EmotionAdapter

INDEXTTS_PATH = r"D:\Git\uv_work\index-tts"
DEFAULT_VOICE_FILE = r"D:\Python\Project\tts_test_output\vibevoice_output.wav"
GIT_BASH_PATH = r"D:\Git\Git\bin\bash.exe"

_executor = ThreadPoolExecutor(max_workers=1)


class IndexTTS2Engine(BaseTTSEngine):
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
            emotion_intensity: float = 0.5
    ) -> bytes:
        """
        IndexTTS2 合成

        Args:
            text: 要合成的文本
            voice: 音色参数（保留兼容）
            reference_audio: 参考音频数据（bytes），如果有则用，否则用默认
            emotion: 情感标签
            emotion_intensity: 情感强度
        """
        # 决定使用哪个参考音频
        voice_file_path = None
        temp_voice_path = None

        # ========== 情感参数处理 ==========
        emo_vector = [0, 0, 0, 0, 0, 0, 0, 0.8]  # 默认 calm
        emo_alpha = emotion_intensity if emotion else 0

        if emotion:
            emo_params = EmotionAdapter.convert("indextts", emotion, emotion_intensity)
            emo_vector = emo_params.get("emo_vector", emo_vector)
            emo_alpha = emo_params.get("emo_alpha", emo_alpha)
            print(f"IndexTTS2 情感参数: emotion={emotion}, intensity={emotion_intensity}")
            print(f"IndexTTS2 emo_vector={emo_vector}, emo_alpha={emo_alpha}")
        # =================================

        try:
            if reference_audio:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(reference_audio)
                    temp_voice_path = tmp.name
                voice_file_path = temp_voice_path
                print(f"使用用户上传的参考音频，长度: {len(reference_audio)} bytes")
            else:
                voice_file_path = DEFAULT_VOICE_FILE

            if not os.path.exists(voice_file_path):
                raise FileNotFoundError(f"参考音频不存在: {voice_file_path}")

            def _sync_synthesize():
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    output_path = tmp.name

                # 将 emo_vector 和 emo_alpha 的值直接写入 Python 代码
                emo_vector_str = str(emo_vector)
                emo_alpha_str = str(emo_alpha)

                # 构建 Python 代码，包含情感参数（直接嵌入数值）
                python_code = f'''
import sys
sys.path.insert(0, r"{INDEXTTS_PATH}")

from indextts.infer_v2 import IndexTTS2

tts = IndexTTS2(
    cfg_path=r"{INDEXTTS_PATH}/checkpoints/config.yaml",
    model_dir=r"{INDEXTTS_PATH}/checkpoints",
    use_fp16=False,
    use_cuda_kernel=False,
    use_deepspeed=False
)

# 情感参数（直接嵌入数值）
emo_vector = {emo_vector_str}
emo_alpha = {emo_alpha_str}

tts.infer(
    spk_audio_prompt=r"{voice_file_path}",
    text=\"\"\"{text}\"\"\",
    output_path=r"{output_path}",
    verbose=False,
    emo_vector=emo_vector,
    emo_alpha=emo_alpha
)
'''
                # 转义单引号
                python_code_escaped = python_code.replace("'", "'\\''")

                cmd = [
                    GIT_BASH_PATH,
                    "-c",
                    f"cd '{INDEXTTS_PATH}' && uv run python -c '{python_code_escaped}'"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=None
                )

                if result.returncode != 0:
                    raise Exception(f"IndexTTS2 失败: {result.stderr}")

                if not os.path.exists(output_path):
                    raise Exception("输出文件未生成")

                with open(output_path, "rb") as f:
                    audio_data = f.read()

                os.unlink(output_path)
                return audio_data

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(_executor, _sync_synthesize)

        finally:
            if temp_voice_path and os.path.exists(temp_voice_path):
                try:
                    os.unlink(temp_voice_path)
                except Exception:
                    pass