<template>
  <div class="status-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
      </div>
      <div class="header-text">
        <h1>权限状态</h1>
        <p>检查系统服务连接状态</p>
      </div>
    </div>

    <!-- 状态卡片列表 -->
    <div class="cards-container">
      <!-- 截图权限卡片 -->
      <div class="status-card" :class="{ connected: hasScreenCapture }">
        <div class="card-top">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <div class="status-indicator" :class="hasScreenCapture ? 'online' : 'offline'">
            <span class="dot"></span>
            {{ hasScreenCapture ? '已授权' : '未授权' }}
          </div>
        </div>
        <h3>截图权限</h3>
        <p>用于捕获屏幕上的文字，首次使用需要授权</p>
        <button 
          v-if="!hasScreenCapture" 
          @click="requestScreenCapture" 
          class="btn-action"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
          开启截图权限
        </button>
      </div>

      <!-- 后端服务卡片 -->
      <div class="status-card" :class="{ connected: backendConnected }">
        <div class="card-top">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="20" height="8" rx="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2"/>
              <line x1="6" y1="6" x2="6" y2="6"/>
              <line x1="6" y1="18" x2="6" y2="18"/>
            </svg>
          </div>
          <div class="status-indicator" :class="backendConnected ? 'online' : 'offline'">
            <span class="dot"></span>
            {{ backendConnected ? '已连接' : '未连接' }}
          </div>
        </div>
        <h3>后端服务</h3>
        <p class="server-url">{{ backendUrl }}</p>
        <button @click="checkBackend" class="btn-refresh" :class="{ loading: checkingBackend }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23,4 23,10 17,10"/>
            <polyline points="1,20 1,14 7,14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          {{ checkingBackend ? '检测中...' : '重新检测' }}
        </button>
      </div>
    </div>

    <!-- 提示信息 -->
    <div class="tips-section">
      <div class="tips-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span>使用提示</span>
      </div>
      <div class="tips-list">
        <div class="tip-item">
          <span class="tip-bullet">01</span>
          <span>截图权限：首次点击「捕获屏幕文字」时会自动弹出授权窗口</span>
        </div>
        <div class="tip-item">
          <span class="tip-bullet">02</span>
          <span>后端服务：请确保后端已启动</span>
        </div>
        <div class="tip-item">
          <span class="tip-bullet">03</span>
          <span>如遇问题，请检查防火墙是否允许 8000 端口</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 后端 API 地址
const backendUrl = import.meta.env.VITE_API_URL || 'http://192.168.37.85:8000';

// 状态
const hasScreenCapture = ref(false);
const backendConnected = ref(false);
const checkingBackend = ref(false);

// 检查截图权限
const checkScreenCapturePermission = async () => {
  try {
    if (typeof window.electronAPI !== 'undefined' && window.electronAPI.checkScreenCapturePermission) {
      const result = await window.electronAPI.checkScreenCapturePermission();
      hasScreenCapture.value = result.hasPermission;
    } else {
      // 开发环境没有 Electron API，模拟已授权
      hasScreenCapture.value = true;
    }
  } catch (err) {
    console.error('检查截图权限失败:', err);
    hasScreenCapture.value = false;
  }
};

// 请求截图权限
const requestScreenCapture = async () => {
  try {
    if (typeof window.electronAPI !== 'undefined' && window.electronAPI.captureScreen) {
      await window.electronAPI.captureScreen();
      // 授权后再次检查权限状态
      await checkScreenCapturePermission();
    } else {
      alert('请在 Electron 应用中运行此功能');
    }
  } catch (err) {
    console.error('截图权限请求失败:', err);
    hasScreenCapture.value = false;
  }
};

// 检查后端连接（使用 AbortController 实现超时）
const checkBackend = async () => {
  checkingBackend.value = true;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${backendUrl}/`, {
      method: 'GET',
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    backendConnected.value = response.ok;
  } catch (err) {
    console.error('后端连接失败:', err);
    backendConnected.value = false;
  } finally {
    checkingBackend.value = false;
  }
};

onMounted(() => {
  checkScreenCapturePermission();
  checkBackend();
});
</script>

<style scoped>
@import '../styles/Status.css';
</style>
