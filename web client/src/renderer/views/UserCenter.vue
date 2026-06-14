<template>
  <div class="user-center">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div class="header-text">
        <h1>个人中心</h1>
        <p>管理账户信息</p>
      </div>
    </div>

    <!-- 用户信息卡片 -->
    <div class="profile-card">
      <div class="avatar-section">
        <div class="avatar">
          {{ avatarText }}
        </div>
        <div class="avatar-glow"></div>
      </div>
      <h2>{{ authStore.username || '用户' }}</h2>
      <span class="user-id">ID: {{ authStore.userId || '—' }}</span>
    </div>

    <!-- 信息列表 -->
    <div class="info-section">
      <div class="info-card">
        <div class="info-item">
          <div class="info-left">
            <div class="info-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="info-text">
              <span class="label">用户名</span>
              <span class="value">{{ authStore.username || '—' }}</span>
            </div>
          </div>
        </div>
        
        <div class="info-divider"></div>
        
        <div class="info-item">
          <div class="info-left">
            <div class="info-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <div class="info-text">
              <span class="label">注册时间</span>
              <span class="value">{{ formattedCreatedAt || '—' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 退出登录 -->
    <button class="logout-btn" @click="showLogoutConfirm = true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16,17 21,12 16,7"/>
        <line x1="21" y1="12" x2="9" y2="12"/>
      </svg>
      退出登录
    </button>

    <!-- 退出确认弹窗 -->
    <Teleport to="body">
      <div v-if="showLogoutConfirm" class="modal-overlay" @click.self="showLogoutConfirm = false">
        <div class="modal-content">
          <div class="modal-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16,17 21,12 16,7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </div>
          <h3>确认退出</h3>
          <p>确定要退出当前账户吗？</p>
          <div class="modal-actions">
            <button class="btn-cancel" @click="showLogoutConfirm = false">取消</button>
            <button class="btn-confirm" @click="handleLogout">确定退出</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const showLogoutConfirm = ref(false);

// 头像文字
const avatarText = computed(() => {
  const name = authStore.username;
  if (name && name.length > 0) {
    return name.charAt(0).toUpperCase();
  }
  return '👤';
});

// 格式化注册时间
const formattedCreatedAt = computed(() => {
  const date = authStore.createdAt;
  if (!date) return '';
  const match = date.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return `${match[1]}年${match[2]}月${match[3]}日`;
  }
  return date;
});

// 退出登录
const handleLogout = async () => {
  await authStore.logout();
  showLogoutConfirm.value = false;
  router.push('/');
};
</script>

<style scoped>
@import '../styles/UserCenter.css';
</style>
