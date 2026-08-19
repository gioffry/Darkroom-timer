#!/usr/bin/env python3
from pathlib import Path

p = Path('experiments/v0102/apply_v0102_test_fixes.py')
s = p.read_text(encoding='utf-8')
old = '''rrep(main,
     r'(@Override protected void onResume\\(\\) \\{\\n        super\\.onResume\\(\\);.*?        restoreRuntimeState\\(\\);)',
     r''' + "'''\\1\n        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);'''" + ''',
     'resume pending test chooser')'''
new = '''rep(main,
''' + "'''        restoreRuntimeState();\n\n        if (pendingDarkroomAfterDndPermission) {'''" + ''',
''' + "'''        restoreRuntimeState();\n        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);\n\n        if (pendingDarkroomAfterDndPermission) {'''" + ''',
    'resume pending test chooser')'''
if old not in s:
    raise SystemExit('prepare v0.10.2: blocco onResume non trovato')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('prepare v0.10.2 OK: onResume replacement senza backreference letterale', flush=True)
