#!/usr/bin/env python3
"""Darkroom 0.7.8: bind MediaSession callback explicitly to Android main looper.

0.7.7 correctly obtained audio focus but crashed while constructing the callback
because SonoffArmService arms from its ScheduledExecutorService, whose thread has
no Looper. Use a Handler backed by Looper.getMainLooper() explicitly.

No changes to SONOFF timing, Inching, polling or provino sequence.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

old_imports = """import android.media.session.PlaybackState;
import android.os.IBinder;
import android.os.PowerManager;"""
new_imports = """import android.media.session.PlaybackState;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;"""
if old_imports not in service:
    raise SystemExit("v0.7.8: expected Android imports not found")
service = service.replace(old_imports, new_imports, 1)

old_callback = """            session.setCallback(new MediaSession.Callback() {
                @Override public boolean onMediaButtonEvent(Intent mediaButtonIntent) {
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ • MediaSession media-button callback ricevuto");
                    return super.onMediaButtonEvent(mediaButtonIntent);
                }
            });"""
new_callback = """            session.setCallback(new MediaSession.Callback() {
                @Override public boolean onMediaButtonEvent(Intent mediaButtonIntent) {
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ • MediaSession media-button callback ricevuto");
                    return super.onMediaButtonEvent(mediaButtonIntent);
                }
            }, new Handler(Looper.getMainLooper()));"""
if old_callback not in service:
    raise SystemExit("v0.7.8: v0.7.7 callback block not found")
service = service.replace(old_callback, new_callback, 1)

if 'private static final String APP_VERSION = "0.13.20";' not in main:
    raise SystemExit("v0.7.8: expected Timer 0.13.20 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.20";',
    'private static final String APP_VERSION = "0.13.21";',
    1,
)

checks = [
    "VOLUME_START_077",
    "new Handler(Looper.getMainLooper())",
    "START VOL+ CALLBACK adjust",
    "START VOL+ CALLBACK absolute",
    "requestAudioFocus",
    "COMANDO switch=on accettato da START VOL+",
]
for needle in checks:
    if needle not in service:
        raise SystemExit("v0.7.8: missing " + needle)

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_start_078=APPLIED")
print("mediasession_callback_looper=MAIN")
print("samsung_paths=ADJUST_PLUS_ABSOLUTE")
print("sonoff_timing_changes=ZERO")
print("timer_internal=0.13.21")
