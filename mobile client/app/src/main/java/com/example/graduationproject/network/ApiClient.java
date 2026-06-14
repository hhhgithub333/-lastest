package com.example.graduationproject.network;

import okhttp3.OkHttpClient;
import java.util.concurrent.TimeUnit;

public class ApiClient {
    public static final String BASE_URL = "http://192.168.37.85:8000";
    private static OkHttpClient client;

    public static OkHttpClient getClient() {
        if (client == null) {
            client = new OkHttpClient.Builder()
                    .connectTimeout(600, TimeUnit.SECONDS)
                    .readTimeout(600, TimeUnit.SECONDS)
                    .writeTimeout(600, TimeUnit.SECONDS)
                    .build();
        }
        return client;
    }
}