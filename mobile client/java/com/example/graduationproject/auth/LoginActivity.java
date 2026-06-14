package com.example.graduationproject.auth;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.example.graduationproject.MainActivity;
import com.example.graduationproject.R;
import com.example.graduationproject.network.ApiClient;
import org.json.JSONObject;
import java.io.IOException;
import okhttp3.*;

public class LoginActivity extends AppCompatActivity {
    private EditText etUsername, etPassword;
    private Button btnLogin;
    private OkHttpClient client;
    private TokenManager tokenManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        tokenManager = new TokenManager(this);
        if (tokenManager.isLoggedIn()) {
            startActivity(new Intent(this, MainActivity.class));
            finish();
            return;
        }

        etUsername = findViewById(R.id.et_username);
        etPassword = findViewById(R.id.et_password);
        btnLogin = findViewById(R.id.btn_login);
        client = ApiClient.getClient();

        btnLogin.setOnClickListener(v -> login());
    }

    private void login() {
        String username = etUsername.getText().toString().trim();
        String password = etPassword.getText().toString().trim();
        if (TextUtils.isEmpty(username) || TextUtils.isEmpty(password)) {
            Toast.makeText(this, "请输入用户名和密码", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            JSONObject body = new JSONObject();
            body.put("username", username);
            body.put("password", password);
            Request request = new Request.Builder()
                    .url(ApiClient.BASE_URL + "/user/login")
                    .post(RequestBody.create(body.toString(), MediaType.parse("application/json")))
                    .build();
            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    runOnUiThread(() -> Toast.makeText(LoginActivity.this, "网络错误", Toast.LENGTH_SHORT).show());
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    String result = response.body().string();
                    runOnUiThread(() -> handleLoginResult(result, response.isSuccessful()));
                }
            });
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void handleLoginResult(String result, boolean isSuccessful) {
        try {
            if (isSuccessful) {
                JSONObject json = new JSONObject(result);
                String token = json.getString("access_token");
                JSONObject user = json.getJSONObject("user");
                tokenManager.saveLogin(token, user.getString("username"), user.getInt("id"), user.getString("created_at"));
                navigateToMain();
            } else {
                Toast.makeText(this, "登录失败", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "登录异常", Toast.LENGTH_SHORT).show();
        }
    }

    private void navigateToMain() {
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }
}
