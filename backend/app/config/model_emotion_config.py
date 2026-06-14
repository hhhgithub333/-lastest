"""
模型情感参数配置中心
统一情感标签: happy, sad, angry, fear, surprised, disgusted, depressed, calm
"""

# ========== 1. CosyVoice 配置 ==========
COSYVOICE_CONFIG = {
    "emotion_map": {
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "fear": "fearful",
        "surprised": "surprised",
        "disgusted": "disgusted",
        "depressed": "sad",      # 忧郁映射到悲伤
        "calm": "neutral"        # 平静映射到中性
    },
    "rate_adjustment": {
        "happy": 1.15,
        "sad": 0.85,
        "angry": 1.05,
        "fear": 1.05,
        "surprised": 1.10,
        "disgusted": 0.95,
        "depressed": 0.80,
        "calm": 1.0
    },
    "instruction_template": "你说话的情感是{emotion}。"
}

# ========== 2. IndexTTS2 配置 ==========
# 8维情感向量: [高兴,愤怒,悲伤,害怕,厌恶,忧郁,惊讶,平静]
INDEXTTS2_CONFIG = {
    "vector_indices": {
        "happy": 0,
        "angry": 1,
        "sad": 2,
        "fear": 3,
        "disgusted": 4,
        "depressed": 5,
        "surprised": 6,
        "calm": 7
    },
    "vectors": {
        "happy": [0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0],
        "sad": [0.0, 0.0, 0.8, 0.0, 0.0, 0.2, 0.0, 0.0],
        "angry": [0.0, 0.8, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0],
        "fear": [0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.2, 0.0],
        "surprised": [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 0.0],
        "disgusted": [0.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0],
        "depressed": [0.0, 0.0, 0.2, 0.0, 0.0, 0.8, 0.0, 0.0],
        "calm": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8]
    }
}

# ========== 3. VoxCPM 配置 ==========
# VoxCPM 通过 valence(效价) 和 arousal(唤醒度) 控制情感
# valence: -1(负面) 到 +1(正面), arousal: 0(平静) 到 1(激动)
VOXCPM_CONFIG = {
    "emotion_to_valence_arousal": {
        "happy": {"valence": 0.9, "arousal": 0.8},   # 提高
        "sad": {"valence": -0.8, "arousal": 0.3},    # 提高绝对值
        "angry": {"valence": -0.7, "arousal": 0.95},  # 提高唤醒度
        "fear": {"valence": -0.6, "arousal": 0.85},
        "surprised": {"valence": 0.4, "arousal": 0.8},
        "disgusted": {"valence": -0.5, "arousal": 0.5},
        "depressed": {"valence": -0.9, "arousal": 0.2},
        "calm": {"valence": 0.0, "arousal": 0.1}
    },
    # 官方文档提到的支配度
    "emotion_to_dominance": {
        "happy": 0.8,
        "sad": 0.2,
        "angry": 0.9,
        "fear": 0.2,
        "surprised": 0.6,
        "disgusted": 0.4,
        "depressed": 0.1,
        "calm": 0.5
    },
    "cfg_range": {"min": 1.5, "max": 1.8},
    "timesteps_range": {"min": 8, "max": 12},
    "max_retries": 1,
}

# ========== 4. Sambert 配置 ==========
# 官方支持: neutral, happy, sad, angry, fearful, surprised, tender
SAMBERT_CONFIG = {
    "emotion_map": {
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "fear": "fearful",
        "surprised": "surprised",
        "disgusted": "angry",      # 厌恶映射到愤怒
        "depressed": "sad",        # 忧郁映射到悲伤
        "calm": "neutral"
    },
    "pitch_scale": {
        "happy": 1.1,
        "sad": 0.95,
        "angry": 1.05,
        "fear": 1.0,
        "surprised": 1.15,
        "calm": 0.9
    },
    "speed_rate": {
        "happy": 1.1,
        "sad": 0.9,
        "angry": 1.05,
        "fear": 1.0,
        "surprised": 1.15,
        "calm": 0.95
    }
}

# ========== 5. VibeVoice 配置 ==========
# 支持情感标签: [happy], [sad], [angry], [neutral], [surprised]
# 同时支持语调参数调节
VIBEVOICE_CONFIG = {
    # 情感标签映射（官方支持的5种 + 降级映射）
    "emotion_tags": {
        "happy": "[happy]",
        "sad": "[sad]",
        "angry": "[angry]",
        "surprised": "[surprised]",
        "calm": "[neutral]",
        # 降级映射：官方不支持的标签映射到最接近的
        "fear": "[sad]",        # 恐惧 → 悲伤
        "disgusted": "[angry]",  # 厌恶 → 愤怒
        "depressed": "[sad]"     # 忧郁 → 悲伤
    },
    # 各情感的基础参数（官方推荐值）
    "params": {
        "happy": {
            "pitch_shift": 1.5,
            "intonation_scale": 1.6,
            "speech_rate": 1.1,
            "emotion_intensity": 0.7
        },
        "sad": {
            "pitch_shift": -1.0,
            "intonation_scale": 0.8,
            "speech_rate": 0.8,
            "pause_duration": 1.3,
            "emotion_intensity": 0.8
        },
        "angry": {
            "pitch_shift": 2.0,
            "intonation_scale": 1.8,
            "speech_rate": 1.2,
            "emotion_intensity": 0.9
        },
        "surprised": {
            "pitch_shift": 2.5,
            "intonation_scale": 2.0,
            "speech_rate": 1.15,
            "emotion_intensity": 0.8
        },
        "calm": {
            "pitch_shift": 0.0,
            "intonation_scale": 0.5,
            "speech_rate": 0.9,
            "emotion_intensity": 0.3
        },
        # 降级情感的参数（使用映射目标的参数）
        "fear": {
            "pitch_shift": -0.5,
            "intonation_scale": 1.4,
            "speech_rate": 0.85,
            "pause_duration": 1.2,
            "emotion_intensity": 0.7
        },
        "disgusted": {
            "pitch_shift": -0.8,
            "intonation_scale": 1.3,
            "speech_rate": 0.9,
            "emotion_intensity": 0.6
        },
        "depressed": {
            "pitch_shift": -1.5,
            "intonation_scale": 0.6,
            "speech_rate": 0.7,
            "pause_duration": 1.5,
            "emotion_intensity": 0.7
        }
    }
}

# ========== 6. Qwen 配置 ==========
# CustomVoice 模式支持自然语言指令
QWEN_CONFIG = {
    "emotion_map": {
        "happy": "忍不住笑出声地",  # 高兴
        "sad": "声音微微发颤地",    # 难过
        "angry": "带着压抑怒火地",   # 愤怒
        "fear": "声音颤抖带着恐惧地", # 恐惧
        "surprised": "猛地吸一口气后", # 惊讶
        "disgusted": "带着厌恶地",     # 厌恶
        "depressed": "有气无力地",     # 忧郁
        "calm": "语气平稳地"           # 平静
    },
}

# ========== 7. ChatterBox 配置 ==========
# 三维情绪参数空间: exaggeration(夸张度), cfg_weight(语速/节奏), temperature(随机性)
CHATTERBOX_CONFIG = {
    "params": {
        "happy": {"exaggeration": 0.8, "cfg_weight": 0.6, "temperature": 0.8},
        "sad": {"exaggeration": 0.4, "cfg_weight": 0.4, "temperature": 0.6},
        "angry": {"exaggeration": 0.9, "cfg_weight": 0.7, "temperature": 0.7},
        "fear": {"exaggeration": 0.7, "cfg_weight": 0.5, "temperature": 0.65},
        "surprised": {"exaggeration": 0.85, "cfg_weight": 0.55, "temperature": 0.85},
        "disgusted": {"exaggeration": 0.75, "cfg_weight": 0.45, "temperature": 0.7},
        "depressed": {"exaggeration": 0.25, "cfg_weight": 0.35, "temperature": 0.55},
        "calm": {"exaggeration": 0.3, "cfg_weight": 0.5, "temperature": 0.5}
    }
}

# ========== 8. XTTS-v2 配置 ==========
# 通过情感参考音频实现情感控制
XTTS_CONFIG = {
    "reference_audio_map": {
        "happy": "D:/Python/Project/tts_test_output/reference_happy.wav",
        "sad": "D:/Python/Project/tts_test_output/reference_sad.wav",
        "angry": "D:/Python/Project/tts_test_output/reference_angry.wav",
        "fear": "D:/Python/Project/tts_test_output/reference_fear.wav",
        "surprised": "D:/Python/Project/tts_test_output/reference_surprised.wav",
        "disgusted": "D:/Python/Project/tts_test_output/reference_disgusted.wav",
        "depressed": "D:/Python/Project/tts_test_output/reference_depressed.wav",
        "calm": "D:/Python/Project/tts_test_output/reference_calm.wav"
    },
    "reference_text_map": {
        "happy": "I can confidently declare that this is the most exquisite chocolate cake my taste buds have ever had the pleasure to encounter! Mo proclaimed, savoring every bite. He could not stop eating!",
        "sad": "I miss Grandma so much. She's gone forever and I feel so sad.",
        "angry": "Life is so unfair and frustrating! Every stupid challenge just makes me angrier. I'm sick of this ridiculous nonsense!",
        "fear": "Jane's eyes wide with terror, she screamed, The brakes aren't working! What do we do now? We're completely trapped, and we're heading straight for that wall, I can't stop it!",
        "surprised": "What? He got into Harvard? That's absolutely incredible! I can't believe my ears! He was never the top student in our class, and now this",
        "disgusted": "This food tastes absolutely disgusting. I feel sick just looking at it. What on earth did they put in this?",
        "depressed": "I don't know. Life just feels so boring and meaningless lately.",
        "calm": "Dyslexia is a common learning difficulty that affects reading and spelling. However, with proper training and support, many people with dyslexia can overcome these challenges."
    }
}

# ========== 模型能力声明 ==========
MODEL_CAPABILITIES = {
    "cosyvoice": {"supports_emotion": True, "method": "instruction"},
    "indextts": {"supports_emotion": True, "method": "vector"},
    "voxcpm": {"supports_emotion": True, "method": "valence_arousal"},
    "sambert": {"supports_emotion": True, "method": "emotion_param"},
    "vibevoice": {"supports_emotion": True, "method": "inline_tag"},
    "qwen": {"supports_emotion": True, "method": "instruction"},
    "chatterbox": {"supports_emotion": True, "method": "parameter"},
    "xtts_v2": {"supports_emotion": True, "method": "reference_audio"}
}

# 统一情感标签列表
UNIFIED_EMOTIONS = ["happy", "sad", "angry", "fear", "surprised", "disgusted", "depressed", "calm"]