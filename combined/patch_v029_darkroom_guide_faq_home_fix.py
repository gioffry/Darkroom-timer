#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
home = root / 'src/main/java/it/darkroom/timer/home/HomeActivity.java'
maintenance = root / 'src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java'

for p in (home, maintenance):
    if not p.exists():
        raise SystemExit('v0.2.9 generated file missing: ' + str(p))


def replace_once(path, old, new, label):
    s = path.read_text(encoding='utf-8')
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'v0.2.9 {label}: expected exactly 1 marker, found {n}')
    path.write_text(s.replace(old, new, 1), encoding='utf-8')
    print('v0.2.9 OK', label, flush=True)


# -----------------------------------------------------------------------------
# 1. HOME micro-fix: the long SVILUPPO PELLICOLA label must never run into the
#    right chevron. Keep every other primary card visually unchanged.
# -----------------------------------------------------------------------------
replace_once(
    home,
    '            TextView name = label(text, secondary ? 15 : 20, IVORY, true, true);\n',
    '            float nameSize = secondary ? 15f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f);\n'
    '            TextView name = label(text, nameSize, IVORY, true, true);\n',
    'Home film label fit'
)

# -----------------------------------------------------------------------------
# 2. DARKROOM guide + ten operational FAQs inside USO E MANUTENZIONE.
#    The complete PDF remains on the user's Google Drive and is opened through
#    the same external-link mechanism already used by the manuals.
# -----------------------------------------------------------------------------
guide_url_marker = '    private static final String COOKBOOK_URL = "https://drive.google.com/file/d/1LfXqGW4t9vamylwurIbPNqJoIsd_4UwR/view";\n'
replace_once(
    maintenance,
    guide_url_marker,
    guide_url_marker + '    private static final String DARKROOM_GUIDE_URL = "https://drive.google.com/file/d/1_40jRUpA5Qxwr9a_n6PiT3V19SqZijQ2/view?usp=drivesdk";\n',
    'Darkroom guide URL'
)

faq_block = r'''    private static final String[] Q_DARKROOM = {
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

'''
replace_once(
    maintenance,
    '    private static final String[] Q_OPEMUS = {\n',
    faq_block + '    private static final String[] Q_OPEMUS = {\n',
    'Darkroom FAQ arrays'
)

root_card = '        body.addView(navCard("MANUALI","Apparecchi e FAQ ricavate dai manuali",()->navigate(this::renderManuals)));\n'
replace_once(
    maintenance,
    root_card,
    '        body.addView(navCard("APP DARKROOM","Guida completa v0.2.8 e 10 FAQ operative",()->navigate(this::renderDarkroom)));\n' + root_card,
    'Darkroom root card'
)

render_darkroom = r'''    private void renderDarkroom(){
        renderFaqPage("APP DARKROOM","Uso operativo di Darkroom · guida completa v0.2.8",Q_DARKROOM,A_DARKROOM,DARKROOM_GUIDE_URL,"APRI GUIDA COMPLETA PDF");
        notice("La v0.2.9 aggiunge queste FAQ e una correzione grafica alla Home; il funzionamento operativo documentato nella guida v0.2.8 resta invariato.");
    }
'''
replace_once(
    maintenance,
    '    private void renderManuals(){\n',
    render_darkroom + '    private void renderManuals(){\n',
    'Darkroom FAQ page'
)

# Guards: fail the build rather than silently shipping a partial update.
hs = home.read_text(encoding='utf-8')
ms = maintenance.read_text(encoding='utf-8')
for marker in [
    '"SVILUPPO PELLICOLA".equals(text) ? 18f : 20f',
    'TextView name = label(text, nameSize, IVORY, true, true);',
    'HomeCard film = new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false);',
]:
    if marker not in hs:
        raise SystemExit('v0.2.9 Home guard failed: ' + marker)

for marker in [
    'DARKROOM_GUIDE_URL', 'Q_DARKROOM', 'A_DARKROOM', 'APP DARKROOM',
    'APRI GUIDA COMPLETA PDF', 'Guida completa v0.2.8 e 10 FAQ operative',
    'Ho premuto ARMA ma l’ingranditore non parte. È un errore?',
    'Come faccio a non perdere LOG e ricette?'
]:
    if marker not in ms:
        raise SystemExit('v0.2.9 maintenance guard failed: ' + marker)

print('Darkroom v0.2.9 guide + FAQ + Home micro-fix patch ready')
