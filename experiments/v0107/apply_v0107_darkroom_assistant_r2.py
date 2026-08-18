#!/usr/bin/env python3
from pathlib import Path

impl = Path(__file__).with_name('apply_v0107_darkroom_assistant_r2_impl.py')
source = impl.read_text(encoding='utf-8')
lines = []
for line in source.splitlines():
    if "'preflight code regex'" in line:
        line = "rep(build, r'versionCode\\s+51\\b', r'versionCode\\s+52\\b', 'preflight code regex')"
    elif "'preflight name regex'" in line:
        line = "rep(build, r'0\\.10\\.6', r'0\\.10\\.7', 'preflight name regex')"
    lines.append(line)
fixed = '\n'.join(lines) + '\n'
exec(compile(fixed, str(impl), 'exec'), {'__name__': '__main__', '__file__': str(impl)})
