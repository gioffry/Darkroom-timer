#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
build = work / 'build_darkroom.py'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    p=Path(p); s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.7.7 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.7.7 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    p=Path(p); s=rd(p); out,n=re.subn(pattern, lambda m: replacement(m) if callable(replacement) else replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.7.7 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.7.7 OK',label,flush=True)

# Versione
rep(build, 'VERSION_NAME = "0.7.6"\nVERSION_CODE = "39"', 'VERSION_NAME = "0.7.7"\nVERSION_CODE = "40"', 'version build')
rep(build, '[Darkroom v0.7.6]', '[Darkroom v0.7.7]', 'tag build')
rep(build, 'versionCode\\s+39\\b', 'versionCode\\s+40\\b', 'preflight code')
rep(build, '0\\.7\\.6', '0\\.7\\.7', 'preflight name')
rep(build, 'versionCode 39 / versionName 0.7.6', 'versionCode 40 / versionName 0.7.7', 'preflight msg')
rep(build, 'Preflight v0.7.6 OK', 'Preflight v0.7.7 OK', 'preflight log')
rep(project/'app/build.gradle', "versionCode 39\n        versionName '0.7.6'", "versionCode 40\n        versionName '0.7.7'", 'gradle')
rep(project/'app/src/main/AndroidManifest.xml', 'android:versionCode="39"\n    android:versionName="0.7.6"', 'android:versionCode="40"\n    android:versionName="0.7.7"', 'manifest')
rep(main, 'private static final String APP_VERSION = "0.7.6";', 'private static final String APP_VERSION = "0.7.7";', 'app version')

# Testo impostazioni: non esiste piu uno stato "normalmente ON" imposto dall'app.
rep(main,
'''                ? "SONOFF SAFELIGHT  •  ID " + safeCfg.deviceId + "\\nNormalmente ON • OFF durante l’esposizione"''',
'''                ? "SONOFF SAFELIGHT  •  ID " + safeCfg.deviceId + "\\nStato manuale rispettato • OFF durante l’ingranditore"''',
'copy impostazioni')

# Stato aggiuntivo per ricordare se la rossa era realmente accesa prima di essere spenta.
rep(service,
'''    private volatile boolean interlockActive = false;\n    private volatile String lastInterlockPrimaryState = "";\n    private volatile int mode = MODE_PRINT;''',
'''    private volatile boolean interlockActive = false;\n    private volatile String lastInterlockPrimaryState = "";\n    private volatile boolean interlockRestoreSafelight = false;\n    private volatile boolean cycleSafelightCaptured = false;\n    private volatile boolean restoreSafelightAfterCycle = false;\n    private volatile int mode = MODE_PRINT;''', 'campi memoria safelight')

# All'avvio di un ciclo si azzera soltanto la memoria interna: nessun comando alla lampada.
rep(service,
'''        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;''',
'''        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            interlockRestoreSafelight = false;\n            cycleSafelightCaptured = false;\n            restoreSafelightAfterCycle = false;\n            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;''', 'reset memoria ciclo')

# Disattivare l'interblocco non deve accendere la luce.
rep(service,
'''        } else if (ACTION_STOP_INTERLOCK.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            loadSafelightConfig();\n            restoreSafelightBestEffort();\n            releaseWakeLock();''',
'''        } else if (ACTION_STOP_INTERLOCK.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            interlockRestoreSafelight = false;\n            releaseWakeLock();''', 'stop senza comando luce')

rep(service,
'''            if (safelightAuto) TechnicalLog.add(this, techSessionId, "SAFELIGHT lasciata ON durante ARMATO");''',
'''            if (safelightAuto) TechnicalLog.add(this, techSessionId, "SAFELIGHT non modificata durante ARMATO");''', 'log ARMATO neutro')

# Alla prima vera accensione del ciclo legge lo stato della rossa: la spegne solo se era ON.
rep(service,
'''                    if (safelightAuto && completed == 0) {\n                        try {\n                            setSafelightConfirmed(false);\n                            TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF confermata alla prima accensione reale dell’ingranditore");\n                        } catch (Exception e) {\n                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: OFF non confermata — " + readable(e));\n                        }\n                    }''',
'''                    if (safelightAuto && completed == 0) {\n                        try {\n                            captureAndDimSafelightForCycle();\n                        } catch (Exception e) {\n                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: stato iniziale non acquisito — " + readable(e));\n                        }\n                    }''', 'cattura stato prima esposizione')

# Il vecchio ripristino forzava sempre ON. Ora ripristina solo se l'app l'aveva trovata ON.
rrep(service,
      r'''    private void restoreSafelightBestEffort\(\) \{.*?\n    \}\n\n''',
      '''    private void restoreSafelightBestEffort() {\n        boolean captured = cycleSafelightCaptured;\n        boolean restore = restoreSafelightAfterCycle;\n        cycleSafelightCaptured = false;\n        restoreSafelightAfterCycle = false;\n        if (!captured || !restore) {\n            if (captured) TechnicalLog.add(this, techSessionId, "SAFELIGHT era OFF prima del ciclo • stato lasciato OFF");\n            return;\n        }\n        try {\n            setSafelightConfirmed(true);\n            TechnicalLog.add(this, techSessionId, "SAFELIGHT ripristinata ON perché era ON prima del ciclo");\n        } catch (Exception e) {\n            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: ripristino stato iniziale fallito — " + readable(e));\n        }\n    }\n\n''', 'ripristino stato originario')

# Inserisce helper di acquisizione stato prima del setter confermato.
anchor='''    private void setSafelightConfirmed(boolean on) throws Exception {'''
helper=r'''    private void captureAndDimSafelightForCycle() throws Exception {
        if (!safelightAuto) return;
        if (safelight == null || !safelight.isValid()) throw new Exception("SONOFF safelight non configurato");
        String observed = SonoffHttp.infoQuick(safelight, 1800);
        if (!"on".equals(observed) && !"off".equals(observed)) throw new Exception("stato safelight non leggibile");
        cycleSafelightCaptured = true;
        restoreSafelightAfterCycle = "on".equals(observed);
        if (restoreSafelightAfterCycle) {
            setSafelightConfirmed(false);
            TechnicalLog.add(this, techSessionId, "SAFELIGHT era ON • spenta per il ciclo");
        } else {
            TechnicalLog.add(this, techSessionId, "SAFELIGHT era già OFF • nessun comando");
        }
    }

'''+anchor
rep(service, anchor, helper, 'helper cattura ciclo')

# Monitor ON/OFF normale: il primo poll è solo osservazione. Nessun comando all'apertura app.
# Sui cambi successivi conserva e ripristina lo stato manuale della rossa.
rrep(service,
      r'''    private void startInterlockMonitor\(\) \{.*?\n    \}\n\n    private void interlockPollOnce\(\) \{.*?\n    \}\n\n    private void cancelInterlockMonitor\(\) \{''',
      '''    private void startInterlockMonitor() {\n        cancelInterlockMonitor();\n        if (!interlockActive || !safelightAuto || device == null || !device.isValid()\n                || safelight == null || !safelight.isValid() || safelight.deviceId.equals(device.deviceId)) return;\n        lastInterlockPrimaryState = "";\n        interlockRestoreSafelight = false;\n        interlockTask = io.scheduleWithFixedDelay(this::interlockPollOnce, 0, 500, TimeUnit.MILLISECONDS);\n    }\n\n    private void interlockPollOnce() {\n        if (!interlockActive || !safelightAuto) return;\n        try {\n            String primary = SonoffHttp.infoQuick(device, 1400);\n            if (lastInterlockPrimaryState.isEmpty()) {\n                lastInterlockPrimaryState = primary;\n                updateNotification("Interblocco attivo • stato manuale luce rossa rispettato");\n                TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline " + primary.toUpperCase(Locale.ITALY) + " • nessun comando safelight");\n                return;\n            }\n            if (primary.equals(lastInterlockPrimaryState)) return;\n\n            if ("on".equals(primary)) {\n                String safeState = SonoffHttp.infoQuick(safelight, 1400);\n                interlockRestoreSafelight = "on".equals(safeState);\n                if (interlockRestoreSafelight) {\n                    setSafelightConfirmed(false);\n                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — rossa era ON, spenta con ingranditore");\n                } else {\n                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — rossa era già OFF, nessun comando");\n                }\n                updateNotification("Ingranditore ON • luce rossa " + (interlockRestoreSafelight ? "spenta automaticamente" : "già OFF"));\n            } else {\n                if (interlockRestoreSafelight) {\n                    setSafelightConfirmed(true);\n                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — ripristinata rossa ON");\n                    updateNotification("Ingranditore OFF • luce rossa ripristinata ON");\n                } else {\n                    updateNotification("Ingranditore OFF • stato manuale luce rossa invariato");\n                }\n                interlockRestoreSafelight = false;\n            }\n            lastInterlockPrimaryState = primary;\n        } catch (Exception e) {\n            updateNotification("Interblocco: attendo i SONOFF…");\n        }\n    }\n\n    private void cancelInterlockMonitor() {''', 'monitor preserva stato manuale')

# Cancellare il monitor non deve cambiare la lampada.
rep(service,
'''        lastInterlockPrimaryState = "";\n    }''',
'''        lastInterlockPrimaryState = "";\n        interlockRestoreSafelight = false;\n    }''', 'reset monitor senza restore')

checks={
    build:['VERSION_NAME = "0.7.7"','VERSION_CODE = "40"'],
    main:['Stato manuale rispettato'],
    service:['captureAndDimSafelightForCycle()','stato manuale luce rossa rispettato','SAFELIGHT era già OFF • nessun comando','ripristinata rossa ON perché era ON prima del ciclo']
}
for p, needles in checks.items():
    text=rd(p)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.7.7 verifica fallita: {needle} in {p}')
print('v0.7.7 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
