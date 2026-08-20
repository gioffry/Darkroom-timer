package it.darkroom.timer.assistant.system;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

import it.darkroom.timer.assistant.data.AssistantDataSchema;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** R9 system screen restyled for v0.12.1; destructive restore confirmations remain modal. */
public final class DataManagementActivity extends Activity {
    private static final int CREATE_BACKUP=9101,OPEN_BACKUP=9102;
    private TextView versionBox,catalogBox;
    private LinearLayout infoHost;
    @Override protected void onCreate(Bundle s){super.onCreate(s);buildUi();refresh();}

    private void buildUi(){LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · 9/9","FONTI · OFFLINE · BACKUP","Catalogo tecnico, provenienza e dati personali rimangono livelli separati.");versionBox=cardText("");root.addView(versionBox,AssistantUi.margin(this,-1,-2,0,0,0,8));catalogBox=cardText("");root.addView(catalogBox,AssistantUi.margin(this,-1,-2,0,0,0,8));
        infoHost=new LinearLayout(this);infoHost.setOrientation(LinearLayout.VERTICAL);root.addView(infoHost);
        Button source=AssistantUi.secondaryButton(this,"SISTEMA FONTI");source.setOnClickListener(v->showSourcesInline());root.addView(source,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,6,0,0));
        Button update=AssistantUi.primaryButton(this,"CONTROLLA AGGIORNAMENTI DATI");update.setOnClickListener(v->{update.setEnabled(false);catalogBox.setText("Controllo catalogo online…\nIl catalogo locale resta utilizzabile durante la verifica.");CatalogManager.checkForUpdates(this,(ok,msg)->{update.setEnabled(true);refresh();infoHost.removeAllViews();infoHost.addView(AssistantUi.emptyState(this,ok?"CATALOGO DATI":"AGGIORNAMENTO NON APPLICATO",msg));});});root.addView(update,AssistantUi.margin(this,-1,AssistantUi.dp(this,54),0,7,0,0));
        Button rollback=AssistantUi.ghostButton(this,"RIPRISTINA CATALOGO INTEGRATO");rollback.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Ripristinare il catalogo integrato?").setMessage("Verrà rimossa soltanto la copia tecnica aggiornata. Ricette, Log, inventario, attrezzatura e preferenze personali non vengono modificati.").setPositiveButton("RIPRISTINA",(d,w)->{CatalogManager.rollbackToBuiltin(this);refresh();toast("Catalogo integrato ripristinato");}).setNegativeButton("ANNULLA",null).show());root.addView(rollback,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,6,0,10));
        root.addView(cardText("OFFLINE FIRST\nTimer STAMPA, PROVINO, Split Grade, Nuovo sviluppo, calcoli, Ricette, Log, inventario, attrezzatura, Assistente operativo e chimica carta funzionano con dati locali. La rete arricchisce Smart Search e aggiornamenti, ma non è requisito operativo."),AssistantUi.margin(this,-1,-2,0,0,0,8));
        Button backup=AssistantUi.secondaryButton(this,"BACKUP DATI");backup.setOnClickListener(v->chooseBackupDestination());root.addView(backup,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,8,0,0));Button restore=AssistantUi.secondaryButton(this,"RIPRISTINA BACKUP");restore.setOnClickListener(v->chooseBackupFile());root.addView(restore,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,6,0,0));root.addView(cardText("BACKUP VERSIONATO\nComprende i dati personali Assistant e le preferenze rilevanti. Non esporta password, chiavi di firma o segreti. La cache del catalogo tecnico non sostituisce mai i dati personali."),AssistantUi.margin(this,-1,-2,0,8,0,8));Button back=AssistantUi.secondaryButton(this,"← INDIETRO");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,8,0,0));}

    private void refresh(){versionBox.setText("VERSIONI\nApp: "+BackupEngine.APP_VERSION+"\nversionCode: "+BackupEngine.VERSION_CODE+"\nSchema database personale: "+AssistantDataSchema.VERSION+"\nCatalogo tecnico: "+CatalogManager.activeVersion(this));catalogBox.setText(CatalogManager.describe(this));}
    private void showSourcesInline(){infoHost.removeAllViews();String text="FONTE UFFICIALE · documentazione del produttore\nFONTE SECONDARIA · fonte tecnica affidabile dichiarata\nDATO INTERNO VERIFICATO · dato consolidato e preservato\nCALCOLO · valore derivato, mai spacciato per sorgente\nADATTAMENTO · regola applicata a un dato sorgente\nDATO PERSONALE · inserito dall'utente\nNON DOCUMENTATO · nessun valore inventato";LinearLayout c=AssistantUi.card(this);c.addView(AssistantUi.cardTitle(this,"PROVENIENZA DEI DATI"));c.addView(AssistantUi.body(this,text));infoHost.addView(c,AssistantUi.margin(this,-1,-2,0,0,0,8));}

    private void chooseBackupDestination(){Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");i.putExtra(Intent.EXTRA_TITLE,"DarkroomTimer-backup-v1.json");startActivityForResult(i,CREATE_BACKUP);}
    private void chooseBackupFile(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");startActivityForResult(i,OPEN_BACKUP);}
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(resultCode!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();if(requestCode==CREATE_BACKUP)writeBackup(uri);else if(requestCode==OPEN_BACKUP)readBackup(uri);}
    private void writeBackup(Uri uri){try{String json=BackupEngine.exportJson(this);try(OutputStream out=getContentResolver().openOutputStream(uri,"w")){if(out==null)throw new Exception("stream di scrittura non disponibile");out.write(json.getBytes(StandardCharsets.UTF_8));out.flush();}toast("Backup creato e validabile tramite SHA-256 interno");}catch(Exception ex){toast("Backup non riuscito: "+ex.getMessage());}}
    private void readBackup(Uri uri){try{String json;try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)throw new Exception("stream di lettura non disponibile");json=readAll(in);}BackupEngine.Validation v=BackupEngine.validate(json);if(!v.ok){toast("Backup rifiutato: "+v.error);return;}showRestoreSummary(json,v.summary);}catch(Exception ex){toast("Backup rifiutato: "+ex.getMessage());}}
    private void showRestoreSummary(String json,String summary){new AlertDialog.Builder(this).setTitle("BACKUP VALIDATO").setMessage(summary+"\n\nScegli la modalità. Il catalogo tecnico non viene sostituito da un backup personale.").setPositiveButton("UNISCI",(d,w)->confirmRestore(json,BackupEngine.MODE_MERGE)).setNeutralButton("SOSTITUISCI DATI PERSONALI",(d,w)->confirmReplace(json)).setNegativeButton("ANNULLA",null).show();}
    private void confirmReplace(String json){new AlertDialog.Builder(this).setTitle("Sostituire i dati personali?").setMessage("Operazione transazionale: in caso di errore il database precedente resta utilizzabile.").setPositiveButton("SOSTITUISCI",(d,w)->confirmRestore(json,BackupEngine.MODE_REPLACE)).setNegativeButton("ANNULLA",null).show();}
    private void confirmRestore(String json,String mode){try{BackupEngine.restore(this,json,mode);refresh();toast(BackupEngine.MODE_MERGE.equals(mode)?"Dati uniti":"Dati personali ripristinati");}catch(Exception ex){toast("Ripristino annullato: "+ex.getMessage());}}
    private TextView cardText(String s){TextView t=AssistantUi.body(this,s);t.setPadding(AssistantUi.dp(this,14),AssistantUi.dp(this,12),AssistantUi.dp(this,14),AssistantUi.dp(this,12));t.setBackground(AssistantUi.round(this,AssistantUi.palette(this).card,11,1,AssistantUi.palette(this).border));return t;}
    private static String readAll(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
