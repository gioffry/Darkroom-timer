#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/patch_v051_sheet_development.py')
s = p.read_text(encoding='utf-8')

old_expected = '''    private final Tank[] tanks = new Tank[]{
            new Tank(\"JOBO 1510\", 140, 1, 0),
            new Tank(\"JOBO 1520\", 240, 2, 2),
            new Tank(\"JOBO 2520\", 270, 2, 1),
            new Tank(\"JOBO 1540\", 470, 4, 4),
            new Tank(\"JOBO 1520 + 1530\", 570, 5, 5)
    };'''
old_actual = '''    private final Tank[] tanks = new Tank[]{
            new Tank(\"JOBO 2520\", 270, 2, 1),
            new Tank(\"JOBO 2563\", 850, 6, 8)
    };'''
new_expected = '''    private final Tank[] tanks = new Tank[]{
            new Tank(\"JOBO 1510\", 140, 1, 0, 0),
            new Tank(\"JOBO 1520\", 240, 2, 2, 0),
            // 4x5: la 2520 usa la spirale/loader 2509N, fino a 6 lastre in rotazione.
            new Tank(\"JOBO 2520\", 270, 2, 1, 6),
            new Tank(\"JOBO 1540\", 470, 4, 4, 0),
            new Tank(\"JOBO 1520 + 1530\", 570, 5, 5, 0)
    };'''
new_actual = '''    private final Tank[] tanks = new Tank[]{
            // 4x5: la 2520 usa la spirale/loader 2509N, fino a 6 lastre in rotazione.
            new Tank(\"JOBO 2520\", 270, 2, 1, 6),
            // La 2563 resta visibile per i formati a rullo, ma 850 ml supera il limite CPE2.
            new Tank(\"JOBO 2563\", 850, 6, 8, 0)
    };'''

if old_expected not in s:
    raise SystemExit('v0.5.1 repair: original expected tank marker missing in patch source')
if new_expected not in s:
    raise SystemExit('v0.5.1 repair: replacement tank marker missing in patch source')
s = s.replace(old_expected, old_actual, 1)
s = s.replace(new_expected, new_actual, 1)
p.write_text(s, encoding='utf-8')
print('v0.5.1 patch source aligned to canonical JOBO 2520/2563 configuration')
