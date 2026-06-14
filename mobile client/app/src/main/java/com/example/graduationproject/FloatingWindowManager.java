package com.example.graduationproject;

import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.net.Uri;
import android.os.Build;
import android.provider.DocumentsContract;
import android.util.Log;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageButton;
import android.widget.SeekBar;
import android.widget.TextView;
import com.example.graduationproject.tts.TTSManager;
import com.example.graduationproject.utils.AudioPlayer;
import com.example.graduationproject.utils.CenterToast;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class FloatingWindowManager {

    private static final String TAG = "FloatingWindowManager";
    private static FloatingWindowManager instance;
    private WindowManager windowManager;
    private View floatingView;
    private Context context;
    private boolean isShowing = false;

    /** 用户上次选择的目录 URI（SAF 持久化后可在会话期间复用） */
    private Uri lastSelectedDirectoryUri = null;

    private int initialX, initialY;
    private float initialTouchX, initialTouchY;

    private ImageButton btnPlayPause;
    private ImageButton btnStop;
    private ImageButton btnDownload;
    private TextView tvStatus;
    private TextView tvCurrentSettings;

    private boolean isModelSelected = false;
    private ImageButton btnSpeed;
    private TextView tvSpeed;
    private float[] speedValues = {0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f};
    private int speedIndex = 2;
    private String[] speedTexts = {"0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"};

    /** 保存用户点击播放时的文本（用于文字内容页面展示） */
    private String playedText = "";

    // ========== 进度条相关 ==========
    private View layoutProgress;
    private SeekBar seekbarProgress;
    private TextView tvCurrentTime;
    private TextView tvTotalTime;
    private boolean isUserSeeking = false; // 标记用户是否正在拖动

    private FloatingWindowManager() {}

    public static FloatingWindowManager getInstance() {
        if (instance == null) {
            instance = new FloatingWindowManager();
        }
        return instance;
    }

    public void init(Context context) {
        this.context = context;
        windowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
    }

    private void showCenterToast(String message) {
        CenterToast.show(context, message);
    }

    public void show() {
        if (isShowing || windowManager == null) return;

        floatingView = LayoutInflater.from(context).inflate(R.layout.floating_window, null);

        WindowManager.LayoutParams params = new WindowManager.LayoutParams();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            params.type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            params.type = WindowManager.LayoutParams.TYPE_PHONE;
        }

        params.format = PixelFormat.TRANSLUCENT;
        params.flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;
        params.gravity = Gravity.TOP | Gravity.START;
        params.width = WindowManager.LayoutParams.MATCH_PARENT;
        params.height = WindowManager.LayoutParams.WRAP_CONTENT;

        int screenHeight = context.getResources().getDisplayMetrics().heightPixels;
        params.x = 0;
        params.y = screenHeight - 200;

        btnPlayPause = floatingView.findViewById(R.id.btn_play_pause);
        btnStop = floatingView.findViewById(R.id.btn_stop);
        btnDownload = floatingView.findViewById(R.id.btn_download);
        tvStatus = floatingView.findViewById(R.id.tv_status);
        tvCurrentSettings = floatingView.findViewById(R.id.tv_current_settings);
        ImageButton btnClose = floatingView.findViewById(R.id.btn_close);

        // ========== 进度条控件初始化 ==========
        layoutProgress = floatingView.findViewById(R.id.layout_progress);
        seekbarProgress = floatingView.findViewById(R.id.seekbar_progress);
        tvCurrentTime = floatingView.findViewById(R.id.tv_current_time);
        tvTotalTime = floatingView.findViewById(R.id.tv_total_time);

        // 进度条拖动监听
        seekbarProgress.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (fromUser) {
                    TTSManager ttsManager = TTSManager.getInstance();
                    if (ttsManager != null) {
                        AudioPlayer player = ttsManager.getAudioPlayer();
                        if (player != null) {
                            long duration = player.getDuration();
                            long seekPos = (long) progress * duration / 100;
                            player.seekTo(seekPos);
                            tvCurrentTime.setText(formatTime(seekPos));
                        }
                    }
                }
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {
                isUserSeeking = true;
            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                isUserSeeking = false;
            }
        });

        btnSpeed = floatingView.findViewById(R.id.btn_speed);
        tvSpeed = floatingView.findViewById(R.id.tv_speed);
        tvSpeed.setText(speedTexts[speedIndex]);

        btnSpeed.setOnClickListener(v -> {
            speedIndex = (speedIndex + 1) % speedValues.length;
            float newSpeed = speedValues[speedIndex];
            tvSpeed.setText(speedTexts[speedIndex]);

            TTSManager ttsManager = TTSManager.getInstance();
            if (ttsManager != null) {
                ttsManager.setSpeed(newSpeed);
            }
            showCenterToast("播放速度: " + speedTexts[speedIndex]);
        });

        btnClose.setOnClickListener(v -> {
            if (context instanceof MainActivity) {
                ((MainActivity) context).stopService();
            } else {
                TTSManager.getInstance().stop();
                hide();
            }
        });

        tvCurrentSettings.setText("请先在侧边栏选择模型和音色");

        // ========== 播放按钮逻辑 ==========
        btnPlayPause.setOnClickListener(v -> {
            if (!isModelSelected) {
                showCenterToast("请先在侧边栏选择模型和音色");
                return;
            }

            TTSManager ttsManager = TTSManager.getInstance();

            if (ttsManager.isPlaying()) {
                ttsManager.pause();
                btnPlayPause.setImageResource(R.drawable.ic_play);
                updateStatusText("已暂停");
            } else if (ttsManager.isPaused()) {
                ttsManager.resume();
                btnPlayPause.setImageResource(R.drawable.ic_pause);
                updateStatusText("播放中");
            } else {
                String currentText = com.example.graduationproject.services.TextCaptureService.getInstance() != null ?
                        com.example.graduationproject.services.TextCaptureService.getInstance().getCurrentScreenText() : "";
                if (currentText != null && !currentText.isEmpty()) {
                    playedText = currentText;
                    // ── 修复：点击播放时同步文字到 TTSManager（用于退出时保存到后端）─────────
                    ttsManager.setCapturedText(currentText);
                    Log.d(TAG, "播放时已保存捕获文字到 TTSManager，长度: " + currentText.length());
                    ttsManager.play(currentText);

                } else {
                    showCenterToast("没有捕获到文字");
                }
            }
        });

        // ========== 下载按钮逻辑 ==========
        btnDownload.setOnClickListener(v -> {
            TTSManager ttsManager = TTSManager.getInstance();
            byte[] audioData = ttsManager.getLastAudioData();

            if (audioData == null || audioData.length == 0) {
                showCenterToast("没有可下载的音频，请先播放");
                return;
            }

            if (context instanceof MainActivity) {
                ((MainActivity) context).openDownloadPicker(audioData);
            } else {
                showCenterToast("下载功能需要在主界面使用");
            }
        });

        btnStop.setOnClickListener(v -> {
            TTSManager.getInstance().stop();
            btnPlayPause.setImageResource(R.drawable.ic_play);
            updateStatusText("已就绪");
            hideProgressBar();
        });

        View rootView = floatingView.findViewById(R.id.floating_root);
        if (rootView == null) rootView = floatingView;

        rootView.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    initialX = params.x;
                    initialY = params.y;
                    initialTouchX = event.getRawX();
                    initialTouchY = event.getRawY();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    params.x = initialX + (int) (event.getRawX() - initialTouchX);
                    params.y = initialY + (int) (event.getRawY() - initialTouchY);
                    windowManager.updateViewLayout(floatingView, params);
                    return true;
            }
            return false;
        });

        try {
            windowManager.addView(floatingView, params);
            isShowing = true;
            updateStatusText("已就绪");
        } catch (Exception e) {
            Log.e(TAG, "悬浮窗显示失败", e);
        }
    }

    // ========== 进度条更新（由 TTSManager 在播放时调用）==========
    /**
     * 更新播放进度
     * @param currentPosition 当前播放位置（毫秒）
     * @param duration 音频总时长（毫秒）
     */
    public void updateProgress(long currentPosition, long duration) {
        if (floatingView == null || seekbarProgress == null || isUserSeeking) return;

        android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
        mainHandler.post(() -> {
            try {
                if (layoutProgress != null && layoutProgress.getVisibility() != View.VISIBLE) {
                    layoutProgress.setVisibility(View.VISIBLE);
                }

                if (duration > 0) {
                    int progress = (int) (currentPosition * 100 / duration);
                    seekbarProgress.setMax(100);
                    seekbarProgress.setProgress(progress);
                }

                if (tvCurrentTime != null) {
                    tvCurrentTime.setText(formatTime(currentPosition));
                }
                if (tvTotalTime != null) {
                    tvTotalTime.setText(formatTime(duration));
                }
            } catch (Exception e) {
                Log.w(TAG, "更新进度条失败: " + e.getMessage());
            }
        });
    }

    /**
     * 隐藏进度条
     */
    public void hideProgressBar() {
        if (floatingView == null) return;
        android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
        mainHandler.post(() -> {
            if (layoutProgress != null) {
                layoutProgress.setVisibility(View.GONE);
            }
            if (seekbarProgress != null) {
                seekbarProgress.setProgress(0);
            }
            if (tvCurrentTime != null) {
                tvCurrentTime.setText("0:00");
            }
        });
    }

    /**
     * 格式化时间（毫秒 -> mm:ss）
     */
    private String formatTime(long millis) {
        long seconds = millis / 1000;
        long minutes = seconds / 60;
        seconds = seconds % 60;
        return String.format(Locale.getDefault(), "%d:%02d", minutes, seconds);
    }

    // ========== SAF 选择结果回调 ==========
    public void onDownloadDirectorySelected(Uri directoryUri, byte[] audioData) {
        if (directoryUri == null || audioData == null || audioData.length == 0) {
            showCenterToast("没有可下载的音频");
            return;
        }

        try {
            final int takeFlags = Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION;
            context.getContentResolver().takePersistableUriPermission(directoryUri, takeFlags);
            lastSelectedDirectoryUri = directoryUri;
            Log.d(TAG, "已获取目录持久化权限: " + directoryUri);
        } catch (SecurityException e) {
            Log.w(TAG, "无法获取目录持久化权限，将使用临时权限", e);
        }

        saveAudioToDirectory(directoryUri, audioData);
    }

    private void saveAudioToDirectory(Uri directoryUri, byte[] audioData) {
        try {
            String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            boolean isWav = audioData.length > 12 &&
                    audioData[0] == 'R' && audioData[1] == 'I' &&
                    audioData[2] == 'F' && audioData[3] == 'F';
            String extension = isWav ? "wav" : "mp3";
            String mimeType = isWav ? "audio/wav" : "audio/mpeg";
            String fileName = "TTS_" + timeStamp + "." + extension;

            String treeDocId = DocumentsContract.getTreeDocumentId(directoryUri);
            Uri documentUri = DocumentsContract.buildDocumentUriUsingTree(directoryUri, treeDocId);

            Uri fileUri = DocumentsContract.createDocument(
                    context.getContentResolver(),
                    documentUri,
                    mimeType,
                    fileName
            );

            if (fileUri == null) {
                showCenterToast("无法创建文件，请重试");
                return;
            }

            OutputStream os = context.getContentResolver().openOutputStream(fileUri);
            if (os == null) {
                showCenterToast("无法打开文件流");
                return;
            }
            os.write(audioData);
            os.close();

            showCenterToast("已保存: " + fileName);
            Log.d(TAG, "音频已保存到: " + fileUri);

        } catch (Exception e) {
            Log.e(TAG, "保存音频失败", e);
            showCenterToast("保存失败: " + e.getMessage());
        }
    }

    private void updateStatusText(String status) {
        if (tvStatus != null) {
            switch (status) {
                case "播放中":
                    tvStatus.setText("● 播放中");
                    tvStatus.setTextColor(0xFF4CAF50);
                    break;
                case "已暂停":
                    tvStatus.setText("● 已暂停");
                    tvStatus.setTextColor(0xFFFF9800);
                    break;
                case "已就绪":
                    tvStatus.setText("● 已就绪");
                    tvStatus.setTextColor(0xFF4CAF50);
                    break;
                case "生成中":
                    tvStatus.setText("⏳ 生成中");
                    tvStatus.setTextColor(0xFF2196F3);
                    break;
            }
        }
    }

    public void updatePlaybackState(boolean isPlayingIcon, String statusText) {
        if (btnPlayPause != null) {
            if (isPlayingIcon) {
                btnPlayPause.setImageResource(R.drawable.ic_pause);
            } else {
                btnPlayPause.setImageResource(R.drawable.ic_play);
            }
        }
        if (tvStatus != null) {
            updateStatusText(statusText);
        }
    }

    public void updateSettings(String settings) {
        if (tvCurrentSettings != null) {
            tvCurrentSettings.setText(settings);
            tvCurrentSettings.setTextColor(0xFF9CA3AF);
            isModelSelected = true;
        }
    }

    public void reset() {
        isModelSelected = false;
        hideProgressBar();
        if (tvCurrentSettings != null) {
            tvCurrentSettings.setText("请先在侧边栏选择模型和音色");
            tvCurrentSettings.setTextColor(0xFFFF9800);
        }
        if (btnPlayPause != null) {
            btnPlayPause.setImageResource(R.drawable.ic_play);
        }
        if (tvStatus != null) {
            tvStatus.setText("● 已就绪");
            tvStatus.setTextColor(0xFF4CAF50);
        }
    }

    public void updatePlayState(boolean isPlaying) {
        if (btnPlayPause != null) {
            if (isPlaying) {
                btnPlayPause.setImageResource(R.drawable.ic_pause);
                updateStatusText("播放中");
            } else {
                btnPlayPause.setImageResource(R.drawable.ic_play);
                updateStatusText("已就绪");
            }
        }
    }

    public void hide() {
        if (isShowing && floatingView != null && windowManager != null) {
            try {
                windowManager.removeView(floatingView);
            } catch (Exception e) {
                Log.e(TAG, "移除悬浮窗失败", e);
            }
            floatingView = null;
            isShowing = false;
        }
    }

    public boolean isShowing() {
        return isShowing;
    }

    public String getPlayedText() {
        return playedText != null ? playedText : "";
    }

    public void setPlayedText(String text) {
        this.playedText = (text != null) ? text : "";
    }
}
