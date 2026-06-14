package com.example.graduationproject.fragments;

import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.ImageButton;
import androidx.fragment.app.Fragment;
import com.example.graduationproject.FloatingWindowManager;
import com.example.graduationproject.R;
import com.google.android.material.button.MaterialButton;

/**
 * 文字内容页面
 * 展示用户点击播放时保存的文本内容
 */
public class TextContentFragment extends Fragment {

    private TextView tvCapturedText;
    private TextView tvTextLength;
    private ImageButton btnRefresh;
    private MaterialButton btnClear;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_text_content, container, false);

        tvCapturedText = view.findViewById(R.id.tv_captured_text);
        tvTextLength = view.findViewById(R.id.tv_text_length);
        btnRefresh = view.findViewById(R.id.btn_refresh);
        btnClear = view.findViewById(R.id.btn_clear);

        // 启用 TextView 滚动功能
        tvCapturedText.setMovementMethod(ScrollingMovementMethod.getInstance());

        // 刷新按钮：从 FloatingWindowManager 获取播放时保存的文本
        btnRefresh.setOnClickListener(v -> updateTextContent());

        // 清空按钮：清空当前显示的文字
        btnClear.setOnClickListener(v -> {
            tvCapturedText.setText("");
            tvTextLength.setText("0 字符");
        });

        // 初始加载一次
        updateTextContent();

        return view;
    }

    @Override
    public void onResume() {
        super.onResume();
        // 每次回到页面时刷新一次文字内容
        updateTextContent();
    }

    /**
     * 从 FloatingWindowManager 获取播放时保存的文本并更新界面
     */
    private void updateTextContent() {
        String text = FloatingWindowManager.getInstance().getPlayedText();

        if (text == null || text.isEmpty()) {
            tvCapturedText.setText("暂无播放记录，请先点击播放按钮朗读文字，内容将显示在此处");
            tvTextLength.setText("0 字符");
        } else {
            tvCapturedText.setText(text);
            tvTextLength.setText(text.length() + " 字符");
        }
    }
}
