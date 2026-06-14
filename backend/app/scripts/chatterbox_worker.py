import os
import argparse
import json
import torch
import torchaudio as ta
from chatterbox.tts_turbo import ChatterboxTurboTTS

DEFAULT_REFERENCE_AUDIO = r"D:\Python\Project\tts_test_output\vibevoice.wav"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--voice_file", type=str, default=DEFAULT_REFERENCE_AUDIO,
                        help="参考音频文件路径（可选，默认为 DEFAULT_REFERENCE_AUDIO）")

    # ========== 新增情感参数 ==========
    parser.add_argument("--exaggeration", type=float, default=None)
    parser.add_argument("--cfg_weight", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    # =================================

    args = parser.parse_args()

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {device}")

        print("加载 ChatterBox Turbo 模型中...")
        model = ChatterboxTurboTTS.from_pretrained(device=device)
        print("模型加载成功")

        # 限制文本长度
        text = args.text
        max_chars = 300
        if len(text) > max_chars:
            text = text[:max_chars]
            print(f"文本过长，已截断至 {max_chars} 字符")

        # 确定参考音频路径
        reference_audio_path = args.voice_file if args.voice_file else DEFAULT_REFERENCE_AUDIO
        if not os.path.exists(reference_audio_path):
            raise Exception(f"参考音频文件不存在: {reference_audio_path}")

        # ========== 应用情感参数 ==========
        kwargs = {
            "audio_prompt_path": reference_audio_path,
        }

        # 使用传入的情感参数，否则使用默认值
        kwargs["exaggeration"] = args.exaggeration if args.exaggeration is not None else 0.5
        kwargs["cfg_weight"] = args.cfg_weight if args.cfg_weight is not None else 0.5
        kwargs["temperature"] = args.temperature if args.temperature is not None else 0.7

        print(f"生成参数: exaggeration={kwargs['exaggeration']}, "
              f"cfg_weight={kwargs['cfg_weight']}, temperature={kwargs['temperature']}")
        # =================================

        wav = model.generate(text, **kwargs)

        ta.save(args.output, wav, model.sr)
        print(f"音频已保存: {args.output}")

        result = {"success": True, "output": args.output}
        print(json.dumps(result))

    except Exception as e:
        result = {"success": False, "error": str(e)}
        print(json.dumps(result))


if __name__ == "__main__":
    main()