package it.darkroom.timer;

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
        if (PrintCorrection.PHASE_BOTH.equals(phase)) return Math.min(split.softMs, split.hardMs);
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
            if (!hasSplit() || phase.equals(c.phase) || c.isBoth()) out.add(c.copy());
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
                    .append(c.phase == null ? PrintCorrection.PHASE_BASE : c.phase).append('|')
                    .append(PrintCorrection.normalizeBurnFilter(c.burnFilterMode)).append('|')
                    .append(PrintCorrection.snap5(c.burnFilterValue));
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
                String ph = f.length >= 5 ? f[4] : PrintCorrection.PHASE_BASE;
                c.phase = (PrintCorrection.PHASE_SOFT.equals(ph) || PrintCorrection.PHASE_HARD.equals(ph) || PrintCorrection.PHASE_BOTH.equals(ph))
                        ? ph : PrintCorrection.PHASE_BASE;
                if (c.isBurn()) {
                    c.burnFilterMode = f.length >= 6 ? PrintCorrection.normalizeBurnFilter(f[5])
                            : (c.isHard() ? PrintCorrection.BURN_FILTER_M_SPLIT : PrintCorrection.BURN_FILTER_Y_SPLIT);
                    if (f.length >= 7) {
                        try { c.burnFilterValue = PrintCorrection.snap5(Integer.parseInt(f[6])); }
                        catch (Exception ignored) { c.burnFilterValue = 0; }
                    }
                    c.phase = c.burnUsesMagenta() ? PrintCorrection.PHASE_HARD : PrintCorrection.PHASE_SOFT;
                }
                out.corrections.add(c);
            } catch (Exception ignored) {}
        }
        if (out.hasSplit()) {
            for (PrintCorrection c : out.corrections) {
                if (!PrintCorrection.PHASE_BASE.equals(c.phase)) continue;
                c.phase = PrintCorrection.PHASE_SOFT;
                if (c.isBurn()) c.burnFilterMode = PrintCorrection.BURN_FILTER_Y_SPLIT;
            }
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
        if (hasSplit()) b.append(split.softLine()).append('\n').append(split.hardLine());
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
