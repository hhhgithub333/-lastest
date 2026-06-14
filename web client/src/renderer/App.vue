<template>
  <div id="app">
    <!-- 登录页不显示导航栏 -->
    <template v-if="!isLoginPage">
      <!-- 导航栏 -->
      <nav class="navbar">
        <div class="nav-brand">阅读辅助系统</div>
        <div class="nav-links">
          <router-link to="/">主页</router-link>
          <router-link to="/tts">TTS设置</router-link>
          <router-link to="/status">权限状态</router-link>
          <router-link to="/tips">使用帮助</router-link>
          <router-link to="/user">个人中心</router-link>
        </div>
      </nav>
      
      <!-- 路由出口：所有页面组件渲染在这里 -->
      <div class="container">
        <router-view />
      </div>
    </template>
    
    <!-- 登录页直接显示 -->
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// 判断是否是登录页
const isLoginPage = computed(() => route.path === '/login');
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: rgba(0, 0, 0, 0.15);
}

.navbar {
  background: white;
  color: black;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  font-size: 18px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-links a {
  color: black;
  text-decoration: none;
  font-size: 14px;
}

.nav-links a:hover {
  color: #4CAF50;
}

.nav-links a.router-link-active {
  color: #4CAF50;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>