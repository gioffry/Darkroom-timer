package it.darkroom.assistant;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Motore di ricerca catalogo. Non dipende da un singolo parser HTML:
 * usa Bing RSS, DuckDuckGo Lite/HTML e cataloghi ufficiali diretti.
 */
final class OnlineCatalogSearch {
    static final int ROLE_FILM_DEV = 1;
    static final int ROLE_PAPER_DEV = 2;
    static final int ROLE_STOP = 4;
    static final int ROLE_FIX = 8;

    static final class SearchResult {
        final String title;
        final String url;
        final String snippet;
        SearchResult(String title, String url, String snippet) {
            this.title = cleanTitle(title);
            this.url = url == null ? "" : url;
            this.snippet = snippet == null ? "" : cleanText(snippet);
        }
    }

    static final class ChemicalData {
        final String name;
        final int roles;
        final boolean stockPrep;
        final String[] filmDilutions;
        final String[] paperDilutions;
        final String workingDilution;
        final String stockInstructions;
        final int expiryDays;
        final String sourceUrl;
        ChemicalData(String name, int roles, boolean stockPrep,
                     String[] filmDilutions, String[] paperDilutions,
                     String workingDilution, String stockInstructions,
                     int expiryDays, String sourceUrl) {
            this.name = name;
            this.roles = roles;
            this.stockPrep = stockPrep;
            this.filmDilutions = filmDilutions == null ? new String[0] : filmDilutions;
            this.paperDilutions = paperDilutions == null ? new String[0] : paperDilutions;
            this.workingDilution = workingDilution;
            this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static final class FilmData {
        final String name;
        final int iso;
        final String format;
        final String sourceUrl;
        FilmData(String name, int iso, String format, String sourceUrl) {
            this.name = name;
            this.iso = iso;
            this.format = format;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static List<SearchResult> searchChemicals(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, true, raw);
        raw.addAll(searchWeb(q + " photographic developer fixer stop bath chemistry"));
        return filterChemicalResults(q, dedupe(raw, 30));
    }

    static List<SearchResult> searchFilms(String query) {
        String q = safeQuery(query);
        List<SearchResult> raw = new ArrayList<>();
        addOfficialCatalogResults(q, false, raw);
        raw.addAll(searchWeb(q + " black white photographic film ISO 35mm 120"));
        return filterFilmResults(q, dedupe(raw, 30));
    }

    private static String safeQuery(String q) {
        return q == null ? "" : q.trim().replaceAll("\\s+", " ");
    }

    private static List<SearchResult> searchWeb(String query) {
        List<SearchResult> out = new ArrayList<>();
        try {
            String u = "https://www.bing.com/search?format=rss&setlang=en&q=" +
                    URLEncoder.encode(query, "UTF-8");
            out.addAll(parseBingRss(fetch(u, 500000)));
        } catch (Exception ignored) {}
        try {
            String u = "https://lite.duckduckgo.com/lite/?q=" +
                    URLEncoder.encode(query, "UTF-8");
            out.addAll(parseGenericSearchLinks(fetch(u, 450000)));
        } catch (Exception ignored) {}
        if (out.size() < 5) {
            try {
                String u = "https://www.bing.com/search?q=" + URLEncoder.encode(query, "UTF-8");
                out.addAll(parseBingHtml(fetch(u, 500000)));
            } catch (Exception ignored) {}
        }
        return dedupe(out, 30);
    }

    private static List<SearchResult> parseBingRss(String xml) {
        List<SearchResult> out = new ArrayList<>();
        if (xml == null) return out;
        Matcher m = Pattern.compile("(?is)<item>(.*?)</item>").matcher(xml);
        while (m.find() && out.size() < 30) {
            String item = m.group(1);
            String title = xmlValue(item, "title");
            String link = xmlValue(item, "link");
            String desc = xmlValue(item, "description");
            if (isHttp(link) && title.length() > 2) out.add(new SearchResult(title, link, desc));
        }
        return out;
    }

    private static String xmlValue(String block, String tag) {
        Matcher m = Pattern.compile("(?is)<" + tag + ">(?:<!\\[CDATA\\[)?(.*?)(?:]]>)?</" + tag + ">").matcher(block);
        return m.find() ? decodeEntities(cleanText(m.group(1))) : "";
    }

    private static List<SearchResult> parseGenericSearchLinks(String html) {
        List<SearchResult> out = new ArrayList<>();
        if (html == null) return out;
        Matcher m = Pattern.compile("(?is)<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>").matcher(html);
        while (m.find() && out.size() < 40) {
            String href = decodeDuckUrl(decodeEntities(m.group(1)));
            String title = cleanText(m.group(2));
            if (!isHttp(href) || title.length() < 3) continue;
            if (href.contains("duckduckgo.com") || href.contains("bing.com")) continue;
            out.add(new SearchResult(title, href, ""));
        }
        return out;
    }

    private static List<SearchResult> parseBingHtml(String html) {
        List<SearchResult> out = new ArrayList<>();
        if (html == null) return out;
        Matcher m = Pattern.compile("(?is)<h2[^>]*>\\s*<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>\\s*</h2>").matcher(html);
        while (m.find() && out.size() < 30) {
            String href = decodeEntities(m.group(1));
            String title = cleanText(m.group(2));
            if (isHttp(href) && title.length() > 2) out.add(new SearchResult(title, href, ""));
        }
        return out;
    }

    private static void addOfficialCatalogResults(String query, boolean chemical, List<SearchResult> out) {
        String n = normalize(query);
        if (n.contains("bell") || n.contains("hydrofen") || n.contains("ecofilm") ||
                n.contains("ornano") || n.contains("f205") || n.contains("fx100")) {
            addBelliniCatalog(query, chemical, out);
        }
        if (n.contains("rollei") || n.startsWith("rolle") || n.contains("supergrain") ||
                n.contains("rpx") || n.contains("retro") || n.contains("superpan")) {
            addRolleiCatalog(query, chemical, out);
        }
        if (!chemical && (n.contains("p30") || n.contains("ferrania"))) {
            out.add(new SearchResult(
                    "Ferrania P30 80 ISO — 35 mm",
                    "https://www.filmferrania.com/it/products/ferrania-p30-bulk-lenght-80-iso",
                    "FILM Ferrania · pellicola bianco e nero pancromatica · 80 ISO"));
            out.add(new SearchResult(
                    "Ferrania P30 — guida ufficiale allo sviluppo",
                    "https://www.filmferrania.com/p30-info",
                    "FILM Ferrania · P30 · 80 ISO · processing guide"));
        }
    }

    private static void addBelliniCatalog(String query, boolean chemical, List<SearchResult> out) {
        if (!chemical) return;
        String[] pages = {
                "https://www.bellinifoto.it/en/tag-prodotto/film-en/",
                "https://www.bellinifoto.it/en/tag-prodotto/developers/"
        };
        for (String page : pages) {
            try {
                String html = fetch(page, 550000);
                Matcher m = Pattern.compile("(?is)<a[^>]+href=[\"']([^\"']*bellinifoto\\.it[^\"']+)[\"'][^>]*>(.*?)</a>").matcher(html);
                while (m.find() && out.size() < 18) {
                    String href = decodeEntities(m.group(1));
                    String title = cleanText(m.group(2));
                    if (!looksChemicalTitle(title)) continue;
                    if (!isBrandOnlyQuery(query, "bell", "bellini") && !queryOverlap(query, title)) continue;
                    out.add(new SearchResult(title, href, "Bellini Foto · photographic chemistry product"));
                }
            } catch (Exception ignored) {}
        }
    }

    private static void addRolleiCatalog(String query, boolean chemical, List<SearchResult> out) {
        try {
            String page = "https://www.rolleianalog.com/downloads/";
            String html = fetch(page, 650000);
            String low = html.toLowerCase(Locale.ROOT);
            int chemistryStart = low.indexOf("chemistry");
            Matcher m = Pattern.compile("(?is)<h3[^>]*>(.*?)</h3>").matcher(html);
            while (m.find() && out.size() < 20) {
                String title = cleanText(m.group(1));
                if (!normalize(title).startsWith("rollei ")) continue;
                boolean isChemical = chemistryStart >= 0 && m.start() > chemistryStart;
                if (chemical != isChemical) continue;
                if (!isBrandOnlyQuery(query, "rollei", "rolle") && !queryOverlap(query, title)) continue;
                int to = Math.min(html.length(), m.end() + 1800);
                String after = html.substring(m.end(), to);
                String href = firstUsefulHref(after, page);
                if (href.isEmpty()) href = page;
                out.add(new SearchResult(title, href,
                        "Rollei official " + (chemical ? "chemistry" : "film") + " data sheet"));
            }
        } catch (Exception ignored) {}
    }

    private static String firstUsefulHref(String html, String base) {
        Matcher m = Pattern.compile("(?is)<a[^>]+href=[\"']([^\"']+)[\"']").matcher(html);
        while (m.find()) {
            String h = decodeEntities(m.group(1));
            if (h.startsWith("#") || h.startsWith("javascript:")) continue;
            if (h.startsWith("http://") || h.startsWith("https://")) return h;
            if (h.startsWith("/")) {
                try {
                    URL b = new URL(base);
                    return b.getProtocol() + "://" + b.getHost() + h;
                } catch (Exception ignored) {}
            }
        }
        return "";
    }

    private static boolean isBrandOnlyQuery(String query, String... aliases) {
        String n = normalize(query);
        for (String a : aliases) {
            if (normalize(a).startsWith(n) || n.startsWith(normalize(a))) return n.length() <= normalize(a).length() + 2;
        }
        return false;
    }

    private static boolean looksChemicalTitle(String title) {
        String s = normalize(title);
        return containsAny(s, "developer", "fixer", "stop", "fiss", "rivel", "wetting",
                "hydrofen", "ecofilm", "fx100", "f205", "nucleol", "gradual", "rodinal",
                "d100", "d warm", "dks", "bwdek", "euro hc", "aminophenol");
    }

    private static List<SearchResult> filterChemicalResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        for (SearchResult r : raw) {
            String all = r.title + " " + r.url + " " + r.snippet;
            if (!queryOverlap(query, all) && !brandQueryMatchesDomain(query, r.url)) continue;
            if (looksEditorial(r.title, r.url)) continue;
            String s = normalize(all);
            boolean signal = looksChemicalTitle(r.title) || containsAny(s,
                    "photographic chemistry", "developer", "fixer", "stop bath", "rivelatore", "fissaggio");
            if (!signal && trustedDomainScore(r.url) < 2) continue;
            out.add(r);
            if (out.size() >= 12) break;
        }
        return dedupe(out, 12);
    }

    private static List<SearchResult> filterFilmResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        for (SearchResult r : raw) {
            String all = r.title + " " + r.url + " " + r.snippet;
            if (!queryOverlap(query, all) && !brandQueryMatchesDomain(query, r.url)) continue;
            if (looksEditorial(r.title, r.url) && !normalize(r.url).contains("p30 info")) continue;
            String s = normalize(all);
            boolean signal = containsAny(s, "film", "pellicola", "35mm", "35 mm", "120", "iso", "asa", "data sheet");
            if (!signal && trustedDomainScore(r.url) < 2) continue;
            out.add(r);
            if (out.size() >= 12) break;
        }
        return dedupe(out, 12);
    }

    private static boolean brandQueryMatchesDomain(String query, String url) {
        String q = normalize(query), u = normalize(url);
        return (q.startsWith("bell") && u.contains("bellinifoto")) ||
                (q.startsWith("rolle") && u.contains("rolleianalog")) ||
                ((q.contains("p30") || q.startsWith("ferr")) && u.contains("filmferrania"));
    }

    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        String body = "";
        if (!r.url.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(r.url, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);
        String all = r.title + " " + r.snippet + " " + focus;
        String low = normalize(all);
        int roles = inferRoles(r.title, low);
        boolean powder = containsAny(low, "powder", "polvere", "pulver");
        boolean stockPrep = powder && containsAny(low, "stock solution", "dissolve", "sciogli", "mix the powder", "prepare stock");
        List<String> dilutions = extractDilutionsNearContext(all);
        String[] filmDil = (roles & ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String[] paperDil = (roles & ROLE_PAPER_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String working = ((roles & (ROLE_STOP | ROLE_FIX)) != 0 && !dilutions.isEmpty()) ? dilutions.get(0) : null;
        int expiry = extractShelfLifeDays(all);
        String instructions = stockPrep ? extractStockInstruction(all) : null;
        return new ChemicalData(cleanTitle(r.title), roles, stockPrep, filmDil, paperDil,
                working, instructions, expiry, r.url);
    }

    private static int inferRoles(String title, String low) {
        String t = normalize(title);
        if (containsAny(t, "citro stop", "stop bath", "ecostop", "indexstop")) return ROLE_STOP;
        if (containsAny(t, "fix acid", "fix neutral", "fixer", "f205", "fx100", "fomafix")) return ROLE_FIX;
        if (containsAny(t, "print neutral", "print warmtone", "lith a", "paper developer", "d100", "d warm")) return ROLE_PAPER_DEV;
        if (containsAny(t, "supergrain", "low contrast", "low speed", "high contrast", "film developer",
                "hydrofen", "ecofilm", "euro hc", "nucleol", "gradual", "aminophenol", "r09")) return ROLE_FILM_DEV;
        boolean stop = containsAny(low, "stop bath", "arresto", "stoppbad");
        boolean fix = containsAny(low, "fixer", "fixing bath", "fissaggio");
        if (stop) return ROLE_STOP;
        if (fix) return ROLE_FIX;
        boolean dev = containsAny(low, "developer", "rivelatore", "entwickler");
        if (!dev) return 0;
        boolean film = containsAny(low, "film developer", "negative developer", "black and white film", "pellicola");
        boolean paper = containsAny(low, "paper developer", "print developer", "photographic paper", "carta fotografica");
        int role = 0;
        if (film) role |= ROLE_FILM_DEV;
        if (paper) role |= ROLE_PAPER_DEV;
        return role;
    }

    private static ChemicalData emptyChemical(SearchResult r) {
        return new ChemicalData(r == null ? "" : cleanTitle(r.title), 0, false,
                new String[0], new String[0], null, null, -1,
                r == null ? "" : r.url);
    }

    static FilmData enrichFilm(SearchResult r) {
        if (r == null) return new FilmData("", 0, null, "");
        String body = "";
        if (!r.url.toLowerCase(Locale.ROOT).contains(".pdf")) {
            try { body = cleanText(fetch(r.url, 600000)); } catch (Exception ignored) {}
        }
        String focus = focusAroundProduct(body, r.title);
        String all = r.title + " " + r.snippet + " " + focus;
        int iso = extractIso(all);
        if (iso == 0 && normalize(r.title).contains("ferrania p30")) iso = 80;
        String format = extractFormat(r.title + " " + r.snippet);
        if (format == null) format = extractFormat(focus);
        return new FilmData(cleanTitle(r.title), iso, format, r.url);
    }

    private static String focusAroundProduct(String body, String title) {
        if (body == null || body.isEmpty()) return "";
        String flat = body.replaceAll("\\s+", " ");
        String nTitle = normalize(title);
        String nBody = normalize(flat);
        int i = nBody.indexOf(nTitle);
        if (i < 0) return flat.length() > 18000 ? flat.substring(0, 18000) : flat;
        int from = Math.max(0, i - 1200);
        int to = Math.min(flat.length(), i + nTitle.length() + 7000);
        return flat.substring(from, to);
    }

    private static List<String> extractDilutionsNearContext(String text) {
        Set<String> values = new LinkedHashSet<>();
        if (text == null) return new ArrayList<>(values);
        Matcher m = Pattern.compile("(?i)\\b(1\\s*[+:]\\s*\\d{1,3})\\b").matcher(text);
        while (m.find() && values.size() < 8) {
            int from = Math.max(0, m.start() - 220), to = Math.min(text.length(), m.end() + 220);
            String ctx = normalize(text.substring(from, to));
            if (!containsAny(ctx, "dilution", "diluizione", "working solution", "developer", "rivelatore",
                    "fixer", "fissaggio", "stop bath", "arresto", "dilute", "mix")) continue;
            values.add(m.group(1).replace(" ", "").replace(':', '+'));
        }
        return new ArrayList<>(values);
    }

    private static String extractStockInstruction(String text) {
        if (text == null) return null;
        String flat = text.replaceAll("\\s+", " ").trim();
        String low = normalize(flat);
        String[] keys = {"stock solution", "dissolve", "mix the powder", "preparation", "soluzione stock", "sciogli", "polvere"};
        int best = -1;
        for (String k : keys) {
            int i = low.indexOf(k);
            if (i >= 0 && (best < 0 || i < best)) best = i;
        }
        if (best < 0) return null;
        String chunk = flat.substring(Math.max(0, best - 200), Math.min(flat.length(), best + 850));
        if (!Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c)").matcher(chunk).find()) return null;
        return chunk.length() > 700 ? chunk.substring(0, 700).trim() + "…" : chunk.trim();
    }

    private static int extractIso(String text) {
        if (text == null) return 0;
        Matcher m = Pattern.compile("(?i)\\b(?:ISO|ASA|EI)\\s*[:=]?\\s*(\\d{2,4})\\b").matcher(text);
        if (m.find()) {
            try { return Integer.parseInt(m.group(1)); } catch (Exception ignored) {}
        }
        return 0;
    }

    private static String extractFormat(String text) {
        if (text == null) return null;
        String s = normalize(text);
        boolean f35 = s.contains("35mm") || s.contains("35 mm") || s.contains("135 film") || s.contains("135 format");
        boolean f120 = s.matches("(?s).*\\b120\\b.*");
        if (f35 && !f120) return "35";
        if (f120 && !f35) return "120";
        return null;
    }

    private static int extractShelfLifeDays(String text) {
        if (text == null) return -1;
        Matcher months = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,70}(\\d{1,2})\\s*(?:months|mesi|month)").matcher(text);
        if (months.find()) try { return Integer.parseInt(months.group(1)) * 30; } catch (Exception ignored) {}
        Matcher years = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,70}(\\d{1,2})\\s*(?:years|anni|year)").matcher(text);
        if (years.find()) try { return Integer.parseInt(years.group(1)) * 365; } catch (Exception ignored) {}
        return -1;
    }

    private static boolean queryOverlap(String query, String text) {
        Set<String> q = significantTokens(query);
        if (q.isEmpty()) return false;
        String n = normalize(text);
        int hit = 0;
        for (String t : q) if (n.contains(t)) hit++;
        return hit >= Math.max(1, (int)Math.ceil(q.size() * 0.5));
    }

    private static Set<String> significantTokens(String s) {
        Set<String> out = new LinkedHashSet<>();
        for (String t : normalize(s).split(" ")) {
            if (t.length() >= 3 && !containsAny(t, "the", "and", "film", "foto", "photo")) out.add(t);
        }
        return out;
    }

    private static List<SearchResult> dedupe(List<SearchResult> in, int max) {
        LinkedHashMap<String, SearchResult> map = new LinkedHashMap<>();
        for (SearchResult r : in) {
            if (r == null || r.title.length() < 3) continue;
            String key = normalize(r.title) + "|" + normalize(r.url);
            if (!map.containsKey(key)) map.put(key, r);
            if (map.size() >= max) break;
        }
        return new ArrayList<>(map.values());
    }

    private static boolean looksEditorial(String title, String url) {
        String s = normalize(title + " " + url);
        return containsAny(s, "/blog/", "/news/", " review ", " guide ", " tutorial ", " forum ",
                "essential guide", "camera basics", "how to ") && !s.contains("filmferrania com p30 info");
    }

    private static int trustedDomainScore(String url) {
        String s = normalize(url);
        if (containsAny(s, "bellinifoto it", "rolleianalog com", "filmferrania com", "ilfordphoto com",
                "harmantechnology com", "foma cz", "adox de", "fotoimpex com", "kodak com", "kodakalaris com")) return 3;
        if (s.contains("digitaltruth com")) return 2;
        return 0;
    }

    private static String cleanTitle(String s) {
        String t = cleanText(s);
        t = t.replaceAll("(?i)\\s*[|–—]\\s*(official.*|bellini foto.*|rollei.*downloads.*)$", "").trim();
        return t.length() > 120 ? t.substring(0, 120).trim() : t;
    }

    private static String cleanText(String s) {
        if (s == null) return "";
        return decodeEntities(s)
                .replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?s)<[^>]+>", " ")
                .replaceAll("\\s+", " ").trim();
    }

    private static String decodeEntities(String s) {
        if (s == null) return "";
        return s.replace("&amp;", "&").replace("&quot;", "\"")
                .replace("&#39;", "'").replace("&apos;", "'")
                .replace("&nbsp;", " ").replace("&ndash;", "–")
                .replace("&mdash;", "—").replace("&deg;", "°")
                .replace("&lt;", "<").replace("&gt;", ">");
    }

    private static String normalize(String s) {
        return cleanText(s).toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9à-ÿ+]+", " ").replaceAll("\\s+", " ").trim();
    }

    private static boolean containsAny(String text, String... terms) {
        if (text == null) return false;
        for (String t : terms) if (text.contains(t)) return true;
        return false;
    }

    private static String fetch(String urlString, int maxChars) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(urlString).openConnection();
        c.setConnectTimeout(8000);
        c.setReadTimeout(10000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36");
        c.setRequestProperty("Accept", "text/html,application/xhtml+xml,application/xml,text/xml;q=0.9,*/*;q=0.5");
        c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
        c.setRequestProperty("Accept-Encoding", "identity");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        InputStream in = c.getInputStream();
        BufferedReader br = new BufferedReader(new InputStreamReader(in));
        StringBuilder sb = new StringBuilder();
        char[] buf = new char[4096];
        int n;
        while ((n = br.read(buf)) > 0 && sb.length() < maxChars) sb.append(buf, 0, n);
        br.close();
        return sb.toString();
    }

    private static String decodeDuckUrl(String href) {
        if (href == null) return "";
        try {
            int i = href.indexOf("uddg=");
            if (i >= 0) {
                String v = href.substring(i + 5);
                int amp = v.indexOf('&');
                if (amp >= 0) v = v.substring(0, amp);
                return URLDecoder.decode(v, "UTF-8");
            }
            if (href.startsWith("//")) return "https:" + href;
        } catch (Exception ignored) {}
        return href;
    }

    private static boolean isHttp(String s) {
        return s != null && (s.startsWith("https://") || s.startsWith("http://"));
    }

    private OnlineCatalogSearch() {}
}
