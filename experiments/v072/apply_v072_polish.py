#!/usr/bin/env python3
from pathlib import Path
import re, sys

work=Path(sys.argv[1]); project=work/'project'; java=project/'app/src/main/java/it/darkroom/timer'

def read(p): return Path(p).read_text(encoding='utf-8')
def write(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    p=Path(p); s=read(p)
    n=s.count(old)
    if n < count: raise SystemExit(f'{label}: atteso >= {count}, trovato {n}')
    s=s.replace(old,new,count); write(p,s); print('OK',label)

# Versione
build=work/'build_darkroom.py'
rep(build,'VERSION_NAME = "0.7.1"\nVERSION_CODE = "34"','VERSION_NAME = "0.7.2"\nVERSION_CODE = "35"','version build')
rep(build,'[Darkroom v0.7.1]','[Darkroom v0.7.2]','tag build')
rep(build,'versionCode\\s+34\\b','versionCode\\s+35\\b','preflight code regex')
rep(build,'0\\.7\\.1','0\\.7\\.2','preflight name regex')
rep(build,'versionCode 34 / versionName 0.7.1','versionCode 35 / versionName 0.7.2','preflight message')
rep(build,'Preflight v0.7.1 OK','Preflight v0.7.2 OK','preflight log')
rep(project/'app/build.gradle',"versionCode 34\n        versionName '0.7.1'","versionCode 35\n        versionName '0.7.2'",'gradle')
rep(project/'app/src/main/AndroidManifest.xml','android:versionCode="34"\n    android:versionName="0.7.1"','android:versionCode="35"\n    android:versionName="0.7.2"','manifest')
main=java/'MainActivity.java'
rep(main,'private static final String APP_VERSION = "0.7.1";','private static final String APP_VERSION = "0.7.2";','app version')

# Stato SONOFF: PRONTO non è ammesso durante la riconnessione.
s=read(main)
old='setStatusPresentation("PRONTO", "RICONNESSIONE AUTOMATICA — nessuna azione richiesta", GREEN);'
new='setStatusPresentation("ATTESA SONOFF", "RICONNESSIONE AUTOMATICA — attendo conferma dal SONOFF", darkroomMode ? RED : AMBER);'
if old not in s: raise SystemExit('stato riconnessione: pattern non trovato')
s=s.replace(old,new)
write(main,s); print('OK stato riconnessione')

# Badge F-STOP helper, red-only in camera oscura.
s=read(main)
anchor='    private String printStepDescription() {'
if anchor not in s: raise SystemExit('anchor helper badge non trovato')
helper='''    private TextView fStopBadge(boolean compact) {\n        TextView badge = text(compact ? "F-STOP  ·  ¼" : "F-STOP  ·  ¼ stop", compact ? 10 : 12, Color.BLACK, true);\n        badge.setGravity(Gravity.CENTER);\n        badge.setPadding(dp(compact ? 8 : 12), dp(compact ? 3 : 5), dp(compact ? 8 : 12), dp(compact ? 3 : 5));\n        badge.setBackground(roundRect(darkroomMode ? RED : GREEN, compact ? 10 : 14, 0, 0));\n        badge.setContentDescription("Modalità F-STOP, passo un quarto di stop");\n        return badge;\n    }\n\n    private void addFStopBadge(LinearLayout parent, boolean compact) {\n        if (parent == null || !TimingMath.isFStop(timingMethod)) return;\n        TextView badge = fStopBadge(compact);\n        parent.addView(badge, margin(lp(compact ? -2 : -1, dp(compact ? 26 : 32)), compact ? 0 : dp(36), dp(6), compact ? 0 : dp(36), dp(6)));\n    }\n\n'''
s=s.replace(anchor,helper+anchor,1)
write(main,s); print('OK helper badge')

# STAMPA: badge subito sotto la riga che già spiega il passo.
s=read(main)
old='''        printStepText = text(printStepDescription(), 12, MUTED, false);\n        printStepText.setGravity(Gravity.CENTER);\n        box.addView(printStepText);'''
new=old+'\n        addFStopBadge(box, false);'
if old not in s: raise SystemExit('badge stampa: pattern non trovato')
s=s.replace(old,new,1); write(main,s); print('OK badge stampa')

# PROVINO: stessa firma visiva.
s=read(main)
old='''        testStepText = text(testStepDescription(), 12, MUTED, false);\n        testStepText.setGravity(Gravity.CENTER);\n        exposure.addView(testStepText);'''
new=old+'\n        addFStopBadge(exposure, false);'
if old not in s: raise SystemExit('badge provino: pattern non trovato')
s=s.replace(old,new,1); write(main,s); print('OK badge provino')

# LOG: chip compatto sulle schede che usano F-STOP.
s=read(main)
needle='''        TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? GREEN : TEXT_PRIMARY, true);\n        row.addView(summary, lp(-1, -2));'''
insert=needle+'''\n        if (TimingMath.isFStop(e.exposureMethod) || TimingMath.isFStop(e.testMethod)) {\n            TextView modeBadge = fStopBadge(true);\n            row.addView(modeBadge, margin(lp(-2, dp(26)), 0, dp(5), 0, dp(2)));\n        }'''
if needle not in s: raise SystemExit('badge log: pattern non trovato')
s=s.replace(needle,insert,1); write(main,s); print('OK badge log')

# Editor LOG: indicazione persistente per i mezzi diaframmi.
s=read(main)
old='''        panel.addView(aperture, margin(lp(-1, dp(52)), 0, 0, 0, 8));'''
new='''        panel.addView(aperture, margin(lp(-1, dp(52)), 0, 0, 0, 3));\n        TextView apertureNote = text("½ stop: indicare 0,5  •  esempio: f/11½ → 11,5", 11, MUTED, false);\n        apertureNote.setPadding(dp(4), 0, dp(4), dp(7));\n        panel.addView(apertureNote, lp(-1, -2));'''
if old not in s: raise SystemExit('nota diaframma: pattern non trovato')
s=s.replace(old,new,1); write(main,s); print('OK nota diaframma')

# JPG: trasforma solo i valori che terminano esattamente in ,5/.5.
jpg=java/'JpegCardRenderer.java'; s=read(jpg)
m=re.search(r'    private static String apertureLabel\(String value\) \{.*?\n    \}',s,re.S)
if not m: raise SystemExit('apertureLabel non trovato')
new_method='''    private static String apertureLabel(String value) {\n        String v = text(value, "—").trim();\n        if ("—".equals(v)) return v;\n        if (v.matches("^[0-9]+[,.]5$")) {\n            v = v.substring(0, v.length() - 2) + "½";\n        }\n        return v.startsWith("f/") ? v : "f/" + v;\n    }'''
s=s[:m.start()]+new_method+s[m.end():]
# JPG badge: overlay in alto a destra, solo quando almeno uno dei due metodi è F-STOP.
ret='        return bitmap;\n    }'
if ret not in s: raise SystemExit('return bitmap non trovato')
badge='''        if (TimingMath.isFStop(e.exposureMethod) || TimingMath.isFStop(e.testMethod)) {\n            Paint badgeFill = new Paint(Paint.ANTI_ALIAS_FLAG);\n            badgeFill.setColor(Color.rgb(80, 207, 70));\n            android.graphics.RectF badgeRect = new android.graphics.RectF(W - 350f, 48f, W - 64f, 112f);\n            canvas.drawRoundRect(badgeRect, 32f, 32f, badgeFill);\n            Paint badgeText = new Paint(Paint.ANTI_ALIAS_FLAG);\n            badgeText.setColor(Color.BLACK);\n            badgeText.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));\n            badgeText.setTextSize(27f);\n            badgeText.setTextAlign(Paint.Align.CENTER);\n            canvas.drawText("F-STOP  ·  ¼ stop", badgeRect.centerX(), badgeRect.centerY() + 10f, badgeText);\n        }\n\n'''+ret
s=s.replace(ret,badge,1)
write(jpg,s); print('OK JPG diaframma + badge')

# Icona: sostituisce il vecchio preparatore v0.6.4, ma usa byte-per-byte l'immagine fornita.
iconmod=work/'v064_icon.py'; b=read(build)
mi=re.search(r'from v064_icon import ([A-Za-z_][A-Za-z0-9_]*)',b)
if not mi: raise SystemExit('import v064_icon non trovato')
func=mi.group(1)
icon_py=f'''from pathlib import Path\nimport base64, hashlib\n\ndef {func}(project):\n    project = Path(project)\n    repo = Path(__file__).resolve().parent.parent\n    source = repo / "assets" / "v072" / "user_icon_exact.b64"\n    raw = base64.b64decode(source.read_text(encoding="ascii"))\n    if not raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):\n        raise RuntimeError("L'icona utente v0.7.2 non è un PNG valido")\n    out = project / "app" / "src" / "main" / "res" / "drawable-nodpi" / "ic_launcher.png"\n    out.parent.mkdir(parents=True, exist_ok=True)\n    out.write_bytes(raw)\n    print("[Darkroom v0.7.2] Icona utente ESATTA: ic_launcher.png (" + format(len(raw), ",") + " byte) SHA-256=" + hashlib.sha256(raw).hexdigest(), flush=True)\n'''
write(iconmod,icon_py); print('OK icona esatta')

# Verifiche finali.
checks={
 main:['ATTESA SONOFF','F-STOP  ·  ¼ stop','½ stop: indicare 0,5','private TextView fStopBadge'],
 jpg:['v.matches("^[0-9]+[,.]5$")','F-STOP  ·  ¼ stop','badgeRect'],
 build:['VERSION_NAME = "0.7.2"','VERSION_CODE = "35"'],
}
for p,ns in checks.items():
 t=read(p)
 for n in ns:
  if n not in t: raise SystemExit(f'verifica finale fallita {n} in {p}')
print('v0.7.2: TUTTE LE VERIFICHE SORGENTE OK')
