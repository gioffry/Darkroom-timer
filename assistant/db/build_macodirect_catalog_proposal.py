#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, re, sqlite3, unicodedata, difflib

INPUT=Path("build-output/macodirect-master/macodirect_products.json")
DB=Path("combined/src/main/assets/mdc_full.sqlite")
OUT=Path("build-output/macodirect-proposal")
OUT.mkdir(parents=True,exist_ok=True)
CHECKED_AT="2026-09-28"

ROLE_FILM_DEV=1
ROLE_PAPER_DEV=2
ROLE_STOP=4
ROLE_FIX=8
ROLE_WETTING=16
ROLE_WASHING=32
ROLE_CHEMISTRY=64
ROLE_FILM=128

def ws(s): return re.sub(r"\s+"," ",str(s or "")).strip()
def norm(s):
    s=unicodedata.normalize("NFKD",ws(s)).encode("ascii","ignore").decode("ascii").lower()
    s=s.replace("–","-").replace("—","-")
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())
def compact(s): return re.sub(r"[^a-z0-9]+","",norm(s))
def slug(s):
    x=re.sub(r"[^a-z0-9]+","-",norm(s)).strip("-")
    return x[:72] or hashlib.sha1(str(s).encode()).hexdigest()[:12]

def film_family(title):
    t=ws(title)
    # Mixed bundles / sets are kept as retailer listings but are not processable film stocks.
    if re.search(r"(?i)\bbundle\b|\bset\s*\|",t):
        return ws(re.sub(r"(?i)\s+(?:35mm|135|roll\s*film|rollfilm).*","",t)), False
    # Minox products identify the stock in parentheses; keep ISO to separate the three.
    m=re.search(r"(?i)^Minox\s+8x11mm\s+Spy\s+Film\s*\|\s*(\d+)\s+ISO.*?\((Delta\s*\d+)\)",t)
    if m:
        return f"Minox Spy Film {m.group(2).replace(' ','')} ISO {m.group(1)}", True
    pats=[
        r"\s+(?:35mm|135)(?:\s*x\s*\d+(?:[.,]\d+)?m|\s+\d+\s*exposures?|\s*-\s*\d+|\s+\d+)?(?:\s+.*)?$",
        r"\s+roll\s*film\s*120(?:\s+.*)?$",
        r"\s+rollfilm\s*120(?:\s+.*)?$",
        r"\s+sheet\s*film\s+.*$",
        r"\s+(?:double\s*super\s*8mm|super\s*8|double\s*8mm|16mm)\b.*$",
        r"\s+\d+(?:[.,]\d+)?\s*mm\s*x\s*\d+(?:[.,]\d+)?m\b.*$",
    ]
    x=t
    for pat in pats:
        y=re.sub(pat,"",x,flags=re.I)
        if y!=x:
            x=y; break
    x=re.sub(r"\s+\d+\s*(?:sheets|exposures)\b.*$","",x,flags=re.I)
    x=ws(x.strip(" |-"))
    nx=norm(x)
    if nx.startswith("fomapan r 100"): x="Fomapan R 100"
    elif nx.startswith("ilford hp5 plus ulf planfilm"): x="ILFORD HP5 PLUS"
    elif nx.startswith("maco em film type s"): x="MACO EM film type S"
    elif nx.startswith("washi handcoated film on kozo paper"): x="WASHI handcoated film on Kozo paper"
    elif nx.startswith("bergger print film"): x="Bergger print film"
    elif nx.startswith("rollei paul reinhold 640"): x="Rollei Paul & Reinhold 640"
    # Collapse known Maco naming variations to one commercial film family.
    canon={
        "fomapan 100":"Fomapan 100 Classic",
        "fomapan 200":"Fomapan 200 Creative",
        "fomapan 400":"Fomapan 400 Action",
        "ilford hp5":"ILFORD HP5 PLUS",
        "ilford hp5 plus":"ILFORD HP5 PLUS",
        "ilford hp5 plus ulf planfilm":"ILFORD HP5 PLUS",
        "ilford fp4":"ILFORD FP4 PLUS",
        "ilford pan f":"ILFORD PAN F PLUS",
        "ilford pan f plus":"ILFORD PAN F PLUS",
        "ilford xp2":"ILFORD XP2 SUPER",
        "ilford xp2 400":"ILFORD XP2 SUPER",
        "kentmere 100":"KENTMERE PAN 100",
        "kentmere pan 100":"KENTMERE PAN 100",
        "kentmere 200":"KENTMERE PAN 200",
        "kentmere pan 200":"KENTMERE PAN 200",
        "kentmere 400":"KENTMERE PAN 400",
        "kentmere pan 400":"KENTMERE PAN 400",
        "kodak tri x":"KODAK TRI-X 400",
        "kodak tri x 400 tx":"KODAK TRI-X 400",
        "kodak t max 100":"KODAK T-MAX 100",
        "kodak t max 100 tmx":"KODAK T-MAX 100",
        "kodak t max 400":"KODAK T-MAX 400",
        "kodak t max p3200":"KODAK T-MAX P3200",
        "rollei ortho 25 plus":"ROLLEI ORTHO 25 PLUS",
        "rollei infrared 400":"ROLLEI INFRARED 400",
        "rollei infrared 400s":"ROLLEI INFRARED 400S",
        "fuji neopan acros 100 ii":"FUJIFILM NEOPAN 100 ACROS II",
        "wolfen np100":"WOLFEN NP100",
    }
    return canon.get(norm(x),x), True

def chem_family(title):
    x=ws(title)
    x=re.sub(r"\s*\|\s*(?:\d+(?:[.,]\d+)?\s*(?:x\s*)?|3x\s*|2x\s*).*$","",x,flags=re.I)
    x=re.sub(r"\s*\|\s*hydroquinone-free\s*$","",x,flags=re.I)
    patterns=[
        r"\s+to\s+(?:make|mix)\s+\d+(?:[.,]\d+)?\s*(?:ml|l|liter|litre|liters|litres|gallons?)\b.*$",
        r"\s+for\s+\d+(?:[.,]\d+)?\s*(?:ml|l|liter|litre|liters|litres)\b.*$",
        r"\s+for\s+\d+\s+(?:films?|determinations?)\b.*$",
        r"\s+\d+\s*x\s*\d+(?:[.,]\d+)?\s*(?:ml|l|liter|litre|cc|g|kg)\b.*$",
        r"\s+\d+(?:[.,]\d+)?\s*(?:ml|cc|l|liter|litre|liters|litres|g|kg)\b(?:\s.*)?$",
        r"\s+für\s+\d+(?:[.,]\d+)?\s+liter(?:\s+arbeitslösung)?\b.*$",
    ]
    for p in patterns: x=re.sub(p,"",x,flags=re.I)
    x=re.sub(r"\s+für\s*$","",x,flags=re.I)
    x=re.sub(r"(?i)(developer|fixer|bath|agent)(?:1l|5l|500ml|250ml|100ml)$",r"\1",x)
    x=ws(x.strip(" |-"))
    # Merge trivial title variants that are exactly the same commercial product.
    replacements={
        "bergger berspeed fine grain film developer":"Bergger BerSpeed fine grain developer",
        "ilford rapid fixer":"Ilford Rapid Fixer",
        "spur cool black paper developer":"Spur Cool Black paper developer",
        "foma universal developer powder":"FOMA Universal",
        "fomadon excel w27":"FOMADON Excel",
        "fomadon lqn":"FOMADON LQN",
        "fomadon lqr":"FOMADON LQR",
        "fomadon p w37 two component negative developer":"FOMADON P",
        "fomadon r09 film developer":"FOMADON R09",
        "fomacitro stop bath":"FOMACITRO",
        "fomafix":"FOMAFIX",
        "foma fotonal wetting agent":"FOTONAL",
        "fomatol lqn former classic pnb":"FOMATOL LQN",
        "fomatol powder p w14 neutral tone paper developer":"FOMATOL P",
        "fomatol powder pw w24 warmtone paper developer":"FOMATOL PW",
        "adox adotol konstant ii paper developer":"ADOX ADOTOL Konstant II",
        "adox adostop eco stop bath with indicator":"ADOX ADOSTOP ECO",
        "adox adostop eco p stop bath with indicator":"ADOX ADOSTOP ECO P",
        "adox adoflo ii":"ADOX ADOFLO II",
        "adox adofix plus express fixer":"ADOX ADOFIX Plus",
        "adox adofix p ii":"ADOX ADOFIX P II",
        "adox adonal":"ADOX ADONAL",
        "adox adotech iv":"ADOX ADOTECH IV",
        "adox atomal 49 film developer":"ADOX ATOMAL 49",
        "adox atomal 49 b w film developer":"ADOX ATOMAL 49",
        "adox d 76 classic powder developer":"ADOX D-76 CLASSIC",
        "adox d 76 eco powder developer":"ADOX D-76 ECO",
        "adox fx 39 ii film developer":"ADOX FX-39 II",
        "adox hr dev":"ADOX HR-DEV",
        "adox mcc developer":"ADOX MCC Developer",
        "adox neutol eco":"ADOX NEUTOL ECO",
        "adox neutol liquid ne":"ADOX NEUTOL NE",
        "adox neutol liquid wa":"ADOX NEUTOL WA",
        "adox silvermax developer":"ADOX SILVERMAX Developer",
        "adox xt 3 film developer":"ADOX XT-3",
        "adox xt 3 b w film developer":"ADOX XT-3",
        "compard fix ag fixer":"Compard Fix Ag",
        "compard fix ag plus fixer":"Compard Fix Ag Plus",
        "compard print ne":"Compard Print NE",
        "compard r09 one shot":"Compard R09 One Shot",
        "compard wac wetting agent former agepon":"Compard WAC",
        "ilford multigrade developer":"ILFORD MULTIGRADE Developer",
        "ilford pq universal":"ILFORD PQ UNIVERSAL",
        "ilford ilfostop":"ILFORD ILFOSTOP",
        "ilford ilfotol":"ILFORD ILFOTOL",
        "ilford hypam fixer":"ILFORD HYPAM Fixer",
        "ilford rapid fixer":"ILFORD Rapid Fixer",
        "kodak d 76 powder developer":"KODAK D-76",
        "kodak dektol powder paper developer":"KODAK DEKTOL",
        "kodak hc 110 film developer":"KODAK HC-110",
        "kodak professional t max developer":"KODAK T-MAX Developer",
        "kodak xtol film developer":"KODAK XTOL",
        "kodak xtol b w film developer":"KODAK XTOL",
        "lineag+ dxone b w monobath film developer":"LineAg+ DxONE B&W Monobath",
        "maco ecoprint universal developer":"MACO ecoprint Universal",
        "maco ecofix fixer":"MACO ecofix",
        "maco eco citrostop stop bath":"MACO eco citrostop",
        "maco ecostop universal stop bath":"MACO ecostop",
        "rollei rhc high contrast document developer":"ROLLEI RHC",
        "rollei rpn print neutral":"ROLLEI RPN Print Neutral",
        "rollei print neutral eco":"ROLLEI Print Neutral eco",
        "rollei rcs citro stop":"ROLLEI RCS Citro Stop",
        "rollei rxa fix acid":"ROLLEI RXA Fix Acid",
        "rollei rxn fix neutral":"ROLLEI RXN Fix Neutral",
        "rollei supergrain":"ROLLEI Supergrain",
        "rollei washjet wash accelerator":"ROLLEI WASHJET",
        "spur acurol n film developer":"SPUR Acurol-N",
        "spur hrx film developer":"SPUR HRX",
        "spur nanotech ur":"SPUR Nanotech UR",
        "spur omega x":"SPUR Omega X",
        "spur sld professional film developer":"SPUR SLD Professional",
        "spur speed major film developer":"SPUR Speed-Major",
        "spur trx 2000 film developer":"SPUR TRX 2000",
        "spur ultrafix a":"SPUR Ultrafix A",
        "spur ultrafix n":"SPUR Ultrafix N",
    }
    return replacements.get(norm(x),x)

def manufacturer(name):
    n=norm(name)
    rules=[
        ("ars imago","ARS-IMAGO"),("lineag+","LINEAG+"),("cinestill","CINESTILL"),
        ("agfaphoto","AGFAPHOTO"),("agfa ","AGFA"),("fujifilm","FUJIFILM"),("fuji ","FUJIFILM"),
        ("wolfen","ORWO/WOLFEN"),("adox","ADOX"),("foma","FOMA"),("fomadon","FOMA"),("fomatol","FOMA"),("fomafix","FOMA"),("fotonal","FOMA"),("fomacitro","FOMA"),
        ("ilford","ILFORD"),("kodak","KODAK"),("bellini","BELLINI"),("bergger","BERGGER"),
        ("compard","COMPARD"),("maco","MACO"),("moersch","MOERSCH"),("rollei","ROLLEI"),
        ("spur","SPUR"),("jobo","JOBO"),("fotospeed","FOTOSPEED"),("calbe","CALBE"),
        ("condor","CONDOR"),("macherey","MACHEREY-NAGEL"),("ferrania","FERRANIA"),
        ("kentmere","KENTMERE"),("kosmo","KOSMO FOTO"),("washi","WASHI"),("gothik","GOTHIK"),
        ("cfp","CFP"),("rera","RERA"),("minox","MINOX"),
    ]
    for prefix,m in rules:
        if n.startswith(prefix): return m
    return ws(name).split(" ")[0].upper() if ws(name) else ""

# Category membership is only a discovery hint. Manufacturer/technical semantics override
# obvious kits/additives and false cross-category placement.
GENERIC_PATTERNS=[
    r"(?i)\bkit\b",r"(?i)\bprocessing set\b",r"(?i)\btest kit\b",
    r"(?i)\bcleaner\b",r"(?i)protective gas",r"(?i)\btester\b",
    r"(?i)\bbleach\b",r"(?i)\bamplifier\b",r"(?i)\bintensifier\b",
    r"(?i)\bstarter\b",r"(?i)\bfinischer\b",r"(?i)\bhardener\b",
    r"(?i)\brestrainer\b",r"(?i)\bfotomask\b",
]
ROLE_OVERRIDES={
    norm("FOMA Universal"): ROLE_FILM_DEV|ROLE_PAPER_DEV|ROLE_CHEMISTRY,
    norm("ILFORD PQ UNIVERSAL"): ROLE_FILM_DEV|ROLE_PAPER_DEV|ROLE_CHEMISTRY,
    norm("MACO ecoprint Universal"): ROLE_FILM_DEV|ROLE_PAPER_DEV|ROLE_CHEMISTRY,
    norm("ROLLEI RHC"): ROLE_FILM_DEV|ROLE_PAPER_DEV|ROLE_CHEMISTRY,
    norm("Bellini D96 film developer"): ROLE_FILM_DEV|ROLE_CHEMISTRY,
    norm("Bellini DUO STEP film developer"): ROLE_FILM_DEV|ROLE_CHEMISTRY,
    norm("Bellini Ornano NUCLEOL BF200 film developer"): ROLE_FILM_DEV|ROLE_CHEMISTRY,
    norm("LineAg+ DxONE B&W Monobath"): ROLE_FILM_DEV|ROLE_CHEMISTRY,
    norm("JOBO 9510 | JOBO Alpha Neutral Fixer & JOBO Alpha Black & White Film Developer"): ROLE_CHEMISTRY,
    norm("JOBO 9515 | JOBO B&W Developer Test Kit"): ROLE_CHEMISTRY,
    norm("ROLLEI WASHJET"): ROLE_WASHING|ROLE_CHEMISTRY,
    norm("Ilford Galerie Washaid"): ROLE_WASHING|ROLE_CHEMISTRY,
    norm("Kodak Hypo Clearing Agent"): ROLE_WASHING|ROLE_CHEMISTRY,
    norm("Fotospeed Wash Aid"): ROLE_WASHING|ROLE_CHEMISTRY,
    # Manufacturer semantics override retailer-category placement:
    # Push-Master is an additive to SPUR SLD, not a standalone developer.
    norm("Spur Push-Master"): ROLE_CHEMISTRY,
    # Moersch SE1 is a positive/paper developer, not a film developer.
    norm("Moersch SE 1 Sepia positive developer"): ROLE_PAPER_DEV|ROLE_CHEMISTRY,
}
def roles_for(name,cats,processable=True):
    if "bw_film" in cats:
        return ROLE_FILM if processable else 0
    nk=norm(name)
    if nk in ROLE_OVERRIDES: return ROLE_OVERRIDES[nk]
    if any(re.search(p,name) for p in GENERIC_PATTERNS): return ROLE_CHEMISTRY
    r=ROLE_CHEMISTRY
    if "film_developer" in cats: r|=ROLE_FILM_DEV
    if "paper_developer" in cats: r|=ROLE_PAPER_DEV
    if "film_stop" in cats or "paper_stop" in cats: r|=ROLE_STOP
    if "film_fixer" in cats or "paper_fixer" in cats: r|=ROLE_FIX
    if "film_wetting" in cats or "paper_wetting" in cats: r|=ROLE_WETTING
    return r

# Explicit direct specialist links. These are identities/repackagings sufficiently
# established to route to existing MDC data. Timing equivalences remain in the
# existing developer_time_equivalents table and are NOT collapsed here.
DEV_LINKS={
    norm("ADOX ADONAL"):"Rodinal",
    norm("Compard R09 One Shot"):"Rodinal",
    norm("Compard R09 Studio"):"Studional",
    norm("ADOX ADOTECH IV"):"Adotech IV",
    norm("ADOX ATOMAL 49"):"Atomal 49",
    norm("ADOX D-76 CLASSIC"):"D-76",
    norm("ADOX D-76 ECO"):"D-76",
    norm("ADOX FX-39 II"):"FX-39",
    norm("ADOX HC-110 PRO ''Original Syrup'' Made in Germany"):"HC-110",
    norm("ADOX HR-DEV"):"Adox HR-DEV",
    norm("ADOX SILVERMAX Developer"):"Silvermax",
    norm("ADOX XT-3"):"XT-3",
    norm("Bellini D96 film developer"):"D-96",
    norm("Bellini DUO STEP film developer"):"Bellini DF2 Duo Step",
    norm("Bellini ECOFILM film developer"):"Bellini B&W Ecofilm",
    norm("Bellini EURO HC film developer"):"Bellini Euro HC",
    norm("Bellini Ornano NUCLEOL BF200 film developer"):"Nucleol BF200",
    norm("Bergger BerSpeed fine grain developer"):"Berspeed",
    norm("Bergger P.M.K. liquide universal developer"):"PMK",
    norm("CineStill Df96 Developer & Fix B&W Monobath"):"Cinestill Df96 Monobath",
    norm("Foma Retro Special powder negative developer"):"Foma Retro Special",
    norm("FOMA Universal"):"Foma Universal",
    norm("FOMADON Excel"):"Fomadon Excel",
    norm("FOMADON LQN"):"Fomadon LQN",
    norm("FOMADON LQR"):"Fomadon LQR",
    norm("FOMADON P"):"Fomadon P",
    norm("FOMADON R09"):"Fomadon R09",
    norm("Ilford ID-11 fine grain film developer"):"ID-11",
    norm("Ilford Ilfosol 3"):"Ilfosol 3",
    norm("Ilford Simplicity Film Developer"):"Ilfosol 3",
    norm("Ilford Ilfotec DD-X"):"Ilfotec DD-X",
    norm("Ilford Ilfotec HC"):"Ilfotec HC",
    norm("Ilford Ilfotec LC29 liquid concentrate film developer"):"Ilfotec LC29",
    norm("Ilford Microphen fine grain film developer"):"Microphen",
    norm("ILFORD MULTIGRADE Developer"):"Ilford Multigrade",
    norm("ILFORD PQ UNIVERSAL"):"PQ Universal",
    norm("Ilford Perceptol fine grain film developer"):"Perceptol",
    norm("JOBO 9511 | JOBO Alpha film developer"):"JOBO Alpha",
    norm("JOBO 9511 | JOBO Alpha Black & White Film Developer"):"JOBO Alpha",
    norm("KODAK D-76"):"D-76",
    norm("KODAK DEKTOL"):"Dektol",
    norm("KODAK HC-110"):"HC-110",
    norm("KODAK T-MAX Developer"):"TMax Dev",
    norm("KODAK XTOL"):"Xtol",
    norm("MACO ecoprint Universal"):"Ecoprint Universal",
    norm("Moersch Finol 200 film developer"):"Finol",
    norm("Moersch Tanol 200 film developer"):"Tanol",
    norm("Moersch Tanol Speed 200 film developer"):"Tanol Speed",
    norm("Moersch eco film developer"):"Moersch eco",
    norm("ROLLEI Supergrain"):"Rollei Supergrain",
    norm("SPUR Acurol-N"):"Acurol-N",
    norm("SPUR HRX"):"Spur HRX",
    norm("SPUR Nanotech UR"):"Spur Nanotech UR",
    norm("SPUR Omega X"):"Spur Omega X",
    norm("SPUR SD 2525 film developer"):"Spur SD 2525",
    norm("SPUR SLD Professional"):"Spur SLD",
    norm("Spur Shadowmax"):"Spur SHADOWmax",
    norm("SPUR Speed-Major"):"Spur Speed-Major",
    norm("SPUR TRX 2000"):"Spur TRX 2000",
    norm("ars-imago MB - Monobath film developer"):"Ars-Imago Monobath",
}
FILM_LINKS={
    norm("Adox CHS 100 II"):"Adox CHS 100 II",
    norm("Adox CMS 20 II"):"Adox CMS 20 II",
    norm("Adox Scala 50"):"Adox Scala 50",
    norm("Agfa Copex Rapid"):"Agfa Copex Rapid",
    norm("AgfaPHOTO APX 100"):"AgfaPhoto APX 100",
    norm("AgfaPHOTO APX 400"):"AgfaPhoto APX 400",
    norm("Bergger Pancro 400"):"Bergger Pancro 400",
    norm("CineStill Double-X BWxx 200"):"CineStill BwXX",
    norm("Ferrania Orto 50"):"Ferrania Orto",
    norm("Ferrania P30"):"Ferrania P30",
    norm("Ferrania P33"):"Ferrania P33",
    norm("Foma Ortho 400"):"Foma Ortho 400",
    norm("Foma Retropan 320"):"Foma Retropan 320",
    norm("Fomapan 100 Classic"):"Fomapan 100",
    norm("Fomapan 200 Creative"):"Fomapan 200",
    norm("Fomapan 400 Action"):"Fomapan 400",
    norm("FUJIFILM NEOPAN 100 ACROS II"):"Fuji Neopan 100 Acros II",
    norm("HP 400 roll film 127 (Ilford HP5)"):"Ilford HP5+",
    norm("Ilford Delta 100"):"Ilford Delta 100 Pro",
    norm("Ilford Delta 3200"):"Ilford Delta 3200 Pro",
    norm("Ilford Delta 400"):"Ilford Delta 400 Pro",
    norm("ILFORD FP4 PLUS"):"Ilford FP4+",
    norm("ILFORD HP5 PLUS"):"Ilford HP5+",
    norm("Ilford Ortho Plus"):"Ilford Ortho Plus",
    norm("ILFORD PAN F PLUS"):"Ilford Pan F+",
    norm("Ilford SFX 200"):"Ilford SFX 200",
    norm("ILFORD XP2 SUPER"):"Ilford XP2 Super",
    norm("KENTMERE PAN 100"):"Kentmere 100",
    norm("KENTMERE PAN 200"):"Kentmere 200",
    norm("KENTMERE PAN 400"):"Kentmere 400",
    norm("Kodak Ektapan 100"):"Kodak Ektapan 100",
    norm("Kodak Ektapan 400"):"Kodak Ektapan 400",
    norm("KODAK T-MAX 100"):"Kodak TMax 100",
    norm("KODAK T-MAX 400"):"Kodak TMax 400",
    norm("KODAK T-MAX P3200"):"Kodak TMax P3200",
    norm("KODAK TRI-X 320"):"Kodak Tri-X 320",
    norm("KODAK TRI-X 400"):"Kodak Tri-X 400",
    norm("Kosmo Foto Mono 100"):"Kosmo Foto Mono",
    norm("MACO TS Eagle AQS"):"Maco Eagle AQS",
    norm("Rera Pan 100F Rollfilm 127"):"ReraPan 100",
    norm("Rera Pan 400 roll film 127"):"ReraPan 400",
    norm("Rollei Blackbird"):"Rollei Blackbird",
    norm("ROLLEI INFRARED 400"):"Rollei Infrared IR400",
    norm("ROLLEI INFRARED 400S"):"Rollei Retro 400S",
    norm("ROLLEI ORTHO 25 PLUS"):"Rollei Ortho 25 Plus",
    norm("Rollei Paul & Reinhold 640 | 2 ×"):"Rollei Paul & Reinhold 640",
    norm("Rollei RPX 100"):"Rollei RPX 100",
    norm("Rollei RPX 25"):"Rollei RPX 25",
    norm("Rollei RPX 400"):"Rollei RPX 400",
    norm("Rollei Retro 400S"):"Rollei Retro 400S",
    norm("Rollei Retro 80S"):"Rollei Retro 80S",
    norm("Rollei Superpan 200"):"Rollei Superpan 200",
    norm("Spur Ultra R 800"):"SPUR Ultra R 800",
    norm("WOLFEN NP100"):"Orwo/Wolfen NP100",
    norm("Minox Spy Film Delta100 ISO 100"):"Ilford Delta 100 Pro",
    norm("Minox Spy Film Delta400 ISO 400"):"Ilford Delta 400 Pro",
    norm("Minox Spy Film Delta3200 ISO 1600"):"Ilford Delta 3200 Pro",
}

def formats_for(listings):
    vals=set()
    for p in listings:
        t=p["title"].lower()
        if re.search(r"\b35mm\b|\b135[- ]",t): vals.add("35")
        if re.search(r"\broll\s*film\s*120\b|\brollfilm\s*120\b",t): vals.add("120")
        if "sheet film" in t or re.search(r"\b4x5\b|\b5x7\b|\b8x10\b|\b9x12\b|\b13x18\b",t): vals.add("4x5")
        if "127" in t: vals.add("127")
        if re.search(r"\b16mm\b|super\s*8|double\s*8",t): vals.add("cine")
        if "8x11mm" in t: vals.add("minox")
    return "|".join(sorted(vals))

products=json.loads(INPUT.read_text(encoding="utf-8"))
groups={}
listing_rows=[]
for p in products:
    if "bw_film" in p["categories"]:
        family,processable=film_family(p["title"])
        kind="film"
    else:
        family=chem_family(p["title"]); processable=True; kind="chemical"
    key=(kind,norm(family))
    g=groups.setdefault(key,{"kind":kind,"name":family,"processable":processable,"listings":[],"categories":set()})
    g["listings"].append(p); g["categories"].update(p["categories"])
    if not processable: g["processable"]=False

# Merge a few commercial-name variants that are definitely the same family.
merge_names={
    norm("Bergger BerSpeed fine grain film developer"):norm("Bergger BerSpeed fine grain developer"),
    norm("Spur Cool black paper developer"):norm("Spur Cool Black paper developer"),
}
for (kind,nk),g in list(groups.items()):
    target=merge_names.get(nk)
    if target and target != nk and (kind,target) in groups:
        groups[(kind,target)]["listings"].extend(g["listings"])
        groups[(kind,target)]["categories"].update(g["categories"])
        del groups[(kind,nk)]

con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
dev_names={norm(r["name"]):r["name"] for r in con.execute("SELECT name FROM developers")}
film_names={norm(r["name"]):r["name"] for r in con.execute("SELECT name FROM films")}
existing={norm(r["name"]):dict(r) for r in con.execute("SELECT * FROM catalog_products")}
scope_rows=[dict(r) for r in con.execute("SELECT developer_name,maco_product_title FROM maco_developer_scope")]

def scope_developer_link(group_name,listings):
    gn=norm(group_name)
    raw_names=[norm(p["title"]) for p in listings]
    best=None
    for s in scope_rows:
        st=norm(s["maco_product_title"])
        # Exact/contained commercial name, or a raw listing contained by the frozen scope title.
        candidates=[gn]+raw_names
        score=0
        for cn in candidates:
            if cn and (cn in st or st in cn): score=max(score,100)
            else:
                a=set(cn.split()); b=set(st.split())
                if a and b: score=max(score,int(100*len(a&b)/max(1,len(a))))
        if score>=70 and (best is None or score>best[0]):
            best=(score,s["developer_name"])
    return None if best is None else best[1]

proposal=[]
unresolved=[]
seen_ids=set()
for (kind,nk),g in sorted(groups.items(),key=lambda kv:(kv[0][0],kv[1]["name"].lower())):
    name=g["name"]; cats=sorted(g["categories"])
    roles=roles_for(name,cats,g["processable"])
    base_id=("film-" if kind=="film" else "chem-")+slug(name)
    pid=base_id
    if pid in seen_ids:
        pid=base_id+"-"+hashlib.sha1(name.encode()).hexdigest()[:7]
    seen_ids.add(pid)
    aliases=[]
    for p in g["listings"]:
        if p["title"] not in aliases: aliases.append(p["title"])
    if name not in aliases: aliases.insert(0,name)
    link_kind=""; link_name=""; link_relation=""
    if kind=="film" and g["processable"]:
        want=FILM_LINKS.get(nk)
        if want and norm(want) in film_names:
            link_kind="film"; link_name=film_names[norm(want)]
            link_relation="REPACKAGED_STOCK" if name.lower().startswith("minox spy film") else "DIRECT_PRODUCT_MAPPING"
    elif kind=="chemical" and roles & (ROLE_FILM_DEV|ROLE_PAPER_DEV):
        # Product identity/equivalence links must be explicit and audited.
        # Never create one from fuzzy retailer-title matching.
        want=DEV_LINKS.get(nk)
        if want and norm(want) in dev_names:
            link_kind="developer"; link_name=dev_names[norm(want)]; link_relation="DIRECT_PRODUCT_MAPPING"
    # Carry existing product ID/technical identity when name already exists.
    ex=existing.get(nk)
    if ex:
        pid=ex["id"]
    existing_ready=bool(ex and (
        (ex.get("film_dilutions") or "").strip() or
        (ex.get("paper_dilutions") or "").strip() or
        (ex.get("working_dilution") or "").strip() or
        kind=="film"
    ))
    status=("LINKED" if link_name else
            ("NON_PROCESSABLE_LISTING" if not g["processable"] else
             ("EXISTING_TECHNICAL" if existing_ready else "CATALOG_ONLY")))
    row={
        "id":pid,"name":name,"manufacturer":manufacturer(name),"kind":kind,
        "roles":roles,"categories":"|".join(cats),"processable":1 if g["processable"] else 0,
        "formats":formats_for(g["listings"]) if kind=="film" else "",
        "aliases":"|".join(a.replace("|"," ") for a in aliases),
        "alias_list":aliases,"listing_count":len(g["listings"]),
        "specialist_kind":link_kind,"specialist_name":link_name,
        "specialist_relation":link_relation,"status":status,
        "source_url":g["listings"][0]["url"],
    }
    proposal.append(row)
    if status=="CATALOG_ONLY" and g["processable"] and (kind=="film" or roles&(ROLE_FILM_DEV|ROLE_PAPER_DEV)):
        unresolved.append(row)

# Validation: every Maco listing belongs to exactly one proposal group.
listing_total=sum(r["listing_count"] for r in proposal)
assert listing_total==len(products),(listing_total,len(products))
assert len({r["id"] for r in proposal})==len(proposal)
assert all(r["name"] and r["manufacturer"] for r in proposal)
# Existing audited timing equivalences are read-only and must remain unchanged.
eq_count=con.execute("SELECT COUNT(*) FROM developer_time_equivalents").fetchone()[0]
assert eq_count==39,eq_count

with (OUT/"catalog_proposal.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(proposal[0].keys())); w.writeheader(); w.writerows(proposal)
(OUT/"catalog_proposal.json").write_text(json.dumps(proposal,ensure_ascii=False,indent=2),encoding="utf-8")
with (OUT/"unresolved_processable.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(proposal[0].keys())); w.writeheader(); w.writerows(unresolved)

summary={
    "macodirect_listings":len(products),
    "canonical_products":len(proposal),
    "film_products":sum(r["kind"]=="film" and r["processable"] for r in proposal),
    "nonprocessable_bundles":sum(not r["processable"] for r in proposal),
    "chemical_products":sum(r["kind"]=="chemical" for r in proposal),
    "film_developers":sum(bool(r["roles"]&ROLE_FILM_DEV) for r in proposal),
    "paper_developers":sum(bool(r["roles"]&ROLE_PAPER_DEV) for r in proposal),
    "dual_film_paper_developers":sum(bool(r["roles"]&ROLE_FILM_DEV and r["roles"]&ROLE_PAPER_DEV) for r in proposal),
    "stops":sum(bool(r["roles"]&ROLE_STOP) for r in proposal),
    "fixers":sum(bool(r["roles"]&ROLE_FIX) for r in proposal),
    "wetting":sum(bool(r["roles"]&ROLE_WETTING) for r in proposal),
    "washing":sum(bool(r["roles"]&ROLE_WASHING) for r in proposal),
    "specialist_links":sum(bool(r["specialist_name"]) for r in proposal),
    "unresolved_processable":len(unresolved),
    "existing_timing_equivalence_rows_preserved":eq_count,
}
(OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
print("\nUNRESOLVED PROCESSABLE")
for r in unresolved:
    print(f"{r['kind']:8} roles={r['roles']:3} {r['name']}")
con.close()
