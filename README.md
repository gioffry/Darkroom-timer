# Darkroom Timer

Repository operativo per gli aggiornamenti automatici dell'app Darkroom Timer.

## Base stabile

La base di compilazione è `DarkroomTimer-v0.5.8-BUILD.zip`, firmata con la chiave stabile conservata nei GitHub Actions Secrets.

## Aggiornamenti successivi

Le modifiche successive alla 0.5.8 vengono salvate come patch testuali nella cartella `patches/`. GitHub Actions:

1. estrae automaticamente la base 0.5.8;
2. applica tutte le patch in ordine;
3. legge la versione risultante;
4. compila l'APK;
5. firma l'APK con la stessa chiave stabile;
6. pubblica l'APK come artifact.

Questo permette di preparare nuove versioni senza dover ricaricare manualmente ZIP o modificare il workflow a ogni aggiornamento.
