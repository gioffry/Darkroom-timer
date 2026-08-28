#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.3: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

# Add imports for global FAQ search UI and lists.
imp_old = 'import android.widget.TextView;\nimport android.widget.Toast;\n\nimport java.util.ArrayDeque;\n'
imp_new = 'import android.widget.TextView;\nimport android.widget.Toast;\nimport android.widget.EditText;\nimport android.text.Editable;\nimport android.text.TextWatcher;\n\nimport java.util.ArrayDeque;\nimport java.util.ArrayList;\nimport java.util.List;\n'
if imp_old not in s:
    raise SystemExit('v0.4.3: import marker missing')
s = s.replace(imp_old, imp_new, 1)

# Rolleiflex 3.5 accessories: preserve the user-provided operational content, reorganized by accessory.
rollei_block = r'''    private static final String[] Q_R35_GENERAL = {
            "Quali accessori sono presenti nel corredo Rolleiflex 3.5?",
            "Su quale obiettivo della Rolleiflex si monta il filtro?",
            "Posso usare contemporaneamente filtro e paraluce?",
            "Se esco con la Rolleiflex 3.5, quale filtro scelgo?",
            "Posso usare i filtri con qualsiasi pellicola B/N?",
            "Come misuro l’esposizione usando un filtro?",
            "Posso misurare la luce attraverso il filtro?",
            "Quali compensazioni posso usare come punto di partenza?",
            "Quali accessori userei davvero più spesso?",
            "Qual è la regola più importante da ricordare?"
    };
    private static final String[] A_R35_GENERAL = {
            "Nel corredo fotografato sono riconoscibili Rolleifilter Sport (giallo molto chiaro), Rollei Gelb Mittel (giallo medio), Rollei Hellgrün (verde chiaro), Rollei Hellrot (rosso chiaro), Rollei Hellblau (azzurro chiaro), paraluce Rolleiflex, Rolleinar 1, Rolleinar 2, Rolleiparkeil 1 e Rolleiparkeil 2. I primi cinque sono filtri fotografici; Rolleinar e Rolleiparkeil servono alla fotografia ravvicinata.",
            "La Rolleiflex ha due obiettivi: quello superiore serve per inquadrare e mettere a fuoco, quello inferiore impressiona la pellicola. Il filtro va normalmente montato solo sull’obiettivo inferiore di ripresa; non serve un secondo filtro sull’obiettivo superiore.",
            "Sì. L’ordine normale è obiettivo → filtro → paraluce. Il filtro usa la baionetta interna e il paraluce originale quella esterna, perciò possono essere usati insieme. Il paraluce è particolarmente utile con vecchi filtri perché riduce luce laterale, flare e perdita di contrasto.",
            "Nessun filtro per la resa naturale; Sport per una correzione molto leggera; Gelb Mittel per il classico B/N da paesaggio ed è il più versatile; Hellgrün se prevalgono vegetazione e fogliame; Hellrot per cieli e nuvole molto drammatici; Hellblau per effetti particolari o per scurire soggetti rossi.",
            "Sì, con una normale pellicola pancromatica. Effetto e compensazione cambiano però leggermente secondo pellicola e illuminazione. I fattori Rollei sono valori medi: dopo alcuni rulli conviene costruire una piccola tabella personale.",
            "Con esposimetro esterno: misura la scena senza filtro, scegli tempo e diaframma, applica la compensazione del filtro, monta il filtro e scatta. Esempio: 1/125 s a f/8; con Hellgrün +1 stop → circa 1/60 s a f/8.",
            "È possibile mettere il filtro davanti alla cellula di un esposimetro separato, ma con questi vecchi filtri è in genere più semplice e ripetibile misurare senza filtro e applicare manualmente la compensazione prevista.",
            "Punti di partenza: Sport circa +1/2 / +2/3 stop; Gelb Mittel circa +1,5 stop; Hellgrün circa +1 stop; Hellrot circa +2–3,5 stop, partendo da +3; Hellblau circa +1/2 stop; Rolleinar 1 nessuna compensazione; Rolleinar 2 nessuna compensazione.",
            "In ordine pratico: Gelb Mittel; paraluce; Hellgrün; Rolleinar 1; Rolleinar 2; Hellrot; Sport; Hellblau. È un ordine d’uso indicativo, non una graduatoria di qualità.",
            "Per i filtri B/N: il filtro tende a schiarire il proprio colore e a scurire il complementare. Per i Rolleinar: stesso numero sopra e sotto, Rolleiparkeil corrispondente e puntino rosso in alto. Per tutti gli accessori: vetro pulito e paraluce quando possibile."
    };

    private static final String[] Q_R35_SPORT = {
            "Che cos’è il Rolleifilter Sport e quando si usa?"
    };
    private static final String[] A_R35_SPORT = {
            "È un giallo molto chiaro, più debole del Gelb Mittel, concepito come filtro generale all’aperto. Produce una correzione delicata: cielo azzurro leggermente più scuro, nuvole un po’ più leggibili, foschia leggermente ridotta, gialli appena più chiari e resa naturale. È indicato per viaggio, paesaggio senza effetto evidente, fotografia urbana e uso quotidiano B/N. Compensazione indicativa circa +1/2 stop, eventualmente fino a circa +2/3 stop."
    };

    private static final String[] Q_R35_YELLOW = {
            "A cosa serve il Gelb Mittel?",
            "Quando userei concretamente il Gelb Mittel?",
            "Quanto devo aumentare l’esposizione con il Gelb Mittel?"
    };
    private static final String[] A_R35_YELLOW = {
            "È il filtro B/N più versatile del corredo: schiarisce gialli e tonalità vicine, scurisce il blu, rende il cielo più scuro e aumenta la separazione fra cielo e nuvole. Il principio guida è che un filtro tende a schiarire i colori simili al proprio e a scurire i complementari.",
            "È ottimo per paesaggi, nuvole, montagne, architettura, fotografia urbana, scene con cielo, neve e fotografia generale B/N. È il primo filtro da imparare a usare perché l’effetto è evidente ma normalmente naturale.",
            "Il riferimento Rollei è circa +1,5 stop, equivalente a un fattore di circa 3×. Esempio: da 1/125 s a f/8 puoi portarti approssimativamente verso 1/45–1/60 s a f/8 oppure aprire il diaframma. La risposta reale dipende anche dalla pellicola."
    };

    private static final String[] Q_R35_GREEN = {
            "Che effetto produce il filtro Hellgrün?",
            "Quando conviene usare il Hellgrün invece del giallo?",
            "Va bene per i ritratti?",
            "Quanto devo compensare il Hellgrün?"
    };
    private static final String[] A_R35_GREEN = {
            "Il verde chiaro schiarisce la vegetazione, differenzia meglio varie tonalità di foglie e scurisce leggermente blu e rosso. Può migliorare la separazione tonale nei paesaggi.",
            "Quando la parte importante dell’immagine è la vegetazione: boschi, prati, alberi, vigneti, paesaggi agricoli e foglie illuminate. Il verde aiuta a separare verdi che altrimenti potrebbero diventare molto simili in B/N.",
            "Va usato con attenzione: tende a scurire componenti rossastre e quindi può rendere più evidenti lentiggini, rossori, imperfezioni cutanee e labbra. Non è in genere la prima scelta per un ritratto classico morbido.",
            "Punto di partenza circa +1 stop, cioè circa 2× il tempo. Esempio: 1/125 s a f/8 → circa 1/60 s a f/8."
    };

    private static final String[] Q_R35_RED = {
            "A cosa serve il filtro Hellrot?",
            "Che tipo di immagini produce?",
            "Quando è particolarmente utile?",
            "Quanto devo compensare con il Hellrot?"
    };
    private static final String[] A_R35_RED = {
            "È il filtro più aggressivo del gruppo: lascia passare molto rosso e blocca gran parte del blu, scurisce fortemente il cielo azzurro, schiarisce soggetti rossi, aumenta molto la separazione fra nuvole e cielo e riduce l’effetto della foschia atmosferica.",
            "Può produrre un aspetto decisamente drammatico: cielo quasi nero, nuvole molto luminose, paesaggi grafici, forte separazione dei toni e atmosfera quasi surreale. Non è un filtro da lasciare sempre montato.",
            "È particolarmente utile con cielo azzurro e grandi nuvole bianche, montagne, paesaggi lontani, architettura drammatica e immagini grafiche B/N. Nei ritratti le tonalità rosse della pelle vengono schiarite e la resa può diventare poco naturale.",
            "La compensazione varia molto con la risposta spettrale della pellicola. Le tabelle Rollei indicano grossomodo +2 fino a +3,5 stop. Come prima prova con una pellicola pancromatica moderna: partire da circa +3 stop. Esempio: 1/125 s a f/8 → circa 1/15 s a f/8."
    };

    private static final String[] Q_R35_BLUE = {
            "A cosa serve il filtro Hellblau?",
            "Quando potrei usarlo oggi?",
            "Quanto devo compensare il Hellblau?"
    };
    private static final String[] A_R35_BLUE = {
            "Produce sostanzialmente l’effetto opposto a giallo e rosso: schiarisce il blu, scurisce il rosso, può rendere la pelle più scura, aumenta la visibilità di rossori e imperfezioni e rende il cielo più chiaro. Storicamente era previsto soprattutto con emulsioni molto sensibili al rosso e in luce artificiale.",
            "Oggi soprattutto per sperimentazione: ritratti volutamente duri, studi tonali, soggetti rossi da rendere più scuri, effetti particolari e alcune riproduzioni. Per il normale paesaggio con cielo e nuvole è di solito l’opposto della scelta desiderabile.",
            "Punto di partenza circa +1/2 stop, fattore approssimativo 1,5×."
    };

    private static final String[] Q_R35_R1 = {
            "Rolleinar 1 è un filtro?",
            "Da quanti pezzi è composto il Rolleinar 1 della Rolleiflex 3.5?",
            "Come si monta il Rolleinar 1?",
            "Qual è la sua distanza di lavoro indicativa?",
            "Devo compensare l’esposizione usando Rolleinar 1?",
            "Come metto a fuoco con Rolleinar 1?",
            "Perché serve il Rolleiparkeil 1?",
            "Posso usare insieme Rolleinar 1 e filtro colorato?"
    };
    private static final String[] A_R35_R1 = {
            "No. È una lente addizionale per fotografia ravvicinata, che permette di mettere a fuoco più vicino del normale.",
            "Il set fotografato è del tipo a tre pezzi: Rolleinar 1 per l’obiettivo inferiore, Rolleinar 1 per l’obiettivo superiore e Rolleiparkeil 1 per correggere la parallasse. Non va mischiato con componenti del set 2.",
            "Obiettivo inferiore di ripresa: Rolleinar 1. Obiettivo superiore di mira: Rolleinar 1 → Rolleiparkeil 1. Il Rolleiparkeil è un prisma e deve avere il puntino rosso in alto.",
            "Indicativamente circa da 1 metro a 45 cm; la distanza esatta varia leggermente con la focale e il modello.",
            "No. Le istruzioni Rollei indicano che Rolleinar non richiede aumento dell’esposizione: tempo e diaframma restano quelli misurati.",
            "Monta correttamente gli elementi, apri il pozzetto, metti a fuoco sul vetro smerigliato e usa la lente d’ingrandimento del pozzetto per la precisione finale. A distanza ravvicinata la profondità di campo è ridotta: quando possibile lavora attorno a f/8–f/11 o più chiuso.",
            "Perché la Rolleiflex è una TLR: a distanza ravvicinata l’obiettivo di mira e quello di ripresa vedono inquadrature sensibilmente diverse. Il Rolleiparkeil sposta l’immagine del mirino per compensare l’errore di parallasse.",
            "Sì. Sull’obiettivo di ripresa: obiettivo → Rolleinar → filtro → eventualmente paraluce. Rolleinar non richiede compensazione, il filtro colorato sì: compensi solo il filtro."
    };

    private static final String[] Q_R35_R2 = {
            "Rolleinar 2 è un filtro?",
            "Da quanti pezzi è composto il Rolleinar 2 della Rolleiflex 3.5?",
            "Come si monta il Rolleinar 2?",
            "Qual è la sua distanza di lavoro indicativa?",
            "Devo compensare l’esposizione usando Rolleinar 2?",
            "Come metto a fuoco con Rolleinar 2?",
            "Perché serve il Rolleiparkeil 2?",
            "Posso usare insieme Rolleinar 2 e filtro colorato?"
    };
    private static final String[] A_R35_R2 = {
            "No. È una lente addizionale più potente del Rolleinar 1, destinata alla fotografia ravvicinata.",
            "Il set fotografato è del tipo a tre pezzi: Rolleinar 2 inferiore, Rolleinar 2 superiore e Rolleiparkeil 2. Rolleiparkeil 2 va con Rolleinar 2 e non va mischiato con il set 1.",
            "Obiettivo inferiore di ripresa: Rolleinar 2. Obiettivo superiore di mira: Rolleinar 2 → Rolleiparkeil 2. Anche qui il puntino rosso del Rolleiparkeil deve stare in alto.",
            "Indicativamente circa da 50 a 31 cm; la distanza esatta varia leggermente con la focale e il modello.",
            "No. Le Rolleinar non richiedono aumento dell’esposizione: tempo e diaframma restano quelli misurati.",
            "Metti a fuoco normalmente sul vetro smerigliato, usando la lente d’ingrandimento del pozzetto per la precisione finale. La profondità di campo è ancora più ridotta rispetto al Rolleinar 1, quindi conviene chiudere il diaframma quando luce e tempi lo consentono.",
            "Serve a compensare la parallasse fra obiettivo di mira e obiettivo di ripresa, che a 30–50 cm diventa molto importante.",
            "Sì. Sull’obiettivo di ripresa: obiettivo → Rolleinar → filtro → eventualmente paraluce. La compensazione esposimetrica riguarda soltanto il filtro colorato."
    };

    private static final String[] Q_R28_GENERAL = {
            "Quali accessori sono presenti nel corredo Rolleiflex 2.8?",
            "Questo Rolleinar 1 è uguale a quello della Rolleiflex 3.5?",
            "Come riconosco i due elementi del Rolleinar 1 della 2.8?"
    };
    private static final String[] A_R28_GENERAL = {
            "Nel corredo fotografato della Rolleiflex 2.8 sono presenti il paraluce Rollei e un Rolleinar 1 completo a due elementi. Non sono stati fotografati altri filtri colorati o un Rolleinar 2 per questa macchina.",
            "No. Quello della Rolleiflex 2.8 fotografato è il tipo a due elementi: non usa un Rolleiparkeil separato. La correzione di parallasse è incorporata nell’elemento superiore Heidosmat-Rolleinar 1.",
            "L’elemento più sottile marcato Rolleinar 1 va sull’obiettivo inferiore di ripresa. L’elemento più spesso marcato Heidosmat-Rolleinar 1 va sull’obiettivo superiore di mira e incorpora il prisma di correzione della parallasse."
    };

    private static final String[] Q_R28_HOOD = {
            "Come uso il paraluce Rollei sulla Rolleiflex 2.8?"
    };
    private static final String[] A_R28_HOOD = {
            "Montalo sulla baionetta esterna dell’obiettivo di ripresa quando la configurazione degli accessori lo consente. Riduce luce laterale e flare ed è particolarmente utile all’aperto. Mantienilo pulito e controlla che sia ben bloccato prima di scattare."
    };

    private static final String[] Q_R28_R1 = {
            "Come si monta il Rolleinar 1 a due elementi sulla Rolleiflex 2.8?",
            "Come va orientato l’Heidosmat-Rolleinar 1?",
            "Qual è la distanza di lavoro indicativa?",
            "Devo compensare l’esposizione?",
            "Come metto a fuoco e cosa devo ricordare sulla profondità di campo?"
    };
    private static final String[] A_R28_R1 = {
            "Sull’obiettivo inferiore di ripresa monta l’elemento Rolleinar 1 sottile. Sull’obiettivo superiore di mira monta l’Heidosmat-Rolleinar 1 più spesso, che integra la correzione della parallasse.",
            "Il puntino rosso dell’Heidosmat-Rolleinar deve stare in alto. L’orientamento è importante perché il prisma incorporato deve spostare l’inquadratura nella direzione corretta.",
            "Per la Rolleiflex 2.8 con obiettivo da 80 mm, il campo indicativo del Rolleinar 1 è circa da 1 metro a 47 cm.",
            "No. Il Rolleinar 1 non richiede compensazione dell’esposizione: usa la lettura normale dell’esposimetro.",
            "Metti a fuoco normalmente sul vetro smerigliato e usa la lente del pozzetto per la precisione finale. A queste distanze la profondità di campo è ridotta: quando possibile chiudi il diaframma, per esempio attorno a f/8–f/11 o oltre se luce e tempi lo consentono."
    };

'''
marker = '    private static final String[] Q_PROCESS_WASH = {\n'
if marker not in s:
    raise SystemExit('v0.4.3: process insertion marker missing')
s = s.replace(marker, rollei_block + marker, 1)

# Add nested Rolleiflex menus under TECNICA.
tech_marker = '        body.addView(navCard("PROCESSO E LAVAGGIO","Provino a contatto · pre-bagno · lavaggio film e carta RC",()->navigate(()->renderFaqPage("PROCESSO E LAVAGGIO","Fonti operative: ILFORD PHOTO + manuali JOBO",Q_PROCESS_WASH,A_PROCESS_WASH,null,null))));\n'
if tech_marker not in s:
    raise SystemExit('v0.4.3: technique insertion marker missing')
s = s.replace(tech_marker, tech_marker + '        body.addView(navCard("FILTRI E ACCESSORI ROLLEIFLEX","Corredi separati Rolleiflex 3.5 e 2.8",()->navigate(this::renderRolleiAccessories)));\n', 1)

# Insert menu rendering methods before renderMaintenance.
method_marker = '    private void renderMaintenance(){\n'
if method_marker not in s:
    raise SystemExit('v0.4.3: renderMaintenance marker missing')
methods = r'''    private void renderRolleiAccessories(){
        begin("FILTRI E ACCESSORI ROLLEIFLEX","Scegli la macchina: i due corredi restano separati.");
        body.addView(navCard("ROLLEIFLEX 3.5","Filtri 28,5 mm · paraluce · Rolleinar 1 e 2",()->navigate(this::renderRollei35Accessories)));
        body.addView(navCard("ROLLEIFLEX 2.8","Paraluce · Rolleinar 1 a due elementi",()->navigate(this::renderRollei28Accessories)));
    }
    private void renderRollei35Accessories(){
        begin("ROLLEIFLEX 3.5 — ACCESSORI","Corredo fotografato: filtri e lenti ravvicinate 28,5 mm.");
        body.addView(navCard("GENERALE","Corredo · montaggio · esposizione · scelta rapida",()->navigate(()->renderFaqPage("ROLLEIFLEX 3.5 — GENERALE","Corredo personale fotografato + indicazioni operative",Q_R35_GENERAL,A_R35_GENERAL,null,null))));
        body.addView(navCard("ROLLEIFILTER SPORT","Giallo molto chiaro",()->navigate(()->renderFaqPage("ROLLEIFILTER SPORT","Accessorio Rolleiflex 3.5",Q_R35_SPORT,A_R35_SPORT,null,null))));
        body.addView(navCard("GELB MITTEL","Giallo medio",()->navigate(()->renderFaqPage("ROLLEI GELB MITTEL","Accessorio Rolleiflex 3.5",Q_R35_YELLOW,A_R35_YELLOW,null,null))));
        body.addView(navCard("HELLGRÜN","Verde chiaro",()->navigate(()->renderFaqPage("ROLLEI HELLGRÜN","Accessorio Rolleiflex 3.5",Q_R35_GREEN,A_R35_GREEN,null,null))));
        body.addView(navCard("HELLROT","Rosso chiaro",()->navigate(()->renderFaqPage("ROLLEI HELLROT","Accessorio Rolleiflex 3.5",Q_R35_RED,A_R35_RED,null,null))));
        body.addView(navCard("HELLBLAU","Azzurro chiaro",()->navigate(()->renderFaqPage("ROLLEI HELLBLAU","Accessorio Rolleiflex 3.5",Q_R35_BLUE,A_R35_BLUE,null,null))));
        body.addView(navCard("ROLLEINAR 1","Ravvicinata · Rolleiparkeil 1",()->navigate(()->renderFaqPage("ROLLEINAR 1 — ROLLEIFLEX 3.5","Set a tre pezzi",Q_R35_R1,A_R35_R1,null,null))));
        body.addView(navCard("ROLLEINAR 2","Ravvicinata · Rolleiparkeil 2",()->navigate(()->renderFaqPage("ROLLEINAR 2 — ROLLEIFLEX 3.5","Set a tre pezzi",Q_R35_R2,A_R35_R2,null,null))));
    }
    private void renderRollei28Accessories(){
        begin("ROLLEIFLEX 2.8 — ACCESSORI","Corredo fotografato: paraluce e Rolleinar 1 a due elementi.");
        body.addView(navCard("GENERALE","Cosa c’è nel corredo e differenze dalla 3.5",()->navigate(()->renderFaqPage("ROLLEIFLEX 2.8 — GENERALE","Corredo personale fotografato",Q_R28_GENERAL,A_R28_GENERAL,null,null))));
        body.addView(navCard("PARALUCE","Uso pratico",()->navigate(()->renderFaqPage("PARALUCE — ROLLEIFLEX 2.8","Accessorio del corredo personale",Q_R28_HOOD,A_R28_HOOD,null,null))));
        body.addView(navCard("ROLLEINAR 1","Due elementi · parallasse integrata",()->navigate(()->renderFaqPage("ROLLEINAR 1 — ROLLEIFLEX 2.8","Rolleinar 1 + Heidosmat-Rolleinar 1",Q_R28_R1,A_R28_R1,null,null))));
    }

'''
s = s.replace(method_marker, methods + method_marker, 1)

# Add global FAQ search box to the Uso e Manutenzione home.
root_old = '        begin("USO E MANUTENZIONE","Manuali, tecnica di camera oscura, manutenzione verificata e ricettario.");\n        body.addView(navCard("APP DARKROOM","Guida completa v0.2.8 e 10 FAQ operative",()->navigate(this::renderAppGuide)));\n'
root_new = '        begin("USO E MANUTENZIONE","Manuali, tecnica di camera oscura, manutenzione verificata e ricettario.");\n        addFaqSearch();\n        body.addView(navCard("APP DARKROOM","Guida completa v0.2.8 e 10 FAQ operative",()->navigate(this::renderAppGuide)));\n'
if root_old not in s:
    raise SystemExit('v0.4.3: root search marker missing')
s = s.replace(root_old, root_new, 1)

# Add search methods before begin(). Search question + answer across all FAQ arrays; tapping opens the exact answer.
begin_marker = '    private void begin(String heading,String subheading){\n'
if begin_marker not in s:
    raise SystemExit('v0.4.3: begin marker missing')
search_methods = r'''    private static final class FaqHit {
        final String section, question, answer;
        FaqHit(String section,String question,String answer){ this.section=section; this.question=question; this.answer=answer; }
    }
    private void addFaqSearch(){
        EditText search=new EditText(this);
        search.setHint("Cerca nelle FAQ…");
        search.setTextColor(WARM); search.setHintTextColor(MUTED); search.setTextSize(16f);
        search.setSingleLine(true); search.setPadding(dp(14),0,dp(14),0);
        GradientDrawable bg=new GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(12)); bg.setStroke(dp(1),BRONZE); search.setBackground(bg);
        body.addView(search,margin(-1,dp(50),0,0,0,dp(8)));
        LinearLayout results=new LinearLayout(this); results.setOrientation(LinearLayout.VERTICAL); body.addView(results);
        search.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence x,int start,int count,int after){}
            public void onTextChanged(CharSequence x,int start,int before,int count){ renderFaqSearchResults(results,x==null?"":x.toString()); }
            public void afterTextChanged(Editable e){}
        });
    }
    private void renderFaqSearchResults(LinearLayout target,String raw){
        target.removeAllViews(); String q=raw.trim().toLowerCase(); if(q.length()<2) return;
        List<FaqHit> hits=new ArrayList<>();
        addFaqMatches(hits,"MEOPTA OPEMUS 6",Q_OPEMUS,A_OPEMUS,q); addFaqMatches(hits,"MEOPTA COLOR 3",Q_COLOR3,A_COLOR3,q); addFaqMatches(hits,"JOBO CPE2",Q_JOBO,A_JOBO,q); addFaqMatches(hits,"THERMAPHOT ACP200",Q_ACP,A_ACP,q); addFaqMatches(hits,"MINOLTA AUTO METER IIIF",Q_MINOLTA,A_MINOLTA,q);
        addFaqMatches(hits,"NIKON L35AF2",Q_NIKON_L35AF,A_NIKON_L35AF,q); addFaqMatches(hits,"NIKON D100",Q_NIKON_D100,A_NIKON_D100,q); addFaqMatches(hits,"NIKON ZOOM 100 AF",Q_NIKON_ZOOM100,A_NIKON_ZOOM100,q); addFaqMatches(hits,"ROLLEIFLEX 3.5 AUTOMAT MX",Q_ROLLEI_35_MX,A_ROLLEI_35_MX,q); addFaqMatches(hits,"ROLLEIFLEX 2.8 E2",Q_ROLLEI_28_E2,A_ROLLEI_28_E2,q);
        addFaqMatches(hits,"PROCESSO E LAVAGGIO",Q_PROCESS_WASH,A_PROCESS_WASH,q); addFaqMatches(hits,"PROVINI E CONTRASTO",Q_TESTSTRIP,A_TESTSTRIP,q); addFaqMatches(hits,"SPLIT GRADE",Q_SPLIT,A_SPLIT,q); addFaqMatches(hits,"SISTEMA ZONALE",Q_ZONE,A_ZONE,q); addFaqMatches(hits,"STAMPA B/N",Q_PRINT,A_PRINT,q);
        addFaqMatches(hits,"ROLLEIFLEX 3.5 — GENERALE",Q_R35_GENERAL,A_R35_GENERAL,q); addFaqMatches(hits,"ROLLEIFILTER SPORT",Q_R35_SPORT,A_R35_SPORT,q); addFaqMatches(hits,"ROLLEI GELB MITTEL",Q_R35_YELLOW,A_R35_YELLOW,q); addFaqMatches(hits,"ROLLEI HELLGRÜN",Q_R35_GREEN,A_R35_GREEN,q); addFaqMatches(hits,"ROLLEI HELLROT",Q_R35_RED,A_R35_RED,q); addFaqMatches(hits,"ROLLEI HELLBLAU",Q_R35_BLUE,A_R35_BLUE,q); addFaqMatches(hits,"ROLLEINAR 1 — ROLLEIFLEX 3.5",Q_R35_R1,A_R35_R1,q); addFaqMatches(hits,"ROLLEINAR 2 — ROLLEIFLEX 3.5",Q_R35_R2,A_R35_R2,q);
        addFaqMatches(hits,"ROLLEIFLEX 2.8 — GENERALE",Q_R28_GENERAL,A_R28_GENERAL,q); addFaqMatches(hits,"PARALUCE — ROLLEIFLEX 2.8",Q_R28_HOOD,A_R28_HOOD,q); addFaqMatches(hits,"ROLLEINAR 1 — ROLLEIFLEX 2.8",Q_R28_R1,A_R28_R1,q);
        if(hits.isEmpty()){ target.addView(subtitle("Nessun risultato nelle FAQ."),margin(-1,-2,0,dp(2),0,dp(8))); return; }
        int limit=Math.min(40,hits.size());
        for(int i=0;i<limit;i++){ final FaqHit h=hits.get(i); LinearLayout c=navCard(h.question,h.section,()->navigate(()->renderSingleFaq(h))); target.addView(c); }
        if(hits.size()>limit) target.addView(subtitle("Mostrati i primi 40 risultati."),margin(-1,-2,0,0,0,dp(8)));
    }
    private void addFaqMatches(List<FaqHit> out,String section,String[] qs,String[] as,String needle){
        if(qs==null||as==null) return; int n=Math.min(qs.length,as.length);
        for(int i=0;i<n;i++){ String qq=qs[i]==null?"":qs[i]; String aa=as[i]==null?"":as[i]; if((qq+" "+aa).toLowerCase().contains(needle)) out.add(new FaqHit(section,qq,aa)); }
    }
    private void renderSingleFaq(FaqHit h){ begin(h.section,"Risultato della ricerca nelle FAQ"); LinearLayout c=faqCard(h.question,h.answer); body.addView(c); TextView q=(TextView)c.getChildAt(0); q.performClick(); }

'''
s = s.replace(begin_marker, search_methods + begin_marker, 1)

# FAQ helper must accept arbitrary non-zero counts now that accessory subpages vary from 1 to 10 entries.
old_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||(questions.length!=4&&questions.length!=5&&questions.length!=10&&questions.length!=11)) throw new IllegalStateException("FAQ count must be 4, 5, 10 or 11 for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
new_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||questions.length<1) throw new IllegalStateException("FAQ arrays invalid for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
if old_helper not in s:
    raise SystemExit('v0.4.3: FAQ helper marker missing')
s = s.replace(old_helper,new_helper,1)

p.write_text(s,encoding='utf-8')
out=p.read_text(encoding='utf-8')
for marker in [
    'Cerca nelle FAQ…','renderFaqSearchResults','renderSingleFaq','FILTRI E ACCESSORI ROLLEIFLEX','ROLLEIFLEX 3.5 — ACCESSORI','ROLLEIFLEX 2.8 — ACCESSORI',
    'Rolleifilter Sport','Gelb Mittel','Hellgrün','Hellrot','Hellblau','Rolleiparkeil 1','Rolleiparkeil 2','Heidosmat-Rolleinar 1','puntino rosso',
    'circa da 1 metro a 47 cm','FAQ arrays invalid for '
]:
    if marker not in out: raise SystemExit('v0.4.3 guard missing: '+marker)
print('Darkroom v0.4.3 Rolleiflex accessories + global FAQ search patch ready')
