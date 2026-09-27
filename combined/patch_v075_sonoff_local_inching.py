#!/usr/bin/env python3
"""Darkroom 0.7.5: let MINIR2 own automatic Inching pulses without ON polling.

0.7.4 anchored automatic exposure timing to the accepted switch=on command,
but still waited for /zeroconf/info to report ON before arming the OFF detector.
With a slow or jittery LAN, a complete 2 s pulse can start and finish while that
confirmation request is still in flight, producing false "ON not confirmed" or
premature-OFF failures.

For app-issued automatic provino steps:
- HTTP switch=on success is the start event;
- MINIR2 local Inching owns the actual 2 s timing;
- Darkroom does not poll during the pulse;
- polling resumes only after the requested pulse width has elapsed, to confirm
  that the relay is OFF before starting the user pause / next step.

The first exposure started by the physical button is unchanged.
"""
from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

old = '''                SonoffHttp.switchOn(device);
                // SONOFF_COMMAND_ANCHOR_074
                // The HTTP call returns only after the MINIR2 has accepted the ON.
                // Keep waiting for an observed ON before arming the OFF detector, but
                // use command acceptance as the timing reference. This avoids making
                // a correct local Inching pulse look short because ON confirmation
                // arrived late over the LAN.
                long commandAcceptedOnAt = System.currentTimeMillis();
                TechnicalLog.add(this, techSessionId, "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count);
                long confirmedOnAt = waitForConfirmedSwitchOn();

                if (completing.get()) return;
                lastObservedOnAt = commandAcceptedOnAt;
                long confirmDelay = Math.max(0L, confirmedOnAt - commandAcceptedOnAt);
                if (lastObservedOffAt > 0) {
                    TechnicalLog.add(this, techSessionId,
                            "OSSERVATO switch=ON confermato • ritardo conferma " + secondsLong(confirmDelay)
                                    + " • pausa comando via rete " + secondsLong(commandAcceptedOnAt - lastObservedOffAt));
                } else {
                    TechnicalLog.add(this, techSessionId,
                            "OSSERVATO switch=ON confermato • ritardo conferma " + secondsLong(confirmDelay));
                }
                seenOn.set(true);
                int current = completed + 1;
                String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);
                broadcast(STATE_EXPOSING, exposing);
                updateNotification(exposing);
                startPolling(120);
'''

new = '''                SonoffHttp.switchOn(device);
                // SONOFF_LOCAL_INCHING_075
                // A successful switch=on response means the MINIR2 accepted the
                // command. The relay duration is then owned locally by Inching.
                // Do not chase an ON state over the LAN: on a slow request a whole
                // short pulse can begin and end before /zeroconf/info returns.
                long commandAcceptedOnAt = System.currentTimeMillis();
                lastObservedOnAt = commandAcceptedOnAt;
                seenOn.set(true);
                TechnicalLog.add(this, techSessionId,
                        "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count
                                + " • temporizzazione affidata a Inching locale");
                if (lastObservedOffAt > 0) {
                    TechnicalLog.add(this, techSessionId,
                            "PAUSA comando via rete • " + secondsLong(commandAcceptedOnAt - lastObservedOffAt));
                }

                int current = completed + 1;
                String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);
                broadcast(STATE_EXPOSING, exposing);
                updateNotification(exposing);

                // Resume state polling only after the locally-timed pulse should have
                // finished. This prevents slow /zeroconf/info round-trips from creating
                // false premature-OFF or missed-ON failures.
                startPolling(currentPulseWidthMs + 100L);
'''

if old not in service:
    raise SystemExit("v0.7.5: expected v0.7.4 automatic exposure block not found")
service = service.replace(old, new, 1)

if 'private static final String APP_VERSION = "0.13.17";' not in main:
    raise SystemExit("v0.7.5: expected Timer 0.13.17 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.17";',
    'private static final String APP_VERSION = "0.13.18";',
    1,
)

checks = [
    "SONOFF_LOCAL_INCHING_075",
    "temporizzazione affidata a Inching locale",
    "startPolling(currentPulseWidthMs + 100L);",
    "lastObservedOnAt = commandAcceptedOnAt;",
]
for needle in checks:
    if needle not in service:
        raise SystemExit("v0.7.5: missing " + needle)

# Automatic steps must no longer wait for an ON confirmation.
auto_start = service.index("SONOFF_LOCAL_INCHING_075")
auto_end = service.index("private void persistCompletedCycle", auto_start)
auto_block = service[auto_start:auto_end]
if "long confirmedOnAt = waitForConfirmedSwitchOn();" in auto_block:
    raise SystemExit("v0.7.5: automatic path still calls ON confirmation")

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("sonoff_local_inching_075=APPLIED")
print("automatic_on_confirmation=NOT_REQUIRED")
print("automatic_pulse_timing=MINIR2_LOCAL_INCHING")
print("automatic_polling=AFTER_REQUESTED_WIDTH")
print("physical_button_flow=UNCHANGED")
print("timer_internal=0.13.18")
