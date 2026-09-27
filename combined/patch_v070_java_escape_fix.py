#!/usr/bin/env python3
"""Compilation-only fix for v0.7.0 generated Java string escapes."""
from pathlib import Path

p = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
s = p.read_text(encoding="utf-8")

replacements = [
    ('                "\nArresto: "', '                "\\nArresto: "'),
    ('                "\nFissaggio: "', '                "\\nFissaggio: "'),
    ('append("\nDiluizione: ")', 'append("\\nDiluizione: ")'),
    ('append("\nMonouso: scartare dopo l\'uso.")', 'append("\\nMonouso: scartare dopo l\'uso.")'),
    ('out.append("\n").append(indicator)', 'out.append("\\n").append(indicator)'),
    ('out.append("\n").append(filmCapacityStatus', 'out.append("\\n").append(filmCapacityStatus'),
]

changed = 0
for bad, good in replacements:
    if bad in s:
        s = s.replace(bad, good)
        changed += 1

p.write_text(s, encoding="utf-8")
print("v070_java_escape_fix=APPLIED")
print("replacements=" + str(changed))
