#!/usr/bin/env python3
from pathlib import Path
import re
import runpy

# Run the v0.4.2 content patch. Its first revision writes the generated source
# before a legacy indentation-based count guard; catch only that known guard
# and replace it below with a real Java-string count.
try:
    runpy.run_path('combined/patch_v042_technique_faqs.py', run_name='__main__')
except SystemExit as exc:
    msg = str(exc)
    if msg not in {
        'v0.4.2 Color3 question count != 11',
        'v0.4.2 Color3 answer count != 11',
        'v0.4.2 process question count != 4',
        'v0.4.2 process answer count != 4',
    }:
        raise

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
s = p.read_text(encoding='utf-8')

def java_string_count(array_name: str, next_name: str) -> int:
    a = s.index('private static final String[] ' + array_name)
    b = s.index('private static final String[] ' + next_name, a)
    block = s[a:b]
    # Count Java string literals, independent of line wrapping/indentation.
    return len(re.findall(r'"(?:\\.|[^"\\])*"', block))

assert java_string_count('Q_COLOR3', 'A_COLOR3') == 11
assert java_string_count('A_COLOR3', 'Q_JOBO') == 11
assert java_string_count('Q_PROCESS_WASH', 'A_PROCESS_WASH') == 4
assert java_string_count('A_PROCESS_WASH', 'Q_TESTSTRIP') == 4

for marker in (
    'Come si sostituisce correttamente la lampada della Meopta Color 3?',
    'GZ 6.35-18',
    'PROCESSO E LAVAGGIO',
    'Come realizzare un provino a contatto?',
    'Quando è utile un pre-bagno della pellicola prima dello sviluppo?',
    'Come lavare correttamente la pellicola?',
    'Come lavare correttamente la carta RC?',
    'non farlo girare nel processore',
    'contenitore separato',
):
    assert marker in s, marker

print('Darkroom v0.4.2 technique FAQ patch r2 ready')
print('color3_questions=11')
print('color3_answers=11')
print('process_wash_questions=4')
print('process_wash_answers=4')
