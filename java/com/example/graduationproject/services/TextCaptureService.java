package com.example.graduationproject.services;

import android.accessibilityservice.AccessibilityService;
import android.graphics.Rect;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import com.example.graduationproject.FloatingWindowManager;
import com.example.graduationproject.tts.TTSManager;

import java.util.LinkedHashSet;
import java.util.Set;
import java.util.regex.Pattern;

public class TextCaptureService extends AccessibilityService {

    private static final String TAG = "TextCaptureService";

    // 单例
    private static volatile TextCaptureService instance;

    // 安全获取实例
    public static TextCaptureService getInstance() {
        return instance;
    }

    // 依赖
    private TTSManager ttsManager;

    // 状态缓存
    private String cachedScreenText = "";
    private String lastCapturedText = "";

    // 停止操作后才真正触发
    private final Handler debounceHandler = new Handler(Looper.getMainLooper());
    private static final long DEBOUNCE_DELAY_MS = 200;
    private final Runnable captureTask = this::performCapture;

    // 动态屏幕边界
    private int contentTopBoundary;
    private int contentBottomBoundary;

    private static final int MAX_LENGTH_DEFAULT = 700;
    private static final int MAX_LENGTH_READER  = 900;
    private static final int MAX_LENGTH_CHAT    = 700;

    // Emoji 正则表达式（编译一次，提高性能）
    private static final Pattern EMOJI_PATTERN = Pattern.compile(
            "[\\x{1F600}-\\x{1F64F}\\x{1F300}-\\x{1F5FF}\\x{1F680}-\\x{1F6FF}" +
                    "\\x{2600}-\\x{26FF}\\x{2700}-\\x{27BF}\\x{1F900}-\\x{1F9FF}" +
                    "\\x{1FA00}-\\x{1FA6F}\\x{1F700}-\\x{1F77F}\\x{1F780}-\\x{1F7FF}" +
                    "\\x{1F800}-\\x{1F8FF}\\x{1FA70}-\\x{1FAFF}]"
    );

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        ttsManager = TTSManager.getInstance();
        initScreenBoundaries();
        Log.d(TAG, "TextCaptureService 已启动，内容区: " + contentTopBoundary + " ~ " + contentBottomBoundary);
    }

    // 动态初始化屏幕边界
    private void initScreenBoundaries() {
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        int statusBarHeight = getStatusBarHeight();
        int navBarHeight = getNavigationBarHeight();

        contentTopBoundary = statusBarHeight;
        contentBottomBoundary = screenHeight - navBarHeight;

        Log.d(TAG, "屏幕高: " + screenHeight + ", 状态栏: " + statusBarHeight + ", 导航栏: " + navBarHeight);
    }

    private int getStatusBarHeight() {
        int resourceId = getResources().getIdentifier("status_bar_height", "dimen", "android");
        if (resourceId > 0) {
            return getResources().getDimensionPixelSize(resourceId);
        }
        return (int) (24 * getResources().getDisplayMetrics().density);
    }

    private int getNavigationBarHeight() {
        int resourceId = getResources().getIdentifier("navigation_bar_height", "dimen", "android");
        if (resourceId > 0) {
            return getResources().getDimensionPixelSize(resourceId);
        }
        return (int) (48 * getResources().getDisplayMetrics().density);
    }

    // 移除 emoji 表情符号
    private String removeEmoji(String text) {
        if (TextUtils.isEmpty(text))
            return text;
        String result = EMOJI_PATTERN.matcher(text).replaceAll("");
        // 将多个连续换行符替换为单个空格
        result = result.replaceAll("\\n\\s*\\n", " ");
        // 将换行符替换为空格
        result = result.replaceAll("\\n", " ");
        // 将多个连续空格替换为单个空格
        result = result.replaceAll("\\s+", " ");
        return result.trim();
    }

    // 事件接收
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        int eventType = event.getEventType();

        switch (eventType) {
            case AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED:
            case AccessibilityEvent.TYPE_VIEW_SCROLLED:
            case AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED:
            case AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED:
                break;
            default:
                return;
        }

        // Trailing Debounce：重置延迟任务
        debounceHandler.removeCallbacks(captureTask);
        debounceHandler.postDelayed(captureTask, DEBOUNCE_DELAY_MS);
    }

    // 实际执行捕获
    private void performCapture() {
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;

        String packageName = "";
        if (rootNode.getPackageName() != null) {
            packageName = rootNode.getPackageName().toString();
        }

        String capturedText = extractVisibleText(rootNode, packageName);
        rootNode.recycle();

        if (!TextUtils.isEmpty(capturedText) && !capturedText.equals(lastCapturedText)) {
            lastCapturedText = capturedText;
            cachedScreenText = capturedText;

            Log.d(TAG, "捕获文字(" + capturedText.length() + "字符) [" + packageName + "]: " + capturedText.substring(0, Math.min(80, capturedText.length())));

            FloatingWindowManager fwm = FloatingWindowManager.getInstance();
            if (fwm != null) {
                fwm.updatePlayState(false);
            }
        }
    }

    // 文本提取入口
    private String extractVisibleText(AccessibilityNodeInfo root, String packageName) {
        Set<String> texts = new LinkedHashSet<>();
        extractVisibleTexts(root, texts, 0, packageName);

        if (texts.isEmpty()) return "";

        StringBuilder sb = new StringBuilder();
        for (String text : texts) {
            if (sb.length() > 0) sb.append(" ");
            sb.append(text);
        }

        return truncateAtSentenceBoundary(sb.toString(), getMaxLength(packageName));
    }

    // 递归提取可见文本
    private void extractVisibleTexts(AccessibilityNodeInfo node, Set<String> texts, int depth, String packageName) {
        if (node == null || depth > 15) return;
        if (!node.isVisibleToUser()) return;
        if (!isInContentArea(node)) return;

        // 基于节点类名过滤UI控件
        if (isUIControlNode(node)) {
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) {
                    extractVisibleTexts(child, texts, depth + 1, packageName);
                    child.recycle();
                }
            }
            return;
        }

        // 优先取 text
        CharSequence text = node.getText();
        if (text != null && text.length() > 1) {
            String textStr = text.toString().trim();
            textStr = removeEmoji(textStr);  // 过滤 emoji
            if (isValidContent(textStr, packageName)) {
                texts.add(textStr);
            }
        } else {
            // 没有 text 时才使用 contentDescription
            CharSequence contentDesc = node.getContentDescription();
            if (contentDesc != null && contentDesc.length() > 1) {
                String descStr = contentDesc.toString().trim();
                descStr = removeEmoji(descStr);  // 过滤 emoji
                if (isValidContent(descStr, packageName)) {
                    texts.add(descStr);
                }
            }
        }

        // 递归子节点
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                extractVisibleTexts(child, texts, depth + 1, packageName);
                child.recycle();
            }
        }
    }

    // 基于节点类名判断是否为UI控件
    private boolean isUIControlNode(AccessibilityNodeInfo node) {
        CharSequence className = node.getClassName();
        if (className == null) return false;
        String cn = className.toString();

        // 按钮类
        if (cn.equals("android.widget.Button")
                || cn.equals("android.widget.ImageButton")
                || cn.equals("android.widget.CheckBox")
                || cn.equals("android.widget.RadioButton")
                || cn.equals("android.widget.Switch")
                || cn.equals("android.widget.ToggleButton")) {
            return true;
        }

        // 导航/Tab 类
        if (cn.equals("android.widget.TabWidget")
                || cn.contains("BottomNavigationView")
                || cn.contains("NavigationView")
                || cn.contains("Toolbar")
                || cn.contains("ActionBar")) {
            return true;
        }

        // 输入框
        if (cn.equals("android.widget.EditText")
                || cn.equals("android.widget.AutoCompleteTextView")) {
            return true;
        }

        // 可点击且文本极短的节点通常是按钮
        CharSequence text = node.getText();
        if (node.isClickable() && text != null && text.length() <= 4) {
            String textStr = text.toString().trim();
            if (!textStr.matches(".*[。！？…].*")) {
                return true;
            }
        }

        return false;
    }

    // 按句子边界截断
    private String truncateAtSentenceBoundary(String text, int maxLength) {
        if (text.length() <= maxLength) return text;

        String sub = text.substring(0, maxLength);
        int lastEnd = -1;

        char[] sentenceEnds = {'。', '！', '？', '…', '\n', '.', '!', '?'};
        for (char c : sentenceEnds) {
            int idx = sub.lastIndexOf(c);
            if (idx > lastEnd) lastEnd = idx;
        }

        if (lastEnd > maxLength / 2) {
            return sub.substring(0, lastEnd + 1);
        }

        int lastSpace = sub.lastIndexOf(' ');
        if (lastSpace > maxLength / 2) {
            return sub.substring(0, lastSpace);
        }

        return sub;
    }

    // 根据包名选择最大字符数
    private int getMaxLength(String packageName) {
        if (packageName == null) return MAX_LENGTH_DEFAULT;

        // 阅读类App
        if (packageName.contains("ireader")
                || packageName.contains("weread")
                || packageName.contains("legado")
                || packageName.contains("novel")
                || packageName.contains("book")) {
            return MAX_LENGTH_READER;
        }

        // 聊天类App
        if (packageName.contains("com.tencent.mm")
                || packageName.contains("com.tencent.mobileqq")
                || packageName.contains("com.sina.weibo")) {
            return MAX_LENGTH_CHAT;
        }

        return MAX_LENGTH_DEFAULT;
    }

    // 文本有效性验证
    private boolean isValidContent(String text, String packageName) {
        if (TextUtils.isEmpty(text)) return false;
        String trimmed = text.trim();

        if (trimmed.length() < 2) return false;
        if (trimmed.matches("^[\\d.,，、：:()（）\\s]+$")) return false;
        if (trimmed.matches("^[\\p{So}\\p{Sm}]+$")) return false;

        return true;
    }

    // 屏幕内容区判断
    private boolean isInContentArea(AccessibilityNodeInfo node) {
        if (node == null) return false;

        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);

        if (bounds.width() <= 0 || bounds.height() <= 0) return false;

        int centerY = (bounds.top + bounds.bottom) / 2;
        return centerY >= contentTopBoundary && centerY <= contentBottomBoundary;
    }

    // 获取当前屏幕文字
    public String getCurrentScreenText() {
        return cachedScreenText;
    }

    // 清空历史文本缓存
    public void clearHistory() {
        cachedScreenText = "";
        lastCapturedText = "";
        debounceHandler.removeCallbacks(captureTask);
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "无障碍服务中断");
        debounceHandler.removeCallbacks(captureTask);
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        debounceHandler.removeCallbacks(captureTask);
        instance = null;
        Log.d(TAG, "无障碍服务已销毁");
    }
}