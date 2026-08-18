#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
print_correction = java / 'PrintCorrection.java'
print_sequence = java / 'PrintSequence.java'
split_grade = java / 'SplitGradePlan.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.9.0 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.9.0 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.9.0 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.9.0 OK', label, flush=True)

# -----------------------------------------------------------------------------
# Versione 0.9.0 / code 43
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.8.1"', 'VERSION_NAME = "0.9.0"', 'version name build')
rep(build, 'VERSION_CODE = "42"', 'VERSION_CODE = "43"', 'version code build')
rep(build, '[Darkroom v0.8.1]', '[Darkroom v0.9.0]', 'build log tag')
rep(build, r'versionCode\s+42\b', r'versionCode\s+43\b', 'preflight code regex')
rep(build, r'0\.8\.1', r'0\.9\.0', 'preflight name regex')
rep(build, 'versionCode 42 / versionName 0.8.1', 'versionCode 43 / versionName 0.9.0', 'preflight message')
rep(build, 'Preflight v0.8.1 OK', 'Preflight v0.9.0 OK', 'preflight log')
rep(gradle, "versionCode 42\n        versionName '0.8.1'", "versionCode 43\n        versionName '0.9.0'", 'gradle version')
rep(manifest, 'android:versionCode="42"\n    android:versionName="0.8.1"', 'android:versionCode="43"\n    android:versionName="0.9.0"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.8.1";', 'private static final String APP_VERSION = "0.9.0";', 'UI version')

# -----------------------------------------------------------------------------
# Modello Split Grade + correzioni associate alla fase
# -----------------------------------------------------------------------------
wr(split_grade, r'''package it.darkroom.timer;

import java.util.Locale;

public final class SplitGradePlan {
    public boolean enabled = false;
    public int softYellow = 50;
    public int softMs = 6000;
    public int hardMagenta = 70;
    public int hardMs = 3000;

    public SplitGradePlan copy() {
        SplitGradePlan s = new SplitGradePlan();
        s.enabled = enabled;
        s.softYellow = softYellow;
        s.softMs = softMs;
        s.hardMagenta = hardMagenta;
        s.hardMs = hardMs;
        return s;
    }

    public void sanitize() {
        softYellow = snap5(softYellow);
        hardMagenta = snap5(hardMagenta);
        softMs = TimingMath.snap500(softMs, 500, 36_000_000);
        hardMs = TimingMath.snap500(hardMs, 500, 36_000_000);
    }

    public int totalMs() { return enabled ? softMs + hardMs : 0; }

    public String softLine() { return "SPLIT · MORBIDA · Y " + softYellow + " · " + seconds(softMs); }
    public String hardLine() { return "SPLIT · DURA · M " + hardMagenta + " · " + seconds(hardMs); }
    public String softPrompt() { return "Imposta Giallo " + softYellow + ". Poi premi il pulsante."; }
    public String hardPrompt() { return "Imposta Magenta " + hardMagenta + ". Poi premi il pulsante."; }

    private static int snap5(int v) {
        int x = Math.max(0, Math.min(200, v));
        return Math.round(x / 5f) * 5;
    }

    private static String seconds(int ms) {
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
''')

wr(print_correction, r'''package it.darkroom.timer;

import java.util.Locale;

public final class PrintCorrection {
    public static final String DODGE = "DODGE";
    public static final String BURN = "BURN";
    public static final String PHASE_BASE = "BASE";
    public static final String PHASE_SOFT = "SOFT";
    public static final String PHASE_HARD = "HARD";

    public String type = DODGE;
    public String label = "";
    public int milliseconds = 1000;
    public int quarterStops = 0;
    public String phase = PHASE_BASE;

    public PrintCorrection() {}
    public PrintCorrection(String type) {
        this.type = BURN.equals(type) ? BURN : DODGE;
        milliseconds = isDodge() ? 2000 : 1500;
    }

    public boolean isDodge() { return DODGE.equals(type); }
    public boolean isBurn() { return BURN.equals(type); }
    public boolean usesFStop() { return quarterStops > 0; }
    public boolean isSoft() { return PHASE_SOFT.equals(phase); }
    public boolean isHard() { return PHASE_HARD.equals(phase); }

    public int resolvedMs(int baseMs) {
        if (!usesFStop()) return TimingMath.snap500(milliseconds, 500, 36_000_000);
        return isDodge() ? TimingMath.dodgeMaskMs(baseMs, quarterStops)
                : TimingMath.burnExtraMs(baseMs, quarterStops);
    }

    public String safeLabel() {
        String v = label == null ? "" : label.trim();
        if (!v.isEmpty()) return v;
        return isDodge() ? "Zona da mascherare" : "Zona da bruciare";
    }

    public String displayLine(int baseMs) { return displayLine(baseMs, false); }
    public String displayLine(int baseMs, boolean showPhase) {
        String amount = usesFStop()
                ? (isDodge() ? TimingMath.dodgeStopLabel(quarterStops) : TimingMath.stopLabel(quarterStops))
                : seconds(resolvedMs(baseMs));
        String suffix = showPhase ? " · " + (isHard() ? "DURA" : "MORBIDA") : "";
        return (isDodge() ? "DODGE · " : "BURN · ") + safeLabel() + " · " + amount + suffix;
    }

    public PrintCorrection copy() {
        PrintCorrection c = new PrintCorrection();
        c.type = type;
        c.label = label;
        c.milliseconds = milliseconds;
        c.quarterStops = quarterStops;
        c.phase = phase;
        return c;
    }

    public static String seconds(int ms) {
        if (ms % 1000 == 0) return (ms / 1000) + ",0 s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
''')

wr(print_sequence, r'''package it.darkroom.timer;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;

public final class PrintSequence {
    public final ArrayList<PrintCorrection> corrections = new ArrayList<>();
    public SplitGradePlan split = new SplitGradePlan();

    public boolean hasSplit() { return split != null && split.enabled; }
    public boolean isEmpty() { return !hasSplit() && corrections.isEmpty(); }
    public int size() { return corrections.size() + (hasSplit() ? 1 : 0); }

    public int baseMsForPhase(String phase, int fallbackBaseMs) {
        if (!hasSplit()) return fallbackBaseMs;
        return PrintCorrection.PHASE_HARD.equals(phase) ? split.hardMs : split.softMs;
    }

    public int baseMsFor(PrintCorrection c, int fallbackBaseMs) {
        return baseMsForPhase(c == null ? PrintCorrection.PHASE_BASE : c.phase, fallbackBaseMs);
    }

    public List<PrintCorrection> dodges() {
        ArrayList<PrintCorrection> out = new ArrayList<>();
        for (PrintCorrection c : corrections) if (c != null && c.isDodge()) out.add(c.copy());
        out.sort(Comparator.comparingInt(a -> a.milliseconds));
        return out;
    }

    public List<PrintCorrection> dodgesForPhase(String phase) {
        ArrayList<PrintCorrection> out = new ArrayList<>();
        for (PrintCorrection c : corrections) {
            if (c == null || !c.isDodge()) continue;
            if (!hasSplit() || phase.equals(c.phase)) out.add(c.copy());
        }
        final int base = baseMsForPhase(phase, 8500);
        out.sort(Comparator.comparingInt(a -> a.resolvedMs(base)));
        return out;
    }

    public List<PrintCorrection> burns() {
        ArrayList<PrintCorrection> out = new ArrayList<>();
        for (PrintCorrection c : corrections) if (c != null && c.isBurn()) out.add(c.copy());
        return out;
    }

    public String encode() {
        StringBuilder b = new StringBuilder();
        if (hasSplit()) {
            split.sanitize();
            b.append('S').append('|').append(split.softYellow).append('|').append(split.softMs)
                    .append('|').append(split.hardMagenta).append('|').append(split.hardMs);
        }
        for (PrintCorrection c : corrections) {
            if (c == null) continue;
            if (b.length() > 0) b.append(';');
            b.append(c.isBurn() ? 'B' : 'D').append('|')
                    .append(enc(c.label)).append('|')
                    .append(Math.max(0, c.milliseconds)).append('|')
                    .append(Math.max(0, c.quarterStops)).append('|')
                    .append(c.phase == null ? PrintCorrection.PHASE_BASE : c.phase);
        }
        return b.toString();
    }

    public static PrintSequence decode(String raw) {
        PrintSequence out = new PrintSequence();
        if (raw == null || raw.trim().isEmpty()) return out;
        for (String row : raw.split(";")) {
            try {
                String[] f = row.split("\\|", -1);
                if (f.length >= 5 && "S".equals(f[0])) {
                    out.split.enabled = true;
                    out.split.softYellow = Integer.parseInt(f[1]);
                    out.split.softMs = Integer.parseInt(f[2]);
                    out.split.hardMagenta = Integer.parseInt(f[3]);
                    out.split.hardMs = Integer.parseInt(f[4]);
                    out.split.sanitize();
                    continue;
                }
                if (f.length < 4) continue;
                PrintCorrection c = new PrintCorrection("B".equals(f[0]) ? PrintCorrection.BURN : PrintCorrection.DODGE);
                c.label = dec(f[1]);
                c.milliseconds = Integer.parseInt(f[2]);
                c.quarterStops = Integer.parseInt(f[3]);
                c.phase = f.length >= 5 && (PrintCorrection.PHASE_SOFT.equals(f[4]) || PrintCorrection.PHASE_HARD.equals(f[4]))
                        ? f[4] : PrintCorrection.PHASE_BASE;
                out.corrections.add(c);
            } catch (Exception ignored) {}
        }
        if (out.hasSplit()) {
            for (PrintCorrection c : out.corrections) if (PrintCorrection.PHASE_BASE.equals(c.phase)) c.phase = PrintCorrection.PHASE_SOFT;
        }
        return out;
    }

    public String summary(int baseMs) {
        int d = dodges().size();
        int b = burns().size();
        ArrayList<String> bits = new ArrayList<>();
        if (hasSplit()) bits.add("SPLIT GRADE");
        if (d > 0) bits.add(d + " DODGE");
        if (b > 0) bits.add(b + " BURN");
        if (bits.isEmpty()) return "Nessuna correzione";
        return String.join(" · ", bits);
    }

    public String detail(int baseMs) {
        if (isEmpty()) return "Nessuna correzione";
        StringBuilder b = new StringBuilder();
        if (hasSplit()) {
            b.append(split.softLine()).append('\n').append(split.hardLine());
        }
        for (PrintCorrection c : corrections) {
            if (c == null) continue;
            if (b.length() > 0) b.append('\n');
            b.append(c.displayLine(baseMsFor(c, baseMs), hasSplit()));
        }
        return b.toString();
    }

    public String[] lines(int baseMs) {
        if (isEmpty()) return new String[0];
        ArrayList<String> out = new ArrayList<>();
        if (hasSplit()) {
            out.add(split.softLine());
            out.add(split.hardLine());
        }
        for (PrintCorrection c : corrections) if (c != null) out.add(c.displayLine(baseMsFor(c, baseMs), hasSplit()));
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
''')
print('v0.9.0 OK modelli piano/split', flush=True)

# -----------------------------------------------------------------------------
# MainActivity: guida vocale, PIANO, editor Split Grade, pulsanti pieni
# -----------------------------------------------------------------------------
rep(main, '    private boolean feedbackBeep;\n', '    private boolean feedbackBeep;\n    private boolean voiceGuide;\n', 'voice field')
rep(main, '        feedbackBeep = p.getBoolean("feedbackBeep", true);\n', '        feedbackBeep = p.getBoolean("feedbackBeep", true);\n        voiceGuide = p.getBoolean("voiceGuide", true);\n', 'voice load')

# Stato split come ciclo attivo.
rep(main,
'''                || SonoffArmService.STATE_PAUSING.equals(state)\n                || SonoffArmService.STATE_WAITING_BURN.equals(state);''',
'''                || SonoffArmService.STATE_PAUSING.equals(state)\n                || SonoffArmService.STATE_WAITING_BURN.equals(state)\n                || SonoffArmService.STATE_WAITING_SPLIT.equals(state);''', 'waiting split cancellable')
rep(main,
'''        } else if (SonoffArmService.STATE_WAITING_BURN.equals(state)) {\n            title = "BRUCIATURA — PREPARA MASCHERA";\n            accent = darkroomMode ? RED : AMBER;\n        } else if (SonoffArmService.STATE_DISARMING.equals(state)) {''',
'''        } else if (SonoffArmService.STATE_WAITING_SPLIT.equals(state)) {\n            title = "SPLIT GRADE — CAMBIA FILTRO";\n            accent = darkroomMode ? RED : SPLIT_VIVA_MAGENTA;\n        } else if (SonoffArmService.STATE_WAITING_BURN.equals(state)) {\n            title = "BRUCIATURA — PREPARA MASCHERA";\n            accent = darkroomMode ? RED : BURN_RUST;\n        } else if (SonoffArmService.STATE_DISARMING.equals(state)) {''', 'waiting split presentation')

# ARMA: non lascia più il vecchio SEQ e segnala il piano.
s=rd(main)
s=s.replace(' + (printSequence != null && !printSequence.isEmpty() ? " · SEQ " + printSequence.size() : ""))',
            ' + (printSequence != null && !printSequence.isEmpty() ? (printSequence.hasSplit() ? " · PIANO SPLIT" : " · PIANO " + printSequence.size()) : ""))')
wr(main,s)

# UI riassunto piano.
update_ui = r'''    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        if (printSequence.isEmpty()) {
            printSequenceButton.setText("PIANO DI STAMPA");
            printSequenceSummary.setText("");
            printSequenceSummary.setVisibility(View.GONE);
        } else {
            String count = printSequence.corrections.isEmpty() ? "" : " + " + printSequence.corrections.size() + " CORREZION" + (printSequence.corrections.size() == 1 ? "E" : "I");
            printSequenceButton.setText(printSequence.hasSplit() ? "PIANO · SPLIT" + count : "PIANO · " + printSequence.corrections.size() + " CORREZION" + (printSequence.corrections.size() == 1 ? "E" : "I"));
            printSequenceSummary.setText(printSequence.detail(printWidthMs));
            printSequenceSummary.setVisibility(View.VISIBLE);
        }
    }

'''
rrep(main, r'    private void updatePrintSequenceUi\(\) \{.*?(?=    private void persistPrintSequence\(\))', update_ui, 'update plan ui')

plan_dialog = r'''    private void showPrintSequenceDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));

        panel.addView(text("PIANO DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1, -2));
        TextView base = text(printSequence != null && printSequence.hasSplit()
                ? "SPLIT GRADE · due esposizioni manuali"
                : "ESPOSIZIONE BASE · " + formatTime(printWidthMs), 14,
                darkroomMode ? RED : (printSequence != null && printSequence.hasSplit() ? SPLIT_VIVA_MAGENTA : GREEN), true);
        base.setPadding(0, dp(6), 0, dp(10));
        panel.addView(base, lp(-1, -2));

        if (printSequence != null && printSequence.hasSplit()) {
            Button splitRow = compactButton("SPLIT GRADE  ·  Y " + printSequence.split.softYellow + " / " + formatTime(printSequence.split.softMs)
                    + "   →   M " + printSequence.split.hardMagenta + " / " + formatTime(printSequence.split.hardMs));
            splitRow.setTextColor(Color.WHITE);
            splitRow.setBackground(roundRect(darkroomMode ? RED : SPLIT_VIVA_MAGENTA, 8, 0, 0));
            if (!darkroomMode) splitRow.setOnClickListener(v -> { dialog.dismiss(); showSplitGradeEditor(false); });
            else splitRow.setEnabled(false);
            panel.addView(splitRow, margin(lp(-1, dp(54)), 0, 0, 0, 8));
        }

        if ((printSequence == null || printSequence.isEmpty())) {
            TextView empty = text("Nessuna correzione. La stampa semplice resta identica.", 12, MUTED, false);
            empty.setPadding(0, dp(2), 0, dp(10));
            panel.addView(empty, lp(-1, -2));
        } else if (printSequence != null) {
            for (int x = 0; x < printSequence.corrections.size(); x++) {
                final int index = x;
                PrintCorrection c = printSequence.corrections.get(x);
                int baseMs = printSequence.baseMsFor(c, printWidthMs);
                Button row = compactButton(c.displayLine(baseMs, printSequence.hasSplit()));
                row.setTextColor(darkroomMode ? RED : (c.isDodge() ? DODGE_BISCAY_BAY : BURN_RUST));
                if (!darkroomMode) row.setOnClickListener(v -> { dialog.dismiss(); showPrintCorrectionEditor(index); });
                else row.setEnabled(false);
                panel.addView(row, margin(lp(-1, dp(50)), 0, 0, 0, 7));
            }
        }

        if (!darkroomMode) {
            Button add = compactButton("+  AGGIUNGI AL PIANO");
            add.setOnClickListener(v -> { dialog.dismiss(); showPlanTypeDialog(); });
            panel.addView(add, margin(lp(-1, dp(50)), 0, 8, 0, 0));

            if (printSequence != null && !printSequence.isEmpty()) {
                Button clear = compactButton("AZZERA PIANO");
                clear.setTextColor(RED);
                clear.setOnClickListener(v -> showAppConfirmDialog("AZZERARE IL PIANO DI STAMPA?",
                        "Verranno eliminati Split Grade, DODGE e BURN.", "AZZERA", () -> {
                            printSequence = new PrintSequence();
                            persistPrintSequence();
                            dialog.dismiss();
                        }, "ANNULLA"));
                panel.addView(clear, margin(lp(-1, dp(46)), 0, 8, 0, 0));
            }
        } else {
            TextView darkNote = text("In modalità camera oscura il piano è consultabile ma non modificabile.", 11, RED, false);
            darkNote.setGravity(Gravity.CENTER);
            panel.addView(darkNote, margin(lp(-1, -2), 0, 8, 0, 0));
        }

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, margin(lp(-1, dp(48)), 0, 8, 0, 0));
        dialog.setContentView(sc);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.84f));
    }

    private void showPlanTypeDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        panel.addView(text("TIPO DI CORREZIONE", 19, TEXT_PRIMARY, true), margin(lp(-1, -2), 0, 0, 0, 12));

        Button dodge = compactButton("DODGE");
        dodge.setTextColor(Color.WHITE);
        dodge.setBackground(roundRect(DODGE_BISCAY_BAY, 9, 0, 0));
        dodge.setOnClickListener(v -> {
            dialog.dismiss();
            PrintCorrection c = new PrintCorrection(PrintCorrection.DODGE);
            c.phase = printSequence.hasSplit() ? PrintCorrection.PHASE_SOFT : PrintCorrection.PHASE_BASE;
            printSequence.corrections.add(c);
            showPrintCorrectionEditor(printSequence.corrections.size() - 1);
        });
        panel.addView(dodge, lp(-1, dp(54)));

        Button burn = compactButton("BURN");
        burn.setTextColor(Color.WHITE);
        burn.setBackground(roundRect(BURN_RUST, 9, 0, 0));
        burn.setOnClickListener(v -> {
            dialog.dismiss();
            PrintCorrection c = new PrintCorrection(PrintCorrection.BURN);
            c.phase = printSequence.hasSplit() ? PrintCorrection.PHASE_SOFT : PrintCorrection.PHASE_BASE;
            printSequence.corrections.add(c);
            showPrintCorrectionEditor(printSequence.corrections.size() - 1);
        });
        panel.addView(burn, margin(lp(-1, dp(54)), 0, 8, 0, 0));

        Button split = compactButton("SPLIT GRADE");
        split.setTextColor(Color.WHITE);
        split.setBackground(roundRect(SPLIT_VIVA_MAGENTA, 9, 0, 0));
        split.setOnClickListener(v -> { dialog.dismiss(); showSplitGradeEditor(!printSequence.hasSplit()); });
        panel.addView(split, margin(lp(-1, dp(54)), 0, 8, 0, 0));

        Button cancel = compactButton("ANNULLA");
        cancel.setTextColor(Color.WHITE);
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(50)), 0, 10, 0, 0));
        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.92f), ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void showSplitGradeEditor(final boolean creating) {
        if (darkroomMode) return;
        if (printSequence == null) printSequence = new PrintSequence();
        final SplitGradePlan original = printSequence.split == null ? new SplitGradePlan() : printSequence.split.copy();
        final SplitGradePlan draft = original.copy();
        draft.enabled = true;
        draft.sanitize();

        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));

        panel.addView(text("SPLIT GRADE", 20, SPLIT_VIVA_MAGENTA, true), lp(-1, -2));
        TextView note = text("Due esposizioni separate. Dopo la fase morbida la guida vocale ti indica il filtro successivo; la seconda fase parte solo quando premi il pulsante fisico.", 12, MUTED, false);
        note.setPadding(0, dp(4), 0, dp(12));
        panel.addView(note, lp(-1, -2));

        final int[] sy = {draft.softYellow};
        final int[] sm = {draft.softMs};
        final int[] hm = {draft.hardMagenta};
        final int[] hmsec = {draft.hardMs};

        panel.addView(text("FASE MORBIDA · GIALLO (Y)", 14, SPLIT_VIVA_MAGENTA, true), margin(lp(-1, -2), 0, 2, 0, 4));
        LinearLayout syRow = new LinearLayout(this); syRow.setOrientation(LinearLayout.HORIZONTAL); syRow.setGravity(Gravity.CENTER);
        Button syMinus = smallButton("−"); Button syPlus = smallButton("+"); final TextView syValue = text("Y " + sy[0], 26, SPLIT_VIVA_MAGENTA, true); syValue.setGravity(Gravity.CENTER);
        syRow.addView(syMinus, lp(dp(62), dp(56))); syRow.addView(syValue, lp(0, dp(60), 1f)); syRow.addView(syPlus, lp(dp(62), dp(56))); panel.addView(syRow, lp(-1,-2));
        syMinus.setOnClickListener(v -> { sy[0]=Math.max(0,sy[0]-5); syValue.setText("Y " + sy[0]); });
        syPlus.setOnClickListener(v -> { sy[0]=Math.min(200,sy[0]+5); syValue.setText("Y " + sy[0]); });

        LinearLayout smRow = new LinearLayout(this); smRow.setOrientation(LinearLayout.HORIZONTAL); smRow.setGravity(Gravity.CENTER);
        Button smMinus = smallButton("−"); Button smPlus = smallButton("+"); final TextView smValue = text(formatTime(sm[0]), 26, SPLIT_VIVA_MAGENTA, true); smValue.setGravity(Gravity.CENTER);
        smRow.addView(smMinus, lp(dp(62), dp(56))); smRow.addView(smValue, lp(0, dp(60), 1f)); smRow.addView(smPlus, lp(dp(62), dp(56))); panel.addView(smRow, margin(lp(-1,-2),0,0,0,8));
        smMinus.setOnClickListener(v -> { sm[0]=Math.max(500,sm[0]-500); smValue.setText(formatTime(sm[0])); });
        smPlus.setOnClickListener(v -> { sm[0]=Math.min(36000000,sm[0]+500); smValue.setText(formatTime(sm[0])); });

        panel.addView(text("FASE DURA · MAGENTA (M)", 14, SPLIT_VIVA_MAGENTA, true), margin(lp(-1, -2), 0, 4, 0, 4));
        LinearLayout hmRow = new LinearLayout(this); hmRow.setOrientation(LinearLayout.HORIZONTAL); hmRow.setGravity(Gravity.CENTER);
        Button hmMinus = smallButton("−"); Button hmPlus = smallButton("+"); final TextView hmValue = text("M " + hm[0], 26, SPLIT_VIVA_MAGENTA, true); hmValue.setGravity(Gravity.CENTER);
        hmRow.addView(hmMinus, lp(dp(62), dp(56))); hmRow.addView(hmValue, lp(0, dp(60), 1f)); hmRow.addView(hmPlus, lp(dp(62), dp(56))); panel.addView(hmRow, lp(-1,-2));
        hmMinus.setOnClickListener(v -> { hm[0]=Math.max(0,hm[0]-5); hmValue.setText("M " + hm[0]); });
        hmPlus.setOnClickListener(v -> { hm[0]=Math.min(200,hm[0]+5); hmValue.setText("M " + hm[0]); });

        LinearLayout htRow = new LinearLayout(this); htRow.setOrientation(LinearLayout.HORIZONTAL); htRow.setGravity(Gravity.CENTER);
        Button htMinus = smallButton("−"); Button htPlus = smallButton("+"); final TextView htValue = text(formatTime(hmsec[0]), 26, SPLIT_VIVA_MAGENTA, true); htValue.setGravity(Gravity.CENTER);
        htRow.addView(htMinus, lp(dp(62), dp(56))); htRow.addView(htValue, lp(0, dp(60), 1f)); htRow.addView(htPlus, lp(dp(62), dp(56))); panel.addView(htRow, margin(lp(-1,-2),0,0,0,10));
        htMinus.setOnClickListener(v -> { hmsec[0]=Math.max(500,hmsec[0]-500); htValue.setText(formatTime(hmsec[0])); });
        htPlus.setOnClickListener(v -> { hmsec[0]=Math.min(36000000,hmsec[0]+500); htValue.setText(formatTime(hmsec[0])); });

        TextView voice = text("Guida vocale: “Imposta Giallo " + sy[0] + "…” poi “Imposta Magenta " + hm[0] + "…”. Funziona anche a display spento.", 11, MUTED, false);
        voice.setGravity(Gravity.CENTER); panel.addView(voice, margin(lp(-1,-2),0,4,0,10));

        Button save = compactButton("SALVA SPLIT GRADE");
        save.setTextColor(Color.WHITE); save.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0));
        save.setOnClickListener(v -> {
            draft.enabled=true; draft.softYellow=sy[0]; draft.softMs=sm[0]; draft.hardMagenta=hm[0]; draft.hardMs=hmsec[0]; draft.sanitize();
            printSequence.split=draft;
            for (PrintCorrection c : printSequence.corrections) if (PrintCorrection.PHASE_BASE.equals(c.phase)) c.phase=PrintCorrection.PHASE_SOFT;
            persistPrintSequence(); dialog.dismiss(); showPrintSequenceDialog();
        });
        panel.addView(save, lp(-1,dp(54)));

        if (!creating && printSequence.hasSplit()) {
            Button remove = compactButton("RIMUOVI SPLIT GRADE");
            remove.setTextColor(RED);
            remove.setOnClickListener(v -> {
                printSequence.split = new SplitGradePlan();
                for (PrintCorrection c : printSequence.corrections) c.phase=PrintCorrection.PHASE_BASE;
                persistPrintSequence(); dialog.dismiss(); showPrintSequenceDialog();
            });
            panel.addView(remove, margin(lp(-1,dp(48)),0,8,0,0));
        }
        Button cancel=compactButton("ANNULLA"); cancel.setOnClickListener(v -> dialog.dismiss()); panel.addView(cancel, margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(sc); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show();
        if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.88f));
    }

'''
rrep(main, r'    private void showPrintSequenceDialog\(\) \{.*?(?=    private void showPrintCorrectionEditor\(final int index\))', plan_dialog, 'plan dialog + split editor')

correction_editor = r'''    private void showPrintCorrectionEditor(final int index) {
        if (darkroomMode || printSequence == null || index < 0 || index >= printSequence.corrections.size()) return;
        final PrintCorrection original = printSequence.corrections.get(index);
        final PrintCorrection c = original.copy();
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));

        final int featureColor = c.isDodge() ? DODGE_BISCAY_BAY : BURN_RUST;
        panel.addView(text(c.isDodge() ? "DODGE" : "BURN", 19, featureColor, true), lp(-1, -2));
        TextView explain = text(c.isDodge()
                ? "Riduce l'esposizione della zona. Al cue: guida vocale + beep/vibrazione → togli la maschera."
                : "Aggiunge esposizione. Ogni BURN parte solo con una nuova pressione del pulsante fisico.", 12, MUTED, false);
        explain.setPadding(0, dp(4), 0, dp(10)); panel.addView(explain, lp(-1,-2));

        final EditText label = editField(c.isDodge() ? "Zona / maschera — es. Volto" : "Zona — es. Cielo", c.label);
        panel.addView(label, margin(lp(-1, dp(52)),0,0,0,10));

        final String[] phase = {printSequence.hasSplit() && c.isHard() ? PrintCorrection.PHASE_HARD : (printSequence.hasSplit() ? PrintCorrection.PHASE_SOFT : PrintCorrection.PHASE_BASE)};
        if (printSequence.hasSplit()) {
            TextView phaseLabel=text("FASE SPLIT GRADE",11,MUTED,true); panel.addView(phaseLabel, margin(lp(-1,-2),0,0,0,4));
            LinearLayout phases=new LinearLayout(this); phases.setOrientation(LinearLayout.HORIZONTAL);
            final Button soft=compactButton("MORBIDA · Y " + printSequence.split.softYellow); final Button hard=compactButton("DURA · M " + printSequence.split.hardMagenta);
            final Runnable style=()->{ boolean sft=PrintCorrection.PHASE_SOFT.equals(phase[0]); soft.setBackground(roundRect(sft?featureColor:BUTTON,8,1,BORDER)); hard.setBackground(roundRect(!sft?featureColor:BUTTON,8,1,BORDER)); soft.setTextColor(sft?Color.WHITE:TEXT_PRIMARY); hard.setTextColor(!sft?Color.WHITE:TEXT_PRIMARY); };
            soft.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_SOFT;style.run();}); hard.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_HARD;style.run();}); style.run();
            phases.addView(soft,margin(lp(0,dp(46),1f),0,0,dp(4),0)); phases.addView(hard,margin(lp(0,dp(46),1f),dp(4),0,0,0)); panel.addView(phases,margin(lp(-1,-2),0,0,0,10));
        }

        final boolean[] useStops={c.quarterStops>0}; final int[] ms={Math.max(c.isDodge()?1000:500,c.milliseconds)}; final int[] quarters={Math.max(1,c.quarterStops>0?c.quarterStops:1)};
        LinearLayout methods=new LinearLayout(this); methods.setOrientation(LinearLayout.HORIZONTAL); final Button secondsMode=compactButton("SECONDI"); final Button stopMode=compactButton("F-STOP");
        methods.addView(secondsMode,margin(lp(0,dp(46),1f),0,0,dp(4),0)); methods.addView(stopMode,margin(lp(0,dp(46),1f),dp(4),0,0,0)); panel.addView(methods,margin(lp(-1,-2),0,0,0,10));
        final Runnable styleMethods=()->{secondsMode.setBackground(roundRect(!useStops[0]?featureColor:BUTTON,8,1,BORDER));stopMode.setBackground(roundRect(useStops[0]?featureColor:BUTTON,8,1,BORDER));secondsMode.setTextColor(!useStops[0]?Color.WHITE:TEXT_PRIMARY);stopMode.setTextColor(useStops[0]?Color.WHITE:TEXT_PRIMARY);};

        LinearLayout selector=new LinearLayout(this); selector.setOrientation(LinearLayout.HORIZONTAL); selector.setGravity(Gravity.CENTER); Button minus=smallButton("−"); Button plus=smallButton("+"); final TextView value=text("",30,featureColor,true); value.setGravity(Gravity.CENTER); value.setSingleLine(true);
        selector.addView(minus,lp(dp(62),dp(58))); selector.addView(value,lp(0,dp(64),1f)); selector.addView(plus,lp(dp(62),dp(58))); panel.addView(selector,lp(-1,-2));
        final Runnable refresh=()->{ if(useStops[0]) value.setText(c.isDodge()?TimingMath.dodgeStopLabel(quarters[0]):TimingMath.stopLabel(quarters[0])); else value.setText(formatTime(ms[0])); };
        secondsMode.setOnClickListener(v->{useStops[0]=false;styleMethods.run();refresh.run();}); stopMode.setOnClickListener(v->{useStops[0]=true;styleMethods.run();refresh.run();});
        minus.setOnClickListener(v->{if(useStops[0])quarters[0]=Math.max(1,quarters[0]-1);else ms[0]=Math.max(c.isDodge()?1000:500,ms[0]-500);refresh.run();});
        plus.setOnClickListener(v->{if(useStops[0])quarters[0]=Math.min(16,quarters[0]+1);else{int baseMs=printSequence.baseMsForPhase(phase[0],printWidthMs);ms[0]=Math.min(c.isDodge()?Math.max(1000,baseMs-500):36000000,ms[0]+500);}refresh.run();}); styleMethods.run(); refresh.run();

        Button save=compactButton("SALVA CORREZIONE"); save.setBackground(roundRect(featureColor,9,0,0)); save.setTextColor(Color.WHITE);
        save.setOnClickListener(v->{String name=label.getText().toString().trim();c.label=name.isEmpty()?(c.isDodge()?"Zona da mascherare":"Zona da bruciare"):name;c.phase=printSequence.hasSplit()?phase[0]:PrintCorrection.PHASE_BASE;int baseMs=printSequence.baseMsFor(c,printWidthMs);if(useStops[0]){c.quarterStops=quarters[0];c.milliseconds=c.resolvedMs(baseMs);}else{c.quarterStops=0;if(c.isDodge()){if(baseMs<=1000){Toast.makeText(this,"Il DODGE richiede una esposizione superiore a 1,0 s",Toast.LENGTH_LONG).show();return;}c.milliseconds=TimingMath.snap500(ms[0],1000,Math.max(1000,baseMs-500));}else c.milliseconds=TimingMath.snap500(ms[0],500,36000000);}printSequence.corrections.set(index,c);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();}); panel.addView(save,margin(lp(-1,dp(52)),0,12,0,0));
        Button delete=compactButton("ELIMINA CORREZIONE");delete.setTextColor(RED);delete.setOnClickListener(v->{printSequence.corrections.remove(index);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();});panel.addView(delete,margin(lp(-1,dp(48)),0,8,0,0));
        Button close=compactButton("ANNULLA");close.setOnClickListener(v->dialog.dismiss());panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));dialog.setContentView(panel);Window w=dialog.getWindow();if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent);dialog.show();if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

'''
rrep(main, r'    private void showPrintCorrectionEditor\(final int index\) \{.*?(?=    private boolean validatePrintSequenceForBase\(\))', correction_editor, 'correction editor split-aware')

validation = r'''    private boolean validatePrintSequenceForBase() {
        if (printSequence == null || printSequence.isEmpty()) return true;
        if (printSequence.hasSplit()) printSequence.split.sanitize();
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
rrep(main, r'    private boolean validatePrintSequenceForBase\(\) \{.*?(?=    private LinearLayout buildTestPanel\(\))', validation, 'validation split')

# Impostazioni: toggle guida vocale.
rep(main,
'''        panel.addView(beep, margin(lp(-1, dp(50)), 0, 0, 0, 8));\n\n        Button diagnostics = compactButton("CRONOLOGIA TECNICA");''',
'''        panel.addView(beep, margin(lp(-1, dp(50)), 0, 0, 0, 8));\n\n        Button voice = compactButton("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));\n        voice.setOnClickListener(v -> {\n            voiceGuide = !voiceGuide;\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("voiceGuide", voiceGuide).apply();\n            voice.setText("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));\n        });\n        panel.addView(voice, margin(lp(-1, dp(50)), 0, 0, 0, 8));\n\n        Button diagnostics = compactButton("CRONOLOGIA TECNICA");''', 'voice settings')

# -----------------------------------------------------------------------------
# Service: Split Grade manuale + guida vocale a display spento
# -----------------------------------------------------------------------------
rep(service, 'import android.os.PowerManager;\n', 'import android.os.PowerManager;\nimport android.speech.tts.TextToSpeech;\n', 'tts import')
rep(service, '    public static final String STATE_WAITING_BURN = "WAITING_BURN";\n', '    public static final String STATE_WAITING_BURN = "WAITING_BURN";\n    public static final String STATE_WAITING_SPLIT = "WAITING_SPLIT";\n', 'split state')
rep(service,
'''    private volatile boolean printBaseDone = false;\n    private volatile int burnIndex = -1;''',
'''    private volatile boolean printBaseDone = false;\n    private volatile int splitStage = 0;\n    private volatile int burnIndex = -1;\n    private volatile TextToSpeech tts;\n    private volatile boolean ttsReady = false;\n    private ScheduledFuture<?> voiceRepeatTask;''', 'service split voice fields')
rep(service,
'''    @Override public void onCreate() {\n        super.onCreate();\n        ensureNotificationChannel();\n    }''',
'''    @Override public void onCreate() {\n        super.onCreate();\n        ensureNotificationChannel();\n        tts = new TextToSpeech(getApplicationContext(), status -> {\n            if (status == TextToSpeech.SUCCESS && tts != null) {\n                int r = tts.setLanguage(Locale.ITALIAN);\n                tts.setSpeechRate(0.95f);\n                ttsReady = r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED;\n            }\n        });\n    }''', 'tts init')
rep(service,
'''            printBaseDone = false;\n            burnIndex = -1;\n            cancelDodgeCues();''',
'''            printBaseDone = false;\n            splitStage = 0;\n            burnIndex = -1;\n            cancelDodgeCues();\n            cancelVoicePrompt();''', 'split reset')
rep(service,
'''            } else {\n                testTargetsMs = new int[0];\n                testPulsesMs = new int[0];\n                currentPulseWidthMs = widthMs;\n            }\n            device = DeviceConfig.load(this);''',
'''            } else {\n                testTargetsMs = new int[0];\n                testPulsesMs = new int[0];\n                currentPulseWidthMs = (printSequence != null && printSequence.hasSplit()) ? printSequence.split.softMs : widthMs;\n            }\n            device = DeviceConfig.load(this);''', 'first split pulse')

# Armato: prima istruzione vocale split.
rrep(service, r'            String msg = mode == MODE_PRINT\n                    \? "ARMATO — premi il pulsante fisico"\n                    : "PROVINO ARMATO — premi il pulsante fisico una volta";\n            broadcast\(STATE_ARMED, msg\);\n            updateNotification\(msg\);', r'''            String msg;
            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) {
                msg = "SPLIT GRADE ARMATO — MORBIDA Y " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + " — premi il pulsante fisico";
            } else {
                msg = mode == MODE_PRINT ? "ARMATO — premi il pulsante fisico" : "PROVINO ARMATO — premi il pulsante fisico una volta";
            }
            broadcast(STATE_ARMED, msg);
            updateNotification(msg);
            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(printSequence.split.softPrompt());''', 'arm split prompt')

# Alla vera accensione: annulla promemoria voce, gestisce safelight seconda fase e messaggio corretto.
rep(service,
'''                            if (mode == MODE_PRINT && printBaseDone) dimSafelightForExposure();\n                            else if (!cycleSafelightCaptured) captureAndDimSafelightForCycle();''',
'''                            if (mode == MODE_PRINT && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) dimSafelightForExposure();\n                            else if (!cycleSafelightCaptured) captureAndDimSafelightForCycle();''', 'split safelight re-dim')
rep(service,
'''                    lastObservedOnAt = observedAt;\n                    if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) scheduleDodgeCues(observedAt);''',
'''                    cancelVoicePrompt();\n                    lastObservedOnAt = observedAt;\n                    if (mode == MODE_PRINT && !printBaseDone && printSequence != null && !printSequence.isEmpty()) scheduleDodgeCues(observedAt);''', 'cancel voice on physical start')
rrep(service, r'                    String msg = mode == MODE_PRINT\n                            \? \(printBaseDone \? burnExposureMessage\(\) : \(printSequence != null && !printSequence.isEmpty\(\) \? "ESPOSIZIONE BASE IN CORSO — " \+ seconds\(widthMs\) : "ESPOSIZIONE IN CORSO — " \+ seconds\(widthMs\)\)\)\n                            : \(TimingMath.isFStop\(timingMethod\) \?', r'''                    String msg = mode == MODE_PRINT
                            ? printExposureMessage()
                            : (TimingMath.isFStop(timingMethod) ?''', 'print exposure message helper')

# Macchina a stati: morbida -> attesa pulsante -> dura -> burn manuali -> fine.
branch = r'''        seenOn.set(false);

        if (mode == MODE_PRINT && printSequence != null && !printSequence.isEmpty()) {
            if (!printBaseDone) {
                cancelDodgeCues();
                if (printSequence.hasSplit() && splitStage == 0) {
                    splitStage = 1;
                    prepareSplitStage();
                    return;
                }
                printBaseDone = true;
                java.util.List<PrintCorrection> burns = printSequence.burns();
                if (!burns.isEmpty()) {
                    burnIndex = 0;
                    prepareBurnStep();
                    return;
                }
            } else {
                burnIndex++;
                java.util.List<PrintCorrection> burns = printSequence.burns();
                if (burnIndex < burns.size()) {
                    prepareBurnStep();
                    return;
                }
            }
        }

        completed++;
'''
rrep(service, r'        seenOn\.set\(false\);\n\n        if \(mode == MODE_PRINT && printSequence != null && !printSequence\.isEmpty\(\)\) \{.*?\n        completed\+\+;\n', branch, 'split state machine')

# Persistenza: nel LOG il tempo principale di uno split è il totale delle due esposizioni.
rep(service,
'''            e.putInt("lastPrintMs", widthMs);''',
'''            e.putInt("lastPrintMs", printSequence != null && printSequence.hasSplit() ? printSequence.split.totalMs() : widthMs);''', 'split total log time')

helpers = r'''    private void prepareSplitStage() {
        cancelPoll();
        cancelDodgeCues();
        cancelVoicePrompt();
        if (printSequence == null || !printSequence.hasSplit() || splitStage != 1) return;
        try {
            temporarilyRestoreSafelightForPause();
            currentPulseWidthMs = printSequence.split.hardMs;
            SonoffHttp.pulseOn(device, currentPulseWidthMs);
            String msg = "SPLIT GRADE — IMPOSTA MAGENTA " + printSequence.split.hardMagenta + " — " + seconds(currentPulseWidthMs) + "\nPoi premi il pulsante fisico";
            TechnicalLog.add(this, techSessionId, "SPLIT fase dura preparata • M " + printSequence.split.hardMagenta + " • " + seconds(currentPulseWidthMs));
            broadcast(STATE_WAITING_SPLIT, msg);
            updateNotification(msg.replace('\n', ' '));
            seenOn.set(false);
            scheduleVoiceInstruction(printSequence.split.hardPrompt());
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile preparare la fase dura Split Grade: " + readable(e));
        }
    }

    private void prepareBurnStep() {
        cancelPoll();
        cancelDodgeCues();
        cancelVoicePrompt();
        java.util.List<PrintCorrection> burns = printSequence == null ? new java.util.ArrayList<>() : printSequence.burns();
        if (burnIndex < 0 || burnIndex >= burns.size()) return;
        PrintCorrection burn = burns.get(burnIndex);
        try {
            temporarilyRestoreSafelightForPause();
            int baseMs = printSequence.baseMsFor(burn, widthMs);
            currentPulseWidthMs = burn.resolvedMs(baseMs);
            SonoffHttp.pulseOn(device, currentPulseWidthMs);
            String filter = burnFilterInstruction(burn);
            String amount = burn.usesFStop() ? TimingMath.stopLabel(burn.quarterStops) : seconds(currentPulseWidthMs);
            String msg = "BRUCIA " + burn.safeLabel().toUpperCase(Locale.ITALY) + " — " + amount + (filter.isEmpty() ? "" : "\n" + filter) + "\nPrepara la maschera e premi il pulsante fisico";
            TechnicalLog.add(this, techSessionId, "BURN preparato " + (burnIndex + 1) + "/" + burns.size() + " • " + burn.displayLine(baseMs, printSequence.hasSplit()));
            broadcast(STATE_WAITING_BURN, msg);
            updateNotification(msg.replace('\n', ' '));
            seenOn.set(false);
            String voice = (filter.isEmpty() ? "" : filter + ". ") + "Burn " + burn.safeLabel() + ". Prepara la maschera. Poi premi il pulsante.";
            scheduleVoiceInstruction(voice);
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile preparare la bruciatura " + (burnIndex + 1) + ": " + readable(e));
        }
    }

    private String burnFilterInstruction(PrintCorrection burn) {
        if (printSequence == null || !printSequence.hasSplit()) return "";
        return burn.isHard() ? "Imposta Magenta " + printSequence.split.hardMagenta : "Imposta Giallo " + printSequence.split.softYellow;
    }

    private String burnExposureMessage() {
        java.util.List<PrintCorrection> burns = printSequence == null ? new java.util.ArrayList<>() : printSequence.burns();
        if (burnIndex < 0 || burnIndex >= burns.size()) return "BRUCIATURA IN CORSO";
        PrintCorrection burn = burns.get(burnIndex);
        return "BRUCIATURA " + (burnIndex + 1) + "/" + burns.size() + " — " + burn.safeLabel() + " · " + seconds(currentPulseWidthMs);
    }

    private String printExposureMessage() {
        if (printBaseDone) return burnExposureMessage();
        if (printSequence != null && printSequence.hasSplit()) {
            return splitStage == 0
                    ? "SPLIT GRADE · MORBIDA · Y " + printSequence.split.softYellow + " · " + seconds(currentPulseWidthMs)
                    : "SPLIT GRADE · DURA · M " + printSequence.split.hardMagenta + " · " + seconds(currentPulseWidthMs);
        }
        return printSequence != null && !printSequence.isEmpty() ? "ESPOSIZIONE BASE IN CORSO — " + seconds(widthMs) : "ESPOSIZIONE IN CORSO — " + seconds(widthMs);
    }

    private void scheduleDodgeCues(long observedOnAt) {
        cancelDodgeCues();
        if (printSequence == null || printSequence.isEmpty()) return;
        String phase = printSequence.hasSplit() ? (splitStage == 1 ? PrintCorrection.PHASE_HARD : PrintCorrection.PHASE_SOFT) : PrintCorrection.PHASE_BASE;
        int baseMs = printSequence.baseMsForPhase(phase, widthMs);
        long elapsed = Math.max(0L, System.currentTimeMillis() - observedOnAt);
        for (PrintCorrection dodge : printSequence.dodgesForPhase(phase)) {
            int dodgeMs = dodge.resolvedMs(baseMs);
            if (dodgeMs <= 0 || dodgeMs >= baseMs) continue;
            long delay = Math.max(0L, dodgeMs - elapsed);
            ScheduledFuture<?> f = cueIo.schedule(() -> {
                if (completing.get() || printBaseDone) return;
                String amount = dodge.usesFStop() ? TimingMath.dodgeStopLabel(dodge.quarterStops) : seconds(dodgeMs);
                String msg = "TOGLI MASCHERA — " + dodge.safeLabel().toUpperCase(Locale.ITALY) + " · " + amount;
                TechnicalLog.add(this, techSessionId, "DODGE CUE — " + msg);
                dodgeCueFeedback();
                speakOnce("Togli maschera " + dodge.safeLabel());
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

    private boolean voiceGuideEnabled() {
        return getSharedPreferences("ui", MODE_PRIVATE).getBoolean("voiceGuide", true);
    }

    private void speakOnce(String words) {
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty() || !ttsReady || tts == null) return;
        try { tts.speak(words, TextToSpeech.QUEUE_FLUSH, null, "darkroom-plan"); } catch (Exception ignored) {}
    }

    private void scheduleVoiceInstruction(final String words) {
        cancelVoicePrompt();
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty()) return;
        voiceRepeatTask = cueIo.scheduleWithFixedDelay(() -> speakOnce(words), 350L, 5000L, TimeUnit.MILLISECONDS);
    }

    private void cancelVoicePrompt() {
        if (voiceRepeatTask != null) {
            voiceRepeatTask.cancel(false);
            voiceRepeatTask = null;
        }
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
        TechnicalLog.add(this, techSessionId, "SAFELIGHT temporaneamente ON per preparare il prossimo passaggio");
    }

    private void dimSafelightForExposure() throws Exception {
        if (!safelightAuto || !cycleSafelightCaptured || !restoreSafelightAfterCycle) return;
        setSafelightConfirmed(false);
        TechnicalLog.add(this, techSessionId, "SAFELIGHT OFF per nuova esposizione del piano");
    }

'''
rrep(service, r'    private void prepareBurnStep\(\) \{.*?(?=    private void startInterlockMonitor\(\))', helpers, 'service split helpers')

# Ogni cancellazione ferma anche i promemoria vocali.
rep(service, '        cancelDodgeCues();\n', '        cancelDodgeCues();\n        cancelVoicePrompt();\n', 'cancel voice with timers', count=1)

# Distruzione TTS.
rep(service,
'''        cueIo.shutdownNow();\n        io.shutdownNow();''',
'''        cancelVoicePrompt();\n        cueIo.shutdownNow();\n        if (tts != null) { try { tts.stop(); tts.shutdown(); } catch (Exception ignored) {} tts = null; }\n        io.shutdownNow();''', 'tts shutdown')

# Static checks
checks = {
    build:['VERSION_NAME = "0.9.0"','VERSION_CODE = "43"'],
    main:['PIANO DI STAMPA','showSplitGradeEditor','showPlanTypeDialog','GUIDA VOCALE PIANO','STATE_WAITING_SPLIT','PIANO SPLIT'],
    split_grade:['softPrompt()','hardPrompt()'],
    print_sequence:['hasSplit()','SPLIT GRADE','baseMsForPhase'],
    print_correction:['PHASE_SOFT','PHASE_HARD'],
    service:['STATE_WAITING_SPLIT','prepareSplitStage','scheduleVoiceInstruction','TextToSpeech','burnFilterInstruction']
}
for p,needles in checks.items():
    text=rd(p)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.9.0 verifica fallita: {needle} in {p}')
print('v0.9.0 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
