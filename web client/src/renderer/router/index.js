import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// 路由配置：路径 → 组件
const routes = [
  {
  path: '/login',
  name: 'Login',
  component: () => import('../components/auth/LoginForm.vue')
  },

  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }  // 需要登录才能访问
  },
  {
    path: '/tts',
    name: 'TTSConfig',
    component: () => import('../views/TTSConfig.vue'),
    meta: { requiresAuth: true }  // 需要登录才能访问
  },
  {
    path: '/status',
    name: 'Status',
    component: () => import('../views/Status.vue'),
    meta: { requiresAuth: true }  // 需要登录才能访问
  },
  {
    path: '/tips',
    name: 'Tips',
    component: () => import('../views/Tips.vue'),
    meta: { requiresAuth: true }  // 需要登录才能访问
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('../views/UserCenter.vue'),
    meta: { requiresAuth: true }  // 需要登录才能访问
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),  // 使用 HTML5 历史模式
  routes
});

// 导航守卫：检查是否需要登录
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  // 如果目标页面需要登录
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      // 未登录，跳转到登录页
      next('/login');
    } else {
      // 已登录，允许访问
      next();
    }
  } 
  // 如果在登录页且已有 token，直接跳主页
  else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/');
  }
  else {
    next();
  }
});

export default router;