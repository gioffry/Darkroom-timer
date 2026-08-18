#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
split_grade = java / 'SplitGradePlan.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.10.3 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.3 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.3 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.3 OK',label,flush=True)
def edit_method(p, start, end, editor, label):
    s=rd(p); a=s.find(start)
    if a < 0: raise SystemExit(f'v0.10.3 {label}: inizio metodo non trovato')
    b=s.find(end,a)
    if b < 0: raise SystemExit(f'v0.10.3 {label}: fine metodo non trovata')
    block=s[a:b]
    new=editor(block)
    if new == block: raise SystemExit(f'v0.10.3 {label}: nessuna modifica applicata')
    wr(p,s[:a]+new+s[b:]); print('v0.10.3 OK',label,flush=True)

# Versione 0.10.3 / code 48
rep(build, 'VERSION_NAME = "0.10.2"', 'VERSION_NAME = "0.10.3"', 'version name build')
rep(build, 'VERSION_CODE = "47"', 'VERSION_CODE = "48"', 'version code build')
rep(build, '[Darkroom v0.10.2]', '[Darkroom v0.10.3]', 'build log tag')
rep(build, r'versionCode\s+47\b', r'versionCode\s+48\b', 'preflight code regex')
rep(build, r'0\.10\.2', r'0\.10\.3', 'preflight name regex')
rep(build, 'versionCode 47 / versionName 0.10.2', 'versionCode 48 / versionName 0.10.3', 'preflight message')
rep(build, 'Preflight v0.10.2 OK', 'Preflight v0.10.3 OK', 'preflight log')
rep(gradle, "versionCode 47\n        versionName '0.10.2'", "versionCode 48\n        versionName '0.10.3'", 'gradle version')
rep(manifest, 'android:versionCode="47"\n    android:versionName="0.10.2"', 'android:versionCode="48"\n    android:versionName="0.10.3"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.2";', 'private static final String APP_VERSION = "0.10.3";', 'UI version')

# Split Grade: nuovi piani partono da filtri 0/0 e tempi minimi sicuri.
rep(split_grade, '    public int softYellow = 50;\n    public int softMs = 6000;\n    public int hardMagenta = 70;\n    public int hardMs = 3000;',
'''    public int softYellow = 0;
    public int softMs = 500;
    public int hardMagenta = 0;
    public int hardMs = 500;''', 'split defaults zero')

def edit_split(block):
    old='''        final SplitGradePlan draft = original.copy();\n        draft.enabled = true;\n        draft.sanitize();'''
    new='''        final SplitGradePlan draft = original.copy();
        draft.enabled = true;
        if (creating) {
            if (printWidthMs < 1000) {
                Toast.makeText(this, "Per lo Split Grade la base deve essere almeno 1,0 s", Toast.LENGTH_LONG).show();
                return;
            }
            draft.softYellow = 0;
            draft.hardMagenta = 0;
            int units = Math.max(2, printWidthMs / 500);
            int softUnits = (units + 1) / 2;
            draft.softMs = softUnits * 500;
            draft.hardMs = (units - softUnits) * 500;
        }
        draft.sanitize();
        if (draft.totalMs() > printWidthMs && printWidthMs >= 1000) {
            int units = Math.max(2, printWidthMs / 500);
            int total = Math.max(1, draft.totalMs());
            int softUnits = Math.max(1, Math.min(units - 1, Math.round((draft.softMs / (float) total) * units)));
            draft.softMs = softUnits * 500;
            draft.hardMs = (units - softUnits) * 500;
        }'''
    if old not in block: raise SystemExit('v0.10.3 split editor: init non trovato')
    block=block.replace(old,new,1)
    old='smPlus.setOnClickListener(v -> { sm[0]=Math.min(36000000,sm[0]+500); smValue.setText(formatTime(sm[0])); });'
    new='smPlus.setOnClickListener(v -> { int maxSoft=Math.max(500,printWidthMs-hmsec[0]); sm[0]=Math.min(maxSoft,sm[0]+500); smValue.setText(formatTime(sm[0])); });'
    if old not in block: raise SystemExit('v0.10.3 split editor: plus morbida non trovato')
    block=block.replace(old,new,1)
    old='htPlus.setOnClickListener(v -> { hmsec[0]=Math.min(36000000,hmsec[0]+500); htValue.setText(formatTime(hmsec[0])); });'
    new='htPlus.setOnClickListener(v -> { int maxHard=Math.max(500,printWidthMs-sm[0]); hmsec[0]=Math.min(maxHard,hmsec[0]+500); htValue.setText(formatTime(hmsec[0])); });'
    if old not in block: raise SystemExit('v0.10.3 split editor: plus dura non trovato')
    old='''        TextView voice = text("Guida vocale: “Imposta Giallo " + sy[0] + "…” poi “Imposta Magenta " + hm[0] + "…”. Funziona anche a display spento.", 11, MUTED, false);'''
    new='''        TextView limit = text("Somma massima delle due esposizioni: " + formatTime(printWidthMs) + " · base operativa", 11, MUTED, true);
        limit.setGravity(Gravity.CENTER); panel.addView(limit, margin(lp(-1,-2),0,2,0,5));
        TextView voice = text("Guida vocale: “Imposta Giallo " + sy[0] + "…” poi “Imposta Magenta " + hm[0] + "…”. Funziona anche a display spento.", 11, MUTED, false);'''
    if old not in block: raise SystemExit('v0.10.3 split editor: nota voce non trovata')
    block=block.replace(old,new,1)
    old='''        save.setOnClickListener(v -> {
            draft.enabled=true; draft.softYellow=sy[0]; draft.softMs=sm[0]; draft.hardMagenta=hm[0]; draft.hardMs=hmsec[0]; draft.sanitize();'''
    new='''        save.setOnClickListener(v -> {
            if (sm[0] + hmsec[0] > printWidthMs) {
                Toast.makeText(this, "La somma dello Split Grade non può superare la base " + formatTime(printWidthMs), Toast.LENGTH_LONG).show();
                return;
            }
            draft.enabled=true; draft.softYellow=sy[0]; draft.softMs=sm[0]; draft.hardMagenta=hm[0]; draft.hardMs=hmsec[0]; draft.sanitize();'''
    if old not in block: raise SystemExit('v0.10.3 split editor: salvataggio non trovato')
    block=block.replace(old,new,1)
    if 'cancel.setOnClickListener(v->dialog.dismiss());' in block:
        block=block.replace('cancel.setOnClickListener(v->dialog.dismiss());','cancel.setOnClickListener(v->{dialog.dismiss();showPrintSequenceDialog();});',1)
    elif 'cancel.setOnClickListener(v -> dialog.dismiss());' in block:
        block=block.replace('cancel.setOnClickListener(v -> dialog.dismiss());','cancel.setOnClickListener(v->{dialog.dismiss();showPrintSequenceDialog();});',1)
    else: raise SystemExit('v0.10.3 split editor: ANNULLA non trovato')
    return block
edit_method(main,'    private void showSplitGradeEditor(final boolean creating) {','    private void showPrintCorrectionEditor(final int index) {',edit_split,'split editor base cap + cancel')

# Dodge/Burn: ANNULLA torna al Piano. Se la correzione era appena creata, ANNULLA la rimuove davvero.
def edit_correction(block):
    old='''        final PrintCorrection original = printSequence.corrections.get(index);\n        final PrintCorrection c = original.copy();'''
    new='''        final PrintCorrection original = printSequence.corrections.get(index);
        final boolean creatingCorrection = original.label == null || original.label.trim().isEmpty();
        final PrintCorrection c = original.copy();'''
    if old not in block: raise SystemExit('v0.10.3 correction editor: original non trovato')
    block=block.replace(old,new,1)
    if 'close.setOnClickListener(v->dialog.dismiss());' in block:
        block=block.replace('close.setOnClickListener(v->dialog.dismiss());',
'''close.setOnClickListener(v->{
            if(creatingCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index)==original){
                printSequence.corrections.remove(index); persistPrintSequence();
            }
            dialog.dismiss(); showPrintSequenceDialog();
        });''',1)
    elif 'close.setOnClickListener(v -> dialog.dismiss());' in block:
        block=block.replace('close.setOnClickListener(v -> dialog.dismiss());',
'''close.setOnClickListener(v->{
            if(creatingCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index)==original){
                printSequence.corrections.remove(index); persistPrintSequence();
            }
            dialog.dismiss(); showPrintSequenceDialog();
        });''',1)
    else: raise SystemExit('v0.10.3 correction editor: ANNULLA non trovato')
    return block
edit_method(main,'    private void showPrintCorrectionEditor(final int index) {','    private boolean validatePrintSequenceForBase() {',edit_correction,'DODGE/BURN cancel returns plan')

# Armamento: Split non può mai superare la base operativa. Burn resta aggiuntivo e Dodge resta locale.
validation=r'''    private boolean validatePrintSequenceForBase() {
        if (printSequence == null || printSequence.isEmpty()) return true;
        if (printSequence.hasSplit()) {
            printSequence.split.sanitize();
            if (printSequence.split.totalMs() > printWidthMs) {
                setStatusPresentation("ATTENZIONE", "SPLIT GRADE: morbida + dura non possono superare la base " + formatTime(printWidthMs), RED);
                return false;
            }
        }
        for (PrintCorrection c : printSequence.dodges()) {
            int baseMs = printSequence.baseMsFor(c, printWidthMs);
            int cueMs = c.resolvedMs(baseMs);
            if (cueMs >= baseMs) {
                setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": il cue deve avvenire prima della fine della esposizione " + (printSequence.hasSplit() ? (c.isHard() ? "dura" : "morbida") : "base"), RED);
                return false;
            }
        }
        return true;
    }

'''
rrep(main,r'    private boolean validatePrintSequenceForBase\(\) \{.*?(?=    private LinearLayout buildTestPanel\(\))',validation,'split total validation')

# Esposizioni brevi: non accettare OFF LAN anticipati. Il MINIR2 resta proprietario dell'Inching.
early_pattern=r'''                long minimumCredibleMs = Math\.max\(250L, Math\.round\(currentPulseWidthMs \* 0\.75\)\);\n                if \(observed > 0 && observed < minimumCredibleMs\) \{.*?                \}\n                consecutiveEarlyOffs = 0;'''
early_repl='''                long minimumCredibleMs = Math.max(250L, currentPulseWidthMs - 50L);
                if (observed > 0 && observed < minimumCredibleMs) {
                    TechnicalLog.add(this, techSessionId,
                            "IGNORATO switch=OFF anticipato • " + secondsLong(observed)
                                    + " < gate " + secondsLong(minimumCredibleMs)
                                    + " • Inching lasciato al MINIR2");
                    consecutiveEarlyOffs = 0;
                    return;
                }
                int neededOffConfirmations = currentPulseWidthMs <= 3000 ? 2 : 1;
                consecutiveEarlyOffs++;
                if (consecutiveEarlyOffs < neededOffConfirmations) {
                    TechnicalLog.add(this, techSessionId,
                            "OFF credibile • conferma " + consecutiveEarlyOffs + "/" + neededOffConfirmations
                                    + " • " + secondsLong(observed));
                    return;
                }
                consecutiveEarlyOffs = 0;'''
rrep(service,early_pattern,early_repl,'short exposure OFF gate')

# Quando il pulsante fisico avvia davvero la fase, interrompi anche l'eventuale frase TTS già in corso.
rep(service,'                    cancelVoicePrompt();\n                    lastObservedOnAt = observedAt;',
'''                    cancelVoicePrompt();
                    try { if (tts != null) tts.stop(); } catch (Exception ignored) {}
                    lastObservedOnAt = observedAt;''','stop current voice on physical start')

checks={
    build:['VERSION_NAME = "0.10.3"','VERSION_CODE = "48"'],
    main:['private static final String APP_VERSION = "0.10.3"','Somma massima delle due esposizioni','morbida + dura non possono superare la base','creatingCorrection','showPrintSequenceDialog();'],
    split_grade:['public int softYellow = 0;','public int hardMagenta = 0;'],
    service:['currentPulseWidthMs - 50L','neededOffConfirmations','OFF credibile • conferma','tts.stop()']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.3 verifica fallita: {needle} in {p}')
print('v0.10.3 TUTTE LE VERIFICHE SORGENTE OK',flush=True)
