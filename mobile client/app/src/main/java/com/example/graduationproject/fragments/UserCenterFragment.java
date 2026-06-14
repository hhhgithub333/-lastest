//package com.example.graduationproject.fragments;
//
//import android.content.Intent;
//import android.os.Bundle;
//import android.view.LayoutInflater;
//import android.view.View;
//import android.view.ViewGroup;
//import android.widget.Button;
//import android.widget.TextView;
//import androidx.appcompat.app.AlertDialog;
//import androidx.fragment.app.Fragment;
//import com.example.graduationproject.MainActivity;
//import com.example.graduationproject.R;
//import com.example.graduationproject.auth.LoginActivity;
//import com.example.graduationproject.auth.TokenManager;
//
//public class UserCenterFragment extends Fragment {
//
//    private TextView tvUsername, tvUserId, tvCreatedAt;
//    private Button btnLogout;
//    private TokenManager tokenManager;
//
//    @Override
//    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
//        View view = inflater.inflate(R.layout.fragment_user_center, container, false);
//
//        tvUsername = view.findViewById(R.id.tv_username);
//        tvUserId = view.findViewById(R.id.tv_user_id);
//        tvCreatedAt = view.findViewById(R.id.tv_created_at);
//        btnLogout = view.findViewById(R.id.btn_logout);
//
//        tokenManager = new TokenManager(getActivity());
//        displayUserInfo();
//
//        btnLogout.setOnClickListener(v -> logout());
//        return view;
//    }
//
//    private void displayUserInfo() {
//        String username = tokenManager.getUsername();
//        int userId = tokenManager.getUserId();
//        String createdAt = tokenManager.getCreatedAt();
//
//        tvUsername.setText(username != null ? username : "未登录");
//        tvUserId.setText(userId != -1 ? String.valueOf(userId) : "未知");
//        tvCreatedAt.setText(createdAt != null ? createdAt : "暂无");
//    }
//
//    private void logout() {
//        new AlertDialog.Builder(getActivity())
//                .setTitle("退出登录")
//                .setMessage("确定要退出登录吗？")
//                .setPositiveButton("确定", (dialog, which) -> performLogout())
//                .setNegativeButton("取消", null)
//                .show();
//    }
//
//    private void performLogout() {
//        if (getActivity() instanceof MainActivity) {
//            ((MainActivity) getActivity()).stopService();
//        }
//        tokenManager.clear();
//        Intent intent = new Intent(getActivity(), LoginActivity.class);
//        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
//        startActivity(intent);
//        getActivity().finish();
//    }
//}


package com.example.graduationproject.fragments;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.Fragment;
import com.example.graduationproject.MainActivity;
import com.example.graduationproject.R;
import com.example.graduationproject.auth.LoginActivity;
import com.example.graduationproject.auth.TokenManager;
import com.example.graduationproject.network.ApiClient;
import com.example.graduationproject.tts.TTSManager;
import okhttp3.*;
import org.json.JSONObject;
import java.io.IOException;
import java.net.URLEncoder;

public class UserCenterFragment extends Fragment {
    private static final String TAG = "UserCenterFragment";
    private TextView tvUsername, tvUserId, tvCreatedAt;
    private Button btnLogout;
    private TokenManager tokenManager;
    private OkHttpClient client;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_user_center, container, false);

        tvUsername = view.findViewById(R.id.tv_username);
        tvUserId = view.findViewById(R.id.tv_user_id);
        tvCreatedAt = view.findViewById(R.id.tv_created_at);
        btnLogout = view.findViewById(R.id.btn_logout);

        tokenManager = new TokenManager(getActivity());
        client = ApiClient.getClient();
        displayUserInfo();

        btnLogout.setOnClickListener(v -> logout());
        return view;
    }

    private void displayUserInfo() {
        String username = tokenManager.getUsername();
        int userId = tokenManager.getUserId();
        String createdAt = tokenManager.getCreatedAt();

        tvUsername.setText(username != null ? username : "未登录");
        tvUserId.setText(userId != -1 ? String.valueOf(userId) : "未知");
        tvCreatedAt.setText(createdAt != null ? createdAt : "暂无");
    }

    private void logout() {
        new AlertDialog.Builder(getActivity())
                .setTitle("退出登录")
                .setMessage("确定要退出登录吗？")
                .setPositiveButton("确定", (dialog, which) -> performLogout())
                .setNegativeButton("取消", null)
                .show();
    }

    private void performLogout() {
        // ── 退出前，将当前 TTS 设置保存到后端 ────────────────
        saveSettingsToBackend();

        if (getActivity() instanceof MainActivity) {
            ((MainActivity) getActivity()).stopService();
        }
        tokenManager.clear();
        Intent intent = new Intent(getActivity(), LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        if (getActivity() != null) getActivity().finish();
    }

    /**
     * 将当前 TTS 设置异步保存到后端
     * 引擎和音色已由 TTSManager 自动保存到本地 SharedPreferences，
     * 此处再同步到后端数据库，供其他设备登录时恢复。
     */
    private void saveSettingsToBackend() {
        String username = tokenManager.getUsername();
        if (username == null || username.isEmpty()) return;

        TTSManager ttsManager = TTSManager.getInstance();

        try {
            JSONObject body = new JSONObject();
            body.put("engine", ttsManager.getCurrentEngineName());
            body.put("voice", ttsManager.getCurrentVoice());
            body.put("speed", ttsManager.getSpeed());
            // 参考音频路径：本地文件路径，没有则传 null
            body.put("reference_audio_path", JSONObject.NULL);
            body.put("captured_text", ttsManager.getCapturedText());

            String encodedUsername;
            try {
                encodedUsername = URLEncoder.encode(username, "UTF-8");
            } catch (Exception e) {
                encodedUsername = username;
            }
            String url = ApiClient.BASE_URL + "/user/settings?username=" + encodedUsername;
            Request request = new Request.Builder()
                    .url(url)
                    .put(RequestBody.create(body.toString(), MediaType.parse("application/json")))
                    .build();

            // 使用同步请求（因为 performLogout 本身就是异步的，不影响用户体验）
            Response response = client.newCall(request).execute();
            if (response.isSuccessful()) {
                Log.d(TAG, "用户设置已保存到后端");
            } else {
                Log.e(TAG, "保存用户设置失败: " + response.code());
            }
            response.close();
        } catch (Exception e) {
            Log.e(TAG, "保存用户设置异常", e);
        }
    }
}
