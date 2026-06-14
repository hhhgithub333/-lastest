<template>
  <div class="home">
    <!-- 顶部导航 -->
    <nav class="nav">
      <div class="nav-brand">
        <div class="nav-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <circle cx="12" cy="12" r="3"/>
            <path d="M3 9h2M19 9h2"/>
          </svg>
        </div>
        <span class="nav-title">屏幕文字捕获</span>
      </div>
      <div class="nav-status" :class="{ active: isFloatingOpen }">
        <span class="status-dot"></span>
        <span>{{ isFloatingOpen ? '服务运行中' : '服务已停止' }}</span>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 服务卡片 -->
      <section class="card service-card">
        <div class="card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <div class="card-content">
          <h2>悬浮窗服务</h2>
          <p>捕获屏幕文字，即时转换为语音播放</p>
        </div>
        <div class="card-actions">
          <button class="btn btn-primary" @click="startService" :disabled="isFloatingOpen">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5,3 19,12 5,21"/>
            </svg>
            启动
          </button>
          <button class="btn btn-secondary" @click="stopService" :disabled="!isFloatingOpen">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="6" width="12" height="12" rx="1"/>
            </svg>
            停止
          </button>
        </div>
      </section>

      <!-- 捕获内容卡片 -->
      <section class="card content-card" v-if="ttsStore.capturedText">
        <div class="card-header">
          <div class="header-left">
            <div class="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <div>
              <h3>捕获内容</h3>
              <span class="char-badge">{{ ttsStore.capturedText.length }} 字</span>
            </div>
          </div>
        </div>
        
        <div class="text-preview">
          <p>{{ ttsStore.capturedText }}</p>
        </div>

        <div class="content-footer">
          <span class="hint">使用悬浮窗播放或下载音频</span>
        </div>
      </section>

      <!-- 空状态 -->
      <section class="card empty-card" v-else>
        <div class="empty-illustration">
          <svg viewBox="0 0 120 100" fill="none">
            <rect x="20" y="10" width="80" height="60" rx="8" stroke="currentColor" stroke-width="2" stroke-dasharray="4 4"/>
            <circle cx="60" cy="40" r="12" stroke="currentColor" stroke-width="2"/>
            <path d="M30 80 L60 60 L90 80" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3>开始捕获</h3>
        <p>点击上方「启动」按钮开启悬浮窗</p>
        <span class="tip">悬浮窗将浮于屏幕边缘，点击捕获按钮即可识别屏幕文字</span>
      </section>
    </main>

    <!-- 底部信息 -->
    <footer class="footer">
      <span>TTS 语音合成 · {{ currentEngine }}</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useTTSStore } from '../stores/tts';

const ttsStore = useTTSStore();

const isFloatingOpen = ref(false);

const currentEngine = computed(() => {
  const engine = localStorage.getItem('tts_engine') || 'qwen';
  const names = {
    'qwen': 'Qwen 云端',
    'cosyvoice': 'CosyVoice 云端',
    'sambert': 'Sambert 云端',
    'chatterbox': 'ChatterBox 本地',
    'indextts': 'IndexTTS 本地',
    'vibevoice': 'VibeVoice 本地',
    'xtts_v2': 'XTTS-v2 本地',
    'voxcpm': 'VoxCPM 本地'
  };
  return names[engine] || engine;
});

// ========== 启动服务 ==========
const startService = async () => {
  try {
    const result = await window.electronAPI.startFloating();
    if (result.success) {
      isFloatingOpen.value = true;
    }
  } catch (err) {
    console.error('启动服务失败:', err);
  }
};

// ========== 停止服务 ==========
const stopService = async () => {
  try {
    const result = await window.electronAPI.stopFloating();
    if (result.success) {
      isFloatingOpen.value = false;
    }
  } catch (err) {
    console.error('停止服务失败:', err);
  }
};

// ========== 检查悬浮窗状态 ==========
const checkFloatingStatus = async () => {
  try {
    const isOpen = await window.electronAPI.isFloatingOpen();
    isFloatingOpen.value = isOpen;
  } catch (err) {
    console.error('检查悬浮窗状态失败:', err);
  }
};

// ========== 监听悬浮窗发来的文字 ==========
const onUpdateCapturedText = (text) => {
  ttsStore.setCapturedText(text);
};

// ========== 监听悬浮窗关闭 ==========
const onFloatingClosed = () => {
  isFloatingOpen.value = false;
};

// ========== 生命周期 ==========
onMounted(() => {
  checkFloatingStatus();
  window.electronAPI.onUpdateCapturedText(onUpdateCapturedText);
  window.electronAPI.onFloatingClosed(onFloatingClosed);
});

onUnmounted(() => {
  if (window.electronAPI.removeUpdateCapturedTextListener) {
    window.electronAPI.removeUpdateCapturedTextListener();
  }
  if (window.electronAPI.removeFloatingClosedListener) {
    window.electronAPI.removeFloatingClosedListener();
  }
});
</script>

<style scoped>
@import '../styles/Home.css';
</style>
