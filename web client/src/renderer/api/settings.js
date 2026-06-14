const BASE_URL = import.meta.env.VITE_API_URL || 'http://100.64.108.78:8000';

/**
 * 从后端获取用户设置
 * @param {string} username
 * @returns {Promise<{success: boolean, settings?: object, error?: string}>}
 */
export async function getSettings(username) {
    try {
        const response = await fetch(`${BASE_URL}/user/settings?username=${encodeURIComponent(username)}`);
        const data = await response.json();

        if (!response.ok) {
            return { success: false, error: data.detail || '获取设置失败' };
        }

        return {
            success: true,
            settings: {
                engine: data.engine || 'qwen',
                voice: data.voice || 'Cherry',
                speed: data.speed || 1.0,
                referenceAudioPath: data.reference_audio_path || null,
                capturedText: data.captured_text || ''
            }
        };
    } catch (err) {
        console.error('获取用户设置失败:', err);
        return { success: false, error: '网络错误' };
    }
}

/**
 * 保存用户设置到后端
 * @param {string} username
 * @param {object} settings - { engine, voice, speed, referenceAudioPath, capturedText }
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function saveSettings(username, settings) {
    try {
        const body = {
            engine: settings.engine,
            voice: settings.voice,
            speed: settings.speed,
            reference_audio_path: settings.referenceAudioPath || null,
            captured_text: settings.capturedText || ''
        };

        const response = await fetch(`${BASE_URL}/user/settings?username=${encodeURIComponent(username)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            return { success: false, error: data.detail || '保存设置失败' };
        }

        return { success: true };
    } catch (err) {
        console.error('保存用户设置失败:', err);
        return { success: false, error: '网络错误' };
    }
}
