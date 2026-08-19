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
    if n < count: raise SystemExit(f'v0.10.1 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.1 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.1 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.1 OK',label,flush=True)

# -----------------------------------------------------------------------------
# Versione 0.10.1 / code 46
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.10.0"', 'VERSION_NAME = "0.10.1"', 'version name build')
rep(build, 'VERSION_CODE = "45"', 'VERSION_CODE = "46"', 'version code build')
rep(build, '[Darkroom v0.10.0]', '[Darkroom v0.10.1]', 'build log tag')
rep(build, r'versionCode\s+45\b', r'versionCode\s+46\b', 'preflight code regex')
rep(build, r'0\.10\.0', r'0\.10\.1', 'preflight name regex')
rep(build, 'versionCode 45 / versionName 0.10.0', 'versionCode 46 / versionName 0.10.1', 'preflight message')
rep(build, 'Preflight v0.10.0 OK', 'Preflight v0.10.1 OK', 'preflight log')
rep(gradle, "versionCode 45\n        versionName '0.10.0'", "versionCode 46\n        versionName '0.10.1'", 'gradle version')
rep(manifest, 'android:versionCode="45"\n    android:versionName="0.10.0"', 'android:versionCode="46"\n    android:versionName="0.10.1"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.0";', 'private static final String APP_VERSION = "0.10.1";', 'UI version')

# -----------------------------------------------------------------------------
# 1) TIMING: never truncate a real MINIR2 Inching exposure because of stale LAN OFF.
# The MINIR2 owns exposure duration. Premature /info OFF is diagnostic only.
# -----------------------------------------------------------------------------
early_pattern = r'''                long minimumCredibleMs = Math\.max\(250L, Math\.round\(currentPulseWidthMs \* 0\.75\)\);\n                if \(observed > 0 && observed < minimumCredibleMs\) \{\n                    consecutiveEarlyOffs\+\+;.*?                consecutiveEarlyOffs = 0;'''
early_repl = '''                long minimumCredibleMs = Math.max(250L, Math.round(currentPulseWidthMs * 0.75));
                if (observed > 0 && observed < minimumCredibleMs) {
                    // The MINIR2 owns the Inching timer. /zeroconf/info may report stale OFF
                    // while the relay is physically still ON. Never stop or fail a print from
                    // an early network observation: doing so would itself truncate the exposure.
                    TechnicalLog.add(this, techSessionId,
                            "IGNORATO switch=OFF prematuro • " + secondsLong(observed)
                                    + " < soglia " + secondsLong(minimumCredibleMs)
                                    + " • timer lasciato al MINIR2");
                    consecutiveEarlyOffs = 0;
                    return;
                }
                consecutiveEarlyOffs = 0;'''
rrep(service, early_pattern, early_repl, 'premature OFF no longer aborts exposure')

# -----------------------------------------------------------------------------
# 2) ERROR UX: keep emergency recovery, add a true RETRY action.
# -----------------------------------------------------------------------------
old_error = '''        } else if (SonoffArmService.STATE_ERROR.equals(state)) {
            armed = false;
            setControlsEnabled(device != null && device.isValid());
            normalButton.setVisibility(View.VISIBLE);
            normalButton.setEnabled(device != null && device.isValid());
            normalButton.setAlpha(normalButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
            setStatusPresentation("ATTENZIONE", message == null ? "Errore del ciclo" : message, RED);
            cancelCycleButton.setVisibility(View.GONE);
            return;
        } else {'''
new_error = '''        } else if (SonoffArmService.STATE_ERROR.equals(state)) {
            armed = false;
            setControlsEnabled(device != null && device.isValid());
            normalButton.setVisibility(View.VISIBLE);
            normalButton.setEnabled(device != null && device.isValid());
            normalButton.setAlpha(normalButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
            actionButton.setVisibility(mode == MODE_LOG ? View.GONE : View.VISIBLE);
            actionButton.setText("RIPROVA");
            actionButton.setEnabled(device != null && device.isValid());
            actionButton.setAlpha(actionButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
            setStatusPresentation("ATTENZIONE", message == null ? "Errore del ciclo" : message, RED);
            cancelCycleButton.setVisibility(View.GONE);
            // An exposure error must not disable the independent manual ON/OFF safelight interlock.
            ensureSafelightIdleOn();
            return;
        } else {'''
rep(main, old_error, new_error, 'RIPROVA on cycle error')

# Service-side robustness too: if the screen is off, an error still restarts the idle interlock.
old_fail_tail = '''        broadcast(STATE_ERROR, message);
        updateNotification("ATTENZIONE — " + message);
        releaseWakeLock();
    }

    private void stopCleanly() {'''
new_fail_tail = '''        broadcast(STATE_ERROR, message);
        updateNotification("ATTENZIONE — " + message);
        if (safelightAuto && device != null && device.isValid() && safelight != null && safelight.isValid()
                && !safelight.deviceId.equals(device.deviceId)) {
            completing.set(false);
            interlockActive = true;
            acquireWakeLock();
            startInterlockMonitor();
            TechnicalLog.add(this, techSessionId, "INTERBLOCCO SAFELIGHT riattivato dopo errore");
        } else {
            releaseWakeLock();
        }
    }

    private void stopCleanly() {'''
rep(service, old_fail_tail, new_fail_tail, 'safelight interlock resumes after error')

# -----------------------------------------------------------------------------
# 3) ALLUNGA TEMPI: deterministic availability for the current base.
# It remains visible in STAMPA; before the first full print it is simply disabled.
# -----------------------------------------------------------------------------
old_can = '''    private boolean canLengthenTimes() {
        SharedPreferences s = getSharedPreferences("log_session", MODE_PRIVATE);
        long lastPrintAt = s.getLong("lastPrintAt", 0L);
        long chosenAt = exposureRecipe == null ? 0L : exposureRecipe.baseChosenAt;
        return lastPrintAt > Math.max(0L, chosenAt);
    }'''
new_can = '''    private boolean canLengthenTimes() {
        SharedPreferences s = getSharedPreferences("log_session", MODE_PRIVATE);
        long lastPrintAt = s.getLong("lastPrintAt", 0L);
        if (lastPrintAt <= 0L) return false;
        long chosenAt = exposureRecipe == null ? 0L : Math.max(0L, exposureRecipe.baseChosenAt);
        return chosenAt <= 0L || lastPrintAt >= chosenAt;
    }'''
rep(main, old_can, new_can, 'stable ALLUNGA TEMPI availability')

# -----------------------------------------------------------------------------
# 4) Main arm label: no meaningless "PIANO 3" counter.
# -----------------------------------------------------------------------------
old_arm = '''("ARMA STAMPA • " + formatTime(printWidthMs) + (printSequence != null && !printSequence.isEmpty() ? (printSequence.hasSplit() ? " · PIANO SPLIT" : " · PIANO " + printSequence.size()) : ""))'''
new_arm = '''(printSequence != null && !printSequence.isEmpty() ? "ARMA PIANO DI STAMPA" : "ARMA STAMPA • " + formatTime(printWidthMs))'''
rep(main, old_arm, new_arm, 'clear ARM label')

# -----------------------------------------------------------------------------
# 5) PIANO UI: Split Grade is EXPOSURE, Dodge/Burn are CORRECTIONS, tools separate.
# -----------------------------------------------------------------------------
update_ui = r'''    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        printSequenceButton.setText("PIANO DI STAMPA");

        String base = recipeBaseSummary();
        boolean hasRecipe = !base.isEmpty() || !printSequence.isEmpty()
                || (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0);
        if (!hasRecipe) {
            printSequenceSummary.setText("");
            printSequenceSummary.setVisibility(View.GONE);
            return;
        }

        StringBuilder s = new StringBuilder();
        if (!base.isEmpty()) s.append(base);
        if (s.length() > 0) s.append("\n\n");
        s.append("ESPOSIZIONE\n");
        if (printSequence.hasSplit()) {
            s.append(printSequence.split.softLine()).append('\n').append(printSequence.split.hardLine());
        } else {
            s.append("SINGOLA · ").append(formatTime(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                String f = exposureRecipe.filterLabel();
                if (!"NESSUNO".equals(f)) s.append(" · ").append(f);
                s.append(" · ").append(exposureRecipe.densityLabel());
            }
        }

        if (!printSequence.corrections.isEmpty()) {
            s.append("\n\nCORREZIONI");
            for (PrintCorrection c : printSequence.corrections) {
                if (c == null) continue;
                int baseMs = printSequence.baseMsFor(c, printWidthMs);
                s.append('\n').append(c.displayLine(baseMs, printSequence.hasSplit()));
            }
        }
        if (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0)
            s.append("\n\nCORREZIONE GLOBALE · ").append(exposureRecipe.globalLabel());
        printSequenceSummary.setText(s.toString());
        printSequenceSummary.setVisibility(View.VISIBLE);
    }

'''
rrep(main, r'    private void updatePrintSequenceUi\(\) \{.*?(?=    private void persistPrintSequence\(\))', update_ui, 'structured plan summary')

plan_dialog = r'''    private void showPrintSequenceDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));
        panel.addView(text("PIANO DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1,-2));

        String base = recipeBaseSummary();
        if (!base.isEmpty()) {
            TextView baseInfo=text(base,13,darkroomMode?RED:GREEN,true);
            baseInfo.setPadding(0,dp(6),0,dp(12));
            panel.addView(baseInfo,lp(-1,-2));
        }

        panel.addView(text("ESPOSIZIONE",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
        if (printSequence != null && printSequence.hasSplit()) {
            Button splitRow=compactButton("SPLIT GRADE  ·  Y "+printSequence.split.softYellow+" / "+formatTime(printSequence.split.softMs)+"  →  M "+printSequence.split.hardMagenta+" / "+formatTime(printSequence.split.hardMs));
            splitRow.setTextColor(Color.WHITE);
            splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_VIVA_MAGENTA,8,0,0));
            if(!darkroomMode) splitRow.setOnClickListener(v->{dialog.dismiss();showSplitGradeEditor(false);}); else splitRow.setEnabled(false);
            panel.addView(splitRow,margin(lp(-1,dp(56)),0,0,0,8));
        } else {
            String f=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.filterLabel():"NESSUNO";
            String d=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.densityLabel():"D0";
            String label="SINGOLA  ·  "+formatTime(printWidthMs)+("NESSUNO".equals(f)?"":" · "+f)+" · "+d;
            Button single=compactButton(label); single.setTextColor(Color.WHITE); single.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),8,0,0)); single.setEnabled(false);
            panel.addView(single,margin(lp(-1,dp(52)),0,0,0,7));
            if(!darkroomMode){
                Button split=compactButton("PASSA A SPLIT GRADE"); split.setTextColor(Color.WHITE); split.setBackground(roundRect(SPLIT_VIVA_MAGENTA,8,0,0)); split.setOnClickListener(v->{dialog.dismiss();showSplitGradeEditor(true);}); panel.addView(split,margin(lp(-1,dp(52)),0,0,0,10));
            }
        }

        panel.addView(text("CORREZIONI",12,MUTED,true),margin(lp(-1,-2),0,4,0,5));
        if(printSequence!=null){
            for(int x=0;x<printSequence.corrections.size();x++){
                final int index=x; PrintCorrection c=printSequence.corrections.get(x); int baseMs=printSequence.baseMsFor(c,printWidthMs);
                Button row=compactButton(c.displayLine(baseMs,printSequence.hasSplit())); int fc=c.isDodge()?DODGE_BISCAY_BAY:BURN_RUST;
                row.setTextColor(Color.WHITE); row.setBackground(roundRect(darkroomMode?RED:fc,8,0,0));
                if(!darkroomMode) row.setOnClickListener(v->{dialog.dismiss();showPrintCorrectionEditor(index);}); else row.setEnabled(false);
                panel.addView(row,margin(lp(-1,dp(50)),0,0,0,7));
            }
        }
        if(!darkroomMode){
            Button dodge=compactButton("+  DODGE"); dodge.setTextColor(Color.WHITE); dodge.setBackground(roundRect(DODGE_BISCAY_BAY,8,0,0)); dodge.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.DODGE);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            Button burn=compactButton("+  BURN"); burn.setTextColor(Color.WHITE); burn.setBackground(roundRect(BURN_RUST,8,0,0)); burn.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.BURN);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            LinearLayout addRow=new LinearLayout(this); addRow.setOrientation(LinearLayout.HORIZONTAL); addRow.addView(dodge,margin(lp(0,dp(50),1f),0,0,dp(4),0)); addRow.addView(burn,margin(lp(0,dp(50),1f),dp(4),0,0,0)); panel.addView(addRow,margin(lp(-1,-2),0,0,0,12));

            panel.addView(text("STRUMENTI",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
            boolean lengthReady=canLengthenTimes();
            Button length=compactButton(lengthReady?"ALLUNGA TEMPI":"ALLUNGA TEMPI · DOPO LA PRIMA STAMPA");
            length.setTextColor(Color.WHITE); length.setBackground(roundRect(lengthReady?ALLUNGA_COLOR:Color.rgb(55,60,64),8,0,0)); length.setEnabled(lengthReady); length.setAlpha(lengthReady?1f:0.55f);
            if(lengthReady) length.setOnClickListener(v->{dialog.dismiss();showLengthenTimesDialog();}); panel.addView(length,lp(-1,dp(52)));

            Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(Color.WHITE); global.setBackground(roundRect(Color.rgb(55,60,64),8,0,0)); global.setOnClickListener(v->{dialog.dismiss();showGlobalCorrectionDialog();}); panel.addView(global,margin(lp(-1,dp(50)),0,7,0,0));

            if((printSequence!=null&&!printSequence.isEmpty()) || (exposureRecipe!=null&&(exposureRecipe.densityQuarterSteps>0||exposureRecipe.globalQuarterStops!=0))){
                Button clear=compactButton("AZZERA PIANO"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("AZZERARE IL PIANO DI STAMPA?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La base originale resta disponibile.","AZZERA",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA")); panel.addView(clear,margin(lp(-1,dp(46)),0,10,0,0));
            }
        } else {
            TextView darkNote=text("In modalità camera oscura il piano è consultabile ma non modificabile.",11,RED,false); darkNote.setGravity(Gravity.CENTER); panel.addView(darkNote,margin(lp(-1,-2),0,8,0,0));
        }
        Button close=compactButton("CHIUDI"); close.setTextColor(Color.WHITE); close.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),9,0,0)); close.setOnClickListener(v->dialog.dismiss()); panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(sc); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.86f));
    }

'''
rrep(main, r'    private void showPrintSequenceDialog\(\) \{.*?(?=    private void showPlanTypeDialog\(\))', plan_dialog, 'separate exposure/corrections/tools')

# Clarify phase selector: it is an attribute of a correction, not a second Split Grade editor.
s=rd(main)
s=s.replace('TextView phaseLabel=text("FASE SPLIT GRADE",11,MUTED,true);', 'TextView phaseLabel=text("APPLICA DURANTE",11,MUTED,true);')
# Filled-state consistency for the two radio-like groups in correction editor.
s=s.replace('soft.setBackground(roundRect(sft?featureColor:BUTTON,8,1,BORDER)); hard.setBackground(roundRect(!sft?featureColor:BUTTON,8,1,BORDER));',
            'soft.setBackground(roundRect(sft?featureColor:Color.rgb(55,60,64),8,0,0)); hard.setBackground(roundRect(!sft?featureColor:Color.rgb(55,60,64),8,0,0));')
s=s.replace('secondsMode.setBackground(roundRect(!useStops[0]?featureColor:BUTTON,8,1,BORDER));stopMode.setBackground(roundRect(useStops[0]?featureColor:BUTTON,8,1,BORDER));',
            'secondsMode.setBackground(roundRect(!useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));stopMode.setBackground(roundRect(useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));')
wr(main,s)
print('v0.10.1 OK correction editor hierarchy and filled toggles',flush=True)

# Source checks.
checks={
    build:['VERSION_NAME = "0.10.1"','VERSION_CODE = "46"'],
    main:['private static final String APP_VERSION = "0.10.1"','RIPROVA','ARMA PIANO DI STAMPA','ESPOSIZIONE','CORREZIONI','STRUMENTI','ALLUNGA TEMPI · DOPO LA PRIMA STAMPA','APPLICA DURANTE'],
    service:['timer lasciato al MINIR2','INTERBLOCCO SAFELIGHT riattivato dopo errore']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.1 verifica fallita: {needle} in {p}')
if 'ERRORE switch=OFF prematuro persistente' in rd(service): raise SystemExit('v0.10.1 verifica fallita: vecchio abort prematuro ancora presente')
print('v0.10.1 TUTTE LE VERIFICHE SORGENTE OK',flush=True)
