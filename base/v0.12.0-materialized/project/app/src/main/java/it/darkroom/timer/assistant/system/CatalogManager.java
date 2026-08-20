package it.darkroom.timer.assistant.system;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

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
import java.util.Locale;

/**
 * R9 optional catalog updater. The built-in APK catalog is always usable offline.
 * Remote data is staged, schema/checksum validated, and only then promoted.
 */
public final class CatalogManager {
    public static final int BUILTIN_VERSION=1;
    public static final int CATALOG_SCHEMA=1;
    private static final String PREF="catalog_meta";
    private static final String REMOTE_URL="https://raw.githubusercontent.com/gioffry/Darkroom-timer/feature-v0120-darkroom-assistant-r7-r8-r9/experiments/v0120/catalog-v1.json";

    public interface Callback { void done(boolean ok,String message); }
    private CatalogManager(){}

    public static int activeVersion(Context c){return c.getSharedPreferences(PREF,Context.MODE_PRIVATE).getInt("active_version",BUILTIN_VERSION);}
    public static String activeOrigin(Context c){return activeVersion(c)==BUILTIN_VERSION&&!catalogFile(c).exists()?"INTEGRATO NELL'APK · OFFLINE":"CATALOGO LOCALE VALIDATO";}

    public static void checkForUpdates(final Context c,final Callback cb){
        new Thread(()->{
            String message;boolean ok=false;HttpURLConnection conn=null;
            try{
                conn=(HttpURLConnection)new URL(REMOTE_URL).openConnection();conn.setConnectTimeout(5000);conn.setReadTimeout(5000);conn.setUseCaches(false);conn.setRequestProperty("Accept","application/json");
                int code=conn.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);
                String raw=readAll(conn.getInputStream());JSONObject root=new JSONObject(raw);
                int version=root.optInt("catalogVersion",-1);int schema=root.optInt("schemaVersion",-1);JSONObject payload=root.optJSONObject("payload");String expected=root.optString("payloadSha256","");
                if(version<1)throw new Exception("versione catalogo non valida");if(schema!=CATALOG_SCHEMA)throw new Exception("schema catalogo non supportato");if(payload==null)throw new Exception("payload mancante");
                String actual=sha256(payload.toString());if(expected.length()!=64||!expected.equalsIgnoreCase(actual))throw new Exception("checksum catalogo non valido");
                int current=activeVersion(c);if(version<=current){ok=true;message="Catalogo dati "+current+" già aggiornato. L'app continua a usare i dati locali.";}
                else {promote(c,raw,version);ok=true;message="Catalogo dati aggiornato alla versione "+version+". Il catalogo precedente è stato conservato.";}
            }catch(Exception ex){message="Impossibile controllare aggiornamenti dati: "+ex.getMessage()+". Nessuna modifica applicata; il catalogo locale resta valido.";}finally{if(conn!=null)conn.disconnect();}
            final boolean result=ok;final String text=message;new Handler(Looper.getMainLooper()).post(()->cb.done(result,text));
        },"darkroom-catalog-update").start();
    }

    private static void promote(Context c,String raw,int version)throws Exception{
        File dir=new File(c.getFilesDir(),"catalog");if(!dir.exists()&&!dir.mkdirs())throw new Exception("impossibile creare cartella catalogo");File target=catalogFile(c),previous=new File(dir,"catalog.previous.json"),tmp=new File(dir,"catalog.tmp.json");
        write(tmp,raw); // validate once more from staged bytes before touching active data
        JSONObject staged=new JSONObject(readFile(tmp));JSONObject payload=staged.getJSONObject("payload");if(staged.getInt("schemaVersion")!=CATALOG_SCHEMA||!staged.getString("payloadSha256").equalsIgnoreCase(sha256(payload.toString())))throw new Exception("integrità staging fallita");
        if(previous.exists()&&!previous.delete())throw new Exception("impossibile sostituire backup catalogo precedente");if(target.exists()&&!target.renameTo(previous))throw new Exception("impossibile conservare catalogo precedente");
        if(!tmp.renameTo(target)){if(previous.exists())previous.renameTo(target);throw new Exception("impossibile attivare nuovo catalogo");}
        if(!c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putInt("active_version",version).putLong("updated_at",System.currentTimeMillis()).commit()){if(target.exists())target.delete();if(previous.exists())previous.renameTo(target);throw new Exception("impossibile registrare versione catalogo");}
    }

    public static void rollbackToBuiltin(Context c){File target=catalogFile(c),previous=new File(new File(c.getFilesDir(),"catalog"),"catalog.previous.json");if(target.exists())target.delete();if(previous.exists())previous.delete();c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putInt("active_version",BUILTIN_VERSION).remove("updated_at").apply();}

    public static String describe(Context c){return "Catalogo dati "+activeVersion(c)+" · "+activeOrigin(c)+"\nSchema catalogo "+CATALOG_SCHEMA+" · rete non necessaria per STAMPA, PROVINO, Split Grade, sviluppi, calcoli, ricette, Log, inventario, attrezzatura o Assistente operativo.";}

    private static File catalogFile(Context c){return new File(new File(c.getFilesDir(),"catalog"),"catalog.active.json");}
    private static void write(File f,String s)throws Exception{try(FileOutputStream out=new FileOutputStream(f)){out.write(s.getBytes(StandardCharsets.UTF_8));out.getFD().sync();}}
    private static String readFile(File f)throws Exception{try(FileInputStream in=new FileInputStream(f)){return readAll(in);}}
    private static String readAll(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}
    private static String sha256(String s)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");byte[] b=md.digest(s.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte x:b)out.append(String.format(Locale.US,"%02x",x&0xff));return out.toString();}
}
