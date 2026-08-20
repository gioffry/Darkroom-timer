#!/usr/bin/env python3
from pathlib import Path
import base64

root = Path('combined')
home = root / 'src/main/java/it/darkroom/timer/home/HomeActivity.java'
assistant = root / 'src/main/java/it/darkroom/assistant/AssistantActivityV2.java'
maintenance = root / 'src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java'
manifest = root / 'src/main/AndroidManifest.xml'

for p in (home, assistant, maintenance, manifest):
    if not p.exists():
        raise SystemExit('v0.2.0: generated base file missing: ' + str(p))

# -----------------------------------------------------------------------------
# HOME: restore the approved CAMERA OSCURA artwork instead of the later HD
# reinterpretation. The existing v0.1.3 asset is the approved 432x768 mockup
# used as the visual source; only the new maintenance control and real version
# label are drawn above it.
# -----------------------------------------------------------------------------
assets = root / 'v012_assets/home_mockup'
parts = sorted(assets.glob('*.part'))
if len(parts) != 2:
    raise SystemExit(f'v0.2.0: expected 2 approved home asset parts, found {len(parts)}')
encoded = ''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
encoded += '=' * (-len(encoded) % 4)
try:
    image_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit('v0.2.0: approved home asset invalid base64: ' + str(exc))
if len(image_bytes) < 16000 or image_bytes[:4] != b'RIFF' or image_bytes[8:12] != b'WEBP':
    raise SystemExit('v0.2.0: approved home asset is not the expected WebP')

drawable = root / 'src/main/res/drawable-nodpi'
drawable.mkdir(parents=True, exist_ok=True)
for old in (drawable / 'home_vintage.jpg', drawable / 'home_vintage.png', drawable / 'home_vintage.webp'):
    if old.exists():
        old.unlink()
(drawable / 'home_vintage.webp').write_bytes(image_bytes)

home_source = r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import it.darkroom.timer.MainActivity;
import it.darkroom.timer.R;
import it.darkroom.assistant.AssistantActivityV2;
import it.darkroom.timer.maintenance.UseMaintenanceActivity;

/**
 * Darkroom Home v0.2.0.
 * The approved CAMERA OSCURA mockup is the artwork itself; controls are only
 * transparent hotspots plus the secondary Uso e Manutenzione control.
 */
public final class HomeActivity extends Activity {
    private static final float ART_W = 432f;
    private static final float ART_H = 768f;
    private static final int BRONZE = Color.rgb(181, 139, 82);
    private static final int WARM = Color.rgb(239, 226, 207);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().setNavigationBarColor(Color.BLACK);

        FrameLayout frame = new FrameLayout(this);
        frame.setBackgroundColor(Color.BLACK);

        ImageView artwork = new ImageView(this);
        artwork.setScaleType(ImageView.ScaleType.FIT_CENTER);
        artwork.setAdjustViewBounds(false);
        artwork.setImageResource(R.drawable.home_vintage);
        frame.addView(artwork, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        View products = hotspot("Prodotti chimici");
        View film = hotspot("Sviluppo pellicola");
        View paper = hotspot("Bagni stampa");
        View timer = hotspot("Timer stampa");
        LinearLayout maintenance = secondaryButton();
        TextView version = versionLabel();

        products.setOnClickListener(v -> openAssistant("products"));
        film.setOnClickListener(v -> openAssistant("film"));
        paper.setOnClickListener(v -> openAssistant("paper"));
        timer.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        maintenance.setOnClickListener(v -> startActivity(new Intent(this, UseMaintenanceActivity.class)));

        frame.addView(products, new FrameLayout.LayoutParams(1, 1));
        frame.addView(film, new FrameLayout.LayoutParams(1, 1));
        frame.addView(paper, new FrameLayout.LayoutParams(1, 1));
        frame.addView(timer, new FrameLayout.LayoutParams(1, 1));
        frame.addView(maintenance, new FrameLayout.LayoutParams(1, 1));
        frame.addView(version, new FrameLayout.LayoutParams(1, 1));

        View[] primary = new View[]{products, film, paper, timer};
        frame.addOnLayoutChangeListener((v, left, top, right, bottom,
                                         oldLeft, oldTop, oldRight, oldBottom) ->
                placeHomeControls(frame, primary, maintenance, version));

        setContentView(frame);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    private View hotspot(String description) {
        View v = new View(this);
        v.setBackground(new ColorDrawable(Color.TRANSPARENT));
        v.setClickable(true);
        v.setFocusable(true);
        v.setContentDescription(description);
        return v;
    }

    private LinearLayout secondaryButton() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(7), dp(3), dp(7), dp(3));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.argb(218, 20, 16, 13));
        bg.setStroke(dp(1), BRONZE);
        bg.setCornerRadius(dp(9));
        bar.setBackground(bg);
        bar.setClickable(true);
        bar.setFocusable(true);
        bar.setContentDescription("Uso e manutenzione");

        FrameLayout iconRing = new FrameLayout(this);
        GradientDrawable ring = new GradientDrawable();
        ring.setShape(GradientDrawable.OVAL);
        ring.setColor(Color.argb(80, 0, 0, 0));
        ring.setStroke(dp(1), Color.argb(180, 181, 139, 82));
        iconRing.setBackground(ring);
        ImageView wrench = new ImageView(this);
        wrench.setImageResource(R.drawable.ic_wrench_bronze);
        wrench.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        FrameLayout.LayoutParams wi = new FrameLayout.LayoutParams(dp(20), dp(20), Gravity.CENTER);
        iconRing.addView(wrench, wi);
        bar.addView(iconRing, new LinearLayout.LayoutParams(dp(31), dp(31)));

        TextView label = new TextView(this);
        label.setText("USO E MANUTENZIONE");
        label.setTextColor(WARM);
        label.setTextSize(12.5f);
        label.setGravity(Gravity.CENTER);
        label.setLetterSpacing(0.055f);
        label.setTypeface(android.graphics.Typeface.create(android.graphics.Typeface.SERIF,
                android.graphics.Typeface.BOLD));
        LinearLayout.LayoutParams ll = new LinearLayout.LayoutParams(0, -1, 1f);
        ll.setMargins(dp(5), 0, dp(4), 0);
        bar.addView(label, ll);

        TextView arrow = new TextView(this);
        arrow.setText("›");
        arrow.setTextColor(BRONZE);
        arrow.setTextSize(25f);
        arrow.setGravity(Gravity.CENTER);
        bar.addView(arrow, new LinearLayout.LayoutParams(dp(20), -1));
        return bar;
    }

    private TextView versionLabel() {
        TextView v = new TextView(this);
        v.setText(readInstalledVersion());
        v.setTextColor(Color.argb(185, 220, 208, 191));
        v.setTextSize(10f);
        v.setGravity(Gravity.CENTER);
        v.setLetterSpacing(0.10f);
        return v;
    }

    private String readInstalledVersion() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(getPackageName(), 0);
            return "v" + p.versionName;
        } catch (Exception ignored) {
            return "v—";
        }
    }

    private void placeHomeControls(FrameLayout frame, View[] v, View maintenance, View version) {
        int w = frame.getWidth();
        int h = frame.getHeight();
        if (w <= 0 || h <= 0 || v.length != 4) return;

        // Must match ImageView.ScaleType.FIT_CENTER: preserve the approved mockup,
        // never crop the title, notebook or outer rounded frame.
        float scale = Math.min(w / ART_W, h / ART_H);
        float dx = (w - ART_W * scale) * 0.5f;
        float dy = (h - ART_H * scale) * 0.5f;

        place(v[0], dx, dy, scale, 52f, 238f, 380f, 320f);
        place(v[1], dx, dy, scale, 52f, 324f, 380f, 407f);
        place(v[2], dx, dy, scale, 52f, 410f, 380f, 494f);
        place(v[3], dx, dy, scale, 52f, 497f, 380f, 582f);

        // Secondary control: deliberately narrower and quieter than the four cards.
        place(maintenance, dx, dy, scale, 123f, 599f, 309f, 631f);
        place(version, dx, dy, scale, 166f, 740f, 266f, 760f);
    }

    private void place(View v, float dx, float dy, float scale,
                       float l, float t, float r, float b) {
        FrameLayout.LayoutParams lp = (FrameLayout.LayoutParams) v.getLayoutParams();
        lp.width = Math.max(1, Math.round((r - l) * scale));
        lp.height = Math.max(1, Math.round((b - t) * scale));
        lp.leftMargin = Math.round(dx + l * scale);
        lp.topMargin = Math.round(dy + t * scale);
        v.setLayoutParams(lp);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }
}
'''
home.write_text(home_source, encoding='utf-8')

# -----------------------------------------------------------------------------
# ASSISTANT SECTIONS: keep all chemistry/development logic untouched and change
# only shared UI builders. This makes PRODOTTI CHIMICI / SVILUPPO PELLICOLA /
# BAGNI STAMPA speak the same operational language as the Timer.
# -----------------------------------------------------------------------------
s = assistant.read_text(encoding='utf-8')

def replace_between(text, start_marker, end_marker, replacement, label):
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit('v0.2.0: assistant UI marker missing: ' + label + ' start')
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise SystemExit('v0.2.0: assistant UI marker missing: ' + label + ' end')
    return text[:start] + replacement + text[end:]

page_method = r'''    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(28));
        page.setBackgroundColor(BG);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView home = label("⌂", 25, WHITE, true);
        home.setGravity(Gravity.CENTER);
        home.setContentDescription("Torna alla Home");
        home.setOnClickListener(v -> {
            saveCurrentUiState();
            finish();
        });
        top.addView(home, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView h = label(title.toUpperCase(Locale.ITALY), 24, WHITE, true);
        h.setGravity(Gravity.CENTER);
        top.addView(h, new LinearLayout.LayoutParams(0, dp(46), 1f));

        View spacer = new View(this);
        top.addView(spacer, new LinearLayout.LayoutParams(dp(46), dp(46)));
        page.addView(top, new LinearLayout.LayoutParams(-1, dp(46)));

        if (subtitle != null && !subtitle.trim().isEmpty()) {
            TextView sub = label(subtitle, 13, MUTED, false);
            sub.setGravity(Gravity.CENTER);
            sub.setPadding(dp(8), dp(5), dp(8), dp(8));
            page.addView(sub);
        }

        View accent = new View(this);
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(dp(34), dp(2));
        ap.gravity = Gravity.CENTER_HORIZONTAL;
        ap.setMargins(0, dp(3), 0, dp(20));
        accent.setLayoutParams(ap);
        accent.setBackground(bg(BURGUNDY_BRIGHT, 2, 0, 0));
        page.addView(accent);
        return page;
    }

'''
s = replace_between(s,
        '    private LinearLayout page(String title, String subtitle) {',
        '    private View homeCard(String text, int color, View.OnClickListener listener) {',
        page_method,
        'page')

home_card_method = r'''    private View homeCard(String text, int color, View.OnClickListener listener) {
        TextView card = label(text + "    ›", 19, WHITE, true);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(20), dp(18), dp(18), dp(18));
        card.setMinHeight(dp(88));
        card.setBackground(bg(color, 12, BORDER, 1));
        card.setOnClickListener(listener);
        return card;
    }

'''
s = replace_between(s,
        '    private View homeCard(String text, int color, View.OnClickListener listener) {',
        '    private LinearLayout fieldBlock(String labelText, View field) {',
        home_card_method,
        'homeCard')

style_input = r'''    private void styleInput(TextView v) {
        v.setTextColor(WHITE);
        v.setHintTextColor(MUTED);
        v.setTextSize(15);
        v.setPadding(dp(13), dp(11), dp(13), dp(11));
        v.setBackground(bg(CARD, 10, BORDER, 1));
        v.setMinHeight(dp(50));
    }

'''
s = replace_between(s,
        '    private void styleInput(TextView v) {',
        '    private EditText edit(String value, int type) {',
        style_input,
        'styleInput')

action_method = r'''    private Button actionButton(String text, int color) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(WHITE);
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setAllCaps(false);
        b.setMinHeight(dp(52));
        b.setPadding(dp(14), 0, dp(14), 0);
        int stroke = color == BURGUNDY ? BURGUNDY_BRIGHT : BORDER;
        b.setBackground(bg(color, 10, stroke, 1));
        return b;
    }

'''
s = replace_between(s,
        '    private Button actionButton(String text, int color) {',
        '    private Button smallButton(String text) {',
        action_method,
        'actionButton')

small_method = r'''    private Button smallButton(String text) {
        Button b = actionButton(text, CARD_2);
        b.setMinHeight(dp(44));
        b.setTextSize(13);
        return b;
    }

'''
s = replace_between(s,
        '    private Button smallButton(String text) {',
        '    private TextView row(String text) {',
        small_method,
        'smallButton')

row_method = r'''    private TextView row(String text) {
        TextView v = label(text, 16, WHITE, true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(16), dp(14), dp(16), dp(14));
        v.setMinHeight(dp(56));
        v.setBackground(bg(CARD, 10, BORDER, 1));
        return v;
    }

'''
s = replace_between(s,
        '    private TextView row(String text) {',
        '    private void resultLine(LinearLayout parent, String labelText, String value) {',
        row_method,
        'row')

result_method = r'''    private void resultLine(LinearLayout parent, String labelText, String value) {
        LinearLayout r = new LinearLayout(this);
        r.setOrientation(LinearLayout.VERTICAL);
        r.setPadding(dp(15), dp(12), dp(15), dp(12));
        r.setBackground(bg(CARD, 10, BORDER, 1));
        r.addView(label(labelText, 11, MUTED, false));
        r.addView(space(4));
        r.addView(label(value, 17, WHITE, true));
        parent.addView(r);
        parent.addView(space(8));
    }

'''
s = replace_between(s,
        '    private void resultLine(LinearLayout parent, String labelText, String value) {',
        '    private ScrollView scroll(View content) {',
        result_method,
        'resultLine')

# Keep the existing black/gray/red palette but remove the third visual language.
s = s.replace('    private static final int CARD_2 = Color.rgb(39, 39, 39);',
              '    private static final int CARD_2 = Color.rgb(32, 32, 32);', 1)
s = s.replace('    private static final int TAUPE = Color.rgb(103, 95, 88);',
              '    private static final int TAUPE = Color.rgb(48, 44, 41);', 1)
assistant.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# USO E MANUTENZIONE: preserve the successful cards/accordion/content, align
# only the common chrome (top bar, black/gray palette and borders) to Timer.
# -----------------------------------------------------------------------------
m = maintenance.read_text(encoding='utf-8')
m = m.replace('    private static final int BG = Color.rgb(9, 8, 7);',
              '    private static final int BG = Color.rgb(0, 0, 0);', 1)
m = m.replace('    private static final int PANEL = Color.rgb(24, 20, 17);',
              '    private static final int PANEL = Color.rgb(24, 24, 24);', 1)
m = m.replace('    private static final int WARM = Color.rgb(232, 221, 203);',
              '    private static final int WARM = Color.rgb(246, 243, 238);', 1)
m = m.replace('    private static final int MUTED = Color.rgb(169, 154, 134);',
              '    private static final int MUTED = Color.rgb(170, 166, 162);', 1)
m = m.replace('    private static final int RED = Color.rgb(103, 34, 30);',
              '    private static final int RED = Color.rgb(124, 31, 31);', 1)

begin_start = '    private void begin(String heading,String subheading){'
begin_end = '    private LinearLayout navCard(String heading,String detail,Runnable action){'
new_begin = r'''    private void begin(String heading,String subheading){
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        body=new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(16),dp(14),dp(16),dp(28));
        scroll.addView(body,new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout top=new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView back=actionText(backStack.isEmpty()?"⌂":"←");
        back.setGravity(Gravity.CENTER);
        back.setContentDescription(backStack.isEmpty()?"Torna alla Home":"Indietro");
        back.setOnClickListener(v->onBackPressed());
        top.addView(back,new LinearLayout.LayoutParams(dp(46),dp(46)));
        TextView h=title(heading,24);
        h.setGravity(Gravity.CENTER);
        top.addView(h,new LinearLayout.LayoutParams(0,dp(46),1f));
        View spacer=new View(this);
        top.addView(spacer,new LinearLayout.LayoutParams(dp(46),dp(46)));
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(46)));

        if(subheading!=null&&!subheading.isEmpty()){
            TextView sub=subtitle(subheading);
            sub.setGravity(Gravity.CENTER);
            body.addView(sub,margin(-1,-2,dp(8),dp(5),dp(8),dp(15)));
        } else {
            body.addView(new View(this),margin(1,1,0,0,0,dp(10)));
        }
        setContentView(scroll);
    }

'''
bs = m.find(begin_start)
be = m.find(begin_end, bs + len(begin_start)) if bs >= 0 else -1
if bs < 0 or be < 0:
    raise SystemExit('v0.2.0: UseMaintenance begin() markers missing')
m = m[:bs] + new_begin + m[be:]

old_card = '    private LinearLayout card(){ LinearLayout c=new LinearLayout(this); c.setOrientation(LinearLayout.VERTICAL); c.setPadding(dp(15),dp(13),dp(15),dp(13)); GradientDrawable bg=new GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(12)); bg.setStroke(dp(1),Color.rgb(72,56,43)); c.setBackground(bg); c.setElevation(dp(1)); c.setLayoutParams(margin(-1,-2,0,0,0,dp(10))); return c; }'
new_card = '    private LinearLayout card(){ LinearLayout c=new LinearLayout(this); c.setOrientation(LinearLayout.VERTICAL); c.setPadding(dp(15),dp(13),dp(15),dp(13)); GradientDrawable bg=new GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(10)); bg.setStroke(dp(1),Color.rgb(67,67,67)); c.setBackground(bg); c.setElevation(dp(1)); c.setLayoutParams(margin(-1,-2,0,0,0,dp(10))); return c; }'
if old_card not in m:
    raise SystemExit('v0.2.0: UseMaintenance card() marker missing')
m = m.replace(old_card, new_card, 1)
maintenance.write_text(m, encoding='utf-8')

# -----------------------------------------------------------------------------
# Static regression guards: UI-only change, no Timer/SONOFF code touched.
# -----------------------------------------------------------------------------
hs = home.read_text(encoding='utf-8')
for marker in [
    'ImageView.ScaleType.FIT_CENTER',
    'R.drawable.home_vintage',
    'openAssistant("products")',
    'openAssistant("film")',
    'openAssistant("paper")',
    'MainActivity.class',
    'UseMaintenanceActivity.class',
    'USO E MANUTENZIONE',
    'getPackageInfo(getPackageName(), 0)',
    'place(maintenance, dx, dy, scale, 123f, 599f, 309f, 631f)',
]:
    if marker not in hs:
        raise SystemExit('v0.2.0: Home guard failed: ' + marker)

asrc = assistant.read_text(encoding='utf-8')
for marker in ['saveCurrentUiState();', 'finish();', 'title.toUpperCase(Locale.ITALY)',
               'bg(CARD, 10, BORDER, 1)', 'showProducts()', 'showFilm()', 'showPaper()']:
    if marker not in asrc:
        raise SystemExit('v0.2.0: Assistant visual guard failed: ' + marker)

msrc = maintenance.read_text(encoding='utf-8')
for marker in ['Q_OPEMUS','Q_COLOR3','Q_JOBO','Q_ACP','Q_MINOLTA','Q_TESTSTRIP','Q_SPLIT','Q_ZONE','Q_PRINT',
               'Svitol è parte dell’intervento personale, NON un’indicazione del manuale',
               'THE DARKROOM COOKBOOK','backStack.isEmpty()?"⌂":"←"']:
    if marker not in msrc:
        raise SystemExit('v0.2.0: UseMaintenance regression guard failed: ' + marker)

if not (drawable / 'home_vintage.webp').exists():
    raise SystemExit('v0.2.0: approved Home artwork not written')
print('Darkroom v0.2.0 visual coherence patch ready')
