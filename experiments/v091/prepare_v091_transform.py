#!/usr/bin/env python3
from pathlib import Path
p=Path('experiments/v091/apply_v091_timing_voice_polish.py')
s=p.read_text(encoding='utf-8')
old="jpeg = java / 'JpegRenderer.java'"
new="jpeg = java / 'JpegCardRenderer.java'"
if old in s:
    p.write_text(s.replace(old,new,1),encoding='utf-8')
elif new not in s:
    raise SystemExit('prepare v0.9.1: renderer path non riconosciuto')
print('prepare v0.9.1 OK: JpegCardRenderer',flush=True)
