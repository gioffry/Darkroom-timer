#!/usr/bin/env python3
from pathlib import Path

p = Path('experiments/v080/apply_v080_print_sequence.py')
s = p.read_text(encoding='utf-8')
label = "'LogStore write sequence')"
end = s.index(label) + len(label)
start = s.rfind('rep(logstore,', 0, end)
if start < 0:
    raise SystemExit('prepare v0.8.0: inizio blocco LogStore non trovato')
new_block = """rep(logstore,\n'''                    .append(enc(e.testStripTimes));''',\n'''                    .append(enc(e.testStripTimes)).append('\\t')\n                    .append(enc(e.printSequence));''', 'LogStore write sequence')"""
s = s[:start] + new_block + s[end:]
p.write_text(s, encoding='utf-8')
print('prepare v0.8.0 OK: matcher LogStore robusto', flush=True)
