from pathlib import Path

# v0.2.2: i risultati mostrati all'utente devono essere ENTITA' (prodotti/pellicole),
# non pagine, menu, categorie o sezioni di siti. Inoltre il popup prodotti deve
# essere realmente scrollabile quando i risultati sono molti.

# ---------------------------------------------------------------------------
# 1) SourceBroker: filtra severamente i risultati dei siti produttori.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/SourceBroker.java')
s = p.read_text(encoding='utf-8')

s = s.replace(
'''            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, true, 14 - out.size())) put(out, r);''',
'''            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, true, 14 - out.size())) {
                if (strictChemicalEntity(query, r)) put(out, r);
            }''', 1)

s = s.replace(
'''            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, false, 14 - out.size())) put(out, r);''',
'''            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, false, 14 - out.size())) {
                if (strictFilmEntity(query, r)) put(out, r);
            }''', 1)

marker = '''    static boolean isManufacturerUrl(String url) {'''
helpers = r'''    /**
     * Un risultato di ricerca puo' essere mostrato solo se descrive un prodotto
     * chimico fotografico. Il solo fatto di provenire da un sito produttore NON basta.
     */
    private static boolean strictChemicalEntity(String query, OnlineCatalogSearch.SearchResult r) {
        if (r == null) return false;
        String title = norm(r.title);
        String snippet = norm(r.snippet);
        String all = title + " " + snippet;
        String q = norm(query);
        if (title.length() < 3) return false;

        // Pagine di navigazione/categorie/editoriali: mai prodotti.
        if (strictAny(title,
                "support", "kontakt", "contact", "partner werden", "privacy", "impressum",
                "digitale kameras", "digital cameras", "fotodrucker", "printers",
                "batterien", "akkus", "ladegeraete", "energy storage", "portable energy",
                "analoge fotografie und einwegkameras", "disposable cameras",
                "news", "blog", "guide", "review", "about us", "homepage")
                && !strictAny(all, "developer", "rivelatore", "fixer", "fissaggio", "stop bath", "arresto")) {
            return false;
        }

        // Deve esserci prova esplicita che si tratti di chimica fotografica.
        boolean chemistry = strictAny(all,
                "film developer", "paper developer", "photographic developer", "developer concentrate",
                "black white developer", "b&w developer", "bw developer", "rivelatore", "sviluppo pellicola",
                "sviluppo carta", "fixer", "fissaggio", "fixing bath", "stop bath", "arresto",
                "rodinal", "r09", "one shot", "one-shot", "entwickler", "fixierer",
                "photographic chemistry", "photo chemistry");
        if (!chemistry) return false;

        // La query deve riferirsi davvero al risultato, non solo al dominio visitato.
        if (q.length() >= 3 && !title.contains(q) && !snippet.contains(q)) {
            Brand b = brandForQuery(query);
            if (b == null) return false;
            boolean aliasHit = false;
            for (String a : b.aliases) {
                String na = norm(a);
                if (title.contains(na) || snippet.contains(na)) { aliasHit = true; break; }
            }
            if (!aliasHit) return false;
        }
        return true;
    }

    /** Un risultato pellicola deve contenere prove esplicite di essere una pellicola. */
    private static boolean strictFilmEntity(String query, OnlineCatalogSearch.SearchResult r) {
        if (r == null) return false;
        String title = norm(r.title);
        String snippet = norm(r.snippet);
        String all = title + " " + snippet;
        String q = norm(query);
        if (title.length() < 3) return false;

        if (strictAny(title,
                "support", "kontakt", "contact", "partner werden", "privacy", "impressum",
                "digital camera", "digitale kamera", "printer", "fotodrucker", "battery", "batterien",
                "lens", "objective", "objektiv", "instax", "news", "blog", "guide", "review")
                && !strictAny(all, " film", "pellicola", "35mm", "35 mm", "120 film", "roll film")) {
            return false;
        }
        boolean film = strictAny(all,
                "photographic film", "black white film", "black and white film", "b&w film", "bw film",
                "pellicola", "negative film", "roll film", "35mm film", "35 mm film", "120 film",
                "iso 25", "iso 50", "iso 80", "iso 100", "iso 125", "iso 200", "iso 400", "iso 800", "iso 3200");
        if (!film) return false;
        if (q.length() >= 3 && !title.contains(q) && !snippet.contains(q)) {
            Brand b = brandForQuery(query);
            if (b == null) return false;
            boolean aliasHit = false;
            for (String a : b.aliases) {
                String na = norm(a);
                if (title.contains(na) || snippet.contains(na)) { aliasHit = true; break; }
            }
            if (!aliasHit) return false;
        }
        return true;
    }

    private static boolean strictAny(String s, String... terms) {
        if (s == null) return false;
        for (String term : terms) if (s.contains(norm(term))) return true;
        return false;
    }

'''
if marker not in s:
    raise SystemExit('SourceBroker insertion marker missing')
s = s.replace(marker, helpers + marker, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 2) OnlineCatalogSearch: il fallback web non puo' mostrare risultati grezzi.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/OnlineCatalogSearch.java')
s = p.read_text(encoding='utf-8')

old = '''        raw.addAll(searchWeb(q + " photographic developer fixer stop bath chemistry"));'''
new = '''        raw.addAll(strictChemicalWebResults(q,
                searchWeb("\\\"" + q + "\\\" photographic developer rivelatore fixer fissaggio rodinal R09 stop bath")));'''
if old not in s:
    raise SystemExit('OnlineCatalogSearch chemical fallback marker missing')
s = s.replace(old, new, 1)

old = '''        raw.addAll(searchWeb(q + " black white photographic film ISO 35mm 120"));'''
new = '''        raw.addAll(strictFilmWebResults(q,
                searchWeb("\\\"" + q + "\\\" photographic film pellicola ISO 35mm 120")));'''
if old not in s:
    raise SystemExit('OnlineCatalogSearch film fallback marker missing')
s = s.replace(old, new, 1)

marker = '''    private static String safeQuery(String q) {'''
helpers = r'''    private static List<SearchResult> strictChemicalWebResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        String q = normalize(query);
        if (raw == null) return out;
        for (SearchResult r : raw) {
            String title = normalize(r.title);
            String snippet = normalize(r.snippet);
            String all = title + " " + snippet;
            if (title.length() < 3) continue;
            if (strictSearchAny(title,
                    "support", "contact", "kontakt", "partner werden", "privacy", "impressum",
                    "digital cameras", "digitale kameras", "fotodrucker", "printers", "battery", "batterien",
                    "energy storage", "portable energy", "disposable cameras", "news", "blog", "guide", "review")
                    && !strictSearchAny(all, "developer", "rivelatore", "fixer", "fissaggio", "stop bath", "arresto")) continue;
            if (!strictSearchAny(all,
                    "film developer", "paper developer", "photographic developer", "developer concentrate",
                    "rivelatore", "fixer", "fissaggio", "fixing bath", "stop bath", "arresto",
                    "rodinal", "r09", "one shot", "one-shot", "entwickler", "fixierer",
                    "photographic chemistry", "photo chemistry")) continue;
            if (q.length() >= 3 && !title.contains(q) && !snippet.contains(q)) continue;
            out.add(r);
            if (out.size() >= 14) break;
        }
        return dedupe(out, 14);
    }

    private static List<SearchResult> strictFilmWebResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        String q = normalize(query);
        if (raw == null) return out;
        for (SearchResult r : raw) {
            String title = normalize(r.title);
            String snippet = normalize(r.snippet);
            String all = title + " " + snippet;
            if (title.length() < 3) continue;
            if (strictSearchAny(title,
                    "support", "contact", "kontakt", "partner werden", "privacy", "impressum",
                    "digital camera", "digitale kamera", "printer", "fotodrucker", "battery", "batterien",
                    "lens", "objective", "objektiv", "news", "blog", "guide", "review")
                    && !strictSearchAny(all, " film", "pellicola", "35mm", "35 mm", "120 film")) continue;
            if (!strictSearchAny(all,
                    "photographic film", "black white film", "black and white film", "b&w film", "bw film",
                    "pellicola", "negative film", "roll film", "35mm film", "35 mm film", "120 film",
                    "iso 25", "iso 50", "iso 80", "iso 100", "iso 125", "iso 200", "iso 400", "iso 800", "iso 3200")) continue;
            if (q.length() >= 3 && !title.contains(q) && !snippet.contains(q)) continue;
            out.add(r);
            if (out.size() >= 16) break;
        }
        return dedupe(out, 16);
    }

    private static boolean strictSearchAny(String s, String... terms) {
        if (s == null) return false;
        for (String term : terms) if (s.contains(normalize(term))) return true;
        return false;
    }

'''
if marker not in s:
    raise SystemExit('OnlineCatalogSearch insertion marker missing')
s = s.replace(marker, helpers + marker, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 3) UI: popup prodotti interamente scrollabile + conteggio dei risultati visibili.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

old = '''        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(wrap)'''
new = '''        ScrollView addProductScroll = new ScrollView(this);
        addProductScroll.setFillViewport(false);
        addProductScroll.addView(wrap);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(addProductScroll)'''
if old not in s:
    raise SystemExit('Add product dialog marker missing')
s = s.replace(old, new, 1)

s = s.replace(
'''                        status.setText(results.isEmpty()
                                ? "Online: nessun risultato. Mostro i dati locali disponibili."
                                : "Online: " + results.size() + " risultati trovati. Tocca un risultato.");''',
'''                        status.setText(visible.isEmpty()
                                ? "Nessun prodotto trovato."
                                : visible.size() + " prodotti trovati. Tocca un prodotto.");''', 1)

s = s.replace(
'''                        filmSearchStatus.setText(results.isEmpty()
                                ? "Online: nessun risultato; mostro i dati locali."
                                : "Online: " + results.size() + " risultati trovati. Tocca un risultato.");''',
'''                        filmSearchStatus.setText(visible.isEmpty()
                                ? "Nessuna pellicola trovata."
                                : visible.size() + " pellicole trovate. Tocca una pellicola.");''', 1)

p.write_text(s, encoding='utf-8')
print('v0.2.2 strict entity search + scroll patch applied')
