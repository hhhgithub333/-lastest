package com.example.graduationproject.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.fragment.app.Fragment;
import androidx.core.content.ContextCompat;
import com.example.graduationproject.MainActivity;
import com.example.graduationproject.R;
import com.google.android.material.button.MaterialButton;

public class StatusFragment extends Fragment {

    private TextView tvServiceStatus;
    private TextView tvOverlayStatus;
    private TextView tvAccessibilityStatus;
    private ImageView ivServiceStatus;
    private ImageView ivOverlayStatus;
    private ImageView ivAccessibilityStatus;
    private MaterialButton btnGoSettings;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_status, container, false);

        // 初始化控件
        tvServiceStatus = view.findViewById(R.id.tv_service_status);
        tvOverlayStatus = view.findViewById(R.id.tv_overlay_status);
        tvAccessibilityStatus = view.findViewById(R.id.tv_accessibility_status);
        ivServiceStatus = view.findViewById(R.id.iv_service_status);
        ivOverlayStatus = view.findViewById(R.id.iv_overlay_status);
        ivAccessibilityStatus = view.findViewById(R.id.iv_accessibility_status);
        btnGoSettings = view.findViewById(R.id.btn_go_settings);

        // 设置按钮点击事件
        btnGoSettings.setOnClickListener(v -> {
            MainActivity activity = (MainActivity) getActivity();
            if (activity != null) {
                // 优先去开启未开启的权限
                if (!activity.isOverlayPermissionGranted()) {
                    activity.openOverlayPermissionSettings();
                } else if (!activity.isAccessibilityServiceGranted()) {
                    activity.openAccessibilityServiceSettings();
                }
            }
        });

        updateStatus();
        return view;
    }

    private void updateStatus() {
        if (getActivity() instanceof MainActivity) {
            MainActivity activity = (MainActivity) getActivity();
            boolean isServiceRunning = activity.isServiceRunning();
            boolean overlayGranted = activity.isOverlayPermissionGranted();
            boolean accessibilityGranted = activity.isAccessibilityServiceGranted();

            // 更新服务状态
            if (isServiceRunning) {
                tvServiceStatus.setText("权限已开启");
                tvServiceStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.teal_700));
                ivServiceStatus.setImageResource(R.drawable.ic_status_on);
                ivServiceStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.teal_700));
            } else {
                tvServiceStatus.setText("服务未启动");
                tvServiceStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.gray_500));
                ivServiceStatus.setImageResource(R.drawable.ic_status_off);
                ivServiceStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.gray_400));
            }

            // 更新悬浮窗权限状态
            if (overlayGranted) {
                tvOverlayStatus.setText("已开启");
                tvOverlayStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.teal_700));
                ivOverlayStatus.setImageResource(R.drawable.ic_status_on);
                ivOverlayStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.teal_700));
            } else {
                tvOverlayStatus.setText("未开启");
                tvOverlayStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.gray_500));
                ivOverlayStatus.setImageResource(R.drawable.ic_status_off);
                ivOverlayStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.gray_400));
            }

            // 更新无障碍服务状态
            if (accessibilityGranted) {
                tvAccessibilityStatus.setText("已开启");
                tvAccessibilityStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.teal_700));
                ivAccessibilityStatus.setImageResource(R.drawable.ic_status_on);
                ivAccessibilityStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.teal_700));
            } else {
                tvAccessibilityStatus.setText("未开启");
                tvAccessibilityStatus.setTextColor(ContextCompat.getColor(getContext(), R.color.gray_500));
                ivAccessibilityStatus.setImageResource(R.drawable.ic_status_off);
                ivAccessibilityStatus.setColorFilter(ContextCompat.getColor(getContext(), R.color.gray_400));
            }

            // 更新按钮状态和提示
            if (overlayGranted && accessibilityGranted) {
                if (isServiceRunning) {
                    btnGoSettings.setText("服务运行中");
                    btnGoSettings.setEnabled(false);
                } else {
                    btnGoSettings.setText("启动服务");
                    btnGoSettings.setEnabled(true);
                    btnGoSettings.setOnClickListener(v -> {
                        MainActivity act = (MainActivity) getActivity();
                        if (act != null) {
                            act.startService();
                        }
                    });
                }
            } else {
                btnGoSettings.setText("去设置");
                btnGoSettings.setEnabled(true);
                btnGoSettings.setOnClickListener(v -> {
                    MainActivity act = (MainActivity) getActivity();
                    if (act != null) {
                        if (!act.isOverlayPermissionGranted()) {
                            act.openOverlayPermissionSettings();
                        } else if (!act.isAccessibilityServiceGranted()) {
                            act.openAccessibilityServiceSettings();
                        }
                    }
                });
            }
        }
    }

    @Override
    public void onResume() {
        super.onResume();
        updateStatus();
    }
}