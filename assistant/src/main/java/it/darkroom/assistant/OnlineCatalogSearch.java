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
            this.filmDilutions = filmDilutions;
            this.paperDilutions = paperDilutions;
            this.workingDilution = workingDilution;
            this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays;
            this.sourceUrl = sourceUrl;
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
            this.sourceUrl = sourceUrl;
        }
    }

    static List<SearchResult> searchChemicals(String query) {
        String q = query + " photographic developer fixer stop bath darkroom chemistry";
        return searchWeb(q, true);
    }

    static List<SearchResult> searchFilms(String query) {
        String q = query + " black white photographic film ISO 35mm 120";
        return searchWeb(q, false);
    }

    private static List<SearchResult> searchWeb(String query, boolean chemical) {
        List<SearchResult> out = new ArrayList<>();
        try {
            String url = "https://html.duckduckgo.com/html/?q=" + URLEncoder.encode(query, "UTF-8");
            String html = fetch(url, 450000);
            out.addAll(parseDuckDuckGo(html, chemical));
        } catch (Exception ignored) {
        }
        if (out.isEmpty()) {
            try {
                String url = "https://www.bing.com/search?q=" + URLEncoder.encode(query, "UTF-8");
                String html = fetch(url, 450000);
                out.addAll(parseBing(html, chemical));
            } catch (Exception ignored) {
            }
        }
        LinkedHashMap<String, SearchResult> dedupe = new LinkedHashMap<>();
        for (SearchResult r : out) {
            String key = r.title.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", " ").trim();
            if (key.length() >= 3 && !dedupe.containsKey(key)) dedupe.put(key, r);
            if (dedupe.size() >= 12) break;
        }
        return new ArrayList<>(dedupe.values());
    }

    private static List<SearchResult> parseDuckDuckGo(String html, boolean chemical) {
        List<SearchResult> out = new ArrayList<>();
        if (html == null) return out;
        Pattern p = Pattern.compile("(?is)<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>(.*?)(?=<a[^>]*class=\"result__a\"|$)");
        Matcher m = p.matcher(html);
        while (m.find() && out.size() < 20) {
            String href = decodeDuckUrl(m.group(1));
            String title = cleanText(m.group(2));
            String block = m.group(3);
            String snippet = "";
            Matcher sm = Pattern.compile("(?is)class=\"result__snippet\"[^>]*>(.*?)</").matcher(block);
            if (sm.find()) snippet = cleanText(sm.group(1));
            if (relevant(title + " " + snippet + " " + href, chemical)) {
                out.add(new SearchResult(title, href, snippet));
            }
        }
        return out;
    }

    private static List<SearchResult> parseBing(String html, boolean chemical) {
        List<SearchResult> out = new ArrayList<>();
        if (html == null) return out;
        Pattern p = Pattern.compile("(?is)<li class=\"b_algo\".*?<h2><a href=\"([^\"]+)\"[^>]*>(.*?)</a></h2>(.*?)(?=<li class=\"b_algo\"|$)");
        Matcher m = p.matcher(html);
        while (m.find() && out.size() < 20) {
            String href = m.group(1);
            String title = cleanText(m.group(2));
            String snippet = cleanText(m.group(3));
            if (relevant(title + " " + snippet + " " + href, chemical)) {
                out.add(new SearchResult(title, href, snippet));
            }
        }
        return out;
    }

    private static boolean relevant(String text, boolean chemical) {
        String s = text.toLowerCase(Locale.ROOT);
        if (chemical) {
            return s.contains("developer") || s.contains("fixer") || s.contains("stop bath") ||
                    s.contains("rivelatore") || s.contains("fissaggio") || s.contains("darkroom") ||
                    s.contains("photographic chemistry") || knownPhotoDomain(s);
        }
        return s.contains("film") || s.contains("pellicola") || s.contains("35mm") ||
                s.contains("35 mm") || s.contains("120") || s.contains("iso") || knownPhotoDomain(s);
    }

    private static boolean knownPhotoDomain(String s) {
        return s.contains("ilfordphoto.com") || s.contains("foma.cz") || s.contains("fomaobchod") ||
                s.contains("adox") || s.contains("bellinifoto") || s.contains("kodak") ||
                s.contains("ferrania") || s.contains("bergger") || s.contains("fotoimpex") ||
                s.contains("harmantechnology") || s.contains("cinestill") || s.contains("digitaltruth");
    }

    static ChemicalData enrichChemical(SearchResult r) {
        String body = "";
        try { body = cleanText(fetch(r.url, 500000)); } catch (Exception ignored) {}
        String all = (r.title + " " + r.snippet + " " + body).toLowerCase(Locale.ROOT);

        int roles = 0;
        if (containsAny(all, "stop bath", "arresto", "stoppbad", "stop-bath")) roles |= ROLE_STOP;
        if (containsAny(all, "fixer", "fixing bath", "fissaggio", "fixierbad")) roles |= ROLE_FIX;

        boolean developer = containsAny(all, "developer", "rivelatore", "entwickler", "developing agent");
        boolean film = containsAny(all, "film developer", "negative developer", "black and white film", "b&w film", "pellicola", "films");
        boolean paper = containsAny(all, "paper developer", "print developer", "photographic paper", "photo paper", "carta fotografica", "prints");
        if (developer) {
            if (film) roles |= ROLE_FILM_DEV;
            if (paper) roles |= ROLE_PAPER_DEV;
            if (!film && !paper) roles |= ROLE_FILM_DEV;
        }
        if (roles == 0 && r.title.toLowerCase(Locale.ROOT).contains("developer")) roles = ROLE_FILM_DEV;

        boolean powder = containsAny(all, "powder", "polvere", "pulver");
        boolean stockPrep = powder && containsAny(all, "stock solution", "stock", "dissolve", "sciogli", "mix the powder");

        List<String> dilutions = extractDilutions(all);
        String[] filmDil = (roles & ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String[] paperDil = (roles & ROLE_PAPER_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String working = ((roles & (ROLE_STOP | ROLE_FIX)) != 0 && !dilutions.isEmpty()) ? dilutions.get(0) : null;

        int expiryDays = extractShelfLifeDays(all);
        String instructions = stockPrep ? "Prodotto in polvere: prepara la soluzione stock seguendo le istruzioni del produttore recuperate dalla fonte online." : null;
        return new ChemicalData(cleanTitle(r.title), roles, stockPrep, filmDil, paperDil, working, instructions, expiryDays, r.url);
    }

    static FilmData enrichFilm(SearchResult r) {
        String body = "";
        try { body = cleanText(fetch(r.url, 500000)); } catch (Exception ignored) {}
        String all = r.title + " " + r.snippet + " " + body;
        int iso = extractIso(all);
        String format = extractFormat(r.title + " " + r.snippet);
        if (format == null) format = extractFormat(body);
        return new FilmData(cleanTitle(r.title), iso, format, r.url);
    }

    private static List<String> extractDilutions(String text) {
        Set<String> values = new LinkedHashSet<>();
        Matcher m = Pattern.compile("(?i)\\b(1\\s*[+:]\\s*\\d{1,3})\\b").matcher(text);
        while (m.find() && values.size() < 8) {
            values.add(m.group(1).replace(" ", "").replace(':', '+'));
        }
        return new ArrayList<>(values);
    }

    private static int extractIso(String text) {
        Matcher m = Pattern.compile("(?i)\\b(?:ISO|ASA|EI)\\s*[:=]?\\s*(\\d{2,4})\\b").matcher(text);
        if (m.find()) {
            try { return Integer.parseInt(m.group(1)); } catch (Exception ignored) {}
        }
        Matcher t = Pattern.compile("\\b(25|50|64|80|100|125|160|200|320|400|800|1600|3200)\\b").matcher(text);
        if (t.find()) {
            try { return Integer.parseInt(t.group(1)); } catch (Exception ignored) {}
        }
        return 0;
    }

    private static String extractFormat(String text) {
        if (text == null) return null;
        String s = text.toLowerCase(Locale.ROOT);
        boolean f35 = s.contains("35mm") || s.contains("35 mm") || s.contains("135 film") || s.contains("135 format");
        boolean f120 = s.matches("(?s).*\\b120\\b.*");
        if (f35 && !f120) return "35";
        if (f120 && !f35) return "120";
        return null;
    }

    private static int extractShelfLifeDays(String text) {
        Matcher months = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,50}(\\d{1,2})\\s*(?:months|mesi|month)").matcher(text);
        if (months.find()) {
            try { return Integer.parseInt(months.group(1)) * 30; } catch (Exception ignored) {}
        }
        Matcher years = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,50}(\\d{1,2})\\s*(?:years|anni|year)").matcher(text);
        if (years.find()) {
            try { return Integer.parseInt(years.group(1)) * 365; } catch (Exception ignored) {}
        }
        return -1;
    }

    private static boolean containsAny(String text, String... terms) {
        for (String t : terms) if (text.contains(t)) return true;
        return false;
    }

    private static String fetch(String urlString, int maxChars) throws Exception {
        if (urlString == null || urlString.length() < 8) throw new IllegalArgumentException("url");
        HttpURLConnection c = (HttpURLConnection) new URL(urlString).openConnection();
        c.setConnectTimeout(7000);
        c.setReadTimeout(9000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Android) DarkroomAssistant/0.1.4");
        c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
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
        try {
            int i = href.indexOf("uddg=");
            if (i >= 0) {
                String v = href.substring(i + 5);
                int amp = v.indexOf('&');
                if (amp >= 0) v = v.substring(0, amp);
                return URLDecoder.decode(v, "UTF-8");
            }
        } catch (Exception ignored) {}
        return href.replace("&amp;", "&");
    }

    private static String cleanTitle(String s) {
        String t = cleanText(s);
        t = t.replaceAll("(?i)\\s*[|–—-]\\s*(Ilford Photo|Foma|ADOX|Bellini Foto|Kodak|Fotoimpex|Ferrania).*$", "").trim();
        return t.length() > 100 ? t.substring(0, 100).trim() : t;
    }

    private static String cleanText(String s) {
        if (s == null) return "";
        return s.replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?s)<[^>]+>", " ")
                .replace("&amp;", "&").replace("&quot;", "\"")
                .replace("&#39;", "'").replace("&apos;", "'")
                .replace("&nbsp;", " ").replace("&ndash;", "–").replace("&mdash;", "—")
                .replaceAll("\\s+", " ").trim();
    }

    private OnlineCatalogSearch() {}
}
