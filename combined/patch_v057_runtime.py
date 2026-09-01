#!/usr/bin/env python3
"""Force installation of the v0.5.7 bundled offline snapshot."""

from pathlib import Path


STORE = Path("combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
source = STORE.read_text(encoding="utf-8")
old = '    private static final String DB_NAME = "mdc_offline_darkroom_v056.sqlite";'
new = '    private static final String DB_NAME = "mdc_offline_darkroom_v057.sqlite";'
if source.count(old) != 1:
    raise SystemExit("v0.5.7 database filename marker missing")
STORE.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Darkroom v0.5.7 runtime uses a fresh bundled offline snapshot")
