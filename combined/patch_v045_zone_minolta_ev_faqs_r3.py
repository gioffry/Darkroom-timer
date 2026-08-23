#!/usr/bin/env python3
from pathlib import Path
import re
import runpy

# Apply the v0.4.5 content patch. The first revision writes the complete source
# before its legacy source-count guards; catch only those known count guards and
# validate the actual Java array bodies below.
try:
    runpy.run_path('combined/patch_v045_zone_minolta_ev_faqs.py', run_name='__main__')
except SystemExit as exc:
    msg = str(exc)
    allowed = {
        'v0.4.5 Minolta question count != 12',
        'v0.4.5 Minolta answer count != 12',
        'v0.4.5 Zone question count != 11',
        'v0.4.5 Zone answer count != 11',
    }
    if msg not in allowed:
        raise

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
s = p.read_text(encoding='utf-8')

def array_body(name: str) -> str:
    marker = 'private static final String[] ' + name + ' = {'
    start = s.index(marker)
    body_start = s.index('{', start) + 1
    end = s.index('\n    };', body_start)
    return s[body_start:end]

def strings(name: str):
    body = array_body(name)
    return re.findall(r'"(?:\\.|[^"\\])*"', body)

q_min = strings('Q_MINOLTA')
a_min = strings('A_MINOLTA')
q_zone = strings('Q_ZONE')
a_zone = strings('A_ZONE')

assert len(q_min) == 12, len(q_min)
assert len(a_min) == 12, len(a_min)
assert len(q_zone) == 11, len(q_zone)
assert len(a_zone) == 11, len(a_zone)

TABLE_Q = 'Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?'
MINOLTA_ZONE_Q = 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?'
ZONE_FIELD_Q = 'Come utilizzo rapidamente il Sistema Zonale sul campo?'

qm = array_body('Q_MINOLTA')
qz = array_body('Q_ZONE')
assert qm.index(TABLE_Q) < qm.index(MINOLTA_ZONE_Q)
assert qz.index(ZONE_FIELD_Q) < qz.index('Cos’è il Sistema Zonale e a cosa serve?')

for marker in (
    TABLE_Q,
    '| 1/125 ★ | 9,9 | — | 11,0 | 11,9 | 13,0 | 13,9 | 15,0 | 15,9 |',
    '★ = Rolleiflex 2.8 E2',
    '● = Rolleiflex 3.5 Tessar MX',
    'Gli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.',
    MINOLTA_ZONE_Q,
    'Passa alla visualizzazione FNo..',
    'togli sempre 2 stop rispetto alla lettura fornita dal Minolta.',
    ZONE_FIELD_Q,
    'EV misurato + 2 = EV di esposizione',
    'Zona III + 5 = Zona VIII',
    'Misura l’ombra con dettaglio → togli 2 stop → scatta.',
    'HorizontalScrollView',
    'Typeface.MONOSPACE',
):
    assert marker in s, marker

print('Darkroom v0.4.5 Zone + Minolta EV FAQs patch r3 ready')
print('minolta_questions=12')
print('minolta_answers=12')
print('minolta_ev_table_first=PASS')
print('minolta_zone_faq_second=PASS')
print('zone_questions=11')
print('zone_answers=11')
print('zone_field_faq_first=PASS')
