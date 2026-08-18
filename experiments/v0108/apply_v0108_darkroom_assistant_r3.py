#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'
home = java / 'home/HomeActivity.java'
assistant = java / 'assistant/AssistantActivity.java'
development_dir = java / 'assistant/development'
chemistry_dir = java / 'assistant/chemistry'
catalog = development_dir / 'DevelopmentCatalog.java'
new_development = development_dir / 'NewDevelopmentActivity.java'
result_activity = development_dir / 'DevelopmentResultActivity.java'
chem_calc = chemistry_dir / 'ChemistryCalculator.java'
prepare_activity = chemistry_dir / 'PrepareChemistryActivity.java'
script_dir = Path(__file__).parent


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s = rd(p); n = s.count(old)
    if n < count: raise SystemExit(f'v0.10.8 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count)); print('v0.10.8 OK', label, flush=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Snapshot di sicurezza dopo la v0.10.7: Home e core STAMPA non devono subire refactor.
timer_before = {p.name: sha(p) for p in java.glob('*.java') if p.name != 'MainActivity.java'}
main_before = rd(main)
home_before = sha(home)

# Versione 0.10.8 / code 53. Application ID e package restano invariati.
rep(build, 'VERSION_NAME = "0.10.7"', 'VERSION_NAME = "0.10.8"', 'version name build')
rep(build, 'VERSION_CODE = "52"', 'VERSION_CODE = "53"', 'version code build')
rep(build, '[Darkroom v0.10.7]', '[Darkroom v0.10.8]', 'build log tag')
rep(build, r'versionCode\s+52\b', r'versionCode\s+53\b', 'preflight code regex')
rep(build, r'0\.10\.7', r'0\.10\.8', 'preflight name regex')
rep(build, 'versionCode 52 / versionName 0.10.7', 'versionCode 53 / versionName 0.10.8', 'preflight message')
rep(build, 'Preflight v0.10.7 OK', 'Preflight v0.10.8 OK', 'preflight log')
rep(gradle, "versionCode 52\n        versionName '0.10.7'", "versionCode 53\n        versionName '0.10.8'", 'gradle version')
rep(manifest, 'android:versionCode="52"\n    android:versionName="0.10.7"', 'android:versionCode="53"\n    android:versionName="0.10.8"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.7";', 'private static final String APP_VERSION = "0.10.8";', 'Timer UI version')

# PARTE A: piccolo comando HOME nel Timer. Nessuna altra logica STAMPA viene toccata.
title_anchor = '        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);\n'
home_button = '''        Button homeButton = compactButton("← HOME");\n        homeButton.setTextSize(13);\n        homeButton.setGravity(Gravity.CENTER);\n        homeButton.setOnClickListener(v -> finish());\n        root.addView(homeButton, margin(lp(dp(94), dp(38)), 0, 0, 0, 4));\n\n'''
rep(main, title_anchor, home_button + title_anchor, 'comando HOME discreto nel Timer')
expected_main = main_before.replace(
    'private static final String APP_VERSION = "0.10.7";',
    'private static final String APP_VERSION = "0.10.8";', 1
).replace(title_anchor, home_button + title_anchor, 1)
if rd(main) != expected_main:
    raise SystemExit('v0.10.8 GUARDRAIL: MainActivity contiene modifiche oltre versione + HOME')

# Registra la funzione autonoma PREPARA CHIMICA.
ms = rd(manifest)
activity_anchor = '''        <activity\n            android:name=".assistant.development.NewDevelopmentActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
prepare_block = '''        <activity\n            android:name=".assistant.chemistry.PrepareChemistryActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n'''
if activity_anchor not in ms:
    raise SystemExit('v0.10.8 manifest: NewDevelopmentActivity anchor non trovata')
ms = ms.replace(activity_anchor, prepare_block + activity_anchor, 1)
wr(manifest, ms)
print('v0.10.8 OK manifest PrepareChemistryActivity', flush=True)

# Il catalogo tempi R2 resta intatto; aggiungiamo solo un accessor per le diluizioni
# disponibili per prodotto, utile alla funzione autonoma PREPARA CHIMICA.
catalog_anchor = '''    public static String[] availableDilutions(String film, int ei, String developer) {\n'''
developer_dilutions = '''    public static String[] developerDilutions(String developer) {\n        LinkedHashSet<String> values = new LinkedHashSet<>();\n        for (Recipe r : RECIPES) if (same(r.developer, developer)) values.add(r.dilution);\n        return values.toArray(new String[0]);\n    }\n\n'''
rep(catalog, catalog_anchor, developer_dilutions + catalog_anchor, 'accessor diluizioni per prodotto')

# Nuovo motore chimica e schermata autonoma, mantenuti nel package Assistant.
wr(chem_calc, rd(script_dir / 'ChemistryCalculator.java'))
wr(prepare_activity, rd(script_dir / 'PrepareChemistryActivity.java'))
wr(result_activity, rd(script_dir / 'DevelopmentResultActivity.java'))
print('v0.10.8 OK ChemistryCalculator + PrepareChemistryActivity + risultato R3', flush=True)

# PREPARA CHIMICA diventa operativa nell'Assistant.
rep(assistant,
    'import it.darkroom.timer.assistant.development.NewDevelopmentActivity;\n',
    'import it.darkroom.timer.assistant.development.NewDevelopmentActivity;\nimport it.darkroom.timer.assistant.chemistry.PrepareChemistryActivity;\n',
    'import PrepareChemistryActivity')
rep(assistant,
    '        addPlaceholder(root, "PREPARA CHIMICA");\n',
    '''        Button prepareChemistry = entry("PREPARA CHIMICA", "Diluizioni, volumi e capacità documentata", true);\n        prepareChemistry.setOnClickListener(v -> startActivity(new Intent(this, PrepareChemistryActivity.class)));\n        root.addView(prepareChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n''',
    'PREPARA CHIMICA operativa')

# Integra volume totale e numero rulli nel flusso NUOVO SVILUPPO.
rep(new_development,
    '    private EditText exposedIsoField, temperatureField;\n',
    '    private EditText exposedIsoField, temperatureField, volumeField, rollsField;\n',
    'campi volume e rulli')
rep(new_development,
    '        TextView eyebrow=text("DARKROOM ASSISTANT · 2/9",12,accent,true);',
    '        TextView eyebrow=text("DARKROOM ASSISTANT · 3/9",12,accent,true);',
    'badge release 3/9')
insert_anchor = '''        dilutionField.setOnFocusChangeListener((v,has) -> { if(has) dilutionField.showDropDown(); });\n\n        label(root,"TEMPERATURA REALE");\n'''
insert_fields = '''        dilutionField.setOnFocusChangeListener((v,has) -> { if(has) dilutionField.showDropDown(); });\n\n        label(root,"NUMERO RULLI");\n        rollsField=editField("es. 1",InputType.TYPE_CLASS_NUMBER); rollsField.setText("1");\n        root.addView(rollsField,lp(-1,dp(52)));\n\n        label(root,"VOLUME TOTALE DA PREPARARE");\n        volumeField=editField("es. 340 ml",InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);\n        volumeField.setText("340"); root.addView(volumeField,lp(-1,dp(52)));\n        TextView volumeNote=text("Inserimento manuale in Release 3 · la tank automatica arriverà in Release 6",11,muted,false);\n        volumeNote.setPadding(dp(4),dp(5),dp(4),dp(2)); root.addView(volumeNote);\n\n        label(root,"TEMPERATURA REALE");\n'''
rep(new_development, insert_anchor, insert_fields, 'UI numero rulli + volume')
rep(new_development,
    '        Button calculate=bigButton("CALCOLA TEMPO");',
    '        Button calculate=bigButton("CALCOLA TEMPO E PREPARA");',
    'azione calcolo R3')

old_calculate = '''    private void calculate() {\n        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());\n        if(film==null){ toast("Seleziona una pellicola dal catalogo."); return; }\n        int exposed=parseInt(exposedIsoField.getText().toString(),-1);\n        if(exposed<=0){ toast("Inserisci un ISO esposto valido."); return; }\n        double temp=parseDouble(temperatureField.getText().toString());\n        if(Double.isNaN(temp)){ toast("Inserisci la temperatura, per esempio 21,7."); return; }\n        DevelopmentCatalog.Result r=DevelopmentCatalog.calculate(film.name,selectedFormat,exposed,\n                developerField.getText().toString(),dilutionField.getText().toString(),temp);\n        if(!r.ok){ toast(r.error); return; }\n        Intent i=new Intent(this,DevelopmentResultActivity.class);\n        i.putExtra("film",r.film); i.putExtra("format",r.format); i.putExtra("nominalIso",r.nominalIso);\n        i.putExtra("exposedIso",r.exposedIso); i.putExtra("developer",r.developer); i.putExtra("dilution",r.dilution);\n        i.putExtra("temperature",r.temperature); i.putExtra("seconds",r.finalSeconds); i.putExtra("source",r.source);\n        i.putExtra("dataType",r.dataType); i.putExtra("sourceData",r.sourceData); i.putExtra("calculation",r.calculation);\n        i.putExtra("alternatives",r.alternatives); startActivity(i);\n    }\n'''
new_calculate = '''    private void calculate() {\n        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());\n        if(film==null){ toast("Seleziona una pellicola dal catalogo."); return; }\n        int exposed=parseInt(exposedIsoField.getText().toString(),-1);\n        if(exposed<=0){ toast("Inserisci un ISO esposto valido."); return; }\n        int rolls=parseInt(rollsField.getText().toString(),-1);\n        if(rolls<=0){ toast("Inserisci il numero di rulli."); return; }\n        double volume=parseDouble(volumeField.getText().toString());\n        if(Double.isNaN(volume)||volume<=0){ toast("Inserisci il volume totale in ml."); return; }\n        if(volume>it.darkroom.timer.assistant.chemistry.ChemistryCalculator.CPE2_MAX_ML){\n            toast("JOBO CPE2: il volume massimo documentato è 600 ml."); return;\n        }\n        double temp=parseDouble(temperatureField.getText().toString());\n        if(Double.isNaN(temp)){ toast("Inserisci la temperatura, per esempio 21,7."); return; }\n        DevelopmentCatalog.Result r=DevelopmentCatalog.calculate(film.name,selectedFormat,exposed,\n                developerField.getText().toString(),dilutionField.getText().toString(),temp);\n        if(!r.ok){ toast(r.error); return; }\n        Intent i=new Intent(this,DevelopmentResultActivity.class);\n        i.putExtra("film",r.film); i.putExtra("format",r.format); i.putExtra("nominalIso",r.nominalIso);\n        i.putExtra("exposedIso",r.exposedIso); i.putExtra("developer",r.developer); i.putExtra("dilution",r.dilution);\n        i.putExtra("temperature",r.temperature); i.putExtra("seconds",r.finalSeconds); i.putExtra("source",r.source);\n        i.putExtra("dataType",r.dataType); i.putExtra("sourceData",r.sourceData); i.putExtra("calculation",r.calculation);\n        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);\n        startActivity(i);\n    }\n'''
rep(new_development, old_calculate, new_calculate, 'integrazione preparazione nel Nuovo sviluppo')
rep(new_development,
    '    private double parseDouble(String s){ try{return Double.parseDouble(s.trim().replace(\',\',\'.\').replace("°C","").trim());}catch(Exception e){return Double.NaN;} }\n',
    '    private double parseDouble(String s){ try{return Double.parseDouble(s.trim().replace(\',\',\'.\').replace("°C","").replace("ml","").trim());}catch(Exception e){return Double.NaN;} }\n',
    'parser ml/temperatura')

# Guardrail: core STAMPA esclusa MainActivity deve essere bit-identico; Home deve essere bit-identica.
timer_after = {p.name: sha(p) for p in java.glob('*.java') if p.name != 'MainActivity.java'}
if timer_before != timer_after:
    changed = sorted(set(timer_before) | set(timer_after))
    bad = [n for n in changed if timer_before.get(n) != timer_after.get(n)]
    raise SystemExit('v0.10.8 GUARDRAIL TIMER: modificate classi non autorizzate: ' + ', '.join(bad))
if sha(home) != home_before:
    raise SystemExit('v0.10.8 GUARDRAIL HOME: HomeActivity v0.10.7 è stata modificata')

# Verifiche statiche Release 3.
mt = rd(manifest)
if mt.count('android.intent.action.MAIN') != 1 or mt.count('android.intent.category.LAUNCHER') != 1:
    raise SystemExit('v0.10.8 HOME: launcher non univoco')
if 'package="it.darkroom.timer"' not in mt:
    raise SystemExit('v0.10.8 package applicazione alterato')
checks = {
    build: ['VERSION_NAME = "0.10.8"','VERSION_CODE = "53"'],
    gradle: ["versionCode 53","versionName '0.10.8'"],
    main: ['private static final String APP_VERSION = "0.10.8"','compactButton("← HOME")','homeButton.setOnClickListener(v -> finish())'],
    manifest: ['.home.HomeActivity','.assistant.chemistry.PrepareChemistryActivity','.assistant.development.NewDevelopmentActivity'],
    assistant: ['PREPARA CHIMICA','PrepareChemistryActivity.class','NUOVO SVILUPPO'],
    catalog: ['developerDilutions','JOBO CPE2','rotazione continua','DATO DIRETTO','DATO ADATTATO / CALCOLATO'],
    new_development: ['NUMERO RULLI','VOLUME TOTALE DA PREPARARE','CALCOLA TEMPO E PREPARA','volumeMl','rolls'],
    chem_calc: ['CPE2_MAX_ML = 600.0','4000 ml working solution → 12 perforated or roll films','Rapporto di diluizione non ancora disponibile dalla fonte','CAPACITY_VERIFIED','CAPACITY_INSUFFICIENT'],
    prepare_activity: ['PREPARA CHIMICA','CALCOLA PREPARAZIONE','USA VOLUME MINIMO','NUMERO RULLI (opzionale)'],
    result_activity: ['TEMPO DA IMPOSTARE SUL TIMER','PREPARA','ChemistryCalculator','USA VOLUME MINIMO','JOBO CPE2  ·  rotazione continua']
}
for p, needles in checks.items():
    text = rd(p)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v0.10.8 verifica fallita: {needle} in {p}')

print('v0.10.8 RELEASE 3 DARKROOM ASSISTANT — VERIFICHE SORGENTE OK', flush=True)
