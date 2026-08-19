package it.darkroom.timer.assistant.chemistry.inventory;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.search.SmartCatalog;
import it.darkroom.timer.assistant.search.SmartSearchActivity;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** Modern R5 inventory: technical catalog metadata and personal ownership data remain separate. */
public final class MyChemistryActivity extends Activity {
    private static final int PICK_PRODUCT=5210;
    private AssistantDatabase db;
    private LinearLayout list,host;

    @Override protected void onCreate(Bundle b){super.onCreate(b);db=new AssistantDatabase(this);build();}
    @Override protected void onResume(){super.onResume();refresh();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}

    private void build(){
        LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · INVENTARIO","LA MIA CHIMICA","Prima scegli il prodotto; poi inserisci soltanto i dati che appartengono a te.");
        Button add=AssistantUi.primaryButton(this,"AGGIUNGI PRODOTTO");add.setOnClickListener(v->openSearch());root.addView(add,AssistantUi.margin(this,-1,AssistantUi.dp(this,58),0,0,0,12));
        host=new LinearLayout(this);host.setOrientation(LinearLayout.VERTICAL);root.addView(host);
        root.addView(AssistantUi.section(this,"INVENTARIO"));list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);root.addView(list);
        Button back=AssistantUi.secondaryButton(this,"← ASSISTANT");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,14,0,0));refresh();
    }

    private void openSearch(){Intent i=new Intent(this,SmartSearchActivity.class);i.putExtra(SmartSearchActivity.EXTRA_TITLE,"CERCA UN PRODOTTO");i.putExtra(SmartSearchActivity.EXTRA_HINT,"Cerca un prodotto...");i.putExtra(SmartSearchActivity.EXTRA_CATEGORIES,"FILM_DEVELOPER,PAPER_DEVELOPER,STOP_BATH,FIXER,WETTING_AGENT,CHEMISTRY");i.putExtra(SmartSearchActivity.EXTRA_ALLOW_MANUAL,true);startActivityForResult(i,PICK_PRODUCT);}

    @Override protected void onActivityResult(int req,int result,Intent data){super.onActivityResult(req,result,data);if(req!=PICK_PRODUCT||result!=RESULT_OK||data==null)return;if(data.getBooleanExtra(SmartSearchActivity.RESULT_MANUAL,false)){showManualForm();return;}String raw=data.getStringExtra(SmartSearchActivity.RESULT_RECORD);if(raw!=null)try{showCatalogForm(new JSONObject(raw));}catch(Exception e){toast("Record catalogo non leggibile");}}

    private void showCatalogForm(JSONObject record){
        host.removeAllViews();JSONObject tech=SmartCatalog.technical(record);LinearLayout card=AssistantUi.card(this);card.addView(AssistantUi.cardTitle(this,record.optString("name","Prodotto")));
        TextView meta=AssistantUi.secondary(this,record.optString("manufacturer","")+" · "+category(record)+"\n"+SmartCatalog.sourceDetail(record));meta.setPadding(0,AssistantUi.dp(this,5),0,AssistantUi.dp(this,8));card.addView(meta);
        String[] dils=SmartCatalog.dilutions(record,false);if(dils.length==0)dils=SmartCatalog.dilutions(record,true);final String[] documentedDils=dils;card.addView(AssistantUi.badge(this,documentedDils.length==0?"DILUIZIONE NON DOCUMENTATA":"DILUIZIONI · "+join(documentedDils),documentedDils.length>0));host.addView(card,AssistantUi.margin(this,-1,-2,0,0,0,8));
        host.addView(AssistantUi.section(this,"DATI PERSONALI"));EditText amount=AssistantUi.numberField(this,"Quantità posseduta");EditText unit=AssistantUi.field(this,"Unità · es. ml o g");unit.setText("polvere".equalsIgnoreCase(tech.optString("physicalState"))?"g":"ml");EditText purchase=AssistantUi.field(this,"Data acquisto · opzionale");EditText opened=AssistantUi.field(this,"Data apertura · opzionale");EditText storage=AssistantUi.field(this,"Posizione / conservazione · opzionale");EditText notes=AssistantUi.field(this,"Note personali · opzionale");for(EditText e:new EditText[]{amount,unit,purchase,opened,storage,notes})host.addView(e,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,7));
        Button save=AssistantUi.primaryButton(this,"AGGIUNGI ALLA MIA CHIMICA");save.setOnClickListener(v->{double q=parse(amount.getText().toString());if(!(q>0)){toast("Inserisci una quantità maggiore di zero: un valore sconosciuto non viene salvato come 0.");return;}AssistantDatabase.ChemicalItem x=new AssistantDatabase.ChemicalItem();x.sourceType=AssistantDatabase.SOURCE_CATALOG;x.sourceProductKey=record.optString("id","");x.manufacturer=record.optString("manufacturer","");x.name=record.optString("name","");x.category=category(record);x.physicalState=tech.optString("physicalState","NON DOCUMENTATO");x.solutionType="NON DOCUMENTATO";x.initialAmount=q;x.remainingAmount=q;x.unit=unit.getText().toString().trim();x.purchaseDate=purchase.getText().toString().trim();x.openDate=opened.getText().toString().trim();x.storage=storage.getText().toString().trim();x.notes=notes.getText().toString().trim();x.documentedDilutions=join(documentedDils);JSONObject src=SmartCatalog.source(record);x.sourceName=src.optString("title","Catalogo verificato");x.dataType=tech.optString("dataType","DATI TECNICI / FONTE");db.saveChemical(x);host.removeAllViews();refresh();toast("Prodotto aggiunto");});host.addView(save,AssistantUi.margin(this,-1,AssistantUi.dp(this,56),0,5,0,10));
        Button cancel=AssistantUi.ghostButton(this,"ANNULLA");cancel.setOnClickListener(v->host.removeAllViews());host.addView(cancel,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,10));
    }

    private void showManualForm(){
        host.removeAllViews();host.addView(AssistantUi.emptyState(this,"PRODOTTO PERSONALE","Questi dati saranno marcati come inseriti dall'utente, mai come fonte tecnica."));EditText maker=AssistantUi.field(this,"Produttore");EditText name=AssistantUi.field(this,"Nome prodotto");EditText category=AssistantUi.field(this,"Categoria");EditText amount=AssistantUi.numberField(this,"Quantità posseduta");EditText unit=AssistantUi.field(this,"Unità · ml / g / litri");EditText dilution=AssistantUi.field(this,"Diluizione personale · opzionale");EditText notes=AssistantUi.field(this,"Note personali");for(EditText e:new EditText[]{maker,name,category,amount,unit,dilution,notes})host.addView(e,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,7,0,0));
        Button save=AssistantUi.primaryButton(this,"SALVA PRODOTTO PERSONALE");save.setOnClickListener(v->{String n=name.getText().toString().trim();double q=parse(amount.getText().toString());if(n.isEmpty()||!(q>0)){toast("Nome e quantità positiva sono necessari");return;}AssistantDatabase.ChemicalItem x=new AssistantDatabase.ChemicalItem();x.sourceType=AssistantDatabase.SOURCE_USER;x.manufacturer=maker.getText().toString().trim();x.name=n;x.category=category.getText().toString().trim();x.physicalState="NON DOCUMENTATO";x.solutionType="NON DOCUMENTATO";x.initialAmount=q;x.remainingAmount=q;x.unit=unit.getText().toString().trim();x.personalDilution=dilution.getText().toString().trim();x.notes=notes.getText().toString().trim();x.dataType="DATO PERSONALE";x.sourceName="Utente";db.saveChemical(x);host.removeAllViews();refresh();toast("Prodotto personale salvato");});host.addView(save,AssistantUi.margin(this,-1,AssistantUi.dp(this,56),0,10,0,10));
    }

    private void refresh(){if(list==null)return;list.removeAllViews();List<AssistantDatabase.ChemicalItem> items=db.listChemicals(true);if(items.isEmpty()){list.addView(AssistantUi.emptyState(this,"INVENTARIO VUOTO","Tocca AGGIUNGI PRODOTTO e inizia a scrivere, per esempio “foma un”."));return;}for(AssistantDatabase.ChemicalItem x:items){String origin=AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType)?"CATALOGO VERIFICATO":"DATO PERSONALE";Button row=AssistantUi.resultRow(this,x.name,fmtQty(x.remainingAmount,x.unit)+" · "+x.status().toUpperCase(Locale.ITALY),origin);row.setOnClickListener(v->detail(x.id));list.addView(row,AssistantUi.margin(this,-1,AssistantUi.dp(this,76),0,0,0,7));}}

    private void detail(long id){AssistantDatabase.ChemicalItem x=db.getChemical(id);if(x==null)return;host.removeAllViews();LinearLayout c=AssistantUi.card(this);c.addView(AssistantUi.cardTitle(this,x.name));String technical=(AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType)?"DATI TECNICI / FONTE\nProduttore: "+empty(x.manufacturer)+"\nDiluizioni documentate: "+empty(x.documentedDilutions)+"\nFonte: "+empty(x.sourceName):"DATO PERSONALE · nessuna fonte tecnica associata");c.addView(AssistantUi.secondary(this,technical));c.addView(AssistantUi.body(this,"\nDATI PERSONALI\nResiduo: "+fmtQty(x.remainingAmount,x.unit)+"\nApertura: "+empty(x.openDate)+"\nConservazione: "+empty(x.storage)+"\nNote: "+empty(x.notes)));host.addView(c);
        Button qty=AssistantUi.secondaryButton(this,"AGGIORNA QUANTITÀ");qty.setOnClickListener(v->remainingForm(id));host.addView(qty,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,8,0,0));Button hist=AssistantUi.secondaryButton(this,"STORICO UTILIZZI");hist.setOnClickListener(v->history(id));host.addView(hist,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,6,0,0));Button archive=AssistantUi.ghostButton(this,x.archived?"RIPRISTINA":"ARCHIVIA");archive.setOnClickListener(v->confirmArchive(id));host.addView(archive,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,6,0,10));}

    private void remainingForm(long id){AssistantDatabase.ChemicalItem x=db.getChemical(id);if(x==null)return;host.removeAllViews();host.addView(AssistantUi.section(this,"QUANTITÀ RESIDUA"));EditText q=AssistantUi.numberField(this,"Quantità residua "+x.unit);q.setText(fmt(x.remainingAmount));host.addView(q,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,7));Button save=AssistantUi.primaryButton(this,"SALVA");save.setOnClickListener(v->{double n=parse(q.getText().toString());if(n<0||Double.isNaN(n)){toast("Quantità non valida");return;}x.remainingAmount=n;db.updateChemical(x);host.removeAllViews();refresh();});host.addView(save,AssistantUi.margin(this,-1,AssistantUi.dp(this,54),0,0,0,10));}
    private void history(long id){host.removeAllViews();List<AssistantDatabase.ChemicalUsage> rows=db.listChemicalUsage(id);if(rows.isEmpty()){host.addView(AssistantUi.emptyState(this,"NESSUN UTILIZZO REGISTRATO","Gli utilizzi vengono aggiunti soltanto dopo conferma esplicita."));return;}for(AssistantDatabase.ChemicalUsage u:rows){LinearLayout c=AssistantUi.card(this);c.addView(AssistantUi.cardTitle(this,date(u.createdAt)));c.addView(AssistantUi.body(this,empty(u.film)+" · "+empty(u.format)+" · "+u.rolls+" rulli\nUsati: "+fmtQty(u.quantityUsed,u.unit)+" · Residuo: "+fmtQty(u.remainingAfter,u.unit)+(u.note.isEmpty()?"":"\n"+u.note)));host.addView(c,AssistantUi.margin(this,-1,-2,0,0,0,7));}}
    private void confirmArchive(long id){AssistantDatabase.ChemicalItem x=db.getChemical(id);if(x==null)return;new AlertDialog.Builder(this).setTitle(x.archived?"Ripristinare prodotto?":"Archiviare prodotto?").setMessage("Questa è un'azione sul tuo inventario personale; i dati tecnici del catalogo non vengono modificati.").setPositiveButton(x.archived?"RIPRISTINA":"ARCHIVIA",(d,w)->{x.archived=!x.archived;db.updateChemical(x);host.removeAllViews();refresh();}).setNegativeButton("ANNULLA",null).show();}

    private static String category(JSONObject r){JSONArray a=r.optJSONArray("categories");String c=a==null?"":a.optString(0,"");if("FILM_DEVELOPER".equals(c))return "rivelatore pellicola";if("PAPER_DEVELOPER".equals(c))return "rivelatore carta";if("STOP_BATH".equals(c))return "arresto";if("FIXER".equals(c))return "fissaggio";if("WETTING_AGENT".equals(c))return "imbibente";return c.isEmpty()?"altro":c.toLowerCase(Locale.ITALY);}
    private static String join(String[] a){StringBuilder b=new StringBuilder();for(String s:a){if(s==null||s.isEmpty())continue;if(b.length()>0)b.append(", ");b.append(s);}return b.toString();}
    private static String empty(String s){return s==null||s.trim().isEmpty()?"—":s;}private static double parse(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return Double.NaN;}}private static String fmt(double v){return Math.abs(v-Math.rint(v))<.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}private static String fmtQty(double v,String u){return fmt(v)+" "+empty(u);}private static String date(long ms){return DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
