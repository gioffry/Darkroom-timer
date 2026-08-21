#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
java = root / 'src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.2.7 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.2.7 OK', label, flush=True)

# Exact v0.2.6 / Timer 0.13.9 baseline. This patch is intentionally tiny.
for p, needle in [
    (main, 'private static final String APP_VERSION = "0.13.9";'),
    (service, 'private volatile boolean testPreExposureDone = true;'),
    (service, 'private void temporarilyRestoreSafelightForPause() throws Exception'),
    (service, 'private void dimSafelightForExposure() throws Exception'),
    (service, 'if (mode == MODE_TEST && testPreExposureMs > 0 && !testPreExposureDone)'),
]:
    if needle not in rd(p):
        raise SystemExit('v0.2.7 base v0.2.6 non riconosciuta: ' + needle)

# Timer internal patch version.
rep(main,
    'private static final String APP_VERSION = "0.13.9";',
    'private static final String APP_VERSION = "0.13.10";',
    'Timer footer version')

# Remember the one special Split-Grade pause in which the safelight has been
# deliberately restored for the filter change. Ordinary test-strip pauses remain
# untouched and keep the red light OFF.
rep(service,
'''    private volatile boolean testPreExposureDone = true;\n    private volatile boolean printBaseDone = false;\n''',
'''    private volatile boolean testPreExposureDone = true;\n    private volatile boolean testSplitFilterPauseSafelightOn = false;\n    private volatile boolean printBaseDone = false;\n''',
    'Split provino safelight pause state')

rep(service,
'''            testPreExposureDone = testPreExposureMs <= 0;\n            printBaseDone = false;\n''',
'''            testPreExposureDone = testPreExposureMs <= 0;\n            testSplitFilterPauseSafelightOn = false;\n            printBaseDone = false;\n''',
    'reset Split provino safelight pause state')

# When the whole-strip soft pre-exposure is complete, temporarily restore the
# safelight exactly like the already-approved PRINT Split transition. The user can
# now see the colour head while zeroing Y and setting M.
rep(service,
'''        if (mode == MODE_TEST && testPreExposureMs > 0 && !testPreExposureDone) {\n            testPreExposureDone = true;\n            cancelPoll();\n            try {\n                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;\n                configurePulseVerified(currentPulseWidthMs);\n                TechnicalLog.add(this, techSessionId, "SPLIT PROVINO • base morbida completata • attesa cambio filtro • prossimo impulso duro " + seconds(currentPulseWidthMs));\n                String transition = testHardTransitionPrompt();\n''',
'''        if (mode == MODE_TEST && testPreExposureMs > 0 && !testPreExposureDone) {\n            testPreExposureDone = true;\n            cancelPoll();\n            try {\n                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;\n                configurePulseVerified(currentPulseWidthMs);\n                boolean canRestoreForFilterChange = safelightAuto && cycleSafelightCaptured && restoreSafelightAfterCycle;\n                temporarilyRestoreSafelightForPause();\n                testSplitFilterPauseSafelightOn = canRestoreForFilterChange;\n                if (testSplitFilterPauseSafelightOn) {\n                    TechnicalLog.add(this, techSessionId, "SPLIT PROVINO • SAFELIGHT ON per cambio filtro morbido → duro");\n                }\n                TechnicalLog.add(this, techSessionId, "SPLIT PROVINO • base morbida completata • attesa cambio filtro • prossimo impulso duro " + seconds(currentPulseWidthMs));\n                String transition = testHardTransitionPrompt();\n''',
    'safelight ON during Split provino filter change')

# At the first hard exposure only, switch the safelight back OFF. After that the
# normal PROVINO rule resumes: it stays OFF through every hard strip and every
# inter-strip pause, then returns ON only when the whole provino finishes.
rep(service,
'''                        try {\n                            if (mode == MODE_TEST && !cycleSafelightCaptured) {\n                                // Il provino è un unico ciclo operativo: rossa OFF dalla prima\n                                // esposizione fino all'ultima, senza lampeggiare durante le pause.\n                                cycleSafelightCaptured = true;\n                                restoreSafelightAfterCycle = true;\n                                setSafelightConfirmed(false);\n                                TechnicalLog.add(this, techSessionId, "PROVINO — SAFELIGHT OFF dalla prima striscia fino a fine provino");\n                            } else if (mode == MODE_PRINT && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) {\n''',
'''                        try {\n                            if (mode == MODE_TEST && testSplitFilterPauseSafelightOn) {\n                                dimSafelightForExposure();\n                                testSplitFilterPauseSafelightOn = false;\n                                TechnicalLog.add(this, techSessionId, "SPLIT PROVINO • SAFELIGHT OFF all'avvio del provino duro; resta OFF tra le strisce");\n                            } else if (mode == MODE_TEST && !cycleSafelightCaptured) {\n                                // Il provino è un unico ciclo operativo: rossa OFF dalla prima\n                                // esposizione fino all'ultima, senza lampeggiare durante le pause.\n                                cycleSafelightCaptured = true;\n                                restoreSafelightAfterCycle = true;\n                                setSafelightConfirmed(false);\n                                TechnicalLog.add(this, techSessionId, "PROVINO — SAFELIGHT OFF dalla prima striscia fino a fine provino");\n                            } else if (mode == MODE_PRINT && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) {\n''',
    'safelight OFF again at first hard Split strip')

# Hard acceptance guards: no timing, strip sequence or voice logic is rewritten.
mt = rd(main)
sv = rd(service)
for needle in [
    'private static final String APP_VERSION = "0.13.10";',
]:
    if needle not in mt:
        raise SystemExit('v0.2.7 Main guard missing: ' + needle)
for needle in [
    'testSplitFilterPauseSafelightOn',
    'temporarilyRestoreSafelightForPause();',
    'SPLIT PROVINO • SAFELIGHT ON per cambio filtro morbido → duro',
    'dimSafelightForExposure();',
    "SPLIT PROVINO • SAFELIGHT OFF all'avvio del provino duro; resta OFF tra le strisce",
    'TimingMath.testStripPulses(testTargetsMs, testStripMethod)',
    'Esposizione uno di due',
    'Esposizione due di due',
    'voiceSeconds(printSequence.split.softMs)',
    'voiceSeconds(printSequence.split.hardMs)',
]:
    if needle not in sv:
        raise SystemExit('v0.2.7 Service guard missing: ' + needle)
if 'cyan' in sv.lower() or 'ciano' in sv.lower():
    raise SystemExit('v0.2.7 regression: cyan/ciano voice reference reappeared')
print('v0.2.7 TRANSFORM OK — safelight ON only at Split provino filter change, OFF again for hard strips', flush=True)
