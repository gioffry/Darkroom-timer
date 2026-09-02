package it.darkroom.timer;

import java.util.Locale;

public final class PrintCorrection {
    public static final String DODGE = "DODGE";
    public static final String BURN = "BURN";
    public static final String PHASE_BASE = "BASE";
    public static final String PHASE_SOFT = "SOFT";
    public static final String PHASE_HARD = "HARD";
    public static final String PHASE_BOTH = "BOTH";

    public static final String BURN_FILTER_Y_SPLIT = "Y_SPLIT";
    public static final String BURN_FILTER_M_SPLIT = "M_SPLIT";
    public static final String BURN_FILTER_CUSTOM_Y = "CUSTOM_Y";
    public static final String BURN_FILTER_CUSTOM_M = "CUSTOM_M";

    public String type = DODGE;
    public String label = "";
    public int milliseconds = 1000;
    public int quarterStops = 0;
    public String phase = PHASE_BASE;
    public String burnFilterMode = BURN_FILTER_Y_SPLIT;
    public int burnFilterValue = 0;

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
    public boolean isBoth() { return PHASE_BOTH.equals(phase); }

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

    public static String normalizeBurnFilter(String raw) {
        if (BURN_FILTER_M_SPLIT.equals(raw) || BURN_FILTER_CUSTOM_Y.equals(raw) || BURN_FILTER_CUSTOM_M.equals(raw))
            return raw;
        return BURN_FILTER_Y_SPLIT;
    }

    public boolean burnUsesMagenta() {
        String m = normalizeBurnFilter(burnFilterMode);
        return BURN_FILTER_M_SPLIT.equals(m) || BURN_FILTER_CUSTOM_M.equals(m);
    }

    public boolean burnIsCustom() {
        String m = normalizeBurnFilter(burnFilterMode);
        return BURN_FILTER_CUSTOM_Y.equals(m) || BURN_FILTER_CUSTOM_M.equals(m);
    }

    public String phaseLabel() {
        if (isBoth()) return "GIALLO + MAGENTA";
        if (isHard()) return "MAGENTA";
        return "GIALLO";
    }

    public String burnFilterLabel() {
        String m = normalizeBurnFilter(burnFilterMode);
        if (BURN_FILTER_M_SPLIT.equals(m)) return "MAGENTA DELLO SPLIT";
        if (BURN_FILTER_CUSTOM_Y.equals(m)) return "Y " + snap5(burnFilterValue);
        if (BURN_FILTER_CUSTOM_M.equals(m)) return "M " + snap5(burnFilterValue);
        return "GIALLO DELLO SPLIT";
    }

    public String displayLine(int baseMs) { return displayLine(baseMs, false); }
    public String displayLine(int baseMs, boolean showPhase) {
        String amount = usesFStop()
                ? (isDodge() ? TimingMath.dodgeStopLabel(quarterStops) : TimingMath.stopLabel(quarterStops))
                : seconds(resolvedMs(baseMs));
        String suffix = "";
        if (showPhase) suffix = isDodge() ? " · " + phaseLabel() : " · " + burnFilterLabel();
        return (isDodge() ? "DODGE · " : "BURN · ") + safeLabel() + " · " + amount + suffix;
    }

    public PrintCorrection copy() {
        PrintCorrection c = new PrintCorrection();
        c.type = type;
        c.label = label;
        c.milliseconds = milliseconds;
        c.quarterStops = quarterStops;
        c.phase = phase;
        c.burnFilterMode = burnFilterMode;
        c.burnFilterValue = burnFilterValue;
        return c;
    }

    public static int snap5(int v) {
        int x = Math.max(0, Math.min(200, v));
        return Math.round(x / 5f) * 5;
    }

    public static String seconds(int ms) {
        if (ms % 1000 == 0) return (ms / 1000) + ",0 s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
