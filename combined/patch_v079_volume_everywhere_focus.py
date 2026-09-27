#!/usr/bin/env python3
"""Darkroom 0.7.9: VOL+ everywhere, VOL- for focus.

Goals:
- VOL+ starts every user-triggered exposure phase handled by SonoffArmService:
  normal print, test strip, split-grade phases, and burn steps.
- VOL- toggles the enlarger relay for focusing while Timer is in the foreground
  and no cycle is armed.
- Existing physical S1/S2 remains a fallback, but is no longer required for
  normal operation.

Safety:
- VOL- focus is disabled while armed.
- Focus explicitly disables Inching before turning the relay on.
- Exposure timing remains owned by MINIR2 local Inching.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# ---------- SonoffArmService: VOL+ everywhere ----------

# All armed entry points should present VOL+ as the primary trigger.
service = service.replace("premi il pulsante fisico una volta", "premi VOL+")
service = service.replace("premi il pulsante fisico", "premi VOL+")
service = service.replace("Premi il pulsante.", "Premi volume più.")

old = "            if (mode == MODE_TEST) enableVolumeStartTrigger();"
if old not in service:
    raise SystemExit("v0.7.9: v0.7.8 initial test-only volume arming not found")
service = service.replace(old, "            enableVolumeStartTrigger();", 1)

# Enable the media session for both PRINT and TEST.
old = "        if (mode != MODE_TEST || completing.get()) return;"
count = service.count(old)
if count < 2:
    raise SystemExit(f"v0.7.9: expected >=2 MODE_TEST volume guards, found {count}")
service = service.replace(old, "        if (completing.get()) return;")

old = "        if (completing.get() || mode != MODE_TEST || seenOn.get()) return;"
if old not in service:
    raise SystemExit("v0.7.9: test-only start method guard not found")
service = service.replace(old, "        if (completing.get() || seenOn.get()) return;", 1)

# Generalize the safelight behavior inside app-triggered START so PRINT follows
# the same logic as the existing physical-start path.
old_safelight = '''            // Mirror the existing first-ON safelight behaviour before issuing ON.
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
            }'''
new_safelight = '''            // Mirror the existing physical-start safelight behaviour.
            if (safelightAuto) {
                try {
                    if (mode == MODE_TEST && testSplitFilterPauseSafelightOn) {
                        dimSafelightForExposure();
                        testSplitFilterPauseSafelightOn = false;
                        TechnicalLog.add(this, techSessionId,
                                "SPLIT PROVINO • SAFELIGHT OFF all'avvio VOL+ del provino duro; resta OFF tra le strisce");
                    } else if (mode == MODE_TEST && !cycleSafelightCaptured) {
                        cycleSafelightCaptured = true;
                        restoreSafelightAfterCycle = true;
                        setSafelightConfirmed(false);
                        TechnicalLog.add(this, techSessionId,
                                "PROVINO — SAFELIGHT OFF prima dello START VOL+; resta OFF fino a fine provino");
                    } else if (mode == MODE_PRINT
                            && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) {
                        dimSafelightForExposure();
                    } else if (!cycleSafelightCaptured) {
                        captureAndDimSafelightForCycle();
                    }
                } catch (Exception e) {
                    TechnicalLog.add(this, techSessionId,
                            "ATTENZIONE SAFELIGHT: sincronizzazione START VOL+ non riuscita — " + readable(e));
                }
            }'''
if old_safelight not in service:
    raise SystemExit("v0.7.9: v0.7.8 VOL+ safelight block not found")
service = service.replace(old_safelight, new_safelight, 1)

# Generalize exposure message + dodge cue scheduling after VOL+.
old_after = '''            TechnicalLog.add(this, techSessionId,
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
            updateNotification(exposing);'''
new_after = '''            String startLabel = mode == MODE_PRINT
                    ? "STAMPA"
                    : "esposizione " + (completed + 1) + "/" + count;
            TechnicalLog.add(this, techSessionId,
                    "COMANDO switch=on accettato da START VOL+ • " + startLabel
                            + " • temporizzazione affidata a Inching locale");

            if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) {
                scheduleDodgeCues(commandAcceptedOnAt);
            }

            int current = completed + 1;
            String exposing = mode == MODE_PRINT
                    ? printExposureMessage()
                    : (!testPreExposureDone
                        ? "ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA — " + seconds(testPreExposureMs)
                        : (TimingMath.isFStop(timingMethod)
                            ? "PROVINO DURO " + current + "/" + count + " — fascia finale "
                                + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod))
                                + " · impulso " + seconds(currentPulseWidthMs)
                            : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs)));
            broadcast(STATE_EXPOSING, exposing);
            updateNotification(exposing);'''
if old_after not in service:
    raise SystemExit("v0.7.9: v0.7.8 VOL+ post-start block not found")
service = service.replace(old_after, new_after, 1)

# Every manual continuation in PRINT must re-arm VOL+.
old = '''            seenOn.set(false);
            scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_HARD));
            startPolling(250);'''
new = '''            seenOn.set(false);
            scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_HARD));
            enableVolumeStartTrigger();
            startPolling(250);'''
if old not in service:
    raise SystemExit("v0.7.9: print split continuation not found")
service = service.replace(old, new, 1)

old = '''            seenOn.set(false);
            String voice = "Bruciatura " + burn.safeLabel() + ". "
                    + (filter.isEmpty() ? "" : filter + ". ")
                    + "Prepara la maschera. Premi volume più.";
            scheduleVoiceInstruction(voice);
            startPolling(250);'''
new = '''            seenOn.set(false);
            String voice = "Bruciatura " + burn.safeLabel() + ". "
                    + (filter.isEmpty() ? "" : filter + ". ")
                    + "Prepara la maschera. Premi volume più.";
            scheduleVoiceInstruction(voice);
            enableVolumeStartTrigger();
            startPolling(250);'''
if old not in service:
    raise SystemExit("v0.7.9: burn continuation not found")
service = service.replace(old, new, 1)

# Clean diagnostic label inherited from 0.7.7.
service = service.replace(
    "START VOL+ ARMATO 0.7.7 • adjust+absolute • valido anche a schermo spento",
    "START VOL+ ARMATO 0.7.9 • tutte le esposizioni • valido anche a schermo spento"
)

# ---------- MainActivity: VOL- focus toggle while idle ----------

old_import = "import android.view.Gravity;\nimport android.view.Window;"
new_import = "import android.view.Gravity;\nimport android.view.KeyEvent;\nimport android.view.Window;"
if old_import not in main:
    raise SystemExit("v0.7.9: MainActivity view imports not found")
main = main.replace(old_import, new_import, 1)

old_field = '''    private final AtomicBoolean validationInFlight = new AtomicBoolean(false);
    private final AtomicBoolean healthCheckInFlight = new AtomicBoolean(false);'''
new_field = '''    private final AtomicBoolean validationInFlight = new AtomicBoolean(false);
    private final AtomicBoolean healthCheckInFlight = new AtomicBoolean(false);
    private final AtomicBoolean focusCommandInFlight = new AtomicBoolean(false);'''
if old_field not in main:
    raise SystemExit("v0.7.9: MainActivity atomic fields not found")
main = main.replace(old_field, new_field, 1)

marker = "    @Override protected void onStop() {"
if marker not in main:
    raise SystemExit("v0.7.9: MainActivity onStop marker not found")

focus_methods = r'''
    // VOLUME_CONTROLS_079
    // While the Timer screen is in the foreground and no cycle is armed,
    // VOL- becomes a simple FOCUS toggle. The key is deliberately NOT active
    // while armed; at that point the MediaSession owns hardware volume keys and
    // VOL+ is the exposure START.
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        if (event != null
                && event.getKeyCode() == KeyEvent.KEYCODE_VOLUME_DOWN
                && !armed
                && mode != MODE_LOG) {
            if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                toggleFocusFromVolume();
            }
            // Consume DOWN + UP so Android does not also change media volume.
            return true;
        }
        return super.dispatchKeyEvent(event);
    }

    private void toggleFocusFromVolume() {
        if (armed || mode == MODE_LOG) return;
        DeviceConfig d = (device != null && device.isValid()) ? device : DeviceConfig.load(this);
        if (d == null || !d.isValid()) {
            setStatusPresentation("FOCUS", "SONOFF ingranditore non disponibile", darkroomMode ? RED : AMBER);
            return;
        }
        if (!focusCommandInFlight.compareAndSet(false, true)) return;

        io.execute(() -> {
            try {
                String before = SonoffHttp.infoQuick(d, 1800);
                final boolean turnOn = !"on".equals(before);

                if (turnOn) {
                    // FOCUS must be continuous, never locally timed.
                    SonoffHttp.pulseOff(d);
                    SonoffHttp.switchOn(d);
                } else {
                    SonoffHttp.switchOff(d);
                }

                String expected = turnOn ? "on" : "off";
                String observed = "";
                for (int attempt = 0; attempt < 4; attempt++) {
                    observed = SonoffHttp.infoQuick(d, 1800);
                    if (expected.equals(observed)) break;
                    try { Thread.sleep(120L); } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
                final boolean confirmed = expected.equals(observed);
                runOnUiThread(() -> {
                    if (armed) return;
                    if (!confirmed) {
                        setStatusPresentation("FOCUS", "Comando non confermato dal MINIR2", darkroomMode ? RED : AMBER);
                    } else if (turnOn) {
                        setStatusPresentation("FOCUS", "INGRANDITORE ON • VOL− per spegnere", darkroomMode ? RED : BLUE);
                    } else {
                        setStatusPresentation("PRONTO", "INGRANDITORE OFF • VOL− per fuoco", GREEN);
                    }
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    if (!armed) setStatusPresentation("FOCUS", "MINIR2 non raggiungibile", darkroomMode ? RED : AMBER);
                });
            } finally {
                focusCommandInFlight.set(false);
            }
        });
    }

'''
main = main.replace(marker, focus_methods + marker, 1)

# Internal version.
if 'private static final String APP_VERSION = "0.13.21";' not in main:
    raise SystemExit("v0.7.9: expected Timer 0.13.21 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.21";',
    'private static final String APP_VERSION = "0.13.22";',
    1,
)

checks_service = [
    "START VOL+ ARMATO 0.7.9",
    "enableVolumeStartTrigger();",
    "String startLabel = mode == MODE_PRINT",
    "scheduleDodgeCues(commandAcceptedOnAt)",
    "printExposureMessage()",
]
for needle in checks_service:
    if needle not in service:
        raise SystemExit("v0.7.9: missing service marker " + needle)

checks_main = [
    "VOLUME_CONTROLS_079",
    "KEYCODE_VOLUME_DOWN",
    "toggleFocusFromVolume",
    "SonoffHttp.pulseOff(d)",
    "SonoffHttp.switchOn(d)",
    "SonoffHttp.switchOff(d)",
]
for needle in checks_main:
    if needle not in main:
        raise SystemExit("v0.7.9: missing MainActivity marker " + needle)

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("volume_controls_079=APPLIED")
print("vol_plus=ALL_USER_TRIGGERED_EXPOSURES")
print("vol_minus=FOCUS_TOGGLE_WHEN_IDLE")
print("focus_inching=FORCED_OFF_BEFORE_ON")
print("screen_off_vol_plus=KEPT")
print("physical_switch=FALLBACK_ONLY")
print("timer_internal=0.13.22")
