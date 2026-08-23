#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.2: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')


def append_array_item(src: str, array_name: str, item: str) -> str:
    marker = f'    private static final String[] {array_name} = {{'
    start = src.find(marker)
    if start < 0:
        raise SystemExit(f'v0.4.2: array not found: {array_name}')
    end = src.find('    };', start)
    if end < 0:
        raise SystemExit(f'v0.4.2: array end not found: {array_name}')
    body = src[start:end].rstrip()
    if not body.endswith('"'):
        raise SystemExit(f'v0.4.2: unexpected array tail: {array_name}')
    body += ',\n            "' + item.replace('\\', '\\\\').replace('"', '\\"') + '"\n'
    return src[:start] + body + src[end:]

# 1) Meopta Color 3: add full lamp replacement FAQ.
s = append_array_item(
    s,
    'Q_COLOR3',
    'Come si sostituisce correttamente la lampada della Meopta Color 3?'
)
s = append_array_item(
    s,
    'A_COLOR3',
    'Scollega la testa dal trasformatore e lasciala raffreddare. La lampada prevista è una alogena a riflettore 12 V / 100 W; il manuale indica Tungsram 55 220, Osram 64 627, Philips 68 34 o Thorn A1/231, con attacco GZ 6.35-18 o equivalente del modello indicato. Svita le due viti del supporto, estrai il portalampada, libera la lampada dalle molle elastiche e scollegala dallo zoccolo sui fili. Inserisci la nuova lampada nello zoccolo e nelle molle facendo coincidere la spalla del riflettore con l’incavo del supporto metallico; verifica i contatti, reinserisci il supporto e serra le due viti. Non toccare con le dita il bulbo né la superficie specchiante interna del riflettore: usa un panno pulito e asciutto. Alla prima sostituzione possono essere presenti dispositivi di sicurezza da trasporto sulle molle fermalampada: vanno rimossi e non rimontati per l’uso normale.'
)

# 2) New technique page with four operational FAQs.
process_block = r'''    private static final String[] Q_PROCESS_WASH = {
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

'''
marker = '    private static final String[] Q_TESTSTRIP = {\n'
if marker not in s:
    raise SystemExit('v0.4.2: Q_TESTSTRIP insertion marker missing')
s = s.replace(marker, process_block + marker, 1)

# 3) Add the new card under TECNICA.
provino_card = '        body.addView(navCard("PROVINI E CONTRASTO","Dal chiaro allo scuro",()->navigate(()->renderFaqPage("PROVINI E CONTRASTO","Principio guida approvato + pratica di camera oscura",Q_TESTSTRIP,A_TESTSTRIP,null,null))));\n'
process_card = '        body.addView(navCard("PROCESSO E LAVAGGIO","Provino a contatto · pre-bagno · lavaggio film e carta RC",()->navigate(()->renderFaqPage("PROCESSO E LAVAGGIO","Fonti operative: ILFORD PHOTO + manuali JOBO",Q_PROCESS_WASH,A_PROCESS_WASH,null,null))));\n'
if provino_card not in s:
    raise SystemExit('v0.4.2: technique card marker missing')
s = s.replace(provino_card, provino_card + process_card, 1)

# 4) FAQ pages now legitimately have 4, 5, 10 or 11 entries.
old_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||(questions.length!=5&&questions.length!=10)) throw new IllegalStateException("FAQ count must be 5 or 10 for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
new_helper = '    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel){ if(questions.length!=answers.length||(questions.length!=4&&questions.length!=5&&questions.length!=10&&questions.length!=11)) throw new IllegalStateException("FAQ count must be 4, 5, 10 or 11 for "+heading); begin(heading,source); for(int i=0;i<questions.length;i++) body.addView(faqCard(questions[i],answers[i])); if(url!=null&&urlLabel!=null) body.addView(linkButton(urlLabel,url)); }\n'
if old_helper not in s:
    raise SystemExit('v0.4.2: FAQ helper marker missing')
s = s.replace(old_helper, new_helper, 1)

p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
required = [
    'Come si sostituisce correttamente la lampada della Meopta Color 3?',
    'Tungsram 55 220', 'Osram 64 627', 'Philips 68 34', 'Thorn A1/231', 'GZ 6.35-18',
    'Q_PROCESS_WASH', 'A_PROCESS_WASH', 'PROCESSO E LAVAGGIO',
    'Come realizzare un provino a contatto?',
    'Quando è utile un pre-bagno della pellicola prima dello sviluppo?',
    'Come lavare correttamente la pellicola?',
    'Come lavare correttamente la carta RC?',
    'non farlo girare nel processore', 'contenitore separato', '5 inversioni', '10 inversioni', '20 inversioni',
    'FAQ count must be 4, 5, 10 or 11 for '
]
for x in required:
    if x not in out:
        raise SystemExit('v0.4.2 guard missing: ' + x)

# Count new blocks and Color 3 expansion.
def count_entries(text, qname, next_name):
    a=text.index('private static final String[] '+qname)
    b=text.index('private static final String[] '+next_name, a)
    return text[a:b].count('            "')

if count_entries(out, 'Q_COLOR3', 'A_COLOR3') != 11:
    raise SystemExit('v0.4.2 Color3 question count != 11')
if count_entries(out, 'A_COLOR3', 'Q_JOBO') != 11:
    raise SystemExit('v0.4.2 Color3 answer count != 11')
if count_entries(out, 'Q_PROCESS_WASH', 'A_PROCESS_WASH') != 4:
    raise SystemExit('v0.4.2 process question count != 4')
if count_entries(out, 'A_PROCESS_WASH', 'Q_TESTSTRIP') != 4:
    raise SystemExit('v0.4.2 process answer count != 4')

print('Darkroom v0.4.2 technique FAQ patch ready')
