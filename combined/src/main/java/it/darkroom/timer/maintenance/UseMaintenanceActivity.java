package it.darkroom.timer.maintenance;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.LinearLayout;
import android.widget.HorizontalScrollView;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.EditText;
import android.text.Editable;
import android.text.TextWatcher;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

/** Autonomous reference module. No Timer state, SONOFF state or Assistant state is read or written here. */
public final class UseMaintenanceActivity extends Activity {
    private static final int BG = Color.rgb(0, 0, 0);
    private static final int PANEL = Color.rgb(24, 24, 24);
    private static final int BRONZE = Color.rgb(181, 139, 82);
    private static final int WARM = Color.rgb(246, 243, 238);
    private static final int MUTED = Color.rgb(170, 166, 162);
    private static final int RED = Color.rgb(124, 31, 31);


    private static final String EV_TABLE_QUESTION = "Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?";
    private static final String[] EV_APERTURES = {"f/2,8", "f/3,5", "f/4", "f/5,6", "f/8", "f/11", "f/16", "f/22"};
    private static final String[] EV_TIMES = {
            "1 s ★●", "1/2 ★●", "1/4 ★", "1/5 ●", "1/8 ★", "1/10 ●", "1/15 ★", "1/25 ●",
            "1/30 ★", "1/50 ●", "1/60 ★", "1/100 ●", "1/125 ★", "1/250 ★●", "1/500 ★●"
    };
    private static final String[][] EV_VALUES = {
            {"3,0", "3,6", "4,0", "5,0", "6,0", "6,9", "8,0", "8,9"},
            {"4,0", "4,6", "5,0", "6,0", "7,0", "7,9", "9,0", "9,9"},
            {"5,0", "—", "6,0", "7,0", "8,0", "8,9", "10,0", "10,9"},
            {"—", "5,9", "6,3", "7,3", "8,3", "9,2", "10,3", "11,2"},
            {"6,0", "—", "7,0", "8,0", "9,0", "9,9", "11,0", "11,9"},
            {"—", "6,9", "7,3", "8,3", "9,3", "10,2", "11,3", "12,2"},
            {"6,9", "—", "7,9", "8,9", "9,9", "10,8", "11,9", "12,8"},
            {"—", "8,3", "8,6", "9,6", "10,6", "11,6", "12,6", "13,6"},
            {"7,9", "—", "8,9", "9,9", "10,9", "11,8", "12,9", "13,8"},
            {"—", "9,3", "9,6", "10,6", "11,6", "12,6", "13,6", "14,6"},
            {"8,9", "—", "9,9", "10,9", "11,9", "12,8", "13,9", "14,8"},
            {"—", "10,3", "10,6", "11,6", "12,6", "13,6", "14,6", "15,6"},
            {"9,9", "—", "11,0", "11,9", "13,0", "13,9", "15,0", "15,9"},
            {"10,9", "11,6", "12,0", "12,9", "14,0", "14,9", "16,0", "16,9"},
            {"11,9", "12,6", "13,0", "13,9", "15,0", "15,9", "17,0", "17,9"}
    };

    private static final String LPL7451_URL = "https://drive.google.com/file/d/1y67xUwISxjz8f4-QFmBUOquabVezXq4A/view?usp=drivesdk";
    private static final String COLOR3_URL = "https://drive.google.com/file/d/1ITpUaCAcMZ_WF6GnTtwwG082nI_ULMn5/view";
    private static final String JOBO_URL = "https://drive.google.com/file/d/1uteXQ0j4VDVM8mvboASGxeZOhqPS48dZ/view";
    private static final String ACP200_URL = "https://drive.google.com/file/d/1-FuGPzvLvTpopfDIgmEv-0WrPCEhSSTr/view";
    private static final String MINOLTA_MANUAL_URL = "https://drive.google.com/file/d/1rniErjqK3_S-0pDY3mvXosb4dk_Y0GOV/view?usp=drivesdk";
    private static final String ZONE_URL = "https://drive.google.com/file/d/1A_zEMVEGD9C8vVtLDEom_NfOKHRO0dnb/view";
    private static final String PRINT_URL = "https://drive.google.com/file/d/1QJuScbe2I9nLx2NY7suCVXZWR_Culvzz/view";
    private static final String COOKBOOK_URL = "https://drive.google.com/file/d/1LfXqGW4t9vamylwurIbPNqJoIsd_4UwR/view";
    private static final String DARKROOM_GUIDE_URL = "https://drive.google.com/file/d/1_40jRUpA5Qxwr9a_n6PiT3V19SqZijQ2/view?usp=drivesdk";
    private static final String NIKON_L35AF_URL = "https://drive.google.com/file/d/1jJn6XXhkkGJqSR9JKD377LqSL7hte14p/view?usp=drivesdk";
    private static final String NIKON_F100_URL = "https://drive.google.com/file/d/1-6_YrOo-hJwlLB4en3-vcBupuHxQm1l9/view?usp=drivesdk";
    private static final String NIKON_ZOOM100_URL = "https://drive.google.com/file/d/1hyDsxIw4Qic4peEWu-vRP95pfMh1BxWI/view?usp=drivesdk";
    private static final String ROLLEI_35_MX_URL = "https://drive.google.com/file/d/1vt9usyPAyd0N5Zd1LS-UTKvMZmBJVAmm/view?usp=drivesdk";
    private static final String ROLLEI_28_E2_URL = "https://drive.google.com/file/d/1aES38tuDIy9I8RQlGTJDVNAVyzf3SdiS/view?usp=drivesdk";

    private final ArrayDeque<Runnable> backStack = new ArrayDeque<>();
    private Runnable currentScreen;
    private LinearLayout body;

    private static final String[] Q_DARKROOM = {
            "Ho premuto ARMA ma l’ingranditore non parte. È un errore?",
            "Darkroom non trova il SONOFF. Cosa devo controllare?",
            "Perché alcuni tempi vengono arrotondati a 0,5 secondi?",
            "Come funziona la luce rossa automatica?",
            "Nello Split Grade devo usare contemporaneamente giallo e magenta?",
            "Posso rifare un provino senza perdere la ricetta che avevo già trovato?",
            "Nessuna striscia del provino mi convince. Cosa devo fare?",
            "Una sequenza sembra bloccata o il SONOFF non è nello stato previsto. Come intervengo?",
            "Perché Darkroom non mi lascia calcolare uno sviluppo o un bagno?",
            "Come faccio a non perdere LOG e ricette?"
    };
    private static final String[] A_DARKROOM = {
            "No. ARMA prepara la sequenza ma non avvia l’esposizione. L’app configura e verifica il SONOFF e attende il consenso dell’operatore. Quando compare ARMATO, l’esposizione parte premendo il pulsante fisico.",
            "Verifica che telefono e SONOFF siano sulla stessa rete locale, che il SONOFF sia in modalità DIY e che in IMPOSTAZIONI sia stato selezionato il dispositivo corretto. Se necessario usa nuovamente CAMBIA SONOFF.",
            "Il sistema SONOFF usato da Darkroom lavora con una risoluzione operativa di 0,5 s. I calcoli possono essere più precisi, ma il tempo finale realmente eseguibile viene adattato al mezzo secondo compatibile.",
            "Serve un secondo SONOFF DIY, separato da quello dell’ingranditore. Se la safelight era accesa prima dell’esposizione, Darkroom la spegne durante il ciclo e poi la ripristina. Se era già spenta, non viene accesa automaticamente alla fine.",
            "No. Lo Split Grade usa due esposizioni consecutive. Per il MORBIDO imposta il giallo e azzera il magenta. Per il DURO imposta il magenta e azzera il giallo. Le due esposizioni interagiscono: giallo non significa solo luci e magenta non significa solo ombre.",
            "Sì. Da una stampa singola puoi usare RIFAI PROVINO SINGOLO. Da una stampa Split Grade puoi scegliere RIFAI SOLO IL DURO oppure RIFAI ENTRAMBI. La ricetta precedente rimane invariata finché non completi il nuovo provino e scegli un nuovo risultato.",
            "Usa NESSUNA MI CONVINCE - REIMPOSTA PROVINO. Puoi modificare tempo iniziale, passo, filtrazione, numero di strisce o altri parametri e ripetere il provino senza trasferire una ricetta sbagliata alla STAMPA.",
            "Prima usa ANNULLA CICLO. Se il sistema non torna correttamente a riposo, usa RIPRISTINO EMERGENZA, che spegne l’uscita dell’ingranditore e disattiva Inching. Prima di riprendere il lavoro verifica lo stato del SONOFF.",
            "Di solito manca un dato necessario oppure la configurazione non è compatibile. Controlla prodotto, diluizione, temperatura, numero di rulli e tank. Per la JOBO CPE2 Darkroom blocca inoltre configurazioni che richiedono più di 600 ml in rotazione. Se manca una diluizione, correggi prima la scheda del prodotto nel magazzino.",
            "Usa periodicamente ESPORTA BACKUP nel LOG: viene creato un backup JSON che può essere ripristinato con IMPORTA BACKUP. Una ricetta salvata può essere riaperta e trasferita nuovamente alla STAMPA con USA PER STAMPA."
    };

    private static final String[] Q_NIKON_L35AF = {
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

    private static final String[] Q_NIKON_F100 = {
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

    private static final String[] Q_LPL7451 = {
            "Quali formati supporta il JOBO/LPL 7451?",
            "Quali obiettivi associa Darkroom ai tre formati?",
            "Quale portanegativi devo montare?",
            "Come inserisco e blocco il portanegativi?",
            "Come regolo ingrandimento e messa a fuoco?",
            "Quali sono le scale del modulo colore?",
            "A cosa serve la leva della luce bianca?",
            "A cosa serve l’attenuatore della luce?",
            "La ventola deve restare accesa durante l’uso?",
            "Quando va controllata la camera di diffusione?",
            "Le manopole del modulo colore e del blocco colonna sono fragili: come si riparano o sostituiscono?"
    };
    private static final String[] A_LPL7451 = {
            "Il modello 7451 copre negativi dal 24×36 mm al 4×5 pollici. In Darkroom i formati operativi sono 35 mm (24×36), 6×6 (56×56) e 4×5 (101,6×127 mm).",
            "L’associazione automatica concordata è: 35 mm → 50 mm; 6×6 → 75 mm; 4×5 → 150 mm. La lente resta registrata nei metadati della ricetta e del LOG.",
            "Usa sempre il portanegativi a formato singolo corrispondente: 35 mm/24×36, 6×6/56×56 oppure 4×5/101,6×127. Il manuale descrive portanegativi di tipo sandwich e segnala che possono essere accessori opzionali in alcune aree.",
            "Solleva la leva del fermo, inserisci il portanegativi frontalmente o lateralmente e riabbassa la leva per bloccarlo. Prima verifica che la piastra del piano portanegativi sia correttamente posizionata sui perni.",
            "Allenta il blocco del carrello, usa la leva per gli spostamenti rapidi e la manopola per quelli fini, quindi riblocca la testa. Metti a fuoco con una delle due manopole; sul lato destro è disponibile la regolazione fine 1:5.",
            "Il modulo dicroico ha scale di densità giallo e ciano 0–200 cc e magenta 0–170 cc. Per la carta multigrade Darkroom usa la tabella LPL dei gradi 0–5 con Y e M, lasciando il ciano a zero.",
            "Portandola in posizione orizzontale, i filtri escono dal percorso ottico senza cambiare i valori impostati. Serve per facilitare composizione e messa a fuoco; prima di esporre riporta i filtri nel percorso ottico.",
            "Inserisce un attenuatore che riduce la luce a circa un quarto, cioè due stop, così puoi ottenere tempi di esposizione più lunghi senza cambiare la filtrazione di contrasto.",
            "Sì. Il manuale prescrive di tenere sempre in funzione la ventola mentre l’ingranditore è in uso e di utilizzare esclusivamente l’alimentatore previsto. Darkroom non gestisce automaticamente la ventola.",
            "Dopo molte ore il rivestimento in materiale espanso può ingiallire. Il manuale descrive la rimozione della piastra superiore e l’estrazione della camera di diffusione; esegui l’intervento a macchina spenta e fredda.",
            "Le tre manopole Ciano, Magenta e Giallo usano lo stesso ricambio LPL 3281-282 e sono intercambiabili tra loro. Se una non entra, verifica a macchina spenta che sul perno non sia rimasta la clip metallica della manopola rotta, senza fare leva sul pannello. Una riparazione con pochissimo adesivo cianoacrilato può reggere sui comandi colore solo se il selettore ruota libero: lavora sulla manopola smontata, perché l’adesivo colato lungo l’alberino può bloccare o danneggiare il meccanismo. La manopola del blocco colonna è invece il ricambio distinto LPL 3481-257 e sopporta molta più coppia: l’incollaggio è solo provvisorio. Prima dell’acquisto misura diametro, lunghezza e profondità utile dell’alberino e distingui 6,00 da 6,35 mm. Se c’è spazio, scegli una manopola robusta da circa 30–35 mm, in alluminio o con boccola metallica, con foro adatto e grano laterale serrato moderatamente sul lato piatto della D. Non forzare il blocco: una manopola più grande aumenta la leva sul meccanismo."
    };

    private static final String[] Q_COLOR3 = {
            "A cosa servono Y, M e C?", "Come si usano Y e M per controllare il contrasto della carta multigrade?", "Come interpreto la scala 0–200 dei filtri Y/M/C?", "Posso usare contemporaneamente giallo e magenta e cosa succede?", "Qual è la lampada prevista dalla Color 3?", "A cosa serve lo schermo di densità D?", "Come si utilizza la Color 3 per stampare in B/N su carta multigrade?", "Perché cambiando filtrazione cambia anche il tempo di esposizione?", "Come si compensa il tempo quando modifico Y/M/C?", "Come si puliscono filtri, diffusore e parti ottiche?",
            "Come si sostituisce correttamente la lampada della Meopta Color 3?"
    };
    private static final String[] A_COLOR3 = {
            "Sono filtri sottrattivi: Y agisce sulla componente blu, M sulla verde e C sulla rossa. La testa li inserisce in modo continuo nel fascio luminoso.",
            "Per la carta multigrade si lavora con Y e M come filtrazioni di contrasto. Il manuale Color 3 però non fornisce una tabella grado-carta: qui quindi non assegniamo numeri di gradazione non documentati.",
            "Ogni filtro ha scala Meopta 0–200, a passi di 2. È una scala propria della testa: il manuale la confronta solo indicativamente con altri sistemi, non con i gradi della carta multigrade.",
            "Sì. Y e M possono essere inseriti insieme: la luce risultante cambia e cambia anche l’esposizione necessaria. Il manuale prevede l’uso combinato dei filtri e fornisce fattori di correzione del tempo.",
            "La Color 3 è prevista con lampada alogena a riflettore 12 V / 100 W.",
            "D attenua la luce senza cambiare le impostazioni dei filtri. La scala 0–60 copre circa due stop complessivi; il manuale usa D≈30 come riferimento pratico di circa uno stop.",
            "Imposta la filtrazione Y/M desiderata e lascia C fuori salvo una necessità specifica. Il manuale non contiene una conversione in gradi multigrade, quindi il contrasto va verificato sulla carta con un provino.",
            "I filtri assorbono quantità diverse di luce. Aumentando o modificando Y/M/C cambia la trasmissione totale e quindi il tempo necessario per ottenere la stessa densità di stampa.",
            "Usa i fattori k riportati nel manuale: t₂ = t₁ × (kY₂×kM₂×kC₂)/(kY₁×kM₁×kC₁). È il metodo documentato per mantenere l’esposizione quando cambi filtrazione.",
            "Proteggi la testa da polvere e umidità. Pulisci il vetro diffusore con panno morbido e tratta con delicatezza la camera di miscelazione. A lampada fredda e scollegata, evita di toccare bulbo e riflettore con le dita.",
            "Scollega la testa dal trasformatore e lasciala raffreddare. La lampada prevista è una alogena a riflettore 12 V / 100 W; il manuale indica Tungsram 55 220, Osram 64 627, Philips 68 34 o Thorn A1/231, con attacco GZ 6.35-18 o equivalente del modello indicato. Svita le due viti del supporto, estrai il portalampada, libera la lampada dalle molle elastiche e scollegala dallo zoccolo sui fili. Inserisci la nuova lampada nello zoccolo e nelle molle facendo coincidere la spalla del riflettore con l’incavo del supporto metallico; verifica i contatti, reinserisci il supporto e serra le due viti. Non toccare con le dita il bulbo né la superficie specchiante interna del riflettore: usa un panno pulito e asciutto. Alla prima sostituzione possono essere presenti dispositivi di sicurezza da trasporto sulle molle fermalampada: vanno rimossi e non rimontati per l’uso normale."
    };

    private static final String[] Q_JOBO = {
            "Come devo posizionare e livellare correttamente la CPE2?", "Quanta acqua devo mettere nella vasca?", "Come porto chimica e macchina alla temperatura corretta?", "Quanto tempo prima devo accendere la CPE2?", "Come si monta correttamente il tank sulla macchina?", "Dove deve essere posizionato il supporto a rulli?", "Come si usa correttamente il Lift?", "Quali tank posso utilizzare sulla CPE2?", "Come si pulisce e si mantiene la CPE2?", "Cosa controllo se motore, riscaldamento o temperatura non funzionano correttamente?"
    };
    private static final String[] A_JOBO = {
            "La macchina deve essere perfettamente in piano. Il manuale indica di controllare con una livella sul bordo anteriore, non sul drum, e di compensare eventuali dislivelli sotto l’apparecchio.",
            "Per la CPE il manuale indica circa 7–8 litri nel bagno d’acqua, in funzione del sistema tank usato. Riempilo prima di alimentare la macchina.",
            "Riempi il bagno, imposta il termostato e controlla la temperatura con un termometro nel bagno o nei prodotti. La chimica raggiunge l’equilibrio reale solo dopo il tempo di riscaldamento.",
            "Per raggiungere con precisione la temperatura dei prodotti, il manuale indica circa 90 minuti. Non basta che il bagno sembri già caldo.",
            "Con il motore fermo o in movimento, accoppia il magnete sul fondo del tank al magnete motore. Verifica che il drum sia sostenuto correttamente e ruoti senza impuntamenti.",
            "Il supporto a rulli deve guidare il drum circa nell’ultimo terzo della sua lunghezza, così da mantenerlo stabile durante la rotazione.",
            "Il manuale italiano disponibile nel Drive non descrive una procedura operativa del Lift. Per evitare istruzioni non verificate, questa FAQ non aggiunge passaggi che la fonte non contiene.",
            "Il manuale tratta i sistemi tank 1500 e 2500/2800 e, sui modelli compatibili, 3000/Expert. La compatibilità effettiva dipende da macchina, tank e carico: non viene aggiunto qui un elenco oltre a quello documentato.",
            "Svuota il bagno d’acqua dopo il lavoro. Il manuale indica lubrificazione occasionale dei rulli guida con vaselina e una pulizia periodica con Processor-Clean JOBO, circa ogni tre mesi.",
            "Motore in una sola direzione: controlla la posizione dello star switch sul magnete motore. Riscaldamento assente: individua la causa e, a macchina fredda, verifica il reset della protezione termica. Per problemi di circolazione, controlla anche rotore/girante."
    };

    private static final String[] Q_ACP = {
            "Come preparo e livello la ACP200 prima dell’uso?", "Quanto prodotto devo mettere nelle vasche?", "Come imposto la temperatura?", "Come si calibra la temperatura reale della macchina?", "Come scelgo tra 45, 120 e 210 secondi?", "Come si cambiano materialmente le velocità tramite gli ingranaggi?", "Come devo inserire la carta nella macchina?", "Quanto tempo devo attendere prima di iniziare a sviluppare?", "Come si svuota, lava e pulisce correttamente la ACP200?", "Cos’è la configurazione High Speed 30/90/150 s e come faccio a capire se la mia macchina la possiede?"
    };
    private static final String[] A_ACP = {
            "Appoggia la macchina su un piano stabile e regolala con i piedini finché è perfettamente orizzontale. Controlla anche che scarichi e vasche siano correttamente chiusi prima di riempire.",
            "Il manuale consolidato indica 2,5 litri di soluzione di lavoro per ciascuna vasca.",
            "Imposta il termostato con il comando TEMP. La spia resta accesa durante il riscaldamento e si spegne quando il termostato raggiunge il punto impostato.",
            "Quando la spia si spegne, misura la temperatura reale del bagno sviluppatore. Se non coincide con la scala, sfila con cautela la manopola e rimontala facendo corrispondere l’indice alla temperatura misurata.",
            "Nella configurazione standard: rosso 45 s, verde 120 s, blu 210 s. La macchina esce di fabbrica sulla velocità 45 s.",
            "Capovolgi la macchina secondo la procedura del manuale, rimuovi il coperchio inferiore, allenta il perno filettato e sposta sul relativo albero l’ingranaggio colorato della velocità scelta. Deve essere impegnato un solo rapporto alla volta.",
            "Apri il coperchio e inserisci il foglio verticalmente finché i rulli lo prendono. Guardando la macchina frontalmente, il lato emulsione deve essere rivolto a sinistra. La fase finale di inserimento va fatta al buio.",
            "Il manuale operativo indica circa 20 minuti perché le soluzioni arrivino alla temperatura di lavoro. Verifica comunque la temperatura reale prima del primo foglio.",
            "A fine lavoro scollega la macchina e apri i tubi di scarico. Risciacqua accuratamente vasche e rack; per uso regolare il manuale raccomanda una pulizia approfondita settimanale. Evita abrasivi e solventi aggressivi.",
            "Il kit High Speed porta i rapporti a rosso 30 s, verde 90 s, blu 150 s e modifica sia rack sviluppo sia bleach-fix con ingranaggi/posizioni specifiche. Per identificarlo, verifica la presenza dell’hardware High Speed descritto nelle figure 3–4; non basta l’etichetta esterna."
    };

    private static final String[] Q_MINOLTA = {
            "Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?",
            "Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?",
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
            "Tabella grafica dei valori EV per le coppie tempo/diaframma delle Rolleiflex 2.8 E2 e 3.5 Tessar MX. La colonna Tempo resta fissa; i diaframmi scorrono orizzontalmente. Gli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.",
            "Il Minolta Auto Meter III F può essere usato molto comodamente con il Sistema Zonale, soprattutto con il mirino 10° per la misura riflessa.\n\n1. Misura il contrasto della scena\n\nImposta:\n\n- gli ISO reali della pellicola;\n- modalità AMBI;\n- visualizzazione EV.\n\nMisura prima l’ultima ombra nella quale vuoi ancora conservare dettaglio, poi l’ultima luce nella quale vuoi ancora conservare dettaglio.\n\nCalcola:\n\nEV luce − EV ombra = intervallo della scena in stop\n\nEsempio:\n\n- ombra: EV 5\n- luce: EV 10\n- differenza: 5 EV = 5 stop\n\nSe deciderai di collocare l’ombra in Zona III, la luce cadrà quindi in Zona VIII.\n\nIndicativamente:\n\n- 4–5 EV → scena con gamma tonale normale e facilmente gestibile;\n- meno di 4 EV → scena tendenzialmente piatta;\n- più di 5 EV → scena progressivamente più contrastata.\n\n2. Determina l’esposizione\n\nPassa alla visualizzazione FNo..\n\nMantieni impostati gli ISO reali della pellicola e scegli sul Minolta il tempo che vuoi utilizzare.\n\nMisura nuovamente l’ombra con dettaglio.\n\nIl diaframma indicato dall’esposimetro collocherebbe quella superficie in Zona V.\n\nPer collocarla invece in Zona III devi togliere 2 stop di esposizione.\n\nPuoi farlo come preferisci:\n\n- chiudendo il diaframma di 2 stop;\n- accorciando il tempo di 2 stop;\n- dividendo i 2 stop fra tempo e diaframma.\n\nEsempio:\n\nil Minolta indica 1/125 s – f/4.\n\nPer mettere quell’ombra in Zona III puoi usare, per esempio:\n\n- 1/125 s – f/8\n- 1/500 s – f/4\n- 1/250 s – f/5,6\n\nLe tre combinazioni danno la stessa esposizione.\n\nIn breve\n\nEV serve per valutare il contrasto della scena.\n\nTempo e diaframma servono per impostare concretamente l’esposizione sulla macchina fotografica.\n\nPer collocare in Zona III un’ombra misurata normalmente dall’esposimetro:\n\ntogli sempre 2 stop rispetto alla lettura fornita dal Minolta.",
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

    private static final String[] Q_R35_GENERAL = {
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

    private static final String[] Q_PROCESS_WASH = {
            "Come realizzare un provino a contatto?",
            "Quando è utile un pre-bagno della pellicola prima dello sviluppo?",
            "Come lavare correttamente la pellicola?",
            "Come lavare correttamente la carta RC?"
    };
    private static final String[] A_PROCESS_WASH = {
            "Usa il provino a contatto per vedere e archiviare in un solo foglio tutti i fotogrammi e scegliere cosa stampare. Porta la testa dell’ingranditore abbastanza in alto da illuminare uniformemente tutto il foglio; per carta multigrade parti da un contrasto normale, circa grado/filtro 2. Metti la carta fotografica con emulsione verso l’alto, appoggia sopra le strisce di negativi con emulsione verso la carta e tienile perfettamente aderenti con un vetro pulito o un contact printer. Fai prima una piccola prova di esposizione: come riferimento iniziale ILFORD indica circa f/8 e 8–15 s per negativi di densità media, ma il tempo va sempre verificato con la tua testa, carta e filtrazione. Sviluppa, arresta, fissa e lava come una normale stampa RC.",
            "Nel flusso B/N JOBO di questa app il pre-bagno NON è la scelta predefinita. Le schede tecniche ILFORD per processori rotativi raccomandano in generale di evitarlo perché può favorire sviluppo non uniforme; senza pre-risciacquo indicano di ridurre fino a circa il 15% i tempi da tank a inversione, che è il criterio già usato dall’app. Esiste però anche una procedura JOBO storica alternativa: pre-risciacquo in acqua per circa 5 minuti e poi uso dei tempi previsti per l’agitazione manuale. Quindi usa il pre-bagno solo se la scheda tecnica di pellicola/rivelatore o il protocollo JOBO che stai seguendo lo richiede esplicitamente, e non sommarlo automaticamente alla riduzione -15%: scegli un solo regime e calibra quella combinazione.",
            "Dopo un fissaggio non indurente, lava la pellicola con acqua alla stessa temperatura del processo, entro circa ±5 °C. Metodo continuo: 5–10 minuti in acqua corrente. Metodo ILFORD a basso consumo: riempi la tank, 5 inversioni, scarica; riempi, 10 inversioni, scarica; riempi, 20 inversioni, scarica. IMBIBENTE CON JOBO ROTATIVA: non farlo girare nel processore e non lasciare che imbibente/stabilizzatore contaminino tank e spirali. JOBO prescrive di togliere la pellicola dalla spirale e fare l’ultimo bagno in un contenitore separato. Per non schiumare: prepara prima l’acqua, aggiungi solo la dose prevista dal produttore (per ILFOTOL, per esempio, 1+200), mescola piano senza agitare né versare dall’alto e immergi delicatamente la pellicola; niente rotazione continua, shaker o agitazione energica. Non risciacquare dopo l’imbibente. Appendi in ambiente pulito e lascia sgocciolare. Risciacqua poi tank e spirali con sola acqua e falli asciugare prima del prossimo sviluppo.",
            "Per carta RC, dopo il fissaggio lava in acqua fresca corrente per circa 2 minuti; ILFORD specifica acqua sopra 5 °C. Non trattarla come carta baritata: tempi molto lunghi non migliorano il lavaggio e l’immersione prolungata può causare penetrazione d’acqua ai bordi e incurvamento; evita tempi bagnati oltre circa 15 minuti. Se serve la massima rapidità, ILFORD ammette un lavaggio energico di circa 30 secondi in acqua corrente. Un ultimo risciacquo con imbibente molto diluito può aiutare l’asciugatura uniforme, ma non è necessario per il lavaggio chimico vero e proprio."
    };

    private static final String[] Q_TESTSTRIP = {
            "Come realizzo correttamente un provino?", "Da quale parte devo leggere il provino?", "Ho trovato prima i bianchi giusti: cosa faccio?", "Ho trovato prima i neri giusti: cosa faccio?", "Come riconosco quando il contrasto è corretto?", "Come scelgo la striscia da portare in stampa?", "Come modifico il contrasto senza perdere il tempo trovato?", "Cosa cambia tra provino in secondi e provino in f-stop?", "Metodo SCOPRIRE e COPRIRE: qual è la differenza?", "Quando devo rifare il provino?"
    };
    private static final String[] A_TESTSTRIP = {
            "Metti a fuoco, scegli un diaframma di lavoro e usa una striscia che contenga insieme zone importanti chiare e scure. Esponi a gradini regolari, sviluppa sempre a fondo e valuta il provino asciutto o comunque nello stesso stato di confronto.",
            "Leggilo dal CHIARO allo SCURO. Cerca dove arrivano prima i bianchi utili e dove arrivano i neri utili: l’ordine in cui li trovi ti dice se il contrasto va corretto.",
            "AUMENTA il contrasto. Hai raggiunto il bianco utile prima del nero utile: serve più separazione tra le due estremità.",
            "DIMINUISCI il contrasto. Hai raggiunto il nero utile prima del bianco utile: la gamma è troppo compressa verso gli estremi.",
            "Quando bianchi e neri desiderati sono corretti nello stesso gradino. Regola guida: bianchi prima → aumenta contrasto; neri prima → diminuisci; insieme → contrasto giusto.",
            "Scegli il gradino in cui il soggetto principale ha il tono giusto e, nello stesso gradino, bianchi e neri conservano il dettaglio che vuoi. Non scegliere solo il nero più profondo o il bianco più brillante.",
            "Mantieni come riferimento il tempo del gradino scelto e cambia solo la filtrazione/gradazione. Poi verifica con un nuovo provino perché un cambio di contrasto può modificare anche la densità percepita.",
            "In secondi aggiungi quantità lineari di tempo; in f-stop ogni passo è un rapporto costante di esposizione. Gli f-stop danno gradini percettivamente più uniformi, soprattutto quando il tempo base cambia molto.",
            "SCOPRIRE: liberi progressivamente nuove porzioni, quindi alcune zone accumulano più esposizione. COPRIRE: parti esposti e copri progressivamente. Cambia il verso in cui si accumulano i tempi; scegli un metodo e leggilo sempre nello stesso verso.",
            "Rifallo se cambi ingrandimento, diaframma, filtrazione/contrasto, carta, negativo o una condizione che altera realmente l’esposizione. Rifallo anche quando nessun gradino mette insieme bianchi e neri come desideri."
    };

    private static final String[] Q_SPLIT = {
            "Cos’è lo Split Grade?", "A cosa serve l’esposizione morbida/gialla?", "A cosa serve l’esposizione dura/magenta?", "Perché giallo non significa semplicemente “luci” e magenta “ombre”?", "Come trovo i due tempi?", "In quale ordine faccio le due esposizioni?", "Come correggo una stampa Split Grade?", "Come integro Dodge e Burn?", "Quando conviene usarlo?", "Quando invece è inutile complicarsi con lo Split Grade?"
    };
    private static final String[] A_SPLIT = {
            "È una stampa ottenuta sommando due esposizioni dello stesso foglio: una a contrasto morbido e una a contrasto duro. La stampa finale nasce dall’interazione delle due.",
            "La filtrazione morbida abbassa il contrasto e aiuta a costruire la struttura dei toni chiari e medi, ma continua a esporre l’intera carta: non agisce solo sulle luci.",
            "La filtrazione dura aumenta separazione e profondità nei toni scuri, ma continua a modificare anche il resto della stampa: non agisce solo sulle ombre.",
            "Perché le due emulsioni della carta ricevono entrambe luce in entrambe le esposizioni. Cambiare il tempo giallo può cambiare anche i toni scuri; cambiare il magenta può spostare anche i toni chiari.",
            "Trova prima un tempo morbido che dia una buona struttura generale, poi aggiungi il duro finché neri e separazione sono corretti. Rivedi entrambi se una correzione importante sposta l’equilibrio.",
            "L’ordine fisico delle due esposizioni non cambia la somma della luce, ma per lavorare in modo ripetibile usa sempre lo stesso ordine. Un flusso pratico è morbido prima, duro dopo.",
            "Correggi il canale che sta causando il problema, poi ristampa. Se tocchi molto un tempo, controlla anche l’altro: le due esposizioni non sono indipendenti.",
            "Puoi mascherare o bruciare durante una sola esposizione oppure durante entrambe, a seconda di quale contrasto locale vuoi ottenere. Registra sempre canale, zona e tempo dell’intervento.",
            "È utile quando una singola filtrazione non ti dà insieme la separazione desiderata nelle zone chiare e scure, o quando vuoi controllare in modo distinto il carattere di aree diverse.",
            "Se una singola filtrazione produce già la stampa che vuoi, lo Split Grade aggiunge solo passaggi e possibilità d’errore. Usalo come strumento, non come obbligo."
    };

    private static final String[] Q_ZONE = {
            "Come utilizzo rapidamente il Sistema Zonale sul campo?",
            "Cos’è il Sistema Zonale e a cosa serve?", "Cosa rappresentano le zone da 0 a X?", "Qual è la Zona V e perché è il riferimento dell’esposimetro?", "Come decido in quale zona collocare una parte della scena?", "Come espongo per mantenere dettaglio nelle ombre?", "Come valuto le alte luci rispetto alle ombre?", "Cosa significa previsualizzare la stampa prima dello scatto?", "Quando serve aumentare lo sviluppo del negativo?", "Quando serve ridurre lo sviluppo del negativo?", "Come collego Sistema Zonale, esposizione e stampa finale?"
    };
    private static final String[] A_ZONE = {
            "Misura l’ultima ombra nella quale vuoi ancora conservare dettaglio; oltre quella accetti quasi nero e nero.\n\nL’esposimetro, se ne segui direttamente la lettura, collocherebbe quella superficie in Zona V.\n\nTu vuoi invece collocarla in Zona III, quindi devi dare 2 stop meno di esposizione.\n\nSe ragioni in EV:\n\nEV misurato + 2 = EV di esposizione\n\nRicorda però che questo non significa obbligatoriamente lavorare con gli EV sulla macchina: i 2 stop possono essere tolti indifferentemente con diaframma, tempo oppure una combinazione dei due.\n\nEsempio:\n\nlettura dell’ombra:\n\n1/125 s – f/4\n\nPossibili esposizioni per collocarla in Zona III:\n\n1/125 – f/8 oppure 1/500 – f/4 oppure 1/250 – f/5,6\n\nPoi misura l’ultima luce nella quale vuoi ancora conservare dettaglio.\n\nPer valutare il contrasto della scena usa gli EV:\n\nEV luce − EV ombra = differenza in stop\n\nEsempio:\n\n- ombra EV 5\n- luce EV 10\n- differenza = 5 EV\n\nAvendo collocato l’ombra in Zona III:\n\nZona III + 5 = Zona VIII\n\nQuindi le ombre importanti cadono in Zona III e le alte luci importanti in Zona VIII.\n\nIndicativamente:\n\n- 4–5 EV di differenza → gamma tonale normale e ben gestibile;\n- meno di 4 EV → scena tendenzialmente piatta;\n- più di 5 EV → scena progressivamente più contrastata.\n\nRegola da ricordare\n\nMisura l’ombra con dettaglio → togli 2 stop → scatta.\n\nEV luce − EV ombra → ti dice quanto è contrastata la scena.",
            "È un metodo per collegare ciò che misuri nella scena con il tono che vuoi ottenere nella stampa. L’idea centrale è decidere prima il risultato, misurare i valori importanti e adattare esposizione e sviluppo al risultato previsto.",
            "Le zone ordinano i toni dal nero estremo al bianco estremo in passi di esposizione. Il testo Drive usa esplicitamente la scala zonale e colloca la pelle chiara circa in Zona VI; non aggiungiamo qui soglie di dettaglio zona-per-zona non riportate nella fonte.",
            "La Zona V è il riferimento del grigio medio. Il materiale Adams indica che la Zona VI è leggermente sopra il grigio medio e cita il cartoncino grigio 18% come valore-base di controllo: da qui si spostano intenzionalmente gli altri toni.",
            "Misura la zona importante e chiediti come vuoi che appaia nella stampa. Se deve risultare più scura del grigio medio, la collochi sotto V; se deve risultare più chiara, sopra V. La scelta è parte della visualizzazione.",
            "Scegli un’ombra in cui vuoi mantenere informazione e assegna a quella misura un tono sufficientemente basso ma non privo del dettaglio desiderato. L’esposizione viene così ancorata alle ombre importanti.",
            "Dopo aver fissato le ombre, misura le alte luci importanti e guarda quanto è ampia l’escursione. Il testo Adams lega proprio questa escursione alla scelta dello sviluppo necessario per ottenere un negativo stampabile.",
            "Significa immaginare prima dello scatto come dovranno diventare nella stampa i principali valori della scena. Poi misuri quei valori e programmi esposizione e sviluppo in funzione dell’immagine finale prefigurata.",
            "Quando la scena ha poca escursione e vuoi un negativo con maggiore separazione tonale, puoi richiedere uno sviluppo più energico. La decisione va presa in funzione del processo di stampa previsto, non come regola automatica.",
            "Quando l’escursione luminosa della scena è troppo ampia per la stampa desiderata, ridurre lo sviluppo aiuta a contenere l’opacità delle alte luci e a comprimere il contrasto del negativo.",
            "Visualizza la stampa, misura i valori principali, scegli l’esposizione e poi adegua lo sviluppo per ottenere un negativo compatibile con quella stampa. Adams descrive il negativo come qualcosa da confezionare su misura per il processo di stampa."
    };

    private static final String[] Q_PRINT = {
            "Come preparo correttamente ingranditore, negativo e carta prima di stampare?", "Come trovo il tempo base con un provino?", "Come scelgo il contrasto corretto?", "Come capisco se una stampa è troppo chiara o troppo scura?", "Come correggo una stampa troppo contrastata o troppo piatta?", "Come uso Dodge e Burn senza perdere il controllo della stampa?", "Quando devo rifare il provino?", "Come valuto correttamente una stampa sotto luce bianca?", "Come mantengo costanti i risultati tra una stampa e la successiva?", "Qual è il flusso corretto dal negativo alla stampa finale?"
    };
    private static final String[] A_PRINT = {
            "Pulisci negativo e parti ottiche, inserisci il negativo correttamente, inquadra e metti a fuoco a diaframma aperto. Poi chiudi a un valore di lavoro intermedio e prepara carta e chimica prima di iniziare le esposizioni.",
            "Fai un provino con più esposizioni sulla stessa immagine, sviluppalo sempre a fondo e identifica il gradino più vicino al risultato desiderato. Poi fai un secondo provino più fine attorno a quel tempo.",
            "Cerca una stampa con neri profondi, bianchi puliti e una gamma di grigi leggibile. Se il risultato è piatto aumenta la gradazione; se è troppo duro riducila, verificando di nuovo il tempo.",
            "Troppo chiara: la carta ha ricevuto poca esposizione, quindi aumenta il tempo. Troppo scura: riduci il tempo. Valuta però solo dopo sviluppo completo e in condizioni di osservazione coerenti.",
            "Troppo contrastata: passa a una gradazione più morbida. Troppo piatta: passa a una più dura. Dopo il cambio fai un nuovo provino, perché contrasto e densità percepita si influenzano.",
            "Dodging/mascheratura riduce localmente l’esposizione; burning/bruciatura ne aggiunge. Muovi continuamente la maschera per evitare bordi netti, prova gli interventi su un provino e annota zona e tempo per renderli ripetibili.",
            "Quando cambi tempo in modo sostanziale, gradazione, diaframma, ingrandimento, carta o un intervento locale importante. Rifallo anche se nessun gradino del provino precedente è davvero convincente.",
            "Guarda la stampa con una luce bianca costante, non sotto la sola luce di sicurezza. Confronta i bianchi con carta non esposta e considera che la stampa può scurirsi asciugando.",
            "Annota almeno tempo, diaframma, altezza/ingrandimento, contrasto, carta, rivelatore e ogni Dodge/Burn. Mantieni costanti sviluppo e condizioni di valutazione: la ripetibilità nasce dalle note.",
            "Prepara e metti a fuoco → provino per il tempo → regola il contrasto → ristampa di verifica → aggiungi eventuali Dodge/Burn → registra tutti i dati → stampa finale e valutazione sotto luce bianca."
    };

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.BLACK); getWindow().setNavigationBarColor(Color.BLACK); showRoot();
    }
    private void showRoot(){ backStack.clear(); currentScreen=this::renderRoot; currentScreen.run(); }
    private void navigate(Runnable next){ if(currentScreen!=null) backStack.push(currentScreen); currentScreen=next; currentScreen.run(); }
    @Override public void onBackPressed(){ if(!backStack.isEmpty()){ currentScreen=backStack.pop(); currentScreen.run(); } else finish(); }

    private void renderRoot(){
        begin("USO E MANUTENZIONE","Manuali, tecnica di camera oscura, manutenzione verificata e ricettario.");
        addFaqSearch();
        body.addView(navCard("APP DARKROOM","Guida completa v0.2.8 e 10 FAQ operative",()->navigate(this::renderDarkroom)));
        body.addView(navCard("MANUALI","Apparecchi e FAQ ricavate dai manuali",()->navigate(this::renderManuals)));
        body.addView(navCard("TECNICA","Provini, Split Grade, Sistema Zonale, stampa B/N",()->navigate(this::renderTechnique)));
        body.addView(navCard("MANUTENZIONE","Solo procedure realmente verificate",()->navigate(this::renderMaintenance)));
        body.addView(navCard("RICETTARIO","The Darkroom Cookbook su Google Drive",()->navigate(this::renderCookbook)));
    }
    private void renderDarkroom(){
        renderFaqPage("APP DARKROOM","Uso operativo di Darkroom · guida completa v0.2.8",Q_DARKROOM,A_DARKROOM,DARKROOM_GUIDE_URL,"APRI GUIDA COMPLETA PDF");
        notice("La v0.2.9 aggiunge queste FAQ e una correzione grafica alla Home; il funzionamento operativo documentato nella guida v0.2.8 resta invariato.");
    }
    private void renderManuals(){
        begin("MANUALI","Tocca un apparecchio. Ogni pagina contiene FAQ operative e il collegamento al manuale completo quando disponibile.");
        body.addView(navCard("JOBO/LPL 7451","Ingranditore a diffusione · 35 mm, 6×6 e 4×5",()->navigate(()->renderFaqPage("JOBO/LPL 7451","Fonte: LPL 7451 - manuale completo tradotto in italiano",Q_LPL7451,A_LPL7451,LPL7451_URL,"APRI MANUALE COMPLETO IT"))));
        body.addView(navCard("MEOPTA COLOR 3","Testa colore",()->navigate(()->renderFaqPage("MEOPTA COLOR 3","Fonte: Meopta Color 3 - Manuale IT",Q_COLOR3,A_COLOR3,COLOR3_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("JOBO CPE2","Processore a rotazione",()->navigate(()->renderFaqPage("JOBO CPE2","Fonte: JOBO CPE2 CPA2 CPP2 - Manuale IT",Q_JOBO,A_JOBO,JOBO_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("THERMAPHOT ACP200","Processore carta",()->navigate(()->renderFaqPage("THERMAPHOT ACP200","Fonte: manuale consolidato completo IT",Q_ACP,A_ACP,ACP200_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("MINOLTA AUTO METER IIIF","Viewfinder 10° · flash · Spot Mask II · manuale completo IT",()->navigate(this::renderMinolta)));
        body.addView(title("FOTOCAMERE",16));
        body.addView(navCard("NIKON L35AF2","One Touch · DX automatico · 35 mm · 10 FAQ",()->navigate(()->renderFaqPage("NIKON L35AF2","Fonte: Nikon L35AF2 / One Touch - Manuale originale completo tradotto in italiano",Q_NIKON_L35AF,A_NIKON_L35AF,NIKON_L35AF_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("NIKON F100","Reflex 35 mm autofocus · 10 FAQ",()->navigate(()->renderFaqPage("NIKON F100","Fonte: Nikon F100 - Manuale IT",Q_NIKON_F100,A_NIKON_F100,NIKON_F100_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("NIKON ZOOM 100 AF","Zoom Touch 470 · 35 mm · 5 FAQ",()->navigate(()->renderFaqPage("NIKON ZOOM 100 AF","Fonte: Nikon Zoom 100 AF - Manuale IT",Q_NIKON_ZOOM100,A_NIKON_ZOOM100,NIKON_ZOOM100_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("ROLLEIFLEX 3.5 AUTOMAT MX","TLR 6×6 · Tessar/Xenar 75 mm · 5 FAQ",()->navigate(()->renderFaqPage("ROLLEIFLEX 3.5 AUTOMAT MX","Fonte: Rolleiflex 3.5 Automat MX - Manuale IT",Q_ROLLEI_35_MX,A_ROLLEI_35_MX,ROLLEI_35_MX_URL,"APRI MANUALE COMPLETO"))));
        body.addView(navCard("ROLLEIFLEX 2.8 E2","TLR 6×6 · Planar/Xenotar 80 mm · 5 FAQ",()->navigate(()->renderFaqPage("ROLLEIFLEX 2.8 E2","Fonte: Rolleiflex 2.8 E2 - Manuale IT",Q_ROLLEI_28_E2,A_ROLLEI_28_E2,ROLLEI_28_E2_URL,"APRI MANUALE COMPLETO"))));
    }
    private void renderMinolta(){ renderFaqPage("MINOLTA AUTO METER IIIF","Fonte: manuale originale Minolta completo · traduzione italiana",Q_MINOLTA,A_MINOLTA,MINOLTA_MANUAL_URL,"APRI MANUALE COMPLETO"); notice("Manuale completo tradotto in italiano con tavole, fotografie, diagrammi e pagine originali conservati."); }
    private void renderTechnique(){
        begin("TECNICA","Consultazione rapida durante il lavoro in camera oscura.");
        body.addView(navCard("PROVINI E CONTRASTO","Dal chiaro allo scuro",()->navigate(()->renderFaqPage("PROVINI E CONTRASTO","Principio guida approvato + pratica di camera oscura",Q_TESTSTRIP,A_TESTSTRIP,null,null))));
        body.addView(navCard("PROCESSO E LAVAGGIO","Provino a contatto · pre-bagno · lavaggio film e carta RC",()->navigate(()->renderFaqPage("PROCESSO E LAVAGGIO","Fonti operative: ILFORD PHOTO + manuali JOBO",Q_PROCESS_WASH,A_PROCESS_WASH,null,null))));
        body.addView(navCard("FILTRI E ACCESSORI ROLLEIFLEX","Corredi separati Rolleiflex 3.5 e 2.8",()->navigate(this::renderRolleiAccessories)));
        body.addView(navCard("SPLIT GRADE","Due esposizioni che interagiscono",()->navigate(()->renderFaqPage("SPLIT GRADE","Tecnica di stampa B/N",Q_SPLIT,A_SPLIT,null,null))));
        body.addView(navCard("SISTEMA ZONALE","Esposizione, sviluppo, previsualizzazione",()->navigate(()->renderFaqPage("SISTEMA ZONALE","Fonte: Ansel Adams - Bianco e Nero",Q_ZONE,A_ZONE,ZONE_URL,"APRI FONTE SU DRIVE"))));
        body.addView(navCard("STAMPA B/N","Dal negativo alla stampa finale",()->navigate(()->renderFaqPage("STAMPA B/N","Fonte: Stampa in Bianco e Nero - Camera Oscura",Q_PRINT,A_PRINT,PRINT_URL,"APRI FONTE SU DRIVE"))));
    }
    private void renderRolleiAccessories(){
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

    private void renderMaintenance(){
        begin("MANUTENZIONE","Procedure JOBO/LPL 7451 ricavate dal manuale italiano.");
        LinearLayout card=card(); card.addView(title("JOBO/LPL 7451",19)); card.addView(subtitle("Controlli meccanici e ottici documentati"));
        card.addView(section("CARRELLO E COLONNA","L’accoppiamento è regolato in fabbrica. Se compare gioco, il manuale prevede una regolazione fine dei dadi e delle viti del carrello: procedere per piccoli incrementi, facendo scorrere la testa e serrando i dadi solo quando il movimento è uniforme."));
        card.addView(section("VENTOLA","Tenerla sempre in funzione durante l’uso dell’ingranditore. Darkroom non effettua alcun comando automatico della ventola."));
        card.addView(section("CAMERA DI DIFFUSIONE","Controllare periodicamente il rivestimento interno: dopo molte ore può ingiallire. Per rimozione e sostituzione seguire la sequenza illustrata nel manuale, a macchina spenta e fredda."));
        card.addView(section("CALIBRAZIONE SCALA","Misura acquisita: indice scala 67, distanza piano negativo–base 73 cm, marginatore 6 mm. L’offset meccanico è 6,0 cm e la distanza negativo–carta è scala + 5,4 cm. Darkroom usa D = f × (β + 1/β + 2), con f in centimetri, e mostra scala LPL = D − 5,4. Il valore è un punto iniziale: completa sempre la messa a fuoco fine sul piano carta."));
        card.addView(section("MANOPOLE","Ciano, Magenta e Giallo: ricambio comune LPL 3281-282. Blocco colonna: ricambio distinto LPL 3481-257; una riparazione incollata è solo provvisoria. Prima di comprare un sostituto distingui alberino a D da 6,00 e 6,35 mm; preferisci, se c’è spazio, una manopola robusta da 30–35 mm con boccola metallica e grano sul lato piatto."));
        body.addView(card);
    }
    private void renderCookbook(){ begin("RICETTARIO","Nessun database aggiuntivo: il libro resta su Google Drive."); LinearLayout card=card(); card.addView(title("THE DARKROOM COOKBOOK",21)); card.addView(subtitle("Formule e preparazione della chimica fotografica")); card.addView(linkButton("APRI SU GOOGLE DRIVE",COOKBOOK_URL)); body.addView(card); }
    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||questions.length<1) throw new IllegalStateException("FAQ arrays invalid for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }

    private static final class FaqHit {
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
        addFaqMatches(hits,"APP DARKROOM",Q_DARKROOM,A_DARKROOM,q);
        addFaqMatches(hits,"JOBO/LPL 7451",Q_LPL7451,A_LPL7451,q); addFaqMatches(hits,"MEOPTA COLOR 3",Q_COLOR3,A_COLOR3,q); addFaqMatches(hits,"JOBO CPE2",Q_JOBO,A_JOBO,q); addFaqMatches(hits,"THERMAPHOT ACP200",Q_ACP,A_ACP,q); addFaqMatches(hits,"MINOLTA AUTO METER IIIF",Q_MINOLTA,A_MINOLTA,q);
        addFaqMatches(hits,"NIKON L35AF2",Q_NIKON_L35AF,A_NIKON_L35AF,q); addFaqMatches(hits,"NIKON F100",Q_NIKON_F100,A_NIKON_F100,q); addFaqMatches(hits,"NIKON ZOOM 100 AF",Q_NIKON_ZOOM100,A_NIKON_ZOOM100,q); addFaqMatches(hits,"ROLLEIFLEX 3.5 AUTOMAT MX",Q_ROLLEI_35_MX,A_ROLLEI_35_MX,q); addFaqMatches(hits,"ROLLEIFLEX 2.8 E2",Q_ROLLEI_28_E2,A_ROLLEI_28_E2,q);
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

    private void begin(String heading,String subheading){
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        body=new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(16),dp(14),dp(16),dp(28));
        scroll.addView(body,new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout top=new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView back=actionText(backStack.isEmpty()?"⌂":"←");
        back.setTextSize(25);
        back.setPadding(0,0,0,0);
        back.setGravity(Gravity.CENTER);
        back.setContentDescription(backStack.isEmpty()?"Torna alla Home":"Indietro");
        back.setOnClickListener(v->onBackPressed());
        top.addView(back,new LinearLayout.LayoutParams(dp(46),dp(46)));
        TextView h=title(heading,24);
        h.setGravity(Gravity.CENTER);
        top.addView(h,new LinearLayout.LayoutParams(0,dp(46),1f));
        View spacer=new View(this);
        top.addView(spacer,new LinearLayout.LayoutParams(dp(46),dp(46)));
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(46)));

        if(subheading!=null&&!subheading.isEmpty()){
            TextView sub=subtitle(subheading);
            sub.setGravity(Gravity.CENTER);
            body.addView(sub,margin(-1,-2,dp(8),dp(5),dp(8),dp(15)));
        } else {
            body.addView(new View(this),margin(1,1,0,0,0,dp(10)));
        }
        setContentView(scroll);
    }

    private LinearLayout navCard(String heading,String detail,Runnable action){ LinearLayout c=card(); c.setClickable(true); c.setFocusable(true); TextView h=title("›  "+heading,18); h.setTextColor(WARM); c.addView(h); c.addView(subtitle(detail)); c.setOnClickListener(v->action.run()); return c; }
    private LinearLayout faqCard(String question,String answerText){
        LinearLayout c=card();
        c.setPadding(dp(14),dp(8),dp(14),dp(8));
        TextView q=text("›  "+question,16,WARM,true);
        q.setPadding(0,dp(9),0,dp(9));
        if(EV_TABLE_QUESTION.equals(question)){
            LinearLayout a=evTableView();
            a.setVisibility(View.GONE);
            q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
            c.addView(q);
            c.addView(a);
            return c;
        }
        TextView a=text(answerText,14,Color.rgb(218,207,190),false);
        a.setLineSpacing(0f,1.12f);
        a.setPadding(dp(2),dp(4),dp(2),dp(12));
        a.setVisibility(View.GONE);
        q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
        c.addView(q);
        c.addView(a);
        return c;
    }

    private LinearLayout evTableView(){
        if(EV_TIMES.length!=EV_VALUES.length) throw new IllegalStateException("EV table row mismatch");
        LinearLayout answer=new LinearLayout(this);
        answer.setOrientation(LinearLayout.VERTICAL);
        answer.setPadding(dp(2),dp(3),dp(2),dp(12));

        TextView hint=text("VALORI EV · scorri i diaframmi  →",12,MUTED,true);
        hint.setPadding(0,0,0,dp(8));
        answer.addView(hint);

        LinearLayout table=new LinearLayout(this);
        table.setOrientation(LinearLayout.HORIZONTAL);
        table.setBaselineAligned(false);

        LinearLayout fixedColumn=new LinearLayout(this);
        fixedColumn.setOrientation(LinearLayout.VERTICAL);
        fixedColumn.addView(evCell("Tempo",88,42,true,false));
        for(int i=0;i<EV_TIMES.length;i++) fixedColumn.addView(evCell(EV_TIMES[i],88,40,false,(i&1)==1));
        table.addView(fixedColumn,new LinearLayout.LayoutParams(dp(88),ViewGroup.LayoutParams.WRAP_CONTENT));

        HorizontalScrollView apertureScroller=new HorizontalScrollView(this);
        apertureScroller.setFillViewport(false);
        apertureScroller.setHorizontalScrollBarEnabled(true);
        apertureScroller.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);

        LinearLayout movingGrid=new LinearLayout(this);
        movingGrid.setOrientation(LinearLayout.VERTICAL);
        movingGrid.addView(evRow(EV_APERTURES,true,false));
        for(int i=0;i<EV_VALUES.length;i++){
            if(EV_VALUES[i].length!=EV_APERTURES.length) throw new IllegalStateException("EV table column mismatch at row "+i);
            movingGrid.addView(evRow(EV_VALUES[i],false,(i&1)==1));
        }
        apertureScroller.addView(movingGrid,new ViewGroup.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        table.addView(apertureScroller,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        answer.addView(table,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView legend=text("★  Rolleiflex 2.8 E2\n●  Rolleiflex 3.5 Tessar MX\n\nGli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.",13,Color.rgb(218,207,190),false);
        legend.setLineSpacing(0f,1.15f);
        legend.setPadding(0,dp(11),0,0);
        answer.addView(legend);
        return answer;
    }

    private LinearLayout evRow(String[] values,boolean header,boolean alternate){
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        int height=header?42:40;
        for(String value:values) row.addView(evCell(value,60,height,header,alternate));
        return row;
    }

    private TextView evCell(String value,int widthDp,int heightDp,boolean header,boolean alternate){
        TextView cell=text(value,header?12:12,header?Color.rgb(241,220,187):WARM,header);
        cell.setGravity(Gravity.CENTER);
        cell.setPadding(dp(4),0,dp(4),0);
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(header?Color.rgb(53,42,30):(alternate?Color.rgb(31,31,31):Color.rgb(23,23,23)));
        bg.setStroke(dp(1),Color.rgb(75,70,63));
        cell.setBackground(bg);
        cell.setLayoutParams(new LinearLayout.LayoutParams(dp(widthDp),dp(heightDp)));
        return cell;
    }
    private LinearLayout card(){ LinearLayout c=new LinearLayout(this); c.setOrientation(LinearLayout.VERTICAL); c.setPadding(dp(15),dp(13),dp(15),dp(13)); GradientDrawable bg=new GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(10)); bg.setStroke(dp(1),Color.rgb(67,67,67)); c.setBackground(bg); c.setElevation(dp(1)); c.setLayoutParams(margin(-1,-2,0,0,0,dp(10))); return c; }
    private TextView title(String value,int sp){ return text(value,sp,WARM,true); }
    private TextView subtitle(String value){ TextView v=text(value,13,MUTED,false); v.setLineSpacing(0f,1.08f); return v; }
    private TextView section(String label,String value){ TextView v=text(label+"\n"+value,14,Color.rgb(220,207,187),false); v.setLineSpacing(0f,1.15f); v.setPadding(0,dp(9),0,dp(5)); return v; }
    private void notice(String value){ TextView v=text(value,13,Color.rgb(225,194,151),false); GradientDrawable bg=new GradientDrawable(); bg.setColor(Color.rgb(38,28,20)); bg.setStroke(dp(1),BRONZE); bg.setCornerRadius(dp(10)); v.setBackground(bg); v.setPadding(dp(12),dp(10),dp(12),dp(10)); body.addView(v,margin(-1,-2,0,dp(2),0,dp(10))); }
    private TextView linkButton(String label,String url){ TextView v=actionText(label); v.setGravity(Gravity.CENTER); v.setTextColor(Color.rgb(237,219,187)); GradientDrawable bg=new GradientDrawable(); bg.setColor(RED); bg.setCornerRadius(dp(9)); bg.setStroke(dp(1),BRONZE); v.setBackground(bg); v.setOnClickListener(view->openUrl(url)); v.setLayoutParams(margin(-1,dp(48),0,dp(8),0,dp(12))); return v; }
    private TextView actionText(String label){ TextView v=text(label,13,Color.rgb(217,195,164),true); v.setGravity(Gravity.CENTER_VERTICAL); v.setPadding(dp(12),0,dp(12),0); return v; }
    private TextView text(String value,int sp,int color,boolean bold){ TextView v=new TextView(this); v.setText(value); v.setTextColor(color); v.setTextSize(sp); v.setTypeface(Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL); v.setIncludeFontPadding(false); return v; }
    private void openUrl(String url){ try{ startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url))); }catch(ActivityNotFoundException e){ Toast.makeText(this,"Nessuna app disponibile per aprire il collegamento.",Toast.LENGTH_LONG).show(); } }
    private int dp(int v){ return Math.round(v*getResources().getDisplayMetrics().density); }
    private LinearLayout.LayoutParams margin(int w,int h,int l,int t,int r,int b){ LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h); p.setMargins(dp(l),dp(t),dp(r),dp(b)); return p; }
}
