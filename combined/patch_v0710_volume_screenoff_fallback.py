#!/usr/bin/env python3
"""Darkroom 0.7.10: make VOL+ screen-off start robust on Samsung.

0.7.9 keeps the MediaSession/VolumeProvider trigger, but the test phone can lose
hardware-volume routing when the display is off. This patch keeps that path and
adds two short-lived safeguards while an exposure is waiting for user START:

1) a completely silent looping MediaPlayer so Android/One UI continues to see
   Darkroom as active media playback while the foreground service is armed;
2) a screen-off STREAM_MUSIC volume probe. If One UI changes the real media
   stream instead of invoking VolumeProvider, an upward step is treated as the
   same VOL+ START and the previous volume is restored immediately.

The fallback is one-shot, active only while volumeStartArmed is true, and never
changes SONOFF/Inching exposure timing. VOL- focus remains foreground-only.
"""

from pathlib import Path
import wave

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"
RAW = Path("combined/src/main/res/raw")
SILENCE = RAW / "darkroom_volume_keepalive.wav"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# Generate a tiny 250 ms mono PCM silent resource used only while waiting for START.
RAW.mkdir(parents=True, exist_ok=True)
with wave.open(str(SILENCE), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(8000)
    wav.writeframes(b"\x00\x00" * 2000)

old_import = """import android.media.AudioManager;
import android.media.ToneGenerator;
import android.media.VolumeProvider;"""
new_import = """import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.ToneGenerator;
import android.media.VolumeProvider;"""
if old_import not in service:
    raise SystemExit("v0.7.10: expected media imports not found")
service = service.replace(old_import, new_import, 1)

old_fields = """    private volatile MediaSession volumeStartSession;
    private volatile AudioManager volumeStartAudioManager;
    private final AudioManager.OnAudioFocusChangeListener volumeStartFocusListener = focusChange -> { };
    private PowerManager.WakeLock wakeLock;"""
new_fields = """    private volatile MediaSession volumeStartSession;
    private volatile AudioManager volumeStartAudioManager;
    private final AudioManager.OnAudioFocusChangeListener volumeStartFocusListener = focusChange -> { };
    private volatile MediaPlayer volumeScreenOffPlayer;
    private final Handler volumeScreenOffHandler = new Handler(Looper.getMainLooper());
    private volatile int volumeScreenOffBaseline = -1;
    private volatile int volumeScreenOffRestoreVolume = -1;
    private volatile boolean volumeScreenOffProbeActive = false;
    private final Runnable volumeScreenOffProbe = new Runnable() {
        @Override public void run() {
            if (!volumeScreenOffProbeActive || !volumeStartArmed.get()) return;
            try {
                AudioManager am = volumeStartAudioManager;
                if (am == null) return;
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                boolean interactive = pm != null && pm.isInteractive();
                int now = am.getStreamVolume(AudioManager.STREAM_MUSIC);
                int before = volumeScreenOffBaseline;
                volumeScreenOffBaseline = now;
                if (!interactive && before >= 0 && now > before) {
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ FALLBACK screen-off • STREAM_MUSIC " + before + "→" + now);
                    requestVolumeStart();
                    return;
                }
            } catch (Exception e) {
                TechnicalLog.add(SonoffArmService.this, techSessionId,
                        "ATTENZIONE START VOL+ FALLBACK • probe — " + readable(e));
            }
            if (volumeScreenOffProbeActive && volumeStartArmed.get()) {
                volumeScreenOffHandler.postDelayed(this, 80L);
            }
        }
    };
    private PowerManager.WakeLock wakeLock;"""
if old_fields not in service:
    raise SystemExit("v0.7.10: expected v0.7.9 volume fields not found")
service = service.replace(old_fields, new_fields, 1)

# Start the screen-off keepalive after the v0.7.9 one-shot trigger is armed.
old_session_arm = """            MediaSession session = new MediaSession(this, "DarkroomTimerVolumeStart");
            volumeStartSession = session;
            volumeStartArmed.set(true);

            session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS"""
new_session_arm = """            MediaSession session = new MediaSession(this, "DarkroomTimerVolumeStart");
            volumeStartSession = session;
            volumeStartArmed.set(true);
            startVolumeScreenOffFallback(am);

            session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS"""
if old_session_arm not in service:
    raise SystemExit("v0.7.10: expected v0.7.9 MediaSession arm block not found")
service = service.replace(old_session_arm, new_session_arm, 1)

marker = "    private void requestVolumeStart() {"
if marker not in service:
    raise SystemExit("v0.7.10: requestVolumeStart marker not found")

methods = r"""    // VOLUME_SCREEN_OFF_0710
    // One UI can stop routing volume keys to a remote VolumeProvider when the
    // display is off. Keep a zero-volume media player STARTED while waiting and,
    // as a second path, watch the real media-stream level only while non-interactive.
    private void startVolumeScreenOffFallback(AudioManager am) {
        stopVolumeScreenOffFallback();
        if (am == null || !volumeStartArmed.get()) return;
        try {
            int max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
            int current = am.getStreamVolume(AudioManager.STREAM_MUSIC);
            volumeScreenOffRestoreVolume = current;
            // If already at maximum, leave one upward hardware step available.
            if (max > 0 && current >= max) {
                am.setStreamVolume(AudioManager.STREAM_MUSIC, max - 1, 0);
                current = max - 1;
            }
            volumeScreenOffBaseline = current;

            MediaPlayer player = MediaPlayer.create(this, R.raw.darkroom_volume_keepalive);
            if (player != null) {
                player.setLooping(true);
                player.setVolume(0.0f, 0.0f);
                player.start();
                volumeScreenOffPlayer = player;
            }

            volumeScreenOffProbeActive = true;
            volumeScreenOffHandler.removeCallbacks(volumeScreenOffProbe);
            volumeScreenOffHandler.postDelayed(volumeScreenOffProbe, 80L);
            TechnicalLog.add(this, techSessionId,
                    "START VOL+ SCREEN-OFF 0.7.10 ARMATO • silent media + stream fallback");
        } catch (Exception e) {
            stopVolumeScreenOffFallback();
            TechnicalLog.add(this, techSessionId,
                    "ATTENZIONE START VOL+ SCREEN-OFF • keepalive — " + readable(e));
        }
    }

    private void stopVolumeScreenOffFallback() {
        volumeScreenOffProbeActive = false;
        volumeScreenOffHandler.removeCallbacks(volumeScreenOffProbe);

        MediaPlayer player = volumeScreenOffPlayer;
        volumeScreenOffPlayer = null;
        if (player != null) {
            try { player.stop(); } catch (Exception ignored) {}
            try { player.release(); } catch (Exception ignored) {}
        }

        AudioManager am = volumeStartAudioManager;
        int restore = volumeScreenOffRestoreVolume;
        volumeScreenOffBaseline = -1;
        volumeScreenOffRestoreVolume = -1;
        if (am != null && restore >= 0) {
            try {
                if (am.getStreamVolume(AudioManager.STREAM_MUSIC) != restore) {
                    am.setStreamVolume(AudioManager.STREAM_MUSIC, restore, 0);
                }
            } catch (Exception ignored) {}
        }
    }

"""
service = service.replace(marker, methods + marker, 1)

# The common release path must always tear down the silent player/probe too.
old_release = """    private void releaseVolumeStartSession() {
        MediaSession session = volumeStartSession;"""
new_release = """    private void releaseVolumeStartSession() {
        stopVolumeScreenOffFallback();
        MediaSession session = volumeStartSession;"""
if old_release not in service:
    raise SystemExit("v0.7.10: releaseVolumeStartSession not found")
service = service.replace(old_release, new_release, 1)

# Update diagnostic label and internal Timer version.
old_label = "START VOL+ ARMATO 0.7.9 • tutte le esposizioni • valido anche a schermo spento"
new_label = "START VOL+ ARMATO 0.7.10 • tutte le esposizioni • screen-off rinforzato"
if old_label not in service:
    raise SystemExit("v0.7.10: v0.7.9 diagnostic label not found")
service = service.replace(old_label, new_label, 1)

if 'private static final String APP_VERSION = "0.13.22";' not in main:
    raise SystemExit("v0.7.10: expected Timer 0.13.22 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.22";',
    'private static final String APP_VERSION = "0.13.23";',
    1,
)

checks_service = [
    "VOLUME_SCREEN_OFF_0710",
    "MediaPlayer volumeScreenOffPlayer",
    "R.raw.darkroom_volume_keepalive",
    "START VOL+ FALLBACK screen-off",
    "START VOL+ SCREEN-OFF 0.7.10 ARMATO",
    "stopVolumeScreenOffFallback();",
    "START VOL+ ARMATO 0.7.10",
]
for needle in checks_service:
    if needle not in service:
        raise SystemExit("v0.7.10: missing service marker " + needle)

if not SILENCE.exists() or SILENCE.stat().st_size < 4000:
    raise SystemExit("v0.7.10: silent keepalive WAV was not created correctly")

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_screen_off_0710=APPLIED")
print("screen_off_primary=MEDIASESSION_VOLUME_PROVIDER")
print("screen_off_keepalive=SILENT_MEDIA_PLAYER")
print("screen_off_fallback=STREAM_MUSIC_UP_WHILE_NON_INTERACTIVE")
print("stream_volume_restored=YES")
print("vol_minus_focus=UNCHANGED_FOREGROUND_ONLY")
print("sonoff_timing_changes=ZERO")
print("timer_internal=0.13.23")
