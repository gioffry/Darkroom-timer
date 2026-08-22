#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sqlite3, sys

DB = Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')

def fp(table):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'PRAGMA table_info({table})')]
    order=','.join('"'+c+'"' for c in cols)
    for row in cur.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode()); h.update(b'\n')
    return h.hexdigest()
before={t:fp(t) for t in PROTECTED}

P={
'510 pyro':'Preparare una soluzione di lavoro monouso dal concentrato. La diluizione standard è 1+100; per maggiore economia e tempi di sviluppo più lunghi sono possibili diluizioni fino a circa 1+500.',
'acu 1':'Preparare lo stock sciogliendo l’intero contenuto della confezione in un quarto di gallone d’acqua a 70–90 °F (circa 21–32 °C). Diluire poi lo stock 1+10 oppure 1+5 secondo la tabella del produttore per la pellicola.',
'acufine':'Sciogliere l’intera confezione in acqua a 70–90 °F (circa 21–32 °C); non preparare quantità parziali della confezione. Se l’acqua è molto mineralizzata o alcalina è raccomandata acqua distillata.',
'acurol n':'Diluire il concentrato con acqua in funzione della pellicola e del risultato desiderato. SPUR documenta un ampio intervallo, comunemente da 1+50 a 1+200.',
'adotech iv':'Diluire il concentrato 1+14 con acqua per l’uso con ADOX CMS 20 II.',
'ars imago fd':'Diluire il concentrato liquido immediatamente prima dell’uso. La diluizione standard è 1+39; la scheda del produttore indica circa da 1+19 a 1+59 secondo pellicola e risultato desiderato.',
'ars imago fe':'Preparare con acqua corrente. Il produttore indica 1+1 per una soluzione di lavoro riutilizzabile e 1+3 per una soluzione monouso.',
'ars imago monobath':'Mescolare 135 ml di concentrato con 165 ml d’acqua per ottenere 300 ml di soluzione di lavoro.',
'atomal 49':'Il kit in polvere prepara una soluzione stock ed è disponibile in confezioni per 1 litro o 5 litri.',
'bellini df2 duo step':'Sistema a due componenti A/B. Per il reintegro di ciascun bagno, ricostituire 1 litro con 500 ml di soluzione di tank già condizionata + 250 ml di concentrato fresco + 250 ml d’acqua; diluizione raccomandata 1+1.',
'bellini hydrofen':'Per il trattamento amatoriale diluire il concentrato 1+15 oppure 1+31 con acqua; la confezione professionale documenta 1+15.',
'bergger superfine':'Agitare bene il concentrato e preparare la soluzione di lavoro 1+4 immediatamente prima dell’uso.',
'berspeed':'Sciogliere la polvere in acqua demineralizzata per preparare la soluzione stock; quando è richiesta una diluizione, preparare la soluzione di lavoro diluita subito prima dell’uso.',
'cinestill df96 monobath':'La versione in polvere va preparata fino a 1 litro seguendo le istruzioni della confezione; la versione liquida pronta all’uso non richiede diluizione.',
'd 76':'Preparare l’intera quantità di polvere della confezione secondo le istruzioni del prodotto. Kodak non raccomanda di suddividere la confezione per preparare volumi inferiori.',
'dektol':'Preparare l’intera confezione fino al volume di stock indicato. Per l’uso in bacinella diluire 1 parte di stock con 2 parti d’acqua (1+2). Kodak non raccomanda di dividere le confezioni in polvere.',
'diafine':'Preparare separatamente le due polveri come Soluzione A e Soluzione B. Sciogliere A in acqua a 75–85 °F (circa 24–29 °C) fino al volume indicato e preparare lo stesso volume di B; mantenere le due soluzioni separate e chiaramente etichettate.',
'eco pro':'Sciogliere in acqua a temperatura ambiente. La Parte A deve essere completamente sciolta prima di aggiungere la Parte B. Preparare 5 litri e conservare la soluzione miscelata a piena concentrazione.',
'ecoprint universal':'Per carta usare 1+7: per esempio, 1 litro di soluzione di lavoro richiede 125 ml di concentrato + 875 ml d’acqua. Per pellicola usare 1+12: per esempio, 260 ml richiedono 20 ml di concentrato + 240 ml d’acqua.',
'f76+':'Rivelatore a diluizione variabile. Intervallo normale da 1+3 a 1+14; 1+19 può essere usato per trattamenti push. Per macchine automatiche con reintegro, preparare circa 1+4–1+5.',
'fx 39':'La diluizione standard monouso è 1+9. Sono documentate anche diluizioni maggiori, come 1+14 e 1+19, per una compensazione più marcata.',
'finol':'Preparare la soluzione di lavoro a due componenti immediatamente prima dell’uso. Diluizione standard 1+1+100; sono documentate alternative da 1+1+50 a 1+1+150. Usare preferibilmente acqua distillata o demineralizzata.',
'hc 110':'Soluzione stock: 1 parte di concentrato + 3 parti d’acqua. Le soluzioni di lavoro possono essere preparate dallo stock oppure direttamente dal concentrato.',
'ilfotec dd':'Diluire ILFOTEC DD Developer 1+4 e usare con ILFOTEC DD Starter seguendo le istruzioni del processo con reintegro.',
'ilfotec rt rapid':'Il reintegratore standard è 1 parte A + 1 parte B + 2 parti d’acqua; è documentata anche la variante 1+1+5. Aggiungere ILFOTEC RT RAPID Starter per trasformare il reintegratore in rivelatore alla concentrazione di lavoro.',
'mzb':'Preparare il kit in polvere come due soluzioni stock separate A e B, ciascuna da 2 litri. Portare entrambe alla temperatura di processo prima dell’uso. Per rotazione Moersch indica 1+1 per entrambe; è possibile anche miscelare A e B in un unico bagno quando non serve la compensazione del contrasto.',
'microdol x':'Usare la soluzione stock preparata a piena concentrazione oppure diluire lo stock 1+3 immediatamente prima del trattamento. Kodak indica di preparare 1+3 subito prima dell’uso e smaltirla dopo quel lotto.',
'moersch eco':'Per la maggior parte delle pellicole preparare rivelatore A + attivatore B + acqua demineralizzata in rapporto 2+1+50; consultare la tabella del produttore per eventuali eccezioni.',
'nucleol bf200':'I due componenti liquidi A e B vengono combinati secondo le istruzioni di sviluppo del prodotto. Bellini identifica il kit come sistema rivelatore alla pirocatechina A+B da 100 ml.',
'pmk':'Mescolare Soluzione A e Soluzione B con acqua; la diluizione di lavoro standard è 1+2+100.',
'promicrol':'Per trattamento manuale o in macchina con reintegro diluire 1+9. Per uso monouso manuale o in macchina diluire 1+14. Il reintegratore si prepara diluendo il concentrato 1+4.',
'rollei supergrain':'Diluire il concentrato con acqua secondo la scheda Rollei. Per 260 ml di soluzione: 1+9 = 26 ml concentrato + 234 ml acqua; 1+12 = 20 ml + 240 ml; 1+15 = circa 16,25 ml + 243,75 ml.',
'silberra aphenol':'Sciogliere in sequenza le buste 1, 2 e 3 in 750 ml di acqua distillata a 55–60 °C; portare poi a 1 litro e raffreddare a temperatura ambiente.',
'silberra ascorol':'Per pellicola diluire il concentrato 1+29 in acqua distillata; per effetti specifici si possono usare 1+19 oppure 1+49.',
'silberra micro f':'Sciogliere la busta 1 e poi la busta 2 in 700–800 ml di acqua distillata a 55–60 °C; portare a 1 litro, raffreddare e attendere 3–4 ore prima dell’uso.',
'silberra microl':'Diluire il concentrato 1+24 con acqua distillata immediatamente prima del trattamento.',
'silberra pyro hd':'Mescolare 1 parte B con 1 parte A, poi diluire con 100 parti di acqua distillata per lo sviluppo standard in tank; per sviluppo stand può essere usato 1:1:200.',
'silberra s 76':'Sciogliere la busta 1 e poi la busta 2 in 750 ml d’acqua a 48–50 °C; portare a 1 litro e raffreddare a 20–22 °C.',
'silvermax':'Diluizione standard 1+29; per esempio 10 ml di concentrato + 290 ml d’acqua producono 300 ml di soluzione di lavoro.',
'sprint standard':'Diluire il concentrato 1+9 con acqua per preparare la soluzione di lavoro.',
'spur dokuspeed sl n':'Preparare la soluzione di lavoro con Parti A e B e acqua distillata. Esempio per 250 ml: 10 ml Parte A + 5 ml Parte B e portare a 250 ml; le quantità esatte A/B variano secondo pellicola e formato nella tabella SPUR.',
'spur hrx':'Mescolare le Parti A e B in quantità uguali e diluire con acqua secondo la tabella specifica della pellicola.',
'spur nanotech ur':'Preparare il rivelatore di lavoro monocomponente con acqua distillata/deionizzata alla diluizione e temperatura di riempimento indicate nella tabella SPUR per la pellicola. Non è necessario il prelavaggio.',
'spur omega x':'Mescolare le Parti A e B in quantità uguali per formare la soluzione di lavoro, poi diluire secondo la tabella.',
'spur sd 2525':'Le Parti A e B formano la soluzione di lavoro secondo la diluizione indicata nella tabella di sviluppo; non è un processo a due bagni.',
'spur shadowmax':'La diluizione della Parte A è indicata dalla tabella; la Parte B viene aggiunta in uno dei quattro rapporti previsti secondo la sensibilità obiettivo della pellicola.',
'spur sld':'Preparare la soluzione di lavoro con acqua distillata alla diluizione e temperatura specifiche della pellicola indicate nella tabella SPUR SLD.',
'spur speed major':'Preparare la soluzione di lavoro con acqua distillata usando diluizione, temperatura di riempimento e agitazione specifiche della pellicola indicate nella tabella SPUR Speed-Major.',
'spur trx 2000':'Preparare la soluzione di lavoro con acqua distillata alla diluizione e temperatura di riempimento specifiche della pellicola indicate nella tabella SPUR TRX 2000; con acqua più dura sono necessari tempi di sviluppo più lunghi.',
'spur ufp':'Diluire il concentrato secondo la tabella di sviluppo della pellicola; per carta la diluizione standard è 1+20.',
'tmax rs':'Preparare la soluzione alla concentrazione di lavoro secondo il formato della confezione. Kodak indica che T-MAX RS Developer and Replenisher produce una soluzione di lavoro utilizzata anche come reintegratore.',
'tanol':'Diluire rivelatore e alcali 1+1+100 con acqua demineralizzata immediatamente prima dello sviluppo.',
'tanol speed':'Diluizione di lavoro standard 1+1+100; usare acqua demineralizzata e preparare la soluzione poco prima dello sviluppo.',
'ultrafin t plus':'Diluire il concentrato 1+4. Il produttore consente di prelevare e miscelare solo la quantità necessaria di concentrato liquido.',
'xt 3':'Preparare la soluzione stock dai componenti in polvere; lasciare raffreddare la soluzione appena preparata prima dell’uso.',
'xtol':'Iniziare con circa il 75% del volume finale d’acqua a 18–30 °C; sciogliere completamente la Parte A, quindi la Parte B, poi portare al volume finale.',
}

for dn,text in P.items():
    cur.execute('UPDATE developer_profiles SET preparation_it=?,translation_status=? WHERE developer_norm=?',(text,'v035_strict_it_complete_prep',dn))

# v0.3.5 core override products were already populated by the previous pass.
raw_count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation,'')<>''").fetchone()[0]
it_count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''").fetchone()[0]
if raw_count!=79 or it_count!=79:
    missing=cur.execute("SELECT developer_norm,developer_name FROM developer_profiles WHERE COALESCE(preparation,'')<>'' AND COALESCE(preparation_it,'')='' ORDER BY developer_name").fetchall()
    raise SystemExit(f'Italian preparation coverage mismatch raw={raw_count} it={it_count} missing={missing}')

bad=re.compile(r'\b(the|and|with|when|should|stored|working solution|original package|minimum|defines|processing|explicitly|before|protected|darkness|oxidation|later use|replace|guaranteed|direct sun|air access|unopened|opened concentrate|prepared|manufacturer states|depending on|once opened|use once|discard|per litre|per liter|rolls|sheets|developer|full tightly|half full)\b',re.I)
for dn,v in cur.execute("SELECT developer_norm,preparation_it FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''"):
    if bad.search(v) or '\\n' in v:
        raise SystemExit(f'Bad Italian preparation {dn}: {v}')
con.commit()
after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    if before[t]!=after[t]: raise SystemExit(f'protected MDC changed: {t}')
print('developer_preparation_raw=79')
print('developer_preparation_clean_italian=79')
print('preparation_translation_coverage=79/79')
print('preparation_literal_backslash_n=0')
for t in PROTECTED: print(f'protected_{t}_unchanged_after_preparation_completion=PASS')
con.close()
