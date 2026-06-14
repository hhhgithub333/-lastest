import Tesseract from 'tesseract.js';

/**
 * 截图
 * 调用 Electron 主进程的截图 API，返回 base64 图片
 */
export async function captureScreen() {
    if (typeof window.electronAPI === 'undefined') {
        console.error('不在 Electron 环境中');
        alert('请在 Electron 应用中运行');
        return null;
    }

    try {
        const imageDataUrl = await window.electronAPI.captureScreen();
        return imageDataUrl;
    } catch (err) {
        console.error('截图失败:', err);
        alert('截图失败：' + err.message);
        return null;
    }
}

/**
 * OCR 文字识别
 * @param {string} imageDataUrl - base64 格式的图片
 * @param {string} lang - 语言包，默认 'chi_sim+eng'（中文简体 + 英文）
 */
export async function recognizeText(imageDataUrl, lang = 'chi_sim+eng') {
    try {
        const result = await Tesseract.recognize(imageDataUrl, lang, {
            tessedit_pageseg_mode: 6,
            preserve_interword_spaces: 0,
        });

        let text = result.data.text.trim();

        // ========== 核心修复：调用清理函数 ==========
        text = cleanOCRText(text);

        // 限制文字长度
        if (text.length > 1000) {
            text = text.substring(0, 1000);
        }

        console.log('OCR 识别结果:', text);
        return text;
    } catch (err) {
        console.error('OCR 识别失败:', err);
        throw new Error('文字识别失败：' + err.message);
    }
}

/**
 * 清理 OCR 识别的文本 - 增强版
 * @param {string} text - 原始 OCR 文本
 * @returns {string} - 清理后的文本
 */
function cleanOCRText(text) {
    if (!text) return '';

    let cleaned = text;

    // ========== 1. 预处理：移除常见的 OCR 噪点模式 ==========

    // 移除形如 "| | | | |" 的竖线干扰
    cleaned = cleaned.replace(/[│┃┆├─┼┤│|¦]/g, ' ');
    cleaned = cleaned.replace(/\s*[│┃┆├─┼┤│|¦]\s*/g, ' ');

    // 移除形如 "─ ─ ─ ─" 的横线干扰
    cleaned = cleaned.replace(/─{2,}/g, ' ');
    cleaned = cleaned.replace(/━{2,}/g, ' ');
    cleaned = cleaned.replace(/={2,}/g, ' ');

    // 移除独立的大括号干扰符
    cleaned = cleaned.replace(/[{}\[\]()]/g, ' ');

    // 移除乱码模式：单独的符号或重复字符
    cleaned = cleaned.replace(/^[_\-=~^.*#@$%&+]+$/gm, '');

    // 移除连续重复的单字符（如 "a a a a" 或 "A A A"）
    cleaned = cleaned.replace(/\b([a-zA-Z])\s+\1(\s+\1)*\b/gi, '$1');

    // 移除类似 "O O O" 或 "o o o" 的单字母重复
    cleaned = cleaned.replace(/\b([a-z])\s+(?:\1\s+)*\1\b/gi, '$1');

    // ========== 2. 统一换行处理 ==========
    cleaned = cleaned.replace(/\r\n/g, '\n');
    cleaned = cleaned.replace(/\r/g, '\n');

    // ========== 3. 逐行分析过滤 ==========
    const lines = cleaned.split('\n');
    const filteredLines = [];

    for (const line of lines) {
        const trimmed = line.trim();

        // 跳过空行
        if (trimmed.length === 0) continue;

        // 跳过纯符号行（只有标点或装饰符）
        const pureSymbols = trimmed.replace(/[\u4e00-\u9fa5a-zA-Z0-9\s]/g, '');
        if (pureSymbols.length === trimmed.length) continue;

        // 跳过太短的行（<2个有效字符）
        const chineseChars = (trimmed.match(/[\u4e00-\u9fa5]/g) || []).length;
        const englishChars = (trimmed.match(/[a-zA-Z]/g) || []).length;
        const digitChars = (trimmed.match(/[0-9]/g) || []).length;
        const validChars = chineseChars + englishChars + digitChars;

        if (validChars < 2) continue;

        // 如果有效字符占比低于 25%，过滤掉
        const totalChars = trimmed.replace(/\s/g, '').length;
        if (validChars / totalChars < 0.25) continue;

        // 跳过包含大量杂项符号的行
        const noiseChars = (trimmed.match(/[│┃┆├─┼┤~^.*#@$%&+/\\|]/g) || []).length;
        if (noiseChars > validChars * 0.3) continue;

        filteredLines.push(trimmed);
    }

    cleaned = filteredLines.join('\n');

    // ========== 4. 合并多余的空格 ==========
    let previous = '';
    let current = cleaned;
    while (previous !== current) {
        previous = current;
        current = current.replace(/([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])/g, '$1$2');
    }
    cleaned = current;

    // 步骤4.2: 删除中文字符串前/后的空格
    cleaned = cleaned.replace(/\s+([\u4e00-\u9fa5]+)/g, '$1');
    cleaned = cleaned.replace(/([\u4e00-\u9fa5]+)\s+/g, '$1');

    // 步骤4.3: 中文与英文/数字之间保留一个空格（"未来LLM" → "未来 LLM"）
    cleaned = cleaned.replace(/([\u4e00-\u9fa5])\s*([a-zA-Z0-9])/g, '$1 $2');
    cleaned = cleaned.replace(/([a-zA-Z0-9])\s*([\u4e00-\u9fa5])/g, '$1 $2');
    // 修复上面可能引入的多个空格
    cleaned = cleaned.replace(/([a-zA-Z0-9])\s+([\u4e00-\u9fa5])/g, '$1 $2');

    // 步骤4.4: 中文标点符号前去除空格
    cleaned = cleaned.replace(/\s+([，。！？；：""''、…—])/g, '$1');
    // 中文标点符号后不加空格（保持紧凑）

    // 步骤4.5: 数字与中文之间（保持紧凑，不强制加空格）
    cleaned = cleaned.replace(/([0-9])\s+([\u4e00-\u9fa5])/g, '$1$2');
    cleaned = cleaned.replace(/([\u4e00-\u9fa5])\s+([0-9])/g, '$1$2');

    // 步骤4.6: 最后统一合并连续空格
    cleaned = cleaned.replace(/\s{2,}/g, ' ');
    // ========== 5. 清理前后空白 ==========
    cleaned = cleaned.trim();

    // ========== 6. 移除行首行尾的非法字符 ==========
    cleaned = cleaned.replace(/^[^\u4e00-\u9fa5a-zA-Z0-9]+/gm, '');
    cleaned = cleaned.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]+$/gm, '');

    // ========== 7. 移除连续的空行 ==========
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

    return cleaned;
}
