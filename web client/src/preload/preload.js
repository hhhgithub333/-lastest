const { contextBridge, ipcRenderer } = require('electron');

// 通过 contextBridge 安全地暴露 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
    // ========== 检查截图权限 ==========
    checkScreenCapturePermission: () => ipcRenderer.invoke('check-screen-capture-permission'),

    // ========== 悬浮窗控制 ==========
    hideFloatingWindow: () => ipcRenderer.invoke('hide-floating-window'),
    showFloatingWindow: () => ipcRenderer.invoke('show-floating-window'),

    // ========== 截图 ==========
    captureScreen: () => ipcRenderer.invoke('capture-screen'),

    // ========== 悬浮窗控制 ==========
    startFloating: () => ipcRenderer.invoke('start-floating'),
    stopFloating: () => ipcRenderer.invoke('stop-floating'),
    isFloatingOpen: () => ipcRenderer.invoke('is-floating-open'),

    // ========== 悬浮窗 → 主窗口：发送捕获的文字 ==========
    sendCapturedText: (text) => ipcRenderer.send('send-captured-text', text),

    // ========== 主窗口 ← 悬浮窗：监听捕获的文字 ==========
    onUpdateCapturedText: (callback) => {
        ipcRenderer.on('update-captured-text', (event, text) => callback(text));
    },

    // ========== 音频下载 ==========
    saveAudioFile: (buffer, defaultFilename) => {
        return ipcRenderer.invoke('save-audio-file', { buffer, defaultFilename });
    },

    // ========== 悬浮窗关闭通知 ==========
    onFloatingClosed: (callback) => {
        ipcRenderer.on('floating-closed', () => callback());
    },

    // ========== 移除监听（可选） ==========
    removeUpdateCapturedTextListener: () => {
        ipcRenderer.removeAllListeners('update-captured-text');
    },
    removeFloatingClosedListener: () => {
        ipcRenderer.removeAllListeners('floating-closed');
    },

    // ========== 参考音频 IPC ==========

    /**
     * 保存参考音频到磁盘（供悬浮窗共享）
     * @param {ArrayBuffer} arrayBuffer - 文件的 ArrayBuffer 数据
     * @param {string} filename - 原始文件名
     */
    saveReferenceAudio: (arrayBuffer, filename) => {
        return ipcRenderer.invoke('save-reference-audio', { arrayBuffer, filename });
    },

    /**
     * 获取当前参考音频信息
     * @returns {{ exists: boolean, path?: string, filename?: string }}
     */
    getReferenceAudio: () => {
        return ipcRenderer.invoke('get-reference-audio');
    },

    /**
     * 获取参考音频的二进制数据（通过 IPC，避免 fetch file:// 限制）
     * @returns {ArrayBuffer} 文件的二进制数据
     */
    getReferenceAudioData: () => {
        return ipcRenderer.invoke('get-reference-audio-data');
    },

     /**
     * 主窗口 → 悬浮窗：推送最新 TTS 设置
     * @param {{ engine: string, voice: string, speed: number }} settings
     */
    syncTTSSettings: (settings) => {
        ipcRenderer.send('sync-tts-settings', settings);
    },

    /**
     * 悬浮窗监听：主窗口推送的 TTS 设置变更
     * @param {function} callback - 收到设置时的回调，参数为 { engine, voice, speed }
     */
    onTTSSettingsUpdated: (callback) => {
        ipcRenderer.on('tts-settings-updated', (event, settings) => callback(settings));
    },

    removeTTSSettingsUpdatedListener: () => {
        ipcRenderer.removeAllListeners('tts-settings-updated');
    },


    /**
     * 清除参考音频
     */
    clearReferenceAudio: () => {
        return ipcRenderer.invoke('clear-reference-audio');
    }
});

console.log('preload.js 已加载');


