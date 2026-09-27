#!/usr/bin/env python3
"""Darkroom 0.7.8: bind the MediaSession callback to Android's main Looper.

0.7.7 proved audio focus is granted, but MediaSession.Callback construction was
happening on the SONOFF ScheduledExecutor thread, which has no Looper. Samsung
then failed before volume-key listening could be armed.

This patch changes only the callback threading:
- imports Handler + Looper;
- supplies new Handler(Looper.getMainLooper()) to MediaSession.setCallback(...).

No SONOFF, Inching, timing, safelight, or exposure-sequence logic is changed.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

old_import = """import android.os.IBinder;
import android.os.PowerManager;"""
new_import = """import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;"""
if old_import not in service:
    raise SystemExit("v0.7.8: expected os imports not found")
service = service.replace(old_import, new_import, 1)

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
    raise SystemExit("v0.7.8: expected v0.7.7 callback not found")
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
    "COMANDO switch=on accettato da START VOL+",
]
for needle in checks:
    if needle not in service:
        raise SystemExit("v0.7.8: missing " + needle)

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_handler_078=APPLIED")
print("media_session_callback_looper=MAIN")
print("volume_start_logic=UNCHANGED_FROM_077")
print("sonoff_timing_changes=ZERO")
print("timer_internal=0.13.21")
