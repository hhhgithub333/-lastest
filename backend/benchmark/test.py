import json
from pathlib import Path
from statistics import mean, median
from benchmark_vibevoice import get_audio_duration  # 替换为你实际模块喵

# JSON 文件路径
json_path_str = r"D:\Python\Project\backend\result2\report_xtts_v2_20260428_130315.json"
json_path = Path(json_path_str)

# 加载 JSON
with open(json_path, "r", encoding="utf-8") as f:
    report = json.load(f)

details = report.get("details", [])

# 遍历每条记录，修正 audio_duration_s 和 rtf
for item in details:
    if not item.get("success"):
        continue  # 跳过失败条目喵

    audio_path = item.get("output_path")
    latency_ms = item.get("latency_ms", 0)

    if audio_path and Path(audio_path).exists():
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        duration = get_audio_duration(audio_bytes)
        item["audio_duration_s"] = round(duration, 4)
        item["rtf"] = round((latency_ms / 1000) / duration, 4) if duration > 0 else 0
    else:
        item["audio_duration_s"] = 0.0
        item["rtf"] = 0

# 重新计算 avg_rtf 和 median_rtf，只用成功生成的条目
rtfs = [item["rtf"] for item in details if item.get("success") and item.get("rtf", 0) > 0]
report["avg_rtf"] = round(mean(rtfs), 4) if rtfs else 0
report["median_rtf"] = round(median(rtfs), 4) if rtfs else 0

# 保存新报告
new_json_path = json_path.parent / f"{json_path.stem}_rtf_fixed.json"
with open(new_json_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"更新完成，新文件保存为: {new_json_path}")
print(f"avg_rtf = {report['avg_rtf']}, median_rtf = {report['median_rtf']}")