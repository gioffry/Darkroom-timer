#!/usr/bin/env python3
from pathlib import Path
import subprocess

root = Path('combined/src/main/java/it/darkroom/timer')
home = root / 'home/HomeActivity.java'
maintenance = root / 'maintenance/UseMaintenanceActivity.java'
main = root / 'MainActivity.java'
enlargement = root / 'EnlargementActivity.java'
drawable = Path('combined/src/main/res/drawable-nodpi')

for p in (home, maintenance, main, enlargement):
    if not p.exists():
        raise SystemExit('v0.2.1: generated source missing: ' + str(p))

# -----------------------------------------------------------------------------
# HOME — Android-decodable JPEG, no visible duplicate overlay.
# -----------------------------------------------------------------------------
webp = drawable / 'home_vintage.webp'
jpg = drawable / 'home_vintage.jpg'
if not webp.exists():
    raise SystemExit('v0.2.1: approved Home WebP source missing before conversion')

subprocess.run([
    'ffmpeg', '-y', '-v', 'error', '-xerror',
    '-i', str(webp),
    '-vf', 'scale=864:1536:flags=lanczos',
    '-frames:v', '1', '-pix_fmt', 'yuvj420p', '-q:v', '2',
    str(jpg),
], check=True)

raw = jpg.read_bytes()
if len(raw) < 150000 or raw[:2] != b'\xff\xd8' or raw[-2:] != b'\xff\xd9':
    raise SystemExit('v0.2.1: generated Home JPEG is invalid')
webp.unlink()
for stale in (drawable / 'home_vintage.png',):
    if stale.exists():
        stale.unlink()

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

/**
 * Home Darkroom v0.2.1.
 * Il mockup CAMERA OSCURA è l'intera interfaccia visiva; sopra restano soltanto
 * hotspot trasparenti e la versione reale dell'app.
 */
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
        frame.addView(artwork, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        View products = hotspot("Prodotti chimici");
        View film = hotspot("Sviluppo pellicola");
        View paper = hotspot("Bagni stampa");
        View timer = hotspot("Timer stampa");
        View maintenance = hotspot("Uso e manutenzione");
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

        final View[] controls = new View[]{products, film, paper, timer, maintenance};
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
        v.setTextColor(Color.argb(190, 225, 216, 203));
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

    private void placeHomeControls(FrameLayout frame, View[] v, View version) {
        int w = frame.getWidth();
        int h = frame.getHeight();
        if (w <= 0 || h <= 0 || v.length != 5) return;

        // Deve corrispondere esattamente a FIT_CENTER: nessun crop del mockup.
        float scale = Math.min(w / ART_W, h / ART_H);
        float dx = (w - ART_W * scale) * 0.5f;
        float dy = (h - ART_H * scale) * 0.5f;

        place(v[0], dx, dy, scale, 120f, 520f, 744f, 682f);
        place(v[1], dx, dy, scale, 120f, 687f, 744f, 854f);
        place(v[2], dx, dy, scale, 120f, 854f, 744f, 1022f);
        place(v[3], dx, dy, scale, 120f, 1022f, 744f, 1192f);
        place(v[4], dx, dy, scale, 230f, 1190f, 634f, 1272f);
        place(version, dx, dy, scale, 340f, 1465f, 524f, 1510f);
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
# USO E MANUTENZIONE — stesso font operativo del Timer.
# -----------------------------------------------------------------------------
m = maintenance.read_text(encoding='utf-8')
old_font = 'v.setTypeface(Typeface.create("sans-serif-condensed",bold?Typeface.BOLD:Typeface.NORMAL));'
new_font = 'v.setTypeface(Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL);'
if old_font not in m:
    raise SystemExit('v0.2.1: UseMaintenance condensed font marker missing')
m = m.replace(old_font, new_font, 1)
maintenance.write_text(m, encoding='utf-8')

# -----------------------------------------------------------------------------
# LOG — oltre al metadato completo, sincronizza i campi visibili CARTA/COLONNA.
# -----------------------------------------------------------------------------
s = main.read_text(encoding='utf-8')
meta_block = '''        long enlargementArmAt = p.getLong("pendingEnlargementAt", 0L);\n        e.enlargementMeta = (printAt > 0 && enlargementArmAt > 0 && enlargementArmAt <= printAt)\n                ? p.getString("pendingEnlargementMeta", "") : "";'''
meta_repl = meta_block + '\n        syncEnlargementDisplayFields(e, e.enlargementMeta);'
if meta_block not in s:
    raise SystemExit('v0.2.1: new LOG enlargement snapshot marker missing')
s = s.replace(meta_block, meta_repl, 1)

editor_marker = '    private void showLogEditor(final LogEntry entry, final boolean isNew) {'
editor_repl = editor_marker + '''\n        if (syncEnlargementDisplayFields(entry, entry.enlargementMeta) && !isNew) {\n            LogStore.save(this, entry);\n        }'''
if editor_marker not in s:
    raise SystemExit('v0.2.1: showLogEditor marker missing')
s = s.replace(editor_marker, editor_repl, 1)

helper_marker = '    private static String enlargementMetaValue(String meta, String key) {'
helper = r'''    private boolean syncEnlargementDisplayFields(LogEntry entry, String meta) {
        if (entry == null || meta == null || meta.trim().isEmpty()) return false;
        boolean changed = false;

        String col = enlargementMetaValue(meta, "col");
        if (!col.isEmpty()) {
            try {
                String value = String.format(Locale.ITALY, "%.1f", Double.parseDouble(col));
                if (entry.columnHeight == null || !value.equals(entry.columnHeight.trim())) {
                    entry.columnHeight = value;
                    changed = true;
                }
            } catch (Exception ignored) {}
        }

        String paper = enlargementMetaValue(meta, "paper");
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
if helper_marker not in s:
    raise SystemExit('v0.2.1: enlargementMetaValue helper marker missing')
s = s.replace(helper_marker, helper + helper_marker, 1)
main.write_text(s, encoding='utf-8')

# Same explicit synchronization for legacy backfill and derived prints.
e = enlargement.read_text(encoding='utf-8')
legacy_old = '''            originEntry.enlargementMeta=meta;\n            if(originEntry.columnHeight==null||originEntry.columnHeight.trim().isEmpty())originEntry.columnHeight=fmt(c.col);'''
legacy_new = '''            originEntry.enlargementMeta=meta;\n            syncLogDisplayFields(originEntry,meta);'''
if legacy_old not in e:
    raise SystemExit('v0.2.1: legacy LOG display sync marker missing')
e = e.replace(legacy_old, legacy_new, 1)

derived_old = 'd.printSequence=x.newSequence.encode();d.recipeState=x.newRecipe.encode();d.enlargementMeta=x.newMeta;'
derived_new = derived_old + 'syncLogDisplayFields(d,x.newMeta);'
if derived_old not in e:
    raise SystemExit('v0.2.1: derived LOG metadata marker missing')
e = e.replace(derived_old, derived_new, 1)

save_marker = '    void saveDerivedLog(Pending x){'
enlargement_helper = r'''    void syncLogDisplayFields(LogEntry entry,String meta){
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
e = e.replace(save_marker, enlargement_helper + save_marker, 1)
enlargement.write_text(e, encoding='utf-8')

# -----------------------------------------------------------------------------
# Static guards.
# -----------------------------------------------------------------------------
hs = home.read_text(encoding='utf-8')
for marker in [
    'ART_W = 864f', 'ART_H = 1536f', 'ImageView.ScaleType.FIT_CENTER',
    'UseMaintenanceActivity.class', 'getPackageInfo(getPackageName(), 0)',
    'place(v[4], dx, dy, scale, 230f, 1190f, 634f, 1272f)',
]:
    if marker not in hs:
        raise SystemExit('v0.2.1: Home guard failed: ' + marker)
for forbidden in ['secondaryButton()', 'ic_wrench_bronze', 'Typeface.SERIF']:
    if forbidden in hs:
        raise SystemExit('v0.2.1: visible Home overlay remains: ' + forbidden)

ms = maintenance.read_text(encoding='utf-8')
if 'sans-serif-condensed' in ms or 'Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL' not in ms:
    raise SystemExit('v0.2.1: UseMaintenance font guard failed')

main_src = main.read_text(encoding='utf-8')
for marker in [
    'syncEnlargementDisplayFields(e, e.enlargementMeta);',
    'entry.columnHeight = value;',
    'entry.paper = current + " · " + format;',
]:
    if marker not in main_src:
        raise SystemExit('v0.2.1: MainActivity LOG guard failed: ' + marker)

enl_src = enlargement.read_text(encoding='utf-8')
for marker in [
    'syncLogDisplayFields(originEntry,meta);',
    'syncLogDisplayFields(d,x.newMeta);',
    'orientation=LANDSCAPE', 'paper=%.1fx%.1f', 'col=%.8f',
]:
    if marker not in enl_src:
        raise SystemExit('v0.2.1: Enlargement LOG guard failed: ' + marker)

print('Darkroom v0.2.1 Home/font/LOG fixes ready')
