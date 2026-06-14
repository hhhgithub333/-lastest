// 后端 API 地址（开发环境可配置环境变量）
const BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.37.85:8000';

/**
 * TTS 语音合成
 * @param {string} text - 要合成的文本
 * @param {string} voice - 音色代码
 * @param {string} engine - 模型名称（qwen, cosyvoice, indextts 等）
 * @param {File|null} referenceAudio - 参考音频文件（可选，部分模型需要）
 * @returns {Promise<Blob>} 音频 Blob 数据
 */
export async function synthesize(text, voice, engine, referenceAudio = null) {
    // 创建 FormData
    const formData = new FormData();
    formData.append('text', text);
    formData.append('voice', voice);
    formData.append('engine', engine);
    
    // 如果有参考音频，添加到表单中
    if (referenceAudio) {
        formData.append('reference_audio', referenceAudio);
        console.log('附加参考音频:', referenceAudio.name, referenceAudio.size, 'bytes');
    }
    
    const response = await fetch(`${BASE_URL}/tts/synthesize`, {
        method: 'POST',
        // 注意：FormData 不需要设置 Content-Type，浏览器会自动设置（包含 boundary）
        body: formData
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS 合成失败:', response.status, errorText);
        throw new Error(`TTS 合成失败: ${response.status} ${errorText}`);
    }
    
    // 返回音频 Blob
    return await response.blob();
}

/**
 * 获取后端支持的引擎列表（可选，用于动态加载）
 */
export async function getEngines() {
    const response = await fetch(`${BASE_URL}/tts/engines`);
    if (!response.ok) {
        throw new Error('获取引擎列表失败');
    }
    return await response.json();
}
