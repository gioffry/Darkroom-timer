from pathlib import Path
import re

# v0.3.8
# - le modifiche manuali ai prodotti salvati hanno precedenza sui dati di catalogo/MDC
# - il catalogo curato stop/fix non sovrascrive piu' le modifiche dell'utente all'avvio
# - testi riutilizzo semplificati

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# 1) findProduct: prima i metadati salvati dall'utente, poi database/catalgogo.
pattern = re.compile(r'''    private Product findProduct\(String name\) \{.*?\n    \}\n\n    private FilmStock findFilm''', re.S)
replacement = r'''    private Product findProduct(String name) {
        if (name == null) return null;
        String wanted = name.trim();

        // Le modifiche fatte dall'utente sono autorevoli e devono sopravvivere
        // a riaperture, catalogo curato e riconoscimento MDC.
        Product saved = loadSavedProduct(wanted);
        if (saved != null) return saved;

        String canonical = MdcOfflineStore.canonicalDeveloperName(wanted);
        if (canonical != null) {
            Product savedCanonical = loadSavedProduct(canonical);
            if (savedCanonical != null) return savedCanonical;
            return offlineDeveloperProduct(canonical);
        }

        Product curated = curatedAuxByName(wanted);
        if (curated != null) return curated;

        for (Product p : fallbackProducts)
            if (p.name.equalsIgnoreCase(wanted)) return p;
        return null;
    }

    private FilmStock findFilm'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('findProduct replacement failed')

# 2) Non sovrascrivere mai un prodotto che l'utente ha gia' salvato/modificato.
pattern = re.compile(r'''    private void repairCuratedAuxInventory\(\) \{.*?\n    \}\n\n''', re.S)
replacement = r'''    private void repairCuratedAuxInventory() {
        Set<String> inv = getInventory();
        if (inv.isEmpty()) return;
        for (String name : inv) {
            Product curated = curatedAuxByName(name);
            if (curated == null) continue;
            if (loadSavedProduct(name) == null) saveProductMetadata(curated);
        }
    }

'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('repairCuratedAuxInventory replacement failed')

# 3) Testi semplici nel pannello RIUTILIZZO BAGNI.
old = '''        if ("Adox Adostop ECO".equalsIgnoreCase(p.name)) {
            return "Riutilizzabile fino al viraggio dell'indicatore verso verde/blu. " +
                    "Rulli passati nel bagno: " + used + ".";
        }
        if ("Compard Fix Ag Plus".equalsIgnoreCase(p.name)) {
            int minCap = (int)Math.floor(20.0 * volumeMl / 1000.0);
            int maxCap = (int)Math.floor(40.0 * volumeMl / 1000.0);
            return "Riutilizzabile · scheda Compard 1+4: 20–40 pellicole/L. " +
                    "Con " + fmt(volumeMl) + " ml ≈ " + minCap + "–" + maxCap +
                    " pellicole · passate " + used + ".";
        }'''
new = '''        if ("Adox Adostop ECO".equalsIgnoreCase(p.name)) {
            return "Riutilizzabile fino al viraggio verde/blu · usati " + used + " rulli.";
        }
        if ("Compard Fix Ag Plus".equalsIgnoreCase(p.name)) {
            int minCap = (int)Math.floor(20.0 * volumeMl / 1000.0);
            int maxCap = (int)Math.floor(40.0 * volumeMl / 1000.0);
            int minRemaining = Math.max(0, minCap - used);
            int maxRemaining = Math.max(0, maxCap - used);
            return "Riutilizzabile · capacità " + minCap + "–" + maxCap +
                    " pellicole · usate " + used + " · residue " +
                    minRemaining + "–" + maxRemaining + ".";
        }'''
if old not in s:
    raise SystemExit('capacity simplification marker missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('v0.3.8 edit persistence + simpler reuse text applied')