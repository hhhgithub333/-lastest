const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('selectionAPI', {
    // 关闭选择器
    close: () => ipcRenderer.invoke('close-screen-selector'),
    
    // 确认选区
    confirmSelection: (x, y, width, height) => {
        return ipcRenderer.invoke('capture-selected-area', { x, y, width, height });
    }
});

console.log('selection-preload.js 已加载');