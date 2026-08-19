from pathlib import Path
import re

# v0.3.0: Digitaltruth is downloaded once into a private SQLite DB on the phone.
# Runtime searches + time lookup are OFFLINE. No Google/Bing/manufacturer-page parsing
# is allowed to decide what a film/developer is.

# ---------------------------------------------------------------------------
# OnlineCatalogSearch -> offline catalog only.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/OnlineCatalogSearch.java')
s = p.read_text(encoding='utf-8')

s, n = re.subn(
    r'    static List<SearchResult> searchChemicals\(String query\) \{.*?\n    \}\n\n    static List<SearchResult> searchFilms',
    '''    static List<SearchResult> searchChemicals(String query) {\n        return MdcOfflineStore.searchDevelopers(query, 60);\n    }\n\n    static List<SearchResult> searchFilms''',
    s, count=1, flags=re.S)
if n != 1: raise SystemExit('searchChemicals offline replacement failed')

s, n = re.subn(
    r'    static List<SearchResult> searchFilms\(String query\) \{.*?\n    \}\n\n    private static String safeQuery',
    '''    static List<SearchResult> searchFilms(String query) {\n        return MdcOfflineStore.searchFilms(query, 80);\n    }\n\n    private static String safeQuery''',
    s, count=1, flags=re.S)
if n != 1: raise SystemExit('searchFilms offline replacement failed')

old = '''    static ChemicalData enrichChemical(SearchResult r) {\n        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);'''
new = '''    static ChemicalData enrichChemical(SearchResult r) {\n        if (r != null && MdcOfflineStore.isOfflineDeveloperResult(r)) {\n            String[] d = MdcOfflineStore.dilutionsForDeveloper(r.title);\n            int roles = ROLE_FILM_DEV;\n            String n = r.title.toLowerCase(Locale.ROOT);\n            if (n.contains("dektol") || n.contains("multigrade") || n.contains("neutol") ||\n                    n.contains("eukobrom") || n.contains("dokumol") || n.contains("ecoprint") ||\n                    n.contains("liquidol")) roles |= ROLE_PAPER_DEV;\n            return new ChemicalData(r.title, roles, false, d, new String[0],\n                    null, null, -1, "https://www.digitaltruth.com/devchart.php");\n        }\n        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);'''
if old not in s: raise SystemExit('enrichChemical offline insertion marker missing')
s = s.replace(old, new, 1)

old = '''    static FilmData enrichFilm(SearchResult r) {\n        if (r == null) return new FilmData("", 0, null, "");'''
new = '''    static FilmData enrichFilm(SearchResult r) {\n        if (r != null && MdcOfflineStore.isOfflineFilmResult(r)) {\n            return new FilmData(r.title, MdcOfflineStore.nominalIsoForFilm(r.title), null,\n                    "https://www.digitaltruth.com/devchart.php");\n        }\n        if (r == null) return new FilmData("", 0, null, "");'''
if old not in s: raise SystemExit('enrichFilm offline insertion marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# DevTimeEngine -> offline SQLite first and exclusively once DB is ready.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/DevTimeEngine.java')
s = p.read_text(encoding='utf-8')
old = '''        if (targetTemp < 18.0 || targetTemp > 27.0) {\n            return Result.notFound("La conversione temperatura automatica è limitata a 18–27 °C.");\n        }\n\n        List<String> producerUrls = new ArrayList<>();'''
new = '''        if (targetTemp < 18.0 || targetTemp > 27.0) {\n            return Result.notFound("La conversione temperatura automatica è limitata a 18–27 °C.");\n        }\n\n        Result offline = MdcOfflineStore.lookup(filmName, format, developer, dilution, iso, targetTemp);\n        if (offline != null) return offline;\n        if (MdcOfflineStore.isReady()) {\n            return Result.notFound("Nessuna combinazione esatta nel database offline Digitaltruth per pellicola + rivelatore + diluizione + ISO.");\n        }\n\n        List<String> producerUrls = new ArrayList<>();'''
if old not in s: raise SystemExit('DevTime offline marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# Activity: initialize/sync DB and remove runtime-web language/behaviour.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')
old = '''        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);\n        showHome();'''
new = '''        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);\n        MdcOfflineStore.init(getApplicationContext());\n        showHome();\n        ensureOfflineDatabase();'''
if old not in s: raise SystemExit('Activity onCreate marker missing')
s = s.replace(old, new, 1)

marker = '''    @Override\n    public void onBackPressed() {'''
method = '''    private void ensureOfflineDatabase() {\n        if (MdcOfflineStore.isReady()) return;\n\n        LinearLayout box = new LinearLayout(this);\n        box.setOrientation(LinearLayout.VERTICAL);\n        box.setPadding(dp(18), dp(8), dp(18), dp(8));\n        TextView msg = label("Scarico una volta sola il database Massive Dev Chart sul telefono. Poi pellicole, rivelatori e tempi funzionano offline.", 14, WHITE, false);\n        box.addView(msg);\n        box.addView(space(12));\n        TextView progress = label("Preparazione…", 13, MUTED, false);\n        box.addView(progress);\n\n        AlertDialog syncDialog = new AlertDialog.Builder(this)\n                .setTitle("Database offline")\n                .setView(box)\n                .create();\n        syncDialog.setCancelable(false);\n        syncDialog.setCanceledOnTouchOutside(false);\n        syncDialog.show();\n\n        MdcOfflineStore.syncAsync(new MdcOfflineStore.ProgressListener() {\n            @Override public void onProgress(int done, int total, String text) {\n                runOnUiThread(() -> progress.setText(text));\n            }\n            @Override public void onComplete(boolean ok, String text, int films, int developers, int rows) {\n                runOnUiThread(() -> {\n                    syncDialog.dismiss();\n                    if (ok) {\n                        toast("Database pronto: " + films + " pellicole · " + developers + " rivelatori · " + rows + " combinazioni");\n                    } else {\n                        new AlertDialog.Builder(AssistantActivityV2.this)\n                                .setTitle("Database non scaricato")\n                                .setMessage(text + "\\n\\nServe Internet solo per questa sincronizzazione iniziale.")\n                                .setNegativeButton("CHIUDI", null)\n                                .setPositiveButton("RIPROVA", (d,w) -> ensureOfflineDatabase())\n                                .show();\n                    }\n                });\n            }\n        });\n    }\n\n'''
if marker not in s: raise SystemExit('Activity ensure insertion marker missing')
s = s.replace(marker, method + marker, 1)

# Offline results must never be re-enriched by generic web text parsing.
needle = '''            if (seed == null && data != null) {\n                seed = new Product(cleanSearchTitle(data.name), data.roles, data.stockPrep,\n                        data.filmDilutions, data.paperDilutions, data.workingDilution,\n                        data.stockInstructions, data.expiryDays, data.sourceUrl,\n                        ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);\n            }\n            if (seed == null) return;\n\n            String source = data != null && data.sourceUrl != null && !data.sourceUrl.isEmpty()'''
repl = '''            if (seed == null && data != null) {\n                seed = new Product(cleanSearchTitle(data.name), data.roles, data.stockPrep,\n                        data.filmDilutions, data.paperDilutions, data.workingDilution,\n                        data.stockInstructions, data.expiryDays, data.sourceUrl,\n                        ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);\n            }\n            if (seed == null) return;\n\n            if (r != null && MdcOfflineStore.isOfflineDeveloperResult(r)) {\n                Product direct = seed;\n                runOnUiThread(() -> startProductAddFlow(direct));\n                return;\n            }\n\n            String source = data != null && data.sourceUrl != null && !data.sourceUrl.isEmpty()'''
if needle not in s: raise SystemExit('Activity direct-offline product marker missing')
s = s.replace(needle, repl, 1)

# Language: what user sees is the local DB, not search-engine plumbing.
replacements = {
    'Ricerca online dopo 3 lettere.':'Cerca nel database offline dopo 3 lettere.',
    'Cerco online…':'Cerco nel database offline…',
    'Recupero dati, preparazione e capacità online…':'Recupero dati dal database offline…',
    'Recupero ISO e formato…':'Recupero dati pellicola…',
    'Scheda locale; il tempo verrà cercato online.':'Scheda locale.',
    'Scheda pellicola recuperata online.':'Pellicola presente nel database offline.',
    'Cerco online la combinazione esatta…':'Cerco la combinazione nel database offline…'
}
for a,b in replacements.items():
    s = s.replace(a,b)

p.write_text(s, encoding='utf-8')
print('v0.3.0 offline MDC patch applied')
