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
    if n < count: raise SystemExit(f'v0.7.6 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.7.6 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    p=Path(p); s=rd(p); out,n=re.subn(pattern, lambda m: replacement(m) if callable(replacement) else replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.7.6 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.7.6 OK',label,flush=True)

# Versione
rep(build, 'VERSION_NAME = "0.7.5"\nVERSION_CODE = "38"', 'VERSION_NAME = "0.7.6"\nVERSION_CODE = "39"', 'version build')
rep(build, '[Darkroom v0.7.5]', '[Darkroom v0.7.6]', 'tag build')
rep(build, 'versionCode\\s+38\\b', 'versionCode\\s+39\\b', 'preflight code')
rep(build, '0\\.7\\.5', '0\\.7\\.6', 'preflight name')
rep(build, 'versionCode 38 / versionName 0.7.5', 'versionCode 39 / versionName 0.7.6', 'preflight msg')
rep(build, 'Preflight v0.7.5 OK', 'Preflight v0.7.6 OK', 'preflight log')
rep(project/'app/build.gradle', "versionCode 38\n        versionName '0.7.5'", "versionCode 39\n        versionName '0.7.6'", 'gradle')
rep(project/'app/src/main/AndroidManifest.xml', 'android:versionCode="38"\n    android:versionName="0.7.5"', 'android:versionCode="39"\n    android:versionName="0.7.6"', 'manifest')
rep(main, 'private static final String APP_VERSION = "0.7.5";', 'private static final String APP_VERSION = "0.7.6";', 'app version')

# UI: quando l'automazione viene disattivata ferma anche il monitor permanente.
rep(main,
'''            updateSafelightStatus();\n            if (safelightAuto) ensureSafelightIdleOn();''',
'''            updateSafelightStatus();\n            if (safelightAuto) ensureSafelightIdleOn(); else stopSafelightInterlock();''',
'UI toggle monitor')

# Il vecchio ensureSafelightIdleOn comandava direttamente ON. Ora avvia il servizio
# permanente che segue lo stato reale dell'ingranditore anche in normale ON/OFF.
rrep(main,
      r'''    private void ensureSafelightIdleOn\(\) \{.*?\n    \}\n\n    private void showDevicePicker\(\) \{''',
      '''    private void ensureSafelightIdleOn() {\n        if (!safelightAuto || armed) return;\n        DeviceConfig primary = DeviceConfig.load(this);\n        DeviceConfig safe = SafelightConfig.load(this);\n        if (!primary.isValid() || !safe.isValid() || safe.deviceId.equals(primary.deviceId)) return;\n        Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_START_INTERLOCK);\n        startServiceCompat(i);\n    }\n\n    private void stopSafelightInterlock() {\n        Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_STOP_INTERLOCK);\n        startServiceCompat(i);\n    }\n\n    private void showDevicePicker() {''', 'MainActivity monitor permanente')

# Service: azioni e stato del monitor permanente.
rep(service,
'''    public static final String ACTION_CANCEL = "it.darkroom.timer.CANCEL";\n    public static final String BROADCAST_STATE = "it.darkroom.timer.STATE";''',
'''    public static final String ACTION_CANCEL = "it.darkroom.timer.CANCEL";\n    public static final String ACTION_START_INTERLOCK = "it.darkroom.timer.START_SAFELIGHT_INTERLOCK";\n    public static final String ACTION_STOP_INTERLOCK = "it.darkroom.timer.STOP_SAFELIGHT_INTERLOCK";\n    public static final String BROADCAST_STATE = "it.darkroom.timer.STATE";''', 'service action monitor')
rep(service,
'''    private ScheduledFuture<?> pollTask;\n    private ScheduledFuture<?> nextTask;''',
'''    private ScheduledFuture<?> pollTask;\n    private ScheduledFuture<?> nextTask;\n    private ScheduledFuture<?> interlockTask;''', 'service future monitor')
rep(service,
'''    private volatile boolean safelightAuto = false;\n    private volatile int mode = MODE_PRINT;''',
'''    private volatile boolean safelightAuto = false;\n    private volatile boolean interlockActive = false;\n    private volatile String lastInterlockPrimaryState = "";\n    private volatile int mode = MODE_PRINT;''', 'service campi monitor')

# Qualsiasi ciclo temporizzato prende il controllo esclusivo e sospende il monitor idle.
rep(service,
'''        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {\n            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;''',
'''        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;''', 'arm sospende monitor')

# Nuove azioni del servizio, prima di CANCEL.
rep(service,
'''        } else if (ACTION_CANCEL.equals(action)) {\n            // Stop any pending automatic test-strip step immediately on receipt.''',
'''        } else if (ACTION_START_INTERLOCK.equals(action)) {\n            device = DeviceConfig.load(this);\n            loadSafelightConfig();\n            if (!safelightAuto || device == null || !device.isValid() || safelight == null || !safelight.isValid()\n                    || safelight.deviceId.equals(device.deviceId)) {\n                interlockActive = false;\n                cancelInterlockMonitor();\n                releaseWakeLock();\n                stopForeground(true);\n                stopSelf();\n                return START_NOT_STICKY;\n            }\n            interlockActive = true;\n            completing.set(false);\n            startForeground(NOTIFICATION_ID, notification("Interblocco luce rossa attivo"));\n            acquireWakeLock();\n            startInterlockMonitor();\n        } else if (ACTION_STOP_INTERLOCK.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            loadSafelightConfig();\n            restoreSafelightBestEffort();\n            releaseWakeLock();\n            stopForeground(true);\n            stopSelf();\n        } else if (ACTION_CANCEL.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            // Stop any pending automatic test-strip step immediately on receipt.''', 'azioni monitor')
rep(service,
'''        } else if (ACTION_DISARM.equals(action)) {\n            completing.set(true);''',
'''        } else if (ACTION_DISARM.equals(action)) {\n            interlockActive = false;\n            cancelInterlockMonitor();\n            completing.set(true);''', 'disarm sospende monitor')

# ARMA NON deve più spegnere la luce rossa: serve per sistemare la carta.
rep(service,
'''            SonoffHttp.pulseOn(device, currentPulseWidthMs);\n            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(currentPulseWidthMs));\n            if (safelightAuto) {\n                setSafelightConfirmed(false);\n                TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF confermata • pronto all’esposizione");\n            }''',
'''            SonoffHttp.pulseOn(device, currentPulseWidthMs);\n            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(currentPulseWidthMs));\n            if (safelightAuto) TechnicalLog.add(this, techSessionId, "SAFELIGHT lasciata ON durante ARMATO");''', 'ARMA lascia rossa ON')
rep(service,
'''            String msg = mode == MODE_PRINT\n                    ? (safelightAuto ? "ARMATO — luce rossa OFF • premi il pulsante fisico" : "ARMATO — premi il pulsante fisico")\n                    : (safelightAuto ? "PROVINO ARMATO — luce rossa OFF • premi il pulsante fisico una volta" : "PROVINO ARMATO — premi il pulsante fisico una volta");''',
'''            String msg = mode == MODE_PRINT\n                    ? "ARMATO — premi il pulsante fisico"\n                    : "PROVINO ARMATO — premi il pulsante fisico una volta";''', 'messaggio ARMATO corretto')

# Alla PRIMA vera accensione dell'ingranditore spegne la rossa. Nei provini resta poi OFF
# per tutte le pause e le esposizioni successive.
rep(service,
'''                if (seenOn.compareAndSet(false, true)) {\n                    lastObservedOnAt = observedAt;''',
'''                if (seenOn.compareAndSet(false, true)) {\n                    if (safelightAuto && completed == 0) {\n                        try {\n                            setSafelightConfirmed(false);\n                            TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF confermata alla prima accensione reale dell’ingranditore");\n                        } catch (Exception e) {\n                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: OFF non confermata — " + readable(e));\n                        }\n                    }\n                    lastObservedOnAt = observedAt;''', 'rossa OFF su ON reale')

# Elimina la riaccensione ad ogni singola esposizione introdotta in v0.7.5.
rep(service,
'''        seenOn.set(false);\n        completed++;\n        if (safelightAuto) {\n            try {\n                setSafelightConfirmed(true);\n                TechnicalLog.add(this, techSessionId, "SAFELIGHT ON confermata dopo esposizione " + completed);\n            } catch (Exception e) {\n                fail("Ingranditore OFF, ma luce rossa non riaccesa: " + readable(e));\n                return;\n            }\n        }''',
'''        seenOn.set(false);\n        completed++;''', 'nessun ON nelle pause provino')

# A fine STAMPA o dopo l'ULTIMA striscia, riaccende la rossa una sola volta.
rep(service,
'''        if (mode == MODE_PRINT || completed >= count) {\n            if (!completing.compareAndSet(false, true)) return;\n            cancelTimers();\n            try {''',
'''        if (mode == MODE_PRINT || completed >= count) {\n            if (!completing.compareAndSet(false, true)) return;\n            cancelTimers();\n            restoreSafelightBestEffort();\n            try {''', 'rossa ON solo a fine ciclo')

# Nessuna commutazione della rossa fra una striscia e la successiva.
rep(service,
'''                if (safelightAuto) {\n                    setSafelightConfirmed(false);\n                    TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF confermata prima della esposizione " + (completed + 1));\n                }\n                SonoffHttp.switchOn(device);''',
'''                SonoffHttp.switchOn(device);''', 'provino rossa resta OFF')

# Il helper non disattiva Inching ad ogni commutazione: lo fa una volta all'avvio monitor.
rep(service,
'''        Exception last = null;\n        // La safelight deve essere in normale ON/OFF, mai in Inching.\n        try { SonoffHttp.pulseOff(safelight); } catch (Exception e) { last = e; }\n        for (int attempt = 1; attempt <= 4; attempt++) {''',
'''        Exception last = null;\n        for (int attempt = 1; attempt <= 4; attempt++) {''', 'helper commutazione leggera')

# Monitor permanente: segue lo switch reale del SONOFF ingranditore anche fuori da STAMPA/PROVINO.
anchor='''    private void loadSafelightConfig() {'''
monitor=r'''    private void startInterlockMonitor() {
        cancelInterlockMonitor();
        if (!interlockActive || !safelightAuto || device == null || !device.isValid()
                || safelight == null || !safelight.isValid() || safelight.deviceId.equals(device.deviceId)) return;
        lastInterlockPrimaryState = "";
        try { SonoffHttp.pulseOff(safelight); } catch (Exception ignored) {}
        interlockTask = io.scheduleWithFixedDelay(this::interlockPollOnce, 0, 500, TimeUnit.MILLISECONDS);
    }

    private void interlockPollOnce() {
        if (!interlockActive || !safelightAuto) return;
        try {
            String primary = SonoffHttp.infoQuick(device, 1400);
            if (!primary.equals(lastInterlockPrimaryState)) {
                boolean safeOn = !"on".equals(primary);
                setSafelightConfirmed(safeOn);
                lastInterlockPrimaryState = primary;
                String text = "on".equals(primary)
                        ? "Ingranditore ON • luce rossa OFF"
                        : "Ingranditore OFF • luce rossa ON";
                updateNotification(text);
                TechnicalLog.add(this, techSessionId, "INTERBLOCCO — " + text);
            }
        } catch (Exception e) {
            updateNotification("Interblocco: attendo i SONOFF…");
        }
    }

    private void cancelInterlockMonitor() {
        if (interlockTask != null) {
            interlockTask.cancel(false);
            interlockTask = null;
        }
        lastInterlockPrimaryState = "";
    }

'''+anchor
rep(service, anchor, monitor, 'helper monitor permanente')

# A ciclo concluso, se l'automazione è ON, il servizio non muore: torna al monitor ON/OFF.
rrep(service,
      r'''    private void stopCleanly\(\) \{.*?\n    \}\n\n    private void cancelTimers''',
      '''    private void stopCleanly() {\n        cancelTimers();\n        if (safelightAuto && device != null && device.isValid() && safelight != null && safelight.isValid()\n                && !safelight.deviceId.equals(device.deviceId)) {\n            completing.set(false);\n            interlockActive = true;\n            startForeground(NOTIFICATION_ID, notification("Interblocco luce rossa attivo"));\n            startInterlockMonitor();\n            return;\n        }\n        interlockActive = false;\n        cancelInterlockMonitor();\n        releaseWakeLock();\n        stopForeground(true);\n        stopSelf();\n    }\n\n    private void cancelTimers''', 'ritorno a monitor dopo ciclo')

# Notifica distinta durante monitor idle, senza pulsante ANNULLA CICLO.
rrep(service,
      r'''    private Notification notification\(String text\) \{.*?\n    \}\n\n    private void updateNotification''',
      '''    private Notification notification(String text) {\n        Intent open = new Intent(this, MainActivity.class);\n        PendingIntent content = PendingIntent.getActivity(this, 1, open, PendingIntent.FLAG_UPDATE_CURRENT | immutableFlag());\n        String title = interlockActive\n                ? "Darkroom Timer — Luce rossa automatica"\n                : (mode == MODE_TEST ? "Darkroom Timer — Provino " + count + " × " + seconds(widthMs) : "Darkroom Timer — " + seconds(widthMs));\n        Notification.Builder b = notificationBuilder()\n                .setContentTitle(title)\n                .setContentText(text)\n                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)\n                .setOngoing(true)\n                .setOnlyAlertOnce(true)\n                .setContentIntent(content);\n        if (!interlockActive) {\n            Intent disarm = new Intent(this, SonoffArmService.class).setAction(ACTION_CANCEL);\n            PendingIntent disarmPi = PendingIntent.getService(this, 2, disarm, PendingIntent.FLAG_UPDATE_CURRENT | immutableFlag());\n            b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "ANNULLA", disarmPi);\n        }\n        return b.build();\n    }\n\n    private void updateNotification''', 'notifica monitor')

# Distruzione completa: cancella anche il monitor.
rep(service,
'''    @Override public void onDestroy() {\n        cancelTimers();''',
'''    @Override public void onDestroy() {\n        cancelTimers();\n        cancelInterlockMonitor();''', 'destroy monitor')

# Verifiche statiche
checks={
    build:['VERSION_NAME = "0.7.6"','VERSION_CODE = "39"'],
    main:['ACTION_START_INTERLOCK','ACTION_STOP_INTERLOCK','stopSafelightInterlock()'],
    service:['ACTION_START_INTERLOCK','interlockPollOnce()','completed == 0','restoreSafelightBestEffort();','Darkroom Timer — Luce rossa automatica']
}
for p, needles in checks.items():
    text=rd(p)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.7.6 verifica fallita: {needle} in {p}')
# Non devono più esistere i testi/automatismi sbagliati di v0.7.5.
s=rd(service)
for forbidden in ['ARMATO — luce rossa OFF', 'SAFELIGHT ON confermata dopo esposizione', 'SAFELIGHT OFF confermata prima della esposizione']:
    if forbidden in s: raise SystemExit('v0.7.6 residuo logica vecchia: '+forbidden)
print('v0.7.6 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
