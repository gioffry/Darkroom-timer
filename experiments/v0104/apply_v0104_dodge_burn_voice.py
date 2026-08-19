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
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.10.4 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.4 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.4 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.4 OK',label,flush=True)

rep(build, 'VERSION_NAME = "0.10.3"', 'VERSION_NAME = "0.10.4"', 'version name build')
rep(build, 'VERSION_CODE = "48"', 'VERSION_CODE = "49"', 'version code build')
rep(build, '[Darkroom v0.10.3]', '[Darkroom v0.10.4]', 'build log tag')
rep(build, r'versionCode\s+48\b', r'versionCode\s+49\b', 'preflight code regex')
rep(build, r'0\.10\.3', r'0\.10\.4', 'preflight name regex')
rep(build, 'versionCode 48 / versionName 0.10.3', 'versionCode 49 / versionName 0.10.4', 'preflight message')
rep(build, 'Preflight v0.10.3 OK', 'Preflight v0.10.4 OK', 'preflight log')
rep(gradle, "versionCode 48\n        versionName '0.10.3'", "versionCode 49\n        versionName '0.10.4'", 'gradle version')
rep(manifest, 'android:versionCode="48"\n    android:versionName="0.10.3"', 'android:versionCode="49"\n    android:versionName="0.10.4"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.3";', 'private static final String APP_VERSION = "0.10.4";', 'UI version')

wr(print_correction, r'''package it.darkroom.timer;

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
''')

wr(print_sequence, r'''package it.darkroom.timer;

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
''')
print('v0.10.4 OK correction models', flush=True)

correction_editor = r'''    private void showPrintCorrectionEditor(final int index) {
        if (darkroomMode || printSequence == null || index < 0 || index >= printSequence.corrections.size()) return;
        final PrintCorrection original = printSequence.corrections.get(index);
        final boolean creatingCorrection = original.label == null || original.label.trim().isEmpty();
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
                ? "Riduce l’esposizione durante la base. Con Split Grade scegli se applicarlo al giallo, al magenta o a entrambe le fasi."
                : "Aggiunge una nuova esposizione dopo la base. Con Split Grade scegli il filtro del BURN.", 12, MUTED, false);
        explain.setPadding(0, dp(4), 0, dp(10)); panel.addView(explain, lp(-1,-2));

        final EditText label = editField(c.isDodge() ? "Zona / maschera — es. Volto" : "Zona — es. Cielo", c.label);
        panel.addView(label, margin(lp(-1, dp(52)),0,0,0,10));

        final String[] phase = {printSequence.hasSplit()
                ? (c.isBoth() ? PrintCorrection.PHASE_BOTH : (c.isHard() ? PrintCorrection.PHASE_HARD : PrintCorrection.PHASE_SOFT))
                : PrintCorrection.PHASE_BASE};
        final String[] burnMode = {PrintCorrection.normalizeBurnFilter(c.burnFilterMode)};
        final int[] burnFilterValue = {PrintCorrection.snap5(c.burnFilterValue)};

        if (printSequence.hasSplit() && c.isDodge()) {
            panel.addView(text("APPLICA DURANTE",11,MUTED,true), margin(lp(-1,-2),0,0,0,4));
            LinearLayout phases=new LinearLayout(this); phases.setOrientation(LinearLayout.HORIZONTAL);
            final Button soft=compactButton("GIALLO");
            final Button hard=compactButton("MAGENTA");
            final Button both=compactButton("ENTRAMBE");
            final Runnable style=()->{
                boolean sft=PrintCorrection.PHASE_SOFT.equals(phase[0]);
                boolean hrd=PrintCorrection.PHASE_HARD.equals(phase[0]);
                boolean bth=PrintCorrection.PHASE_BOTH.equals(phase[0]);
                soft.setBackground(roundRect(sft?featureColor:Color.rgb(55,60,64),8,0,0));
                hard.setBackground(roundRect(hrd?featureColor:Color.rgb(55,60,64),8,0,0));
                both.setBackground(roundRect(bth?featureColor:Color.rgb(55,60,64),8,0,0));
                soft.setTextColor(Color.WHITE); hard.setTextColor(Color.WHITE); both.setTextColor(Color.WHITE);
            };
            soft.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_SOFT;style.run();});
            hard.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_HARD;style.run();});
            both.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_BOTH;style.run();});
            style.run();
            phases.addView(soft,margin(lp(0,dp(46),1f),0,0,dp(3),0));
            phases.addView(hard,margin(lp(0,dp(46),1f),dp(3),0,dp(3),0));
            phases.addView(both,margin(lp(0,dp(46),1f),dp(3),0,0,0));
            panel.addView(phases,margin(lp(-1,-2),0,0,0,10));
        }

        final LinearLayout customFilterPanel = new LinearLayout(this);
        customFilterPanel.setOrientation(LinearLayout.VERTICAL);
        if (printSequence.hasSplit() && c.isBurn()) {
            panel.addView(text("FILTRO DEL BURN",11,MUTED,true), margin(lp(-1,-2),0,0,0,4));
            LinearLayout filters=new LinearLayout(this); filters.setOrientation(LinearLayout.HORIZONTAL);
            final Button fy=compactButton("GIALLO SPLIT");
            final Button fm=compactButton("MAGENTA SPLIT");
            final Button fc=compactButton("PERSONALIZZATO");
            final Runnable[] filterStyle = new Runnable[1];
            filterStyle[0]=()->{
                String m=PrintCorrection.normalizeBurnFilter(burnMode[0]);
                boolean y=PrintCorrection.BURN_FILTER_Y_SPLIT.equals(m);
                boolean mg=PrintCorrection.BURN_FILTER_M_SPLIT.equals(m);
                boolean custom=!y&&!mg;
                fy.setBackground(roundRect(y?featureColor:Color.rgb(55,60,64),8,0,0));
                fm.setBackground(roundRect(mg?featureColor:Color.rgb(55,60,64),8,0,0));
                fc.setBackground(roundRect(custom?featureColor:Color.rgb(55,60,64),8,0,0));
                fy.setTextColor(Color.WHITE); fm.setTextColor(Color.WHITE); fc.setTextColor(Color.WHITE);
                customFilterPanel.setVisibility(custom?View.VISIBLE:View.GONE);
            };
            fy.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_Y_SPLIT;phase[0]=PrintCorrection.PHASE_SOFT;filterStyle[0].run();});
            fm.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_M_SPLIT;phase[0]=PrintCorrection.PHASE_HARD;filterStyle[0].run();});
            fc.setOnClickListener(v->{
                if(!PrintCorrection.BURN_FILTER_CUSTOM_Y.equals(burnMode[0])&&!PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0]))
                    burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_Y;
                phase[0]=PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0])?PrintCorrection.PHASE_HARD:PrintCorrection.PHASE_SOFT;
                filterStyle[0].run();
            });
            filters.addView(fy,margin(lp(0,dp(48),1f),0,0,dp(3),0));
            filters.addView(fm,margin(lp(0,dp(48),1f),dp(3),0,dp(3),0));
            filters.addView(fc,margin(lp(0,dp(48),1f),dp(3),0,0,0));
            panel.addView(filters,margin(lp(-1,-2),0,0,0,7));

            customFilterPanel.addView(text("FILTRO PERSONALIZZATO",11,MUTED,true),margin(lp(-1,-2),0,2,0,4));
            LinearLayout customType=new LinearLayout(this); customType.setOrientation(LinearLayout.HORIZONTAL);
            final Button cy=compactButton("GIALLO"); final Button cm=compactButton("MAGENTA");
            customType.addView(cy,margin(lp(0,dp(44),1f),0,0,dp(4),0));
            customType.addView(cm,margin(lp(0,dp(44),1f),dp(4),0,0,0));
            customFilterPanel.addView(customType,lp(-1,-2));
            LinearLayout customValueRow=new LinearLayout(this); customValueRow.setOrientation(LinearLayout.HORIZONTAL); customValueRow.setGravity(Gravity.CENTER);
            Button cfMinus=smallButton("−"); Button cfPlus=smallButton("+");
            final TextView cfValue=text("",28,featureColor,true); cfValue.setGravity(Gravity.CENTER);
            customValueRow.addView(cfMinus,lp(dp(62),dp(56))); customValueRow.addView(cfValue,lp(0,dp(60),1f)); customValueRow.addView(cfPlus,lp(dp(62),dp(56)));
            customFilterPanel.addView(customValueRow,lp(-1,-2));
            final Runnable customStyle=()->{
                boolean mag=PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0]);
                cy.setBackground(roundRect(!mag?featureColor:Color.rgb(55,60,64),8,0,0));
                cm.setBackground(roundRect(mag?featureColor:Color.rgb(55,60,64),8,0,0));
                cy.setTextColor(Color.WHITE);cm.setTextColor(Color.WHITE);
                cfValue.setText((mag?"M ":"Y ")+burnFilterValue[0]);
            };
            cy.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_Y;phase[0]=PrintCorrection.PHASE_SOFT;customStyle.run();filterStyle[0].run();});
            cm.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_M;phase[0]=PrintCorrection.PHASE_HARD;customStyle.run();filterStyle[0].run();});
            cfMinus.setOnClickListener(v->{burnFilterValue[0]=Math.max(0,burnFilterValue[0]-5);customStyle.run();});
            cfPlus.setOnClickListener(v->{burnFilterValue[0]=Math.min(200,burnFilterValue[0]+5);customStyle.run();});
            customStyle.run();
            panel.addView(customFilterPanel,margin(lp(-1,-2),0,0,0,10));
            filterStyle[0].run();
        }

        final boolean[] useStops={c.quarterStops>0};
        final int[] ms={Math.max(c.isDodge()?1000:500,c.milliseconds)};
        final int[] quarters={Math.max(1,c.quarterStops>0?c.quarterStops:1)};
        LinearLayout methods=new LinearLayout(this); methods.setOrientation(LinearLayout.HORIZONTAL);
        final Button secondsMode=compactButton("SECONDI"); final Button stopMode=compactButton("F-STOP");
        methods.addView(secondsMode,margin(lp(0,dp(46),1f),0,0,dp(4),0)); methods.addView(stopMode,margin(lp(0,dp(46),1f),dp(4),0,0,0)); panel.addView(methods,margin(lp(-1,-2),0,0,0,10));
        final Runnable styleMethods=()->{
            secondsMode.setBackground(roundRect(!useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));
            stopMode.setBackground(roundRect(useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));
            secondsMode.setTextColor(Color.WHITE);stopMode.setTextColor(Color.WHITE);
        };

        LinearLayout selector=new LinearLayout(this); selector.setOrientation(LinearLayout.HORIZONTAL); selector.setGravity(Gravity.CENTER);
        Button minus=smallButton("−"); Button plus=smallButton("+"); final TextView value=text("",30,featureColor,true); value.setGravity(Gravity.CENTER); value.setSingleLine(true);
        selector.addView(minus,lp(dp(62),dp(58))); selector.addView(value,lp(0,dp(64),1f)); selector.addView(plus,lp(dp(62),dp(58))); panel.addView(selector,lp(-1,-2));
        final Runnable refresh=()->{
            if(useStops[0]) value.setText(c.isDodge()?TimingMath.dodgeStopLabel(quarters[0]):TimingMath.stopLabel(quarters[0]));
            else value.setText(formatTime(ms[0]));
        };
        secondsMode.setOnClickListener(v->{useStops[0]=false;styleMethods.run();refresh.run();});
        stopMode.setOnClickListener(v->{useStops[0]=true;styleMethods.run();refresh.run();});
        minus.setOnClickListener(v->{if(useStops[0])quarters[0]=Math.max(1,quarters[0]-1);else ms[0]=Math.max(c.isDodge()?1000:500,ms[0]-500);refresh.run();});
        plus.setOnClickListener(v->{
            if(useStops[0]) quarters[0]=Math.min(16,quarters[0]+1);
            else if(c.isDodge()){
                int baseMs;
                if(printSequence.hasSplit()&&PrintCorrection.PHASE_BOTH.equals(phase[0])) baseMs=Math.min(printSequence.split.softMs,printSequence.split.hardMs);
                else baseMs=printSequence.baseMsForPhase(phase[0],printWidthMs);
                ms[0]=Math.min(Math.max(1000,baseMs-500),ms[0]+500);
            } else ms[0]=Math.min(36000000,ms[0]+500);
            refresh.run();
        });
        styleMethods.run(); refresh.run();

        Button save=compactButton("SALVA CORREZIONE"); save.setBackground(roundRect(featureColor,9,0,0)); save.setTextColor(Color.WHITE);
        save.setOnClickListener(v->{
            String name=label.getText().toString().trim();
            c.label=name.isEmpty()?(c.isDodge()?"Zona da mascherare":"Zona da bruciare"):name;
            if(c.isDodge()){
                c.phase=printSequence.hasSplit()?phase[0]:PrintCorrection.PHASE_BASE;
                int baseMs=(printSequence.hasSplit()&&c.isBoth())?Math.min(printSequence.split.softMs,printSequence.split.hardMs):printSequence.baseMsFor(c,printWidthMs);
                if(useStops[0]){
                    c.quarterStops=quarters[0]; c.milliseconds=c.resolvedMs(baseMs);
                } else {
                    if(baseMs<=1000){Toast.makeText(this,"Il DODGE richiede una fase superiore a 1,0 s",Toast.LENGTH_LONG).show();return;}
                    c.quarterStops=0; c.milliseconds=TimingMath.snap500(ms[0],1000,Math.max(1000,baseMs-500));
                }
            } else {
                c.burnFilterMode=printSequence.hasSplit()?PrintCorrection.normalizeBurnFilter(burnMode[0]):PrintCorrection.BURN_FILTER_Y_SPLIT;
                c.burnFilterValue=PrintCorrection.snap5(burnFilterValue[0]);
                c.phase=printSequence.hasSplit()?(c.burnUsesMagenta()?PrintCorrection.PHASE_HARD:PrintCorrection.PHASE_SOFT):PrintCorrection.PHASE_BASE;
                int baseMs=printSequence.baseMsFor(c,printWidthMs);
                if(useStops[0]){c.quarterStops=quarters[0];c.milliseconds=c.resolvedMs(baseMs);}
                else{c.quarterStops=0;c.milliseconds=TimingMath.snap500(ms[0],500,36000000);}
            }
            printSequence.corrections.set(index,c);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();
        });
        panel.addView(save,margin(lp(-1,dp(52)),0,12,0,0));

        Button delete=compactButton("ELIMINA CORREZIONE");delete.setTextColor(Color.WHITE);delete.setBackground(roundRect(RED,9,0,0));
        delete.setOnClickListener(v->{printSequence.corrections.remove(index);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();});
        panel.addView(delete,margin(lp(-1,dp(48)),0,8,0,0));

        Button close=compactButton("ANNULLA");close.setTextColor(Color.WHITE);close.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
        close.setOnClickListener(v->{
            if(creatingCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index)==original){
                printSequence.corrections.remove(index); persistPrintSequence();
            }
            dialog.dismiss(); showPrintSequenceDialog();
        });
        panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel);Window w=dialog.getWindow();if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent);dialog.show();
        if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.96f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

'''
rrep(main, r'    private void showPrintCorrectionEditor\(final int index\) \{.*?(?=    private boolean validatePrintSequenceForBase\(\))', correction_editor, 'DODGE/BURN editor semantics')

validation = r'''    private boolean validatePrintSequenceForBase() {
        if (printSequence == null || printSequence.isEmpty()) return true;
        if (printSequence.hasSplit()) {
            printSequence.split.sanitize();
            if (printSequence.split.totalMs() > printWidthMs) {
                setStatusPresentation("ATTENZIONE", "SPLIT GRADE: morbida + dura non possono superare la base " + formatTime(printWidthMs), RED);
                return false;
            }
        }
        for (PrintCorrection c : printSequence.dodges()) {
            if (printSequence.hasSplit() && c.isBoth()) {
                int softCue = c.resolvedMs(printSequence.split.softMs);
                int hardCue = c.resolvedMs(printSequence.split.hardMs);
                if (softCue >= printSequence.split.softMs || hardCue >= printSequence.split.hardMs) {
                    setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": deve poter terminare prima della fine sia del giallo sia del magenta", RED);
                    return false;
                }
                continue;
            }
            int baseMs = printSequence.baseMsFor(c, printWidthMs);
            int cueMs = c.resolvedMs(baseMs);
            if (cueMs >= baseMs) {
                setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": il cue deve avvenire prima della fine della esposizione " + (printSequence.hasSplit() ? (c.isHard() ? "magenta" : "gialla") : "base"), RED);
                return false;
            }
        }
        return true;
    }

'''
rrep(main, r'    private boolean validatePrintSequenceForBase\(\) \{.*?(?=    private LinearLayout buildTestPanel\(\))', validation, 'DODGE both validation')

rep(service, 'msg = "SPLIT GRADE ARMATO — MORBIDA Y " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + " — premi il pulsante fisico";', 'msg = "SPLIT GRADE ARMATO — GIALLO " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + dodgeStatusSuffix(PrintCorrection.PHASE_SOFT) + " — premi il pulsante fisico";', 'first split status with dodge')
rep(service, 'if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(printSequence.split.softPrompt());', 'if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_SOFT));', 'first split voice with dodge')

split_stage = r'''    private void prepareSplitStage() {
        cancelPoll();
        cancelDodgeCues();
        cancelVoiceRepeatsKeepSpeech();
        if (printSequence == null || !printSequence.hasSplit() || splitStage != 1) return;
        String transition = "FASE GIALLA CONCLUSA — preparo il magenta";
        broadcast(STATE_WAITING_SPLIT, transition);
        updateNotification(transition);
        try {
            temporarilyRestoreSafelightForPause();
            currentPulseWidthMs = printSequence.split.hardMs;
            configurePulseVerified(currentPulseWidthMs);
            String msg = "SPLIT GRADE — MAGENTA " + printSequence.split.hardMagenta + " — " + seconds(currentPulseWidthMs)
                    + dodgeStatusSuffix(PrintCorrection.PHASE_HARD) + "\nPoi premi il pulsante fisico";
            TechnicalLog.add(this, techSessionId, "SPLIT fase magenta preparata • M " + printSequence.split.hardMagenta + " • " + seconds(currentPulseWidthMs));
            broadcast(STATE_WAITING_SPLIT, msg);
            updateNotification(msg.replace('\n', ' '));
            seenOn.set(false);
            scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_HARD));
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile preparare la fase magenta Split Grade: " + readable(e));
        }
    }

'''
rrep(service, r'    private void prepareSplitStage\(\) \{.*?(?=    private void prepareBurnStep\(\))', split_stage, 'split next-phase instructions')

burn_step = r'''    private void prepareBurnStep() {
        cancelPoll();
        cancelDodgeCues();
        cancelVoiceRepeatsKeepSpeech();
        java.util.List<PrintCorrection> burns = printSequence == null ? new java.util.ArrayList<>() : printSequence.burns();
        if (burnIndex < 0 || burnIndex >= burns.size()) return;
        PrintCorrection burn = burns.get(burnIndex);
        try {
            temporarilyRestoreSafelightForPause();
            int baseMs = printSequence.baseMsFor(burn, widthMs);
            currentPulseWidthMs = burn.resolvedMs(baseMs);
            configurePulseVerified(currentPulseWidthMs);
            String filter = burnFilterInstruction(burn);
            String amount = burn.usesFStop() ? TimingMath.stopLabel(burn.quarterStops) : seconds(currentPulseWidthMs);
            String msg = "BURN " + burn.safeLabel().toUpperCase(Locale.ITALY) + " — " + amount
                    + (filter.isEmpty() ? "" : "\n" + filter)
                    + "\nPrepara la maschera e premi il pulsante fisico";
            TechnicalLog.add(this, techSessionId, "BURN preparato " + (burnIndex + 1) + "/" + burns.size() + " • " + burn.displayLine(baseMs, printSequence.hasSplit()));
            broadcast(STATE_WAITING_BURN, msg);
            updateNotification(msg.replace('\n', ' '));
            seenOn.set(false);
            String voice = "Bruciatura " + burn.safeLabel() + ". "
                    + (filter.isEmpty() ? "" : filter + ". ")
                    + "Prepara la maschera. Premi il pulsante.";
            scheduleVoiceInstruction(voice);
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile preparare la bruciatura " + (burnIndex + 1) + ": " + readable(e));
        }
    }

'''
rrep(service, r'    private void prepareBurnStep\(\) \{.*?(?=    private String burnFilterInstruction\(PrintCorrection burn\))', burn_step, 'burn post-split step')

burn_filter = r'''    private String burnFilterInstruction(PrintCorrection burn) {
        if (burn == null || printSequence == null || !printSequence.hasSplit()) return "";
        String mode = PrintCorrection.normalizeBurnFilter(burn.burnFilterMode);
        if (PrintCorrection.BURN_FILTER_M_SPLIT.equals(mode)) return "Imposta Magenta " + printSequence.split.hardMagenta;
        if (PrintCorrection.BURN_FILTER_CUSTOM_Y.equals(mode)) return "Imposta Giallo " + PrintCorrection.snap5(burn.burnFilterValue);
        if (PrintCorrection.BURN_FILTER_CUSTOM_M.equals(mode)) return "Imposta Magenta " + PrintCorrection.snap5(burn.burnFilterValue);
        return "Imposta Giallo " + printSequence.split.softYellow;
    }

    private String dodgePreparationText(String phase) {
        if (printSequence == null || !printSequence.hasSplit()) return "";
        java.util.List<PrintCorrection> ds = printSequence.dodgesForPhase(phase);
        if (ds.isEmpty()) return "";
        StringBuilder b = new StringBuilder();
        for (PrintCorrection d : ds) {
            if (b.length() > 0) b.append(", ");
            b.append(d.safeLabel());
        }
        return b.toString();
    }

    private String dodgeStatusSuffix(String phase) {
        String d = dodgePreparationText(phase);
        return d.isEmpty() ? "" : " · PREPARA DODGE " + d.toUpperCase(Locale.ITALY);
    }

    private String splitPhasePrompt(String phase) {
        boolean hard = PrintCorrection.PHASE_HARD.equals(phase);
        String d = dodgePreparationText(phase);
        StringBuilder b = new StringBuilder();
        b.append(hard ? "Magenta " : "Giallo ")
                .append(hard ? printSequence.split.hardMagenta : printSequence.split.softYellow).append(".");
        if (!d.isEmpty()) b.append(" Prepara il dodge ").append(d).append(".");
        b.append(" Premi il pulsante.");
        return b.toString();
    }

'''
rrep(service, r'    private String burnFilterInstruction\(PrintCorrection burn\) \{.*?(?=    private String burnExposureMessage\(\))', burn_filter, 'burn filter + dodge prep helpers')

rep(service, '                    cancelVoicePrompt();\n                    long estimatedOnAt = observedAt;', '                    cancelVoiceRepeatsKeepSpeech();\n                    long estimatedOnAt = observedAt;', 'do not truncate setup voice on relay ON')

rep(service, '    private volatile String voiceRepeatWords = "";\n    private ScheduledFuture<?> voiceRepeatTask;', '    private volatile String voiceRepeatWords = "";\n    private volatile long voiceRepeatGeneration = 0L;\n    private ScheduledFuture<?> voiceRepeatTask;', 'voice generation field')
rep(service, '                        if (utteranceId != null && utteranceId.startsWith("darkroom-repeat-")) scheduleNextVoiceRepeat();', '                        handleVoiceRepeatFinished(utteranceId);', 'voice listener generation', count=2)

voice_helpers = r'''    private boolean voiceGuideEnabled() {
        return getSharedPreferences("ui", MODE_PRIVATE).getBoolean("voiceGuide", true);
    }

    private void speakOnce(String words) {
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty() || !ttsReady || tts == null) return;
        try { tts.speak(words, TextToSpeech.QUEUE_FLUSH, null, "darkroom-once-" + System.nanoTime()); } catch (Exception ignored) {}
    }

    private void scheduleVoiceInstruction(final String words) {
        cancelVoiceRepeatsKeepSpeech();
        if (!voiceGuideEnabled() || words == null || words.trim().isEmpty()) return;
        voiceRepeatActive = true;
        voiceRepeatWords = words.trim();
        final long gen = ++voiceRepeatGeneration;
        voiceRepeatTask = cueIo.schedule(() -> speakRepeatingVoice(gen), 250L, TimeUnit.MILLISECONDS);
    }

    private void speakRepeatingVoice(final long gen) {
        if (gen != voiceRepeatGeneration || !voiceRepeatActive || !voiceGuideEnabled()
                || voiceRepeatWords.isEmpty() || !ttsReady || tts == null) return;
        try {
            if (tts.isSpeaking()) {
                voiceRepeatTask = cueIo.schedule(() -> speakRepeatingVoice(gen), 250L, TimeUnit.MILLISECONDS);
                return;
            }
            tts.speak(voiceRepeatWords, TextToSpeech.QUEUE_ADD, null,
                    "darkroom-repeat-" + gen + "-" + System.nanoTime());
        } catch (Exception ignored) {
            scheduleNextVoiceRepeat(gen);
        }
    }

    private void handleVoiceRepeatFinished(String utteranceId) {
        long gen = voiceRepeatGeneration;
        if (utteranceId != null && utteranceId.startsWith("darkroom-repeat-" + gen + "-"))
            scheduleNextVoiceRepeat(gen);
    }

    private void scheduleNextVoiceRepeat(final long gen) {
        if (gen != voiceRepeatGeneration || !voiceRepeatActive || voiceRepeatWords.isEmpty()) return;
        if (voiceRepeatTask != null) voiceRepeatTask.cancel(false);
        voiceRepeatTask = cueIo.schedule(() -> speakRepeatingVoice(gen), 8_000L, TimeUnit.MILLISECONDS);
    }

    private void cancelVoiceRepeatsKeepSpeech() {
        voiceRepeatActive = false;
        voiceRepeatWords = "";
        voiceRepeatGeneration++;
        if (voiceRepeatTask != null) {
            voiceRepeatTask.cancel(false);
            voiceRepeatTask = null;
        }
    }

    private void cancelVoicePrompt() {
        cancelVoiceRepeatsKeepSpeech();
        try { if (tts != null) tts.stop(); } catch (Exception ignored) {}
    }

'''
rrep(service, r'    private boolean voiceGuideEnabled\(\) \{.*?(?=    private void dodgeCueFeedback\(\))', voice_helpers, 'voice no-truncate + 8 second repeat')

checks = {
    build:['VERSION_NAME = "0.10.4"','VERSION_CODE = "49"'],
    main:['private static final String APP_VERSION = "0.10.4"','APPLICA DURANTE','ENTRAMBE','FILTRO DEL BURN','PERSONALIZZATO'],
    print_correction:['PHASE_BOTH','BURN_FILTER_CUSTOM_Y','burnFilterLabel()'],
    print_sequence:['c.isBoth()','burnFilterMode','burnFilterValue'],
    service:['splitPhasePrompt','dodgeStatusSuffix','cancelVoiceRepeatsKeepSpeech','8_000L','BURN_FILTER_CUSTOM_M']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.4 verifica fallita: {needle} in {p}')
print('v0.10.4 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
