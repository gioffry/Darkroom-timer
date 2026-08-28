#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.0 Minolta: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

NEW_URL = 'https://drive.google.com/file/d/1rniErjqK3_S-0pDY3mvXosb4dk_Y0GOV/view?usp=drivesdk'

# Replace the old reference-document link with the complete Italian PDF.
s, n = re.subn(
    r'private static final String MINOLTA_REFERENCE_URL = "[^"]+";',
    'private static final String MINOLTA_MANUAL_URL = "' + NEW_URL + '";',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('v0.4.0 Minolta: old reference URL marker missing')

start = s.find('    private static final String[] Q_MINOLTA = {')
end = s.find('    private static final String[] Q_TESTSTRIP = {', start)
if start < 0 or end < 0:
    raise SystemExit('v0.4.0 Minolta: FAQ block markers missing')

faq_block = r'''    private static final String[] Q_MINOLTA = {
            "Quale batteria usa il Minolta Auto Meter IIIF?",
            "Come imposto la sensibilità ISO/ASA della pellicola?",
            "Come uso correttamente il Viewfinder 10° per una misura riflessa selettiva?",
            "Come scelgo tra visualizzazione numero f ed EV e come leggo i decimi di stop?",
            "Come funzionano memoria, richiamo e calcolo della media?",
            "Come misuro un flash elettronico?",
            "Come confronto luce ambiente e flash?",
            "Come misuro il rapporto di illuminazione tra due sorgenti o zone?",
            "Come uso il Minolta in camera oscura per ricavare esposizioni di ingrandimento con Spot Mask II?",
            "Come regolo finemente la taratura dell’esposimetro se le letture non coincidono con un riferimento?"
    };
    private static final String[] A_MINOLTA = {
            "Usa una sola batteria da 6 V. Il manuale ammette tre famiglie equivalenti: alcalina-manganese 4LR44 (Eveready 537 o equivalente), litio 2CR-1/3N o equivalente, oppure ossido d’argento 4SR44 (Eveready 544 o equivalente). Se l’esposimetro resta inutilizzato per due settimane o più, Minolta consiglia di rimuovere la batteria. Quando la tensione è quasi insufficiente, il display lampeggia per circa 8 secondi dopo la pressione del pulsante di misura; a batteria esaurita il display resta vuoto.",
            "Accendi l’esposimetro e porta la visualizzazione sulla sensibilità pellicola con ASA/TIME. Regola ASA con i tasti di incremento e decremento: ogni pressione cambia di 1/3 di stop, nel campo ASA/ISO 12-6400. In questa modalità non si eseguono misure; sono attivi soltanto incremento, decremento e ASA/TIME. Se la pellicola è indicata in DIN, usa la tabella ASA/DIN sul retro del corpo.",
            "Monta il Viewfinder 10° sulla testa ricevente allineando il riferimento rosso, inseriscilo nel suo innesto e ruotalo fino al bloccaggio. In AMBI imposta ASA, tempo e modalità FNo oppure EV. Ruota la testa ricevente di circa 180° finché l’oculare si trova davanti. Dalla posizione della fotocamera guarda attraverso il mirino: il cerchio interrotto delimita il campo di 10° e il punto indica il centro. Tieni premuto il pulsante di misura finché la lettura si stabilizza, poi rilascialo per conservarla sul display.",
            "Con FNo/EV puoi alternare fra numero f ed EV anche dopo una misura. In modalità numero f il display mostra l’apertura e una cifra decimale in decimi di stop: per esempio f/8 con decimale 0 significa esattamente f/8; f/8 con decimale 5 richiede una posizione a metà fra f/8 e f/11. In modalità EV la lettura è espressa in passi di 0,1 EV. Dopo una misura, cambiare ASA o tempo modifica direttamente il numero f; in EV è il cambio ASA a modificare la lettura EV digitale.",
            "Dopo una misura premi MEMORY per memorizzarla. Il Minolta può conservare due misure; la lettura corrente e quelle memorizzate compaiono anche come indici sulla scala analogica. RECALL richiama in sequenza i dati memorizzati; M-CLR cancella la memoria. Per ottenere la media devi prima memorizzare due misure e poi premere AVERAGE: sul display appare la media e la lettera A, mentre sulla scala analogica resta visibile anche il rapporto fra le letture. Premendo RECALL si esce dalla visualizzazione della media. Passare da AMBI a FLASH o viceversa cancella la memoria.",
            "Imposta prima la sensibilità pellicola in AMBI, poi sposta il selettore su FLASH. Non usare 1/50 s come tempo di misura flash: scegli 60 (1/60 s) oppure 250 (1/250 s), normalmente quello più vicino al tempo di sincronizzazione della fotocamera. Tieni il diffusore sferico rivolto verso la fotocamera dal punto del soggetto. Premi a fondo il pulsante di misura e rilascialo: il circuito resta pronto per circa 20 secondi e sul display compare F. Attendi circa un secondo, poi fai scattare il flash; il display mostra il numero f misurato. I flash a lampadina non sono misurabili.",
            "In modalità FLASH puoi registrare separatamente ambiente e flash. Imposta ASA e 60 o 250, premi il pulsante di misura una volta per preparare il flash, quindi premilo di nuovo: viene misurata la luce ambiente. Memorizza la lettura con MEMORY. Premi ancora il pulsante di misura e fai scattare il flash: la lettura flash appare digitalmente e le letture ambiente/flash possono essere confrontate sulla scala analogica. Se vuoi considerare la luce ambiente a 1/125 s, il manuale indica di misurare e memorizzare a 60 e a 250 e poi usare AVERAGE.",
            "Con il diffusore piano misura prima la sorgente principale, in EV, e memorizzala; poi orienta il diffusore verso la sorgente secondaria e fai una seconda misura. La differenza in EV si ricava sottraendo le due letture oppure contando gli intervalli sulla scala analogica. La tabella I del manuale converte la differenza in rapporto di illuminazione: ad esempio una differenza di circa 1,5 EV corrisponde a circa 3:1. Lo stesso principio può essere usato per rapporti di contrasto con il Viewfinder 10° o l’accessorio riflesso 40°.",
            "Il manuale prevede l’uso in camera oscura con Spot Mask II. Prepara prima una stampa di prova soddisfacente da un negativo con una zona di densità media. Con l’ingranditore nelle stesse condizioni, posa il Minolta sul piano di stampa nella zona in cui quella tonalità cade sullo Spot Mask, seleziona AMBI e EV, misura e memorizza il valore. Con negativi successivi di qualità e tonalità simili, colloca il Minolta nella zona corrispondente e regola il diaframma dell’obiettivo dell’ingranditore finché l’EV coincide con quello memorizzato; usa quindi lo stesso tempo di esposizione della stampa di prova.",
            "La vite di regolazione del livello di misura si trova sotto il coperchio batteria. Minolta la calibra in fabbrica, ma consente una regolazione continua fino a circa ±1 EV. Le tacche bianche attorno alla vite corrispondono a circa 0,2 EV ciascuna. A parità di luce, ruotando verso destra si ottengono letture più basse, verso sinistra più alte. Non superare i limiti ±1 EV e intervieni solo dopo aver verificato con esperienza lo scostamento reale. Per le misure di illuminamento la vite deve essere riportata alla posizione standard originale."
    };

'''
s = s[:start] + faq_block + s[end:]

old_nav = '        body.addView(navCard("MINOLTA AUTO METER IIIF","Viewfinder 10° · manuale completo non disponibile",()->navigate(this::renderMinolta)));'
new_nav = '        body.addView(navCard("MINOLTA AUTO METER IIIF","Viewfinder 10° · flash · Spot Mask II · manuale completo IT",()->navigate(this::renderMinolta)));'
if old_nav not in s:
    raise SystemExit('v0.4.0 Minolta: navigation card marker missing')
s = s.replace(old_nav, new_nav, 1)

old_render = '    private void renderMinolta(){ String[] answers=new String[Q_MINOLTA.length]; for(int i=0;i<answers.length;i++) answers[i]=MINOLTA_PENDING; renderFaqPage("MINOLTA AUTO METER IIIF","Viewfinder 10° · fonte completa non disponibile nel Drive",Q_MINOLTA,answers,MINOLTA_REFERENCE_URL,"APRI RIFERIMENTO DRIVE"); notice("La cupoletta incidente non viene trattata. Le FAQ sono impostate sul Viewfinder 10°, ma le risposte tecniche restano sospese finché non è disponibile il manuale completo."); }'
new_render = '    private void renderMinolta(){ renderFaqPage("MINOLTA AUTO METER IIIF","Fonte: manuale originale Minolta completo · traduzione italiana",Q_MINOLTA,A_MINOLTA,MINOLTA_MANUAL_URL,"APRI MANUALE COMPLETO"); notice("Manuale completo tradotto in italiano con tavole, fotografie, diagrammi e pagine originali conservati."); }'
if old_render not in s:
    raise SystemExit('v0.4.0 Minolta: old renderMinolta marker missing')
s = s.replace(old_render, new_render, 1)

p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
required = [
    'MINOLTA_MANUAL_URL', NEW_URL,
    'Quale batteria usa il Minolta Auto Meter IIIF?',
    '4LR44', '2CR-1/3N', '4SR44',
    'Viewfinder 10°', 'Spot Mask II',
    'A_MINOLTA', 'APRI MANUALE COMPLETO',
    'manuale originale Minolta completo · traduzione italiana',
]
for marker in required:
    if marker not in out:
        raise SystemExit('v0.4.0 Minolta guard missing: ' + marker)
for forbidden in ['MINOLTA_PENDING', 'manuale completo non disponibile', 'APRI RIFERIMENTO DRIVE', 'MINOLTA_REFERENCE_URL']:
    if forbidden in out:
        raise SystemExit('v0.4.0 Minolta obsolete marker remains: ' + forbidden)

# Exactly ten questions and ten answers.
q = out[out.index('private static final String[] Q_MINOLTA'):out.index('private static final String[] A_MINOLTA')]
a = out[out.index('private static final String[] A_MINOLTA'):out.index('private static final String[] Q_TESTSTRIP')]
if q.count('            "') != 10 or a.count('            "') != 10:
    raise SystemExit('v0.4.0 Minolta FAQ count is not 10/10')

print('Darkroom v0.4.0 Minolta manual/FAQ patch ready')
