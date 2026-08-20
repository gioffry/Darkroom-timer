package it.darkroom.timer.assistant.development;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/** Input del primo flusso operativo del Darkroom Assistant. */
public final class NewDevelopmentActivity extends Activity {
    private int primary, muted, border, card, accent;
    private AutoCompleteTextView filmField, developerField, dilutionField;
    private TextView nominalIsoText;
    private EditText exposedIsoField, temperatureField, volumeField, rollsField;
    private TextView tankChoice;
    private long selectedTankId=0;
    private String selectedTankPlan="";
    private Button format35, format120;
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
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true); scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(16),dp(18),dp(28));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));

        TextView eyebrow=text("DARKROOM ASSISTANT · 9/9",12,accent,true); eyebrow.setGravity(Gravity.CENTER); root.addView(eyebrow);
        TextView title=text("NUOVO SVILUPPO",24,primary,true); title.setGravity(Gravity.CENTER); root.addView(title);
        TextView processor=text("JOBO CPE2  ·  ROTAZIONE CONTINUA",13,accent,true); processor.setGravity(Gravity.CENTER);
        processor.setPadding(0,dp(5),0,dp(18)); root.addView(processor);
        if(getIntent().getIntExtra("repeatTimeSeconds",0)>0){
            TextView repeat=text("RICETTA DAL LOG · tempo storico "+DevelopmentCatalog.formatTime(getIntent().getIntExtra("repeatTimeSeconds",0)),12,accent,true);
            repeat.setGravity(Gravity.CENTER); repeat.setPadding(0,0,0,dp(10)); root.addView(repeat);
        }

        label(root,"PELLICOLA");
        filmField=autoField("Cerca o seleziona pellicola");
        filmField.setAdapter(adapter(DevelopmentCatalog.filmNames()));
        root.addView(filmField, lp(-1,dp(52)));
        filmField.setOnClickListener(v -> filmField.showDropDown());
        filmField.setOnFocusChangeListener((v,has) -> { if(has) filmField.showDropDown(); });
        filmField.setOnItemClickListener((p,v,pos,id) -> onFilmChanged());

        label(root,"FORMATO");
        LinearLayout formats=new LinearLayout(this); formats.setOrientation(LinearLayout.HORIZONTAL);
        format35=smallChoice("35 mm"); format120=smallChoice("120");
        format35.setOnClickListener(v -> selectFormat("35 mm")); format120.setOnClickListener(v -> selectFormat("120"));
        formats.addView(format35,margin(lp(0,dp(48),1f),0,0,5,0));
        formats.addView(format120,margin(lp(0,dp(48),1f),5,0,0,0)); root.addView(formats);
        selectFormat("120");

        label(root,"ISO NOMINALE");
        nominalIsoText=text("—",19,primary,true); nominalIsoText.setPadding(dp(14),dp(12),dp(14),dp(12));
        nominalIsoText.setBackground(roundRect(card,9,1,border)); root.addView(nominalIsoText,lp(-1,dp(50)));

        label(root,"ISO ESPOSTO");
        exposedIsoField=editField("es. 1600",InputType.TYPE_CLASS_NUMBER); root.addView(exposedIsoField,lp(-1,dp(52)));
        exposedIsoField.addTextChangedListener(new TextWatcher(){ public void beforeTextChanged(CharSequence s,int st,int c,int a){} public void onTextChanged(CharSequence s,int st,int b,int c){ refreshDilutions(); } public void afterTextChanged(Editable e){} });

        label(root,"RIVELATORE");
        developerField=autoField("Scelta indipendente dalla marca");
        developerField.setAdapter(adapter(DevelopmentCatalog.developerNames())); root.addView(developerField,lp(-1,dp(52)));
        developerField.setOnClickListener(v -> developerField.showDropDown());
        developerField.setOnFocusChangeListener((v,has) -> { if(has) developerField.showDropDown(); });
        developerField.setOnItemClickListener((p,v,pos,id) -> refreshDilutions());

        label(root,"DILUIZIONE");
        dilutionField=autoField("Seleziona dopo pellicola e rivelatore"); root.addView(dilutionField,lp(-1,dp(52)));
        dilutionField.setOnClickListener(v -> dilutionField.showDropDown());
        dilutionField.setOnFocusChangeListener((v,has) -> { if(has) dilutionField.showDropDown(); });

        label(root,"NUMERO RULLI");
        rollsField=editField("es. 1",InputType.TYPE_CLASS_NUMBER); rollsField.setText("1");
        root.addView(rollsField,lp(-1,dp(52)));

        label(root,"VOLUME TOTALE DA PREPARARE");
        volumeField=editField("es. 340 ml",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        volumeField.setText("340"); root.addView(volumeField,lp(-1,dp(52)));
        TextView volumeNote=text("Volume manuale disponibile anche senza attrezzatura configurata",11,muted,false);
        volumeNote.setPadding(dp(4),dp(5),dp(4),dp(2)); root.addView(volumeNote);

        label(root,"TANK");
        tankChoice=text("Nessuna tank selezionata · volume manuale",12,muted,true);
        tankChoice.setPadding(dp(4),dp(4),dp(4),dp(6)); root.addView(tankChoice);
        LinearLayout tankActions=new LinearLayout(this); tankActions.setOrientation(LinearLayout.HORIZONTAL);
        Button chooseTank=smallChoice("SCEGLI TANK"); chooseTank.setOnClickListener(v->chooseTankManual());
        Button bestTank=smallChoice("TANK MIGLIORE"); bestTank.setOnClickListener(v->chooseTankBest());
        tankActions.addView(chooseTank,lp(0,dp(52),1)); tankActions.addView(bestTank,lp(0,dp(52),1)); root.addView(tankActions);

        label(root,"TEMPERATURA REALE");
        temperatureField=editField("es. 21,7 °C",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        temperatureField.setText("20,0"); root.addView(temperatureField,lp(-1,dp(52)));
        TextView tempNote=text("Inserimento manuale dal tuo sondino · intervallo supportato R2: 16–26 °C",11,muted,false);
        tempNote.setPadding(dp(4),dp(5),dp(4),dp(12)); root.addView(tempNote);

        Button calculate=bigButton("CALCOLA TEMPO E PREPARA"); calculate.setOnClickListener(v -> calculate());
        root.addView(calculate,margin(lp(-1,dp(60)),0,12,0,0));
        TextView sourceNote=text("Il risultato usa solo dati documentati FOMA / ILFORD / KODAK. Se una combinazione non è documentata, l’app non inventa un tempo.",11,muted,false);
        sourceNote.setGravity(Gravity.CENTER); sourceNote.setPadding(dp(6),dp(10),dp(6),dp(14)); root.addView(sourceNote);

        Button back=bigButton("←  ASSISTANT"); back.setOnClickListener(v -> finish()); root.addView(back,lp(-1,dp(52)));
        setContentView(scroll);
        applyPrefill();
    }

    private void applyPrefill() {
        Intent src=getIntent(); if(!src.hasExtra("prefillFilm")) return;
        filmField.setText(src.getStringExtra("prefillFilm"),false); onFilmChanged();
        selectFormat(src.getStringExtra("prefillFormat") == null ? "120" : src.getStringExtra("prefillFormat"));
        exposedIsoField.setText(Integer.toString(src.getIntExtra("prefillExposedIso",DevelopmentCatalog.findFilm(filmField.getText().toString()).nominalIso)));
        developerField.setText(src.getStringExtra("prefillDeveloper"),false); refreshDilutions();
        dilutionField.setText(src.getStringExtra("prefillDilution"),false);
        temperatureField.setText(String.format(java.util.Locale.ITALY,"%.1f",src.getDoubleExtra("prefillTemperature",20.0)));
        rollsField.setText(Integer.toString(src.getIntExtra("prefillRolls",1)));
        volumeField.setText(ChemistryNumber.format(src.getDoubleExtra("prefillVolume",340.0)));
    }

    private static final class ChemistryNumber { static String format(double v){ return Math.abs(v-Math.rint(v))<0.05 ? String.format(java.util.Locale.ITALY,"%.0f",v) : String.format(java.util.Locale.ITALY,"%.1f",v); } }

    private void onFilmChanged() {
        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());
        if(film==null){ nominalIsoText.setText("—"); return; }
        nominalIsoText.setText(Integer.toString(film.nominalIso));
        exposedIsoField.setText(Integer.toString(film.nominalIso));
        if(!film.format120 && "120".equals(selectedFormat)) selectFormat("35 mm");
        refreshDilutions();
    }

    private void refreshDilutions() {
        if(dilutionField==null || filmField==null || developerField==null || exposedIsoField==null) return;
        int ei=parseInt(exposedIsoField.getText().toString(),-1);
        String[] values=DevelopmentCatalog.availableDilutions(filmField.getText().toString(),ei,developerField.getText().toString());
        dilutionField.setAdapter(adapter(values));
        if(values.length>0 && !containsIgnoreCase(values,dilutionField.getText().toString())) dilutionField.setText(values[0],false);
        if(values.length==0) dilutionField.setText("");
    }

    private void selectFormat(String format) {
        selectedFormat=format;
        if(format35==null || format120==null) return;
        format35.setBackground(roundRect(card,9,1,"35 mm".equals(format)?accent:border));
        format120.setBackground(roundRect(card,9,1,"120".equals(format)?accent:border));
        format35.setTextColor("35 mm".equals(format)?accent:primary);
        format120.setTextColor("120".equals(format)?accent:primary);
    }

    private void chooseTankManual() {
        it.darkroom.timer.assistant.data.AssistantDatabase db=new it.darkroom.timer.assistant.data.AssistantDatabase(this);
        java.util.List<it.darkroom.timer.assistant.data.AssistantDatabase.TankItem> tanks=db.listTanks(); db.close();
        if(tanks.isEmpty()){ toast("Nessuna tank personale configurata. Puoi continuare con il volume manuale."); return; }
        String[] labels=new String[tanks.size()]; for(int i=0;i<tanks.size();i++) labels[i]=tanks.get(i).displayName();
        new android.app.AlertDialog.Builder(this).setTitle("SCEGLI TANK").setItems(labels,(d,which)->{
            it.darkroom.timer.assistant.data.AssistantDatabase.TankItem t=tanks.get(which); selectedTankId=t.id; selectedTankPlan="Scelta manuale · "+t.displayName(); tankChoice.setText(selectedTankPlan);
        }).show();
    }

    private void chooseTankBest() {
        int rolls=parseInt(rollsField.getText().toString(),-1); double volume=parseDouble(volumeField.getText().toString());
        if(rolls<=0||Double.isNaN(volume)||volume<=0){ toast("Inserisci prima numero rulli e volume."); return; }
        it.darkroom.timer.assistant.data.AssistantDatabase db=new it.darkroom.timer.assistant.data.AssistantDatabase(this);
        java.util.List<it.darkroom.timer.assistant.data.AssistantDatabase.TankItem> tanks=db.listTanks();
        it.darkroom.timer.assistant.data.AssistantDatabase.ChemicalItem inv=db.findChemicalForDeveloper(developerField.getText().toString());
        it.darkroom.timer.assistant.equipment.TankPlanner.Plan p=it.darkroom.timer.assistant.equipment.TankPlanner.chooseBest(tanks,selectedFormat,rolls,volume,developerField.getText().toString(),dilutionField.getText().toString(),inv); db.close();
        if(!p.ok){ selectedTankId=0; selectedTankPlan=p.problem; tankChoice.setText(p.problem); new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.problem).setPositiveButton("OK",null).show(); return; }
        selectedTankId=p.tank.id; selectedTankPlan=p.summary(); tankChoice.setText(p.tank.displayName()+" · "+p.cycles+(p.cycles==1?" ciclo":" cicli"));
        new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.summary()).setPositiveButton("USA QUESTA",null).show();
    }

    private void calculate() {
        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());
        if(film==null){ toast("Seleziona una pellicola dal catalogo."); return; }
        int exposed=parseInt(exposedIsoField.getText().toString(),-1);
        if(exposed<=0){ toast("Inserisci un ISO esposto valido."); return; }
        int rolls=parseInt(rollsField.getText().toString(),-1);
        if(rolls<=0){ toast("Inserisci il numero di rulli."); return; }
        double volume=parseDouble(volumeField.getText().toString());
        if(Double.isNaN(volume)||volume<=0){ toast("Inserisci il volume totale in ml."); return; }
        if(volume>it.darkroom.timer.assistant.chemistry.ChemistryCalculator.CPE2_MAX_ML){
            toast("JOBO CPE2: il volume massimo documentato è 600 ml."); return;
        }
        double temp=parseDouble(temperatureField.getText().toString());
        if(Double.isNaN(temp)){ toast("Inserisci la temperatura, per esempio 21,7."); return; }
        DevelopmentCatalog.Result r=DevelopmentCatalog.calculate(film.name,selectedFormat,exposed,
                developerField.getText().toString(),dilutionField.getText().toString(),temp);
        if(!r.ok){ toast(r.error); return; }
        Intent i=new Intent(this,DevelopmentResultActivity.class);
        i.putExtra("film",r.film); i.putExtra("format",r.format); i.putExtra("nominalIso",r.nominalIso);
        i.putExtra("exposedIso",r.exposedIso); i.putExtra("developer",r.developer); i.putExtra("dilution",r.dilution);
        i.putExtra("temperature",r.temperature); i.putExtra("seconds",r.finalSeconds); i.putExtra("source",r.source);
        i.putExtra("dataType",r.dataType); i.putExtra("sourceData",r.sourceData); i.putExtra("calculation",r.calculation);
        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);
        i.putExtra("selectedTankId",selectedTankId); i.putExtra("tankPlanSummary",selectedTankPlan);
        if(getIntent().getIntExtra("repeatTimeSeconds",0)>0){ i.putExtra("repeatTimeSeconds",getIntent().getIntExtra("repeatTimeSeconds",0)); i.putExtra("repeatOrigin",getIntent().getStringExtra("repeatOrigin")); }
        startActivity(i);
    }

    private AutoCompleteTextView autoField(String hint) {
        AutoCompleteTextView v=new AutoCompleteTextView(this); v.setHint(hint); v.setThreshold(0); v.setSingleLine(true);
        v.setTextSize(16); v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0);
        v.setBackground(roundRect(card,9,1,border)); return v;
    }
    private EditText editField(String hint,int type) {
        EditText v=new EditText(this); v.setHint(hint); v.setSingleLine(true); v.setInputType(type); v.setTextSize(16);
        v.setTextColor(primary); v.setHintTextColor(muted); v.setPadding(dp(14),0,dp(14),0); v.setBackground(roundRect(card,9,1,border)); return v;
    }
    private ArrayAdapter<String> adapter(String[] values) {
        ArrayAdapter<String> a=new ArrayAdapter<String>(this,android.R.layout.simple_dropdown_item_1line,values);
        return a;
    }
    private Button smallChoice(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return b; }
    private Button bigButton(String t){ Button b=new Button(this); b.setText(t); b.setAllCaps(false); b.setTextSize(16); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD); b.setTextColor(primary); b.setBackground(roundRect(card,10,1,accent)); return b; }
    private void label(LinearLayout root,String s){ TextView l=text(s,11,muted,true); l.setPadding(dp(3),dp(13),0,dp(5)); root.addView(l); }
    private TextView text(String v,float s,int c,boolean bold){ TextView t=new TextView(this); t.setText(v); t.setTextSize(s); t.setTextColor(c); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); return t; }
    private GradientDrawable roundRect(int c,int r,int sw,int sc){ GradientDrawable d=new GradientDrawable(); d.setColor(c); d.setCornerRadius(dp(r)); if(sw>0)d.setStroke(dp(sw),sc); return d; }
    private LinearLayout.LayoutParams lp(int w,int h){ return new LinearLayout.LayoutParams(w,h); }
    private LinearLayout.LayoutParams lp(int w,int h,float weight){ return new LinearLayout.LayoutParams(w,h,weight); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){ p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
    private int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
    private int parseInt(String s,int fallback){ try{return Integer.parseInt(s.trim());}catch(Exception e){return fallback;} }
    private double parseDouble(String s){ try{return Double.parseDouble(s.trim().replace(',','.').replace("°C","").replace("ml","").trim());}catch(Exception e){return Double.NaN;} }
    private boolean containsIgnoreCase(String[] values,String q){ if(q==null)return false; for(String v:values)if(v.equalsIgnoreCase(q.trim()))return true; return false; }
    private void toast(String s){ Toast.makeText(this,s,Toast.LENGTH_LONG).show(); }
}
