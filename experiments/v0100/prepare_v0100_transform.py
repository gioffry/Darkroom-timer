#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).with_name('apply_v0100_pro_recipe.py')
s=p.read_text(encoding='utf-8')
s=s.replace("r'versionCode\\\\\\\\s+44\\\\\\\\b'", "r'versionCode\\\\s+44\\\\b'")
s=s.replace("r'versionCode\\\\\\\\s+45\\\\\\\\b'", "r'versionCode\\\\s+45\\\\b'")
s=s.replace("r'0\\\\\\\\.9\\\\\\\\.1'", "r'0\\\\.9\\\\.1'")
s=s.replace("r'0\\\\\\\\.10\\\\\\\\.0'", "r'0\\\\.10\\\\.0'")
p.write_text(s,encoding='utf-8')
print('prepare v0.10.0 OK: regex preflight normalizzate',flush=True)
