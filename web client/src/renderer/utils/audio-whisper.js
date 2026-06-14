import { generateSimpleTimestamps } from './audio.js'

/**
 * 调用后端 WhisperX 对齐接口，获取逐字时间戳
 *
 * @param {string} text      - 原始文本
 * @param {Blob}   audioBlob - TTS 合成出的音频 Blob
 * @param {number} duration  - 音频总时长（秒，备用）
 * @returns {Promise<Array>} [{ char, start, end }, ...]
 */
export async function generateWhisperTimestamps(text, audioBlob, duration = 0) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)

    try {
        const formData = new FormData()
        const ext = (audioBlob.type === 'audio/mpeg' || audioBlob.type === 'audio/mp3') ? 'mp3' : 'wav'
        formData.append('audio', audioBlob, `audio.${ext}`)
        formData.append('text', text)

        const res = await fetch('http://localhost:8000/tts/align', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        })
        clearTimeout(timeoutId)

        if (!res.ok) {
            const err = await res.text()
            throw new Error(`对齐接口返回 ${res.status}: ${err}`)
        }

        const data = await res.json()
        let timestamps = data.timestamps || []

        if (timestamps.length === 0) {
            throw new Error('后端返回空时间戳')
        }

        // 直接映射：后端应已返回逐字时间戳，字段可能是 word 或 char
        const rawTimestamps = timestamps.map(t => ({
            char: t.word || t.char,
            start: t.start,
            end: t.end
        }))

        // 将空格、标点等无声字符插回到时间戳的正确位置
        return insertSilentChars(rawTimestamps, text)

    } catch (e) {
        clearTimeout(timeoutId)
        console.warn('[WhisperX] 对齐失败，降级为平均分配：', e.message)
        return generateSimpleTimestamps(text, duration || 3)
    }
}

/**
 * 将空格、标点等无声字符插回到时间戳数组的正确位置
 * 
 * WhisperX 返回的时间戳只包含有声字符，空格和标点会被丢弃。
 * 这个函数按原始文本的字符顺序，把无声字符插回去，
 * 时间设为和前一个有声字符的 end 相同（零时长，不占高亮时间）。
 * 
 * @param {Array} timestamps - 后端返回的时间戳 [{ char, start, end }, ...]
 * @param {string} originalText - 原始文本
 * @returns {Array} 包含无声字符的完整时间戳
 */
function insertSilentChars(timestamps, originalText) {
    if (!timestamps.length || !originalText) return timestamps

    const result = []
    let tsIdx = 0  // 当前匹配到时间戳数组的第几个

    // 过滤掉原始文本中和时间戳字符一致的部分，遇到无声字符就插入
    const originalChars = [...originalText]

    for (let i = 0; i < originalChars.length; i++) {
        const ch = originalChars[i]

        // 判断是否为无声字符（空格、换行、制表符等）
        if (isSilentChar(ch)) {
            // 插入无声字符，时间继承前一个字符的 end
            const prevEnd = result.length > 0 ? result[result.length - 1].end : 0
            result.push({
                char: ch,
                start: prevEnd,
                end: prevEnd
            })
        } else {
            // 有声字符，从时间戳数组中取下一个
            if (tsIdx < timestamps.length) {
                result.push({
                    char: ch,  // 使用原始文本的字符，避免 WhisperX 返回的字符和原文不一致
                    start: timestamps[tsIdx].start,
                    end: timestamps[tsIdx].end
                })
                tsIdx++
            } else {
                // 时间戳用完了，剩余有声字符按均分补齐
                const prevEnd = result.length > 0 ? result[result.length - 1].end : 0
                result.push({
                    char: ch,
                    start: prevEnd,
                    end: prevEnd + 0.15
                })
            }
        }
    }

    return result
}

/**
 * 判断字符是否为无声字符（不会被 WhisperX 分配时间戳的字符）
 */
function isSilentChar(ch) {
    // 空白类
    if (/\s/.test(ch)) return true
    return false
}

function mergeWordsToChars(wordTimestamps, originalText) {
    const chars = originalText.split('')
    const result = []
    let charIdx = 0

    for (const wt of wordTimestamps) {
        const word = wt.word || ''
        const wordChars = [...word]
        if (wordChars.length === 0) continue

        const durationPerChar = (wt.end - wt.start) / wordChars.length

        for (let i = 0; i < wordChars.length; i++) {
            if (charIdx >= chars.length) break
            result.push({
                char: chars[charIdx],
                start: Math.round((wt.start + i * durationPerChar) * 1000) / 1000,
                end:   Math.round((wt.start + (i + 1) * durationPerChar) * 1000) / 1000,
            })
            charIdx++
        }
    }

    // 对齐不完整时，用最后时间点往后补
    const lastEnd = result.length > 0 ? result[result.length - 1].end : 0
    while (charIdx < chars.length) {
        result.push({
            char: chars[charIdx],
            start: lastEnd + (charIdx - (result.length - 1)) * 0.32,
            end:   lastEnd + (charIdx - (result.length - 1) + 1) * 0.32,
        })
        charIdx++
    }

    return result
}
