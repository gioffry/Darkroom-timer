#!/usr/bin/env python3
from pathlib import Path
p=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
s=p.read_text(encoding='utf-8')
old='        List<FaqHit> hits=new ArrayList<>();\n        addFaqMatches(hits,"MEOPTA OPEMUS 6",Q_OPEMUS,A_OPEMUS,q);'
new='        List<FaqHit> hits=new ArrayList<>();\n        addFaqMatches(hits,"APP DARKROOM",Q_DARKROOM,A_DARKROOM,q);\n        addFaqMatches(hits,"MEOPTA OPEMUS 6",Q_OPEMUS,A_OPEMUS,q);'
if old not in s: raise SystemExit('v0.4.3b search registry marker missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
out=p.read_text(encoding='utf-8')
if 'addFaqMatches(hits,"APP DARKROOM",Q_DARKROOM,A_DARKROOM,q);' not in out: raise SystemExit('v0.4.3b app FAQ search missing')
print('Darkroom v0.4.3b APP DARKROOM FAQ search registry ready')
