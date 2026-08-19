#!/usr/bin/env python3
from pathlib import Path
import re
import shutil

root = Path.cwd()
combined = root / 'combined'
out = combined / 'src/main'
timer = root / 'work/project/app/src/main'
assistant = root / 'assistant/src/main'

if not timer.exists():
    raise SystemExit('Timer materializzato non trovato: work/project/app/src/main')
if not assistant.exists():
    raise SystemExit('Assistant source non trovato')

if out.exists():
    shutil.rmtree(out)
shutil.copytree(timer, out)

# Integra il codice dell'Assistant attuale nello stesso APK.
adst_assistant_java = out / 'java/it/darkroom/assistant'
shutil.copytree(assistant / 'java/it/darkroom/assistant', dst_assistant_java, dirs_exist_ok=True)

# Database offline Digitaltruth e altri asset dell'Assistant.
(out / 'assets').mkdir(parents=True, exist_ok=True)
if (assistant / 'assets').exists():
    for p in (assistant / 'assets').iterdir():
        if p.is_file():
            shutil.copy2(p, out / 'assets' / p.name)

# ---------------------------------------------------------------------------
# HOME UNICA: 4 grandi accessi con sfondo grafico darkroom.
# ---------------------------------------------------------------------------
home = out / 'java/it/darkroom/timer/home/HomeActivity.java'
home.parent.mkdir(parents=True, exist_ok=True)
home.write_text(r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import it.darkroom.timer.MainActivity;
import it.darkroom.assistant.AssistantActivityV2;

/** Home unica dell'app Darkroom. */
public final class HomeActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        buildUi();
    }

    private void buildUi() {
        FrameLayout frame = new FrameLayout(this);
        frame.setBackgroundColor(Color.BLACK);
        frame.addView(new DarkroomBackdrop(this), new FrameLayout.LayoutParams(-1, -1));

        View veil = new View(this);
        veil.setBackgroundColor(Color.argb(82, 0, 0, 0));
        frame.addView(veil, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(24), dp(44), dp(24), dp(28));

        TextView title = new TextView(this);
        title.setText("DARKROOM");
        title.setTextColor(Color.rgb(246, 243, 238));
        title.setTextSize(42);
        title.setGravity(Gravity.CENTER);
        title.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        root.addView(title, lp(-1, -2));

        TextView sub = new TextView(this);
        sub.setText("camera oscura");
        sub.setTextColor(Color.rgb(196, 188, 181));
        sub.setTextSize(16);
        sub.setGravity(Gravity.CENTER);
        root.addView(sub, margin(lp(-1, -2), 0, 4, 0, 34));

        Button products = card("PRODOTTI CHIMICI", Color.argb(220, 88, 23, 25));
        products.setOnClickListener(v -> openAssistant("products"));
        root.addView(products, margin(lp(-1, dp(82)), 0, 0, 0, 13));

        Button film = card("SVILUPPO PELLICOLA", Color.argb(220, 30, 30, 31));
        film.setOnClickListener(v -> openAssistant("film"));
        root.addView(film, margin(lp(-1, dp(82)), 0, 0, 0, 13));

        Button paper = card("BAGNI STAMPA", Color.argb(220, 73, 62, 54));
        paper.setOnClickListener(v -> openAssistant("paper"));
        root.addView(paper, margin(lp(-1, dp(82)), 0, 0, 0, 13));

        Button timer = card("TIMER STAMPA", Color.argb(230, 132, 26, 30));
        timer.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        root.addView(timer, lp(-1, dp(82)));

        LinearLayout.LayoutParams rootLp = new LinearLayout.LayoutParams(-1, -1);
        frame.addView(root, new FrameLayout.LayoutParams(-1, -1));
        setContentView(frame);
    }

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }

    private Button card(String text, int color) {
        Button b = new Button(this);
        b.setText(text + "    ›");
        b.setAllCaps(false);
        b.setTextColor(Color.rgb(248, 245, 240));
        b.setTextSize(20);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        b.setPadding(dp(24), 0, dp(18), 0);
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(22));
        g.setStroke(dp(1), Color.argb(130, 180, 169, 160));
        b.setBackground(g);
        return b;
    }

    private LinearLayout.LayoutParams lp(int w, int h) { return new LinearLayout.LayoutParams(w, h); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(dp(l), dp(t), dp(r), dp(b)); return p;
    }
    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }

    /** Illustrazione analogica disegnata direttamente: ingranditore, luce rossa, bacinella e stampa. */
    private static final class DarkroomBackdrop extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        DarkroomBackdrop(android.content.Context c) { super(c); }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            float w=getWidth(), h=getHeight();
            p.setShader(new LinearGradient(0,0,0,h,
                    new int[]{Color.rgb(16,10,10),Color.rgb(3,3,3),Color.BLACK},
                    new float[]{0f,.54f,1f}, Shader.TileMode.CLAMP));
            c.drawRect(0,0,w,h,p); p.setShader(null);

            // Alone rosso della luce inattinica.
            p.setShader(new RadialGradient(w*.82f,h*.17f,w*.34f,
                    new int[]{Color.argb(120,170,22,24),Color.argb(30,120,10,12),Color.TRANSPARENT},
                    null,Shader.TileMode.CLAMP));
            c.drawCircle(w*.82f,h*.17f,w*.34f,p); p.setShader(null);
            p.setColor(Color.argb(205,145,25,28)); c.drawCircle(w*.84f,h*.13f,w*.035f,p);

            // Sagoma ingranditore a sinistra.
            p.setColor(Color.argb(190,65,58,55));
            c.drawRoundRect(w*.10f,h*.12f,w*.18f,h*.52f,12,12,p);
            c.drawRoundRect(w*.07f,h*.19f,w*.31f,h*.27f,20,20,p);
            c.drawRoundRect(w*.13f,h*.27f,w*.25f,h*.34f,16,16,p);
            p.setColor(Color.argb(160,205,188,172));
            c.drawRect(w*.17f,h*.34f,w*.21f,h*.57f,p);
            p.setColor(Color.argb(175,71,62,58));
            c.drawRoundRect(w*.06f,h*.56f,w*.34f,h*.61f,16,16,p);

            // Piano/bacinella in basso con foglio fotografico.
            p.setColor(Color.argb(170,45,41,39));
            c.drawRoundRect(w*.05f,h*.78f,w*.95f,h*.91f,24,24,p);
            p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(3);
            p.setColor(Color.argb(150,133,116,107));
            c.drawRoundRect(w*.08f,h*.80f,w*.92f,h*.89f,20,20,p);
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb(180,220,211,198));
            c.save(); c.rotate(-5,w*.61f,h*.845f);
            c.drawRoundRect(w*.47f,h*.81f,w*.76f,h*.88f,8,8,p); c.restore();

            // Grana / riflessi discreti.
            p.setColor(Color.argb(28,255,235,220));
            for(int i=0;i<34;i++) {
                float x=((i*97)%1000)/1000f*w;
                float y=((i*151)%1000)/1000f*h;
                c.drawCircle(x,y,1.2f+(i%3),p);
            }
        }
    }
}
''', encoding='utf-8')

# Application combinata: conserva le migrazioni leggere dell'Assistant.
app_file = out / 'java/it/darkroom/timer/combined/CombinedApp.java'
app_file.parent.mkdir(parents=True, exist_ok=True)
app_file.write_text(r'''package it.darkroom.timer.combined;
public final class CombinedApp extends it.darkroom.assistant.DarkroomAssistantApp { }
''', encoding='utf-8')

# ---------------------------------------------------------------------------
# Assistant: ingresso diretto dalle 3 card, HOME unica, stato dei campi persistente.
# ---------------------------------------------------------------------------
afile = dst_assistant_java / 'AssistantActivityV2.java'
s = afile.read_text(encoding='utf-8')

# Solo le due tank richieste. 2563 mantiene il riempimento rotazione documentato.
s = re.sub(r'''    private final Tank\[\] tanks = new Tank\[\]\{.*?\n    \};''',
'''    private final Tank[] tanks = new Tank[]{
            new Tank("JOBO 2520", 270, 2, 1),
            new Tank("JOBO 2563", 850, 6, 8)
    };''', s, count=1, flags=re.S)

# Mostra entrambe le tank se hanno capienza; la 2563 viene poi bloccata se supera il limite CPE2.
s = s.replace('if (cap >= rolls && t.rotaryMl <= 600) compatibleTanks.add(t);',
              'if (cap >= rolls) compatibleTanks.add(t);')

# Protezione CPE2: 2563 visibile ma non si inventa un volume inferiore a quello documentato.
needle = '        Tank tank = selectedTank();\n        if (tank == null) { resultFilmError("Nessuna tank compatibile."); return; }'
repl = '''        Tank tank = selectedTank();
        if (tank == null) { resultFilmError("Nessuna tank compatibile."); return; }
        if (tank.rotaryMl > 600) {
            resultFilmError(tank.name + " richiede " + tank.rotaryMl +
                    " ml in rotazione: supera il limite 600 ml della JOBO CPE2.");
            return;
        }'''
if needle in s:
    s = s.replace(needle, repl, 1)

# onCreate: apre direttamente la sezione richiesta dalla Home unica.
old = '''        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);
        showHome();'''
new = '''        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);
        String target = getIntent().getStringExtra("darkroom_target");
        if ("products".equals(target)) showProducts();
        else if ("film".equals(target)) showFilm();
        else if ("paper".equals(target)) showPaper();
        else finish();'''
if old not in s:
    raise SystemExit('Assistant onCreate marker missing')
s = s.replace(old, new, 1)

# Back = Home unica.
s = re.sub(r'''    @Override\n    public void onBackPressed\(\) \{.*?\n    \}\n''',
'''    @Override
    public void onBackPressed() {
        saveCurrentUiState();
        finish();
    }

    @Override
    protected void onPause() {
        saveCurrentUiState();
        super.onPause();
    }
''', s, count=1, flags=re.S)

# Casetta in alto a sinistra in tutte le pagine Assistant.
s = s.replace('TextView home = label("☰", 28, WHITE, false);',
              'TextView home = label("⌂", 30, WHITE, true);')
s = s.replace('home.setOnClickListener(v -> showHome());',
              'home.setOnClickListener(v -> { saveCurrentUiState(); finish(); });')

# Ripristino dopo costruzione delle schermate.
def add_restore(method_name, call):
    global s
    start = s.find('    private void ' + method_name + '(')
    if start < 0: raise SystemExit(method_name + ' not found')
    nxt = s.find('\n    private ', start + 20)
    if nxt < 0: nxt = len(s)
    seg = s[start:nxt]
    marker = '        setContentView(scroll(page));'
    if marker not in seg: raise SystemExit(method_name + ' setContentView marker missing')
    seg = seg.replace(marker, marker + '\n        ' + call + ';', 1)
    s = s[:start] + seg + s[nxt:]

add_restore('showFilm', 'restoreFilmUiState()')
add_restore('showPaper', 'restorePaperUiState()')

# Helper stato prima della sezione UI / UTILITY.
marker = '    // ---------------------------------------------------------------------\n    // UI / UTILITY\n    // ---------------------------------------------------------------------'
if marker not in s:
    raise SystemExit('UI utility marker missing')
helpers = r'''    // ---------------------------------------------------------------------
    // STATO ULTIMA SESSIONE: i campi restano popolati uscendo e rientrando.
    // ---------------------------------------------------------------------
    private void saveCurrentUiState() {
        if (prefs == null) return;
        SharedPreferences.Editor e = prefs.edit();
        if (currentScreen == FILM && filmField != null) {
            e.putString("last_film_name", filmField.getText().toString().trim());
            e.putInt("last_film_nominal", selectedFilm == null ? 0 : selectedFilm.nominalIso);
            e.putString("last_film_format", selectedFilm == null ? "" : selectedFilm.format);
            e.putString("last_film_iso", isoField == null ? "" : isoField.getText().toString());
            e.putString("last_film_rolls", spinnerText(rollsSpinner));
            e.putString("last_film_tank", spinnerText(tankSpinner));
            e.putString("last_film_dev", spinnerText(developerSpinner));
            e.putString("last_film_dil", spinnerText(dilutionSpinner));
            e.putString("last_film_temp", temperatureField == null ? "" : temperatureField.getText().toString());
            e.putString("last_film_stop", spinnerText(stopSpinner));
            e.putString("last_film_fix", spinnerText(fixSpinner));
        } else if (currentScreen == PAPER && paperVolumeField != null) {
            e.putString("last_paper_dev", spinnerText(paperDeveloperSpinner));
            e.putString("last_paper_dil", spinnerText(paperDeveloperDilutionSpinner));
            e.putString("last_paper_stop", spinnerText(paperStopSpinner));
            e.putString("last_paper_fix", spinnerText(paperFixSpinner));
            e.putString("last_paper_volume", paperVolumeField.getText().toString());
            e.putString("last_paper_w", paperWidthField.getText().toString());
            e.putString("last_paper_h", paperHeightField.getText().toString());
            e.putString("last_paper_sheets", paperSheetsField.getText().toString());
        }
        e.apply();
    }

    private void restoreFilmUiState() {
        String film = prefs.getString("last_film_name", "");
        if (!film.isEmpty()) {
            int nominal = prefs.getInt("last_film_nominal", 0);
            String format = prefs.getString("last_film_format", "");
            selectFilm(new FilmStock(film, nominal, format, ""));
        }
        String iso = prefs.getString("last_film_iso", "");
        if (!iso.isEmpty() && isoField != null) isoField.setText(iso);
        String temp = prefs.getString("last_film_temp", "");
        if (!temp.isEmpty() && temperatureField != null) temperatureField.setText(temp);
        selectSpinnerText(rollsSpinner, prefs.getString("last_film_rolls", ""));
        updateCompatibleTanks();
        selectSpinnerText(tankSpinner, prefs.getString("last_film_tank", ""));
        selectSpinnerText(developerSpinner, prefs.getString("last_film_dev", ""));
        selectSpinnerText(stopSpinner, prefs.getString("last_film_stop", ""));
        selectSpinnerText(fixSpinner, prefs.getString("last_film_fix", ""));
        if (developerSpinner != null) developerSpinner.post(() ->
                selectSpinnerText(dilutionSpinner, prefs.getString("last_film_dil", "")));
    }

    private void restorePaperUiState() {
        selectSpinnerText(paperDeveloperSpinner, prefs.getString("last_paper_dev", ""));
        selectSpinnerText(paperStopSpinner, prefs.getString("last_paper_stop", ""));
        selectSpinnerText(paperFixSpinner, prefs.getString("last_paper_fix", ""));
        if (paperDeveloperSpinner != null) paperDeveloperSpinner.post(() ->
                selectSpinnerText(paperDeveloperDilutionSpinner, prefs.getString("last_paper_dil", "")));
        setIfSaved(paperVolumeField, "last_paper_volume");
        setIfSaved(paperWidthField, "last_paper_w");
        setIfSaved(paperHeightField, "last_paper_h");
        setIfSaved(paperSheetsField, "last_paper_sheets");
    }

    private void setIfSaved(EditText field, String key) {
        if (field == null) return;
        String v = prefs.getString(key, "");
        if (!v.isEmpty()) field.setText(v);
    }

    private String spinnerText(Spinner s) {
        return s == null || s.getSelectedItem() == null ? "" : String.valueOf(s.getSelectedItem());
    }

    private void selectSpinnerText(Spinner s, String wanted) {
        if (s == null || wanted == null || wanted.isEmpty() || s.getAdapter() == null) return;
        for (int i=0; i<s.getAdapter().getCount(); i++) {
            if (wanted.equals(String.valueOf(s.getAdapter().getItem(i)))) {
                s.setSelection(i);
                return;
            }
        }
    }

'''
s = s.replace(marker, helpers + marker, 1)
afile.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# Timer: la HOME esistente diventa una piccola casetta in alto a sinistra.
# ---------------------------------------------------------------------------
tmain = out / 'java/it/darkroom/timer/MainActivity.java'
ts = tmain.read_text(encoding='utf-8')
ts = ts.replace('compactButton("← HOME")', 'compactButton("⌂")')
ts = ts.replace('margin(lp(dp(94), dp(38)), 0, 0, 0, 4)',
                'margin(lp(dp(52), dp(38)), 0, 0, 0, 4)')
tmain.write_text(ts, encoding='utf-8')

# ---------------------------------------------------------------------------
# Manifest combinato: nuovo nome/app id da Gradle, launcher Home timer sostituita,
# Assistant V2 registrato nello stesso APK.
# ---------------------------------------------------------------------------
manifest = out / 'AndroidManifest.xml'
ms = manifest.read_text(encoding='utf-8')
ms = re.sub(r'android:versionCode="[^"]+"', 'android:versionCode="1"', ms, count=1)
ms = re.sub(r'android:versionName="[^"]+"', 'android:versionName="0.1.0"', ms, count=1)
ms = ms.replace('android:label="Darkroom Timer"', 'android:label="Darkroom"')
if 'android:name=' not in ms.split('<application',1)[1].split('>',1)[0]:
    ms = ms.replace('<application\n', '<application\n        android:name="it.darkroom.timer.combined.CombinedApp"\n', 1)
else:
    ms = re.sub(r'(<application[^>]*?)android:name="[^"]+"',
                r'\1android:name="it.darkroom.timer.combined.CombinedApp"', ms, count=1, flags=re.S)
assistant_activity = '''\n        <activity\n            android:name="it.darkroom.assistant.AssistantActivityV2"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
if 'it.darkroom.assistant.AssistantActivityV2' not in ms:
    ms = ms.replace('</application>', assistant_activity + '    </application>', 1)
manifest.write_text(ms, encoding='utf-8')

# Guardrail chiari.
assert (out/'assets/mdc_full.sqlite').exists(), 'MDC DB missing'
assert 'PRODOTTI CHIMICI' in home.read_text(encoding='utf-8')
assert 'SVILUPPO PELLICOLA' in home.read_text(encoding='utf-8')
assert 'BAGNI STAMPA' in home.read_text(encoding='utf-8')
assert 'TIMER STAMPA' in home.read_text(encoding='utf-8')
assert 'new Tank("JOBO 2520", 270, 2, 1)' in s
assert 'new Tank("JOBO 2563", 850, 6, 8)' in s
assert 'JOBO 1510' not in s[s.find('private final Tank[] tanks'):s.find('private FilmStock selectedFilm')]
assert 'restoreFilmUiState();' in s and 'restorePaperUiState();' in s
assert 'compactButton("⌂")' in ts
print('Combined Darkroom sources prepared')
