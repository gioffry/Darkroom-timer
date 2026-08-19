package it.darkroom.timer.assistant.paper;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;

/** R8 — paper chemistry is optional and never gates the enlarger timer. */
public final class PaperChemistryActivity extends Activity {
    private int primary,muted,accent,card;
    private AssistantDatabase db;
    private EditText paper,volume,devName,devDil,stopName,stopDil,fixName,fixDil,notes;
    private TextView devOrigin,stopOrigin,fixOrigin,preview;

    @Override protected void onCreate(Bundle state){super.onCreate(state);palette();db=new AssistantDatabase(this);buildUi();load();refreshPreview();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
    private void palette(){boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);if(dark){primary=Color.rgb(255,42,42);muted=Color.rgb(145,34,34);accent=Color.rgb(255,42,42);card=Color.rgb(18,0,0);}else{primary=Color.rgb(238,240,242);muted=Color.rgb(145,151,158);accent=Color.rgb(197,54,58);card=Color.rgb(24,26,30);}}

    private void buildUi(){ScrollView s=new ScrollView(this);s.setFillViewport(true);s.setBackgroundColor(Color.BLACK);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(18),dp(18),dp(28));s.addView(root);
        TextView eye=text("DARKROOM ASSISTANT · CHIMICA CARTA",12,accent,true);eye.setGravity(Gravity.CENTER);root.addView(eye);TextView title=text("SESSIONE DI STAMPA",25,primary,true);title.setGravity(Gravity.CENTER);root.addView(title);TextView intro=text("Configurazione opzionale. STAMPA, PROVINO e Split Grade restano utilizzabili anche senza sessione chimica.",12,muted,true);intro.setGravity(Gravity.CENTER);intro.setPadding(dp(4),dp(5),dp(4),dp(14));root.addView(intro);
        paper=field("Carta");paper.setText(PaperChemistryStore.PAPER_DEFAULT);root.addView(label("CARTA"));root.addView(paper);
        volume=field("Volume di lavoro ml");volume.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);root.addView(label("VOLUME DI LAVORO"));root.addView(volume);
        addComponent(root,"RIVELATORE CARTA",0);addComponent(root,"ARRESTO",1);addComponent(root,"FISSAGGIO",2);
        notes=field("Note sessione / trattamento finale / lavaggio");root.addView(label("NOTE / TRATTAMENTO FINALE"));root.addView(notes);
        preview=text("",12,primary,false);preview.setPadding(dp(12),dp(12),dp(12),dp(12));preview.setBackgroundColor(card);root.addView(preview);
        Button calc=button("CALCOLA PREPARAZIONE");calc.setOnClickListener(v->refreshPreview());root.addView(calc);
        Button active=button("ATTIVA SESSIONE CHIMICA");active.setOnClickListener(v->saveSession());root.addView(active);
        Button add=button("AGGIUNGI PRODOTTO A LA MIA CHIMICA");add.setOnClickListener(v->addProduct());root.addView(add);
        Button clear=button("DISATTIVA SESSIONE");clear.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("DISATTIVARE LA SESSIONE?").setMessage("Non verranno cancellati prodotti o inventario.").setPositiveButton("DISATTIVA",(d,w)->{PaperChemistryStore.clear(this);load();refreshPreview();toast("Nessuna sessione chimica attiva");}).setNegativeButton("ANNULLA",null).show());root.addView(clear);
        Button back=button("← INDIETRO");back.setOnClickListener(v->finish());root.addView(back);setContentView(s);}

    private void addComponent(LinearLayout root,String title,int which){root.addView(label(title));LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);EditText name=field("Prodotto");EditText dil=field("Diluizione, es. 1+9");TextView origin=text("NON DOCUMENTATO",10,muted,true);Button choose=button("SCEGLI");choose.setOnClickListener(v->chooseChemical(which));row.addView(name,new LinearLayout.LayoutParams(0,dp(52),1f));row.addView(choose,new LinearLayout.LayoutParams(dp(100),dp(52)));root.addView(row);root.addView(dil);root.addView(origin);if(which==0){devName=name;devDil=dil;devOrigin=origin;}else if(which==1){stopName=name;stopDil=dil;stopOrigin=origin;}else{fixName=name;fixDil=dil;fixOrigin=origin;}}

    private void chooseChemical(int which){final List<AssistantDatabase.ChemicalItem> items=db.listChemicals(false);if(items.isEmpty()){toast("La mia chimica è vuota. Aggiungi un prodotto personale oppure continua manualmente.");return;}String[] labels=new String[items.size()];for(int i=0;i<items.size();i++){AssistantDatabase.ChemicalItem x=items.get(i);labels[i]=x.name+" · "+(AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType)?"DATI DOCUMENTATI":"DATI PERSONALI");}new AlertDialog.Builder(this).setTitle("SCEGLI DA LA MIA CHIMICA").setItems(labels,(d,index)->{AssistantDatabase.ChemicalItem x=items.get(index);EditText n=which==0?devName:which==1?stopName:fixName;EditText dil=which==0?devDil:which==1?stopDil:fixDil;TextView o=which==0?devOrigin:which==1?stopOrigin:fixOrigin;n.setText(x.name);String suggested=!empty(x.personalDilution)?x.personalDilution:x.documentedDilutions;if(!empty(suggested)&&!suggested.contains(","))dil.setText(suggested);o.setText(originLabel(x));refreshPreview();}).show();}

    private String originLabel(AssistantDatabase.ChemicalItem x){if(AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType))return "DATI DOCUMENTATI · "+emptyOr(x.sourceName,"fonte catalogo");return "DATI PERSONALI · inseriti dall'utente";}

    private void load(){PaperChemistryStore.Session x=PaperChemistryStore.load(this);paper.setText(empty(x.paper)?PaperChemistryStore.PAPER_DEFAULT:x.paper);volume.setText(fmt(x.volumeMl));devName.setText(x.developer);devDil.setText(x.developerDilution);devOrigin.setText(emptyOr(x.developerOrigin,"NON DOCUMENTATO"));stopName.setText(x.stop);stopDil.setText(x.stopDilution);stopOrigin.setText(emptyOr(x.stopOrigin,"NON DOCUMENTATO"));fixName.setText(x.fixer);fixDil.setText(x.fixerDilution);fixOrigin.setText(emptyOr(x.fixerOrigin,"NON DOCUMENTATO"));notes.setText(x.notes);}

    private PaperChemistryStore.Session current(){PaperChemistryStore.Session x=new PaperChemistryStore.Session();x.paper=paper.getText().toString().trim();x.volumeMl=parseDouble(volume.getText().toString());x.developer=devName.getText().toString().trim();x.developerDilution=devDil.getText().toString().trim();x.developerOrigin=devOrigin.getText().toString();x.stop=stopName.getText().toString().trim();x.stopDilution=stopDil.getText().toString().trim();x.stopOrigin=stopOrigin.getText().toString();x.fixer=fixName.getText().toString().trim();x.fixerDilution=fixDil.getText().toString().trim();x.fixerOrigin=fixOrigin.getText().toString();x.notes=notes.getText().toString();return x;}
    private void saveSession(){PaperChemistryStore.Session x=current();if(!(x.volumeMl>0)){toast("Inserisci un volume di lavoro valido.");return;}PaperChemistryStore.save(this,x);refreshPreview();toast("Sessione chimica carta attiva");}

    private void refreshPreview(){PaperChemistryStore.Session x=current();StringBuilder b=new StringBuilder();b.append("PREPARAZIONE CHIMICA CARTA\nVolume per soluzione: ").append(x.volumeMl>0?fmt(x.volumeMl)+" ml":"NON DETERMINABILE").append("\n\n");appendMix(b,"Rivelatore",x.developer,x.developerDilution,x.volumeMl,x.developerOrigin);appendMix(b,"Arresto",x.stop,x.stopDilution,x.volumeMl,x.stopOrigin);appendMix(b,"Fissaggio",x.fixer,x.fixerDilution,x.volumeMl,x.fixerOrigin);b.append("\nNessun tempo di esposizione STAMPA viene modificato dalla chimica carta.");preview.setText(b.toString());}
    private void appendMix(StringBuilder b,String label,String name,String dilution,double total,String origin){b.append(label).append(": ").append(empty(name)?"non configurato":name).append("\n");if(empty(name)){b.append("  NON DOCUMENTATO\n");return;}PaperChemistryStore.Mix m=PaperChemistryStore.calculate(dilution,total);if(m.known)b.append("  ").append(fmt(m.productMl)).append(" ml prodotto + ").append(fmt(m.waterMl)).append(" ml acqua = ").append(fmt(m.totalMl)).append(" ml\n  CALCOLO · ").append(dilution).append("\n");else b.append("  ").append(m.message).append(" · nessun valore inventato\n");b.append("  Origine: ").append(emptyOr(origin,"NON DOCUMENTATO")).append("\n");}

    private void addProduct(){LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);EditText manufacturer=field("Produttore");EditText name=field("Nome prodotto");Spinner category=new Spinner(this);String[] cats={"RIVELATORE CARTA","ARRESTO","FISSAGGIO","LAVAGGIO / TRATTAMENTO FINALE","ALTRO"};category.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,cats));EditText amount=field("Quantità disponibile");amount.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);EditText unit=field("Unità, es. ml");unit.setText("ml");EditText dil=field("Diluizione personale, opzionale");b.addView(manufacturer);b.addView(name);b.addView(category);b.addView(amount);b.addView(unit);b.addView(dil);new AlertDialog.Builder(this).setTitle("PRODOTTO PERSONALE · CHIMICA CARTA").setMessage("Sarà salvato in LA MIA CHIMICA come DATO PERSONALE, non come fonte ufficiale.").setView(b).setPositiveButton("SALVA",(d,w)->{String n=name.getText().toString().trim();double q=parseDouble(amount.getText().toString());if(empty(n)||Double.isNaN(q)||q<0){toast("Nome o quantità non validi");return;}AssistantDatabase.ChemicalItem x=new AssistantDatabase.ChemicalItem();x.sourceType=AssistantDatabase.SOURCE_USER;x.manufacturer=manufacturer.getText().toString().trim();x.name=n;x.category=cats[category.getSelectedItemPosition()];x.initialAmount=q;x.remainingAmount=q;x.unit=unit.getText().toString().trim();x.personalDilution=dil.getText().toString().trim();x.dataType="DATO PERSONALE";x.sourceName="Inserito dall'utente";db.saveChemical(x);toast("Prodotto aggiunto a La mia chimica");}).setNegativeButton("ANNULLA",null).show();}

    private TextView label(String s){TextView t=text(s,11,muted,true);t.setPadding(dp(2),dp(10),dp(2),dp(3));return t;}private EditText field(String h){EditText x=new EditText(this);x.setHint(h);x.setHintTextColor(muted);x.setTextColor(primary);return x;}private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(primary);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return b;}private TextView text(String s,float z,int c,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}private static boolean empty(String s){return s==null||s.trim().isEmpty();}private static String emptyOr(String s,String f){return empty(s)?f:s.trim();}private static double parseDouble(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return Double.NaN;}}private static String fmt(double v){if(Double.isNaN(v))return "NON DETERMINABILE";return Math.abs(v-Math.rint(v))<0.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}
}
