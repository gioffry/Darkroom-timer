#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / "project"
app = project / "app"
java = app / "src/main/java/it/darkroom/timer"
manifest = app / "src/main/AndroidManifest.xml"
gradle = app / "build.gradle"
build = work / "build_darkroom.py"
main = java / "MainActivity.java"
backup = java / "assistant/system/BackupEngine.java"
engine = java / "assistant/search/SmartSearchEngine.java"
binder = java / "assistant/search/SmartSearchBinder.java"
catalog = java / "assistant/search/SmartCatalog.java"
paper_activity = java / "assistant/paper/PaperChemistryActivity.java"
paper_store = java / "assistant/paper/PaperChemistryStore.java"
prepare = java / "assistant/chemistry/PrepareChemistryActivity.java"

def rd(p):
    return Path(p).read_text(encoding="utf-8")

def wr(p, s):
    Path(p).write_text(s, encoding="utf-8")

def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f"v0.12.2 {label}: atteso >= {count}, trovato {n}")
    wr(p, s.replace(old, new, count))
    print("v0.12.2 OK", label, flush=True)

checks = [
    (manifest, 'android:versionName="0.12.1"'),
    (manifest, 'android:versionCode="58"'),
    (main, 'private static final String APP_VERSION = "0.12.1";'),
    (backup, 'public static final String APP_VERSION="0.12.1";'),
    (backup, 'public static final int VERSION_CODE=58;'),
]
for p, needle in checks:
    if needle not in rd(p):
        raise SystemExit("v0.12.2 BASE v0.12.1 non riconosciuta: " + needle)

s = rd(build)
required = ['VERSION_NAME = "0.12.1"', 'VERSION_CODE = "58"']
for needle in required:
    if needle not in s:
        raise SystemExit("v0.12.2 builder base non riconosciuta: " + needle)
s = s.replace('VERSION_NAME = "0.12.1"', 'VERSION_NAME = "0.12.2"')
s = s.replace('VERSION_CODE = "58"', 'VERSION_CODE = "59"')
s = s.replace('[Darkroom v0.12.1]', '[Darkroom v0.12.2]')
s = s.replace('versionCode 58', 'versionCode 59')
s = s.replace(r'versionCode\s+58\b', r'versionCode\s+59\b')
s = s.replace('0.12.1', '0.12.2')
wr(build, s)

rep(gradle, "versionCode 58\n        versionName '0.12.1'",
    "versionCode 59\n        versionName '0.12.2'", "Gradle version")
rep(manifest, 'android:versionCode="58"\n    android:versionName="0.12.1"',
    'android:versionCode="59"\n    android:versionName="0.12.2"', "manifest version")
rep(main, 'private static final String APP_VERSION = "0.12.1";',
    'private static final String APP_VERSION = "0.12.2";', "Timer footer version")
rep(backup, 'public static final String APP_VERSION="0.12.1";',
    'public static final String APP_VERSION="0.12.2";', "backup app version")
rep(backup, 'public static final int VERSION_CODE=58;',
    'public static final int VERSION_CODE=59;', "backup versionCode")

item_anchor = '''            this.subtitle=safe(subtitle);this.origin=safe(origin);this.recordJson=safe(recordJson);this.remote=remote;
        }
        public boolean hasCategory(String category){'''
item_fixed = '''            this.subtitle=safe(subtitle);this.origin=safe(origin);this.recordJson=safe(recordJson);this.remote=remote;
        }
        @Override public String toString(){return name;}
        public boolean hasCategory(String category){'''
rep(engine, item_anchor, item_fixed, "SmartSearch Item human-readable toString")

filter_old = '''        @Override public Filter getFilter(){return new Filter(){@Override protected FilterResults performFiltering(CharSequence constraint){FilterResults r=new FilterResults();r.values=new ArrayList<>(rows);r.count=rows.size();return r;}@Override protected void publishResults(CharSequence constraint,FilterResults results){notifyDataSetChanged();}};}'''
filter_new = '''        @Override public Filter getFilter(){return new Filter(){@Override public CharSequence convertResultToString(Object resultValue){return resultValue instanceof SmartSearchEngine.Item?((SmartSearchEngine.Item)resultValue).name:super.convertResultToString(resultValue);}@Override protected FilterResults performFiltering(CharSequence constraint){FilterResults r=new FilterResults();r.values=new ArrayList<>(rows);r.count=rows.size();return r;}@Override protected void publishResults(CharSequence constraint,FilterResults results){notifyDataSetChanged();}};}'''
rep(binder, filter_old, filter_new, "AutoComplete explicit result-to-name conversion")

label_old = '''    public static String categoryLabel(SmartSearchEngine.Item i){if(i.categories.isEmpty())return "Catalogo tecnico";String c=i.categories.get(0);if("FILM".equals(c))return "Pellicola";if("FILM_DEVELOPER".equals(c))return "Rivelatore pellicola";if("PAPER".equals(c))return "Carta";if("PAPER_DEVELOPER".equals(c))return "Rivelatore carta";if("STOP_BATH".equals(c))return "Arresto";if("FIXER".equals(c))return "Fissaggio";if("WETTING_AGENT".equals(c))return "Imbibente";if("TANK".equals(c))return "Tank";if("PROCESSOR".equals(c))return "Processore";return c;}'''
label_new = '''    public static String categoryLabel(SmartSearchEngine.Item i){if(i.categories.isEmpty())return "Catalogo tecnico";boolean filmDev=i.hasCategory("FILM_DEVELOPER"),paperDev=i.hasCategory("PAPER_DEVELOPER");if(filmDev&&paperDev)return "Rivelatore pellicola / carta";if(i.hasCategory("FILM"))return "Pellicola";if(filmDev)return "Rivelatore pellicola";if(i.hasCategory("PAPER"))return "Carta";if(paperDev)return "Rivelatore carta";if(i.hasCategory("STOP_BATH"))return "Arresto";if(i.hasCategory("FIXER"))return "Fissaggio";if(i.hasCategory("WETTING_AGENT"))return "Imbibente";if(i.hasCategory("TANK"))return "Tank";if(i.hasCategory("PROCESSOR"))return "Processore";return i.categories.get(0);}'''
rep(catalog, label_old, label_new, "multifunction category label")

stock_old = '''        String d=dilution.trim().replace(" ","");
        String[] p=d.split("\\\\+");'''
stock_new = '''        String d=dilution.trim().replace(" ","");
        if("stock".equalsIgnoreCase(d)){r.productMl=totalMl;r.waterMl=0;r.known=true;r.message="USO STOCK";return r;}
        String[] p=d.split("\\\\+");'''
rep(paper_store, stock_old, stock_new, "paper chemistry stock calculation")

rep(paper_activity,
    'import it.darkroom.timer.assistant.search.SmartSearchActivity;\n',
    'import it.darkroom.timer.assistant.search.SmartSearchActivity;\nimport it.darkroom.timer.assistant.search.SmartSearchEngine;\n',
    "paper chemistry SmartSearchEngine import")

load_old = '''    private void load(){PaperChemistryStore.Session x=PaperChemistryStore.load(this);paperName.setText(empty(x.paper)?PaperChemistryStore.PAPER_DEFAULT:x.paper);volume.setText(x.volumeMl>0?fmt(x.volumeMl):"");set(devName,x.developer,"NON CONFIGURATO");devDil.setText(x.developerDilution);devOrigin.setText(emptyOr(x.developerOrigin,"NON DOCUMENTATO"));set(stopName,x.stop,"NON CONFIGURATO");stopDil.setText(x.stopDilution);stopOrigin.setText(emptyOr(x.stopOrigin,"NON DOCUMENTATO"));set(fixName,x.fixer,"NON CONFIGURATO");fixDil.setText(x.fixerDilution);fixOrigin.setText(emptyOr(x.fixerOrigin,"NON DOCUMENTATO"));notes.setText(x.notes);}'''
load_new = '''    private void load(){PaperChemistryStore.Session x=PaperChemistryStore.load(this);paperName.setText(empty(x.paper)?PaperChemistryStore.PAPER_DEFAULT:x.paper);volume.setText(x.volumeMl>0?fmt(x.volumeMl):"");set(devName,x.developer,"NON CONFIGURATO");devDil.setText(x.developerDilution);devOrigin.setText(emptyOr(x.developerOrigin,"NON DOCUMENTATO"));set(stopName,x.stop,"NON CONFIGURATO");stopDil.setText(x.stopDilution);stopOrigin.setText(emptyOr(x.stopOrigin,"NON DOCUMENTATO"));set(fixName,x.fixer,"NON CONFIGURATO");fixDil.setText(x.fixerDilution);fixOrigin.setText(emptyOr(x.fixerOrigin,"NON DOCUMENTATO"));notes.setText(x.notes);hydrateCatalogDefaults(devName,devOrigin,devDil,"PAPER_DEVELOPER",true);hydrateCatalogDefaults(stopName,stopOrigin,stopDil,"STOP_BATH",false);hydrateCatalogDefaults(fixName,fixOrigin,fixDil,"FIXER",false);}
    private void hydrateCatalogDefaults(TextView name,TextView origin,EditText dilution,String category,boolean paper){String q=name.getText().toString();if(empty(q)||"NON CONFIGURATO".equals(q))return;SmartSearchEngine.Item item=SmartCatalog.findLocal(this,q,category);if(item==null)return;JSONObject r=SmartCatalog.record(item);name.setText(item.name);String src=origin.getText().toString();if(empty(src)||"NON DOCUMENTATO".equals(src))origin.setText(SmartCatalog.sourceDetail(r));String[] ds=SmartCatalog.dilutions(r,paper);if(empty(dilution.getText().toString())&&ds.length==1)dilution.setText(ds[0]);}'''
rep(paper_activity, load_old, load_new, "restore documented paper chemistry defaults")

manual_old = '''if(data.getBooleanExtra(SmartSearchActivity.RESULT_MANUAL,false)){toast("Puoi digitare manualmente il nome/diluizione nei dati sessione soltanto se il catalogo non contiene il prodotto.");return;}'''
manual_new = '''if(data.getBooleanExtra(SmartSearchActivity.RESULT_MANUAL,false)){manualEntry(request);return;}'''
rep(paper_activity, manual_old, manual_new, "paper chemistry manual fallback")

manual_anchor = '''    private void load(){'''
manual_method = '''    private void manualEntry(int request){final EditText n=AssistantUi.field(this,request==PICK_PAPER?"Nome carta":"Nome prodotto");final EditText d=AssistantUi.field(this,"Diluizione (es. stock, 1+19)");LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);int pad=AssistantUi.dp(this,16);box.setPadding(pad,pad,pad,0);box.addView(n,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,8));if(request!=PICK_PAPER)box.addView(d,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,0));new AlertDialog.Builder(this).setTitle("INSERIMENTO MANUALE").setMessage("Usa questa modalità solo se il catalogo non contiene il prodotto. I dati manuali restano esplicitamente non documentati.").setView(box).setPositiveButton("USA",(dialog,which)->{String name=n.getText().toString().trim();if(empty(name)){toast("Nome prodotto mancante");return;}if(request==PICK_PAPER){paperName.setText(name);}else{TextView targetName=request==PICK_DEV?devName:request==PICK_STOP?stopName:fixName;TextView targetOrigin=request==PICK_DEV?devOrigin:request==PICK_STOP?stopOrigin:fixOrigin;EditText targetDil=request==PICK_DEV?devDil:request==PICK_STOP?stopDil:fixDil;targetName.setText(name);targetOrigin.setText("INSERITO MANUALMENTE · NON DOCUMENTATO");targetDil.setText(d.getText().toString().trim());}refreshPreview();}).setNegativeButton("ANNULLA",null).show();}

'''
rep(paper_activity, manual_anchor, manual_method + manual_anchor, "working manual paper chemistry entry")

rep(prepare, "/** Funzione autonoma PREPARA CHIMICA — Release 3/9. */",
    "/** Funzione autonoma PREPARA CHIMICA — Assistant completo 9/9. */", "Prepare Chemistry comment")
rep(prepare, 'TextView eyebrow=text("DARKROOM ASSISTANT · 3/9",12,accent,true);',
    'TextView eyebrow=text("DARKROOM ASSISTANT · 9/9",12,accent,true);', "Prepare Chemistry 9/9 label")

if 'public static final int VERSION = 3;' not in rd(java / "assistant/data/AssistantDataSchema.java"):
    raise SystemExit("v0.12.2 database schema changed unexpectedly")
if 'testFromPrint' in rd(main) or 'NUOVO PROVINO DA QUESTA STAMPA' in rd(main):
    raise SystemExit("v0.12.2 regression: STAMPA->PROVINO reappeared")
if 'package="it.darkroom.timer"' not in rd(manifest):
    raise SystemExit("v0.12.2 package changed")

print("v0.12.2 TRANSFORM OK — real-device Smart Search and chemistry repairs applied", flush=True)
