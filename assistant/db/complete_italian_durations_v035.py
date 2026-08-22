#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sqlite3,sys

DB=Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')
def fp(table):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'PRAGMA table_info({table})')]
    order=','.join('"'+c+'"' for c in cols)
    for row in cur.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode()); h.update(b'\n')
    return h.hexdigest()
before={t:fp(t) for t in PROTECTED}

UNOPENED={
'acurol n':'Almeno 4–5 anni nella bottiglia originale sigillata.',
'bellini euro hc':'Concentrato non aperto: 1–2 anni dall’acquisto se conservato in condizioni idonee, secondo le indicazioni generali Bellini per la chimica B/N.',
'moersch eco':'Concentrato A: minimo garantito 2 anni; concentrato B: durata non limitata dichiarata.',
'promicrol':'Concentrato non aperto: almeno 12 mesi se conservato a temperatura stabile di 13–18 °C; evitare temperature inferiori a 5 °C perché può verificarsi cristallizzazione.',
'rollei supergrain':'Indicazione generale Rollei per la propria chimica: i concentrati non aperti si conservano normalmente circa 1–2 anni al fresco e al buio. Non è una durata garantita specifica per Supergrain.',
'spur hrx':'Parte A: almeno 2,5 anni se conservata al fresco; Parte B: durata praticamente non limitata.',
'spur omega x':'Parte A: almeno 2 anni nella bottiglia originale non aperta se conservata al fresco; Parte B: durata quasi non limitata.',
}
OPENED={
'ars imago fd':'Concentrato aperto: usare entro 6 mesi; ridurre al minimo l’aria nella bottiglia oppure usare gas inerte.',
'ars imago fe':'Concentrato aperto: usare entro 4 mesi in un contenitore completamente pieno oppure entro 2 mesi in un contenitore parzialmente pieno.',
'ars imago monobath':'Concentrato aperto: usare entro 1 mese; la durata può arrivare a 8–12 mesi se l’aria viene rimossa efficacemente e il concentrato è conservato correttamente.',
'bellini euro hc':'Concentrato in bottiglia chiusa con l’aria espulsa: 6–8 settimane, secondo le indicazioni generali Bellini per i rivelatori B/N.',
'bergger superfine':'Concentrato: raccomandato l’uso entro 9 mesi dall’apertura.',
'fx 39':'Concentrato parzialmente aperto: se protetto dall’aria con gas, bottiglia comprimibile o biglie di vetro si conserva per almeno altri 6 mesi, in funzione del livello di riempimento.',
'ilfotec dd':'Dopo l’apertura usare completamente il concentrato entro 3 mesi e mantenerlo ben chiuso fino all’uso.',
'ilfotec rt rapid':'Dopo l’apertura usare completamente il concentrato entro 3 mesi; mantenere le bottiglie ben chiuse fino all’uso.',
'silvermax':'Concentrato aperto: fino a 6 mesi, in funzione della quantità di ossigeno presente nella bottiglia.',
}
STOCK={
'acu 1':'Soluzione stock: circa 1 anno se protetta da contaminazione e ossidazione.',
'atomal 49':'Soluzione stock: almeno 6 settimane; le istruzioni ADOX indicano fino a 8 settimane se conservata in bottiglie di vetro scuro completamente piene.',
'berspeed':'Soluzione preparata: 6 mesi.',
'cinestill df96 monobath':'Chimica miscelata: durata prevista di 1 anno in bottiglia sigillata prima dell’uso.',
'dektol':'Soluzione stock preparata: circa 6 mesi in un contenitore pieno e chiuso.',
'eco pro':'Soluzione miscelata a piena concentrazione: circa 6 mesi in contenitore pieno e ben chiuso; circa 2 mesi in contenitore a metà e ben chiuso.',
'mzb':'Le due soluzioni stock restano stabili per almeno 6 mesi anche in bottiglie parzialmente piene; escludendo l’aria, Moersch riporta per esperienza circa 1 anno.',
'microdol x':'Stock a piena concentrazione: 6 mesi in bottiglia piena e ben chiusa; 2 mesi in bottiglia a metà e ben chiusa.',
'xt 3':'Stock miscelato: almeno 6 settimane e fino a 6 mesi secondo conservazione ed esaurimento, se tenuto in bottiglie di vetro scuro piene oppure sotto gas protettivo.',
'xtol':'Soluzione miscelata: 6 mesi in contenitore pieno e ben chiuso; almeno 2 mesi in contenitore parzialmente pieno e ben chiuso.',
}
WORKING={
'adotech iii':'Soluzione di lavoro: fino a 6 settimane secondo la documentazione storica ADOX relativa ad ADOTECH III.',
'adotech iv':'ADOTECH IV diluito: fino a 14 giorni in bottiglie completamente piene; la refrigerazione può prolungare la durata della soluzione di lavoro.',
'ars imago monobath':'Con 135 ml di soluzione di lavoro: usare entro 5 giorni; la formulazione corrente da 500 ml indica il riutilizzo entro 2 settimane.',
'bellini euro hc':'Soluzione di lavoro: 2 settimane se lasciata aperta oppure 4 settimane in bottiglia chiusa, secondo le indicazioni generali Bellini.',
'cinestill df96 monobath':'Dopo il primo utilizzo, riutilizzare entro 2 mesi.',
'd 76':'A piena concentrazione: circa 24 ore in bacinella aperta oppure 1 mese in tank. Kodak non raccomanda il riutilizzo della diluizione 1+1.',
'fx 39':'La soluzione di lavoro preparata è monouso e va smaltita dopo l’uso.',
'hc 110':'A 18–24 °C, durata in mesi per contenitore pieno / contenitore a metà / tank con coperchio galleggiante: diluizione A 6/2/2; B 3/1/1; C 6/2/2; D 3/1/1; E 2/1/1. La conservazione della diluizione F non è raccomandata.',
'ilfotec dd':'Rivelatore in tank con reintegro: indicazione generale di sostituzione 6–12 mesi. Soluzione di lavoro senza reintegro: 6 mesi in contenitore pieno e chiuso; 2 mesi sotto coperchio galleggiante; 1 mese in contenitore a metà e ben chiuso.',
'ilfotec rt rapid':'Rivelatore con reintegro: indicazione generale di sostituzione 6–12 mesi nel tank di processo. Soluzione senza reintegro: fino a 6 mesi in contenitore pieno e ben chiuso; 2 mesi sotto coperchio galleggiante; 1 mese in contenitore a metà e ben chiuso.',
'microdol x':'A piena concentrazione: circa 24 ore in bacinella oppure 1 mese in tank grande con coperchio galleggiante. A 1+3 conservazione e riutilizzo non sono raccomandati: preparare immediatamente prima dell’uso.',
'moersch eco':'La soluzione di lavoro resta utilizzabile per alcuni giorni, ma il produttore raccomanda di preparare soltanto la quantità da usare immediatamente.',
'promicrol':'Le soluzioni di lavoro in tank macchina non devono restare inutilizzate per più di 1 settimana; preparare ogni volta non più di una settimana di reintegratore.',
'silberra aphenol':'Soluzione di lavoro: 4 mesi se non utilizzata; dopo il primo utilizzo non oltre 30 giorni.',
'silberra micro f':'Soluzione di lavoro: 1 mese se ben chiusa; il rivelatore parzialmente utilizzato non deve essere conservato.',
'silberra microl':'Soluzione di lavoro: massimo 3 giorni; per la soluzione parzialmente utilizzata non è dichiarata una durata garantita.',
'silberra s 76':'Soluzione di lavoro non utilizzata: fino a 6 mesi se ben chiusa; soluzione parzialmente utilizzata: fino a 45 giorni, ma non conservarla dopo aver superato metà della capacità prevista.',
'spur dokuspeed sl':'Soluzione di lavoro preparata: almeno 4 settimane in una bottiglia completamente piena.',
'spur dokuspeed sl n':'Soluzione di lavoro: circa 1 settimana in una bottiglia riempita fino all’orlo.',
'spur nanotech ur':'Soluzione di lavoro: 10–14 giorni in bottiglie completamente piene; la conservazione in frigorifero può prolungarne la durata.',
'spur omega x':'La soluzione di lavoro preparata deve essere usata entro poche ore.',
'tmax dev':'Soluzione alla concentrazione di lavoro: 6 mesi in bottiglia piena e ben chiusa; 2 mesi in bottiglia a metà; 1 mese in tank coperto.',
'tmax rs':'Soluzione alla concentrazione di lavoro: 6 mesi in bottiglia piena e ben chiusa; 2 mesi in bottiglia a metà; 1 mese in tank coperto.',
'tanol speed':'La soluzione di lavoro deve essere usata entro circa 10–15 minuti dalla miscelazione.',
}

for field,mapping in [('shelf_life_unopened_it',UNOPENED),('shelf_life_opened_it',OPENED),('shelf_life_stock_it',STOCK),('shelf_life_working_it',WORKING)]:
    for dn,text in mapping.items():
        cur.execute(f'UPDATE developer_profiles SET {field}=?,translation_status=? WHERE developer_norm=?',(text,'v035_strict_it_complete_duration',dn))
con.commit()

bad=re.compile(r'\b(the|and|with|when|should|stored|working solution|original package|minimum|defines|processing|explicitly|before|protected|darkness|oxidation|later use|replace|guaranteed|direct sun|air access|unopened|opened concentrate|prepared|manufacturer states|depending on|once opened|use once|discard|per litre|per liter|rolls|sheets|developer|full tightly|half full)\b',re.I)
for raw,it,expected in [
 ('shelf_life_unopened','shelf_life_unopened_it',45),
 ('shelf_life_opened','shelf_life_opened_it',24),
 ('shelf_life_stock','shelf_life_stock_it',16),
 ('shelf_life_working','shelf_life_working_it',46),
]:
    rc=cur.execute(f"SELECT COUNT(*) FROM developer_profiles WHERE COALESCE({raw},'')<>''").fetchone()[0]
    ic=cur.execute(f"SELECT COUNT(*) FROM developer_profiles WHERE COALESCE({it},'')<>''").fetchone()[0]
    if rc!=expected or ic!=expected:
        missing=cur.execute(f"SELECT developer_norm,developer_name,{raw} FROM developer_profiles WHERE COALESCE({raw},'')<>'' AND COALESCE({it},'')='' ORDER BY developer_name").fetchall()
        raise SystemExit(f'duration coverage mismatch {raw} raw={rc} it={ic} missing={missing}')
    for dn,v in cur.execute(f"SELECT developer_norm,{it} FROM developer_profiles WHERE COALESCE({it},'')<>''"):
        if bad.search(v) or '\\n' in v:
            raise SystemExit(f'Bad Italian duration {dn}.{it}: {v}')
after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    if before[t]!=after[t]: raise SystemExit(f'protected MDC changed: {t}')
print('duration_unopened_translation_coverage=45/45')
print('duration_opened_translation_coverage=24/24')
print('duration_stock_translation_coverage=16/16')
print('duration_working_translation_coverage=46/46')
print('duration_literal_backslash_n=0')
for t in PROTECTED: print(f'protected_{t}_unchanged_after_duration_completion=PASS')
con.close()
