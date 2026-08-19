#!/usr/bin/env python3
from pathlib import Path
import re,sys
work=Path(sys.argv[1]); p=work/'project/app/src/main/java/it/darkroom/timer/assistant/search/SmartSearchActivity.java'
s=p.read_text(encoding='utf-8')
s,n=re.subn(r'\n\s*if\(allowManual\)\{Button manual=.*?\}\n', '\n', s, count=1)
if n!=1: raise SystemExit('v0.12.3 manual button block not found')
s=s.replace('    private void returnManual(){status.setText("Inserimento manuale disattivato: cerca il prodotto online.");}\n','')
p.write_text(s,encoding='utf-8')
if 'INSERISCI MANUALMENTE' in s or 'returnManual()' in s: raise SystemExit('v0.12.3 manual creation UI still present')
print('v0.12.3 OK manual product creation removed completely')
