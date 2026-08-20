package it.darkroom.timer;

import java.util.Locale;

/**
 * Local-only technical state of the print base. It deliberately contains no
 * device/network logic: it is a compact archival description used by UI/LOG.
 */
public final class ExposureRecipe {
    public static final String FILTER_NONE = "NONE";
    public static final String FILTER_MAGENTA = "M";
    public static final String FILTER_YELLOW = "Y";

    /** Base selected at the end of the test strip / starting print. */
    public int originalBaseMs = 0;
    /** Current base time actually used by a normal print. */
    public int operationalBaseMs = 0;
    /** Contrast filtration inherited from the test strip. */
    public String filterType = FILTER_NONE;
    public int filterValue = 0;
    /** Neutral density in quarter-stop units: 1 = D7.5, 4 = D30, 8 = D60. */
    public int densityQuarterSteps = 0;
    /** Final whole-recipe exposure correction in quarter-stop units. */
    public int globalQuarterStops = 0;
    /** Timestamp when the current starting base was chosen. */
    public long baseChosenAt = 0L;

    public ExposureRecipe copy() {
        ExposureRecipe r = new ExposureRecipe();
        r.originalBaseMs = originalBaseMs;
        r.operationalBaseMs = operationalBaseMs;
        r.filterType = filterType;
        r.filterValue = filterValue;
        r.densityQuarterSteps = densityQuarterSteps;
        r.globalQuarterStops = globalQuarterStops;
        r.baseChosenAt = baseChosenAt;
        return r;
    }

    public boolean hasBase() { return originalBaseMs > 0 || operationalBaseMs > 0; }

    public void ensureBase(int currentMs) {
        int ms = TimingMath.snap500(Math.max(500, currentMs), 500, 36_000_000);
        if (originalBaseMs <= 0) originalBaseMs = ms;
        if (operationalBaseMs <= 0) operationalBaseMs = ms;
        filterType = normalizeFilter(filterType);
        filterValue = snap5(filterValue);
        densityQuarterSteps = clampDensity(densityQuarterSteps);
        globalQuarterStops = clampGlobal(globalQuarterStops);
        if (baseChosenAt <= 0L) baseChosenAt = System.currentTimeMillis();
    }

    public String encode() {
        return "R1|" + Math.max(0, originalBaseMs)
                + "|" + Math.max(0, operationalBaseMs)
                + "|" + normalizeFilter(filterType)
                + "|" + snap5(filterValue)
                + "|" + clampDensity(densityQuarterSteps)
                + "|" + clampGlobal(globalQuarterStops)
                + "|" + Math.max(0L, baseChosenAt);
    }

    public static ExposureRecipe decode(String raw) {
        ExposureRecipe r = new ExposureRecipe();
        if (raw == null || raw.trim().isEmpty()) return r;
        try {
            String[] f = raw.split("\\|", -1);
            if (f.length < 8 || !"R1".equals(f[0])) return r;
            r.originalBaseMs = Integer.parseInt(f[1]);
            r.operationalBaseMs = Integer.parseInt(f[2]);
            r.filterType = normalizeFilter(f[3]);
            r.filterValue = snap5(Integer.parseInt(f[4]));
            r.densityQuarterSteps = clampDensity(Integer.parseInt(f[5]));
            r.globalQuarterStops = clampGlobal(Integer.parseInt(f[6]));
            r.baseChosenAt = Long.parseLong(f[7]);
        } catch (Exception ignored) {
            return new ExposureRecipe();
        }
        return r;
    }

    public String filterLabel() { return filterLabel(filterType, filterValue); }

    public static String filterLabel(String type, int value) {
        String t = normalizeFilter(type);
        if (FILTER_NONE.equals(t)) return "NESSUNO";
        return t + snap5(value);
    }

    public String densityLabel() { return densityLabel(densityQuarterSteps); }

    public static String densityLabel(int quarterSteps) {
        int q = clampDensity(quarterSteps);
        double d = q * 7.5;
        if (Math.abs(d - Math.rint(d)) < 0.0001) return "D" + (int)Math.rint(d);
        return "D" + String.format(Locale.ITALY, "%.1f", d);
    }

    public String globalLabel() { return globalLabel(globalQuarterStops); }

    public static String globalLabel(int quarterStops) {
        int q = clampGlobal(quarterStops);
        if (q == 0) return "0";
        String sign = q > 0 ? "+" : "−";
        int a = Math.abs(q);
        int whole = a / 4;
        int rem = a % 4;
        String fraction = rem == 1 ? "¼" : rem == 2 ? "½" : rem == 3 ? "¾" : "";
        String value = (whole > 0 ? String.valueOf(whole) : "") + fraction;
        return sign + value + " stop";
    }

    public String originalLine() {
        if (!hasBase()) return "—";
        int ms = originalBaseMs > 0 ? originalBaseMs : operationalBaseMs;
        return seconds(ms) + " · " + filterForLine() + " · D0";
    }

    public String operationalLine(int fallbackMs) {
        int ms = operationalBaseMs > 0 ? operationalBaseMs : fallbackMs;
        if (ms <= 0) return "—";
        return seconds(ms) + " · " + filterForLine() + " · " + densityLabel();
    }

    private String filterForLine() {
        String f = filterLabel();
        return "NESSUNO".equals(f) ? "senza M/Y" : f;
    }

    public static int scaledMs(int ms, int quarterStopsDelta) {
        if (ms <= 0) return 0;
        double factor = Math.pow(2.0, quarterStopsDelta / 4.0);
        long raw = Math.round(ms * factor);
        return TimingMath.snap500((int)Math.max(500L, Math.min(36_000_000L, raw)), 500, 36_000_000);
    }

    public static String normalizeFilter(String type) {
        if (FILTER_MAGENTA.equalsIgnoreCase(type)) return FILTER_MAGENTA;
        if (FILTER_YELLOW.equalsIgnoreCase(type)) return FILTER_YELLOW;
        return FILTER_NONE;
    }

    public static int snap5(int value) {
        int x = Math.max(0, Math.min(200, value));
        return Math.round(x / 5f) * 5;
    }

    public static int clampDensity(int q) { return Math.max(0, Math.min(8, q)); }
    public static int clampGlobal(int q) { return Math.max(-4, Math.min(4, q)); }

    public static String seconds(int ms) {
        if (ms <= 0) return "—";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
