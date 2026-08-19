from pathlib import Path

# v0.3.4
# Fix esatto del problema mostrato su Android:
# l'asset SQLite viene generato con PRAGMA user_version=2, mentre
# SQLiteOpenHelper era ancora configurato con DB_VERSION=1. Android quindi
# tentava un downgrade 2 -> 1 e rifiutava di aprire il database.

p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')

if 'private static final int DB_VERSION = 1;' not in s:
    raise SystemExit('DB_VERSION=1 marker missing')
s = s.replace('private static final int DB_VERSION = 1;',
              'private static final int DB_VERSION = 2;', 1)

# Nuovo nome: ignora il file v0.3.3 gia copiato sul telefono.
if 'private static final String DB_NAME = "mdc_offline_v033.sqlite";' not in s:
    raise SystemExit('v033 DB name marker missing')
s = s.replace('private static final String DB_NAME = "mdc_offline_v033.sqlite";',
              'private static final String DB_NAME = "mdc_offline_v034.sqlite";', 1)

p.write_text(s, encoding='utf-8')
print('v0.3.4 SQLite schema version aligned: asset=2 helper=2')
