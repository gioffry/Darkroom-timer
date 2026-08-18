package it.darkroom.timer.assistant.development;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.Locale;

import it.darkroom.timer.assistant.chemistry.ChemistryCalculator;

/** Risultato R3: tempo in evidenza + preparazione chimica, nessun countdown. */
public final class DevelopmentResultActivity extends Activity {
    private int primary, muted, border, card, accent;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);
        if(darkroomMode){ primary=Color.rgb(255,42,42); muted=Color.rgb(145,34,34); border=Color.rgb(112,20,20); card=Color.rgb(18,0,0); accent=Color.rgb(255,42,42); }
        else { primary=Color.rgb(238,240,242); muted=Color.rgb(145,151,158); border=Color.rgb(60,64,70); card=Color.rgb(24,26,30); accent=Color.rgb(197,54,58); }
        buildUi();
    }

    private void buildUi() {
        Bundle e=getIntent().getExtras(); if(e==null){ finish(); return; }
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(18),dp(18),dp(28));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));

        TextView film=text(e.getString("film",""),25,primary,true); film.setGravity(Gravity.CENTER); root.addView(film);
        TextView line1=text(e.getString("format","")+"  ·  ISO "+e.getInt("exposedIso"),15,muted,true); line1.setGravity(Gravity.CENTER); root.addView(line1);
        TextView chemistry=text(e.getString("developer","")+"  ·  "+e.getString("dilution",""),17,primary,true); chemistry.setGravity(Gravity.CENTER); chemistry.setPadding(0,dp(16),0,dp(4)); root.addView(chemistry);
        TextView temp=text(String.format(Locale.ITALY,"%.1f °C",e.getDouble("temperature")),16,primary,false); temp.setGravity(Gravity.CENTER); root.addView(temp);
        TextView processor=text("JOBO CPE2  ·  rotazione continua",15,accent,true); processor.setGravity(Gravity.CENTER); processor.setPadding(0,dp(6),0,dp(20)); root.addView(processor);

        TextView label=text("TEMPO DA IMPOSTARE SUL TIMER",12,muted,true); label.setGravity(Gravity.CENTER); root.addView(label);
        TextView time=text(DevelopmentCatalog.formatTime(e.getInt("seconds")),38,accent,true); time.setGravity(Gravity.CENTER); time.setPadding(0,dp(6),0,dp(18)); root.addView(time);

        LinearLayout prepareCard=new LinearLayout(this); prepareCard.setOrientation(LinearLayout.VERTICAL);
        prepareCard.setPadding(dp(14),dp(12),dp(14),dp(12)); prepareCard.setBackground(roundRect(card,10,1,accent));
        root.addView(prepareCard,lp(-1,-2));
        renderPrepare(prepareCard,e,e.getDouble("volumeMl",0.0));

        LinearLayout sourceCard=new LinearLayout(this); sourceCard.setOrientation(LinearLayout.VERTICAL); sourceCard.setPadding(dp(14),dp(12),dp(14),dp(12)); sourceCard.setBackground(roundRect(card,10,1,border));
        sourceCard.addView(text("Fonte: "+e.getString("source",""),13,primary,true));
        TextView kind=text("Tipo dato: "+e.getString("dataType",""),13,accent,true); kind.setPadding(0,dp(7),0,0); sourceCard.addView(kind);
        TextView sourceData=text("Dato fonte: "+e.getString("sourceData",""),12,muted,false); sourceData.setPadding(0,dp(7),0,0); sourceCard.addView(sourceData);
        TextView calc=text(e.getString("calculation",""),12,muted,false); calc.setPadding(0,dp(7),0,0); sourceCard.addView(calc);
        root.addView(sourceCard,margin(lp(-1,-2),0,12,0,0));

        String alternatives=e.getString("alternatives","");
        if(alternatives!=null && !alternatives.trim().isEmpty()) {
            Button toggle=button("ALTRE FONTI"); TextView alt=text(alternatives,12,muted,false); alt.setVisibility(View.GONE); alt.setPadding(dp(8),dp(8),dp(8),dp(8));
            toggle.setOnClickListener(v -> alt.setVisibility(alt.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE));
            root.addView(toggle,margin(lp(-1,dp(50)),0,12,0,0)); root.addView(alt);
        }

        TextView note=text("Nessun conto alla rovescia: imposta il tempo indicato sul tuo timer fisico.",11,muted,false); note.setGravity(Gravity.CENTER); note.setPadding(dp(6),dp(14),dp(6),dp(14)); root.addView(note);
        Button back=button("←  MODIFICA SVILUPPO"); back.setOnClickListener(v -> finish()); root.addView(back,lp(-1,dp(54)));
        setContentView(scroll);
    }

    private void renderPrepare(LinearLayout box, Bundle e, double volumeMl) {
        box.removeAllViews();
        int rolls=e.getInt("rolls",1);
        String format=e.getString("format","120");
        String developer=e.getString("developer","");
        String dilution=e.getString("dilution","");
        ChemistryCalculator.Result p=ChemistryCalculator.calculate(developer,dilution,volumeMl,format,rolls);

        box.addView(text("PREPARA",12,accent,true));
        TextView recipe=text(developer+"  "+dilution,17,primary,true); recipe.setPadding(0,dp(4),0,dp(7)); box.addView(recipe);
        if(!p.inputValid) {
            box.addView(text(p.error,13,accent,true));
            return;
        }
        if(p.dilutionKnown) {
            box.addView(text(ChemistryCalculator.formatMl(p.productMl)+" ml prodotto / stock",17,primary,true));
            box.addView(text(ChemistryCalculator.formatMl(p.waterMl)+" ml acqua",17,primary,true));
            box.addView(text(ChemistryCalculator.formatMl(p.totalMl)+" ml totale",17,primary,true));
        } else {
            box.addView(text(p.dilutionMessage,13,accent,true));
        }
        TextView rollsLine=text(rolls+" × "+format,13,muted,true); rollsLine.setPadding(0,dp(9),0,0); box.addView(rollsLine);
        TextView cap=text(p.capacityMessage,13,
                ChemistryCalculator.CAPACITY_INSUFFICIENT.equals(p.capacityState)?accent:muted,
                ChemistryCalculator.CAPACITY_VERIFIED.equals(p.capacityState));
        cap.setPadding(0,dp(5),0,0); box.addView(cap);
        if(!p.capacitySource.isEmpty()) {
            TextView src=text("Fonte capacità: "+p.capacitySource,10,muted,false); src.setPadding(0,dp(5),0,0); box.addView(src);
        }
        TextView cpe=text(p.cpe2Message,11,p.cpe2Compatible?muted:accent,!p.cpe2Compatible);
        cpe.setPadding(0,dp(7),0,0); box.addView(cpe);
        if(p.canAdoptMinimum) {
            Button adopt=button("USA VOLUME MINIMO · "+ChemistryCalculator.formatMl(p.minimumVolumeMl)+" ml");
            adopt.setOnClickListener(v -> { e.putDouble("volumeMl",p.minimumVolumeMl); renderPrepare(box,e,p.minimumVolumeMl); });
            box.addView(adopt,margin(lp(-1,dp(50)),0,9,0,0));
        }
    }

    private Button button(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); b.setTextColor(primary); b.setBackground(roundRect(card,10,1,accent)); return b; }
    private TextView text(String v,float s,int c,boolean bold){ TextView t=new TextView(this); t.setText(v); t.setTextSize(s); t.setTextColor(c); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return t; }
    private GradientDrawable roundRect(int c,int r,int sw,int sc){ GradientDrawable d=new GradientDrawable(); d.setColor(c); d.setCornerRadius(dp(r)); if(sw>0)d.setStroke(dp(sw),sc); return d; }
    private LinearLayout.LayoutParams lp(int w,int h){ return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){ p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
    private int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
}
