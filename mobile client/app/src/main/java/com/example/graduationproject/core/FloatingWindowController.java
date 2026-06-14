package com.example.graduationproject.core;

import android.content.Context;
import com.example.graduationproject.FloatingWindowManager;
import com.example.graduationproject.utils.CenterToast;

public class FloatingWindowController {

    private final Context context;
    private final FloatingWindowManager floatingWindowManager;
    private boolean isServiceRunning = false;

    public FloatingWindowController(Context context) {
        this.context = context;
        this.floatingWindowManager = FloatingWindowManager.getInstance();
        this.floatingWindowManager.init(context);
    }

    public void start() {
        if (isServiceRunning) {
            CenterToast.show(context, "服务已在运行");
            return;
        }
        floatingWindowManager.show();
        isServiceRunning = true;
        CenterToast.show(context, "服务已启动");
    }

    public void stop() {
        if (!isServiceRunning) return;
        floatingWindowManager.hide();
        floatingWindowManager.reset();
        isServiceRunning = false;
        CenterToast.show(context, "服务已停止");
    }

    public void reset() {
        floatingWindowManager.reset();
        isServiceRunning = false;
    }

    public void updatePlayState(boolean isPlaying) {
        floatingWindowManager.updatePlayState(isPlaying);
    }

    public void updateSettings(String settings) {
        floatingWindowManager.updateSettings(settings);
    }

    public boolean isRunning() {
        return floatingWindowManager.isShowing();
    }

    public void hide() {
        floatingWindowManager.hide();
    }
}