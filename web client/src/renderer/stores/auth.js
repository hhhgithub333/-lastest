import { defineStore } from 'pinia';
import { ref, computed, nextTick } from 'vue';
import { login as apiLogin, register as apiRegister, logout as apiLogout } from '../api/auth';
import { getSettings, saveSettings } from '../api/settings';
import { useTTSStore } from './tts';

export const useAuthStore = defineStore('auth', () => {
    // ========== 状态 ==========
    const token = ref(localStorage.getItem('token') || null);
    const username = ref(localStorage.getItem('username') || null);
    const userId = ref(parseInt(localStorage.getItem('userId') || '0') || null);
    const createdAt = ref(localStorage.getItem('createdAt') || null);

    // ========== 计算属性 ==========
    const isLoggedIn = computed(() => !!token.value);

    // ========== 操作方法 ==========
    const login = async (usernameVal, passwordVal) => {
        const res = await apiLogin(usernameVal, passwordVal);

        if (res.success) {
            token.value = res.token;
            username.value = res.username;
            userId.value = res.userId;
            createdAt.value = res.createdAt;

            localStorage.setItem('token', res.token);
            localStorage.setItem('username', res.username);
            localStorage.setItem('userId', String(res.userId));
            localStorage.setItem('createdAt', res.createdAt);

            // 登录成功后，从后端恢复用户设置
            await loadSettings(usernameVal);
        }

        return res;
    };

    const register = async (usernameVal, passwordVal, emailVal = '') => {
        return await apiRegister(usernameVal, passwordVal, emailVal);
    };

    /**
     * 用户登出
     */
    const logout = async () => {
        // 登出前，将当前 TTS 设置保存到后端
        await saveCurrentSettings();

        await apiLogout();

        token.value = null;
        username.value = null;
        userId.value = null;
        createdAt.value = null;

        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
        localStorage.removeItem('createdAt');
    };

    /**
     * 从后端加载用户设置，覆盖到 TTSStore
     */
    const loadSettings = async (usernameVal) => {
        const res = await getSettings(usernameVal);
        if (!res.success || !res.settings) return;

        const tts = useTTSStore();
        tts.setModel(res.settings.engine);
        tts.setVoice(res.settings.voice);
        tts.setSpeedValue(res.settings.speed);
        if (res.settings.capturedText) {
            tts.setCapturedText(res.settings.capturedText);
        }

        console.log('[Auth] 已恢复用户设置:', res.settings);
    };

    /**
     * 将当前 TTSStore 状态保存到后端
     */
    const saveCurrentSettings = async () => {
        const tts = useTTSStore();
        const settings = {
            engine: tts.currentModel,
            voice: tts.currentVoice,
            speed: tts.speed,
            referenceAudioPath: tts.referenceAudioName || null,
            capturedText: tts.capturedText || ''
        };

        await saveSettings(username.value, settings);
        console.log('[Auth] 已保存用户设置:', settings);
    };

    // ========== 初始化：若已登录，恢复用户设置 ==========
    // 放在所有函数定义之后，避免引用错误
    if (username.value) {
        nextTick(() => {
            loadSettings(username.value).catch(err => {
                console.warn('[Auth] 初始化恢复设置失败:', err);
            });
        });
    }

    return {
        token,
        username,
        userId,
        createdAt,
        isLoggedIn,
        login,
        register,
        logout,
        loadSettings,
        saveCurrentSettings
    };
});
