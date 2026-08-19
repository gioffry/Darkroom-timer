package it.darkroom.timer.assistant.log;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.development.DevelopmentCatalog;
import it.darkroom.timer.assistant.development.NewDevelopmentActivity;

/** R5/R6 keeps the R4 Log behavior and represents unknown chemistry quantities explicitly. */
public final class DevelopmentLogActivity extends Activity {
    private AssistantDatabase db;
    private LinearLayout list;
    private int primary, muted, accent;

    @Override protected void onCreate(Bundle b){ super.onCreate(b); palette(); db=new AssistantDatabase(this); build(); }
    @Override protected void onResume(){ super.onResume(); refresh(); }
    @Override protected void onDestroy(){ if(db!=null)db.close(); super.onDestroy(); }

    private void palette(){ boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false); primary=dark?Color.rgb(255,42,42):Color.rgb(238,240,242); muted=dark?Color.rgb(145,34,34):Color.rgb(145,151,158); accent=dark?Color.rgb(255,42,42):Color.rgb(197,54,58); }
    private void build(){ ScrollView s=new ScrollView(this); s.setBackgroundColor(Color.BLACK); LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(16),dp(18),dp(28)); s.addView(root); TextView t=text("LOG SVILUPPI",25,primary,true);t.setGravity(Gravity.CENTER);root.addView(t); TextView sub=text("Solo sviluppi salvati esplicitamente",12,muted,false);sub.setGravity(Gravity.CENTER);sub.setPadding(0,dp(4),0,dp(14));root.addView(sub); list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);root.addView(list); Button back=button("← ASSISTANT");back.setOnClickListener(v->finish());root.addView(back);setContentView(s);refresh(); }
    private void refresh(){ if(list==null)return; list.removeAllViews(); List<AssistantDatabase.LogEntry> logs=db.listLogs(); if(logs.isEmpty()){TextView e=text("Nessuno sviluppo salvato nel Log.",14,muted,false);e.setPadding(0,dp(20),0,dp(20));list.addView(e);return;} for(AssistantDatabase.LogEntry l:logs){String stars=stars(l.rating); String label=date(l.createdAt)+"\n"+l.source.film+" · "+l.source.format+" · ISO "+l.source.exposedIso+"\n"+l.source.developer+" "+l.source.dilution+" · "+fmt(l.actualTemp)+" °C\n"+DevelopmentCatalog.formatTime(l.actualSeconds)+(stars.isEmpty()?"":" · "+stars); Button b=button(label);b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);b.setOnClickListener(v->detail(l.id));list.addView(b,margin(-1,dp(108),0,0,0,dp(9)));} }

    private void detail(long id){
        AssistantDatabase.LogEntry l=db.getLog(id); if(l==null)return;
        String productLine=l.productKnown ? fmtMl(l.productMl)+" ml prodotto/stock" : "Quantità prodotto: non determinata";
        String waterLine=l.waterKnown ? fmtMl(l.waterMl)+" ml acqua" : "Quantità acqua: non determinata";
        String msg=date(l.createdAt)+"\n"+l.source.film+" · "+l.source.format+" · ISO "+l.source.exposedIso+
                "\n"+l.source.developer+" "+l.source.dilution+"\n"+fmt(l.actualTemp)+" °C · JOBO CPE2 · rotazione continua"+
                "\n\nTEMPO EFFETTIVO: "+DevelopmentCatalog.formatTime(l.actualSeconds)+"\nOrigine tempo: "+l.timeOrigin+
                "\nFonte originaria: "+l.source.sourceName+"\nTempo sorgente: "+DevelopmentCatalog.formatTime(l.source.originalSeconds)+" @ "+fmt(l.source.originalTemp)+" °C"+
                "\n\nPREPARA\n"+productLine+"\n"+waterLine+"\n"+fmtMl(l.volumeMl)+" ml totale · "+l.rolls+" rulli\n"+l.capacityMessage+
                "\n\nValutazione: "+(l.rating>0?stars(l.rating):"—")+"\nNote: "+(l.notes.isEmpty()?"—":l.notes);
        new AlertDialog.Builder(this).setTitle("Sviluppo").setMessage(msg).setPositiveButton("AZIONI",(d,w)->actions(id)).setNegativeButton("CHIUDI",null).show();
    }

    private void actions(long id){ String[] a={"RIPETI","USA COME MIA RICETTA","IMPOSTA COME RICETTA PREFERITA","CONFRONTA SVILUPPI"}; new AlertDialog.Builder(this).setTitle("Azioni Log").setItems(a,(d,w)->{if(w==0)repeat(id);else if(w==1)makeRecipe(id,false);else if(w==2)makeRecipe(id,true);else compare(id);}).show(); }
    private void makeRecipe(long id,boolean favorite){ long r=db.recipeFromLog(id,favorite); if(r>0)Toast.makeText(this,favorite?"Impostata come ricetta preferita":"Ricetta personale creata",Toast.LENGTH_LONG).show(); }
    private void repeat(long id){ AssistantDatabase.LogEntry l=db.getLog(id); if(l==null)return; Intent i=new Intent(this,NewDevelopmentActivity.class); i.putExtra("prefillFilm",l.source.film);i.putExtra("prefillFormat",l.source.format);i.putExtra("prefillExposedIso",l.source.exposedIso);i.putExtra("prefillDeveloper",l.source.developer);i.putExtra("prefillDilution",l.source.dilution);i.putExtra("prefillTemperature",l.actualTemp);i.putExtra("prefillRolls",l.rolls);i.putExtra("prefillVolume",l.volumeMl);i.putExtra("repeatTimeSeconds",l.actualSeconds);i.putExtra("repeatOrigin","RICETTA DAL LOG");startActivity(i); }
    private void compare(long id){ AssistantDatabase.LogEntry current=db.getLog(id); if(current==null)return; List<AssistantDatabase.LogEntry> logs=db.logsForCombo(current.comboKey()); StringBuilder b=new StringBuilder("Data | Temp | Tempo | Valutazione\n\n"); for(int x=logs.size()-1;x>=0;x--){AssistantDatabase.LogEntry l=logs.get(x); b.append(dateShort(l.createdAt)).append(" | ").append(fmt(l.actualTemp)).append("° | ").append(DevelopmentCatalog.formatTime(l.actualSeconds)).append(" | ").append(l.rating>0?stars(l.rating):"—"); if(!l.notes.isEmpty())b.append("\n  ").append(l.notes); b.append("\n");} new AlertDialog.Builder(this).setTitle("CONFRONTA SVILUPPI").setMessage(b.toString()).setPositiveButton("OK",null).show(); }

    private static String stars(int n){StringBuilder b=new StringBuilder();for(int i=0;i<n;i++)b.append('★');return b.toString();}
    private static String date(long ms){return DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}
    private static String dateShort(long ms){return DateFormat.getDateInstance(DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}
    private static String fmt(double v){return String.format(Locale.ITALY,"%.1f",v);}
    private static String fmtMl(double v){return Math.abs(v-Math.rint(v))<.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}
    private TextView text(String s,float z,int c,boolean b){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(primary);b.setTextSize(14);return b;}
    private LinearLayout.LayoutParams margin(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}
}
