#!/usr/bin/env python3
from pathlib import Path
p = Path('experiments/v081/apply_v081_print_plan_polish.py')
s = p.read_text(encoding='utf-8')
old = "    s=rd(p); out,n=re.subn(pattern,repl,s,count=1,flags=re.S)\n"
new = "    s=rd(p); out,n=re.subn(pattern,lambda m: repl,s,count=1,flags=re.S)\n"
if old not in s:
    raise SystemExit('prepare v0.8.1: regex_replace non trovato')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('prepare v0.8.1 OK: replacement regex preserva backslash Java', flush=True)
