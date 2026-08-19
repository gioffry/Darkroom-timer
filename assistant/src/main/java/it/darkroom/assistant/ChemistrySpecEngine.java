package it.darkroom.assistant;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Recupera dalla fonte online le informazioni operative che servono davvero
 * all'Assistant: preparazione stock e capacità/riutilizzo.
 *
 * Se un dato non è abbastanza chiaro, restituisce "non determinato":
 * non inventa valori.
 */
final class ChemistrySpecEngine {
    static final int REUSE_UNKNOWN = 0;
    static final int REUSE_ONE_SHOT = 1;
    static final int REUSE_REUSABLE = 2;

    static final class Spec {
        final String stockInstructions;
        final int reuseMode;
        final double filmCapacityPerLiter;
        final double paperCapacitySqMPerLiter;
        final String sourceUrl;

        Spec(String stockInstructions,
             int reuseMode,
             double filmCapacityPerLiter,
             double paperCapacitySqMPerLiter,
             String sourceUrl) {
            this.stockInstructions = stockInstructions;
            this.reuseMode = reuseMode;
            this.filmCapacityPerLiter = filmCapacityPerLiter;
            this.paperCapacitySqMPerLiter = paperCapacitySqMPerLiter;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static Spec enrich(String productName,
                       String initialSourceUrl,
                       String fallbackInstructions) {
        List<String> urls = new ArrayList<>();
        if (isHttp(initialSourceUrl)) urls.add(initialSourceUrl);
        urls.addAll(searchCandidateUrls(productName));

        Set<String> dedupe = new LinkedHashSet<>(urls);
        StringBuilder all = new StringBuilder();
        String bestSource = isHttp(initialSourceUrl) ? initialSourceUrl : "";

        int tried = 0;
        for (String u : dedupe) {
            if (!isHttp(u)) continue;
            if (tried++ >= 5) break;
            try {
                String html = fetch(u, 650000);
                String text = cleanText(html);
                if (text.length() < 80) continue;
                all.append("\n").append(text);
                if (bestSource.isEmpty() || scoreDomain(u) > scoreDomain(bestSource)) {
                    bestSource = u;
                }
            } catch (Exception ignored) {
            }
        }

        String text = all.toString();
        String low = text.toLowerCase(Locale.ROOT);

        String instructions = extractStockInstructions(text);
        if (!isUsefulInstruction(instructions) && isUsefulInstruction(fallbackInstructions)) {
            instructions = fallbackInstructions;
        }

        double filmCapacity = extractFilmCapacityPerLiter(low);
        double paperCapacity = extractPaperCapacitySqMPerLiter(low);

        int reuse = REUSE_UNKNOWN;
        if (containsAny(low,
                "one shot", "one-shot", "single use", "single-use",
                "discard after use", "use once", "monouso", "usa e getta")) {
            reuse = REUSE_ONE_SHOT;
        } else if (filmCapacity > 0 || paperCapacity > 0 || containsAny(low,
                "reusable", "re-use", "reuse", "reused", "can be re-used",
                "can be reused", "riutilizz", "capacity", "capacità")) {
            reuse = REUSE_REUSABLE;
        }

        return new Spec(instructions, reuse, filmCapacity, paperCapacity, bestSource);
    }

    private static List<String> searchCandidateUrls(String productName) {
        List<String> out = new ArrayList<>();
        try {
            String q = "\"" + productName + "\" photographic chemistry datasheet stock solution capacity";
            String url = "https://html.duckduckgo.com/html/?q=" +
                    URLEncoder.encode(q, "UTF-8");
            String html = fetch(url, 350000);
            Matcher m = Pattern.compile(
                    "(?is)<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"")
                    .matcher(html);
            while (m.find() && out.size() < 10) {
                String u = decodeDuckUrl(m.group(1));
                if (isHttp(u)) out.add(u);
            }
        } catch (Exception ignored) {
        }

        out.sort((a, b) -> Integer.compare(scoreDomain(b), scoreDomain(a)));
        return out;
    }

    private static int scoreDomain(String url) {
        if (url == null) return 0;
        String s = url.toLowerCase(Locale.ROOT);
        if (s.contains("foma.cz") || s.contains("ilfordphoto.com") ||
                s.contains("harmantechnology.com") || s.contains("adox.de") ||
                s.contains("fotoimpex.com") || s.contains("bellinifoto.it") ||
                s.contains("kodakalaris.com") || s.contains("kodak.com") ||
                s.contains("ferrania.it") || s.contains("bergger.com")) return 100;
        if (s.contains("digitaltruth.com")) return 70;
        if (s.contains("pdf")) return 60;
        return 10;
    }

    private static String extractStockInstructions(String text) {
        if (text == null || text.length() < 20) return null;
        String normalized = text.replace('\n', ' ').replaceAll("\\s+", " ").trim();
        String low = normalized.toLowerCase(Locale.ROOT);

        String[] keys = new String[]{
                "stock solution", "dissolve", "dissolving", "mix the powder",
                "mixing instructions", "preparation", "prepare", "polvere",
                "sciogli", "soluzione stock", "water at", "acqua a"
        };

        int best = -1;
        for (String key : keys) {
            int i = low.indexOf(key);
            if (i >= 0 && (best < 0 || i < best)) best = i;
        }
        if (best < 0) return null;

        int from = Math.max(0, best - 220);
        int to = Math.min(normalized.length(), best + 850);
        String chunk = normalized.substring(from, to);

        // Cerchiamo una porzione che contenga almeno una misura/temperatura,
        // altrimenti il testo non è abbastanza operativo.
        if (!Pattern.compile("(?i)(\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c|c\\b))")
                .matcher(chunk).find()) {
            return null;
        }

        chunk = chunk.replaceAll("\\s+", " ").trim();
        if (chunk.length() > 700) chunk = chunk.substring(0, 700).trim() + "…";
        return chunk;
    }

    private static boolean isUsefulInstruction(String s) {
        if (s == null || s.trim().length() < 20) return false;
        return Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c|c\\b)")
                .matcher(s).find();
    }

    private static double extractFilmCapacityPerLiter(String text) {
        if (text == null) return -1;
        Pattern[] patterns = new Pattern[]{
                Pattern.compile("(?i)(\\d{1,3}(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)"),
                Pattern.compile("(?i)(?:capacity|capacità)[^.;]{0,90}?(\\d{1,3}(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,60}?(?:litre|liter|litro|l\\b)"),
                Pattern.compile("(?i)(?:process|processes|develop|develops)[^.;]{0,60}?(\\d{1,3})\\s*(?:35\\s*mm|135)?\\s*(?:rolls?|films?)")
        };
        for (Pattern p : patterns) {
            Matcher m = p.matcher(text);
            if (m.find()) {
                double v = parseNum(m.group(1));
                if (v > 0 && v <= 500) return v;
            }
        }
        return -1;
    }

    private static double extractPaperCapacitySqMPerLiter(String text) {
        if (text == null) return -1;

        Matcher area = Pattern.compile(
                "(?i)(\\d+(?:[.,]\\d+)?)\\s*m(?:2|²)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)")
                .matcher(text);
        if (area.find()) {
            double v = parseNum(area.group(1));
            if (v > 0 && v < 200) return v;
        }

        // Esempio: 80 sheets 20x25 cm per litre -> converte in m²/L.
        Matcher sheets = Pattern.compile(
                "(?i)(\\d{1,4})\\s*(?:sheets?|prints?|fogli)[^.;]{0,90}?(\\d+(?:[.,]\\d+)?)\\s*[x×]\\s*(\\d+(?:[.,]\\d+)?)\\s*(cm|in|inch|inches)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)")
                .matcher(text);
        if (sheets.find()) {
            double n = parseNum(sheets.group(1));
            double w = parseNum(sheets.group(2));
            double h = parseNum(sheets.group(3));
            String unit = sheets.group(4).toLowerCase(Locale.ROOT);
            if (!unit.equals("cm")) {
                w *= 2.54;
                h *= 2.54;
            }
            double sqm = n * (w / 100.0) * (h / 100.0);
            if (sqm > 0 && sqm < 200) return sqm;
        }
        return -1;
    }

    private static double parseNum(String s) {
        try {
            return Double.parseDouble(s.replace(',', '.'));
        } catch (Exception e) {
            return -1;
        }
    }

    private static boolean containsAny(String text, String... terms) {
        for (String t : terms) if (text.contains(t)) return true;
        return false;
    }

    private static String fetch(String urlString, int maxChars) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(urlString).openConnection();
        c.setConnectTimeout(7000);
        c.setReadTimeout(9000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Android) DarkroomAssistant/0.1.5");
        c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        InputStream in = c.getInputStream();
        BufferedReader br = new BufferedReader(new InputStreamReader(in));
        StringBuilder sb = new StringBuilder();
        char[] buf = new char[4096];
        int n;
        while ((n = br.read(buf)) > 0 && sb.length() < maxChars) {
            sb.append(buf, 0, n);
        }
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
        } catch (Exception ignored) {
        }
        return href.replace("&amp;", "&");
    }

    private static String cleanText(String s) {
        if (s == null) return "";
        return s.replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?s)<[^>]+>", " ")
                .replace("&amp;", "&")
                .replace("&quot;", "\"")
                .replace("&#39;", "'")
                .replace("&apos;", "'")
                .replace("&nbsp;", " ")
                .replace("&deg;", "°")
                .replaceAll("\\s+", " ")
                .trim();
    }

    private static boolean isHttp(String s) {
        return s != null && (s.startsWith("https://") || s.startsWith("http://"));
    }

    private ChemistrySpecEngine() {}
}
