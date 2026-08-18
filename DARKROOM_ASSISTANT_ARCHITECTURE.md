# Darkroom Assistant — architettura modulare

## Release 1 / 9

Il progetto resta una sola app Android, un solo repository e un solo APK con application ID `it.darkroom.timer`.

### STAMPA

Il modulo STAMPA coincide con il Darkroom Timer esistente.

- package esistente: `it.darkroom.timer`
- `MainActivity` resta l'entry point dell'app
- SONOFF, LAN, pulsante fisico, safelight, timer, secondi/f-stop, provini, Dodge, Burn, Split Grade, filtri, Log e impostazioni restano nel percorso esistente
- in Release 1 viene aggiunto soltanto un ingresso verso il nuovo modulo

Non spostare o rifattorizzare il Timer senza una release dedicata e test specifici: la priorità è evitare regressioni.

### SVILUPPO & CHIMICA

Il nuovo Darkroom Assistant vive in un package separato:

`it.darkroom.timer.assistant`

Release 1 introduce soltanto `AssistantActivity`, con i segnaposto:

- Nuovo sviluppo
- Prepara chimica
- La mia chimica
- Le mie ricette
- Log sviluppi
- La mia attrezzatura

Nessuno di questi elementi contiene ancora logica applicativa.

### Componenti condivisi futuri

Creare componenti condivisi solo quando servono realmente a entrambi i moduli. Se necessario, potranno essere introdotti in futuro in un'area dedicata (per esempio `it.darkroom.timer.shared`) per persistenza, impostazioni generali, attrezzatura comune o backup.

Release 1 non crea database, API, inventari, ricette, calcoli chimici o altre infrastrutture anticipate.

### Compatibilità installazione

Invarianti da preservare:

- application ID/package installato: `it.darkroom.timer`
- stessa identità dell'app
- stessa firma stabile gestita da GitHub Actions
- stessi nomi delle preferenze e degli archivi esistenti
- nessuna cancellazione o migrazione dei dati del Timer

La Release 1 usa `versionName 0.7.0` e `versionCode 33` per consentire l'aggiornamento sopra la 0.6.4.
