package it.darkroom.timer.assistant.log;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.development.DevelopmentCatalog;
import it.darkroom.timer.assistant.development.NewDevelopmentActivity;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** Development Log with inline details/actions/comparison; no routine AlertDialog navigation. */
public final class DevelopmentLogActivity extends Activity {
    private AssistantDatabase db;
    private LinearLayout list,host;

    @Override protected void onCreate(Bundle b){super.onCreate(b);db=new AssistantDatabase(this);build();}
    @Override protected void onResume(){super.onResume();refresh();}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}

    private void build(){
        LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · LOG","LOG SVILUPPI","Solo sviluppi salvati esplicitamente. Tocca una voce per dettagli e azioni.");
        host=new LinearLayout(this);host.setOrientation(LinearLayout.VERTICAL);root.addView(host);
        root.addView(AssistantUi.section(this,"SVILUPPI SALVATI"));list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);root.addView(list);
        Button back=AssistantUi.secondaryButton(this,"← ASSISTANT");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,14,0,0));refresh();
    }

    private void refresh(){
        if(list==null)return;list.removeAllViews();List<AssistantDatabase.LogEntry> logs=db.listLogs();
        if(logs.isEmpty()){list.addView(AssistantUi.emptyState(this,"NESSUNO SVILUPPO NEL LOG","Il salvataggio resta esplicito al termine dello sviluppo."));return;}
        for(AssistantDatabase.LogEntry l:logs){String rating=l.rating>0?" · "+stars(l.rating):"";Button row=AssistantUi.resultRow(this,l.source.film+" · "+l.source.format+" · ISO "+l.source.exposedIso,l.source.developer+" "+l.source.dilution+" · "+DevelopmentCatalog.formatTime(l.actualSeconds)+rating,date(l.createdAt));row.setOnClickListener(v->detail(l.id));list.addView(row,AssistantUi.margin(this,-1,AssistantUi.dp(this,82),0,0,0,7));}
    }

    private void detail(long id){
        AssistantDatabase.LogEntry l=db.getLog(id);if(l==null)return;host.removeAllViews();
        String product=l.productKnown?fmtMl(l.productMl)+" ml prodotto/stock":"Quantità prodotto: NON DETERMINATA";
        String water=l.waterKnown?fmtMl(l.waterMl)+" ml acqua":"Quantità acqua: NON DETERMINATA";
        LinearLayout card=AssistantUi.card(this);card.addView(AssistantUi.cardTitle(this,l.source.film+" · "+l.source.developer));
        card.addView(AssistantUi.body(this,date(l.createdAt)+"\n"+l.source.format+" · ISO "+l.source.exposedIso+" · "+fmt(l.actualTemp)+" °C\n\nTEMPO EFFETTIVO · "+DevelopmentCatalog.formatTime(l.actualSeconds)+"\nOrigine tempo · "+empty(l.timeOrigin)+"\n\nPREPARA\n"+product+"\n"+water+"\n"+fmtMl(l.volumeMl)+" ml totale · "+l.rolls+" rulli"));
        card.addView(AssistantUi.secondary(this,"\nCAPACITÀ / PROVENIENZA\n"+empty(l.capacityMessage)+"\nFonte originaria: "+empty(l.source.sourceName)+"\nTempo sorgente: "+DevelopmentCatalog.formatTime(l.source.originalSeconds)+" @ "+fmt(l.source.originalTemp)+" °C\n\nValutazione: "+(l.rating>0?stars(l.rating):"—")+"\nNote: "+empty(l.notes)));
        host.addView(card,AssistantUi.margin(this,-1,-2,0,0,0,8));
        Button repeat=AssistantUi.primaryButton(this,"RIPETI SVILUPPO");repeat.setOnClickListener(v->repeat(id));host.addView(repeat,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,6));
        Button recipe=AssistantUi.secondaryButton(this,"USA COME MIA RICETTA");recipe.setOnClickListener(v->makeRecipe(id,false));host.addView(recipe,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,6));
        Button fav=AssistantUi.secondaryButton(this,"IMPOSTA COME RICETTA PREFERITA");fav.setOnClickListener(v->makeRecipe(id,true));host.addView(fav,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,6));
        Button compare=AssistantUi.secondaryButton(this,"CONFRONTA SVILUPPI");compare.setOnClickListener(v->compareInline(id));host.addView(compare,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,0,0,12));
    }

    private void makeRecipe(long id,boolean favorite){long r=db.recipeFromLog(id,favorite);if(r>0)toast(favorite?"Impostata come ricetta preferita":"Ricetta personale creata");}
    private void repeat(long id){AssistantDatabase.LogEntry l=db.getLog(id);if(l==null)return;Intent i=new Intent(this,NewDevelopmentActivity.class);i.putExtra("prefillFilm",l.source.film);i.putExtra("prefillFormat",l.source.format);i.putExtra("prefillExposedIso",l.source.exposedIso);i.putExtra("prefillDeveloper",l.source.developer);i.putExtra("prefillDilution",l.source.dilution);i.putExtra("prefillTemperature",l.actualTemp);i.putExtra("prefillRolls",l.rolls);i.putExtra("prefillVolume",l.volumeMl);i.putExtra("repeatTimeSeconds",l.actualSeconds);i.putExtra("repeatOrigin","RICETTA DAL LOG");startActivity(i);}

    private void compareInline(long id){
        AssistantDatabase.LogEntry current=db.getLog(id);if(current==null)return;host.removeAllViews();host.addView(AssistantUi.section(this,"CONFRONTA SVILUPPI"));
        List<AssistantDatabase.LogEntry> rows=db.logsForCombo(current.comboKey());if(rows.isEmpty()){host.addView(AssistantUi.emptyState(this,"NESSUN CONFRONTO DISPONIBILE","Non ci sono altri sviluppi con la stessa combinazione."));return;}
        for(int x=rows.size()-1;x>=0;x--){AssistantDatabase.LogEntry l=rows.get(x);LinearLayout c=AssistantUi.card(this);c.addView(AssistantUi.cardTitle(this,dateShort(l.createdAt)+" · "+DevelopmentCatalog.formatTime(l.actualSeconds)));c.addView(AssistantUi.body(this,fmt(l.actualTemp)+" °C · "+(l.rating>0?stars(l.rating):"nessuna valutazione")));if(!l.notes.isEmpty())c.addView(AssistantUi.secondary(this,l.notes));host.addView(c,AssistantUi.margin(this,-1,-2,0,0,0,7));}
        Button back=AssistantUi.secondaryButton(this,"← TORNA ALLO SVILUPPO");back.setOnClickListener(v->detail(id));host.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,48),0,8,0,10));
    }

    private static String stars(int n){StringBuilder b=new StringBuilder();for(int i=0;i<n;i++)b.append('★');return b.toString();}
    private static String date(long ms){return DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}private static String dateShort(long ms){return DateFormat.getDateInstance(DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}private static String fmt(double v){return String.format(Locale.ITALY,"%.1f",v);}private static String fmtMl(double v){return Math.abs(v-Math.rint(v))<.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}private static String empty(String s){return s==null||s.trim().isEmpty()?"—":s;}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
}
