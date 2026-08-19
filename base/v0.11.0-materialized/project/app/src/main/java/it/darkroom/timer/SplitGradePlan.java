package it.darkroom.timer;

import java.util.Locale;

public final class SplitGradePlan {
    public boolean enabled = false;
    public int softYellow = 60;
    public int softMs = 500;
    public int hardMagenta = 180;
    public int hardMs = 500;

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

    public String softLine() { return "SPLIT · MORBIDA · " + softYellow + "Y / 0M · " + seconds(softMs); }
    public String hardLine() { return "SPLIT · DURA · 0Y / " + hardMagenta + "M · " + seconds(hardMs); }
    public String softPrompt() { return "Imposta " + softYellow + "Y / 0M. Poi premi il pulsante."; }
    public String hardPrompt() { return "Imposta 0Y / " + hardMagenta + "M. Poi premi il pulsante."; }

    private static int snap5(int v) {
        int x = Math.max(0, Math.min(200, v));
        return Math.round(x / 5f) * 5;
    }

    private static String seconds(int ms) {
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
