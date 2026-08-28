#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# Runtime safety net: even if a future database row accidentally contains
# English prose in an *_it field, the Italian card must not display a hybrid.
pat = re.compile(r'''    private boolean containsEnglishTechnical\(String value\) \{.*?\n    \}\n\n    private String safeItalianTechnical''', re.S)
rep = r'''    private boolean containsEnglishTechnical(String value) {
        String v = " " + cleanTechnicalText(value).toLowerCase(Locale.ROOT)
                .replace('\n', ' ') + " ";
        String[] bad = new String[]{
                " the ", " and ", " with ", " when ", " should ", " would ", " could ",
                " stored ", " store ", " keep ", " working ", " working solution ",
                " original package ", " minimum ", " defines ", " processing ",
                " explicitly ", " before ", " after ", " protected ", " darkness ",
                " oxidation ", " later ", " replace ", " guaranteed ", " reached ",
                " direct sun ", " air access ", " unopened ", " opened concentrate ",
                " prepared ", " manufacturer ", " depending on ", " once opened ",
                " use once ", " discard ", " recommended ", " about ",
                " per litre ", " per liter ", " rolls ", " sheets ", " developer ",
                " replenisher ", " concentrate ", " powder ", " liquid ",
                " full-strength ", " full strength ", " full closed ", " closed container ",
                " without use ", " lists ", " useful tank ", " chemistry matrix ",
                " us gallon ", " bottle ", " shelf life ", " dissolve ", " water ",
                " stir ", " cool ", " fresh ", " reuse ", " partially exhausted ",
                " well-closed ", " ready-to-use ", " at least ", " up to "
        };
        for (String word : bad) if (v.contains(word)) return true;
        return false;
    }

    private String safeItalianTechnical'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.7 English display gate replacement failed')

# Operational shelf-life text must pass the same Italian gate as the rest of
# the technical card. v0.3.7 database generation already writes structured
# Italian duration sentences; these replacements prevent any raw fallback.
pat = re.compile(r'''    private void appendOperationalDuration\(StringBuilder out, String kind, String value, String condition\) \{.*?\n    \}\n\n    private String operationalSourceLabel''', re.S)
rep = r'''    private void appendOperationalDuration(StringBuilder out, String kind, String value, String condition) {
        String v = safeItalianTechnical(value);
        if (v.isEmpty()) return;
        String label = "STOCK_PREPARATO".equals(kind)
                ? "Durata stock preparato · bottiglia piena"
                : "Durata concentrato aperto · bottiglia piena";
        appendTechRaw(out, label, v);
        String c = safeItalianTechnical(condition);
        if (!c.isEmpty()) appendTechRaw(out, "Condizione di conservazione usata", c);
    }

    private String operationalSourceLabel'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.7 operational duration gate replacement failed')

s = s.replace('"Durata: " + cleanTechnicalText(info.text) + "\\nScadenza automatica non calcolabile da un intervallo non numerico."',
              '"Durata: " + safeItalianTechnical(info.text) + "\\nScadenza automatica non calcolabile da un intervallo non numerico."')
s = s.replace('.append(cleanTechnicalText(life.text));', '.append(safeItalianTechnical(life.text));')
s = s.replace('TextView durationView = label(cleanTechnicalText(lifeInfo.text), 14, WHITE, false);',
              'TextView durationView = label(safeItalianTechnical(lifeInfo.text), 14, WHITE, false);')

# Acceptance markers used by CI.
if '" useful tank "' not in s or 'safeItalianTechnical(lifeInfo.text)' not in s:
    raise SystemExit('v0.3.7 runtime Italian acceptance markers missing')

p.write_text(s, encoding='utf-8')

# Force a fresh extraction of the cleaned bundled SQLite when upgrading from
# v0.3.6; otherwise an already-installed app could keep the old English/hybrid
# database file on disk even though the APK contains the corrected asset.
m = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms = m.read_text(encoding='utf-8')
if 'mdc_offline_darkroom_v036.sqlite' not in ms:
    raise SystemExit('v0.3.7 expected v0.3.6 DB filename missing')
ms = ms.replace('mdc_offline_darkroom_v036.sqlite', 'mdc_offline_darkroom_v037.sqlite')
m.write_text(ms, encoding='utf-8')

print('v0.3.7 runtime Italian display gate applied')
print('v0.3.7 fresh SQLite copy marker applied')
