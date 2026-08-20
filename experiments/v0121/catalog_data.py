#!/usr/bin/env python3
import json, hashlib

SOURCES=[]
RECORDS=[]
REMOTE=[]

def source(i,author,title,url,version=""):
    SOURCES.append({"id":i,"author":author,"title":title,"reference":"Documentazione ufficiale produttore","url":url,"sourceType":"FONTE UFFICIALE","documentVersion":version,"verificationStatus":"VERIFICATO"})

def record(i,name,maker,categories,aliases,subtitle,source_id,technical=None,remote=False):
    row={"id":i,"name":name,"manufacturer":maker,"categories":categories,"aliases":aliases,"subtitle":subtitle,"sourceId":source_id,"technical":technical or {},"dataDate":"2026-08-19","verificationStatus":"VERIFICATO"}
    (REMOTE if remote else RECORDS).append(row)

source("foma-handbook","FOMA BOHEMIA","B&W Photo Materials and Developing Information","https://www.foma.cz/en/catalogue_bw_photo_materials_and_developing_information","2020")
source("foma-universal","FOMA BOHEMIA","FOMA Universal","https://www.foma.cz/en/catalogue-foma-universal-detail-1109")
source("foma-fotonal","FOMA BOHEMIA","FOTONAL","https://www.foma.cz/en/catalogue-fotonal-detail-293")
source("foma-fomatol-lqn","FOMA BOHEMIA","FOMATOL LQN","https://www.foma.cz/en/catalogue-fomatol-lqn-detail-286")
source("foma-fomafix","FOMA BOHEMIA","FOMAFIX","https://www.foma.cz/en/catalogue-fomafix-detail-821")
source("ilford-hp5","HARMAN technology / ILFORD","HP5 PLUS Technical Information","https://www.ilfordphoto.com/amfile/file/download/file/1903/product/693/","Nov 2018")
source("kodak-bw-processing","Kodak Alaris","Processing KODAK PROFESSIONAL Black-and-White Films","https://www.kodakprofessional.com/sites/default/files/wysiwyg/pro/resources/edbwf_0.pdf","Mar 2023")
source("kodak-trix","Kodak Alaris","KODAK PROFESSIONAL TRI-X 320 and 400 Films","https://kodakprofessional.com/sites/default/files/wysiwyg/film/f4017_trix_320400.pdf","Oct 2021")
source("adox-adostop","ADOX Fotowerke GmbH","ADOSTOP ECO","https://www.adox.de/adostop-eco-2/")
source("jobo-1510","JOBO International GmbH","#1510 JOBO 35mm Tank","https://www.jobo.com/en/analogue/1510-jobo-35mm-tank-")
source("jobo-1520","JOBO International GmbH","#1520 JOBO Uni Tank + LAB Kit M","https://www.jobo.com/en/analogue/1500m-lab-kit-m")
source("jobo-1540","JOBO International GmbH","#1540 JOBO Multi Tank + LAB Kit L","https://www.jobo.com/en/analogue/1500l-lab-kit-l")
source("jobo-2502","JOBO International GmbH","#2502 JOBO Duo Set Reel","https://www.jobo.com/en/analogue/2502-jobo-duo-set-reel")
source("jobo-2520","JOBO International GmbH","#2520 JOBO Multitank 2","https://www.jobo.com/en/analogue/2520-jobo-multi-tank-2-")
source("jobo-2540","JOBO International GmbH","#2540 JOBO Multitank 1","https://www.jobo.com/en/analogue/2540-jobo-multi-tank-1")
source("jobo-2550","JOBO International GmbH","#2550 JOBO Multitank 5","https://www.jobo.com/en/analogue/2550-jobo-multi-tank-5")
source("jobo-processors","JOBO International GmbH","JOBO analogue processors","https://www.jobo.com/en/analogue/")

# Films: only identity/ISO/format facts that are documented in the source catalog.
record("film-fomapan-100","Fomapan 100 Classic","FOMA",["FILM"],["foma 100","fomapan100","foma classic 100"],"Pellicola B/N · ISO 100","foma-handbook",{"nominalIso":100,"formats":["35 mm","120"],"dataType":"DATO DIRETTO"})
record("film-fomapan-200","Fomapan 200 Creative","FOMA",["FILM"],["foma 200","foma 2","fomapan200"],"Pellicola B/N · ISO 200","foma-handbook",{"nominalIso":200,"formats":["35 mm","120"],"dataType":"DATO DIRETTO"})
record("film-fomapan-400","Fomapan 400 Action","FOMA",["FILM"],["foma 400","fomapan400","foma action"],"Pellicola B/N · ISO 400","foma-handbook",{"nominalIso":400,"formats":["35 mm","120"],"dataType":"DATO DIRETTO"})
record("film-hp5","ILFORD HP5 PLUS","ILFORD",["FILM"],["hp5","hp5+","hp 5","ilford hp5","hp5 plus"],"Pellicola B/N · ISO 400","ilford-hp5",{"nominalIso":400,"formats":["35 mm","120"],"dataType":"DATO DIRETTO"})
record("film-trix400","KODAK TRI-X 400","KODAK",["FILM"],["tri x","trix","tri-x","400tx","kodak trix"],"Pellicola B/N · ISO 400","kodak-trix",{"nominalIso":400,"formats":["35 mm","120"],"dataType":"DATO DIRETTO"})
record("film-tmax100","KODAK T-MAX 100","KODAK",["FILM"],["tmax 100","t max 100","100tmx"],"Pellicola B/N · ISO 100","kodak-bw-processing",{"nominalIso":100,"dataType":"DATO DIRETTO"})
record("film-tmax400","KODAK T-MAX 400","KODAK",["FILM"],["tmax 400","t max 400","400tmy"],"Pellicola B/N · ISO 400","kodak-bw-processing",{"nominalIso":400,"dataType":"DATO DIRETTO"})

# Film developers. The technical-development engine in v0.12.0 remains authoritative for timing.
record("dev-foma-universal","FOMA Universal","FOMA",["FILM_DEVELOPER","PAPER_DEVELOPER","CHEMISTRY"],["foma universal developer","foma un","universal developer foma"],"Rivelatore film e carta","foma-universal",{"filmDilutions":["1+3"],"paperDilutions":["stock"],"physicalState":"polvere","dataType":"DATO DIRETTO"})
record("dev-fomadon-r09","FOMADON R09","FOMA",["FILM_DEVELOPER","CHEMISTRY"],["r09","r 09","foma r09","fomadon r 09"],"Rivelatore pellicola","foma-handbook",{"dilutions":["1+25","1+50","1+100"],"dataType":"DATO DIRETTO"})
record("dev-fomadon-lqn","FOMADON LQN","FOMA",["FILM_DEVELOPER","CHEMISTRY"],["lqn","foma lqn"],"Rivelatore pellicola","foma-handbook",{"dilutions":["1+10","1+14"],"dataType":"DATO DIRETTO"})
record("dev-fomadon-lqr","FOMADON LQR","FOMA",["FILM_DEVELOPER","CHEMISTRY"],["lqr","foma lqr"],"Rivelatore pellicola","foma-handbook",{"dilutions":["1+10","1+14"],"dataType":"DATO DIRETTO"})
record("dev-fomadon-excel","FOMADON Excel","FOMA",["FILM_DEVELOPER","CHEMISTRY"],["foma excel","fomadon excel developer"],"Rivelatore pellicola","foma-handbook",{"dataType":"DATO DIRETTO"})
record("dev-kodak-d76","KODAK D-76","KODAK",["FILM_DEVELOPER","CHEMISTRY"],["d76","d-76","d 76","kodak d76"],"Rivelatore pellicola","kodak-bw-processing",{"dilutions":["stock","1+1"],"dataType":"DATO DIRETTO"})
record("dev-kodak-xtol","KODAK XTOL","KODAK",["FILM_DEVELOPER","CHEMISTRY"],["xtol","x tol","kodak x-tol"],"Rivelatore pellicola","kodak-bw-processing",{"dilutions":["stock","1+1"],"dataType":"DATO DIRETTO"})
record("dev-kodak-hc110","KODAK HC-110","KODAK",["FILM_DEVELOPER","CHEMISTRY"],["hc110","hc 110","hc-110"],"Rivelatore pellicola","kodak-bw-processing",{"dilutions":["B"],"dataType":"DATO DIRETTO"})
record("dev-kodak-tmax","KODAK T-MAX","KODAK",["FILM_DEVELOPER","CHEMISTRY"],["tmax developer","t max developer","kodak tmax developer"],"Rivelatore pellicola","kodak-bw-processing",{"dilutions":["1+4"],"dataType":"DATO DIRETTO"})
record("dev-ilford-id11","ILFORD ID-11","ILFORD",["FILM_DEVELOPER","CHEMISTRY"],["id11","id-11","id 11","ilford id11"],"Rivelatore pellicola","foma-handbook",{"dilutions":["stock","1+1","1+3"],"dataType":"DATO DIRETTO","note":"Diluizioni già presenti nel catalogo tecnico v0.12.0"})
record("dev-ilford-microphen","ILFORD MICROPHEN","ILFORD",["FILM_DEVELOPER","CHEMISTRY"],["microphen","ilford microphen developer"],"Rivelatore pellicola","foma-handbook",{"dilutions":["stock","1+1","1+3"],"dataType":"DATO DIRETTO","note":"Diluizioni già presenti nel catalogo tecnico v0.12.0"})
record("dev-ilford-ddx","ILFORD ILFOTEC DD-X","ILFORD",["FILM_DEVELOPER","CHEMISTRY"],["ddx","dd-x","dd x","ilfotec ddx"],"Rivelatore pellicola","ilford-hp5",{"dilutions":["1+4"],"dataType":"DATO DIRETTO"})

# Paper and chemistry.
record("paper-fomaspeed-311","Fomaspeed Variant 311","FOMA",["PAPER"],["foma 311","fomaspeed 311","variant 311","foma variant 311"],"Carta RC multigrade · glossy","foma-handbook",{"family":"Fomaspeed Variant","surfaceCode":"311","dataType":"DATO DIRETTO"})
record("paperdev-fomatol-lqn","FOMATOL LQN","FOMA",["PAPER_DEVELOPER","CHEMISTRY"],["fomatol","foma paper developer","foma lqn paper"],"Rivelatore carta","foma-fomatol-lqn",{"dilutions":["1+7"],"use":"manuale","dataType":"DATO DIRETTO"})
record("stop-adox-adostop","ADOX Adostop ECO","ADOX",["STOP_BATH","CHEMISTRY"],["ado stop","adostop","adox stop","adostop eco"],"Bagno d'arresto","adox-adostop",{"dilutions":["1+19"],"capacity":"> 3 m²/L soluzione di lavoro","workingSolutionLife":"1–2 settimane raccomandate","dataType":"DATO DIRETTO"})
record("fix-fomafix","FOMAFIX","FOMA",["FIXER","CHEMISTRY"],["foma fix","fomafix rapid fixer"],"Fissaggio rapido film/carta","foma-fomafix",{"dilutions":[],"dataType":"DATO DIRETTO","note":"La pagina prodotto conferma uso film/carta; la diluizione non è valorizzata se non verificata per il contesto fotografico."})
record("wet-fotonal","FOTONAL","FOMA",["WETTING_AGENT","CHEMISTRY"],["foma fotonal","wetting agent fotonal"],"Imbibente / agente bagnante","foma-fotonal",{"dilutions":["5 ml / 1 L acqua"],"dataType":"DATO DIRETTO"})

# JOBO tanks. Unknown compatibility is omitted, never encoded as false/zero.
record("tank-jobo-1510","JOBO 1510","JOBO",["TANK","EQUIPMENT"],["1510","jobo1510","jobo 15"],"System 1500 · 35 mm Tank","jobo-1510",{"system":"System 1500","tankType":"35mm Tank","capacity35":1,"capacity120":0,"capacityDataType":"DATO DIRETTO","minInversionMl":250,"minRotationMl":140,"cogCompatible":True,"liftCompatible":True,"processorCompatibility":"JOBO processors dopo retrofit magnete/cog","processorCompatibilityDataType":"DATO DIRETTO","dataType":"DATO DIRETTO"})
record("tank-jobo-1520","JOBO 1520","JOBO",["TANK","EQUIPMENT"],["1520","jobo1520","jobo 15","jobo uni tank"],"System 1500 · Uni Tank","jobo-1520",{"system":"System 1500","tankType":"Uni Tank","capacity35":2,"capacity120":2,"capacityDataType":"DATO DIRETTO","minInversionMl":485,"minRotationMl":240,"cogCompatible":True,"liftCompatible":True,"processorCompatibility":"JOBO processors dopo retrofit magnete/cog","processorCompatibilityDataType":"DATO DIRETTO","dataType":"DATO DIRETTO"})
record("tank-jobo-1540","JOBO 1540","JOBO",["TANK","EQUIPMENT"],["1540","jobo1540","jobo 15","jobo multi tank"],"System 1500 · Multi Tank","jobo-1540",{"system":"System 1500","tankType":"Multi Tank","capacity35":4,"capacity120":4,"capacityDataType":"DATO DIRETTO","minInversionMl":975,"minRotationMl":470,"cogCompatible":True,"liftCompatible":True,"processorCompatibility":"JOBO processors dopo retrofit magnete/cog","processorCompatibilityDataType":"DATO DIRETTO","dataType":"DATO DIRETTO"})
record("tank-jobo-2520","JOBO 2520","JOBO",["TANK","EQUIPMENT"],["2520","jobo2520","jobo 25","multitank 2","multi tank 2"],"System 2500 · Multitank 2","jobo-2520",{"system":"System 2500","tankType":"Multitank 2","reels2502":2,"capacity35":2,"capacity120":2,"capacityDataType":"DATO INTERNO VERIFICATO","minInversionMl":775,"minInversionDataType":"DATO INTERNO VERIFICATO","minRotationMl":270,"cogCompatible":True,"liftCompatible":True,"cpe2Compatible":True,"cpe2CompatibilityDataType":"DATO INTERNO VERIFICATO","dataType":"DATO DIRETTO + DATO INTERNO VERIFICATO","note":"I valori 35/120, inversione e compatibilità CPE2 preservano il record verificato v0.12.0; JOBO corrente conferma 2 spirali 2502 e 270 ml."})
record("tank-jobo-2540","JOBO 2540","JOBO",["TANK","EQUIPMENT"],["2540","jobo2540","jobo 25","multitank 1","multi tank 1"],"System 2500 · Multitank 1","jobo-2540",{"system":"System 2500","tankType":"Multitank 1","reels2502":1,"minRotationMl":140,"cogCompatible":True,"liftCompatible":True,"processorCompatibility":"JOBO processors","processorCompatibilityDataType":"DATO DIRETTO","capacity35":1,"capacity120":2,"capacityDataType":"CALCOLO","capacityCalculation":"1 spirale 2502; la 2502 può accogliere 2 rollfilm 120 con clip","dataType":"DATO DIRETTO + CALCOLO"})
record("tank-jobo-2550","JOBO 2550","JOBO",["TANK","EQUIPMENT"],["2550","jobo2550","jobo 25","multitank 5","multi tank 5"],"System 2500 · Multitank 5","jobo-2550",{"system":"System 2500","tankType":"Multitank 5","reels2502":5,"minRotationMl":640,"cogCompatible":True,"liftCompatible":True,"processorCompatibility":"JOBO processors; pagina corrente: CPE-3 e CPP-3","processorCompatibilityDataType":"DATO DIRETTO","capacity35":5,"capacity120":10,"capacityDataType":"CALCOLO","capacityCalculation":"5 spirali 2502; ogni 2502 può accogliere 2 rollfilm 120 con clip","dataType":"DATO DIRETTO + CALCOLO"})
record("processor-jobo-cpe3","JOBO CPE-3","JOBO",["PROCESSOR","EQUIPMENT"],["cpe3","cpe 3","jobo cpe"],"Processore a rotazione","jobo-processors",{"dataType":"DATO DIRETTO"})
record("processor-jobo-cpp3","JOBO CPP-3","JOBO",["PROCESSOR","EQUIPMENT"],["cpp3","cpp 3","jobo cpp"],"Processore a rotazione","jobo-processors",{"temperatureRangeC":[20,40],"dataType":"DATO DIRETTO"})

# Remote-only extension: same schema, real source-backed records. It never contains user data.
record("dev-fomadon-p","FOMADON P","FOMA",["FILM_DEVELOPER","CHEMISTRY"],["fomadon p developer","foma p developer"],"Rivelatore pellicola","foma-handbook",{"dataType":"DATO DIRETTO"},True)
record("paperdev-fomatol-p","FOMATOL P","FOMA",["PAPER_DEVELOPER","CHEMISTRY"],["fomatol p","foma paper p"],"Rivelatore carta","foma-handbook",{"dilutions":["working solution"],"fomaspeedTimeSeconds":[60,90],"dataType":"DATO DIRETTO"},True)
record("paperdev-fomatol-pw","FOMATOL PW","FOMA",["PAPER_DEVELOPER","CHEMISTRY"],["fomatol pw","foma warmtone developer"],"Rivelatore carta warmtone","foma-handbook",{"dilutions":["stock","1+1","1+2"],"dataType":"DATO DIRETTO"},True)
record("fix-fomafix-p","FOMAFIX P","FOMA",["FIXER","CHEMISTRY"],["foma fix p","fomafix powder"],"Fissaggio in polvere","foma-fomafix",{"dataType":"DATO DIRETTO","note":"Parametri assenti restano NON DOCUMENTATO."},True)
record("film-retropan320","RETROPAN 320 Soft","FOMA",["FILM"],["retropan","retro 320","foma retropan"],"Pellicola B/N · ISO 320","foma-handbook",{"nominalIso":320,"dataType":"DATO DIRETTO"},True)

def build(version, rows, note):
    payload={"note":note,"aliasesVersion":1,"sources":SOURCES,"records":rows}
    compact=json.dumps(payload,ensure_ascii=False,separators=(",",":"))
    return {"catalogVersion":version,"schemaVersion":2,"payload":payload,"payloadSha256":hashlib.sha256(compact.encode("utf-8")).hexdigest()}

def local_catalog():
    return build(2,RECORDS,"Catalogo tecnico integrato v2: Smart Search offline-first, dati tecnici solo con provenienza esplicita.")

def remote_catalog():
    return build(3,RECORDS+REMOTE,"Catalogo tecnico remoto v3: estensione opzionale del catalogo integrato; nessun dato personale.")

def dump(obj):
    return json.dumps(obj,ensure_ascii=False,indent=2)+"\n"

if __name__=="__main__":
    import sys
    mode=sys.argv[1] if len(sys.argv)>1 else "local"
    print(dump(remote_catalog() if mode=="remote" else local_catalog()),end="")
