#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'
assistant_dir = java / 'assistant'
assistant = assistant_dir / 'AssistantActivity.java'


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def wr(p, s):
    Path(p).write_text(s, encoding='utf-8')


def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.10.6 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.10.6 OK', label, flush=True)


# Versione 0.10.6 / code 51. Nessun cambio di package/applicationId.
rep(build, 'VERSION_NAME = "0.10.5"', 'VERSION_NAME = "0.10.6"', 'version name build')
rep(build, 'VERSION_CODE = "50"', 'VERSION_CODE = "51"', 'version code build')
rep(build, '[Darkroom v0.10.5]', '[Darkroom v0.10.6]', 'build log tag')
rep(build, r'versionCode\s+50\b', r'versionCode\s+51\b', 'preflight code regex')
rep(build, r'0\.10\.5', r'0\.10\.6', 'preflight name regex')
rep(build, 'versionCode 50 / versionName 0.10.5', 'versionCode 51 / versionName 0.10.6', 'preflight message')
rep(build, 'Preflight v0.10.5 OK', 'Preflight v0.10.6 OK', 'preflight log')
rep(gradle, "versionCode 50\n        versionName '0.10.5'", "versionCode 51\n        versionName '0.10.6'", 'gradle version')
rep(manifest, 'android:versionCode="50"\n    android:versionName="0.10.5"', 'android:versionCode="51"\n    android:versionName="0.10.6"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.5";', 'private static final String APP_VERSION = "0.10.6";', 'UI version')

# Registra il nuovo modulo senza toccare MainActivity come entry point dell'app.
ms = rd(manifest)
activity_name = '.assistant.AssistantActivity'
if activity_name not in ms:
    anchor = '''        <service\n            android:name=".SonoffArmService"'''
    if anchor not in ms:
        raise SystemExit('v0.10.6 manifest AssistantActivity: anchor SonoffArmService non trovato')
    block = '''        <activity\n            android:name=".assistant.AssistantActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n'''
    ms = ms.replace(anchor, block + anchor, 1)
    wr(manifest, ms)
print('v0.10.6 OK manifest AssistantActivity', flush=True)

# Navigazione minima dal modulo STAMPA al nuovo modulo.
# Inserimento immediatamente prima del footer: non modifica timer, pannelli o logica SONOFF.
mt = rd(main)
assistant_ref = 'it.darkroom.timer.assistant.AssistantActivity.class'
if assistant_ref not in mt:
    footer = '        TextView footer = text("Darkroom Timer di F.G. - v" + APP_VERSION,'
    if footer not in mt:
        raise SystemExit('v0.10.6 pulsante Assistant: footer anchor non trovato')
    button = '''        Button assistantButton = compactButton("SVILUPPO & CHIMICA  ›");\n        assistantButton.setOnClickListener(v -> startActivity(\n                new Intent(this, it.darkroom.timer.assistant.AssistantActivity.class)));\n        root.addView(assistantButton, margin(lp(-1, dp(52)), 0, 14, 0, 0));\n\n'''
    mt = mt.replace(footer, button + footer, 1)
    wr(main, mt)
print('v0.10.6 OK navigazione Assistant', flush=True)

# Modulo separato: in Release 1 contiene solo shell e segnaposto.
assistant_dir.mkdir(parents=True, exist_ok=True)
assistant_source = r'''package it.darkroom.timer.assistant;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Darkroom Assistant — Release 1/9.
 *
 * Questo package è separato dal modulo STAMPA (it.darkroom.timer).
 * In questa release non contiene logica di sviluppo, chimica, tank,
 * tempi, diluizioni, ricette o database.
 */
public final class AssistantActivity extends Activity {
    private int primary;
    private int muted;
    private int border;
    private int card;
    private int accent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode = getSharedPreferences("ui", MODE_PRIVATE)
                .getBoolean("darkroomMode", false);
        configurePalette(darkroomMode);
        buildUi();
    }

    private void configurePalette(boolean darkroomMode) {
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
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.BLACK);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView eyebrow = text("DARKROOM ASSISTANT", 12, accent, true);
        eyebrow.setGravity(Gravity.CENTER);
        root.addView(eyebrow, lp(-1, -2));

        TextView title = text("SVILUPPO & CHIMICA", 25, primary, true);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(5), 0, 0);
        root.addView(title, lp(-1, -2));

        TextView intro = text(
                "Release 1 di 9 • fondamenta del nuovo modulo. Le funzioni operative arriveranno nelle release successive.",
                13, muted, false);
        intro.setGravity(Gravity.CENTER);
        intro.setPadding(dp(8), dp(8), dp(8), dp(18));
        root.addView(intro, lp(-1, -2));

        addPlaceholder(root, "Nuovo sviluppo");
        addPlaceholder(root, "Prepara chimica");
        addPlaceholder(root, "La mia chimica");
        addPlaceholder(root, "Le mie ricette");
        addPlaceholder(root, "Log sviluppi");
        addPlaceholder(root, "La mia attrezzatura");

        TextView note = text(
                "In questa release le voci sono solo segnaposto e non modificano dati o impostazioni.",
                12, muted, false);
        note.setGravity(Gravity.CENTER);
        note.setPadding(dp(8), dp(14), dp(8), dp(14));
        root.addView(note, lp(-1, -2));

        Button back = new Button(this);
        back.setText("←  TORNA A STAMPA");
        back.setAllCaps(false);
        back.setTextSize(15);
        back.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        back.setTextColor(primary);
        back.setBackground(roundRect(Color.BLACK, 10, 1, accent));
        back.setOnClickListener(v -> finish());
        root.addView(back, margin(lp(-1, dp(54)), 0, 4, 0, 0));

        setContentView(scroll);
    }

    private void addPlaceholder(LinearLayout root, String label) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(13), dp(16), dp(13));
        box.setBackground(roundRect(card, 10, 1, border));

        TextView title = text(label, 16, primary, true);
        box.addView(title, lp(-1, -2));

        TextView status = text("Prossimamente", 12, muted, false);
        status.setPadding(0, dp(3), 0, 0);
        box.addView(status, lp(-1, -2));

        root.addView(box, margin(lp(-1, -2), 0, 0, 0, 8));
    }

    private TextView text(String value, float sizeSp, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sizeSp);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private GradientDrawable roundRect(int color, int radiusDp, int strokeDp, int strokeColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radiusDp));
        if (strokeDp > 0) drawable.setStroke(dp(strokeDp), strokeColor);
        return drawable;
    }

    private LinearLayout.LayoutParams lp(int width, int height) {
        return new LinearLayout.LayoutParams(width, height);
    }

    private LinearLayout.LayoutParams margin(
            LinearLayout.LayoutParams p, int left, int top, int right, int bottom) {
        p.setMargins(dp(left), dp(top), dp(right), dp(bottom));
        return p;
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
'''
wr(assistant, assistant_source)
print('v0.10.6 OK AssistantActivity', flush=True)

# Verifiche statiche della Release 1: il modulo STAMPA resta entry point e il nuovo
# modulo non introduce logiche operative premature.
checks = {
    build: ['VERSION_NAME = "0.10.6"', 'VERSION_CODE = "51"'],
    gradle: ["versionCode 51", "versionName '0.10.6'"],
    manifest: ['android:versionCode="51"', 'android:versionName="0.10.6"', '.MainActivity', '.assistant.AssistantActivity'],
    main: ['private static final String APP_VERSION = "0.10.6"', assistant_ref, 'SVILUPPO & CHIMICA'],
    assistant: ['package it.darkroom.timer.assistant;', 'Nuovo sviluppo', 'Prepara chimica', 'La mia chimica', 'Le mie ricette', 'Log sviluppi', 'La mia attrezzatura', 'TORNA A STAMPA']
}
for p, needles in checks.items():
    t = rd(p)
    for needle in needles:
        if needle not in t:
            raise SystemExit(f'v0.10.6 verifica fallita: {needle} in {p}')

if 'package="it.darkroom.timer"' not in rd(manifest):
    raise SystemExit('v0.10.6 package applicazione alterato')

print('v0.10.6 RELEASE 1 DARKROOM ASSISTANT — VERIFICHE SORGENTE OK', flush=True)
