#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.10.5 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.5 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.5 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.5 OK',label,flush=True)

# Versione 0.10.5 / code 50
rep(build, 'VERSION_NAME = "0.10.4"', 'VERSION_NAME = "0.10.5"', 'version name build')
rep(build, 'VERSION_CODE = "49"', 'VERSION_CODE = "50"', 'version code build')
rep(build, '[Darkroom v0.10.4]', '[Darkroom v0.10.5]', 'build log tag')
rep(build, r'versionCode\s+49\b', r'versionCode\s+50\b', 'preflight code regex')
rep(build, r'0\.10\.4', r'0\.10\.5', 'preflight name regex')
rep(build, 'versionCode 49 / versionName 0.10.4', 'versionCode 50 / versionName 0.10.5', 'preflight message')
rep(build, 'Preflight v0.10.4 OK', 'Preflight v0.10.5 OK', 'preflight log')
rep(gradle, "versionCode 49\n        versionName '0.10.4'", "versionCode 50\n        versionName '0.10.5'", 'gradle version')
rep(manifest, 'android:versionCode="49"\n    android:versionName="0.10.4"', 'android:versionCode="50"\n    android:versionName="0.10.5"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.4";', 'private static final String APP_VERSION = "0.10.5";', 'UI version')

# FAIL-SAFE: un OFF prematuro non viene più ignorato.
# Un singolo campione OFF anticipato viene confermato; due OFF anticipati consecutivi
# interrompono il ciclo, lasciano il relè OFF, disattivano l'Inching e ripristinano la safelight.
early_pattern = r'''                long minimumCredibleMs = Math\.max\(250L, currentPulseWidthMs - 50L\);\n                if \(observed > 0 && observed < minimumCredibleMs\) \{\n                    TechnicalLog\.add\(this, techSessionId,\n                            "IGNORATO switch=OFF anticipato • " \+ secondsLong\(observed\)\n                                    \+ " < gate " \+ secondsLong\(minimumCredibleMs\)\n                                    \+ " • Inching lasciato al MINIR2"\);\n                    consecutiveEarlyOffs = 0;\n                    return;\n                \}'''
early_repl = '''                long minimumCredibleMs = Math.max(250L, currentPulseWidthMs - 50L);
                if (observed > 0 && observed < minimumCredibleMs) {
                    consecutiveEarlyOffs++;
                    final int earlyOffConfirmations = 2;
                    TechnicalLog.add(this, techSessionId,
                            "OFF PREMATURO • conferma " + consecutiveEarlyOffs + "/" + earlyOffConfirmations
                                    + " • " + secondsLong(observed)
                                    + " < gate " + secondsLong(minimumCredibleMs));
                    if (consecutiveEarlyOffs < earlyOffConfirmations) return;
                    fail("ESPOSIZIONE ABORTITA — RELÈ OFF PREMATURO • "
                            + secondsLong(observed) + " su " + secondsLong(currentPulseWidthMs));
                    return;
                }'''
rrep(service, early_pattern, early_repl, 'early OFF abort fail-safe')

checks = {
    build:['VERSION_NAME = "0.10.5"','VERSION_CODE = "50"'],
    main:['private static final String APP_VERSION = "0.10.5"'],
    service:['final int earlyOffConfirmations = 2;',
             'OFF PREMATURO • conferma ',
             'ESPOSIZIONE ABORTITA — RELÈ OFF PREMATURO',
             'currentPulseWidthMs - 50L']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.5 verifica fallita: {needle} in {p}')
if 'IGNORATO switch=OFF anticipato' in rd(service):
    raise SystemExit('v0.10.5 verifica fallita: vecchia logica IGNORATO OFF anticipato ancora presente')
print('v0.10.5 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
