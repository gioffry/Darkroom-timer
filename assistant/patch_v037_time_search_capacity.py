from pathlib import Path
import re

# v0.3.7
# - ricerca rivelatori per marca (es. "kod" -> D-76 / HC-110 / Xtol ...)
# - diagnostica precisa quando la combinazione tempo non esiste
# - fallback locale FP4+ + Foma Universal 1+3 @125, chiaramente marcato come STIMA
# - correzione Compard Fix Ag Plus per pellicola: 1+4 e capacita' dichiarata 20-40 film/L
# - messaggi riutilizzo sensati: niente "non determinato" + contatori fasulli
# - il pulsante registra solo l'utilizzo dei bagni, non un log sviluppo inesistente

# ---------------------------------------------------------------------------
# 1) MdcOfflineStore: alias marca + diagnostica combinazioni.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')

pattern = re.compile(r'''    static List<OnlineCatalogSearch\.SearchResult> searchDevelopers\(String query, int max\) \{.*?\n    \}\n\n    static List<OnlineCatalogSearch\.SearchResult> searchFilms''', re.S)
replacement = r'''    static List<OnlineCatalogSearch.SearchResult> searchDevelopers(String query, int max) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        if (!isReady()) return out;
        String q = norm(query);
        if (q.length() < 3) return out;
        SQLiteDatabase db = helper.getReadableDatabase();
        LinkedHashSet<String> names = new LinkedHashSet<>();
        try (Cursor c = db.rawQuery(
                "SELECT name FROM developers WHERE norm_name LIKE ? LIMIT 120",
                new String[]{"%" + q + "%"})) {
            while (c.moveToNext()) names.add(c.getString(0));
        }

        // Digitaltruth usa spesso il nome della formula senza il marchio.
        // Questi alias NON aggiungono prodotti: rendono ricercabili nomi gia' presenti nel DB.
        if (q.startsWith("kod") || q.equals("kodak")) {
            addKnownDevelopers(names, db, new String[]{
                    "D-76", "HC-110", "Xtol", "TMax Dev", "TMax RS",
                    "Microdol-X", "DK-50", "D-23", "D-25", "D-96", "D-97", "D-19", "D-11"});
        }
        if (q.startsWith("ilf") || q.equals("ilford")) {
            addKnownDevelopers(names, db, new String[]{
                    "ID-11", "Ilfosol 3", "Ilfotec DD-X", "Ilfotec HC", "Ilfotec LC29",
                    "Microphen", "Perceptol"});
        }
        if (q.startsWith("fom") || q.equals("foma")) {
            addKnownDevelopers(names, db, new String[]{
                    "Foma Universal", "Fomadon R09", "Fomadon LQN", "Fomadon LQR",
                    "Fomadon P", "Fomadon Excel", "Foma Retro Special", "Foma W-17 Hydrofen"});
        }
        if (q.startsWith("rol") || q.equals("rollei")) {
            addKnownDevelopers(names, db, new String[]{
                    "Rollei Supergrain", "Rollei RLS", "Rollei RHS", "Rollei High Speed"});
        }

        List<String> sorted = new ArrayList<>(names);
        sortMatches(sorted, q);
        for (String name : sorted) {
            out.add(new OnlineCatalogSearch.SearchResult(
                    name, SOURCE_HOME, "MDC_OFFLINE_DEVELOPER"));
            if (out.size() >= max) break;
        }
        return out;
    }

    private static void addKnownDevelopers(Set<String> names, SQLiteDatabase db, String[] candidates) {
        for (String candidate : candidates) {
            try (Cursor c = db.rawQuery(
                    "SELECT name FROM developers WHERE norm_name=? LIMIT 1",
                    new String[]{norm(candidate)})) {
                if (c.moveToFirst()) names.add(c.getString(0));
            }
        }
    }

    static List<OnlineCatalogSearch.SearchResult> searchFilms'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('searchDevelopers replacement failed')

marker = '''    static DevTimeEngine.Result lookup(String filmName, String format, String developer,'''
helper = r'''    static String combinationDiagnostic(String filmName, String developer, String dilution, int iso) {
        if (!isReady()) return "Database offline non disponibile.";
        SQLiteDatabase db = helper.getReadableDatabase();
        String fn = norm(stripFormat(filmName));
        String dn = norm(developer);
        String dil = normDilution(dilution);

        List<String> isos = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT DISTINCT iso FROM times WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso>0 ORDER BY iso",
                new String[]{fn, dn, dil})) {
            while (c.moveToNext()) isos.add(String.valueOf(c.getInt(0)));
        }
        if (!isos.isEmpty()) {
            return "Digitaltruth contiene questa pellicola + rivelatore + diluizione agli ISO: " +
                    joinValues(isos) + ", ma non a ISO " + iso + ".";
        }

        List<String> dils = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT DISTINCT dilution FROM times WHERE film_norm=? AND developer_norm=? AND dilution<>'' ORDER BY dilution",
                new String[]{fn, dn})) {
            while (c.moveToNext()) dils.add(c.getString(0));
        }
        if (!dils.isEmpty()) {
            return "Digitaltruth contiene questa pellicola + rivelatore, ma con diluizioni: " +
                    joinValues(dils) + ".";
        }

        try (Cursor c = db.rawQuery(
                "SELECT 1 FROM times WHERE film_norm=? AND developer_norm=? LIMIT 1",
                new String[]{fn, dn})) {
            if (c.moveToFirst()) return "La combinazione esiste nel database, ma non con i parametri selezionati.";
        }
        return "Digitaltruth non contiene una riga per questa pellicola + rivelatore. " +
                "Temperatura e JOBO possono essere calcolati solo dopo avere un tempo base.";
    }

    private static String joinValues(List<String> values) {
        StringBuilder b = new StringBuilder();
        for (String v : values) {
            if (b.length() > 0) b.append(", ");
            b.append(v);
        }
        return b.toString();
    }

'''
if marker not in s:
    raise SystemExit('lookup marker for diagnostic missing')
s = s.replace(marker, helper + marker, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 2) DevTimeEngine: MDC -> ricetta locale -> diagnostica precisa.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/DevTimeEngine.java')
s = p.read_text(encoding='utf-8')
old = '''        Result offline = MdcOfflineStore.lookup(filmName, format, developer, dilution, iso, targetTemp);
        if (offline != null) return offline;
        return Result.notFound("Nessuna combinazione esatta nel database offline Digitaltruth per pellicola + rivelatore + diluizione + ISO.");'''
new = '''        Result offline = MdcOfflineStore.lookup(filmName, format, developer, dilution, iso, targetTemp);
        if (offline != null) return offline;
        Result local = LocalRecipeEngine.lookup(filmName, format, developer, dilution, iso, targetTemp);
        if (local != null) return local;
        return Result.notFound(MdcOfflineStore.combinationDiagnostic(
                filmName, developer, dilution, iso));'''
if old not in s:
    raise SystemExit('DevTime offline fallback marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 3) Activity: correggi dati / riutilizzo / etichetta registrazione.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# Compard Fix Ag Plus: scheda ufficiale film 1+4, carta RC tipicamente 1+9 disponibile.
old = '''            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[]{"1+5"}, new String[]{"1+9"}, "1+5", null,
                    90, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),'''
new = '''            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    90, "", ChemistrySpecEngine.REUSE_REUSABLE, 20, 2.1),'''
if old not in s:
    raise SystemExit('Compard curated marker missing')
s = s.replace(old, new, 1)

# Foma Universal nel flusso pellicola dell'app: monouso 1+3, niente contatore riuso.
old = '''    private Product offlineDeveloperProduct(String canonicalName) {
        return new Product(canonicalName, ROLE_FILM_DEV, false,
                MdcOfflineStore.dilutionsForDeveloper(canonicalName), new String[0], null,
                null, -1, "", ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);
    }'''
new = '''    private Product offlineDeveloperProduct(String canonicalName) {
        int reuse = "Foma Universal".equalsIgnoreCase(canonicalName)
                ? ChemistrySpecEngine.REUSE_ONE_SHOT
                : ChemistrySpecEngine.REUSE_UNKNOWN;
        return new Product(canonicalName, ROLE_FILM_DEV, false,
                MdcOfflineStore.dilutionsForDeveloper(canonicalName), new String[0], null,
                null, -1, "", reuse, -1, -1);
    }'''
if old not in s:
    raise SystemExit('offlineDeveloperProduct marker missing')
s = s.replace(old, new, 1)

# Il bottone non e' un log sviluppo: registra i contatori dei bagni.
s = s.replace('actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY)',
              'actionButton("REGISTRA UTILIZZO BAGNI", BURGUNDY)', 1)
s = s.replace('toast(rolls + (rolls == 1 ? " rullo registrato." : " rulli registrati."));',
              'toast(rolls + (rolls == 1 ? " rullo aggiunto ai contatori dei bagni." : " rulli aggiunti ai contatori dei bagni."));', 1)

# Status film: niente contatori per riutilizzo sconosciuto; casi curati con testo utile.
pattern = re.compile(r'''    private String filmCapacityStatus\(Product p, double volumeMl\) \{.*?\n    \}\n\n    private String paperCapacityStatus''', re.S)
replacement = r'''    private String filmCapacityStatus(Product p, double volumeMl) {
        if (p == null) return "—";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: prepara il bagno fresco e scartalo dopo lo sviluppo.";

        int used = prefs.getInt("film_used_" + key(p.name), 0);
        float storedVol = prefs.getFloat("film_bath_volume_" + key(p.name), 0f);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;

        if ("Adox Adostop ECO".equalsIgnoreCase(p.name)) {
            return "Riutilizzabile fino al viraggio dell'indicatore verso verde/blu. " +
                    "Rulli passati nel bagno: " + used + ".";
        }
        if ("Compard Fix Ag Plus".equalsIgnoreCase(p.name)) {
            int minCap = (int)Math.floor(20.0 * volumeMl / 1000.0);
            int maxCap = (int)Math.floor(40.0 * volumeMl / 1000.0);
            return "Riutilizzabile · scheda Compard 1+4: 20–40 pellicole/L. " +
                    "Con " + fmt(volumeMl) + " ml ≈ " + minCap + "–" + maxCap +
                    " pellicole · passate " + used + ".";
        }

        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE)
            return "Il database tempi non contiene dati affidabili sul riutilizzo: nessun contatore applicato.";
        if (p.filmCapacityPerLiter <= 0)
            return "Riutilizzabile; il produttore non esprime la capacità in rulli. " +
                    "Rulli passati nel bagno: " + used + ".";
        int capacity = (int) Math.floor(p.filmCapacityPerLiter * volumeMl / 1000.0 + 1e-9);
        int remaining = Math.max(0, capacity - used);
        return "Bagno " + fmt(volumeMl) + " ml · capacità almeno " + capacity +
                " rulli · passati " + used + " · residui almeno " + remaining + ".";
    }

    private String paperCapacityStatus'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('filmCapacityStatus replacement failed')

# Non incrementare mai un contatore quando il riutilizzo e' sconosciuto.
old = '''    private void registerFilmUse(Product p, double volumeMl, int rolls) {
        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;'''
new = '''    private void registerFilmUse(Product p, double volumeMl, int rolls) {
        if (p == null || p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE) return;'''
if old not in s:
    raise SystemExit('registerFilmUse marker missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('v0.3.7 time/search/capacity patch applied')
