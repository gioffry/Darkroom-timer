#!/usr/bin/env python3
from pathlib import Path

p = Path('experiments/v01010/apply_v01010_timer_splitgrade_provini.py')
s = p.read_text(encoding='utf-8')

# Rendi robusta la sostituzione delle sole etichette/prompt del modello Split Grade.
start = s.find("rep(split_grade,\n'''    public String softLine()")
end = s.find("\n\n\ndef edit_split", start)
if start < 0 or end < 0:
    raise SystemExit('prepare v0.10.10: blocco etichette SplitGradePlan non trovato')

replacement = r'''def rewrite_split_grade_labels():
    src = rd(split_grade)
    a = src.find('    public String softLine() {')
    b = src.find('    private static int snap5(', a)
    if a < 0 or b < 0:
        raise SystemExit('v0.10.10 etichette Split Grade: metodi modello non trovati')
    methods = ''' + "r'''" + r'''    public String softLine() { return "SPLIT · MORBIDA · " + softYellow + "Y / 0M · " + seconds(softMs); }
    public String hardLine() { return "SPLIT · DURA · 0Y / " + hardMagenta + "M · " + seconds(hardMs); }
    public String softPrompt() { return "Imposta " + softYellow + "Y / 0M. Poi premi il pulsante."; }
    public String hardPrompt() { return "Imposta 0Y / " + hardMagenta + "M. Poi premi il pulsante."; }

''' + "'''" + r'''
    wr(split_grade, src[:a] + methods + src[b:])
    print('v0.10.10 OK etichette Split Grade esplicite', flush=True)

rewrite_split_grade_labels()'''

s = s[:start] + replacement + s[end:]

# Non toccare l'editor DODGE/BURN: il requisito esplicito e' che le correzioni
# stampa gia' esistenti rimangano invariate. Le nuove etichette 60Y/180M sono
# rese evidenti nella schermata Split Grade, non nell'editor correzioni.
start = s.find("# Anche nell'editor DODGE/BURN")
end = s.find("\n\n# -----------------------------------------------------------------------------\n# 3. STAMPA -> PROVINO", start)
if start < 0 or end < 0:
    raise SystemExit('prepare v0.10.10: blocco accessorio DODGE/BURN non trovato')
s = s[:start] + "# DODGE/BURN lasciato intenzionalmente invariato.\n" + s[end:]

p.write_text(s, encoding='utf-8')
print('prepare v0.10.10 OK: SplitGradePlan robusto + correzioni stampa intatte', flush=True)
