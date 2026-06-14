let currentAudio = null;
let progressCallback = null;  // 进度回调
let rafHandle = null;          // requestAnimationFrame 句柄（替代 setInterval）
let audioUrl = null;           // Blob URL（需要保留用于 seek）


/**
 * 生成简单时间戳（平均分配）
 * 用于前端逐字/逐词高亮
 * @param {string} text - 文本
 * @param {number} duration - 音频总时长（秒）
 * @param {number} charDuration - 每个字符平均时长（秒），默认 0.3
 * @returns {Array} [{char, start, end}, ...]
 */
export function generateSimpleTimestamps(text, duration = 3, charDuration = 0.3) {
    const chars = text.split('');
    const totalChars = chars.length;
    const estimatedDuration = totalChars * charDuration;
    const scale = duration / Math.max(estimatedDuration, 1);

    const timestamps = [];
    let currentTime = 0;

    for (const char of chars) {
        const charLen = char.trim() === '' ? charDuration * 0.36 : charDuration;  // 空格短一点
        const endTime = currentTime + charLen * scale;
        timestamps.push({
            char,
            start: currentTime,
            end: endTime
        });
        currentTime = endTime;
    }

    return timestamps;
}

/**
 * 设置进度回调
 * @param {Function} callback - 回调函数，接收 { currentTime, duration } 参数
 */
export function setProgressCallback(callback) {
    progressCallback = callback;
}

/**
 * 清除进度跟踪
 */
function clearProgressTracking() {
    if (rafHandle !== null) {
        cancelAnimationFrame(rafHandle);
        rafHandle = null;
    }
    progressCallback = null;
}

/**
 * 开始进度跟踪（用 requestAnimationFrame 替代 setInterval）
 * rAF 在 Electron 渲染进程中不会被节流，每帧约 16ms，远优于 setInterval
 */
function startProgressTracking() {
    if (!currentAudio) return;

    // 先取消已有的 rAF 循环，防止重叠
    if (rafHandle !== null) {
        cancelAnimationFrame(rafHandle);
        rafHandle = null;
    }

    function tick() {
        if (currentAudio && !currentAudio.paused && progressCallback) {
            progressCallback({
                currentTime: currentAudio.currentTime,
                duration: currentAudio.duration || 0
            });
        }
        // 只要音频还在播放就继续循环
        if (currentAudio && !currentAudio.paused) {
            rafHandle = requestAnimationFrame(tick);
        } else {
            rafHandle = null;
        }
    }

    rafHandle = requestAnimationFrame(tick);
}

/**
 * 设置播放倍速
 * @param {number} speed - 倍速值（0.5 - 2.0）
 */
export function setSpeed(speed) {
    if (currentAudio) {
        currentAudio.playbackRate = speed;
        console.log(`[音频] 倍速已调整为: ${speed}x`);
    }
}

/**
 * 跳转到指定时间（秒）
 * @param {number} time - 目标时间（秒）
 */
export function seekTo(time) {
    if (currentAudio) {
        currentAudio.currentTime = time;
        console.log(`[音频] 跳转至: ${time.toFixed(2)}s`);
    }
}

/**
 * 获取当前音频总时长
 * @returns {number} 时长（秒）
 */
export function getDuration() {
    return currentAudio ? (currentAudio.duration || 0) : 0;
}

/**
 * 获取当前播放时间
 * @returns {number} 当前时间（秒）
 */
export function getCurrentTime() {
    return currentAudio ? currentAudio.currentTime : 0;
}

/**
 * 播放音频
 * @param {Blob} audioBlob - 音频数据
 * @param {number} speed - 播放倍速
 * @param {number} duration - 音频时长（秒），用于计算时间戳
 * @returns {Promise} 播放完成时 resolve
 */
export async function playAudio(audioBlob, speed = 1.0, duration = 3) {
    // 先清理旧的
    stopAudio();

    audioUrl = URL.createObjectURL(audioBlob);
    currentAudio = new Audio(audioUrl);
    currentAudio.playbackRate = speed;

    if (duration <= 0) duration = 3;

    return new Promise((resolve, reject) => {
        currentAudio.onended = () => {
            cleanup();
            if (progressCallback) progressCallback({ currentTime: -1, duration });
            console.log('[音频] 播放完成');
            resolve();
        };

        currentAudio.onerror = (err) => {
            cleanup();
            console.error('[音频] 播放错误:', err);
            reject(new Error('音频播放失败'));
        };

        currentAudio.oncanplay = () => {
            // 音频可以播放时触发
            console.log('[音频] 音频已就绪');
        };

        // 暂停时停止 rAF 循环，恢复时重新启动（避免后台空转）
        currentAudio.onpause = () => {
            if (rafHandle !== null) {
                cancelAnimationFrame(rafHandle);
                rafHandle = null;
            }
        };

        currentAudio.onplay = () => {
            startProgressTracking();
        };

        currentAudio.play().then(() => {
            startProgressTracking();
        }).catch((err) => {
            cleanup();
            reject(err);
        });
    });
}

/**
 * 清理资源
 */
function cleanup() {
    if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        audioUrl = null;
    }
    currentAudio = null;
    clearProgressTracking();
}

/**
 * 停止播放
 */
export function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        cleanup();
        console.log('[音频] 播放已停止');
    }
}

/**
 * 暂停播放
 */
export function pauseAudio() {
    if (currentAudio) {
        currentAudio.pause();
        console.log('[音频] 播放已暂停');
    }
}

/**
 * 恢复播放
 */
export function resumeAudio() {
    if (currentAudio) {
        currentAudio.play().then(() => {
            startProgressTracking();
        });
        console.log('[音频] 播放已恢复');
    }
}

/**
 * 检查是否正在播放
 * @returns {boolean}
 */
export function isPlaying() {
    return currentAudio !== null && !currentAudio.paused;
}
