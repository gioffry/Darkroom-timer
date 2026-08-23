#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.4: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

# Replace the Nikon D100 FAQ block with Nikon F100 content based on the Nikon F100 Instruction Manual.
start = s.index('    private static final String[] Q_NIKON_D100 = {')
end = s.index('    private static final String[] Q_NIKON_ZOOM100 = {', start)
new_block = r'''    private static final String[] Q_NIKON_F100 = {
            "Quali batterie usa la Nikon F100?",
            "Come funziona la sensibilità ISO e la lettura DX?",
            "Come si carica correttamente la pellicola?",
            "Quali obiettivi sono pienamente compatibili con la F100?",
            "Quando usare AF-S, AF-C e Dynamic AF?",
            "Quando usare Matrix, ponderata centrale o Spot?",
            "Come funzionano i modi di esposizione P, S, A e M?",
            "Come si riavvolge il rullino, anche a metà?",
            "Qual è il tempo di sincronizzazione flash e come funziona il TTL?",
            "Come si riportano rapidamente le impostazioni ai valori di partenza?"
    };
    private static final String[] A_NIKON_F100 = {
            "La F100 usa normalmente quattro batterie AA da 1,5 V nel portabatterie MS-12: alcalino-manganese oppure al litio. Sostituiscile tutte insieme, a fotocamera spenta, usando elementi freschi dello stesso tipo e marca. Con accessori opzionali può usare anche due CR123A/DL123A tramite MS-13 oppure il battery pack MB-15.",
            "Puoi lasciare ISO su DX: con pellicole codificate la F100 legge automaticamente sensibilità da ISO 25 a 5000. In manuale puoi impostare ISO 6-6400 a passi di 1/3. È possibile anche sovrascrivere manualmente la sensibilità di un rullo DX per ottenere una variazione intenzionale dell’esposizione.",
            "Imposta ISO su DX se usi un rullo DX. Apri il dorso, inserisci il rullo dall’alto e tira la coda della pellicola fino all’indice rosso senza superarlo. Chiudi il dorso e premi una volta il pulsante di scatto: la F100 avanza automaticamente al fotogramma 1. Se lampeggiano Err ed E, riapri e ricarica la pellicola.",
            "Per avere tutte le funzioni usa AF Nikkor tipo D o G, inclusi gli AF-S/AF-I compatibili. Gli AF non D/G mantengono quasi tutte le funzioni ma non la misurazione Matrix 3D. Con ottiche non CPU la F100 lavora in A o M con misurazione ponderata centrale o Spot e il diaframma si imposta sulla ghiera dell’obiettivo. Gli IX-Nikkor non vanno montati.",
            "AF-S è adatto ai soggetti fermi: lo scatto è a priorità di fuoco e, una volta raggiunta la messa a fuoco, puoi bloccarla e ricomporre. AF-C è adatto ai soggetti in movimento: la fotocamera continua a inseguire il soggetto e lavora a priorità di scatto. Dynamic AF usa le cinque aree per mantenere il soggetto agganciato quando si sposta nel fotogramma.",
            "Matrix/3D Matrix è la scelta generale e usa un sensore a 10 segmenti; con ottiche D/G integra anche l’informazione di distanza. La ponderata centrale concentra gran parte della lettura nel cerchio centrale da 12 mm ed è utile quando vuoi controllare una zona precisa. Spot misura una zona di circa 4 mm, circa l’1% del fotogramma, e serve per misure molto selettive.",
            "P sceglie automaticamente tempo e diaframma e permette il Programma Flessibile. S ti fa scegliere il tempo da 30 s a 1/8000 s e la macchina determina il diaframma. A ti fa scegliere il diaframma e la macchina determina il tempo. M lascia a te tempo e diaframma ed è il modo da usare anche per la posa Bulb.",
            "Per riavvolgere a metà rullo premi contemporaneamente i due pulsanti di riavvolgimento per circa un secondo. Durante il riavvolgimento il contatore procede all’indietro; quando compare E lampeggiante puoi aprire il dorso. Se il riavvolgimento si ferma per batterie scariche, spegni, sostituisci le batterie, riaccendi e ripeti.",
            "La sincronizzazione X arriva fino a 1/250 s. Con lampeggiatori Nikon TTL compatibili sono disponibili TTL standard e, con combinazioni compatibili di flash e obiettivi, Multi-Sensor Balanced Fill-Flash e 3D Multi-Sensor Balanced Fill-Flash. Con misurazione Spot il sistema passa al TTL standard. Il campo ISO per TTL automatico è circa ISO 25-1000.",
            "Usa il reset a due pulsanti: tieni premuti contemporaneamente i due pulsanti indicati dal manuale per oltre 2 secondi. Tornano ai valori iniziali, fra le altre cose, area AF centrale, modo P, Programma Flessibile annullato, blocchi tempo/diaframma annullati, compensazione a zero, AE-L e bracketing annullati e flash sulla sincronizzazione normale alla prima tendina. Le impostazioni personalizzate hanno un reset separato."
    };

'''
s = s[:start] + new_block + s[end:]

# The Drive file ID is intentionally preserved: the old D100 PDF was replaced in place by the F100 Italian manual.
s = s.replace('NIKON_D100_URL', 'NIKON_F100_URL')
s = s.replace('Q_NIKON_D100', 'Q_NIKON_F100')
s = s.replace('A_NIKON_D100', 'A_NIKON_F100')
s = s.replace('NIKON D100', 'NIKON F100')
s = s.replace('Nikon D100 - Manuale IT', 'Nikon F100 - Manuale IT')
s = s.replace('Reflex digitale DX · 5 FAQ', 'Reflex 35 mm autofocus · 10 FAQ')

p.write_text(s, encoding='utf-8')
out = p.read_text(encoding='utf-8')

required = [
    'NIKON_F100_URL', 'Q_NIKON_F100', 'A_NIKON_F100',
    'NIKON F100', 'Nikon F100 - Manuale IT',
    'Reflex 35 mm autofocus · 10 FAQ',
    'quattro batterie AA da 1,5 V',
    'ISO 25 a 5000', 'ISO 6-6400',
    '1/8000 s', '1/250 s',
    'Multi-Sensor Balanced Fill-Flash',
    'addFaqMatches(hits,"NIKON F100",Q_NIKON_F100,A_NIKON_F100,q);'
]
for x in required:
    if x not in out:
        raise SystemExit('v0.4.4 guard missing: ' + x)

for forbidden in ['NIKON_D100_URL', 'Q_NIKON_D100', 'A_NIKON_D100', 'NIKON D100', 'Nikon D100 - Manuale IT']:
    if forbidden in out:
        raise SystemExit('v0.4.4 old D100 residue: ' + forbidden)

# Count exactly 10 F100 questions and answers.
def count(a,b):
    x=out.index('private static final String[] '+a)
    y=out.index('private static final String[] '+b,x)
    return out[x:y].count('            "')
if count('Q_NIKON_F100','A_NIKON_F100') != 10:
    raise SystemExit('v0.4.4 F100 question count != 10')
if count('A_NIKON_F100','Q_NIKON_ZOOM100') != 10:
    raise SystemExit('v0.4.4 F100 answer count != 10')

print('Darkroom v0.4.4 Nikon F100 manual + 10 Italian FAQs patch ready')
