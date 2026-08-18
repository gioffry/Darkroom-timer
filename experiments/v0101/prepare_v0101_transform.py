#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).with_name('apply_v0101_stability_ux.py')
s=p.read_text(encoding='utf-8')
old='''old_arm = ''' + "'''(\"ARMA STAMPA • \" + formatTime(printWidthMs) + (printSequence != null && !printSequence.isEmpty() ? (printSequence.hasSplit() ? \" · PIANO SPLIT\" : \" · PIANO \" + printSequence.size()) : \"\"))'''"
new='''old_arm = ''' + "'''(\"ARMA STAMPA • \" + formatTime(printWidthMs) + (printSequence != null && !printSequence.isEmpty() ? (printSequence.hasSplit() ? \" · PIANO \" + printSequence.size() : \" · PIANO \" + printSequence.size()) : \"\"))'''"
if old not in s:
    raise SystemExit('prepare v0.10.1: old_arm matcher non trovato')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('prepare v0.10.1 OK: matcher ARMA aggiornato',flush=True)
