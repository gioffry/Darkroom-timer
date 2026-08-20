package it.darkroom.timer.assistant.system;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/** Offline-first versioned technical catalog. Network is optional enrichment only. */
public final class CatalogManager {
    public static final int BUILTIN_VERSION=2;
    public static final int CATALOG_SCHEMA=2;
    public static final int REMOTE_VERSION=3;
    private static final String PREF="catalog_meta";
    private static final String REMOTE_URL="https://raw.githubusercontent.com/gioffry/Darkroom-timer/feature-v0121-assistant-ux-smart-catalog/catalog/catalog-v3.json";
    private static final long SEARCH_CACHE_MS=5*60*1000L;
    private static volatile String recentRemote="";
    private static volatile long recentRemoteAt=0;

    public interface Callback { void done(boolean ok,String message); }
    public interface RemoteCallback { void done(String raw,String error); }
    private CatalogManager(){}

    public static int activeVersion(Context c){return c.getSharedPreferences(PREF,Context.MODE_PRIVATE).getInt("active_version",BUILTIN_VERSION);}
    public static String activeOrigin(Context c){return catalogFile(c).exists()?"CATALOGO LOCALE VALIDATO":"INTEGRATO NELL'APK · OFFLINE";}

    public static void checkForUpdates(final Context c,final Callback cb){
        fetchRemoteForSearch(c,(raw,error)->{
            boolean ok=false;String message;
            if(error!=null){message="Impossibile controllare aggiornamenti dati: "+error+". Nessuna modifica applicata; il catalogo locale resta valido.";}
            else try{
                JSONObject root=validate(raw);int version=root.getInt("catalogVersion");int current=activeVersion(c);
                if(version<=current){ok=true;message="Catalogo dati "+current+" già aggiornato. L'app continua a usare i dati locali.";}
                else{promote(c,raw,version);ok=true;message="Catalogo dati aggiornato alla versione "+version+". Il catalogo precedente è stato conservato.";}
            }catch(Exception ex){message="Aggiornamento non applicato: "+ex.getMessage()+". Il catalogo precedente resta valido.";}
            cb.done(ok,message);
        });
    }

    /** Debounced callers may invoke this repeatedly; the actual HTTP payload is cached for five minutes. */
    public static void fetchRemoteForSearch(final Context c,final RemoteCallback cb){
        long now=System.currentTimeMillis();String cached=recentRemote;
        if(!cached.isEmpty()&&now-recentRemoteAt<SEARCH_CACHE_MS){new Handler(Looper.getMainLooper()).post(()->cb.done(cached,null));return;}
        new Thread(()->{
            HttpURLConnection conn=null;String raw=null,error=null;
            try{
                conn=(HttpURLConnection)new URL(REMOTE_URL).openConnection();conn.setConnectTimeout(4500);conn.setReadTimeout(4500);conn.setUseCaches(false);conn.setRequestProperty("Accept","application/json");
                int code=conn.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);
                raw=readAll(conn.getInputStream());validate(raw);recentRemote=raw;recentRemoteAt=System.currentTimeMillis();
            }catch(Exception ex){error=ex.getMessage();}finally{if(conn!=null)conn.disconnect();}
            final String r=raw,e=error;new Handler(Looper.getMainLooper()).post(()->cb.done(r,e));
        },"darkroom-smart-catalog").start();
    }

    public static String readActiveCatalog(Context c){try{return catalogFile(c).exists()?readFile(catalogFile(c)):"";}catch(Exception e){return "";}}

    /** Cache only selected technical records; personal inventory fields never enter this file. */
    public static synchronized void cacheSelectedRecord(Context c,JSONObject record){
        try{
            String id=record.optString("id","").trim(),name=record.optString("name","").trim();if(id.isEmpty()||name.isEmpty())return;
            File f=selectedCacheFile(c);JSONObject root=f.exists()?new JSONObject(readFile(f)):new JSONObject();JSONArray rows=root.optJSONArray("records");if(rows==null)rows=new JSONArray();
            LinkedHashMap<String,JSONObject> map=new LinkedHashMap<>();for(int i=0;i<rows.length();i++){JSONObject x=rows.optJSONObject(i);if(x!=null&&!x.optString("id","").isEmpty())map.put(x.optString("id"),x);}map.put(id,new JSONObject(record.toString()));
            JSONArray out=new JSONArray();for(JSONObject x:map.values())out.put(x);JSONObject next=new JSONObject();next.put("schemaVersion",1);next.put("records",out);writeAtomic(f,next.toString());
        }catch(Exception ignored){}
    }
    public static synchronized JSONArray cachedSelectedRecords(Context c){try{File f=selectedCacheFile(c);if(!f.exists())return new JSONArray();JSONObject root=new JSONObject(readFile(f));if(root.optInt("schemaVersion",-1)!=1)return new JSONArray();JSONArray a=root.optJSONArray("records");return a==null?new JSONArray():a;}catch(Exception e){return new JSONArray();}}

    private static JSONObject validate(String raw)throws Exception{
        JSONObject root=new JSONObject(raw);int version=root.optInt("catalogVersion",-1),schema=root.optInt("schemaVersion",-1);JSONObject payload=root.optJSONObject("payload");String expected=root.optString("payloadSha256","");
        if(version<BUILTIN_VERSION)throw new Exception("versione catalogo non valida");if(schema!=CATALOG_SCHEMA)throw new Exception("schema catalogo non supportato");if(payload==null)throw new Exception("payload mancante");
        JSONArray rows=payload.optJSONArray("records"),sources=payload.optJSONArray("sources");if(rows==null||rows.length()<1)throw new Exception("catalogo senza record tecnici");if(sources==null||sources.length()<1)throw new Exception("catalogo senza fonti");
        String actual=sha256(payload.toString());if(expected.length()!=64||!expected.equalsIgnoreCase(actual))throw new Exception("checksum catalogo non valido");return root;
    }

    private static void promote(Context c,String raw,int version)throws Exception{
        validate(raw);File dir=dir(c);if(!dir.exists()&&!dir.mkdirs())throw new Exception("impossibile creare cartella catalogo");File target=catalogFile(c),previous=new File(dir,"catalog.previous.json"),tmp=new File(dir,"catalog.tmp.json");write(tmp,raw);validate(readFile(tmp));
        if(previous.exists()&&!previous.delete())throw new Exception("impossibile sostituire backup catalogo precedente");if(target.exists()&&!target.renameTo(previous))throw new Exception("impossibile conservare catalogo precedente");
        if(!tmp.renameTo(target)){if(previous.exists())previous.renameTo(target);throw new Exception("impossibile attivare nuovo catalogo");}
        if(!c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putInt("active_version",version).putLong("updated_at",System.currentTimeMillis()).commit()){if(target.exists())target.delete();if(previous.exists())previous.renameTo(target);throw new Exception("impossibile registrare versione catalogo");}
    }

    public static void rollbackToBuiltin(Context c){File target=catalogFile(c),previous=new File(dir(c),"catalog.previous.json");if(target.exists())target.delete();if(previous.exists())previous.delete();c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putInt("active_version",BUILTIN_VERSION).remove("updated_at").apply();recentRemote="";recentRemoteAt=0;}
    public static String describe(Context c){return "Catalogo dati "+activeVersion(c)+" · "+activeOrigin(c)+"\nSchema catalogo "+CATALOG_SCHEMA+" · Smart Search usa subito il catalogo locale; la rete aggiunge risultati senza bloccare l'app.";}

    private static File dir(Context c){return new File(c.getFilesDir(),"catalog");}
    private static File catalogFile(Context c){return new File(dir(c),"catalog.active.json");}
    private static File selectedCacheFile(Context c){return new File(dir(c),"selected-records.json");}
    private static void writeAtomic(File f,String s)throws Exception{File d=f.getParentFile();if(d!=null&&!d.exists()&&!d.mkdirs())throw new Exception("cartella cache non disponibile");File tmp=new File(d,f.getName()+".tmp");write(tmp,s);if(f.exists()&&!f.delete())throw new Exception("cache non sostituibile");if(!tmp.renameTo(f))throw new Exception("cache non attivabile");}
    private static void write(File f,String s)throws Exception{try(FileOutputStream out=new FileOutputStream(f)){out.write(s.getBytes(StandardCharsets.UTF_8));out.getFD().sync();}}
    private static String readFile(File f)throws Exception{try(FileInputStream in=new FileInputStream(f)){return readAll(in);}}
    private static String readAll(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}
    private static String sha256(String s)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");byte[] b=md.digest(s.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte x:b)out.append(String.format(Locale.US,"%02x",x&0xff));return out.toString();}
}
