package it.darkroom.assistant;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/** Unified OFFLINE catalog: full MDC SQLite + verified local darkroom chemistry. */
final class FullCatalogStore {
    static final int ROLE_FILM_DEV = 1;
    static final int ROLE_PAPER_DEV = 2;
    static final int ROLE_STOP = 4;
    static final int ROLE_FIX = 8;
    static final int ROLE_WETTING = 16;
    static final int ROLE_WASHING = 32;
    static final int ROLE_CHEMISTRY = 64;
    static final int ROLE_FILM = 128;

    static final class Chemical {
        final String name, manufacturer, categories, physicalState, sourceUrl, verification;
        final int roles;
        final boolean stockPrep;
        final String[] filmDilutions, paperDilutions;
        final String workingDilution;
        Chemical(String name,String manufacturer,String categories,String physicalState,String sourceUrl,
                 String verification,int roles,boolean stockPrep,String[] filmDilutions,
                 String[] paperDilutions,String workingDilution) {
            this.name=name; this.manufacturer=manufacturer; this.categories=categories;
            this.physicalState=physicalState; this.sourceUrl=sourceUrl; this.verification=verification;
            this.roles=roles; this.stockPrep=stockPrep; this.filmDilutions=filmDilutions;
            this.paperDilutions=paperDilutions; this.workingDilution=workingDilution;
        }
    }

    static final class FilmInfo {
        final String displayName, sourceUrl;
        final int iso;
        FilmInfo(String displayName,int iso,String sourceUrl){this.displayName=displayName;this.iso=iso;this.sourceUrl=sourceUrl;}
    }

    private static final class Candidate {
        final String name, aliases, snippet;
        final int score;
        Candidate(String name,String aliases,String snippet,int score){this.name=name;this.aliases=aliases;this.snippet=snippet;this.score=score;}
    }

    private static SQLiteDatabase db() { return MdcOfflineStore.database(); }

    static List<OnlineCatalogSearch.SearchResult> searchFilmDevelopers(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name FROM developers",null)){
            while(c.moveToNext()) {
                String name=c.getString(0);
                add(map,q,name,developerAliases(name),"MDC_OFFLINE_DEVELOPER|"+developerManufacturer(name));
            }
        }
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM_DEV)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"LOCAL_CATALOG_DEVELOPER|"+nz(c.getString(2)));
        }
        return results(map,max);
    }

    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name FROM films",null)){
            while(c.moveToNext()) add(map,q,c.getString(0),"","MDC_OFFLINE_FILM");
        }
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"LOCAL_CATALOG_FILM|"+nz(c.getString(2)));
        }
        return results(map,max);
    }

    static List<String> searchChemicalNames(String query, int role, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(role)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),nz(c.getString(2)));
        }
        List<Candidate> cs=sorted(map);
        List<String> out=new ArrayList<>(); for(Candidate c:cs){out.add(c.name); if(out.size()>=max)break;} return out;
    }

    static Chemical chemical(String name) {
        if(name==null) return null; SQLiteDatabase d=db(); if(d==null) return null;
        String canonical = catalogCanonical(name);
        if(canonical!=null) {
            try(Cursor c=d.rawQuery("SELECT name,manufacturer,categories,physical_state,source_url,verification,roles,stock_prep,film_dilutions,paper_dilutions,working_dilution FROM catalog_products WHERE norm_name=? LIMIT 1",new String[]{norm(canonical)})){
                if(c.moveToFirst()) {
                    return new Chemical(c.getString(0),nz(c.getString(1)),nz(c.getString(2)),nz(c.getString(3)),nz(c.getString(4)),nz(c.getString(5)),c.getInt(6),c.getInt(7)!=0,split(c.getString(8)),split(c.getString(9)),emptyToNull(c.getString(10)));
                }
            }
        }
        String dev = canonicalDeveloper(name);
        if (dev != null) {
            return new Chemical(dev, developerManufacturer(dev),
                    "FILM_DEVELOPER|CHEMISTRY", "",
                    "https://www.digitaltruth.com/devchart.php", "MASSIVE_DEV_CHART",
                    ROLE_FILM_DEV | ROLE_CHEMISTRY, false,
                    MdcOfflineStore.dilutionsForDeveloper(dev), new String[0], null);
        }
        return null;
    }

    static FilmInfo filmInfo(String name) {
        if(name==null) return null; SQLiteDatabase d=db(); if(d==null) return null;
        String canonical=catalogCanonical(name);
        if(canonical==null) return null;
        try(Cursor c=d.rawQuery("SELECT name,nominal_iso,source_url FROM catalog_products WHERE norm_name=? AND (roles & ?)<>0 LIMIT 1",new String[]{norm(canonical),String.valueOf(ROLE_FILM)})){
            if(c.moveToFirst()) return new FilmInfo(c.getString(0),c.getInt(1),nz(c.getString(2)));
        }
        return null;
    }

    static String canonicalDeveloper(String name) {
        return canonicalFromTable("developers",name);
    }
    static String canonicalFilm(String name) {
        String direct=canonicalFromTable("films",stripFormat(name));
        if(direct!=null) return direct;
        FilmInfo fi=filmInfo(stripFormat(name));
        if(fi!=null) return canonicalFromTable("films",fi.displayName);
        return null;
    }

    private static String catalogCanonical(String name) {
        SQLiteDatabase d=db(); if(d==null) return null;
        String n=norm(name), cp=compact(name);
        try(Cursor c=d.rawQuery("SELECT name FROM catalog_products WHERE norm_name=? OR compact_name=? LIMIT 1",new String[]{n,cp})){
            if(c.moveToFirst()) return c.getString(0);
        }
        try(Cursor c=d.rawQuery("SELECT p.name FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id WHERE a.norm_alias=? OR a.compact_alias=? LIMIT 1",new String[]{n,cp})){
            if(c.moveToFirst()) return c.getString(0);
        }
        return null;
    }

    private static String canonicalFromTable(String table,String wanted) {
        if(wanted==null) return null; SQLiteDatabase d=db(); if(d==null)return null;
        String q=norm(wanted), qc=compact(wanted); String best=null; int bestScore=0;
        try(Cursor c=d.rawQuery("SELECT name FROM "+table,null)){
            while(c.moveToNext()){
                String name=c.getString(0); int s=score(q,qc,name,"");
                if(s>bestScore){bestScore=s;best=name;}
            }
        }
        if(bestScore>=700) return best;
        String alias=catalogCanonical(wanted);
        if(alias!=null && !alias.equalsIgnoreCase(wanted)){
            try(Cursor c=d.rawQuery("SELECT name FROM "+table,null)){
                while(c.moveToNext()){
                    String name=c.getString(0); int s=score(norm(alias),compact(alias),name,"");
                    if(s>bestScore){bestScore=s;best=name;}
                }
            }
        }
        return bestScore>=620?best:null;
    }

    private static String developerAliases(String name) {
        String n=norm(name); List<String> a=new ArrayList<>();
        String m=developerManufacturer(name);
        if (!m.isEmpty()) a.add(m + " " + name);
        if (n.equals("d 76")) { a.add("Kodak D-76"); a.add("Kodak D76"); }
        if (n.equals("xtol")) { a.add("Kodak XTOL"); a.add("Kodak Xtol"); }
        if (n.equals("hc 110")) { a.add("Kodak HC-110"); a.add("Kodak HC110"); }
        if (n.equals("tmax dev")) { a.add("Kodak T-Max Developer"); a.add("Kodak TMax Developer"); }
        if (n.equals("tmax rs")) { a.add("Kodak T-Max RS"); }
        if (n.equals("id 11")) { a.add("Ilford ID-11"); a.add("Ilford ID11"); }
        if (n.equals("ilfotec dd x")) { a.add("Ilford DD-X"); a.add("Ilford DDX"); }
        if (n.equals("rodinal")) { a.add("Adox Rodinal"); a.add("Adonal"); a.add("Agfa Rodinal"); }
        return String.join("|", a);
    }

    private static String developerManufacturer(String name) {
        String n=norm(name);
        if (n.startsWith("foma ") || n.startsWith("fomadon ")) return "FOMA";
        if (n.startsWith("ilford ") || n.startsWith("ilfo") || n.equals("id 11") ||
                n.equals("microphen") || n.equals("perceptol")) return "ILFORD";
        if (n.equals("d 76") || n.equals("d 76d") || n.equals("hc 110") || n.equals("xtol") ||
                n.startsWith("tmax ") || n.equals("d 96") || n.equals("d 97")) return "KODAK";
        if (n.equals("rodinal") || n.equals("adonal") || n.startsWith("adox ") || n.startsWith("adotech ")) return "ADOX";
        if (n.startsWith("rollei ")) return "ROLLEI";
        if (n.startsWith("bellini ")) return "BELLINI";
        if (n.startsWith("bergger ")) return "BERGGER";
        if (n.startsWith("tetenal ") || n.equals("ultrafin") || n.startsWith("ultrafin ")) return "TETENAL";
        if (n.startsWith("fuji ")) return "FUJIFILM";
        if (n.startsWith("ars imago ")) return "ARS-IMAGO";
        return "";
    }

    private static void add(Map<String,Candidate> map,String q,String name,String aliases,String snippet){
        int s=score(q,compact(q),name,aliases); if(s<=0)return; String k=norm(name);
        Candidate old=map.get(k); if(old==null||s>old.score)map.put(k,new Candidate(name,aliases,snippet,s));
    }
    private static List<OnlineCatalogSearch.SearchResult> results(Map<String,Candidate> map,int max){
        List<Candidate> cs=sorted(map); List<OnlineCatalogSearch.SearchResult> out=new ArrayList<>();
        for(Candidate c:cs){out.add(new OnlineCatalogSearch.SearchResult(c.name,"",c.snippet)); if(out.size()>=max)break;} return out;
    }
    private static List<Candidate> sorted(Map<String,Candidate> map){
        List<Candidate> cs=new ArrayList<>(map.values());
        Collections.sort(cs,(a,b)->a.score!=b.score?Integer.compare(b.score,a.score):a.name.compareToIgnoreCase(b.name)); return cs;
    }
    private static int score(String q,String qc,String name,String aliases){
        if(q==null||q.length()<3)return 0; String n=norm(name), nc=compact(name);
        int best=scoreOne(q,qc,n,nc);
        if(aliases!=null&&!aliases.trim().isEmpty())for(String a:aliases.split("\\|")){
            String an=norm(a); if(an.isEmpty())continue;
            best=Math.max(best,scoreOne(q,qc,an,compact(a)));
        }
        return best;
    }
    private static int scoreOne(String q,String qc,String n,String nc){
        if(n==null||n.isEmpty()||nc==null||nc.isEmpty())return 0;
        if(n.equals(q)||nc.equals(qc))return 1000;
        if(n.startsWith(q)||nc.startsWith(qc))return 950;
        if(q.startsWith(n)||qc.startsWith(nc)||q.endsWith(" "+n)||qc.endsWith(nc))return 930;
        for(String t:n.split(" "))if(!t.isEmpty()&&t.startsWith(q))return 910;
        if(n.contains(q)||(!qc.isEmpty()&&nc.contains(qc)))return 850;
        String[] qt=q.split(" "); boolean all=true; for(String t:qt)if(!n.contains(t)){all=false;break;} if(all)return 760;
        return 0;
    }
    private static String norm(String s){
        String x=Normalizer.normalize(s==null?"":s,Normalizer.Form.NFD).replaceAll("\\p{M}+","").toLowerCase(Locale.ROOT).replace('–',' ').replace('—',' ').replace('-',' ');
        return x.replaceAll("[^a-z0-9+]+"," ").trim().replaceAll("\\s+"," ");
    }
    private static String compact(String s){return norm(s).replaceAll("[^a-z0-9]+","");}
    private static String stripFormat(String s){if(s==null)return "";return s.replaceAll("(?i)\\s*[—-]\\s*(35\\s*mm|120)\\s*$","").trim();}
    private static String[] split(String s){if(s==null||s.trim().isEmpty())return new String[0];String[] r=s.split("\\|");List<String>o=new ArrayList<>();for(String x:r)if(!x.trim().isEmpty())o.add(x.trim());return o.toArray(new String[0]);}
    private static String nz(String s){return s==null?"":s;}
    private static String emptyToNull(String s){return s==null||s.trim().isEmpty()?null:s.trim();}
}
