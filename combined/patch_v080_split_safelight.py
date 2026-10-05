#!/usr/bin/env python3
from pathlib import Path

SERVICE = Path("combined/src/main/java/it/darkroom/timer/SonoffArmService.java")
text = SERVICE.read_text(encoding="utf-8")

MARKER = "SPLIT_SAFELIGHT_080"
if MARKER in text:
    print("v080_split_safelight_already_applied=PASS")
    raise SystemExit(0)

old_test = """                boolean canRestoreForFilterChange = safelightAuto && cycleSafelightCaptured && restoreSafelightAfterCycle;
                temporarilyRestoreSafelightForPause();
                testSplitFilterPauseSafelightOn = canRestoreForFilterChange;
"""
new_test = """                testSplitFilterPauseSafelightOn = enableSafelightForSplitFilterChange("provino: cambio morbido -> duro");
"""
if text.count(old_test) != 1:
    raise SystemExit("v0.8: split-provino transition anchor not found exactly once")
text = text.replace(old_test, new_test, 1)

old_print = """        try {
            temporarilyRestoreSafelightForPause();
            currentPulseWidthMs = printSequence.split.hardMs;
"""
new_print = """        try {
            enableSafelightForSplitFilterChange("stampa: cambio giallo -> magenta");
            currentPulseWidthMs = printSequence.split.hardMs;
"""
if text.count(old_print) != 1:
    raise SystemExit("v0.8: split-print transition anchor not found exactly once")
text = text.replace(old_print, new_print, 1)

anchor = """    private void dimSafelightForExposure() throws Exception {
"""
helper = """    private boolean enableSafelightForSplitFilterChange(String context) throws Exception {
        if (!safelightAuto) return false;
        if (safelight == null || !safelight.isValid()) throw new Exception("SONOFF safelight non configurato");
        if (device != null && device.isValid() && safelight.deviceId.equals(device.deviceId)) {
            throw new Exception("il SONOFF safelight coincide con l’ingranditore");
        }

        // SPLIT_SAFELIGHT_080: WAITING_SPLIT is an enlarger-OFF interval.
        // With automatic safelight enabled, make the CMY dials readable even if
        // the earlier cycle-state capture was missed or stale.
        setSafelightConfirmed(true);
        cycleSafelightCaptured = true;
        restoreSafelightAfterCycle = true;
        TechnicalLog.add(this, techSessionId, "SPLIT_SAFELIGHT_080 • SAFELIGHT ON • " + context);
        return true;
    }

"""
if text.count(anchor) != 1:
    raise SystemExit("v0.8: safelight helper insertion anchor not found exactly once")
text = text.replace(anchor, helper + anchor, 1)

assert MARKER in text
assert 'testSplitFilterPauseSafelightOn = enableSafelightForSplitFilterChange("provino: cambio morbido -> duro")' in text
assert 'enableSafelightForSplitFilterChange("stampa: cambio giallo -> magenta")' in text
assert 'dimSafelightForExposure();' in text
assert 'setSafelightConfirmed(false);' in text

SERVICE.write_text(text, encoding="utf-8")
print("v080_split_safelight=PASS")
print("split_waiting_safelight=FORCED_ON_WHEN_AUTO_ENABLED")
print("split_next_exposure_safelight=OFF_VIA_EXISTING_INTERLOCK")
