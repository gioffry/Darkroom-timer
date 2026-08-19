#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
logentry = java / 'LogEntry.java'
logstore = java / 'LogStore.java'
jpeg = java / 'JpegCardRenderer.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'
recipe = java / 'ExposureRecipe.java'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.10.0 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.0 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.0 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.0 OK', label, flush=True)

# -----------------------------------------------------------------------------
# Versione 0.10.0 / code 45
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.9.1"', 'VERSION_NAME = "0.10.0"', 'version name build')
rep(build, 'VERSION_CODE = "44"', 'VERSION_CODE = "45"', 'version code build')
rep(build, '[Darkroom v0.9.1]', '[Darkroom v0.10.0]', 'build log tag')
rep(build, r'versionCode\\s+44\\b', r'versionCode\\s+45\\b', 'preflight code regex')
rep(build, r'0\\.9\\.1', r'0\\.10\\.0', 'preflight name regex')
rep(build, 'versionCode 44 / versionName 0.9.1', 'versionCode 45 / versionName 0.10.0', 'preflight message')
rep(build, 'Preflight v0.9.1 OK', 'Preflight v0.10.0 OK', 'preflight log')
rep(gradle, "versionCode 44\n        versionName '0.9.1'", "versionCode 45\n        versionName '0.10.0'", 'gradle version')
rep(manifest, 'android:versionCode="44"\n    android:versionName="0.9.1"', 'android:versionCode="45"\n    android:versionName="0.10.0"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.9.1";', 'private static final String APP_VERSION = "0.10.0";', 'UI version')

# Model copied verbatim from the release-specific source template.
model_src = Path(__file__).with_name('ExposureRecipe.java').read_text(encoding='utf-8')
wr(recipe, model_src)
print('v0.10.0 OK ExposureRecipe model', flush=True)

# -----------------------------------------------------------------------------
# LOG persistence: test filter + complete recipe state, backward compatible.
# -----------------------------------------------------------------------------
rep(logentry,
'''    public String printSequence = "";\n}''',
'''    public String printSequence = "";\n    /** Filtro M/Y realmente usato durante il provino. */\n    public String testBaseFilterType = ExposureRecipe.FILTER_NONE;\n    public int testBaseFilterValue = 0;\n    /** Base originale/operativa, D e correzione globale. */\n    public String recipeState = "";\n}''', 'LogEntry recipe fields')

rep(logstore,
'''                    e.printSequence = f.length >= 21 ? dec(f[20]) : "";''',
'''                    e.printSequence = f.length >= 21 ? dec(f[20]) : "";\n                    e.testBaseFilterType = f.length >= 22 ? ExposureRecipe.normalizeFilter(dec(f[21])) : ExposureRecipe.FILTER_NONE;\n                    if (f.length >= 23) { try { e.testBaseFilterValue = ExposureRecipe.snap5(Integer.parseInt(f[22])); } catch (Exception ignored) { e.testBaseFilterValue = 0; } }\n                    e.recipeState = f.length >= 24 ? dec(f[23]) : "";''', 'LogStore parse recipe fields')
rep(logstore,
'''                    e.printSequence = "";\n                }''',
'''                    e.printSequence = "";\n                    e.testBaseFilterType = ExposureRecipe.FILTER_NONE;\n                    e.testBaseFilterValue = 0;\n                    e.recipeState = "";\n                }''', 'LogStore legacy recipe defaults')
rep(logstore,
'''                    .append(enc(e.testStripTimes)).append('\\t')\n                    .append(enc(e.printSequence));''',
'''                    .append(enc(e.testStripTimes)).append('\\t')\n                    .append(enc(e.printSequence)).append('\\t')\n                    .append(enc(ExposureRecipe.normalizeFilter(e.testBaseFilterType))).append('\\t')\n                    .append(ExposureRecipe.snap5(e.testBaseFilterValue)).append('\\t')\n                    .append(enc(e.recipeState));''', 'LogStore write recipe fields')

# -----------------------------------------------------------------------------
# MainActivity fields/load: filter provino + recipe state.
# -----------------------------------------------------------------------------
rep(main,
'''    private TextView testFStopBadge;\n    private TextView printSequenceSummary;''',
'''    private TextView testFStopBadge;\n    private Button testBaseFilterButton;\n    private TextView printSequenceSummary;''', 'test filter button field')
rep(main,
'''    private int printWidthMs = 8500;\n    private PrintSequence printSequence = new PrintSequence();\n    private int testWidthMs = 2000;''',
'''    private int printWidthMs = 8500;\n    private PrintSequence printSequence = new PrintSequence();\n    private ExposureRecipe exposureRecipe = new ExposureRecipe();\n    private String testBaseFilterType = ExposureRecipe.FILTER_NONE;\n    private int testBaseFilterValue = 0;\n    private static final int ALLUNGA_COLOR = Color.rgb(154, 119, 43);\n    private int testWidthMs = 2000;''', 'recipe state fields')
rep(main,
'''        printSequence = PrintSequence.decode(p.getString("printSequence", ""));\n        testWidthMs = p.getInt("testWidthMs", 2000);''',
'''        printSequence = PrintSequence.decode(p.getString("printSequence", ""));\n        exposureRecipe = ExposureRecipe.decode(p.getString("exposureRecipe", ""));\n        testBaseFilterType = ExposureRecipe.normalizeFilter(p.getString("testBaseFilterType", ExposureRecipe.FILTER_NONE));\n        testBaseFilterValue = ExposureRecipe.snap5(p.getInt("testBaseFilterValue", 0));\n        testWidthMs = p.getInt("testWidthMs", 2000);''', 'load recipe state')

# Base filter appears in the test preparation panel, before any test is armed.
rep(main,
'''        testStepText.setGravity(Gravity.CENTER);\n        exposure.addView(testStepText);''',
'''        testStepText.setGravity(Gravity.CENTER);\n        exposure.addView(testStepText);\n        testBaseFilterButton = compactButton(testBaseFilterButtonLabel());\n        testBaseFilterButton.setOnClickListener(v -> showTestBaseFilterDialog());\n        exposure.addView(testBaseFilterButton, margin(lp(-1, dp(50)), 0, 10, 0, 0));''', 'base filter in test panel')

# Keep recipe state in sync when base time is manually refined.
set_print = r'''    private void setPrintTime(int ms) {
        if (armed) return;
        printWidthMs = snap(ms, 500, 36_000_000);
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        if (exposureRecipe.hasBase()) exposureRecipe.operationalBaseMs = printWidthMs;
        SharedPreferences.Editor edit = getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("printWidthMs", printWidthMs);
        if (exposureRecipe.hasBase()) edit.putString("exposureRecipe", exposureRecipe.encode());
        edit.apply();
        printTimeText.setText(formatTime(printWidthMs));
        updatePrintSequenceUi();
        applyModeUi();
    }
'''
rrep(main, r'    private void setPrintTime\(int ms\) \{.*?\n    \}\n\n    private void setTestTime', set_print + '\n    private void setTestTime', 'setPrintTime recipe sync')

# Helpers inserted before buildTestPanel.
helpers = r'''    private String testBaseFilterButtonLabel() {
        String f = ExposureRecipe.filterLabel(testBaseFilterType, testBaseFilterValue);
        return "FILTRO BASE · " + ("NESSUNO".equals(f) ? "NESSUNO" : f);
    }

    private void refreshTestBaseFilterUi() {
        if (testBaseFilterButton != null) testBaseFilterButton.setText(testBaseFilterButtonLabel());
    }

    private void persistTestBaseFilter() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(testBaseFilterType))
                .putInt("testBaseFilterValue", ExposureRecipe.snap5(testBaseFilterValue))
                .apply();
        refreshTestBaseFilterUi();
    }

    private void showTestBaseFilterDialog() {
        if (darkroomMode || armed) return;
        String[] choices = {"NESSUNO", "MAGENTA (M)", "GIALLO (Y)"};
        showAppChoiceDialog("FILTRO BASE DEL PROVINO", choices, which -> {
            if (which == 0) {
                testBaseFilterType = ExposureRecipe.FILTER_NONE;
                testBaseFilterValue = 0;
                persistTestBaseFilter();
                return;
            }
            showTestBaseFilterValueDialog(which == 1 ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW);
        }, "ANNULLA");
    }

    private void showTestBaseFilterValueDialog(final String type) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        int accent = ExposureRecipe.FILTER_MAGENTA.equals(type) ? SPLIT_VIVA_MAGENTA : AMBER;
        panel.addView(text("FILTRO BASE · " + (ExposureRecipe.FILTER_MAGENTA.equals(type) ? "MAGENTA" : "GIALLO"), 19, accent, true), lp(-1,-2));
        TextView note = text("Impostalo fisicamente sulla testa colore prima di iniziare il provino. Sarà associato a tutte le strisce e passerà automaticamente alla stampa e al LOG.", 12, MUTED, false);
        note.setPadding(0, dp(5), 0, dp(12)); panel.addView(note, lp(-1,-2));
        final int[] value = { ExposureRecipe.normalizeFilter(testBaseFilterType).equals(type) ? ExposureRecipe.snap5(testBaseFilterValue) : (ExposureRecipe.FILTER_MAGENTA.equals(type) ? 40 : 30) };
        LinearLayout row = new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER);
        Button minus = smallButton("−"); Button plus = smallButton("+");
        TextView number = text(type + value[0], 32, accent, true); number.setGravity(Gravity.CENTER);
        row.addView(minus, lp(dp(62),dp(58))); row.addView(number, lp(0,dp(64),1f)); row.addView(plus, lp(dp(62),dp(58))); panel.addView(row, lp(-1,-2));
        minus.setOnClickListener(v -> { value[0]=Math.max(0,value[0]-5); number.setText(type+value[0]); });
        plus.setOnClickListener(v -> { value[0]=Math.min(200,value[0]+5); number.setText(type+value[0]); });
        Button save = compactButton("SALVA"); save.setTextColor(Color.WHITE); save.setBackground(roundRect(accent,9,0,0));
        save.setOnClickListener(v -> { testBaseFilterType=type; testBaseFilterValue=value[0]; persistTestBaseFilter(); dialog.dismiss(); });
        panel.addView(save, margin(lp(-1,dp(52)),0,10,0,0));
        Button cancel = compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show();
        if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void ensureExposureRecipeBase() {
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        exposureRecipe.ensureBase(printWidthMs);
        exposureRecipe.operationalBaseMs = printWidthMs;
    }

    private void persistExposureRecipe() {
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).apply();
        updatePrintSequenceUi();
    }

    private boolean canLengthenTimes() {
        SharedPreferences s = getSharedPreferences("log_session", MODE_PRIVATE);
        long lastPrintAt = s.getLong("lastPrintAt", 0L);
        long chosenAt = exposureRecipe == null ? 0L : exposureRecipe.baseChosenAt;
        return lastPrintAt > Math.max(0L, chosenAt);
    }

    private void scaleWholeRecipe(int quarterStopDelta) {
        if (quarterStopDelta == 0) return;
        ensureExposureRecipeBase();
        int oldBase = printWidthMs;
        int newBase = ExposureRecipe.scaledMs(oldBase, quarterStopDelta);
        if (printSequence != null) {
            if (printSequence.hasSplit()) {
                printSequence.split.softMs = ExposureRecipe.scaledMs(printSequence.split.softMs, quarterStopDelta);
                printSequence.split.hardMs = ExposureRecipe.scaledMs(printSequence.split.hardMs, quarterStopDelta);
                printSequence.split.sanitize();
            }
            for (PrintCorrection c : printSequence.corrections) {
                if (c == null || c.quarterStops > 0) continue;
                c.milliseconds = ExposureRecipe.scaledMs(c.milliseconds, quarterStopDelta);
            }
        }
        exposureRecipe.operationalBaseMs = newBase;
        printWidthMs = newBase;
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("printWidthMs", printWidthMs)
                .putString("printSequence", printSequence == null ? "" : printSequence.encode())
                .putString("exposureRecipe", exposureRecipe.encode()).apply();
        if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));
        updatePrintSequenceUi();
        applyModeUi();
    }

    private String recipeBaseSummary() {
        if (exposureRecipe == null || !exposureRecipe.hasBase()) return "";
        if (printSequence != null && printSequence.hasSplit()) {
            return "BASE DI PARTENZA · " + exposureRecipe.originalLine()
                    + (exposureRecipe.densityQuarterSteps > 0 ? "\nDENSITÀ OPERATIVA · " + exposureRecipe.densityLabel() + " · applicata alla ricetta finale" : "");
        }
        String s = "BASE · " + exposureRecipe.operationalLine(printWidthMs);
        if (exposureRecipe.originalBaseMs > 0 && (exposureRecipe.originalBaseMs != exposureRecipe.operationalBaseMs || exposureRecipe.densityQuarterSteps > 0))
            s = "BASE ORIGINALE · " + exposureRecipe.originalLine() + "\nBASE OPERATIVA · " + exposureRecipe.operationalLine(printWidthMs);
        return s;
    }

    private void showLengthenTimesDialog() {
        if (darkroomMode || armed || !canLengthenTimes()) return;
        ensureExposureRecipeBase();
        final int currentQ = ExposureRecipe.clampDensity(exposureRecipe.densityQuarterSteps);
        final int[] targetQ = {currentQ};
        final Dialog dialog = new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("ALLUNGA TEMPI",20,ALLUNGA_COLOR,true),lp(-1,-2));
        TextView note=text("Scegli quanto tempo vuoi avere per lavorare. L’app calcola il filtro D equivalente; la filtrazione di contrasto resta invariata.",12,MUTED,false); note.setPadding(0,dp(5),0,dp(12)); panel.addView(note,lp(-1,-2));
        TextView from=text("ORA · "+formatTime(printWidthMs)+" · "+exposureRecipe.filterLabel()+" · "+exposureRecipe.densityLabel(),13,TEXT_PRIMARY,true); from.setGravity(Gravity.CENTER); panel.addView(from,margin(lp(-1,-2),0,0,0,8));
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER);
        Button minus=smallButton("−"); Button plus=smallButton("+"); TextView time=text("",34,ALLUNGA_COLOR,true); time.setGravity(Gravity.CENTER);
        row.addView(minus,lp(dp(62),dp(58))); row.addView(time,lp(0,dp(66),1f)); row.addView(plus,lp(dp(62),dp(58))); panel.addView(row,lp(-1,-2));
        TextView instruction=text("",18,TEXT_PRIMARY,true); instruction.setGravity(Gravity.CENTER); panel.addView(instruction,margin(lp(-1,-2),0,4,0,4));
        TextView contrast=text("",12,MUTED,false); contrast.setGravity(Gravity.CENTER); panel.addView(contrast,margin(lp(-1,-2),0,0,0,12));
        final Runnable refresh=()->{ int delta=targetQ[0]-currentQ; int preview=ExposureRecipe.scaledMs(printWidthMs,delta); time.setText(formatTime(preview)); instruction.setText("IMPOSTA "+ExposureRecipe.densityLabel(targetQ[0])); String f=exposureRecipe.filterLabel(); contrast.setText(("NESSUNO".equals(f)?"Nessun filtro M/Y":"Mantieni "+f)+" · esposizione equivalente nominale"); };
        minus.setOnClickListener(v->{targetQ[0]=Math.max(0,targetQ[0]-1);refresh.run();}); plus.setOnClickListener(v->{targetQ[0]=Math.min(8,targetQ[0]+1);refresh.run();}); refresh.run();
        Button apply=compactButton("APPLICA"); apply.setTextColor(Color.WHITE); apply.setBackground(roundRect(ALLUNGA_COLOR,9,0,0));
        apply.setOnClickListener(v->{ int delta=targetQ[0]-currentQ; scaleWholeRecipe(delta); exposureRecipe.densityQuarterSteps=targetQ[0]; exposureRecipe.operationalBaseMs=printWidthMs; persistExposureRecipe(); persistPrintSequence(); dialog.dismiss(); String f=exposureRecipe.filterLabel(); setStatusPresentation("ALLUNGA TEMPI — "+formatTime(printWidthMs),"IMPOSTA "+exposureRecipe.densityLabel()+("NESSUNO".equals(f)?"":" · mantieni "+f),ALLUNGA_COLOR); }); panel.addView(apply,margin(lp(-1,dp(52)),0,10,0,0));
        Button cancel=compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v->dialog.dismiss()); panel.addView(cancel,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void showGlobalCorrectionDialog() {
        if (darkroomMode || armed) return;
        ensureExposureRecipeBase();
        final Dialog dialog=new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel=new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("CORREZIONE GLOBALE",19,TEXT_PRIMARY,true),lp(-1,-2));
        TextView note=text("Schiarisce o scurisce l’intera ricetta mantenendo invariati i rapporti relativi tra base, DODGE, BURN e SPLIT GRADE.",12,MUTED,false); note.setPadding(0,dp(5),0,dp(12)); panel.addView(note,lp(-1,-2));
        int current=exposureRecipe.globalQuarterStops;
        int[] qs={-1,0,1}; String[] labels={"−¼ STOP","0 · NESSUNA","+¼ STOP"};
        for(int x=0;x<qs.length;x++){ final int q=qs[x]; Button b=compactButton((current==q?"✓  ":"")+labels[x]); b.setTextColor(Color.WHITE); b.setBackground(roundRect(BUTTON,9,0,0)); b.setOnClickListener(v->{int delta=q-exposureRecipe.globalQuarterStops; scaleWholeRecipe(delta); exposureRecipe.globalQuarterStops=q; exposureRecipe.operationalBaseMs=printWidthMs; persistExposureRecipe(); persistPrintSequence(); dialog.dismiss();}); panel.addView(b,margin(lp(-1,dp(50)),0,x==0?0:7,0,0)); }
        Button cancel=compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v->dialog.dismiss()); panel.addView(cancel,margin(lp(-1,dp(48)),0,10,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private String recipeOriginalLabel(LogEntry entry, String fallback) {
        ExposureRecipe r=ExposureRecipe.decode(entry==null?"":entry.recipeState);
        return r.hasBase()?r.originalLine():fallback;
    }
    private String recipeOperationalLabel(LogEntry entry, String fallback) {
        ExposureRecipe r=ExposureRecipe.decode(entry==null?"":entry.recipeState);
        return r.hasBase()?r.operationalLine(entry.exposureMs):fallback;
    }
    private String testFilterLabel(LogEntry entry) {
        if(entry==null) return "—";
        String f=ExposureRecipe.filterLabel(entry.testBaseFilterType,entry.testBaseFilterValue);
        return "NESSUNO".equals(f)?"Nessuno":f;
    }

'''
rep(main, '    private LinearLayout buildTestPanel() {', helpers + '    private LinearLayout buildTestPanel() {', 'recipe helper methods')

# Test-arm payload and print recipe payload: all local metadata only.
rep(main,
'''            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_PRINT_SEQUENCE, printSequence == null ? "" : printSequence.encode());''',
'''            ensureExposureRecipeBase();\n            persistExposureRecipe();\n            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_PRINT_SEQUENCE, printSequence == null ? "" : printSequence.encode());\n            i.putExtra(SonoffArmService.EXTRA_RECIPE_STATE, exposureRecipe.encode());''', 'print arm recipe payload')
rep(main,
'''            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());''',
'''            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.normalizeFilter(testBaseFilterType));\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, ExposureRecipe.snap5(testBaseFilterValue));''', 'test arm base filter payload')

# Chosen strip carries time + filter into the base recipe.
rep(main,
'''        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(strips[i]);\n        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {\n            int imported = strips[which];\n            setMode(MODE_PRINT);\n            setPrintTime(imported);''',
'''        final String chosenFilterType = ExposureRecipe.normalizeFilter(session.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));\n        final int chosenFilterValue = ExposureRecipe.snap5(session.getInt("lastTestBaseFilterValue", 0));\n        final String chosenFilter = ExposureRecipe.filterLabel(chosenFilterType, chosenFilterValue);\n        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(strips[i]) + ("NESSUNO".equals(chosenFilter) ? "" : " · " + chosenFilter);\n        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {\n            int imported = strips[which];\n            exposureRecipe = new ExposureRecipe();\n            exposureRecipe.originalBaseMs = imported;\n            exposureRecipe.operationalBaseMs = imported;\n            exposureRecipe.filterType = chosenFilterType;\n            exposureRecipe.filterValue = chosenFilterValue;\n            exposureRecipe.densityQuarterSteps = 0;\n            exposureRecipe.globalQuarterStops = 0;\n            exposureRecipe.baseChosenAt = System.currentTimeMillis();\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).apply();\n            setMode(MODE_PRINT);\n            setPrintTime(imported);''', 'strip time plus filter transfer')
rep(main,
'''            setStatusPresentation("DAL PROVINO — " + formatTime(imported),\n                    "Tempo precompilato e ancora modificabile con + / − o scorciatoie prima di armare.", GREEN);''',
'''            setStatusPresentation("DAL PROVINO — " + formatTime(imported) + ("NESSUNO".equals(chosenFilter) ? "" : " · " + chosenFilter),\n                    "Tempo + filtrazione trasferiti insieme alla base di stampa.", GREEN);''', 'strip transfer status')

# -----------------------------------------------------------------------------
# PIANO DI STAMPA: base recipe + DODGE/BURN/SPLIT + ALLUNGA TEMPI.
# Global correction is deliberately secondary.
# -----------------------------------------------------------------------------
update_plan_ui = r'''    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        String base = recipeBaseSummary();
        if (printSequence.isEmpty()) {
            printSequenceButton.setText("PIANO DI STAMPA");
            if (base.isEmpty()) { printSequenceSummary.setText(""); printSequenceSummary.setVisibility(View.GONE); }
            else { printSequenceSummary.setText(base + (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0 ? "\nCORREZIONE GLOBALE · " + exposureRecipe.globalLabel() : "")); printSequenceSummary.setVisibility(View.VISIBLE); }
        } else {
            int steps = printSequence.size();
            printSequenceButton.setText("PIANO · " + steps + " PASSAGGI" + (steps == 1 ? "O" : ""));
            StringBuilder s = new StringBuilder();
            if (!base.isEmpty()) s.append(base);
            if (s.length() > 0) s.append('\n');
            s.append(printSequence.detail(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0) s.append("\nCORREZIONE GLOBALE · ").append(exposureRecipe.globalLabel());
            printSequenceSummary.setText(s.toString());
            printSequenceSummary.setVisibility(View.VISIBLE);
        }
    }

'''
rrep(main, r'    private void updatePrintSequenceUi\(\) \{.*?(?=    private void persistPrintSequence\(\))', update_plan_ui, 'plan UI recipe summary')

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
            TextView baseInfo=text(base,13,darkroomMode?RED:GREEN,true); baseInfo.setPadding(0,dp(6),0,dp(10)); panel.addView(baseInfo,lp(-1,-2));
        }

        if (printSequence != null && printSequence.hasSplit()) {
            Button splitRow=compactButton("SPLIT GRADE  ·  Y "+printSequence.split.softYellow+" / "+formatTime(printSequence.split.softMs)+"   →   M "+printSequence.split.hardMagenta+" / "+formatTime(printSequence.split.hardMs));
            splitRow.setTextColor(Color.WHITE); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_VIVA_MAGENTA,8,0,0));
            if(!darkroomMode) splitRow.setOnClickListener(v->{dialog.dismiss();showSplitGradeEditor(false);}); else splitRow.setEnabled(false);
            panel.addView(splitRow,margin(lp(-1,dp(54)),0,0,0,8));
        }
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
            Button add=compactButton("+  AGGIUNGI AL PIANO"); add.setTextColor(Color.WHITE); add.setBackground(roundRect(BUTTON,9,0,0)); add.setOnClickListener(v->{dialog.dismiss();showPlanTypeDialog();}); panel.addView(add,margin(lp(-1,dp(50)),0,8,0,0));
            if(canLengthenTimes()){
                Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(Color.WHITE); global.setBackground(roundRect(BUTTON,9,0,0)); global.setOnClickListener(v->{dialog.dismiss();showGlobalCorrectionDialog();}); panel.addView(global,margin(lp(-1,dp(48)),0,8,0,0));
            }
            if((printSequence!=null&&!printSequence.isEmpty()) || (exposureRecipe!=null&&(exposureRecipe.densityQuarterSteps>0||exposureRecipe.globalQuarterStops!=0))){
                Button clear=compactButton("AZZERA PIANO"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("AZZERARE IL PIANO DI STAMPA?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La base originale resta disponibile.","AZZERA",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA")); panel.addView(clear,margin(lp(-1,dp(46)),0,8,0,0));
            }
        } else {
            TextView darkNote=text("In modalità camera oscura il piano è consultabile ma non modificabile.",11,RED,false); darkNote.setGravity(Gravity.CENTER); panel.addView(darkNote,margin(lp(-1,-2),0,8,0,0));
        }
        Button close=compactButton("CHIUDI"); close.setTextColor(Color.WHITE); close.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):BUTTON,9,0,0)); close.setOnClickListener(v->dialog.dismiss()); panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(sc); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.84f));
    }

'''
rrep(main, r'    private void showPrintSequenceDialog\(\) \{.*?(?=    private void showPlanTypeDialog\(\))', plan_dialog, 'plan dialog recipe')

plan_type = r'''    private void showPlanTypeDialog() {
        final Dialog dialog=new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel=new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("AGGIUNGI AL PIANO",19,TEXT_PRIMARY,true),margin(lp(-1,-2),0,0,0,12));
        Button dodge=compactButton("DODGE"); dodge.setTextColor(Color.WHITE); dodge.setBackground(roundRect(DODGE_BISCAY_BAY,9,0,0)); dodge.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.DODGE);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);}); panel.addView(dodge,lp(-1,dp(54)));
        Button burn=compactButton("BURN"); burn.setTextColor(Color.WHITE); burn.setBackground(roundRect(BURN_RUST,9,0,0)); burn.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.BURN);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);}); panel.addView(burn,margin(lp(-1,dp(54)),0,8,0,0));
        Button split=compactButton("SPLIT GRADE"); split.setTextColor(Color.WHITE); split.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0)); split.setOnClickListener(v->{dialog.dismiss();showSplitGradeEditor(!printSequence.hasSplit());}); panel.addView(split,margin(lp(-1,dp(54)),0,8,0,0));
        if(canLengthenTimes()){ Button length=compactButton("ALLUNGA TEMPI"); length.setTextColor(Color.WHITE); length.setBackground(roundRect(ALLUNGA_COLOR,9,0,0)); length.setOnClickListener(v->{dialog.dismiss();showLengthenTimesDialog();}); panel.addView(length,margin(lp(-1,dp(54)),0,8,0,0)); }
        Button cancel=compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v->dialog.dismiss()); panel.addView(cancel,margin(lp(-1,dp(50)),0,10,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

'''
rrep(main, r'    private void showPlanTypeDialog\(\) \{.*?(?=    private void showSplitGradeEditor\(final boolean creating\))', plan_type, 'plan type with allunga')

# Solid/solid consistency in editor action groups.
s=rd(main)
s=s.replace('delete.setTextColor(RED);delete.setOnClickListener', 'delete.setTextColor(Color.WHITE);delete.setBackground(roundRect(RED,9,0,0));delete.setOnClickListener')
s=s.replace('Button close=compactButton("ANNULLA");close.setOnClickListener', 'Button close=compactButton("ANNULLA");close.setTextColor(Color.WHITE);close.setBackground(roundRect(BUTTON,9,0,0));close.setOnClickListener')
s=s.replace('remove.setTextColor(RED);\n            remove.setOnClickListener', 'remove.setTextColor(Color.WHITE);\n            remove.setBackground(roundRect(RED,9,0,0));\n            remove.setOnClickListener')
s=s.replace('Button cancel=compactButton("ANNULLA"); cancel.setOnClickListener', 'Button cancel=compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener')
wr(main,s)
print('v0.10.0 OK solid action groups', flush=True)

# -----------------------------------------------------------------------------
# Session -> LOG and USA PER STAMPA restore full recipe.
# -----------------------------------------------------------------------------
rep(main,
'''            e.printSequence = p.getString("lastPrintSequence", "");\n            if (testAt > 0) {''',
'''            e.printSequence = p.getString("lastPrintSequence", "");\n            e.recipeState = p.getString("lastRecipeState", "");\n            if (testAt > 0) {''', 'new log recipe state')
rep(main,
'''                e.testCount = p.getInt("lastTestCount", 0);''',
'''                e.testCount = p.getInt("lastTestCount", 0);\n                e.testBaseFilterType = ExposureRecipe.normalizeFilter(p.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));\n                e.testBaseFilterValue = ExposureRecipe.snap5(p.getInt("lastTestBaseFilterValue", 0));''', 'new log test filter')

# Fallback recipe for old sessions / simple prints, then automatic legacy M/Y/D fields.
rep(main,
'''        applyReprintTemplate(e);\n        return e;''',
'''        if (e.recipeState == null || e.recipeState.trim().isEmpty()) {\n            ExposureRecipe r = new ExposureRecipe();\n            if (e.exposureMs > 0) { r.originalBaseMs=e.exposureMs; r.operationalBaseMs=e.exposureMs; r.filterType=e.testBaseFilterType; r.filterValue=e.testBaseFilterValue; r.baseChosenAt=e.timestamp; e.recipeState=r.encode(); }\n        }\n        ExposureRecipe autoRecipe = ExposureRecipe.decode(e.recipeState);\n        if (autoRecipe.hasBase()) {\n            if (ExposureRecipe.FILTER_MAGENTA.equals(autoRecipe.filterType)) e.magenta=String.valueOf(autoRecipe.filterValue);\n            if (ExposureRecipe.FILTER_YELLOW.equals(autoRecipe.filterType)) e.yellow=String.valueOf(autoRecipe.filterValue);\n            e.density=autoRecipe.densityLabel();\n        }\n        applyReprintTemplate(e);\n        return e;''', 'new log recipe fallback')

# USA PER STAMPA: use operational base (not split total), restore recipe/filter and require a fresh first print.
rep(main,
'''        setPrintTime(entry.exposureMs);\n        printSequence = PrintSequence.decode(entry.printSequence);''',
'''        exposureRecipe = ExposureRecipe.decode(entry.recipeState);\n        if (!exposureRecipe.hasBase()) { exposureRecipe.originalBaseMs=entry.exposureMs; exposureRecipe.operationalBaseMs=entry.exposureMs; exposureRecipe.filterType=entry.testBaseFilterType; exposureRecipe.filterValue=entry.testBaseFilterValue; }\n        exposureRecipe.baseChosenAt = System.currentTimeMillis();\n        setPrintTime(exposureRecipe.operationalBaseMs > 0 ? exposureRecipe.operationalBaseMs : entry.exposureMs);\n        printSequence = PrintSequence.decode(entry.printSequence);\n        testBaseFilterType = ExposureRecipe.normalizeFilter(entry.testBaseFilterType);\n        testBaseFilterValue = ExposureRecipe.snap5(entry.testBaseFilterValue);\n        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).putString("testBaseFilterType", testBaseFilterType).putInt("testBaseFilterValue", testBaseFilterValue).apply();\n        refreshTestBaseFilterUi();''', 'use log restores recipe')

# Store recipe in reprint template and restore it into new log cards.
rep(main,
'''                .putString("printSequence", entry.printSequence == null ? "" : entry.printSequence)\n                .apply();''',
'''                .putString("printSequence", entry.printSequence == null ? "" : entry.printSequence)\n                .putString("recipeState", entry.recipeState == null ? "" : entry.recipeState)\n                .putString("testBaseFilterType", entry.testBaseFilterType == null ? ExposureRecipe.FILTER_NONE : entry.testBaseFilterType)\n                .putInt("testBaseFilterValue", entry.testBaseFilterValue)\n                .apply();''', 'reprint template recipe')
rep(main,
'''        entry.printSequence = template.getString("printSequence", "");\n    }''',
'''        entry.printSequence = template.getString("printSequence", "");\n        if (entry.recipeState == null || entry.recipeState.trim().isEmpty()) entry.recipeState = template.getString("recipeState", "");\n        if (entry.testBaseFilterType == null || ExposureRecipe.FILTER_NONE.equals(entry.testBaseFilterType)) entry.testBaseFilterType = template.getString("testBaseFilterType", ExposureRecipe.FILTER_NONE);\n        if (entry.testBaseFilterValue <= 0) entry.testBaseFilterValue = template.getInt("testBaseFilterValue", 0);\n    }''', 'template applies recipe')

# LOG automatic block: original base, operational base, filter used in test, complete plan.
rep(main,
'''                "Esposizione finale: " + exposure +\n                "\\nMetodo stampa: " + printMethod +''',
'''                "Base originale: " + recipeOriginalLabel(entry, exposure) +\n                "\\nBase operativa: " + recipeOperationalLabel(entry, exposure) +\n                "\\nFiltro provino: " + testFilterLabel(entry) +\n                "\\nMetodo stampa: " + printMethod +''', 'log automatic recipe labels')

# -----------------------------------------------------------------------------
# SonoffArmService: metadata travels locally with the already-local cycle.
# -----------------------------------------------------------------------------
rep(service,
'''    public static final String EXTRA_PRINT_SEQUENCE = "print_sequence";\n    public static final String EXTRA_STATE = "state";''',
'''    public static final String EXTRA_PRINT_SEQUENCE = "print_sequence";\n    public static final String EXTRA_RECIPE_STATE = "recipe_state";\n    public static final String EXTRA_TEST_FILTER_TYPE = "test_filter_type";\n    public static final String EXTRA_TEST_FILTER_VALUE = "test_filter_value";\n    public static final String EXTRA_STATE = "state";''', 'service recipe extras')
rep(service,
'''    private volatile PrintSequence printSequence = new PrintSequence();\n    private volatile boolean printBaseDone = false;''',
'''    private volatile PrintSequence printSequence = new PrintSequence();\n    private volatile String recipeState = "";\n    private volatile String testBaseFilterType = ExposureRecipe.FILTER_NONE;\n    private volatile int testBaseFilterValue = 0;\n    private volatile boolean printBaseDone = false;''', 'service recipe fields')
rep(service,
'''            printSequence = mode == MODE_PRINT ? PrintSequence.decode(intent.getStringExtra(EXTRA_PRINT_SEQUENCE)) : new PrintSequence();\n            printBaseDone = false;''',
'''            printSequence = mode == MODE_PRINT ? PrintSequence.decode(intent.getStringExtra(EXTRA_PRINT_SEQUENCE)) : new PrintSequence();\n            recipeState = mode == MODE_PRINT ? (intent.getStringExtra(EXTRA_RECIPE_STATE) == null ? "" : intent.getStringExtra(EXTRA_RECIPE_STATE)) : "";\n            testBaseFilterType = mode == MODE_TEST ? ExposureRecipe.normalizeFilter(intent.getStringExtra(EXTRA_TEST_FILTER_TYPE)) : ExposureRecipe.FILTER_NONE;\n            testBaseFilterValue = mode == MODE_TEST ? ExposureRecipe.snap5(intent.getIntExtra(EXTRA_TEST_FILTER_VALUE, 0)) : 0;\n            printBaseDone = false;''', 'service load recipe metadata')

rep(service,
'''            e.putString("lastPrintSequence", printSequence == null ? "" : printSequence.encode());\n            e.putLong("lastPrintAt", now);''',
'''            e.putString("lastPrintSequence", printSequence == null ? "" : printSequence.encode());\n            e.putString("lastRecipeState", recipeState == null ? "" : recipeState);\n            e.putLong("lastPrintAt", now);''', 'persist print recipe state')
rep(service,
'''            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));\n            e.putLong("lastTestAt", now);''',
'''            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));\n            e.putString("lastTestBaseFilterType", ExposureRecipe.normalizeFilter(testBaseFilterType));\n            e.putInt("lastTestBaseFilterValue", ExposureRecipe.snap5(testBaseFilterValue));\n            e.putLong("lastTestAt", now);''', 'persist test filter metadata')

# Technical log makes the filter explicit, without changing timing or network architecture.
rep(service,
'''            if (mode == MODE_PRINT && !printSequence.isEmpty()) {''',
'''            if (mode == MODE_TEST) { String tf=ExposureRecipe.filterLabel(testBaseFilterType,testBaseFilterValue); TechnicalLog.add(this, techSessionId, "FILTRO BASE PROVINO • " + ("NESSUNO".equals(tf)?"nessuno":tf)); }\n            if (mode == MODE_PRINT && !printSequence.isEmpty()) {''', 'technical test filter log')

# -----------------------------------------------------------------------------
# JPG: use automatic recipe data and distinguish starting base from final plan.
# -----------------------------------------------------------------------------
rep(jpeg, '"Densità", "Esposizione finale", "Metodo stampa"', '"Densità", "Base operativa", "Metodo stampa"', 'JPG base label')
rep(jpeg,
'''                text(e.magenta, "0"),\n                text(e.yellow, "0"),\n                text(e.density, "0"),\n                seconds(e.exposureMs),''',
'''                autoMagenta(e),\n                autoYellow(e),\n                autoDensity(e),\n                autoOperationalBase(e),''', 'JPG automatic filter values')
rep(jpeg,
'''        PrintSequence sequence = PrintSequence.decode(e.printSequence);\n        if (!sequence.isEmpty()) drawPrintSequence(c, sequence, e.exposureMs, noteTop + 126f);''',
'''        PrintSequence sequence = PrintSequence.decode(e.printSequence);\n        ExposureRecipe recipe = ExposureRecipe.decode(e.recipeState);\n        if (!sequence.isEmpty() || recipe.hasBase()) drawPrintRecipe(c, sequence, recipe, e.exposureMs, noteTop + 126f);''', 'JPG recipe draw call')

recipe_draw = r'''    private static void drawPrintRecipe(Canvas c, PrintSequence sequence, ExposureRecipe recipe, int baseMs, float top) {
        java.util.ArrayList<String> lines = new java.util.ArrayList<>();
        if (recipe != null && recipe.hasBase()) {
            lines.add("BASE ORIGINALE · " + recipe.originalLine());
            if (sequence != null && sequence.hasSplit()) {
                if (recipe.densityQuarterSteps > 0) lines.add("DENSITÀ · " + recipe.densityLabel() + " · su ricetta finale");
            } else {
                lines.add("BASE OPERATIVA · " + recipe.operationalLine(baseMs));
            }
            if (recipe.globalQuarterStops != 0) lines.add("CORREZIONE GLOBALE · " + recipe.globalLabel());
        }
        if (sequence != null) for (String s : sequence.lines(baseMs)) lines.add(s);
        if (lines.isEmpty()) return;
        Paint label = new Paint(Paint.ANTI_ALIAS_FLAG); label.setColor(ACCENT); label.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD)); label.setTextSize(25f); c.drawText("PIANO DI STAMPA",94,top+26f,label);
        Paint value = new Paint(Paint.ANTI_ALIAS_FLAG); value.setColor(INK); value.setTypeface(Typeface.create("sans-serif-condensed", Typeface.NORMAL)); value.setTextSize(21f);
        int perColumn=7; float leftX=94f,rightX=548f,y0=top+56f,dy=24f; int max=Math.min(lines.size(),perColumn*2);
        for(int i=0;i<max;i++){int row=i%perColumn;float x=i<perColumn?leftX:rightX;String s=lines.get(i);if(s.length()>45)s=s.substring(0,44)+"…";c.drawText(s,x,y0+row*dy,value);} if(lines.size()>max)c.drawText("+ "+(lines.size()-max)+" passaggi nel LOG",rightX,y0+perColumn*dy,value);
    }

    private static String autoMagenta(LogEntry e) {
        ExposureRecipe r=ExposureRecipe.decode(e==null?"":e.recipeState); if(r.hasBase()&&ExposureRecipe.FILTER_MAGENTA.equals(r.filterType))return String.valueOf(r.filterValue); return text(e==null?"":e.magenta,"0");
    }
    private static String autoYellow(LogEntry e) {
        ExposureRecipe r=ExposureRecipe.decode(e==null?"":e.recipeState); if(r.hasBase()&&ExposureRecipe.FILTER_YELLOW.equals(r.filterType))return String.valueOf(r.filterValue); return text(e==null?"":e.yellow,"0");
    }
    private static String autoDensity(LogEntry e) {
        ExposureRecipe r=ExposureRecipe.decode(e==null?"":e.recipeState); if(r.hasBase())return r.densityLabel(); return text(e==null?"":e.density,"D0");
    }
    private static String autoOperationalBase(LogEntry e) {
        ExposureRecipe r=ExposureRecipe.decode(e==null?"":e.recipeState); if(r.hasBase())return r.operationalLine(e==null?0:e.exposureMs); return seconds(e==null?0:e.exposureMs);
    }

'''
rrep(jpeg, r'    private static void drawPrintSequence\(Canvas c, PrintSequence sequence, int baseMs, float top\) \{.*?(?=    private static void drawValueFitted)', recipe_draw, 'JPG complete recipe block')

# -----------------------------------------------------------------------------
# Static release checks: no waypoint/tree feature and no new cloud dependency.
# -----------------------------------------------------------------------------
checks = {
    build:['VERSION_NAME = "0.10.0"','VERSION_CODE = "45"'],
    main:['FILTRO BASE ·','ALLUNGA TEMPI','CORREZIONE GLOBALE','ExposureRecipe','EXTRA_TEST_FILTER_TYPE','EXTRA_RECIPE_STATE','AGGIUNGI AL PIANO'],
    service:['lastTestBaseFilterType','lastRecipeState','ExposureRecipe.filterLabel','INCHING CONFERMATO'],
    logentry:['recipeState','testBaseFilterType'],
    logstore:['e.recipeState','e.testBaseFilterValue'],
    jpeg:['BASE ORIGINALE','BASE OPERATIVA','drawPrintRecipe'],
    recipe:['newBaseMs' if False else 'scaledMs','densityLabel','globalLabel']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.0 verifica fallita: {needle} in {p}')
for p in [main,service,logentry,logstore,jpeg,recipe]:
    t=rd(p).lower()
    if 'waypoint' in t or 'burn tree' in t or 'burn gerarch' in t: raise SystemExit(f'v0.10.0 funzione vietata trovata in {p}')
# Existing INTERNET permission is intentionally retained for LAN HTTP; no new manifest permissions/services are introduced here.
print('v0.10.0 TUTTE LE VERIFICHE SORGENTE OK — architettura LAN locale invariata', flush=True)
