#!/usr/bin/env python3
from pathlib import Path
import base64
import re

root = Path.cwd()
combined = root / 'combined'
home = combined / 'src/main/java/it/darkroom/timer/home/HomeActivity.java'
manifest = combined / 'src/main/AndroidManifest.xml'
gradle = combined / 'build.gradle'
assets = combined / 'v012_assets/home_mockup'

for p in (home, manifest, gradle):
    if not p.exists():
        raise SystemExit('Darkroom v0.1.2: file base mancante: ' + str(p))

old_home = home.read_text(encoding='utf-8')
for needle in [
    'openAssistant("products")',
    'openAssistant("film")',
    'openAssistant("paper")',
    'new Intent(this, MainActivity.class)',
    'PRODOTTI CHIMICI', 'SVILUPPO PELLICOLA', 'BAGNI STAMPA', 'TIMER STAMPA']:
    if needle not in old_home:
        raise SystemExit('Darkroom v0.1.2: Home v0.1.1 non riconosciuta: ' + needle)

# Ricostruisce il mockup approvato come asset WebP esatto.
parts = sorted(assets.glob('*.part'))
if len(parts) != 2:
    raise SystemExit(f'Darkroom v0.1.2: attese 2 parti asset, trovate {len(parts)}')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
try:
    image_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit('Darkroom v0.1.2: asset base64 non valido: ' + str(exc))
if len(image_bytes) < 16000 or image_bytes[:4] != b'RIFF' or image_bytes[8:12] != b'WEBP':
    raise SystemExit('Darkroom v0.1.2: asset WebP non valido')
drawable = combined / 'src/main/res/drawable-nodpi/home_vintage.webp'
drawable.parent.mkdir(parents=True, exist_ok=True)
drawable.write_bytes(image_bytes)

home_source = r'''package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Build;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;

import it.darkroom.timer.MainActivity;
import it.darkroom.assistant.AssistantActivityV2;

/**
 * Home unica Darkroom. Lo sfondo e i quattro accessi visibili coincidono con il
 * mockup approvato; le aree trasparenti sopra le quattro card mantengono tutte
 * le funzioni reali della v0.1.1.
 */
public final class HomeActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        enterImmersive();
        setContentView(new VintageHomeView());
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) enterImmersive();
    }

    private void enterImmersive() {
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        }
    }

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }

    private final class VintageHomeView extends View {
        private static final float ART_W = 432f;
        private static final float ART_H = 768f;
        private final Bitmap artwork;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG
                | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
        private final RectF destination = new RectF();
        private float scale = 1f;
        private float dx = 0f;
        private float dy = 0f;

        VintageHomeView() {
            super(HomeActivity.this);
            setBackgroundColor(Color.BLACK);
            setContentDescription("Darkroom camera oscura");
            artwork = BitmapFactory.decodeResource(getResources(), R.drawable.home_vintage);
            if (artwork == null) throw new IllegalStateException("home_vintage non disponibile");
        }

        @Override
        protected void onSizeChanged(int w, int h, int oldw, int oldh) {
            super.onSizeChanged(w, h, oldw, oldh);
            // CENTER_CROP: riempie lo schermo senza deformazioni. Il crop interessa
            // soltanto i margini scenografici; le quattro card restano visibili.
            scale = Math.max(w / ART_W, h / ART_H);
            float renderedW = ART_W * scale;
            float renderedH = ART_H * scale;
            dx = (w - renderedW) * 0.5f;
            dy = (h - renderedH) * 0.5f;
            destination.set(dx, dy, dx + renderedW, dy + renderedH);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            canvas.drawColor(Color.BLACK);
            canvas.drawBitmap(artwork, null, destination, paint);
        }

        private boolean inside(float x, float y, float l, float t, float r, float b) {
            return x >= l && x <= r && y >= t && y <= b;
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            if (event.getActionMasked() != MotionEvent.ACTION_UP) return true;
            float x = (event.getX() - dx) / scale;
            float y = (event.getY() - dy) / scale;

            if (inside(x, y, 52f, 238f, 380f, 320f)) {
                performClick();
                openAssistant("products");
                return true;
            }
            if (inside(x, y, 52f, 324f, 380f, 407f)) {
                performClick();
                openAssistant("film");
                return true;
            }
            if (inside(x, y, 52f, 410f, 380f, 494f)) {
                performClick();
                openAssistant("paper");
                return true;
            }
            if (inside(x, y, 52f, 497f, 380f, 582f)) {
                performClick();
                startActivity(new Intent(HomeActivity.this, MainActivity.class));
                return true;
            }
            return true;
        }

        @Override
        public boolean performClick() {
            super.performClick();
            return true;
        }
    }
}
'''
home.write_text(home_source, encoding='utf-8')

ms = manifest.read_text(encoding='utf-8')
if 'android:versionName="0.1.1"' not in ms or 'android:versionCode="2"' not in ms:
    raise SystemExit('Darkroom v0.1.2: manifest v0.1.1 non riconosciuto')
ms = ms.replace('android:versionCode="2"', 'android:versionCode="3"', 1)
ms = ms.replace('android:versionName="0.1.1"', 'android:versionName="0.1.2"', 1)
manifest.write_text(ms, encoding='utf-8')

gs = gradle.read_text(encoding='utf-8')
if "versionCode 2" not in gs or "versionName '0.1.1'" not in gs:
    raise SystemExit('Darkroom v0.1.2: Gradle v0.1.1 non riconosciuto')
gs = gs.replace('versionCode 2', 'versionCode 3', 1)
gs = gs.replace("versionName '0.1.1'", "versionName '0.1.2'", 1)
gradle.write_text(gs, encoding='utf-8')

# Guardrail funzionali: nessun placeholder, tutte e quattro le funzioni reali restano instradate.
hs = home.read_text(encoding='utf-8')
for needle in [
    'openAssistant("products");',
    'openAssistant("film");',
    'openAssistant("paper");',
    'startActivity(new Intent(HomeActivity.this, MainActivity.class));',
    'R.drawable.home_vintage',
    'Math.max(w / ART_W, h / ART_H)']:
    if needle not in hs:
        raise SystemExit('Darkroom v0.1.2: guard Home mancante: ' + needle)
if 'modulo in preparazione' in hs.lower() or 'Toast.makeText' in hs:
    raise SystemExit('Darkroom v0.1.2: placeholder rilevato nella Home')
if drawable.stat().st_size != len(image_bytes):
    raise SystemExit('Darkroom v0.1.2: asset size mismatch')

print('Darkroom v0.1.2 HOME OK — mockup approvato + 4 funzioni reali preservate')
