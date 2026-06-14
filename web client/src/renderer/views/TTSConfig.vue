<template>
  <div class="config-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      </div>
      <div class="header-text">
        <h1>TTS 设置</h1>
        <p>配置语音合成参数</p>
      </div>
    </div>

    <!-- TTS 模型选择 -->
    <div class="section-card">
      <h2 class="section-title">TTS 模型</h2>
      <div class="model-grid">
        <div
          v-for="(config, modelId) in MODEL_CONFIGS"
          :key="modelId"
          class="model-item"
          :class="{ active: currentModel === modelId, cloud: !config.isLocal, local: config.isLocal }"
          @click="selectModel(modelId)"
        >
          <div class="model-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="!config.isLocal" d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
              <path v-else d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            </svg>
          </div>
          <div class="model-info">
            <span class="model-name">{{ config.name }}</span>
            <span class="model-type">{{ config.isLocal ? '本地' : '云端' }}</span>
          </div>
          <div class="model-check" v-if="currentModel === modelId">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20,6 9,17 4,12"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 音色选择 -->
    <div class="section-card" v-if="currentVoices.length > 0">
      <h2 class="section-title">音色选择</h2>
      <div class="voice-grid">
        <div
          v-for="(voiceName, index) in currentVoiceNames"
          :key="index"
          class="voice-item"
          :class="{ active: currentVoice === currentVoices[index] }"
          @click="selectVoice(currentVoices[index])"
        >
          {{ voiceName }}
        </div>
      </div>
    </div>

    <!-- 参考音频上传（本地模型需要） -->
    <div class="section-card" v-if="needsReference">
      <h2 class="section-title">参考音频</h2>
      <p class="section-desc">上传人声音频提取音色特征</p>

      <div class="audio-upload-area">
        <input
          type="file"
          ref="audioInputRef"
          @change="onAudioFileChange"
          accept=".wav,.mp3,.ogg,.flac,audio/*"
          style="display: none;"
        />

        <div class="upload-zone" @click="triggerFileInput" :class="{ uploading }">
          <div class="upload-icon" v-if="!referenceAudioName">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="upload-icon success" v-else>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20,6 9,17 4,12"/>
            </svg>
          </div>
          <div class="upload-text" v-if="!uploading">
            <span v-if="referenceAudioName">{{ referenceAudioName }}</span>
            <span v-else>点击上传音频文件</span>
          </div>
          <div class="upload-text loading" v-else>
            正在保存...
          </div>
        </div>

        <button
          v-if="referenceAudioName"
          class="btn-clear"
          @click="handleClearReferenceAudio"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
          清除
        </button>
      </div>

      <div class="setting-hint tip">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        请上传 5-30 秒的人声音频，用于提取音色特征
      </div>

     
    </div>

    <!-- 播放设置 -->
    <div class="section-card">
      <h2 class="section-title">播放设置</h2>
      <div class="setting-row">
        <div class="setting-label">
          <span>播放速度</span>
          <code>{{ playbackSpeed }}x</code>
        </div>
        <div class="speed-slider">
          <button
            v-for="speed in SPEED_OPTIONS"
            :key="speed"
            class="speed-btn"
            :class="{ active: playbackSpeed === speed }"
            @click="setSpeed(speed)"
          >
            {{ speed }}x
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useTTSStore } from '../stores/tts';
import { useAuthStore } from '../stores/auth';
import { MODEL_CONFIGS, SPEED_OPTIONS, modelNeedsReference } from '../utils/constants';

const ttsStore = useTTSStore();
const authStore = useAuthStore();

const audioInputRef = ref(null);
const uploading = ref(false);

// 从 store 获取状态
const currentModel = computed(() => ttsStore.currentModel);
const currentVoice = computed(() => ttsStore.currentVoice);
const playbackSpeed = computed(() => ttsStore.speed);
const referenceAudioName = computed(() => ttsStore.referenceAudioName);
const needsReference = computed(() => modelNeedsReference(currentModel.value));

// 音色列表
const currentVoices = computed(() => MODEL_CONFIGS[currentModel.value]?.voices || []);
const currentVoiceNames = computed(() => MODEL_CONFIGS[currentModel.value]?.voiceNames || []);

// ========== 是否已登录 ==========
const isLoggedIn = computed(() => !!authStore.username);

// ========== 选择模型 ==========
const selectModel = (modelId) => {
  ttsStore.setModel(modelId);
  afterSettingChange();
};

// ========== 选择音色 ==========
const selectVoice = (voiceId) => {
  ttsStore.setVoice(voiceId);
  afterSettingChange();
};

// ========== 设置速度 ==========
const setSpeed = (speed) => {
  ttsStore.setSpeedValue(speed);
  afterSettingChange();
};

// ========== 设置变更后的统一处理 ==========
const afterSettingChange = () => {
  // 始终写 localStorage（供悬浮窗读取，未登录时也作为本地持久化）
  saveToLocalStorage();

  // 已登录时，同步保存到后端
  if (isLoggedIn.value) {
    authStore.saveCurrentSettings().catch(err => {
      console.warn('[TTSConfig] 保存用户设置到后端失败:', err);
    });
  }
};

// ========== 参考音频上传相关（IPC方式）==========

// 触发文件选择
const triggerFileInput = () => {
  audioInputRef.value?.click();
};

// 处理文件选择（正确的 IPC 上传逻辑）
const onAudioFileChange = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // 验证文件类型
  const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/flac'];
  const validExts = ['.wav', '.mp3', '.ogg', '.flac'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
    alert('不支持的音频格式，请上传 WAV、MP3、OGG 或 FLAC 格式');
    event.target.value = '';
    return;
  }

  uploading.value = true;
  try {
    // 读取文件为 ArrayBuffer
    const arrayBuffer = await file.arrayBuffer();

    // 通过 IPC 保存到主进程（磁盘）
    const result = await window.electronAPI.saveReferenceAudio(arrayBuffer, file.name);

    if (result.success) {
      // 保存到 store（仅文件名，用于 UI 显示）
      ttsStore.setReferenceAudioName(file.name);
      console.log('[TTSConfig] 参考音频已保存到:', result.path);

      // 已登录时同步保存到后端
      if (isLoggedIn.value) {
        authStore.saveCurrentSettings().catch(err => {
          console.warn('[TTSConfig] 保存参考音频设置到后端失败:', err);
        });
      }
    } else {
      alert('保存参考音频失败: ' + result.error);
    }
  } catch (err) {
    console.error('上传参考音频失败:', err);
    alert('上传失败: ' + err.message);
  } finally {
    uploading.value = false;
    event.target.value = '';  // 清空 input
  }
};

// 清除参考音频
const handleClearReferenceAudio = async () => {
  try {
    await window.electronAPI.clearReferenceAudio();
    ttsStore.clearReferenceAudioName();

    // 已登录时同步保存到后端
    if (isLoggedIn.value) {
      authStore.saveCurrentSettings().catch(err => {
        console.warn('[TTSConfig] 清除参考音频后保存设置到后端失败:', err);
      });
    }
  } catch (err) {
    console.error('清除参考音频失败:', err);
  }
};

// ========== localStorage 持久化（悬浮窗读取 + 未登录时本地持久化）==========

// 保存设置到 localStorage（供悬浮窗读取，未登录时作为本地持久化）
const saveToLocalStorage = () => {
  localStorage.setItem('tts_engine', currentModel.value);
  localStorage.setItem('tts_voice', currentVoice.value);
  localStorage.setItem('tts_speed', playbackSpeed.value.toString());
  console.log('[TTSConfig] 设置已保存到 localStorage');

  // 实时同步给悬浮窗
  if (window.electronAPI?.syncTTSSettings) {
    window.electronAPI.syncTTSSettings({
      engine: currentModel.value,
      voice: currentVoice.value,
      speed: playbackSpeed.value
    });
    console.log('[TTSConfig] 设置已推送给悬浮窗:', currentModel.value, currentVoice.value);
  }
};

// 从 localStorage 读取设置（仅未登录时使用）
const loadFromLocalStorage = () => {
  const savedEngine = localStorage.getItem('tts_engine');
  const savedVoice = localStorage.getItem('tts_voice');
  const savedSpeed = localStorage.getItem('tts_speed');

  if (savedEngine && MODEL_CONFIGS[savedEngine]) {
    ttsStore.setModel(savedEngine);
  }
  if (savedVoice) {
    ttsStore.setVoice(savedVoice);
  }
  if (savedSpeed) {
    const speedNum = parseFloat(savedSpeed);
    if (!isNaN(speedNum) && SPEED_OPTIONS.includes(speedNum)) {
      ttsStore.setSpeedValue(speedNum);
    }
  }
};

// ========== 初始化 ==========
onMounted(() => {
  if (isLoggedIn.value) {
    // 已登录：设置已由 auth.js 的 loadSettings() 从后端恢复，无需再读 localStorage
    console.log('[TTSConfig] 用户已登录，跳过 localStorage 加载，使用后端恢复的设置');
    // 同步一次给悬浮窗（确保悬浮窗拿到最新值）
    saveToLocalStorage();
  } else {
    // 未登录：从 localStorage 恢复（作为本地持久化）
    console.log('[TTSConfig] 用户未登录，从 localStorage 恢复设置');
    loadFromLocalStorage();
    saveToLocalStorage();
  }
});
</script>

<style scoped>
@import '../styles/TTSConfig.css';
</style>
