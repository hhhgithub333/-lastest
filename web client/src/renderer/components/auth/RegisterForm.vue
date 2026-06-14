<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>注册</h3>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label>用户名</label>
          <input 
            type="text" 
            v-model="username" 
            placeholder="请输入用户名"
            @keyup.enter="handleRegister"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            type="password" 
            v-model="password" 
            placeholder="请输入密码（至少6位）"
            @keyup.enter="handleRegister"
          />
        </div>
        
        <div class="form-group">
          <label>确认密码</label>
          <input 
            type="password" 
            v-model="confirmPassword" 
            placeholder="请再次输入密码"
            @keyup.enter="handleRegister"
          />
        </div>
        
        <div class="form-group">
          <label>邮箱（选填）</label>
          <input 
            type="email" 
            v-model="email" 
            placeholder="请输入邮箱"
          />
        </div>
        
        <div class="form-actions">
          <button class="btn-primary" @click="handleRegister" :disabled="loading">
            {{ loading ? '注册中...' : '注册' }}
          </button>
          <button class="btn-link" @click="$emit('close')">已有账号？去登录</button>
        </div>
        
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../../stores/auth';

const emit = defineEmits(['close', 'success']);
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const email = ref('');
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

const handleRegister = async () => {
  // 清空提示
  errorMsg.value = '';
  successMsg.value = '';
  
  // 验证用户名
  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名';
    return;
  }
  if (username.value.length < 3) {
    errorMsg.value = '用户名至少3个字符';
    return;
  }
  
  // 验证密码
  if (!password.value) {
    errorMsg.value = '请输入密码';
    return;
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码至少6个字符';
    return;
  }
  
  // 验证确认密码
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致';
    return;
  }
  
  loading.value = true;
  
  try {
    const res = await authStore.register(
      username.value.trim(), 
      password.value, 
      email.value.trim()
    );
    
    if (res.success) {
      successMsg.value = '注册成功！请登录';
      // 2秒后关闭弹窗
      setTimeout(() => {
        emit('close');
        emit('success');
      }, 1500);
    } else {
      errorMsg.value = res.error || '注册失败';
    }
  } catch (err) {
    errorMsg.value = '网络错误，请检查后端服务';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
@import '../../styles/RegisterForm.css';
</style>