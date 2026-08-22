package it.darkroom.assistant;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Adapter di sola lettura: dati MDC/produttore restano invariati nel DB; l'interfaccia è italiana. */
final class DeveloperProfileStore {
    static final class Profile {
        String name="", manufacturer="", state="", preparation="", reuse="", capacity="";
        String shelfUnopened="", shelfOpened="", shelfStock="", shelfWorking="", sourceUrl="";
    }
    private DeveloperProfileStore() {}

    static Profile profile(String name) {
        if (name==null) return null;
        SQLiteDatabase db=MdcOfflineStore.database(); if(db==null)return null;
        String canonical=FullCatalogStore.canonicalDeveloper(name);
        String dn=norm(canonical==null?name:canonical);
        try(Cursor c=db.rawQuery("SELECT developer_name,manufacturer,physical_state,preparation,reuse_mode,capacity_text,shelf_life_unopened,shelf_life_opened,shelf_life_stock,shelf_life_working FROM developer_profiles WHERE developer_norm=? LIMIT 1",new String[]{dn})){
            if(!c.moveToFirst())return null;
            Profile p=new Profile();
            p.name=nz(c.getString(0)); p.manufacturer=nz(c.getString(1)); p.state=nz(c.getString(2));
            p.preparation=nz(c.getString(3)); p.reuse=nz(c.getString(4)); p.capacity=nz(c.getString(5));
            p.shelfUnopened=nz(c.getString(6)); p.shelfOpened=nz(c.getString(7)); p.shelfStock=nz(c.getString(8)); p.shelfWorking=nz(c.getString(9));
            try(Cursor s=db.rawQuery("SELECT source_url FROM developer_profile_sources WHERE developer_norm=? AND source_kind='MANUFACTURER' ORDER BY checked_at DESC LIMIT 1",new String[]{dn})){
                if(s.moveToFirst())p.sourceUrl=nz(s.getString(0));
            }
            return p;
        }catch(Throwable t){return null;}
    }

    static String[] filmDilutions(String name){
        String[] d=MdcOfflineStore.dilutionsForDeveloper(name); return d==null?new String[0]:d;
    }

    static int reuseCode(Profile p){
        if(p==null)return ChemistrySpecEngine.REUSE_UNKNOWN;
        String m=p.reuse.toLowerCase(Locale.ROOT);
        if(m.contains("one_shot")||m.contains("single_use")||m.contains("fresh_working_solution_per_batch"))return ChemistrySpecEngine.REUSE_ONE_SHOT;
        if(m.contains("reusable")||m.contains("replenish")||m.contains("reuse")||m.contains("limited_reuse")||m.contains("two_bath")||m.contains("single_or_two_film"))return ChemistrySpecEngine.REUSE_REUSABLE;
        return ChemistrySpecEngine.REUSE_UNKNOWN;
    }

    static boolean stockPrep(Profile p){
        if(p==null)return false; String s=(p.state+" "+p.preparation).toLowerCase(Locale.ROOT);
        return s.contains("powder")||s.contains("polvere")||s.contains("two-part")||s.contains("two-component")||s.contains("part a")||s.contains("part b");
    }

    static double filmCapacity(Profile p){
        if(p==null)return -1; String s=p.capacity;
        Matcher a=Pattern.compile("(?i)1\\s*(?:litre|liter|litro|l)\\b[^0-9]{0,120}(\\d{1,3})(?:\\s*[-–]\\s*(\\d{1,3}))?\\s*(?:rolls?|films?|rulli|pellicole)").matcher(s);
        if(a.find())return num(a.group(2)!=null?a.group(2):a.group(1));
        Matcher b=Pattern.compile("(?i)(\\d{1,3})(?:\\s*[-–]\\s*(\\d{1,3}))?\\s*(?:rolls?|films?|rulli|pellicole)[^.;]{0,100}(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l)\\b").matcher(s);
        return b.find()?num(b.group(2)!=null?b.group(2):b.group(1)):-1;
    }

    static String prepItalian(Profile p){
        if(p==null)return null; String n=norm(p.name);
        if(n.equals("rollei supergrain"))return "Diluire il concentrato con acqua. Per 260 ml: 1+9 = 26 ml + 234 ml acqua; 1+12 = 20 ml + 240 ml; 1+15 = circa 16,25 ml + 243,75 ml.";
        if(n.equals("fomadon excel"))return "Sciogliere prima la busta piccola e poi la grande in 700 ml d'acqua a 20–30 °C; quindi portare a 1 litro.";
        if(isItalian(p.preparation))return p.preparation;
        return p.preparation.isEmpty()?null:"Preparazione documentata nella scheda tecnica del produttore.";
    }

    static String detailsItalian(String name){
        Profile p=profile(name); if(p==null)return ""; String n=norm(p.name);
        StringBuilder b=new StringBuilder("SCHEDA TECNICA");
        if(!p.manufacturer.isEmpty())b.append("\nProduttore: ").append(p.manufacturer);
        String st=stateIt(p.state); if(!st.isEmpty())b.append("\nStato: ").append(st);
        String prep=prepItalian(p); if(prep!=null&&!prep.isEmpty())b.append("\nPreparazione: ").append(prep);
        b.append("\nRiutilizzo: ").append(reuseIt(p));
        String cap=capacityIt(p,n); if(!cap.isEmpty())b.append("\nCapacità: ").append(cap);
        String keep=keepingIt(p,n); if(!keep.isEmpty())b.append("\nConservazione: ").append(keep);
        if(n.equals("rollei supergrain"))b.append("\nNote: Conservare ben chiuso, al fresco e al riparo dalla luce; ridurre al minimo l'aria dopo l'apertura. Diluizioni ufficiali: 1+9, 1+12, 1+15.");
        if(!p.sourceUrl.isEmpty())b.append("\nFonte: produttore / scheda tecnica verificata");
        return b.toString();
    }

    private static String reuseIt(Profile p){
        String n=norm(p.name),m=p.reuse.toLowerCase(Locale.ROOT);
        if(n.equals("rollei supergrain"))return "Soluzione di lavoro fresca consigliata da Rollei; non è pubblicata una procedura specifica di reintegro per SUPERGRAIN.";
        if(m.contains("one_shot")||m.contains("single_use"))return "Monouso.";
        if(m.contains("replenish"))return "Riutilizzabile con reintegro secondo le istruzioni del produttore.";
        if(m.contains("reusable")||m.contains("reuse")||m.contains("single_or_two_film"))return "Riutilizzabile secondo le istruzioni del produttore.";
        if(m.contains("fresh_working_solution_recommended"))return "Soluzione di lavoro fresca consigliata dal produttore.";
        return "Non determinato.";
    }

    private static String capacityIt(Profile p,String n){
        if(n.equals("rollei supergrain"))return "500 ml di concentrato: circa 20–60 pellicole, secondo diluizione e volume di lavoro.";
        if(n.equals("fomadon excel"))return "1 litro di soluzione: 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.";
        if(isItalian(p.capacity))return p.capacity;
        return p.capacity.isEmpty()?"":"Dato dichiarato dal produttore nella scheda tecnica.";
    }

    private static String keepingIt(Profile p,String n){
        if(n.equals("rollei supergrain"))return "Indicazione generale Rollei: concentrato non aperto circa 1–2 anni se conservato al fresco e al buio; non è una garanzia specifica per SUPERGRAIN.";
        boolean any=!p.shelfUnopened.isEmpty()||!p.shelfOpened.isEmpty()||!p.shelfStock.isEmpty()||!p.shelfWorking.isEmpty();
        return any?"Dati di conservazione documentati nella scheda tecnica del produttore.":"";
    }

    private static String stateIt(String s){
        String x=nz(s).toLowerCase(Locale.ROOT); if(x.isEmpty())return "";
        if((x.contains("two-component")||x.contains("two-part"))&&x.contains("powder"))return "polvere a due componenti";
        if(x.contains("powder"))return "polvere";
        if((x.contains("two-component")||x.contains("two-part"))&&x.contains("liquid"))return "concentrato liquido a due componenti";
        if(x.contains("liquid concentrate")||x.contains("developer concentrate"))return "concentrato liquido";
        return isItalian(s)?s:"";
    }
    private static boolean isItalian(String s){
        String x=" "+nz(s).toLowerCase(Locale.ITALY)+" "; int n=0;
        for(String w:new String[]{" il "," la "," di "," con "," per "," acqua "," soluzione "," pellicola "," concentrato "})if(x.contains(w))n++;
        return n>=2;
    }
    private static double num(String s){try{return Double.parseDouble(s.replace(',','.'));}catch(Exception e){return -1;}}
    private static String nz(String s){return s==null?"":s.trim();}
    private static String norm(String s){String x=Normalizer.normalize(nz(s),Normalizer.Form.NFD).replaceAll("\\p{M}+","").toLowerCase(Locale.ROOT).replace('–',' ').replace('—',' ').replace('-',' ');return x.replaceAll("[^a-z0-9+]+"," ").trim().replaceAll("\\s+"," ");}
}
