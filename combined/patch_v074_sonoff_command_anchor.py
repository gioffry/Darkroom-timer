#!/usr/bin/env python3
"""Darkroom 0.7.4: anchor automatic SONOFF exposure timing to accepted ON command.

The MINIR2 owns the Inching duration locally. For automatic test-strip steps,
Darkroom used to measure the exposure from the later /zeroconf/info ON
confirmation. On a slow LAN/API round-trip that makes a correct 2.0 s pulse
look artificially short (for example 1.8 s) and can trigger a false
"RELÈ OFF PREMATURO" abort.

For app-issued ON commands, the accepted switch command is a conservative
lower bound for the real relay start: the device has processed ON before the
HTTP call returns. We still require an ON confirmation before arming the OFF
detector, but premature-OFF plausibility is measured from command acceptance.
Physical-button exposures keep the existing observed-ON timing path.
"""
from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
SERVICE = ROOT / "SonoffArmService.java"
MAIN = ROOT / "MainActivity.java"

service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

old = '''                SonoffHttp.switchOn(device);
                TechnicalLog.add(this, techSessionId, "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count);
                long confirmedOnAt = waitForConfirmedSwitchOn();

                if (completing.get()) return;
                lastObservedOnAt = confirmedOnAt;
                if (lastObservedOffAt > 0) {
                    TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON confermato • pausa osservata via rete " + secondsLong(confirmedOnAt - lastObservedOffAt));
                } else {
                    TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON confermato");
                }
'''

new = '''                SonoffHttp.switchOn(device);
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
'''

if old not in service:
    raise SystemExit("v0.7.4: automatic SONOFF ON timing block not found")
service = service.replace(old, new, 1)

if 'private static final String APP_VERSION = "0.13.16";' not in main:
    raise SystemExit("v0.7.4: expected Timer 0.13.16 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.16";',
    'private static final String APP_VERSION = "0.13.17";',
    1,
)

if "SONOFF_COMMAND_ANCHOR_074" not in service:
    raise SystemExit("v0.7.4: SONOFF command anchor marker missing")
if "lastObservedOnAt = commandAcceptedOnAt;" not in service:
    raise SystemExit("v0.7.4: command acceptance timing reference missing")
if "lastObservedOnAt = confirmedOnAt;" in service:
    raise SystemExit("v0.7.4: old confirmed-ON timing reference still present")

SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("sonoff_command_anchor_074=APPLIED")
print("automatic_exposure_reference=SWITCH_ON_COMMAND_ACCEPTED")
print("on_confirmation=STILL_REQUIRED_BEFORE_OFF_DETECTOR")
print("physical_button_reference=UNCHANGED")
print("timer_internal=0.13.17")
