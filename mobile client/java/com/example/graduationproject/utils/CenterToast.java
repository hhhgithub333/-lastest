package com.example.graduationproject.utils;

import android.content.Context;
import android.view.Gravity;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

public class CenterToast {
    public static void show(Context context, String message) { show(context, message, Toast.LENGTH_SHORT); }
    public static void showLong(Context context, String message) { show(context, message, Toast.LENGTH_LONG); }

    private static void show(Context context, String message, int duration) {
        Toast toast = new Toast(context);
        TextView textView = new TextView(context);
        textView.setText(message);
        textView.setTextSize(14);
        textView.setPadding(50, 25, 50, 25);
        textView.setBackgroundResource(android.R.drawable.toast_frame);
        toast.setView(textView);
        toast.setDuration(duration);
        int screenHeight = context.getResources().getDisplayMetrics().heightPixels;
        int yOffset = (int) (screenHeight * 0.25f);
        toast.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL, 0, yOffset);
        toast.show();
    }
}