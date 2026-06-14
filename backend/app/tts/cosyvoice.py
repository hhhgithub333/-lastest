import os
import json
import uuid
import asyncio
import websockets
from .base import BaseTTSEngine
from ..tts.emotion_adapter import EmotionAdapter


class CosyVoiceEngine(BaseTTSEngine):
    """CosyVoice v3-plus 手写 WebSocket 实现"""

    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    def get_model_name(self) -> str:
        return "cosyvoice-v3-plus"

    def get_api_url(self) -> str:
        return "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

    def get_voices(self) -> list:
        return ["longanyang", "longanhuan"]

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
        if voice is None:
            voice = "longanhuan"

        # 情感指令
        instruction = None
        rate_value = 1.0
        if emotion:
            emotion_params = EmotionAdapter.convert("cosyvoice", emotion, emotion_intensity)
            instruction = emotion_params.get("instruction")
            rate_value = emotion_params.get("rate", 1.0)
            print(f"CosyVoice 情感指令: {instruction}, 语速: {rate_value}")

        task_id = str(uuid.uuid4())
        audio_chunks = []

        # 构建 WebSocket 消息 - 使用官方参数名
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": self.get_model_name(),
                "parameters": {
                    "text_type": "PlainText",
                    "voice": voice,
                    "format": "mp3",
                    "sample_rate": 22050,
                    "volume": 50,
                    "rate": rate_value,      # ✅ 官方参数名
                    "pitch": 1.0,            # ✅ 官方参数名
                    "enable_ssml": False
                },
                "input": {}  # 必须存在，不能省略
            }
        }
        if instruction:
            run_task["payload"]["parameters"]["instruction"] = instruction

        print(f"发送请求: {json.dumps(run_task, ensure_ascii=False)}")

        async with websockets.connect(
            self.get_api_url(),
            extra_headers={
                "Authorization": f"bearer {self.api_key}",
                "X-DashScope-DataInspection": "enable"
            }
        ) as ws:
            # 发送 run-task
            await ws.send(json.dumps(run_task))

            # 接收响应 - 等待 task-started
            response = await ws.recv()
            msg = json.loads(response)
            print(f"收到响应: {msg}")

            if msg.get("header", {}).get("event") == "task-failed":
                raise Exception(f"任务启动失败: {msg.get('header', {}).get('error_message', '未知错误')}")

            if msg.get("header", {}).get("event") != "task-started":
                raise Exception(f"未收到 task-started 事件")

            # 发送 continue-task（待合成文本）
            continue_task = {
                "header": {
                    "action": "continue-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "input": {"text": text}
                }
            }
            await ws.send(json.dumps(continue_task))

            # 发送 finish-task
            finish_task = {
                "header": {
                    "action": "finish-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {"input": {}}
            }
            await ws.send(json.dumps(finish_task))

            # 接收音频数据
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30)

                    if isinstance(message, bytes):
                        audio_chunks.append(message)
                        print(f"收到音频块，大小: {len(message)}")
                    else:
                        msg = json.loads(message)
                        event = msg.get("header", {}).get("event")

                        if event == "task-finished":
                            break
                        elif event == "task-failed":
                            error_msg = msg.get("header", {}).get("error_message", "未知错误")
                            raise Exception(f"合成失败: {error_msg}")

                except asyncio.TimeoutError:
                    print("接收超时")
                    break

        if not audio_chunks:
            raise Exception("未接收到音频数据")

        print(f"合成完成，总音频大小: {sum(len(c) for c in audio_chunks)} 字节")
        return b''.join(audio_chunks)