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

# Contatore separato: serve solo a confermare che un OFF prematuro sia reale,
# senza interferire con le conferme di fine esposizione della v0.10.3/0.10.4.
s = rd(service)
field = '    private volatile int consecutivePrematureOffs = 0;\n'
if field not in s:
    anchor = '    private volatile int consecutiveEarlyOffs = 0;\n'
    if anchor in s:
        s = s.replace(anchor, anchor + field, 1)
    else:
        anchor = '    private volatile long lastObservedOffAt = 0L;\n'
        if anchor not in s: raise SystemExit('v0.10.5 campo contatore: anchor non trovato')
        s = s.replace(anchor, anchor + field, 1)
    wr(service, s)
print('v0.10.5 OK contatore OFF prematuro', flush=True)

# Una nuova lettura ON azzera il sospetto: per abortire servono due OFF prematuri consecutivi.
rep(service,
'''            String sw = status.switchState;\n            long observedAt = status.midpointAt();\n            if ("on".equals(sw)) {''',
'''            String sw = status.switchState;\n            long observedAt = status.midpointAt();\n            if ("on".equals(sw)) {\n                consecutivePrematureOffs = 0;''',
    'reset prematuro su ON')

# Fail-safe: la rete non decide la durata, ma se il MINIR2 riporta OFF prematuro
# due volte di seguito non possiamo fingere che l'esposizione sia ancora valida.
# Si abortisce il piano; fail() spegne uscita, disattiva Inching, ripristina safelight
# e porta la UI in errore/RIPROVA. Nessuna riaccensione o compensazione.
pattern = r'''                long minimumCredibleMs = Math\.max\(250L, currentPulseWidthMs - 50L\);.*?                int neededOffConfirmations = currentPulseWidthMs <= 3000 \? 2 : 1;.*?                consecutiveEarlyOffs = 0;'''
replacement = '''                long minimumCredibleMs = Math.max(250L, currentPulseWidthMs - 50L);
                if (observed > 0 && observed < minimumCredibleMs) {
                    consecutiveEarlyOffs = 0;
                    consecutivePrematureOffs++;
                    final int neededPrematureConfirmations = 2;
                    if (consecutivePrematureOffs < neededPrematureConfirmations) {
                        TechnicalLog.add(this, techSessionId,
                                "OFF PREMATURO sospetto • conferma " + consecutivePrematureOffs + "/" + neededPrematureConfirmations
                                        + " • " + secondsLong(observed) + " < attesi " + seconds(currentPulseWidthMs));
                        return;
                    }
                    TechnicalLog.add(this, techSessionId,
                            "ESPOSIZIONE ABORTITA — RELÈ OFF PREMATURO • osservato " + secondsLong(observed)
                                    + " • richiesti " + seconds(currentPulseWidthMs));
                    seenOn.set(false);
                    consecutivePrematureOffs = 0;
                    fail("ESPOSIZIONE ABORTITA — RELÈ OFF PREMATURO (" + secondsLong(observed)
                            + " su " + seconds(currentPulseWidthMs) + ")");
                    return;
                }

                consecutivePrematureOffs = 0;
                int neededOffConfirmations = currentPulseWidthMs <= 3000 ? 2 : 1;
                consecutiveEarlyOffs++;
                if (consecutiveEarlyOffs < neededOffConfirmations) {
                    TechnicalLog.add(this, techSessionId,
                            "OFF credibile • conferma " + consecutiveEarlyOffs + "/" + neededOffConfirmations
                                    + " • " + secondsLong(observed));
                    return;
                }
                consecutiveEarlyOffs = 0;'''
rrep(service, pattern, replacement, 'fail-safe OFF prematuro')

# Reset esplicito a ogni armamento, oltre al reset su ON.
rep(service,
'''            completed = 0;\n            seenOn.set(false);\n            completing.set(false);''',
'''            completed = 0;\n            seenOn.set(false);\n            consecutivePrematureOffs = 0;\n            completing.set(false);''',
    'reset prematuro in armamento')

checks = {
    build:['VERSION_NAME = "0.10.5"','VERSION_CODE = "50"'],
    main:['private static final String APP_VERSION = "0.10.5"'],
    service:['consecutivePrematureOffs','neededPrematureConfirmations = 2','OFF PREMATURO sospetto','ESPOSIZIONE ABORTITA — RELÈ OFF PREMATURO','neededOffConfirmations = currentPulseWidthMs <= 3000 ? 2 : 1']
}
for p, needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.5 verifica fallita: {needle} in {p}')
print('v0.10.5 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
