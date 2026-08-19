#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'
assistant_dir = java / 'assistant'
development_dir = assistant_dir / 'development'
home_dir = java / 'home'
assistant = assistant_dir / 'AssistantActivity.java'
home = home_dir / 'HomeActivity.java'
catalog = development_dir / 'DevelopmentCatalog.java'
new_development = development_dir / 'NewDevelopmentActivity.java'
result_activity = development_dir / 'DevelopmentResultActivity.java'


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def wr(p, s):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(s, encoding='utf-8')


def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.10.7 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.10.7 OK', label, flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Safety snapshot: no v0.10.7 change may touch Timer core classes other than MainActivity.
timer_before = {p.name: sha(p) for p in java.glob('*.java') if p.name != 'MainActivity.java'}
main_before = rd(main)

# Versione 0.10.7 / code 52. Application ID/package invariato.
rep(build, 'VERSION_NAME = "0.10.6"', 'VERSION_NAME = "0.10.7"', 'version name build')
rep(build, 'VERSION_CODE = "51"', 'VERSION_CODE = "52"', 'version code build')
rep(build, '[Darkroom v0.10.6]', '[Darkroom v0.10.7]', 'build log tag')
rep(build, r'versionCode\\s+51\\b', r'versionCode\\s+52\\b', 'preflight code regex')
rep(build, r'0\\.10\\.6', r'0\\.10\\.7', 'preflight name regex')
rep(build, 'versionCode 51 / versionName 0.10.6', 'versionCode 52 / versionName 0.10.7', 'preflight message')
rep(build, 'Preflight v0.10.6 OK', 'Preflight v0.10.7 OK', 'preflight log')
rep(gradle, "versionCode 51\n        versionName '0.10.6'", "versionCode 52\n        versionName '0.10.7'", 'gradle version')
rep(manifest, 'android:versionCode="51"\n    android:versionName="0.10.6"', 'android:versionCode="52"\n    android:versionName="0.10.7"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.6";', 'private static final String APP_VERSION = "0.10.7";', 'Timer UI version')

# Correzione Release 1: il vecchio accesso Assistant in fondo al Timer viene rimosso.
old_assistant_button = '''        Button assistantButton = compactButton("SVILUPPO & CHIMICA  ›");\n        assistantButton.setOnClickListener(v -> startActivity(\n                new Intent(this, it.darkroom.timer.assistant.AssistantActivity.class)));\n        root.addView(assistantButton, margin(lp(-1, dp(52)), 0, 14, 0, 0));\n\n'''
rep(main, old_assistant_button, '', 'rimozione pulsante Assistant dal Timer')

# Guardrail forte su MainActivity: sono ammessi SOLO bump versione + rimozione pulsante R1.
expected_main = main_before.replace(
    'private static final String APP_VERSION = "0.10.6";',
    'private static final String APP_VERSION = "0.10.7";', 1
).replace(old_assistant_button, '', 1)
if rd(main) != expected_main:
    raise SystemExit('v0.10.7 GUARDRAIL: MainActivity contiene modifiche non autorizzate')

# Vera HOME: diventa l'unico launcher. MainActivity resta il modulo STAMPA interno.
ms = rd(manifest)
old_main_block = '''        <activity\n            android:name=".MainActivity"\n            android:screenOrientation="portrait"\n            android:exported="true">\n            <intent-filter>\n                <action android:name="android.intent.action.MAIN" />\n                <category android:name="android.intent.category.LAUNCHER" />\n            </intent-filter>\n        </activity>\n'''
new_home_and_main = '''        <activity\n            android:name=".home.HomeActivity"\n            android:screenOrientation="portrait"\n            android:exported="true">\n            <intent-filter>\n                <action android:name="android.intent.action.MAIN" />\n                <category android:name="android.intent.category.LAUNCHER" />\n            </intent-filter>\n        </activity>\n\n        <activity\n            android:name=".MainActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
if old_main_block not in ms:
    raise SystemExit('v0.10.7 manifest HOME: blocco launcher MainActivity non trovato')
ms = ms.replace(old_main_block, new_home_and_main, 1)
assistant_block = '''        <activity\n            android:name=".assistant.AssistantActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
if assistant_block not in ms:
    raise SystemExit('v0.10.7 manifest: AssistantActivity R1 non trovata')
new_dev_activities = '''\n        <activity\n            android:name=".assistant.development.NewDevelopmentActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.development.DevelopmentResultActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
ms = ms.replace(assistant_block, assistant_block + new_dev_activities, 1)
wr(manifest, ms)
print('v0.10.7 OK vera HOME e Activity sviluppo', flush=True)

home_source = r'''package it.darkroom.timer.home;

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
'''
wr(home, home_source)
print('v0.10.7 OK HomeActivity', flush=True)

assistant_source = r'''package it.darkroom.timer.assistant;

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
import android.widget.ScrollView;
import android.widget.TextView;

import it.darkroom.timer.assistant.development.NewDevelopmentActivity;

/** Darkroom Assistant — Release 2/9. */
public final class AssistantActivity extends Activity {
    private int primary;
    private int muted;
    private int border;
    private int card;
    private int accent;

    @Override protected void onCreate(Bundle savedInstanceState) {
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
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView eyebrow = text("DARKROOM ASSISTANT", 12, accent, true);
        eyebrow.setGravity(Gravity.CENTER);
        root.addView(eyebrow, lp(-1, -2));
        TextView title = text("SVILUPPO & CHIMICA", 25, primary, true);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(5), 0, dp(18));
        root.addView(title, lp(-1, -2));

        Button newDevelopment = entry("NUOVO SVILUPPO", "Pellicola, ISO, rivelatore, temperatura e tempo JOBO CPE2", true);
        newDevelopment.setOnClickListener(v -> startActivity(new Intent(this, NewDevelopmentActivity.class)));
        root.addView(newDevelopment, margin(lp(-1, dp(78)), 0, 0, 0, 9));

        addPlaceholder(root, "PREPARA CHIMICA");
        addPlaceholder(root, "LA MIA CHIMICA");
        addPlaceholder(root, "LE MIE RICETTE");
        addPlaceholder(root, "LOG SVILUPPI");
        addPlaceholder(root, "LA MIA ATTREZZATURA");

        Button back = entry("←  TORNA ALLA HOME", "", false);
        back.setOnClickListener(v -> finish());
        root.addView(back, margin(lp(-1, dp(58)), 0, 14, 0, 0));
        setContentView(scroll);
    }

    private void addPlaceholder(LinearLayout root, String label) {
        Button b = entry(label, "Prossimamente", false);
        b.setEnabled(false);
        b.setAlpha(0.58f);
        root.addView(b, margin(lp(-1, dp(68)), 0, 0, 0, 8));
    }

    private Button entry(String title, String subtitle, boolean emphasized) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(subtitle.isEmpty() ? title : title + "\n" + subtitle);
        b.setTextSize(emphasized ? 16 : 15);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(primary);
        b.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        b.setPadding(dp(16), dp(8), dp(14), dp(8));
        b.setBackground(roundRect(card, 11, 1, emphasized ? accent : border));
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

    private LinearLayout.LayoutParams lp(int w, int h) { return new LinearLayout.LayoutParams(w, h); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(dp(l), dp(t), dp(r), dp(b)); return p;
    }
    private int dp(int v) { return (int) (v * getResources().getDisplayMetrics().density + 0.5f); }
}
'''
wr(assistant, assistant_source)
print('v0.10.7 OK AssistantActivity R2', flush=True)

catalog_source = r'''package it.darkroom.timer.assistant.development;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Catalogo iniziale source-backed per Darkroom Assistant R2.
 * Nessun tempo viene stimato quando manca un dato sorgente compatibile.
 */
public final class DevelopmentCatalog {
    public static final String PROCESSOR = "JOBO CPE2";
    public static final String PROCESS_METHOD = "rotazione continua";

    private static final String MANUAL = "manuale/intermittente";
    private static final String ROTARY = "rotary/continua";
    private static final String SRC_FOMA = "FOMA — B&W Photo Materials and Developing Information / FOMA 04/23";
    private static final String SRC_ILFORD_HP5 = "ILFORD — HP5 PLUS Technical Information, Nov 2018";
    private static final String SRC_KODAK_TRIX = "KODAK — TRI-X 320/400 Technical Data F-4017, Oct 2021";
    private static final String TEMP_METHOD = "FOMA — tabella ufficiale di correzione temperatura 16–26 °C";
    private static final String ROTARY_METHOD = "ILFORD — guida rotary processor: fino a −15% senza pre-rinse";

    public static final class Film {
        public final String name;
        public final int nominalIso;
        public final boolean format35;
        public final boolean format120;
        Film(String name, int nominalIso, boolean format35, boolean format120) {
            this.name = name; this.nominalIso = nominalIso;
            this.format35 = format35; this.format120 = format120;
        }
    }

    private static final class Recipe {
        final String film;
        final int ei;
        final String developer;
        final String dilution;
        final double tempC;
        final int minSeconds;
        final int maxSeconds;
        final String method;
        final String source;
        final String sourceNote;

        Recipe(String film, int ei, String developer, String dilution, double tempC,
               int minSeconds, int maxSeconds, String method, String source, String sourceNote) {
            this.film = film; this.ei = ei; this.developer = developer; this.dilution = dilution;
            this.tempC = tempC; this.minSeconds = minSeconds; this.maxSeconds = maxSeconds;
            this.method = method; this.source = source; this.sourceNote = sourceNote;
        }
        boolean range() { return minSeconds != maxSeconds; }
        int midpoint() { return (int) Math.round((minSeconds + maxSeconds) / 2.0); }
    }

    public static final class Result {
        public final boolean ok;
        public final String error;
        public final String film;
        public final String format;
        public final int nominalIso;
        public final int exposedIso;
        public final String developer;
        public final String dilution;
        public final double temperature;
        public final int finalSeconds;
        public final String source;
        public final String dataType;
        public final String sourceData;
        public final String calculation;
        public final String alternatives;

        private Result(boolean ok, String error, String film, String format, int nominalIso, int exposedIso,
                       String developer, String dilution, double temperature, int finalSeconds,
                       String source, String dataType, String sourceData, String calculation, String alternatives) {
            this.ok = ok; this.error = error; this.film = film; this.format = format;
            this.nominalIso = nominalIso; this.exposedIso = exposedIso; this.developer = developer;
            this.dilution = dilution; this.temperature = temperature; this.finalSeconds = finalSeconds;
            this.source = source; this.dataType = dataType; this.sourceData = sourceData;
            this.calculation = calculation; this.alternatives = alternatives;
        }

        static Result error(String message) {
            return new Result(false, message, "", "", 0, 0, "", "", 0, 0, "", "", "", "", "");
        }
    }

    private static final class Candidate {
        int seconds;
        int score;
        boolean adapted;
        String source;
        String sourceData;
        String calculation;
    }

    private static final List<Film> FILMS = new ArrayList<>();
    private static final List<Recipe> RECIPES = new ArrayList<>();

    static {
        FILMS.add(new Film("Fomapan 100 Classic", 100, true, true));
        FILMS.add(new Film("Fomapan 200 Creative", 200, true, true));
        FILMS.add(new Film("Fomapan 400 Action", 400, true, true));
        FILMS.add(new Film("ILFORD HP5 PLUS", 400, true, true));
        FILMS.add(new Film("KODAK TRI-X 400", 400, true, true));

        // FOMA official 20 °C manual/intermittent data. Ranges are preserved;
        // when one final timer value is required, the app transparently uses the midpoint.
        addManual("Fomapan 100 Classic",100,"FOMA Universal","1+3",300,SRC_FOMA,"5 min @20 °C");
        addManual("Fomapan 100 Classic",100,"FOMADON R09","1+25",240,SRC_FOMA,"4 min @20 °C");
        addManual("Fomapan 100 Classic",100,"FOMADON R09","1+50",540,SRC_FOMA,"9 min @20 °C");
        addRange("Fomapan 100 Classic",100,"KODAK D-76","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","1+1",480,600,SRC_FOMA,"8–10 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","1+3",900,960,SRC_FOMA,"15–16 min @20 °C");
        addRange("Fomapan 100 Classic",100,"KODAK XTOL","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","stock",300,420,SRC_FOMA,"5–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","1+1",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","1+3",780,840,SRC_FOMA,"13–14 min @20 °C");

        addManual("Fomapan 200 Creative",200,"FOMA Universal","1+3",210,SRC_FOMA,"3 min 30 s @20 °C");
        addManual("Fomapan 200 Creative",200,"FOMADON R09","1+25",300,SRC_FOMA,"5 min @20 °C");
        addManual("Fomapan 200 Creative",200,"FOMADON R09","1+50",600,SRC_FOMA,"10 min @20 °C");
        addRange("Fomapan 200 Creative",200,"KODAK D-76","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","1+1",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","1+3",720,780,SRC_FOMA,"12–13 min @20 °C");
        addRange("Fomapan 200 Creative",200,"KODAK XTOL","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD MICROPHEN","stock",300,360,SRC_FOMA,"5–6 min @20 °C");

        addManual("Fomapan 400 Action",400,"FOMA Universal","1+3",450,SRC_FOMA,"7 min 30 s @20 °C");
        addManual("Fomapan 400 Action",400,"FOMADON R09","1+25",360,SRC_FOMA,"6 min @20 °C");
        addManual("Fomapan 400 Action",400,"FOMADON R09","1+50",720,SRC_FOMA,"12 min @20 °C");
        addRange("Fomapan 400 Action",400,"KODAK D-76","stock",420,480,SRC_FOMA,"7–8 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","stock",420,480,SRC_FOMA,"7–8 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","1+1",720,780,SRC_FOMA,"12–13 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","1+3",1320,1380,SRC_FOMA,"22–23 min @20 °C");
        addManual("Fomapan 400 Action",400,"KODAK XTOL","stock",420,SRC_FOMA,"7 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD MICROPHEN","stock",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD MICROPHEN","1+1",720,780,SRC_FOMA,"12–13 min @20 °C");

        // ILFORD HP5 PLUS official 20 °C spiral-tank data, including non-ILFORD developers.
        hp5(400,"ILFORD ILFOTEC DD-X","1+4",540); hp5(800,"ILFORD ILFOTEC DD-X","1+4",600);
        hp5(1600,"ILFORD ILFOTEC DD-X","1+4",780); hp5(3200,"ILFORD ILFOTEC DD-X","1+4",1200);
        hp5(400,"ILFORD ID-11","stock",450); hp5(800,"ILFORD ID-11","stock",630); hp5(1600,"ILFORD ID-11","stock",840);
        hp5(400,"ILFORD ID-11","1+1",780); hp5(800,"ILFORD ID-11","1+1",990);
        hp5(400,"ILFORD ID-11","1+3",1200);
        hp5(400,"ILFORD MICROPHEN","stock",390); hp5(800,"ILFORD MICROPHEN","stock",480);
        hp5(1600,"ILFORD MICROPHEN","stock",660); hp5(3200,"ILFORD MICROPHEN","stock",960);
        hp5(400,"KODAK D-76","stock",450); hp5(800,"KODAK D-76","stock",570); hp5(1600,"KODAK D-76","stock",750);
        hp5(400,"KODAK D-76","1+1",660); hp5(800,"KODAK D-76","1+1",780);
        hp5(400,"KODAK D-76","1+3",1320);
        hp5(400,"AGFA RODINAL","1+25",360); hp5(800,"AGFA RODINAL","1+25",480);
        hp5(400,"AGFA RODINAL","1+50",660);
        hp5(400,"KODAK XTOL","stock",480); hp5(800,"KODAK XTOL","stock",660);
        hp5(1600,"KODAK XTOL","stock",840); hp5(3200,"KODAK XTOL","stock",1140);

        // KODAK TRI-X 400 official Rotary-Tube / continuous agitation tables.
        addTrixRotarySet(400,"KODAK T-MAX","stock", new int[]{405,360,345,330,285});
        addTrixRotarySet(400,"KODAK T-MAX RS","stock", new int[]{285,270,255,240,210});
        addTrixRotarySet(400,"KODAK HC-110","B", new int[]{270,225,210,180,150});
        addTrixRotarySet(400,"KODAK D-76","stock", new int[]{480,405,375,330,285});
        addTrixRotarySet(400,"KODAK D-76","1+1", new int[]{645,585,540,510,465});
        addTrixRotarySet(400,"KODAK XTOL","stock", new int[]{480,420,375,345,285});
        addTrixRotarySet(400,"KODAK XTOL","1+1", new int[]{600,540,510,480,435});

        addTrixRotarySet(1600,"KODAK T-MAX","stock", new int[]{570,525,495,465,420});
        addTrixRotarySet(1600,"KODAK T-MAX RS","stock", new int[]{510,465,435,405,360});
        addTrixRotarySet(1600,"KODAK HC-110","B", new int[]{420,360,330,300,255});
        addTrixRotarySet(1600,"KODAK D-76","stock", new int[]{675,570,525,465,390});
        addTrixRotarySet(1600,"KODAK D-76","1+1", new int[]{885,795,750,705,645});
        addTrixRotarySet(1600,"KODAK XTOL","stock", new int[]{675,585,525,480,405});
        addTrixRotarySet(1600,"KODAK XTOL","1+1", new int[]{870,795,735,690,630});

        addTrixRotarySetPartial(3200,"KODAK T-MAX RS","stock", new double[]{20,21,22,24}, new int[]{570,540,495,450});
        addTrixRotarySet(3200,"KODAK D-76","stock", new int[]{765,660,585,540,450});
        addTrixRotarySet(3200,"KODAK D-76","1+1", new int[]{1050,960,900,855,765});
        addTrixRotarySetPartial(3200,"KODAK XTOL","stock", new double[]{20,21,22,24}, new int[]{690,630,570,480});
        addTrixRotarySetPartial(3200,"KODAK XTOL","1+1", new double[]{20,21,22,24}, new int[]{930,870,825,735});
    }

    private DevelopmentCatalog() {}

    private static void addManual(String film, int ei, String dev, String dilution, int seconds, String source, String note) {
        RECIPES.add(new Recipe(film,ei,dev,dilution,20.0,seconds,seconds,MANUAL,source,note));
    }
    private static void addRange(String film, int ei, String dev, String dilution, int min, int max, String source, String note) {
        RECIPES.add(new Recipe(film,ei,dev,dilution,20.0,min,max,MANUAL,source,note));
    }
    private static void hp5(int ei, String dev, String dilution, int seconds) {
        addManual("ILFORD HP5 PLUS",ei,dev,dilution,seconds,SRC_ILFORD_HP5,formatTime(seconds)+" @20 °C — spiral tank");
    }
    private static void addTrixRotarySet(int ei, String dev, String dilution, int[] seconds) {
        double[] temps = {18,20,21,22,24};
        addTrixRotarySetPartial(ei,dev,dilution,temps,seconds);
    }
    private static void addTrixRotarySetPartial(int ei, String dev, String dilution, double[] temps, int[] seconds) {
        for (int i=0;i<temps.length;i++) {
            RECIPES.add(new Recipe("KODAK TRI-X 400",ei,dev,dilution,temps[i],seconds[i],seconds[i],ROTARY,
                    SRC_KODAK_TRIX,formatTime(seconds[i])+" @"+trimTemp(temps[i])+" °C — Rotary Tube / continuous agitation"));
        }
    }

    public static String[] filmNames() {
        String[] out = new String[FILMS.size()];
        for (int i=0;i<FILMS.size();i++) out[i] = FILMS.get(i).name;
        return out;
    }

    public static Film findFilm(String name) {
        if (name == null) return null;
        for (Film f : FILMS) if (f.name.equalsIgnoreCase(name.trim())) return f;
        return null;
    }

    public static String[] developerNames() {
        Set<String> names = new LinkedHashSet<>();
        for (Recipe r : RECIPES) names.add(r.developer);
        ArrayList<String> out = new ArrayList<>(names);
        Collections.sort(out);
        return out.toArray(new String[0]);
    }

    public static String[] availableDilutions(String film, int ei, String developer) {
        LinkedHashSet<String> exact = new LinkedHashSet<>();
        LinkedHashSet<String> fallback = new LinkedHashSet<>();
        for (Recipe r : RECIPES) {
            if (!same(r.film,film) || !same(r.developer,developer)) continue;
            fallback.add(r.dilution);
            if (r.ei == ei) exact.add(r.dilution);
        }
        Set<String> selected = exact.isEmpty() ? fallback : exact;
        return selected.toArray(new String[0]);
    }

    public static Result calculate(String filmName, String format, int exposedIso, String developer, String dilution, double temperature) {
        Film film = findFilm(filmName);
        if (film == null) return Result.error("Seleziona una pellicola presente nel catalogo.");
        if (!("35 mm".equals(format) || "120".equals(format))) return Result.error("Formato non valido.");
        if ("35 mm".equals(format) && !film.format35) return Result.error("Questa pellicola non è disponibile in 35 mm nel profilo dati.");
        if ("120".equals(format) && !film.format120) return Result.error("Questa pellicola non è disponibile in 120 nel profilo dati.");
        if (exposedIso <= 0) return Result.error("ISO esposto non valido.");
        if (temperature < 16.0 || temperature > 26.0)
            return Result.error("Per la Release 2 l’adattamento affidabile è limitato a 16–26 °C.");

        ArrayList<Recipe> matches = new ArrayList<>();
        for (Recipe r : RECIPES) {
            if (same(r.film, film.name) && r.ei == exposedIso && same(r.developer,developer) && same(r.dilution,dilution))
                matches.add(r);
        }
        if (matches.isEmpty()) {
            return Result.error("Nessun tempo sorgente verificato per questa combinazione a ISO " + exposedIso
                    + ". Darkroom Assistant non inventa un tempo: prova un’altra diluizione/rivelatore oppure un EI documentato.");
        }

        Map<String,List<Recipe>> groups = new LinkedHashMap<>();
        for (Recipe r : matches) {
            String key = r.source + "|" + r.method;
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(r);
        }
        ArrayList<Candidate> candidates = new ArrayList<>();
        for (List<Recipe> group : groups.values()) {
            Candidate c = computeCandidate(group, temperature);
            if (c != null) candidates.add(c);
        }
        if (candidates.isEmpty()) return Result.error("Esistono dati sorgente, ma non un adattamento affidabile alla temperatura indicata.");
        candidates.sort((a,b) -> Integer.compare(b.score,a.score));
        Candidate best = candidates.get(0);

        StringBuilder alternatives = new StringBuilder();
        for (int i=1;i<candidates.size();i++) {
            Candidate c = candidates.get(i);
            if (alternatives.length() > 0) alternatives.append("\n\n");
            alternatives.append("• ").append(c.source).append(" — ").append(formatTime(c.seconds))
                    .append(c.adapted ? " (adattato)" : " (diretto)");
        }

        return new Result(true,"",film.name,format,film.nominalIso,exposedIso,developer,dilution,temperature,
                best.seconds,best.source,best.adapted ? "DATO ADATTATO / CALCOLATO" : "DATO DIRETTO",
                best.sourceData,best.calculation,alternatives.toString());
    }

    private static Candidate computeCandidate(List<Recipe> group, double temp) {
        if (group.isEmpty()) return null;
        Recipe first = group.get(0);
        if (ROTARY.equals(first.method)) return rotaryCandidate(group,temp);
        return manualCandidate(first,temp);
    }

    private static Candidate rotaryCandidate(List<Recipe> group, double temp) {
        group.sort(Comparator.comparingDouble(r -> r.tempC));
        for (Recipe r : group) {
            if (Math.abs(r.tempC-temp) < 0.051) {
                Candidate c = new Candidate();
                c.seconds = r.midpoint(); c.score = 1000; c.adapted = false; c.source = r.source;
                c.sourceData = r.sourceNote;
                c.calculation = "Dato già pubblicato per Rotary Tube / agitazione continua; usato direttamente nel profilo "
                        + PROCESSOR + " — " + PROCESS_METHOD + ".";
                return c;
            }
        }
        Recipe lo = null, hi = null;
        for (Recipe r : group) {
            if (r.tempC < temp) lo = r;
            if (r.tempC > temp) { hi = r; break; }
        }
        if (lo != null && hi != null) {
            double ratio = (temp-lo.tempC)/(hi.tempC-lo.tempC);
            int seconds = (int)Math.round(lo.midpoint() + ratio*(hi.midpoint()-lo.midpoint()));
            Candidate c = new Candidate();
            c.seconds = seconds; c.score = 950; c.adapted = true; c.source = first.source;
            c.sourceData = "Tabella rotary: " + trimTemp(lo.tempC) + " °C → " + formatTime(lo.midpoint())
                    + "; " + trimTemp(hi.tempC) + " °C → " + formatTime(hi.midpoint());
            c.calculation = "Interpolazione lineare fra due temperature pubblicate dalla stessa fonte; nessuna correzione di agitazione aggiuntiva.";
            return c;
        }
        Recipe at20 = null;
        for (Recipe r : group) if (Math.abs(r.tempC-20.0)<0.01) at20=r;
        if (at20 == null) return null;
        double factor = tempFactor(temp);
        if (Double.isNaN(factor)) return null;
        Candidate c = new Candidate();
        c.seconds = (int)Math.round(at20.midpoint()*factor); c.score = 900; c.adapted = true; c.source = first.source;
        c.sourceData = at20.sourceNote;
        c.calculation = "Temperatura fuori dai punti tabellati della fonte rotary: applicato fattore "
                + String.format(Locale.ITALY,"%.3f",factor) + " da " + TEMP_METHOD + ".";
        return c;
    }

    private static Candidate manualCandidate(Recipe r, double temp) {
        double factor = tempFactor(temp);
        if (Double.isNaN(factor)) return null;
        int base = r.midpoint();
        double tempAdjusted = base * factor;
        int finalSeconds = (int)Math.round(tempAdjusted * 0.85);
        Candidate c = new Candidate();
        c.seconds = finalSeconds;
        c.score = r.range() ? 710 : 760;
        c.adapted = true;
        c.source = r.source;
        c.sourceData = r.sourceNote + (r.range() ? " (punto medio usato: " + formatTime(base) + ")" : "");
        c.calculation = (r.range() ? "Intervallo fonte → punto medio; " : "")
                + "temperatura: fattore " + String.format(Locale.ITALY,"%.3f",factor) + " secondo " + TEMP_METHOD
                + "; rotazione continua: −15% come valore iniziale secondo " + ROTARY_METHOD
                + ". Risultato esplicitamente adattato, non pubblicato come tempo CPE2 dalla fonte.";
        return c;
    }

    private static double tempFactor(double t) {
        double[] temp = {16,18,20,22,24,26};
        double[] factor = {1.45,1.20,1.00,0.85,0.75,0.60};
        if (t < 16 || t > 26) return Double.NaN;
        for (int i=0;i<temp.length;i++) if (Math.abs(t-temp[i])<0.0001) return factor[i];
        for (int i=0;i<temp.length-1;i++) {
            if (t>temp[i] && t<temp[i+1]) {
                double x=(t-temp[i])/(temp[i+1]-temp[i]);
                return factor[i]+x*(factor[i+1]-factor[i]);
            }
        }
        return Double.NaN;
    }

    public static String formatTime(int seconds) {
        int m = seconds/60, s = seconds%60;
        if (m == 0) return s + " s";
        if (s == 0) return m + " min";
        return m + " min " + s + " s";
    }

    private static String trimTemp(double t) {
        if (Math.abs(t-Math.rint(t)) < 0.001) return Integer.toString((int)Math.rint(t));
        return String.format(Locale.ITALY,"%.1f",t);
    }
    private static boolean same(String a, String b) {
        return a != null && b != null && a.trim().equalsIgnoreCase(b.trim());
    }
}
'''
wr(catalog, catalog_source)
print('v0.10.7 OK DevelopmentCatalog source-backed', flush=True)

new_development_source = r'''package it.darkroom.timer.assistant.development;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/** Input del primo flusso operativo del Darkroom Assistant. */
public final class NewDevelopmentActivity extends Activity {
    private int primary, muted, border, card, accent;
    private AutoCompleteTextView filmField, developerField, dilutionField;
    private TextView nominalIsoText;
    private EditText exposedIsoField, temperatureField;
    private Button format35, format120;
    private String selectedFormat = "120";

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode = getSharedPreferences("ui", MODE_PRIVATE).getBoolean("darkroomMode", false);
        configurePalette(darkroomMode);
        buildUi();
    }

    private void configurePalette(boolean darkroomMode) {
        if (darkroomMode) {
            primary=Color.rgb(255,42,42); muted=Color.rgb(145,34,34); border=Color.rgb(112,20,20);
            card=Color.rgb(18,0,0); accent=Color.rgb(255,42,42);
        } else {
            primary=Color.rgb(238,240,242); muted=Color.rgb(145,151,158); border=Color.rgb(60,64,70);
            card=Color.rgb(24,26,30); accent=Color.rgb(197,54,58);
        }
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true); scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(16),dp(18),dp(28));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));

        TextView eyebrow=text("DARKROOM ASSISTANT · 2/9",12,accent,true); eyebrow.setGravity(Gravity.CENTER); root.addView(eyebrow);
        TextView title=text("NUOVO SVILUPPO",24,primary,true); title.setGravity(Gravity.CENTER); root.addView(title);
        TextView processor=text("JOBO CPE2  ·  ROTAZIONE CONTINUA",13,accent,true); processor.setGravity(Gravity.CENTER);
        processor.setPadding(0,dp(5),0,dp(18)); root.addView(processor);

        label(root,"PELLICOLA");
        filmField=autoField("Cerca o seleziona pellicola");
        filmField.setAdapter(adapter(DevelopmentCatalog.filmNames()));
        root.addView(filmField, lp(-1,dp(52)));
        filmField.setOnClickListener(v -> filmField.showDropDown());
        filmField.setOnFocusChangeListener((v,has) -> { if(has) filmField.showDropDown(); });
        filmField.setOnItemClickListener((p,v,pos,id) -> onFilmChanged());

        label(root,"FORMATO");
        LinearLayout formats=new LinearLayout(this); formats.setOrientation(LinearLayout.HORIZONTAL);
        format35=smallChoice("35 mm"); format120=smallChoice("120");
        format35.setOnClickListener(v -> selectFormat("35 mm")); format120.setOnClickListener(v -> selectFormat("120"));
        formats.addView(format35,margin(lp(0,dp(48),1f),0,0,5,0));
        formats.addView(format120,margin(lp(0,dp(48),1f),5,0,0,0)); root.addView(formats);
        selectFormat("120");

        label(root,"ISO NOMINALE");
        nominalIsoText=text("—",19,primary,true); nominalIsoText.setPadding(dp(14),dp(12),dp(14),dp(12));
        nominalIsoText.setBackground(roundRect(card,9,1,border)); root.addView(nominalIsoText,lp(-1,dp(50)));

        label(root,"ISO ESPOSTO");
        exposedIsoField=editField("es. 1600",InputType.TYPE_CLASS_NUMBER); root.addView(exposedIsoField,lp(-1,dp(52)));
        exposedIsoField.addTextChangedListener(new TextWatcher(){ public void beforeTextChanged(CharSequence s,int st,int c,int a){} public void onTextChanged(CharSequence s,int st,int b,int c){ refreshDilutions(); } public void afterTextChanged(Editable e){} });

        label(root,"RIVELATORE");
        developerField=autoField("Scelta indipendente dalla marca");
        developerField.setAdapter(adapter(DevelopmentCatalog.developerNames())); root.addView(developerField,lp(-1,dp(52)));
        developerField.setOnClickListener(v -> developerField.showDropDown());
        developerField.setOnFocusChangeListener((v,has) -> { if(has) developerField.showDropDown(); });
        developerField.setOnItemClickListener((p,v,pos,id) -> refreshDilutions());

        label(root,"DILUIZIONE");
        dilutionField=autoField("Seleziona dopo pellicola e rivelatore"); root.addView(dilutionField,lp(-1,dp(52)));
        dilutionField.setOnClickListener(v -> dilutionField.showDropDown());
        dilutionField.setOnFocusChangeListener((v,has) -> { if(has) dilutionField.showDropDown(); });

        label(root,"TEMPERATURA REALE");
        temperatureField=editField("es. 21,7 °C",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        temperatureField.setText("20,0"); root.addView(temperatureField,lp(-1,dp(52)));
        TextView tempNote=text("Inserimento manuale dal tuo sondino · intervallo supportato R2: 16–26 °C",11,muted,false);
        tempNote.setPadding(dp(4),dp(5),dp(4),dp(12)); root.addView(tempNote);

        Button calculate=bigButton("CALCOLA TEMPO"); calculate.setOnClickListener(v -> calculate());
        root.addView(calculate,margin(lp(-1,dp(60)),0,12,0,0));
        TextView sourceNote=text("Il risultato usa solo dati documentati FOMA / ILFORD / KODAK. Se una combinazione non è documentata, l’app non inventa un tempo.",11,muted,false);
        sourceNote.setGravity(Gravity.CENTER); sourceNote.setPadding(dp(6),dp(10),dp(6),dp(14)); root.addView(sourceNote);

        Button back=bigButton("←  ASSISTANT"); back.setOnClickListener(v -> finish()); root.addView(back,lp(-1,dp(52)));
        setContentView(scroll);
    }

    private void onFilmChanged() {
        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());
        if(film==null){ nominalIsoText.setText("—"); return; }
        nominalIsoText.setText(Integer.toString(film.nominalIso));
        exposedIsoField.setText(Integer.toString(film.nominalIso));
        if(!film.format120 && "120".equals(selectedFormat)) selectFormat("35 mm");
        refreshDilutions();
    }

    private void refreshDilutions() {
        if(dilutionField==null || filmField==null || developerField==null || exposedIsoField==null) return;
        int ei=parseInt(exposedIsoField.getText().toString(),-1);
        String[] values=DevelopmentCatalog.availableDilutions(filmField.getText().toString(),ei,developerField.getText().toString());
        dilutionField.setAdapter(adapter(values));
        if(values.length>0 && !containsIgnoreCase(values,dilutionField.getText().toString())) dilutionField.setText(values[0],false);
        if(values.length==0) dilutionField.setText("");
    }

    private void selectFormat(String format) {
        selectedFormat=format;
        if(format35==null || format120==null) return;
        format35.setBackground(roundRect(card,9,1,"35 mm".equals(format)?accent:border));
        format120.setBackground(roundRect(card,9,1,"120".equals(format)?accent:border));
        format35.setTextColor("35 mm".equals(format)?accent:primary);
        format120.setTextColor("120".equals(format)?accent:primary);
    }

    private void calculate() {
        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());
        if(film==null){ toast("Seleziona una pellicola dal catalogo."); return; }
        int exposed=parseInt(exposedIsoField.getText().toString(),-1);
        if(exposed<=0){ toast("Inserisci un ISO esposto valido."); return; }
        double temp=parseDouble(temperatureField.getText().toString());
        if(Double.isNaN(temp)){ toast("Inserisci la temperatura, per esempio 21,7."); return; }
        DevelopmentCatalog.Result r=DevelopmentCatalog.calculate(film.name,selectedFormat,exposed,
                developerField.getText().toString(),dilutionField.getText().toString(),temp);
        if(!r.ok){ toast(r.error); return; }
        Intent i=new Intent(this,DevelopmentResultActivity.class);
        i.putExtra("film",r.film); i.putExtra("format",r.format); i.putExtra("nominalIso",r.nominalIso);
        i.putExtra("exposedIso",r.exposedIso); i.putExtra("developer",r.developer); i.putExtra("dilution",r.dilution);
        i.putExtra("temperature",r.temperature); i.putExtra("seconds",r.finalSeconds); i.putExtra("source",r.source);
        i.putExtra("dataType",r.dataType); i.putExtra("sourceData",r.sourceData); i.putExtra("calculation",r.calculation);
        i.putExtra("alternatives",r.alternatives); startActivity(i);
    }

    private AutoCompleteTextView autoField(String hint) {
        AutoCompleteTextView v=new AutoCompleteTextView(this); v.setHint(hint); v.setThreshold(0); v.setSingleLine(true);
        v.setTextSize(16); v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0);
        v.setBackground(roundRect(card,9,1,border)); return v;
    }
    private EditText editField(String hint,int type) {
        EditText v=new EditText(this); v.setHint(hint); v.setSingleLine(true); v.setInputType(type); v.setTextSize(16);
        v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0); v.setBackground(roundRect(card,9,1,border)); return v;
    }
    private ArrayAdapter<String> adapter(String[] values) {
        ArrayAdapter<String> a=new ArrayAdapter<String>(this,android.R.layout.simple_dropdown_item_1line,values);
        return a;
    }
    private Button smallChoice(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return b; }
    private Button bigButton(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(16); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); b.setTextColor(primary); b.setBackground(roundRect(card,10,1,accent)); return b; }
    private void label(LinearLayout root,String s){ TextView l=text(s,11,muted,true); l.setPadding(dp(3),dp(13),0,dp(5)); root.addView(l); }
    private TextView text(String v,float s,int c,boolean bold){ TextView t=new TextView(this); t.setText(v); t.setTextSize(s); t.setTextColor(c); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return t; }
    private GradientDrawable roundRect(int c,int r,int sw,int sc){ GradientDrawable d=new GradientDrawable(); d.setColor(c); d.setCornerRadius(dp(r)); if(sw>0)d.setStroke(dp(sw),sc); return d; }
    private LinearLayout.LayoutParams lp(int w,int h){ return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams lp(int w,int h,float weight){ return new LinearLayout.LayoutParams(w,h,weight); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){ p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
    private int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
    private int parseInt(String s,int fallback){ try{return Integer.parseInt(s.trim());}catch(Exception e){return fallback;} }
    private double parseDouble(String s){ try{return Double.parseDouble(s.trim().replace(',','.').replace("°C","").trim());}catch(Exception e){return Double.NaN;} }
    private boolean containsIgnoreCase(String[] values,String q){ if(q==null)return false; for(String v:values)if(v.equalsIgnoreCase(q.trim()))return true; return false; }
    private void toast(String s){ Toast.makeText(this,s,Toast.LENGTH_LONG).show(); }
}
'''
wr(new_development, new_development_source)
print('v0.10.7 OK NewDevelopmentActivity', flush=True)

result_source = r'''package it.darkroom.timer.assistant.development;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.Locale;

/** Risultato essenziale: nessun countdown, solo il tempo da riportare sul timer fisico. */
public final class DevelopmentResultActivity extends Activity {
    private int primary, muted, border, card, accent;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);
        if(darkroomMode){ primary=Color.rgb(255,42,42); muted=Color.rgb(145,34,34); border=Color.rgb(112,20,20); card=Color.rgb(18,0,0); accent=Color.rgb(255,42,42); }
        else { primary=Color.rgb(238,240,242); muted=Color.rgb(145,151,158); border=Color.rgb(60,64,70); card=Color.rgb(24,26,30); accent=Color.rgb(197,54,58); }
        buildUi();
    }

    private void buildUi() {
        Bundle e=getIntent().getExtras(); if(e==null){ finish(); return; }
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(18),dp(18),dp(28));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));

        TextView film=text(e.getString("film",""),25,primary,true); film.setGravity(Gravity.CENTER); root.addView(film);
        TextView line1=text(e.getString("format","")+"  ·  ISO "+e.getInt("exposedIso"),15,muted,true); line1.setGravity(Gravity.CENTER); root.addView(line1);
        TextView chemistry=text(e.getString("developer","")+"  ·  "+e.getString("dilution",""),17,primary,true); chemistry.setGravity(Gravity.CENTER); chemistry.setPadding(0,dp(16),0,dp(4)); root.addView(chemistry);
        TextView temp=text(String.format(Locale.ITALY,"%.1f °C",e.getDouble("temperature")),16,primary,false); temp.setGravity(Gravity.CENTER); root.addView(temp);
        TextView processor=text("JOBO CPE2  ·  rotazione continua",15,accent,true); processor.setGravity(Gravity.CENTER); processor.setPadding(0,dp(6),0,dp(20)); root.addView(processor);

        TextView label=text("TEMPO DA IMPOSTARE SUL TIMER",12,muted,true); label.setGravity(Gravity.CENTER); root.addView(label);
        TextView time=text(DevelopmentCatalog.formatTime(e.getInt("seconds")),38,accent,true); time.setGravity(Gravity.CENTER); time.setPadding(0,dp(6),0,dp(20)); root.addView(time);

        LinearLayout sourceCard=new LinearLayout(this); sourceCard.setOrientation(LinearLayout.VERTICAL); sourceCard.setPadding(dp(14),dp(12),dp(14),dp(12)); sourceCard.setBackground(roundRect(card,10,1,border));
        sourceCard.addView(text("Fonte: "+e.getString("source",""),13,primary,true));
        TextView kind=text("Tipo dato: "+e.getString("dataType",""),13,accent,true); kind.setPadding(0,dp(7),0,0); sourceCard.addView(kind);
        TextView sourceData=text("Dato fonte: "+e.getString("sourceData",""),12,muted,false); sourceData.setPadding(0,dp(7),0,0); sourceCard.addView(sourceData);
        TextView calc=text(e.getString("calculation",""),12,muted,false); calc.setPadding(0,dp(7),0,0); sourceCard.addView(calc);
        root.addView(sourceCard,lp(-1,-2));

        String alternatives=e.getString("alternatives","");
        if(alternatives!=null && !alternatives.trim().isEmpty()) {
            Button toggle=button("ALTRE FONTI"); TextView alt=text(alternatives,12,muted,false); alt.setVisibility(View.GONE); alt.setPadding(dp(8),dp(8),dp(8),dp(8));
            toggle.setOnClickListener(v -> alt.setVisibility(alt.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE));
            root.addView(toggle,margin(lp(-1,dp(50)),0,12,0,0)); root.addView(alt);
        }

        TextView note=text("Nessun conto alla rovescia: imposta questo tempo sul tuo timer fisico.",11,muted,false); note.setGravity(Gravity.CENTER); note.setPadding(dp(6),dp(14),dp(6),dp(14)); root.addView(note);
        Button back=button("←  MODIFICA SVILUPPO"); back.setOnClickListener(v -> finish()); root.addView(back,lp(-1,dp(54)));
        setContentView(scroll);
    }

    private Button button(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); b.setTextColor(primary); b.setBackground(roundRect(card,10,1,accent)); return b; }
    private TextView text(String v,float s,int c,boolean bold){ TextView t=new TextView(this); t.setText(v); t.setTextSize(s); t.setTextColor(c); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return t; }
    private GradientDrawable roundRect(int c,int r,int sw,int sc){ GradientDrawable d=new GradientDrawable(); d.setColor(c); d.setCornerRadius(dp(r)); if(sw>0)d.setStroke(dp(sw),sc); return d; }
    private LinearLayout.LayoutParams lp(int w,int h){ return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){ p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
    private int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
}
'''
wr(result_activity, result_source)
print('v0.10.7 OK DevelopmentResultActivity', flush=True)

# Guardrail Timer core: tutte le classi STAMPA (eccetto MainActivity) devono essere bit-identiche alla v0.10.6.
timer_after = {p.name: sha(p) for p in java.glob('*.java') if p.name != 'MainActivity.java'}
if timer_before != timer_after:
    changed = sorted(set(timer_before) | set(timer_after))
    bad = [n for n in changed if timer_before.get(n) != timer_after.get(n)]
    raise SystemExit('v0.10.7 GUARDRAIL TIMER: modificate classi non autorizzate: ' + ', '.join(bad))

# Static acceptance checks.
mt = rd(manifest)
if mt.count('android.intent.action.MAIN') != 1 or mt.count('android.intent.category.LAUNCHER') != 1:
    raise SystemExit('v0.10.7 HOME: launcher non univoco')
if 'package="it.darkroom.timer"' not in mt:
    raise SystemExit('v0.10.7 package applicazione alterato')
if 'SVILUPPO & CHIMICA  ›' in rd(main) or 'assistant.AssistantActivity.class' in rd(main):
    raise SystemExit('v0.10.7 Timer: vecchio pulsante Assistant ancora presente')
checks = {
    build: ['VERSION_NAME = "0.10.7"','VERSION_CODE = "52"'],
    gradle: ["versionCode 52","versionName '0.10.7'"],
    manifest: ['.home.HomeActivity','.MainActivity','.assistant.AssistantActivity','.assistant.development.NewDevelopmentActivity','.assistant.development.DevelopmentResultActivity'],
    home: ['STAMPA','Timer ingranditore','SVILUPPO & CHIMICA','Pellicole, chimica e ricette','MainActivity.class','AssistantActivity.class'],
    assistant: ['NUOVO SVILUPPO','NewDevelopmentActivity.class','PREPARA CHIMICA','LA MIA CHIMICA','LE MIE RICETTE','LOG SVILUPPI','LA MIA ATTREZZATURA'],
    catalog: ['JOBO CPE2','rotazione continua','Fomapan 100 Classic','KODAK D-76','ILFORD ID-11','ILFORD HP5 PLUS','KODAK TRI-X 400','DATO DIRETTO','DATO ADATTATO / CALCOLATO','FOMA — tabella ufficiale di correzione temperatura','Rotary Tube / continuous agitation'],
    new_development: ['ISO NOMINALE','ISO ESPOSTO','TEMPERATURA REALE','Scelta indipendente dalla marca','CALCOLA TEMPO'],
    result_activity: ['TEMPO DA IMPOSTARE SUL TIMER','Fonte: ','Tipo dato: ','JOBO CPE2  ·  rotazione continua','timer fisico']
}
for p, needles in checks.items():
    text = rd(p)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v0.10.7 verifica fallita: {needle} in {p}')

# Cross-brand minimum acceptance: Fomapan + Kodak D-76 and HP5 + Kodak D-76 are explicitly present.
ct = rd(catalog)
if '"Fomapan 100 Classic",100,"KODAK D-76"' not in ct or 'hp5(400,"KODAK D-76"' not in ct:
    raise SystemExit('v0.10.7 cross-brand dataset assente')

print('v0.10.7 RELEASE 2 DARKROOM ASSISTANT — VERIFICHE SORGENTE OK', flush=True)
