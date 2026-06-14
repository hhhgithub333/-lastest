// 后端 API 地址
const BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.37.85:8000';

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<{success: boolean, token?: string, username?: string, userId?: number, createdAt?: string, error?: string}>}
 */
export async function login(username, password) {
    try {
        const response = await fetch(`${BASE_URL}/user/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            return {
                success: false,
                error: data.detail || '登录失败'
            };
        }
        
        return {
            success: true,
            token: data.access_token,
            username: data.user.username,
            userId: data.user.id,
            createdAt: data.user.created_at
        };
    } catch (err) {
        console.error('登录请求失败:', err);
        return {
            success: false,
            error: '网络错误，请检查后端服务是否启动'
        };
    }
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} email - 邮箱（可选）
 * @returns {Promise<{success: boolean, userId?: number, username?: string, error?: string}>}
 */
export async function register(username, password, email = '') {
    try {
        const body = { username, password };
        if (email && email.trim()) {
            body.email = email.trim();
        }
        
        const response = await fetch(`${BASE_URL}/user/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            return {
                success: false,
                error: data.detail || '注册失败'
            };
        }
        
        return {
            success: true,
            userId: data.id,
            username: data.username
        };
    } catch (err) {
        console.error('注册请求失败:', err);
        return {
            success: false,
            error: '网络错误，请检查后端服务是否启动'
        };
    }
}

/**
 * 用户登出（前端清除本地状态即可，后端无状态）
 */
export async function logout() {
    // 后端使用 JWT 无状态认证，登出只需前端清除 token
    return { success: true };
}