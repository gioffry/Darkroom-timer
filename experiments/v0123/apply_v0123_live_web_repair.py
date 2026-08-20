#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; java=app/'src/main/java/it/darkroom/timer'
manifest=app/'src/main/AndroidManifest.xml'; gradle=app/'build.gradle'; build=work/'build_darkroom.py'; main=java/'MainActivity.java'; backup=java/'assistant/system/BackupEngine.java'
newdev=java/'assistant/development/NewDevelopmentActivity.java'; search=java/'assistant/search/SmartSearchActivity.java'; here=Path(__file__).parent

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n<count: raise SystemExit(f'v0.12.3 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.12.3 OK',label,flush=True)
def rrep(p,pat,new,label,count=1,flags=re.S):
    s=rd(p); out,n=re.subn(pat,new,s,count=count,flags=flags)
    if n!=count: raise SystemExit(f'v0.12.3 {label}: regex {n}, attesa {count}')
    wr(p,out); print('v0.12.3 OK',label,flush=True)

for p,needle in [(manifest,'android:versionName="0.12.2"'),(manifest,'android:versionCode="59"'),(main,'private static final String APP_VERSION = "0.12.2";'),(backup,'public static final String APP_VERSION="0.12.2";'),(backup,'public static final int VERSION_CODE=59;')]:
    if needle not in rd(p): raise SystemExit('v0.12.3 BASE v0.12.2 non riconosciuta: '+needle)

s=rd(build)
for needle in ['VERSION_NAME = "0.12.2"','VERSION_CODE = "59"']:
    if needle not in s: raise SystemExit('v0.12.3 builder base non riconosciuta: '+needle)
s=s.replace('VERSION_NAME = "0.12.2"','VERSION_NAME = "0.12.3"').replace('VERSION_CODE = "59"','VERSION_CODE = "60"').replace('[Darkroom v0.12.2]','[Darkroom v0.12.3]').replace('versionCode 59','versionCode 60').replace(r'versionCode\s+59\b',r'versionCode\s+60\b').replace('0.12.2','0.12.3')
wr(build,s)
rep(gradle,"versionCode 59\n        versionName '0.12.2'","versionCode 60\n        versionName '0.12.3'",'Gradle version')
rep(manifest,'android:versionCode="59"\n    android:versionName="0.12.2"','android:versionCode="60"\n    android:versionName="0.12.3"','manifest version')
rep(main,'private static final String APP_VERSION = "0.12.2";','private static final String APP_VERSION = "0.12.3";','Timer footer version')
rep(backup,'public static final String APP_VERSION="0.12.2";','public static final String APP_VERSION="0.12.3";','backup app version')
rep(backup,'public static final int VERSION_CODE=59;','public static final int VERSION_CODE=60;','backup versionCode')

# Add the pure parser and Android live resolver. No manual product creation is introduced.
for p in (here/'src').rglob('*.java'):
    dst=app/'src/main/java'/p.relative_to(here/'src'); wr(dst,rd(p)); print('v0.12.3 source',p.relative_to(here/'src'),flush=True)

# A selected film must populate ISO from the Smart Catalog record itself, then fall back to the legacy development table only for timing logic.
film_method='''    private void onFilmChanged() {
        it.darkroom.timer.assistant.search.SmartSearchEngine.Item smart=it.darkroom.timer.assistant.search.SmartCatalog.findLocal(this,filmField.getText().toString(),"FILM");
        int nominal=0; boolean supports120=true;
        if(smart!=null){org.json.JSONObject rec=it.darkroom.timer.assistant.search.SmartCatalog.record(smart);org.json.JSONObject tech=it.darkroom.timer.assistant.search.SmartCatalog.technical(rec);nominal=tech.optInt("nominalIso",0);org.json.JSONArray formats=tech.optJSONArray("formats");if(formats!=null&&formats.length()>0){supports120=false;for(int i=0;i<formats.length();i++)if(formats.optString(i,"").contains("120"))supports120=true;}}
        String canonical=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,filmField.getText().toString(),"FILM");
        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(canonical);
        if(nominal<=0&&film!=null)nominal=film.nominalIso;
        if(nominal<=0){nominalIsoText.setText("—");return;}
        nominalIsoText.setText(Integer.toString(nominal));
        exposedIsoField.setText(Integer.toString(nominal));
        if((film!=null&&!film.format120||!supports120)&&"120".equals(selectedFormat))selectFormat("35 mm");
        refreshDilutions();
    }

    private void refreshDilutions'''
rrep(newdev,r'    private void onFilmChanged\(\) \{.*?\n    \}\n\n    private void refreshDilutions',film_method,'Smart Catalog ISO propagation')

# Manual insertion is prohibited: every picker must use catalog/local or automatic Internet discovery.
rep(search,'allowManual=getIntent().getBooleanExtra(EXTRA_ALLOW_MANUAL,true);','allowManual=false;','disable manual creation globally')

remote_method='''    private void requestRemote(){
        final int token=generation;final String q=query();if(q.isEmpty())return;status.setText("Catalogo locale · controllo catalogo online…");
        CatalogManager.fetchRemoteForSearch(this,(raw,error)->{
            if(token!=generation||!q.equals(query()))return;
            if(error==null&&raw!=null){
                List<SmartSearchEngine.Item> remote=SmartCatalog.onlineItems(raw);HashSet<String> localIds=new HashSet<>();for(SmartSearchEngine.Item i:localItems)localIds.add(i.id);ArrayList<SmartSearchEngine.Item> extra=new ArrayList<>();for(SmartSearchEngine.Item i:remote)if(!localIds.contains(i.id))extra.add(i);
                List<SmartSearchEngine.Result> rows=SmartSearchEngine.search(extra,q,categories,5);onlineBox.removeAllViews();if(!rows.isEmpty()){onlineTitle.setVisibility(View.VISIBLE);for(SmartSearchEngine.Result r:rows)addResult(onlineBox,r.item);status.setText("Catalogo locale + risultati online");return;}
            }
            requestLiveWeb(token,q);
        });
    }

    private void requestLiveWeb(final int token,final String q){
        status.setText("Prodotto non presente nel catalogo · ricerca Internet automatica…");onlineBox.removeAllViews();onlineTitle.setVisibility(View.GONE);
        WebProductResolver.resolve(this,q,categories,(items,error)->{
            if(token!=generation||!q.equals(query()))return;onlineBox.removeAllViews();
            if(items==null||items.isEmpty()){onlineTitle.setVisibility(View.GONE);status.setText(error==null?"Nessun risultato attendibile trovato sul Web":"Ricerca Internet non riuscita · "+error);return;}
            onlineTitle.setText("RISULTATI DAL WEB");onlineTitle.setVisibility(View.VISIBLE);for(SmartSearchEngine.Item item:items)addResult(onlineBox,item);status.setText("Prodotto trovato sul Web · fonte conservata · puoi correggere dopo la selezione");
        });
    }

    private void addResult'''
rrep(search,r'    private void requestRemote\(\)\{.*?\n    \}\n\n    private void addResult',remote_method,'live Internet fallback')

return_methods='''    private void returnItem(SmartSearchEngine.Item item){
        if(item!=null&&item.origin.startsWith("RICERCA WEB LIVE")){confirmWebItem(item);return;}returnItemDirect(item);
    }
    private void returnItemDirect(SmartSearchEngine.Item item){if(item.remote)try{CatalogManager.cacheSelectedRecord(this,new JSONObject(item.recordJson));}catch(Exception ignored){}Intent out=new Intent();out.putExtra(RESULT_RECORD,item.recordJson);out.putExtra(RESULT_NAME,item.name);out.putExtra(RESULT_ID,item.id);out.putExtra(RESULT_ORIGIN,item.origin);setResult(RESULT_OK,out);finish();}
    private void confirmWebItem(SmartSearchEngine.Item item){String d=WebProductResolver.dilutionCsv(item),url=WebProductResolver.sourceUrl(item);StringBuilder msg=new StringBuilder();msg.append(item.name);if(!item.manufacturer.isEmpty())msg.append("\nProduttore: ").append(item.manufacturer);msg.append("\nDiluizioni trovate: ").append(d.isEmpty()?"non estratte — nessun dato inventato":d);if(!url.isEmpty())msg.append("\n\nFonte: ").append(url);msg.append("\n\nPuoi usare i dati trovati oppure correggerli. L'originale e la fonte verranno conservati.");new android.app.AlertDialog.Builder(this).setTitle("PRODOTTO TROVATO ONLINE").setMessage(msg.toString()).setPositiveButton("USA DATI",(x,w)->returnItemDirect(item)).setNeutralButton("CORREGGI",(x,w)->editWebItem(item)).setNegativeButton("ANNULLA",null).show();}
    private void editWebItem(SmartSearchEngine.Item item){final EditText name=AssistantUi.field(this,"Nome prodotto");name.setText(item.name);final EditText maker=AssistantUi.field(this,"Produttore");maker.setText(item.manufacturer);final EditText dil=AssistantUi.field(this,"Diluizioni separate da virgola");dil.setText(WebProductResolver.dilutionCsv(item));LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);int p=AssistantUi.dp(this,16);box.setPadding(p,p,p,0);box.addView(name,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,8));box.addView(maker,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,8));box.addView(dil,AssistantUi.margin(this,-1,AssistantUi.dp(this,52),0,0,0,0));new android.app.AlertDialog.Builder(this).setTitle("CORREGGI DATI TROVATI").setMessage("Non stai creando un prodotto da zero: stai correggendo la scheda trovata online. La versione originale resta memorizzata insieme alla fonte.").setView(box).setPositiveButton("SALVA CORREZIONI",(x,w)->{try{JSONObject r=WebProductResolver.correctedCopy(item,name.getText().toString(),maker.getText().toString(),dil.getText().toString());returnItemDirect(WebProductResolver.itemFromRecord(r));}catch(Exception e){status.setText("Correzione non salvata: "+e.getMessage());}}).setNegativeButton("ANNULLA",null).show();}
    private void returnManual(){status.setText("Inserimento manuale disattivato: cerca il prodotto online.");}
    private String query()'''
rrep(search,r'    private void returnItem\(SmartSearchEngine\.Item item\)\{.*?\n    private String query\(\)',return_methods,'web-found confirmation and correction')

# Regression guards matching the user's screenshots and explicit workflow.
for needle,label in [('allowManual=false;','manual disabled'),('requestLiveWeb','live web fallback'),('CORREGGI DATI TROVATI','post-search correction'),('_originalRecord','original preservation')]:
    target=rd(search) if needle!='_originalRecord' else rd(java/'assistant/search/WebProductResolver.java')
    if needle not in target: raise SystemExit('v0.12.3 missing '+label)
if 'optInt("nominalIso",0)' not in rd(newdev): raise SystemExit('v0.12.3 nominal ISO propagation missing')
if 'public static final int VERSION = 3;' not in rd(java/'assistant/data/AssistantDataSchema.java'): raise SystemExit('v0.12.3 database schema changed unexpectedly')
if 'testFromPrint' in rd(main) or 'NUOVO PROVINO DA QUESTA STAMPA' in rd(main): raise SystemExit('v0.12.3 regression: STAMPA->PROVINO reappeared')
if 'package="it.darkroom.timer"' not in rd(manifest): raise SystemExit('v0.12.3 package changed')
print('v0.12.3 TRANSFORM OK — ISO propagation + automatic live web discovery + correction-after-import',flush=True)
