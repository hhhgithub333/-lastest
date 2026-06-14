import os
import sys
import asyncio
import tempfile
import subprocess
import logging
from typing import Optional
from .base import BaseTTSEngine
from ..tts.emotion_adapter import EmotionAdapter

logger = logging.getLogger("xtts_v2")

CONDA_BASE = r"E:\miniconda3"
PYTHON_PATH = os.path.join(CONDA_BASE, "envs", "xtts_v2", "python.exe")
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "xtts_v2_worker.py"))


class XTTSv2Engine(BaseTTSEngine):

    def get_voices(self) -> list:
        return []

    def get_audio_format(self) -> str:
        return "wav"

    async def synthesize(
            self,
            text: str,
            voice: str = None,
            reference_audio: bytes = None,
            emotion: str = None,
            emotion_intensity: float = 0.5
    ) -> bytes:
        """
        XTTS-v2 合成

        Args:
            text: 要合成的文本
            voice: 音色参数（保留兼容）
            reference_audio: 参考音频数据（bytes），如果有则优先使用
            emotion: 情感标签
            emotion_intensity: 情感强度
        """
        logger.info(f"XTTS-v2 合成请求: {text[:30]}..." if len(text) > 30 else f"XTTS-v2 合成请求: {text}")
        logger.info(f"📋 情感标签: {emotion}, 强度: {emotion_intensity}")

        voice_file = None
        temp_voice_path = None

        # ========== 情感参数处理 ==========
        xtts_params = {}
        if emotion:
            xtts_params = EmotionAdapter.convert("xtts_v2", emotion, emotion_intensity)
            logger.info(f"XTTS-v2 情感参数: {xtts_params}")
        # =================================

        try:
            # ========== 决定使用哪个参考音频 ==========
            if reference_audio:
                # 优先级1：用户上传的参考音频
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(reference_audio)
                    temp_voice_path = tmp.name
                voice_file = temp_voice_path
                logger.info(f"✅ 使用用户上传的参考音频，长度: {len(reference_audio)} bytes")
                logger.info(f"   📁 临时文件: {voice_file}")

            elif xtts_params and "speaker_wav" in xtts_params:
                # 优先级2：使用情感对应的预设参考音频
                preset_audio = xtts_params["speaker_wav"]
                if os.path.exists(preset_audio):
                    voice_file = preset_audio
                    logger.info(f"✅ 使用情感预设参考音频: {preset_audio}")
                    logger.info(f"   😊 对应情感: {emotion}, 强度: {emotion_intensity}")
                else:
                    logger.warning(f"⚠️ 情感预设参考音频不存在: {preset_audio} (emotion={emotion})")
                    voice_file = None
            else:
                voice_file = None
                logger.warning("⚠️ 没有参考音频，将使用默认（可能效果不佳）")

            # 检查参考音频是否存在
            if voice_file and not os.path.exists(voice_file):
                logger.warning(f"⚠️ 参考音频不存在: {voice_file}，将使用默认")
                voice_file = None

            # 打印最终使用的参考音频
            if voice_file:
                logger.info(f"🎤 最终使用的参考音频: {voice_file}")
            else:
                logger.warning("🎤 没有可用的参考音频")

            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = tmp.name

            # 构建命令
            cmd = [
                PYTHON_PATH,
                SCRIPT_PATH,
                "--text", text,
                "--output", output_path
            ]

            if voice_file:
                cmd.extend(["--voice_file", voice_file])
                logger.info(f"🔧 命令参数: --voice_file {voice_file}")

            logger.info(f"🚀 开始合成...")
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._run_subprocess,
                cmd,
                output_path
            )

            logger.info(f"✅ 合成成功，音频大小: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"❌ XTTS-v2 合成失败: {e}")
            raise

        finally:
            if temp_voice_path and os.path.exists(temp_voice_path):
                try:
                    os.unlink(temp_voice_path)
                    logger.debug(f"🗑️ 已删除临时文件: {temp_voice_path}")
                except Exception:
                    pass

    def _run_subprocess(self, cmd: list, output_path: str) -> bytes:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise RuntimeError(f"TTS Worker 错误: {error_msg}")

            if not os.path.exists(output_path):
                raise FileNotFoundError(f"输出文件未生成: {output_path}")

            with open(output_path, "rb") as f:
                audio_data = f.read()

            try:
                os.unlink(output_path)
            except Exception:
                pass

            return audio_data

        except subprocess.TimeoutExpired:
            raise TimeoutError("TTS 合成超时")
        except Exception as e:
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except Exception:
                    pass
            raise