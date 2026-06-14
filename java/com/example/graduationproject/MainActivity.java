package com.example.graduationproject;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.view.GravityCompat;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.fragment.app.Fragment;
import com.example.graduationproject.auth.LoginActivity;
import com.example.graduationproject.auth.TokenManager;
import com.example.graduationproject.core.PermissionController;
import com.example.graduationproject.core.TTSController;
import com.example.graduationproject.fragments.*;
import com.example.graduationproject.network.ApiClient;
import com.example.graduationproject.tts.*;
import com.example.graduationproject.utils.CenterToast;
import com.google.android.material.navigation.NavigationView;
import okhttp3.*;
import org.json.JSONObject;
import java.io.IOException;
import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity";
    private static final int REQUEST_OVERLAY = 100;
    private static final int REQUEST_DOWNLOAD_FOLDER = 200;

    private DrawerLayout drawer;
    private NavigationView nav;
    private TTSController tts;
    private TokenManager token;
    private byte[] pendingAudioData = null;

    /** 静态持有实例，供 FloatingWindowManager 调用 */
    private static MainActivity instance = null;

    /** 引擎名称 → 引擎实例映射（用于后端恢复时动态创建引擎对象） */
    private Map<String, BaseTTSEngine> engineMap = new HashMap<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        instance = this;

        token = new TokenManager(this);
        if (!token.isLoggedIn()) {
            startActivity(new Intent(this, LoginActivity.class)
                    .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
            finish();
            return;
        }

        initEngineMap();
        initViews();
        initDrawer();
        initTTS();
        updateUserInfo();

        if (savedInstanceState == null) {
            switchFragment(new HomeFragment());
            nav.setCheckedItem(R.id.nav_home);
            getSupportActionBar().setTitle("主页");
        }
    }

    /** 初始化引擎映射表（与 TTSFragment 保持一致） */
    private void initEngineMap() {
        engineMap.put("千问", new QwenTTSEngine());
        engineMap.put("CosyVoice", new CosyVoiceTTSEngine());
        engineMap.put("Sambert", new SambertTTSEngine());
        engineMap.put("VibeVoice", new VibeVoiceEngine());
        engineMap.put("ChatterBox", new ChatterBoxEngine());
        engineMap.put("IndexTTS", new IndexTTSEngine());
        engineMap.put("VoxCPM", new VoxCPMEngine());
        engineMap.put("XTTS-v2", new XTTSv2Engine());
    }

    private void initViews() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        drawer = findViewById(R.id.drawer_layout);
        nav = findViewById(R.id.nav_view);
    }

    private void initDrawer() {
        ActionBarDrawerToggle toggle = new ActionBarDrawerToggle(this, drawer, findViewById(R.id.toolbar), 0, 0);
        drawer.addDrawerListener(toggle);
        toggle.syncState();

        nav.setNavigationItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) switchFragment(new HomeFragment());
            else if (id == R.id.nav_text_content) switchFragment(new TextContentFragment());
            else if (id == R.id.nav_tts) switchFragment(new TTSFragment());
            else if (id == R.id.nav_status) switchFragment(new StatusFragment());
            else if (id == R.id.nav_tips) switchFragment(new TipsFragment());
            else if (id == R.id.nav_user_center) switchFragment(new UserCenterFragment());
            else if (id == R.id.nav_logout) showLogoutDialog();

            item.setChecked(true);
            drawer.closeDrawer(GravityCompat.START);
            return true;
        });
    }

    private void initTTS() {
        tts = new TTSController(this);
        tts.setListener(new TTSController.TTSListener() {
            @Override
            public void onPlayStateChanged(boolean isPlaying) {
                runOnUiThread(() -> updateHomeStatus());
            }
            @Override
            public void onError(String error) {
                runOnUiThread(() -> CenterToast.show(MainActivity.this, "TTS错误: " + error));
            }
        });

        // TTS 初始化完成后，从后端恢复用户个性化设置
        restoreUserSettings();
    }

    /** 从后端获取用户设置并恢复到 TTS 引擎 */
    private void restoreUserSettings() {
        String username = token.getUsername();
        if (username == null || username.isEmpty()) return;

        String encodedUsername;
        try {
            encodedUsername = URLEncoder.encode(username, "UTF-8");
        } catch (Exception e) {
            encodedUsername = username;
        }

        String url = ApiClient.BASE_URL + "/user/settings?username=" + encodedUsername;
        Request request = new Request.Builder().url(url).get().build();

        ApiClient.getClient().newCall(request).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {
                Log.e(TAG, "获取用户设置失败，网络错误");
            }

            @Override public void onResponse(Call call, Response response) throws IOException {
                String result = response.body().string();
                try {
                    if (response.isSuccessful()) {
                        JSONObject json = new JSONObject(result);
                        TTSManager manager = tts.getManager();

                        // ── 恢复引擎 ──────────────────────────────────────────
                        String engineName = json.optString("engine", "");
                        if (!engineName.isEmpty() && engineMap.containsKey(engineName)) {
                            manager.setEngine(engineMap.get(engineName), engineName);
                            Log.d(TAG, "已恢复引擎: " + engineName);
                        }

                        // ── 恢复音色 ──────────────────────────────────────────
                        String voice = json.optString("voice", "");
                        if (!voice.isEmpty()) {
                            manager.setVoice(voice);
                            Log.d(TAG, "已恢复音色: " + voice);
                        }

                        // ── 恢复倍速 ──────────────────────────────────────────
                        float speed = (float) json.optDouble("speed", 1.0);
                        manager.setSpeed(speed);
                        Log.d(TAG, "已恢复倍速: " + speed);

                        // ── 恢复捕获文本 ──────────────────────────────────────
                        String capturedText = json.optString("captured_text", "");
                        if (!capturedText.isEmpty()) {
                            manager.setCapturedText(capturedText);
                            FloatingWindowManager.getInstance().setPlayedText(capturedText);
                            Log.d(TAG, "已恢复捕获文本，长度: " + capturedText.length());
                        }

                    } else {
                        Log.e(TAG, "获取用户设置失败: " + response.code());
                    }
                } catch (Exception e) {
                    Log.e(TAG, "解析用户设置异常", e);
                }
            }
        });
    }

    /** 退出登录时将当前本地设置同步到后端（异步，不阻塞退出） */
    private void logoutUserSettings() {
        String username = token.getUsername();
        if (username == null || username.isEmpty()) return;

        String encodedUsername;
        try {
            encodedUsername = URLEncoder.encode(username, "UTF-8");
        } catch (Exception e) {
            encodedUsername = username;
        }

        try {
            JSONObject body = new JSONObject();
            TTSManager manager = tts.getManager();
            body.put("engine", manager.getCurrentEngineName());
            body.put("voice", manager.getCurrentVoice());
            body.put("speed", manager.getSpeed());
            body.put("captured_text", manager.getCapturedText());

            String url = ApiClient.BASE_URL + "/user/settings?username=" + encodedUsername;
            Request request = new Request.Builder()
                    .url(url)
                    .put(RequestBody.create(body.toString(), MediaType.parse("application/json")))
                    .build();

            ApiClient.getClient().newCall(request).enqueue(new Callback() {
                @Override public void onFailure(Call call, IOException e) {
                    Log.w(TAG, "退出登录时同步设置失败（网络错误）");
                }
                @Override public void onResponse(Call call, Response response) {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "退出登录时已同步设置到后端");
                    } else {
                        Log.w(TAG, "退出登录时同步设置失败: " + response.code());
                    }
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "退出登录同步设置异常", e);
        }
    }

    private void updateUserInfo() {
        View header = nav.getHeaderView(0);
        TextView tv = header.findViewById(R.id.tv_username);
        String username = token.getUsername();
        if (tv != null) tv.setText(username != null ? username : "用户");
    }

    private void updateHomeStatus() {
        Fragment f = getSupportFragmentManager().findFragmentById(R.id.fragment_container);
        if (f instanceof HomeFragment) {
            ((HomeFragment) f).updateStatus();
        }
    }

    private void switchFragment(Fragment fragment) {
        getSupportFragmentManager()
                .beginTransaction()
                .replace(R.id.fragment_container, fragment)
                .commit();
    }

    // ========== SAF 下载目录选择器 ==========
    public void openDownloadPicker(byte[] audioData) {
        this.pendingAudioData = audioData;

        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            intent.putExtra("android.content.extra.INITIAL_URI",
                    android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI);
        }

        startActivityForResult(intent, REQUEST_DOWNLOAD_FOLDER);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_OVERLAY) {
            if (new PermissionController(this).hasOverlayPermission()) {
                startService();
            }
            return;
        }

        if (requestCode == REQUEST_DOWNLOAD_FOLDER) {
            if (resultCode == RESULT_OK && data != null) {
                Uri selectedUri = data.getData();
                if (selectedUri != null && pendingAudioData != null) {
                    FloatingWindowManager.getInstance().onDownloadDirectorySelected(selectedUri, pendingAudioData);
                }
            }
            pendingAudioData = null;
        }
    }

    // ========== 服务控制方法 ==========
    public void startService() {
        PermissionController perm = new PermissionController(this);
        if (!perm.hasOverlayPermission()) {
            CenterToast.showLong(this, "请先开启悬浮窗权限");
            perm.requestOverlayPermission(REQUEST_OVERLAY);
            return;
        }
        if (!perm.hasAccessibilityPermission()) {
            CenterToast.show(this, "请先开启无障碍服务");
            perm.openAccessibilitySettings();
            return;
        }
        tts.startService();
        updateHomeStatus();
    }

    public void stopService() {
        tts.stopService();
        updateHomeStatus();
    }

    public boolean isServiceRunning() {
        return tts.isServiceRunning();
    }

    public boolean isOverlayPermissionGranted() {
        return new PermissionController(this).hasOverlayPermission();
    }

    public boolean isAccessibilityServiceGranted() {
        return new PermissionController(this).hasAccessibilityPermission();
    }

    public void openOverlayPermissionSettings() {
        new PermissionController(this).requestOverlayPermission(REQUEST_OVERLAY);
    }

    public void openAccessibilityServiceSettings() {
        new PermissionController(this).openAccessibilitySettings();
    }

    // ========== 退出登录 ==========
    private void showLogoutDialog() {
        new AlertDialog.Builder(this)
                .setTitle("退出登录")
                .setMessage("确定要退出登录吗？")
                .setPositiveButton("确定", (d, w) -> performLogout())
                .setNegativeButton("取消", null)
                .show();
    }

    private void performLogout() {
        // ── 1. 停止悬浮窗服务（必须先 stop 再 release，否则窗口删不掉）──
        if (tts != null) {
            tts.stopService();  // 内部调用 hide()，真正关闭悬浮窗
            tts.release();
        }

        // ── 2. 退出登录前同步当前设置到后端（异步，不阻塞退出）──────────
        logoutUserSettings();

        // ── 3. 清除本地 Token，跳转到登录页 ──────────────────────────
        token.clear();
        startActivity(new Intent(this, LoginActivity.class)
                .setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
        finish();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateHomeStatus();
    }

    @Override
    public void onBackPressed() {
        if (drawer.isDrawerOpen(GravityCompat.START)) {
            drawer.closeDrawer(GravityCompat.START);
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (tts != null) tts.release();
        instance = null;
    }

    public static MainActivity getInstance() {
        return instance;
    }
}
