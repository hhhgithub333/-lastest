package com.example.graduationproject.fragments;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.fragment.app.Fragment;
import com.example.graduationproject.FloatingWindowManager;
import com.example.graduationproject.R;
import com.example.graduationproject.tts.*;
import com.google.android.material.button.MaterialButton;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class TTSFragment extends Fragment {
    private static final String TAG = "TTSFragment";

    private Spinner spinnerModel, spinnerVoice;
    private TextView tvStatus;
    private TTSEngine currentEngine;
    private String currentVoice = "Cherry";
    private int currentModelIndex = 0;
    private int currentVoiceIndex = 0;

    // 参考音频相关 UI
    private LinearLayout layoutReferenceAudio;
    private Button btnSelectAudio;
    private TextView tvAudioFileName;
    private TextView tvClearAudio;

    // 保存按钮
    private MaterialButton btnSaveSettings;

    // 文件选择器
    private ActivityResultLauncher<Intent> audioPickerLauncher;

    // ── 哪些引擎支持/需要参考音频 ────────────────────────────────────
    private static final boolean[] NEEDS_REFERENCE_AUDIO = {
            false,  // 千问 TTS
            false,  // CosyVoice
            false,  // Sambert
            true,   // XTTS-v2
            true,   // VoxCPM
            true,   // ChatterBox
            false,  // VibeVoice
            true,   // IndexTTS
    };

    private static class ModelItem {
        String name; String[] voices; String[] voiceNames; TTSEngine engine;
        ModelItem(String name, String[] voices, String[] voiceNames, TTSEngine engine) {
            this.name = name; this.voices = voices; this.voiceNames = voiceNames; this.engine = engine;
        }
    }

    private ModelItem[] models = {
            new ModelItem("千问 TTS",
                    new String[]{"Cherry", "Serena", "Ethan", "Chelsie", "Momo", "Vivian", "Moon", "Maia", "Kai", "Nofish", "Bella", "Jennifer", "Ryan", "Katerina", "Aiden", "Eldric Sage", "Mia", "Mochi", "Bellona", "Vincent", "Bunny", "Neil", "Elias", "Arthur"},
                    new String[]{"🍒 Cherry - 芊悦", "⭐ Serena - 苏瑶", "👨 Ethan - 晨煦", "🌸 Chelsie - 千雪", "🐰 Momo - 茉兔", "💜 Vivian - 十三", "🌙 Moon - 月白", "📚 Maia - 四月", "🎸 Kai - 凯", "🐟 Nofish - 不吃鱼", "👶 Bella - 萌宝", "🎬 Jennifer - 詹妮弗", "🎭 Ryan - 甜茶", "👑 Katerina - 卡捷琳娜", "🍳 Aiden - 艾登", "🧓 Eldric Sage - 沧明子", "👧 Mia - 乖小妹", "🧒 Mochi - 沙小弥", "⚔️ Bellona - 燕铮莺", "🎸 Vincent - 田叔", "🐰 Bunny - 萌小姬", "📺 Neil - 阿闻", "🎓 Elias - 墨讲师", "👴 Arthur - 徐大爷"},
                    new QwenTTSEngine()),
            new ModelItem("CosyVoice",
                    new String[]{"longanyang", "longanhuan"},
                    new String[]{"🦁 龙安洋", "🦊 龙安欢"},
                    new CosyVoiceTTSEngine()),
            new ModelItem("Sambert",
                    new String[]{"zhinan", "zhiqi", "zhichu", "zhide", "zhijia", "zhiru", "zhiqian", "zhixiang", "zhiwei", "zhihao", "zhijing", "zhiming", "zhimo", "zhina", "zhishu", "zhistella", "zhiting", "zhixiao", "zhiya", "zhiye", "zhiying", "zhiyuan", "zhiyue", "zhigui", "zhishuo", "zhimiao-emo", "zhimao"},
                    new String[]{"👨 知楠", "👩 知琪", "👨 知厨", "👨 知德", "👩 知佳", "👩 知茹", "👩 知倩", "👨 知祥", "👩 知薇", "👨 知浩", "👩 知婧", "👨 知茗", "👨 知墨", "👩 知娜", "👨 知树", "👩 知莎", "👩 知婷", "👩 知笑", "👩 知雅", "👨 知晔", "👩 知颖", "👩 知媛", "👩 知悦", "👩 知柜", "👨 知硕", "👩 知妙", "👩 知猫"},
                    new SambertTTSEngine()),
            new ModelItem("XTTS-v2",
                    new String[]{"default"},
                    new String[]{"🎤 默认声音"},
                    new XTTSv2Engine()),
            new ModelItem("VoxCPM",
                    new String[]{"default"},
                    new String[]{"🎤 默认声音"},
                    new VoxCPMEngine()),
            new ModelItem("ChatterBox",
                    new String[]{"default"},
                    new String[]{"🎤 默认声音"},
                    new ChatterBoxEngine()),
            new ModelItem("VibeVoice",
                    new String[]{"en-Mike_man", "en-Emma_woman", "en-Carter_man", "en-Davis_man", "en-Frank_man", "en-Grace_woman", "jp-Spk0_man", "jp-Spk1_woman", "fr-Spk0_man", "fr-Spk1_woman"},
                    new String[]{"🇺🇸 Mike - 英文男声", "🇺🇸 Emma - 英文女声", "🇺🇸 Carter - 英文男声", "🇺🇸 Davis - 英文男声", "🇺🇸 Frank - 英文男声", "🇺🇸 Grace - 英文女声",  "🇯🇵 Spk0 - 日文男声", "🇯🇵 Spk1 - 日文女声", "🇫🇷 Spk0 - 法文男声", "🇫🇷 Spk1 - 法文女声"},
                    new VibeVoiceEngine()),
            new ModelItem("IndexTTS",
                    new String[]{"default"},
                    new String[]{"🎤 默认声音"},
                    new IndexTTSEngine()),
    };

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        audioPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                        Uri uri = result.getData().getData();
                        handleAudioFileSelected(uri);
                    }
                }
        );
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.activity_test_tts, container, false);
        spinnerModel = view.findViewById(R.id.spinner_model);
        spinnerVoice = view.findViewById(R.id.spinner_voice);
        tvStatus = view.findViewById(R.id.tv_tts_status);
        layoutReferenceAudio = view.findViewById(R.id.layout_reference_audio);
        btnSelectAudio = view.findViewById(R.id.btn_select_audio);
        tvAudioFileName = view.findViewById(R.id.tv_audio_filename);
        tvClearAudio = view.findViewById(R.id.tv_clear_audio);
        btnSaveSettings = view.findViewById(R.id.btn_save_settings);

        // ── 保存按钮点击事件 ───────────────────────────────
        btnSaveSettings.setOnClickListener(v -> saveAndSyncToFloating());

        // ── 初始化所有引擎（只调用一次）────────────────────────────
        for (ModelItem model : models) model.engine.init(getActivity(), "");

        // ── 构建 Spinner 数据 ────────────────────────────────────────
        String[] modelNames = new String[models.length];
        for (int i = 0; i < models.length; i++) modelNames[i] = models[i].name;
        ArrayAdapter<String> modelAdapter = new ArrayAdapter<>(getActivity(), R.layout.spinner_dropdown_item, modelNames);
        spinnerModel.setAdapter(modelAdapter);

        // ── 从 TTSManager 恢复上次的引擎/音色状态 ──────────────────
        TTSManager ttsManager = TTSManager.getInstance();
        String savedEngineName = ttsManager.getCurrentEngineName();
        String savedVoice = ttsManager.getCurrentVoice();

        boolean restored = false;
        if (savedEngineName != null) {
            for (int i = 0; i < models.length; i++) {
                if (models[i].name.equals(savedEngineName)) {
                    currentModelIndex = i;
                    currentEngine = models[i].engine;
                    spinnerModel.setSelection(i, false);
                    restored = true;
                    break;
                }
            }
        }
        if (!restored) {
            currentModelIndex = 0;
            currentEngine = models[0].engine;
            spinnerModel.setSelection(0, false);
        }

        // 更新音色下拉列表
        updateVoiceSpinner();

        // ✅ 修复：恢复音色时，如果找不到匹配的音色，使用默认音色（索引0）
        if (savedVoice != null && !savedVoice.isEmpty()) {
            String[] voices = models[currentModelIndex].voices;
            boolean found = false;
            for (int i = 0; i < voices.length; i++) {
                if (voices[i].equals(savedVoice)) {
                    currentVoiceIndex = i;
                    currentVoice = savedVoice;
                    spinnerVoice.setSelection(i, false);
                    found = true;
                    Log.d(TAG, "恢复音色成功: " + savedVoice);
                    break;
                }
            }
            if (!found) {
                // 该模型没有保存的音色，使用默认音色
                currentVoiceIndex = 0;
                currentVoice = voices[0];
                spinnerVoice.setSelection(0, false);
                // 同步更新到 TTSManager
                ttsManager.setVoice(currentVoice);
                Log.d(TAG, "音色 '" + savedVoice + "' 不在当前模型音色列表中，已重置为默认音色: " + currentVoice);
            }
        } else {
            // 没有保存的音色，使用默认音色
            currentVoiceIndex = 0;
            currentVoice = models[currentModelIndex].voices[0];
            spinnerVoice.setSelection(0, false);
            Log.d(TAG, "没有保存的音色，使用默认音色: " + currentVoice);
        }

        // ── 设置监听器（放在恢复状态之后）───────────────────────
        spinnerModel.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (position == currentModelIndex) return; // 防止重复触发

                currentModelIndex = position;
                currentEngine = models[position].engine;
                updateVoiceSpinner();
                updateReferenceAudioVisibility();

                // ✅ 切换模型后，检查当前音色是否在新模型的音色列表中
                String[] voices = models[currentModelIndex].voices;
                boolean voiceFound = false;
                for (int i = 0; i < voices.length; i++) {
                    if (voices[i].equals(currentVoice)) {
                        currentVoiceIndex = i;
                        voiceFound = true;
                        break;
                    }
                }
                if (!voiceFound) {
                    // 音色不存在，使用默认音色
                    currentVoiceIndex = 0;
                    currentVoice = voices[0];
                    spinnerVoice.setSelection(0, false);
                    Log.d(TAG, "切换模型后音色不存在，已重置为: " + currentVoice);
                } else {
                    spinnerVoice.setSelection(currentVoiceIndex, false);
                }
            }
            @Override public void onNothingSelected(AdapterView<?> parent) {}
        });

        spinnerVoice.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (position == currentVoiceIndex) return; // 防止重复触发

                currentVoiceIndex = position;
                currentVoice = models[currentModelIndex].voices[position];
            }
            @Override public void onNothingSelected(AdapterView<?> parent) {}
        });

        // ── 恢复参考音频 UI 状态 ─────────────────────────────────
        updateReferenceAudioVisibility();
        byte[] refAudio = ttsManager.getReferenceAudio();
        if (refAudio != null) {
            tvAudioFileName.setText("✅ 已选参考音频 (" + refAudio.length + " bytes)");
            tvClearAudio.setVisibility(View.VISIBLE);
            btnSelectAudio.setText("重新选择");
        } else {
            tvAudioFileName.setText("未选择文件");
            tvClearAudio.setVisibility(View.GONE);
            btnSelectAudio.setText("选择音频文件");
        }

        // ── 恢复状态栏文字 ─────────────────────────────────────
        String settingsText = models[currentModelIndex].name + " · " + models[currentModelIndex].voiceNames[currentVoiceIndex];
        tvStatus.setText("当前: " + settingsText);

        // ── 按钮点击 ─────────────────────────────────────────────
        btnSelectAudio.setOnClickListener(v -> openAudioPicker());
        tvClearAudio.setOnClickListener(v -> clearSelectedAudio());

        return view;
    }

    /** 根据当前引擎决定是否显示参考音频区域 */
    private void updateReferenceAudioVisibility() {
        if (layoutReferenceAudio == null) return;
        boolean needs = currentModelIndex < NEEDS_REFERENCE_AUDIO.length
                && NEEDS_REFERENCE_AUDIO[currentModelIndex];
        layoutReferenceAudio.setVisibility(needs ? View.VISIBLE : View.GONE);
    }

    /** 更新音色下拉列表，并保留当前选中的音色索引 */
    private void updateVoiceSpinner() {
        ModelItem model = models[currentModelIndex];
        String[] voices = model.voices;

        // ✅ 边界检查：确保 currentVoiceIndex 有效
        if (currentVoiceIndex >= voices.length) {
            currentVoiceIndex = 0;
        }

        ArrayAdapter<String> adapter = new ArrayAdapter<>(
                getActivity(), R.layout.spinner_dropdown_item, model.voiceNames
        );
        spinnerVoice.setAdapter(adapter);

        // ✅ 设置选中位置
        if (currentVoiceIndex < adapter.getCount()) {
            spinnerVoice.setSelection(currentVoiceIndex, false);
            currentVoice = voices[currentVoiceIndex];
        }
    }

    /** 打开系统文件选择器 */
    private void openAudioPicker() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("audio/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        audioPickerLauncher.launch(Intent.createChooser(intent, "选择参考音频"));
    }

    /** 处理选中的音频文件 */
    private void handleAudioFileSelected(Uri uri) {
        if (uri == null) return;
        try {
            InputStream is = requireContext().getContentResolver().openInputStream(uri);
            byte[] audioData = readAllBytesCompat(is);
            is.close();

            TTSManager.getInstance().setReferenceAudio(audioData);

            String fileName = getFileNameFromUri(uri);
            tvAudioFileName.setText("✅ 已选: " + fileName + " (" + formatSize(audioData.length) + ")");
            tvClearAudio.setVisibility(View.VISIBLE);
            btnSelectAudio.setText("重新选择");

            Toast.makeText(getContext(), "参考音频已加载，点击保存生效", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(getContext(), "读取音频失败: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    /** 清除已选的参考音频 */
    private void clearSelectedAudio() {
        TTSManager.getInstance().setReferenceAudio(null);

        tvAudioFileName.setText("未选择文件");
        tvClearAudio.setVisibility(View.GONE);
        btnSelectAudio.setText("选择音频文件");

        Toast.makeText(getContext(), "参考音频已清除，点击保存生效", Toast.LENGTH_SHORT).show();
    }

    /** 兼容低版本的 InputStream 读取全部字节 */
    private byte[] readAllBytesCompat(InputStream is) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] data = new byte[8192];
        int bytesRead;
        while ((bytesRead = is.read(data, 0, data.length)) != -1) {
            buffer.write(data, 0, bytesRead);
        }
        return buffer.toByteArray();
    }

    /** 从 Uri 获取文件名 */
    private String getFileNameFromUri(Uri uri) {
        String path = uri.getLastPathSegment();
        if (path != null && path.contains("/")) path = path.substring(path.lastIndexOf('/') + 1);
        return path != null ? path : "audio_file";
    }

    /** 格式化文件大小 */
    private String formatSize(int bytes) {
        if (bytes < 1024) return bytes + " B";
        else if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        else return String.format("%.1f MB", bytes / (1024.0 * 1024));
    }

    /**
     * 保存设置并同步到悬浮窗
     * 用户点击"保存"按钮时调用，将当前选择的引擎、音色、参考音频全部同步
     */
    private void saveAndSyncToFloating() {
        try {
            TTSManager ttsManager = TTSManager.getInstance();

            // 1. 获取当前选择的设置
            String engineName = models[currentModelIndex].name;
            String voiceId = currentVoiceIndex < models[currentModelIndex].voices.length
                    ? models[currentModelIndex].voices[currentVoiceIndex]
                    : "default";
            String voiceName = models[currentModelIndex].voiceNames[currentVoiceIndex];

            // 2. 应用到 TTSManager（这会自动保存到 SharedPreferences）
            ttsManager.setEngine(currentEngine, engineName);
            ttsManager.setVoice(voiceId);

            // 3. 参考音频已经在选择时设置到 TTSManager，无需重复设置

            // 4. 更新悬浮窗显示
            String settingsText = engineName + " · " + voiceName;
            FloatingWindowManager.getInstance().updateSettings(settingsText);

            // 5. 更新状态提示
            tvStatus.setText("✅ 已保存: " + settingsText);

            // 6. 显示成功提示
            Toast.makeText(getContext(), "设置已保存，悬浮窗将使用新配置", Toast.LENGTH_SHORT).show();

            Log.d(TAG, "保存设置 - 引擎: " + engineName + ", 音色: " + voiceId);

        } catch (Exception e) {
            Log.e(TAG, "保存设置失败: " + e.getMessage(), e);
            Toast.makeText(getContext(), "保存失败: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        for (ModelItem model : models) model.engine.release();
    }
}