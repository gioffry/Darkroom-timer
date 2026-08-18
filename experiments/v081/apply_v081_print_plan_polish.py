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
timing = java / 'TimingMath.java'
jpeg = java / 'JpegCardRenderer.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def must_replace(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.8.1 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.8.1 OK', label, flush=True)
def regex_replace(p, pattern, repl, label):
    s=rd(p); out,n=re.subn(pattern,repl,s,count=1,flags=re.S)
    if n != 1: raise SystemExit(f'v0.8.1 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.8.1 OK', label, flush=True)

# -----------------------------------------------------------------------------
# Versione
# -----------------------------------------------------------------------------
must_replace(build, 'VERSION_NAME = "0.8.0"', 'VERSION_NAME = "0.8.1"', 'version name build')
must_replace(build, 'VERSION_CODE = "41"', 'VERSION_CODE = "42"', 'version code build')
must_replace(build, '[Darkroom v0.8.0]', '[Darkroom v0.8.1]', 'build log tag')
must_replace(build, r'versionCode\s+41\b', r'versionCode\s+42\b', 'preflight code regex')
must_replace(build, r'0\.8\.0', r'0\.8\.1', 'preflight name regex')
must_replace(build, 'versionCode 41 / versionName 0.8.0', 'versionCode 42 / versionName 0.8.1', 'preflight message')
must_replace(build, 'Preflight v0.8.0 OK', 'Preflight v0.8.1 OK', 'preflight log')
must_replace(gradle, "versionCode 41\n        versionName '0.8.0'", "versionCode 42\n        versionName '0.8.1'", 'gradle version')
must_replace(manifest, 'android:versionCode="41"\n    android:versionName="0.8.0"', 'android:versionCode="42"\n    android:versionName="0.8.1"', 'manifest version')
must_replace(main, 'private static final String APP_VERSION = "0.8.0";', 'private static final String APP_VERSION = "0.8.1";', 'UI version')

# -----------------------------------------------------------------------------
# DODGE/BURN: modello simmetrico secondi/F-stop e visualizzazione non ridondante
# -----------------------------------------------------------------------------
new_correction = r'''package it.darkroom.timer;

import java.util.Locale;

public final class PrintCorrection {
    public static final String DODGE = "DODGE";
    public static final String BURN = "BURN";

    public String type = DODGE;
    public String label = "";
    /** DODGE: durata mascheratura dall'inizio; BURN: durata esposizione aggiuntiva. */
    public int milliseconds = 1000;
    /** Quarti di stop. >0 significa modalità F-stop sia per DODGE sia per BURN. */
    public int quarterStops = 0;

    public PrintCorrection() {}
    public PrintCorrection(String type) {
        this.type = BURN.equals(type) ? BURN : DODGE;
        milliseconds = isDodge() ? 2000 : 1500;
    }

    public boolean isDodge() { return DODGE.equals(type); }
    public boolean isBurn() { return BURN.equals(type); }
    public boolean usesFStop() { return quarterStops > 0; }

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

    public String displayLine(int baseMs) {
        if (usesFStop()) {
            return (isDodge() ? "DODGE · " : "BURN · ") + safeLabel() + " · "
                    + (isDodge() ? TimingMath.dodgeStopLabel(quarterStops) : TimingMath.stopLabel(quarterStops));
        }
        return (isDodge() ? "DODGE · " : "BURN · ") + safeLabel() + " · " + seconds(resolvedMs(baseMs));
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
wr(print_correction, new_correction)

must_replace(timing, '    public static String toCsv(int[] values) {', '''    public static int dodgeMaskMs(int baseMs, int quarterStops) {\n        int base = snap500(baseMs, 500, 36_000_000);\n        int q = Math.max(1, Math.min(16, quarterStops));\n        double target = base / Math.pow(2.0, q / 4.0);\n        int mask = (int)Math.round(base - target);\n        return snap500(Math.max(500, Math.min(base - 500, mask)), 500, Math.max(500, base - 500));\n    }\n\n    public static String dodgeStopLabel(int quarterStops) {\n        String plus = stopLabel(quarterStops);\n        return plus.startsWith("+") ? "-" + plus.substring(1) : "-" + plus;\n    }\n\n    public static String toCsv(int[] values) {''', 'TimingMath dodge f-stop')

# Non azzerare più gli stop dei DODGE durante il decode.
must_replace(print_sequence, '                if (c.isDodge()) c.quarterStops = 0;\n', '', 'decode dodge f-stop')

# -----------------------------------------------------------------------------
# Colori Pantone (approssimazioni sRGB per schermo) e nome PIANO DI STAMPA
# -----------------------------------------------------------------------------
must_replace(main, '    private int TEXT_PRIMARY;\n', '''    private int TEXT_PRIMARY;\n    // Pantone FHI approssimati in sRGB per display. In modalità camera oscura resta RED puro.\n    private static final int DODGE_BISCAY_BAY = Color.rgb(9, 121, 136);   // 18-4726 TCX\n    private static final int BURN_RUST = Color.rgb(181, 90, 48);          // 18-1248 TCX\n    private static final int SPLIT_VIVA_MAGENTA = Color.rgb(187, 38, 73);// 18-1750 TCX\n''', 'Pantone constants')

for old,new in [
    ('SEQUENZA DI STAMPA','PIANO DI STAMPA'),
    ('SEQUENZA · ','PIANO · '),
    ('AZZERA SEQUENZA','AZZERA PIANO'),
    ('AZZERARE LA SEQUENZA?','AZZERARE IL PIANO DI STAMPA?'),
    ('sequenza completa','piano completo'),
    ('Sequenza di stampa: ','Piano di stampa: '),
]:
    s=rd(main)
    if old in s: wr(main, s.replace(old,new))

# Colori delle righe del piano.
must_replace(main,
'                row.setTextColor(darkroomMode ? RED : (c.isDodge() ? BLUE : AMBER));',
'                row.setTextColor(darkroomMode ? RED : (c.isDodge() ? DODGE_BISCAY_BAY : BURN_RUST));',
'row colors')

# -----------------------------------------------------------------------------
# Editor DODGE/BURN: stessa UI, F-stop su entrambi, una sola unità visibile
# -----------------------------------------------------------------------------
editor = r'''    private void showPrintCorrectionEditor(final int index) {
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
                ? "Riduce l'esposizione della zona. Al cue: beep + vibrazione → togli la maschera."
                : "Aggiunge esposizione dopo la base. Ogni BURN parte solo con una nuova pressione del pulsante fisico.", 12, MUTED, false);
        explain.setPadding(0, dp(4), 0, dp(10));
        panel.addView(explain, lp(-1, -2));

        final EditText label = editField(c.isDodge() ? "Zona / maschera — es. Volto" : "Zona — es. Cielo", c.label);
        panel.addView(label, margin(lp(-1, dp(52)), 0, 0, 0, 10));

        final boolean[] useStops = {c.quarterStops > 0};
        final int[] ms = {Math.max(c.isDodge() ? 1000 : 500, c.milliseconds)};
        final int[] quarters = {Math.max(1, c.quarterStops > 0 ? c.quarterStops : 1)};

        LinearLayout methods = new LinearLayout(this);
        methods.setOrientation(LinearLayout.HORIZONTAL);
        final Button secondsMode = compactButton("SECONDI");
        final Button stopMode = compactButton("F-STOP");
        methods.addView(secondsMode, margin(lp(0, dp(46), 1f), 0, 0, dp(4), 0));
        methods.addView(stopMode, margin(lp(0, dp(46), 1f), dp(4), 0, 0, 0));
        panel.addView(methods, margin(lp(-1, -2), 0, 0, 0, 10));

        final Runnable styleMethods = () -> {
            secondsMode.setBackground(roundRect(!useStops[0] ? featureColor : BUTTON, 8, 1, BORDER));
            stopMode.setBackground(roundRect(useStops[0] ? featureColor : BUTTON, 8, 1, BORDER));
            secondsMode.setTextColor(!useStops[0] ? Color.BLACK : TEXT_PRIMARY);
            stopMode.setTextColor(useStops[0] ? Color.BLACK : TEXT_PRIMARY);
        };

        LinearLayout selector = new LinearLayout(this);
        selector.setOrientation(LinearLayout.HORIZONTAL);
        selector.setGravity(Gravity.CENTER);
        Button minus = smallButton("−");
        Button plus = smallButton("+");
        final TextView value = text("", 30, featureColor, true);
        value.setGravity(Gravity.CENTER);
        value.setSingleLine(true);
        selector.addView(minus, lp(dp(62), dp(58)));
        selector.addView(value, lp(0, dp(64), 1f));
        selector.addView(plus, lp(dp(62), dp(58)));
        panel.addView(selector, lp(-1, -2));

        final Runnable refresh = () -> {
            if (useStops[0]) value.setText(c.isDodge() ? TimingMath.dodgeStopLabel(quarters[0]) : TimingMath.stopLabel(quarters[0]));
            else value.setText(formatTime(ms[0]));
        };
        secondsMode.setOnClickListener(v -> { useStops[0] = false; styleMethods.run(); refresh.run(); });
        stopMode.setOnClickListener(v -> { useStops[0] = true; styleMethods.run(); refresh.run(); });
        minus.setOnClickListener(v -> {
            if (useStops[0]) quarters[0] = Math.max(1, quarters[0] - 1);
            else ms[0] = Math.max(c.isDodge() ? 1000 : 500, ms[0] - 500);
            refresh.run();
        });
        plus.setOnClickListener(v -> {
            if (useStops[0]) quarters[0] = Math.min(16, quarters[0] + 1);
            else ms[0] = Math.min(36_000_000, ms[0] + 500);
            refresh.run();
        });
        styleMethods.run();
        refresh.run();

        TextView calc = text(useStops[0]
                ? "Il tempo reale viene calcolato internamente dalla esposizione base e arrotondato a 0,5 s per il SONOFF."
                : (c.isDodge() ? "Il valore indica per quanto tempo la zona resta mascherata dall'inizio." : "Il valore indica il tempo aggiuntivo di bruciatura."), 11, MUTED, false);
        calc.setGravity(Gravity.CENTER);
        panel.addView(calc, margin(lp(-1, -2), 0, 6, 0, 10));

        Button save = compactButton("SALVA CORREZIONE");
        save.setBackground(roundRect(featureColor, 9, 0, 0));
        save.setTextColor(Color.BLACK);
        save.setOnClickListener(v -> {
            String name = label.getText().toString().trim();
            c.label = name.isEmpty() ? (c.isDodge() ? "Zona da mascherare" : "Zona da bruciare") : name;
            if (useStops[0]) {
                c.quarterStops = quarters[0];
                c.milliseconds = c.isDodge() ? TimingMath.dodgeMaskMs(printWidthMs, quarters[0]) : TimingMath.burnExtraMs(printWidthMs, quarters[0]);
            } else {
                c.quarterStops = 0;
                if (c.isDodge()) {
                    if (printWidthMs <= 1000) { Toast.makeText(this, "Il DODGE richiede una esposizione base superiore a 1,0 s", Toast.LENGTH_LONG).show(); return; }
                    c.milliseconds = TimingMath.snap500(ms[0], 1000, Math.max(1000, printWidthMs - 500));
                } else {
                    c.milliseconds = TimingMath.snap500(ms[0], 500, 36_000_000);
                }
            }
            printSequence.corrections.set(index, c);
            persistPrintSequence();
            dialog.dismiss();
            showPrintSequenceDialog();
        });
        panel.addView(save, margin(lp(-1, dp(52)), 0, 12, 0, 0));

        Button delete = compactButton("ELIMINA CORREZIONE");
        delete.setTextColor(RED);
        delete.setOnClickListener(v -> {
            printSequence.corrections.remove(index);
            persistPrintSequence();
            dialog.dismiss();
            showPrintSequenceDialog();
        });
        panel.addView(delete, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        Button close = compactButton("ANNULLA");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, margin(lp(-1, dp(48)), 0, 8, 0, 0));
        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), ViewGroup.LayoutParams.WRAP_CONTENT);
    }

'''
regex_replace(main, r'    private void showPrintCorrectionEditor\(final int index\) \{.*?(?=    private boolean validatePrintSequenceForBase\(\))', editor, 'editor DODGE/BURN')

# -----------------------------------------------------------------------------
# Safelight picker: elimina AlertDialog standard e usa dialog custom dell'app
# -----------------------------------------------------------------------------
safe_picker = r'''    private void showSafelightPicker() {
        ArrayList<FoundDevice> list = new ArrayList<>();
        for (FoundDevice f : foundDevices.values()) {
            if (!f.diyCandidate) continue;
            if (f.config.deviceId.equals(selectedDeviceId)) continue;
            list.add(f);
        }
        Collections.sort(list, Comparator.comparing(a -> a.config.deviceId));
        if (list.isEmpty()) {
            showAppConfirmDialog("NESSUN SECONDO SONOFF DIY TROVATO",
                    "La luce rossa richiede un secondo SONOFF in modalità DIY, diverso da quello dell'ingranditore. Attendi la ricerca di rete e riprova.",
                    "OK", null, null);
            return;
        }
        String[] labels = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            FoundDevice f = list.get(i);
            String selected = f.config.deviceId.equals(selectedSafelightDeviceId) ? "  ✓" : "";
            labels[i] = "ID " + f.config.deviceId + selected + "\n" + f.config.host + ":" + f.config.port + " • DIY";
        }
        showAppChoiceDialog("SCEGLI IL SONOFF DELLA LUCE ROSSA", labels,
                which -> selectSafelight(list.get(which)), "ANNULLA");
    }

'''
regex_replace(main, r'    private void showSafelightPicker\(\) \{.*?(?=    private void selectSafelight\(FoundDevice found\))', safe_picker, 'custom safelight picker')

# -----------------------------------------------------------------------------
# Runtime DODGE F-stop: usa sempre il tempo risolto dalla base corrente
# -----------------------------------------------------------------------------
must_replace(service,
'''        for (PrintCorrection dodge : printSequence.dodges()) {\n            if (dodge.milliseconds <= 0 || dodge.milliseconds >= widthMs) continue;\n            long delay = Math.max(0L, dodge.milliseconds - elapsed);''',
'''        for (PrintCorrection dodge : printSequence.dodges()) {\n            int dodgeMs = dodge.resolvedMs(widthMs);\n            if (dodgeMs <= 0 || dodgeMs >= widthMs) continue;\n            long delay = Math.max(0L, dodgeMs - elapsed);''', 'runtime dodge resolved')
must_replace(service,
'''                String msg = "TOGLI MASCHERA — " + dodge.safeLabel().toUpperCase(Locale.ITALY) + " · " + seconds(dodge.milliseconds);''',
'''                String msg = "TOGLI MASCHERA — " + dodge.safeLabel().toUpperCase(Locale.ITALY) + " · " + (dodge.usesFStop() ? TimingMath.dodgeStopLabel(dodge.quarterStops) : seconds(dodgeMs));''', 'runtime dodge message')

# BURN: anche nello stato d'attesa mostra una sola unità, come richiesto.
must_replace(service,
'''            String msg = "BRUCIA " + burn.safeLabel().toUpperCase(Locale.ITALY) + " — "\n                    + (burn.usesFStop() ? TimingMath.stopLabel(burn.quarterStops) + " · " : "")\n                    + seconds(currentPulseWidthMs) + "\\nPosiziona la maschera e premi il pulsante fisico";''',
'''            String msg = "BRUCIA " + burn.safeLabel().toUpperCase(Locale.ITALY) + " — "\n                    + (burn.usesFStop() ? TimingMath.stopLabel(burn.quarterStops) : seconds(currentPulseWidthMs))\n                    + "\\nPosiziona la maschera e premi il pulsante fisico";''', 'burn single unit waiting')

# -----------------------------------------------------------------------------
# LOG + JPG: nomenclatura PIANO e ricetta sempre visibile
# -----------------------------------------------------------------------------
s=rd(jpeg).replace('SEQUENZA DI STAMPA','PIANO DI STAMPA')
wr(jpeg,s)

# Nel LOG compatto mostra anche DODGE/BURN sotto le stampe non raggruppate.
log_anchor = '''        } else if (e.testMs > 0) {\n            int[] strips = TimingMath.fromCsv(e.testStripTimes);'''
if log_anchor in rd(main):
    must_replace(main, log_anchor, '''        } else if (e.exposureMs > 0 && e.printSequence != null && !e.printSequence.trim().isEmpty()) {\n            PrintSequence recipe = PrintSequence.decode(e.printSequence);\n            if (!recipe.isEmpty()) {\n                TextView plan = text("PIANO · " + recipe.summary(e.exposureMs) + "\\n" + recipe.detail(e.exposureMs), 11, MUTED, false);\n                plan.setPadding(0, dp(3), 0, 0);\n                row.addView(plan, lp(-1, -2));\n            }\n        } else if (e.testMs > 0) {\n            int[] strips = TimingMath.fromCsv(e.testStripTimes);''', 'log list plan')
else:
    print('v0.8.1 nota: anchor log compatto non trovato, editor/JPG restano comunque completi', flush=True)

# Static checks
checks = {
    build: ['VERSION_NAME = "0.8.1"', 'VERSION_CODE = "42"'],
    main: ['PIANO DI STAMPA', 'DODGE_BISCAY_BAY', 'BURN_RUST', 'SPLIT_VIVA_MAGENTA', 'showAppChoiceDialog("SCEGLI IL SONOFF DELLA LUCE ROSSA"'],
    timing: ['dodgeMaskMs', 'dodgeStopLabel'],
    print_correction: ['usesFStop() { return quarterStops > 0; }', 'TimingMath.dodgeStopLabel'],
    service: ['int dodgeMs = dodge.resolvedMs(widthMs);'],
    jpeg: ['PIANO DI STAMPA']
}
for p, needles in checks.items():
    text=rd(p)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.8.1 verifica fallita: {needle} in {p}')
print('v0.8.1 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
