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

# Il percorso inverso deve riutilizzare la stessa filtrazione che PROVINO -> STAMPA
# salva in ExposureRecipe. Per uno Split Grade NON la convertiamo in un filtro unico:
# il piano Y/M resta separato in printSequence.split e il filtro base normale viene azzerato.
old = r'''        testWidthMs = snap(printWidthMs, 500, 36_000_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putBoolean("testFromPrint", true)
                .putInt("testWidthMs", testWidthMs)
                .apply();
        setMode(MODE_TEST);'''
new = r'''        testWidthMs = snap(printWidthMs, 500, 36_000_000);
        boolean splitSource = printSequence != null && printSequence.hasSplit();
        if (!splitSource && exposureRecipe != null) {
            testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);
            testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);
        } else if (splitSource) {
            // Nessuna equivalenza arbitraria: 60Y/180M (o i valori personalizzati)
            // rimangono nel piano Split Grade separato, non diventano un singolo filtro.
            testBaseFilterType = ExposureRecipe.FILTER_NONE;
            testBaseFilterValue = 0;
        }
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putBoolean("testFromPrint", true)
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", testBaseFilterType)
                .putInt("testBaseFilterValue", testBaseFilterValue)
                .apply();
        refreshTestBaseFilterUi();
        setMode(MODE_TEST);'''
if old not in s:
    raise SystemExit('prepare v0.10.10: blocco migrazione filtrazione non trovato')
s = s.replace(old, new, 1)

# Rafforza l'accettazione sorgente della release per il requisito filtro/contrasto.
extra = r'''

# Verifica aggiuntiva preparata: STAMPA -> PROVINO riusa la filtrazione della ricetta
# normale e non appiattisce lo Split Grade in una filtrazione equivalente.
_main_v01010 = rd(main)
for _needle in [
    'testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);',
    'testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);',
    '.putString("testBaseFilterType", testBaseFilterType)',
    'testBaseFilterType = ExposureRecipe.FILTER_NONE;',
    'printSequence.split.softLine()',
    'printSequence.split.hardLine()',
    'nessuna conversione in esposizione singola'
]:
    if _needle not in _main_v01010:
        raise SystemExit('v0.10.10 verifica filtro/migrazione fallita: ' + _needle)
print('v0.10.10 STAMPA->PROVINO — FILTRAZIONE E SPLIT SEPARATO OK', flush=True)
'''
s += extra

p.write_text(s, encoding='utf-8')
print('prepare v0.10.10 OK: SplitGrade robusto + correzioni intatte + filtrazione inversa', flush=True)
