#!/usr/bin/env python3
from pathlib import Path
import re, sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; java=app/'src/main/java/it/darkroom/timer'
manifest=(app/'src/main/AndroidManifest.xml').read_text(); gradle=(app/'build.gradle').read_text(); main=(java/'MainActivity.java').read_text()
newdev=(java/'assistant/development/NewDevelopmentActivity.java').read_text(); search=(java/'assistant/search/SmartSearchActivity.java').read_text(); resolver=(java/'assistant/search/WebProductResolver.java').read_text(); parser=(java/'assistant/search/WebSearchParser.java').read_text(); backup=(java/'assistant/system/BackupEngine.java').read_text()

def must(cond,msg):
    if not cond: raise SystemExit('FAIL '+msg)
    print('PASS',msg)

must('android:versionName="0.12.3"' in manifest and 'android:versionCode="60"' in manifest,'version 0.12.3 / 60')
must('private static final String APP_VERSION = "0.12.3";' in main,'Timer footer version only')
must('public static final String APP_VERSION="0.12.3";' in backup and 'public static final int VERSION_CODE=60;' in backup,'backup metadata')
must('optInt("nominalIso",0)' in newdev and 'nominalIsoText.setText(Integer.toString(nominal))' in newdev and 'exposedIsoField.setText(Integer.toString(nominal))' in newdev,'selected film propagates nominal/exposed ISO')
must('requestLiveWeb' in search and 'WebProductResolver.resolve' in search,'unknown product invokes automatic live web lookup')
must('allowManual=false;' in search,'manual creation disabled')
must('PRODOTTO TROVATO ONLINE' in search and 'CORREGGI DATI TROVATI' in search,'correction offered only after web discovery')
must('_originalRecord' in resolver and '_userCorrected' in resolver,'original discovered record preserved before correction')
must('html.duckduckgo.com' in resolver and 'www.bing.com/search' in resolver,'real Internet search engines configured')
must('HttpURLConnection' in resolver and 'get(h.url' in resolver,'resolver follows retrieved web sources')
must('extractDilutions' in parser and '1\\s*\\+\\s*' in parser,'documented dilution extraction')
must('RICERCA WEB AUTOMATICA' in resolver and 'url' in resolver,'web source provenance stored')
must('DATO WEB ESTRATTO AUTOMATICAMENTE' in resolver,'web data explicitly marked')
must('public static final int VERSION = 3;' in (java/'assistant/data/AssistantDataSchema.java').read_text(),'database schema unchanged')
must('testFromPrint' not in main and 'NUOVO PROVINO DA QUESTA STAMPA' not in main,'STAMPA -> PROVINO remains removed')
must('package="it.darkroom.timer"' in manifest,'package unchanged')
print('v0.12.3 RELEASE GUARDS PASS')
