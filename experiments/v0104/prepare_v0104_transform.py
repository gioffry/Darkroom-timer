#!/usr/bin/env python3
from pathlib import Path
p=Path('experiments/v0104/apply_v0104_dodge_burn_voice.py')
s=p.read_text(encoding='utf-8')
old="rrep(main, r'    private boolean validatePrintSequenceForBase\\(\\) \\{.*?(?=    private LinearLayout buildTestPanel\\(\\))', validation, 'DODGE both validation')"
new="rrep(main, r'    private boolean validatePrintSequenceForBase\\(\\) \\{.*?(?=    private String testBaseFilterButtonLabel\\(\\))', validation, 'DODGE both validation')"
if old not in s:
    raise SystemExit('prepare v0.10.4: matcher validation non trovato')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('prepare v0.10.4 OK: helper ricetta preservati',flush=True)
