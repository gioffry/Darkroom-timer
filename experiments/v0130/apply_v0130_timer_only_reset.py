#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; main_dir=app/'src/main'; java=main_dir/'java/it/darkroom/timer'
manifest=main_dir/'AndroidManifest.xml'; gradle=app/'build.gradle'; build=work/'build_darkroom.py'; main=java/'MainActivity.java'; logentry=java/'LogEntry.java'; logstore=java/'LogStore.java'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n<count: raise SystemExit(f'v0.13.0 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.0 OK',label,flush=True)

# Exact functional base: successful v0.12.3 image reconstructed by workflow.
for p,needle in [(manifest,'android:versionName="0.12.3"'),(manifest,'android:versionCode="60"'),(main,'private static final String APP_VERSION = "0.12.3";')]:
    if needle not in rd(p): raise SystemExit('v0.13.0 BASE v0.12.3 non riconosciuta: '+needle)

# Version only. No Timer behavior changes.
s=rd(build)
if 'VERSION_NAME = "0.12.3"' not in s or 'VERSION_CODE = "60"' not in s: raise SystemExit('v0.13.0 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.12.3"','VERSION_NAME = "0.13.0"').replace('VERSION_CODE = "60"','VERSION_CODE = "61"')
s=s.replace('[Darkroom v0.12.3]','[Darkroom v0.13.0]').replace('versionCode 60','versionCode 61').replace(r'versionCode\s+60\b',r'versionCode\s+61\b').replace('0.12.3','0.13.0')
wr(build,s)
rep(gradle,"versionCode 60\n        versionName '0.12.3'","versionCode 61\n        versionName '0.13.0'",'Gradle version')
rep(main,'private static final String APP_VERSION = "0.12.3";','private static final String APP_VERSION = "0.13.0";','Timer footer version')

# Remove the two Assistant integrations that had entered the Timer itself.
chem_block='''        Button chemistrySession = compactButton("CHIMICA SESSIONE · " + it.darkroom.timer.assistant.paper.PaperChemistryStore.shortStatus(this));
        chemistrySession.setOnClickListener(v -> showAppConfirmDialog(
                "CHIMICA SESSIONE",
                it.darkroom.timer.assistant.paper.PaperChemistryStore.summary(this),
                "CONFIGURA", () -> startActivity(new Intent(this, it.darkroom.timer.assistant.paper.PaperChemistryActivity.class)), "CHIUDI"));
        box.addView(chemistrySession, margin(lp(-1, dp(48)), 0, 8, 0, 0));
'''
rep(main,chem_block,'','remove chemistry-session button from Timer')
rep(main,'            e.paperChemistrySnapshot = it.darkroom.timer.assistant.paper.PaperChemistryStore.activeSnapshot(this);\n','','remove chemistry snapshot capture')

# Remove the chemistry snapshot field from the Timer LOG model/serializer, while old 25-column rows remain readable (extra tail is simply ignored).
rep(logentry,'    /** Immutable snapshot of the optional active paper-chemistry session. */\n    public String paperChemistrySnapshot = "";\n','','remove Assistant field from LogEntry')
rep(logstore,'                    e.paperChemistrySnapshot = f.length >= 25 ? dec(f[24]) : "";\n','','remove Assistant field parse')
rep(logstore,"                    .append(enc(e.recipeState)).append('\\t')\n                    .append(enc(e.paperChemistrySnapshot));","                    .append(enc(e.recipeState));",'remove Assistant field serialization')

# Remove the old Assistant module and the temporary two-entry Home. Launcher returns directly to the Timer.
for d in (java/'assistant', java/'home'):
    if d.exists(): shutil.rmtree(d)
for p in (main_dir/'AndroidManifest.xml.orig', java/'MainActivity.java.orig'):
    if p.exists(): p.unlink()

clean_manifest='''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="it.darkroom.timer"
    android:versionCode="61"
    android:versionName="0.13.0">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE" />
    <uses-permission android:name="android.permission.ACCESS_NOTIFICATION_POLICY" />

    <application
        android:allowBackup="false"
        android:label="Darkroom Timer"
        android:icon="@drawable/ic_launcher"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.Holo.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:screenOrientation="portrait"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".SonoffArmService"
            android:exported="false"
            android:foregroundServiceType="connectedDevice" />
    </application>
</manifest>
'''
wr(manifest,clean_manifest)

# Hard guards: no Assistant residue in the application image and core Timer features remain.
for p in main_dir.rglob('*'):
    if p.is_file() and p.suffix in ('.java','.xml'):
        t=rd(p).lower()
        if 'assistant' in t or 'smart search' in t or 'sviluppo & chimica' in t or 'chimica sessione' in t or 'paperchemistry' in t:
            raise SystemExit('v0.13.0 riferimento Assistant residuo: '+str(p))
if (java/'assistant').exists() or (java/'home').exists(): raise SystemExit('v0.13.0 directory obsolete ancora presente')
mt=rd(main)
for needle in ['SPLIT GRADE','PROVINO','ARMA','F-STOP','SonoffArmService','PrintSequence','ExposureRecipe']:
    if needle not in mt: raise SystemExit('v0.13.0 regressione Timer: manca '+needle)
if 'testFromPrint' in mt or 'NUOVO PROVINO DA QUESTA STAMPA' in mt: raise SystemExit('v0.13.0 regressione: STAMPA->PROVINO ricomparso')
if 'android:name=".MainActivity"' not in rd(manifest) or 'android.intent.category.LAUNCHER' not in rd(manifest): raise SystemExit('v0.13.0 launcher Timer non valido')
print('v0.13.0 TRANSFORM OK — Timer-only, Assistant completamente rimosso',flush=True)
