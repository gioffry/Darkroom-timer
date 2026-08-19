from pathlib import Path

# OnlineCatalogSearch: merge generic broker + read official HTML/PDF + generic manufacturer trust
p = Path('assistant/src/main/java/it/darkroom/assistant/OnlineCatalogSearch.java')
s = p.read_text(encoding='utf-8')

old = '''    static List<SearchResult> searchChemicals(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, true, raw);
        raw.addAll(searchWeb(q + " photographic developer fixer stop bath chemistry"));
        return filterChemicalResults(q, dedupe(raw, 30));
    }'''
new = '''    static List<SearchResult> searchChemicals(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, true, raw);
        raw.addAll(SourceBroker.searchChemicals(q));
        raw.addAll(searchWeb(q + " photographic developer fixer stop bath chemistry"));
        return filterChemicalResults(q, dedupe(raw, 40));
    }'''
if old not in s: raise SystemExit('searchChemicals marker missing')
s = s.replace(old,new,1)

old = '''    static List<SearchResult> searchFilms(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, false, raw);
        raw.addAll(searchWeb(q + " black white photographic film ISO 35mm 120"));
        return filterFilmResults(q, dedupe(raw, 30));
    }'''
new = '''    static List<SearchResult> searchFilms(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, false, raw);
        raw.addAll(SourceBroker.searchFilms(q));
        raw.addAll(searchWeb(q + " black white photographic film ISO 35mm 120"));
        return filterFilmResults(q, dedupe(raw, 40));
    }'''
if old not in s: raise SystemExit('searchFilms marker missing')
s = s.replace(old,new,1)

old = '''    private static boolean brandQueryMatchesDomain(String query, String url) {
        String q = normalize(query), u = normalize(url);
        return (q.startsWith("bell") && u.contains("bellinifoto")) ||
                (q.startsWith("rolle") && u.contains("rolleianalog")) ||
                ((q.contains("p30") || q.startsWith("ferr")) && u.contains("filmferrania"));
    }'''
new = '''    private static boolean brandQueryMatchesDomain(String query, String url) {
        if (SourceBroker.matchesQueryDomain(query, url)) return true;
        String q = normalize(query), u = normalize(url);
        return (q.startsWith("bell") && u.contains("bellinifoto")) ||
                (q.startsWith("rolle") && u.contains("rolleianalog")) ||
                ((q.contains("p30") || q.startsWith("ferr")) && u.contains("filmferrania"));
    }'''
if old not in s: raise SystemExit('brandQueryMatchesDomain marker missing')
s = s.replace(old,new,1)

old = '''    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        String sourceUrl = canonicalProductUrl(r.title, r.url);
        String body = "";
        if (!sourceUrl.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(sourceUrl, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);'''
new = '''    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        ChemicalData broker = SourceBroker.enrichChemical(r);
        if (broker != null && (broker.roles != 0 || broker.filmDilutions.length > 0 || broker.paperDilutions.length > 0 || broker.workingDilution != null)) return broker;
        String sourceUrl = canonicalProductUrl(r.title, r.url);
        String body = "";
        try { body = SourceText.fetchText(sourceUrl, 600000); } catch (Exception ignored) {}
        String focus = focusAroundProduct(body, r.title);'''
if old not in s: raise SystemExit('enrichChemical marker missing')
s = s.replace(old,new,1)

old = '''    static FilmData enrichFilm(SearchResult r) {
        if (r == null) return new FilmData("", 0, null, "");
        String body = "";
        if (!r.url.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(r.url, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);'''
new = '''    static FilmData enrichFilm(SearchResult r) {
        if (r == null) return new FilmData("", 0, null, "");
        FilmData broker = SourceBroker.enrichFilm(r);
        if (broker != null && broker.iso > 0) return broker;
        String body = "";
        try { body = SourceText.fetchText(r.url, 600000); } catch (Exception ignored) {}
        String focus = focusAroundProduct(body, r.title);'''
if old not in s: raise SystemExit('enrichFilm marker missing')
s = s.replace(old,new,1)

old = '''    private static int trustedDomainScore(String url) {
        String s = normalize(url);
        if (containsAny(s, "bellinifoto it", "rolleianalog com", "filmferrania com", "ilfordphoto com",
                "harmantechnology com", "foma cz", "adox de", "fotoimpex com", "kodak com", "kodakalaris com")) return 3;
        if (s.contains("digitaltruth com")) return 2;
        return 0;
    }'''
new = '''    private static int trustedDomainScore(String url) {
        if (SourceBroker.isManufacturerUrl(url)) return 3;
        String s = normalize(url);
        if (containsAny(s, "bellinifoto it", "rolleianalog com", "filmferrania com", "ilfordphoto com",
                "harmantechnology com", "foma cz", "adox de", "fotoimpex com", "kodak com", "kodakalaris com")) return 3;
        if (s.contains("digitaltruth com")) return 2;
        return 0;
    }'''
if old not in s: raise SystemExit('trustedDomainScore marker missing')
s = s.replace(old,new,1)

p.write_text(s, encoding='utf-8')

# ChemistrySpecEngine: resolve official manufacturer source and parse PDFs too
p = Path('assistant/src/main/java/it/darkroom/assistant/ChemistrySpecEngine.java')
s = p.read_text(encoding='utf-8')
old = '''        List<Candidate> candidates = new ArrayList<>();
        String pn = normalize(productName);'''
new = '''        List<Candidate> candidates = new ArrayList<>();
        String resolvedOfficial = SourceBroker.resolveOfficialUrl(productName, true, initialSourceUrl);
        if (isHttp(resolvedOfficial)) candidates.add(new Candidate(resolvedOfficial, productName));
        String pn = normalize(productName);'''
if old not in s: raise SystemExit('spec candidate start marker missing')
s = s.replace(old,new,1)
old = '''                String text = cleanText(fetch(c.url, 600000));'''
new = '''                String text = SourceText.fetchText(c.url, 600000);'''
if old not in s: raise SystemExit('spec source read marker missing')
s = s.replace(old,new,1)
old = '''        if (containsAny(s,"foma.cz","ilfordphoto.com","harmantechnology.com","adox.de","bellinifoto.it","rolleianalog.com","kodakalaris.com","kodak.com","ferrania.it","bergger.com","cinestillfilm.com")) return 100;'''
new = '''        if (SourceBroker.isManufacturerUrl(url)) return 100;
        if (containsAny(s,"foma.cz","ilfordphoto.com","harmantechnology.com","adox.de","bellinifoto.it","rolleianalog.com","kodakalaris.com","kodak.com","ferrania.it","bergger.com","cinestillfilm.com")) return 100;'''
if old not in s: raise SystemExit('spec domain marker missing')
s = s.replace(old,new,1)
p.write_text(s, encoding='utf-8')

# DevTimeEngine: producer PDF/HTML source must also be readable, then Massive Dev Chart fallback remains
p = Path('assistant/src/main/java/it/darkroom/assistant/DevTimeEngine.java')
s = p.read_text(encoding='utf-8')
old = '''                String html = fetch(sourceUrl, 700000);
                List<Row> rows = parseGenericTable(html, sourceUrl, "Produttore");'''
new = '''                String html = SourceText.fetchText(sourceUrl, 700000);
                List<Row> rows = parseGenericTable(html, sourceUrl, "Produttore");'''
if old not in s: raise SystemExit('DevTime producer source marker missing')
s = s.replace(old,new,1)
p.write_text(s, encoding='utf-8')

# Application: initialize PDFBox once
p = Path('assistant/src/main/java/it/darkroom/assistant/DarkroomAssistantApp.java')
s = p.read_text(encoding='utf-8')
if 'com.tom_roush.pdfbox.android.PDFBoxResourceLoader' not in s:
    s = s.replace('import android.content.SharedPreferences;','import android.content.SharedPreferences;\nimport com.tom_roush.pdfbox.android.PDFBoxResourceLoader;')
s = s.replace('''        super.onCreate();
        cleanupInvalidInventoryEntries();''','''        super.onCreate();
        PDFBoxResourceLoader.init(getApplicationContext());
        cleanupInvalidInventoryEntries();''',1)
p.write_text(s, encoding='utf-8')

print('v0.2.0 source-brain patch applied')
