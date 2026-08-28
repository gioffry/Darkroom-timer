#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.5: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

TABLE_Q = 'Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?'
MINOLTA_ZONE_Q = 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?'
ZONE_FIELD_Q = 'Come utilizzo rapidamente il Sistema Zonale sul campo?'

TABLE_A = '''| Tempo | f/2,8 | f/3,5 | f/4 | f/5,6 | f/8 | f/11 | f/16 | f/22 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 s ★● | EV 3,0 | EV 3,6 | EV 4,0 | EV 5,0 | EV 6,0 | EV 6,9 | EV 8,0 | EV 8,9 |
| 1/2 ★● | 4,0 | 4,6 | 5,0 | 6,0 | 7,0 | 7,9 | 9,0 | 9,9 |
| 1/4 ★ | 5,0 | — | 6,0 | 7,0 | 8,0 | 8,9 | 10,0 | 10,9 |
| 1/5 ● | — | 5,9 | 6,3 | 7,3 | 8,3 | 9,2 | 10,3 | 11,2 |
| 1/8 ★ | 6,0 | — | 7,0 | 8,0 | 9,0 | 9,9 | 11,0 | 11,9 |
| 1/10 ● | — | 6,9 | 7,3 | 8,3 | 9,3 | 10,2 | 11,3 | 12,2 |
| 1/15 ★ | 6,9 | — | 7,9 | 8,9 | 9,9 | 10,8 | 11,9 | 12,8 |
| 1/25 ● | — | 8,3 | 8,6 | 9,6 | 10,6 | 11,6 | 12,6 | 13,6 |
| 1/30 ★ | 7,9 | — | 8,9 | 9,9 | 10,9 | 11,8 | 12,9 | 13,8 |
| 1/50 ● | — | 9,3 | 9,6 | 10,6 | 11,6 | 12,6 | 13,6 | 14,6 |
| 1/60 ★ | 8,9 | — | 9,9 | 10,9 | 11,9 | 12,8 | 13,9 | 14,8 |
| 1/100 ● | — | 10,3 | 10,6 | 11,6 | 12,6 | 13,6 | 14,6 | 15,6 |
| 1/125 ★ | 9,9 | — | 11,0 | 11,9 | 13,0 | 13,9 | 15,0 | 15,9 |
| 1/250 ★● | 10,9 | 11,6 | 12,0 | 12,9 | 14,0 | 14,9 | 16,0 | 16,9 |
| 1/500 ★● | 11,9 | 12,6 | 13,0 | 13,9 | 15,0 | 15,9 | 17,0 | 17,9 |

★ = Rolleiflex 2.8 E2
● = Rolleiflex 3.5 Tessar MX

Gli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.'''

MINOLTA_ZONE_A = '''Il Minolta Auto Meter III F può essere usato molto comodamente con il Sistema Zonale, soprattutto con il mirino 10° per la misura riflessa.

1. Misura il contrasto della scena

Imposta:

- gli ISO reali della pellicola;
- modalità AMBI;
- visualizzazione EV.

Misura prima l’ultima ombra nella quale vuoi ancora conservare dettaglio, poi l’ultima luce nella quale vuoi ancora conservare dettaglio.

Calcola:

EV luce − EV ombra = intervallo della scena in stop

Esempio:

- ombra: EV 5
- luce: EV 10
- differenza: 5 EV = 5 stop

Se deciderai di collocare l’ombra in Zona III, la luce cadrà quindi in Zona VIII.

Indicativamente:

- 4–5 EV → scena con gamma tonale normale e facilmente gestibile;
- meno di 4 EV → scena tendenzialmente piatta;
- più di 5 EV → scena progressivamente più contrastata.

2. Determina l’esposizione

Passa alla visualizzazione FNo..

Mantieni impostati gli ISO reali della pellicola e scegli sul Minolta il tempo che vuoi utilizzare.

Misura nuovamente l’ombra con dettaglio.

Il diaframma indicato dall’esposimetro collocherebbe quella superficie in Zona V.

Per collocarla invece in Zona III devi togliere 2 stop di esposizione.

Puoi farlo come preferisci:

- chiudendo il diaframma di 2 stop;
- accorciando il tempo di 2 stop;
- dividendo i 2 stop fra tempo e diaframma.

Esempio:

il Minolta indica 1/125 s – f/4.

Per mettere quell’ombra in Zona III puoi usare, per esempio:

- 1/125 s – f/8
- 1/500 s – f/4
- 1/250 s – f/5,6

Le tre combinazioni danno la stessa esposizione.

In breve

EV serve per valutare il contrasto della scena.

Tempo e diaframma servono per impostare concretamente l’esposizione sulla macchina fotografica.

Per collocare in Zona III un’ombra misurata normalmente dall’esposimetro:

togli sempre 2 stop rispetto alla lettura fornita dal Minolta.'''

ZONE_FIELD_A = '''Misura l’ultima ombra nella quale vuoi ancora conservare dettaglio; oltre quella accetti quasi nero e nero.

L’esposimetro, se ne segui direttamente la lettura, collocherebbe quella superficie in Zona V.

Tu vuoi invece collocarla in Zona III, quindi devi dare 2 stop meno di esposizione.

Se ragioni in EV:

EV misurato + 2 = EV di esposizione

Ricorda però che questo non significa obbligatoriamente lavorare con gli EV sulla macchina: i 2 stop possono essere tolti indifferentemente con diaframma, tempo oppure una combinazione dei due.

Esempio:

lettura dell’ombra:

1/125 s – f/4

Possibili esposizioni per collocarla in Zona III:

1/125 – f/8 oppure 1/500 – f/4 oppure 1/250 – f/5,6

Poi misura l’ultima luce nella quale vuoi ancora conservare dettaglio.

Per valutare il contrasto della scena usa gli EV:

EV luce − EV ombra = differenza in stop

Esempio:

- ombra EV 5
- luce EV 10
- differenza = 5 EV

Avendo collocato l’ombra in Zona III:

Zona III + 5 = Zona VIII

Quindi le ombre importanti cadono in Zona III e le alte luci importanti in Zona VIII.

Indicativamente:

- 4–5 EV di differenza → gamma tonale normale e ben gestibile;
- meno di 4 EV → scena tendenzialmente piatta;
- più di 5 EV → scena progressivamente più contrastata.

Regola da ricordare

Misura l’ombra con dettaglio → togli 2 stop → scatta.

EV luce − EV ombra → ti dice quanto è contrastata la scena.'''


def j(text: str) -> str:
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '').replace('\n', '\\n') + '"'


def prepend_items(src: str, array_name: str, items):
    marker = f'    private static final String[] {array_name} = {{\n'
    if marker not in src:
        raise SystemExit('v0.4.5 array marker missing: ' + array_name)
    ins = ''.join('            ' + j(x) + ',\n' for x in items)
    return src.replace(marker, marker + ins, 1)

# Minolta: EV table MUST be the first FAQ, then the new Minolta-specific Zone System FAQ.
s = prepend_items(s, 'Q_MINOLTA', [TABLE_Q, MINOLTA_ZONE_Q])
s = prepend_items(s, 'A_MINOLTA', [TABLE_A, MINOLTA_ZONE_A])

# Zone System: add the requested quick field workflow as the first FAQ.
s = prepend_items(s, 'Q_ZONE', [ZONE_FIELD_Q])
s = prepend_items(s, 'A_ZONE', [ZONE_FIELD_A])

# Render the EV table as a horizontally scrollable monospace table while preserving
# the normal collapsible FAQ behaviour everywhere else (including global search).
imp = 'import android.widget.LinearLayout;\n'
if 'import android.widget.HorizontalScrollView;' not in s:
    if imp not in s:
        raise SystemExit('v0.4.5 HorizontalScrollView import marker missing')
    s = s.replace(imp, imp + 'import android.widget.HorizontalScrollView;\n', 1)

old_faq = '''    private LinearLayout faqCard(String question,String answerText){ LinearLayout c=card(); c.setPadding(dp(14),dp(8),dp(14),dp(8)); TextView q=text("›  "+question,16,WARM,true); q.setPadding(0,dp(9),0,dp(9)); TextView a=text(answerText,14,Color.rgb(218,207,190),false); a.setLineSpacing(0f,1.12f); a.setPadding(dp(2),dp(4),dp(2),dp(12)); a.setVisibility(View.GONE); q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); }); c.addView(q); c.addView(a); return c; }'''
new_faq = '''    private LinearLayout faqCard(String question,String answerText){ LinearLayout c=card(); c.setPadding(dp(14),dp(8),dp(14),dp(8)); TextView q=text("›  "+question,16,WARM,true); q.setPadding(0,dp(9),0,dp(9)); if("''' + TABLE_Q + '''".equals(question)){ TextView a=text(answerText,11,Color.rgb(218,207,190),false); a.setTypeface(Typeface.MONOSPACE); a.setLineSpacing(0f,1.15f); a.setPadding(dp(2),dp(4),dp(8),dp(12)); a.setHorizontallyScrolling(true); a.setTextIsSelectable(true); HorizontalScrollView hs=new HorizontalScrollView(this); hs.setFillViewport(false); hs.setHorizontalScrollBarEnabled(true); hs.addView(a); hs.setVisibility(View.GONE); q.setOnClickListener(v->{ boolean open=hs.getVisibility()==View.VISIBLE; hs.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); }); c.addView(q); c.addView(hs); return c; } TextView a=text(answerText,14,Color.rgb(218,207,190),false); a.setLineSpacing(0f,1.12f); a.setPadding(dp(2),dp(4),dp(2),dp(12)); a.setVisibility(View.GONE); q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); }); c.addView(q); c.addView(a); return c; }'''
if old_faq not in s:
    raise SystemExit('v0.4.5 faqCard marker missing')
s = s.replace(old_faq, new_faq, 1)

p.write_text(s, encoding='utf-8')
out = p.read_text(encoding='utf-8')

for marker in [
    TABLE_Q, '1/500 ★●', 'Gli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.',
    MINOLTA_ZONE_Q, 'Passa alla visualizzazione FNo..', 'togli sempre 2 stop rispetto alla lettura fornita dal Minolta.',
    ZONE_FIELD_Q, 'EV misurato + 2 = EV di esposizione', 'Zona III + 5 = Zona VIII',
    'Misura l’ombra con dettaglio → togli 2 stop → scatta.', 'HorizontalScrollView', 'Typeface.MONOSPACE'
]:
    if marker not in out:
        raise SystemExit('v0.4.5 guard missing: ' + marker)

# Order and counts: Minolta table first, Minolta Zone second; Zone quick guide first.
q_min_start = out.index('private static final String[] Q_MINOLTA')
q_min_end = out.index('private static final String[] A_MINOLTA', q_min_start)
q_min = out[q_min_start:q_min_end]
if q_min.find(TABLE_Q) > q_min.find(MINOLTA_ZONE_Q):
    raise SystemExit('v0.4.5 Minolta order invalid')
if q_min.count('            "') != 12:
    raise SystemExit('v0.4.5 Minolta question count != 12')
a_min_start = q_min_end
a_min_end = out.index('private static final String[] Q_PROCESS_WASH', a_min_start) if 'private static final String[] Q_PROCESS_WASH' in out[a_min_start:] else out.index('private static final String[] Q_TESTSTRIP', a_min_start)
a_min = out[a_min_start:a_min_end]
if a_min.count('            "') != 12:
    raise SystemExit('v0.4.5 Minolta answer count != 12')
qz_start = out.index('private static final String[] Q_ZONE')
qz_end = out.index('private static final String[] A_ZONE', qz_start)
if out[qz_start:qz_end].count('            "') != 11:
    raise SystemExit('v0.4.5 Zone question count != 11')
az_start = qz_end
az_end = out.index('private static final String[] Q_PRINT', az_start)
if out[az_start:az_end].count('            "') != 11:
    raise SystemExit('v0.4.5 Zone answer count != 11')

print('Darkroom v0.4.5 Zone + Minolta EV FAQs patch ready')
