from .base import BaseTTSEngine
import json
import websockets
import asyncio
import uuid
from ..tts.emotion_adapter import EmotionAdapter


class SambertEngine(BaseTTSEngine):

    def _get_model_by_voice(self, voice: str) -> str:
        model_map = {
            "zhinan": "sambert-zhinan-v1",
            "zhiqi": "sambert-zhiqi-v1",
            "zhichu": "sambert-zhichu-v1",
            "zhide": "sambert-zhide-v1",
            "zhijia": "sambert-zhijia-v1",
            "zhiru": "sambert-zhiru-v1",
            "zhiqian": "sambert-zhiqian-v1",
            "zhixiang": "sambert-zhixiang-v1",
            "zhiwei": "sambert-zhiwei-v1",
            "zhihao": "sambert-zhihao-v1",
            "zhijing": "sambert-zhijing-v1",
            "zhiming": "sambert-zhiming-v1",
            "zhimo": "sambert-zhimo-v1",
            "zhina": "sambert-zhina-v1",
            "zhishu": "sambert-zhishu-v1",
            "zhistella": "sambert-zhistella-v1",
            "zhiting": "sambert-zhiting-v1",
            "zhixiao": "sambert-zhixiao-v1",
            "zhiya": "sambert-zhiya-v1",
            "zhiye": "sambert-zhiye-v1",
            "zhiying": "sambert-zhiying-v1",
            "zhiyuan": "sambert-zhiyuan-v1",
            "zhiyue": "sambert-zhiyue-v1",
            "zhigui": "sambert-zhigui-v1",
            "zhishuo": "sambert-zhishuo-v1",
            "zhimiao-emo": "sambert-zhimiao-emo-v1",
            "zhimao": "sambert-zhimao-v1"
        }
        return model_map.get(voice, "sambert-zhichu-v1")

    def _get_sample_rate(self, voice: str) -> int:
        high_rate_voices = [
            "zhimao", "zhinan", "zhiqi", "zhichu", "zhide", "zhijia",
            "zhiru", "zhiqian", "zhixiang", "zhiwei", "zhihao",
            "zhijing", "zhiming", "zhimo", "zhina", "zhishu",
            "zhistella", "zhiting", "zhixiao", "zhiya", "zhiye",
            "zhiying", "zhiyuan", "zhiyue", "zhigui", "zhishuo",
            "zhimiao-emo"
        ]
        return 48000 if voice in high_rate_voices else 16000

    async def synthesize(
            self,
            text: str,
            voice: str,
            reference_audio: bytes = None,
            emotion: str = None,
            emotion_intensity: float = 0.5
    ) -> bytes:
        """Sambert TTS，云端 API"""

        # ========== 情感参数处理 ==========
        sambert_emotion = None
        sambert_emotion_weight = None
        sambert_pitch_scale = None
        sambert_speed_rate = None

        if emotion:
            emotion_params = EmotionAdapter.convert("sambert", emotion, emotion_intensity)
            sambert_emotion = emotion_params.get("emotion")
            sambert_emotion_weight = emotion_params.get("emotion_weight")
            sambert_pitch_scale = emotion_params.get("pitch_scale")
            sambert_speed_rate = emotion_params.get("speed_rate")

        print(f"Sambert 情感参数: emotion={sambert_emotion}, weight={sambert_emotion_weight}, "
              f"pitch_scale={sambert_pitch_scale}, speed_rate={sambert_speed_rate}")
        # =================================

        task_id = str(uuid.uuid4())
        model = self._get_model_by_voice(voice)
        sample_rate = self._get_sample_rate(voice)

        parameters = {
            "text_type": "PlainText",
            "voice": voice,
            "format": "wav",
            "sample_rate": sample_rate,
            "volume": 50,
            "rate": 1,
            "pitch": 1
        }

        # ✅ 通过参数传递情感，不在 text 中加标签
        if sambert_emotion:
            parameters["emotion"] = sambert_emotion
        if sambert_emotion_weight:
            parameters["emotion_weight"] = sambert_emotion_weight
        if sambert_pitch_scale:
            parameters["pitch_scale"] = sambert_pitch_scale
        if sambert_speed_rate:
            parameters["speed_rate"] = sambert_speed_rate

        # ✅ 使用原始文本，不加任何标签
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "out"
            },
            "payload": {
                "model": model,
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "input": {"text": text},  # 原始文本
                "parameters": parameters
            }
        }

        audio_data = bytearray()

        async with websockets.connect(
                "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
                extra_headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-DashScope-DataInspection": "enable"
                }
        ) as ws:
            await ws.send(json.dumps(run_task))

            while True:
                message = await ws.recv()

                if isinstance(message, bytes):
                    audio_data.extend(message)
                else:
                    msg = json.loads(message)
                    event = msg.get("header", {}).get("event")
                    if event == "task-finished":
                        break
                    elif event == "task-failed":
                        error = msg.get("header", {}).get("error_message", "未知错误")
                        raise Exception(f"Sambert 合成失败: {error}")

        return bytes(audio_data)

    def get_voices(self) -> list:
        return [
            "zhimao", "zhinan", "zhiqi", "zhichu", "zhide", "zhijia",
            "zhiru", "zhiqian", "zhixiang", "zhiwei", "zhihao",
            "zhijing", "zhiming", "zhimo", "zhina", "zhishu",
            "zhistella", "zhiting", "zhixiao", "zhiya", "zhiye",
            "zhiying", "zhiyuan", "zhiyue", "zhigui", "zhishuo",
            "zhimiao-emo"
        ]

    def get_audio_format(self) -> str:
        return "mp3"