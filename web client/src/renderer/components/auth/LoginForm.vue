<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>屏幕文字捕获</h1>
        <p>请登录以继续使用</p>
      </div>
      
      <div class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            type="text" 
            v-model="username" 
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            type="password" 
            v-model="password" 
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="form-actions">
          <button class="btn-primary" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
          <button class="btn-link" @click="showRegister = true">没有账号？立即注册</button>
        </div>
        
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>
    </div>
    
    <!-- 注册弹窗 -->
    <RegisterForm 
      v-if="showRegister" 
      @close="showRegister = false" 
      @success="onRegisterSuccess" 
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import RegisterForm from './RegisterForm.vue';

const router = useRouter();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const loading = ref(false);
const errorMsg = ref('');
const showRegister = ref(false);

const handleLogin = async () => {
  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名';
    return;
  }
  if (!password.value) {
    errorMsg.value = '请输入密码';
    return;
  }
  
  loading.value = true;
  errorMsg.value = '';
  
  try {
    const res = await authStore.login(username.value.trim(), password.value);
    
    if (res.success) {
      // 登录成功，跳转到主页
      router.push('/');
    } else {
      errorMsg.value = res.error || '登录失败';
    }
  } catch (err) {
    errorMsg.value = '网络错误，请检查后端服务';
  } finally {
    loading.value = false;
  }
};

const onRegisterSuccess = () => {
  showRegister.value = false;
  // 注册成功后自动填充用户名
  // 可以扩展从注册组件获取用户名
};
</script>

<style scoped>
@import '../../styles/LoginForm.css';
</style>