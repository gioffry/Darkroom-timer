#!/usr/bin/env python3
from pathlib import Path
import base64
import sys

work = Path(sys.argv[1])
project = work / 'project'
app = project / 'app'
main_dir = app / 'src/main'
java = main_dir / 'java/it/darkroom/timer'
manifest = main_dir / 'AndroidManifest.xml'
gradle = app / 'build.gradle'
build = work / 'build_darkroom.py'
main = java / 'MainActivity.java'
home = java / 'HomeActivity.java'
assets = Path(__file__).resolve().parent / 'assets/home_mockup'


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def wr(p, s):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(s, encoding='utf-8')


def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.13.8 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.13.8 OK', label, flush=True)


# Exact base: successful v0.13.7. This release changes only launcher/home UI and version metadata.
for p, needle in [
    (manifest, 'android:versionName="0.13.7"'),
    (manifest, 'android:versionCode="68"'),
    (main, 'private static final String APP_VERSION = "0.13.7";')]:
    if needle not in rd(p):
        raise SystemExit('v0.13.8 BASE v0.13.7 non riconosciuta: ' + needle)

s = rd(build)
if 'VERSION_NAME = "0.13.7"' not in s or 'VERSION_CODE = "68"' not in s:
    raise SystemExit('v0.13.8 builder base non riconosciuta')
s = s.replace('VERSION_NAME = "0.13.7"', 'VERSION_NAME = "0.13.8"')
s = s.replace('VERSION_CODE = "68"', 'VERSION_CODE = "69"')
s = s.replace('[Darkroom v0.13.7]', '[Darkroom v0.13.8]')
s = s.replace('versionCode 68', 'versionCode 69')
s = s.replace(r'versionCode\s+68\b', r'versionCode\s+69\b')
s = s.replace('0.13.7', '0.13.8')
wr(build, s)

rep(gradle,
    "versionCode 68\n        versionName '0.13.7'",
    "versionCode 69\n        versionName '0.13.8'",
    'Gradle version')
rep(main,
    'private static final String APP_VERSION = "0.13.7";',
    'private static final String APP_VERSION = "0.13.8";',
    'Timer footer version')

# Recreate the exact supplied visual reference as a drawable. The source is kept in small text chunks
# only so it can live safely in the patch branch; the APK receives the decoded WebP binary.
parts = sorted(assets.glob('*.part'))
if len(parts) != 2:
    raise SystemExit(f'v0.13.8 home asset: attese 2 parti, trovate {len(parts)}')
encoded = ''.join(rd(p).strip() for p in parts)
try:
    image_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit('v0.13.8 home asset base64 non valido: ' + str(exc))
if len(image_bytes) < 16000 or image_bytes[:4] != b'RIFF' or image_bytes[8:12] != b'WEBP':
    raise SystemExit('v0.13.8 home asset WebP non valido')
drawable = main_dir / 'res/drawable-nodpi/home_vintage.webp'
drawable.parent.mkdir(parents=True, exist_ok=True)
drawable.write_bytes(image_bytes)
print('v0.13.8 OK home mockup drawable', len(image_bytes), 'bytes', flush=True)

home_source = r'''package it.darkroom.timer;

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
import android.widget.Toast;

/**
 * Full-screen launcher reproducing the approved vintage darkroom mockup.
 * The artwork itself is the reference UI, so typography, texture, light and card geometry
 * stay visually identical instead of being reinterpreted with Android widgets.
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

    private void openTimer() {
        startActivity(new Intent(this, MainActivity.class));
    }

    private void notReady(String section) {
        Toast.makeText(this, section + " · modulo in preparazione", Toast.LENGTH_SHORT).show();
    }

    private final class VintageHomeView extends View {
        private static final float ART_W = 432f;
        private static final float ART_H = 768f;
        private final Bitmap artwork;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
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
            // CENTER_CROP: no letterboxing on modern tall phones. Only the outer scenic margins may crop;
            // all four cards remain fully visible and preserve their original aspect ratio.
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

        private boolean inside(float sx, float sy, float left, float top, float right, float bottom) {
            return sx >= left && sx <= right && sy >= top && sy <= bottom;
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            if (event.getActionMasked() != MotionEvent.ACTION_UP) return true;
            float sx = (event.getX() - dx) / scale;
            float sy = (event.getY() - dy) / scale;

            // Hit areas match the four visible card rectangles in the approved 432x768 artwork.
            if (inside(sx, sy, 52f, 238f, 380f, 320f)) {
                performClick();
                notReady("PRODOTTI CHIMICI");
                return true;
            }
            if (inside(sx, sy, 52f, 324f, 380f, 407f)) {
                performClick();
                notReady("SVILUPPO PELLICOLA");
                return true;
            }
            if (inside(sx, sy, 52f, 410f, 380f, 494f)) {
                performClick();
                notReady("BAGNI STAMPA");
                return true;
            }
            if (inside(sx, sy, 52f, 497f, 380f, 582f)) {
                performClick();
                openTimer();
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
wr(home, home_source)
print('v0.13.8 OK HomeActivity', flush=True)

# Move launcher ownership from Timer to the new Home. MainActivity itself is left functionally untouched.
old_activity = '''        <activity
            android:name=".MainActivity"
            android:screenOrientation="portrait"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
'''
new_activity = '''        <activity
            android:name=".HomeActivity"
            android:screenOrientation="portrait"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name=".MainActivity"
            android:screenOrientation="portrait"
            android:exported="false" />
'''
rep(manifest, old_activity, new_activity, 'Home launcher manifest')
rep(manifest,
    'android:versionCode="68"\n    android:versionName="0.13.7"',
    'android:versionCode="69"\n    android:versionName="0.13.8"',
    'manifest version')

# Hard guards: preserve Timer core and ensure Home is the only launcher.
mt = rd(main)
hs = rd(home)
ms = rd(manifest)
for needle in ['SPLIT GRADE', 'PROVINO', 'ARMA', 'F-STOP', 'SonoffArmService', 'PrintSequence', 'ExposureRecipe']:
    if needle not in mt:
        raise SystemExit('v0.13.8 regressione Timer: manca ' + needle)
for needle in [
    'R.drawable.home_vintage',
    'notReady("PRODOTTI CHIMICI")',
    'notReady("SVILUPPO PELLICOLA")',
    'notReady("BAGNI STAMPA")',
    'openTimer();',
    'Math.max(w / ART_W, h / ART_H)']:
    if needle not in hs:
        raise SystemExit('v0.13.8 guard Home mancante: ' + needle)
if ms.count('android.intent.category.LAUNCHER') != 1:
    raise SystemExit('v0.13.8 launcher count non valido')
if 'android:name=".HomeActivity"' not in ms:
    raise SystemExit('v0.13.8 HomeActivity non registrata')
if 'android:versionName="0.13.8"' not in ms or 'android:versionCode="69"' not in ms:
    raise SystemExit('v0.13.8 versione manifest non valida')
if drawable.stat().st_size != len(image_bytes):
    raise SystemExit('v0.13.8 drawable size mismatch')

print('v0.13.8 TRANSFORM OK — vintage Home from approved mockup; Timer preserved; three future modules are safe placeholders', flush=True)
