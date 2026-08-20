#!/usr/bin/env python3
from pathlib import Path

root = Path('combined/src/main/java/it/darkroom/timer')
main = root / 'MainActivity.java'
enlargement = root / 'EnlargementActivity.java'

for p in (main, enlargement, root / 'LogEntry.java', root / 'LogStore.java'):
    if not p.exists():
        raise SystemExit('v0.2.0 enlargement/log: generated file missing: ' + str(p))

# -----------------------------------------------------------------------------
# MAIN ACTIVITY
# -----------------------------------------------------------------------------
s = main.read_text(encoding='utf-8')

# 1) The v0.1.8 patch added a resize button inside every session mini-card.
# Remove it completely: the action belongs only to the individual STAMPA editor.
sg = s.find('    private void showLogGroup(final LogGroup group) {')
if sg < 0:
    raise SystemExit('v0.2.0 enlargement/log: showLogGroup missing')
sg_end = s.find('\n    private ', sg + 20)
if sg_end < 0:
    raise SystemExit('v0.2.0 enlargement/log: showLogGroup end missing')
seg = s[sg:sg_end]
resize_marker = '                Button resizeEntry = compactButton("RIDIMENSIONA STAMPA");'
rm = seg.find(resize_marker)
if rm < 0:
    raise SystemExit('v0.2.0 enlargement/log: old session resize button missing')
rm_start = seg.rfind('            if (item.exposureMs > 0) {', 0, rm)
rm_end = seg.find('            step.setClickable(true);', rm)
if rm_start < 0 or rm_end < 0:
    raise SystemExit('v0.2.0 enlargement/log: cannot isolate old session resize button')
seg = seg[:rm_start] + seg[rm_end:]
s = s[:sg] + seg + s[sg_end:]

# 2) Snapshot enlargement metadata at ARM time, without touching SONOFF timing.
# The timestamp lets LOG reject a stale snapshot after a later failed arm attempt.
arm_marker = '''        if (mode == MODE_PRINT) {\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);'''
arm_repl = '''        if (mode == MODE_PRINT) {\n            SharedPreferences activeUi = getSharedPreferences("ui", MODE_PRIVATE);\n            getSharedPreferences("log_session", MODE_PRIVATE).edit()\n                    .putString("pendingEnlargementMeta", activeUi.getString("enlargementMeta", ""))\n                    .putLong("pendingEnlargementAt", System.currentTimeMillis())\n                    .apply();\n            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);'''
if arm_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: ARM print marker missing')
s = s.replace(arm_marker, arm_repl, 1)

# 3) Fix new LogEntry snapshot. v0.1.8 read enlargementMeta from log_session under
# a key that was never written. Associate the snapshot with the completed print.
wrong_snapshot = '        e.enlargementMeta = p.getString("enlargementMeta", "");'
right_snapshot = '''        long enlargementArmAt = p.getLong("pendingEnlargementAt", 0L);\n        e.enlargementMeta = (printAt > 0 && enlargementArmAt > 0 && enlargementArmAt <= printAt)\n                ? p.getString("pendingEnlargementMeta", "") : "";'''
if wrong_snapshot not in s:
    raise SystemExit('v0.2.0 enlargement/log: v0.1.8 enlargement snapshot marker missing')
s = s.replace(wrong_snapshot, right_snapshot, 1)

# 4) When a LOG print becomes the active plan, carry its own enlargement snapshot.
old_use_prefs = '''        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).putString("testBaseFilterType", testBaseFilterType).putInt("testBaseFilterValue", testBaseFilterValue).apply();'''
new_use_prefs = '''        getSharedPreferences("ui", MODE_PRIVATE).edit()\n                .putString("exposureRecipe", exposureRecipe.encode())\n                .putString("testBaseFilterType", testBaseFilterType)\n                .putInt("testBaseFilterValue", testBaseFilterValue)\n                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n                .apply();'''
if old_use_prefs not in s:
    raise SystemExit('v0.2.0 enlargement/log: useLogEntryForPrint prefs marker missing')
s = s.replace(old_use_prefs, new_use_prefs, 1)

# Keep the same metadata in the reprint template as a fallback for the next log.
reprint_marker = '''                .putString("recipeState", entry.recipeState == null ? "" : entry.recipeState)\n                .putString("testBaseFilterType", entry.testBaseFilterType == null ? ExposureRecipe.FILTER_NONE : entry.testBaseFilterType)'''
reprint_repl = '''                .putString("recipeState", entry.recipeState == null ? "" : entry.recipeState)\n                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n                .putString("testBaseFilterType", entry.testBaseFilterType == null ? ExposureRecipe.FILTER_NONE : entry.testBaseFilterType)'''
if reprint_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: reprint template marker missing')
s = s.replace(reprint_marker, reprint_repl, 1)

apply_template_marker = '''        entry.printSequence = template.getString("printSequence", "");\n        if (entry.recipeState == null || entry.recipeState.trim().isEmpty()) entry.recipeState = template.getString("recipeState", "");'''
apply_template_repl = '''        entry.printSequence = template.getString("printSequence", "");\n        if (entry.recipeState == null || entry.recipeState.trim().isEmpty()) entry.recipeState = template.getString("recipeState", "");\n        if (entry.enlargementMeta == null || entry.enlargementMeta.trim().isEmpty()) entry.enlargementMeta = template.getString("enlargementMeta", "");'''
if apply_template_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: applyReprintTemplate marker missing')
s = s.replace(apply_template_marker, apply_template_repl, 1)

# 5) Show the enlargement snapshot in the individual LOG editor.
auto_marker = '''                "\\nPiano di stampa: " + sequenceRecipe +\n                "\\nData: " + formatDate(entry.timestamp) +'''
auto_repl = '''                "\\nPiano di stampa: " + sequenceRecipe +\n                "\\nIngrandimento: " + enlargementLogSummary(entry.enlargementMeta) +\n                "\\nData: " + formatDate(entry.timestamp) +'''
if auto_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: LOG automatic data marker missing')
s = s.replace(auto_marker, auto_repl, 1)

# Helper for a concise, readable LOG line.
editor_marker = '    private void showLogEditor(final LogEntry entry, final boolean isNew) {'
if editor_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: showLogEditor marker missing')
helper = r'''    private static String enlargementMetaValue(String meta, String key) {
        if (meta == null || meta.trim().isEmpty()) return "";
        for (String part : meta.split("\\|")) {
            if (part.startsWith(key + "=")) return part.substring(key.length() + 1);
        }
        return "";
    }

    private String enlargementLogSummary(String meta) {
        if (meta == null || meta.trim().isEmpty()) return "—";
        String paper = enlargementMetaValue(meta, "paper").replace('.', ',').replace("x", " × ");
        String lens = enlargementMetaValue(meta, "lens");
        String beta = enlargementMetaValue(meta, "beta");
        String col = enlargementMetaValue(meta, "col");
        String fill = enlargementMetaValue(meta, "fill");
        String mode = "0".equals(fill) ? "immagine intera" : ("1".equals(fill) ? "riempi larghezza" : ("2".equals(fill) ? "riempi altezza" : ""));
        StringBuilder b = new StringBuilder();
        if (!paper.isEmpty()) b.append(paper).append(" cm · orizzontale");
        if (!lens.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(lens).append(" mm");
        if (!beta.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
            catch (Exception ignored) {}
        }
        if (!col.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("colonna ").append(String.format(Locale.ITALY, "%.1f", Double.parseDouble(col))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(mode);
        return b.length() == 0 ? "—" : b.toString();
    }

'''
s = s.replace(editor_marker, helper + editor_marker, 1)

# 6) Move RIDIMENSIONA STAMPA into the individual STAMPA editor, immediately
# after USA PER STAMPA and before JPG export. It saves any visible editor changes
# into that exact LogEntry before handing its id to EnlargementActivity.
use_end = '''                panel.addView(useForPrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n            }'''
resize_block = '''                panel.addView(useForPrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n\n                Button resizePrint = compactButton("RIDIMENSIONA STAMPA");\n                resizePrint.setTextColor(Color.WHITE);\n                resizePrint.setBackground(roundRect(Color.rgb(55,60,64), 9, 0, 0));\n                resizePrint.setOnClickListener(v -> {\n                    entry.title = title.getText().toString().trim();\n                    entry.negative = negative[0];\n                    entry.aperture = aperture.getText().toString().trim();\n                    entry.columnHeight = column.getText().toString().trim();\n                    entry.magenta = magenta.getText().toString().trim();\n                    entry.yellow = yellow.getText().toString().trim();\n                    entry.density = density.getText().toString().trim();\n                    entry.paper = paper.getText().toString().trim();\n                    entry.notes = trimNotes(notes.getText().toString().trim());\n                    entry.favorite = favorite[0];\n                    LogStore.save(this, entry);\n                    dialog.dismiss();\n                    Intent resizeIntent = new Intent(this, EnlargementActivity.class)\n                            .putExtra("mode", "resize")\n                            .putExtra("originLogId", entry.id);\n                    startActivity(resizeIntent);\n                });\n                panel.addView(resizePrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n            }'''
if use_end not in s:
    raise SystemExit('v0.2.0 enlargement/log: USA PER STAMPA block end missing')
s = s.replace(use_end, resize_block, 1)

# 7) Reload derived filter/contrast state in place together with recipe and sequence.
onresume_marker = '''            exposureRecipe = ExposureRecipe.decode(ep.getString("exposureRecipe", ""));\n            printSequence = PrintSequence.decode(ep.getString("printSequence", ""));\n            mode = MODE_PRINT;'''
onresume_repl = '''            exposureRecipe = ExposureRecipe.decode(ep.getString("exposureRecipe", ""));\n            printSequence = PrintSequence.decode(ep.getString("printSequence", ""));\n            if (exposureRecipe != null && exposureRecipe.hasBase()) {\n                testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);\n                testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);\n            }\n            mode = MODE_PRINT;'''
if onresume_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: v0.1.8 onResume reload marker missing')
s = s.replace(onresume_marker, onresume_repl, 1)
refresh_marker = '''            if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));\n            updatePrintSequenceUi();\n            applyModeUi();'''
refresh_repl = '''            if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));\n            refreshTestBaseFilterUi();\n            updatePrintSequenceUi();\n            applyModeUi();'''
if refresh_marker not in s:
    raise SystemExit('v0.2.0 enlargement/log: onResume UI refresh marker missing')
s = s.replace(refresh_marker, refresh_repl, 1)

main.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# ENLARGEMENT ACTIVITY
# Rewrite the small activity cleanly. The validated Meopta tables and formula are
# unchanged; only flow, per-LogEntry sourcing, inline result and LOG derivation change.
# -----------------------------------------------------------------------------
java = r'''package it.darkroom.timer;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.Locale;

public final class EnlargementActivity extends Activity {
    // Validated Meopta Opemus 6 calibration tables. DO NOT change.
    static final double[][] C80={{1,6},{1.5,7},{2,10},{2.5,13},{3,17},{3.5,20},{4,24},{5,32},{6,40},{7,48},{7.6,53}};
    static final double[][] C50={{2.5,1},{3,2},{3.5,4},{4,6},{5,11},{6,16},{7,21},{7.6,24},{9,32},{10,37},{11,42},{13,52}};

    static final String[] PAPERS={
            "8,9 × 12,7","10,5 × 14,8","12,7 × 17,8","17,8 × 24,0","20,3 × 25,4",
            "24,0 × 30,5","27,9 × 35,6","30,5 × 40,6","40,6 × 50,8","50,8 × 61,0","PERSONALIZZATO"};
    static final double[][] PD={{8.9,12.7},{10.5,14.8},{12.7,17.8},{17.8,24.0},{20.3,25.4},{24.0,30.5},{27.9,35.6},{30.5,40.6},{40.6,50.8},{50.8,61.0}};
    static final String[] FILLS={"IMMAGINE INTERA","RIEMPI LARGHEZZA","RIEMPI ALTEZZA"};

    static final int BG=Color.BLACK;
    static final int PANEL=Color.rgb(24,24,24);
    static final int BUTTON=Color.rgb(55,60,64);
    static final int BORDER=Color.rgb(67,67,67);
    static final int MUTED=Color.rgb(170,166,162);
    static final int GREEN=Color.rgb(82,190,82);
    static final int TEXT=Color.rgb(246,243,238);

    SharedPreferences p;
    String mode;
    long originLogId;
    LogEntry originEntry;
    LinearLayout root;
    Spinner paper, fill, neg;
    EditText w,h;
    LinearLayout resultBox;
    Pending pending;

    static final class Pending {
        boolean is35;
        double W,H,b1,b2,c1,c2,factor,stops,pw,ph;
        String crop, oldMeta, newMeta, note;
        int oldBase,newBase;
        ExposureRecipe oldRecipe,newRecipe;
        PrintSequence oldSequence,newSequence;
    }

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        p=getSharedPreferences("ui",MODE_PRIVATE);
        mode=getIntent().getStringExtra("mode");
        if(mode==null)mode="setup";
        originLogId=getIntent().getLongExtra("originLogId",0L);
        originEntry=originLogId>0?findLogEntry(originLogId):null;
        if("resize".equals(mode)&&originEntry!=null&&!hasUsableMeta(originEntry)) renderLegacyOrigin();
        else renderMain();
    }

    LogEntry findLogEntry(long id){
        for(LogEntry e:LogStore.load(this)) if(e!=null&&e.id==id) return e;
        return null;
    }

    boolean hasUsableMeta(LogEntry e){
        if(e==null||e.enlargementMeta==null||e.enlargementMeta.trim().isEmpty())return false;
        if(Double.isNaN(num(e.enlargementMeta,"beta"))||Double.isNaN(num(e.enlargementMeta,"col")))return false;
        Boolean n=negativeFromEntry(e);
        if(n==null)return false;
        String mn=val(e.enlargementMeta,"neg");
        if(!mn.isEmpty() && (n?!"35".equals(mn):!"66".equals(mn))) return false;
        return true;
    }

    Boolean negativeFromEntry(LogEntry e){
        if(e==null)return null;
        String n=e.negative==null?"":e.negative.trim().toLowerCase(Locale.ITALY);
        if(n.contains("35"))return true;
        if(n.contains("6x6")||n.contains("6×6")||n.equals("66"))return false;
        return null;
    }

    Boolean sourceNegative(){
        if(originEntry!=null){Boolean e=negativeFromEntry(originEntry);if(e!=null)return e;}
        String m=sourceMeta();String n=val(m,"neg");
        if("35".equals(n))return true;if("66".equals(n))return false;
        return null;
    }

    String sourceMeta(){return originEntry!=null?(originEntry.enlargementMeta==null?"":originEntry.enlargementMeta):p.getString("enlargementMeta","");}
    String sourceRecipe(){return originEntry!=null?(originEntry.recipeState==null?"":originEntry.recipeState):p.getString("exposureRecipe","");}
    String sourceSequence(){return originEntry!=null?(originEntry.printSequence==null?"":originEntry.printSequence):p.getString("printSequence","");}

    int sourceBase(){
        ExposureRecipe r=ExposureRecipe.decode(sourceRecipe());
        if(r!=null&&r.operationalBaseMs>0)return r.operationalBaseMs;
        if(originEntry!=null&&originEntry.exposureMs>0)return originEntry.exposureMs;
        return p.getInt("printWidthMs",8500);
    }

    void renderMain(){
        boolean resize="resize".equals(mode);
        begin(resize?"RIDIMENSIONA STAMPA":"IMPOSTA INGRANDIMENTO",
                resize?"Trasforma una stampa mantenendo ricetta, filtri e rapporti temporali.":"Imposta il formato prima di trovare o salvare la stampa.");
        if(resize){
            Boolean a=sourceNegative();
            String sm=sourceMeta();
            if(a==null||Double.isNaN(num(sm,"beta"))){
                info("Mancano i dati necessari della stampa origine.");return;
            }
            root.addView(section("ORIGINE",originSummary(sm,a)));
            addFixedNegative(a);
            addPaperFields(sm);
            fill=spinner(FILLS);
            int fi=intVal(sm,"fill",0);fill.setSelection(Math.max(0,Math.min(2,fi)));
            root.addView(label("MODALITÀ FINALE",12,MUTED,true));root.addView(fill,lp(-1,dp(50)));
            Button calc=button("CALCOLA",BUTTON);calc.setOnClickListener(v->calculateResize(a));
            root.addView(calc,margin(lp(-1,dp(52)),0,dp(12),0,dp(10)));
            resultBox=new LinearLayout(this);resultBox.setOrientation(LinearLayout.VERTICAL);root.addView(resultBox,lp(-1,-2));
        }else{
            neg=spinner(new String[]{"35 mm — 50 mm","6×6 — 80 mm"});
            neg.setSelection(p.getInt("enlargementUiNeg",0));
            root.addView(label("NEGATIVO",12,MUTED,true));root.addView(neg,lp(-1,dp(50)));
            addPaperFields(p.getString("enlargementMeta",""));
            fill=spinner(FILLS);fill.setSelection(Math.max(0,Math.min(2,p.getInt("enlargementUiFill",0))));
            root.addView(label("MODALITÀ",12,MUTED,true));root.addView(fill,lp(-1,dp(50)));
            Button calc=button("CALCOLA",BUTTON);calc.setOnClickListener(v->calculateSetup());
            root.addView(calc,margin(lp(-1,dp(52)),0,dp(12),0,dp(10)));
            resultBox=new LinearLayout(this);resultBox.setOrientation(LinearLayout.VERTICAL);root.addView(resultBox,lp(-1,-2));
        }
    }

    void renderLegacyOrigin(){
        begin("RIDIMENSIONA STAMPA","Questa vecchia stampa non contiene ancora i dati d’ingrandimento. Registrali una sola volta.");
        Boolean a=negativeFromEntry(originEntry);
        if(a==null){
            info("Completa prima il campo NEGATIVO della scheda LOG (35 mm oppure 6×6), poi riprova.");return;
        }
        addFixedNegative(a);
        root.addView(label("FORMATO ORIGINALE DELLA STAMPA",13,TEXT,true));
        addPaperFields("");
        fill=spinner(FILLS);
        root.addView(label("MODALITÀ ORIGINALE",12,MUTED,true));root.addView(fill,lp(-1,dp(50)));
        Button save=button("SALVA E CONTINUA",GREEN);save.setTextColor(Color.BLACK);
        save.setOnClickListener(v->saveLegacyAndContinue(a));
        root.addView(save,margin(lp(-1,dp(54)),0,dp(14),0,0));
    }

    void saveLegacyAndContinue(boolean a){
        try{
            Dims d=readDims();Calc c=calc(a,d.W,d.H,fill.getSelectedItemPosition());
            if(c==null){info("FORMATO FUORI DALL’INTERVALLO CALIBRATO");return;}
            String meta=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.pw,c.ph,c.crop,0L,"");
            originEntry.enlargementMeta=meta;
            if(originEntry.columnHeight==null||originEntry.columnHeight.trim().isEmpty())originEntry.columnHeight=fmt(c.col);
            LogStore.save(this,originEntry);
            Toast.makeText(this,"Dati originali registrati nel LOG",Toast.LENGTH_SHORT).show();
            renderMain();
        }catch(Exception e){info("Inserisci dimensioni carta valide.");}
    }

    void calculateSetup(){
        try{
            boolean a=neg.getSelectedItemPosition()==0;Dims d=readDims();Calc c=calc(a,d.W,d.H,fill.getSelectedItemPosition());
            clearResult();
            if(c==null){infoInto(resultBox,"FORMATO FUORI DALL’INTERVALLO CALIBRATO");return;}
            String meta=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.pw,c.ph,c.crop,0L,"");
            p.edit().putString("enlargementMeta",meta).putString("enlargementLastLog","IMPOSTA INGRANDIMENTO · "+meta)
                    .putInt("enlargementUiNeg",neg.getSelectedItemPosition()).putInt("enlargementUiFill",fill.getSelectedItemPosition()).apply();
            resultBox.addView(section("RISULTATO",resultText(c)));
            TextView ok=label("Registrato nella ricetta corrente.",13,GREEN,true);ok.setGravity(Gravity.CENTER);resultBox.addView(ok,margin(lp(-1,-2),0,dp(8),0,0));
        }catch(Exception e){clearResult();infoInto(resultBox,"Inserisci dimensioni carta valide.");}
    }

    void calculateResize(boolean a){
        try{
            Dims d=readDims();Calc c=calc(a,d.W,d.H,fill.getSelectedItemPosition());clearResult();
            if(c==null){infoInto(resultBox,"FORMATO FUORI DALL’INTERVALLO CALIBRATO");return;}
            String old=sourceMeta();double b1=num(old,"beta"),c1=num(old,"col");
            if(Double.isNaN(b1)||Double.isNaN(c1)){if(originEntry!=null){renderLegacyOrigin();return;}infoInto(resultBox,"Mancano i dati dell’ingrandimento iniziale.");return;}
            double factor=Math.pow((c.beta+1)/(b1+1),2); // validated formula: unchanged
            double stops=Math.log(factor)/Math.log(2);
            int oldBase=sourceBase(),newBase=snap(oldBase*factor); // validated SONOFF 0.5 s rounding: unchanged
            ExposureRecipe oldR=ExposureRecipe.decode(sourceRecipe());
            ExposureRecipe newR=scaleRecipe(oldR,oldBase,factor);
            PrintSequence oldQ=PrintSequence.decode(sourceSequence());
            PrintSequence newQ=scaleSequence(oldQ,factor);
            String from=paperDisplay(old);String to=paperDisplay(d.W,d.H);
            String note="Derivata da "+from+" → "+to;
            String nm=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.pw,c.ph,c.crop,originLogId,from);
            Pending x=new Pending();x.is35=a;x.W=d.W;x.H=d.H;x.b1=b1;x.b2=c.beta;x.c1=c1;x.c2=c.col;x.factor=factor;x.stops=stops;x.pw=c.pw;x.ph=c.ph;x.crop=c.crop;x.oldMeta=old;x.newMeta=nm;x.note=note;x.oldBase=oldBase;x.newBase=newBase;x.oldRecipe=oldR;x.newRecipe=newR;x.oldSequence=oldQ;x.newSequence=newQ;pending=x;
            showPending(x);
        }catch(Exception e){clearResult();infoInto(resultBox,"Inserisci dimensioni carta valide.");}
    }

    void showPending(Pending x){
        clearResult();
        resultBox.addView(section("RISULTATO",String.format(Locale.ITALY,"β finale %.3f\nColonna teorica finale %.2f\nImmagine proiettata %.1f × %.1f cm\nCrop: %s",x.b2,x.c2,x.pw,x.ph,cropLabel(x.crop))));
        StringBuilder comp=new StringBuilder();
        comp.append(String.format(Locale.ITALY,"β %.3f → %.3f\nColonna %.2f → %.2f\nFattore ×%.2f\nVariazione %+.2f stop\nTempo base %.1f s → %.1f s",x.b1,x.b2,x.c1,x.c2,x.factor,x.stops,x.oldBase/1000.0,x.newBase/1000.0));
        String timed=timedChanges(x);
        if(!timed.isEmpty())comp.append('\n').append(timed);
        resultBox.addView(section("COMPENSAZIONE",comp.toString()));
        Button create=button("CREA",GREEN);create.setTextColor(Color.BLACK);create.setOnClickListener(v->{v.setEnabled(false);createDerived(x);});
        Button cancel=button("ANNULLA",BUTTON);cancel.setOnClickListener(v->{pending=null;clearResult();});
        resultBox.addView(create,margin(lp(-1,dp(54)),0,dp(12),0,0));
        resultBox.addView(cancel,margin(lp(-1,dp(48)),0,dp(8),0,dp(14)));
    }

    String timedChanges(Pending x){
        StringBuilder b=new StringBuilder();
        if(x.oldSequence.hasSplit()&&x.newSequence.hasSplit()){
            b.append(String.format(Locale.ITALY,"Split Grade morbido %.1f s → %.1f s",x.oldSequence.split.softMs/1000.0,x.newSequence.split.softMs/1000.0));
            b.append(String.format(Locale.ITALY,"\nSplit Grade duro %.1f s → %.1f s",x.oldSequence.split.hardMs/1000.0,x.newSequence.split.hardMs/1000.0));
        }
        int n=Math.min(x.oldSequence.corrections.size(),x.newSequence.corrections.size());
        for(int i=0;i<n;i++){
            PrintCorrection o=x.oldSequence.corrections.get(i),nn=x.newSequence.corrections.get(i);if(o==null||nn==null)continue;
            int ob=x.oldSequence.baseMsFor(o,x.oldBase),nb=x.newSequence.baseMsFor(nn,x.newBase);
            int om=o.resolvedMs(ob),nm=nn.resolvedMs(nb);
            if(b.length()>0)b.append('\n');
            b.append(o.isDodge()?"Dodge · ":"Burn · ").append(o.safeLabel()).append(String.format(Locale.ITALY," %.1f s → %.1f s",om/1000.0,nm/1000.0));
        }
        return b.toString();
    }

    ExposureRecipe scaleRecipe(ExposureRecipe r,int oldBase,double factor){
        if(r==null)r=new ExposureRecipe();
        ExposureRecipe n=ExposureRecipe.decode(r.encode());
        if(n.originalBaseMs>0)n.originalBaseMs=snap(n.originalBaseMs*factor);
        n.operationalBaseMs=snap((n.operationalBaseMs>0?n.operationalBaseMs:oldBase)*factor);
        n.baseChosenAt=System.currentTimeMillis();
        return n;
    }

    PrintSequence scaleSequence(PrintSequence q,double factor){
        PrintSequence n=PrintSequence.decode(q==null?"":q.encode());
        if(n.hasSplit()){n.split.softMs=snap(n.split.softMs*factor);n.split.hardMs=snap(n.split.hardMs*factor);n.split.sanitize();}
        for(PrintCorrection c:n.corrections)if(c!=null&&c.milliseconds>0)c.milliseconds=snap(c.milliseconds*factor);
        return n;
    }

    void createDerived(Pending x){
        p.edit().putString("exposureRecipe",x.newRecipe.encode()).putString("printSequence",x.newSequence.encode())
                .putInt("printWidthMs",x.newBase).putString("enlargementMeta",x.newMeta).putString("enlargementLastLog",x.note)
                .putString("testBaseFilterType",ExposureRecipe.normalizeFilter(x.newRecipe.filterType)).putInt("testBaseFilterValue",ExposureRecipe.snap5(x.newRecipe.filterValue))
                .putInt("mode",0).putBoolean("enlargementReloadPending",true).apply();
        saveDerivedLog(x);
        Toast.makeText(this,"Stampa ridimensionata · tempi a 0,5 s",Toast.LENGTH_LONG).show();
        finish();
    }

    void saveDerivedLog(Pending x){
        long now=System.currentTimeMillis();LogEntry d=new LogEntry();
        if(originEntry!=null){
            d.title=originEntry.title;d.negative=originEntry.negative;d.aperture=originEntry.aperture;d.magenta=originEntry.magenta;d.yellow=originEntry.yellow;d.density=originEntry.density;d.paper=originEntry.paper;d.notes=originEntry.notes;
            d.exposureMethod=originEntry.exposureMethod;d.exposureStep=originEntry.exposureStep;d.testMs=originEntry.testMs;d.testCount=originEntry.testCount;d.testMethod=originEntry.testMethod;d.testStep=originEntry.testStep;d.testStripTimes=originEntry.testStripTimes;d.testBaseFilterType=originEntry.testBaseFilterType;d.testBaseFilterValue=originEntry.testBaseFilterValue;
        }else{
            d.title="Stampa ridimensionata";d.negative=x.is35?"35mm":"6x6";d.exposureMethod=TimingMath.normalizeMethod(p.getString("timingMethod",TimingMath.METHOD_SECONDS));d.exposureStep=TimingMath.stepLabel(d.exposureMethod);d.testBaseFilterType=ExposureRecipe.normalizeFilter(x.newRecipe.filterType);d.testBaseFilterValue=ExposureRecipe.snap5(x.newRecipe.filterValue);
        }
        d.id=now;d.timestamp=now;d.favorite=false;d.columnHeight=fmt(x.c2);d.exposureMs=x.newSequence.hasSplit()?x.newSequence.split.totalMs():x.newBase;d.printSequence=x.newSequence.encode();d.recipeState=x.newRecipe.encode();d.enlargementMeta=x.newMeta;
        String oldNotes=d.notes==null?"":d.notes.trim();d.notes=oldNotes.isEmpty()?x.note:(oldNotes+" · "+x.note);
        LogStore.save(this,d);
    }

    void addFixedNegative(boolean a){
        root.addView(label("NEGATIVO / OBIETTIVO",12,MUTED,true));
        TextView fixed=label(a?"35 mm · obiettivo 50 mm":"6×6 · obiettivo 80 mm",16,TEXT,true);fixed.setPadding(dp(13),dp(12),dp(13),dp(12));fixed.setBackground(bg(PANEL,10,BORDER,1));root.addView(fixed,margin(lp(-1,-2),0,0,0,dp(10)));
    }

    void addPaperFields(String meta){
        paper=spinner(PAPERS);w=input("Larghezza carta cm");h=input("Altezza carta cm");
        root.addView(label("FORMATO CARTA FOMA",12,MUTED,true));root.addView(paper,lp(-1,dp(50)));
        root.addView(label("LARGHEZZA CARTA (cm)",12,MUTED,true));root.addView(w,lp(-1,dp(50)));
        root.addView(label("ALTEZZA CARTA (cm)",12,MUTED,true));root.addView(h,lp(-1,dp(50)));
        TextView landscape=label("ORIENTAMENTO · ORIZZONTALE",12,MUTED,true);root.addView(landscape,margin(lp(-1,-2),0,dp(5),0,dp(10)));
        paper.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?>a){}public void onItemSelected(AdapterView<?>a,View v,int pos,long id){if(pos<PD.length){w.setText(fmt(Math.max(PD[pos][0],PD[pos][1])));h.setText(fmt(Math.min(PD[pos][0],PD[pos][1])));w.setEnabled(false);h.setEnabled(false);}else{w.setEnabled(true);h.setEnabled(true);}}});
        double[] dims=metaDims(meta);int pi=presetIndex(dims[0],dims[1]);
        if(pi>=0)paper.setSelection(pi);else if(dims[0]>0&&dims[1]>0){paper.setSelection(PAPERS.length-1);w.setText(fmt(Math.max(dims[0],dims[1])));h.setText(fmt(Math.min(dims[0],dims[1])));}
        else paper.setSelection(2);
    }

    static final class Dims{double W,H;Dims(double W,double H){this.W=W;this.H=H;}}
    static final class Calc{double beta,col,pw,ph;String crop;}

    Dims readDims(){double aw=Double.parseDouble(w.getText().toString().replace(',','.'))*10,ah=Double.parseDouble(h.getText().toString().replace(',','.'))*10;return new Dims(Math.max(aw,ah),Math.min(aw,ah));}
    Calc calc(boolean a,double W,double H,int fidx){double nw=a?36:56,nh=a?24:56,beta=fidx==1?W/nw:fidx==2?H/nh:Math.min(W/nw,H/nh),col=b2c(beta,a?C50:C80);if(Double.isNaN(col))return null;Calc c=new Calc();c.beta=beta;c.col=col;c.pw=beta*nw/10;c.ph=beta*nh/10;c.crop=(c.pw>W/10+.001||c.ph>H/10+.001)?"SI":"NO";return c;}

    String buildMeta(boolean a,double W,double H,int fidx,double beta,double col,double pw,double ph,String crop,long sourceId,String from){
        String base=String.format(Locale.US,"neg=%s|lens=%d|paper=%.1fx%.1f|w=%.1f|h=%.1f|orientation=LANDSCAPE|fill=%d|beta=%.8f|col=%.8f|proj=%.2fx%.2f|crop=%s",a?"35":"66",a?50:80,W/10,H/10,W/10,H/10,fidx,beta,col,pw,ph,crop);
        if(sourceId>0)base+="|sourceId="+sourceId;if(from!=null&&!from.isEmpty())base+="|derivedFrom="+from.replace(" × ","x").replace(',','.');return base;
    }

    String resultText(Calc c){return String.format(Locale.ITALY,"β %.3f\nColonna teorica %.2f\nImmagine proiettata %.1f × %.1f cm\nCrop: %s",c.beta,c.col,c.pw,c.ph,cropLabel(c.crop));}
    String originSummary(String meta,boolean a){return paperDisplay(meta)+" · "+(a?"35 mm / 50 mm":"6×6 / 80 mm")+String.format(Locale.ITALY,"\nβ %.3f · colonna %.2f",num(meta,"beta"),num(meta,"col"));}

    String paperDisplay(String meta){double[] d=metaDims(meta);return paperDisplay(d[0]*10,d[1]*10);}
    String paperDisplay(double W,double H){if(W<=0||H<=0)return "formato non registrato";double wcm=W/10,hcm=H/10;return String.format(Locale.ITALY,"%.1f×%.1f",Math.min(wcm,hcm),Math.max(wcm,hcm));}
    double[] metaDims(String meta){double ww=num(meta,"w"),hh=num(meta,"h");if(!Double.isNaN(ww)&&!Double.isNaN(hh))return new double[]{ww,hh};String pp=val(meta,"paper");try{String[] x=pp.split("x");if(x.length==2)return new double[]{Double.parseDouble(x[0]),Double.parseDouble(x[1])};}catch(Exception ignored){}return new double[]{-1,-1};}
    int presetIndex(double a,double b){if(a<=0||b<=0)return -1;double hi=Math.max(a,b),lo=Math.min(a,b);for(int i=0;i<PD.length;i++){double ph=Math.max(PD[i][0],PD[i][1]),pl=Math.min(PD[i][0],PD[i][1]);if(Math.abs(ph-hi)<.06&&Math.abs(pl-lo)<.06)return i;}return -1;}

    void begin(String title,String subtitle){ScrollView sc=new ScrollView(this);sc.setFillViewport(true);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(14),dp(18),dp(30));root.setBackgroundColor(BG);sc.addView(root,new ScrollView.LayoutParams(-1,-2));Button back=button("←  INDIETRO",BUTTON);back.setOnClickListener(v->finish());root.addView(back,lp(-1,dp(46)));TextView h=label(title,24,TEXT,true);h.setGravity(Gravity.CENTER);root.addView(h,margin(lp(-1,-2),0,dp(10),0,dp(3)));TextView sub=label(subtitle,12,MUTED,false);sub.setGravity(Gravity.CENTER);root.addView(sub,margin(lp(-1,-2),0,0,0,dp(16)));setContentView(sc);}
    LinearLayout section(String title,String body){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(0,dp(8),0,dp(8));box.addView(label(title,12,MUTED,true));TextView v=label(body,15,TEXT,false);v.setLineSpacing(0,1.12f);v.setPadding(0,dp(5),0,0);box.addView(v);return box;}
    void info(String x){TextView v=label(x,14,Color.rgb(230,196,150),false);v.setGravity(Gravity.CENTER);root.addView(v,margin(lp(-1,-2),0,dp(18),0,0));}
    void infoInto(LinearLayout parent,String x){TextView v=label(x,14,Color.rgb(230,196,150),false);v.setGravity(Gravity.CENTER);parent.addView(v,margin(lp(-1,-2),0,dp(10),0,0));}
    void clearResult(){pending=null;if(resultBox!=null)resultBox.removeAllViews();}

    EditText input(String hint){EditText e=new EditText(this);e.setHint(hint);e.setTextColor(TEXT);e.setHintTextColor(MUTED);e.setTextSize(15);e.setInputType(2|8192);e.setPadding(dp(13),0,dp(13),0);e.setBackground(bg(PANEL,10,BORDER,1));return e;}
    Spinner spinner(String[] items){Spinner sp=new Spinner(this);ArrayAdapter<String>a=new ArrayAdapter<String>(this,android.R.layout.simple_spinner_item,items){@Override public View getView(int pos,View cv,ViewGroup parent){TextView t=(TextView)super.getView(pos,cv,parent);t.setTextColor(TEXT);t.setTextSize(15);t.setPadding(dp(10),dp(9),dp(10),dp(9));return t;}@Override public View getDropDownView(int pos,View cv,ViewGroup parent){TextView t=(TextView)super.getDropDownView(pos,cv,parent);t.setTextColor(Color.WHITE);t.setBackgroundColor(Color.rgb(38,38,38));t.setPadding(dp(12),dp(12),dp(12),dp(12));return t;}};a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);sp.setAdapter(a);sp.setBackground(bg(PANEL,10,BORDER,1));return sp;}
    Button button(String text,int color){Button b=new Button(this);b.setText(text);b.setAllCaps(false);b.setTextColor(TEXT);b.setTextSize(15);b.setTypeface(Typeface.DEFAULT_BOLD);b.setBackground(bg(color,10,BORDER,1));return b;}
    TextView label(String x,float z,int color,boolean bold){TextView v=new TextView(this);v.setText(x);v.setTextSize(z);v.setTextColor(color);v.setTypeface(Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL);return v;}
    GradientDrawable bg(int c,int r,int stroke,int sw){GradientDrawable g=new GradientDrawable();g.setColor(c);g.setCornerRadius(dp(r));if(sw>0)g.setStroke(dp(sw),stroke);return g;}
    LinearLayout.LayoutParams lp(int w,int h){return new LinearLayout.LayoutParams(w,h);}LinearLayout.LayoutParams margin(LinearLayout.LayoutParams x,int l,int t,int r,int b){x.setMargins(dp(l),dp(t),dp(r),dp(b));return x;}int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}

    static double b2c(double b,double[][]t){if(b<t[0][0]||b>t[t.length-1][0])return Double.NaN;for(int i=0;i<t.length-1;i++)if(b>=t[i][0]&&b<=t[i+1][0]){double q=(b-t[i][0])/(t[i+1][0]-t[i][0]);return t[i][1]+q*(t[i+1][1]-t[i][1]);}return t[t.length-1][1];}
    static int snap(double ms){return(int)Math.round(ms/500.0)*500;}
    static String val(String m,String k){if(m==null)return"";for(String x:m.split("\\|"))if(x.startsWith(k+"="))return x.substring(k.length()+1);return"";}
    static double num(String m,String k){try{return Double.parseDouble(val(m,k));}catch(Exception e){return Double.NaN;}}
    static int intVal(String m,String k,int fallback){try{return Integer.parseInt(val(m,k));}catch(Exception e){return fallback;}}
    static String fmt(double x){return String.format(Locale.ITALY,"%.1f",x);}
    static String cropLabel(String c){return "SI".equals(c)?"SÌ":"NO";}
}
'''
enlargement.write_text(java, encoding='utf-8')

# -----------------------------------------------------------------------------
# REGRESSION GUARDS
# -----------------------------------------------------------------------------
ms = main.read_text(encoding='utf-8')
es = enlargement.read_text(encoding='utf-8')
for marker in [
    'pendingEnlargementMeta', 'pendingEnlargementAt', 'originLogId',
    'RIDIMENSIONA STAMPA', 'enlargementLogSummary',
    '.putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)',
    'refreshTestBaseFilterUi();'
]:
    if marker not in ms:
        raise SystemExit('v0.2.0 enlargement/log MainActivity guard failed: ' + marker)

# The session list must not contain its old per-mini-card resize control.
sg = ms[ms.index('    private void showLogGroup(final LogGroup group) {'):]
sg = sg[:sg.index('\n    private ', 20)]
if 'Button resizeEntry = compactButton("RIDIMENSIONA STAMPA")' in sg:
    raise SystemExit('v0.2.0 enlargement/log: resize still present in session mini-cards')

for marker in [
    'FORMATO ORIGINALE DELLA STAMPA', 'MODALITÀ ORIGINALE', 'SALVA E CONTINUA',
    'ORIENTAMENTO · ORIZZONTALE', 'RISULTATO', 'COMPENSAZIONE',
    'Button create=button("CREA"', 'LogStore.save(this,originEntry)',
    'LogStore.save(this,d)', 'Derivata da ', 'originLogId',
    'Math.pow((c.beta+1)/(b1+1),2)', 'Math.round(ms/500.0)*500'
]:
    if marker not in es:
        raise SystemExit('v0.2.0 enlargement/log EnlargementActivity guard failed: ' + marker)
for forbidden in ['new Dialog(', 'confirmDerived(', 'INVERTI LARGHEZZA']:
    if forbidden in es:
        raise SystemExit('v0.2.0 enlargement/log forbidden old UI remains: ' + forbidden)

print('Darkroom v0.2.0 enlargement/log flow patch ready')
