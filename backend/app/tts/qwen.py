from .base import BaseTTSEngine
import httpx
import base64
from ..tts.emotion_adapter import EmotionAdapter


class QwenTTSEngine(BaseTTSEngine):

    async def synthesize(
            self,
            text: str,
            voice: str,
            reference_audio: bytes = None,
            emotion: str = None,
            emotion_intensity: float = 0.5
    ) -> bytes:
        """千问 TTS，云端 API"""

        # ========== 情感参数处理 ==========
        instruct = None
        final_text = text
        if emotion:
            qwen_params = EmotionAdapter.convert("qwen", emotion, emotion_intensity)
            instruct = qwen_params.get("instructions")
            if instruct:
                print(f"Qwen 情感指令: {instruct}")
        # =================================

        async with httpx.AsyncClient() as client:
            # 构建参数
            parameters = {
                "voice": voice,
                "language_type": "auto"
            }

            # 如果有情感指令，添加到 parameters 中
            if instruct:
                parameters["instructions"] = instruct  # ← 关键：独立参数，不拼接到文本
                parameters["optimize_instructions"] = True

            payload = {
                "model": "qwen3-tts-instruct-flash",
                "input": {"text": final_text},  # ← 文本保持原样
                "parameters": parameters
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                json=payload,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"千问 TTS API 错误: {response.text}")

            result = response.json()
            audio_url = result.get("output", {}).get("audio", {}).get("url")

            if not audio_url:
                audio_data = result.get("output", {}).get("audio", {}).get("data")
                if audio_data:
                    return base64.b64decode(audio_data)
                raise Exception("未获取到音频")

            audio_response = await client.get(audio_url)
            return audio_response.content

    def get_voices(self) -> list:
        return ["Cherry", "Stella", "James", "Bella", "Alex", "Emma", "Liam", "Mia", "Noah", "Olivia"]

    def get_audio_format(self) -> str:
        return "mp3"