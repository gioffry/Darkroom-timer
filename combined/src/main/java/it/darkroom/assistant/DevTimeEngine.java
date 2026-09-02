package it.darkroom.assistant;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Motore tempi sviluppo.
 *
 * Gerarchia:
 * 1) dato produttore strutturato, quando la pagina sorgente contiene una tabella
 *    riconoscibile per quella combinazione;
 * 2) Massive Dev Chart / Digitaltruth;
 * 3) nessun dato: non viene inventato alcun tempo.
 *
 * Il tempo trovato viene convertito alla temperatura richiesta con la
 * compensazione Ilford (fattore ~0,91 per °C, equivalente alla tabella ufficiale,
 * arrotondata a 15 s), quindi viene applicata la regola configurata per JOBO
 * CPE2 a rotazione continua: -15%.
 */
final class DevTimeEngine {
    private static final double JOBO_FACTOR = 0.85;
    private static final double TEMP_FACTOR_PER_C = 0.91;

    static final class Result {
        final boolean found;
        final int finalLowSeconds;
        final int finalHighSeconds;
        final int baseLowSeconds;
        final int baseHighSeconds;
        final double baseTemperature;
        final double targetTemperature;
        final String sourceName;
        final String sourceUrl;
        final String sourceFilm;
        final String sourceDeveloper;
        final String sourceDilution;
        final int sourceIso;
        final String format;
        final boolean temperatureConverted;
        final boolean joboAdjusted;
        final String warning;
        final String diagnostic;

        Result(boolean found,
               int finalLowSeconds, int finalHighSeconds,
               int baseLowSeconds, int baseHighSeconds,
               double baseTemperature, double targetTemperature,
               String sourceName, String sourceUrl,
               String sourceFilm, String sourceDeveloper,
               String sourceDilution, int sourceIso, String format,
               boolean temperatureConverted, boolean joboAdjusted,
               String warning, String diagnostic) {
            this.found = found;
            this.finalLowSeconds = finalLowSeconds;
            this.finalHighSeconds = finalHighSeconds;
            this.baseLowSeconds = baseLowSeconds;
            this.baseHighSeconds = baseHighSeconds;
            this.baseTemperature = baseTemperature;
            this.targetTemperature = targetTemperature;
            this.sourceName = sourceName;
            this.sourceUrl = sourceUrl;
            this.sourceFilm = sourceFilm;
            this.sourceDeveloper = sourceDeveloper;
            this.sourceDilution = sourceDilution;
            this.sourceIso = sourceIso;
            this.format = format;
            this.temperatureConverted = temperatureConverted;
            this.joboAdjusted = joboAdjusted;
            this.warning = warning;
            this.diagnostic = diagnostic;
        }

        static Result notFound(String diagnostic) {
            return new Result(false, 0, 0, 0, 0, 20, 20,
                    "", "", "", "", "", 0, "",
                    false, false, "", diagnostic);
        }

        String finalDisplay() {
            if (!found) return "Tempo non disponibile";
            if (finalHighSeconds > finalLowSeconds) {
                return formatSeconds(finalLowSeconds) + " – " + formatSeconds(finalHighSeconds);
            }
            return formatSeconds(finalLowSeconds);
        }

        String baseDisplay() {
            if (!found) return "";
            if (baseHighSeconds > baseLowSeconds) {
                return formatSeconds(baseLowSeconds) + " – " + formatSeconds(baseHighSeconds);
            }
            return formatSeconds(baseLowSeconds);
        }
    }

    private static final class Row {
        String film;
        String developer;
        String dilution;
        int iso;
        String time35;
        String time120;
        String timeSheet;
        double temp;
        String notes;
        String sourceUrl;
        String sourceName;
    }

    static Result lookup(String filmName,
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
        Result local = LocalRecipeEngine.lookup(filmName, format, developer, dilution, iso, targetTemp);
        if (local != null) return local;
        return Result.notFound(MdcOfflineStore.combinationDiagnostic(
                filmName, developer, dilution, iso));
    }

    private static Result build(Row row, double targetTemp, String format, String diagnostic) {
        String raw = "4x5".equalsIgnoreCase(format) ? row.timeSheet : ("120".equals(format) ? row.time120 : row.time35);
        int[] range = parseTimeRange(raw);
        if (range == null) {
            return Result.notFound("La combinazione esiste, ma non ha un tempo per il formato selezionato.");
        }

        int low = range[0];
        int high = range[1];

        boolean tempConverted = Math.abs(targetTemp - row.temp) > 0.01;
        if (tempConverted) {
            low = temperatureConvert(low, row.temp, targetTemp);
            high = temperatureConvert(high, row.temp, targetTemp);
        }

        low = roundTo5((int) Math.round(low * JOBO_FACTOR));
        high = roundTo5((int) Math.round(high * JOBO_FACTOR));

        String warning = "";
        if (low < 300) {
            warning = "Attenzione: il tempo finale è sotto 5 minuti; tempi così brevi aumentano il rischio di sviluppo non uniforme.";
        }

        return new Result(true,
                low, high,
                range[0], range[1],
                row.temp, targetTemp,
                row.sourceName, row.sourceUrl,
                row.film, row.developer, row.dilution, row.iso, format,
                tempConverted, true, warning, diagnostic);
    }

    private static int temperatureConvert(int seconds, double fromC, double toC) {
        double adjusted = seconds * Math.pow(TEMP_FACTOR_PER_C, toC - fromC);
        return roundTo15((int) Math.round(adjusted));
    }

    private static int roundTo15(int seconds) {
        return Math.max(15, (int) Math.round(seconds / 15.0) * 15);
    }

    private static int roundTo5(int seconds) {
        return Math.max(5, (int) Math.round(seconds / 5.0) * 5);
    }

    private static List<Row> parseDigitaltruth(String html, String sourceUrl) {
        List<Row> out = new ArrayList<>();
        if (html == null) return out;

        Pattern tr = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>");
        Pattern td = Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>");
        Matcher rm = tr.matcher(html);
        while (rm.find()) {
            List<String> cells = new ArrayList<>();
            Matcher cm = td.matcher(rm.group(1));
            while (cm.find()) cells.add(cleanHtml(cm.group(1)));
            if (cells.size() < 8) continue;
            if (cells.get(0).toLowerCase(Locale.ROOT).contains("film") &&
                    cells.get(1).toLowerCase(Locale.ROOT).contains("developer")) continue;

            Row r = new Row();
            r.film = cells.get(0);
            r.developer = cells.get(1);
            r.dilution = normalizeDilution(cells.get(2));
            r.iso = parseIso(cells.get(3));
            r.time35 = cells.size() > 4 ? cleanTime(cells.get(4)) : "";
            r.time120 = cells.size() > 5 ? cleanTime(cells.get(5)) : "";
            r.timeSheet = cells.size() > 6 ? cleanTime(cells.get(6)) : "";
            r.temp = cells.size() > 7 ? parseTemp(cells.get(7)) : 20.0;
            r.notes = cells.size() > 8 ? cells.get(8) : "";
            r.sourceUrl = sourceUrl;
            r.sourceName = "Massive Dev Chart";
            if (!r.film.isEmpty() && !r.developer.isEmpty()) out.add(r);
        }

        if (out.isEmpty()) {
            String text = cleanHtml(html);
            Pattern line = Pattern.compile("(?im)^(.+?)\\s{2,}(.+?)\\s{2,}(stock|1\\s*\\+\\s*\\d+(?:\\s*\\+\\s*\\d+)?)\\s{2,}(\\d{2,4}|#)\\s{2,}(.+?)\\s{2,}(.+?)\\s{2,}(.+?)\\s{2,}(\\d{2}(?:\\.\\d+)?C)");
            Matcher lm = line.matcher(text);
            while (lm.find()) {
                Row r = new Row();
                r.film = lm.group(1).trim();
                r.developer = lm.group(2).trim();
                r.dilution = normalizeDilution(lm.group(3));
                r.iso = parseIso(lm.group(4));
                r.time35 = cleanTime(lm.group(5));
                r.time120 = cleanTime(lm.group(6));
                r.timeSheet = cleanTime(lm.group(7));
                r.temp = parseTemp(lm.group(8));
                r.sourceUrl = sourceUrl;
                r.sourceName = "Massive Dev Chart";
                out.add(r);
            }
        }
        return out;
    }

    private static List<Row> parseGenericTable(String html, String sourceUrl, String sourceName) {
        List<Row> out = new ArrayList<>();
        if (html == null) return out;
        Pattern tr = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>");
        Pattern td = Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>");
        Matcher rm = tr.matcher(html);
        while (rm.find()) {
            List<String> cells = new ArrayList<>();
            Matcher cm = td.matcher(rm.group(1));
            while (cm.find()) cells.add(cleanHtml(cm.group(1)));
            if (cells.size() < 5) continue;

            String joined = String.join(" | ", cells);
            if (!joined.toLowerCase(Locale.ROOT).matches("(?s).*(iso|asa|ei).*") &&
                    !joined.matches("(?s).*\\b(50|80|100|125|200|400|800|1600|3200)\\b.*")) continue;
            if (!joined.matches("(?s).*\\b\\d{1,2}(?::\\d{2}|\\.\\d+)?\\b.*")) continue;
            if (!joined.toLowerCase(Locale.ROOT).matches("(?s).*(18|19|20|21|22|23|24|25|26|27)\\s*°?\\s*c.*")) continue;

            String film = cells.get(0);
            String dilution = null;
            int iso = 0;
            String time = null;
            double temp = 20;
            for (String c : cells) {
                if (dilution == null && (c.equalsIgnoreCase("stock") || c.matches("(?i)1\\s*[+:]\\s*\\d+(?:\\s*[+:]\\s*\\d+)?"))) {
                    dilution = normalizeDilution(c);
                }
                if (iso == 0 && c.matches("\\d{2,4}")) {
                    int n = parseIso(c);
                    if (n >= 25 && n <= 12800) iso = n;
                }
                if (time == null && parseTimeRange(c) != null) time = c;
                if (c.toLowerCase(Locale.ROOT).matches(".*\\b(?:18|19|20|21|22|23|24|25|26|27)(?:\\.\\d+)?\\s*°?\\s*c\\b.*")) {
                    temp = parseTemp(c);
                }
            }
            if (dilution == null || iso == 0 || time == null) continue;
            Row r = new Row();
            r.film = film;
            r.developer = "";
            r.dilution = dilution;
            r.iso = iso;
            r.time35 = time;
            r.time120 = time;
            r.timeSheet = "";
            r.temp = temp;
            r.sourceUrl = sourceUrl;
            r.sourceName = sourceName;
            out.add(r);
        }
        return out;
    }

    private static Row chooseBest(List<Row> rows,
                                  String filmName, String format,
                                  String developer, String dilution, int iso) {
        Row best = null;
        double bestScore = -1;
        String nd = normalizeName(developer);
        String dil = normalizeDilution(dilution);

        for (Row r : rows) {
            if (r.iso != iso) continue;
            if (!normalizeDilution(r.dilution).equalsIgnoreCase(dil)) continue;

            String time = "4x5".equalsIgnoreCase(format) ? r.timeSheet : ("120".equals(format) ? r.time120 : r.time35);
            if (parseTimeRange(time) == null) continue;

            double filmScore = nameSimilarity(filmName, r.film);
            if (filmScore < 0.60) continue;

            double devScore;
            if (r.developer == null || r.developer.trim().isEmpty()) {
                devScore = 0.80;
            } else {
                String rd = normalizeName(r.developer);
                devScore = rd.equals(nd) ? 1.0 : nameSimilarity(developer, r.developer);
                if (devScore < 0.65) continue;
            }

            double score = filmScore * 0.72 + devScore * 0.28;
            if (score > bestScore) {
                bestScore = score;
                best = r;
            }
        }
        return best;
    }

    private static double nameSimilarity(String a, String b) {
        Set<String> aa = tokens(a);
        Set<String> bb = tokens(b);
        if (aa.isEmpty() || bb.isEmpty()) return 0;
        int intersection = 0;
        for (String x : aa) if (bb.contains(x)) intersection++;
        int min = Math.min(aa.size(), bb.size());
        int union = aa.size() + bb.size() - intersection;
        double containment = intersection / (double) min;
        double jaccard = intersection / (double) union;
        return containment * 0.70 + jaccard * 0.30;
    }

    private static Set<String> tokens(String s) {
        String n = normalizeName(s);
        Set<String> out = new LinkedHashSet<>();
        for (String t : n.split("\\s+")) {
            if (t.length() < 2) continue;
            if (t.equals("mm") || t.equals("film") || t.equals("pellicola") ||
                    t.equals("classic") || t.equals("creative") || t.equals("action") ||
                    t.equals("professional") || t.equals("pro")) continue;
            if ((n.contains("hp5") && t.equals("400")) || (n.contains("fp4") && t.equals("125"))) continue;
            if (t.equals("pan") && n.contains("kentmere")) continue;
            out.add(t);
        }
        return out;
    }

    private static String normalizeName(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT)
                .replace("plus", "")
                .replace("+", "")
                .replace("–", " ")
                .replace("—", " ")
                .replaceAll("\\b35\\s*mm\\b", " ")
                .replaceAll("\\b120\\b(?=\\s*$)", " ")
                .replaceAll("[^a-z0-9]+", " ")
                .trim();
    }

    private static String compactFilmQuery(String filmName) {
        String n = filmName == null ? "" : filmName;
        n = n.replaceAll("(?i)\\s*[—–-]\\s*(35\\s*mm|120)\\s*$", "");
        n = n.replaceAll("(?i)\\b(classic|creative|action|professional)\\b", "");
        return n.trim().replaceAll("\\s+", " ");
    }

    private static String normalizeDilution(String s) {
        if (s == null) return "";
        String d = cleanHtml(s).toLowerCase(Locale.ROOT).trim();
        if (d.contains("stock")) return "stock";
        d = d.replace(":", "+").replaceAll("\\s+", "");
        Matcher m = Pattern.compile("(\\d+(?:\\+\\d+)+)").matcher(d);
        return m.find() ? m.group(1) : d;
    }

    private static int parseIso(String s) {
        if (s == null) return 0;
        Matcher m = Pattern.compile("\\b(\\d{2,5})\\b").matcher(s.replace(",", ""));
        if (m.find()) {
            try { return Integer.parseInt(m.group(1)); } catch (Exception ignored) {}
        }
        return 0;
    }

    private static double parseTemp(String s) {
        if (s == null) return 20;
        Matcher m = Pattern.compile("(\\d{1,2}(?:[\\.,]\\d+)?)").matcher(s);
        if (m.find()) {
            try { return Double.parseDouble(m.group(1).replace(',', '.')); } catch (Exception ignored) {}
        }
        return 20;
    }

    private static String cleanTime(String s) {
        if (s == null) return "";
        String c = cleanHtml(s).replace('\u00a0', ' ').trim();
        if (c.equals("#") || c.equals("-") || c.equals("—")) return "";
        return c;
    }

    static int[] parseTimeRange(String raw) {
        if (raw == null) return null;
        String s = cleanTime(raw).toLowerCase(Locale.ROOT)
                .replace("min", "").replace("mins", "").replace("minutes", "")
                .replace(',', '.').trim();
        if (s.isEmpty()) return null;

        Matcher range = Pattern.compile("^\\s*([0-9]+(?::[0-9]{1,2}|\\.[0-9]+)?)\\s*[-–]\\s*([0-9]+(?::[0-9]{1,2}|\\.[0-9]+)?)\\s*$").matcher(s);
        if (range.find()) {
            int a = parseOneTime(range.group(1));
            int b = parseOneTime(range.group(2));
            if (a > 0 && b >= a) return new int[]{a, b};
        }

        int one = parseOneTime(s);
        return one > 0 ? new int[]{one, one} : null;
    }

    private static int parseOneTime(String s) {
        s = s.trim();
        if (s.matches("\\d{1,3}:\\d{1,2}")) {
            String[] p = s.split(":");
            try {
                int min = Integer.parseInt(p[0]);
                int sec = Integer.parseInt(p[1]);
                if (sec >= 60) return 0;
                return min * 60 + sec;
            } catch (Exception ignored) { return 0; }
        }
        if (s.matches("\\d{1,3}(?:\\.\\d+)?")) {
            try {
                double min = Double.parseDouble(s);
                return (int) Math.round(min * 60.0);
            } catch (Exception ignored) { return 0; }
        }
        return 0;
    }

    private static String cleanHtml(String s) {
        if (s == null) return "";
        String x = s
                .replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?is)<br\\s*/?>", " ")
                .replaceAll("(?is)<[^>]+>", " ")
                .replace("&nbsp;", " ")
                .replace("&#160;", " ")
                .replace("&amp;", "&")
                .replace("&quot;", "\"")
                .replace("&#39;", "'")
                .replace("&plus;", "+")
                .replace("&#43;", "+")
                .replace("&deg;", "°");
        return x.replaceAll("\\s+", " ").trim();
    }

    private static boolean looksLikeManufacturer(String url) {
        if (url == null) return false;
        String u = url.toLowerCase(Locale.ROOT);
        return u.contains("ilfordphoto.com") || u.contains("harmantechnology.com") ||
                u.contains("foma.cz") || u.contains("fomaobchod") ||
                u.contains("bellinifoto") || u.contains("adox") ||
                u.contains("kodak") || u.contains("cinestill") ||
                u.contains("bergger") || u.contains("ferrania");
    }

    private static void addUnique(List<String> list, String value) {
        if (value == null || value.trim().isEmpty()) return;
        if (!list.contains(value)) list.add(value);
    }

    private static String fetch(String url, int maxChars) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setInstanceFollowRedirects(true);
        c.setConnectTimeout(9000);
        c.setReadTimeout(13000);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Android) DarkroomAssistant/0.2");
        c.setRequestProperty("Accept-Language", "en-US,en;q=0.9,it;q=0.8");
        c.setRequestProperty("Accept", "text/html,application/xhtml+xml,*/*;q=0.8");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        InputStream in = c.getInputStream();
        BufferedReader br = new BufferedReader(new InputStreamReader(in));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null && sb.length() < maxChars) {
            sb.append(line).append('\n');
        }
        br.close();
        c.disconnect();
        return sb.toString();
    }

    static String formatSeconds(int seconds) {
        int m = seconds / 60;
        int s = seconds % 60;
        return s == 0 ? m + " min" : String.format(Locale.ITALY, "%d min %02d s", m, s);
    }
}
