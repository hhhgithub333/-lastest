package com.example.graduationproject.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import androidx.fragment.app.Fragment;
import com.example.graduationproject.MainActivity;
import com.example.graduationproject.R;

public class HomeFragment extends Fragment {

    private Button btnStart;
    private Button btnStop;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_home, container, false);

        btnStart = view.findViewById(R.id.btn_start);
        btnStop = view.findViewById(R.id.btn_stop);

        btnStart.setOnClickListener(v -> {
            if (getActivity() instanceof MainActivity) {
                ((MainActivity) getActivity()).startService();
            }
        });

        btnStop.setOnClickListener(v -> {
            if (getActivity() instanceof MainActivity) {
                ((MainActivity) getActivity()).stopService();
            }
        });

        updateStatus();
        return view;
    }

    public void updateStatus() {
        if (getActivity() instanceof MainActivity) {
            MainActivity activity = (MainActivity) getActivity();
            boolean isRunning = activity.isServiceRunning();
            if (isRunning) {
                btnStart.setEnabled(false);
                btnStop.setEnabled(true);
            } else {
                btnStart.setEnabled(true);
                btnStop.setEnabled(false);
            }
        }
    }

    @Override
    public void onResume() {
        super.onResume();
        updateStatus();
    }
}