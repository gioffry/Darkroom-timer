#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
maintenance = root / 'src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java'

if not maintenance.exists():
    raise SystemExit('v0.3.0 generated file missing: ' + str(maintenance))


def replace_once(path, old, new, label):
    s = path.read_text(encoding='utf-8')
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'v0.3.0 {label}: expected exactly 1 marker, found {n}')
    path.write_text(s.replace(old, new, 1), encoding='utf-8')
    print('v0.3.0 OK', label, flush=True)


guide_line = '    private static final String DARKROOM_GUIDE_URL = "https://drive.google.com/file/d/1_40jRUpA5Qxwr9a_n6PiT3V19SqZijQ2/view?usp=drivesdk";\n'
camera_urls = r'''    private static final String NIKON_L35AF_URL = "https://drive.google.com/file/d/1jIPGhIIwLcnDRN4D4Bb8AtLZMV6UsqPT/view?usp=drivesdk";
    private static final String NIKON_D100_URL = "https://drive.google.com/file/d/1-6_YrOo-hJwlLB4en3-vcBupuHxQm1l9/view?usp=drivesdk";
    private static final String NIKON_ZOOM100_URL = "https://drive.google.com/file/d/1hyDsxIw4Qic4peEWu-vRP95pfMh1BxWI/view?usp=drivesdk";
    private static final String ROLLEI_35_MX_URL = "https://drive.google.com/file/d/1vt9usyPAyd0N5Zd1LS-UTKvMZmBJVAmm/view?usp=drivesdk";
    private static final String ROLLEI_28_E2_URL = "https://drive.google.com/file/d/1aES38tuDIy9I8RQlGTJDVNAVyzf3SdiS/view?usp=drivesdk";
'''
replace_once(maintenance, guide_line, guide_line + camera_urls, 'camera manual Drive URLs')

faq_block = r'''    private static final String[] Q_NIKON_L35AF = {
            "Quali batterie usa la Nikon L35AF?",
            "Come si imposta la sensibilità della pellicola?",
            "Perché il flash si alza da solo?",
            "Come si fotografa un soggetto in controluce?",
            "Cosa faccio se l’autofocus mette a fuoco il punto sbagliato?"
    };
    private static final String[] A_NIKON_L35AF = {
            "Usa 2 batterie AA alcaline da 1,5 V. È consigliabile sostituirle entrambe insieme. Se il trascinamento della pellicola o la ricarica del flash diventano lenti, le batterie sono probabilmente scariche.",
            "La sensibilità non viene letta automaticamente: va impostata sulla ghiera ASA/ISO, da 50 a 1000 ISO, facendo coincidere il valore con l’indice bianco.",
            "Quando la luce è insufficiente, premendo il pulsante di scatto a metà il flash si solleva automaticamente. La macchina impedisce lo scatto finché il flash non è completamente carico.",
            "Tieni premuta la leva di compensazione del controluce durante lo scatto. La L35AF aumenta l’esposizione di circa +2 EV; se si solleva anche il flash, puoi utilizzarlo contemporaneamente.",
            "Centra nel riquadro AF un oggetto posto alla stessa distanza del soggetto, premi il pulsante a metà e mantienilo premuto. Ricomponi quindi l’immagine e scatta: è il blocco della messa a fuoco."
    };

    private static final String[] Q_NIKON_D100 = {
            "Qual è una buona configurazione di partenza per fotografare?",
            "Quali schede di memoria utilizza?",
            "Quando devo usare AF-S e quando AF-C?",
            "Meglio RAW o JPEG?",
            "Cosa faccio se vedo sempre le stesse macchie nelle fotografie?"
    };
    private static final String[] A_NIKON_D100 = {
            "Per un uso generale puoi partire da P, misurazione Matrix, AF-S, area AF singola e ISO 200. Da questa configurazione puoi poi modificare rapidamente tempo, diaframma o ISO in base alla scena.",
            "La D100 usa schede CompactFlash Type I e II e supporta anche i Microdrive. È preferibile formattare la scheda direttamente nella fotocamera e non rimuoverla mai mentre la spia di accesso è accesa.",
            "Usa AF-S per soggetti fermi: la messa a fuoco può essere bloccata premendo il pulsante a metà. Usa AF-C per soggetti in movimento, perché la fotocamera continua ad aggiornare la distanza.",
            "Il formato NEF/RAW a 12 bit conserva il maggior margine per la regolazione successiva di esposizione e colore. JPEG Fine è più pratico e occupa meno spazio, ma offre minore possibilità di correzione.",
            "Probabilmente c’è polvere sul filtro davanti al sensore CCD. Prova prima con un soffietto manuale, senza toccare il sensore e senza usare bombolette di aria compressa; per sporco persistente è preferibile una pulizia professionale."
    };

    private static final String[] Q_NIKON_ZOOM100 = {
            "Quale batteria usa la Nikon Zoom 100 AF?",
            "Devo impostare manualmente gli ISO della pellicola?",
            "Come uso correttamente lo zoom?",
            "Come metto a fuoco un soggetto che non si trova al centro?",
            "Cosa devo fare alla fine del rullo?"
    };
    private static final String[] A_NIKON_ZOOM100 = {
            "Utilizza una batteria al litio CR123A. La stessa batteria alimenta autofocus, zoom, flash e trascinamento della pellicola, quindi più funzioni che diventano lente contemporaneamente indicano spesso una batteria debole.",
            "Normalmente no: la macchina legge automaticamente la codifica DX del rullo. Per un funzionamento prevedibile è quindi preferibile utilizzare pellicole con codifica DX.",
            "Il comando W porta verso il grandangolo 35 mm, mentre T porta verso il tele 70 mm. Non trattenere né spingere mai manualmente il barilotto mentre lo zoom motorizzato si muove.",
            "Centra temporaneamente il soggetto nell’area AF, premi il pulsante di scatto a metà, mantienilo premuto e ricomponi. Premi poi completamente per scattare.",
            "La macchina normalmente riavvolge automaticamente la pellicola. Non aprire il dorso finché il motore non si è fermato e il riavvolgimento non è terminato; se si interrompe per batteria scarica, sostituisci la batteria prima di aprire."
    };

    private static final String[] Q_ROLLEI_35_MX = {
            "Devo allineare le frecce della pellicola 120 quando la carico?",
            "Perché il contafotogrammi non arriva alla posa 1?",
            "Come funziona la manovella dopo ogni fotografia?",
            "Perché bisogna fare attenzione al tempo di 1/500 s?",
            "Quale posizione devo usare con un flash elettronico moderno?"
    };
    private static final String[] A_ROLLEI_35_MX = {
            "No. Il sistema Automat rileva automaticamente l’inizio della pellicola attraverso lo spessore del materiale e porta il contatore alla posa 1, purché la carta sia passata correttamente tra i rulli sensori.",
            "La causa più comune è un caricamento errato: la carta protettiva non è passata correttamente nel sistema Automat. Non continuare a girare con forza la manovella: apri e controlla il percorso della pellicola.",
            "La manovella fa avanzare la pellicola e arma l’otturatore. Completa sempre il movimento fino all’arresto e riportala nella posizione prevista, senza forzarla.",
            "Sugli otturatori Compur/Synchro-Compur d’epoca il 1/500 s può richiedere uno sforzo maggiore. Se il comando è molto duro non insistere: forzarlo può danneggiare il meccanismo e può essere necessario un intervento di revisione.",
            "Usa la sincronizzazione X. La posizione M è destinata alle vecchie lampadine flash, che richiedevano un anticipo prima del lampo."
    };

    private static final String[] Q_ROLLEI_28_E2 = {
            "Come riconosco una Rolleiflex 2.8 E2?",
            "Posso fidarmi dell’esposimetro al selenio?",
            "Posso usare tranquillamente il tempo di 1/500 s?",
            "Quali filtri e paraluce devo acquistare?",
            "Quale sincronizzazione devo usare con un flash elettronico?"
    };
    private static final String[] A_ROLLEI_28_E2 = {
            "La E2 è il modello K7E2, prodotto nel 1959-1960; i numeri di serie documentati sono circa 2.350.000–2.356.999. Una caratteristica importante della generazione E2 è il pozzetto/schermo removibile.",
            "Prima va confrontato con un esposimetro moderno. Il selenio non richiede batterie, ma dopo oltre sessant’anni può aver perso sensibilità: se le letture sono irregolari è meglio usare un esposimetro esterno.",
            "Sì, ma solo se il comando funziona normalmente. Se il 1/500 s è duro, non forzarlo: è uno dei punti in cui un vecchio Synchro-Compur può manifestare la necessità di una revisione.",
            "La Rolleiflex 2.8 E2 utilizza accessori con baionetta Rollei Bay III. Non va confusa con la Rolleiflex 3.5, che normalmente utilizza Bay I.",
            "Imposta il selettore su X. La posizione M serviva alle vecchie lampadine flash; anche l’autoscatto va trattato con cautela e non va forzato se il meccanismo appare duro o esitante."
    };

'''
replace_once(
    maintenance,
    '    private static final String[] Q_OPEMUS = {\n',
    faq_block + '    private static final String[] Q_OPEMUS = {\n',
    'camera FAQ arrays'
)

replace_once(
    maintenance,
    '        begin("MANUALI","Tocca un apparecchio. Ogni pagina contiene 10 FAQ brevi e il collegamento alla fonte completa quando disponibile.");\n',
    '        begin("MANUALI","Tocca un apparecchio. Ogni pagina contiene FAQ operative e il collegamento al manuale completo quando disponibile.");\n',
    'manuals intro'
)

minolta_card = '        body.addView(navCard("MINOLTA AUTO METER IIIF","Viewfinder 10° · manuale completo non disponibile",()->navigate(this::renderMinolta)));\n'
camera_cards = r'''        body.addView(title("FOTOCAMERE",16));
        body.addView(navCard("NIKON L35AF","Compatta 35 mm autofocus · 5 FAQ",()->navigate(()->renderFaqPage("NIKON L35AF","Fonte: Nikon L35AF - Manuale IT",Q_NIKON_L35AF,A_NIKON_L35AF,NIKON_L35AF_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("NIKON D100","Reflex digitale DX · 5 FAQ",()->navigate(()->renderFaqPage("NIKON D100","Fonte: Nikon D100 - Manuale IT",Q_NIKON_D100,A_NIKON_D100,NIKON_D100_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("NIKON ZOOM 100 AF","Zoom Touch 470 · 35 mm · 5 FAQ",()->navigate(()->renderFaqPage("NIKON ZOOM 100 AF","Fonte: Nikon Zoom 100 AF - Manuale IT",Q_NIKON_ZOOM100,A_NIKON_ZOOM100,NIKON_ZOOM100_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("ROLLEIFLEX 3.5 AUTOMAT MX","TLR 6×6 · Tessar/Xenar 75 mm · 5 FAQ",()->navigate(()->renderFaqPage("ROLLEIFLEX 3.5 AUTOMAT MX","Fonte: Rolleiflex 3.5 Automat MX - Manuale IT",Q_ROLLEI_35_MX,A_ROLLEI_35_MX,ROLLEI_35_MX_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("ROLLEIFLEX 2.8 E2","TLR 6×6 · Planar/Xenotar 80 mm · 5 FAQ",()->navigate(()->renderFaqPage("ROLLEIFLEX 2.8 E2","Fonte: Rolleiflex 2.8 E2 - Manuale IT",Q_ROLLEI_28_E2,A_ROLLEI_28_E2,ROLLEI_28_E2_URL,"APRI MANUALE COMPLETO"))));
'''
replace_once(maintenance, minolta_card, minolta_card + camera_cards, 'camera manual cards')

old_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=10||answers.length!=10) throw new IllegalStateException("FAQ count must be 10 for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
new_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||(questions.length!=5&&questions.length!=10)) throw new IllegalStateException("FAQ count must be 5 or 10 for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
replace_once(maintenance, old_helper, new_helper, 'FAQ helper 5 or 10')

ms = maintenance.read_text(encoding='utf-8')
for marker in [
    'NIKON_L35AF_URL', 'NIKON_D100_URL', 'NIKON_ZOOM100_URL',
    'ROLLEI_35_MX_URL', 'ROLLEI_28_E2_URL',
    'Q_NIKON_L35AF', 'A_NIKON_L35AF',
    'Q_NIKON_D100', 'A_NIKON_D100',
    'Q_NIKON_ZOOM100', 'A_NIKON_ZOOM100',
    'Q_ROLLEI_35_MX', 'A_ROLLEI_35_MX',
    'Q_ROLLEI_28_E2', 'A_ROLLEI_28_E2',
    'NIKON L35AF', 'NIKON D100', 'NIKON ZOOM 100 AF',
    'ROLLEIFLEX 3.5 AUTOMAT MX', 'ROLLEIFLEX 2.8 E2',
    'FAQ count must be 5 or 10 for '
]:
    if marker not in ms:
        raise SystemExit('v0.3.0 maintenance guard failed: ' + marker)

for url_id in [
    '1jIPGhIIwLcnDRN4D4Bb8AtLZMV6UsqPT',
    '1-6_YrOo-hJwlLB4en3-vcBupuHxQm1l9',
    '1hyDsxIw4Qic4peEWu-vRP95pfMh1BxWI',
    '1vt9usyPAyd0N5Zd1LS-UTKvMZmBJVAmm',
    '1aES38tuDIy9I8RQlGTJDVNAVyzf3SdiS'
]:
    if url_id not in ms:
        raise SystemExit('v0.3.0 Drive URL guard failed: ' + url_id)

print('Darkroom v0.3.0 camera manuals + 25 FAQ patch ready')
