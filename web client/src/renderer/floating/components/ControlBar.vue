<template>
  <div class="controls">
    <!-- 捕获按钮 -->
    <button
      class="btn-capture"
      @click="$emit('capture')"
      :disabled="capturing"
      :class="{ loading: capturing }"
    >
      <div class="btn-inner">
        <svg v-if="!capturing" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <circle cx="12" cy="12" r="3"/>
          <path d="M3 9h2M19 9h2"/>
        </svg>
        <svg v-else class="icon spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
        </svg>
        <span>{{ capturing ? '识别中' : '捕获' }}</span>
      </div>
      <div class="btn-glow"></div>
    </button>

    <!-- 播放/暂停按钮 -->
    <button
      class="btn-play"
      @click="$emit('toggle-play')"
      :disabled="!hasText"
      :class="{ active: playing && !paused }"
    >
      <div class="btn-inner">
        <svg v-if="!playing || paused" class="icon" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5,3 19,12 5,21"/>
        </svg>
        <svg v-else class="icon" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16"/>
          <rect x="14" y="4" width="4" height="16"/>
        </svg>
        <span>{{ playing && !paused ? '暂停' : '播放' }}</span>
      </div>
      <div class="btn-glow"></div>
    </button>

    <!-- 停止按钮 -->
    <button
      class="btn-stop"
      @click="$emit('stop')"
      :disabled="!playing && !paused"
    >
      <div class="btn-inner">
        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="6" width="12" height="12" rx="1"/>
        </svg>
        <span>停止</span>
      </div>
      <div class="btn-glow"></div>
    </button>

    <!-- 下载按钮 -->
    <button
      class="btn-download"
      @click="$emit('download')"
      :disabled="!currentAudioBlob || downloading"
      :class="{ loading: downloading }"
    >
      <div class="btn-inner">
        <svg v-if="!downloading" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7,10 12,15 17,10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <svg v-else class="icon spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
        </svg>
        <span>{{ downloading ? '保存中' : '下载' }}</span>
      </div>
      <div class="btn-glow"></div>
    </button>

    <!-- 倍速选择 -->
    <div class="speed-selector">
      <button
        v-for="s in speedOptions"
        :key="s"
        :class="{ active: currentSpeed === s }"
        @click="$emit('set-speed', s)"
      >
        {{ s }}x
      </button>
    </div>
  </div>

  <!-- 参考音频提示 -->
  <div v-if="showRefTip" class="ref-tip">
    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    <button class="close-tip" @click="$emit('close-tip')">×</button>
  </div>
</template>

<script setup>
defineProps({
  capturing: { type: Boolean, default: false },
  playing: { type: Boolean, default: false },
  paused: { type: Boolean, default: false },
  hasText: { type: Boolean, default: false },
  currentSpeed: { type: Number, default: 1.0 },
  currentAudioBlob: { type: Object, default: null },
  showRefTip: { type: Boolean, default: false },
  downloading: { type: Boolean, default: false },
  speedOptions: { type: Array, default: () => [0.5, 0.75, 1.0, 1.5, 2.0] }
});

defineEmits(['capture', 'toggle-play', 'stop', 'download', 'set-speed', 'close-tip']);
</script>

<style scoped>
@import '../../styles/control-bar.css';
</style>
