#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
manifest = project / 'app/src/main/AndroidManifest.xml'
main = project / 'app/src/main/java/it/darkroom/timer/MainActivity.java'
service = project / 'app/src/main/java/it/darkroom/timer/SonoffArmService.java'

m = manifest.read_text(encoding='utf-8')
needle = '    <uses-permission android:name="android.permission.WAKE_LOCK" />\n'
if 'android.permission.VIBRATE' not in m:
    if needle not in m: raise SystemExit('v0.8.0 fixup: punto permesso VIBRATE non trovato')
    m = m.replace(needle, needle + '    <uses-permission android:name="android.permission.VIBRATE" />\n', 1)
manifest.write_text(m, encoding='utf-8')

s = main.read_text(encoding='utf-8')
# I cue molto brevi sarebbero dominati dalla latenza di rilevamento LAN: 1,0 s è il minimo pratico.
s = s.replace('ms[0] = Math.max(500, ms[0] - 500);', 'ms[0] = Math.max(c.isDodge() ? 1000 : 500, ms[0] - 500);')
s = s.replace('c.milliseconds = TimingMath.snap500(ms[0], 500, Math.max(500, printWidthMs - 500));', 'c.milliseconds = TimingMath.snap500(Math.max(1000, ms[0]), 1000, Math.max(1000, printWidthMs - 500));')
main.write_text(s, encoding='utf-8')

svc = service.read_text(encoding='utf-8')
svc = svc.replace("printSequence.detail(widthMs).replace('\\n', ' • ')", 'printSequence.detail(widthMs).replace("\\n", " • ")')
service.write_text(svc, encoding='utf-8')

if 'android.permission.VIBRATE' not in manifest.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.0 fixup: VIBRATE mancante')
if 'Math.max(1000, ms[0])' not in main.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.0 fixup: minimo DODGE non applicato')
if "replace('\\n', ' • ')" in service.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.0 fixup: replace Java invalido ancora presente')
print('v0.8.0 FIXUPS OK: VIBRATE + DODGE min 1,0 s + log Java', flush=True)
