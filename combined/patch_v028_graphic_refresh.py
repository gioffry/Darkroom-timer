#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
java = root / 'src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
home = java / 'home/HomeActivity.java'
maintenance = java / 'maintenance/UseMaintenanceActivity.java'
assistant = root / 'src/main/java/it/darkroom/assistant/AssistantActivityV2.java'
enlargement = java / 'EnlargementActivity.java'
manifest = root / 'src/main/AndroidManifest.xml'
res = root / 'src/main/res'

for p in (main, home, maintenance, assistant, enlargement, manifest):
    if not p.exists():
        raise SystemExit('v0.2.8 generated file missing: ' + str(p))


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.2.8 {label}: expected >= {count}, found {n}')
    wr(p, s.replace(old, new, count))
    print('v0.2.8 OK', label, flush=True)

def replace_between(p, start_marker, end_marker, replacement, label):
    s = rd(p)
    a = s.find(start_marker)
    if a < 0: raise SystemExit('v0.2.8 '+label+': start marker missing')
    b = s.find(end_marker, a + len(start_marker))
    if b < 0: raise SystemExit('v0.2.8 '+label+': end marker missing')
    wr(p, s[:a] + replacement + s[b:])
    print('v0.2.8 OK', label, flush=True)

# -----------------------------------------------------------------------------
# 0. FINAL HOME — entirely native Android, no bitmap/artwork/hotspots.
# -----------------------------------------------------------------------------
home_source = r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import it.darkroom.assistant.AssistantActivityV2;
import it.darkroom.timer.MainActivity;
import it.darkroom.timer.maintenance.UseMaintenanceActivity;

/** Final native Home: no decorative bitmap dependency. */
public final class HomeActivity extends Activity {
    private static final int BG = Color.rgb(5, 6, 7);
    private static final int CARD = Color.rgb(18, 19, 20);
    private static final int IVORY = Color.rgb(235, 210, 174);
    private static final int MUTED = Color.rgb(164, 151, 133);
    private static final int BORDER = Color.rgb(164, 139, 105);

    private static final int ICON_CHEM = 1;
    private static final int ICON_FILM = 2;
    private static final int ICON_TRAY = 3;
    private static final int ICON_TIMER = 4;
    private static final int ICON_WRENCH = 5;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        buildUi();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(22), dp(30), dp(22), dp(22));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView title = label("CAMERA OSCURA", 35, IVORY, true, true);
        title.setGravity(Gravity.CENTER);
        title.setLetterSpacing(0.045f);
        root.addView(title, lp(-1, -2));

        TextView sub = label("di Federico e Francesco", 16, IVORY, false, true);
        sub.setGravity(Gravity.CENTER);
        sub.setLetterSpacing(0.05f);
        root.addView(sub, margin(lp(-1, -2), 0, 3, 0, 10));

        View rule = new View(this);
        rule.setBackgroundColor(Color.rgb(91, 76, 59));
        LinearLayout.LayoutParams ruleLp = lp(dp(230), dp(1));
        ruleLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(rule, margin(ruleLp, 0, 0, 0, 22));

        HomeCard products = new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, false);
        products.setOnClickListener(v -> openAssistant("products"));
        root.addView(products, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard film = new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false);
        film.setOnClickListener(v -> openAssistant("film"));
        root.addView(film, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard paper = new HomeCard("BAGNI STAMPA", ICON_TRAY, false);
        paper.setOnClickListener(v -> openAssistant("paper"));
        root.addView(paper, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard timer = new HomeCard("TIMER STAMPA", ICON_TIMER, false);
        timer.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        root.addView(timer, margin(lp(-1, dp(88)), 0, 0, 0, 18));

        HomeCard maintenance = new HomeCard("USO E MANUTENZIONE", ICON_WRENCH, true);
        maintenance.setOnClickListener(v -> startActivity(new Intent(this, UseMaintenanceActivity.class)));
        LinearLayout.LayoutParams mLp = lp(dp(294), dp(62));
        mLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(maintenance, margin(mLp, 0, 0, 0, 26));

        TextView motto = label("LA PAZIENZA È PARTE DEL PROCESSO", 11, IVORY, true, true);
        motto.setGravity(Gravity.CENTER);
        motto.setLetterSpacing(0.12f);
        root.addView(motto, margin(lp(-1, -2), 0, 4, 0, 14));

        TextView version = label(readInstalledVersion(), 11, Color.rgb(104, 100, 96), false, true);
        version.setGravity(Gravity.CENTER);
        version.setLetterSpacing(0.06f);
        root.addView(version, margin(lp(-1, dp(30)), 0, 0, 0, 8));

        setContentView(scroll);
    }

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }

    private String readInstalledVersion() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return "v" + info.versionName;
        } catch (Exception ignored) { return "v—"; }
    }

    private TextView label(String value, float sp, int color, boolean bold, boolean serif) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setTypeface(Typeface.create(serif ? Typeface.SERIF : Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL));
        v.setIncludeFontPadding(false);
        return v;
    }

    private GradientDrawable cardBg(boolean secondary) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(secondary ? Color.rgb(15, 16, 17) : CARD);
        g.setCornerRadius(dp(13));
        g.setStroke(dp(1), BORDER);
        return g;
    }

    private final class HomeCard extends LinearLayout {
        HomeCard(String text, int icon, boolean secondary) {
            super(HomeActivity.this);
            setOrientation(HORIZONTAL);
            setGravity(Gravity.CENTER_VERTICAL);
            setPadding(dp(14), dp(8), dp(12), dp(8));
            setBackground(cardBg(secondary));
            setClickable(true);
            setFocusable(true);

            LineIcon iconView = new LineIcon(HomeActivity.this, icon);
            addView(iconView, new LinearLayout.LayoutParams(dp(secondary ? 42 : 54), dp(secondary ? 42 : 54)));

            TextView name = label(text, secondary ? 15 : 20, IVORY, true, true);
            name.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
            name.setSingleLine(true);
            LinearLayout.LayoutParams nameLp = new LinearLayout.LayoutParams(0, -1, 1f);
            nameLp.setMargins(dp(13), 0, dp(8), 0);
            addView(name, nameLp);

            TextView arrow = label("›", secondary ? 27 : 32, IVORY, false, true);
            arrow.setGravity(Gravity.CENTER);
            addView(arrow, new LinearLayout.LayoutParams(dp(26), -1));
        }
    }

    private static final class LineIcon extends View {
        private final int kind;
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path path = new Path();
        LineIcon(android.content.Context c, int kind) { super(c); this.kind=kind; p.setStyle(Paint.Style.STROKE); p.setStrokeCap(Paint.Cap.ROUND); p.setStrokeJoin(Paint.Join.ROUND); }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            float w=getWidth(), h=getHeight(), cx=w/2f, cy=h/2f, s=Math.min(w,h);
            p.setColor(IVORY); p.setStrokeWidth(Math.max(1.6f,s*.035f)); p.setStyle(Paint.Style.STROKE);
            c.drawCircle(cx,cy,s*.44f,p);
            path.reset();
            if(kind==ICON_CHEM){
                path.moveTo(cx-s*.10f,cy-s*.23f);path.lineTo(cx+s*.10f,cy-s*.23f);path.moveTo(cx-s*.05f,cy-s*.23f);path.lineTo(cx-s*.05f,cy-s*.05f);path.lineTo(cx-s*.18f,cy+s*.22f);path.quadTo(cx,cy+s*.31f,cx+s*.18f,cy+s*.22f);path.lineTo(cx+s*.05f,cy-s*.05f);path.lineTo(cx+s*.05f,cy-s*.23f);c.drawPath(path,p);c.drawLine(cx-s*.12f,cy+s*.13f,cx+s*.12f,cy+s*.13f,p);
            } else if(kind==ICON_FILM){
                RectF r=new RectF(cx-s*.16f,cy-s*.27f,cx+s*.16f,cy+s*.27f);c.drawRect(r,p);c.drawLine(cx-s*.08f,cy-s*.13f,cx+s*.08f,cy-s*.13f,p);c.drawLine(cx-s*.08f,cy+s*.02f,cx+s*.08f,cy+s*.02f,p);c.drawLine(cx-s*.08f,cy+s*.17f,cx+s*.08f,cy+s*.17f,p);for(int i=-2;i<=2;i++){float y=cy+i*s*.105f;c.drawCircle(cx-s*.13f,y,s*.012f,p);c.drawCircle(cx+s*.13f,y,s*.012f,p);}
            } else if(kind==ICON_TRAY){
                path.moveTo(cx-s*.25f,cy-s*.09f);path.lineTo(cx+s*.25f,cy-s*.09f);path.lineTo(cx+s*.18f,cy+s*.18f);path.lineTo(cx-s*.18f,cy+s*.18f);path.close();c.drawPath(path,p);c.drawLine(cx-s*.19f,cy+s*.02f,cx+s*.19f,cy+s*.02f,p);
            } else if(kind==ICON_TIMER){
                c.drawCircle(cx,cy+s*.04f,s*.24f,p);c.drawLine(cx,cy-s*.20f,cx,cy-s*.30f,p);c.drawLine(cx-s*.07f,cy-s*.30f,cx+s*.07f,cy-s*.30f,p);c.drawLine(cx,cy+s*.04f,cx+s*.10f,cy-s*.07f,p);c.drawLine(cx+s*.17f,cy-s*.17f,cx+s*.23f,cy-s*.23f,p);
            } else {
                path.moveTo(cx-s*.23f,cy+s*.20f);path.lineTo(cx-s*.03f,cy);path.cubicTo(cx-s*.10f,cy-s*.19f,cx+s*.05f,cy-s*.30f,cx+s*.20f,cy-s*.23f);path.lineTo(cx+s*.08f,cy-s*.11f);path.lineTo(cx+s*.17f,cy-s*.02f);path.lineTo(cx+s*.28f,cy-s*.14f);path.cubicTo(cx+s*.33f,cy+s*.03f,cx+s*.20f,cy+s*.16f,cx+s*.04f,cy+s*.08f);path.lineTo(cx-s*.16f,cy+s*.27f);c.drawPath(path,p);
            }
        }
    }

    private LinearLayout.LayoutParams lp(int w,int h){return new LinearLayout.LayoutParams(w,h);}
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(float v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
'''
wr(home, home_source)

# Remove all previous Home artwork resources: no bitmap dependency in final Home.
if (res/'drawable-nodpi').exists():
    for p in (res/'drawable-nodpi').iterdir():
        if p.is_file() and p.name.lower().startswith('home_vintage.'):
            p.unlink()
for d in [res/'drawable', res/'mipmap', res/'mipmap-hdpi', res/'mipmap-mdpi', res/'mipmap-xhdpi', res/'mipmap-xxhdpi', res/'mipmap-xxxhdpi']:
    if d.exists():
        for p in d.iterdir():
            if p.is_file() and p.name.lower().startswith('home_vintage.'):
                p.unlink()

# -----------------------------------------------------------------------------
# App icon — native vector based on approved whole-darkroom proposal.
# Chemistry + enlarger + film + tray/print, not timer-centric.
# -----------------------------------------------------------------------------
for d in [res/'drawable', res/'drawable-nodpi', res/'mipmap', res/'mipmap-hdpi', res/'mipmap-mdpi', res/'mipmap-xhdpi', res/'mipmap-xxhdpi', res/'mipmap-xxxhdpi']:
    if d.exists():
        for p in list(d.iterdir()):
            if p.is_file() and p.stem == 'ic_launcher':
                p.unlink()
(res/'drawable').mkdir(parents=True, exist_ok=True)
icon_xml = '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#08090A" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="2.2"
        android:pathData="M54,7 A47,47 0,1 1,54,101 A47,47 0,1 1,54,7"/>
    <path android:fillColor="#00000000" android:strokeColor="#B99A74" android:strokeWidth="0.8"
        android:pathData="M54,10 A44,44 0,1 1,54,98 A44,44 0,1 1,54,10"/>
    <!-- central enlarger -->
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="2.0" android:strokeLineJoin="round"
        android:pathData="M47,18h14v5h-14z M45,24h18v4h-18z M46,29h16v4h-16z M43,34h22v21h-22z M50,55h8v9h-8z"/>
    <path android:fillColor="#7E231E" android:strokeColor="#E8CAA0" android:strokeWidth="1.4"
        android:pathData="M54,40 A6,6 0,1 1,54,52 A6,6 0,1 1,54,40"/>
    <!-- chemistry bottle left -->
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="1.8" android:strokeLineJoin="round"
        android:pathData="M23,45h7v4l4,6v17h-15v-17l4,-6z M20,65h13"/>
    <path android:fillColor="#7E231E" android:pathData="M21,66h11v4h-11z"/>
    <!-- film canister / strip right -->
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="1.8" android:strokeLineJoin="round"
        android:pathData="M75,47h10v24h-10z M85,51h6v18h-6z M87,54h2 M87,58h2 M87,62h2 M87,66h2"/>
    <path android:fillColor="#7E231E" android:pathData="M86,52h4v16h-4z"/>
    <!-- developing tray -->
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="2.0" android:strokeLineJoin="round"
        android:pathData="M33,68h42l-4,12h-34z M38,73h32"/>
    <path android:fillColor="#6E1F1B" android:pathData="M38,74h32l-1.3,4h-29.4z"/>
    <!-- print -->
    <path android:fillColor="#00000000" android:strokeColor="#E8CAA0" android:strokeWidth="1.6"
        android:pathData="M40,84h28v10h-28z M43,91l5,-4l4,3l5,-5l7,6"/>
    <path android:fillColor="#8B2B24" android:pathData="M61,86 A2,2 0,1 1,61,90 A2,2 0,1 1,61,86"/>
    <!-- darkroom red accents -->
    <path android:fillColor="#8B2B24" android:strokeColor="#E8CAA0" android:strokeWidth="1.0"
        android:pathData="M18,30 C15,35 15,39 18,41 C21,39 21,35 18,30z"/>
    <path android:fillColor="#8B2B24" android:strokeColor="#E8CAA0" android:strokeWidth="1.0"
        android:pathData="M89,32v9 M86,38h6 M89,41 A2,2 0,1 1,89,45 A2,2 0,1 1,89,41"/>
</vector>
'''
(res/'drawable/ic_launcher.xml').write_text(icon_xml, encoding='utf-8')

# -----------------------------------------------------------------------------
# 1,2,4,7 — Timer chrome: uniform Home target, TIMER title, compact hardware,
# no internal version footer.
# -----------------------------------------------------------------------------
rep(main, 'private static final String APP_VERSION = "0.13.10";',
          'private static final String APP_VERSION = "0.13.11";', 'Timer internal visual version')

rep(main,
'''        topBar.addView(homeButton, lp(dp(48), dp(48)));\n        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);\n        title.setGravity(Gravity.CENTER);\n        topBar.addView(title, lp(0, dp(48), 1f));\n        View navSpacer = new View(this);\n        topBar.addView(navSpacer, lp(dp(48), dp(48)));\n        root.addView(topBar, lp(-1, dp(48)));''',
'''        topBar.addView(homeButton, lp(dp(46), dp(46)));\n        TextView title = text("TIMER", 27, TEXT_PRIMARY, true);\n        title.setGravity(Gravity.CENTER);\n        topBar.addView(title, lp(0, dp(46), 1f));\n        View navSpacer = new View(this);\n        topBar.addView(navSpacer, lp(dp(46), dp(46)));\n        root.addView(topBar, lp(-1, dp(46)));''','Timer Home size/title')

rep(main,
'''        LinearLayout deviceCard = card();\n        LinearLayout deviceTop = new LinearLayout(this);''',
'''        LinearLayout deviceCard = card();\n        deviceCard.setPadding(dp(14), dp(9), dp(14), dp(9));\n        LinearLayout deviceTop = new LinearLayout(this);''','compact enlarger card padding')
rep(main,
'''        deviceTop.addView(selectDeviceButton, lp(dp(56), dp(40)));''',
'''        deviceTop.addView(selectDeviceButton, lp(dp(48), dp(36)));''','compact settings gear')
rep(main,
'''        deviceStatus.setPadding(0, dp(8), 0, 0);''',
'''        deviceStatus.setPadding(0, dp(4), 0, 0);''','compact device status spacing')
rep(main,
'''        safelightStatus.setPadding(0, dp(4), 0, 0);''',
'''        safelightStatus.setPadding(0, dp(2), 0, 0);''','compact safelight spacing')
rep(main,
'''        root.addView(deviceCard, margin(lp(-1, -2), 0, 4, 0, 14));''',
'''        root.addView(deviceCard, margin(lp(-1, -2), 0, 4, 0, 10));''','compact enlarger outer spacing')

footer_block='''        TextView footer = text("Darkroom Timer di F.G. - v" + APP_VERSION, 12, darkroomMode ? Color.rgb(92, 18, 18) : Color.rgb(105, 112, 118), false);\n        footer.setGravity(Gravity.CENTER);\n        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 6));\n\n'''
rep(main, footer_block, '', 'remove internal Timer footer')

# Assistant already uses the medium 46dp top target; guard it explicitly.
asrc=rd(assistant)
for marker in ['label("⌂", 25, WHITE, true)', 'new LinearLayout.LayoutParams(dp(46), dp(46))']:
    if marker not in asrc: raise SystemExit('v0.2.8 Assistant medium Home standard missing: '+marker)

# Maintenance: same 46dp box, enlarge glyph itself to the same visual size.
rep(maintenance,
'''        TextView back=actionText(backStack.isEmpty()?"⌂":"←");\n        back.setGravity(Gravity.CENTER);''',
'''        TextView back=actionText(backStack.isEmpty()?"⌂":"←");\n        back.setTextSize(25);\n        back.setPadding(0,0,0,0);\n        back.setGravity(Gravity.CENTER);''','Maintenance Home glyph medium size')

# -----------------------------------------------------------------------------
# 3. SETTINGS — one scrollable dialog, grouped by logical sector.
# -----------------------------------------------------------------------------
settings_helpers = r'''    private LinearLayout settingsGroup(String heading) {
        LinearLayout g = card();
        g.setPadding(dp(12), dp(10), dp(12), dp(12));
        TextView h = text(heading, 11, MUTED, true);
        h.setPadding(dp(4), 0, dp(4), dp(8));
        g.addView(h, lp(-1,-2));
        return g;
    }

'''
settings_method = r'''    private void showSettingsDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView settingsScroll = new ScrollView(this);
        settingsScroll.setFillViewport(true);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        settingsScroll.addView(panel, new ScrollView.LayoutParams(-1,-2));

        panel.addView(text("IMPOSTAZIONI", 20, TEXT_PRIMARY, true), margin(lp(-1,-2),0,0,0,12));

        LinearLayout timingGroup = settingsGroup("TEMPORIZZAZIONE");
        Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);
        timing.setOnClickListener(v -> {
            timingMethod = TimingMath.isFStop(timingMethod) ? TimingMath.METHOD_SECONDS : TimingMath.METHOD_FSTOP;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("timingMethod", timingMethod).apply();
            timing.setText("METODO DI TEMPORIZZAZIONE: " + timingMethod);
            updateTimingUi();
        });
        timingGroup.addView(timing, lp(-1,dp(50)));
        panel.addView(timingGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout darkroomGroup = settingsGroup("CAMERA OSCURA E LUCE ROSSA");
        Button safelightToggle = compactButton("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
        safelightToggle.setOnClickListener(v -> {
            if (!safelightAuto) {
                DeviceConfig safe = SafelightConfig.load(this);
                if (!safe.isValid()) { Toast.makeText(this, "Prima seleziona il SONOFF della luce rossa", Toast.LENGTH_LONG).show(); return; }
                if (safe.deviceId.equals(selectedDeviceId)) { Toast.makeText(this, "Ingranditore e luce rossa devono usare due SONOFF diversi", Toast.LENGTH_LONG).show(); return; }
                safelightAuto = true;
            } else safelightAuto = false;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("safelightAuto", safelightAuto).apply();
            safelightToggle.setText("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
            updateSafelightStatus();
            if (safelightAuto) ensureSafelightIdleOn(); else stopSafelightInterlock();
        });
        darkroomGroup.addView(safelightToggle, lp(-1,dp(50)));

        DeviceConfig safeCfg = SafelightConfig.load(this);
        String safeInfo = safeCfg.isValid()
                ? "SONOFF SAFELIGHT  •  ID " + safeCfg.deviceId + "\nStato manuale rispettato • OFF durante l’ingranditore"
                : "SONOFF SAFELIGHT  •  non configurato";
        TextView safeDetails = text(safeInfo, 12, MUTED, false);
        safeDetails.setPadding(dp(4), dp(7), dp(4), dp(5));
        darkroomGroup.addView(safeDetails, lp(-1,-2));
        Button safePick = compactButton(safeCfg.isValid() ? "CAMBIA SONOFF SAFELIGHT" : "SCEGLI SONOFF SAFELIGHT");
        safePick.setOnClickListener(v -> { dialog.dismiss(); showSafelightPicker(); });
        darkroomGroup.addView(safePick, margin(lp(-1,dp(48)),0,0,0,8));

        Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));
        dark.setOnClickListener(v -> setDarkroomModeFromSettings(!darkroomMode, dialog));
        darkroomGroup.addView(dark, margin(lp(-1,dp(50)),0,0,0,7));

        Button protection = compactButton("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
        protection.setOnClickListener(v -> {
            darkroomProtection = !darkroomProtection;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomProtection", darkroomProtection).apply();
            protection.setText("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
            syncDarkroomProtection();
        });
        darkroomGroup.addView(protection, margin(lp(-1,dp(50)),0,0,0,6));

        if (darkroomProtection && !hasDndAccess()) {
            Button authorizeDnd = compactButton("AUTORIZZA NON DISTURBARE");
            authorizeDnd.setTextColor(AMBER);
            authorizeDnd.setOnClickListener(v -> { dialog.dismiss(); openDndAccessSettings(); });
            darkroomGroup.addView(authorizeDnd, margin(lp(-1,dp(46)),0,0,0,5));
        }
        TextView protectionNote = text("Non disturbare blocca chiamate/notifiche e sopprime gli avvisi visivi durante la modalità camera oscura; tornando alla modalità normale vengono ripristinate le impostazioni precedenti.", 11, MUTED, false);
        protectionNote.setPadding(dp(4), dp(2), dp(4), 0);
        darkroomGroup.addView(protectionNote, lp(-1,-2));
        panel.addView(darkroomGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout feedbackGroup = settingsGroup("FEEDBACK DURANTE IL LAVORO");
        Button beep = compactButton("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));
        beep.setOnClickListener(v -> { feedbackBeep=!feedbackBeep; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("feedbackBeep",feedbackBeep).apply(); beep.setText("BEEP FINE CICLO: "+(feedbackBeep?"ON":"OFF")); });
        feedbackGroup.addView(beep, lp(-1,dp(50)));
        Button voice = compactButton("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));
        voice.setOnClickListener(v -> { voiceGuide=!voiceGuide; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("voiceGuide",voiceGuide).apply(); voice.setText("GUIDA VOCALE PIANO: "+(voiceGuide?"ON":"OFF")); });
        feedbackGroup.addView(voice, margin(lp(-1,dp(50)),0,7,0,0));
        panel.addView(feedbackGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout diagnosticsGroup = settingsGroup("DIAGNOSTICA");
        Button diagnostics = compactButton("CRONOLOGIA TECNICA");
        diagnostics.setOnClickListener(v -> showTechnicalLogDialog());
        diagnosticsGroup.addView(diagnostics, lp(-1,dp(50)));
        panel.addView(diagnosticsGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout hardwareGroup = settingsGroup("HARDWARE INGRANDITORE");
        DeviceConfig saved = DeviceConfig.load(this);
        String tech = "SONOFF INGRANDITORE\n";
        if (selectedDeviceId == null || selectedDeviceId.isEmpty()) tech += "Nessun dispositivo selezionato";
        else tech += (device != null && device.isValid() ? "DIY verificata" : "non verificato")
                + "\nDevice ID: " + selectedDeviceId
                + (saved.host == null || saved.host.isEmpty() ? "" : "\nIP: " + saved.host + ":" + saved.port);
        TextView details = text(tech, 13, MUTED, false);
        details.setPadding(dp(4), dp(2), dp(4), dp(8));
        hardwareGroup.addView(details, lp(-1,-2));
        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");
        change.setOnClickListener(v -> { dialog.dismiss(); showDevicePicker(); });
        hardwareGroup.addView(change, lp(-1,dp(50)));
        panel.addView(hardwareGroup, margin(lp(-1,-2),0,0,0,10));

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, lp(-1,dp(50)));

        dialog.setContentView(settingsScroll);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.90f));
    }

'''
replace_between(main, '    private void showSettingsDialog() {', '    private static int snap(int ms, int min, int max) {',
                settings_helpers + settings_method, 'grouped settings')

# -----------------------------------------------------------------------------
# 5. Print plan command and compact summary.
# -----------------------------------------------------------------------------
summary_method = r'''    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        printSequenceButton.setText("PIANO DI STAMPA");

        boolean noLocalPlan = printSequence.isEmpty();
        boolean noRecipeCorrections = exposureRecipe == null || (exposureRecipe.densityQuarterSteps == 0 && exposureRecipe.globalQuarterStops == 0);
        if (noLocalPlan && noRecipeCorrections) {
            boolean hasBase = (exposureRecipe != null && exposureRecipe.hasBase()) || printWidthMs > 0;
            if (!hasBase) { printSequenceSummary.setText(""); printSequenceSummary.setVisibility(View.GONE); return; }
            StringBuilder one = new StringBuilder("STAMPA BASE · ").append(formatTime(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                String f=exposureRecipe.filterLabel();
                if (!"NESSUNO".equals(f)) one.append(" · ").append(f);
                one.append(" · ").append(exposureRecipe.densityLabel());
            }
            printSequenceSummary.setText(one.toString());
            printSequenceSummary.setVisibility(View.VISIBLE);
            return;
        }

        String base = recipeBaseSummary();
        boolean hasRecipe = !base.isEmpty() || !printSequence.isEmpty()
                || (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0);
        if (!hasRecipe) { printSequenceSummary.setText(""); printSequenceSummary.setVisibility(View.GONE); return; }

        StringBuilder s = new StringBuilder();
        if (!base.isEmpty()) s.append(base);
        if (s.length() > 0) s.append("\n\n");
        s.append("ESPOSIZIONE\n");
        if (printSequence.hasSplit()) s.append(printSequence.split.softLine()).append('\n').append(printSequence.split.hardLine());
        else {
            s.append("SINGOLA · ").append(formatTime(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                String f=exposureRecipe.filterLabel();
                if (!"NESSUNO".equals(f)) s.append(" · ").append(f);
                s.append(" · ").append(exposureRecipe.densityLabel());
            }
        }
        if (!printSequence.corrections.isEmpty()) {
            s.append("\n\nCORREZIONI");
            for (PrintCorrection c : printSequence.corrections) {
                if (c == null) continue;
                s.append('\n').append(c.displayLine(printSequence.baseMsFor(c, printWidthMs), printSequence.hasSplit()));
            }
        }
        if (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0)
            s.append("\n\nCORREZIONE GLOBALE · ").append(exposureRecipe.globalLabel());
        printSequenceSummary.setText(s.toString());
        printSequenceSummary.setVisibility(View.VISIBLE);
    }

'''
replace_between(main, '    private void updatePrintSequenceUi() {', '    private void persistPrintSequence() {',
                summary_method, 'deduplicated print summary')

rep(main,
'''                Button clear=compactButton("AZZERA PIANO"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("AZZERARE IL PIANO DI STAMPA?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La base originale resta disponibile.","AZZERA",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA"));''',
'''                Button clear=compactButton("RIMUOVI CORREZIONI"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("RIMUOVERE LE CORREZIONI?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La stampa base trovata con il provino resta disponibile.","RIMUOVI",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA"));''','rename remove corrections')

# -----------------------------------------------------------------------------
# 6. Enlargement navigation: setup finishes with CHIUDI after successful save;
# resize keeps INDIETRO at the top.
# -----------------------------------------------------------------------------
rep(enlargement,
'''    void begin(String title,String subtitle){ScrollView sc=new ScrollView(this);sc.setFillViewport(true);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(14),dp(18),dp(30));root.setBackgroundColor(BG);sc.addView(root,new ScrollView.LayoutParams(-1,-2));Button back=button("←  INDIETRO",BUTTON);back.setOnClickListener(v->finish());root.addView(back,lp(-1,dp(46)));TextView h=label(title,24,TEXT,true);h.setGravity(Gravity.CENTER);root.addView(h,margin(lp(-1,-2),0,dp(10),0,dp(3)));TextView sub=label(subtitle,12,MUTED,false);sub.setGravity(Gravity.CENTER);root.addView(sub,margin(lp(-1,-2),0,0,0,dp(16)));setContentView(sc);}''',
'''    void begin(String title,String subtitle){ScrollView sc=new ScrollView(this);sc.setFillViewport(true);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(14),dp(18),dp(30));root.setBackgroundColor(BG);sc.addView(root,new ScrollView.LayoutParams(-1,-2));if("resize".equals(mode)){Button back=button("←  INDIETRO",BUTTON);back.setOnClickListener(v->finish());root.addView(back,lp(-1,dp(46)));}TextView h=label(title,24,TEXT,true);h.setGravity(Gravity.CENTER);root.addView(h,margin(lp(-1,-2),0,dp(10),0,dp(3)));TextView sub=label(subtitle,12,MUTED,false);sub.setGravity(Gravity.CENTER);root.addView(sub,margin(lp(-1,-2),0,0,0,dp(16)));setContentView(sc);}''','conditional enlargement back button')
rep(enlargement,
'''            TextView ok=label("Registrato nella ricetta corrente.",13,GREEN,true);ok.setGravity(Gravity.CENTER);resultBox.addView(ok,margin(lp(-1,-2),0,dp(8),0,0));''',
'''            TextView ok=label("Registrato nella ricetta corrente.",13,GREEN,true);ok.setGravity(Gravity.CENTER);resultBox.addView(ok,margin(lp(-1,-2),0,dp(8),0,0));Button close=button("CHIUDI",BUTTON);close.setOnClickListener(v->finish());resultBox.addView(close,margin(lp(-1,dp(50)),0,dp(12),0,dp(4)));''','setup close after saved result')

# -----------------------------------------------------------------------------
# Static guards.
# -----------------------------------------------------------------------------
hs=rd(home); ms=rd(main); mas=rd(maintenance); ens=rd(enlargement)
for x in ['CAMERA OSCURA','di Federico e Francesco','PRODOTTI CHIMICI','SVILUPPO PELLICOLA','BAGNI STAMPA','TIMER STAMPA','USO E MANUTENZIONE','LA PAZIENZA È PARTE DEL PROCESSO','LineIcon','getPackageInfo(getPackageName(), 0)']:
    if x not in hs: raise SystemExit('v0.2.8 Home guard missing: '+x)
for forbidden in ['ImageView','home_vintage','HOME PROVVISORIA']:
    if forbidden in hs: raise SystemExit('v0.2.8 Home forbidden remains: '+forbidden)
for x in ['text("TIMER", 27','TEMPORIZZAZIONE','CAMERA OSCURA E LUCE ROSSA','FEEDBACK DURANTE IL LAVORO','DIAGNOSTICA','HARDWARE INGRANDITORE','RIMUOVI CORREZIONI','STAMPA BASE · ','private static final String APP_VERSION = "0.13.11";']:
    if x not in ms: raise SystemExit('v0.2.8 Main guard missing: '+x)
if 'Darkroom Timer di F.G. - v' in ms: raise SystemExit('v0.2.8 Timer footer still present')
if 'AZZERA PIANO' in ms: raise SystemExit('v0.2.8 old reset label still present')
if 'back.setTextSize(25);' not in mas: raise SystemExit('v0.2.8 Maintenance Home size not normalized')
for x in ['if("resize".equals(mode)){Button back=button("←  INDIETRO"','Button close=button("CHIUDI",BUTTON)','Registrato nella ricetta corrente.']:
    if x not in ens: raise SystemExit('v0.2.8 Enlargement guard missing: '+x)
if not (res/'drawable/ic_launcher.xml').exists(): raise SystemExit('v0.2.8 launcher vector missing')
if 'android:icon="@drawable/ic_launcher"' not in rd(manifest): raise SystemExit('v0.2.8 manifest launcher reference changed unexpectedly')
print('Darkroom v0.2.8 GRAPHIC REFRESH TRANSFORM OK', flush=True)
