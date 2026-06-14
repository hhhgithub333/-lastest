//package com.example.graduationproject.tts;
//
//import android.content.Context;
//import android.util.Log;
//import com.example.graduationproject.network.ApiClient;
//import org.json.JSONObject;
//import java.io.IOException;
//import java.util.concurrent.RejectedExecutionException;
//import java.util.concurrent.ExecutorService;
//import java.util.concurrent.Executors;
//import okhttp3.*;
//
//public abstract class BaseTTSEngine implements TTSEngine {
//    private static final String TAG = "BaseTTSEngine";
//    protected TTSEngine.Callback callback;
//    protected OkHttpClient client;
//    protected ExecutorService executor;
//    protected String engineName;
//
//    public BaseTTSEngine(String engineName) { this.engineName = engineName; }
//
//    @Override
//    public void init(Context context, String apiKey) {
//        client = ApiClient.getClient();
//        if (executor == null || executor.isShutdown() || executor.isTerminated()) {
//            executor = Executors.newSingleThreadExecutor();
//            Log.d(TAG, engineName + " 引擎初始化完成");
//        }
//    }
//
//    @Override
//    public void synthesize(String text, String voice, TTSEngine.Callback callback) {
//        this.callback = callback;
//        if (executor == null || executor.isShutdown() || executor.isTerminated()) {
//            Log.d(TAG, "线程池不可用，重新初始化");
//            init(null, null);
//        }
//        try {
//            executor.execute(() -> doSynthesize(text, voice));
//        } catch (RejectedExecutionException e) {
//            Log.e(TAG, "线程池已关闭，重新初始化", e);
//            init(null, null);
//            try {
//                executor.execute(() -> doSynthesize(text, voice));
//            } catch (RejectedExecutionException ex) {
//                if (callback != null) callback.onError("引擎不可用");
//            }
//        }
//    }
//
//    private void doSynthesize(String text, String voice) {
//        try {
//            JSONObject body = new JSONObject();
//            body.put("text", text);
//            body.put("voice", voice);
//            body.put("engine", engineName);
//            Request request = new Request.Builder()
//                    .url(ApiClient.BASE_URL + "/tts/synthesize")
//                    .post(RequestBody.create(body.toString(), MediaType.parse("application/json")))
//                    .build();
//            Response response = client.newCall(request).execute();
//            if (response.isSuccessful()) {
//                byte[] audioData = response.body().bytes();
//                if (callback != null) {
//                    callback.onStart();
//                    callback.onAudioData(audioData);
//                }
//            } else {
//                String error = response.body().string();
//                if (callback != null) callback.onError("后端错误: " + error);
//            }
//        } catch (Exception e) {
//            Log.e(TAG, "合成失败", e);
//            if (callback != null) callback.onError(e.getMessage());
//        }
//    }
//
//    @Override public void stop() {}
//    @Override public void release() {
//        if (executor != null && !executor.isShutdown()) executor.shutdown();
//    }
//}

package com.example.graduationproject.tts;

import android.content.Context;
import android.util.Log;
import com.example.graduationproject.network.ApiClient;
import java.io.IOException;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import okhttp3.*;

public abstract class BaseTTSEngine implements TTSEngine {
    private static final String TAG = "BaseTTSEngine";
    protected TTSEngine.Callback callback;
    protected OkHttpClient client;
    protected ExecutorService executor;
    protected String engineName;

    public BaseTTSEngine(String engineName) { this.engineName = engineName; }

    @Override
    public void init(Context context, String apiKey) {
        client = ApiClient.getClient();
        if (executor == null || executor.isShutdown() || executor.isTerminated()) {
            executor = Executors.newSingleThreadExecutor();
            Log.d(TAG, engineName + " 引擎初始化完成");
        }
    }

    // ── 无参考音频版本（接口原有方法）──────────────────────────────────
    @Override
    public void synthesize(String text, String voice, TTSEngine.Callback callback) {
        synthesize(text, voice, null, callback);
    }

    // ── 带参考音频版本（新增）──────────────────────────────────────────
    @Override
    public void synthesize(String text, String voice, byte[] referenceAudio, TTSEngine.Callback callback) {
        this.callback = callback;
        if (executor == null || executor.isShutdown() || executor.isTerminated()) {
            Log.d(TAG, "线程池不可用，重新初始化");
            init(null, null);
        }
        try {
            executor.execute(() -> doSynthesize(text, voice, referenceAudio));
        } catch (RejectedExecutionException e) {
            Log.e(TAG, "线程池已关闭，重新初始化", e);
            init(null, null);
            try {
                executor.execute(() -> doSynthesize(text, voice, referenceAudio));
            } catch (RejectedExecutionException ex) {
                if (callback != null) callback.onError("引擎不可用");
            }
        }
    }

    // ── 核心网络请求：JSON → FormData（multipart/form-data）──────────
    private void doSynthesize(String text, String voice, byte[] referenceAudio) {
        try {
            MultipartBody.Builder builder = new MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("text", text)
                    .addFormDataPart("voice", voice)
                    .addFormDataPart("engine", engineName);

            // 如果有参考音频，附加文件字段
            if (referenceAudio != null && referenceAudio.length > 0) {
                builder.addFormDataPart(
                        "reference_audio",
                        "reference.wav",
                        RequestBody.create(referenceAudio, MediaType.parse("audio/wav"))
                );
                Log.d(TAG, "携带参考音频，大小: " + referenceAudio.length + " bytes");
            }

            Request request = new Request.Builder()
                    .url(ApiClient.BASE_URL + "/tts/synthesize")
                    .post(builder.build())
                    .build();

            Response response = client.newCall(request).execute();
            if (response.isSuccessful()) {
                byte[] audioData = response.body().bytes();
                if (callback != null) {
                    callback.onStart();
                    callback.onAudioData(audioData);
                    callback.onComplete();
                }
            } else {
                String error = response.body().string();
                if (callback != null) callback.onError("后端错误: " + error);
            }
        } catch (Exception e) {
            Log.e(TAG, "合成失败", e);
            if (callback != null) callback.onError(e.getMessage());
        }
    }

    @Override public void stop() {}
    @Override public void release() {
        if (executor != null && !executor.isShutdown()) executor.shutdown();
    }
}
