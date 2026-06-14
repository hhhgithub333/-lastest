//package com.example.graduationproject.tts;
//
//import android.content.Context;
//
//public interface TTSEngine {
//    void init(Context context, String apiKey);
//    void synthesize(String text, String voice, Callback callback);
//    void stop();
//    void release();
//
//    interface Callback {
//        void onStart();
//        void onAudioData(byte[] data);
//        void onComplete();
//        void onError(String error);
//    }
//}

package com.example.graduationproject.tts;

import android.content.Context;

public interface TTSEngine {
    void init(Context context, String apiKey);

    /** 无参考音频合成（原有接口，兼容所有引擎） */
    void synthesize(String text, String voice, Callback callback);

    /**
     * 带参考音频合成（新增）
     * 不支持参考音频的引擎会忽略 referenceAudio，直接走普通合成。
     * BaseTTSEngine 已提供默认实现，子类无需重写。
     */
    default void synthesize(String text, String voice, byte[] referenceAudio, Callback callback) {
        // 默认实现：忽略参考音频，走普通合成
        synthesize(text, voice, callback);
    }

    void stop();
    void release();

    interface Callback {
        void onStart();
        void onAudioData(byte[] data);
        void onComplete();
        void onError(String error);
    }
}
