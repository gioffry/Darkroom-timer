package it.darkroom.timer.assistant.paper;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.util.Locale;

import it.darkroom.timer.assistant.chemistry.inventory.MyChemistryActivity;
import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.search.SmartCatalog;
import it.darkroom.timer.assistant.search.SmartSearchActivity;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** Optional paper-chemistry session with Smart Catalog pickers. Exposure logic remains independent. */
public final class PaperChemistryActivity extends Activity {
    private static final int PICK_PAPER=8100,PICK_DEV=8101,PICK_STOP=8102,PICK_FIX=8103;
    private EditText volume,devDil,stopDil,fixDil,notes;
    private TextView paperName,devName,stopName,fixName,devOrigin,stopOrigin,fixOrigin,preview;
    private AssistantDatabase db;

    @Override protected void onCreate(Bundle state){super.onCreate(state);db=new AssistantDatabase(this);buildUi();load();refreshPreview();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}

    private void buildUi(){LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · CHIMICA CARTA","SESSIONE DI STAMPA","Opzionale: STAMPA, PROVINO e Split Grade restano immediatamente disponibili.");
        root.addView(AssistantUi.section(this,"CARTA"));LinearLayout paperCard=AssistantUi.card(this);paperName=AssistantUi.cardTitle(this,PaperChemistryStore.PAPER_DEFAULT);paperCard.addView(paperName);Button paperSearch=AssistantUi.secondaryButton(this,"CERCA CARTA");paperSearch.setOnClickListener(v->pick(PICK_PAPER,"CERCA CARTA","Cerca carta...","PAPER",paperName.getText().toString()));paperCard.addView(paperSearch,AssistantUi.margin(this,-1,AssistantUi.dp(this,46),0,8,0,0));root.addView(paperCard);
        root.addView(AssistantUi.section(this,"VOLUME DI LAVORO"));volume=AssistantUi.numberField(this,"Volume per soluzione · ml");root.addView(volume,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,4));root.addView(AssistantUi.secondary(this,"Il volume non viene assunto dalla vaschetta se non è stato indicato."));
        addComponent(root,"RIVELATORE CARTA",PICK_DEV);addComponent(root,"ARRESTO",PICK_STOP);addComponent(root,"FISSAGGIO",PICK_FIX);
        root.addView(AssistantUi.section(this,"NOTE / TRATTAMENTO FINALE"));notes=AssistantUi.field(this,"Lavaggio, trattamento finale, note sessione");root.addView(notes,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,10));
        preview=AssistantUi.body(this,"");preview.setPadding(AssistantUi.dp(this,14),AssistantUi.dp(this,12),AssistantUi.dp(this,14),AssistantUi.dp(this,12));preview.setBackground(AssistantUi.round(this,AssistantUi.palette(this).card,11,1,AssistantUi.palette(this).border));root.addView(preview);
        Button calc=AssistantUi.secondaryButton(this,"CALCOLA PREPARAZIONE");calc.setOnClickListener(v->refreshPreview());root.addView(calc,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,10,0,0));Button active=AssistantUi.primaryButton(this,"ATTIVA SESSIONE CHIMICA");active.setOnClickListener(v->saveSession());root.addView(active,AssistantUi.margin(this,-1,AssistantUi.dp(this,56),0,7,0,0));
        Button inventory=AssistantUi.secondaryButton(this,"APRI LA MIA CHIMICA");inventory.setOnClickListener(v->startActivity(new Intent(this,MyChemistryActivity.class)));root.addView(inventory,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,7,0,0));
        Button clear=AssistantUi.ghostButton(this,"DISATTIVA SESSIONE");clear.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Disattivare la sessione?").setMessage("Non verranno cancellati inventario, prodotti o Log.").setPositiveButton("DISATTIVA",(d,w)->{PaperChemistryStore.clear(this);load();refreshPreview();toast("Sessione disattivata");}).setNegativeButton("ANNULLA",null).show());root.addView(clear,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,7,0,10));Button back=AssistantUi.secondaryButton(this,"← INDIETRO");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,4,0,0));}

    private void addComponent(LinearLayout root,String title,int request){root.addView(AssistantUi.section(this,title));LinearLayout c=AssistantUi.card(this);TextView name=AssistantUi.cardTitle(this,"NON CONFIGURATO");TextView origin=AssistantUi.secondary(this,"NON DOCUMENTATO");origin.setPadding(0,AssistantUi.dp(this,4),0,AssistantUi.dp(this,6));EditText dilution=AssistantUi.field(this,"Diluizione · se documentata viene proposta automaticamente");Button search=AssistantUi.secondaryButton(this,"CERCA NEL CATALOGO");String cats=request==PICK_DEV?"PAPER_DEVELOPER":request==PICK_STOP?"STOP_BATH":"FIXER";search.setOnClickListener(v->pick(request,"CERCA "+title,"Cerca prodotto...",cats,name.getText().toString()));c.addView(name);c.addView(origin);c.addView(dilution,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,2,0,6));c.addView(search,AssistantUi.margin(this,-1,AssistantUi.dp(this,46),0,0,0,0));root.addView(c);if(request==PICK_DEV){devName=name;devOrigin=origin;devDil=dilution;}else if(request==PICK_STOP){stopName=name;stopOrigin=origin;stopDil=dilution;}else{fixName=name;fixOrigin=origin;fixDil=dilution;}}
    private void pick(int request,String title,String hint,String categories,String query){Intent i=new Intent(this,SmartSearchActivity.class);i.putExtra(SmartSearchActivity.EXTRA_TITLE,title);i.putExtra(SmartSearchActivity.EXTRA_HINT,hint);i.putExtra(SmartSearchActivity.EXTRA_CATEGORIES,categories);i.putExtra(SmartSearchActivity.EXTRA_QUERY,"NON CONFIGURATO".equals(query)?"":query);i.putExtra(SmartSearchActivity.EXTRA_ALLOW_MANUAL,true);startActivityForResult(i,request);}

    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null)return;if(data.getBooleanExtra(SmartSearchActivity.RESULT_MANUAL,false)){toast("Puoi digitare manualmente il nome/diluizione nei dati sessione soltanto se il catalogo non contiene il prodotto.");return;}String raw=data.getStringExtra(SmartSearchActivity.RESULT_RECORD);if(raw==null)return;try{JSONObject r=new JSONObject(raw);if(request==PICK_PAPER){paperName.setText(r.optString("name",paperName.getText().toString()));refreshPreview();return;}boolean paper=request==PICK_DEV;String[] d=SmartCatalog.dilutions(r,paper);TextView n=request==PICK_DEV?devName:request==PICK_STOP?stopName:fixName;TextView o=request==PICK_DEV?devOrigin:request==PICK_STOP?stopOrigin:fixOrigin;EditText dil=request==PICK_DEV?devDil:request==PICK_STOP?stopDil:fixDil;n.setText(r.optString("name",""));o.setText(SmartCatalog.sourceDetail(r));if(d.length==1)dil.setText(d[0]);else if(d.length>1&&!contains(d,dil.getText().toString()))dil.setText(d[0]);refreshPreview();}catch(Exception e){toast("Record catalogo non leggibile");}}

    private void load(){PaperChemistryStore.Session x=PaperChemistryStore.load(this);paperName.setText(empty(x.paper)?PaperChemistryStore.PAPER_DEFAULT:x.paper);volume.setText(x.volumeMl>0?fmt(x.volumeMl):"");set(devName,x.developer,"NON CONFIGURATO");devDil.setText(x.developerDilution);devOrigin.setText(emptyOr(x.developerOrigin,"NON DOCUMENTATO"));set(stopName,x.stop,"NON CONFIGURATO");stopDil.setText(x.stopDilution);stopOrigin.setText(emptyOr(x.stopOrigin,"NON DOCUMENTATO"));set(fixName,x.fixer,"NON CONFIGURATO");fixDil.setText(x.fixerDilution);fixOrigin.setText(emptyOr(x.fixerOrigin,"NON DOCUMENTATO"));notes.setText(x.notes);}
    private PaperChemistryStore.Session current(){PaperChemistryStore.Session x=new PaperChemistryStore.Session();x.paper=paperName.getText().toString();x.volumeMl=parse(volume.getText().toString());x.developer=configured(devName);x.developerDilution=devDil.getText().toString().trim();x.developerOrigin=devOrigin.getText().toString();x.stop=configured(stopName);x.stopDilution=stopDil.getText().toString().trim();x.stopOrigin=stopOrigin.getText().toString();x.fixer=configured(fixName);x.fixerDilution=fixDil.getText().toString().trim();x.fixerOrigin=fixOrigin.getText().toString();x.notes=notes.getText().toString();return x;}
    private void saveSession(){PaperChemistryStore.Session x=current();if(!(x.volumeMl>0)){toast("Inserisci un volume di lavoro valido");return;}PaperChemistryStore.save(this,x);refreshPreview();toast("Sessione chimica carta attiva");}
    private void refreshPreview(){PaperChemistryStore.Session x=current();StringBuilder b=new StringBuilder("PREPARAZIONE\n");b.append("Volume per soluzione: ").append(x.volumeMl>0?fmt(x.volumeMl)+" ml":"NON DETERMINABILE").append("\n\n");mix(b,"Rivelatore",x.developer,x.developerDilution,x.volumeMl);mix(b,"Arresto",x.stop,x.stopDilution,x.volumeMl);mix(b,"Fissaggio",x.fixer,x.fixerDilution,x.volumeMl);b.append("\nEsposizione e trattamento chimico restano separati: nessun tempo STAMPA viene modificato.");preview.setText(b.toString());}
    private void mix(StringBuilder b,String label,String name,String dilution,double total){b.append(label).append(": ").append(empty(name)?"non configurato":name).append("\n");if(empty(name)){b.append("  NON DOCUMENTATO\n");return;}PaperChemistryStore.Mix m=PaperChemistryStore.calculate(dilution,total);if(m.known)b.append("  ").append(fmt(m.productMl)).append(" ml prodotto + ").append(fmt(m.waterMl)).append(" ml acqua = ").append(fmt(m.totalMl)).append(" ml\n");else b.append("  ").append(m.message).append(" · nessun valore inventato\n");}

    private static void set(TextView t,String v,String fallback){t.setText(empty(v)?fallback:v);}private static String configured(TextView t){String x=t.getText().toString();return "NON CONFIGURATO".equals(x)?"":x;}private static boolean contains(String[] a,String s){for(String x:a)if(x.equalsIgnoreCase(s))return true;return false;}private static boolean empty(String s){return s==null||s.trim().isEmpty();}private static String emptyOr(String s,String f){return empty(s)?f:s.trim();}private static double parse(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return Double.NaN;}}private static String fmt(double v){return Double.isNaN(v)?"NON DETERMINABILE":Math.abs(v-Math.rint(v))<.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
