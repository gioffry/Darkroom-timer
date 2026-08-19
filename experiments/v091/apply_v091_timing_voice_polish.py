#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
sequence = java / 'PrintSequence.java'
split = java / 'SplitGradePlan.java'
jpeg = java / 'JpegRenderer.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.9.1 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.9.1 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.9.1 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.9.1 OK', label, flush=True)

# Versione 0.9.1 / code 44
rep(build, 'VERSION_NAME = "0.9.0"', 'VERSION_NAME = "0.9.1"', 'version name build')
rep(build, 'VERSION_CODE = "43"', 'VERSION_CODE = "44"', 'version code build')
rep(build, '[Darkroom v0.9.0]', '[Darkroom v0.9.1]', 'build log tag')
rep(build, r'versionCode\s+43\b', r'versionCode\s+44\b', 'preflight code regex')
rep(build, r'0\.9\.0', r'0\.9\.1', 'preflight name regex')
rep(build, 'versionCode 43 / versionName 0.9.0', 'versionCode 44 / versionName 0.9.1', 'preflight message')
rep(build, 'Preflight v0.9.0 OK', 'Preflight v0.9.1 OK', 'preflight log')
rep(gradle, "versionCode 43\n        versionName '0.9.0'", "versionCode 44\n        versionName '0.9.1'", 'gradle version')
rep(manifest, 'android:versionCode="43"\n    android:versionName="0.9.0"', 'android:versionCode="44"\n    android:versionName="0.9.1"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.9.0";', 'private static final String APP_VERSION = "0.9.1";', 'UI version')

# Terminologia: il PIANO contiene passaggi, non "correzioni".
s=rd(sequence).replace('Nessuna correzione','Nessun passaggio')
wr(sequence,s)

update_ui = r'''    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        if (printSequence.isEmpty()) {
            printSequenceButton.setText("PIANO DI STAMPA");
            printSequenceSummary.setText("");
            printSequenceSummary.setVisibility(View.GONE);
        } else {
            int steps = printSequence.size();
            printSequenceButton.setText("PIANO · " + steps + " PASSAGGI" + (steps == 1 ? "O" : ""));
            printSequenceSummary.setText(printSequence.detail(printWidthMs));
            printSequenceSummary.setVisibility(View.VISIBLE);
        }
    }

'''
rrep(main, r'    private void updatePrintSequenceUi\(\) \{.*?(?=    private void persistPrintSequence\(\))', update_ui, 'passaggi in piano UI')

s=rd(main)
s=s.replace('text("TIPO DI CORREZIONE", 19, TEXT_PRIMARY, true)', 'text("AGGIUNGI AL PIANO", 19, TEXT_PRIMARY, true)')
s=s.replace('"Nessuna correzione. La stampa semplice resta identica."', '"Nessun passaggio. La stampa semplice resta identica."')
s=s.replace('compactButton("SALVA CORREZIONE")', 'compactButton("SALVA")')
s=s.replace('compactButton("ELIMINA CORREZIONE")', 'compactButton("ELIMINA DAL PIANO")')
s=s.replace('" · PIANO SPLIT"', '" · PIANO " + printSequence.size()')
# Etichetta automatica nel LOG.
s=s.replace('"\\nSequenza di stampa: "', '"\\nPiano di stampa: "')
wr(main,s)

s=rd(jpeg)
s=s.replace('SEQUENZA DI STAMPA','PIANO DI STAMPA').replace('correzioni nel LOG','passaggi nel LOG')
wr(jpeg,s)

# Frasi Split Grade in italiano naturale per la guida vocale.
s=rd(split)
s=s.replace('return "Imposta Giallo " + softYellow + ". Poi premi il pulsante.";', 'return "Prima esposizione. Imposta giallo " + softYellow + ". Poi premi il pulsante.";')
s=s.replace('return "Imposta Magenta " + hardMagenta + ". Poi premi il pulsante.";', 'return "Seconda esposizione. Imposta magenta " + hardMagenta + ". Poi premi il pulsante.";')
wr(split,s)

# TTS: ripeti 12 secondi DOPO la fine della frase, non 5 secondi dall'inizio.
rep(service, 'import android.speech.tts.TextToSpeech;\n', 'import android.speech.tts.TextToSpeech;\nimport android.speech.tts.UtteranceProgressListener;\n', 'tts progress import')
rep(service,
'''    private volatile boolean ttsReady = false;\n    private ScheduledFuture<?> voiceRepeatTask;''',
'''    private volatile boolean ttsReady = false;\n    private volatile boolean voiceRepeatActive = false;\n    private volatile String voiceRepeatWords = "";\n    private ScheduledFuture<?> voiceRepeatTask;''', 'voice repeat fields')

old_tts = r'''        tts = new TextToSpeech(getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS && tts != null) {
                int r = tts.setLanguage(Locale.ITALIAN);
                tts.setSpeechRate(0.95f);
                ttsReady = r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED;
            }
        });'''
new_tts = r'''        tts = new TextToSpeech(getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS && tts != null) {
                int r = tts.setLanguage(Locale.ITALIAN);
                tts.setSpeechRate(0.95f);
                ttsReady = r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED;
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override public void onStart(String utteranceId) {}
                    @Override public void onDone(String utteranceId) {
                        if (utteranceId != null && utteranceId.startsWith("darkroom-repeat-")) scheduleNextVoiceRepeat();
                    }
                    @Override public void onError(String utteranceId) {
                        if (utteranceId != null && utteranceId.startsWith("darkroom-repeat-")) scheduleNextVoiceRepeat();
                    }
                });
            }
        });'''
rep(service, old_tts, new_tts, 'tts completion listener')

voice_helpers = r'''    private boolean voiceGuideEnabled() {
        return getSharedPreferences("ui", MODE_PRIVATE).getBoolean("voiceGuide", true);
    }

    private void speakOnce(String words) {
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty() || !ttsReady || tts == null) return;
        try { tts.speak(words, TextToSpeech.QUEUE_FLUSH, null, "darkroom-once-" + System.nanoTime()); } catch (Exception ignored) {}
    }

    private void scheduleVoiceInstruction(final String words) {
        cancelVoicePrompt();
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty()) return;
        voiceRepeatActive = true;
        voiceRepeatWords = words.trim();
        voiceRepeatTask = cueIo.schedule(this::speakRepeatingVoice, 350L, TimeUnit.MILLISECONDS);
    }

    private void speakRepeatingVoice() {
        if (!voiceRepeatActive || !voiceGuideEnabled() || voiceRepeatWords.isEmpty() || !ttsReady || tts == null) return;
        try { tts.speak(voiceRepeatWords, TextToSpeech.QUEUE_FLUSH, null, "darkroom-repeat-" + System.nanoTime()); } catch (Exception ignored) {
            scheduleNextVoiceRepeat();
        }
    }

    private void scheduleNextVoiceRepeat() {
        if (!voiceRepeatActive || voiceRepeatWords.isEmpty()) return;
        if (voiceRepeatTask != null) voiceRepeatTask.cancel(false);
        voiceRepeatTask = cueIo.schedule(this::speakRepeatingVoice, 12_000L, TimeUnit.MILLISECONDS);
    }

    private void cancelVoicePrompt() {
        voiceRepeatActive = false;
        voiceRepeatWords = "";
        if (voiceRepeatTask != null) {
            voiceRepeatTask.cancel(false);
            voiceRepeatTask = null;
        }
        try { if (tts != null) tts.stop(); } catch (Exception ignored) {}
    }

'''
rrep(service, r'    private boolean voiceGuideEnabled\(\) \{.*?(?=    private void dodgeCueFeedback\(\))', voice_helpers, 'voice repeat after utterance')

s=rd(service)
s=s.replace('speakOnce("Togli maschera " + dodge.safeLabel());', 'speakOnce("Togli la maschera: " + dodge.safeLabel());')
s=s.replace('"Burn " + burn.safeLabel() + ". Prepara la maschera. Poi premi il pulsante."', '"Bruciatura " + burn.safeLabel() + ". Prepara la maschera. Poi premi il pulsante."')
s=s.replace('"SEQUENZA DI STAMPA • "', '"PIANO DI STAMPA • "')
wr(service,s)

# -----------------------------------------------------------------------------
# Timing hardening.
# 1) ogni pulseWidth viene letto e confermato dal SONOFF prima di armare il pulsante;
# 2) ON reale stimato tra ultimo OFF e primo ON, per un DODGE molto meno dipendente dalla LAN;
# 3) OFF prematuro persistente non viene piu' mascherato come "stale": il ciclo viene fermato.
# -----------------------------------------------------------------------------
rep(service,
'''    private volatile long lastObservedOnAt = 0L;\n    private volatile long lastObservedOffAt = 0L;''',
'''    private volatile long lastObservedOnAt = 0L;\n    private volatile long lastObservedOffAt = 0L;\n    private volatile long lastConfirmedOffBeforeOnAt = 0L;\n    private volatile int consecutiveEarlyOffs = 0;''', 'timing observation fields')
rep(service,
'''            lastObservedOnAt = 0L;\n            lastObservedOffAt = 0L;''',
'''            lastObservedOnAt = 0L;\n            lastObservedOffAt = 0L;\n            lastConfirmedOffBeforeOnAt = 0L;\n            consecutiveEarlyOffs = 0;''', 'timing reset')

# Tutti i settaggi Inching passano dalla verifica vera di pulse + pulseWidth.
s=rd(service)
count=s.count('SonoffHttp.pulseOn(device, currentPulseWidthMs);')
if count < 3: raise SystemExit(f'v0.9.1 pulse verify replacement: atteso >=3, trovato {count}')
s=s.replace('SonoffHttp.pulseOn(device, currentPulseWidthMs);', 'configurePulseVerified(currentPulseWidthMs);')
wr(service,s)
print('v0.9.1 OK pulse verify calls', count, flush=True)

# Se durante l'attesa il relay e' OFF, memorizza l'ultimo OFF: il primo ON viene brackettato tra due poll.
rep(service,
'''            if ("on".equals(sw)) {\n                if (seenOn.compareAndSet(false, true)) {''',
'''            if ("on".equals(sw)) {\n                consecutiveEarlyOffs = 0;\n                if (seenOn.compareAndSet(false, true)) {''', 'reset early off on ON')

rep(service,
'''                    cancelVoicePrompt();\n                    lastObservedOnAt = observedAt;\n                    if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) scheduleDodgeCues(observedAt);''',
'''                    cancelVoicePrompt();\n                    long estimatedOnAt = observedAt;\n                    long bracket = lastConfirmedOffBeforeOnAt;\n                    if (bracket > 0L && observedAt > bracket && observedAt - bracket <= 1500L) {\n                        estimatedOnAt = bracket + (observedAt - bracket) / 2L;\n                        TechnicalLog.add(this, techSessionId, "AVVIO RELAY stimato tra OFF/ON • finestra " + secondsLong(observedAt - bracket));\n                    }\n                    lastObservedOnAt = estimatedOnAt;\n                    lastConfirmedOffBeforeOnAt = 0L;\n                    if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) scheduleDodgeCues(estimatedOnAt);''', 'estimate relay start')

old_early = r'''                long minimumCredibleMs = Math.max(250L, Math.round(currentPulseWidthMs * 0.75));
                if (observed > 0 && observed < minimumCredibleMs) {
                    TechnicalLog.add(this, techSessionId,
                            "IGNORATO switch=OFF prematuro • " + secondsLong(observed)
                                    + " < soglia " + secondsLong(minimumCredibleMs));
                    return;
                }'''
new_early = r'''                long minimumCredibleMs = Math.max(250L, Math.round(currentPulseWidthMs * 0.75));
                if (observed > 0 && observed < minimumCredibleMs) {
                    consecutiveEarlyOffs++;
                    if (consecutiveEarlyOffs == 1) {
                        TechnicalLog.add(this, techSessionId,
                                "IGNORATO singolo switch=OFF prematuro • " + secondsLong(observed)
                                        + " < soglia " + secondsLong(minimumCredibleMs));
                        return;
                    }
                    TechnicalLog.add(this, techSessionId,
                            "ERRORE switch=OFF prematuro persistente • osservati " + secondsLong(observed)
                                    + " • attesi " + seconds(currentPulseWidthMs)
                                    + " • Inching era stato verificato");
                    fail("Il SONOFF ha spento l’ingranditore troppo presto: " + secondsLong(observed)
                            + " invece di " + seconds(currentPulseWidthMs) + ". Ciclo fermato per non falsare la stampa.");
                    return;
                }
                consecutiveEarlyOffs = 0;'''
rep(service, old_early, new_early, 'persistent early OFF detection')

rep(service,
'''                onExposureFinished();\n            }\n        } catch (Exception e) {''',
'''                onExposureFinished();\n            } else if ("off".equals(sw)) {\n                lastConfirmedOffBeforeOnAt = observedAt;\n                consecutiveEarlyOffs = 0;\n            }\n        } catch (Exception e) {''', 'track OFF while waiting')

# Appena termina la fase morbida, lo stato a schermo cambia PRIMA delle operazioni di rete.
rep(service,
'''    private void prepareSplitStage() {\n        cancelPoll();\n        cancelDodgeCues();\n        cancelVoicePrompt();\n        if (printSequence == null || !printSequence.hasSplit() || splitStage != 1) return;\n        try {''',
'''    private void prepareSplitStage() {\n        cancelPoll();\n        cancelDodgeCues();\n        cancelVoicePrompt();\n        if (printSequence == null || !printSequence.hasSplit() || splitStage != 1) return;\n        String transition = "FASE MORBIDA CONCLUSA — preparo il cambio filtro";\n        broadcast(STATE_WAITING_SPLIT, transition);\n        updateNotification(transition);\n        try {''', 'split immediate transition')

# Helper di verifica Inching, prima del watchdog finale.
pulse_helper = r'''    private void configurePulseVerified(int requestedMs) throws Exception {
        int wanted = sanitizeWidth(requestedMs);
        Exception last = null;
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                SonoffHttp.pulseOn(device, wanted);
                TechnicalLog.add(this, techSessionId, "COMANDO Inching pulse=ON • richiesti " + seconds(wanted) + " • tentativo " + attempt + "/3");
                for (int check = 0; check < 4; check++) {
                    SonoffHttp.TimedStatus status = SonoffHttp.infoStatusTimed(device, 2500);
                    TechnicalLog.add(this, techSessionId, "VERIFICA Inching • pulse=" + status.pulseState + " • pulseWidth=" + status.pulseWidthMs + " ms");
                    if ("on".equals(status.pulseState) && status.pulseWidthMs == wanted) {
                        currentPulseWidthMs = wanted;
                        TechnicalLog.add(this, techSessionId, "INCHING CONFERMATO • " + seconds(wanted));
                        return;
                    }
                    last = new Exception("pulse=" + status.pulseState + ", pulseWidth=" + status.pulseWidthMs + " ms");
                    try { Thread.sleep(120L); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); throw ie; }
                }
            } catch (Exception e) {
                last = e;
            }
        }
        throw new Exception("Inching non confermato a " + seconds(wanted) + ": " + readable(last));
    }

'''
rrep(service, r'    private void pulseOffWithWatchdog\(\) throws Exception \{', pulse_helper + '    private void pulseOffWithWatchdog() throws Exception {', 'pulse verification helper')

# Le stringhe del vecchio log "accettato" non devono far pensare che basti l'HTTP 200.
s=rd(service).replace('COMANDO pulse=on accettato • ', 'SETTAGGIO Inching richiesto • ')
wr(service,s)

# Check sorgente
checks={
    build:['VERSION_NAME = "0.9.1"','VERSION_CODE = "44"'],
    main:['AGGIUNGI AL PIANO','PASSAGGI','ELIMINA DAL PIANO','private static final String APP_VERSION = "0.9.1"'],
    service:['configurePulseVerified','INCHING CONFERMATO','switch=OFF prematuro persistente','AVVIO RELAY stimato','UtteranceProgressListener','12_000L','Bruciatura ','FASE MORBIDA CONCLUSA'],
    sequence:['Nessun passaggio'],
    jpeg:['PIANO DI STAMPA']
}
for p, needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.9.1 verifica fallita: {needle} in {p}')
print('v0.9.1 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
