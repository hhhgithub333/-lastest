from .qwen import QwenTTSEngine
from .cosyvoice import CosyVoiceEngine
from .sambert import SambertEngine
from .xtts_v2 import XTTSv2Engine
from .voxcpm import VoxCPMEngine
from .chatterbox import ChatterBoxEngine
from .vibevoice import VibeVoiceEngine
from .indextts import IndexTTS2Engine



# 引擎实例（延迟初始化，避免启动时加载所有模型）
_engines = None


def _get_engines():
    """获取所有引擎实例（延迟初始化）"""
    global _engines
    if _engines is None:
        _engines = {
            "qwen": QwenTTSEngine(),
            "cosyvoice": CosyVoiceEngine(),
            "sambert": SambertEngine(),
            "xtts_v2": XTTSv2Engine(),
            "voxcpm": VoxCPMEngine(),
            "chatterbox": ChatterBoxEngine(),
            "vibevoice": VibeVoiceEngine(),
            "indextts": IndexTTS2Engine()
        }
    return _engines


def get_engine(engine_name: str):
    """获取指定引擎实例"""
    engines = _get_engines()
    if engine_name not in engines:
        raise ValueError(f"不支持的引擎: {engine_name}")
    return engines[engine_name]


def get_engines_info():
    """获取所有引擎信息"""
    engines = _get_engines()
    return {
        name: {
            "name": name,
            "voices": engine.get_voices(),
            "audio_format": engine.get_audio_format()
        }
        for name, engine in engines.items()
    }