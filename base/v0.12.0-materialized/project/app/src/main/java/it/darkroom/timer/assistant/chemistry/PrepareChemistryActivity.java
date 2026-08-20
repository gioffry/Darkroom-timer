package it.darkroom.timer.assistant.chemistry;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import it.darkroom.timer.assistant.development.DevelopmentCatalog;

/** Funzione autonoma PREPARA CHIMICA — Release 3/9. */
public final class PrepareChemistryActivity extends Activity {
    private int primary, muted, border, card, accent;
    private AutoCompleteTextView developerField, dilutionField;
    private EditText volumeField, rollsField;
    private Button format35, format120;
    private LinearLayout resultBox;
    private String selectedFormat = "120";

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode = getSharedPreferences("ui", MODE_PRIVATE).getBoolean("darkroomMode", false);
        configurePalette(darkroomMode);
        buildUi();
    }

    private void configurePalette(boolean darkroomMode) {
        if (darkroomMode) {
            primary=Color.rgb(255,42,42); muted=Color.rgb(145,34,34); border=Color.rgb(112,20,20);
            card=Color.rgb(18,0,0); accent=Color.rgb(255,42,42);
        } else {
            primary=Color.rgb(238,240,242); muted=Color.rgb(145,151,158); border=Color.rgb(60,64,70);
            card=Color.rgb(24,26,30); accent=Color.rgb(197,54,58);
        }
    }

    private void buildUi() {
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18),dp(16),dp(18),dp(28));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));

        TextView eyebrow=text("DARKROOM ASSISTANT · 3/9",12,accent,true); eyebrow.setGravity(Gravity.CENTER); root.addView(eyebrow);
        TextView title=text("PREPARA CHIMICA",24,primary,true); title.setGravity(Gravity.CENTER); root.addView(title);
        TextView processor=text("JOBO CPE2  ·  ROTAZIONE CONTINUA",13,accent,true); processor.setGravity(Gravity.CENTER);
        processor.setPadding(0,dp(5),0,dp(16)); root.addView(processor);

        label(root,"RIVELATORE / PRODOTTO");
        developerField=autoField("Seleziona prodotto"); developerField.setAdapter(adapter(DevelopmentCatalog.developerNames()));
        developerField.setOnClickListener(v -> developerField.showDropDown());
        developerField.setOnFocusChangeListener((v,has) -> { if(has) developerField.showDropDown(); });
        developerField.setOnItemClickListener((p,v,pos,id) -> refreshDilutions());
        root.addView(developerField,lp(-1,dp(52)));

        label(root,"DILUIZIONE");
        dilutionField=autoField("es. 1+3, stock, B");
        dilutionField.setOnClickListener(v -> dilutionField.showDropDown());
        dilutionField.setOnFocusChangeListener((v,has) -> { if(has) dilutionField.showDropDown(); });
        root.addView(dilutionField,lp(-1,dp(52)));

        label(root,"VOLUME TOTALE DA PREPARARE");
        volumeField=editField("es. 340 ml",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        volumeField.setText("340"); root.addView(volumeField,lp(-1,dp(52)));

        TextView optional=text("VERIFICA CAPACITÀ · opzionale",12,muted,true); optional.setPadding(dp(2),dp(16),0,dp(4)); root.addView(optional);
        LinearLayout formats=new LinearLayout(this); formats.setOrientation(LinearLayout.HORIZONTAL);
        format35=choice("35 mm"); format120=choice("120");
        format35.setOnClickListener(v -> selectFormat("35 mm")); format120.setOnClickListener(v -> selectFormat("120"));
        formats.addView(format35,margin(lp(0,dp(46),1f),0,0,5,0));
        formats.addView(format120,margin(lp(0,dp(46),1f),5,0,0,0)); root.addView(formats);
        selectFormat("120");

        label(root,"NUMERO RULLI (opzionale)");
        rollsField=editField("es. 1",InputType.TYPE_CLASS_NUMBER); root.addView(rollsField,lp(-1,dp(52)));

        Button calculate=bigButton("CALCOLA PREPARAZIONE"); calculate.setOnClickListener(v -> calculate());
        root.addView(calculate,margin(lp(-1,dp(60)),0,14,0,0));

        resultBox=new LinearLayout(this); resultBox.setOrientation(LinearLayout.VERTICAL);
        resultBox.setPadding(dp(14),dp(12),dp(14),dp(12)); resultBox.setBackground(roundRect(card,10,1,border));
        resultBox.setVisibility(View.GONE); root.addView(resultBox,lp(-1,-2));

        TextView note=text("Diluizione matematica e capacità chimica sono controlli separati. Se la fonte non dichiara la capacità, l’app non la presume.",11,muted,false);
        note.setGravity(Gravity.CENTER); note.setPadding(dp(5),dp(12),dp(5),dp(14)); root.addView(note);
        Button back=bigButton("←  ASSISTANT"); back.setOnClickListener(v -> finish()); root.addView(back,lp(-1,dp(52)));
        setContentView(scroll);
    }

    private void refreshDilutions() {
        String[] values=DevelopmentCatalog.developerDilutions(developerField.getText().toString());
        dilutionField.setAdapter(adapter(values));
        if(values.length>0) dilutionField.setText(values[0],false); else dilutionField.setText("");
    }

    private void calculate() {
        double volume=parseDouble(volumeField.getText().toString());
        if(Double.isNaN(volume)||volume<=0){ toast("Inserisci un volume totale valido in ml."); return; }
        int rolls=parseOptionalInt(rollsField.getText().toString());
        if(rolls<0){ toast("Numero rulli non valido."); return; }
        ChemistryCalculator.Result r=ChemistryCalculator.calculate(developerField.getText().toString(),
                dilutionField.getText().toString(),volume,selectedFormat,rolls);
        if(!r.inputValid){ toast(r.error); return; }
        render(r);
    }

    private void render(ChemistryCalculator.Result r) {
        resultBox.removeAllViews(); resultBox.setVisibility(View.VISIBLE);
        resultBox.addView(text("PREPARA",12,accent,true));
        TextView recipe=text(developerField.getText().toString()+"  ·  "+dilutionField.getText().toString(),17,primary,true);
        recipe.setPadding(0,dp(4),0,dp(8)); resultBox.addView(recipe);
        if(r.dilutionKnown) {
            resultBox.addView(text(ChemistryCalculator.formatMl(r.productMl)+" ml prodotto / stock",17,primary,true));
            resultBox.addView(text(ChemistryCalculator.formatMl(r.waterMl)+" ml acqua",17,primary,true));
            resultBox.addView(text(ChemistryCalculator.formatMl(r.totalMl)+" ml totale",17,primary,true));
        } else {
            resultBox.addView(text(r.dilutionMessage,14,accent,true));
        }
        TextView cap=text(r.capacityMessage,13,
                ChemistryCalculator.CAPACITY_INSUFFICIENT.equals(r.capacityState)?accent:muted,
                ChemistryCalculator.CAPACITY_VERIFIED.equals(r.capacityState));
        cap.setPadding(0,dp(10),0,0); resultBox.addView(cap);
        if(!r.capacitySource.isEmpty()) {
            TextView src=text("Fonte capacità: "+r.capacitySource,11,muted,false); src.setPadding(0,dp(5),0,0); resultBox.addView(src);
        }
        TextView cpe=text(r.cpe2Message,12,r.cpe2Compatible?muted:accent,!r.cpe2Compatible);
        cpe.setPadding(0,dp(8),0,0); resultBox.addView(cpe);
        TextView cpeSource=text("Fonte limite CPE2: "+ChemistryCalculator.CPE2_LIMIT_SOURCE,10,muted,false);
        cpeSource.setPadding(0,dp(4),0,0); resultBox.addView(cpeSource);
        if(r.canAdoptMinimum) {
            Button adopt=bigButton("USA VOLUME MINIMO · "+ChemistryCalculator.formatMl(r.minimumVolumeMl)+" ml");
            adopt.setOnClickListener(v -> { volumeField.setText(ChemistryCalculator.formatMl(r.minimumVolumeMl)); calculate(); });
            resultBox.addView(adopt,margin(lp(-1,dp(52)),0,10,0,0));
        }
    }

    private void selectFormat(String format) {
        selectedFormat=format;
        if(format35==null||format120==null)return;
        format35.setBackground(roundRect(card,9,1,"35 mm".equals(format)?accent:border));
        format120.setBackground(roundRect(card,9,1,"120".equals(format)?accent:border));
        format35.setTextColor("35 mm".equals(format)?accent:primary);
        format120.setTextColor("120".equals(format)?accent:primary);
    }

    private AutoCompleteTextView autoField(String hint){ AutoCompleteTextView v=new AutoCompleteTextView(this); v.setHint(hint); v.setThreshold(0); v.setSingleLine(true); v.setTextSize(16); v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0); v.setBackground(roundRect(card,9,1,border)); return v; }
    private EditText editField(String hint,int type){ EditText v=new EditText(this); v.setHint(hint); v.setSingleLine(true); v.setInputType(type); v.setTextSize(16); v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0); v.setBackground(roundRect(card,9,1,border)); return v; }
    private ArrayAdapter<String> adapter(String[] values){ return new ArrayAdapter<String>(this,android.R.layout.simple_dropdown_item_1line,values); }
    private Button choice(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return b; }
    private Button bigButton(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); b.setTextColor(primary); b.setBackground(roundRect(card,10,1,accent)); return b; }
    private void label(LinearLayout root,String s){ TextView l=text(s,11,muted,true); l.setPadding(dp(3),dp(13),0,dp(5)); root.addView(l); }
    private TextView text(String v,float s,int c,boolean bold){ TextView t=new TextView(this); t.setText(v); t.setTextSize(s); t.setTextColor(c); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return t; }
    private GradientDrawable roundRect(int c,int r,int sw,int sc){ GradientDrawable d=new GradientDrawable(); d.setColor(c); d.setCornerRadius(dp(r)); if(sw>0)d.setStroke(dp(sw),sc); return d; }
    private LinearLayout.LayoutParams lp(int w,int h){ return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams lp(int w,int h,float weight){ return new LinearLayout.LayoutParams(w,h,weight); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){ p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
    private int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
    private double parseDouble(String s){ try{return Double.parseDouble(s.trim().replace(',','.').replace("ml","").trim());}catch(Exception e){return Double.NaN;} }
    private int parseOptionalInt(String s){ if(s==null||s.trim().isEmpty())return 0; try{return Integer.parseInt(s.trim());}catch(Exception e){return -1;} }
    private void toast(String s){ Toast.makeText(this,s,Toast.LENGTH_LONG).show(); }
}
