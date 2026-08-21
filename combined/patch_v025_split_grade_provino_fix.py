#!/usr/bin/env python3
from pathlib import Path

main=Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')
s=main.read_text(encoding='utf-8')
old='''        provinoFlow=PROVINO_SINGLE;\n        testBaseFilterType=ExposureRecipe.normalizeFilter(splitReturnFilterType);\n        testBaseFilterValue=ExposureRecipe.snap5(splitReturnFilterValue);\n        testWidthMs=snap(splitReturnTestWidthMs,500,30_000);\n        persistSplitProvinoState();\n        refreshTestBaseFilterUi();\n        setMode(MODE_PRINT);\n'''
new='''        provinoFlow=PROVINO_SINGLE;\n        testBaseFilterType=ExposureRecipe.normalizeFilter(splitReturnFilterType);\n        testBaseFilterValue=ExposureRecipe.snap5(splitReturnFilterValue);\n        testWidthMs=snap(splitReturnTestWidthMs,500,30_000);\n        getSharedPreferences("ui",MODE_PRIVATE).edit()\n                .putInt("testWidthMs",testWidthMs)\n                .putString("testBaseFilterType",testBaseFilterType)\n                .putInt("testBaseFilterValue",testBaseFilterValue)\n                .apply();\n        persistSplitProvinoState();\n        refreshTestBaseFilterUi();\n        setMode(MODE_PRINT);\n'''
if old not in s: raise SystemExit('v0.2.5 fix: final single-provino restore anchor missing')
s=s.replace(old,new,1)
s=s.replace('Due esposizioni consecutive, tempi indipendenti.','Due esposizioni consecutive, con tempi distinti.',1)
if 'tempi indipendenti' in s: raise SystemExit('v0.2.5 fix: forbidden independence wording remains')
if 'Due esposizioni consecutive, con tempi distinti.' not in s: raise SystemExit('v0.2.5 fix: corrected wording missing')
main.write_text(s,encoding='utf-8')
print('v0.2.5 FIX OK — restored single-provino settings persist; no independence wording',flush=True)
