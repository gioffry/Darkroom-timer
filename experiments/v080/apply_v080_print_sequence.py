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
timing = java / 'TimingMath.java'
jpeg = java / 'JpegCardRenderer.java'
build = work / 'build_darkroom.py'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    p=Path(p); s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.8.0 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.8.0 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    p=Path(p); s=rd(p); out,n=re.subn(pattern, lambda m: replacement(m) if callable(replacement) else replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.8.0 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.8.0 OK',label,flush=True)

# -----------------------------------------------------------------------------
# Versione 0.8.0 / code 41
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.7.7"', 'VERSION_NAME = "0.8.0"', 'version name build')
rep(build, 'VERSION_CODE = "40"', 'VERSION_CODE = "41"', 'version code build')
rep(build, '[Darkroom v0.7.7]', '[Darkroom v0.8.0]', 'build log tag')
rep(build, r'versionCode\s+40\b', r'versionCode\s+41\b', 'preflight code regex')
rep(build, r'0\.7\.7', r'0\.8\.0', 'preflight name regex')
rep(build, 'versionCode 40 / versionName 0.7.7', 'versionCode 41 / versionName 0.8.0', 'preflight message')
rep(build, 'Preflight v0.7.7 OK', 'Preflight v0.8.0 OK', 'preflight log')
rep(project/'app/build.gradle', "versionCode 40\n        versionName '0.7.7'", "versionCode 41\n        versionName '0.8.0'", 'gradle version')
rep(project/'app/src/main/AndroidManifest.xml', 'android:versionCode="40"\n    android:versionName="0.7.7"', 'android:versionCode="41"\n    android:versionName="0.8.0"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.7.7";', 'private static final String APP_VERSION = "0.8.0";', 'UI version')

# -----------------------------------------------------------------------------
# Modello dati della sequenza
# -----------------------------------------------------------------------------
print_correction = r'''package it.darkroom.timer;

import java.util.Locale;

public final class PrintCorrection {
    public static final String DODGE = "DODGE";
    public static final String BURN = "BURN";

    public String type = DODGE;
    public String label = "";
    /** DODGE: istante del cue; BURN in secondi: durata aggiuntiva. */
    public int milliseconds = 1000;
    /** BURN F-stop: quarti di stop aggiuntivi. 0 = usa milliseconds. */
    public int quarterStops = 0;

    public PrintCorrection() {}

    public PrintCorrection(String type) {
        this.type = BURN.equals(type) ? BURN : DODGE;
        if (isDodge()) milliseconds = 2000;
        else milliseconds = 1500;
    }

    public boolean isDodge() { return DODGE.equals(type); }
    public boolean isBurn() { return BURN.equals(type); }
    public boolean usesFStop() { return isBurn() && quarterStops > 0; }

    public int resolvedMs(int baseMs) {
        if (usesFStop()) return TimingMath.burnExtraMs(baseMs, quarterStops);
        return TimingMath.snap500(milliseconds, 500, 36_000_000);
    }

    public String safeLabel() {
        String v = label == null ? "" : label.trim();
        if (!v.isEmpty()) return v;
        return isDodge() ? "Zona da mascherare" : "Zona da bruciare";
    }

    public String displayLine(int baseMs) {
        if (isDodge()) return "DODGE · " + safeLabel() + " · " + seconds(milliseconds);
        if (usesFStop()) return "BURN · " + safeLabel() + " · " + TimingMath.stopLabel(quarterStops) + " · " + seconds(resolvedMs(baseMs));
        return "BURN · " + safeLabel() + " · " + seconds(resolvedMs(baseMs));
    }

    public PrintCorrection copy() {
        PrintCorrection c = new PrintCorrection();
        c.type = type;
        c.label = label;
        c.milliseconds = milliseconds;
        c.quarterStops = quarterStops;
        return c;
    }

    public static String seconds(int ms) {
        if (ms % 1000 == 0) return (ms / 1000) + ",0 s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
'''
wr(java/'PrintCorrection.java', print_correction)

print_sequence = r'''package it.darkroom.timer;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;

public final class PrintSequence {
    public final ArrayList<PrintCorrection> corrections = new ArrayList<>();

    public boolean isEmpty() { return corrections.isEmpty(); }
    public int size() { return corrections.size(); }

    public List<PrintCorrection> dodges() {
        ArrayList<PrintCorrection> out = new ArrayList<>();
        for (PrintCorrection c : corrections) if (c != null && c.isDodge()) out.add(c.copy());
        out.sort(Comparator.comparingInt(a -> a.milliseconds));
        return out;
    }

    public List<PrintCorrection> burns() {
        ArrayList<PrintCorrection> out = new ArrayList<>();
        for (PrintCorrection c : corrections) if (c != null && c.isBurn()) out.add(c.copy());
        return out;
    }

    public String encode() {
        StringBuilder b = new StringBuilder();
        for (PrintCorrection c : corrections) {
            if (c == null) continue;
            if (b.length() > 0) b.append(';');
            b.append(c.isBurn() ? 'B' : 'D').append('|')
                    .append(enc(c.label)).append('|')
                    .append(Math.max(0, c.milliseconds)).append('|')
                    .append(Math.max(0, c.quarterStops));
        }
        return b.toString();
    }

    public static PrintSequence decode(String raw) {
        PrintSequence out = new PrintSequence();
        if (raw == null || raw.trim().isEmpty()) return out;
        for (String row : raw.split(";")) {
            try {
                String[] f = row.split("\\|", -1);
                if (f.length < 4) continue;
                PrintCorrection c = new PrintCorrection("B".equals(f[0]) ? PrintCorrection.BURN : PrintCorrection.DODGE);
                c.label = dec(f[1]);
                c.milliseconds = Integer.parseInt(f[2]);
                c.quarterStops = Integer.parseInt(f[3]);
                if (c.isDodge()) c.quarterStops = 0;
                out.corrections.add(c);
            } catch (Exception ignored) {}
        }
        return out;
    }

    public String summary(int baseMs) {
        int d = dodges().size();
        int b = burns().size();
        ArrayList<String> bits = new ArrayList<>();
        if (d > 0) bits.add(d + " DODGE");
        if (b > 0) bits.add(b + " BURN");
        if (bits.isEmpty()) return "Nessuna correzione";
        return String.join(" · ", bits);
    }

    public String detail(int baseMs) {
        if (isEmpty()) return "Nessuna correzione";
        StringBuilder b = new StringBuilder();
        for (PrintCorrection c : corrections) {
            if (c == null) continue;
            if (b.length() > 0) b.append('\n');
            b.append(c.displayLine(baseMs));
        }
        return b.toString();
    }

    public String[] lines(int baseMs) {
        if (isEmpty()) return new String[0];
        ArrayList<String> out = new ArrayList<>();
        for (PrintCorrection c : corrections) if (c != null) out.add(c.displayLine(baseMs));
        return out.toArray(new String[0]);
    }

    private static String enc(String s) {
        String v = s == null ? "" : s;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(v.getBytes(StandardCharsets.UTF_8));
    }

    private static String dec(String s) {
        if (s == null || s.isEmpty()) return "";
        return new String(Base64.getUrlDecoder().decode(s), StandardCharsets.UTF_8);
    }
}
'''
wr(java/'PrintSequence.java', print_sequence)
print('v0.8.0 OK nuovi modelli sequenza', flush=True)

# TimingMath: calcolo bruciature in quarti di stop.
rep(timing,
'''    public static String toCsv(int[] values) {''',
'''    public static int burnExtraMs(int baseMs, int quarterStops) {\n        int base = snap500(baseMs, 500, 36_000_000);\n        int q = Math.max(1, Math.min(16, quarterStops));\n        double total = base * Math.pow(2.0, q / 4.0);\n        int extra = (int)Math.round(total - base);\n        return snap500(Math.max(500, extra), 500, 36_000_000);\n    }\n\n    public static String stopLabel(int quarterStops) {\n        int q = Math.max(1, Math.min(16, quarterStops));\n        int whole = q / 4;\n        int rem = q % 4;\n        String fraction = rem == 1 ? "¼" : rem == 2 ? "½" : rem == 3 ? "¾" : "";\n        String value = (whole > 0 ? String.valueOf(whole) : "") + fraction;\n        return "+" + value + " stop";\n    }\n\n    public static String toCsv(int[] values) {''', 'TimingMath burn f-stop')

# -----------------------------------------------------------------------------
# LOG: nuova colonna persistente con l'intera ricetta
# -----------------------------------------------------------------------------
rep(logentry,
'''    public String testStripTimes = "";\n}''',
'''    public String testStripTimes = "";\n    /** Sequenza completa DODGE/BURN codificata da PrintSequence. */\n    public String printSequence = "";\n}''', 'LogEntry printSequence')

rep(logstore,
'''                    e.testStripTimes = dec(f[19]);\n                } else {''',
'''                    e.testStripTimes = dec(f[19]);\n                    e.printSequence = f.length >= 21 ? dec(f[20]) : "";\n                } else {''', 'LogStore parse sequence')
rep(logstore,
'''                    if (e.testMs > 0 && e.testCount > 0) e.testStripTimes = TimingMath.toCsv(TimingMath.cumulativeSecondsSeries(e.testMs, e.testCount));\n                }''',
'''                    if (e.testMs > 0 && e.testCount > 0) e.testStripTimes = TimingMath.toCsv(TimingMath.cumulativeSecondsSeries(e.testMs, e.testCount));\n                    e.printSequence = "";\n                }''', 'LogStore legacy sequence')
rep(logstore,
'''                    .append(enc(textOr(e.testStep, TimingMath.stepLabel(testMethod)))).append('\t')\n                    .append(enc(e.testStripTimes));''',
'''                    .append(enc(textOr(e.testStep, TimingMath.stepLabel(testMethod)))).append('\t')\n                    .append(enc(e.testStripTimes)).append('\t')\n                    .append(enc(e.printSequence));''', 'LogStore write sequence')

# -----------------------------------------------------------------------------
# MainActivity: stato UI + caricamento
# -----------------------------------------------------------------------------
rep(main,
'''    private TextView printFStopBadge;\n    private TextView testFStopBadge;''',
'''    private TextView printFStopBadge;\n    private TextView testFStopBadge;\n    private TextView printSequenceSummary;\n    private Button printSequenceButton;''', 'UI sequence fields')
rep(main,
'''    private int printWidthMs = 8500;\n    private int testWidthMs = 2000;''',
'''    private int printWidthMs = 8500;\n    private PrintSequence printSequence = new PrintSequence();\n    private int testWidthMs = 2000;''', 'sequence model field')
rep(main,
'''        printWidthMs = p.getInt("printWidthMs", 8500);\n        testWidthMs = p.getInt("testWidthMs", 2000);''',
'''        printWidthMs = p.getInt("printWidthMs", 8500);\n        printSequence = PrintSequence.decode(p.getString("printSequence", ""));\n        testWidthMs = p.getInt("testWidthMs", 2000);''', 'load sequence')

# UI sotto il tempo di stampa.
rep(main,
'''        box.addView(grid, lp(-1, -2));\n        return box;\n    }\n\n    private LinearLayout buildTestPanel() {''',
'''        box.addView(grid, lp(-1, -2));\n\n        printSequenceButton = compactButton("SEQUENZA DI STAMPA");\n        printSequenceButton.setOnClickListener(v -> showPrintSequenceDialog());\n        box.addView(printSequenceButton, margin(lp(-1, dp(50)), 0, 12, 0, 0));\n        printSequenceSummary = text("", 12, darkroomMode ? RED : AMBER, false);\n        printSequenceSummary.setGravity(Gravity.CENTER);\n        printSequenceSummary.setPadding(dp(6), dp(6), dp(6), 0);\n        box.addView(printSequenceSummary, lp(-1, -2));\n        updatePrintSequenceUi();\n        return box;\n    }\n\n    private void updatePrintSequenceUi() {\n        if (printSequenceButton == null || printSequenceSummary == null) return;\n        if (printSequence == null) printSequence = new PrintSequence();\n        if (printSequence.isEmpty()) {\n            printSequenceButton.setText("SEQUENZA DI STAMPA");\n            printSequenceSummary.setText("");\n            printSequenceSummary.setVisibility(View.GONE);\n        } else {\n            printSequenceButton.setText("SEQUENZA · " + printSequence.size() + " CORREZION" + (printSequence.size() == 1 ? "E" : "I"));\n            printSequenceSummary.setText(printSequence.detail(printWidthMs));\n            printSequenceSummary.setVisibility(View.VISIBLE);\n        }\n    }\n\n    private void persistPrintSequence() {\n        if (printSequence == null) printSequence = new PrintSequence();\n        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("printSequence", printSequence.encode()).apply();\n        updatePrintSequenceUi();\n        applyModeUi();\n    }\n\n    private void showPrintSequenceDialog() {\n        final Dialog dialog = new Dialog(this);\n        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);\n        ScrollView sc = new ScrollView(this);\n        LinearLayout panel = new LinearLayout(this);\n        panel.setOrientation(LinearLayout.VERTICAL);\n        panel.setPadding(dp(18), dp(16), dp(18), dp(18));\n        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));\n        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));\n\n        panel.addView(text("SEQUENZA DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1, -2));\n        TextView base = text("ESPOSIZIONE BASE · " + formatTime(printWidthMs), 14, GREEN, true);\n        base.setPadding(0, dp(6), 0, dp(10));\n        panel.addView(base, lp(-1, -2));\n\n        if (printSequence == null || printSequence.isEmpty()) {\n            TextView empty = text("Nessuna correzione. La stampa semplice resta identica.", 12, MUTED, false);\n            empty.setPadding(0, dp(2), 0, dp(10));\n            panel.addView(empty, lp(-1, -2));\n        } else {\n            for (int x = 0; x < printSequence.corrections.size(); x++) {\n                final int index = x;\n                PrintCorrection c = printSequence.corrections.get(x);\n                Button row = compactButton(c.displayLine(printWidthMs));\n                row.setTextColor(darkroomMode ? RED : (c.isDodge() ? BLUE : AMBER));\n                if (!darkroomMode) row.setOnClickListener(v -> { dialog.dismiss(); showPrintCorrectionEditor(index); });\n                else row.setEnabled(false);\n                panel.addView(row, margin(lp(-1, dp(50)), 0, 0, 0, 7));\n            }\n        }\n\n        if (!darkroomMode) {\n            Button add = compactButton("+  AGGIUNGI CORREZIONE");\n            add.setOnClickListener(v -> {\n                dialog.dismiss();\n                showAppChoiceDialog("TIPO DI CORREZIONE",\n                        new String[]{"DODGE — mascheratura durante l’esposizione base", "BURN — esposizione aggiuntiva dopo la base"},\n                        which -> {\n                            PrintCorrection c = new PrintCorrection(which == 0 ? PrintCorrection.DODGE : PrintCorrection.BURN);\n                            printSequence.corrections.add(c);\n                            showPrintCorrectionEditor(printSequence.corrections.size() - 1);\n                        }, "ANNULLA");\n            });\n            panel.addView(add, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n\n            if (printSequence != null && !printSequence.isEmpty()) {\n                Button clear = compactButton("AZZERA SEQUENZA");\n                clear.setTextColor(RED);\n                clear.setOnClickListener(v -> showAppConfirmDialog("AZZERARE LA SEQUENZA?",\n                        "Verranno eliminate tutte le correzioni DODGE e BURN.", "AZZERA", () -> {\n                            printSequence = new PrintSequence();\n                            persistPrintSequence();\n                            dialog.dismiss();\n                        }, "ANNULLA"));\n                panel.addView(clear, margin(lp(-1, dp(46)), 0, 8, 0, 0));\n            }\n        } else {\n            TextView darkNote = text("In modalità camera oscura la sequenza è consultabile ma non modificabile, per evitare l’apertura della tastiera Android.", 11, RED, false);\n            darkNote.setGravity(Gravity.CENTER);\n            panel.addView(darkNote, margin(lp(-1, -2), 0, 8, 0, 0));\n        }\n\n        Button close = compactButton("CHIUDI");\n        close.setOnClickListener(v -> dialog.dismiss());\n        panel.addView(close, margin(lp(-1, dp(48)), 0, 8, 0, 0));\n        dialog.setContentView(sc);\n        Window w = dialog.getWindow();\n        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);\n        dialog.show();\n        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.84f));\n    }\n\n    private void showPrintCorrectionEditor(final int index) {\n        if (darkroomMode || printSequence == null || index < 0 || index >= printSequence.corrections.size()) return;\n        final PrintCorrection original = printSequence.corrections.get(index);\n        final PrintCorrection c = original.copy();\n        final Dialog dialog = new Dialog(this);\n        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);\n        LinearLayout panel = new LinearLayout(this);\n        panel.setOrientation(LinearLayout.VERTICAL);\n        panel.setPadding(dp(18), dp(16), dp(18), dp(18));\n        panel.setBackground(roundRect(CARD, 14, 1, BORDER));\n\n        panel.addView(text(c.isDodge() ? "DODGE" : "BURN", 19, c.isDodge() ? BLUE : AMBER, true), lp(-1, -2));\n        TextView explain = text(c.isDodge()\n                ? "Tempo durante il quale la zona resta mascherata. Al momento indicato: beep + vibrazione → togli la maschera."\n                : "Esposizione aggiuntiva dopo la base. Ogni BURN parte solo dopo una nuova pressione del pulsante fisico.", 12, MUTED, false);\n        explain.setPadding(0, dp(4), 0, dp(10));\n        panel.addView(explain, lp(-1, -2));\n\n        final EditText label = editField(c.isDodge() ? "Zona / maschera — es. Volto" : "Zona — es. Cielo", c.label);\n        panel.addView(label, margin(lp(-1, dp(52)), 0, 0, 0, 10));\n\n        final boolean[] useStops = {c.isBurn() && c.quarterStops > 0};\n        final int[] ms = {Math.max(500, c.milliseconds)};\n        final int[] quarters = {Math.max(1, c.quarterStops > 0 ? c.quarterStops : 1)};\n\n        if (c.isBurn()) {\n            LinearLayout methods = new LinearLayout(this);\n            methods.setOrientation(LinearLayout.HORIZONTAL);\n            final Button secondsMode = compactButton("SECONDI");\n            final Button stopMode = compactButton("F-STOP");\n            methods.addView(secondsMode, margin(lp(0, dp(46), 1f), 0, 0, dp(4), 0));\n            methods.addView(stopMode, margin(lp(0, dp(46), 1f), dp(4), 0, 0, 0));\n            panel.addView(methods, margin(lp(-1, -2), 0, 0, 0, 10));\n            final Runnable styleMethods = () -> {\n                secondsMode.setBackground(roundRect(!useStops[0] ? AMBER : BUTTON, 8, 1, BORDER));\n                stopMode.setBackground(roundRect(useStops[0] ? AMBER : BUTTON, 8, 1, BORDER));\n                secondsMode.setTextColor(!useStops[0] ? Color.BLACK : TEXT_PRIMARY);\n                stopMode.setTextColor(useStops[0] ? Color.BLACK : TEXT_PRIMARY);\n            };\n            secondsMode.setOnClickListener(v -> { useStops[0] = false; styleMethods.run(); });\n            stopMode.setOnClickListener(v -> { useStops[0] = true; styleMethods.run(); });\n            styleMethods.run();\n        }\n\n        LinearLayout selector = new LinearLayout(this);\n        selector.setOrientation(LinearLayout.HORIZONTAL);\n        selector.setGravity(Gravity.CENTER);\n        Button minus = smallButton("−");\n        Button plus = smallButton("+");\n        final TextView value = text("", 30, c.isDodge() ? BLUE : AMBER, true);\n        value.setGravity(Gravity.CENTER);\n        selector.addView(minus, lp(dp(62), dp(58)));\n        selector.addView(value, lp(0, dp(64), 1f));\n        selector.addView(plus, lp(dp(62), dp(58)));\n        panel.addView(selector, lp(-1, -2));\n\n        final Runnable refresh = () -> {\n            if (c.isDodge()) value.setText(formatTime(ms[0]));\n            else if (useStops[0]) value.setText(TimingMath.stopLabel(quarters[0]) + "  →  " + formatTime(TimingMath.burnExtraMs(printWidthMs, quarters[0])));\n            else value.setText(formatTime(ms[0]));\n        };\n        minus.setOnClickListener(v -> {\n            if (c.isBurn() && useStops[0]) quarters[0] = Math.max(1, quarters[0] - 1);\n            else ms[0] = Math.max(500, ms[0] - 500);\n            refresh.run();\n        });\n        plus.setOnClickListener(v -> {\n            if (c.isBurn() && useStops[0]) quarters[0] = Math.min(16, quarters[0] + 1);\n            else ms[0] = Math.min(36_000_000, ms[0] + 500);\n            refresh.run();\n        });\n        refresh.run();\n\n        if (c.isBurn()) {\n            TextView calc = text("In F-stop il tempo aggiuntivo viene ricalcolato dalla esposizione base e arrotondato a 0,5 s per il SONOFF.", 11, MUTED, false);\n            calc.setGravity(Gravity.CENTER);\n            panel.addView(calc, margin(lp(-1, -2), 0, 6, 0, 10));\n        }\n\n        Button save = compactButton("SALVA CORREZIONE");\n        save.setBackground(roundRect(c.isDodge() ? BLUE : AMBER, 9, 0, 0));\n        save.setTextColor(Color.BLACK);\n        save.setOnClickListener(v -> {\n            String name = label.getText().toString().trim();\n            c.label = name.isEmpty() ? (c.isDodge() ? "Zona da mascherare" : "Zona da bruciare") : name;\n            if (c.isDodge()) {\n                if (printWidthMs <= 500) { Toast.makeText(this, "Il DODGE richiede una esposizione base di almeno 1,0 s", Toast.LENGTH_LONG).show(); return; }\n                c.milliseconds = TimingMath.snap500(ms[0], 500, Math.max(500, printWidthMs - 500));\n                c.quarterStops = 0;\n            } else if (useStops[0]) {\n                c.quarterStops = quarters[0];\n                c.milliseconds = TimingMath.burnExtraMs(printWidthMs, quarters[0]);\n            } else {\n                c.quarterStops = 0;\n                c.milliseconds = TimingMath.snap500(ms[0], 500, 36_000_000);\n            }\n            printSequence.corrections.set(index, c);\n            persistPrintSequence();\n            dialog.dismiss();\n            showPrintSequenceDialog();\n        });\n        panel.addView(save, margin(lp(-1, dp(52)), 0, 12, 0, 0));\n\n        Button delete = compactButton("ELIMINA CORREZIONE");\n        delete.setTextColor(RED);\n        delete.setOnClickListener(v -> {\n            printSequence.corrections.remove(index);\n            persistPrintSequence();\n            dialog.dismiss();\n            showPrintSequenceDialog();\n        });\n        panel.addView(delete, margin(lp(-1, dp(46)), 0, 8, 0, 0));\n        Button cancel = compactButton("ANNULLA");\n        cancel.setOnClickListener(v -> dialog.dismiss());\n        panel.addView(cancel, margin(lp(-1, dp(46)), 0, 6, 0, 0));\n\n        dialog.setContentView(panel);\n        Window w = dialog.getWindow();\n        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);\n        dialog.show();\n        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), ViewGroup.LayoutParams.WRAP_CONTENT);\n    }\n\n    private boolean validatePrintSequenceForBase() {\n        if (printSequence == null || printSequence.isEmpty()) return true;\n        for (PrintCorrection c : printSequence.dodges()) {\n            if (c.milliseconds >= printWidthMs) {\n                setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": il cue deve avvenire prima della fine della esposizione base", RED);\n                return false;\n            }\n        }\n        return true;\n    }\n\n    private LinearLayout buildTestPanel() {''', 'print sequence UI')

# Stato WAITING_BURN va trattato come ciclo attivo e mostrato distintamente.
rep(main,
'''        boolean cancellable = SonoffArmService.STATE_ARMED.equals(state)\n                || SonoffArmService.STATE_ARMING.equals(state)\n                || SonoffArmService.STATE_EXPOSING.equals(state)\n                || SonoffArmService.STATE_PAUSING.equals(state);''',
'''        boolean cancellable = SonoffArmService.STATE_ARMED.equals(state)\n                || SonoffArmService.STATE_ARMING.equals(state)\n                || SonoffArmService.STATE_EXPOSING.equals(state)\n                || SonoffArmService.STATE_PAUSING.equals(state)\n                || SonoffArmService.STATE_WAITING_BURN.equals(state);''', 'waiting burn cancellable')
rep(main,
'''        } else if (SonoffArmService.STATE_PAUSING.equals(state)) {\n            title = "PAUSA PROVINO";\n            accent = BLUE;\n        } else if (SonoffArmService.STATE_DISARMING.equals(state)) {''',
'''        } else if (SonoffArmService.STATE_PAUSING.equals(state)) {\n            title = "PAUSA PROVINO";\n            accent = BLUE;\n        } else if (SonoffArmService.STATE_WAITING_BURN.equals(state)) {\n            title = "BRUCIATURA — PREPARA MASCHERA";\n            accent = darkroomMode ? RED : AMBER;\n        } else if (SonoffArmService.STATE_DISARMING.equals(state)) {''', 'waiting burn presentation')

# Pulsante ARMA comunica la presenza della sequenza.
rep(main,
'''            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)\n                    : (TimingMath.isFStop(timingMethod)''',
'''            actionButton.setText(print ? ("ARMA STAMPA • " + formatTime(printWidthMs) + (printSequence != null && !printSequence.isEmpty() ? " · SEQ " + printSequence.size() : ""))\n                    : (TimingMath.isFStop(timingMethod)''', 'ARMA sequence label')

# Arm: validazione + payload sequenza.
rep(main,
'''        if (safelightAuto) {\n            DeviceConfig safe = SafelightConfig.load(this);''',
'''        if (mode == MODE_PRINT && !validatePrintSequenceForBase()) return;\n        if (safelightAuto) {\n            DeviceConfig safe = SafelightConfig.load(this);''', 'arm validate sequence')
rep(main,
'''            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);''',
'''            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_PRINT_SEQUENCE, printSequence == null ? "" : printSequence.encode());''', 'arm pass sequence')

# Se cambia il tempo base, aggiorna immediatamente i tempi BURN F-stop mostrati.
rep(main,
'''        printTimeText.setText(formatTime(printWidthMs));\n        applyModeUi();''',
'''        printTimeText.setText(formatTime(printWidthMs));\n        updatePrintSequenceUi();\n        applyModeUi();''', 'update sequence on base change')

# LOG sessione: conserva la ricetta completata.
rep(main,
'''            e.exposureStep = p.getString("lastPrintStep", TimingMath.stepLabel(e.exposureMethod));\n            if (testAt > 0) {''',
'''            e.exposureStep = p.getString("lastPrintStep", TimingMath.stepLabel(e.exposureMethod));\n            e.printSequence = p.getString("lastPrintSequence", "");\n            if (testAt > 0) {''', 'new log entry sequence')

# USA PER STAMPA: ricarica sequenza + template futuro.
rep(main,
'''        setPrintTime(entry.exposureMs);\n        getSharedPreferences("log_reprint", MODE_PRIVATE).edit()''',
'''        setPrintTime(entry.exposureMs);\n        printSequence = PrintSequence.decode(entry.printSequence);\n        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("printSequence", printSequence.encode()).apply();\n        updatePrintSequenceUi();\n        getSharedPreferences("log_reprint", MODE_PRIVATE).edit()''', 'use log restores sequence')
rep(main,
'''                .putString("notes", entry.notes == null ? "" : entry.notes)\n                .apply();''',
'''                .putString("notes", entry.notes == null ? "" : entry.notes)\n                .putString("printSequence", entry.printSequence == null ? "" : entry.printSequence)\n                .apply();''', 'reprint template saves sequence')
rep(main,
'''        Toast.makeText(this, "Tempo " + formatTime(entry.exposureMs) + " caricato in STAMPA", Toast.LENGTH_SHORT).show();''',
'''        Toast.makeText(this, "Stampa " + formatTime(entry.exposureMs) + (printSequence.isEmpty() ? "" : " + sequenza completa") + " caricata in STAMPA", Toast.LENGTH_SHORT).show();''', 'use log toast')
rep(main,
'''        entry.notes = template.getString("notes", "");\n    }''',
'''        entry.notes = template.getString("notes", "");\n        entry.printSequence = template.getString("printSequence", "");\n    }''', 'template applies sequence')

# Editor LOG: mostra tutta la ricetta nei dati automatici.
rep(main,
'''        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) : "—";\n        TextView autoValues = text(''',
'''        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) : "—";\n        PrintSequence savedSequence = PrintSequence.decode(entry.printSequence);\n        String sequenceRecipe = savedSequence.isEmpty() ? "—" : ("\\n" + savedSequence.detail(entry.exposureMs));\n        TextView autoValues = text(''', 'log editor sequence variable')
rep(main,
'''                "\nTempi strisce: " + strips +\n                "\nData: " + formatDate(entry.timestamp) +''',
'''                "\nTempi strisce: " + strips +\n                "\nSequenza di stampa: " + sequenceRecipe +\n                "\nData: " + formatDate(entry.timestamp) +''', 'log editor sequence display')

# -----------------------------------------------------------------------------
# SonoffArmService: motore sequenza, DODGE cues, BURN manuali
# -----------------------------------------------------------------------------
rep(service,
'''    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";\n    public static final String EXTRA_STATE = "state";''',
'''    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";\n    public static final String EXTRA_PRINT_SEQUENCE = "print_sequence";\n    public static final String EXTRA_STATE = "state";''', 'service sequence extra')
rep(service,
'''    public static final String STATE_PAUSING = "PAUSING";\n    public static final String STATE_DISARMING = "DISARMING";''',
'''    public static final String STATE_PAUSING = "PAUSING";\n    public static final String STATE_WAITING_BURN = "WAITING_BURN";\n    public static final String STATE_DISARMING = "DISARMING";''', 'service waiting state')
rep(service,
'''    private final ScheduledExecutorService io = Executors.newSingleThreadScheduledExecutor();\n    private ScheduledFuture<?> pollTask;''',
'''    private final ScheduledExecutorService io = Executors.newSingleThreadScheduledExecutor();\n    private final ScheduledExecutorService cueIo = Executors.newSingleThreadScheduledExecutor();\n    private final java.util.concurrent.CopyOnWriteArrayList<ScheduledFuture<?>> dodgeCueTasks = new java.util.concurrent.CopyOnWriteArrayList<>();\n    private ScheduledFuture<?> pollTask;''', 'cue executor')
rep(service,
'''    private volatile int widthMs = 8500;\n    private volatile int count = 7;''',
'''    private volatile int widthMs = 8500;\n    private volatile PrintSequence printSequence = new PrintSequence();\n    private volatile boolean printBaseDone = false;\n    private volatile int burnIndex = -1;\n    private volatile int count = 7;''', 'service sequence fields')

# Caricamento sequenza ad ogni armamento.
rep(service,
'''            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));\n            count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));''',
'''            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));\n            printSequence = mode == MODE_PRINT ? PrintSequence.decode(intent.getStringExtra(EXTRA_PRINT_SEQUENCE)) : new PrintSequence();\n            printBaseDone = false;\n            burnIndex = -1;\n            cancelDodgeCues();\n            count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));''', 'service load sequence')
rep(service,
'''            lastObservedOnAt = 0L;\n            lastObservedOffAt = 0L;''',
'''            lastObservedOnAt = 0L;\n            lastObservedOffAt = 0L;\n            if (mode == MODE_PRINT && !printSequence.isEmpty()) {\n                TechnicalLog.add(this, techSessionId, "SEQUENZA DI STAMPA • " + printSequence.summary(widthMs) + " • " + printSequence.detail(widthMs).replace('\\n', ' • '));\n            }''', 'tech log sequence')

# Alla vera accensione: safelight corretta per base/burn + cue DODGE.
rep(service,
'''                    if (safelightAuto && completed == 0) {\n                        try {\n                            captureAndDimSafelightForCycle();\n                        } catch (Exception e) {\n                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: stato iniziale non acquisito — " + readable(e));\n                        }\n                    }\n                    lastObservedOnAt = observedAt;''',
'''                    if (safelightAuto) {\n                        try {\n                            if (mode == MODE_PRINT && printBaseDone) dimSafelightForExposure();\n                            else if (!cycleSafelightCaptured) captureAndDimSafelightForCycle();\n                        } catch (Exception e) {\n                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: sincronizzazione non riuscita — " + readable(e));\n                        }\n                    }\n                    lastObservedOnAt = observedAt;\n                    if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) scheduleDodgeCues(observedAt);''', 'ON handles sequence safelight cues')
rep(service,
'''                    String msg = mode == MODE_PRINT\n                            ? "ESPOSIZIONE IN CORSO — " + seconds(widthMs)\n                            : (TimingMath.isFStop(timingMethod) ?''',
'''                    String msg = mode == MODE_PRINT\n                            ? (printBaseDone ? burnExposureMessage() : (printSequence != null && !printSequence.isEmpty() ? "ESPOSIZIONE BASE IN CORSO — " + seconds(widthMs) : "ESPOSIZIONE IN CORSO — " + seconds(widthMs)))\n                            : (TimingMath.isFStop(timingMethod) ?''', 'exposure message sequence')

# Al termine: se sequenza stampa gestisce prima base e poi burn manuali.
rep(service,
'''        seenOn.set(false);\n        completed++;\n\n        if (mode == MODE_PRINT || completed >= count) {''',
'''        seenOn.set(false);\n\n        if (mode == MODE_PRINT && printSequence != null && !printSequence.isEmpty()) {\n            if (!printBaseDone) {\n                printBaseDone = true;\n                cancelDodgeCues();\n                java.util.List<PrintCorrection> burns = printSequence.burns();\n                if (!burns.isEmpty()) {\n                    burnIndex = 0;\n                    prepareBurnStep();\n                    return;\n                }\n            } else {\n                burnIndex++;\n                java.util.List<PrintCorrection> burns = printSequence.burns();\n                if (burnIndex < burns.size()) {\n                    prepareBurnStep();\n                    return;\n                }\n            }\n        }\n\n        completed++;\n\n        if (mode == MODE_PRINT || completed >= count) {''', 'onExposureFinished sequence branch')

# Persistenza log_session della ricetta realmente eseguita.
rep(service,
'''            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));\n            e.putLong("lastPrintAt", now);''',
'''            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));\n            e.putString("lastPrintSequence", printSequence == null ? "" : printSequence.encode());\n            e.putLong("lastPrintAt", now);''', 'persist completed sequence')

# Cancel/disarm non forza mai safelight ON: ripristina lo stato originario catturato.
rep(service,
'''            if (safelightAuto) {\n                setSafelightConfirmed(true);\n                TechnicalLog.add(this, techSessionId, "SAFELIGHT ON confermata durante ripristino");\n            }\n            pulseOffWithWatchdog();''',
'''            restoreSafelightBestEffort();\n            pulseOffWithWatchdog();''', 'disarm preserves safelight state')

# Helper della sequenza prima di startInterlockMonitor.
anchor='''    private void startInterlockMonitor() {'''
helpers=r'''    private void prepareBurnStep() {
        cancelPoll();
        cancelDodgeCues();
        java.util.List<PrintCorrection> burns = printSequence == null ? new java.util.ArrayList<>() : printSequence.burns();
        if (burnIndex < 0 || burnIndex >= burns.size()) return;
        PrintCorrection burn = burns.get(burnIndex);
        try {
            temporarilyRestoreSafelightForPause();
            currentPulseWidthMs = burn.resolvedMs(widthMs);
            SonoffHttp.pulseOn(device, currentPulseWidthMs);
            TechnicalLog.add(this, techSessionId, "BURN preparato " + (burnIndex + 1) + "/" + burns.size() + " • " + burn.displayLine(widthMs));
            String msg = "BRUCIA " + burn.safeLabel().toUpperCase(Locale.ITALY) + " — "
                    + (burn.usesFStop() ? TimingMath.stopLabel(burn.quarterStops) + " · " : "")
                    + seconds(currentPulseWidthMs) + "\nPosiziona la maschera e premi il pulsante fisico";
            broadcast(STATE_WAITING_BURN, msg);
            updateNotification(msg.replace('\n', ' '));
            seenOn.set(false);
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile preparare la bruciatura " + (burnIndex + 1) + ": " + readable(e));
        }
    }

    private String burnExposureMessage() {
        java.util.List<PrintCorrection> burns = printSequence == null ? new java.util.ArrayList<>() : printSequence.burns();
        if (burnIndex < 0 || burnIndex >= burns.size()) return "BRUCIATURA IN CORSO";
        PrintCorrection burn = burns.get(burnIndex);
        return "BRUCIATURA " + (burnIndex + 1) + "/" + burns.size() + " — " + burn.safeLabel() + " · " + seconds(currentPulseWidthMs);
    }

    private void scheduleDodgeCues(long observedOnAt) {
        cancelDodgeCues();
        if (printSequence == null || printSequence.isEmpty()) return;
        long elapsed = Math.max(0L, System.currentTimeMillis() - observedOnAt);
        for (PrintCorrection dodge : printSequence.dodges()) {
            if (dodge.milliseconds <= 0 || dodge.milliseconds >= widthMs) continue;
            long delay = Math.max(0L, dodge.milliseconds - elapsed);
            ScheduledFuture<?> f = cueIo.schedule(() -> {
                if (completing.get() || printBaseDone) return;
                String msg = "TOGLI MASCHERA — " + dodge.safeLabel().toUpperCase(Locale.ITALY) + " · " + seconds(dodge.milliseconds);
                TechnicalLog.add(this, techSessionId, "DODGE CUE — " + msg);
                dodgeCueFeedback();
                broadcast(STATE_EXPOSING, msg);
                updateNotification(msg);
            }, delay, TimeUnit.MILLISECONDS);
            dodgeCueTasks.add(f);
        }
    }

    private void cancelDodgeCues() {
        for (ScheduledFuture<?> f : dodgeCueTasks) if (f != null) f.cancel(false);
        dodgeCueTasks.clear();
    }

    private void dodgeCueFeedback() {
        try {
            if (getSharedPreferences("ui", MODE_PRIVATE).getBoolean("feedbackBeep", true)) {
                ToneGenerator tone = new ToneGenerator(AudioManager.STREAM_NOTIFICATION, 65);
                tone.startTone(ToneGenerator.TONE_PROP_BEEP2, 150);
                try { Thread.sleep(170L); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
                tone.release();
            }
        } catch (Exception ignored) {}
        try {
            android.os.Vibrator vibrator = (android.os.Vibrator) getSystemService(VIBRATOR_SERVICE);
            if (vibrator != null && vibrator.hasVibrator()) {
                if (android.os.Build.VERSION.SDK_INT >= 26) vibrator.vibrate(android.os.VibrationEffect.createOneShot(180L, 160));
                else vibrator.vibrate(180L);
            }
        } catch (Exception ignored) {}
    }

    private void temporarilyRestoreSafelightForPause() throws Exception {
        if (!safelightAuto || !cycleSafelightCaptured || !restoreSafelightAfterCycle) return;
        setSafelightConfirmed(true);
        TechnicalLog.add(this, techSessionId, "SAFELIGHT temporaneamente ON per preparare la bruciatura");
    }

    private void dimSafelightForExposure() throws Exception {
        if (!safelightAuto || !cycleSafelightCaptured || !restoreSafelightAfterCycle) return;
        setSafelightConfirmed(false);
        TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF per nuova esposizione della sequenza");
    }

'''+anchor
rep(service, anchor, helpers, 'sequence service helpers')

# Tutte le cancellazioni timer eliminano anche i cue DODGE.
rep(service,
'''    private void cancelTimers() {\n        cancelPoll();''',
'''    private void cancelTimers() {\n        cancelPoll();\n        cancelDodgeCues();''', 'cancel dodge cues')

# Distruzione: chiude anche executor cue.
rep(service,
'''    @Override public void onDestroy() {\n        cancelTimers();\n        cancelInterlockMonitor();''',
'''    @Override public void onDestroy() {\n        cancelTimers();\n        cancelInterlockMonitor();\n        cueIo.shutdownNow();''', 'shutdown cue executor')

# -----------------------------------------------------------------------------
# JPG: ricetta DODGE/BURN in due colonne
# -----------------------------------------------------------------------------
rep(jpeg,
'''        drawNotes(c, note, 210, (int)(noteTop + 10), WIDTH - 300, 112);\n\n        p.setStyle(Paint.Style.FILL);''',
'''        drawNotes(c, note, 210, (int)(noteTop + 10), WIDTH - 300, 112);\n        PrintSequence sequence = PrintSequence.decode(e.printSequence);\n        if (!sequence.isEmpty()) drawPrintSequence(c, sequence, e.exposureMs, noteTop + 126f);\n\n        p.setStyle(Paint.Style.FILL);''', 'JPG sequence draw call')
rep(jpeg,
'''    private static void drawValueFitted(Canvas c, String s, float x, float baseline, float maxWidth, Paint p) {''',
'''    private static void drawPrintSequence(Canvas c, PrintSequence sequence, int baseMs, float top) {\n        String[] lines = sequence.lines(baseMs);\n        if (lines.length == 0) return;\n        Paint label = new Paint(Paint.ANTI_ALIAS_FLAG);\n        label.setColor(ACCENT);\n        label.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));\n        label.setTextSize(25f);\n        c.drawText("SEQUENZA DI STAMPA", 94, top + 26f, label);\n\n        Paint value = new Paint(Paint.ANTI_ALIAS_FLAG);\n        value.setColor(INK);\n        value.setTypeface(Typeface.create("sans-serif-condensed", Typeface.NORMAL));\n        value.setTextSize(21f);\n        int perColumn = 7;\n        float leftX = 94f;\n        float rightX = 548f;\n        float y0 = top + 56f;\n        float dy = 24f;\n        int max = Math.min(lines.length, perColumn * 2);\n        for (int i = 0; i < max; i++) {\n            int row = i % perColumn;\n            float x = i < perColumn ? leftX : rightX;\n            String s = lines[i];\n            if (s.length() > 45) s = s.substring(0, 44) + "…";\n            c.drawText(s, x, y0 + row * dy, value);\n        }\n        if (lines.length > max) c.drawText("+ " + (lines.length - max) + " correzioni nel LOG", rightX, y0 + perColumn * dy, value);\n    }\n\n    private static void drawValueFitted(Canvas c, String s, float x, float baseline, float maxWidth, Paint p) {''', 'JPG sequence helper')

# Static checks
checks = {
    build: ['VERSION_NAME = "0.8.0"', 'VERSION_CODE = "41"'],
    main: ['SEQUENZA DI STAMPA', 'EXTRA_PRINT_SEQUENCE', 'printSequence.detail', 'showPrintCorrectionEditor', 'validatePrintSequenceForBase'],
    service: ['STATE_WAITING_BURN', 'prepareBurnStep()', 'scheduleDodgeCues', 'temporarilyRestoreSafelightForPause', 'lastPrintSequence'],
    logentry: ['printSequence'],
    logstore: ['e.printSequence'],
    timing: ['burnExtraMs', 'stopLabel'],
    jpeg: ['drawPrintSequence']
}
for p, needles in checks.items():
    text = rd(p)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.8.0 verifica fallita: {needle} in {p}')
print('v0.8.0 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
