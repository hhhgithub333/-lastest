from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)


class BaseTTSEngine(ABC):
    """TTS 引擎基类"""

    def __init__(self):
        """初始化，从环境变量读取 API Key"""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        reference_audio: bytes = None,
        emotion: str = None,
        emotion_intensity: float = 0.5
    ) -> bytes:
        """
        合成语音，返回音频数据

        Args:
            text: 要合成的文本
            voice: 音色代码（云端模型使用）
            reference_audio: 参考音频文件路径（本地克隆模型使用）
            emotion: 情感标签 (happy, sad, angry, fear, surprised, disgusted, depressed, calm)
            emotion_intensity: 情感强度 (0.0-1.0)

        Returns:
            bytes: 音频数据（MP3 或 WAV 格式）
        """
        pass

    @abstractmethod
    def get_voices(self) -> list:
        """获取该引擎支持的所有音色列表"""
        pass

    @abstractmethod
    def get_audio_format(self) -> str:
        """获取返回的音频格式"""
        return "mp3"