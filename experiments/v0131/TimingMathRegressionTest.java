package it.darkroom.timer;

import java.util.Arrays;

public final class TimingMathRegressionTest {
    private static void eq(int[] actual,int[] expected,String label){
        if(!Arrays.equals(actual,expected)) throw new RuntimeException(label+" expected="+Arrays.toString(expected)+" actual="+Arrays.toString(actual));
        System.out.println("PASS "+label+" "+Arrays.toString(actual));
    }
    private static int[] suffixSums(int[] pulses){
        int[] out=new int[pulses.length];
        int sum=0;
        for(int i=pulses.length-1;i>=0;i--){sum+=pulses[i];out[i]=sum;}
        return out;
    }
    private static int[] reversed(int[] in){
        int[] out=new int[in.length];
        for(int i=0;i<in.length;i++) out[i]=in[in.length-1-i];
        return out;
    }
    public static void main(String[] args){
        int[] fTargets=TimingMath.cumulativeFStopSeries(4000,6);
        eq(fTargets,new int[]{4000,5000,5500,6500,8000,9500},"F-STOP targets from 4.0 s at quarter stop");

        int[] fPulses=TimingMath.subtractivePulses(fTargets);
        eq(fPulses,new int[]{1500,1500,1000,500,1000,4000},"F-STOP chronological a-levare pulses");
        eq(suffixSums(fPulses),reversed(fTargets),"F-STOP physical bands darkest-to-lightest");

        int[] secTargets=TimingMath.cumulativeSecondsSeries(4000,3);
        eq(secTargets,new int[]{4000,8000,12000},"seconds targets unchanged");
        eq(TimingMath.incrementalPulses(secTargets),new int[]{4000,4000,4000},"seconds a-levare pulses unchanged");

        int[] seven=TimingMath.cumulativeFStopSeries(4000,7);
        int[] sevenPulses=TimingMath.subtractivePulses(seven);
        eq(suffixSums(sevenPulses),reversed(seven),"seven-strip suffix invariant");
        System.out.println("ALL v0.13.1 TIMING REGRESSIONS PASS");
    }
}
