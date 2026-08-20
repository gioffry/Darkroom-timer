#!/usr/bin/env python3
from pathlib import Path
import base64

root = Path.cwd()
combined = root / 'combined'
home = combined / 'src/main/java/it/darkroom/timer/home/HomeActivity.java'
manifest = combined / 'src/main/AndroidManifest.xml'
gradle = combined / 'build.gradle'
assets = combined / 'v012_assets/home_mockup'

for p in (home, manifest, gradle):
    if not p.exists():
        raise SystemExit('Darkroom v0.1.3: file base mancante: ' + str(p))

old_home = home.read_text(encoding='utf-8')
for needle in [
    'openAssistant("products")',
    'openAssistant("film")',
    'openAssistant("paper")',
    'new Intent(this, MainActivity.class)',
    'PRODOTTI CHIMICI', 'SVILUPPO PELLICOLA', 'BAGNI STAMPA', 'TIMER STAMPA']:
    if needle not in old_home:
        raise SystemExit('Darkroom v0.1.3: Home v0.1.1 non riconosciuta: ' + needle)

parts = sorted(assets.glob('*.part'))
if len(parts) != 2:
    raise SystemExit(f'Darkroom v0.1.3: attese 2 parti asset, trovate {len(parts)}')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
try:
    image_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit('Darkroom v0.1.3: asset base64 non valido: ' + str(exc))
if len(image_bytes) < 16000 or image_bytes[:4] != b'RIFF' or image_bytes[8:12] != b'WEBP':
    raise SystemExit('Darkroom v0.1.3: asset WebP non valido')
drawable = combined / 'src/main/res/drawable-nodpi/home_vintage.webp'
drawable.parent.mkdir(parents=True, exist_ok=True)
drawable.write_bytes(image_bytes)

home_source = r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;

import it.darkroom.timer.MainActivity;
import it.darkroom.timer.R;
import it.darkroom.assistant.AssistantActivityV2;

/** Home unica Darkroom: grafica mockup approvata + quattro funzioni reali. */
public final class HomeActivity extends Activity {
    private static final float ART_W = 432f;
    private static final float ART_H = 768f;

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
        artwork.setScaleType(ImageView.ScaleType.CENTER_CROP);
        artwork.setAdjustViewBounds(false);
        artwork.setImageResource(R.drawable.home_vintage);
        frame.addView(artwork, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        View products = hotspot("Prodotti chimici");
        View film = hotspot("Sviluppo pellicola");
        View paper = hotspot("Bagni stampa");
        View timer = hotspot("Timer stampa");

        products.setOnClickListener(v -> openAssistant("products"));
        film.setOnClickListener(v -> openAssistant("film"));
        paper.setOnClickListener(v -> openAssistant("paper"));
        timer.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));

        frame.addView(products, new FrameLayout.LayoutParams(1, 1));
        frame.addView(film, new FrameLayout.LayoutParams(1, 1));
        frame.addView(paper, new FrameLayout.LayoutParams(1, 1));
        frame.addView(timer, new FrameLayout.LayoutParams(1, 1));

        final View[] hotspots = new View[]{products, film, paper, timer};
        frame.addOnLayoutChangeListener((v, left, top, right, bottom,
                                         oldLeft, oldTop, oldRight, oldBottom) ->
                placeHotspots(frame, hotspots));

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

    private void placeHotspots(FrameLayout frame, View[] v) {
        int w = frame.getWidth();
        int h = frame.getHeight();
        if (w <= 0 || h <= 0 || v.length != 4) return;

        float scale = Math.max(w / ART_W, h / ART_H);
        float dx = (w - ART_W * scale) * 0.5f;
        float dy = (h - ART_H * scale) * 0.5f;

        place(v[0], dx, dy, scale, 52f, 238f, 380f, 320f);
        place(v[1], dx, dy, scale, 52f, 324f, 380f, 407f);
        place(v[2], dx, dy, scale, 52f, 410f, 380f, 494f);
        place(v[3], dx, dy, scale, 52f, 497f, 380f, 582f);
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

ms = manifest.read_text(encoding='utf-8')
if 'android:versionName="0.1.1"' not in ms or 'android:versionCode="2"' not in ms:
    raise SystemExit('Darkroom v0.1.3: manifest v0.1.1 non riconosciuto')
ms = ms.replace('android:versionCode="2"', 'android:versionCode="4"', 1)
ms = ms.replace('android:versionName="0.1.1"', 'android:versionName="0.1.3"', 1)
manifest.write_text(ms, encoding='utf-8')

gs = gradle.read_text(encoding='utf-8')
if "versionCode 2" not in gs or "versionName '0.1.1'" not in gs:
    raise SystemExit('Darkroom v0.1.3: Gradle v0.1.1 non riconosciuto')
gs = gs.replace('versionCode 2', 'versionCode 4', 1)
gs = gs.replace("versionName '0.1.1'", "versionName '0.1.3'", 1)
gradle.write_text(gs, encoding='utf-8')

hs = home.read_text(encoding='utf-8')
for needle in [
    'openAssistant("products")',
    'openAssistant("film")',
    'openAssistant("paper")',
    'new Intent(this, MainActivity.class)',
    'ImageView.ScaleType.CENTER_CROP',
    'R.drawable.home_vintage',
    'WindowManager.LayoutParams.FLAG_FULLSCREEN']:
    if needle not in hs:
        raise SystemExit('Darkroom v0.1.3: guard Home mancante: ' + needle)
for forbidden in ['BitmapFactory', 'WindowInsetsController', 'IllegalStateException("home_vintage']:
    if forbidden in hs:
        raise SystemExit('Darkroom v0.1.3: codice Home rischioso rilevato: ' + forbidden)
if drawable.stat().st_size != len(image_bytes):
    raise SystemExit('Darkroom v0.1.3: asset size mismatch')

print('Darkroom v0.1.3 HOME SAFE OK — mockup approvato + 4 funzioni reali preservate')
