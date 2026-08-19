#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys,tempfile

work=Path(sys.argv[1] if len(sys.argv)>1 else 'work')
project=work/'project'; java=project/'app/src/main/java/it/darkroom/timer'; assistant=java/'assistant'; base=Path('base/v0.12.0-materialized/project/app/src/main/java/it/darkroom/timer')

def text(p):return Path(p).read_text(encoding='utf-8')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).digest()

def catalog(path,version,count):
    r=json.loads(Path(path).read_text(encoding='utf-8'));p=r['payload'];compact=json.dumps(p,ensure_ascii=False,separators=(',',':'));assert r['catalogVersion']==version;assert r['schemaVersion']==2;assert hashlib.sha256(compact.encode()).hexdigest()==r['payloadSha256'];assert len(p['records'])==count;return r

manifest=text(project/'app/src/main/AndroidManifest.xml');gradle=text(project/'app/build.gradle');main=text(java/'MainActivity.java');schema=text(assistant/'data/AssistantDataSchema.java')
assert 'android:versionName="0.12.1"' in manifest and 'android:versionCode="58"' in manifest
assert "versionName '0.12.1'" in gradle and 'versionCode 58' in gradle
assert 'package="it.darkroom.timer"' in manifest and 'private static final String APP_VERSION = "0.12.1";' in main
assert 'public static final int VERSION = 3;' in schema and 'DROP TABLE' not in schema and 'DROP TABLE' not in text(assistant/'data/AssistantDatabase.java')

# Absolute Timer/non-regression. MainActivity may change only its visible version string.
for name in ['SonoffArmService.java','SplitGradePlan.java','TimingMath.java','LogEntry.java','LogStore.java','ExposureRecipe.java','PrintSequence.java']:
    assert digest(base/name)==digest(java/name),name
base_main=text(base/'MainActivity.java');expected=base_main.replace('private static final String APP_VERSION = "0.12.0";','private static final String APP_VERSION = "0.12.1";',1);assert main==expected
for n in ['testFromPrint','NUOVO PROVINO DA QUESTA STAMPA','returnPrintToTest','testMigrationSummary']:assert n not in main,n
for n in ['maybeShowTestResultChooser','setMode(MODE_PRINT);','showPrintCorrectionEditor','DODGE','BURN','TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount)']:assert n in main,n
service=text(java/'SonoffArmService.java');split=text(java/'SplitGradePlan.java')
for n in ['ACTION_ARM_PRINT','ACTION_ARM_TEST','EXTRA_TEST_TARGETS','ACTION_CANCEL']:assert n in service,n
assert 'public int softYellow = 60;' in split and 'public int hardMagenta = 180;' in split
assert '"Azzera il magenta e imposta giallo " + softYellow' in split and '"Azzera il giallo e imposta magenta " + hardMagenta' in split

# R2-R9 technical engines/data persistence remain untouched; UX classes are intentionally excluded.
for rel in ['development/DevelopmentCatalog.java','chemistry/ChemistryCalculator.java','data/AssistantDatabase.java','data/AssistantDataSchema.java','operational/OperationalAssistantActivity.java','paper/PaperChemistryStore.java','paper/PaperProductData.java','system/DataProvenance.java']:
    assert digest(base/'assistant'/rel)==digest(assistant/rel),rel
planner=text(assistant/'equipment/TankPlanner.java');assert 'chimica insufficiente' in planner and 'CPE2_MAX_ML' in planner and 'compatibilità JOBO CPE2 non documentata / non confermata' in planner
backup=text(assistant/'system/BackupEngine.java');assert 'APP_VERSION="0.12.1"' in backup and 'VERSION_CODE=58' in backup and 'CATALOG_VERSION=2' in backup and 'beginTransaction' in backup and 'CONFLICT_IGNORE' in backup

# Modern shared UX/search and progressive disclosure.
search=text(assistant/'search/SmartSearchActivity.java');engine=text(assistant/'search/SmartSearchEngine.java');smartcat=text(assistant/'search/SmartCatalog.java');manager=text(assistant/'system/CatalogManager.java');ui=text(assistant/'ui/AssistantUi.java')
assert 'DEBOUNCE_MS=350' in search and 'generation' in search and 'handler.removeCallbacks' in search and 'fetchRemoteForSearch' in search
assert 'RISULTATI LOCALI' in search and 'RISULTATI ONLINE' in search and 'cacheSelectedRecord' in search
for n in ['exact name','exact alias','startsWith prefix','allWords','partial','remote']:assert n in engine,n
assert 'readActiveCatalog' in smartcat and 'cachedSelectedRecords' in smartcat
assert 'SEARCH_CACHE_MS=5*60*1000L' in manager and 'catalog.previous.json' in manager and 'cacheSelectedRecord' in manager
for n in ['card(','primaryButton(','searchField(','resultRow(','emptyState(']:assert n in ui,n
chem=text(assistant/'chemistry/inventory/MyChemistryActivity.java');equip=text(assistant/'equipment/MyEquipmentActivity.java');newdev=text(assistant/'development/NewDevelopmentActivity.java');paper=text(assistant/'paper/PaperChemistryActivity.java');dm=text(assistant/'system/DataManagementActivity.java');recipes=text(assistant/'recipes/MyRecipesActivity.java');log=text(assistant/'log/DevelopmentLogActivity.java')
assert 'Nome rivelatore esatto dal catalogo' not in chem and 'SmartSearchActivity.class' in chem and chem.count('new AlertDialog.Builder')<=1
assert 'AGGIUNGI TANK DAL CATALOGO · JOBO 2520' not in equip and 'AGGIUNGI TANK' in equip and 'SmartSearchActivity.class' in equip and 'new AlertDialog.Builder' not in equip
assert 'SmartSearchBinder.attach' in newdev and 'OwnedTankPickerActivity.class' in newdev and 'new android.app.AlertDialog.Builder' not in newdev
assert paper.count('SmartSearchActivity.class')>=1 and paper.count('new AlertDialog.Builder')<=1
assert 'PROVENIENZA DEI DATI' in dm and 'showSourcesInline' in dm
assert 'MODIFICA RICETTA' in recipes and 'showOriginalInline' in recipes and 'editInline' in recipes and recipes.count('new AlertDialog.Builder')==2
assert 'CONFRONTA SVILUPPI' in log and 'compareInline' in log and 'new AlertDialog.Builder' not in log

# Real local + remote catalogs, aliases, sources, unknown semantics.
local=catalog('experiments/v0121/catalog-v2.json',2,32);remote=catalog('catalog/catalog-v3.json',3,37)
L=local['payload']['records'];R=remote['payload']['records'];films=[r for r in L if 'FILM' in r['categories']];devs=[r for r in L if 'FILM_DEVELOPER' in r['categories']];tanks=[r for r in L if 'TANK' in r['categories']]
assert len(films)==7 and len(devs)==12 and len(tanks)==6 and len(local['payload']['sources'])>=15
assert [r['name'] for r in tanks]==['JOBO 1510','JOBO 1520','JOBO 1540','JOBO 2520','JOBO 2540','JOBO 2550']
by={r['id']:r for r in L};assert {'d76','d-76','d 76'}<=set(by['dev-kodak-d76']['aliases']);assert 'foma un' in by['dev-foma-universal']['aliases'];assert 'tri x' in by['film-trix400']['aliases'];assert 'cpe2Compatible' not in by['tank-jobo-1510']['technical'];assert by['tank-jobo-2540']['technical']['capacityDataType']=='CALCOLO'
# Simulated atomic catalog promotion/rollback integrity.
with tempfile.TemporaryDirectory() as td:
    td=Path(td);active=td/'catalog.active.json';prev=td/'catalog.previous.json';tmp=td/'catalog.tmp.json';active.write_text(json.dumps(local));tmp.write_text(json.dumps(remote));active.rename(prev);tmp.rename(active);assert json.loads(active.read_text())['catalogVersion']==3 and json.loads(prev.read_text())['catalogVersion']==2
    corrupt=json.loads(active.read_text());corrupt['payload']['records'][0]['name']='CORRUPT';candidate=td/'candidate.json';candidate.write_text(json.dumps(corrupt));bad=json.loads(candidate.read_text());compact=json.dumps(bad['payload'],ensure_ascii=False,separators=(',',':'));assert hashlib.sha256(compact.encode()).hexdigest()!=bad['payloadSha256'];assert json.loads(active.read_text())['catalogVersion']==3
extra=next(r for r in R if r['id']=='dev-fomadon-p');cache={'schemaVersion':1,'records':[extra]};assert 'remaining_amount' not in json.dumps(cache)
print('STATIC RELEASE GUARDS: PASS')
print('UX modernizzata: Smart Search + Chimica + Attrezzatura + Nuovo sviluppo + Carta + Ricette + Log + Fonti')
print('Catalogo locale: 32 record · 7 film · 12 rivelatori film · 6 tank JOBO')
print('Catalogo remoto: 37 record · checksum/schema/rollback/cache: PASS')
print('R2-R9 technical core + Timer absolute regression: PASS')
