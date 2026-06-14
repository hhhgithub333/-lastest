<template>
  <div class="floating-window">
    <!-- 顶部状态栏 -->
    <StatusBar
      :status-text="statusText"
      :voice-name="voiceName"
      :has-text="hasText"
    />

    <!-- ========== 文字显示区 ========== -->
    <TextDisplay
      :display-text="displayText"
      :text-chars="textCharsRef"
      ref="textDisplayRef"
    />

    <!-- ========== 进度条 ========== -->
    <div class="progress-section" v-if="hasText && progressDuration > 0">
      <div class="progress-bar-wrapper">
        <span class="time-label">{{ formatTime(progressTime) }}</span>
        <input
          type="range"
          class="progress-slider"
          min="0"
          :max="progressDuration"
          step="0.1"
          v-model.number="progressTime"
          :style="{ '--progress': (progressTime / Math.max(progressDuration, 1) * 100) + '%' }"
          @mousedown="isSeeking = true"
          @mouseup="onSeekEnd"
          @touchstart="isSeeking = true"
          @touchend="onSeekEnd"
          @input="onSeekDrag"
          @change="onSeekEnd"
        />
        <span class="time-label">{{ formatTime(progressDuration) }}</span>
      </div>
    </div>

    <!-- 控制按钮区 -->
    <ControlBar
      :capturing="capturing"
      :playing="playing"
      :paused="paused"
      :has-text="hasText"
      :current-speed="currentSpeed"
      :current-audio-blob="currentAudioBlob"
      :show-ref-tip="showRefTip"
      :downloading="downloading"
      :speed-options="speedOptions"
      @capture="captureAndSend"
      @toggle-play="togglePlay"
      @stop="stop"
      @download="downloadAudio"
      @set-speed="setSpeed"
      @close-tip="showRefTip = false"
    />

    <!-- 关闭按钮 -->
    <button class="btn-close" @click="closeWindow" title="关闭悬浮窗">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { captureScreen, recognizeText } from '../utils/capture';
import { synthesize } from '../api/tts';
import {
  playAudio,
  stopAudio,
  setSpeed as setAudioSpeed,
  pauseAudio,
  resumeAudio,
  setProgressCallback,
  generateSimpleTimestamps,
  seekTo
} from '../utils/audio';
import { generateWhisperTimestamps } from '../utils/audio-whisper.js';
import { modelNeedsReference } from '../utils/constants';

import StatusBar from './components/StatusBar.vue';
import TextDisplay from './components/TextDisplay.vue';
import ControlBar from './components/ControlBar.vue';

// ========== 倍速选项 ==========
const speedOptions = [0.5, 0.75, 1.0,1.25, 1.5, 2.0];
const currentSpeed = ref(1.0);

// ========== 状态 ==========
const capturing = ref(false);
const playing = ref(false);
const paused = ref(false);
const hasText = ref(false);
const showRefTip = ref(false);
const downloading = ref(false);

// ========== 新增：音频生成状态 ==========
const generating = ref(false);        // 正在合成中
const audioGenerated = ref(false);   // 是否已生成过音频（用于判断首次播放）
const playComplete = ref(false);     // 播放完成提示
const stopped = ref(false);          // 停止后提示"已退出"

// ========== 进度条状态 ==========
const progressTime = ref(0);
const progressDuration = ref(0);
const isSeeking = ref(false);

// ========== 文字显示相关 ==========
const displayText = ref('');
const textCharsRef = ref([]);
const textDisplayRef = ref(null);

let currentText = '';
let currentAudioBlob = null;

// ========== 纯 JS 追踪，不走 Vue 响应式 ==========
let _textChars = [];
let _currentIndex = -1;

/**
 * 获取音频实际时长
 */
const getAudioDuration = (blob) => {
    return new Promise((resolve) => {
        const audio = new Audio();
        audio.src = URL.createObjectURL(blob);
        audio.addEventListener('loadedmetadata', () => {
            URL.revokeObjectURL(audio.src);
            resolve(audio.duration || 3);
        });
        audio.addEventListener('error', () => {
            resolve(3);
        });
    });
};

// ========== 模型信息 ==========
const voiceName = ref('Cherry');

// ========== 状态文字 ==========
const statusText = computed(() => {
    if (capturing.value) return '识别中...';
    if (downloading.value) return '保存中...';
    if (generating.value) return '正在生成中...';
    if (stopped.value) return '已退出';          // 停止后提示
    if (playComplete.value) return '播放完成';
    if (playing.value && !paused.value) return '播放中';
    if (paused.value) return '已暂停';
    if (hasText.value) return '已就绪';
    return '等待捕获';
});

/**
 * 获取文字显示区的真实 DOM div 元素
 */
function _getDisplayContainer() {
    if (!textDisplayRef.value) return null;
    return textDisplayRef.value.innerRef || null;
}

/**
 * 直接更新 DOM className（只改当前和上一个字符）
 * 关键：span 元素通过 :data-char-idx 定位，完全绕过 Vue diff
 */
function _updateHighlightInDOM(prevIndex, newIndex) {
    const container = _getDisplayContainer();
    if (!container) {
        console.warn('[高亮] 文字容器 DOM 未就绪，跳过');
        return;
    }

    const spans = container.querySelectorAll('[data-char-idx]');
    if (!spans.length) {
        console.warn('[高亮] 未找到字符 span 元素，跳过');
        return;
    }

    // 上一个 → read
    if (prevIndex >= 0 && spans[prevIndex]) {
        spans[prevIndex].className = 'char-read';
    }
    // 当前 → current
    if (newIndex >= 0 && spans[newIndex]) {
        spans[newIndex].className = 'char-current';

        // 自动滚动：仅在字符超出可视区时才滚动
        const el = spans[newIndex];
        const elTop = el.offsetTop;
        const containerTop = container.scrollTop;
        const containerBottom = containerTop + container.clientHeight;
        if (elTop < containerTop || elTop > containerBottom - 24) {
            container.scrollTop = Math.max(0, elTop - container.clientHeight / 2);
        }
    }
}

/**
 * 批量更新 DOM（播放结束/停止时）
 */
function _updateAllDOM(startIndex, endIndex, status) {
    const container = _getDisplayContainer();
    if (!container) return;
    const spans = container.querySelectorAll('[data-char-idx]');
    const cls = `char-${status}`;
    for (let i = startIndex; i < endIndex && i < spans.length; i++) {
        spans[i].className = cls;
    }
}

/**
 * 根据当前播放时间重新渲染所有字符的 class
 * 用于进度条拖回时同步高亮（Bug 2 fix）
 */
function _syncHighlightToTime(currentTime) {
    const container = _getDisplayContainer();
    if (!container) return;
    const spans = container.querySelectorAll('[data-char-idx]');
    if (!spans.length) return;

    let newCurrentIndex = -1;
    for (let i = 0; i < _textChars.length; i++) {
        const item = _textChars[i];
        if (currentTime >= item.start && currentTime < item.end) {
            newCurrentIndex = i;
            break;
        }
    }

    // 全量遍历：只更新有变化的字符
    for (let i = 0; i < spans.length; i++) {
        if (i < _textChars.length) {
            const shouldBe = i < newCurrentIndex ? 'char-read'
                           : i === newCurrentIndex ? 'char-current'
                           : 'char-upcoming';
            spans[i].className = shouldBe;
        }
    }
    _currentIndex = newCurrentIndex;
}

// ========== 更新高亮状态（由 rAF 驱动，每帧约 16ms 调用一次） ==========
const updateHighlight = ({ currentTime, duration }) => {
    if (!_textChars.length) return;

    if (!isSeeking.value) {
        progressTime.value = currentTime;
        progressDuration.value = duration || 0;
    }

    // 播放结束
    if (currentTime < 0) {
        _updateAllDOM(0, _textChars.length, 'read');
        _currentIndex = -1;
        progressTime.value = 0;
        return;
    }

    // 遍历时间戳找当前字符
    for (let i = 0; i < _textChars.length; i++) {
        const item = _textChars[i];
        if (currentTime >= item.start && currentTime < item.end) {
            if (_currentIndex !== i) {
                const prev = _currentIndex;
                _currentIndex = i;
                _updateHighlightInDOM(prev, i);
            }
            break;
        }
    }
};

// ========== 进度条拖动 ==========
const onSeekDrag = () => {
    isSeeking.value = true;
    seekTo(progressTime.value);
};

const onSeekEnd = () => {
    seekTo(progressTime.value);
    isSeeking.value = false;
    // 拖回后全量同步高亮（Bug 2 fix）
    if (_textChars.length) {
        _syncHighlightToTime(progressTime.value);
    }
};

// ========== 格式化时间 ==========
const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// ========== 从 localStorage 读取设置 ==========
const loadSettings = () => {
    const engine = localStorage.getItem('tts_engine');
    const voice = localStorage.getItem('tts_voice');
    const speed = localStorage.getItem('tts_speed');
    console.log('[悬浮窗] 读取设置:', { engine, voice, speed });
    if (voice) voiceName.value = voice;
    if (speed) currentSpeed.value = parseFloat(speed);
};

// ========== 倍速设置 ==========
const setSpeed = (s) => {
    currentSpeed.value = s;
    localStorage.setItem('tts_speed', s.toString());
    if (playing.value) {
        setAudioSpeed(s);
    }
};

// ========== 捕获并发送文字给主窗口 ==========
const captureAndSend = async () => {
    capturing.value = true;

    // Bug 1 fix：在做任何异步操作之前，先清掉旧 span 的 class
    // stopAudio() 可能早已结束（progressCallback 已清），_updateAllDOM 没机会执行
    // 所以这里手动清空，防止 Vue diff 复用旧 span 时 char-read 残留
    const oldContainer = _getDisplayContainer();
    if (oldContainer) {
        const oldSpans = oldContainer.querySelectorAll('[data-char-idx]');
        for (const span of oldSpans) {
            span.className = 'char-upcoming';
        }
    }

    try {
        await window.electronAPI.hideFloatingWindow();
        console.log('悬浮窗已隐藏，开始截图...');
        await new Promise(resolve => setTimeout(resolve, 100));
    } catch (err) {
        console.error('隐藏悬浮窗失败:', err);
    }

    try {
        const imageData = await window.electronAPI.captureScreen();
        if (!imageData) {
            console.error('截图失败');
            return;
        }

        console.log('截图成功，图片大小:', imageData.length);

        const text = await recognizeText(imageData);
        console.log('原始识别结果:', text);

        if (!text) {
            console.error('未识别到文字');
            return;
        }

        currentText = text;
        hasText.value = true;
        currentAudioBlob = null;
        audioGenerated.value = false;
        playComplete.value = false;
        stopped.value = false;
        displayText.value = text;
        _currentIndex = -1;

        _textChars = text.split('').map(char => ({
            char,
            start: 0,
            end: 0,
            status: 'upcoming'
        }));
        textCharsRef.value = [..._textChars];

        window.electronAPI.sendCapturedText(text);

    } catch (err) {
        console.error('识别失败:', err);
    } finally {
        capturing.value = false;
        try {
            await window.electronAPI.showFloatingWindow();
            console.log('悬浮窗已重新显示');
        } catch (err) {
            console.error('显示悬浮窗失败:', err);
        }
    }
};

// ========== 播放/暂停切换 ==========
const togglePlay = async () => {
    if (playing.value && !paused.value) {
        pause();
    } else if (paused.value) {
        resume();
    } else {
        await play();
    }
};

// ========== 播放 ==========
const play = async () => {
    console.log('[悬浮窗] play() 开始');

    if (!currentText) {
        console.log('[悬浮窗] 没有文字，跳过');
        return;
    }

    // 每次点击播放都重置状态
    playComplete.value = false;
    stopped.value = false;

    // ========== 检查缓存 ==========
    if (currentAudioBlob) {
        console.log('[悬浮窗] 使用缓存的音频，直接播放');

        playing.value = true;
        paused.value = false;
        _currentIndex = -1;

        const container = _getDisplayContainer();
        if (container) {
            const spans = container.querySelectorAll('[data-char-idx]');
            for (const span of spans) {
                span.className = 'char-upcoming';
            }
        }
        try {
            const actualDuration = await getAudioDuration(currentAudioBlob);

            let timestamps;
            try {
                // 直接使用 WhisperX 原始时间戳，不做整体偏移
                // WhisperX 对中文合成语音的对齐结果与 audio.currentTime 基本同步
                timestamps = await generateWhisperTimestamps(currentText, currentAudioBlob, actualDuration);
            } catch (e) {
                console.warn('[播放] Whisper 对齐失败，使用平均分配：', e);
                timestamps = generateSimpleTimestamps(currentText, actualDuration);
            }

            _textChars = timestamps.map(t => ({ ...t, status: 'upcoming' }));
            textCharsRef.value = [..._textChars];

            setProgressCallback(updateHighlight);
            await playAudio(currentAudioBlob, currentSpeed.value, actualDuration);
            console.log('[悬浮窗] 播放完成');
            playComplete.value = true;
            setTimeout(() => {
                if (playComplete.value) playComplete.value = false;
            }, 3000);
        } catch (err) {
            console.error('[悬浮窗] 播放失败:', err);
        } finally {
            playing.value = false;
            paused.value = false;
        }
        return;
    }
    // ========== 缓存检查结束 ==========

    const engine = localStorage.getItem('tts_engine') || 'qwen';
    console.log('[悬浮窗] 当前引擎:', engine);

    let referenceAudioFile = null;

    if (modelNeedsReference(engine)) {
        console.log('[悬浮窗] 模型需要参考音频，通过 IPC 读取...');

        try {
            const audioResult = await window.electronAPI.getReferenceAudioData();
            console.log('[悬浮窗] getReferenceAudioData 返回:', audioResult ? `(${audioResult.data.byteLength} bytes, ${audioResult.mimeType})` : 'null');

            if (!audioResult || !audioResult.data) {
                console.log('[悬浮窗] 没有读取到参考音频数据，显示提示');
                showRefTip.value = true;
            }

            const ext = audioResult.filename.split('.').pop().toLowerCase();
            const mimeMap = {
                'wav': 'audio/wav',
                'mp3': 'audio/mpeg',
                'flac': 'audio/flac',
                'm4a': 'audio/mp4',
                'ogg': 'audio/ogg',
                'aac': 'audio/aac'
            };
            const mimeType = mimeMap[ext] || audioResult.mimeType || 'audio/wav';

            referenceAudioFile = new File(
                [audioResult.data],
                audioResult.filename,
                { type: mimeType }
            );
            console.log('[悬浮窗] 参考音频读取完成:', referenceAudioFile);
        } catch (err) {
            console.error('[悬浮窗] 读取参考音频失败:', err);
            showRefTip.value = true;
        }
    } else {
        console.log('[悬浮窗] 模型不需要参考音频');
    }

    playing.value = true;
    paused.value = false;
    generating.value = true;   // 开始合成，显示"正在生成中"
    _currentIndex = -1;

    // 预填 placeholder（保证 TextDisplay 有内容可渲染）
    _textChars = currentText.split('').map(char => ({
        char,
        start: 0,
        end: 0,
        status: 'upcoming'
    }));
    textCharsRef.value = [..._textChars];

    try {
        const voice = localStorage.getItem('tts_voice') || 'Cherry';
        console.log('[悬浮窗] 调用 synthesize，参数:', { text长度: currentText.length, voice, engine, 有参考音频: !!referenceAudioFile });

        const audioBlob = await synthesize(currentText, voice, engine, referenceAudioFile);
        console.log('[悬浮窗] synthesize 返回，blob 大小:', audioBlob?.size);

        generating.value = false;
        audioGenerated.value = true;
        currentAudioBlob = audioBlob;
        
        if (referenceAudioFile) {
            window.electronAPI.clearReferenceAudio();
            console.log('[悬浮窗] 已清除参考音频缓存');
        }

        const actualDuration = await getAudioDuration(audioBlob);
        console.log('[悬浮窗] 音频实际时长:', actualDuration.toFixed(2) + '秒');

        let timestamps;
        try {
            // 直接使用 WhisperX 原始时间戳，不做整体偏移
            // WhisperX 对合成语音的对齐结果与 audio.currentTime 基本同步
            timestamps = await generateWhisperTimestamps(currentText, audioBlob, actualDuration);
        } catch (e) {
            console.warn('[播放] Whisper 对齐失败，使用平均分配：', e);
            timestamps = generateSimpleTimestamps(currentText, actualDuration);
        }

        _textChars = timestamps.map(t => ({ ...t, status: 'upcoming' }));
        textCharsRef.value = [..._textChars];

        setProgressCallback(updateHighlight);
        await playAudio(audioBlob, currentSpeed.value, actualDuration);
        console.log('[悬浮窗] 播放完成');
        playComplete.value = true;
        setTimeout(() => {
            if (playComplete.value) playComplete.value = false;
        }, 3000);

    } catch (err) {
        generating.value = false;
        console.error('[悬浮窗] 播放失败:', err);
    } finally {
        playing.value = false;
    }
};

// ========== 暂停 ==========
const pause = () => {
    pauseAudio();
    paused.value = true;
    // statusText computed 会自动显示"已暂停"
};

// ========== 继续播放 ==========
const resume = () => {
    resumeAudio();
    paused.value = false;
    // statusText computed 会自动回到"播放中"
};

// ========== 停止 ==========
const stop = () => {
    stopAudio();
    playing.value = false;
    paused.value = false;
    playComplete.value = false;
    stopped.value = true;          // 显示"已退出"
    setTimeout(() => {
        stopped.value = false;     // 3秒后自动消失
    }, 3000);
    progressTime.value = 0;
    progressDuration.value = 0;
    _currentIndex = -1;

    _textChars = currentText.split('').map(char => ({
        char,
        start: 0,
        end: 0,
        status: 'upcoming'
    }));
    textCharsRef.value = [..._textChars];
};

// ========== 下载音频 ==========
const downloadAudio = async () => {
    if (!currentAudioBlob || downloading.value) return;

    try {
        downloading.value = true;
        console.log('[悬浮窗] 开始下载音频，大小:', currentAudioBlob.size);

        const arrayBuffer = await currentAudioBlob.arrayBuffer();
        const result = await window.electronAPI.saveAudioFile(arrayBuffer, 'tts_output.wav');

        if (result.canceled) {
            console.log('[悬浮窗] 用户取消保存');
        } else if (result.success) {
            console.log('[悬浮窗] 音频已保存:', result.filePath);
        } else {
            console.error('[悬浮窗] 保存失败:', result.error);
        }
    } catch (err) {
        console.error('[悬浮窗] 下载失败:', err);
    } finally {
        downloading.value = false;
    }
};

// ========== 关闭悬浮窗 ==========
const closeWindow = async () => {
    stopAudio();
    await window.electronAPI.stopFloating();
};

// ========== 生命周期 ==========
onMounted(() => {
    loadSettings();
    console.log('[悬浮窗] 已启动');

    if (window.electronAPI?.onTTSSettingsUpdated) {
        window.electronAPI.onTTSSettingsUpdated((settings) => {
            console.log('[悬浮窗] 收到设置更新:', settings);

            // ===== Bug Fix：引擎或音色变更时清空音频缓存 =====
            // 防止切换模型后播放时仍使用旧引擎合成的缓存音频
            const prevEngine = localStorage.getItem('tts_engine');
            const prevVoice = localStorage.getItem('tts_voice');
            const engineChanged = settings.engine && settings.engine !== prevEngine;
            const voiceChanged = settings.voice && settings.voice !== prevVoice;
            if (engineChanged || voiceChanged) {
                currentAudioBlob = null;
                audioGenerated.value = false;
                console.log('[悬浮窗] 引擎/音色已变更，音频缓存已清空');
            }
            // ===== Bug Fix End =====

            if (settings.engine) localStorage.setItem('tts_engine', settings.engine);
            if (settings.voice) {
                localStorage.setItem('tts_voice', settings.voice);
                voiceName.value = settings.voice;
            }
            if (settings.speed !== undefined) {
                localStorage.setItem('tts_speed', settings.speed.toString());
                currentSpeed.value = settings.speed;
            }
        });
    }
});


onUnmounted(() => {
    stopAudio();
    if (window.electronAPI?.removeTTSSettingsUpdatedListener) {
        window.electronAPI.removeTTSSettingsUpdatedListener();
    }
});

</script>

<style scoped>
@import '../styles/floating-app.css';
</style>
