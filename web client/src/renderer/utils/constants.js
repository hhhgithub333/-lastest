// 模型配置，与 Android 端完全一致
export const MODEL_CONFIGS = {
    // ========== 云端模型（不需要参考音频）==========
    qwen: {
        name: "千问 TTS",
        isLocal: false, 
        needReference: false,  // 不需要参考音频
        voices: ["Cherry", "Serena", "Ethan", "Chelsie", "Momo", "Vivian", "Moon", "Maia", "Kai", "Nofish", "Bella", "Jennifer", "Ryan", "Katerina", "Aiden", "Eldric Sage", "Mia", "Mochi", "Bellona", "Vincent", "Bunny", "Neil", "Elias", "Arthur"],
        voiceNames: ["🍒 Cherry - 芊悦", "⭐ Serena - 苏瑶", "👨 Ethan - 晨煦", "🌸 Chelsie - 千雪", "🐰 Momo - 茉兔", "💜 Vivian - 十三", "🌙 Moon - 月白", "📚 Maia - 四月", "🎧 Kai - 凯", "🐟 Nofish - 不吃鱼", "👶 Bella - 萌宝", "🎬 Jennifer - 詹妮弗", "🎭 Ryan - 甜茶", "👑 Katerina - 卡捷琳娜", "🍳 Aiden - 艾登", "🧓 Eldric Sage - 沧明子", "👧 Mia - 乖小妹", "🧒 Mochi - 沙小弥", "⚔️ Bellona - 燕铮莺", "🎸 Vincent - 田叔", "🐰 Bunny - 萌小姬", "📺 Neil - 阿闻", "🎓 Elias - 墨讲师", "👴 Arthur - 徐大爷"]
    },
    cosyvoice: {
        name: "CosyVoice",
        needReference: false,
        isLocal: false,
        voices: ["longanyang", "longanhuan"],
        voiceNames: ["🦁 龙安洋", "🦊 龙安欢"]
    },
    sambert: {
        name: "Sambert",
        isLocal: false,
        needReference: false,
        voices: ["zhinan", "zhiqi", "zhichu", "zhide", "zhijia", "zhiru", "zhiqian", "zhixiang", "zhiwei", "zhihao", "zhijing", "zhiming", "zhimo", "zhina", "zhishu", "zhistella", "zhiting", "zhixiao", "zhiya", "zhiye", "zhiying", "zhiyuan", "zhiyue", "zhigui", "zhishuo", "zhimiao-emo", "zhimao"],
        voiceNames: ["👨 知楠", "👩 知琪", "👨 知厨", "👨 知德", "👩 知佳", "👩 知茹", "👩 知倩", "👨 知祥", "👩 知薇", "👨 知浩", "👩 知婧", "👨 知茗", "👨 知墨", "👩 知娜", "👨 知树", "👩 知莎", "👩 知婷", "👩 知笑", "👩 知雅", "👨 知晔", "👩 知颖", "👩 知媛", "👩 知悦", "👩 知柜", "👨 知硕", "👩 知妙", "👩 知猫"]
    },
    
    // ========== 本地模型（需要参考音频）==========
    xtts_v2: {
        name: "XTTS-v2",
        isLocal: true, 
        needReference: true,  // ✅ 需要参考音频
        voices: ["default"],
        voiceNames: ["🎤 默认声音"]
    },
    voxcpm: {
        name: "VoxCPM",
        isLocal: true, 
        needReference: true,  // ✅ 需要参考音频
        voices: ["default"],
        voiceNames: ["需要参考音频"]
    },
    chatterbox: {
        name: "ChatterBox",
        isLocal: true, 
        needReference: true,  // ✅ 需要参考音频
        voices: ["default"],
        voiceNames: ["🎤 默认声音"]
    },
    vibevoice: {
        name: "VibeVoice",
        isLocal: true, 
        needReference: false,  // ✅ 需要参考音频
        voices: ["en-Mike_man", "en-Emma_woman", "en-Carter_man", "en-Davis_man", "en-Frank_man", "en-Grace_woman"],
        voiceNames: ["🇺🇸 Mike - 英文男声", "🇺🇸 Emma - 英文女声", "🇺🇸 Carter - 英文男声", "🇺🇸 Davis - 英文男声", "🇺🇸 Frank - 英文男声", "🇺🇸 Grace - 英文女声"]
    },
    indextts: {
        name: "IndexTTS",
        isLocal: true, 
        needReference: true,  // ✅ 需要参考音频
        voices: ["default"],
        voiceNames: ["🎤 默认声音"]
    }
};

// ========== 需要参考音频的模型列表 ==========
export const MODELS_NEED_REFERENCE = ['xtts_v2', 'voxcpm', 'chatterbox', 'indextts'];

/**
 * 检查某个模型是否需要参考音频
 * @param {string} modelKey - 模型 key
 * @returns {boolean}
 */
export function modelNeedsReference(modelKey) {
    return MODELS_NEED_REFERENCE.includes(modelKey);
}

// 倍速选项
export const SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
export const SPEED_LABELS = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"];

// 支持的参考音频格式
export const SUPPORTED_AUDIO_FORMATS = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/flac'];
export const SUPPORTED_AUDIO_EXTENSIONS = ['.wav', '.mp3', '.ogg', '.flac'];
