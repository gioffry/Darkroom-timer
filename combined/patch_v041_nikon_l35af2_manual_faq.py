#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.1 Nikon L35AF2: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

NEW_URL = 'https://drive.google.com/file/d/1jJn6XXhkkGJqSR9JKD377LqSL7hte14p/view?usp=drivesdk'

# The previous entry was for the first L35AF, which has a manual ASA/ISO ring.
# This release targets the user's later Nikon L35AF2 / One Touch with automatic DX.
s, n = re.subn(
    r'private static final String NIKON_L35AF_URL = "[^"]+";',
    'private static final String NIKON_L35AF_URL = "' + NEW_URL + '";',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('v0.4.1 Nikon L35AF2: old manual URL marker missing')

start = s.find('    private static final String[] Q_NIKON_L35AF = {')
end = s.find('    private static final String[] Q_NIKON_D100 = {', start)
if start < 0 or end < 0:
    raise SystemExit('v0.4.1 Nikon L35AF2: FAQ block markers missing')

faq_block = r'''    private static final String[] Q_NIKON_L35AF = {
            "Quali batterie usa la Nikon L35AF2?",
            "Come si imposta la sensibilità ISO della pellicola?",
            "Come si carica correttamente la pellicola?",
            "Come si usa l’autofocus e il blocco della messa a fuoco?",
            "Quando si alza il flash e qual è la sua portata?",
            "Qual è la distanza minima di messa a fuoco?",
            "Come si usa l’autoscatto?",
            "Come si riavvolge e si rimuove il rullo?",
            "Come si accende e si spegne la fotocamera?",
            "Come va conservata e quando conviene togliere le batterie?"
    };
    private static final String[] A_NIKON_L35AF = {
            "Usa 2 batterie AA alcalino-manganese da 1,5 V. Il manuale specifica di sostituirle entrambe insieme e indica che le batterie Ni-Cd non devono essere usate. Con batterie fresche l’autonomia dichiarata è circa 100 rulli da 24 pose senza flash oppure circa 10 rulli se tutte le fotografie richiedono il flash.",
            "Non si imposta manualmente: la L35AF2 legge automaticamente il codice DX. Il manuale dichiara il campo ISO 50-1600. Se il rullo non ha codifica DX, la fotocamera lo imposta automaticamente a ISO 100. Questa versione non possiede la ghiera ASA/ISO della prima L35AF.",
            "Apri il dorso, inserisci la cartuccia e porta la coda della pellicola fino al riferimento rosso nel vano. Controlla che non ci sia troppo lasco e che le perforazioni siano correttamente impegnate. Chiudi il dorso e premi una volta il pulsante di scatto: la macchina avanza automaticamente fino al fotogramma 1. L’indicatore di avanzamento deve ruotare durante il trascinamento.",
            "Centra il soggetto nei riferimenti AF del mirino e premi leggermente il pulsante di scatto: la messa a fuoco viene misurata e bloccata finché mantieni la pressione. Se il soggetto è decentrato, dopo il blocco ricomponi senza sollevare il dito e poi premi fino in fondo. Il manuale consiglia il focus lock anche con soggetti molto piccoli, lucidi, dietro un vetro o con forti sorgenti luminose.",
            "Con luce insufficiente il flash incorporato si solleva automaticamente quando premi leggermente il pulsante di scatto. Attendi la spia di pronto flash: finché il flash non è carico lo scatto resta bloccato. Portata dichiarata: ISO 50 circa 0,7-2,5 m; ISO 100 circa 0,7-3,6 m; ISO 200-1600 circa 0,7-4,0 m. Il tempo di ricarica indicativo è circa 6 secondi con batterie fresche.",
            "Il sistema autofocus attivo è dichiarato operativo da circa 0,7 m all’infinito. Per soggetti più vicini di 70 cm il manuale non garantisce una messa a fuoco corretta.",
            "Porta la leva dell’autoscatto fino a fine corsa e premi il pulsante di scatto. Il ritardo è di circa 10 secondi e la lampada dell’autoscatto segnala il funzionamento. Per annullare prima dello scatto, riporta la leva nella posizione iniziale.",
            "Alla fine del rullo l’avanzamento si arresta. Premi il pulsante di riavvolgimento mentre fai scorrere l’interruttore dedicato e attendi che il riavvolgimento finisca prima di aprire il dorso. Il manuale indica circa 20 secondi per un rullo da 24 pose; il contafotogrammi arretra durante il riavvolgimento e si azzera quando apri il dorso.",
            "Il copriobiettivo scorrevole funge anche da interruttore. Aprendolo la fotocamera si accende; chiudendolo la fotocamera si spegne e il pulsante di scatto viene bloccato. È quindi buona pratica richiuderlo quando non usi la macchina.",
            "Conservala in un luogo fresco e asciutto, evita temperature eccessive e pulisci delicatamente lente, finestre autofocus ed esposimetro. Se si bagna, asciugala completamente con un panno morbido. Il manuale raccomanda di rimuovere le batterie se la fotocamera non verrà usata per più di due settimane. Al freddo la capacità delle batterie diminuisce temporaneamente; per guasti o malfunzionamenti è indicata l’assistenza Nikon autorizzata."
    };

'''
s = s[:start] + faq_block + s[end:]

old_card = '        body.addView(navCard("NIKON L35AF","Compatta 35 mm autofocus · 5 FAQ",()->navigate(()->renderFaqPage("NIKON L35AF","Fonte: Nikon L35AF - Manuale IT",Q_NIKON_L35AF,A_NIKON_L35AF,NIKON_L35AF_URL,"APRI MANUALE COMPLETO"))));'
new_card = '        body.addView(navCard("NIKON L35AF2","One Touch · DX automatico · 35 mm · 10 FAQ",()->navigate(()->renderFaqPage("NIKON L35AF2","Fonte: Nikon L35AF2 / One Touch - Manuale originale completo tradotto in italiano",Q_NIKON_L35AF,A_NIKON_L35AF,NIKON_L35AF_URL,"APRI MANUALE COMPLETO"))));'
if old_card not in s:
    raise SystemExit('v0.4.1 Nikon L35AF2: old navigation card marker missing')
s = s.replace(old_card, new_card, 1)

p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
required = [
    NEW_URL,
    'NIKON L35AF2',
    'DX automatico',
    'Quali batterie usa la Nikon L35AF2?',
    'ISO 50-1600',
    'ISO 100',
    '2 batterie AA',
    '0,7-3,6 m',
    'circa 10 secondi',
    'circa 20 secondi',
    'più di due settimane',
    'APRI MANUALE COMPLETO',
]
for marker in required:
    if marker not in out:
        raise SystemExit('v0.4.1 Nikon L35AF2 guard missing: ' + marker)

for forbidden in [
    'La sensibilità non viene letta automaticamente: va impostata sulla ghiera ASA/ISO',
    'da 50 a 1000 ISO',
    'Fonte: Nikon L35AF - Manuale IT',
    'Compatta 35 mm autofocus · 5 FAQ',
]:
    if forbidden in out:
        raise SystemExit('v0.4.1 Nikon L35AF2 obsolete marker remains: ' + forbidden)

q = out[out.index('private static final String[] Q_NIKON_L35AF'):out.index('private static final String[] A_NIKON_L35AF')]
a = out[out.index('private static final String[] A_NIKON_L35AF'):out.index('private static final String[] Q_NIKON_D100')]
if q.count('            "') != 10 or a.count('            "') != 10:
    raise SystemExit('v0.4.1 Nikon L35AF2 FAQ count is not 10/10')

print('Darkroom v0.4.1 Nikon L35AF2 manual/FAQ patch ready')
