import os
import sys
import argparse
import json
import struct
import urllib.parse
import websocket

VIBEVOICE_PORT = 3000
VIBEVOICE_WS_URL = f"ws://127.0.0.1:{VIBEVOICE_PORT}/stream"

# 根据情感动态设置 cfg_scale（1.0 ~ 3.0）
EMOTION_CFG_MAP = {
    "angry": 2.3,
    "happy": 2.3,
    "surprised": 2.2,
    "sad": 2.2,
    "fear": 2.0,
    "disgusted": 2.2,
    "depressed": 2.0,
    "calm": 1.9,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--voice", type=str, default="en-Grace_woman")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--emotion", type=str, default=None)
    parser.add_argument("--emotion-intensity", type=float, default=0.5)
    args = parser.parse_args()

    try:
        # 根据情感动态设置 cfg_scale
        if args.emotion and args.emotion in EMOTION_CFG_MAP:
            cfg_value = EMOTION_CFG_MAP[args.emotion]
        else:
            cfg_value = 2.5  # 默认最高

        # 构建 URL - 只传必要参数，不加情感标签
        ws_url = f"{VIBEVOICE_WS_URL}?voice={args.voice}&cfg={cfg_value}&steps=14"
        ws_url += f"&text={urllib.parse.quote(args.text)}"

        print(f"DEBUG: emotion={args.emotion}, cfg={cfg_value}", file=sys.stderr)
        print(f"DEBUG: ws_url = {ws_url[:200]}...", file=sys.stderr)

        audio_data = bytearray()
        ws = websocket.create_connection(ws_url, timeout=None)

        while True:
            try:
                message = ws.recv()
                if isinstance(message, bytes):
                    audio_data.extend(message)
                else:
                    continue
            except websocket.WebSocketTimeoutException:
                break
            except Exception:
                break

        ws.close()

        if len(audio_data) == 0:
            raise RuntimeError("未接收到音频数据")

        # 添加 WAV 头
        sample_rate = 24000
        channels = 1
        bits_per_sample = 16
        bytes_per_sample = bits_per_sample // 8

        wav_header = struct.pack('<4sI4s', b'RIFF', 0, b'WAVE')
        wav_header += struct.pack('<4sI', b'fmt ', 16)
        wav_header += struct.pack('<HHIIHH', 1, channels, sample_rate,
                                  sample_rate * channels * bytes_per_sample,
                                  channels * bytes_per_sample, bits_per_sample)
        wav_header += struct.pack('<4sI', b'data', len(audio_data))

        with open(args.output, "wb") as f:
            f.write(wav_header)
            f.write(audio_data)

        result = {"success": True, "output": args.output}
        print(json.dumps(result))

    except Exception as e:
        result = {"success": False, "error": str(e)}
        print(json.dumps(result))


if __name__ == "__main__":
    main()