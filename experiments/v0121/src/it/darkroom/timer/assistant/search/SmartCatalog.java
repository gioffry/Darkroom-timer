package it.darkroom.timer.assistant.search;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import it.darkroom.timer.R;
import it.darkroom.timer.assistant.system.CatalogManager;

/** Merges bundled, validated downloaded and selected-record caches without touching personal data. */
public final class SmartCatalog {
    private SmartCatalog(){}

    public static List<SmartSearchEngine.Item> localItems(Context c){
        LinkedHashMap<String,SmartSearchEngine.Item> map=new LinkedHashMap<>();
        try{putAll(map,parseCatalog(readBuiltin(c),false,"CATALOGO LOCALE"));}catch(Exception ignored){}
        String active=CatalogManager.readActiveCatalog(c);if(!active.isEmpty())try{putAll(map,parseCatalog(active,false,"CATALOGO LOCALE AGGIORNATO"));}catch(Exception ignored){}
        JSONArray cached=CatalogManager.cachedSelectedRecords(c);for(int i=0;i<cached.length();i++)try{SmartSearchEngine.Item x=parseRecord(cached.getJSONObject(i),null,false,"CACHE LOCALE");map.put(x.id,x);}catch(Exception ignored){}
        return new ArrayList<>(map.values());
    }

    public static List<SmartSearchEngine.Item> onlineItems(String raw){
        try{return parseCatalog(raw,true,"CATALOGO ONLINE");}catch(Exception e){return new ArrayList<>();}
    }

    public static SmartSearchEngine.Item findLocal(Context c,String query,String category){
        List<SmartSearchEngine.Result> r=SmartSearchEngine.search(localItems(c),query,category,1);return r.isEmpty()?null:r.get(0).item;
    }

    public static String canonicalName(Context c,String query,String category){SmartSearchEngine.Item i=findLocal(c,query,category);return i==null?safe(query).trim():i.name;}

    public static JSONObject record(SmartSearchEngine.Item item){try{return new JSONObject(item.recordJson);}catch(Exception e){return new JSONObject();}}
    public static JSONObject technical(JSONObject record){JSONObject t=record.optJSONObject("technical");return t==null?new JSONObject():t;}
    public static JSONObject source(JSONObject record){JSONObject s=record.optJSONObject("_source");return s==null?new JSONObject():s;}
    public static String sourceDetail(JSONObject record){JSONObject s=source(record);if(s.length()==0)return "NON DOCUMENTATO";StringBuilder b=new StringBuilder();b.append(s.optString("sourceType","FONTE")).append(" · ").append(s.optString("author",""));String title=s.optString("title","");if(!title.isEmpty())b.append("\n").append(title);String ver=s.optString("documentVersion","");if(!ver.isEmpty())b.append(" · ").append(ver);String url=s.optString("url","");if(!url.isEmpty())b.append("\n").append(url);String type=technical(record).optString("dataType","");if(!type.isEmpty())b.append("\n").append(type);return b.toString();}

    public static String[] dilutions(JSONObject record,boolean paper){
        JSONObject t=technical(record);JSONArray a=paper?t.optJSONArray("paperDilutions"):t.optJSONArray("filmDilutions");if(a==null)a=t.optJSONArray("dilutions");if(a==null)return new String[0];String[] out=new String[a.length()];for(int i=0;i<a.length();i++)out[i]=a.optString(i,"");return out;
    }

    public static Set<String> categories(String csv){LinkedHashSet<String> out=new LinkedHashSet<>();if(csv==null)return out;for(String x:csv.split(",")){x=x.trim();if(!x.isEmpty())out.add(x);}return out;}
    public static String categoryLabel(SmartSearchEngine.Item i){if(i.categories.isEmpty())return "Catalogo tecnico";String c=i.categories.get(0);if("FILM".equals(c))return "Pellicola";if("FILM_DEVELOPER".equals(c))return "Rivelatore pellicola";if("PAPER".equals(c))return "Carta";if("PAPER_DEVELOPER".equals(c))return "Rivelatore carta";if("STOP_BATH".equals(c))return "Arresto";if("FIXER".equals(c))return "Fissaggio";if("WETTING_AGENT".equals(c))return "Imbibente";if("TANK".equals(c))return "Tank";if("PROCESSOR".equals(c))return "Processore";return c;}

    private static List<SmartSearchEngine.Item> parseCatalog(String raw,boolean remote,String origin)throws Exception{
        JSONObject root=new JSONObject(raw),payload=root.getJSONObject("payload");JSONArray rows=payload.getJSONArray("records"),src=payload.optJSONArray("sources");LinkedHashMap<String,JSONObject> sources=new LinkedHashMap<>();if(src!=null)for(int i=0;i<src.length();i++){JSONObject s=src.optJSONObject(i);if(s!=null)sources.put(s.optString("id",""),s);}
        ArrayList<SmartSearchEngine.Item> out=new ArrayList<>();for(int i=0;i<rows.length();i++){JSONObject r=rows.getJSONObject(i);out.add(parseRecord(r,sources.get(r.optString("sourceId","")),remote,origin));}return out;
    }
    private static SmartSearchEngine.Item parseRecord(JSONObject raw,JSONObject source,boolean remote,String origin)throws Exception{
        JSONObject r=new JSONObject(raw.toString());if(source!=null)r.put("_source",new JSONObject(source.toString()));r.put("_origin",origin);
        ArrayList<String> cats=list(r.optJSONArray("categories")),aliases=list(r.optJSONArray("aliases"));String subtitle=r.optString("subtitle","");String maker=r.optString("manufacturer","");String shown=maker+(subtitle.isEmpty()?"":" · "+subtitle);
        return new SmartSearchEngine.Item(r.optString("id",""),r.optString("name",""),maker,cats,aliases,shown,origin+("VERIFICATO".equals(r.optString("verificationStatus"))?" · FONTE VERIFICATA":""),r.toString(),remote);
    }
    private static ArrayList<String> list(JSONArray a){ArrayList<String> out=new ArrayList<>();if(a!=null)for(int i=0;i<a.length();i++){String x=a.optString(i,"");if(!x.isEmpty())out.add(x);}return out;}
    private static void putAll(LinkedHashMap<String,SmartSearchEngine.Item> map,List<SmartSearchEngine.Item> rows){for(SmartSearchEngine.Item i:rows)map.put(i.id,i);}
    private static String readBuiltin(Context c)throws Exception{try(InputStream in=c.getResources().openRawResource(R.raw.catalog_v2)){return readAll(in);}}
    private static String readAll(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}
    private static String safe(String x){return x==null?"":x;}
}
