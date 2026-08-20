package it.darkroom.timer;

import java.util.Arrays;

public final class TimingMathRegressionTest {
    private static void eq(String label, int[] got, int[] expected) {
        if (!Arrays.equals(got, expected)) {
            throw new AssertionError(label + " got=" + Arrays.toString(got) + " expected=" + Arrays.toString(expected));
        }
        System.out.println("PASS " + label + " " + Arrays.toString(got));
    }

    public static void main(String[] args) {
        int[] f = TimingMath.cumulativeFStopSeries(4000, 6);
        eq("F-STOP targets", f, new int[]{4000, 5000, 5500, 6500, 8000, 9500});

        eq("SCOPRIRE pulses F-STOP",
                TimingMath.testStripPulses(f, TimingMath.MASK_REVEAL),
                new int[]{1500, 1500, 1000, 500, 1000, 4000});
        eq("SCOPRIRE physical bands F-STOP",
                TimingMath.physicalTargets(f, TimingMath.MASK_REVEAL),
                new int[]{9500, 8000, 6500, 5500, 5000, 4000});

        eq("COPRIRE pulses F-STOP",
                TimingMath.testStripPulses(f, TimingMath.MASK_COVER),
                new int[]{4000, 1000, 500, 1000, 1500, 1500});
        eq("COPRIRE physical bands F-STOP",
                TimingMath.physicalTargets(f, TimingMath.MASK_COVER),
                new int[]{4000, 5000, 5500, 6500, 8000, 9500});

        int[] seconds = TimingMath.cumulativeSecondsSeries(4000, 3);
        eq("seconds targets unchanged", seconds, new int[]{4000, 8000, 12000});
        eq("SCOPRIRE pulses seconds unchanged",
                TimingMath.testStripPulses(seconds, TimingMath.MASK_REVEAL),
                new int[]{4000, 4000, 4000});
        eq("COPRIRE pulses seconds unchanged",
                TimingMath.testStripPulses(seconds, TimingMath.MASK_COVER),
                new int[]{4000, 4000, 4000});
        eq("SCOPRIRE physical bands seconds",
                TimingMath.physicalTargets(seconds, TimingMath.MASK_REVEAL),
                new int[]{12000, 8000, 4000});
        eq("COPRIRE physical bands seconds",
                TimingMath.physicalTargets(seconds, TimingMath.MASK_COVER),
                new int[]{4000, 8000, 12000});

        if (TimingMath.physicalTargetAt(f, 0, TimingMath.MASK_REVEAL) != 9500) throw new AssertionError("SCOPRIRE first physical strip");
        if (TimingMath.physicalTargetAt(f, 0, TimingMath.MASK_COVER) != 4000) throw new AssertionError("COPRIRE first physical strip");
        if (!TimingMath.MASK_REVEAL.equals(TimingMath.normalizeMaskingMethod(null))) throw new AssertionError("default masking method");

        System.out.println("ALL v0.13.2 TIMING/MASKING REGRESSIONS PASS");
    }
}
