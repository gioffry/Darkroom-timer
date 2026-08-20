#!/usr/bin/env python3
from pathlib import Path
import re,sys
work=Path(sys.argv[1]); p=work/'project/app/src/main/java/it/darkroom/timer/assistant/search/SmartSearchActivity.java'
s=p.read_text(encoding='utf-8')
s,n=re.subn(r'\n\s*if\(allowManual\)\{Button manual=.*?\}\n', '\n', s, count=1)
if n!=1: raise SystemExit('v0.12.3 manual button block not found')
s=s.replace('    private void returnManual(){status.setText("Inserimento manuale disattivato: cerca il prodotto online.");}\n','')
fixes=[
    ('msg.append("\nProduttore: ")','msg.append("\\nProduttore: ")'),
    ('msg.append("\nDiluizioni trovate: ")','msg.append("\\nDiluizioni trovate: ")'),
    ('msg.append("\n\nFonte: ")','msg.append("\\n\\nFonte: ")'),
    ("msg.append(\"\n\nPuoi usare i dati trovati oppure correggerli. L'originale e la fonte verranno conservati.\")","msg.append(\"\\n\\nPuoi usare i dati trovati oppure correggerli. L'originale e la fonte verranno conservati.\")"),
]
for old,new in fixes:
    if old not in s: raise SystemExit('v0.12.3 Java newline target missing: '+repr(old))
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
if 'INSERISCI MANUALMENTE' in s or 'returnManual()' in s: raise SystemExit('v0.12.3 manual creation UI still present')
if 'msg.append("\nProduttore' in s: raise SystemExit('v0.12.3 raw newline remains in Java string')
print('v0.12.3 OK manual creation removed and Java newline literals escaped')
