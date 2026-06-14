package com.example.graduationproject.auth;

import android.content.Context;
import android.content.SharedPreferences;

public class TokenManager {
    private static final String PREFS_NAME = "app_prefs";
    private static final String KEY_TOKEN = "token";
    private static final String KEY_USERNAME = "username";
    private static final String KEY_USER_ID = "user_id";
    private static final String KEY_CREATED_AT = "created_at";
    private final SharedPreferences prefs;

    public TokenManager(Context context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public void saveLogin(String token, String username, int userId, String createdAt) {
        prefs.edit().putString(KEY_TOKEN, token).putString(KEY_USERNAME, username)
                .putInt(KEY_USER_ID, userId).putString(KEY_CREATED_AT, createdAt)
                .putBoolean("is_logged_in", true).apply();
    }

    public boolean isLoggedIn() { return prefs.getBoolean("is_logged_in", false); }
    public String getToken() { return prefs.getString(KEY_TOKEN, null); }
    public String getUsername() { return prefs.getString(KEY_USERNAME, null); }
    public int getUserId() { return prefs.getInt(KEY_USER_ID, -1); }
    public String getCreatedAt() { return prefs.getString(KEY_CREATED_AT, null); }
    public void clear() { prefs.edit().clear().apply(); }
}