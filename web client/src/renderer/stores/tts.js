import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { MODEL_CONFIGS, modelNeedsReference } from '../utils/constants';
import { synthesize } from '../api/tts';
import { playAudio, setSpeed as setAudioSpeed, stopAudio, pauseAudio, resumeAudio } from '../utils/audio';

export const useTTSStore = defineStore('tts', () => {
    // ========== 状态 ==========
    const currentModel = ref('qwen');
    const currentVoice = ref('Cherry');
    const speed = ref(1.0);
    const isPlaying = ref(false);
    const isPaused = ref(false);

    // ========== 捕获的文字（持久化）==========
    const capturedText = ref('');

    // ========== 参考音频状态（仅存储文件名，文件存在磁盘）==========
    const referenceAudioName = ref('');    // 文件名（用于 UI 显示）

    // ========== 音频缓存 ==========
    const audioCache = ref(new Map());  // key: "引擎|音色|文字", value: { audioBlob, timestamp }
    const CACHE_MAX_SIZE = 10;         // 最多缓存 10 条
    const CACHE_EXPIRE_TIME = 30 * 60 * 1000;  // 30 分钟过期

    // ========== 生成缓存 key ==========
    const getCacheKey = (text, voice, engine) => {
        const shortText = text.length > 100 ? text.substring(0, 100) : text;
        return `${engine}|${voice}|${shortText}`;
    };

    // ========== 清理过期缓存 ==========
    const cleanExpiredCache = () => {
        const now = Date.now();
        for (const [key, value] of audioCache.value.entries()) {
            if (now - value.timestamp > CACHE_EXPIRE_TIME) {
                audioCache.value.delete(key);
            }
        }
    };

    // ========== 添加缓存 ==========
    const addToCache = (key, audioBlob) => {
        if (audioCache.value.size >= CACHE_MAX_SIZE) {
            const oldestKey = audioCache.value.keys().next().value;
            audioCache.value.delete(oldestKey);
        }
        audioCache.value.set(key, {
            audioBlob,
            timestamp: Date.now()
        });
    };

    // ========== 从缓存获取 ==========
    const getFromCache = (key) => {
        const cached = audioCache.value.get(key);
        if (cached) {
            if (Date.now() - cached.timestamp < CACHE_EXPIRE_TIME) {
                return cached.audioBlob;
            } else {
                audioCache.value.delete(key);
            }
        }
        return null;
    };

    // ========== 清空缓存 ==========
    const clearCache = () => {
        audioCache.value.clear();
    };

    // ========== 合成并播放 ==========
    const speak = async (text, referenceAudio = null) => {
        if (!text || text.trim().length === 0) {
            console.warn('没有可朗读的文字');
            return;
        }

        cleanExpiredCache();
        const cacheKey = getCacheKey(text, currentVoice.value, currentModel.value);

        let audioBlob = null;
        if (!referenceAudio) {
            audioBlob = getFromCache(cacheKey);
        }

        if (audioBlob) {
            console.log('使用缓存的音频');
        } else {
            try {
                audioBlob = await synthesize(
                    text,
                    currentVoice.value,
                    currentModel.value,
                    referenceAudio
                );
                if (!referenceAudio) {
                    addToCache(cacheKey, audioBlob);
                }
            } catch (err) {
                console.error('TTS 合成失败:', err);
                throw err;
            }
        }

        try {
            isPlaying.value = true;
            await playAudio(audioBlob, speed.value);
        } catch (err) {
            console.error('播放失败:', err);
            throw err;
        } finally {
            isPlaying.value = false;
        }
    };

    // ========== 计算属性 ==========
    const models = computed(() => MODEL_CONFIGS);

    const currentVoices = computed(() => {
        return MODEL_CONFIGS[currentModel.value]?.voices || [];
    });

    const currentVoiceNames = computed(() => {
        return MODEL_CONFIGS[currentModel.value]?.voiceNames || [];
    });

    const needsReferenceAudio = computed(() => {
        return modelNeedsReference(currentModel.value);
    });

    // ========== 操作方法 ==========
    const setModel = (modelName) => {
        currentModel.value = modelName;
        const voices = MODEL_CONFIGS[modelName]?.voices || [];
        if (voices.length > 0) {
            currentVoice.value = voices[0];
        }
    };

    const setVoice = (voice) => {
        currentVoice.value = voice;
    };

    const setSpeedValue = (newSpeed) => {
        speed.value = newSpeed;
        setAudioSpeed(newSpeed);
    };

    const stop = () => {
        stopAudio();
        isPlaying.value = false;
        isPaused.value = false;
    };

    const pause = () => {
        pauseAudio();
        isPaused.value = true;
    };

    const resume = () => {
        resumeAudio();
        isPaused.value = false;
    };

    // ========== 捕获文字相关 ==========
    const setCapturedText = (text) => {
        capturedText.value = text;
    };

    const clearCapturedText = () => {
        capturedText.value = '';
    };

    // ========== 参考音频相关（仅存储文件名）==========
    const setReferenceAudioName = (name) => {
        referenceAudioName.value = name;
        console.log('参考音频文件名已设置:', name);
    };

    const clearReferenceAudioName = () => {
        referenceAudioName.value = '';
        console.log('参考音频文件名已清除');
    };

    // 兼容旧方法（如果其他地方用到）
    const setReferenceAudio = (file) => {
        if (file) {
            referenceAudioName.value = file.name;
        }
    };

    const clearReferenceAudio = () => {
        referenceAudioName.value = '';
    };

    return {
        // 状态
        currentModel,
        currentVoice,
        speed,
        isPlaying,
        isPaused,
        capturedText,
        referenceAudioName,
        needsReferenceAudio,
        // 计算属性
        models,
        currentVoices,
        currentVoiceNames,
        // 方法
        setModel,
        setVoice,
        setSpeedValue,
        speak,
        stop,
        pause,
        resume,
        clearCache,
        setCapturedText,
        clearCapturedText,
        setReferenceAudioName,
        clearReferenceAudioName,
        setReferenceAudio,
        clearReferenceAudio
    };
});

