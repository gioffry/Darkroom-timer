#!/usr/bin/env python3
from pathlib import Path
import subprocess
import base64

root = Path('combined')
home = root / 'src/main/java/it/darkroom/timer/home/HomeActivity.java'
maintenance = root / 'src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java'
main = root / 'src/main/java/it/darkroom/timer/MainActivity.java'
enlargement = root / 'src/main/java/it/darkroom/timer/EnlargementActivity.java'
drawable = root / 'src/main/res/drawable-nodpi'

for p in (home, maintenance, main, enlargement):
    if not p.exists():
        raise SystemExit('v0.2.1: generated source missing: ' + str(p))

# -----------------------------------------------------------------------------
# HOME — rebuild the approved mockup as an Android-decodable JPEG.
# -----------------------------------------------------------------------------
drawable.mkdir(parents=True, exist_ok=True)
source_webp = drawable / 'home_vintage.webp'
target_jpg = drawable / 'home_vintage.jpg'

# Use the exact source path that already produced the visible v0.1.9 Home:
# validated HD artwork plus the clean lower patch.
hd = root / 'v014_assets/home_hd'
parts = sorted(hd.glob('*.part'))
if len(parts) != 8:
    raise SystemExit(f'v0.2.1: expected 8 HD Home parts, found {len(parts)}')
encoded = ''.join(''.join(part.read_text(encoding='utf-8').split()) for part in parts)
raw_source = base64.b64decode(encoded + '=' * (-len(encoded) % 4), validate=True)
if len(raw_source) < 80_000 or raw_source[:4] != b'RIFF' or raw_source[8:12] != b'WEBP':
    raise SystemExit('v0.2.1: validated HD Home source is invalid')
source = Path('/tmp/home_v021_hd_source.webp')
source.write_bytes(raw_source)
bottom = root / 'v015_assets/home_bottom.jpg'
if not bottom.exists() or bottom.read_bytes()[:2] != b'\xff\xd8':
    raise SystemExit('v0.2.1: clean Home bottom patch missing')

for old in (drawable / 'home_vintage.png', target_jpg):
    if old.exists():
        old.unlink()
subprocess.run([
    'ffmpeg', '-y', '-v', 'warning', '-err_detect', 'ignore_err',
    '-i', str(source), '-i', str(bottom),
    '-filter_complex', '[0:v]scale=864:-2,pad=864:1536:0:0:black[base];[base][1:v]overlay=0:1320:format=auto',
    '-frames:v', '1', '-pix_fmt', 'yuvj420p', '-q:v', '2', str(target_jpg),
], check=True)
raw = target_jpg.read_bytes()
if len(raw) < 150_000 or raw[:2] != b'\xff\xd8' or raw[-2:] != b'\xff\xd9':
    raise SystemExit('v0.2.1: generated Home JPEG is invalid')
if source_webp.exists():
    source_webp.unlink()

home_source = r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;

import it.darkroom.timer.MainActivity;
import it.darkroom.timer.R;
import it.darkroom.assistant.AssistantActivityV2;
import it.darkroom.timer.maintenance.UseMaintenanceActivity;

/** Exact approved CAMERA OSCURA Home: artwork + transparent functional hotspots. */
public final class HomeActivity extends Activity {
    private static final float ART_W = 864f;
    private static final float ART_H = 1536f;

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
        artwork.setContentDescription("CAMERA OSCURA");
        frame.addView(artwork, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        View products = hotspot("PRODOTTI CHIMICI");
        View film = hotspot("SVILUPPO PELLICOLA");
        View paper = hotspot("BAGNI STAMPA");
        View timer = hotspot("TIMER STAMPA");
        View maintenance = hotspot("USO E MANUTENZIONE");
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

        View[] controls = new View[]{products, film, paper, timer, maintenance};
        frame.addOnLayoutChangeListener((v, left, top, right, bottom,
                                         oldLeft, oldTop, oldRight, oldBottom) ->
                placeHomeControls(frame, controls, version));

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

    private TextView versionLabel() {
        TextView v = new TextView(this);
        v.setText(readInstalledVersion());
        v.setTextColor(Color.argb(190, 220, 214, 205));
        v.setTextSize(10f);
        v.setGravity(Gravity.CENTER);
        v.setLetterSpacing(0.08f);
        v.setBackgroundColor(Color.TRANSPARENT);
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

    private void placeHomeControls(FrameLayout frame, View[] v, View version) {
        int w = frame.getWidth();
        int h = frame.getHeight();
        if (w <= 0 || h <= 0 || v.length != 5) return;

        float scale = Math.min(w / ART_W, h / ART_H);
        float dx = (w - ART_W * scale) * 0.5f;
        float dy = (h - ART_H * scale) * 0.5f;

        place(v[0], dx, dy, scale, 128f, 522f, 732f, 681f);
        place(v[1], dx, dy, scale, 128f, 691f, 732f, 852f);
        place(v[2], dx, dy, scale, 128f, 858f, 732f, 1022f);
        place(v[3], dx, dy, scale, 128f, 1028f, 732f, 1190f);
        place(v[4], dx, dy, scale, 244f, 1194f, 612f, 1266f);
        place(version, dx, dy, scale, 330f, 1480f, 534f, 1520f);
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

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }
}
'''
home.write_text(home_source, encoding='utf-8')

# -----------------------------------------------------------------------------
# USO E MANUTENZIONE — same default sans-serif family as Timer.
# -----------------------------------------------------------------------------
m = maintenance.read_text(encoding='utf-8')
old_font = 'v.setTypeface(Typeface.create("sans-serif-condensed",bold?Typeface.BOLD:Typeface.NORMAL));'
new_font = 'v.setTypeface(Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL);'
if old_font not in m:
    raise SystemExit('v0.2.1: maintenance legacy font marker missing')
m = m.replace(old_font, new_font, 1)
maintenance.write_text(m, encoding='utf-8')

# -----------------------------------------------------------------------------
# LOG — explicit paper size and column height in visible fields, while keeping
# the complete per-print enlargementMeta snapshot.
# -----------------------------------------------------------------------------
s = main.read_text(encoding='utf-8')
snapshot = '''        e.enlargementMeta = (printAt > 0 && enlargementArmAt > 0 && enlargementArmAt <= printAt)
                ? p.getString("pendingEnlargementMeta", "") : "";'''
if snapshot not in s:
    raise SystemExit('v0.2.1: per-print enlargement snapshot marker missing')
s = s.replace(snapshot, snapshot + '\n        applyEnlargementSnapshotToVisibleLogFields(e);', 1)

summary_marker = '    private String enlargementLogSummary(String meta) {'
if summary_marker not in s:
    raise SystemExit('v0.2.1: enlargementLogSummary marker missing')
helper = r'''    private static boolean applyEnlargementSnapshotToVisibleLogFields(LogEntry entry) {
        if (entry == null || entry.enlargementMeta == null || entry.enlargementMeta.trim().isEmpty()) return false;
        boolean changed = false;
        String col = enlargementMetaValue(entry.enlargementMeta, "col");
        if (!col.isEmpty()) {
            try {
                String value = String.format(Locale.ITALY, "%.1f", Double.parseDouble(col));
                if (entry.columnHeight == null || !value.equals(entry.columnHeight.trim())) {
                    entry.columnHeight = value;
                    changed = true;
                }
            } catch (Exception ignored) {}
        }
        String paper = enlargementMetaValue(entry.enlargementMeta, "paper");
        if (!paper.isEmpty()) {
            String format = paper.replace('.', ',').replace("x", " × ") + " cm";
            String current = entry.paper == null ? "" : entry.paper.trim();
            if (current.isEmpty()) {
                entry.paper = format;
                changed = true;
            } else if (!current.contains(format) && !current.contains(paper)) {
                entry.paper = current + " · " + format;
                changed = true;
            }
        }
        return changed;
    }

'''
s = s.replace(summary_marker, helper + summary_marker, 1)

editor_marker = '    private void showLogEditor(final LogEntry entry, final boolean isNew) {'
if editor_marker not in s:
    raise SystemExit('v0.2.1: showLogEditor marker missing')
s = s.replace(editor_marker, editor_marker + '\n        if (applyEnlargementSnapshotToVisibleLogFields(entry) && !isNew) LogStore.save(this, entry);', 1)

old_summary = '        if (!paper.isEmpty()) b.append(paper).append(" cm · orizzontale");'
new_summary = '        if (!paper.isEmpty()) b.append("formato carta ").append(paper).append(" cm · orizzontale");'
if old_summary not in s:
    raise SystemExit('v0.2.1: paper summary marker missing')
s = s.replace(old_summary, new_summary, 1)

old_line = '                "\\nIngrandimento: " + enlargementLogSummary(entry.enlargementMeta) +'
new_line = '                "\\nFormato e ingrandimento: " + enlargementLogSummary(entry.enlargementMeta) +'
if old_line not in s:
    raise SystemExit('v0.2.1: LOG automatic enlargement line missing')
s = s.replace(old_line, new_line, 1)
main.write_text(s, encoding='utf-8')

# Legacy backfill and derived prints also synchronize the visible fields.
e = enlargement.read_text(encoding='utf-8')
legacy_old = '''            originEntry.enlargementMeta=meta;
            if(originEntry.columnHeight==null||originEntry.columnHeight.trim().isEmpty())originEntry.columnHeight=fmt(c.col);'''
legacy_new = '''            originEntry.enlargementMeta=meta;
            syncLogDisplayFields(originEntry,meta);'''
if legacy_old not in e:
    raise SystemExit('v0.2.1: legacy display-field marker missing')
e = e.replace(legacy_old, legacy_new, 1)

derived_old = 'd.printSequence=x.newSequence.encode();d.recipeState=x.newRecipe.encode();d.enlargementMeta=x.newMeta;'
if derived_old not in e:
    raise SystemExit('v0.2.1: derived display-field marker missing')
e = e.replace(derived_old, derived_old + 'syncLogDisplayFields(d,x.newMeta);', 1)

save_marker = '    void saveDerivedLog(Pending x){'
helper_enl = r'''    void syncLogDisplayFields(LogEntry entry,String meta){
        if(entry==null||meta==null||meta.trim().isEmpty())return;
        String col=val(meta,"col");
        if(!col.isEmpty()){
            try{entry.columnHeight=String.format(Locale.ITALY,"%.1f",Double.parseDouble(col));}catch(Exception ignored){}
        }
        String paper=val(meta,"paper");
        if(!paper.isEmpty()){
            String format=paper.replace('.',',').replace("x"," × ")+" cm";
            String current=entry.paper==null?"":entry.paper.trim();
            if(current.isEmpty())entry.paper=format;
            else if(!current.contains(format)&&!current.contains(paper))entry.paper=current+" · "+format;
        }
    }

'''
if save_marker not in e:
    raise SystemExit('v0.2.1: saveDerivedLog marker missing')
e = e.replace(save_marker, helper_enl + save_marker, 1)
enlargement.write_text(e, encoding='utf-8')

# -----------------------------------------------------------------------------
# Static guards.
# -----------------------------------------------------------------------------
hs = home.read_text(encoding='utf-8')
for marker in [
    'ImageView.ScaleType.FIT_CENTER', 'R.drawable.home_vintage',
    'hotspot("PRODOTTI CHIMICI")', 'hotspot("SVILUPPO PELLICOLA")',
    'hotspot("BAGNI STAMPA")', 'hotspot("TIMER STAMPA")',
    'hotspot("USO E MANUTENZIONE")', 'getPackageInfo(getPackageName(), 0)',
    'ART_W = 864f', 'ART_H = 1536f',
]:
    if marker not in hs:
        raise SystemExit('v0.2.1: Home guard failed: ' + marker)
for forbidden in ['secondaryButton()', 'GradientDrawable', 'home_vintage.webp']:
    if forbidden in hs:
        raise SystemExit('v0.2.1: forbidden Home overlay/format remains: ' + forbidden)

ms = maintenance.read_text(encoding='utf-8')
if 'Typeface.create("sans-serif-condensed"' in ms:
    raise SystemExit('v0.2.1: maintenance condensed font still present')
if 'Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL' not in ms:
    raise SystemExit('v0.2.1: maintenance default Timer font missing')

logs = main.read_text(encoding='utf-8')
for marker in [
    'applyEnlargementSnapshotToVisibleLogFields(e);',
    'entry.columnHeight = value;', 'entry.paper = current + " · " + format;',
    'formato carta ', 'Formato e ingrandimento:', 'pendingEnlargementMeta',
]:
    if marker not in logs:
        raise SystemExit('v0.2.1: LOG guard failed: ' + marker)

enl = enlargement.read_text(encoding='utf-8')
for marker in ['syncLogDisplayFields(originEntry,meta);', 'syncLogDisplayFields(d,x.newMeta);']:
    if marker not in enl:
        raise SystemExit('v0.2.1: Enlargement LOG guard failed: ' + marker)

if not target_jpg.exists() or source_webp.exists():
    raise SystemExit('v0.2.1: final Home resource format guard failed')

print('Darkroom v0.2.1 Home/font/LOG fix patch ready')
