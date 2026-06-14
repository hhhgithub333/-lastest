package com.example.graduationproject.tts;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import com.example.graduationproject.FloatingWindowManager;
import com.example.graduationproject.services.TextCaptureService;
import com.example.graduationproject.utils.AudioPlayer;
import com.example.graduationproject.utils.CenterToast;
import java.io.ByteArrayOutputStream;
import java.util.LinkedList;
import java.util.Queue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;

public class TTSManager {
    private static final String TAG = "TTSManager";
    private static TTSManager instance;
    private Context context;
    private TTSEngine currentEngine;
    private String currentEngineName;
    private Queue<String> textQueue = new LinkedList<>();
    private AtomicBoolean isProcessing = new AtomicBoolean(false);
    private AtomicBoolean isPaused = new AtomicBoolean(false);
    private AtomicBoolean isPlaying = new AtomicBoolean(false);

    private Thread workThread;
    private volatile boolean workThreadRunning = false;
    private Handler mainHandler = new Handler(Looper.getMainLooper());
    private AudioPlayer audioPlayer;
    private String currentVoice = "Cherry";
    private TTSListener listener;

    /** 当前参考音频字节数组，null 表示不使用参考音频 */
    private byte[] currentReferenceAudio = null;

    // ========== 音频缓存 ==========
    private ConcurrentHashMap<String, byte[]> audioCache = new ConcurrentHashMap<>();
    private ConcurrentHashMap<String, Long> cacheTimestamp = new ConcurrentHashMap<>();
    private static final int CACHE_MAX_SIZE = 20;
    private static final long CACHE_EXPIRE_TIME = 30 * 60 * 1000; // 30分钟

    // ========== 文本差异检测 ==========
    private String lastProcessedText = "";  // 上次处理的完整文字

    // ========== 保存最后一次合成的完整音频数据 ==========
    private volatile byte[] lastAudioData = null;

    // ========== 捕获文本缓存（供 UserCenterFragment 读取保存到后端）==========
    private String cachedScreenText = "";
    private String lastCapturedText = "";

    // ========== SharedPreferences keys ==========
    private static final String PREF_NAME = "tts_settings";
    private static final String KEY_ENGINE_NAME = "engine_name";
    private static final String KEY_VOICE = "voice";
    private static final String KEY_REFERENCE_AUDIO = "reference_audio";
    private SharedPreferences prefs;
    private static final String KEY_SPEED = "speed";
    private static final String KEY_CAPTURED_TEXT = "captured_text";


    public interface TTSListener {
        void onStart();
        void onProgress(String text);
        void onComplete();
        void onError(String error);
        void onPaused();
        void onResumed();
    }

    private TTSManager() {}
    public static TTSManager getInstance() {
        if (instance == null) instance = new TTSManager();
        return instance;
    }

    /** 获取当前引擎名（用于 Fragment 恢复状态） */
    public String getCurrentEngineName() { return currentEngineName; }

    /** 获取当前音色名（用于 Fragment 恢复状态） */
    public String getCurrentVoice() { return currentVoice; }

    public void init(Context context, String apiKey) {
        this.context = context;
        this.audioPlayer = new AudioPlayer();
        this.audioPlayer.init(context);
        this.audioPlayer.setOnCompletionListener(() -> {
            isPlaying.set(false);
            mainHandler.post(() -> {
                if (listener != null) listener.onComplete();
                FloatingWindowManager.getInstance().updatePlaybackState(false, "已就绪");
                
            });
            Log.d(TAG, "音频播放完毕");
        });
        this.audioPlayer.setOnProgressListener(new AudioPlayer.OnProgressListener() {
             @Override
             public void onProgress(long currentPosition, long duration) {
                 FloatingWindowManager.getInstance().updateProgress(currentPosition, duration);
             }
        });


            // ========== 初始化 SharedPreferences 并恢复保存的设置 ==========
        prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        currentEngineName = prefs.getString(KEY_ENGINE_NAME, "千问 TTS");   // 默认千问
        currentVoice  = prefs.getString(KEY_VOICE, "Cherry");          // 默认 Cherry

        // 恢复倍速
        float savedSpeed = prefs.getFloat(KEY_SPEED, 1.0f);
        if (audioPlayer != null) audioPlayer.setSpeed(savedSpeed);

        // 恢复捕获文本
        cachedScreenText = prefs.getString(KEY_CAPTURED_TEXT, "");
        lastCapturedText = cachedScreenText;

        // 尝试恢复参考音频（Base64 编码存储）
        String refAudioBase64 = prefs.getString(KEY_REFERENCE_AUDIO, null);
        if (refAudioBase64 != null && !refAudioBase64.isEmpty()) {
            try {
                currentReferenceAudio = android.util.Base64.decode(refAudioBase64, android.util.Base64.DEFAULT);
                Log.d(TAG, "已从 SharedPreferences 恢复参考音频，大小: " + currentReferenceAudio.length + " bytes");
            } catch (Exception e) {
                Log.e(TAG, "恢复参考音频失败，清除记录", e);
                currentReferenceAudio = null;
                prefs.edit().remove(KEY_REFERENCE_AUDIO).apply();
            }
        }

        Log.d(TAG, "TTSManager 初始化完成，已恢复设置 - 引擎: " + currentEngineName + ", 音色: " + currentVoice + ", 倍速: " + savedSpeed);

    }

    public void setEngine(TTSEngine engine, String engineName) {
        if (currentEngine != null) currentEngine.release();
        this.currentEngine = engine;
        this.currentEngineName = engineName;
        this.currentEngine.init(context, "");
        clearCache(); // 切换引擎时清空缓存
        lastProcessedText = ""; // 重置文本记录
        lastAudioData = null;   // 清除上次音频数据

        // ========== 持久化保存 ==========
        if (prefs != null) {
            prefs.edit().putString(KEY_ENGINE_NAME, engineName).apply();
        }
        Log.d(TAG, "切换到引擎: " + engineName + "（已保存）");
    }

    public void setVoice(String voice) {
        this.currentVoice = voice;
        clearCache(); // 切换音色时清空缓存
        lastAudioData = null; // 清除上次音频数据

        // ========== 持久化保存 ==========
        if (prefs != null) {
            prefs.edit().putString(KEY_VOICE, voice).apply();
        }
        Log.d(TAG, "切换到音色: " + voice + "（已保存）");
    }

    public void setSpeed(float speed) {
        if (audioPlayer != null) audioPlayer.setSpeed(speed);
        if (prefs != null) {
            prefs.edit().putFloat(KEY_SPEED, speed).apply();
        }
    }

    public void setCapturedText(String text) {
        this.cachedScreenText = (text != null) ? text : "";
        this.lastCapturedText = this.cachedScreenText;
        if (prefs != null) {
            prefs.edit().putString(KEY_CAPTURED_TEXT, this.cachedScreenText).apply();
        }
    }

    /**
     * 获取当前捕获的文本（供 UserCenterFragment 读取并保存到后端）
     */
    public String getCapturedText() {
        return (cachedScreenText != null) ? cachedScreenText : "";
    }

    public float getSpeed() {
        return (audioPlayer != null) ? audioPlayer.getSpeed() : 1.0f;
    }


    public AudioPlayer getAudioPlayer() {
         return audioPlayer;
     }

        public void setListener(TTSListener listener) { this.listener = listener; }

    // ========== 缓存方法 ==========
    private String getCacheKey(String text, String voice, String engine) {
        return engine + "|" + voice + "|" + text.hashCode();
    }

    private void addToCache(String key, byte[] audioData) {
        if (audioCache.size() >= CACHE_MAX_SIZE) {
            String oldestKey = null;
            long oldestTime = Long.MAX_VALUE;
            for (String k : cacheTimestamp.keySet()) {
                Long t = cacheTimestamp.get(k);
                if (t != null && t < oldestTime) {
                    oldestTime = t;
                    oldestKey = k;
                }
            }
            if (oldestKey != null) {
                audioCache.remove(oldestKey);
                cacheTimestamp.remove(oldestKey);
            }
        }
        audioCache.put(key, audioData);
        cacheTimestamp.put(key, System.currentTimeMillis());
        Log.d(TAG, "添加缓存，大小: " + audioData.length);
    }

    private byte[] getFromCache(String key) {
        byte[] data = audioCache.get(key);
        if (data != null) {
            Long timestamp = cacheTimestamp.get(key);
            if (timestamp != null && System.currentTimeMillis() - timestamp < CACHE_EXPIRE_TIME) {
                Log.d(TAG, "✅ 命中缓存");
                return data;
            } else {
                audioCache.remove(key);
                cacheTimestamp.remove(key);
            }
        }
        return null;
    }

    public void clearCache() {
        audioCache.clear();
        cacheTimestamp.clear();
        Log.d(TAG, "已清空缓存");
    }

    // ========== 新增：获取最后一次合成的音频数据 ==========
    /**
     * 获取最后一次成功合成的音频数据
     * @return 音频数据字节数组，如果没有则返回 null
     */
    public byte[] getLastAudioData() {
        return lastAudioData;
    }

    // ========== 文本差异检测 ==========
    /**
     * 检测新文本相对于旧文本的新增部分（用于滑动阅读场景）
     * @param oldText 旧文本
     * @param newText 新文本
     * @return 新增的文本内容，如果没有新增返回 null
     */
    private String getNewContent(String oldText, String newText) {
        if (newText == null || newText.isEmpty()) return null;
        if (oldText == null || oldText.isEmpty()) return newText;
        if (newText.equals(oldText)) return null;

        // 查找 oldText 在 newText 中的位置
        int index = newText.indexOf(oldText);
        if (index >= 0) {
            // oldText 在 newText 中，取后面的部分
            String after = newText.substring(index + oldText.length()).trim();
            if (!after.isEmpty()) {
                Log.d(TAG, "检测到重叠，新增后缀: " + after);
                return after;
            }
        }

        // 如果找不到，再试试查找共同前缀
        int commonPrefixLen = 0;
        int minLen = Math.min(oldText.length(), newText.length());
        for (int i = 0; i < minLen; i++) {
            if (oldText.charAt(i) == newText.charAt(i)) commonPrefixLen++;
            else break;
        }
        if (commonPrefixLen > 10) {
            String after = newText.substring(commonPrefixLen).trim();
            if (!after.isEmpty()) {
                Log.d(TAG, "检测到共同前缀，新增后缀: " + after);
                return after;
            }
        }

        // 没有重叠，返回完整新文本
        Log.d(TAG, "未检测到重叠，返回完整新文本");
        return newText;
    }

    /**
     * 设置参考音频（声音克隆用）
     * @param audioData 音频文件字节数组，传 null 清除
     */
    public void setReferenceAudio(byte[] audioData) {
        this.currentReferenceAudio = audioData;
        if (audioData != null) {
            Log.d(TAG, "已设置参考音频，大小: " + audioData.length + " bytes");
            clearCache(); // 有参考音频时清空缓存
            lastAudioData = null; // 清除上次音频数据

            // ========== 持久化保存（Base64 编码）==========
            if (prefs != null) {
                String base64 = android.util.Base64.encodeToString(audioData, android.util.Base64.DEFAULT);
                prefs.edit().putString(KEY_REFERENCE_AUDIO, base64).apply();
                Log.d(TAG, "参考音频已持久化，大小: " + audioData.length + " bytes");
            }
        } else {
            Log.d(TAG, "已清除参考音频");
            if (prefs != null) {
                prefs.edit().remove(KEY_REFERENCE_AUDIO).apply();
            }
        }
    }

    /** 获取当前参考音频 */
    public byte[] getReferenceAudio() { return currentReferenceAudio; }

    private boolean isEngineAvailable() { return currentEngine != null; }

    public void play(String text) {
        if (text == null || text.trim().isEmpty()) return;
        if (!isEngineAvailable()) {
            Log.e(TAG, "引擎不可用");
            if (listener != null) listener.onError("引擎未初始化");
            return;
        }

        String trimmedText = text.trim();

        // ========== 1. 先检查缓存（完全相同的内容直接播放缓存）==========
        if (currentReferenceAudio == null) {
            String cacheKey = getCacheKey(trimmedText, currentVoice, currentEngineName);
            byte[] cachedAudio = getFromCache(cacheKey);
            if (cachedAudio != null) {
                Log.d(TAG, "✅ 使用缓存的音频，不调用 TTS");
                lastAudioData = cachedAudio; // 保存缓存的音频数据
                FloatingWindowManager.getInstance().updatePlaybackState(true, "播放中");
                audioPlayer.play(cachedAudio, currentEngineName);
                isPlaying.set(true);
                return;
            }
        }
        // ========== 缓存检查结束 ==========

        // ========== 2. 文本差异检测：提取新增内容 ==========
        String newContent = getNewContent(lastProcessedText, trimmedText);

        if (newContent == null) {
            // 没有新内容，尝试播放缓存（用户可能重复点击播放同一段文字）
            Log.d(TAG, "没有检测到新内容，尝试播放缓存");
            if (currentReferenceAudio == null) {
                String cacheKey = getCacheKey(trimmedText, currentVoice, currentEngineName);
                byte[] cachedAudio = getFromCache(cacheKey);
                if (cachedAudio != null) {
                    Log.d(TAG, "✅ 播放缓存音频");
                    lastAudioData = cachedAudio;
                    FloatingWindowManager.getInstance().updatePlaybackState(true, "播放中");
                    audioPlayer.play(cachedAudio, currentEngineName);
                    isPlaying.set(true);
                    return;
                }
            }
            // 缓存也没有，重新合成完整文本
            Log.d(TAG, "缓存未命中，重新合成完整文本");
            newContent = trimmedText;
        }

        // 更新已处理的完整文本
        lastProcessedText = trimmedText;

        Log.d(TAG, "完整文本: " + (trimmedText.length() > 100 ? trimmedText.substring(0, 100) + "..." : trimmedText));
        Log.d(TAG, "新增内容: " + (newContent.length() > 100 ? newContent.substring(0, 100) + "..." : newContent));
        // ========== 文本差异检测结束 ==========

        // 3. 合成新增内容
        Log.d(TAG, "开始合成新增内容: " + (newContent.length() > 100 ? newContent.substring(0, 100) + "..." : newContent));
        if (workThread != null && workThread.isAlive()) {
            try { workThread.join(500); } catch (InterruptedException e) { workThread.interrupt(); }
        }
        stop();
        isPlaying.set(false); isPaused.set(false); isProcessing.set(false);
        synchronized (textQueue) { textQueue.clear(); textQueue.offer(newContent); }
        FloatingWindowManager.getInstance().updatePlaybackState(false, "生成中");
        startWorkThread();
    }

    public void pause() {
        if (isPaused.get()) return;
        Log.d(TAG, "暂停");
        isPaused.set(true);
        if (audioPlayer != null) audioPlayer.pause();
        if (currentEngine != null) currentEngine.stop();
        isPlaying.set(false);
        mainHandler.post(() -> {
            if (listener != null) listener.onPaused();
            FloatingWindowManager.getInstance().updatePlaybackState(false, "已暂停");
        });
    }

    public void resume() {
        if (!isPaused.get()) return;
        Log.d(TAG, "继续");
        isPaused.set(false);
        if (audioPlayer != null) { audioPlayer.resume(); isPlaying.set(true); }
        mainHandler.post(() -> {
            if (listener != null) listener.onResumed();
            FloatingWindowManager.getInstance().updatePlaybackState(true, "播放中");
        });
    }

    public void togglePlayPause() {
        if (isPlaying.get()) pause();
        else if (isPaused.get()) resume();
        else {
            String text = TextCaptureService.getInstance() != null ?
                    TextCaptureService.getInstance().getCurrentScreenText() : "";
            if (text != null && !text.isEmpty()) play(text);
            else if (context != null) CenterToast.show(context, "没有捕获到文字");
        }
    }

    public void stop() {
        Log.d(TAG, "停止");
        isPaused.set(false); isPlaying.set(false);
        synchronized (textQueue) { textQueue.clear(); }
        if (currentEngine != null) currentEngine.stop();
        if (audioPlayer != null) audioPlayer.stop();
        isProcessing.set(false);
        mainHandler.post(() -> {
            FloatingWindowManager.getInstance().updatePlaybackState(false, "已就绪");
            FloatingWindowManager.getInstance().hideProgressBar();
        });
    }

    private synchronized void startWorkThread() {
        if (workThread != null && workThread.isAlive()) {
            try { workThread.join(500); } catch (InterruptedException e) { workThread.interrupt(); }
        }
        workThreadRunning = true;
        workThread = new Thread(() -> { processQueue(); workThreadRunning = false; workThread = null; });
        workThread.start();
    }

    private void processQueue() {
        while (workThreadRunning) {
            while (isPaused.get() && workThreadRunning) {
                try { Thread.sleep(100); } catch (InterruptedException e) { return; }
            }
            if (!workThreadRunning) break;
            String text;
            synchronized (textQueue) { text = textQueue.poll(); }
            if (text == null) break;
            if (!isEngineAvailable()) break;

            final Object taskLock = new Object();
            final AtomicBoolean completed = new AtomicBoolean(false);
            final String currentText = text;

            // 用于收集音频数据的流（收集完整音频后供下载使用）
            final ByteArrayOutputStream audioStream = new ByteArrayOutputStream();

            mainHandler.post(() -> { if (listener != null) listener.onStart(); });
            Log.d(TAG, "开始合成: " + (text.length() > 100 ? text.substring(0, 100) + "..." : text));

            try {
                currentEngine.synthesize(text, currentVoice, currentReferenceAudio, new TTSEngine.Callback() {
                    @Override public void onStart() {}
                    final boolean[] isFirstAudio = {true};
                    @Override public void onAudioData(byte[] data) {
                        if (isPaused.get()) return;
                        if (data != null && data.length > 0) {
                            if (isFirstAudio[0]) {
                                isFirstAudio[0] = false;
                                mainHandler.post(() -> {
                                    FloatingWindowManager.getInstance().updatePlaybackState(true, "播放中");
                                });
                            }
                            // 收集音频数据
                            try {
                                audioStream.write(data);
                            } catch (Exception e) {
                                Log.e(TAG, "收集音频数据失败", e);
                            }

                            // 边播边缓存（使用完整文本的 key）
                            if (currentReferenceAudio == null) {
                                String fullText = lastProcessedText;
                                String cacheKey = getCacheKey(fullText, currentVoice, currentEngineName);
                                addToCache(cacheKey, data);
                            }

                            if (audioPlayer != null) {
                                audioPlayer.play(data, currentEngineName);
                                isPlaying.set(true);
                            }
                        }
                    }
                    @Override public void onComplete() {
                        lastAudioData = audioStream.toByteArray();
                        Log.d(TAG, "完整音频数据已保存，大小: "
                                + (lastAudioData != null ? lastAudioData.length : 0) + " bytes");
                        synchronized (taskLock) { completed.set(true); taskLock.notify(); }
                        mainHandler.post(() -> { if (listener != null) listener.onProgress(currentText); });
                    }

                    @Override public void onError(String error) {
                        Log.e(TAG, "错误: " + error);
                        isPlaying.set(false);
                        FloatingWindowManager.getInstance().updatePlaybackState(false, "已就绪");
                        FloatingWindowManager.getInstance().hideProgressBar();
                        synchronized (taskLock) { completed.set(true); taskLock.notify(); }
                        mainHandler.post(() -> { if (listener != null) listener.onError(error); });
                    }

                });
            } catch (RejectedExecutionException e) {
                Log.e(TAG, "引擎任务被拒绝", e);
                mainHandler.post(() -> { if (listener != null) listener.onError("引擎不可用"); });
                break;
            }
            try {
                synchronized (taskLock) {
                    while (!completed.get() && workThreadRunning) taskLock.wait();
                }
            } catch (InterruptedException e) { break; }
        }
        isProcessing.set(false); workThreadRunning = false;
        Log.d(TAG, "队列处理完成，线程退出");
    }

    public boolean isPlaying() { return isPlaying.get(); }
    public boolean isPaused() { return isPaused.get(); }
    public void release() { stop(); if (currentEngine != null) currentEngine.release(); if (audioPlayer != null) audioPlayer.release(); }
}