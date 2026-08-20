package it.darkroom.timer.assistant.system;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

import it.darkroom.timer.assistant.data.AssistantDataSchema;

/** R9 information, provenance, offline catalog management and SAF backup/restore. */
public final class DataManagementActivity extends Activity {
    private static final int CREATE_BACKUP=9101,OPEN_BACKUP=9102;
    private int primary,muted,accent,card;
    private TextView versionBox,catalogBox;

    @Override protected void onCreate(Bundle s){super.onCreate(s);palette();buildUi();refresh();}
    private void palette(){boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);if(dark){primary=Color.rgb(255,42,42);muted=Color.rgb(145,34,34);accent=Color.rgb(255,42,42);card=Color.rgb(18,0,0);}else{primary=Color.rgb(238,240,242);muted=Color.rgb(145,151,158);accent=Color.rgb(197,54,58);card=Color.rgb(24,26,30);}}

    private void buildUi(){ScrollView sc=new ScrollView(this);sc.setFillViewport(true);sc.setBackgroundColor(Color.BLACK);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(18),dp(18),dp(28));sc.addView(root);
        TextView eye=text("DARKROOM ASSISTANT · 9/9",12,accent,true);eye.setGravity(Gravity.CENTER);root.addView(eye);TextView title=text("FONTI · OFFLINE · BACKUP",24,primary,true);title.setGravity(Gravity.CENTER);root.addView(title);
        versionBox=cardText("");root.addView(versionBox);catalogBox=cardText("");root.addView(catalogBox);

        Button source=button("SISTEMA FONTI");source.setOnClickListener(v->showSources());root.addView(source);
        Button update=button("CONTROLLA AGGIORNAMENTI DATI");update.setOnClickListener(v->{update.setEnabled(false);CatalogManager.checkForUpdates(this,(ok,msg)->{update.setEnabled(true);refresh();new AlertDialog.Builder(this).setTitle(ok?"CATALOGO DATI":"AGGIORNAMENTO NON APPLICATO").setMessage(msg).setPositiveButton("OK",null).show();});});root.addView(update);
        Button rollback=button("RIPRISTINA CATALOGO INTEGRATO");rollback.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("RIPRISTINARE IL CATALOGO INTEGRATO?").setMessage("Verrà eliminata solo l'eventuale copia dati aggiornata. Ricette, Log, inventario, attrezzatura e preferenze personali non vengono modificati.").setPositiveButton("RIPRISTINA",(d,w)->{CatalogManager.rollbackToBuiltin(this);refresh();toast("Catalogo integrato ripristinato");}).setNegativeButton("ANNULLA",null).show());root.addView(rollback);

        TextView offline=cardText("MODALITÀ OFFLINE\nTimer STAMPA, PROVINO, Split Grade, Nuovo sviluppo, calcoli, Ricette, Log, La mia chimica, La mia attrezzatura, Assistente operativo, chimica carta e fonti locali non richiedono Internet. La rete viene usata solo quando scegli esplicitamente di controllare aggiornamenti dati.");root.addView(offline);

        Button backup=button("BACKUP DATI");backup.setOnClickListener(v->chooseBackupDestination());root.addView(backup);
        Button restore=button("RIPRISTINA BACKUP");restore.setOnClickListener(v->chooseBackupFile());root.addView(restore);
        TextView note=cardText("BACKUP VERSIONATO\nInclude dati personali Assistant e preferenze rilevanti, compresi Log STAMPA e valori Split Grade persistenti. Non legge né esporta password, chiavi di firma o segreti GitHub. Il ripristino valida formato, versione e SHA-256 prima di proporre UNISCI o SOSTITUISCI DATI PERSONALI.");root.addView(note);
        Button back=button("← INDIETRO");back.setOnClickListener(v->finish());root.addView(back);setContentView(sc);}

    private void refresh(){versionBox.setText("VERSIONI\nApp: "+BackupEngine.APP_VERSION+"\nversionCode: "+BackupEngine.VERSION_CODE+"\nSchema database personale: "+AssistantDataSchema.VERSION+"\nCatalogo tecnico: "+CatalogManager.activeVersion(this));catalogBox.setText(CatalogManager.describe(this));}

    private void showSources(){String msg="Ogni dato tecnico rilevante distingue la propria origine:\n\n• "+DataProvenance.OFFICIAL+"\n• "+DataProvenance.SECONDARY+"\n• "+DataProvenance.INTERNAL_VERIFIED+"\n• "+DataProvenance.CALCULATION+"\n• "+DataProvenance.ADAPTATION+"\n• "+DataProvenance.PERSONAL+"\n• "+DataProvenance.UNDOCUMENTED+"\n\nNei risultati sviluppo il dato sorgente resta separato dalla regola applicata e dal risultato. Un calcolo o adattamento non viene presentato come frase direttamente contenuta nella fonte. Se la fonte manca, viene mostrato NON DOCUMENTATO.";new AlertDialog.Builder(this).setTitle("SISTEMA FONTI").setMessage(msg).setPositiveButton("CHIUDI",null).show();}

    private void chooseBackupDestination(){Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");i.putExtra(Intent.EXTRA_TITLE,"DarkroomTimer-backup-v1.json");startActivityForResult(i,CREATE_BACKUP);}
    private void chooseBackupFile(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");startActivityForResult(i,OPEN_BACKUP);}

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(resultCode!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();if(requestCode==CREATE_BACKUP)writeBackup(uri);else if(requestCode==OPEN_BACKUP)readBackup(uri);}

    private void writeBackup(Uri uri){try{String json=BackupEngine.exportJson(this);try(OutputStream out=getContentResolver().openOutputStream(uri,"w")){if(out==null)throw new Exception("stream di scrittura non disponibile");out.write(json.getBytes(StandardCharsets.UTF_8));out.flush();}toast("Backup creato e verificabile tramite SHA-256 interno");}catch(Exception ex){new AlertDialog.Builder(this).setTitle("BACKUP NON RIUSCITO").setMessage(ex.getMessage()).setPositiveButton("OK",null).show();}}
    private void readBackup(Uri uri){try{String json;try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)throw new Exception("stream di lettura non disponibile");json=readAll(in);}BackupEngine.Validation v=BackupEngine.validate(json);if(!v.ok){new AlertDialog.Builder(this).setTitle("BACKUP RIFIUTATO").setMessage(v.error+"\n\nI dati correnti non sono stati modificati.").setPositiveButton("OK",null).show();return;}showRestoreSummary(json,v.summary);}catch(Exception ex){new AlertDialog.Builder(this).setTitle("BACKUP RIFIUTATO").setMessage("Impossibile leggere il backup: "+ex.getMessage()+"\n\nI dati correnti non sono stati modificati.").setPositiveButton("OK",null).show();}}

    private void showRestoreSummary(String json,String summary){new AlertDialog.Builder(this).setTitle("BACKUP VALIDATO").setMessage(summary+"\n\nScegli la modalità. Il catalogo tecnico integrato non viene sostituito da un backup personale.").setPositiveButton("UNISCI",(d,w)->confirmRestore(json,BackupEngine.MODE_MERGE)).setNeutralButton("SOSTITUISCI DATI PERSONALI",(d,w)->confirmReplace(json)).setNegativeButton("ANNULLA",null).show();}
    private void confirmReplace(String json){new AlertDialog.Builder(this).setTitle("SOSTITUIRE I DATI PERSONALI?").setMessage("Questa operazione sostituisce i dati personali inclusi nel backup. Viene eseguita in transazione: in caso di errore il database precedente resta utilizzabile. Il catalogo tecnico dell'app non viene sostituito.").setPositiveButton("SOSTITUISCI",(d,w)->confirmRestore(json,BackupEngine.MODE_REPLACE)).setNegativeButton("ANNULLA",null).show();}
    private void confirmRestore(String json,String mode){try{BackupEngine.restore(this,json,mode);refresh();new AlertDialog.Builder(this).setTitle("RIPRISTINO COMPLETATO").setMessage(BackupEngine.MODE_MERGE.equals(mode)?"Dati uniti senza sovrascrivere le righe già esistenti.":"Dati personali sostituiti dal backup validato.").setPositiveButton("OK",null).show();}catch(Exception ex){new AlertDialog.Builder(this).setTitle("RIPRISTINO ANNULLATO").setMessage("Errore durante il restore: "+ex.getMessage()+"\n\nLa transazione è stata annullata; nessun ripristino parziale deve essere considerato valido.").setPositiveButton("OK",null).show();}}

    private static String readAll(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}
    private TextView cardText(String s){TextView t=text(s,12,primary,false);t.setPadding(dp(14),dp(12),dp(14),dp(12));t.setBackgroundColor(card);return t;}private TextView text(String s,float z,int c,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(primary);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return b;}private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
