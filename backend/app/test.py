# import requests
#
# # 注册
# resp = requests.post(
#     "http://localhost:8000/user/register",
#     json={"username": "test", "password": "123456"}
# )
# print("注册:", resp.json())
#
# # 登录
# resp = requests.post(
#     "http://localhost:8000/user/login",
#     json={"username": "test", "password": "123456"}
# )
# print("登录:", resp.json())


# import pandas as pd
# import glob
# from pathlib import Path
#
# # 设置路径
# data_dir = Path("F:/音频数据集/EmergentTTS-Eval/data")
# output_file = Path("D:/Python/Project/backend/benchmark/texts/english2.txt")
#
# # 确保输出目录存在
# output_file.parent.mkdir(parents=True, exist_ok=True)
#
# # 获取所有 parquet 文件
# parquet_files = sorted(data_dir.glob("*.parquet"))
# print(f"找到 {len(parquet_files)} 个 parquet 文件")
#
# # 读取所有文件并提取文本
# all_texts = []
#
# for file_path in parquet_files:
#     print(f"正在读取: {file_path.name}")
#     df = pd.read_parquet(file_path)
#
#     # 检查列名
#     if 'text_to_synthesize' in df.columns:
#         texts = df['text_to_synthesize'].tolist()
#     elif 'text' in df.columns:
#         texts = df['text'].tolist()
#     else:
#         print(f"  警告: 未找到文本列，可用列: {df.columns.tolist()}")
#         continue
#
#     all_texts.extend(texts)
#     print(f"  提取了 {len(texts)} 条，累计 {len(all_texts)} 条")
#
# # 保存到 english.txt（覆盖原有文件）
# with open(output_file, "w", encoding="utf-8") as f:
#     for text in all_texts:
#         f.write(text + "\n")
#
# print(f"\n✅ 完成！共 {len(all_texts)} 条测试文本")
# print(f"✅ 已保存到: {output_file}")


# import os
# import json
# import glob
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.rcParams['font.family'] = 'sans-serif'
# matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用于中文显示，若不需要中文可移除
# matplotlib.rcParams['axes.unicode_minus'] = False
#
# # 路径设置
# results_dir = r"D:\Python\Project\backend\result2"
# output_dir = r"D:\Python\Project\backend\train"
# os.makedirs(output_dir, exist_ok=True)
#
# # 读取所有 json 文件
# json_files = glob.glob(os.path.join(results_dir, "*.json"))
# model_data = {}  # {model_name: data_dict}
#
# for file in json_files:
#     with open(file, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     model_name = data.get("engine", os.path.basename(file).replace("_", " ").split('.')[0])
#     model_data[model_name] = data
#
# # 提取指标
# models = list(model_data.keys())
# avg_latency = []
# avg_rtf = []
# avg_wer = []
# success_rate = []
# match_rate = []  # match_count / success_count
# emotion_distributions = []  # 每个模型的情感分布字典
#
# for m in models:
#     d = model_data[m]
#     avg_latency.append(d["avg_latency_ms"])
#     avg_rtf.append(d["avg_rtf"])
#     # 计算平均 WER (有些文件可能直接有 avg_wer, 如果没有则从 details 计算)
#     if "avg_wer" in d:
#         avg_wer.append(d["avg_wer"])
#     else:
#         wers = [item["wer"] for item in d["details"] if item.get("wer") is not None]
#         avg_wer.append(np.mean(wers) if wers else 0)
#     success_rate.append(d["success_rate"] * 100)  # 转为百分比
#     if d["success_count"] > 0:
#         match_rate.append(d["match_count"] / d["success_count"] * 100)
#     else:
#         match_rate.append(0)
#     emotion_distributions.append(d.get("emotion_distribution", {}))
#
# # 设定颜色
# colors = plt.cm.Set3(np.linspace(0, 1, len(models))) if len(models) > 1 else ['#1f77b4']
#
# # 1. 平均合成延迟对比 (柱状图 + 误差线)
# fig, ax = plt.subplots(figsize=(10, 6))
# bars = ax.bar(models, avg_latency, color=colors, edgecolor='black')
# ax.set_ylabel("平均延迟 (ms)")
# ax.set_title("各模型平均合成延迟对比")
# ax.set_xticklabels(models, rotation=45, ha='right')
# # 添加数值标签
# for bar, val in zip(bars, avg_latency):
#     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'{val:.0f}', ha='center', va='bottom', fontsize=9)
# plt.tight_layout()
# plt.savefig(os.path.join(output_dir, "1_avg_latency.png"), dpi=150)
# plt.close()
#
# # 2. 平均实时率 RTF 对比
# fig, ax = plt.subplots(figsize=(10, 6))
# bars = ax.bar(models, avg_rtf, color=colors, edgecolor='black')
# ax.axhline(y=1.0, color='red', linestyle='--', label='RTF=1')
# ax.set_ylabel("平均 RTF")
# ax.set_title("各模型平均实时率对比")
# ax.set_xticklabels(models, rotation=45, ha='right')
# for bar, val in zip(bars, avg_rtf):
#     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f'{val:.3f}', ha='center', va='bottom', fontsize=9)
# ax.legend()
# plt.tight_layout()
# plt.savefig(os.path.join(output_dir, "2_avg_rtf.png"), dpi=150)
# plt.close()
#
# # 3. 平均词错误率 WER 对比
# fig, ax = plt.subplots(figsize=(10, 6))
# bars = ax.bar(models, avg_wer, color=colors, edgecolor='black')
# ax.set_ylabel("平均 WER")
# ax.set_title("各模型平均词错误率对比")
# ax.set_xticklabels(models, rotation=45, ha='right')
# for bar, val in zip(bars, avg_wer):
#     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{val:.3f}', ha='center', va='bottom', fontsize=9)
# plt.tight_layout()
# plt.savefig(os.path.join(output_dir, "3_avg_wer.png"), dpi=150)
# plt.close()
#
# # 4. 成功率与完全匹配率对比 (分组柱状图)
# x = np.arange(len(models))
# width = 0.35
# fig, ax = plt.subplots(figsize=(10, 6))
# bars1 = ax.bar(x - width/2, success_rate, width, label='成功率 (%)', color='skyblue', edgecolor='black')
# bars2 = ax.bar(x + width/2, match_rate, width, label='完全匹配率 (%)', color='lightcoral', edgecolor='black')
# ax.set_ylabel("百分比 (%)")
# ax.set_title("各模型成功率与完全匹配率对比")
# ax.set_xticks(x)
# ax.set_xticklabels(models, rotation=45, ha='right')
# ax.legend()
# for bar, val in zip(bars1, success_rate):
#     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}', ha='center', va='bottom', fontsize=9)
# for bar, val in zip(bars2, match_rate):
#     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}', ha='center', va='bottom', fontsize=9)
# plt.tight_layout()
# plt.savefig(os.path.join(output_dir, "4_success_match.png"), dpi=150)
# plt.close()
#
# print(f"所有图表已保存至: {output_dir}")

import nltk
nltk.download('punkt_tab')