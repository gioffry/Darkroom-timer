#!/usr/bin/env python3
from pathlib import Path
import sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; main_dir=app/'src/main'; java=main_dir/'java/it/darkroom/timer'
manifest=main_dir/'AndroidManifest.xml'; gradle=app/'build.gradle'; build=work/'build_darkroom.py'; main=java/'MainActivity.java'; timing=java/'TimingMath.java'; service=java/'SonoffArmService.java'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n<count: raise SystemExit(f'v0.13.1 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.1 OK',label,flush=True)

for p,needle in [(manifest,'android:versionName="0.13.0"'),(manifest,'android:versionCode="61"'),(main,'private static final String APP_VERSION = "0.13.0";')]:
    if needle not in rd(p): raise SystemExit('v0.13.1 BASE v0.13.0 non riconosciuta: '+needle)
if (java/'assistant').exists() or (java/'home').exists(): raise SystemExit('v0.13.1 base non Timer-only')

s=rd(build)
if 'VERSION_NAME = "0.13.0"' not in s or 'VERSION_CODE = "61"' not in s: raise SystemExit('v0.13.1 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.0"','VERSION_NAME = "0.13.1"').replace('VERSION_CODE = "61"','VERSION_CODE = "62"')
s=s.replace('[Darkroom v0.13.0]','[Darkroom v0.13.1]').replace('versionCode 61','versionCode 62').replace(r'versionCode\s+61\b',r'versionCode\s+62\b').replace('0.13.0','0.13.1')
wr(build,s)
rep(gradle,"versionCode 61\n        versionName '0.13.0'","versionCode 62\n        versionName '0.13.1'",'Gradle version')
rep(manifest,'android:versionCode="61"\n    android:versionName="0.13.0"','android:versionCode="62"\n    android:versionName="0.13.1"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.0";','private static final String APP_VERSION = "0.13.1";','Timer footer version')

old='''    public static int[] cumulativeFStopSeries(int firstStripMs, int count) {
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
'''
new='''    public static int[] cumulativeFStopSeries(int firstStripMs, int count) {
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
'''
rep(timing,old,new,'direct-from-base quarter-stop targets')

anchor='''    public static int[] incrementalPulses(int[] cumulative) {
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
'''
addition=anchor+'''\n    /**
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
'''
rep(timing,anchor,addition,'a-levare f-stop pulse generator')

rep(service,'                testPulsesMs = TimingMath.incrementalPulses(testTargetsMs);','                testPulsesMs = TimingMath.isFStop(timingMethod) ? TimingMath.subtractivePulses(testTargetsMs) : TimingMath.incrementalPulses(testTargetsMs);','use subtractive pulses only for F-STOP')
rep(service,'? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));','? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(testTargetsMs[count - current]) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));','first F-STOP exposure label')
rep(service,'TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • cumulativo " + seconds(testTargetsMs[completed]));','TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • fascia finale " + seconds(testTargetsMs[count - completed - 1]));','accurate F-STOP technical log')
rep(service,'String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);','String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(testTargetsMs[count - current]) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);','subsequent F-STOP exposure label')

# Hard guards.
t=rd(timing); sv=rd(service); mt=rd(main)
for needle in ['Math.pow(QUARTER_STOP_FACTOR, i)','subtractivePulses','forward[n - 1 - i]']:
    if needle not in t: raise SystemExit('v0.13.1 timing guard missing: '+needle)
if 'TimingMath.isFStop(timingMethod) ? TimingMath.subtractivePulses(testTargetsMs) : TimingMath.incrementalPulses(testTargetsMs)' not in sv:
    raise SystemExit('v0.13.1 service guard missing')
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists(): raise SystemExit('v0.13.1 Assistant residue')
for needle in ['SPLIT GRADE','PROVINO','ARMA','F-STOP','SonoffArmService']:
    if needle not in mt: raise SystemExit('v0.13.1 Timer regression: '+needle)
print('v0.13.1 TRANSFORM OK — F-STOP a levare, secondi invariati',flush=True)
