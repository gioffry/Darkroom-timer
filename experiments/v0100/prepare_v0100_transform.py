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
s = '\n'.join(lines) + '\n'
# The transformer text was created through JSON and the Java tab literal in the
# LogStore matcher picked up one escaping layer too many. Normalize only that
# escaped-tab form; leave regex/backslash handling elsewhere untouched.
s = s.replace(r"\\t", r"\t")
p.write_text(s, encoding='utf-8')
print('prepare v0.10.0 OK: regex preflight + tab Java normalizzati', flush=True)
