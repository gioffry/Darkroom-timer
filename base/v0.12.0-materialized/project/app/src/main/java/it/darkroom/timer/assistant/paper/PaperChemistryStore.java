package it.darkroom.timer.assistant.paper;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.Locale;

/** Local/offline paper-chemistry session state. Unknown values stay unknown, never numeric zero. */
public final class PaperChemistryStore {
    public static final String PREF="paper_chemistry_session";
    public static final String PAPER_DEFAULT="Fomaspeed Variant 311";

    public static final class Mix {
        public boolean known;
        public double productMl,waterMl,totalMl;
        public String message="";
    }
    public static final class Session {
        public boolean active;
        public long createdAt;
        public String paper="",developer="",developerDilution="",developerOrigin="";
        public String stop="",stopDilution="",stopOrigin="";
        public String fixer="",fixerDilution="",fixerOrigin="";
        public double volumeMl=1000;
        public String notes="";
    }

    private PaperChemistryStore(){}

    public static Mix calculate(String dilution,double totalMl){
        Mix r=new Mix();r.totalMl=totalMl;
        if(!(totalMl>0)){r.message="Volume di lavoro non valido";return r;}
        if(dilution==null){r.message="DILUIZIONE NON DOCUMENTATA";return r;}
        String d=dilution.trim().replace(" ","");
        String[] p=d.split("\\+");
        if(p.length!=2){r.message="DILUIZIONE NON DOCUMENTATA";return r;}
        try{double a=Double.parseDouble(p[0].replace(',','.'));double b=Double.parseDouble(p[1].replace(',','.'));if(a<=0||b<0)throw new Exception();double unit=totalMl/(a+b);r.productMl=unit*a;r.waterMl=unit*b;r.known=true;r.message="CALCOLO da rapporto "+d;return r;}catch(Exception ex){r.message="DILUIZIONE NON DETERMINABILE";return r;}
    }

    public static Session load(Context c){SharedPreferences p=c.getSharedPreferences(PREF,Context.MODE_PRIVATE);Session s=new Session();s.active=p.getBoolean("active",false);s.createdAt=p.getLong("created_at",0);s.paper=p.getString("paper",PAPER_DEFAULT);s.developer=p.getString("developer","");s.developerDilution=p.getString("developer_dilution","");s.developerOrigin=p.getString("developer_origin","");s.stop=p.getString("stop","");s.stopDilution=p.getString("stop_dilution","");s.stopOrigin=p.getString("stop_origin","");s.fixer=p.getString("fixer","");s.fixerDilution=p.getString("fixer_dilution","");s.fixerOrigin=p.getString("fixer_origin","");s.volumeMl=Double.longBitsToDouble(p.getLong("volume_bits",Double.doubleToRawLongBits(1000.0)));s.notes=p.getString("notes","");return s;}

    public static void save(Context c,Session s){c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putBoolean("active",true).putLong("created_at",System.currentTimeMillis()).putString("paper",safe(s.paper)).putString("developer",safe(s.developer)).putString("developer_dilution",safe(s.developerDilution)).putString("developer_origin",safe(s.developerOrigin)).putString("stop",safe(s.stop)).putString("stop_dilution",safe(s.stopDilution)).putString("stop_origin",safe(s.stopOrigin)).putString("fixer",safe(s.fixer)).putString("fixer_dilution",safe(s.fixerDilution)).putString("fixer_origin",safe(s.fixerOrigin)).putLong("volume_bits",Double.doubleToRawLongBits(s.volumeMl)).putString("notes",safe(s.notes)).apply();}
    public static void clear(Context c){c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().clear().apply();}

    public static String shortStatus(Context c){Session s=load(c);return s.active?"PRONTA":"NESSUNA SESSIONE ATTIVA";}
    public static String summary(Context c){Session s=load(c);if(!s.active)return "NESSUNA SESSIONE CHIMICA ATTIVA";StringBuilder b=new StringBuilder();b.append("Carta: ").append(empty(s.paper,"non indicata")).append("\n");b.append("Volume: ").append(fmt(s.volumeMl)).append(" ml\n");b.append("Rivelatore: ").append(component(s.developer,s.developerDilution,s.developerOrigin)).append("\n");b.append("Arresto: ").append(component(s.stop,s.stopDilution,s.stopOrigin)).append("\n");b.append("Fissaggio: ").append(component(s.fixer,s.fixerDilution,s.fixerOrigin));return b.toString();}
    public static String activeSnapshot(Context c){Session s=load(c);if(!s.active)return "";return "PAPER_SESSION_V1|created="+s.createdAt+"|paper="+esc(s.paper)+"|volumeMl="+fmt(s.volumeMl)+"|developer="+esc(s.developer)+"|developerDilution="+esc(s.developerDilution)+"|developerOrigin="+esc(s.developerOrigin)+"|stop="+esc(s.stop)+"|stopDilution="+esc(s.stopDilution)+"|stopOrigin="+esc(s.stopOrigin)+"|fixer="+esc(s.fixer)+"|fixerDilution="+esc(s.fixerDilution)+"|fixerOrigin="+esc(s.fixerOrigin)+"|notes="+esc(s.notes);}

    private static String component(String name,String dilution,String origin){if(name==null||name.trim().isEmpty())return "non configurato";String x=name.trim();if(dilution!=null&&!dilution.trim().isEmpty())x+=" · "+dilution.trim();if(origin!=null&&!origin.trim().isEmpty())x+=" · "+origin.trim();return x;}
    private static String empty(String s,String fallback){return s==null||s.trim().isEmpty()?fallback:s.trim();}private static String safe(String s){return s==null?"":s;}private static String esc(String s){return safe(s).replace("\\","\\\\").replace("|","\\|").replace("\n","\\n");}private static String fmt(double v){return Math.abs(v-Math.rint(v))<0.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}
}
