#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys, tempfile

work = Path(sys.argv[1])
project = work / "project"
app = project / "app"
java = app / "src/main/java/it/darkroom/timer"

def rd(p):
    return Path(p).read_text(encoding="utf-8")

manifest = rd(app / "src/main/AndroidManifest.xml")
gradle = rd(app / "build.gradle")
main = rd(java / "MainActivity.java")
backup = rd(java / "assistant/system/BackupEngine.java")
engine = rd(java / "assistant/search/SmartSearchEngine.java")
binder = rd(java / "assistant/search/SmartSearchBinder.java")
catalog = rd(java / "assistant/search/SmartCatalog.java")
paper_activity = rd(java / "assistant/paper/PaperChemistryActivity.java")
paper_store = rd(java / "assistant/paper/PaperChemistryStore.java")
prepare = rd(java / "assistant/chemistry/PrepareChemistryActivity.java")
schema = rd(java / "assistant/data/AssistantDataSchema.java")

assert 'android:versionName="0.12.2"' in manifest
assert 'android:versionCode="59"' in manifest
assert "versionCode 59" in gradle and "versionName '0.12.2'" in gradle
assert 'private static final String APP_VERSION = "0.12.2";' in main
assert 'public static final String APP_VERSION="0.12.2";' in backup
assert 'public static final int VERSION_CODE=59;' in backup
assert 'public static final int VERSION = 3;' in schema
assert 'package="it.darkroom.timer"' in manifest

assert '@Override public String toString(){return name;}' in engine
assert 'convertResultToString(Object resultValue)' in binder
assert '((SmartSearchEngine.Item)resultValue).name' in binder
assert 'Rivelatore pellicola / carta' in catalog
assert '"stock".equalsIgnoreCase(d)' in paper_store
assert 'hydrateCatalogDefaults(devName,devOrigin,devDil,"PAPER_DEVELOPER",true)' in paper_activity
assert 'manualEntry(request)' in paper_activity
assert 'INSERITO MANUALMENTE · NON DOCUMENTATO' in paper_activity
assert 'DARKROOM ASSISTANT · 3/9' not in prepare
assert 'DARKROOM ASSISTANT · 9/9' in prepare
assert 'testFromPrint' not in main and 'NUOVO PROVINO DA QUESTA STAMPA' not in main

android_home = os.environ.get("ANDROID_HOME", "")
android_jar = Path(android_home) / "platforms/android-34/android.jar"
if not android_jar.is_file():
    raise SystemExit("android-34 android.jar non trovato per i test real-device-equivalent")

engine_path = java / "assistant/search/SmartSearchEngine.java"
store_path = java / "assistant/paper/PaperChemistryStore.java"

harness = r'''
import java.util.*;
import it.darkroom.timer.assistant.search.SmartSearchEngine;
import it.darkroom.timer.assistant.paper.PaperChemistryStore;

public final class V0122BehaviorTest {
    private static void check(boolean ok,String message){if(!ok)throw new RuntimeException(message);}
    private static boolean close(double a,double b){return Math.abs(a-b)<0.001;}
    public static void main(String[] args){
        SmartSearchEngine.Item foma = new SmartSearchEngine.Item(
            "dev-foma-universal","FOMA Universal","FOMA",
            Arrays.asList("FILM_DEVELOPER","PAPER_DEVELOPER","CHEMISTRY"),
            Arrays.asList("foma universal developer","foma un","universal developer foma"),
            "Rivelatore film e carta","CATALOGO LOCALE","{}",false);
        check("FOMA Universal".equals(foma.toString()),"AutoComplete mostra ancora Object.toString()");
        List<SmartSearchEngine.Result> found = SmartSearchEngine.search(
            Arrays.asList(foma),"foma un","FILM_DEVELOPER",1);
        check(found.size()==1 && "FOMA Universal".equals(found.get(0).item.name),
            "Alias foma un non risolve FOMA Universal");

        PaperChemistryStore.Mix stock = PaperChemistryStore.calculate("stock",1000);
        check(stock.known && close(stock.productMl,1000) && close(stock.waterMl,0),
            "stock non viene calcolato come 100% prodotto");

        PaperChemistryStore.Mix stop = PaperChemistryStore.calculate("1+19",1000);
        check(stop.known && close(stop.productMl,50) && close(stop.waterMl,950),
            "rapporto 1+19 regressione");

        System.out.println("V0122_BEHAVIOR_PASS");
    }
}
'''

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    test = td / "V0122BehaviorTest.java"
    test.write_text(harness, encoding="utf-8")
    cp = str(android_jar)
    subprocess.run([
        "javac","-cp",cp,"-d",str(td),
        str(engine_path),str(store_path),str(test)
    ], check=True)
    subprocess.run([
        "java","-cp",str(td)+os.pathsep+cp,"V0122BehaviorTest"
    ], check=True)

print("V0122_RELEASE_GUARDS_PASS")
