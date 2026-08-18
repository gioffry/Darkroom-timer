# Diario Percorsi

> Progetto separato da Darkroom Timer. Questa app vive nel branch `diario-percorsi` e nella directory `diario-percorsi/`; non va unita a `main`.

Versione GitHub-first dell'app Android.

## Come funziona il flusso

- Il codice sorgente vive su GitHub.
- Le modifiche di Diario Percorsi vengono fatte solo nel branch `diario-percorsi`.
- GitHub Actions compila automaticamente l'APK di Diario Percorsi.
- Darkroom Timer resta su `main` e non viene modificato da questo progetto.
- Eventuali chiavi future vanno in GitHub Secrets, non nel codice.

## Mappa

La mappa Camminata usa Leaflet + OpenStreetMap, quindi non richiede una API key Google.

È presente una ricerca manuale di città e luoghi, per esempio `Tarzana`, tramite OpenStreetMap/Nominatim. La ricerca non usa il GPS.

## Build

Con JDK 17 e Gradle 8.7:

```bash
python3 scripts/write_config.py
gradle assembleDebug
```

L'APK viene creato in `app/build/outputs/apk/debug/app-debug.apk`.

## Isolamento

- `main`: Darkroom Timer.
- `diario-percorsi`: Diario Percorsi.
- Directory applicativa: `diario-percorsi/`.
- Nessun merge automatico tra i due progetti.
- Application ID Diario Percorsi: `app.diariopercorsi`.
