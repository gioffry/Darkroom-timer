#!/usr/bin/env python3
from pathlib import Path

p = Path('experiments/v080/apply_v080_print_sequence.py')
s = p.read_text(encoding='utf-8')

def replace_labeled_block(label_text, start_token, new_block):
    global s
    label = "'" + label_text + "')"
    end = s.index(label) + len(label)
    start = s.rfind(start_token, 0, end)
    if start < 0:
        raise SystemExit('prepare v0.8.0: inizio blocco non trovato: ' + label_text)
    s = s[:start] + new_block + s[end:]

replace_labeled_block(
    'LogStore write sequence', 'rep(logstore,',
    """rep(logstore,\n'''                    .append(enc(e.testStripTimes));''',\n'''                    .append(enc(e.testStripTimes)).append('\\t')\n                    .append(enc(e.printSequence));''', 'LogStore write sequence')""")

replace_labeled_block(
    'log editor sequence display', 'rep(main,',
    r'''_s = rd(main)
_old = r''' + "'''                \"\\nData: \" + formatDate(entry.timestamp) +'''" + r'''
_new = r''' + "'''                \"\\nSequenza di stampa: \" + sequenceRecipe +\n                \"\\nData: \" + formatDate(entry.timestamp) +'''" + r'''
if _old not in _s: raise SystemExit('v0.8.0 log editor sequence display: target non trovato')
wr(main, _s.replace(_old, _new, 1)); print('v0.8.0 OK log editor sequence display', flush=True)''')

p.write_text(s, encoding='utf-8')
print('prepare v0.8.0 OK: matcher LogStore + ricetta LOG robusti', flush=True)
