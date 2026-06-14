const { app, BrowserWindow, ipcMain, desktopCapturer } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let floatingWindow = null;

// ========== 参考音频存储路径 ==========
let referenceAudioPath = null;  // 当前保存的参考音频路径

// ========== 获取参考音频目录 ==========
function getRefAudioDir() {
    const userDataPath = app.getPath('userData');
    const refAudioDir = path.join(userDataPath, 'reference_audio');
    if (!fs.existsSync(refAudioDir)) {
        fs.mkdirSync(refAudioDir, { recursive: true });
    }
    return refAudioDir;
}

// ========== 创建主窗口 ==========
function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 900,
        height: 700,
        webPreferences: {
            preload: path.join(__dirname, '../preload/preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        },
        title: '辅助阅读系统'
    });

    mainWindow.loadURL('http://localhost:5173');

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// ========== 创建悬浮窗 ==========
function createFloatingWindow() {
    if (floatingWindow !== null) {
        floatingWindow.focus();
        return;
    }

    floatingWindow = new BrowserWindow({
        width: 640,
        height: 260,
        x: 480,
        y: 680,
        transparent: true,
        alwaysOnTop: true,
        frame: false,
        skipTaskbar: false,
        resizable: false,
        focusable: true,
        webPreferences: {
            preload: path.join(__dirname, '../preload/preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // 设置最高置顶层级，确保悬浮在所有应用之上
    floatingWindow.setAlwaysOnTop(true, 'screen-saver');

    floatingWindow.loadURL('http://localhost:5173/floating.html');

    // 窗口失焦时重新置顶，防止被其他应用遮挡
    floatingWindow.on('focus-lost', () => {
        if (floatingWindow && !floatingWindow.isDestroyed()) {
            floatingWindow.setAlwaysOnTop(true, 'screen-saver');
            floatingWindow.moveTop();
        }
    });

    floatingWindow.on('closed', () => {
        if (mainWindow) {
            mainWindow.webContents.send('floating-closed');
        }
        floatingWindow = null;
    });
}

// ========== 关闭悬浮窗 ==========
function closeFloatingWindow() {
    if (floatingWindow) {
        floatingWindow.close();
    }
}

// ========== 检查截图权限 ==========
ipcMain.handle('check-screen-capture-permission', async () => {
    try {
        const sources = await desktopCapturer.getSources({
            types: ['screen'],
            thumbnailSize: { width: 1, height: 1 }  // 只需最小尺寸检测
        });
        // 有屏幕源说明权限正常
        return { hasPermission: sources.length > 0 };
    } catch (error) {
        console.error('检查截图权限失败:', error);
        return { hasPermission: false };
    }
});

// ========== 截图 API（支持区域选择）==========
ipcMain.handle('capture-screen', async () => {
    try {
        // 获取屏幕实际尺寸
        const { screen } = require('electron');
        const primaryDisplay = screen.getPrimaryDisplay();
        const { width: screenWidth, height: screenHeight } = primaryDisplay.size;
        
        console.log('屏幕实际尺寸:', screenWidth, 'x', screenHeight);
        
        // 获取屏幕截图（使用屏幕实际尺寸）
        const sources = await desktopCapturer.getSources({
            types: ['screen'],
            thumbnailSize: { width: screenWidth, height: screenHeight }
        });

        if (sources.length === 0) {
            console.error('没有找到屏幕源');
            return null;
        }

        const source = sources[0];
        const fullScreenshot = source.thumbnail;
        const imageSize = fullScreenshot.getSize();
        
        console.log('截图实际尺寸:', imageSize.width, 'x', imageSize.height);
        
        // 计算缩放比例（截图尺寸可能和屏幕尺寸不同）
        const scaleX = imageSize.width / screenWidth;
        const scaleY = imageSize.height / screenHeight;
        
        console.log('缩放比例:', scaleX, scaleY);
        
        const { BrowserWindow } = require('electron');
        
        // 创建全屏选择窗口
        const selectionWindow = new BrowserWindow({
            width: screenWidth,
            height: screenHeight,
            x: 0,
            y: 0,
            transparent: true,
            frame: false,
            alwaysOnTop: true,
            skipTaskbar: true,
            hasShadow: false,
            show: true,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false
            }
        });
        
        const imageDataURL = fullScreenshot.toDataURL();
        const htmlPath = path.join(__dirname, '../renderer/templates/screenshot.html');
        await selectionWindow.loadURL(`${htmlPath}?image=${encodeURIComponent(imageDataURL)}`);
        
        // 等待用户选择
        return new Promise((resolve) => {
            const onComplete = (event, { x, y, width: w, height: h }) => {
                console.log('收到选择完成事件:', { x, y, w, h });
                cleanup();
                try {
                    // 关键修复：将屏幕坐标转换为截图坐标
                    const cropX = Math.floor(x * scaleX);
                    const cropY = Math.floor(y * scaleY);
                    const cropW = Math.floor(w * scaleX);
                    const cropH = Math.floor(h * scaleY);
                    
                    console.log('裁剪坐标（换算后）:', { 
                        原始: { x, y, w, h },
                        缩放比例: { scaleX, scaleY },
                        裁剪: { cropX, cropY, cropW, cropH }
                    });
                    
                    // 确保裁剪区域在图片范围内
                    const finalX = Math.max(0, Math.min(cropX, imageSize.width - 1));
                    const finalY = Math.max(0, Math.min(cropY, imageSize.height - 1));
                    const finalW = Math.min(cropW, imageSize.width - finalX);
                    const finalH = Math.min(cropH, imageSize.height - finalY);
                    
                    console.log('最终裁剪区域:', { finalX, finalY, finalW, finalH });
                    
                    const cropped = fullScreenshot.crop({ 
                        x: finalX, 
                        y: finalY, 
                        width: finalW, 
                        height: finalH 
                    });
                    
                    const result = cropped.toDataURL();
                    console.log('裁剪完成，结果图片大小:', result.length);
                    resolve(result);
                } catch (err) {
                    console.error('裁剪失败:', err);
                    resolve(null);
                }
            };
            
            const onCancel = () => {
                console.log('用户取消选择');
                cleanup();
                resolve(null);
            };
            
            const cleanup = () => {
                ipcMain.removeListener('selection-complete', onComplete);
                ipcMain.removeListener('selection-cancel', onCancel);
                if (selectionWindow && !selectionWindow.isDestroyed()) {
                    selectionWindow.destroy();
                }
            };
            
            ipcMain.once('selection-complete', onComplete);
            ipcMain.once('selection-cancel', onCancel);
            
            // 设置超时
            setTimeout(() => {
                if (selectionWindow && !selectionWindow.isDestroyed()) {
                    console.log('截图超时（30秒），自动取消');
                    cleanup();
                    resolve(null);
                }
            }, 30000);
        });
        
    } catch (error) {
        console.error('截图失败:', error);
        return null;
    }
});

// ========== 控制悬浮窗显示/隐藏 ==========
ipcMain.handle('hide-floating-window', () => {
    if (floatingWindow && !floatingWindow.isDestroyed()) {
        floatingWindow.hide();
        console.log('悬浮窗已隐藏');
        return { success: true };
    }
    return { success: false };
});

ipcMain.handle('show-floating-window', () => {
    if (floatingWindow && !floatingWindow.isDestroyed()) {
        floatingWindow.show();
        console.log('悬浮窗已显示');
        return { success: true };
    }
    return { success: false };
});

// ========== 悬浮窗控制 API ==========
ipcMain.handle('start-floating', () => {
    createFloatingWindow();
    return { success: true };
});

ipcMain.handle('stop-floating', () => {
    closeFloatingWindow();
    return { success: true };
});

ipcMain.handle('is-floating-open', () => {
    return floatingWindow !== null;
});

// ========== 通信：悬浮窗 → 主窗口（发送捕获的文字） ==========
ipcMain.on('send-captured-text', (event, text) => {
    if (mainWindow) {
        mainWindow.webContents.send('update-captured-text', text);
    }
});

// ========== 主窗口 → 悬浮窗：同步 TTS 设置 ==========
ipcMain.on('sync-tts-settings', (event, settings) => {
    console.log('[主进程] 收到 TTS 设置同步:', settings);
    if (floatingWindow) {
        floatingWindow.webContents.send('tts-settings-updated', settings);
        console.log('[主进程] 已推送设置给悬浮窗');
    }
});

// ========== 新增：参考音频存储 API ==========

// 保存参考音频到磁盘
ipcMain.handle('save-reference-audio', async (event, { arrayBuffer, filename }) => {
    try {
        const refAudioDir = getRefAudioDir();
        const ext = path.extname(filename) || '.wav';
        const savePath = path.join(refAudioDir, `reference_audio${ext}`);

        // 将 ArrayBuffer 转为 Buffer 并写入文件
        const buffer = Buffer.from(arrayBuffer);
        fs.writeFileSync(savePath, buffer);

        referenceAudioPath = savePath;
        console.log('参考音频已保存:', savePath);

        return { success: true, path: savePath };
    } catch (error) {
        console.error('保存参考音频失败:', error);
        return { success: false, error: error.message };
    }
});

// 获取当前参考音频信息
ipcMain.handle('get-reference-audio', async () => {
    if (referenceAudioPath && fs.existsSync(referenceAudioPath)) {
        return {
            exists: true,
            path: referenceAudioPath,
            filename: path.basename(referenceAudioPath)
        };
    }
    return { exists: false };
});

// 清除参考音频
ipcMain.handle('clear-reference-audio', async () => {
    try {
        if (referenceAudioPath && fs.existsSync(referenceAudioPath)) {
            fs.unlinkSync(referenceAudioPath);
        }
        referenceAudioPath = null;
        console.log('参考音频已清除');
        return { success: true };
    } catch (error) {
        console.error('清除参考音频失败:', error);
        return { success: false, error: error.message };
    }
});

// ========== 应用生命周期 ==========
app.whenReady().then(() => {
    createMainWindow();
});

app.on('window-all-closed', () => {
    if (floatingWindow) {
        floatingWindow.close();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createMainWindow();
    }
});

// ========== 获取参考音频数据（通过 IPC 读取，避免 fetch file:// 限制）==========
// 支持多种音频格式，自动检测目录中的文件
ipcMain.handle('get-reference-audio-data', async () => {
    try {
        const fs = require('fs').promises;
        const path = require('path');
        const audioDir = path.join(app.getPath('userData'), 'reference_audio');
        
        // 读取目录，找到第一个音频文件
        const files = await fs.readdir(audioDir);
        const audioExts = ['.wav', '.mp3', '.flac', '.m4a', '.ogg'];
        const audioFile = files.find(f => audioExts.includes(path.extname(f).toLowerCase()));
        
        if (!audioFile) {
            console.log('参考音频目录中没有找到音频文件');
            return null;
        }
        
        const audioPath = path.join(audioDir, audioFile);
        const buffer = await fs.readFile(audioPath);
        const ext = path.extname(audioFile).toLowerCase();
        
        // 返回数据 + 扩展名，让前端知道真实格式
        return {
            data: new Uint8Array(buffer),
            filename: audioFile,
            extension: ext,
            mimeType: getMimeType(ext)
        };
    } catch (error) {
        console.error('读取参考音频失败:', error);
        return null;
    }
});

// 根据扩展名获取 MIME type
function getMimeType(ext) {
    const mimeTypes = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.flac': 'audio/flac',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg'
    };
    return mimeTypes[ext] || 'audio/wav';
}
// ========== 保存音频文件（用户选择路径）==========
ipcMain.handle('save-audio-file', async (event, { buffer, defaultFilename }) => {
    try {
        const { dialog } = require('electron');
        const fs = require('fs').promises;

        const result = await dialog.showSaveDialog({
            title: '保存音频文件',
            defaultPath: defaultFilename || 'tts_output.wav',
            filters: [
                { name: 'WAV 文件', extensions: ['wav'] },
                { name: 'MP3 文件', extensions: ['mp3'] },
                { name: '所有文件', extensions: ['*'] }
            ]
        });

        if (result.canceled || !result.filePath) {
            return { success: false, canceled: true };
        }

        await fs.writeFile(result.filePath, Buffer.from(buffer));
        console.log('[主进程] 音频已保存:', result.filePath);
        return { success: true, filePath: result.filePath };
    } catch (error) {
        console.error('[主进程] 保存音频失败:', error);
        return { success: false, error: error.message };
    }
});
