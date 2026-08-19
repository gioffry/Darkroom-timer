#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])/'project/app/src/main/java/it/darkroom/timer/assistant/search/SmartSearchActivity.java'
s=p.read_text(encoding='utf-8')
fixes={
    'msg.append("\nProduttore: ")': r'msg.append("\nProduttore: ")',
    'msg.append("\nDiluizioni trovate: ")': r'msg.append("\nDiluizioni trovate: ")',
    'msg.append("\n\nFonte: ")': r'msg.append("\n\nFonte: ")',
    'msg.append("\n\nPuoi usare i dati trovati oppure correggerli. L\'originale e la fonte verranno conservati.")': r'msg.append("\n\nPuoi usare i dati trovati oppure correggerli. L\'originale e la fonte verranno conservati.")',
}
for old,new in fixes.items():
    if old not in s: raise SystemExit('v0.12.3 Java newline target missing: '+repr(old))
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
if 'msg.append("\nProduttore' in s: raise SystemExit('v0.12.3 raw newline remains in Java string')
print('v0.12.3 OK generated Java newline literals escaped')
