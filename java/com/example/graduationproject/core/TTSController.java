//package com.example.graduationproject.core;
//
//import android.content.Context;
//import com.example.graduationproject.services.TextCaptureService;
//import com.example.graduationproject.tts.QwenTTSEngine;
//import com.example.graduationproject.tts.TTSManager;
//import com.example.graduationproject.utils.CenterToast;
//
//public class TTSController {
//
//    private final Context context;
//    private final TTSManager ttsManager;
//    private final FloatingWindowController floatingWindowController;
//    private TTSListener listener;
//
//    public interface TTSListener {
//        void onPlayStateChanged(boolean isPlaying);
//        void onError(String error);
//    }
//
//    public TTSController(Context context) {
//        this.context = context;
//        this.ttsManager = TTSManager.getInstance();
//        this.floatingWindowController = new FloatingWindowController(context);
//        init();
//    }
//
//    private void init() {
//        ttsManager.init(context, "");
//        ttsManager.setEngine(new QwenTTSEngine(), "千问");
//        ttsManager.setVoice("Cherry");
//
//        ttsManager.setListener(new TTSManager.TTSListener() {
//            @Override public void onStart() {
//                floatingWindowController.updatePlayState(true);
//                if (listener != null) listener.onPlayStateChanged(true);
//            }
//            @Override public void onComplete() {
//                floatingWindowController.updatePlayState(false);
//                if (listener != null) listener.onPlayStateChanged(false);
//            }
//            @Override public void onPaused() {
//                floatingWindowController.updatePlayState(false);
//                if (listener != null) listener.onPlayStateChanged(false);
//            }
//            @Override public void onResumed() {
//                floatingWindowController.updatePlayState(true);
//                if (listener != null) listener.onPlayStateChanged(true);
//            }
//            @Override public void onError(String error) {
//                floatingWindowController.updatePlayState(false);
//                if (listener != null) listener.onError(error);
//                CenterToast.show(context, "TTS错误: " + error);
//            }
//            @Override public void onProgress(String text) {}
//        });
//    }
//
//    public void setListener(TTSListener listener) { this.listener = listener; }
//    public TTSManager getManager() { return ttsManager; }
//
//    public void play(String text) {
//        if (text == null || text.isEmpty()) {
//            CenterToast.show(context, "没有捕获到文字");
//            return;
//        }
//        ttsManager.play(text);
//    }
//
//    public void pause() { ttsManager.pause(); }
//    public void resume() { ttsManager.resume(); }
//    public void stop() { ttsManager.stop(); }
//
//    public void togglePlayPause() {
//        if (ttsManager.isPlaying()) ttsManager.pause();
//        else if (ttsManager.isPaused()) ttsManager.resume();
//        else {
//            String text = TextCaptureService.getInstance() != null ?
//                    TextCaptureService.getInstance().getCurrentScreenText() : "";
//            play(text);
//        }
//    }
//
//    public void startService() { floatingWindowController.start(); }
//    public void stopService() { ttsManager.stop(); floatingWindowController.stop(); }
//    public void release() { ttsManager.release(); floatingWindowController.reset(); }
//    public boolean isServiceRunning() { return floatingWindowController.isRunning(); }
//    public boolean isPlaying() { return ttsManager.isPlaying(); }
//    public boolean isPaused() { return ttsManager.isPaused(); }
//    public void updateFloatingWindowSettings(String settings) { floatingWindowController.updateSettings(settings); }
//}

package com.example.graduationproject.core;

import android.content.Context;
import com.example.graduationproject.services.TextCaptureService;
import com.example.graduationproject.tts.TTSManager;
import com.example.graduationproject.utils.CenterToast;

public class TTSController {

    private final Context context;
    private final TTSManager ttsManager;
    private final FloatingWindowController floatingWindowController;
    private TTSListener listener;

    public interface TTSListener {
        void onPlayStateChanged(boolean isPlaying);
        void onError(String error);
    }

    public TTSController(Context context) {
        this.context = context;
        this.ttsManager = TTSManager.getInstance();
        this.floatingWindowController = new FloatingWindowController(context);
        init();
    }

    private void init() {
        // 初始化 TTSManager，从 SharedPreferences 恢复本地保存的设置
        // 引擎/音色不再硬编码，由本地恢复 + MainActivity 后端恢复接管
        ttsManager.init(context, "");

        ttsManager.setListener(new TTSManager.TTSListener() {
            @Override public void onStart() {
                floatingWindowController.updatePlayState(true);
                if (listener != null) listener.onPlayStateChanged(true);
            }
            @Override public void onComplete() {
                floatingWindowController.updatePlayState(false);
                if (listener != null) listener.onPlayStateChanged(false);
            }
            @Override public void onPaused() {
                floatingWindowController.updatePlayState(false);
                if (listener != null) listener.onPlayStateChanged(false);
            }
            @Override public void onResumed() {
                floatingWindowController.updatePlayState(true);
                if (listener != null) listener.onPlayStateChanged(true);
            }
            @Override public void onError(String error) {
                floatingWindowController.updatePlayState(false);
                if (listener != null) listener.onError(error);
                CenterToast.show(context, "TTS错误: " + error);
            }
            @Override public void onProgress(String text) {}
        });
    }

    public void setListener(TTSListener listener) { this.listener = listener; }
    public TTSManager getManager() { return ttsManager; }

    public void play(String text) {
        if (text == null || text.isEmpty()) {
            CenterToast.show(context, "没有捕获到文字");
            return;
        }
        ttsManager.play(text);
    }

    public void pause() { ttsManager.pause(); }
    public void resume() { ttsManager.resume(); }
    public void stop() { ttsManager.stop(); }

    public void togglePlayPause() {
        if (ttsManager.isPlaying()) ttsManager.pause();
        else if (ttsManager.isPaused()) ttsManager.resume();
        else {
            String text = TextCaptureService.getInstance() != null ?
                    TextCaptureService.getInstance().getCurrentScreenText() : "";
            play(text);
        }
    }

    public void startService() { floatingWindowController.start(); }
    public void stopService() { ttsManager.stop(); floatingWindowController.stop(); }
    public void release() { ttsManager.release(); floatingWindowController.reset(); }
    public boolean isServiceRunning() { return floatingWindowController.isRunning(); }
    public boolean isPlaying() { return ttsManager.isPlaying(); }
    public boolean isPaused() { return ttsManager.isPaused(); }
    public void updateFloatingWindowSettings(String settings) { floatingWindowController.updateSettings(settings); }
}
