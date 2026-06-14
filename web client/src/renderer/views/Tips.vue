<template>
  <div class="tips-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="header-text">
        <h1>使用帮助</h1>
        <p>快速上手指南</p>
      </div>
    </div>

    <!-- 步骤指南 -->
    <div class="steps-section">
      <div class="step-card" v-for="(step, index) in steps" :key="index">
        <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="step-content">
          <h3>{{ step.title }}</h3>
          <p>{{ step.desc }}</p>
          <code v-if="step.code">{{ step.code }}</code>
        </div>
      </div>
    </div>

    <!-- 常见问题 -->
    <div class="faq-section">
      <div class="faq-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span>常见问题</span>
      </div>

      <div class="faq-list">
        <div class="faq-item" v-for="(faq, index) in faqs" :key="index">
          <div class="faq-question">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            {{ faq.q }}
          </div>
          <div class="faq-answer">{{ faq.a }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const steps = [
  {
    title: '开启权限',
    desc: '首次使用需要开启截图权限。点击主页的「捕获屏幕文字」按钮，浏览器会弹出授权窗口，选择要分享的屏幕即可。',
  },
  {
    title: '启动后端服务',
    desc: 'TTS 合成需要后端服务支持。请确保后端已启动：',
    code: 'uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
  },
  {
    title: '选择模型和音色',
    desc: '在「TTS设置」页面，可以选择不同的语音模型和音色。云端模型（千问、CosyVoice、Sambert）响应最快，本地模型需要后端支持。',
  },
  {
    title: '捕获屏幕文字',
    desc: '点击「捕获屏幕文字」按钮，选择要识别的屏幕区域，系统会自动识别文字并朗读。',
  },
  {
    title: '调整播放速度',
    desc: '在「TTS设置」页面可以调整播放速度，支持 0.5x 到 2.0x 多档速度。',
  }
];

const faqs = [
  {
    q: '截图后识别出的文字是乱码怎么办？',
    a: '请确保截图区域文字清晰、大小适中。建议选择纯文本区域，避免截图包含过多图标或图片。'
  },
  {
    q: '点击朗读没有声音？',
    a: '请检查「权限状态」页面，确认后端服务已连接。如果后端未启动，请运行 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
  },
  {
    q: '本地模型生成很慢？',
    a: '本地模型（XTTS-v2、VoxCPM、ChatterBox、VibeVoice）需要加载模型到内存，首次使用较慢。建议优先使用云端模型（千问、CosyVoice、Sambert）。'
  },
  {
    q: '如何更新后端 IP 地址？',
    a: '如果后端 IP 变化，可以修改项目根目录的 .env 文件，设置 VITE_API_URL=http://新IP:8000，然后重新构建。'
  }
];
</script>

<style scoped>
@import '../styles/Tips.css';
</style>
