package it.darkroom.timer.assistant.equipment;

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
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;

/** Darkroom Assistant R6 — personal equipment, first integrated category: tanks. */
public final class MyEquipmentActivity extends Activity {
    private AssistantDatabase db; private LinearLayout list; private int primary,muted,accent;
    private static final String JOBO_SOURCE="JOBO Tank System 2500 instruction manual / JOBO Analog catalog: 2520 rotary minimum 270 ml; 2×35 mm; up to 2×120 with 2502 reel separating clip.";

    @Override protected void onCreate(Bundle b){super.onCreate(b);palette();db=new AssistantDatabase(this);build();}
    @Override protected void onResume(){super.onResume();refresh();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
    private void palette(){boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);primary=dark?Color.rgb(255,42,42):Color.rgb(238,240,242);muted=dark?Color.rgb(145,34,34):Color.rgb(145,151,158);accent=dark?Color.rgb(255,42,42):Color.rgb(197,54,58);}

    private void build(){ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.BLACK);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(16),dp(18),dp(28));s.addView(root);TextView t=text("LA MIA ATTREZZATURA",25,primary,true);t.setGravity(Gravity.CENTER);root.addView(t);TextView sub=text("TANK · dati tecnici separati dai dati personali",12,muted,false);sub.setGravity(Gravity.CENTER);sub.setPadding(0,dp(4),0,dp(14));root.addView(sub);
        Button catalog=button("AGGIUNGI TANK DAL CATALOGO · JOBO 2520");catalog.setOnClickListener(v->addJobo2520());root.addView(catalog,margin(-1,dp(58),0,0,0,dp(8)));
        Button manual=button("AGGIUNGI TANK MANUALMENTE");manual.setOnClickListener(v->manualDialog());root.addView(manual,margin(-1,dp(58),0,0,0,dp(14)));
        list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);root.addView(list);Button back=button("← ASSISTANT");back.setOnClickListener(v->finish());root.addView(back);setContentView(s);refresh();}

    private void addJobo2520(){LinearLayout box=form();EditText personal=field("Nome personale (opzionale)");EditText qty=field("Quantità posseduta");qty.setInputType(InputType.TYPE_CLASS_NUMBER);qty.setText("1");box.addView(personal);box.addView(qty);
        String msg="DATI TECNICI DOCUMENTATI\nJOBO 2520 · System 2500\nRotazione: minimo 270 ml\n35 mm: 2 rulli\n120: fino a 2 rulli con separatore 2502\nCompatibile con processore JOBO e lift tramite cog.\n\nIl limite macchina CPE2 di 600 ml resta un vincolo separato.";
        new AlertDialog.Builder(this).setTitle("JOBO 2520").setMessage(msg).setView(box).setPositiveButton("AGGIUNGI",(d,w)->{AssistantDatabase.TankItem t=new AssistantDatabase.TankItem();t.sourceType=AssistantDatabase.SOURCE_CATALOG;t.sourceModelKey="JOBO-2520";t.manufacturer="JOBO";t.model="2520";t.personalName=personal.getText().toString();t.quantityOwned=Math.max(1,parseInt(qty.getText().toString(),1));t.system="System 2500";t.tankType="Multi Tank 2";t.capacity35=2;t.capacity120=2;t.minRotationMl=270;t.minInversionMl=775;t.maxVolumeMl=0;t.cpe2Compatible=true;t.liftCompatible=true;t.technicalSource=JOBO_SOURCE;t.dataType="DATI TECNICI DOCUMENTATI";t.notes="Inversione: 775 ml è il minimo documentato per 1×35 mm; altre configurazioni richiedono più volume. Il planner usa il dato di rotazione, non quello di inversione.";db.saveTank(t);toast("JOBO 2520 aggiunta");refresh();}).setNegativeButton("ANNULLA",null).show();}

    private void manualDialog(){LinearLayout box=form();EditText maker=field("Produttore");EditText model=field("Modello");EditText personal=field("Nome personale (opzionale)");EditText c35=number("Capacità 35 mm · rulli");EditText c120=number("Capacità 120 · rulli");EditText minInv=decimal("Volume minimo inversione ml · 0 se non noto");EditText minRot=decimal("Volume minimo rotazione ml · 0 se non noto");EditText max=decimal("Volume massimo tank ml · 0 se non noto");EditText notes=field("Note / compatibilità");for(EditText x:new EditText[]{maker,model,personal,c35,c120,minInv,minRot,max,notes})box.addView(x);
        new AlertDialog.Builder(this).setTitle("AGGIUNGI TANK MANUALMENTE").setMessage("Questi valori saranno marcati DATI INSERITI DALL'UTENTE. Inserire 0 solo per un campo numerico non documentato; il planner lo tratterà come non determinabile, non come capacità zero.").setView(box).setPositiveButton("SALVA",(d,w)->{if(model.getText().toString().trim().isEmpty()){toast("Inserisci il modello");return;}AssistantDatabase.TankItem t=new AssistantDatabase.TankItem();t.sourceType=AssistantDatabase.SOURCE_USER;t.manufacturer=maker.getText().toString();t.model=model.getText().toString();t.personalName=personal.getText().toString();t.capacity35=Math.max(0,parseInt(c35.getText().toString(),0));t.capacity120=Math.max(0,parseInt(c120.getText().toString(),0));t.minInversionMl=Math.max(0,parseDouble(minInv.getText().toString(),0));t.minRotationMl=Math.max(0,parseDouble(minRot.getText().toString(),0));t.maxVolumeMl=Math.max(0,parseDouble(max.getText().toString(),0));t.cpe2Compatible=notes.getText().toString().toLowerCase(Locale.ITALY).contains("cpe2");t.liftCompatible=notes.getText().toString().toLowerCase(Locale.ITALY).contains("lift");t.notes=notes.getText().toString();t.dataType="DATI INSERITI DALL'UTENTE";t.technicalSource="Utente";db.saveTank(t);toast("Tank personale salvata");refresh();}).setNegativeButton("ANNULLA",null).show();}

    private void refresh(){if(list==null)return;list.removeAllViews();List<AssistantDatabase.TankItem> tanks=db.listTanks();if(tanks.isEmpty()){TextView e=text("Nessuna tank configurata. NUOVO SVILUPPO continuerà a funzionare con il volume manuale.",13,muted,false);e.setPadding(0,dp(16),0,dp(16));list.addView(e);return;}for(AssistantDatabase.TankItem t:tanks){String cap="35 mm "+knownInt(t.capacity35)+" · 120 "+knownInt(t.capacity120);Button b=button("TANK · "+t.displayName()+"\n"+cap);b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);b.setOnClickListener(v->detail(t.id));list.addView(b,margin(-1,dp(86),0,0,0,dp(8)));}}
    private void detail(long id){AssistantDatabase.TankItem t=db.getTank(id);if(t==null)return;String inv=t.minInversionMl>0?fmt(t.minInversionMl)+" ml":"NON DOCUMENTATO";String rot=t.minRotationMl>0?fmt(t.minRotationMl)+" ml":"NON DOCUMENTATO";String max=t.maxVolumeMl>0?fmt(t.maxVolumeMl)+" ml":"NON DOCUMENTATO";String msg=(AssistantDatabase.SOURCE_USER.equals(t.sourceType)?"DATI INSERITI DALL'UTENTE":"DATI TECNICI DOCUMENTATI")+"\n\nProduttore/modello: "+t.manufacturer+" "+t.model+"\nSistema: "+t.system+"\nTipo: "+t.tankType+"\nCapacità 35 mm: "+knownInt(t.capacity35)+"\nCapacità 120: "+knownInt(t.capacity120)+"\nMinimo inversione: "+inv+"\nMinimo rotazione: "+rot+"\nMassimo fisico tank: "+max+"\nCompatibilità CPE2: "+yesNo(t.cpe2Compatible)+"\nCompatibilità lift: "+yesNo(t.liftCompatible)+"\n\nLimite macchina JOBO CPE2: 600 ml\n\nFonte tecnica: "+empty(t.technicalSource)+"\nNote personali: "+empty(t.notes);new AlertDialog.Builder(this).setTitle(t.displayName()).setMessage(msg).setPositiveButton("CHIUDI",null).show();}

    private static String knownInt(int v){return v>0?Integer.toString(v):"NON DOCUMENTATA";}private static String yesNo(boolean v){return v?"sì":"non dichiarata/no";}private static String empty(String s){return s==null||s.trim().isEmpty()?"—":s;}private static String fmt(double v){return String.format(Locale.ITALY,"%.0f",v);}private LinearLayout form(){LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);b.setPadding(dp(18),0,dp(18),0);return b;}private EditText field(String h){EditText x=new EditText(this);x.setHint(h);x.setHintTextColor(muted);x.setTextColor(primary);return x;}private EditText number(String h){EditText x=field(h);x.setInputType(InputType.TYPE_CLASS_NUMBER);return x;}private EditText decimal(String h){EditText x=field(h);x.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);return x;}private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(primary);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return b;}private TextView text(String s,float z,int c,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}private LinearLayout.LayoutParams margin(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}private int parseInt(String s,int d){try{return Integer.parseInt(s.trim());}catch(Exception e){return d;}}private double parseDouble(String s,double d){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return d;}}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
