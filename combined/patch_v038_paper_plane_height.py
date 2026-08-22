#!/usr/bin/env python3
from pathlib import Path

root = Path("combined/src/main/java/it/darkroom/timer")
main = root / "MainActivity.java"
enlargement = root / "EnlargementActivity.java"

for p in (main, enlargement):
    if not p.exists():
        raise SystemExit("v0.3.8 paper-plane: generated source missing: " + str(p))

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit("v0.3.8 paper-plane marker missing: " + label)
    return text.replace(old, new, 1)

def replace_between(text, start, end, replacement, label):
    a = text.find(start)
    if a < 0:
        raise SystemExit("v0.3.8 paper-plane start marker missing: " + label)
    b = text.find(end, a + len(start))
    if b < 0:
        raise SystemExit("v0.3.8 paper-plane end marker missing: " + label)
    return text[:a] + replacement + text[b:]

# -----------------------------------------------------------------------------
# MAIN SETTINGS — persistent enlarger paper-plane height.
# -----------------------------------------------------------------------------
s = main.read_text(encoding="utf-8")
main_marker = '''        hardwareGroup.addView(details, lp(-1,-2));
        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");'''
main_insert = '''        hardwareGroup.addView(details, lp(-1,-2));

        TextView paperPlaneTitle = text("ALTEZZA PIANO CARTA (spessore marginatore)", 12, TEXT_PRIMARY, true);
        paperPlaneTitle.setPadding(dp(4), dp(10), dp(4), dp(4));
        hardwareGroup.addView(paperPlaneTitle, lp(-1,-2));
        final android.widget.EditText paperPlaneHeight = new android.widget.EditText(this);
        paperPlaneHeight.setSingleLine(true);
        paperPlaneHeight.setTextColor(TEXT_PRIMARY);
        paperPlaneHeight.setHintTextColor(MUTED);
        paperPlaneHeight.setTextSize(15);
        paperPlaneHeight.setPadding(dp(12), 0, dp(12), 0);
        paperPlaneHeight.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        paperPlaneHeight.setBackground(roundRect(darkroomMode ? Color.rgb(26,0,0) : Color.rgb(34,36,38), 8, 1, BORDER));
        float savedPaperPlaneMm;
        try { savedPaperPlaneMm = getSharedPreferences("ui", MODE_PRIVATE).getFloat("enlargementPaperPlaneHeightMm", 0f); }
        catch (Exception ignored) { savedPaperPlaneMm = 0f; }
        savedPaperPlaneMm = Math.max(0f, Math.min(50f, savedPaperPlaneMm));
        paperPlaneHeight.setText(String.format(java.util.Locale.ITALY, "%.1f", savedPaperPlaneMm));
        hardwareGroup.addView(paperPlaneHeight, lp(-1,dp(48)));
        TextView paperPlaneNote = text("0–50 mm · 0 mm = piano originale · valore liberamente modificabile (precisione almeno 0,5 mm).", 11, MUTED, false);
        paperPlaneNote.setPadding(dp(4), dp(4), dp(4), dp(6));
        hardwareGroup.addView(paperPlaneNote, lp(-1,-2));
        paperPlaneHeight.addTextChangedListener(new android.text.TextWatcher() {
            public void beforeTextChanged(CharSequence x, int start, int count, int after) {}
            public void onTextChanged(CharSequence x, int start, int before, int count) {}
            public void afterTextChanged(android.text.Editable x) {
                try {
                    double mm = Double.parseDouble(x.toString().trim().replace(',', '.'));
                    if (mm >= 0.0 && mm <= 50.0)
                        getSharedPreferences("ui", MODE_PRIVATE).edit().putFloat("enlargementPaperPlaneHeightMm", (float) mm).apply();
                } catch (Exception ignored) {}
            }
        });
        paperPlaneHeight.setOnFocusChangeListener((view, hasFocus) -> {
            if (hasFocus) return;
            try {
                double mm = Double.parseDouble(paperPlaneHeight.getText().toString().trim().replace(',', '.'));
                if (mm < 0.0 || mm > 50.0) throw new IllegalArgumentException();
                getSharedPreferences("ui", MODE_PRIVATE).edit().putFloat("enlargementPaperPlaneHeightMm", (float) mm).apply();
                paperPlaneHeight.setText(String.format(java.util.Locale.ITALY, "%.1f", mm));
            } catch (Exception bad) {
                Toast.makeText(this, "Altezza piano carta: inserisci un valore tra 0 e 50 mm", Toast.LENGTH_LONG).show();
                float mm = getSharedPreferences("ui", MODE_PRIVATE).getFloat("enlargementPaperPlaneHeightMm", 0f);
                paperPlaneHeight.setText(String.format(java.util.Locale.ITALY, "%.1f", Math.max(0f, Math.min(50f, mm))));
            }
        });

        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");'''
s = replace_once(s, main_marker, main_insert, "MainActivity hardware enlarger settings")
main.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# ENLARGEMENT ACTIVITY — keep calibration untouched; apply paper-plane offset.
# -----------------------------------------------------------------------------
s = enlargement.read_text(encoding="utf-8")

s = replace_once(
    s,
    '''    Spinner paper, fill, neg;
    EditText w,h;
    LinearLayout resultBox;''',
    '''    Spinner paper, fill, neg;
    EditText w,h,paperPlane;
    LinearLayout resultBox;
    boolean paperPlaneBinding=false;
    boolean hasCalculated=false;''',
    "Enlargement fields",
)

s = replace_once(
    s,
    '''        double W,H,b1,b2,c1,c2,factor,stops,pw,ph;''',
    '''        double W,H,b1,b2,c1,c2,effective1,effective2,factor,stops,pw,ph,sourcePlaneMm,targetPlaneMm;''',
    "Pending physical/effective fields",
)

s = replace_once(
    s,
    '''        if(resize){
            Boolean a=sourceNegative();''',
    '''        addPaperPlaneHeightControl();
        if(resize){
            Boolean a=sourceNegative();''',
    "show paper-plane control in setup/resize",
)

s = replace_once(
    s,
    '''        Boolean a=negativeFromEntry(originEntry);
        if(a==null){''',
    '''        root.addView(section("RICETTA ORIGINE", "Altezza piano carta: 0,0 mm · compatibilità automatica con le vecchie ricette."));
        addPaperPlaneHeightControl();
        Boolean a=negativeFromEntry(originEntry);
        if(a==null){''',
    "legacy recipe default zero and current control",
)

s = replace_once(
    s,
    '''            String meta=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.pw,c.ph,c.crop,0L,"");''',
    '''            String meta=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.col,0.0,c.pw,c.ph,c.crop,0L,"");''',
    "legacy metadata defaults to zero plane",
)

setup_method = r'''    void calculateSetup(){
        try{
            Double plane=readPaperPlaneHeightMm();
            clearResult();
            if(plane==null){infoInto(resultBox,"Altezza piano carta: usa un valore tra 0 e 50 mm.");return;}
            hasCalculated=true;
            boolean a=neg.getSelectedItemPosition()==0;Dims d=readDims();Calc c=calc(a,d.W,d.H,fill.getSelectedItemPosition());
            if(c==null){infoInto(resultBox,"FORMATO FUORI DALL’INTERVALLO CALIBRATO");return;}
            double physical=physicalCol(c.col,plane);
            String meta=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,physical,c.col,plane,c.pw,c.ph,c.crop,0L,"");
            p.edit().putString("enlargementMeta",meta).putString("enlargementLastLog","IMPOSTA INGRANDIMENTO · "+meta)
                    .putInt("enlargementUiNeg",neg.getSelectedItemPosition()).putInt("enlargementUiFill",fill.getSelectedItemPosition()).apply();
            resultBox.addView(section("RISULTATO",resultText(c,plane)));
            TextView ok=label("Registrato nella ricetta corrente.",13,GREEN,true);ok.setGravity(Gravity.CENTER);resultBox.addView(ok,margin(lp(-1,-2),0,dp(8),0,0));Button close=button("CHIUDI",BUTTON);close.setOnClickListener(v->finish());resultBox.addView(close,margin(lp(-1,dp(50)),0,dp(12),0,dp(4)));
        }catch(Exception e){clearResult();infoInto(resultBox,"Inserisci dimensioni carta valide.");}
    }

'''
s = replace_between(s, "    void calculateSetup(){", "    void calculateResize(boolean a){", setup_method, "calculateSetup")

resize_method = r'''    void calculateResize(boolean a){
        try{
            Double plane=readPaperPlaneHeightMm();
            clearResult();
            if(plane==null){infoInto(resultBox,"Altezza piano carta: usa un valore tra 0 e 50 mm.");return;}
            hasCalculated=true;
            Dims d=readDims();Calc c=calc(a,d.W,d.H,fill.getSelectedItemPosition());
            if(c==null){infoInto(resultBox,"FORMATO FUORI DALL’INTERVALLO CALIBRATO");return;}
            String old=sourceMeta();double b1=num(old,"beta"),c1=num(old,"col");
            if(Double.isNaN(b1)||Double.isNaN(c1)){if(originEntry!=null){renderLegacyOrigin();return;}infoInto(resultBox,"Mancano i dati dell’ingrandimento iniziale.");return;}
            double sourcePlane=metaPlaneMm(old),effective1=metaEffectiveCol(old),c2=physicalCol(c.col,plane);
            double factor=Math.pow((c.beta+1)/(b1+1),2); // validated exposure formula: unchanged
            double stops=Math.log(factor)/Math.log(2);
            int oldBase=sourceBase(),newBase=snap(oldBase*factor); // SONOFF final step remains 0.5 s
            ExposureRecipe oldR=sourceRecipeForResize(oldBase);
            ExposureRecipe newR=scaleRecipe(oldR,oldBase,factor);
            PrintSequence oldQ=PrintSequence.decode(sourceSequence());
            PrintSequence newQ=scaleSequence(oldQ,factor);
            String from=paperDisplay(old);String to=paperDisplay(d.W,d.H);
            String note="Derivata da "+from+" → "+to;
            String nm=buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c2,c.col,plane,c.pw,c.ph,c.crop,originLogId,from);
            Pending x=new Pending();x.is35=a;x.W=d.W;x.H=d.H;x.b1=b1;x.b2=c.beta;x.c1=c1;x.c2=c2;x.effective1=effective1;x.effective2=c.col;x.sourcePlaneMm=sourcePlane;x.targetPlaneMm=plane;x.factor=factor;x.stops=stops;x.pw=c.pw;x.ph=c.ph;x.crop=c.crop;x.oldMeta=old;x.newMeta=nm;x.note=note;x.oldBase=oldBase;x.newBase=newBase;x.oldRecipe=oldR;x.newRecipe=newR;x.oldSequence=oldQ;x.newSequence=newQ;pending=x;
            showPending(x);
        }catch(Exception e){clearResult();infoInto(resultBox,"Inserisci dimensioni carta valide.");}
    }

'''
s = replace_between(s, "    void calculateResize(boolean a){", "    void showPending(Pending x){", resize_method, "calculateResize")

pending_method = r'''    void showPending(Pending x){
        clearResult();
        pending=x;
        resultBox.addView(section("RISULTATO",String.format(Locale.ITALY,"β finale %.3f\nPiano carta %+.1f mm\nDistanza effettiva obiettivo-carta %.2f cm\nAltezza fisica dal piano originale %.2f cm\nImmagine proiettata %.1f × %.1f cm\nCrop: %s",x.b2,x.targetPlaneMm,x.effective2,x.c2,x.pw,x.ph,cropLabel(x.crop))));
        StringBuilder comp=new StringBuilder();
        comp.append(String.format(Locale.ITALY,"β %.3f → %.3f\nPiano carta %+.1f → %+.1f mm\nDistanza effettiva obiettivo-carta %.2f → %.2f cm\nAltezza dal piano originale %.2f → %.2f cm\nFattore ×%.2f\nVariazione %+.2f stop\nTempo base %.1f s → %.1f s",x.b1,x.b2,x.sourcePlaneMm,x.targetPlaneMm,x.effective1,x.effective2,x.c1,x.c2,x.factor,x.stops,x.oldBase/1000.0,x.newBase/1000.0));
        String timed=timedChanges(x);
        if(!timed.isEmpty())comp.append('\n').append(timed);
        resultBox.addView(section("COMPENSAZIONE",comp.toString()));
        Button create=button("CREA",GREEN);create.setTextColor(Color.BLACK);create.setOnClickListener(v->{v.setEnabled(false);createDerived(x);});
        Button cancel=button("ANNULLA",BUTTON);cancel.setOnClickListener(v->{pending=null;clearResult();});
        resultBox.addView(create,margin(lp(-1,dp(54)),0,dp(12),0,0));
        resultBox.addView(cancel,margin(lp(-1,dp(48)),0,dp(8),0,dp(14)));
    }

'''
s = replace_between(s, "    void showPending(Pending x){", "    String timedChanges(Pending x){", pending_method, "showPending")

paper_helpers = r'''    static final String PREF_PAPER_PLANE_MM="enlargementPaperPlaneHeightMm";

    void addPaperPlaneHeightControl(){
        root.addView(label("IMPOSTAZIONI INGRANDITORE",12,MUTED,true));
        root.addView(label("ALTEZZA PIANO CARTA (spessore marginatore)",13,TEXT,true),margin(lp(-1,-2),0,dp(5),0,dp(4)));
        paperPlane=input("Altezza piano carta mm");
        double saved=storedPaperPlaneHeightMm();
        paperPlaneBinding=true;paperPlane.setText(fmtPlane(saved));paperPlaneBinding=false;
        root.addView(paperPlane,lp(-1,dp(50)));
        TextView note=label("0–50 mm · 0 mm = piano originale · es. +10 mm per un marginatore spesso 10 mm.",11,MUTED,false);
        root.addView(note,margin(lp(-1,-2),0,dp(4),0,dp(5)));
        LinearLayout step=new LinearLayout(this);step.setOrientation(LinearLayout.HORIZONTAL);
        Button minus=button("− 0,5 mm",BUTTON),plus=button("+ 0,5 mm",BUTTON);
        minus.setOnClickListener(v->stepPaperPlane(-0.5));plus.setOnClickListener(v->stepPaperPlane(0.5));
        step.addView(minus,new LinearLayout.LayoutParams(0,dp(44),1f));step.addView(plus,new LinearLayout.LayoutParams(0,dp(44),1f));
        root.addView(step,margin(lp(-1,-2),0,0,0,dp(12)));
        paperPlane.addTextChangedListener(new android.text.TextWatcher(){
            public void beforeTextChanged(CharSequence x,int start,int count,int after){}
            public void onTextChanged(CharSequence x,int start,int before,int count){}
            public void afterTextChanged(android.text.Editable x){
                if(paperPlaneBinding)return;
                Double mm=parsePaperPlane(x.toString());
                if(mm==null)return;
                p.edit().putFloat(PREF_PAPER_PLANE_MM,mm.floatValue()).apply();
                if(hasCalculated){
                    if("resize".equals(mode)){Boolean a=sourceNegative();if(a!=null)calculateResize(a);}
                    else calculateSetup();
                }
            }
        });
    }

    void stepPaperPlane(double delta){
        Double current=readPaperPlaneHeightMm();double mm=current==null?storedPaperPlaneHeightMm():current;
        mm=Math.max(0.0,Math.min(50.0,Math.round((mm+delta)*2.0)/2.0));
        paperPlane.setText(fmtPlane(mm));paperPlane.setSelection(paperPlane.getText().length());
    }

    double storedPaperPlaneHeightMm(){
        try{return Math.max(0.0,Math.min(50.0,p.getFloat(PREF_PAPER_PLANE_MM,0f)));}catch(Exception ignored){return 0.0;}
    }

    Double readPaperPlaneHeightMm(){
        if(paperPlane==null)return storedPaperPlaneHeightMm();
        return parsePaperPlane(paperPlane.getText().toString());
    }

    Double parsePaperPlane(String raw){
        try{
            double mm=Double.parseDouble(raw.trim().replace(',','.'));
            if(mm<0.0||mm>50.0)return null;
            return mm;
        }catch(Exception ignored){return null;}
    }

    static String fmtPlane(double mm){return String.format(Locale.ITALY,"%.1f",mm);}
    static double physicalCol(double effectiveColCm,double paperPlaneMm){return effectiveColCm+paperPlaneMm/10.0;}
    static double metaPlaneMm(String meta){double mm=num(meta,"paperPlaneMm");return Double.isNaN(mm)||mm<0.0||mm>50.0?0.0:mm;}
    static double metaEffectiveCol(String meta){double e=num(meta,"effectiveCol");if(!Double.isNaN(e))return e;double c=num(meta,"col");return Double.isNaN(c)?Double.NaN:c-metaPlaneMm(meta)/10.0;}

'''
s = replace_once(s, "    void addPaperFields(String meta){", paper_helpers + "    void addPaperFields(String meta){", "paper-plane helpers")

build_old_start = "    String buildMeta(boolean a,double W,double H,int fidx,double beta,double col,double pw,double ph,String crop,long sourceId,String from){"
build_new = r'''    String buildMeta(boolean a,double W,double H,int fidx,double beta,double col,double effectiveCol,double planeMm,double pw,double ph,String crop,long sourceId,String from){
        String base=String.format(Locale.US,"neg=%s|lens=%d|paper=%.1fx%.1f|w=%.1f|h=%.1f|orientation=LANDSCAPE|fill=%d|beta=%.8f|col=%.8f|effectiveCol=%.8f|paperPlaneMm=%.1f|proj=%.2fx%.2f|crop=%s",a?"35":"66",a?50:80,W/10,H/10,W/10,H/10,fidx,beta,col,effectiveCol,planeMm,pw,ph,crop);
        if(sourceId>0)base+="|sourceId="+sourceId;if(from!=null&&!from.isEmpty())base+="|derivedFrom="+from.replace(" × ","x").replace(',','.');return base;
    }

    String resultText(Calc c,double planeMm){double physical=physicalCol(c.col,planeMm);return String.format(Locale.ITALY,"β %.3f\nPiano carta %+.1f mm\nDistanza effettiva obiettivo-carta %.2f cm\nAltezza fisica dal piano originale %.2f cm\nImmagine proiettata %.1f × %.1f cm\nCrop: %s",c.beta,planeMm,c.col,physical,c.pw,c.ph,cropLabel(c.crop));}
    String originSummary(String meta,boolean a){double plane=metaPlaneMm(meta),effective=metaEffectiveCol(meta),physical=num(meta,"col");return paperDisplay(meta)+" · "+(a?"35 mm / 50 mm":"6×6 / 80 mm")+String.format(Locale.ITALY,"\nβ %.3f · piano carta %+.1f mm\nDistanza effettiva %.2f cm · altezza dal piano originale %.2f cm",num(meta,"beta"),plane,effective,physical);}

'''
s = replace_between(s, build_old_start, "    String paperDisplay(String meta){", build_new, "metadata/result/origin helpers")

for marker in [
    'PREF_PAPER_PLANE_MM="enlargementPaperPlaneHeightMm"',
    'ALTEZZA PIANO CARTA (spessore marginatore)',
    'paperPlaneMm=%.1f',
    'effectiveCol=%.8f',
    'physicalCol(c.col,plane)',
    'Math.pow((c.beta+1)/(b1+1),2)',
    'Math.round(ms/500.0)*500',
    'metaPlaneMm(old)',
    'buildMeta(a,d.W,d.H,fill.getSelectedItemPosition(),c.beta,c.col,c.col,0.0',
]:
    if marker not in s:
        raise SystemExit("v0.3.8 paper-plane enlargement guard failed: " + marker)

if 'paperPlaneMm=10' in s or 'enlargementPaperPlaneHeightMm",10' in s:
    raise SystemExit("v0.3.8 paper-plane height must not be hardcoded to 10 mm")

enlargement.write_text(s, encoding="utf-8")

ms = main.read_text(encoding="utf-8")
es = enlargement.read_text(encoding="utf-8")
for marker in [
    'ALTEZZA PIANO CARTA (spessore marginatore)',
    'enlargementPaperPlaneHeightMm',
    '0–50 mm',
]:
    if marker not in ms:
        raise SystemExit("v0.3.8 MainActivity settings guard failed: " + marker)
    if marker not in es:
        raise SystemExit("v0.3.8 EnlargementActivity guard failed: " + marker)

print("Darkroom v0.3.8 paper-plane height patch ready")
