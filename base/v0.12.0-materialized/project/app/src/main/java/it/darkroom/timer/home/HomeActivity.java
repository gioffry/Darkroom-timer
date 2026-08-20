package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import it.darkroom.timer.MainActivity;
import it.darkroom.timer.assistant.AssistantActivity;

/** Entry point neutro: sceglie tra STAMPA e SVILUPPO & CHIMICA. */
public final class HomeActivity extends Activity {
    private int primary;
    private int muted;
    private int border;
    private int card;
    private int accent;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode = getSharedPreferences("ui", MODE_PRIVATE)
                .getBoolean("darkroomMode", false);
        if (darkroomMode) {
            primary = Color.rgb(255, 42, 42);
            muted = Color.rgb(145, 34, 34);
            border = Color.rgb(112, 20, 20);
            card = Color.rgb(18, 0, 0);
            accent = Color.rgb(255, 42, 42);
        } else {
            primary = Color.rgb(238, 240, 242);
            muted = Color.rgb(145, 151, 158);
            border = Color.rgb(60, 64, 70);
            card = Color.rgb(24, 26, 30);
            accent = Color.rgb(197, 54, 58);
        }
        buildUi();
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(22), dp(24), dp(22), dp(24));
        root.setBackgroundColor(Color.BLACK);

        TextView title = text("DARKROOM", 30, primary, true);
        title.setGravity(Gravity.CENTER);
        root.addView(title, margin(lp(-1, -2), 0, 0, 0, 30));

        Button print = entryButton("STAMPA\nTimer ingranditore");
        print.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        root.addView(print, margin(lp(-1, dp(116)), 0, 0, 0, 16));

        Button assistant = entryButton("SVILUPPO & CHIMICA\nPellicole, chimica e ricette");
        assistant.setOnClickListener(v -> startActivity(new Intent(this, AssistantActivity.class)));
        root.addView(assistant, lp(-1, dp(116)));

        setContentView(root);
    }

    private Button entryButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setAllCaps(false);
        b.setTextSize(19);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(primary);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(14), dp(12), dp(14), dp(12));
        b.setBackground(roundRect(card, 14, 1, border));
        return b;
    }

    private TextView text(String value, float size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private GradientDrawable roundRect(int color, int radius, int stroke, int strokeColor) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        if (stroke > 0) d.setStroke(dp(stroke), strokeColor);
        return d;
    }

    private LinearLayout.LayoutParams lp(int w, int h) {
        return new LinearLayout.LayoutParams(w, h);
    }

    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(dp(l), dp(t), dp(r), dp(b));
        return p;
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }
}
