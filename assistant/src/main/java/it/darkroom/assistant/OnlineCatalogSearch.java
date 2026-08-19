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

/** Ricerca online prudente: le pagine editoriali non diventano mai schede prodotto. */
final class OnlineCatalogSearch {
    static final int ROLE_FILM_DEV = 1;
    static final int ROLE_PAPER_DEV = 2;
    static final int ROLE_STOP = 4;
    static final int ROLE_FIX = 8;

    static final class SearchResult {
        final String title; final String url; final String snippet;
        SearchResult(String title, String url, String snippet) {
            this.title = cleanTitle(title); this.url = url == null ? "" : url;
            this.snippet = snippet == null ? "" : cleanText(snippet);
        }
    }

    static final class ChemicalData {
        final String name; final int roles; final boolean stockPrep;
        final String[] filmDilutions; final String[] paperDilutions;
        final String workingDilution; final String stockInstructions;
        final int expiryDays; final String sourceUrl;
        ChemicalData(String name, int roles, boolean stockPrep,
                     String[] filmDilutions, String[] paperDilutions,
                     String workingDilution, String stockInstructions,
                     int expiryDays, String sourceUrl) {
            this.name = name; this.roles = roles; this.stockPrep = stockPrep;
            this.filmDilutions = filmDilutions == null ? new String[0] : filmDilutions;
            this.paperDilutions = paperDilutions == null ? new String[0] : paperDilutions;
            this.workingDilution = workingDilution; this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays; this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static final class FilmData {
        final String name; final int iso; final String format; final String sourceUrl;
        FilmData(String name, int iso, String format, String sourceUrl) {
            this.name = name; this.iso = iso; this.format = format;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static List<SearchResult> searchChemicals(String query) {
        String q = "\"" + query + "\" photographic developer fixer stop bath chemistry product";
        return filterChemicalResults(query, searchWeb(q, true));
    }

    static List<SearchResult> searchFilms(String query) {
        String q = "\"" + query + "\" black white photographic film ISO 35mm 120";
        return filterFilmResults(query, searchWeb(q, false));
    }

    private static List<SearchResult> searchWeb(String query, boolean chemical) {
        List<SearchResult> out = new ArrayList<>();
        try {
            String url = "https://html.duckduckgo.com/html/?q=" + URLEncoder.encode(query, "UTF-8");
            out.addAll(parseDuckDuckGo(fetch(url, 450000), chemical));
        } catch (Exception ignored) {}
        if (out.isEmpty()) {
            try {
                String url = "https://www.bing.com/search?q=" + URLEncoder.encode(query, "UTF-8");
                out.addAll(parseBing(fetch(url, 450000), chemical));
            } catch (Exception ignored) {}
        }
        return dedupe(out, 20);
    }

    private static List<SearchResult> filterChemicalResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        for (SearchResult r : raw) {
            if (!queryOverlap(query, r.title + " " + r.url + " " + r.snippet)) continue;
            if (looksEditorial(r.title, r.url)) continue;
            String s = (r.title + " " + r.snippet + " " + r.url).toLowerCase(Locale.ROOT);
            boolean chemistrySignal = containsAny(s, "developer", "rivelatore", "fixer", "fissaggio",
                    "stop bath", "arresto", "photographic chemistry", "concentrate",
                    "powder developer", "liquid developer", "darkroom chemical");
            if (!chemistrySignal && trustedDomainScore(r.url) < 2) continue;
            if (containsAny(s, "35mm film", "35 mm film", "120 film", "black and white film") && !chemistrySignal) continue;
            out.add(r); if (out.size() >= 8) break;
        }
        return out;
    }

    private static List<SearchResult> filterFilmResults(String query, List<SearchResult> raw) {
        List<SearchResult> out = new ArrayList<>();
        for (SearchResult r : raw) {
            if (!queryOverlap(query, r.title + " " + r.url + " " + r.snippet)) continue;
            if (looksEditorial(r.title, r.url)) continue;
            String s = (r.title + " " + r.snippet + " " + r.url).toLowerCase(Locale.ROOT);
            boolean filmSignal = containsAny(s, "film", "pellicola", "35mm", "35 mm", "120", "iso", "asa", "black and white");
            if (!filmSignal && trustedDomainScore(r.url) < 2) continue;
            out.add(r); if (out.size() >= 8) break;
        }
        return out;
    }

    private static List<SearchResult> dedupe(List<SearchResult> in, int max) {
        LinkedHashMap<String, SearchResult> m = new LinkedHashMap<>();
        for (SearchResult r : in) {
            String key = normalize(r.title);
            if (key.length() < 3 || m.containsKey(key)) continue;
            m.put(key, r); if (m.size() >= max) break;
        }
        return new ArrayList<>(m.values());
    }

    private static List<SearchResult> parseDuckDuckGo(String html, boolean chemical) {
        List<SearchResult> out = new ArrayList<>(); if (html == null) return out;
        Pattern p = Pattern.compile("(?is)<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>(.*?)(?=<a[^>]*class=\"result__a\"|$)");
        Matcher m = p.matcher(html);
        while (m.find() && out.size() < 30) {
            String href = decodeDuckUrl(m.group(1)); String title = cleanText(m.group(2)); String block = m.group(3); String snippet = "";
            Matcher sm = Pattern.compile("(?is)class=\"result__snippet\"[^>]*>(.*?)</").matcher(block);
            if (sm.find()) snippet = cleanText(sm.group(1));
            if (relevant(title + " " + snippet + " " + href, chemical)) out.add(new SearchResult(title, href, snippet));
        }
        return out;
    }

    private static List<SearchResult> parseBing(String html, boolean chemical) {
        List<SearchResult> out = new ArrayList<>(); if (html == null) return out;
        Pattern p = Pattern.compile("(?is)<li class=\"b_algo\".*?<h2><a href=\"([^\"]+)\"[^>]*>(.*?)</a></h2>(.*?)(?=<li class=\"b_algo\"|$)");
        Matcher m = p.matcher(html);
        while (m.find() && out.size() < 30) {
            String href = m.group(1), title = cleanText(m.group(2)), snippet = cleanText(m.group(3));
            if (relevant(title + " " + snippet + " " + href, chemical)) out.add(new SearchResult(title, href, snippet));
        }
        return out;
    }

    private static boolean relevant(String text, boolean chemical) {
        String s = text.toLowerCase(Locale.ROOT);
        if (chemical) return containsAny(s, "developer", "fixer", "stop bath", "rivelatore", "fissaggio", "photographic chemistry", "darkroom") || trustedDomainScore(s) >= 2;
        return containsAny(s, "film", "pellicola", "35mm", "35 mm", "120", "iso") || trustedDomainScore(s) >= 2;
    }

    static ChemicalData enrichChemical(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return emptyChemical(r);
        String html = ""; try { html = fetch(r.url, 550000); } catch (Exception ignored) {}
        String body = cleanText(html);
        String identityText = r.title + " " + r.snippet + " " + (body.length() > 18000 ? body.substring(0, 18000) : body);
        if (!looksLikeProductIdentity(r.title, r.url, identityText)) return emptyChemical(r);

        String low = identityText.toLowerCase(Locale.ROOT); int roles = 0;
        boolean stop = containsAny(low, "stop bath", "arresto", "stoppbad", "stop-bath");
        boolean fix = containsAny(low, "fixer", "fixing bath", "fissaggio", "fixierbad");
        boolean developer = containsAny(low, "developer", "rivelatore", "entwickler", "developing agent");
        if (stop) roles |= ROLE_STOP; if (fix) roles |= ROLE_FIX;
        if (developer && !stop && !fix) {
            boolean film = containsAny(low, "film developer", "negative developer", "b&w film", "black and white film", "pellicola");
            boolean paper = containsAny(low, "paper developer", "print developer", "photographic paper", "photo paper", "carta fotografica");
            if (film) roles |= ROLE_FILM_DEV; if (paper) roles |= ROLE_PAPER_DEV;
            if (!film && !paper) roles = 0;
        }

        boolean powder = containsAny(low, "powder", "polvere", "pulver");
        boolean stockPrep = powder && containsAny(low, "stock solution", "dissolve", "sciogli", "mix the powder", "prepare stock");
        List<String> dilutions = extractDilutionsNearContext(identityText);
        String[] filmDil = (roles & ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String[] paperDil = (roles & ROLE_PAPER_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String working = ((roles & (ROLE_STOP | ROLE_FIX)) != 0 && !dilutions.isEmpty()) ? dilutions.get(0) : null;
        int expiryDays = extractShelfLifeDays(identityText);
        String instructions = stockPrep ? extractStockInstruction(identityText) : null;
        return new ChemicalData(cleanTitle(r.title), roles, stockPrep, filmDil, paperDil, working, instructions, expiryDays, r.url);
    }

    private static ChemicalData emptyChemical(SearchResult r) {
        return new ChemicalData(r == null ? "" : cleanTitle(r.title), 0, false,
                new String[0], new String[0], null, null, -1, r == null ? "" : r.url);
    }

    static FilmData enrichFilm(SearchResult r) {
        if (r == null || looksEditorial(r.title, r.url)) return new FilmData(r == null ? "" : cleanTitle(r.title), 0, null, r == null ? "" : r.url);
        String body = ""; try { body = cleanText(fetch(r.url, 500000)); } catch (Exception ignored) {}
        String all = r.title + " " + r.snippet + " " + body;
        int iso = extractIso(all); String format = extractFormat(r.title + " " + r.snippet); if (format == null) format = extractFormat(body);
        return new FilmData(cleanTitle(r.title), iso, format, r.url);
    }

    private static List<String> extractDilutionsNearContext(String text) {
        Set<String> values = new LinkedHashSet<>(); if (text == null) return new ArrayList<>(values);
        Matcher m = Pattern.compile("(?i)\\b(1\\s*[+:]\\s*\\d{1,3})\\b").matcher(text);
        while (m.find() && values.size() < 6) {
            int from = Math.max(0, m.start() - 180), to = Math.min(text.length(), m.end() + 180);
            String ctx = text.substring(from, to).toLowerCase(Locale.ROOT);
            if (!containsAny(ctx, "dilution", "diluizione", "working solution", "mix ", "developer", "rivelatore", "fixer", "fissaggio", "stop bath", "arresto", "use at", "dilute")) continue;
            values.add(m.group(1).replace(" ", "").replace(':', '+'));
        }
        return new ArrayList<>(values);
    }

    private static String extractStockInstruction(String text) {
        if (text == null) return null; String flat = text.replaceAll("\\s+", " ").trim(), low = flat.toLowerCase(Locale.ROOT);
        String[] keys = {"stock solution", "dissolve", "mix the powder", "preparation", "soluzione stock", "sciogli", "polvere"};
        int best = -1; for (String k : keys) { int i = low.indexOf(k); if (i >= 0 && (best < 0 || i < best)) best = i; }
        if (best < 0) return null;
        String chunk = flat.substring(Math.max(0, best - 180), Math.min(flat.length(), best + 750));
        if (!Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c)").matcher(chunk).find()) return null;
        return chunk.length() > 650 ? chunk.substring(0, 650).trim() + "…" : chunk.trim();
    }

    private static int extractIso(String text) {
        Matcher m = Pattern.compile("(?i)\\b(?:ISO|ASA|EI)\\s*[:=]?\\s*(\\d{2,4})\\b").matcher(text);
        if (m.find()) try { return Integer.parseInt(m.group(1)); } catch (Exception ignored) {}
        return 0;
    }

    private static String extractFormat(String text) {
        if (text == null) return null; String s = text.toLowerCase(Locale.ROOT);
        boolean f35 = s.contains("35mm") || s.contains("35 mm") || s.contains("135 film") || s.contains("135 format");
        boolean f120 = s.matches("(?s).*\\b120\\b.*");
        if (f35 && !f120) return "35"; if (f120 && !f35) return "120"; return null;
    }

    private static int extractShelfLifeDays(String text) {
        if (text == null) return -1;
        Matcher months = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,60}(\\d{1,2})\\s*(?:months|mesi|month)").matcher(text);
        if (months.find()) try { return Integer.parseInt(months.group(1)) * 30; } catch (Exception ignored) {}
        Matcher years = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,60}(\\d{1,2})\\s*(?:years|anni|year)").matcher(text);
        if (years.find()) try { return Integer.parseInt(years.group(1)) * 365; } catch (Exception ignored) {}
        return -1;
    }

    private static boolean queryOverlap(String query, String text) {
        Set<String> q = significantTokens(query); if (q.isEmpty()) return false; String n = normalize(text); int hit = 0;
        for (String t : q) if (n.contains(t)) hit++;
        return hit >= Math.max(1, (int)Math.ceil(q.size() * 0.5));
    }

    private static Set<String> significantTokens(String s) {
        Set<String> out = new LinkedHashSet<>();
        for (String t : normalize(s).split("\\s+")) if (t.length() >= 3 && !containsAny(t, "the", "and", "for", "con", "foto", "photo", "film")) out.add(t);
        return out;
    }

    private static boolean looksLikeProductIdentity(String title, String url, String text) {
        if (looksEditorial(title, url)) return false; String s = (title + " " + text).toLowerCase(Locale.ROOT);
        return containsAny(s, "developer", "rivelatore", "fixer", "fissaggio", "stop bath", "arresto", "photographic chemistry", "concentrate", "powder", "liquid") || trustedDomainScore(url) >= 2;
    }

    private static boolean looksEditorial(String title, String url) {
        String s = (title + " " + url).toLowerCase(Locale.ROOT);
        return containsAny(s, "guide", "basics", "tutorial", "how to", "how-to", "review", "blog", "/blog/", "/article/", "article", "forum", "reddit", "youtube", "facebook", "instagram", "best ", "top 10", "essential guide", "camera basics", "film chemicals 20", "darkroom chemistry guide", "comparison", "vs.");
    }

    private static int trustedDomainScore(String s) {
        if (s == null) return 0; String x = s.toLowerCase(Locale.ROOT);
        if (containsAny(x, "foma.cz", "ilfordphoto.com", "harmantechnology.com", "adox.de", "bellinifoto.it", "kodakalaris.com", "kodak.com", "ferrania.it", "bergger.com", "cinestillfilm.com")) return 3;
        if (containsAny(x, "fotoimpex.com", "macodirect.de", "ars-imago.com", "puntofotoroma.it", "pfg.it")) return 2;
        if (x.contains("digitaltruth.com")) return 1; return 0;
    }

    private static String fetch(String urlString, int maxChars) throws Exception {
        if (urlString == null || urlString.length() < 8) throw new IllegalArgumentException("url");
        HttpURLConnection c = (HttpURLConnection) new URL(urlString).openConnection(); c.setConnectTimeout(7000); c.setReadTimeout(9000); c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Android) DarkroomAssistant/0.1.6"); c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
        int code = c.getResponseCode(); if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        InputStream in = c.getInputStream(); BufferedReader br = new BufferedReader(new InputStreamReader(in)); StringBuilder sb = new StringBuilder(); char[] buf = new char[4096]; int n;
        while ((n = br.read(buf)) > 0 && sb.length() < maxChars) sb.append(buf, 0, n); br.close(); return sb.toString();
    }

    private static String decodeDuckUrl(String href) {
        try { int i = href.indexOf("uddg="); if (i >= 0) { String v = href.substring(i + 5); int amp = v.indexOf('&'); if (amp >= 0) v = v.substring(0, amp); return URLDecoder.decode(v, "UTF-8"); } } catch (Exception ignored) {}
        return href.replace("&amp;", "&");
    }

    private static boolean containsAny(String text, String... terms) { if (text == null) return false; for (String t : terms) if (text.contains(t)) return true; return false; }
    private static String normalize(String s) { if (s == null) return ""; return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", " ").replaceAll("\\s+", " ").trim(); }
    private static String cleanTitle(String s) { String t = cleanText(s); t = t.replaceAll("(?i)\\s*[|–—-]\\s*(Ilford Photo|Foma|ADOX|Bellini Foto|Kodak|Fotoimpex|Ferrania).*$", "").trim(); return t.length() > 100 ? t.substring(0, 100).trim() : t; }
    private static String cleanText(String s) { if (s == null) return ""; return s.replaceAll("(?is)<script.*?</script>", " ").replaceAll("(?is)<style.*?</style>", " ").replaceAll("(?s)<[^>]+>", " ").replace("&amp;", "&").replace("&quot;", "\"").replace("&#39;", "'").replace("&apos;", "'").replace("&nbsp;", " ").replace("&ndash;", "–").replace("&mdash;", "—").replace("&deg;", "°").replaceAll("\\s+", " ").trim(); }
    private OnlineCatalogSearch() {}
}
