#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).with_name('apply_v0100_pro_recipe.py')
lines = p.read_text(encoding='utf-8').splitlines()
found_code = False
found_name = False
for i, line in enumerate(lines):
    if "'preflight code regex'" in line:
        lines[i] = "rep(build, r'versionCode\\s+44\\b', r'versionCode\\s+45\\b', 'preflight code regex')"
        found_code = True
    elif "'preflight name regex'" in line:
        lines[i] = "rep(build, r'0\\.9\\.1', r'0\\.10\\.0', 'preflight name regex')"
        found_name = True
if not found_code or not found_name:
    raise SystemExit(f'prepare v0.10.0: righe preflight non trovate code={found_code} name={found_name}')
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('prepare v0.10.0 OK: regex preflight riscritte in forma canonica', flush=True)
