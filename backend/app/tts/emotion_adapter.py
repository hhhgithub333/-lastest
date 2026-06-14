"""
统一情感适配器
功能：将情感标签转换为各模型的具体参数
"""

from typing import Dict
from ..config.model_emotion_config import (
    COSYVOICE_CONFIG,
    INDEXTTS2_CONFIG,
    VOXCPM_CONFIG,
    SAMBERT_CONFIG,
    VIBEVOICE_CONFIG,
    QWEN_CONFIG,
    CHATTERBOX_CONFIG,
    XTTS_CONFIG,
    MODEL_CAPABILITIES
)


class EmotionAdapter:
    """
    统一情感适配器
    将统一情感标签转换为各模型的具体参数
    """

    @staticmethod
    def convert(engine: str, emotion: str, intensity: float = 0.5) -> Dict:
        """
        转换情感为模型参数

        Args:
            engine: 模型名称 (cosyvoice, indextts, voxcpm, sambert, vibevoice, qwen, chatterbox, xtts_v2)
            emotion: 情感标签 (happy, sad, angry, fear, surprised, disgusted, depressed, calm)
            intensity: 情感强度 0.0-1.0

        Returns:
            模型特定的参数字典
        """
        # 确保强度在有效范围内
        intensity = max(0.0, min(1.0, intensity))

        method = MODEL_CAPABILITIES.get(engine, {}).get("method")

        if method == "instruction":
            return EmotionAdapter._to_cosyvoice(emotion, intensity)
        elif method == "vector":
            return EmotionAdapter._to_indextts(emotion, intensity)
        elif method == "valence_arousal":
            return EmotionAdapter._to_voxcpm(emotion, intensity)
        elif method == "emotion_param":
            return EmotionAdapter._to_sambert(emotion, intensity)
        elif method == "inline_tag":
            return EmotionAdapter._to_vibevoice(emotion, intensity)
        elif method == "parameter":
            return EmotionAdapter._to_chatterbox(emotion, intensity)
        elif method == "reference_audio":
            return EmotionAdapter._to_xtts(emotion, intensity)

        # Qwen 也使用 instruction 方式
        if engine == "qwen":
            return EmotionAdapter._to_qwen(emotion, intensity)

        return {}

    @staticmethod
    def _to_cosyvoice(emotion: str, intensity: float) -> Dict:
        """转换为 CosyVoice 参数"""
        # 情感值映射（使用官方支持的英文情感值）
        emotion_map = {
            "happy": "happy",
            "sad": "sad",
            "angry": "angry",
            "fear": "fearful",
            "surprised": "surprised",
            "disgusted": "disgusted",
            "depressed": "sad",
            "calm": "neutral"
        }

        emotion_cn = emotion_map.get(emotion, "neutral")

        # ✅ 关键：必须使用官方固定格式（结尾一定要有句号）
        # 格式：你说话的情感是<情感值>。
        instructions = f"你说话的情感是{emotion_cn}。"

        # 语速调整
        rate_map = {
            "happy": 1.15,
            "sad": 0.85,
            "angry": 1.05,
            "fear": 1.05,
            "surprised": 1.10,
            "disgusted": 0.95,
            "depressed": 0.80,
            "calm": 1.0
        }
        base_rate = rate_map.get(emotion, 1.0)
        rate = base_rate * (0.8 + intensity * 0.4)
        rate = max(0.5, min(2.0, rate))

        return {
            "instruction": instructions,
            "rate": rate
        }

    @staticmethod
    def _to_indextts(emotion: str, intensity: float) -> Dict:
        """转换为 IndexTTS2 参数"""
        vector = INDEXTTS2_CONFIG["vectors"].get(emotion, INDEXTTS2_CONFIG["vectors"]["calm"])

        # 根据强度缩放向量
        scaled_vector = [v * intensity for v in vector]
        # 归一化
        total = sum(scaled_vector)
        if total > 0:
            scaled_vector = [v / total for v in scaled_vector]

        return {
            "emo_vector": scaled_vector,
            "emo_alpha": intensity
        }

    @staticmethod
    def _to_voxcpm(emotion: str, intensity: float) -> Dict:
        """转换为 VoxCPM 参数"""
        # 从配置读取
        va = VOXCPM_CONFIG["emotion_to_valence_arousal"].get(emotion, {"valence": 0.0, "arousal": 0.1})
        valence = va["valence"] * intensity
        arousal = va["arousal"] * intensity

        # cfg_value：从配置文件读取范围
        cfg_min = VOXCPM_CONFIG["cfg_range"]["min"]
        cfg_max = VOXCPM_CONFIG["cfg_range"]["max"]
        # 可选：限制强度上限，避免 cfg 过高导致不稳定
        effective_intensity = min(intensity, 0.8)  # 最高 0.8 强度映射到 cfg
        cfg_value = cfg_min + (cfg_max - cfg_min) * effective_intensity

        # timesteps：从配置文件读取范围
        ts_min = VOXCPM_CONFIG["timesteps_range"]["min"]
        ts_max = VOXCPM_CONFIG["timesteps_range"]["max"]
        timesteps = int(ts_min + (ts_max - ts_min) * intensity)
        timesteps = max(ts_min, min(ts_max, timesteps))  # 边界保护

        return {
            "valence": valence,
            "arousal": arousal,
            "cfg_value": cfg_value,
            "inference_timesteps": timesteps
        }

    @staticmethod
    def _to_sambert(emotion: str, intensity: float) -> Dict:
        """转换为 Sambert 参数（支持情感强度）"""
        emotion_val = SAMBERT_CONFIG["emotion_map"].get(emotion, "neutral")

        emotion_weight = 1.2

        pitch_scale = SAMBERT_CONFIG.get("pitch_scale", {}).get(emotion, 1.0)
        speed_rate = SAMBERT_CONFIG.get("speed_rate", {}).get(emotion, 1.0)

        # 根据强度调整 pitch 和 speed
        pitch_scale = 1.0 + (pitch_scale - 1.0) * intensity
        speed_rate = 1.0 + (speed_rate - 1.0) * intensity

        return {
            "emotion": emotion_val,
            "emotion_weight": round(emotion_weight, 2),
            "pitch_scale": round(pitch_scale, 2),
            "speed_rate": round(speed_rate, 2)
        }
    @staticmethod
    def _to_vibevoice(emotion: str, intensity: float) -> Dict:
        # 获取情感标签（降级映射已在 config 中处理）
        tag = VIBEVOICE_CONFIG["emotion_tags"].get(emotion, "[neutral]")

        # 获取基础参数（如果 emotion 不在 params 中，使用 calm 作为默认）
        base_params = VIBEVOICE_CONFIG["params"].get(emotion)
        if base_params is None:
            # 降级情感使用映射目标的参数
            mapped_emotion = None
            for k, v in VIBEVOICE_CONFIG["emotion_tags"].items():
                if v == tag and k != emotion:
                    mapped_emotion = k
                    break
            base_params = VIBEVOICE_CONFIG["params"].get(mapped_emotion, VIBEVOICE_CONFIG["params"]["calm"])

        # 根据用户强度调整参数
        adjusted_params = {}
        for key, value in base_params.items():
            if isinstance(value, (int, float)):
                if key == "emotion_intensity":
                    # ✅ 修复：直接使用用户强度，不乘基准值
                    # 范围 0.1-1.0，但如果用户强度为0，至少保持0.1
                    adjusted_params[key] = max(0.1, min(1.0, intensity))
                elif key in ["pitch_shift", "intonation_scale", "speech_rate", "pause_duration"]:
                    # 根据强度线性插值
                    baseline = 0.0 if key == "pitch_shift" else 1.0
                    adjusted_params[key] = baseline + (value - baseline) * intensity
                    # 边界裁剪
                    if key == "pitch_shift":
                        adjusted_params[key] = max(-3.0, min(3.0, adjusted_params[key]))
                    elif key in ["intonation_scale", "speech_rate", "pause_duration"]:
                        adjusted_params[key] = max(0.5, min(2.0, adjusted_params[key]))
                else:
                    adjusted_params[key] = value
            else:
                adjusted_params[key] = value

        # ✅ 重要：VibeVoice 需要成对的情感标签
        # 返回时带上 tag_open 和 tag_close，让后端或调用方包裹文本
        tag_open = tag
        tag_close = tag.replace('[', '[/') if '[' in tag else f'[/{tag[1:]}'

        return {
            "emotion_tag": tag,
            "tag_open": tag_open,
            "tag_close": tag_close,
            **adjusted_params
        }

    @staticmethod
    def _to_qwen(emotion: str, intensity: float) -> Dict:
        """转换为 Qwen 参数（通过自然语言指令）"""
        emotion_cn = QWEN_CONFIG["emotion_map"].get(emotion, "平静")

        # 生成官方推荐格式的指令（用括号包裹）
        instruction = f"（{emotion_cn}）"
        return {"instructions": instruction}

    @staticmethod
    def _to_chatterbox(emotion: str, intensity: float) -> Dict:
        """转换为 ChatterBox 参数"""
        base_params = CHATTERBOX_CONFIG["params"].get(emotion, CHATTERBOX_CONFIG["params"]["calm"])

        # 根据强度调整
        return {
            "exaggeration": base_params["exaggeration"] * intensity,
            "cfg_weight": base_params["cfg_weight"] * (0.5 + intensity * 0.5),
            "temperature": base_params["temperature"]
        }

    @staticmethod
    def _to_xtts(emotion: str, intensity: float) -> Dict:
        """转换为 XTTS-v2 参数"""
        audio_file = XTTS_CONFIG["reference_audio_map"].get(emotion, "reference_calm.wav")
        return {"speaker_wav": audio_file}
