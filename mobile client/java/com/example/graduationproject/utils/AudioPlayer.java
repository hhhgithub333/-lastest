package com.example.graduationproject.utils;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import com.google.android.exoplayer2.ExoPlayer;
import com.google.android.exoplayer2.MediaItem;
import com.google.android.exoplayer2.PlaybackException;
import com.google.android.exoplayer2.Player;
import com.google.android.exoplayer2.audio.AudioAttributes;
import java.io.File;
import java.io.FileOutputStream;

public class AudioPlayer {
    private static final String TAG = "AudioPlayer";
    private ExoPlayer exoPlayer;
    private File tempFile;
    private Context context;
    private boolean isPlaying = false;
    private float currentSpeed = 1.0f;
    private OnCompletionListener onCompletionListener;

    // 主线程 Handler
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    // 进度回调
    private OnProgressListener onProgressListener;
    private final Handler progressHandler = new Handler(Looper.getMainLooper());
    private boolean isProgressTracking = false;
    private static final int PROGRESS_UPDATE_INTERVAL_MS = 100; // 每100ms更新一次

    public interface OnCompletionListener {
        void onComplete();
    }

    public interface OnProgressListener {
        /**
         * 播放进度更新回调
         * @param currentPosition 当前播放位置（毫秒）
         * @param duration 音频总时长（毫秒）
         */
        void onProgress(long currentPosition, long duration);
    }

    public void init(Context context) {
        this.context = context;
        Log.d(TAG, "AudioPlayer 初始化完成");
    }

    /**
     * 设置播放进度监听器
     */
    public void setOnProgressListener(OnProgressListener listener) {
        this.onProgressListener = listener;
    }

    /**
     * 开始进度跟踪
     */
    private void startProgressTracking() {
        if (isProgressTracking) return;
        isProgressTracking = true;

        progressHandler.post(new Runnable() {
            @Override
            public void run() {
                if (!isProgressTracking || exoPlayer == null) return;

                if (exoPlayer.isPlaying()) {
                    long position = exoPlayer.getCurrentPosition();
                    long duration = exoPlayer.getDuration();
                    if (onProgressListener != null && duration > 0) {
                        onProgressListener.onProgress(position, duration);
                    }
                }
                // 继续轮询
                if (isProgressTracking) {
                    progressHandler.postDelayed(this, PROGRESS_UPDATE_INTERVAL_MS);
                }
            }
        });
    }

    /**
     * 停止进度跟踪
     */
    private void stopProgressTracking() {
        isProgressTracking = false;
        progressHandler.removeCallbacksAndMessages(null);
    }

    /**
     * 实时调整倍速 — 必须在主线程调用
     */
    public void setSpeed(float speed) {
        this.currentSpeed = speed;
        if (exoPlayer != null) {
            mainHandler.post(() -> {
                if (exoPlayer != null) {
                    exoPlayer.setPlaybackSpeed(speed);
                    Log.d(TAG, "ExoPlayer 实时调整倍速: " + speed + "x");
                }
            });
        }
    }

    public float getSpeed() {
        return currentSpeed;
    }

    public void setOnCompletionListener(OnCompletionListener listener) {
        this.onCompletionListener = listener;
    }

    /**
     * 统一使用 ExoPlayer 播放所有音频（必须在主线程调用）
     */
    public void play(byte[] data, String engineName) {
        mainHandler.post(() -> {
            try {
                playInternal(data, engineName);
            } catch (Exception e) {
                Log.e(TAG, "播放失败", e);
                if (onCompletionListener != null) {
                    onCompletionListener.onComplete();
                }
            }
        });
    }

    /**
     * 实际的播放逻辑（在主线程执行）
     */
    private void playInternal(byte[] data, String engineName) {
        try {
            stopInternal();

            String suffix = ".mp3";
            boolean isWav = data.length > 12 &&
                    data[0] == 'R' && data[1] == 'I' &&
                    data[2] == 'F' && data[3] == 'F';

            if (isWav || "chatterbox".equals(engineName)) {
                suffix = ".wav";
            }

            tempFile = new File(context.getCacheDir(), "tts_" + System.currentTimeMillis() + suffix);
            FileOutputStream fos = new FileOutputStream(tempFile);
            fos.write(data);
            fos.close();

            if (exoPlayer == null) {
                exoPlayer = new ExoPlayer.Builder(context).build();
            }

            AudioAttributes audioAttributes = new AudioAttributes.Builder()
                    .setUsage(com.google.android.exoplayer2.C.USAGE_MEDIA)
                    .setContentType(com.google.android.exoplayer2.C.AUDIO_CONTENT_TYPE_MUSIC)
                    .build();
            exoPlayer.setAudioAttributes(audioAttributes, true);
            exoPlayer.setPlaybackSpeed(currentSpeed);
            Log.d(TAG, "ExoPlayer 开始播放，初始倍速: " + currentSpeed + "x, 格式: " + suffix);

            MediaItem mediaItem = MediaItem.fromUri(tempFile.getAbsolutePath());
            exoPlayer.setMediaItem(mediaItem);
            exoPlayer.prepare();
            exoPlayer.play();
            isPlaying = true;

            exoPlayer.removeListener(playerListener);
            exoPlayer.addListener(playerListener);

            // 开始进度跟踪
            startProgressTracking();

        } catch (Exception e) {
            Log.e(TAG, "播放失败", e);
            if (onCompletionListener != null) {
                onCompletionListener.onComplete();
            }
        }
    }

    // 监听器单独定义，避免重复添加
    private final Player.Listener playerListener = new Player.Listener() {
        @Override
        public void onPlaybackStateChanged(int playbackState) {
            if (playbackState == Player.STATE_ENDED) {
                mainHandler.post(() -> {
                    stop();
                    if (onCompletionListener != null) {
                        onCompletionListener.onComplete();
                    }
                });
            }
        }

        @Override
        public void onPlayerError(PlaybackException error) {
            Log.e(TAG, "ExoPlayer 播放错误: " + error.getMessage());
            mainHandler.post(() -> {
                stop();
                if (onCompletionListener != null) {
                    onCompletionListener.onComplete();
                }
            });
        }
    };

    /**
     * 内部停止方法（必须在主线程调用）
     */
    private void stopInternal() {
        stopProgressTracking();
        if (exoPlayer != null) {
            try {
                exoPlayer.stop();
                exoPlayer.release();
            } catch (Exception e) {
                Log.e(TAG, "释放 ExoPlayer 失败", e);
            }
            exoPlayer = null;
        }
        isPlaying = false;

        if (tempFile != null && tempFile.exists()) {
            tempFile.delete();
            tempFile = null;
        }
    }

    public void pause() {
        mainHandler.post(() -> {
            if (exoPlayer != null && exoPlayer.isPlaying()) {
                exoPlayer.pause();
                isPlaying = false;
                stopProgressTracking();
                Log.d(TAG, "暂停播放");
            }
        });
    }

    public void resume() {
        mainHandler.post(() -> {
            if (exoPlayer != null && !exoPlayer.isPlaying()) {
                exoPlayer.play();
                isPlaying = true;
                startProgressTracking();
                Log.d(TAG, "恢复播放");
            }
        });
    }

    public void stop() {
        mainHandler.post(() -> {
            stopInternal();
        });
    }

    /**
     * 获取当前播放位置（毫秒）
     */
    public long getCurrentPosition() {
        if (exoPlayer != null) {
            return exoPlayer.getCurrentPosition();
        }
        return 0;
    }

    /**
     * 获取音频总时长（毫秒）
     */
    public long getDuration() {
        if (exoPlayer != null) {
            long duration = exoPlayer.getDuration();
            return duration > 0 ? duration : 0;
        }
        return 0;
    }

    /**
     * 跳转到指定位置（毫秒）
     */
    public void seekTo(long positionMs) {
        mainHandler.post(() -> {
            if (exoPlayer != null) {
                exoPlayer.seekTo(positionMs);
                Log.d(TAG, "跳转至: " + positionMs + "ms");
            }
        });
    }

    public boolean isPlaying() {
        return isPlaying;
    }

    public void release() {
        mainHandler.post(() -> {
            stopInternal();
        });
    }
}
