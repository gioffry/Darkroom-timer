package it.darkroom.timer.assistant.data;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class AssistantDatabase extends SQLiteOpenHelper {
    public static final String PROCESSOR = "JOBO CPE2";
    public static final String METHOD = "rotazione continua";
    public static final double TEMP_MATCH_TOLERANCE_C = 0.2;

    public static final class SourceSnapshot {
        public String film="", format="", developer="", dilution="", processor=PROCESSOR, method=METHOD;
        public int nominalIso, exposedIso, originalSeconds;
        public double originalTemp;
        public String sourceName="", dataType="", sourceData="", calculation="";
        public String comboKey(){ return AssistantDatabase.comboKey(film,format,exposedIso,developer,dilution,processor,method); }
    }

    public static final class PersonalRecipe {
        public long id, createdAt, updatedAt;
        public SourceSnapshot source = new SourceSnapshot();
        public double personalTemp;
        public int personalSeconds;
        public String note="";
        public boolean favorite;
    }

    public static final class LogEntry {
        public long id, createdAt;
        public SourceSnapshot source = new SourceSnapshot();
        public double actualTemp, volumeMl, productMl, waterMl;
        public int actualSeconds, rolls=1, rating;
        public String timeOrigin="", capacityState="", capacityMessage="", notes="";
        public String comboKey(){ return source.comboKey(); }
    }

    public AssistantDatabase(Context context) { super(context, AssistantDataSchema.DB_NAME, null, AssistantDataSchema.VERSION); }

    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL(AssistantDataSchema.CREATE_RECIPES);
        db.execSQL(AssistantDataSchema.CREATE_LOGS);
        db.execSQL(AssistantDataSchema.CREATE_FAVORITE_INDEX);
        db.execSQL(AssistantDataSchema.CREATE_LOG_COMBO_INDEX);
        db.execSQL(AssistantDataSchema.CREATE_ORIGINAL_IMMUTABLE_TRIGGER);
    }

    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        if (oldVersion < 1) onCreate(db);
        // Future releases add migrations here. Never drop personal data.
    }

    public long saveRecipe(SourceSnapshot s, int seconds, double temp, String note, boolean favorite) {
        SQLiteDatabase db=getWritableDatabase(); db.beginTransaction();
        try {
            if(favorite) clearFavorite(db,s.comboKey());
            long now=System.currentTimeMillis(); ContentValues v=sourceValues(s);
            v.put("personal_temp",temp); v.put("personal_seconds",seconds); v.put("note",safe(note));
            v.put("favorite",favorite?1:0); v.put("created_at",now); v.put("updated_at",now);
            long id=db.insertOrThrow("personal_recipes",null,v); db.setTransactionSuccessful(); return id;
        } finally { db.endTransaction(); }
    }

    public void updateRecipe(long id,int seconds,double temp,String note,boolean favorite) {
        SQLiteDatabase db=getWritableDatabase(); db.beginTransaction();
        try {
            PersonalRecipe r=getRecipe(db,id); if(r==null) return;
            if(favorite) clearFavorite(db,r.source.comboKey());
            ContentValues v=new ContentValues(); v.put("personal_seconds",seconds); v.put("personal_temp",temp);
            v.put("note",safe(note)); v.put("favorite",favorite?1:0); v.put("updated_at",System.currentTimeMillis());
            db.update("personal_recipes",v,"id=?",new String[]{Long.toString(id)}); db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }

    public void setFavorite(long id,boolean favorite) {
        SQLiteDatabase db=getWritableDatabase(); db.beginTransaction();
        try { PersonalRecipe r=getRecipe(db,id); if(r==null)return; if(favorite)clearFavorite(db,r.source.comboKey());
            ContentValues v=new ContentValues(); v.put("favorite",favorite?1:0); v.put("updated_at",System.currentTimeMillis());
            db.update("personal_recipes",v,"id=?",new String[]{Long.toString(id)}); db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }

    public void resetOriginal(long id) {
        PersonalRecipe r=getRecipe(id); if(r==null)return;
        ContentValues v=new ContentValues(); v.put("personal_seconds",r.source.originalSeconds); v.put("personal_temp",r.source.originalTemp);
        v.put("note",""); v.put("updated_at",System.currentTimeMillis());
        getWritableDatabase().update("personal_recipes",v,"id=?",new String[]{Long.toString(id)});
    }

    public void deleteRecipe(long id){ getWritableDatabase().delete("personal_recipes","id=?",new String[]{Long.toString(id)}); }

    public PersonalRecipe getRecipe(long id){ return getRecipe(getReadableDatabase(),id); }
    private PersonalRecipe getRecipe(SQLiteDatabase db,long id){
        Cursor c=db.query("personal_recipes",null,"id=?",new String[]{Long.toString(id)},null,null,null);
        try { return c.moveToFirst()?readRecipe(c):null; } finally { c.close(); }
    }

    public List<PersonalRecipe> listRecipes(){
        ArrayList<PersonalRecipe> out=new ArrayList<>(); Cursor c=getReadableDatabase().query("personal_recipes",null,null,null,null,null,"updated_at DESC");
        try { while(c.moveToNext())out.add(readRecipe(c)); } finally { c.close(); } return out;
    }

    public PersonalRecipe findPreferred(String comboKey){
        Cursor c=getReadableDatabase().query("personal_recipes",null,"combo_key=? AND favorite=1",new String[]{comboKey},null,null,"updated_at DESC","1");
        try { return c.moveToFirst()?readRecipe(c):null; } finally { c.close(); }
    }

    public PersonalRecipe findLatest(String comboKey){
        Cursor c=getReadableDatabase().query("personal_recipes",null,"combo_key=?",new String[]{comboKey},null,null,"updated_at DESC","1");
        try { return c.moveToFirst()?readRecipe(c):null; } finally { c.close(); }
    }

    public long saveLog(LogEntry l){
        ContentValues v=sourceValues(l.source); v.put("created_at",l.createdAt>0?l.createdAt:System.currentTimeMillis());
        v.put("actual_temp",l.actualTemp); v.put("actual_seconds",l.actualSeconds); v.put("time_origin",safe(l.timeOrigin));
        v.put("source_seconds",l.source.originalSeconds); v.put("source_temp",l.source.originalTemp);
        v.put("volume_ml",l.volumeMl); v.put("product_ml",l.productMl); v.put("water_ml",l.waterMl); v.put("rolls",l.rolls);
        v.put("capacity_state",safe(l.capacityState)); v.put("capacity_message",safe(l.capacityMessage));
        v.put("rating",Math.max(0,Math.min(5,l.rating))); v.put("notes",safe(l.notes));
        v.remove("original_temp"); v.remove("original_seconds"); v.remove("favorite"); v.remove("personal_temp"); v.remove("personal_seconds"); v.remove("note"); v.remove("updated_at");
        return getWritableDatabase().insertOrThrow("development_logs",null,v);
    }

    public LogEntry getLog(long id){ Cursor c=getReadableDatabase().query("development_logs",null,"id=?",new String[]{Long.toString(id)},null,null,null);
        try{return c.moveToFirst()?readLog(c):null;}finally{c.close();}}
    public List<LogEntry> listLogs(){ return queryLogs(null,null); }
    public List<LogEntry> logsForCombo(String key){ return queryLogs("combo_key=?",new String[]{key}); }
    private List<LogEntry> queryLogs(String where,String[] args){ ArrayList<LogEntry> out=new ArrayList<>(); Cursor c=getReadableDatabase().query("development_logs",null,where,args,null,null,"created_at DESC");
        try{while(c.moveToNext())out.add(readLog(c));}finally{c.close();} return out; }

    public long recipeFromLog(long logId,boolean favorite){
        LogEntry l=getLog(logId); if(l==null)return -1;
        return saveRecipe(l.source,l.actualSeconds,l.actualTemp,l.notes,favorite);
    }

    public static boolean sameTemperature(double a,double b){ return Math.abs(a-b)<=TEMP_MATCH_TOLERANCE_C; }
    public static String comboKey(String film,String format,int exposedIso,String developer,String dilution,String processor,String method){
        return norm(film)+"|"+norm(format)+"|"+exposedIso+"|"+norm(developer)+"|"+norm(dilution)+"|"+norm(processor)+"|"+norm(method);
    }

    private void clearFavorite(SQLiteDatabase db,String key){ ContentValues v=new ContentValues(); v.put("favorite",0); db.update("personal_recipes",v,"combo_key=? AND favorite=1",new String[]{key}); }
    private static ContentValues sourceValues(SourceSnapshot s){ ContentValues v=new ContentValues(); v.put("combo_key",s.comboKey()); v.put("film",safe(s.film)); v.put("format",safe(s.format));
        v.put("nominal_iso",s.nominalIso); v.put("exposed_iso",s.exposedIso); v.put("developer",safe(s.developer)); v.put("dilution",safe(s.dilution)); v.put("processor",safe(s.processor)); v.put("method",safe(s.method));
        v.put("original_temp",s.originalTemp); v.put("original_seconds",s.originalSeconds); v.put("source_name",safe(s.sourceName)); v.put("data_type",safe(s.dataType)); v.put("source_data",safe(s.sourceData)); v.put("calculation",safe(s.calculation)); return v; }

    private static PersonalRecipe readRecipe(Cursor c){ PersonalRecipe r=new PersonalRecipe(); r.id=l(c,"id"); r.source=sourceFromRecipe(c); r.personalTemp=d(c,"personal_temp"); r.personalSeconds=i(c,"personal_seconds"); r.note=s(c,"note"); r.favorite=i(c,"favorite")==1; r.createdAt=l(c,"created_at"); r.updatedAt=l(c,"updated_at"); return r; }
    private static SourceSnapshot sourceFromRecipe(Cursor c){ SourceSnapshot x=new SourceSnapshot(); x.film=s(c,"film"); x.format=s(c,"format"); x.nominalIso=i(c,"nominal_iso"); x.exposedIso=i(c,"exposed_iso"); x.developer=s(c,"developer"); x.dilution=s(c,"dilution"); x.processor=s(c,"processor"); x.method=s(c,"method"); x.originalTemp=d(c,"original_temp"); x.originalSeconds=i(c,"original_seconds"); x.sourceName=s(c,"source_name"); x.dataType=s(c,"data_type"); x.sourceData=s(c,"source_data"); x.calculation=s(c,"calculation"); return x; }
    private static LogEntry readLog(Cursor c){ LogEntry l=new LogEntry(); l.id=l(c,"id"); l.createdAt=l(c,"created_at"); SourceSnapshot x=new SourceSnapshot(); x.film=s(c,"film"); x.format=s(c,"format"); x.nominalIso=i(c,"nominal_iso"); x.exposedIso=i(c,"exposed_iso"); x.developer=s(c,"developer"); x.dilution=s(c,"dilution"); x.processor=s(c,"processor"); x.method=s(c,"method"); x.originalTemp=d(c,"source_temp"); x.originalSeconds=i(c,"source_seconds"); x.sourceName=s(c,"source_name"); x.dataType=s(c,"data_type"); x.sourceData=s(c,"source_data"); x.calculation=s(c,"calculation"); l.source=x; l.actualTemp=d(c,"actual_temp"); l.actualSeconds=i(c,"actual_seconds"); l.timeOrigin=s(c,"time_origin"); l.volumeMl=d(c,"volume_ml"); l.productMl=d(c,"product_ml"); l.waterMl=d(c,"water_ml"); l.rolls=i(c,"rolls"); l.capacityState=s(c,"capacity_state"); l.capacityMessage=s(c,"capacity_message"); l.rating=i(c,"rating"); l.notes=s(c,"notes"); return l; }
    private static String s(Cursor c,String n){return c.getString(c.getColumnIndexOrThrow(n));} private static int i(Cursor c,String n){return c.getInt(c.getColumnIndexOrThrow(n));} private static long l(Cursor c,String n){return c.getLong(c.getColumnIndexOrThrow(n));} private static double d(Cursor c,String n){return c.getDouble(c.getColumnIndexOrThrow(n));}
    private static String safe(String s){return s==null?"":s;} private static String norm(String s){return safe(s).trim().toLowerCase(Locale.ITALY);}
}
