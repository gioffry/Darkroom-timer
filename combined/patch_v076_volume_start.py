#!/usr/bin/env python3
"""Darkroom 0.7.6: start a test strip with VOL+ even when the screen is off.

While a provino is ARMED, SonoffArmService owns a short-lived active MediaSession
with a remote VolumeProvider. A single VOL+ event is consumed as START for the
first exposure; repeated key events are ignored. The screen may be really off:
the foreground service + PARTIAL_WAKE_LOCK already keep the timing state machine
alive.

The first app-started exposure uses the same v0.7.5 rule as automatic strips:
- switch=on acceptance is the start reference;
- MINIR2 local Inching owns exposure duration;
- no ON polling is required during the pulse;
- OFF polling resumes only after the requested width.

The existing physical S1/S2 start remains available as a fallback.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# Android media-session imports.
old_imports = """import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.IBinder;"""
new_imports = """import android.media.AudioManager;
import android.media.ToneGenerator;
import android.media.VolumeProvider;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.IBinder;"""
if old_imports not in service:
    raise SystemExit("v0.7.6: expected media imports not found")
service = service.replace(old_imports, new_imports, 1)

# Runtime state for one-shot VOL+ arming.
old_fields = """    private final AtomicBoolean seenOn = new AtomicBoolean(false);
    private final AtomicBoolean completing = new AtomicBoolean(false);
    private PowerManager.WakeLock wakeLock;"""
new_fields = """    private final AtomicBoolean seenOn = new AtomicBoolean(false);
    private final AtomicBoolean completing = new AtomicBoolean(false);
    private final AtomicBoolean volumeStartArmed = new AtomicBoolean(false);
    private volatile MediaSession volumeStartSession;
    private PowerManager.WakeLock wakeLock;"""
if old_fields not in service:
    raise SystemExit("v0.7.6: expected service fields not found")
service = service.replace(old_fields, new_fields, 1)

# Reset any stale media-session trigger whenever a new arm begins.
old_arm_start = """        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {
            interlockActive = false;"""
new_arm_start = """        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {
            disableVolumeStartTrigger();
            interlockActive = false;"""
if old_arm_start not in service:
    raise SystemExit("v0.7.6: arm entry not found")
service = service.replace(old_arm_start, new_arm_start, 1)

# Make the armed UI explain the new screen-off trigger, and arm it only for provini.
old_armed = """            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) {
                msg = "SPLIT GRADE ARMATO — GIALLO " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + dodgeStatusSuffix(PrintCorrection.PHASE_SOFT) + " — premi il pulsante fisico";
            } else if (mode == MODE_TEST && testPreExposureMs > 0) {
                msg = "SPLIT GRADE · BASE MORBIDA ARMATA — " + testPreExposureFilterValue + "Y / 0M · " + seconds(testPreExposureMs) + " — premi il pulsante fisico";
            } else {
                msg = mode == MODE_PRINT ? "ARMATO — premi il pulsante fisico" : "PROVINO ARMATO — premi il pulsante fisico una volta";
            }
            broadcast(STATE_ARMED, msg);
            updateNotification(msg);
            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_SOFT));
            else if (mode == MODE_TEST && testPreExposureMs > 0) scheduleVoiceInstruction(testPreExposurePrompt());
            startPolling(250);"""
new_armed = """            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) {
                msg = "SPLIT GRADE ARMATO — GIALLO " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + dodgeStatusSuffix(PrintCorrection.PHASE_SOFT) + " — premi il pulsante fisico";
            } else if (mode == MODE_TEST && testPreExposureMs > 0) {
                msg = "SPLIT GRADE · BASE MORBIDA ARMATA — " + testPreExposureFilterValue + "Y / 0M · " + seconds(testPreExposureMs) + " — spegni lo schermo e premi VOL+";
            } else {
                msg = mode == MODE_PRINT ? "ARMATO — premi il pulsante fisico" : "PROVINO ARMATO — spegni lo schermo e premi VOL+";
            }
            broadcast(STATE_ARMED, msg);
            updateNotification(msg);
            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_SOFT));
            else if (mode == MODE_TEST && testPreExposureMs > 0) scheduleVoiceInstruction(testPreExposurePrompt());
            if (mode == MODE_TEST) enableVolumeStartTrigger();
            startPolling(250);"""
if old_armed not in service:
    raise SystemExit("v0.7.6: armed block not found")
service = service.replace(old_armed, new_armed, 1)

# If the user starts with the existing physical input, immediately stop intercepting volume.
old_seen_on = """                if (seenOn.compareAndSet(false, true)) {
                    if (safelightAuto) {"""
new_seen_on = """                if (seenOn.compareAndSet(false, true)) {
                    disableVolumeStartTrigger();
                    if (safelightAuto) {"""
if old_seen_on not in service:
    raise SystemExit("v0.7.6: observed-ON block not found")
service = service.replace(old_seen_on, new_seen_on, 1)

# Split-grade hard phase is another user-started provino phase: VOL+ should work there too.
old_split_transition = """                broadcast(STATE_WAITING_SPLIT, transition);
                updateNotification(transition);
                scheduleVoiceInstruction(transition);
                startPolling(180);"""
new_split_transition = """                broadcast(STATE_WAITING_SPLIT, transition);
                updateNotification(transition);
                scheduleVoiceInstruction(transition);
                enableVolumeStartTrigger();
                startPolling(180);"""
if old_split_transition not in service:
    raise SystemExit("v0.7.6: split transition block not found")
service = service.replace(old_split_transition, new_split_transition, 1)

# Tell the spoken split-grade prompt about VOL+ too.
old_prompt = """. Premi il pulsante fisico per iniziare il provino duro.";"""
new_prompt = """. Spegni lo schermo e premi volume più per iniziare il provino duro.";"""
if old_prompt not in service:
    raise SystemExit("v0.7.6: split prompt not found")
service = service.replace(old_prompt, new_prompt, 1)

# Add the screen-off VOL+ implementation just before polling helpers.
marker = """    private void startPolling(long initialDelayMs) {"""
if marker not in service:
    raise SystemExit("v0.7.6: startPolling marker not found")

methods = r'''
    // VOLUME_START_076
    // A short-lived active MediaSession routes hardware volume adjustments to this
    // foreground service. The session exists only while a provino phase is waiting
    // for its first user START, so normal phone volume behaviour returns immediately
    // after START/cancel/physical trigger.
    private void enableVolumeStartTrigger() {
        disableVolumeStartTrigger();
        if (mode != MODE_TEST || completing.get()) return;
        try {
            MediaSession session = new MediaSession(this, "DarkroomTimerVolumeStart");
            volumeStartSession = session;
            volumeStartArmed.set(true);

            PlaybackState playbackState = new PlaybackState.Builder()
                    .setActions(PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PLAY_PAUSE)
                    .setState(PlaybackState.STATE_PLAYING, 0L, 1.0f)
                    .build();
            session.setPlaybackState(playbackState);
            session.setPlaybackToRemote(new VolumeProvider(
                    VolumeProvider.VOLUME_CONTROL_RELATIVE, 100, 50) {
                @Override public void onAdjustVolume(int direction) {
                    if (direction > 0) requestVolumeStart();
                }
            });
            session.setActive(true);
            TechnicalLog.add(this, techSessionId, "START VOL+ ARMATO • valido anche a schermo spento");
        } catch (Exception e) {
            volumeStartArmed.set(false);
            releaseVolumeStartSession();
            TechnicalLog.add(this, techSessionId,
                    "ATTENZIONE START VOL+: MediaSession non disponibile — " + readable(e));
        }
    }

    private void requestVolumeStart() {
        if (mode != MODE_TEST || completing.get()) return;
        if (!volumeStartArmed.compareAndSet(true, false)) return;
        releaseVolumeStartSession();
        TechnicalLog.add(this, techSessionId, "START VOL+ RICEVUTO • primo impulso richiesto");
        io.execute(this::startProvinoExposureFromVolume);
    }

    private void startProvinoExposureFromVolume() {
        if (completing.get() || mode != MODE_TEST || seenOn.get()) return;
        try {
            cancelPoll();

            // Mirror the existing first-ON safelight behaviour before issuing ON.
            if (safelightAuto) {
                try {
                    if (testSplitFilterPauseSafelightOn) {
                        dimSafelightForExposure();
                        testSplitFilterPauseSafelightOn = false;
                        TechnicalLog.add(this, techSessionId,
                                "SPLIT PROVINO • SAFELIGHT OFF all'avvio VOL+ del provino duro; resta OFF tra le strisce");
                    } else if (!cycleSafelightCaptured) {
                        cycleSafelightCaptured = true;
                        restoreSafelightAfterCycle = true;
                        setSafelightConfirmed(false);
                        TechnicalLog.add(this, techSessionId,
                                "PROVINO — SAFELIGHT OFF prima dello START VOL+; resta OFF fino a fine provino");
                    }
                } catch (Exception e) {
                    TechnicalLog.add(this, techSessionId,
                            "ATTENZIONE SAFELIGHT: sincronizzazione START VOL+ non riuscita — " + readable(e));
                }
            }

            cancelVoiceRepeatsKeepSpeech();
            SonoffHttp.switchOn(device);
            long commandAcceptedOnAt = System.currentTimeMillis();

            // Same v0.7.5 local-Inching ownership used by automatic strips.
            lastObservedOnAt = commandAcceptedOnAt;
            lastConfirmedOffBeforeOnAt = 0L;
            seenOn.set(true);
            consecutivePrematureOffs = 0;
            consecutiveEarlyOffs = 0;
            TechnicalLog.add(this, techSessionId,
                    "COMANDO switch=on accettato da START VOL+ • esposizione " + (completed + 1) + "/" + count
                            + " • temporizzazione affidata a Inching locale");

            int current = completed + 1;
            String exposing = !testPreExposureDone
                    ? "ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA — " + seconds(testPreExposureMs)
                    : (TimingMath.isFStop(timingMethod)
                        ? "PROVINO " + current + "/" + count + " — fascia finale "
                            + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod))
                            + " · impulso " + seconds(currentPulseWidthMs)
                        : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));
            broadcast(STATE_EXPOSING, exposing);
            updateNotification(exposing);

            // Do not poll ON: the MINIR2's local Inching timer owns this pulse.
            startPolling(currentPulseWidthMs + 100L);
        } catch (Exception e) {
            fail("Avvio VOL+ non riuscito: " + readable(e));
        }
    }

    private void disableVolumeStartTrigger() {
        volumeStartArmed.set(false);
        releaseVolumeStartSession();
    }

    private void releaseVolumeStartSession() {
        MediaSession session = volumeStartSession;
        volumeStartSession = null;
        if (session == null) return;
        try { session.setActive(false); } catch (Exception ignored) {}
        try { session.release(); } catch (Exception ignored) {}
    }

'''
service = service.replace(marker, methods + marker, 1)

# Release interception on every exit path.
for old, new, label in [
    ("""        } else if (ACTION_CANCEL.equals(action)) {
            interlockActive = false;""",
     """        } else if (ACTION_CANCEL.equals(action)) {
            disableVolumeStartTrigger();
            interlockActive = false;""", "cancel"),
    ("""        } else if (ACTION_DISARM.equals(action)) {
            interlockActive = false;""",
     """        } else if (ACTION_DISARM.equals(action)) {
            disableVolumeStartTrigger();
            interlockActive = false;""", "disarm"),
    ("""    private void fail(String message) {
        TechnicalLog.add(this, techSessionId, "ERRORE — " + message);""",
     """    private void fail(String message) {
        disableVolumeStartTrigger();
        TechnicalLog.add(this, techSessionId, "ERRORE — " + message);""", "fail"),
    ("""    private void stopCleanly() {
        cancelTimers();""",
     """    private void stopCleanly() {
        disableVolumeStartTrigger();
        cancelTimers();""", "stop"),
    ("""    @Override public void onDestroy() {
        cancelTimers();""",
     """    @Override public void onDestroy() {
        disableVolumeStartTrigger();
        cancelTimers();""", "destroy"),
]:
    if old not in service:
        raise SystemExit("v0.7.6: exit block not found: " + label)
    service = service.replace(old, new, 1)

# Internal version.
if 'private static final String APP_VERSION = "0.13.18";' not in main:
    raise SystemExit("v0.7.6: expected Timer 0.13.18 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.18";',
    'private static final String APP_VERSION = "0.13.19";',
    1,
)

checks = [
    "VOLUME_START_076",
    "START VOL+ ARMATO",
    "START VOL+ RICEVUTO",
    "COMANDO switch=on accettato da START VOL+",
    "MediaSession volumeStartSession",
    "VolumeProvider.VOLUME_CONTROL_RELATIVE",
    "startPolling(currentPulseWidthMs + 100L);",
    "enableVolumeStartTrigger();",
    "disableVolumeStartTrigger();",
]
for needle in checks:
    if needle not in service:
        raise SystemExit("v0.7.6: missing " + needle)

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_start_076=APPLIED")
print("screen_off_start=VOL_PLUS")
print("volume_start_scope=PROVINO_USER_START_PHASES")
print("volume_repeat_guard=ONE_SHOT")
print("first_app_pulse_timing=MINIR2_LOCAL_INCHING")
print("physical_start_fallback=UNCHANGED")
print("timer_internal=0.13.19")
