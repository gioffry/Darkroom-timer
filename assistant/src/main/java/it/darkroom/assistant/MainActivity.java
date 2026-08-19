package it.darkroom.assistant;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Window;

public class MainActivity extends Activity {
    private DarkroomView darkroomView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window window = getWindow();
        window.setStatusBarColor(Color.BLACK);
        window.setNavigationBarColor(Color.BLACK);
        darkroomView = new DarkroomView(this);
        setContentView(darkroomView);
    }

    @Override
    public void onBackPressed() {
        if (darkroomView != null && darkroomView.goHome()) return;
        super.onBackPressed();
    }
}
