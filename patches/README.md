# Aggiornamenti Darkroom Timer

La v0.5.8 è la base stabile del progetto.

Le versioni successive vengono applicate in ordine tramite file `.patch` presenti in questa cartella. Ogni patch può modificare sia i sorgenti sotto `project/` sia `build_darkroom.py` (per aggiornare versionName/versionCode del builder).

GitHub Actions estrae automaticamente la base 0.5.8, applica tutte le patch in ordine alfabetico, compila l'APK e lo firma con la chiave stabile conservata nei Repository Secrets.

Convenzione file: `v0.5.9.patch`, `v0.6.0.patch`, ecc.
