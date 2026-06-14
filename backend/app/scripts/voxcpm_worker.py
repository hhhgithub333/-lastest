import os
import sys
import argparse
import json
import shutil
from gradio_client import Client, handle_file
import io

GRADIO_URL = "http://localhost:7860"

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--voice_file", type=str, required=False, default=None)
    parser.add_argument("--output", type=str, required=True)

    # ========== 情感参数 ==========
    parser.add_argument("--emotion", type=str, default=None)
    parser.add_argument("--emotion_intensity", type=float, default=0.5)
    #valence 和 arousal（官方核心参数）
    parser.add_argument("--valence", type=float, default=None)
    parser.add_argument("--arousal", type=float, default=None)
    parser.add_argument("--cfg_value", type=float, default=None)
    parser.add_argument("--timesteps", type=int, default=None)

    # ========== 参考音频对应文本 ==========
    parser.add_argument("--prompt_text", type=str, default=None)

    args = parser.parse_args()

    try:
        client = Client(GRADIO_URL)

        prompt_wav = None
        if args.voice_file and os.path.exists(args.voice_file):
            prompt_wav = handle_file(args.voice_file)

        prompt_text = args.prompt_text if args.prompt_text else ""

        if not prompt_text and args.emotion:
            EMOTION_PROMPTS = {
                "happy": "I can confidently declare that this is the most exquisite chocolate cake my taste buds have ever had the pleasure to encounter! Mo proclaimed, savoring every bite. He could not stop eating!",
                "sad": "I miss Grandma so much. She's gone forever and I feel so sad.",
                "angry": "Life is so unfair and frustrating! Every stupid challenge just makes me angrier. I'm sick of this ridiculous nonsense!",
                "fear": "Jane's eyes wide with terror, she screamed, The brakes aren't working! What do we do now? We're completely trapped, and we're heading straight for that wall, I can't stop it!",
                "surprised": "What? He got into Harvard? That's absolutely incredible! I can't believe my ears! He was never the top student in our class, and now this",
                "disgusted": "This food tastes absolutely disgusting. I feel sick just looking at it. What on earth did they put in this?",
                "depressed": "I don't know. Life just feels so boring and meaningless lately.",
                "calm": "Dyslexia is a common learning difficulty that affects reading and spelling. However, with proper training and support, many people with dyslexia can overcome these challenges."
            }
            prompt_text = EMOTION_PROMPTS.get(args.emotion, "")

        cfg_value = args.cfg_value if args.cfg_value is not None else 1.8
        timesteps = args.timesteps if args.timesteps is not None else 12

        # 如果 API 支持直接传 valence/arousal：
        result = client.predict(
            text_input=args.text,
            prompt_wav_path_input=prompt_wav,
            prompt_text_input=prompt_text,
            cfg_value_input=cfg_value,
            inference_timesteps_input=timesteps,
            do_normalize=True,
            denoise=True,
            api_name="/generate"
        )

        shutil.copy(result, args.output)

        result_json = {"success": True, "output": args.output}
        print(json.dumps(result_json))

    except Exception as e:
        result_json = {"success": False, "error": str(e)}
        print(json.dumps(result_json))


if __name__ == "__main__":
    main()