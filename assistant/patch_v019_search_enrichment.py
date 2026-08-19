from pathlib import Path

# --- OnlineCatalogSearch -------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/OnlineCatalogSearch.java')
s = p.read_text(encoding='utf-8')

old = '''        if (n.contains("rollei") || n.startsWith("rolle") || n.contains("supergrain") ||
                n.contains("rpx") || n.contains("retro") || n.contains("superpan")) {
            addRolleiCatalog(query, chemical, out);
        }'''
new = '''        boolean rolleiPrefix = n.length() >= 3 && (
                "rollei".startsWith(n) || "supergrain".startsWith(n) ||
                "rpx".startsWith(n) || "retro".startsWith(n) || "superpan".startsWith(n));
        if (n.contains("rollei") || n.startsWith("rolle") || n.contains("supergrain") ||
                n.contains("rpx") || n.contains("retro") || n.contains("superpan") || rolleiPrefix) {
            addRolleiCatalog(query, chemical, out);
        }'''
if old not in s:
    raise SystemExit('rollei trigger marker missing')
s = s.replace(old, new, 1)

old = '''                String href = firstUsefulHref(after, page);
                if (href.isEmpty()) href = page;
                out.add(new SearchResult(title, href,
                        "Rollei official " + (chemical ? "chemistry" : "film") + " data sheet"));'''
new = '''                String href = firstUsefulHref(after, page);
                if (href.isEmpty()) href = page;
                href = canonicalProductUrl(title, href);
                out.add(new SearchResult(title, href,
                        "Rollei official " + (chemical ? "chemistry" : "film") + " data sheet"));'''
if old not in s:
    raise SystemExit('rollei href marker missing')
s = s.replace(old, new, 1)

insert_before = '''    private static String firstUsefulHref(String html, String base) {'''
helper = '''    private static String canonicalProductUrl(String title, String fallback) {
        String t = normalize(title);
        if (t.contains("rollei supergrain"))
            return "https://www.rolleianalog.com/products/rollei-supergrain/?lang=en";
        return fallback == null ? "" : fallback;
    }

'''
if insert_before not in s:
    raise SystemExit('canonical helper insertion marker missing')
s = s.replace(insert_before, helper + insert_before, 1)

old = '''    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        String body = "";
        if (!r.url.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(r.url, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);'''
new = '''    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        String sourceUrl = canonicalProductUrl(r.title, r.url);
        String body = "";
        if (!sourceUrl.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(sourceUrl, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);'''
if old not in s:
    raise SystemExit('enrich source marker missing')
s = s.replace(old, new, 1)

old = '''        List<String> dilutions = extractDilutionsNearContext(all);
        String[] filmDil = (roles & ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];'''
new = '''        List<String> dilutions = extractDilutionsNearContext(all);
        if (dilutions.isEmpty() && roles != 0) dilutions = extractDilutionsLoose(focus);
        String[] filmDil = (roles & ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];'''
if old not in s:
    raise SystemExit('dilution fallback marker missing')
s = s.replace(old, new, 1)

old = '''        return new ChemicalData(cleanTitle(r.title), roles, stockPrep, filmDil, paperDil,
                working, instructions, expiry, r.url);'''
new = '''        return new ChemicalData(cleanTitle(r.title), roles, stockPrep, filmDil, paperDil,
                working, instructions, expiry, sourceUrl);'''
if old not in s:
    raise SystemExit('source return marker missing')
s = s.replace(old, new, 1)

insert_before = '''    private static String extractStockInstruction(String text) {'''
helper = '''    private static List<String> extractDilutionsLoose(String text) {
        Set<String> values = new LinkedHashSet<>();
        if (text == null) return new ArrayList<>(values);
        Matcher m = Pattern.compile("(?i)\\\\b(1\\\\s*[+:]\\\\s*\\\\d{1,3})\\\\b").matcher(text);
        while (m.find() && values.size() < 8)
            values.add(m.group(1).replace(" ", "").replace(':', '+'));
        return new ArrayList<>(values);
    }

'''
if insert_before not in s:
    raise SystemExit('loose dilution insertion marker missing')
s = s.replace(insert_before, helper + insert_before, 1)

p.write_text(s, encoding='utf-8')

# --- ChemistrySpecEngine -------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/ChemistrySpecEngine.java')
s = p.read_text(encoding='utf-8')

old = '''        List<Candidate> candidates = new ArrayList<>();
        if (isHttp(initialSourceUrl)) candidates.add(new Candidate(initialSourceUrl, productName));
        candidates.addAll(searchCandidateUrls(productName));'''
new = '''        List<Candidate> candidates = new ArrayList<>();
        String pn = normalize(productName);
        if (pn.contains("rollei supergrain")) {
            candidates.add(new Candidate("https://www.rolleianalog.com/products/rollei-supergrain/?lang=en", productName));
            candidates.add(new Candidate("https://www.bhphotovideo.com/c/product/1349037-REG/rollei_422312_supergrain_film_developer_500ml.html", productName));
        }
        if (isHttp(initialSourceUrl)) candidates.add(new Candidate(initialSourceUrl, productName));
        candidates.addAll(searchCandidateUrls(productName));'''
if old not in s:
    raise SystemExit('spec candidates marker missing')
s = s.replace(old, new, 1)

old = '''        if (containsAny(s,"foma.cz","ilfordphoto.com","harmantechnology.com","adox.de","bellinifoto.it","kodakalaris.com","kodak.com","ferrania.it","bergger.com","cinestillfilm.com")) return 100;'''
new = '''        if (containsAny(s,"foma.cz","ilfordphoto.com","harmantechnology.com","adox.de","bellinifoto.it","rolleianalog.com","kodakalaris.com","kodak.com","ferrania.it","bergger.com","cinestillfilm.com")) return 100;'''
if old not in s:
    raise SystemExit('score domain marker missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('v0.1.9 search enrichment patch applied')
