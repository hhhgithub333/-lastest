import os
import re
import wave
from typing import Tuple


# ─── 1. 归一化 ───

def normalize_chinese(text: str) -> str:
    """
    中文文本归一化（Whisper 风格 + 中文适配）
    - 全角转半角
    - 去标点符号
    - 合并多余空格
    """
    # 全角转半角
    result = []
    for ch in text:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    text = ''.join(result)

    # 移除标点符号
    text = re.sub(r'[，。！？、；：""''《》（）【】「」『』,!?;:"\'()\[\]{}/\\]', '', text)
    # 移除其他符号
    text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s]', '', text)
    # 合并空格
    text = re.sub(r'\s+', '', text)
    return text.lower().strip()


def normalize_english(text: str) -> str:
    """
    英文文本归一化（Whisper 官方风格）
    - 转小写
    - 去标点
    - 标准化空白
    - 缩写规范化
    - 数字格式化
    """
    # 转小写
    text = text.lower()

    # 常见缩写规范化
    replacements = {
        "i'm": "i am", "i've": "i have", "i'll": "i will", "i'd": "i would",
        "you're": "you are", "you've": "you have", "you'll": "you will",
        "he's": "he is", "she's": "she is", "it's": "it is",
        "we're": "we are", "we've": "we have", "we'll": "we will",
        "they're": "they are", "they've": "they have", "they'll": "they will",
        "that's": "that is", "what's": "what is", "who's": "who is",
        "there's": "there is", "here's": "here is",
        "don't": "do not", "doesn't": "does not", "didn't": "did not",
        "can't": "cannot", "couldn't": "could not",
        "won't": "will not", "wouldn't": "would not",
        "shouldn't": "should not", "mightn't": "might not",
        "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
        "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
        "let's": "let us",
    }
    for abbr, full in replacements.items():
        text = text.replace(abbr, full)

    # 去标点（仅保留字母、数字、空格）
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # 标准化空白
    text = ' '.join(text.split())
    return text.strip()


# ─── 2. Levenshtein 距离（CER/WER 核心）──────────────────────────────────────

def levenshtein_distance(ref: str, hyp: str) -> Tuple[int, int, int]:
    """
    计算 Levenshtein 距离，返回 (substitutions, deletions, insertions)
    ref / hyp 已经是归一化后的字符串
    """
    ref_chars = list(ref)
    hyp_chars = list(hyp)

    m, n = len(ref_chars), len(hyp_chars)
    # dp[i][j] = 编辑距离（ref[:i] -> hyp[:j]）
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i  # 全删
    for j in range(n + 1):
        dp[0][j] = j  # 全插

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    # 回溯统计替换/删除/插入
    s, d, ins = 0, 0, 0
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_chars[i - 1] == hyp_chars[j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            s += 1
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            d += 1
            i -= 1
        else:
            ins += 1
            j -= 1

    return s, d, ins


def cer(reference: str, hypothesis: str) -> float:
    """
    字符错误率（Character Error Rate）
    适用于中文
    reference / hypothesis: 归一化后的字符串
    """
    ref = normalize_chinese(reference)
    hyp = normalize_chinese(hypothesis)

    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0

    s, d, ins = levenshtein_distance(ref, hyp)
    return (s + d + ins) / len(ref)


def wer(reference: str, hypothesis: str) -> float:
    """
    词错误率（Word Error Rate）
    适用于英文
    reference / hypothesis: 归一化后的字符串
    """
    ref = normalize_english(reference)
    hyp = normalize_english(hypothesis)

    ref_words = ref.split()
    hyp_words = hyp.split()

    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0

    s, d, ins = levenshtein_distance(ref_words, hyp_words)
    return (s + d + ins) / len(ref_words)


# ─── 3. 音频时长计算 ─────────────────────────────────────────────────────────

def get_audio_duration(audio_path: str) -> float:
    """
    读取 WAV 文件，返回时长（秒）
    audio_path: .wav 文件路径
    """
    if not os.path.exists(audio_path):
        return 0.0
    try:
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        # fallback: 尝试 pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0


def save_audio_pcm16(pcm_data: bytes, output_path: str, sample_rate: int = 24000):
    """
    将 PCM16 数据保存为 WAV 文件
    pcm_data: bytes，int16 数组
    output_path: .wav 文件路径
    sample_rate: 采样率（默认 24000）
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
