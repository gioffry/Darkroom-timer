#!/usr/bin/env python3
"""Darkroom 0.7.1: force installation of the bundled timing database after app update."""
from pathlib import Path

STORE = Path("combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
s = STORE.read_text(encoding="utf-8")

old = 'private static final String DB_NAME = "mdc_offline_darkroom_v058.sqlite";'
new = 'private static final String DB_NAME = "mdc_offline_darkroom_v071.sqlite";'
if old not in s:
    raise SystemExit("v0.7.1 old DB_NAME marker missing")
s = s.replace(old, new, 1)

marker = "final class MdcOfflineStore {\n"
if marker not in s:
    raise SystemExit("v0.7.1 class marker missing")
s = s.replace(marker, marker + "    // DATABASE_REFRESH_071 — new bundled timing DB must install on app update.\n", 1)

STORE.write_text(s, encoding="utf-8")

assert 'mdc_offline_darkroom_v071.sqlite' in s
assert 'DATABASE_REFRESH_071' in s
print("database_refresh_071=APPLIED")
print("database_name=mdc_offline_darkroom_v071.sqlite")
print("user_preferences_changed=NO")
