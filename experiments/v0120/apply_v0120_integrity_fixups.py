#!/usr/bin/env python3
from pathlib import Path
import sys
work=Path(sys.argv[1]);java=work/'project/app/src/main/java/it/darkroom/timer';here=Path(__file__).parent

def rd(p):return Path(p).read_text(encoding='utf-8')
def wr(p,s):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(s,encoding='utf-8')
def rep(p,o,n,label):
    s=rd(p)
    if o not in s:raise SystemExit('v0.12.0 fixup anchor missing: '+label)
    wr(p,s.replace(o,n,1));print('v0.12.0 FIXUP OK',label,flush=True)

backup=java/'assistant/system/BackupEngine.java';paper=java/'assistant/paper/PaperChemistryActivity.java'
# Personal backup must not replace the technical catalog/cache.
rep(backup,'"personal_equipment","personal_tanks","assistant_sessions","paper_chemistry_sessions","technical_source_cache"','"personal_equipment","personal_tanks","assistant_sessions","paper_chemistry_sessions"','exclude technical source cache from personal backup')
rep(backup,'"assistant_operational","assistant_settings","paper_chemistry_session","catalog_meta","print_log"','"assistant_operational","assistant_settings","paper_chemistry_session","print_log"','exclude catalog metadata from personal backup')
rep(backup,'"personal_recipes","assistant_sessions","paper_chemistry_sessions","technical_source_cache"','"personal_recipes","assistant_sessions","paper_chemistry_sessions"','do not delete technical catalog during replace')

# R8 common metadata shape supports documented or personal paper products without inventing missing values.
wr(java/'assistant/paper/PaperProductData.java',rd(here/'PaperProductData.java'))
rep(paper,'if(AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType))return "DATI DOCUMENTATI · "+emptyOr(x.sourceName,"fonte catalogo");return "DATI PERSONALI · inseriti dall\'utente";',
'''String base=AssistantDatabase.SOURCE_CATALOG.equals(x.sourceType)?"DATI DOCUMENTATI · "+emptyOr(x.sourceName,"fonte catalogo"):"DATI PERSONALI · inseriti dall'utente";\n        if(x.capacityValue>0&&!empty(x.capacityUnit))base+=" · CAPACITÀ "+fmt(x.capacityValue)+" "+x.capacityUnit;else base+=" · CAPACITÀ NON DOCUMENTATA";\n        return base;''','paper capacity provenance')

bt=rd(backup);pt=rd(java/'assistant/paper/PaperProductData.java')
if 'technical_source_cache' in bt or 'catalog_meta' in bt:raise SystemExit('v0.12.0 backup still contains technical catalog data')
for n in ['temperatureC=null','timeSeconds=null','capacityValue=null','solutionLife','useMode','sourceType']:
    if n not in pt:raise SystemExit('v0.12.0 paper product field missing: '+n)
print('v0.12.0 R8/R9 data-separation fixups: OK',flush=True)
