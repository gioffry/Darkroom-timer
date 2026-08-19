#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'


def read(path):
    return Path(path).read_text(encoding='utf-8')

def write(path, text):
    Path(path).write_text(text, encoding='utf-8')

def replace(path, old, new, label):
    p = Path(path)
    text = read(p)
    if old not in text:
        raise SystemExit(f'v0.7.1: pattern mancante: {label} in {p}')
    text = text.replace(old, new, 1)
    write(p, text)
    print(f'v0.7.1: OK {label}', flush=True)

def regex_replace(path, pattern, replacement, label, flags=0):
    p = Path(path)
    text = read(p)
    new, n = re.subn(pattern, replacement, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v0.7.1: regex {label} trovata {n} volte in {p}')
    write(p, new)
    print(f'v0.7.1: OK {label}', flush=True)

build = work / 'build_darkroom.py'
replace(build, 'VERSION_NAME = "0.6.4"\nVERSION_CODE = "32"', 'VERSION_NAME = "0.7.1"\nVERSION_CODE = "34"', 'versione build')
replace(build, '[Darkroom v0.6.4]', '[Darkroom v0.7.1]', 'tag log build')
replace(build,
        'if not re.search(r"versionCode\\s+32\\b", g) or not re.search(r"versionName\\s+[\'\\\"]0\\.6\\.4[\'\\\"]", g):\n            fail("app/build.gradle non riporta versionCode 32 / versionName 0.6.4")\n    log("Preflight v0.6.4 OK: manifest/versione/requisiti SONOFF invarianti verificati")',
        'if not re.search(r"versionCode\\s+34\\b", g) or not re.search(r"versionName\\s+[\'\\\"]0\\.7\\.1[\'\\\"]", g):\n            fail("app/build.gradle non riporta versionCode 34 / versionName 0.7.1")\n    log("Preflight v0.7.1 OK: manifest/versione/requisiti SONOFF invarianti verificati")',
        'preflight build')
replace(project / 'app/build.gradle', "versionCode 32\n        versionName '0.6.4'", "versionCode 34\n        versionName '0.7.1'", 'gradle')
replace(project / 'app/src/main/AndroidManifest.xml', 'android:versionCode="32"\n    android:versionName="0.6.4"', 'android:versionCode="34"\n    android:versionName="0.7.1"', 'manifest')

timing_java = r'''package it.darkroom.timer;

import java.util.Locale;

public final class TimingMath {
    public static final String METHOD_SECONDS = "SECONDI";
    public static final String METHOD_FSTOP = "F-STOP";
    public static final String STEP_SECONDS = "0,5 s";
    public static final String STEP_FSTOP = "¼ stop";
    private static final double QUARTER_STOP_FACTOR = Math.pow(2.0, 0.25);

    private TimingMath() {}

    public static boolean isFStop(String method) {
        return METHOD_FSTOP.equalsIgnoreCase(method == null ? "" : method.trim());
    }

    public static String normalizeMethod(String method) {
        return isFStop(method) ? METHOD_FSTOP : METHOD_SECONDS;
    }

    public static String stepLabel(String method) {
        return isFStop(method) ? STEP_FSTOP : STEP_SECONDS;
    }

    public static int snap500(int ms, int min, int max) {
        ms = Math.max(min, Math.min(max, ms));
        int snapped = Math.round(ms / 500f) * 500;
        return Math.max(min, Math.min(max, snapped));
    }

    public static int quarterStop(int currentMs, int direction, int min, int max) {
        int current = snap500(currentMs, min, max);
        if (direction == 0) return current;
        double raw = current * (direction > 0 ? QUARTER_STOP_FACTOR : 1.0 / QUARTER_STOP_FACTOR);
        int next = snap500((int)Math.round(raw), min, max);
        if (direction > 0 && next <= current && current < max) next = snap500(current + 500, min, max);
        if (direction < 0 && next >= current && current > min) next = snap500(current - 500, min, max);
        return next;
    }

    public static int[] cumulativeSecondsSeries(int incrementMs, int count) {
        int n = Math.max(0, count);
        int[] out = new int[n];
        int step = snap500(incrementMs, 500, 36_000_000);
        for (int i = 0; i < n; i++) out[i] = Math.min(36_000_000, step * (i + 1));
        return out;
    }

    public static int[] cumulativeFStopSeries(int firstStripMs, int count) {
        int n = Math.max(0, count);
        int[] out = new int[n];
        if (n == 0) return out;
        out[0] = snap500(firstStripMs, 500, 36_000_000);
        for (int i = 1; i < n; i++) {
            out[i] = quarterStop(out[i - 1], +1, 500, 36_000_000);
            if (out[i] <= out[i - 1]) out[i] = Math.min(36_000_000, out[i - 1] + 500);
        }
        return out;
    }

    public static int[] cumulativeSeries(String method, int baseMs, int count) {
        return isFStop(method) ? cumulativeFStopSeries(baseMs, count) : cumulativeSecondsSeries(baseMs, count);
    }

    public static int[] incrementalPulses(int[] cumulative) {
        if (cumulative == null) return new int[0];
        int[] out = new int[cumulative.length];
        int previous = 0;
        for (int i = 0; i < cumulative.length; i++) {
            int target = snap500(cumulative[i], 500, 36_000_000);
            int pulse = target - previous;
            out[i] = snap500(Math.max(500, pulse), 500, 36_000_000);
            previous = target;
        }
        return out;
    }

    public static String toCsv(int[] values) {
        if (values == null || values.length == 0) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) b.append(',');
            b.append(values[i]);
        }
        return b.toString();
    }

    public static int[] fromCsv(String csv) {
        if (csv == null || csv.trim().isEmpty()) return new int[0];
        String[] bits = csv.split(",");
        int[] out = new int[bits.length];
        try {
            for (int i = 0; i < bits.length; i++) out[i] = Integer.parseInt(bits[i].trim());
            return out;
        } catch (Exception e) {
            return new int[0];
        }
    }

    public static String seriesLabel(int[] values) {
        if (values == null || values.length == 0) return "—";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) b.append(" · ");
            b.append(String.format(Locale.ITALY, "%.1f", values[i] / 1000.0));
        }
        return b.append(" s").toString();
    }
}
'''
write(java / 'TimingMath.java', timing_java)
print('v0.7.1: OK TimingMath.java', flush=True)

log_entry_java = r'''package it.darkroom.timer;

public final class LogEntry {
    public long id;
    public long timestamp;
    public String title = "";
    public String negative = "";
    public String aperture = "";
    public String columnHeight = "";
    public String magenta = "";
    public String yellow = "";
    public String density = "";
    public String paper = "";
    public String notes = "";
    public int exposureMs = 0;
    public int testMs = 0;
    public int testCount = 0;
    public boolean favorite = false;
    public String exposureMethod = TimingMath.METHOD_SECONDS;
    public String exposureStep = TimingMath.STEP_SECONDS;
    public String testMethod = TimingMath.METHOD_SECONDS;
    public String testStep = TimingMath.STEP_SECONDS;
    public String testStripTimes = "";
}
'''
write(java / 'LogEntry.java', log_entry_java)
print('v0.7.1: OK LogEntry.java', flush=True)

log_store_java = r'''package it.darkroom.timer;

import android.content.Context;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class LogStore {
    private static final String PREFS = "print_log";
    private static final String KEY = "entries_v1";

    private LogStore() {}

    public static List<LogEntry> load(Context context) {
        String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, "");
        return parsePayload(raw);
    }

    public static String exportPayload(Context context) {
        String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, "");
        return raw == null ? "" : raw;
    }

    public static List<LogEntry> parsePayload(String raw) {
        ArrayList<LogEntry> result = new ArrayList<>();
        if (raw == null || raw.isEmpty()) return result;
        String[] rows = raw.split("\\n");
        for (String row : rows) {
            try {
                String[] f = row.split("\\t", -1);
                if (f.length < 13) continue;
                LogEntry e = new LogEntry();
                e.id = Long.parseLong(f[0]);
                e.timestamp = Long.parseLong(f[1]);
                e.exposureMs = Integer.parseInt(f[2]);
                e.testMs = Integer.parseInt(f[3]);
                e.testCount = Integer.parseInt(f[4]);
                e.title = dec(f[5]);
                e.negative = dec(f[6]);
                e.aperture = dec(f[7]);
                e.columnHeight = dec(f[8]);
                e.magenta = dec(f[9]);
                e.yellow = dec(f[10]);
                e.density = dec(f[11]);
                if (f.length >= 14) {
                    e.paper = dec(f[12]);
                    e.notes = dec(f[13]);
                } else {
                    e.paper = "Fomaspeed Variant 311 RC lucida";
                    e.notes = dec(f[12]);
                }
                if (e.paper == null || e.paper.trim().isEmpty()) e.paper = "Fomaspeed Variant 311 RC lucida";
                e.favorite = f.length >= 15 && "1".equals(f[14]);
                if (f.length >= 20) {
                    e.exposureMethod = TimingMath.normalizeMethod(dec(f[15]));
                    e.exposureStep = textOr(dec(f[16]), TimingMath.stepLabel(e.exposureMethod));
                    e.testMethod = TimingMath.normalizeMethod(dec(f[17]));
                    e.testStep = textOr(dec(f[18]), TimingMath.stepLabel(e.testMethod));
                    e.testStripTimes = dec(f[19]);
                } else {
                    e.exposureMethod = TimingMath.METHOD_SECONDS;
                    e.exposureStep = TimingMath.STEP_SECONDS;
                    e.testMethod = TimingMath.METHOD_SECONDS;
                    e.testStep = TimingMath.STEP_SECONDS;
                    if (e.testMs > 0 && e.testCount > 0) e.testStripTimes = TimingMath.toCsv(TimingMath.cumulativeSecondsSeries(e.testMs, e.testCount));
                }
                result.add(e);
            } catch (Exception ignored) {}
        }
        result.sort((a, b) -> Long.compare(b.timestamp, a.timestamp));
        return result;
    }

    public static void save(Context context, LogEntry entry) {
        List<LogEntry> list = load(context);
        boolean replaced = false;
        for (int i = 0; i < list.size(); i++) {
            if (list.get(i).id == entry.id) {
                list.set(i, entry);
                replaced = true;
                break;
            }
        }
        if (!replaced) list.add(entry);
        write(context, list);
    }

    public static void delete(Context context, long id) {
        List<LogEntry> list = load(context);
        for (int i = list.size() - 1; i >= 0; i--) if (list.get(i).id == id) list.remove(i);
        write(context, list);
    }

    public static void replaceAll(Context context, List<LogEntry> entries) {
        write(context, entries == null ? new ArrayList<>() : new ArrayList<>(entries));
    }

    public static void merge(Context context, List<LogEntry> imported) {
        Map<Long, LogEntry> byId = new LinkedHashMap<>();
        for (LogEntry e : load(context)) byId.put(e.id, e);
        if (imported != null) for (LogEntry e : imported) byId.put(e.id, e);
        write(context, new ArrayList<>(byId.values()));
    }

    private static void write(Context context, List<LogEntry> list) {
        list.sort((a, b) -> Long.compare(b.timestamp, a.timestamp));
        StringBuilder out = new StringBuilder();
        for (LogEntry e : list) {
            if (out.length() > 0) out.append('\n');
            String exposureMethod = TimingMath.normalizeMethod(e.exposureMethod);
            String testMethod = TimingMath.normalizeMethod(e.testMethod);
            out.append(e.id).append('\t')
                    .append(e.timestamp).append('\t')
                    .append(e.exposureMs).append('\t')
                    .append(e.testMs).append('\t')
                    .append(e.testCount).append('\t')
                    .append(enc(e.title)).append('\t')
                    .append(enc(e.negative)).append('\t')
                    .append(enc(e.aperture)).append('\t')
                    .append(enc(e.columnHeight)).append('\t')
                    .append(enc(e.magenta)).append('\t')
                    .append(enc(e.yellow)).append('\t')
                    .append(enc(e.density)).append('\t')
                    .append(enc(e.paper)).append('\t')
                    .append(enc(e.notes)).append('\t')
                    .append(e.favorite ? "1" : "0").append('\t')
                    .append(enc(exposureMethod)).append('\t')
                    .append(enc(textOr(e.exposureStep, TimingMath.stepLabel(exposureMethod)))).append('\t')
                    .append(enc(testMethod)).append('\t')
                    .append(enc(textOr(e.testStep, TimingMath.stepLabel(testMethod)))).append('\t')
                    .append(enc(e.testStripTimes));
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, out.toString()).apply();
    }

    private static String textOr(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }

    private static String enc(String value) {
        String v = value == null ? "" : value;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(v.getBytes(StandardCharsets.UTF_8));
    }

    private static String dec(String value) {
        if (value == null || value.isEmpty()) return "";
        return new String(Base64.getUrlDecoder().decode(value), StandardCharsets.UTF_8);
    }
}
'''
write(java / 'LogStore.java', log_store_java)
print('v0.7.1: OK LogStore.java', flush=True)

jpg = java / 'JpegCardRenderer.java'
replace(jpg, 'float rowH = 104f;', 'float rowH = 96f;', 'JPG altezza righe')
replace(jpg,
'''        String[] labels = {
                "Titolo", "Negativo", "Diaframma", "Altezza colonna", "Magenta", "Yellow",
                "Densità", "Esposizione finale", "Provino", "N. esposizioni provino", "Carta"
        };
        String[] values = {
                text(e.title, "—"),
                negativeLabel(e.negative),
                apertureLabel(e.aperture),
                unitLabel(e.columnHeight, "cm"),
                text(e.magenta, "0"),
                text(e.yellow, "0"),
                text(e.density, "0"),
                seconds(e.exposureMs),
                e.testMs > 0 ? seconds(e.testMs) + " per striscia" : "—",
                e.testCount > 0 ? String.valueOf(e.testCount) : "—",
                text(e.paper, "Fomaspeed Variant 311 RC lucida")
        };''',
'''        String[] labels = {
                "Titolo", "Negativo", "Diaframma", "Altezza colonna", "Magenta", "Yellow",
                "Densità", "Esposizione finale", "Metodo stampa", "Provino", "Metodo provino", "Carta"
        };
        String[] values = {
                text(e.title, "—"),
                negativeLabel(e.negative),
                apertureLabel(e.aperture),
                unitLabel(e.columnHeight, "cm"),
                text(e.magenta, "0"),
                text(e.yellow, "0"),
                text(e.density, "0"),
                seconds(e.exposureMs),
                timingLabel(e.exposureMethod, e.exposureStep, e.exposureMs > 0),
                testStripLabel(e),
                timingLabel(e.testMethod, e.testStep, e.testMs > 0),
                text(e.paper, "Fomaspeed Variant 311 RC lucida")
        };''', 'JPG campi temporizzazione')
replace(jpg,
'''    private static String seconds(int ms) {
        if (ms <= 0) return "—";
        if (ms % 1000 == 0) return (ms / 1000) + " s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}''',
'''    private static String timingLabel(String method, String step, boolean present) {
        if (!present) return "—";
        String m = TimingMath.normalizeMethod(method);
        String s = text(step, TimingMath.stepLabel(m));
        return m + " · " + s;
    }

    private static String testStripLabel(LogEntry e) {
        if (e == null || e.testMs <= 0 || e.testCount <= 0) return "—";
        int[] strips = TimingMath.fromCsv(e.testStripTimes);
        if (strips.length != e.testCount) strips = TimingMath.cumulativeSeries(e.testMethod, e.testMs, e.testCount);
        return TimingMath.seriesLabel(strips);
    }

    private static String seconds(int ms) {
        if (ms <= 0) return "—";
        if (ms % 1000 == 0) return (ms / 1000) + " s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}''', 'JPG helper timing')

main = java / 'MainActivity.java'
replace(main, 'private static final String APP_VERSION = "0.6.4";', 'private static final String APP_VERSION = "0.7.1";', 'versione UI')
replace(main, '    private boolean darkroomProtection;\n    private boolean pendingDarkroomAfterDndPermission = false;', '    private boolean darkroomProtection;\n    private String timingMethod = TimingMath.METHOD_SECONDS;\n    private boolean pendingDarkroomAfterDndPermission = false;', 'campo metodo temporizzazione')
replace(main, '    private TextView testCumulativeText;\n    private Button actionButton;', '    private TextView testCumulativeText;\n    private TextView printStepText;\n    private TextView testPromptText;\n    private TextView testStepText;\n    private Button actionButton;', 'campi UI temporizzazione')
replace(main, '        darkroomProtection = p.getBoolean("darkroomProtection", true);\n        logGroupingEnabled = p.getBoolean("logGroupingEnabled", true);', '        darkroomProtection = p.getBoolean("darkroomProtection", true);\n        timingMethod = TimingMath.normalizeMethod(p.getString("timingMethod", TimingMath.METHOD_SECONDS));\n        logGroupingEnabled = p.getBoolean("logGroupingEnabled", true);', 'caricamento metodo')
replace(main, '        TextView sub = text("Singola esposizione • passo 0,5 s", 12, MUTED, false);\n        sub.setGravity(Gravity.CENTER);\n        box.addView(sub);', '        printStepText = text(printStepDescription(), 12, MUTED, false);\n        printStepText.setGravity(Gravity.CENTER);\n        box.addView(printStepText);', 'STAMPA descrizione passo')
replace(main, '        minus.setOnClickListener(v -> setPrintTime(printWidthMs - 500));\n        plus.setOnClickListener(v -> setPrintTime(printWidthMs + 500));', '        minus.setOnClickListener(v -> adjustPrintTime(-1));\n        plus.setOnClickListener(v -> adjustPrintTime(+1));', 'STAMPA +/-')
replace(main, '        TextView prompt = text("Incremento del provino", 16, TEXT_PRIMARY, true);\n        prompt.setGravity(Gravity.CENTER);\n        exposure.addView(prompt);\n        TextView sub = text("Ogni esposizione ha lo stesso tempo", 12, MUTED, false);\n        sub.setGravity(Gravity.CENTER);\n        exposure.addView(sub);', '        testPromptText = text(testPromptDescription(), 16, TEXT_PRIMARY, true);\n        testPromptText.setGravity(Gravity.CENTER);\n        exposure.addView(testPromptText);\n        testStepText = text(testStepDescription(), 12, MUTED, false);\n        testStepText.setGravity(Gravity.CENTER);\n        exposure.addView(testStepText);', 'PROVINO descrizione passo')
replace(main, '        minus.setOnClickListener(v -> setTestTime(testWidthMs - 500));\n        plus.setOnClickListener(v -> setTestTime(testWidthMs + 500));', '        minus.setOnClickListener(v -> adjustTestTime(-1));\n        plus.setOnClickListener(v -> adjustTestTime(+1));', 'PROVINO +/-')
regex_replace(main, r'''    private String cumulativeTimes\(\) \{.*?\n    \}\n\n    private void updateCumulativeTimes\(\) \{\n        if \(testCumulativeText != null\) testCumulativeText\.setText\(cumulativeTimes\(\)\);\n    \}''', '''    private int[] currentTestStripTargets() {
        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);
    }

    private String cumulativeTimes() {
        return "TEMPI CUMULATIVI  " + TimingMath.seriesLabel(currentTestStripTargets());
    }

    private void updateTimingUi() {
        if (printStepText != null) printStepText.setText(printStepDescription());
        if (testPromptText != null) testPromptText.setText(testPromptDescription());
        if (testStepText != null) testStepText.setText(testStepDescription());
        updateCumulativeTimes();
        applyModeUi();
    }

    private String printStepDescription() {
        return TimingMath.isFStop(timingMethod) ? "Singola esposizione • passo ¼ stop" : "Singola esposizione • passo 0,5 s";
    }

    private String testPromptDescription() {
        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";
    }

    private String testStepDescription() {
        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";
    }

    private void updateCumulativeTimes() {
        if (testCumulativeText != null) testCumulativeText.setText(cumulativeTimes());
    }''', 'tempi cumulativi metodo', flags=re.S)
replace(main, '        TextView title = text("IMPOSTAZIONI", 20, TEXT_PRIMARY, true);\n        panel.addView(title, margin(lp(-1, -2), 0, 0, 0, 14));\n\n        Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));', '        TextView title = text("IMPOSTAZIONI", 20, TEXT_PRIMARY, true);\n        panel.addView(title, margin(lp(-1, -2), 0, 0, 0, 14));\n\n        Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);\n        timing.setOnClickListener(v -> {\n            timingMethod = TimingMath.isFStop(timingMethod) ? TimingMath.METHOD_SECONDS : TimingMath.METHOD_FSTOP;\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("timingMethod", timingMethod).apply();\n            timing.setText("METODO DI TEMPORIZZAZIONE: " + timingMethod);\n            updateTimingUi();\n        });\n        panel.addView(timing, margin(lp(-1, dp(50)), 0, 0, 0, 8));\n\n        Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));', 'impostazione metodo')
replace(main, '    private void setPrintTime(int ms) {\n        if (armed) return;', '    private void adjustPrintTime(int direction) {\n        if (armed) return;\n        if (TimingMath.isFStop(timingMethod)) setPrintTime(TimingMath.quarterStop(printWidthMs, direction, 500, 36_000_000));\n        else setPrintTime(printWidthMs + direction * 500);\n    }\n\n    private void adjustTestTime(int direction) {\n        if (armed) return;\n        if (TimingMath.isFStop(timingMethod)) setTestTime(TimingMath.quarterStop(testWidthMs, direction, 500, 30_000));\n        else setTestTime(testWidthMs + direction * 500);\n    }\n\n    private void setPrintTime(int ms) {\n        if (armed) return;', 'helper +/-')
replace(main, '        if (mode == MODE_PRINT) {\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);\n            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n        } else {\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);\n            i.putExtra(SonoffArmService.EXTRA_WIDTH, testWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_COUNT, testCount);\n            i.putExtra(SonoffArmService.EXTRA_PAUSE, testPauseMs);\n        }', '        if (mode == MODE_PRINT) {\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);\n            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n        } else {\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);\n            i.putExtra(SonoffArmService.EXTRA_WIDTH, testWidthMs);\n            i.putExtra(SonoffArmService.EXTRA_COUNT, testCount);\n            i.putExtra(SonoffArmService.EXTRA_PAUSE, testPauseMs);\n            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());\n        }', 'arm metodo e targets')
replace(main, '            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)\n                    : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs));', '            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)\n                    : (TimingMath.isFStop(timingMethod)\n                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"\n                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));', 'etichetta ARMA provino')
regex_replace(main, r'''        final int step = session\.getInt\("lastTestMs", testWidthMs\);\n        final int n = Math\.max\(2, Math\.min\(20, session\.getInt\("lastTestCount", testCount\)\)\);\n        String\[\] choices = new String\[n\];\n        for \(int i = 0; i < n; i\+\+\) \{\n            int cumulative = step \* \(i \+ 1\);\n            choices\[i\] = \(i \+ 1\) \+ "ª striscia   —   " \+ formatTime\(cumulative\);\n        \}\n        showAppChoiceDialog\("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> \{\n            int imported = step \* \(which \+ 1\);''', '''        final int step = session.getInt("lastTestMs", testWidthMs);
        final int n = Math.max(2, Math.min(20, session.getInt("lastTestCount", testCount)));
        int[] storedStrips = TimingMath.fromCsv(session.getString("lastTestStripTimes", ""));
        final int[] strips = storedStrips.length == n ? storedStrips : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);
        String[] choices = new String[n];
        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(strips[i]);
        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {
            int imported = strips[which];''', 'chooser strisce reali', flags=re.S)
replace(main, '            e.timestamp = printAt;\n            e.exposureMs = p.getInt("lastPrintMs", 0);\n            if (testAt > 0) {\n                e.testMs = p.getInt("lastTestMs", 0);\n                e.testCount = p.getInt("lastTestCount", 0);\n            }', '            e.timestamp = printAt;\n            e.exposureMs = p.getInt("lastPrintMs", 0);\n            e.exposureMethod = TimingMath.normalizeMethod(p.getString("lastPrintMethod", TimingMath.METHOD_SECONDS));\n            e.exposureStep = p.getString("lastPrintStep", TimingMath.stepLabel(e.exposureMethod));\n            if (testAt > 0) {\n                e.testMs = p.getInt("lastTestMs", 0);\n                e.testCount = p.getInt("lastTestCount", 0);\n                e.testMethod = TimingMath.normalizeMethod(p.getString("lastTestMethod", TimingMath.METHOD_SECONDS));\n                e.testStep = p.getString("lastTestStep", TimingMath.stepLabel(e.testMethod));\n                e.testStripTimes = p.getString("lastTestStripTimes", "");\n            }', 'LOG stampa metodo')
replace(main, '            e.timestamp = testAt;\n            e.testMs = p.getInt("lastTestMs", 0);\n            e.testCount = p.getInt("lastTestCount", 0);', '            e.timestamp = testAt;\n            e.testMs = p.getInt("lastTestMs", 0);\n            e.testCount = p.getInt("lastTestCount", 0);\n            e.testMethod = TimingMath.normalizeMethod(p.getString("lastTestMethod", TimingMath.METHOD_SECONDS));\n            e.testStep = p.getString("lastTestStep", TimingMath.stepLabel(e.testMethod));\n            e.testStripTimes = p.getString("lastTestStripTimes", "");', 'LOG provino metodo')
regex_replace(main, r'''        String exposure = entry\.exposureMs > 0 \? formatTime\(entry\.exposureMs\) : "—";\n        String test = entry\.testMs > 0 \? formatTime\(entry\.testMs\) : "—";\n        String ntest = entry\.testCount > 0 \? String\.valueOf\(entry\.testCount\) : "—";\n        TextView autoValues = text\(\n                "Esposizione finale: " \+ exposure \+\n                "\\nProvino — sec striscia: " \+ test \+\n                "\\nNumero esposizioni provino: " \+ ntest \+\n                "\\nData: " \+ formatDate\(entry\.timestamp\) \+\n                "\\nOra: " \+ formatClock\(entry\.timestamp\), 14, TEXT_PRIMARY, false\);''', '''        String exposure = entry.exposureMs > 0 ? formatTime(entry.exposureMs) : "—";
        String ntest = entry.testCount > 0 ? String.valueOf(entry.testCount) : "—";
        int[] stripValues = TimingMath.fromCsv(entry.testStripTimes);
        if (entry.testMs > 0 && entry.testCount > 0 && stripValues.length != entry.testCount) stripValues = TimingMath.cumulativeSeries(entry.testMethod, entry.testMs, entry.testCount);
        String strips = entry.testMs > 0 ? TimingMath.seriesLabel(stripValues) : "—";
        String printMethod = entry.exposureMs > 0 ? TimingMath.normalizeMethod(entry.exposureMethod) + " · " + (entry.exposureStep == null || entry.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(entry.exposureMethod) : entry.exposureStep) : "—";
        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) : "—";
        TextView autoValues = text(
                "Esposizione finale: " + exposure +
                "\\nMetodo stampa: " + printMethod +
                "\\nProvino — strisce: " + ntest +
                "\\nMetodo provino: " + testMethod +
                "\\nTempi strisce: " + strips +
                "\\nData: " + formatDate(entry.timestamp) +
                "\\nOra: " + formatClock(entry.timestamp), 14, TEXT_PRIMARY, false);''', 'editor dati automatici', flags=re.S)
replace(main, '        TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? GREEN : TEXT_PRIMARY, true);\n        row.addView(summary, lp(-1, -2));\n\n        ArrayList<String> filterBits = new ArrayList<>();', '        TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? GREEN : TEXT_PRIMARY, true);\n        row.addView(summary, lp(-1, -2));\n        if (e.exposureMs > 0) {\n            TextView method = text("Metodo: " + TimingMath.normalizeMethod(e.exposureMethod) + " · " + (e.exposureStep == null || e.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(e.exposureMethod) : e.exposureStep), 11, MUTED, false);\n            method.setPadding(0, dp(3), 0, 0);\n            row.addView(method, lp(-1, -2));\n        }\n\n        ArrayList<String> filterBits = new ArrayList<>();', 'LOG card metodo stampa')
replace(main, '        } else if (e.testMs > 0) {\n            String provino = "Provino " + formatTime(e.testMs) + (e.testCount > 0 ? " × " + e.testCount : "");\n            TextView test = text(provino, 11, BLUE, false);\n            test.setPadding(0, dp(3), 0, 0);\n            row.addView(test, lp(-1, -2));\n        }', '        } else if (e.testMs > 0) {\n            int[] strips = TimingMath.fromCsv(e.testStripTimes);\n            if (strips.length != e.testCount) strips = TimingMath.cumulativeSeries(e.testMethod, e.testMs, e.testCount);\n            String provino = "Provino · " + TimingMath.normalizeMethod(e.testMethod) + " · " + (e.testStep == null || e.testStep.trim().isEmpty() ? TimingMath.stepLabel(e.testMethod) : e.testStep) + "\\nStrisce: " + TimingMath.seriesLabel(strips);\n            TextView test = text(provino, 11, BLUE, false);\n            test.setPadding(0, dp(3), 0, 0);\n            row.addView(test, lp(-1, -2));\n        }', 'LOG card provino')
replace(main, '            if (item.exposureMs > 0) {\n                kind = "STAMPA  " + formatTime(item.exposureMs);\n                accent = GREEN;\n            } else if (item.testMs > 0) {\n                kind = "PROVINO  " + formatTime(item.testMs) + (item.testCount > 0 ? " × " + item.testCount : "");\n                accent = BLUE;', '            if (item.exposureMs > 0) {\n                kind = "STAMPA  " + formatTime(item.exposureMs) + "  ·  " + TimingMath.normalizeMethod(item.exposureMethod) + " · " + (item.exposureStep == null || item.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(item.exposureMethod) : item.exposureStep);\n                accent = GREEN;\n            } else if (item.testMs > 0) {\n                kind = "PROVINO  " + TimingMath.normalizeMethod(item.testMethod) + " · " + (item.testStep == null || item.testStep.trim().isEmpty() ? TimingMath.stepLabel(item.testMethod) : item.testStep);\n                accent = BLUE;', 'LOG sessione metodo')

service = java / 'SonoffArmService.java'
replace(service, '    public static final String EXTRA_PAUSE = "pause_ms";\n    public static final String EXTRA_STATE = "state";', '    public static final String EXTRA_PAUSE = "pause_ms";\n    public static final String EXTRA_TIMING_METHOD = "timing_method";\n    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";\n    public static final String EXTRA_STATE = "state";', 'service extras')
replace(service, '    private volatile int pauseMs = 2000;\n    private volatile int completed = 0;', '    private volatile int pauseMs = 2000;\n    private volatile String timingMethod = TimingMath.METHOD_SECONDS;\n    private volatile int[] testTargetsMs = new int[0];\n    private volatile int[] testPulsesMs = new int[0];\n    private volatile int currentPulseWidthMs = 8500;\n    private volatile int completed = 0;', 'service campi timing')
replace(service, '            pauseMs = sanitizePause(intent.getIntExtra(EXTRA_PAUSE, 2000));\n            device = DeviceConfig.load(this);\n            techSessionId = TechnicalLog.startSession(this, mode == MODE_PRINT\n                    ? "STAMPA richiesta " + seconds(widthMs)\n                    : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs));', '            pauseMs = sanitizePause(intent.getIntExtra(EXTRA_PAUSE, 2000));\n            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));\n            if (mode == MODE_TEST) {\n                int[] requested = intent.getIntArrayExtra(EXTRA_TEST_TARGETS);\n                if (requested != null && requested.length == count) {\n                    testTargetsMs = new int[count];\n                    for (int x = 0; x < count; x++) testTargetsMs[x] = sanitizeWidth(requested[x]);\n                } else testTargetsMs = TimingMath.cumulativeSeries(timingMethod, widthMs, count);\n                testPulsesMs = TimingMath.incrementalPulses(testTargetsMs);\n                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;\n            } else {\n                testTargetsMs = new int[0];\n                testPulsesMs = new int[0];\n                currentPulseWidthMs = widthMs;\n            }\n            device = DeviceConfig.load(this);\n            techSessionId = TechnicalLog.startSession(this, mode == MODE_PRINT\n                    ? "STAMPA richiesta " + seconds(widthMs) + " • " + timingMethod + " · " + TimingMath.stepLabel(timingMethod)\n                    : (TimingMath.isFStop(timingMethod) ? "PROVINO F-STOP · ¼ stop • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs) : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs)));', 'service piano test')
replace(service, '            broadcast(STATE_ARMING, mode == MODE_PRINT\n                    ? "Imposto Inching a " + seconds(widthMs)\n                    : "Preparo provino: " + count + " × " + seconds(widthMs));', '            broadcast(STATE_ARMING, mode == MODE_PRINT\n                    ? "Imposto Inching a " + seconds(widthMs)\n                    : (TimingMath.isFStop(timingMethod) ? "Preparo provino: " + count + " strisce • ¼ stop" : "Preparo provino: " + count + " × " + seconds(widthMs)));', 'service stato armamento')
replace(service, '            SonoffHttp.pulseOn(device, widthMs);\n            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(widthMs));', '            SonoffHttp.pulseOn(device, currentPulseWidthMs);\n            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(currentPulseWidthMs));', 'service primo pulse')
replace(service, '                    String msg = mode == MODE_PRINT\n                            ? "ESPOSIZIONE IN CORSO — " + seconds(widthMs)\n                            : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);', '                    String msg = mode == MODE_PRINT\n                            ? "ESPOSIZIONE IN CORSO — " + seconds(widthMs)\n                            : (TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));', 'service messaggio esposizione')
replace(service, '                long minimumCredibleMs = Math.max(250L, Math.round(widthMs * 0.75));', '                long minimumCredibleMs = Math.max(250L, Math.round(currentPulseWidthMs * 0.75));', 'service soglia pulse corrente')
replace(service, '                SonoffHttp.switchOn(device);\n                TechnicalLog.add(this, techSessionId, "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count);', '                if (TimingMath.isFStop(timingMethod) && testPulsesMs.length == count) {\n                    currentPulseWidthMs = testPulsesMs[completed];\n                    SonoffHttp.pulseOn(device, currentPulseWidthMs);\n                    TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • cumulativo " + seconds(testTargetsMs[completed]));\n                } else currentPulseWidthMs = widthMs;\n                SonoffHttp.switchOn(device);\n                TechnicalLog.add(this, techSessionId, "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count);', 'service pulse variabile')
replace(service, '                String exposing = "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);', '                String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);', 'service secondo messaggio esposizione')
replace(service, '        long timeoutMs = Math.max(900L, Math.min(3000L, (long) widthMs + 500L));', '        long timeoutMs = Math.max(900L, Math.min(3000L, (long) currentPulseWidthMs + 500L));', 'service timeout pulse corrente')
replace(service, '        if (mode == MODE_PRINT) {\n            e.putInt("lastPrintMs", widthMs);\n            e.putLong("lastPrintAt", now);\n        } else {\n            e.putInt("lastTestMs", widthMs);\n            e.putInt("lastTestCount", count);\n            e.putLong("lastTestAt", now);\n        }', '        if (mode == MODE_PRINT) {\n            e.putInt("lastPrintMs", widthMs);\n            e.putString("lastPrintMethod", timingMethod);\n            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));\n            e.putLong("lastPrintAt", now);\n        } else {\n            e.putInt("lastTestMs", widthMs);\n            e.putInt("lastTestCount", count);\n            e.putString("lastTestMethod", timingMethod);\n            e.putString("lastTestStep", TimingMath.stepLabel(timingMethod));\n            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));\n            e.putLong("lastTestAt", now);\n        }', 'service persistenza metodo')
replace(service, '        String title = mode == MODE_TEST\n                ? "Darkroom Timer — Provino " + count + " × " + seconds(widthMs)\n                : "Darkroom Timer — " + seconds(widthMs);', '        String title = mode == MODE_TEST\n                ? (TimingMath.isFStop(timingMethod) ? "Darkroom Timer — Provino " + count + " strisce · ¼ stop" : "Darkroom Timer — Provino " + count + " × " + seconds(widthMs))\n                : "Darkroom Timer — " + seconds(widthMs);', 'service notifica metodo')

checks = {
    main: ['METODO DI TEMPORIZZAZIONE', 'TimingMath.quarterStop', 'EXTRA_TEST_TARGETS', 'Tempi strisce:', 'Metodo stampa:', 'currentTestStripTargets()'],
    service: ['testPulsesMs', 'lastTestStripTimes', 'currentPulseWidthMs', 'EXTRA_TIMING_METHOD'],
    java / 'LogStore.java': ['exposureMethod', 'testStripTimes', 'f.length >= 20'],
    jpg: ['Metodo stampa', 'Metodo provino', 'testStripLabel(e)'],
}
for path, needles in checks.items():
    text = read(path)
    for needle in needles:
        if needle not in text: raise SystemExit(f'v0.7.1: verifica finale fallita: {needle} in {path.name}')
print('v0.7.1: TUTTE LE VERIFICHE SORGENTE OK', flush=True)
