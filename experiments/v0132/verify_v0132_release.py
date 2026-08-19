#!/usr/bin/env python3
from pathlib import Path
import sys

work=Path(sys.argv[1]); root=work/'project/app/src/main'; java=root/'java/it/darkroom/timer'
main=java/'MainActivity.java'; timing=java/'TimingMath.java'; service=java/'SonoffArmService.java'; manifest=root/'AndroidManifest.xml'; logentry=java/'LogEntry.java'; logstore=java/'LogStore.java'

def text(p): return p.read_text(encoding='utf-8')

def need(p, needle, label):
    if needle not in text(p): raise SystemExit('FAIL '+label+': '+needle)
    print('PASS '+label)

need(manifest,'android:versionName="0.13.2"','versionName')
need(manifest,'android:versionCode="63"','versionCode')
need(main,'private static final String APP_VERSION = "0.13.2";','footer version')
need(timing,'MASK_REVEAL = "SCOPRIRE"','SCOPRIRE constant')
need(timing,'MASK_COVER = "COPRIRE"','COPRIRE constant')
need(timing,'testStripPulses','shared pulse plan')
need(timing,'physicalTargets','physical target mapping')
need(main,'METODO PROVINO ·','masking selector')
need(main,'physicalStrips','preferred-strip physical mapping')
need(main,'.putString("printSequence", "")','stale print plan reset')
need(main,'postDelayed(this::maybeShowTestResultChooser, 450L)','chooser retry')
need(service,'EXTRA_TEST_MASKING_METHOD','service masking input')
need(service,'lastTestStripMethod','service masking persistence')
need(service,'scheduleSafelightRestoreRetry','safelight retry watchdog')
need(service,'ON non ancora confermato','safelight pending diagnostic')
need(logentry,'testStripMethod = TimingMath.MASK_REVEAL','log masking field')
need(logstore,'normalizeMaskingMethod(e.testStripMethod)','log masking serialization')

mt=text(main)
if 'testFromPrint' in mt or 'NUOVO PROVINO DA QUESTA STAMPA' in mt: raise SystemExit('FAIL STAMPA->PROVINO regression')
for p in root.rglob('*'):
    if p.is_file() and p.suffix in ('.java','.xml'):
        low=text(p).lower()
        if 'it.darkroom.timer.assistant' in low or 'smart search' in low or 'sviluppo & chimica' in low:
            raise SystemExit('FAIL Assistant residue: '+str(p))
print('PASS Timer-only / no Assistant residue')
print('ALL v0.13.2 RELEASE GUARDS PASS')
