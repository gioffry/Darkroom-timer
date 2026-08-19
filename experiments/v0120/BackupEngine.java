package it.darkroom.timer.assistant.system;

import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import it.darkroom.timer.assistant.data.AssistantDataSchema;
import it.darkroom.timer.assistant.data.AssistantDatabase;

/** Versioned, validated backup/restore. No secrets or signing material are read. */
public final class BackupEngine {
    public static final int FORMAT_VERSION=1;
    public static final int CATALOG_VERSION=1;
    public static final String APP_VERSION="0.12.0";
    public static final int VERSION_CODE=57;
    public static final String MODE_MERGE="MERGE";
    public static final String MODE_REPLACE="REPLACE";

    private static final String[] TABLES={
            "personal_recipes","development_logs","chemical_inventory","chemical_usage",
            "personal_equipment","personal_tanks","assistant_sessions","paper_chemistry_sessions","technical_source_cache"
    };
    private static final String[] PREFS={"ui","assistant_operational","assistant_settings","paper_chemistry_session","catalog_meta","print_log"};

    public static final class Validation { public boolean ok; public String error="",summary=""; public JSONObject root; }
    private BackupEngine(){}

    public static String exportJson(Context c) throws Exception {
        AssistantDatabase helper=new AssistantDatabase(c);SQLiteDatabase db=helper.getReadableDatabase();JSONObject payload=new JSONObject();JSONObject tables=new JSONObject();
        for(String table:TABLES)tables.put(table,readTable(db,table));payload.put("tables",tables);
        JSONObject prefs=new JSONObject();for(String name:PREFS)prefs.put(name,readPrefs(c.getSharedPreferences(name,Context.MODE_PRIVATE)));payload.put("preferences",prefs);
        String payloadText=payload.toString();JSONObject root=new JSONObject();root.put("backupFormatVersion",FORMAT_VERSION);root.put("appVersion",APP_VERSION);root.put("versionCode",VERSION_CODE);root.put("databaseSchemaVersion",AssistantDataSchema.VERSION);root.put("catalogVersion",CATALOG_VERSION);root.put("createdAt",System.currentTimeMillis());root.put("payload",payload);root.put("payloadSha256",sha256(payloadText));helper.close();return root.toString(2);
    }

    public static Validation validate(String json){Validation v=new Validation();try{JSONObject root=new JSONObject(json);if(root.optInt("backupFormatVersion",-1)!=FORMAT_VERSION){v.error="Versione formato backup non supportata";return v;}int schema=root.optInt("databaseSchemaVersion",-1);if(schema<1||schema>AssistantDataSchema.VERSION){v.error="Versione schema backup non compatibile: "+schema;return v;}JSONObject payload=root.getJSONObject("payload");String expected=root.optString("payloadSha256","");String actual=sha256(payload.toString());if(expected.length()!=64||!expected.equalsIgnoreCase(actual)){v.error="Integrità backup non valida: checksum SHA-256 differente";return v;}JSONObject tables=payload.getJSONObject("tables");StringBuilder s=new StringBuilder();s.append("Backup v").append(root.optString("appVersion","?")).append(" · schema ").append(schema).append(" · catalogo ").append(root.optInt("catalogVersion",0)).append("\n");for(String table:TABLES){JSONArray a=tables.optJSONArray(table);s.append(table).append(": ").append(a==null?0:a.length()).append("\n");}v.ok=true;v.root=root;v.summary=s.toString().trim();return v;}catch(Exception ex){v.error="File backup non valido o corrotto: "+ex.getMessage();return v;}}

    public static void restore(Context c,String json,String mode) throws Exception {
        Validation check=validate(json);if(!check.ok)throw new IllegalArgumentException(check.error);JSONObject payload=check.root.getJSONObject("payload");JSONObject incomingTables=payload.getJSONObject("tables");JSONObject incomingPrefs=payload.getJSONObject("preferences");
        JSONObject oldPrefs=new JSONObject();for(String name:PREFS)oldPrefs.put(name,readPrefs(c.getSharedPreferences(name,Context.MODE_PRIVATE)));
        AssistantDatabase helper=new AssistantDatabase(c);SQLiteDatabase db=helper.getWritableDatabase();boolean prefsChanged=false;db.beginTransaction();try{
            if(MODE_REPLACE.equals(mode)){for(String table:new String[]{"chemical_usage","personal_tanks","personal_equipment","chemical_inventory","development_logs","personal_recipes","assistant_sessions","paper_chemistry_sessions","technical_source_cache"})db.delete(table,null,null);}
            for(String table:TABLES){JSONArray rows=incomingTables.optJSONArray(table);if(rows==null)continue;for(int i=0;i<rows.length();i++){ContentValues cv=jsonToValues(rows.getJSONObject(i));if(MODE_REPLACE.equals(mode))db.insertOrThrow(table,null,cv);else db.insertWithOnConflict(table,null,cv,SQLiteDatabase.CONFLICT_IGNORE);}}
            for(String prefName:PREFS){JSONObject p=incomingPrefs.optJSONObject(prefName);if(p!=null){restorePrefs(c.getSharedPreferences(prefName,Context.MODE_PRIVATE),p,MODE_REPLACE.equals(mode));prefsChanged=true;}}
            db.setTransactionSuccessful();
        }catch(Exception ex){if(prefsChanged)restorePreferenceSnapshot(c,oldPrefs);throw ex;}finally{try{db.endTransaction();}catch(Exception end){if(prefsChanged)restorePreferenceSnapshot(c,oldPrefs);helper.close();throw end;}helper.close();}
    }

    private static JSONArray readTable(SQLiteDatabase db,String table)throws Exception{JSONArray out=new JSONArray();Cursor c=db.query(table,null,null,null,null,null,null);try{String[] cols=c.getColumnNames();while(c.moveToNext()){JSONObject row=new JSONObject();for(int i=0;i<cols.length;i++){int type=c.getType(i);if(type==Cursor.FIELD_TYPE_NULL)row.put(cols[i],JSONObject.NULL);else if(type==Cursor.FIELD_TYPE_INTEGER)row.put(cols[i],c.getLong(i));else if(type==Cursor.FIELD_TYPE_FLOAT)row.put(cols[i],c.getDouble(i));else if(type==Cursor.FIELD_TYPE_BLOB)row.put(cols[i],android.util.Base64.encodeToString(c.getBlob(i),android.util.Base64.NO_WRAP));else row.put(cols[i],c.getString(i));}out.put(row);}}finally{c.close();}return out;}
    private static ContentValues jsonToValues(JSONObject row)throws Exception{ContentValues v=new ContentValues();JSONArray names=row.names();if(names==null)return v;for(int i=0;i<names.length();i++){String k=names.getString(i);Object x=row.get(k);if(x==JSONObject.NULL)v.putNull(k);else if(x instanceof Boolean)v.put(k,(Boolean)x?1:0);else if(x instanceof Integer)v.put(k,(Integer)x);else if(x instanceof Long)v.put(k,(Long)x);else if(x instanceof Number)v.put(k,((Number)x).doubleValue());else v.put(k,String.valueOf(x));}return v;}

    private static JSONObject readPrefs(SharedPreferences p)throws Exception{JSONObject o=new JSONObject();for(Map.Entry<String,?> e:p.getAll().entrySet()){Object x=e.getValue();if(x instanceof Set){JSONArray a=new JSONArray();for(Object y:(Set<?>)x)a.put(String.valueOf(y));JSONObject wrap=new JSONObject();wrap.put("__type","string_set");wrap.put("value",a);o.put(e.getKey(),wrap);}else o.put(e.getKey(),x==null?JSONObject.NULL:x);}return o;}
    private static void restorePrefs(SharedPreferences p,JSONObject data,boolean replace)throws Exception{SharedPreferences.Editor ed=p.edit();if(replace)ed.clear();JSONArray names=data.names();if(names!=null)for(int i=0;i<names.length();i++){String k=names.getString(i);if(!replace&&p.contains(k))continue;Object x=data.get(k);if(x==JSONObject.NULL)ed.remove(k);else if(x instanceof JSONObject&&"string_set".equals(((JSONObject)x).optString("__type"))){JSONArray a=((JSONObject)x).getJSONArray("value");Set<String> set=new HashSet<>();for(int j=0;j<a.length();j++)set.add(a.getString(j));ed.putStringSet(k,set);}else if(x instanceof Boolean)ed.putBoolean(k,(Boolean)x);else if(x instanceof Integer)ed.putInt(k,(Integer)x);else if(x instanceof Long)ed.putLong(k,(Long)x);else if(x instanceof Number){double d=((Number)x).doubleValue();long l=((Number)x).longValue();if(Math.abs(d-l)<0.0000001&&l>=Integer.MIN_VALUE&&l<=Integer.MAX_VALUE)ed.putInt(k,(int)l);else ed.putLong(k,Double.doubleToRawLongBits(d));}else ed.putString(k,String.valueOf(x));}if(!ed.commit())throw new IllegalStateException("Impossibile scrivere preferenze");}
    private static void restorePreferenceSnapshot(Context c,JSONObject oldPrefs){try{for(String name:PREFS){JSONObject p=oldPrefs.optJSONObject(name);if(p!=null)restorePrefs(c.getSharedPreferences(name,Context.MODE_PRIVATE),p,true);}}catch(Exception ignored){}}
    private static String sha256(String s)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");byte[] b=md.digest(s.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte x:b)out.append(String.format(java.util.Locale.US,"%02x",x&0xff));return out.toString();}
}
