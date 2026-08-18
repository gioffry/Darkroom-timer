package it.darkroom.timer.assistant.recipes;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
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

public final class MyRecipesActivity extends Activity {
    private LinearLayout list;
    private AssistantDatabase db;
    private int primary, muted, accent;

    @Override protected void onCreate(Bundle b){ super.onCreate(b); palette(); db=new AssistantDatabase(this); build(); }
    @Override protected void onResume(){ super.onResume(); refresh(); }
    @Override protected void onDestroy(){ if(db!=null)db.close(); super.onDestroy(); }

    private void palette(){ boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false); primary=dark?Color.rgb(255,42,42):Color.rgb(238,240,242); muted=dark?Color.rgb(145,34,34):Color.rgb(145,151,158); accent=dark?Color.rgb(255,42,42):Color.rgb(197,54,58); }
    private void build(){ ScrollView s=new ScrollView(this); s.setBackgroundColor(Color.BLACK); LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(16),dp(18),dp(28)); s.addView(root);
        TextView t=text("LE MIE RICETTE",25,primary,true); t.setGravity(Gravity.CENTER); root.addView(t); TextView sub=text("Ricette personali separate dal dato originale",12,muted,false); sub.setGravity(Gravity.CENTER); sub.setPadding(0,dp(4),0,dp(14)); root.addView(sub);
        list=new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); root.addView(list);
        Button back=button("← ASSISTANT"); back.setOnClickListener(v->finish()); root.addView(back); setContentView(s); refresh(); }

    private void refresh(){ if(list==null)return; list.removeAllViews(); List<AssistantDatabase.PersonalRecipe> rs=db.listRecipes(); if(rs.isEmpty()){ TextView e=text("Nessuna ricetta personale salvata.",14,muted,false); e.setPadding(0,dp(20),0,dp(20)); list.addView(e); return; }
        for(AssistantDatabase.PersonalRecipe r:rs){ String label=r.source.film+" · "+r.source.format+"\n"+r.source.developer+" "+r.source.dilution+" · ISO "+r.source.exposedIso+"\n"+String.format(Locale.ITALY,"%.1f °C",r.personalTemp)+" · JOBO CPE2\n"+DevelopmentCatalog.formatTime(r.personalSeconds)+(r.favorite?"   ★ Preferita":""); Button b=button(label); b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL); b.setOnClickListener(v->showRecipe(r.id)); list.addView(b,margin(-1,dp(104),0,0,0,dp(9))); } }

    private void showRecipe(long id){ AssistantDatabase.PersonalRecipe r=db.getRecipe(id); if(r==null)return; String msg="MIA RICETTA\n"+DevelopmentCatalog.formatTime(r.personalSeconds)+" @ "+fmt(r.personalTemp)+" °C"+(r.favorite?"\n★ PREFERITA":"")+"\n\nORIGINALE FONTE\n"+DevelopmentCatalog.formatTime(r.source.originalSeconds)+" @ "+fmt(r.source.originalTemp)+" °C\nFonte: "+r.source.sourceName+"\nTipo: "+r.source.dataType+"\n\nDifferenza tempo: "+delta(r.personalSeconds-r.source.originalSeconds)+"\nNota: "+(r.note.isEmpty()?"—":r.note)+"\nCreato: "+date(r.createdAt)+"\nModificato: "+date(r.updatedAt);
        new AlertDialog.Builder(this).setTitle(r.source.film+" · "+r.source.developer).setMessage(msg).setPositiveButton("MODIFICA",(d,w)->edit(id)).setNegativeButton("CHIUDI",null).setNeutralButton("AZIONI",(d,w)->actions(id)).show(); }

    private void actions(long id){ AssistantDatabase.PersonalRecipe r=db.getRecipe(id); if(r==null)return; String fav=r.favorite?"RIMUOVI PREFERITA":"IMPOSTA PREFERITA"; String[] a={fav,"VEDI ORIGINALE","RIPRISTINA ORIGINALE","ELIMINA RICETTA PERSONALE"}; new AlertDialog.Builder(this).setTitle("Azioni ricetta").setItems(a,(d,which)->{ if(which==0){db.setFavorite(id,!r.favorite);refresh();} else if(which==1)showOriginal(r); else if(which==2)confirmReset(id); else confirmDelete(id); }).show(); }
    private void showOriginal(AssistantDatabase.PersonalRecipe r){ new AlertDialog.Builder(this).setTitle("ORIGINALE FONTE").setMessage(r.source.film+" · "+r.source.format+" · ISO "+r.source.exposedIso+"\n"+r.source.developer+" "+r.source.dilution+"\n"+fmt(r.source.originalTemp)+" °C · JOBO CPE2 · rotazione continua\n\nTempo originale: "+DevelopmentCatalog.formatTime(r.source.originalSeconds)+"\nFonte: "+r.source.sourceName+"\nTipo dato: "+r.source.dataType+"\nDato sorgente: "+r.source.sourceData+"\n\n"+r.source.calculation).setPositiveButton("OK",null).show(); }
    private void confirmReset(long id){ new AlertDialog.Builder(this).setTitle("Ripristina originale?").setMessage("Le modifiche personali di tempo, temperatura e nota verranno azzerate. Il dato sorgente resta intatto.").setPositiveButton("RIPRISTINA",(d,w)->{db.resetOriginal(id);refresh();}).setNegativeButton("ANNULLA",null).show(); }
    private void confirmDelete(long id){ new AlertDialog.Builder(this).setTitle("Eliminare la ricetta personale?").setMessage("Il dato originale della fonte non viene modificato.").setPositiveButton("ELIMINA",(d,w)->{db.deleteRecipe(id);refresh();}).setNegativeButton("ANNULLA",null).show(); }

    private void edit(long id){ AssistantDatabase.PersonalRecipe r=db.getRecipe(id); if(r==null)return; LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(20),dp(6),dp(20),0); EditText time=field("Tempo m:ss"); time.setText(timeText(r.personalSeconds)); EditText temp=field("Temperatura °C"); temp.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL); temp.setText(fmt(r.personalTemp)); EditText note=field("Nota personale"); note.setText(r.note); CheckBox fav=new CheckBox(this); fav.setText("PREFERITA"); fav.setTextColor(primary); fav.setChecked(r.favorite); box.addView(time); box.addView(temp); box.addView(note); box.addView(fav);
        new AlertDialog.Builder(this).setTitle("Modifica mia ricetta").setView(box).setPositiveButton("SALVA",(d,w)->{ int sec=parseTime(time.getText().toString()); double tc=parseDouble(temp.getText().toString()); if(sec<=0||Double.isNaN(tc)){Toast.makeText(this,"Tempo o temperatura non validi",Toast.LENGTH_LONG).show();return;} db.updateRecipe(id,sec,tc,note.getText().toString(),fav.isChecked()); refresh(); }).setNegativeButton("ANNULLA",null).show(); }

    public static int parseTime(String s){ try{String x=s.trim(); if(x.contains(":")){String[] p=x.split(":"); return Integer.parseInt(p[0].trim())*60+Integer.parseInt(p[1].trim());} return Integer.parseInt(x);}catch(Exception e){return -1;} }
    private static double parseDouble(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception e){return Double.NaN;}}
    private static String timeText(int sec){return String.format(Locale.ITALY,"%d:%02d",sec/60,sec%60);} private static String fmt(double v){return String.format(Locale.ITALY,"%.1f",v);} private static String delta(int d){return (d>=0?"+":"")+d+" s";} private static String date(long ms){return DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT,Locale.ITALY).format(new Date(ms));}
    private TextView text(String s,float z,int c,boolean b){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;} private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(primary);b.setTextSize(14);return b;} private EditText field(String h){EditText e=new EditText(this);e.setHint(h);e.setHintTextColor(muted);e.setTextColor(primary);e.setSingleLine(false);return e;} private LinearLayout.LayoutParams margin(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;} private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);} 
}
