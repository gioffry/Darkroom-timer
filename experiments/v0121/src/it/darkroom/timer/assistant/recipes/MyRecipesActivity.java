package it.darkroom.timer.assistant.recipes;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.development.DevelopmentCatalog;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** R4 recipes with progressive disclosure: routine viewing/editing is inline, not dialog-driven. */
public final class MyRecipesActivity extends Activity {
    private AssistantDatabase db;
    private LinearLayout list,host;

    @Override protected void onCreate(Bundle b){super.onCreate(b);db=new AssistantDatabase(this);build();}
    @Override protected void onResume(){super.onResume();refresh();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}

    private void build(){
        LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · RICETTE","LE MIE RICETTE","Ricetta personale e dato originale rimangono separati e leggibili a richiesta.");
        host=new LinearLayout(this);host.setOrientation(LinearLayout.VERTICAL);root.addView(host);
        root.addView(AssistantUi.section(this,"RICETTE SALVATE"));list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);root.addView(list);
        Button back=AssistantUi.secondaryButton(this,"← ASSISTANT");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,14,0,0));
        refresh();
    }

    private void refresh(){
        if(list==null)return;list.removeAllViews();List<AssistantDatabase.PersonalRecipe> rows=db.listRecipes();
        if(rows.isEmpty()){list.addView(AssistantUi.emptyState(this,"NESSUNA RICETTA PERSONALE","Le ricette create dal Log o da Nuovo sviluppo appariranno qui."));return;}
        for(AssistantDatabase.PersonalRecipe r:rows){
            String sub=r.source.developer+" "+r.source.dilution+" · "+fmt(r.personalTemp)+" °C · "+DevelopmentCatalog.formatTime(r.personalSeconds);
            String origin=(r.favorite?"★ PREFERITA · ":"")+"DATO PERSONALE";
            Button row=AssistantUi.resultRow(this,r.source.film+" · "+r.source.format+" · ISO "+r.source.exposedIso,sub,origin);
            row.setOnClickListener(v->showRecipe(r.id));list.addView(row,AssistantUi.margin(this,-1,AssistantUi.dp(this,82),0,0,0,7));
        }
    }

    private void showRecipe(long id){
        AssistantDatabase.PersonalRecipe r=db.getRecipe(id);if(r==null)return;host.removeAllViews();
        LinearLayout card=AssistantUi.card(this);card.addView(AssistantUi.cardTitle(this,r.source.film+" · "+r.source.developer));
        card.addView(AssistantUi.body(this,"MIA RICETTA\n"+DevelopmentCatalog.formatTime(r.personalSeconds)+" @ "+fmt(r.personalTemp)+" °C"+(r.favorite?" · ★ PREFERITA":"")+"\n\nDifferenza dal tempo sorgente: "+delta(r.personalSeconds-r.source.originalSeconds)+"\nNota: "+empty(r.note)+"\nModificato: "+date(r.updatedAt)));
        card.addView(AssistantUi.secondary(this,"\nFONTE ORIGINALE DISPONIBILE · tocca VEDI ORIGINALE per i dettagli"));host.addView(card,AssistantUi.margin(this,-1,-2,0,0,0,8));
        Button edit=AssistantUi.primaryButton(this,"MODIFICA RICETTA");edit.setOnClickListener(v->editInline(id));host.addView(edit,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,6));
        Button fav=AssistantUi.secondaryButton(this,r.favorite?"RIMUOVI PREFERITA":"IMPOSTA PREFERITA");fav.setOnClickListener(v->{db.setFavorite(id,!r.favorite);refresh();showRecipe(id);});host.addView(fav,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,6));
        Button original=AssistantUi.secondaryButton(this,"VEDI ORIGINALE");original.setOnClickListener(v->showOriginalInline(id));host.addView(original,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,6));
        Button reset=AssistantUi.ghostButton(this,"RIPRISTINA ORIGINALE");reset.setOnClickListener(v->confirmReset(id));host.addView(reset,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,6));
        Button delete=AssistantUi.ghostButton(this,"ELIMINA RICETTA PERSONALE");delete.setOnClickListener(v->confirmDelete(id));host.addView(delete,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,12));
    }

    private void showOriginalInline(long id){
        AssistantDatabase.PersonalRecipe r=db.getRecipe(id);if(r==null)return;host.removeAllViews();
        LinearLayout card=AssistantUi.card(this);card.addView(AssistantUi.cardTitle(this,"ORIGINALE FONTE"));
        card.addView(AssistantUi.body(this,r.source.film+" · "+r.source.format+" · ISO "+r.source.exposedIso+"\n"+r.source.developer+" "+r.source.dilution+"\n"+fmt(r.source.originalTemp)+" °C · JOBO CPE2 · rotazione continua\n\nTempo originale: "+DevelopmentCatalog.formatTime(r.source.originalSeconds)));
        card.addView(AssistantUi.secondary(this,"\nFonte: "+empty(r.source.sourceName)+"\nTipo dato: "+empty(r.source.dataType)+"\nDato sorgente: "+empty(r.source.sourceData)+"\n"+empty(r.source.calculation)));
        host.addView(card);Button back=AssistantUi.secondaryButton(this,"← TORNA ALLA RICETTA");back.setOnClickListener(v->showRecipe(id));host.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,8,0,10));
    }

    private void editInline(long id){
        AssistantDatabase.PersonalRecipe r=db.getRecipe(id);if(r==null)return;host.removeAllViews();host.addView(AssistantUi.section(this,"MODIFICA MIA RICETTA"));
        EditText time=AssistantUi.field(this,"Tempo m:ss");time.setText(timeText(r.personalSeconds));
        EditText temp=AssistantUi.numberField(this,"Temperatura °C");temp.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);temp.setText(fmt(r.personalTemp));
        EditText note=AssistantUi.field(this,"Nota personale");note.setText(r.note);
        for(EditText e:new EditText[]{time,temp,note})host.addView(e,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,7));
        Button save=AssistantUi.primaryButton(this,"SALVA MODIFICHE");save.setOnClickListener(v->{int sec=parseTime(time.getText().toString());double tc=parseDouble(temp.getText().toString());if(sec<=0||Double.isNaN(tc)){toast("Tempo o temperatura non validi");return;}db.updateRecipe(id,sec,tc,note.getText().toString(),r.favorite);refresh();showRecipe(id);});host.addView(save,AssistantUi.margin(this,-1,AssistantUi.dp(this,54),0,4,0,6));
        Button cancel=AssistantUi.secondaryButton(this,"ANNULLA");cancel.setOnClickListener(v->showRecipe(id));host.addView(cancel,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,10));
    }

    private void confirmReset(long id){new AlertDialog.Builder(this).setTitle("Ripristina originale?").setMessage("Le modifiche personali di tempo, temperatura e nota verranno azzerate. Il dato sorgente resta intatto.").setPositiveButton("RIPRISTINA",(d,w)->{db.resetOriginal(id);refresh();showRecipe(id);}).setNegativeButton("ANNULLA",null).show();}
    private void confirmDelete(long id){new AlertDialog.Builder(this).setTitle("Eliminare la ricetta personale?").setMessage("Il dato originale della fonte non viene modificato.").setPositiveButton("ELIMINA",(d,w)->{db.deleteRecipe(id);host.removeAllViews();refresh();}).setNegativeButton("ANNULLA",null).show();}

    public static int parseTime(String s){try{String x=s.trim();if(x.contains(":")){String[] p=x.split(":");return Integer.parseInt(p[0].trim())*60+Integer.parseInt(p[1].trim());}return Integer.parseInt(x);}catch(Exception e){return -1;}}
    private static double parseDouble(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return Double.NaN;}}
    private static String timeText(int sec){return String.format(Locale.ITALY,"%d:%02d",sec/60,sec%60);}private static String fmt(double v){return String.format(Locale.ITALY,"%.1f",v);}private static String delta(int d){return(d>=0?"+":"")+d+" s";}private static String date(long ms){return DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}private static String empty(String s){return s==null||s.trim().isEmpty()?"—":s;}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
