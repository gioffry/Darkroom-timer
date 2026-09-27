#!/usr/bin/env python3
"""Darkroom 0.7.7: harden VOL+ start for Samsung / One UI.

0.7.6 proved the MediaSession is created (START VOL+ ARMATO) but on the test
device no volume callback reached the service. This patch:
- requests transient media audio focus while waiting for START;
- marks the session as handling media buttons / transport controls;
- installs a MediaSession callback for diagnostics;
- changes the remote provider to ABSOLUTE and handles BOTH onAdjustVolume()
  and onSetVolumeTo(), because vendor SystemUI implementations may use either;
- keeps the one-shot guard and releases session/focus immediately after START.

No change to the v0.7.5 local-Inching exposure timing.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# Fields: keep track of temporary audio focus.
old_fields = """    private final AtomicBoolean volumeStartArmed = new AtomicBoolean(false);
    private volatile MediaSession volumeStartSession;
    private PowerManager.WakeLock wakeLock;"""
new_fields = """    private final AtomicBoolean volumeStartArmed = new AtomicBoolean(false);
    private volatile MediaSession volumeStartSession;
    private volatile AudioManager volumeStartAudioManager;
    private final AudioManager.OnAudioFocusChangeListener volumeStartFocusListener = focusChange -> { };
    private PowerManager.WakeLock wakeLock;"""
if old_fields not in service:
    raise SystemExit("v0.7.7: v0.7.6 volume fields not found")
service = service.replace(old_fields, new_fields, 1)

start = service.index("    // VOLUME_START_076")
end = service.index("    private void requestVolumeStart()", start)
old_enable = service[start:end]

new_enable = r'''    // VOLUME_START_077
    // Samsung/One UI hardening: while a provino is waiting for its first START,
    // publish an active media session with remote absolute volume. SystemUI may
    // express a hardware volume key either as a relative adjustment or as an
    // absolute target, therefore both callbacks are accepted.
    private void enableVolumeStartTrigger() {
        disableVolumeStartTrigger();
        if (mode != MODE_TEST || completing.get()) return;
        try {
            AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
            volumeStartAudioManager = am;
            int focus = am == null ? AudioManager.AUDIOFOCUS_REQUEST_FAILED
                    : am.requestAudioFocus(
                        volumeStartFocusListener,
                        AudioManager.STREAM_MUSIC,
                        AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);
            TechnicalLog.add(this, techSessionId,
                    "START VOL+ • audio focus=" + (focus == AudioManager.AUDIOFOCUS_REQUEST_GRANTED ? "GRANTED" : "NOT_GRANTED"));

            MediaSession session = new MediaSession(this, "DarkroomTimerVolumeStart");
            volumeStartSession = session;
            volumeStartArmed.set(true);

            session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS
                    | MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
            session.setCallback(new MediaSession.Callback() {
                @Override public boolean onMediaButtonEvent(Intent mediaButtonIntent) {
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ • MediaSession media-button callback ricevuto");
                    return super.onMediaButtonEvent(mediaButtonIntent);
                }
            });

            PlaybackState playbackState = new PlaybackState.Builder()
                    .setActions(PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PLAY_PAUSE)
                    .setState(PlaybackState.STATE_PLAYING, 0L, 1.0f)
                    .build();
            session.setPlaybackState(playbackState);

            session.setPlaybackToRemote(new VolumeProvider(
                    VolumeProvider.VOLUME_CONTROL_ABSOLUTE, 100, 50) {
                @Override public void onAdjustVolume(int direction) {
                    int before = getCurrentVolume();
                    int after = Math.max(0, Math.min(getMaxVolume(), before + direction));
                    setCurrentVolume(after);
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ CALLBACK adjust • direction=" + direction
                                    + " • " + before + "→" + after);
                    if (direction == AudioManager.ADJUST_RAISE || direction > 0) {
                        requestVolumeStart();
                    }
                }

                @Override public void onSetVolumeTo(int volume) {
                    int before = getCurrentVolume();
                    int after = Math.max(0, Math.min(getMaxVolume(), volume));
                    setCurrentVolume(after);
                    TechnicalLog.add(SonoffArmService.this, techSessionId,
                            "START VOL+ CALLBACK absolute • " + before + "→" + after);
                    if (after > before) {
                        requestVolumeStart();
                    }
                }
            });

            session.setActive(true);
            TechnicalLog.add(this, techSessionId,
                    "START VOL+ ARMATO 0.7.7 • adjust+absolute • valido anche a schermo spento");
        } catch (Exception e) {
            volumeStartArmed.set(false);
            releaseVolumeStartSession();
            TechnicalLog.add(this, techSessionId,
                    "ATTENZIONE START VOL+: MediaSession non disponibile — " + readable(e));
        }
    }

'''
service = service[:start] + new_enable + service[end:]

# Release audio focus together with the media session.
old_release = """    private void releaseVolumeStartSession() {
        MediaSession session = volumeStartSession;
        volumeStartSession = null;
        if (session == null) return;
        try { session.setActive(false); } catch (Exception ignored) {}
        try { session.release(); } catch (Exception ignored) {}
    }
"""
new_release = """    private void releaseVolumeStartSession() {
        MediaSession session = volumeStartSession;
        volumeStartSession = null;
        if (session != null) {
            try { session.setActive(false); } catch (Exception ignored) {}
            try { session.release(); } catch (Exception ignored) {}
        }
        AudioManager am = volumeStartAudioManager;
        volumeStartAudioManager = null;
        if (am != null) {
            try { am.abandonAudioFocus(volumeStartFocusListener); } catch (Exception ignored) {}
        }
    }
"""
if old_release not in service:
    raise SystemExit("v0.7.7: v0.7.6 release method not found")
service = service.replace(old_release, new_release, 1)

# Internal version.
if 'private static final String APP_VERSION = "0.13.19";' not in main:
    raise SystemExit("v0.7.7: expected Timer 0.13.19 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.19";',
    'private static final String APP_VERSION = "0.13.20";',
    1,
)

checks = [
    "VOLUME_START_077",
    "VOLUME_CONTROL_ABSOLUTE",
    "START VOL+ CALLBACK adjust",
    "START VOL+ CALLBACK absolute",
    "requestAudioFocus",
    "FLAG_HANDLES_MEDIA_BUTTONS",
    "abandonAudioFocus",
    "START VOL+ ARMATO 0.7.7",
    "COMANDO switch=on accettato da START VOL+",
]
for needle in checks:
    if needle not in service:
        raise SystemExit("v0.7.7: missing " + needle)

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_start_077=APPLIED")
print("samsung_paths=ADJUST_PLUS_ABSOLUTE")
print("audio_focus=TRANSIENT_MAY_DUCK")
print("media_session_flags=ENABLED")
print("screen_off_start=VOL_PLUS")
print("first_app_pulse_timing=MINIR2_LOCAL_INCHING")
print("timer_internal=0.13.20")
