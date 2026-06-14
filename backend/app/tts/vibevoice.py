import os
import asyncio
import json
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor
from .base import BaseTTSEngine

CONDA_BASE = r"E:\miniconda3"
PYTHON_PATH = os.path.join(CONDA_BASE, "envs", "vibevoice310", "python.exe")

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "vibevoice_worker.py"
)
SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)

_executor = ThreadPoolExecutor(max_workers=2)


class VibeVoiceEngine(BaseTTSEngine):
    def __init__(self):
        super().__init__()

    def get_voices(self) -> list:
        return ["en-Mike_man", "en-Emma_woman", "en-Carter_man", "en-Davis_man", "en-Frank_man", "en-Grace_woman"]

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
        VibeVoice 合成
        """
        try:
            voice_param = voice if voice else "en-Mike_man"
            print(f"[VibeVoice] 使用预设音色: {voice_param}")

            def _sync_synthesize():
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    output_path = tmp.name

                # 构建命令 - 只传必要参数，不传情感参数
                cmd = [
                    PYTHON_PATH,
                    SCRIPT_PATH,
                    "--text", text,
                    "--voice", voice_param,
                    "--output", output_path
                ]

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

                raise Exception(f"VibeVoice 合成失败: {result.stderr}")

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(_executor, _sync_synthesize)

        finally:
            pass