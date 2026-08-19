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
    public static final String PROCESSOR="JOBO CPE2";
    public static final String METHOD="rotazione continua";
    public static final double TEMP_MATCH_TOLERANCE_C=0.2;
    public static final String SOURCE_CATALOG="CATALOG";
    public static final String SOURCE_USER="USER";

    public static final class SourceSnapshot {
        public String film="",format="",developer="",dilution="",processor=PROCESSOR,method=METHOD;
        public int nominalIso,exposedIso,originalSeconds; public double originalTemp;
        public String sourceName="",dataType="",sourceData="",calculation="";
        public String comboKey(){return AssistantDatabase.comboKey(film,format,exposedIso,developer,dilution,processor,method);}
    }
    public static final class PersonalRecipe {
        public long id,createdAt,updatedAt; public SourceSnapshot source=new SourceSnapshot();
        public double personalTemp; public int personalSeconds; public String note=""; public boolean favorite;
    }
    public static final class LogEntry {
        public long id,createdAt; public SourceSnapshot source=new SourceSnapshot();
        public double actualTemp,volumeMl,productMl,waterMl; public boolean productKnown,waterKnown;
        public int actualSeconds,rolls=1,rating; public String timeOrigin="",capacityState="",capacityMessage="",notes="";
        public String comboKey(){return source.comboKey();}
    }
    public static final class ChemicalItem {
        public long id,createdAt,updatedAt; public String sourceType=SOURCE_USER,sourceProductKey="",manufacturer="",name="",category="",physicalState="liquido",solutionType="concentrato",unit="ml";
        public double initialAmount,remainingAmount,capacityValue; public String purchaseDate="",openDate="",preparedDate="",expiryDate="",notes="",storage="",personalDilution="",documentedDilutions="",capacityUnit="",capacitySource="",sourceName="",dataType=""; public boolean archived;
        public String status(){ if(archived)return "archiviato"; if(remainingAmount<=0.0001)return "esaurito"; if(initialAmount>0&&remainingAmount<=initialAmount*0.15)return "quasi esaurito"; return "disponibile"; }
    }
    public static final class ChemicalUsage {
        public long id,createdAt,chemicalId,developmentLogId; public String productName="",developer="",dilution="",film="",format="",unit="ml",note=""; public int rolls; public double quantityUsed,remainingAfter;
    }
    public static final class TankItem {
        public long id,createdAt,updatedAt; public String sourceType=SOURCE_USER,sourceModelKey="",manufacturer="",model="",personalName="",notes="",system="",tankType="",technicalSource="",dataType=""; public int quantityOwned=1,capacity35,capacity120; public double minInversionMl,minRotationMl,maxVolumeMl; public boolean cpe2Compatible,liftCompatible;
        public String displayName(){String n=(personalName==null?"":personalName.trim());return n.isEmpty()?(manufacturer+" "+model).trim():n+" · "+manufacturer+" "+model;}
        public int capacityFor(String format){return "35 mm".equals(format)?capacity35:("120".equals(format)?capacity120:0);}
    }

    public AssistantDatabase(Context c){super(c,AssistantDataSchema.DB_NAME,null,AssistantDataSchema.VERSION);}
    @Override public void onCreate(SQLiteDatabase db){
        db.execSQL(AssistantDataSchema.CREATE_RECIPES); db.execSQL(AssistantDataSchema.CREATE_LOGS);
        createR5R6(db); createR7R8R9(db); db.execSQL(AssistantDataSchema.CREATE_FAVORITE_INDEX); db.execSQL(AssistantDataSchema.CREATE_LOG_COMBO_INDEX); db.execSQL(AssistantDataSchema.CREATE_ORIGINAL_IMMUTABLE_TRIGGER);
    }
    private static void createR5R6(SQLiteDatabase db){
        db.execSQL(AssistantDataSchema.CREATE_CHEMICALS); db.execSQL(AssistantDataSchema.CREATE_CHEMICAL_USAGE); db.execSQL(AssistantDataSchema.CREATE_EQUIPMENT); db.execSQL(AssistantDataSchema.CREATE_TANKS);
        db.execSQL(AssistantDataSchema.CREATE_CHEM_NAME_INDEX); db.execSQL(AssistantDataSchema.CREATE_USAGE_INDEX); db.execSQL(AssistantDataSchema.CREATE_TANK_INDEX);
    }
    private static void createR7R8R9(SQLiteDatabase db){
        db.execSQL(AssistantDataSchema.CREATE_ASSISTANT_SESSIONS);
        db.execSQL(AssistantDataSchema.CREATE_PAPER_SESSIONS);
        db.execSQL(AssistantDataSchema.CREATE_TECHNICAL_SOURCE_CACHE);
        db.execSQL(AssistantDataSchema.CREATE_SESSION_INDEX);
        db.execSQL(AssistantDataSchema.CREATE_PAPER_SESSION_INDEX);
        db.execSQL(AssistantDataSchema.CREATE_SOURCE_CACHE_INDEX);
    }
    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){
        if(oldVersion<1){onCreate(db);return;}
        if(oldVersion<2){
            db.execSQL("ALTER TABLE development_logs ADD COLUMN product_known INTEGER NOT NULL DEFAULT 0");
            db.execSQL("ALTER TABLE development_logs ADD COLUMN water_known INTEGER NOT NULL DEFAULT 0");
            db.execSQL("UPDATE development_logs SET product_known=1,water_known=1 WHERE product_ml>0 OR water_ml>0");
            createR5R6(db);
        }
        if(oldVersion<3){
            createR7R8R9(db);
        }
    }

    public long saveRecipe(SourceSnapshot s,int seconds,double temp,String note,boolean favorite){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{if(favorite)clearFavorite(db,s.comboKey());long now=System.currentTimeMillis();ContentValues v=sourceValues(s);v.put("personal_temp",temp);v.put("personal_seconds",seconds);v.put("note",safe(note));v.put("favorite",favorite?1:0);v.put("created_at",now);v.put("updated_at",now);long id=db.insertOrThrow("personal_recipes",null,v);db.setTransactionSuccessful();return id;}finally{db.endTransaction();}}
    public void updateRecipe(long id,int seconds,double temp,String note,boolean favorite){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{PersonalRecipe r=getRecipe(db,id);if(r==null)return;if(favorite)clearFavorite(db,r.source.comboKey());ContentValues v=new ContentValues();v.put("personal_seconds",seconds);v.put("personal_temp",temp);v.put("note",safe(note));v.put("favorite",favorite?1:0);v.put("updated_at",System.currentTimeMillis());db.update("personal_recipes",v,"id=?",new String[]{Long.toString(id)});db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public void setFavorite(long id,boolean favorite){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{PersonalRecipe r=getRecipe(db,id);if(r==null)return;if(favorite)clearFavorite(db,r.source.comboKey());ContentValues v=new ContentValues();v.put("favorite",favorite?1:0);v.put("updated_at",System.currentTimeMillis());db.update("personal_recipes",v,"id=?",new String[]{Long.toString(id)});db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public void resetOriginal(long id){PersonalRecipe r=getRecipe(id);if(r==null)return;ContentValues v=new ContentValues();v.put("personal_seconds",r.source.originalSeconds);v.put("personal_temp",r.source.originalTemp);v.put("note","");v.put("updated_at",System.currentTimeMillis());getWritableDatabase().update("personal_recipes",v,"id=?",new String[]{Long.toString(id)});}
    public void deleteRecipe(long id){getWritableDatabase().delete("personal_recipes","id=?",new String[]{Long.toString(id)});}
    public PersonalRecipe getRecipe(long id){return getRecipe(getReadableDatabase(),id);} private PersonalRecipe getRecipe(SQLiteDatabase db,long id){Cursor c=db.query("personal_recipes",null,"id=?",new String[]{Long.toString(id)},null,null,null);try{return c.moveToFirst()?readRecipe(c):null;}finally{c.close();}}
    public List<PersonalRecipe> listRecipes(){ArrayList<PersonalRecipe> out=new ArrayList<>();Cursor c=getReadableDatabase().query("personal_recipes",null,null,null,null,null,"updated_at DESC");try{while(c.moveToNext())out.add(readRecipe(c));}finally{c.close();}return out;}
    public PersonalRecipe findPreferred(String k){Cursor c=getReadableDatabase().query("personal_recipes",null,"combo_key=? AND favorite=1",new String[]{k},null,null,"updated_at DESC","1");try{return c.moveToFirst()?readRecipe(c):null;}finally{c.close();}}
    public PersonalRecipe findLatest(String k){Cursor c=getReadableDatabase().query("personal_recipes",null,"combo_key=?",new String[]{k},null,null,"updated_at DESC","1");try{return c.moveToFirst()?readRecipe(c):null;}finally{c.close();}}

    public long saveLog(LogEntry l){ContentValues v=sourceValues(l.source);v.put("created_at",l.createdAt>0?l.createdAt:System.currentTimeMillis());v.put("actual_temp",l.actualTemp);v.put("actual_seconds",l.actualSeconds);v.put("time_origin",safe(l.timeOrigin));v.put("source_seconds",l.source.originalSeconds);v.put("source_temp",l.source.originalTemp);v.put("volume_ml",l.volumeMl);v.put("product_ml",l.productMl);v.put("water_ml",l.waterMl);v.put("product_known",l.productKnown?1:0);v.put("water_known",l.waterKnown?1:0);v.put("rolls",l.rolls);v.put("capacity_state",safe(l.capacityState));v.put("capacity_message",safe(l.capacityMessage));v.put("rating",Math.max(0,Math.min(5,l.rating)));v.put("notes",safe(l.notes));for(String k:new String[]{"original_temp","original_seconds","favorite","personal_temp","personal_seconds","note","updated_at"})v.remove(k);return getWritableDatabase().insertOrThrow("development_logs",null,v);}
    public LogEntry getLog(long id){Cursor c=getReadableDatabase().query("development_logs",null,"id=?",new String[]{Long.toString(id)},null,null,null);try{return c.moveToFirst()?readLog(c):null;}finally{c.close();}}
    public List<LogEntry> listLogs(){return queryLogs(null,null);} public List<LogEntry> logsForCombo(String k){return queryLogs("combo_key=?",new String[]{k});}
    private List<LogEntry> queryLogs(String w,String[] a){ArrayList<LogEntry> out=new ArrayList<>();Cursor c=getReadableDatabase().query("development_logs",null,w,a,null,null,"created_at DESC");try{while(c.moveToNext())out.add(readLog(c));}finally{c.close();}return out;}
    public long recipeFromLog(long logId,boolean favorite){LogEntry l=getLog(logId);return l==null?-1:saveRecipe(l.source,l.actualSeconds,l.actualTemp,l.notes,favorite);}

    public long saveChemical(ChemicalItem x){long now=System.currentTimeMillis();ContentValues v=chemicalValues(x);v.put("created_at",x.createdAt>0?x.createdAt:now);v.put("updated_at",now);return getWritableDatabase().insertOrThrow("chemical_inventory",null,v);}
    public void updateChemical(ChemicalItem x){ContentValues v=chemicalValues(x);v.put("updated_at",System.currentTimeMillis());getWritableDatabase().update("chemical_inventory",v,"id=?",new String[]{Long.toString(x.id)});}
    public ChemicalItem getChemical(long id){Cursor c=getReadableDatabase().query("chemical_inventory",null,"id=?",new String[]{Long.toString(id)},null,null,null);try{return c.moveToFirst()?readChemical(c):null;}finally{c.close();}}
    public List<ChemicalItem> listChemicals(boolean includeArchived){ArrayList<ChemicalItem> out=new ArrayList<>();Cursor c=getReadableDatabase().query("chemical_inventory",null,includeArchived?null:"archived=0",null,null,null,"updated_at DESC");try{while(c.moveToNext())out.add(readChemical(c));}finally{c.close();}return out;}
    public ChemicalItem findChemicalForDeveloper(String developer){Cursor c=getReadableDatabase().query("chemical_inventory",null,"archived=0 AND lower(name)=lower(?)",new String[]{safe(developer).trim()},null,null,"updated_at DESC","1");try{return c.moveToFirst()?readChemical(c):null;}finally{c.close();}}
    public List<ChemicalUsage> listChemicalUsage(long chemicalId){ArrayList<ChemicalUsage> out=new ArrayList<>();Cursor c=getReadableDatabase().query("chemical_usage",null,"chemical_id=?",new String[]{Long.toString(chemicalId)},null,null,"created_at DESC");try{while(c.moveToNext())out.add(readUsage(c));}finally{c.close();}return out;}
    public long registerChemicalUsage(long chemicalId,long logId,double quantity,String unit,LogEntry log,String note){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{ChemicalItem x=getChemical(chemicalId);if(x==null||quantity<0)return-1;double after=Math.max(0,x.remainingAmount-quantity);ContentValues u=new ContentValues();u.put("created_at",System.currentTimeMillis());u.put("chemical_id",chemicalId);u.put("development_log_id",logId);u.put("product_name",x.name);u.put("developer",log==null?"":log.source.developer);u.put("dilution",log==null?"":log.source.dilution);u.put("film",log==null?"":log.source.film);u.put("format",log==null?"":log.source.format);u.put("rolls",log==null?0:log.rolls);u.put("quantity_used",quantity);u.put("unit",safe(unit));u.put("remaining_after",after);u.put("note",safe(note));long id=db.insertOrThrow("chemical_usage",null,u);ContentValues cv=new ContentValues();cv.put("remaining_amount",after);cv.put("updated_at",System.currentTimeMillis());db.update("chemical_inventory",cv,"id=?",new String[]{Long.toString(chemicalId)});db.setTransactionSuccessful();return id;}finally{db.endTransaction();}}

    public long saveTank(TankItem t){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{long now=System.currentTimeMillis();ContentValues e=new ContentValues();e.put("created_at",t.createdAt>0?t.createdAt:now);e.put("updated_at",now);e.put("category","TANK");e.put("source_type",safe(t.sourceType));e.put("source_model_key",safe(t.sourceModelKey));e.put("manufacturer",safe(t.manufacturer));e.put("model",safe(t.model));e.put("personal_name",safe(t.personalName));e.put("quantity_owned",Math.max(1,t.quantityOwned));e.put("notes",safe(t.notes));long id=db.insertOrThrow("personal_equipment",null,e);ContentValues v=tankValues(t);v.put("equipment_id",id);db.insertOrThrow("personal_tanks",null,v);db.setTransactionSuccessful();return id;}finally{db.endTransaction();}}
    public TankItem getTank(long id){String sql="SELECT e.*,t.system,t.tank_type,t.capacity_35,t.capacity_120,t.min_inversion_ml,t.min_rotation_ml,t.max_volume_ml,t.cpe2_compatible,t.lift_compatible,t.technical_source,t.data_type FROM personal_equipment e JOIN personal_tanks t ON t.equipment_id=e.id WHERE e.id=?";Cursor c=getReadableDatabase().rawQuery(sql,new String[]{Long.toString(id)});try{return c.moveToFirst()?readTank(c):null;}finally{c.close();}}
    public List<TankItem> listTanks(){ArrayList<TankItem> out=new ArrayList<>();String sql="SELECT e.*,t.system,t.tank_type,t.capacity_35,t.capacity_120,t.min_inversion_ml,t.min_rotation_ml,t.max_volume_ml,t.cpe2_compatible,t.lift_compatible,t.technical_source,t.data_type FROM personal_equipment e JOIN personal_tanks t ON t.equipment_id=e.id WHERE e.category='TANK' ORDER BY e.updated_at DESC";Cursor c=getReadableDatabase().rawQuery(sql,null);try{while(c.moveToNext())out.add(readTank(c));}finally{c.close();}return out;}

    public static boolean sameTemperature(double a,double b){return Math.abs(a-b)<=TEMP_MATCH_TOLERANCE_C;}
    public static String comboKey(String film,String format,int exposedIso,String developer,String dilution,String processor,String method){return norm(film)+"|"+norm(format)+"|"+exposedIso+"|"+norm(developer)+"|"+norm(dilution)+"|"+norm(processor)+"|"+norm(method);}
    private void clearFavorite(SQLiteDatabase db,String k){ContentValues v=new ContentValues();v.put("favorite",0);db.update("personal_recipes",v,"combo_key=? AND favorite=1",new String[]{k});}
    private static ContentValues sourceValues(SourceSnapshot s){ContentValues v=new ContentValues();v.put("combo_key",s.comboKey());v.put("film",safe(s.film));v.put("format",safe(s.format));v.put("nominal_iso",s.nominalIso);v.put("exposed_iso",s.exposedIso);v.put("developer",safe(s.developer));v.put("dilution",safe(s.dilution));v.put("processor",safe(s.processor));v.put("method",safe(s.method));v.put("original_temp",s.originalTemp);v.put("original_seconds",s.originalSeconds);v.put("source_name",safe(s.sourceName));v.put("data_type",safe(s.dataType));v.put("source_data",safe(s.sourceData));v.put("calculation",safe(s.calculation));return v;}
    private static ContentValues chemicalValues(ChemicalItem x){ContentValues v=new ContentValues();v.put("source_type",safe(x.sourceType));v.put("source_product_key",safe(x.sourceProductKey));v.put("manufacturer",safe(x.manufacturer));v.put("name",safe(x.name));v.put("category",safe(x.category));v.put("physical_state",safe(x.physicalState));v.put("solution_type",safe(x.solutionType));v.put("initial_amount",x.initialAmount);v.put("remaining_amount",x.remainingAmount);v.put("unit",safe(x.unit));v.put("purchase_date",safe(x.purchaseDate));v.put("open_date",safe(x.openDate));v.put("prepared_date",safe(x.preparedDate));v.put("expiry_date",safe(x.expiryDate));v.put("notes",safe(x.notes));v.put("storage",safe(x.storage));v.put("personal_dilution",safe(x.personalDilution));v.put("documented_dilutions",safe(x.documentedDilutions));v.put("capacity_value",x.capacityValue);v.put("capacity_unit",safe(x.capacityUnit));v.put("capacity_source",safe(x.capacitySource));v.put("source_name",safe(x.sourceName));v.put("data_type",safe(x.dataType));v.put("archived",x.archived?1:0);return v;}
    private static ContentValues tankValues(TankItem t){ContentValues v=new ContentValues();v.put("system",safe(t.system));v.put("tank_type",safe(t.tankType));v.put("capacity_35",t.capacity35);v.put("capacity_120",t.capacity120);v.put("min_inversion_ml",t.minInversionMl);v.put("min_rotation_ml",t.minRotationMl);v.put("max_volume_ml",t.maxVolumeMl);v.put("cpe2_compatible",t.cpe2Compatible?1:0);v.put("lift_compatible",t.liftCompatible?1:0);v.put("technical_source",safe(t.technicalSource));v.put("data_type",safe(t.dataType));return v;}
    private static PersonalRecipe readRecipe(Cursor c){PersonalRecipe r=new PersonalRecipe();r.id=l(c,"id");r.source=sourceFromRecipe(c);r.personalTemp=d(c,"personal_temp");r.personalSeconds=i(c,"personal_seconds");r.note=s(c,"note");r.favorite=i(c,"favorite")==1;r.createdAt=l(c,"created_at");r.updatedAt=l(c,"updated_at");return r;}
    private static SourceSnapshot sourceFromRecipe(Cursor c){SourceSnapshot x=new SourceSnapshot();x.film=s(c,"film");x.format=s(c,"format");x.nominalIso=i(c,"nominal_iso");x.exposedIso=i(c,"exposed_iso");x.developer=s(c,"developer");x.dilution=s(c,"dilution");x.processor=s(c,"processor");x.method=s(c,"method");x.originalTemp=d(c,"original_temp");x.originalSeconds=i(c,"original_seconds");x.sourceName=s(c,"source_name");x.dataType=s(c,"data_type");x.sourceData=s(c,"source_data");x.calculation=s(c,"calculation");return x;}
    private static LogEntry readLog(Cursor c){LogEntry l=new LogEntry();l.id=l(c,"id");l.createdAt=l(c,"created_at");SourceSnapshot x=new SourceSnapshot();x.film=s(c,"film");x.format=s(c,"format");x.nominalIso=i(c,"nominal_iso");x.exposedIso=i(c,"exposed_iso");x.developer=s(c,"developer");x.dilution=s(c,"dilution");x.processor=s(c,"processor");x.method=s(c,"method");x.originalTemp=d(c,"source_temp");x.originalSeconds=i(c,"source_seconds");x.sourceName=s(c,"source_name");x.dataType=s(c,"data_type");x.sourceData=s(c,"source_data");x.calculation=s(c,"calculation");l.source=x;l.actualTemp=d(c,"actual_temp");l.actualSeconds=i(c,"actual_seconds");l.timeOrigin=s(c,"time_origin");l.volumeMl=d(c,"volume_ml");l.productMl=d(c,"product_ml");l.waterMl=d(c,"water_ml");l.productKnown=i(c,"product_known")==1;l.waterKnown=i(c,"water_known")==1;l.rolls=i(c,"rolls");l.capacityState=s(c,"capacity_state");l.capacityMessage=s(c,"capacity_message");l.rating=i(c,"rating");l.notes=s(c,"notes");return l;}
    private static ChemicalItem readChemical(Cursor c){ChemicalItem x=new ChemicalItem();x.id=l(c,"id");x.createdAt=l(c,"created_at");x.updatedAt=l(c,"updated_at");x.sourceType=s(c,"source_type");x.sourceProductKey=s(c,"source_product_key");x.manufacturer=s(c,"manufacturer");x.name=s(c,"name");x.category=s(c,"category");x.physicalState=s(c,"physical_state");x.solutionType=s(c,"solution_type");x.initialAmount=d(c,"initial_amount");x.remainingAmount=d(c,"remaining_amount");x.unit=s(c,"unit");x.purchaseDate=s(c,"purchase_date");x.openDate=s(c,"open_date");x.preparedDate=s(c,"prepared_date");x.expiryDate=s(c,"expiry_date");x.notes=s(c,"notes");x.storage=s(c,"storage");x.personalDilution=s(c,"personal_dilution");x.documentedDilutions=s(c,"documented_dilutions");x.capacityValue=d(c,"capacity_value");x.capacityUnit=s(c,"capacity_unit");x.capacitySource=s(c,"capacity_source");x.sourceName=s(c,"source_name");x.dataType=s(c,"data_type");x.archived=i(c,"archived")==1;return x;}
    private static ChemicalUsage readUsage(Cursor c){ChemicalUsage x=new ChemicalUsage();x.id=l(c,"id");x.createdAt=l(c,"created_at");x.chemicalId=l(c,"chemical_id");x.developmentLogId=l(c,"development_log_id");x.productName=s(c,"product_name");x.developer=s(c,"developer");x.dilution=s(c,"dilution");x.film=s(c,"film");x.format=s(c,"format");x.rolls=i(c,"rolls");x.quantityUsed=d(c,"quantity_used");x.unit=s(c,"unit");x.remainingAfter=d(c,"remaining_after");x.note=s(c,"note");return x;}
    private static TankItem readTank(Cursor c){TankItem t=new TankItem();t.id=l(c,"id");t.createdAt=l(c,"created_at");t.updatedAt=l(c,"updated_at");t.sourceType=s(c,"source_type");t.sourceModelKey=s(c,"source_model_key");t.manufacturer=s(c,"manufacturer");t.model=s(c,"model");t.personalName=s(c,"personal_name");t.quantityOwned=i(c,"quantity_owned");t.notes=s(c,"notes");t.system=s(c,"system");t.tankType=s(c,"tank_type");t.capacity35=i(c,"capacity_35");t.capacity120=i(c,"capacity_120");t.minInversionMl=d(c,"min_inversion_ml");t.minRotationMl=d(c,"min_rotation_ml");t.maxVolumeMl=d(c,"max_volume_ml");t.cpe2Compatible=i(c,"cpe2_compatible")==1;t.liftCompatible=i(c,"lift_compatible")==1;t.technicalSource=s(c,"technical_source");t.dataType=s(c,"data_type");return t;}
    private static String s(Cursor c,String n){return c.getString(c.getColumnIndexOrThrow(n));} private static int i(Cursor c,String n){return c.getInt(c.getColumnIndexOrThrow(n));} private static long l(Cursor c,String n){return c.getLong(c.getColumnIndexOrThrow(n));} private static double d(Cursor c,String n){return c.getDouble(c.getColumnIndexOrThrow(n));}
    private static String safe(String x){return x==null?"":x;} private static String norm(String x){return safe(x).trim().toLowerCase(Locale.ITALY);}
}
