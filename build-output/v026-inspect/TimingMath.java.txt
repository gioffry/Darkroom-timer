package it.darkroom.timer;

import java.util.Locale;

public final class TimingMath {
    public static final String METHOD_SECONDS = "SECONDI";
    public static final String METHOD_FSTOP = "F-STOP";
    public static final String STEP_SECONDS = "0,5 s";
    public static final String STEP_FSTOP = "¼ stop";
    public static final String MASK_REVEAL = "SCOPRIRE";
    public static final String MASK_COVER = "COPRIRE";
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
        int base = snap500(firstStripMs, 500, 36_000_000);
        for (int i = 0; i < n; i++) {
            double exact = base * Math.pow(QUARTER_STOP_FACTOR, i);
            int target = snap500((int)Math.round(exact), 500, 36_000_000);
            if (i > 0 && target <= out[i - 1]) target = Math.min(36_000_000, out[i - 1] + 500);
            out[i] = target;
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

    /**
     * Impulsi cronologici per il provino "a levare": si espone una fascia,
     * poi se ne scopre una in più a ogni passaggio. Gli obiettivi sono memorizzati
     * in ordine crescente; gli impulsi fisici sono quindi le differenze in ordine inverso.
     */
    public static int[] subtractivePulses(int[] ascendingTargets) {
        int[] forward = incrementalPulses(ascendingTargets);
        int n = forward.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) out[i] = forward[n - 1 - i];
        return out;
    }

    public static String normalizeMaskingMethod(String method) {
        return MASK_COVER.equalsIgnoreCase(method == null ? "" : method.trim()) ? MASK_COVER : MASK_REVEAL;
    }

    /** Chronological relay pulses for the selected physical test-strip gesture. */
    public static int[] testStripPulses(int[] ascendingTargets, String maskingMethod) {
        return MASK_REVEAL.equals(normalizeMaskingMethod(maskingMethod))
                ? subtractivePulses(ascendingTargets)
                : incrementalPulses(ascendingTargets);
    }

    /** Final exposure times in physical strip order (1st strip, 2nd strip, ...). */
    public static int[] physicalTargets(int[] ascendingTargets, String maskingMethod) {
        if (ascendingTargets == null) return new int[0];
        int n = ascendingTargets.length;
        int[] out = new int[n];
        boolean reveal = MASK_REVEAL.equals(normalizeMaskingMethod(maskingMethod));
        for (int i = 0; i < n; i++) out[i] = ascendingTargets[reveal ? n - 1 - i : i];
        return out;
    }

    public static int physicalTargetAt(int[] ascendingTargets, int physicalIndex, String maskingMethod) {
        int[] physical = physicalTargets(ascendingTargets, maskingMethod);
        if (physicalIndex < 0 || physicalIndex >= physical.length) return 0;
        return physical[physicalIndex];
    }

    public static int burnExtraMs(int baseMs, int quarterStops) {
        int base = snap500(baseMs, 500, 36_000_000);
        int q = Math.max(1, Math.min(16, quarterStops));
        double total = base * Math.pow(2.0, q / 4.0);
        int extra = (int)Math.round(total - base);
        return snap500(Math.max(500, extra), 500, 36_000_000);
    }

    public static String stopLabel(int quarterStops) {
        int q = Math.max(1, Math.min(16, quarterStops));
        int whole = q / 4;
        int rem = q % 4;
        String fraction = rem == 1 ? "¼" : rem == 2 ? "½" : rem == 3 ? "¾" : "";
        String value = (whole > 0 ? String.valueOf(whole) : "") + fraction;
        return "+" + value + " stop";
    }

    public static int dodgeMaskMs(int baseMs, int quarterStops) {
        int base = snap500(baseMs, 500, 36_000_000);
        int q = Math.max(1, Math.min(16, quarterStops));
        double target = base / Math.pow(2.0, q / 4.0);
        int mask = (int)Math.round(base - target);
        return snap500(Math.max(500, Math.min(base - 500, mask)), 500, Math.max(500, base - 500));
    }

    public static String dodgeStopLabel(int quarterStops) {
        String plus = stopLabel(quarterStops);
        return plus.startsWith("+") ? "-" + plus.substring(1) : "-" + plus;
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
