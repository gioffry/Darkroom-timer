from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "work")
project = root / "project"
main_path = project / "app/src/main/java/it/darkroom/timer/MainActivity.java"
build_path = root / "build_darkroom.py"
gradle_path = project / "app/build.gradle"
manifest_path = project / "app/src/main/AndroidManifest.xml"


def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"v0.7.0: aggancio non trovato: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"v0.7.0: OK {label}")


replace_once(build_path, 'VERSION_NAME = "0.6.4"\nVERSION_CODE = "32"',
             'VERSION_NAME = "0.7.0"\nVERSION_CODE = "33"', 'versione build')
replace_once(build_path, '[Darkroom v0.6.4]', '[Darkroom v0.7.0]', 'tag log build')
replace_once(build_path,
             'if not re.search(r"versionCode\\s+32\\b", g) or not re.search(r"versionName\\s+[\'\\\"]0\\.6\\.4[\'\\\"]", g):\n            fail("app/build.gradle non riporta versionCode 32 / versionName 0.6.4")\n    log("Preflight v0.6.4 OK: manifest/versione/requisiti SONOFF invarianti verificati")',
             'if not re.search(r"versionCode\\s+33\\b", g) or not re.search(r"versionName\\s+[\'\\\"]0\\.7\\.0[\'\\\"]", g):\n            fail("app/build.gradle non riporta versionCode 33 / versionName 0.7.0")\n    log("Preflight v0.7.0 OK: manifest/versione/requisiti SONOFF invarianti verificati")',
             'preflight build')
replace_once(gradle_path, "versionCode 32\n        versionName '0.6.4'",
             "versionCode 33\n        versionName '0.7.0'", 'gradle')
replace_once(manifest_path, 'android:versionCode="32"\n    android:versionName="0.6.4"',
             'android:versionCode="33"\n    android:versionName="0.7.0"', 'manifest')
replace_once(main_path, 'private static final String APP_VERSION = "0.6.4";',
             'private static final String APP_VERSION = "0.7.0";', 'versione UI')

replace_once(main_path,
'''    private Button saveLogButton;
    private Button cancelCycleButton;
    private LinearLayout printPanel;''',
'''    private Button saveLogButton;
    private Button cancelCycleButton;
    private Button printMinusButton;
    private Button printPlusButton;
    private final List<Button> printShortcutButtons = new ArrayList<>();
    private LinearLayout printPanel;''', 'campi STAMPA analogici')

replace_once(main_path,
'''        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);''',
'''        TextView title = text("DARKROOM TIMER", 25, TEXT_PRIMARY, true);
        if (!darkroomMode) title.setLetterSpacing(0.055f);
        title.setGravity(Gravity.CENTER);''', 'titolo strumentale')

replace_once(main_path,
'''        LinearLayout deviceCard = card();
        LinearLayout deviceTop = new LinearLayout(this);''',
'''        LinearLayout deviceCard = card();
        if (!darkroomMode) deviceCard.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.DEVICE));
        LinearLayout deviceTop = new LinearLayout(this);''', 'pannello ingranditore')

replace_once(main_path,
'''    private LinearLayout buildPrintPanel() {
        LinearLayout box = card();
        TextView prompt = text("Tempo di stampa", 16, TEXT_PRIMARY, true);''',
'''    private LinearLayout buildPrintPanel() {
        LinearLayout box = card();
        if (!darkroomMode) {
            box.setPadding(dp(15), dp(15), dp(15), dp(15));
            box.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.PANEL));
        }
        TextView prompt = text("Tempo di stampa", 16, TEXT_PRIMARY, true);
        if (!darkroomMode) prompt.setTextColor(Color.rgb(232, 226, 214));''', 'pannello Tempo di stampa')

replace_once(main_path,
'''        TextView sub = text("Singola esposizione • passo 0,5 s", 12, MUTED, false);
        sub.setGravity(Gravity.CENTER);''',
'''        TextView sub = text("Singola esposizione • passo 0,5 s", 12, MUTED, false);
        if (!darkroomMode) sub.setTextColor(Color.rgb(177, 169, 157));
        sub.setGravity(Gravity.CENTER);''', 'sottotitolo caldo')

replace_once(main_path,
'''        Button minus = smallButton("−");
        Button plus = smallButton("+");
        printTimeText = text(formatTime(printWidthMs), 48, GREEN, true);
        printTimeText.setGravity(Gravity.CENTER);
        selector.addView(minus, lp(dp(62), dp(58)));
        selector.addView(printTimeText, lp(0, dp(68), 1f));
        selector.addView(plus, lp(dp(62), dp(58)));
        minus.setOnClickListener(v -> setPrintTime(printWidthMs - 500));
        plus.setOnClickListener(v -> setPrintTime(printWidthMs + 500));''',
'''        printMinusButton = smallButton("−");
        printPlusButton = smallButton("+");
        printTimeText = text(formatTime(printWidthMs), 48, GREEN, true);
        printTimeText.setGravity(Gravity.CENTER);
        selector.addView(printMinusButton, lp(dp(62), dp(58)));
        selector.addView(printTimeText, lp(0, dp(68), 1f));
        selector.addView(printPlusButton, lp(dp(62), dp(58)));
        printMinusButton.setOnClickListener(v -> setPrintTime(printWidthMs - 500));
        printPlusButton.setOnClickListener(v -> setPrintTime(printWidthMs + 500));''', 'tasti meno più')

replace_once(main_path,
'''            Button b = shortcutButton(s + " s", GREEN);
            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();''',
'''            Button b = shortcutButton(s + " s", GREEN);
            b.setTag(s * 1000);
            printShortcutButtons.add(b);
            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();''', 'preset tempi')

replace_once(main_path,
'''        box.addView(grid, lp(-1, -2));
        return box;
    }

    private LinearLayout buildTestPanel()''',
'''        box.addView(grid, lp(-1, -2));
        if (!darkroomMode) {
            printTimeText.setTextColor(Color.rgb(113, 190, 72));
            printMinusButton.setTextColor(Color.rgb(221, 214, 201));
            printPlusButton.setTextColor(Color.rgb(221, 214, 201));
            printMinusButton.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.BUTTON));
            printPlusButton.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.BUTTON));
            updateProposal2PresetStyles();
        }
        return box;
    }

    private LinearLayout buildTestPanel()''', 'finitura controlli STAMPA')

replace_once(main_path,
'''        if (stateCard != null) stateCard.setBackground(roundRect(CARD, 12, 1, accent));''',
'''        if (stateCard != null) {
            if (!darkroomMode && mode == MODE_PRINT) {
                stateCard.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.STATE, accent));
            } else {
                stateCard.setBackground(roundRect(CARD, 12, 1, accent));
            }
        }''', 'stato analogico')

replace_once(main_path,
'''        if (!log) {
            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));
            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)
                    : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs));
        }
    }

    private void arm()''',
'''        if (!log) {
            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));
            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)
                    : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs));
        }
        if (!darkroomMode && print) {
            actionButton.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.ACTION, GREEN));
            actionButton.setTextColor(Color.rgb(238, 232, 220));
            actionButton.setPadding(dp(30), 0, dp(14), 0);
            saveLogButton.setBackground(new AnalogProposal2Drawable(this, AnalogProposal2Drawable.BUTTON));
            saveLogButton.setTextColor(Color.rgb(232, 226, 214));
            updateProposal2PresetStyles();
        } else if (!darkroomMode) {
            actionButton.setPadding(0, 0, 0, 0);
            saveLogButton.setBackground(roundRect(LOG_ACCENT, 10, 0, 0));
            saveLogButton.setTextColor(Color.WHITE);
        }
    }

    private void updateProposal2PresetStyles() {
        if (darkroomMode) return;
        for (Button b : printShortcutButtons) {
            Object tag = b.getTag();
            boolean selected = tag instanceof Integer && ((Integer) tag) == printWidthMs;
            b.setBackground(new AnalogProposal2Drawable(this,
                    selected ? AnalogProposal2Drawable.PRESET_ACTIVE : AnalogProposal2Drawable.BUTTON));
            b.setTextColor(selected ? Color.rgb(132, 207, 83) : Color.rgb(111, 184, 70));
        }
    }

    private void arm()''', 'azione ARMA e LED')

replace_once(main_path,
'''    private void styleNavButton(Button button, boolean selected, int normalAccent) {
        int foreground;''',
'''    private void styleNavButton(Button button, boolean selected, int normalAccent) {
        if (!darkroomMode && mode == MODE_PRINT) {
            int proposalForeground = selected ? Color.rgb(239, 235, 225) : Color.rgb(187, 180, 168);
            button.setTextColor(proposalForeground);
            button.setBackground(new AnalogProposal2Drawable(this,
                    selected ? AnalogProposal2Drawable.NAV_ACTIVE : AnalogProposal2Drawable.NAV_INACTIVE,
                    selected ? normalAccent : 0));
            if (button instanceof PrimaryNavButton) ((PrimaryNavButton) button).setIconColor(proposalForeground);
            return;
        }
        int foreground;''', 'pulsantiera principale')

java = r'''package it.darkroom.timer;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;

public final class AnalogProposal2Drawable extends Drawable {
    public static final int PANEL = 1;
    public static final int BUTTON = 2;
    public static final int NAV_ACTIVE = 3;
    public static final int NAV_INACTIVE = 4;
    public static final int ACTION = 5;
    public static final int STATE = 6;
    public static final int PRESET_ACTIVE = 7;
    public static final int DEVICE = 8;

    private final float d;
    private final int kind;
    private final int accent;
    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int alpha = 255;
    private boolean pressed;

    public AnalogProposal2Drawable(Context context, int kind) { this(context, kind, 0); }

    public AnalogProposal2Drawable(Context context, int kind, int accent) {
        d = context.getResources().getDisplayMetrics().density;
        this.kind = kind;
        this.accent = accent;
    }

    @Override public void draw(Canvas canvas) {
        RectF r = new RectF(getBounds());
        r.inset(d, d);
        float radius = 10f * d;
        int top, bottom, outer, inner;

        if (kind == NAV_ACTIVE || kind == ACTION) {
            int g = accent != 0 ? accent : Color.rgb(94, 177, 57);
            top = mix(g, Color.WHITE, pressed ? 0.02f : 0.13f);
            bottom = mix(g, Color.BLACK, pressed ? 0.36f : 0.23f);
            outer = mix(g, Color.WHITE, 0.20f);
            inner = mix(g, Color.BLACK, 0.42f);
        } else if (kind == PRESET_ACTIVE) {
            top = Color.rgb(48, 80, 36);
            bottom = Color.rgb(24, 47, 20);
            outer = Color.rgb(93, 142, 65);
            inner = Color.rgb(15, 27, 13);
        } else if (kind == STATE) {
            top = Color.rgb(10, 11, 10);
            bottom = Color.rgb(5, 6, 5);
            outer = accent != 0 ? accent : Color.rgb(91, 169, 57);
            inner = Color.rgb(16, 29, 14);
        } else {
            top = kind == DEVICE ? Color.rgb(31, 29, 26) : Color.rgb(34, 31, 27);
            bottom = Color.rgb(13, 14, 13);
            outer = Color.rgb(78, 72, 64);
            inner = Color.rgb(17, 17, 16);
        }

        p.setStyle(Paint.Style.FILL);
        p.setAlpha(alpha);
        p.setShader(new LinearGradient(0, r.top, 0, r.bottom, top, bottom, Shader.TileMode.CLAMP));
        canvas.drawRoundRect(r, radius, radius, p);
        p.setShader(null);

        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.15f * d);
        p.setColor(outer);
        p.setAlpha(alpha);
        canvas.drawRoundRect(r, radius, radius, p);

        RectF innerRect = new RectF(r);
        innerRect.inset(3.2f * d, 3.2f * d);
        p.setStrokeWidth(0.9f * d);
        p.setColor(inner);
        canvas.drawRoundRect(innerRect, 7.4f * d, 7.4f * d, p);

        RectF bevel = new RectF(innerRect);
        bevel.inset(1.4f * d, 1.4f * d);
        p.setStrokeWidth(0.55f * d);
        p.setColor(kind == NAV_ACTIVE || kind == ACTION
                ? Color.argb(120, 228, 245, 217)
                : Color.argb(80, 183, 172, 153));
        canvas.drawRoundRect(bevel, 6.2f * d, 6.2f * d, p);

        if (kind == PANEL) drawScrews(canvas, r);
        if (kind == ACTION) drawLed(canvas, r);
        if (pressed && kind != STATE) {
            p.setStyle(Paint.Style.FILL);
            p.setShader(null);
            p.setColor(Color.argb(28, 0, 0, 0));
            canvas.drawRoundRect(r, radius, radius, p);
        }
    }

    private void drawScrews(Canvas canvas, RectF r) {
        float o = 11f * d;
        screw(canvas, r.left + o, r.top + o);
        screw(canvas, r.right - o, r.top + o);
        screw(canvas, r.left + o, r.bottom - o);
        screw(canvas, r.right - o, r.bottom - o);
    }

    private void screw(Canvas canvas, float x, float y) {
        p.setShader(null);
        p.setStyle(Paint.Style.FILL);
        p.setColor(Color.rgb(7, 7, 7));
        canvas.drawCircle(x, y, 4.1f * d, p);
        p.setColor(Color.rgb(62, 58, 52));
        canvas.drawCircle(x, y, 3.1f * d, p);
        p.setColor(Color.rgb(104, 97, 86));
        canvas.drawCircle(x - 0.8f * d, y - 0.9f * d, 1.0f * d, p);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(0.8f * d);
        p.setColor(Color.rgb(20, 19, 18));
        canvas.drawLine(x - 1.8f * d, y + 1.8f * d, x + 1.8f * d, y - 1.8f * d, p);
    }

    private void drawLed(Canvas canvas, RectF r) {
        float x = r.left + 22f * d;
        float y = r.centerY();
        float radius = 6f * d;
        p.setStyle(Paint.Style.FILL);
        p.setShader(new RadialGradient(x, y, radius * 2.2f,
                new int[] { Color.argb(170, 255, 70, 48), Color.argb(120, 164, 25, 17), Color.TRANSPARENT },
                new float[] { 0f, 0.42f, 1f }, Shader.TileMode.CLAMP));
        canvas.drawCircle(x, y, radius * 2.2f, p);
        p.setShader(null);
        p.setColor(Color.rgb(78, 9, 7));
        canvas.drawCircle(x, y, 4.8f * d, p);
        p.setColor(Color.rgb(236, 58, 43));
        canvas.drawCircle(x, y, 3.3f * d, p);
        p.setColor(Color.rgb(255, 183, 164));
        canvas.drawCircle(x - 1.0f * d, y - 1.2f * d, 1.0f * d, p);
    }

    private static int mix(int a, int b, float t) {
        t = Math.max(0f, Math.min(1f, t));
        return Color.rgb(
                Math.round(Color.red(a) + (Color.red(b) - Color.red(a)) * t),
                Math.round(Color.green(a) + (Color.green(b) - Color.green(a)) * t),
                Math.round(Color.blue(a) + (Color.blue(b) - Color.blue(a)) * t));
    }

    @Override public boolean isStateful() { return true; }

    @Override protected boolean onStateChange(int[] state) {
        boolean nowPressed = false;
        for (int s : state) if (s == android.R.attr.state_pressed) { nowPressed = true; break; }
        if (nowPressed != pressed) {
            pressed = nowPressed;
            invalidateSelf();
            return true;
        }
        return false;
    }

    @Override public void setAlpha(int alpha) { this.alpha = alpha; invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter colorFilter) { p.setColorFilter(colorFilter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
'''

java_path = project / "app/src/main/java/it/darkroom/timer/AnalogProposal2Drawable.java"
java_path.write_text(java, encoding="utf-8")
print("v0.7.0: OK AnalogProposal2Drawable.java")
