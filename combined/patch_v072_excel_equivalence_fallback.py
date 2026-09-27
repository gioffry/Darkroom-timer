#!/usr/bin/env python3
"""Darkroom 0.7.2: allow approved Fomadon Excel equivalence fallback when no exact time exists."""
from pathlib import Path

ACT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
s = ACT.read_text(encoding="utf-8")

old = '''            if (result != null && result.found &&
                    "Fomadon Excel".equalsIgnoreCase(dev.name) &&
                    result.diagnostic != null &&
                    result.diagnostic.startsWith("EQUIVALENTE_APPROVATO|")) {
                result = DevTimeEngine.Result.notFound(
                        "Fomadon Excel " + dilution +
                        ": nessun tempo esatto disponibile. Per sicurezza non viene usata automaticamente un'equivalenza con un altro rivelatore.");
            }
'''
if old not in s:
    raise SystemExit("v0.7.2 legacy Excel equivalence blocker missing")

s = s.replace(old, "", 1)

marker = "public class AssistantActivityV2 extends Activity {\n"
if marker not in s:
    raise SystemExit("v0.7.2 Assistant class marker missing")
s = s.replace(marker, marker + "    // EXCEL_EQUIVALENCE_FALLBACK_072\n", 1)

if 'EXCEL_EQUIVALENCE_FALLBACK_072' not in s:
    raise SystemExit("v0.7.2 marker missing")
if 'Per sicurezza non viene usata automaticamente un\'equivalenza con un altro rivelatore.' in s:
    raise SystemExit("v0.7.2 blocker still present")

ACT.write_text(s, encoding="utf-8")
print("excel_equivalence_fallback_072=APPLIED")
print("fomadon_excel_approved_equivalence=ENABLED_WHEN_EXACT_MISSING")
