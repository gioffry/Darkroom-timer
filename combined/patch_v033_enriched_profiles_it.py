from pathlib import Path
import re, shutil, subprocess, sys

ROOT=Path('.')
DB=ROOT/'assistant/src/main/assets/mdc_full.sqlite'
if not DB.exists(): raise SystemExit('v033: mdc_full.sqlite missing')

def run(*a): subprocess.run([sys.executable,*map(str,a)],check=True)

# MDC resta la base; produttori riempiono solo campi vuoti.
run('assistant/db/enrich_developer_profiles.py')
for i in range(2,13):
    p=ROOT/f'assistant/db/producer_enrichment_batch{i}.json'
    if p.exists(): run('assistant/db/apply_manufacturer_batch.py',p)
for p in sorted((ROOT/'assistant/db').glob('macodirect_enrichment_batch*.json')):
    run('assistant/db/apply_macodirect_scoped_batch.py',p)
run('assistant/db/audit_developer_profiles.py')
run('assistant/db/audit_macodirect_scope.py')

# Aggiunge l'adapter italiano al sorgente ricostruito.
dst=ROOT/'assistant/src/main/java/it/darkroom/assistant/DeveloperProfileStore.java'
dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'combined/v033/DeveloperProfileStore.java',dst)

p=ROOT/'assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java'
s=p.read_text(encoding='utf-8')

# Mantiene le modifiche manuali utente prioritarie e usa il profilo evoluto per i rivelatori.
pat=re.compile(r'''    private Product findProduct\(String name\) \{.*?\n    \}\n\n    private FilmStock findFilm''',re.S)
rep=r'''    private Product findProduct(String name) {
        if (name == null) return null;
        String wanted = name.trim();
        Product saved = loadSavedProduct(wanted);
        if (saved != null) return saved;

        FullCatalogStore.Chemical cat = FullCatalogStore.chemical(wanted);
        DeveloperProfileStore.Profile prof = DeveloperProfileStore.profile(wanted);
        if (cat != null && (cat.roles & ~128) != 0) {
            String[] filmDil = cat.filmDilutions;
            if ((cat.roles & ROLE_FILM_DEV) != 0) {
                String[] mdc = DeveloperProfileStore.filmDilutions(cat.name);
                if (mdc.length > 0) filmDil = mdc;
            }
            String source = prof != null && !prof.sourceUrl.isEmpty() ? prof.sourceUrl : cat.sourceUrl;
            return new Product(cat.name, cat.roles,
                    cat.stockPrep || DeveloperProfileStore.stockPrep(prof),
                    filmDil, cat.paperDilutions, cat.workingDilution,
                    DeveloperProfileStore.prepItalian(prof), -1, source,
                    DeveloperProfileStore.reuseCode(prof), DeveloperProfileStore.filmCapacity(prof), -1);
        }

        String canonical = FullCatalogStore.canonicalDeveloper(wanted);
        if (canonical != null) {
            Product savedCanonical = loadSavedProduct(canonical);
            if (savedCanonical != null) return savedCanonical;
            prof = DeveloperProfileStore.profile(canonical);
            if (prof != null) return new Product(canonical, ROLE_FILM_DEV,
                    DeveloperProfileStore.stockPrep(prof), DeveloperProfileStore.filmDilutions(canonical),
                    new String[0], null, DeveloperProfileStore.prepItalian(prof), -1,
                    prof.sourceUrl, DeveloperProfileStore.reuseCode(prof), DeveloperProfileStore.filmCapacity(prof), -1);
            return offlineDeveloperProduct(canonical);
        }
        Product curated = curatedAuxByName(wanted);
        if (curated != null) return curated;
        for (Product q : fallbackProducts) if (q.name.equalsIgnoreCase(wanted)) return q;
        return null;
    }

    private FilmStock findFilm'''
s,n=pat.subn(rep,s,count=1)
if n!=1: raise SystemExit('v033: findProduct patch failed')

# Per i rivelatori mostra la scheda italiana; il testo inglese sorgente non arriva alla UI.
needle='''        FullCatalogStore.Chemical catalogInfo = FullCatalogStore.chemical(p.name);\n        if (catalogInfo != null) {'''
repl='''        DeveloperProfileStore.Profile developerProfile = DeveloperProfileStore.profile(p.name);\n        FullCatalogStore.Chemical catalogInfo = FullCatalogStore.chemical(p.name);\n        if (catalogInfo != null && developerProfile == null) {'''
if needle not in s: raise SystemExit('v033: catalog detail marker missing')
s=s.replace(needle,repl,1)
needle='''        msg.append("\\n\\n").append(reuseDescription(p));'''
repl='''        if (developerProfile != null) {\n            String detailsIt = DeveloperProfileStore.detailsItalian(p.name);\n            if (!detailsIt.isEmpty()) msg.append("\\n\\n").append(detailsIt);\n        } else {\n            msg.append("\\n\\n").append(reuseDescription(p));\n        }'''
if needle not in s: raise SystemExit('v033: reuse detail marker missing')
s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')

for marker in ['DeveloperProfileStore.profile','DeveloperProfileStore.detailsItalian','DeveloperProfileStore.filmDilutions']:
    if marker not in s: raise SystemExit('v033 marker missing: '+marker)
print('v033 enriched DB + Italian UI applied')
