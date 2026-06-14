import os
import sys
import argparse
import json
import re

XTTS_V2_PATH = r"D:\Python\Project\xtts_v2"

# 默认参考音频（当用户没有上传时使用）
DEFAULT_VOICE_FILE = r"D:\Python\Project\tts_test_output\reference_happy.wav"


def detect_language(text: str) -> str:
    """检测文本语言，返回 'zh' 或 'en'"""
    # 检测是否包含中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    if chinese_pattern.search(text):
        return "zh"
    else:
        return "en"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--voice_file", type=str, required=False, default=None)
    parser.add_argument("--output", type=str, required=True)
    # 新增：可选的语言参数，如果不传则自动检测
    parser.add_argument("--language", type=str, default=None)
    args = parser.parse_args()

    # 如果没有传 voice_file，使用默认参考音频
    voice_file = args.voice_file if args.voice_file else DEFAULT_VOICE_FILE

    # 确定语言
    if args.language:
        language = args.language
    else:
        language = detect_language(args.text)

    print(f"检测到语言: {language}", file=sys.stderr)

    try:
        from TTS.api import TTS

        tts = TTS(
            model_path=XTTS_V2_PATH,
            config_path=os.path.join(XTTS_V2_PATH, "config.json"),
            gpu=True
        )

        tts.tts_to_file(
            text=args.text,
            file_path=args.output,
            speaker_wav=voice_file,
            language=language
        )

        result = {"success": True, "output": args.output, "language": language}
        print(json.dumps(result))

    except Exception as e:
        result = {"success": False, "error": str(e)}
        print(json.dumps(result))


if __name__ == "__main__":
    main()