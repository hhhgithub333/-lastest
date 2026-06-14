import os
from typing import Dict

os.environ['HF_HUB_OFFLINE'] = '1'
# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 尝试导入 transformers
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("[EmotionRecognizer] 请安装 transformers: pip install transformers")


# 11种情绪到你的8种的映射
EMOTION_MAPPING = {
    "anger": "angry",
    "sadness": "sad",
    "joy": "happy",
    "fear": "fear",
    "surprise": "surprised",
    "disgust": "disgusted",
    "frustration": "angry",
    "gratitude": "happy",
    "love": "happy",
    "contempt": "disgusted",
    "neutral": "calm"
}

# 关键词匹配词典（降级方案）
EMOTION_KEYWORDS = {
    "angry": [
        "愤怒", "生气", "可恶", "讨厌", "恨", "气死", "恼火", "混蛋", "不公平", "抓狂",
        "angry", "mad", "furious", "hate", "rage", "annoyed", "irritated", "unfair",
        "frustrated", "frustrating", "outrage", "resent", "angrier"
    ],
    "happy": [
        "开心", "高兴", "快乐", "兴奋", "激动", "太棒了", "耶", "哈哈", "爽", "美好", "喜悦",
        "happy", "joy", "excited", "wonderful", "great", "awesome", "amazing",
        "fantastic", "glad", "cheerful", "delighted", "pleased", "lovely"
    ],
    "sad": [
        "难过", "伤心", "悲伤", "痛苦", "失望", "唉", "可惜", "哭了", "难受", "忧郁",
        "sad", "unhappy", "depressed", "disappointed", "sorry", "grief", "sorrow",
        "miserable", "heartbroken", "upset", "lonely"
    ],
    "fear": [
        "害怕", "恐惧", "紧张", "担心", "焦虑", "可怕", "吓人", "惊慌",
        "fear", "afraid", "scared", "terrified", "frightened", "anxious", "nervous",
        "worried", "panic", "dread", "horror"
    ],
    "surprised": [
        "惊讶", "震惊", "意外", "居然", "竟然", "哇", "天哪", "吃惊",
        "surprised", "shocked", "astonished", "amazed", "unexpected", "wow", "oh my",
        "startled", "stunned", "incredible"
    ],
    "disgusted": [
        "厌恶", "恶心", "反感", "讨厌", "嫌弃", "呕吐",
        "disgusted", "disgusting", "repulsed", "revolted", "gross", "sick", "awful",
        "horrible", "terrible", "nasty"
    ],
    "depressed": [
        "抑郁", "绝望", "无助", "空虚", "没意思", "累", "疲惫",
        "depressed", "hopeless", "helpless", "empty", "worthless", "tired", "exhausted",
        "despair", "gloomy", "miserable", "down"
    ],
    "calm": [
        "平静", "淡定", "从容", "安宁", "放松", "安静", "平和",
        "calm", "peaceful", "relaxed", "quiet", "serene", "tranquil", "cool",
        "composed", "steady", "balanced", "neutral"
    ]
}


class EmotionRecognizer:
    """
    多语言情感识别器
    使用 tabularisai/multilingual-emotion-classification 模型
    支持中文、英文等23种语言
    """

    def __init__(self):
        self.cache = {}

        if not HAS_TRANSFORMERS:
            print("[EmotionRecognizer] transformers 未安装，使用关键词匹配")
            self.classifier = None
            return

        try:
            print("[EmotionRecognizer] 加载多语言情感识别模型...")
            local_model_path = r"E:\hf_cache\huggingface\hub\models--tabularisai--multilingual-emotion-classification\snapshots\24895f06e3f50c532aa29c400e6708b57db1c16d"
            self.classifier = pipeline(
                "text-classification",
                model=local_model_path,
                top_k=3
            )
            print("[EmotionRecognizer] 模型加载完成，支持23种语言")
        except Exception as e:
            print(f"[EmotionRecognizer] 模型加载失败: {e}")
            print("[EmotionRecognizer] 降级使用关键词匹配")
            self.classifier = None

    def _analyze_with_keywords(self, text: str) -> Dict:
        """使用关键词匹配分析（降级方案）"""
        text_lower = text.lower()
        scores = {emotion: 0 for emotion in EMOTION_KEYWORDS}

        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                count = text_lower.count(keyword_lower)
                if count > 0:
                    scores[emotion] += count * 2
                    if keyword_lower * 2 in text_lower:
                        scores[emotion] += 3
                    # 英文词额外加分
                    if keyword[0].isalpha() and ord(keyword[0]) < 128:
                        scores[emotion] += 1

        max_emotion = max(scores, key=scores.get)
        max_score = scores[max_emotion]

        if max_score == 0:
            return {"emotion": "calm", "intensity": 0.5, "confidence": 0.5}

        intensity = min(1.0, max_score / 40)

        return {
            "emotion": max_emotion,
            "intensity": intensity,
            "confidence": 0.6 + intensity * 0.3
        }

    def analyze(self, text: str) -> Dict:
        if not text or not text.strip():
            return {"emotion": "calm", "intensity": 0.5, "confidence": 0.5}

        # 检查缓存
        if text in self.cache:
            return self.cache[text]

        # 检查模型是否可用，不可用时降级到关键词匹配
        if self.classifier is None:
            result = self._analyze_with_keywords(text)
            self.cache[text] = result
            return result

        try:
            results = self.classifier(text)
        except Exception as e:
            print(f"[EmotionRecognizer] 识别失败: {e}")
            result = self._analyze_with_keywords(text)
            self.cache[text] = result
            return result

        if not results or not results[0]:
            result = self._analyze_with_keywords(text)
            self.cache[text] = result
            return result

        # 兼容不同的返回格式
        top = results[0]
        if isinstance(top, list) and len(top) > 0:
            top = top[0]

        # 确保 top 是字典
        if not isinstance(top, dict):
            result = self._analyze_with_keywords(text)
            self.cache[text] = result
            return result

        raw_emotion = top.get('label', 'neutral')
        intensity = top.get('score', 0.5)
        emotion = EMOTION_MAPPING.get(raw_emotion, "calm")
        all_emotions = {}
        try:
            for item in results:
                if isinstance(item, dict):
                    all_emotions[item.get('label', 'unknown')] = item.get('score', 0)
                elif isinstance(item, list):
                    for sub_item in item:
                        if isinstance(sub_item, dict):
                            all_emotions[sub_item.get('label', 'unknown')] = sub_item.get('score', 0)
        except Exception:
            all_emotions = {raw_emotion: intensity}

        result = {
            "emotion": emotion,
            "emotion_raw": raw_emotion,
            "intensity": intensity,
            "confidence": intensity,
            "all_emotions": all_emotions
        }

        # 存入缓存
        self.cache[text] = result
        return result


# 全局单例
_emotion_recognizer = None


def get_emotion_recognizer() -> EmotionRecognizer:
    """获取情感识别器单例"""
    global _emotion_recognizer
    if _emotion_recognizer is None:
        _emotion_recognizer = EmotionRecognizer()
    return _emotion_recognizer