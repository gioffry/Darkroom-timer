from pathlib import Path
import re

# v0.3.2
# - ZERO ricerca web a runtime: solo SQLite incluso nell'APK
# - nessun merge con cataloghi fallback / vecchi risultati
# - ripara automaticamente prodotti storici corrotti (es. Rodinal=fixer)
# - forza nomi canonici Digitaltruth per rivelatori e pellicole

# ---------------------------------------------------------------------------
# MdcOfflineStore: nuovo DB, riconoscimento canonico rivelatori.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')
s = s.replace('private static final String DB_NAME = "mdc_offline_v031.sqlite";',
              'private static final String DB_NAME = "mdc_offline_v032.sqlite";', 1)

marker = '''    static DevTimeEngine.Result lookup(String filmName, String format, String developer,'''
helpers = r'''    static boolean isKnownDeveloper(String name) {
        if (!isReady() || name == null) return false;
        try (Cursor c = helper.getReadableDatabase().rawQuery(
                "SELECT 1 FROM developers WHERE norm_name=? LIMIT 1", new String[]{norm(name)})) {
            return c.moveToFirst();
        }
    }

    static String canonicalDeveloperName(String name) {
        if (!isReady() || name == null) return null;
        try (Cursor c = helper.getReadableDatabase().rawQuery(
                "SELECT name FROM developers WHERE norm_name=? LIMIT 1", new String[]{norm(name)})) {
            return c.moveToFirst() ? c.getString(0) : null;
        }
    }

    /**
     * Migrazione dei risultati spazzatura delle vecchie versioni.
     * Esempio: "Kodak Professional DEKTOL Paper Developer (To Make 1 gal)"
     * viene ricondotto a "Dektol" se il nome canonico del MDC compare come
     * sequenza di token completa. Sceglie sempre il match canonico piu' lungo.
     */
    static String canonicalDeveloperForLooseName(String legacyName) {
        if (!isReady() || legacyName == null) return null;
        String input = " " + norm(legacyName) + " ";
        String best = null;
        int bestLen = 0;
        try (Cursor c = helper.getReadableDatabase().rawQuery(
                "SELECT name,norm_name FROM developers", null)) {
            while (c.moveToNext()) {
                String name = c.getString(0);
                String n = c.getString(1);
                if (n == null || n.length() < 4) continue;
                String token = " " + n + " ";
                if (input.contains(token) && n.length() > bestLen) {
                    best = name;
                    bestLen = n.length();
                }
            }
        }
        return best;
    }

'''
if marker not in s:
    raise SystemExit('MdcOfflineStore lookup marker missing')
s = s.replace(marker, helpers + marker, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# OnlineCatalogSearch: solo facade del DB locale. Nessun fallback web.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/OnlineCatalogSearch.java')
s = p.read_text(encoding='utf-8')

# search methods were already replaced in v0.3.0; enforce them again.
s, n = re.subn(
    r'    static List<SearchResult> searchChemicals\(String query\) \{.*?\n    \}\n\n    static List<SearchResult> searchFilms',
    '''    static List<SearchResult> searchChemicals(String query) {\n        return MdcOfflineStore.searchDevelopers(query, 80);\n    }\n\n    static List<SearchResult> searchFilms''',
    s, count=1, flags=re.S)
if n != 1: raise SystemExit('pure-offline searchChemicals replacement failed')

s, n = re.subn(
    r'    static List<SearchResult> searchFilms\(String query\) \{.*?\n    \}\n\n    private static String safeQuery',
    '''    static List<SearchResult> searchFilms(String query) {\n        return MdcOfflineStore.searchFilms(query, 100);\n    }\n\n    private static String safeQuery''',
    s, count=1, flags=re.S)
if n != 1: raise SystemExit('pure-offline searchFilms replacement failed')

# Enrichment is also offline-only. Any non-MDC result is rejected rather than parsed from web.
start = s.find('    static ChemicalData enrichChemical(SearchResult r) {')
end = s.find('    static FilmData enrichFilm(SearchResult r) {', start)
if start < 0 or end < 0: raise SystemExit('enrichChemical boundaries missing')
chem = r'''    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || !MdcOfflineStore.isOfflineDeveloperResult(r)) return emptyChemical(r);
        String canonical = MdcOfflineStore.canonicalDeveloperName(r.title);
        if (canonical == null) canonical = r.title;
        String[] d = MdcOfflineStore.dilutionsForDeveloper(canonical);
        return new ChemicalData(canonical, ROLE_FILM_DEV, false, d, new String[0],
                null, null, -1, "");
    }

'''
s = s[:start] + chem + s[end:]

start = s.find('    static FilmData enrichFilm(SearchResult r) {')
# next helper after enrichFilm in current source
end_candidates = [s.find('\n    private static ', start+10), s.find('\n    static ', start+10)]
end_candidates = [x for x in end_candidates if x > start]
if not end_candidates: raise SystemExit('enrichFilm end boundary missing')
end = min(end_candidates)
film = r'''    static FilmData enrichFilm(SearchResult r) {
        if (r == null || !MdcOfflineStore.isOfflineFilmResult(r))
            return new FilmData("", 0, null, "");
        return new FilmData(r.title, MdcOfflineStore.nominalIsoForFilm(r.title), null, "");
    }
'''
s = s[:start] + film + s[end:]
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# DevTimeEngine: elimina completamente il percorso online dal metodo lookup.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/DevTimeEngine.java')
s = p.read_text(encoding='utf-8')
start = s.find('    static Result lookup(String filmName,')
end = s.find('    private static Result build(', start)
if start < 0 or end < 0: raise SystemExit('DevTime lookup boundaries missing')
lookup = r'''    static Result lookup(String filmName,
                         String format,
                         String developer,
                         String dilution,
                         int iso,
                         double targetTemp,
                         String filmSourceUrl,
                         String developerSourceUrl) {
        if (filmName == null || developer == null || dilution == null) {
            return Result.notFound("Parametri incompleti.");
        }
        if (targetTemp < 18.0 || targetTemp > 27.0) {
            return Result.notFound("La conversione temperatura automatica è limitata a 18–27 °C.");
        }
        if (!MdcOfflineStore.isReady()) {
            return Result.notFound("Database offline non disponibile.");
        }
        Result offline = MdcOfflineStore.lookup(filmName, format, developer, dilution, iso, targetTemp);
        if (offline != null) return offline;
        return Result.notFound("Nessuna combinazione esatta nel database offline Digitaltruth per pellicola + rivelatore + diluizione + ISO.");
    }

'''
s = s[:start] + lookup + s[end:]
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# Activity: ricerca SOLO DB, niente fallback locali; migrazione vecchio magazzino.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# After DB init, repair legacy product metadata once.
old = '''        MdcOfflineStore.init(getApplicationContext());
        showHome();
        ensureOfflineDatabase();'''
new = '''        MdcOfflineStore.init(getApplicationContext());
        repairLegacyInventoryFromOfflineDb();
        showHome();
        ensureOfflineDatabase();'''
if old not in s: raise SystemExit('Activity v031 onCreate marker missing')
s = s.replace(old, new, 1)

# Search lists must contain ONLY SQLite results; localProductMatches/localFilmMatches are now empty.
s, n = re.subn(r'''    private List<String> localProductMatches\(String q\) \{.*?\n    \}\n\n    private List<String> localFilmMatches\(String q\) \{.*?\n    \}''',
'''    private List<String> localProductMatches(String q) {\n        return new ArrayList<>();\n    }\n\n    private List<String> localFilmMatches(String q) {\n        return new ArrayList<>();\n    }''', s, count=1, flags=re.S)
if n != 1: raise SystemExit('local fallback removal failed')

# Known MDC developer always overrides stale saved metadata (Rodinal can never remain a fixer).
old = '''    private Product findProduct(String name) {
        if (name == null) return null;
        Product saved = loadSavedProduct(name.trim());'''
new = '''    private Product findProduct(String name) {
        if (name == null) return null;
        String canonical = MdcOfflineStore.canonicalDeveloperName(name.trim());
        if (canonical != null) return offlineDeveloperProduct(canonical);
        Product saved = loadSavedProduct(name.trim());'''
if old not in s: raise SystemExit('findProduct repair marker missing')
s = s.replace(old, new, 1)

# No fallback films in search/calculation.
s, n = re.subn(r'''    private FilmStock findFilm\(String name\) \{.*?\n    \}''',
'''    private FilmStock findFilm(String name) {\n        return null;\n    }''', s, count=1, flags=re.S)
if n != 1: raise SystemExit('findFilm fallback removal failed')

# Insert migration + offline Product helper before persistence section.
marker = '''    // ---------------------------------------------------------------------
    // PERSISTENZA MAGAZZINO
    // ---------------------------------------------------------------------'''
methods = r'''    private Product offlineDeveloperProduct(String canonicalName) {
        return new Product(canonicalName, ROLE_FILM_DEV, false,
                MdcOfflineStore.dilutionsForDeveloper(canonicalName), new String[0], null,
                null, -1, "", ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);
    }

    private void repairLegacyInventoryFromOfflineDb() {
        if (!MdcOfflineStore.isReady()) return;
        Set<String> oldSet = getInventory();
        if (oldSet.isEmpty()) return;
        Set<String> newSet = new HashSet<>();
        SharedPreferences.Editor moveDates = prefs.edit();
        for (String oldName : oldSet) {
            String canonical = MdcOfflineStore.canonicalDeveloperName(oldName);
            if (canonical == null) canonical = MdcOfflineStore.canonicalDeveloperForLooseName(oldName);
            if (canonical == null) {
                newSet.add(oldName);
                continue;
            }
            long opened = prefs.getLong("opened_" + key(oldName), 0L);
            Product corrected = offlineDeveloperProduct(canonical);
            saveProductMetadata(corrected);
            newSet.add(canonical);
            if (!oldName.equalsIgnoreCase(canonical)) {
                deleteProductMetadata(oldName);
                moveDates.remove("opened_" + key(oldName));
                if (opened > 0) moveDates.putLong("opened_" + key(canonical), opened);
            }
        }
        moveDates.putStringSet("inventory", newSet).apply();
    }

'''
if marker not in s: raise SystemExit('persistence insertion marker missing')
s = s.replace(marker, methods + marker, 1)

# User-facing wording: no mention of online/source lookup.
repls = {
    'Ricerca online dopo 3 lettere.':'Cerca nel database dopo 3 lettere.',
    'Cerco online…':'Cerco nel database…',
    'Online: nessun risultato. Mostro i dati locali disponibili.':'Nessun rivelatore trovato nel database.',
    'Online: ':'',
    ' risultati trovati.':' risultati trovati.',
    'Recupero dati, preparazione e capacità online…':'Recupero dati dal database…',
    'Recupero ISO e formato…':'Recupero dati pellicola…',
    'La fonte non indica il formato in modo univoco.':'Scegli il formato della pellicola.',
    'Scheda locale; il tempo verrà cercato online.':'Pellicola selezionata.',
    'Scheda pellicola recuperata online.':'Pellicola presente nel database.',
    'Cerco online la combinazione esatta…':'Cerco la combinazione nel database…',
    'Fonte online salvata':'Fonte dati salvata'
}
for a,b in repls.items(): s=s.replace(a,b)

p.write_text(s, encoding='utf-8')
print('v0.3.2 pure offline patch applied')
