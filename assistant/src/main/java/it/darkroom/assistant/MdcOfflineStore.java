package it.darkroom.assistant;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Copia LOCALE privata del Massive Dev Chart.
 *
 * Il database completo NON e' incluso nell'APK. Al primo avvio viene scaricato
 * direttamente da Digitaltruth sul dispositivo dell'utente e poi usato offline.
 * Le ricerche nell'app interrogano esclusivamente SQLite: niente Google, Bing,
 * negozi, menu di siti o classificazioni euristiche.
 */
final class MdcOfflineStore {
    private static final String DB_NAME = "mdc_offline.sqlite";
    private static final int DB_VERSION = 1;
    private static final String SOURCE_NAME = "Massive Dev Chart / Digitaltruth (copia offline personale)";
    private static final String SOURCE_HOME = "https://www.digitaltruth.com/devchart.php";
    private static final double JOBO_FACTOR = 0.85;
    private static final double TEMP_FACTOR_PER_C = 0.91;

    interface ProgressListener {
        void onProgress(int done, int total, String message);
        void onComplete(boolean ok, String message, int films, int developers, int rows);
    }

    private static Context app;
    private static Helper helper;
    private static volatile boolean syncing = false;

    private static final class TimeRow {
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
    }

    private MdcOfflineStore() {}

    static synchronized void init(Context context) {
        if (helper != null) return;
        app = context.getApplicationContext();
        helper = new Helper(app);
        helper.getWritableDatabase();
    }

    static boolean isReady() {
        if (helper == null) return false;
        SQLiteDatabase db = helper.getReadableDatabase();
        return scalar(db, "SELECT COUNT(*) FROM times") >= 1000 &&
                scalar(db, "SELECT COUNT(*) FROM developers") >= 100 &&
                scalar(db, "SELECT COUNT(*) FROM films") >= 150;
    }

    static int rowCount() {
        if (helper == null) return 0;
        return scalar(helper.getReadableDatabase(), "SELECT COUNT(*) FROM times");
    }

    static int filmCount() {
        if (helper == null) return 0;
        return scalar(helper.getReadableDatabase(), "SELECT COUNT(*) FROM films");
    }

    static int developerCount() {
        if (helper == null) return 0;
        return scalar(helper.getReadableDatabase(), "SELECT COUNT(*) FROM developers");
    }

    static String lastSyncLabel() {
        if (helper == null) return "";
        SQLiteDatabase db = helper.getReadableDatabase();
        try (Cursor c = db.rawQuery("SELECT value FROM meta WHERE key='last_sync'", null)) {
            return c.moveToFirst() ? c.getString(0) : "";
        }
    }

    static List<OnlineCatalogSearch.SearchResult> searchDevelopers(String query, int max) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        if (!isReady()) return out;
        String q = norm(query);
        if (q.length() < 3) return out;
        SQLiteDatabase db = helper.getReadableDatabase();
        List<String> names = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT name FROM developers WHERE norm_name LIKE ? LIMIT 120",
                new String[]{"%" + q + "%"})) {
            while (c.moveToNext()) names.add(c.getString(0));
        }
        sortMatches(names, q);
        for (String name : names) {
            out.add(new OnlineCatalogSearch.SearchResult(
                    name, SOURCE_HOME, "MDC_OFFLINE_DEVELOPER"));
            if (out.size() >= max) break;
        }
        return out;
    }

    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query, int max) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        if (!isReady()) return out;
        String q = norm(query);
        if (q.length() < 3) return out;
        SQLiteDatabase db = helper.getReadableDatabase();
        List<String> names = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT name FROM films WHERE norm_name LIKE ? LIMIT 150",
                new String[]{"%" + q + "%"})) {
            while (c.moveToNext()) names.add(c.getString(0));
        }
        sortMatches(names, q);
        for (String name : names) {
            out.add(new OnlineCatalogSearch.SearchResult(
                    name, SOURCE_HOME, "MDC_OFFLINE_FILM"));
            if (out.size() >= max) break;
        }
        return out;
    }

    static String[] dilutionsForDeveloper(String developer) {
        if (!isReady()) return new String[0];
        LinkedHashSet<String> vals = new LinkedHashSet<>();
        SQLiteDatabase db = helper.getReadableDatabase();
        try (Cursor c = db.rawQuery(
                "SELECT dilution FROM times WHERE developer_norm=? AND dilution<>'' GROUP BY dilution ORDER BY dilution",
                new String[]{norm(developer)})) {
            while (c.moveToNext()) vals.add(c.getString(0));
        }
        return vals.toArray(new String[0]);
    }

    static int nominalIsoForFilm(String film) {
        if (!isReady()) return 0;
        String n = stripFormat(film);
        SQLiteDatabase db = helper.getReadableDatabase();
        Map<Integer,Integer> freq = new LinkedHashMap<>();
        try (Cursor c = db.rawQuery(
                "SELECT iso, COUNT(*) n FROM times WHERE film_norm=? AND iso>0 GROUP BY iso ORDER BY n DESC, iso ASC",
                new String[]{norm(n)})) {
            while (c.moveToNext()) freq.put(c.getInt(0), c.getInt(1));
        }
        int hinted = isoFromName(n);
        if (hinted > 0 && freq.containsKey(hinted)) return hinted;
        if (!freq.isEmpty()) return freq.keySet().iterator().next();
        return hinted;
    }

    static boolean isOfflineDeveloperResult(OnlineCatalogSearch.SearchResult r) {
        return r != null && r.snippet != null && r.snippet.contains("MDC_OFFLINE_DEVELOPER");
    }

    static boolean isOfflineFilmResult(OnlineCatalogSearch.SearchResult r) {
        return r != null && r.snippet != null && r.snippet.contains("MDC_OFFLINE_FILM");
    }

    static DevTimeEngine.Result lookup(String filmName, String format, String developer,
                                       String dilution, int iso, double targetTemp) {
        if (!isReady()) return null;
        if (targetTemp < 18.0 || targetTemp > 27.0) return null;
        String fn = norm(stripFormat(filmName));
        String dn = norm(developer);
        String dil = normDilution(dilution);
        SQLiteDatabase db = helper.getReadableDatabase();

        List<TimeRow> candidates = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT film,developer,dilution,iso,time35,time120,timesheet,temp,notes,source_url " +
                        "FROM times WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso=?",
                new String[]{fn, dn, dil, String.valueOf(iso)})) {
            while (c.moveToNext()) {
                TimeRow r = new TimeRow();
                r.film = c.getString(0); r.developer = c.getString(1); r.dilution = c.getString(2);
                r.iso = c.getInt(3); r.time35 = c.getString(4); r.time120 = c.getString(5);
                r.timeSheet = c.getString(6); r.temp = c.getDouble(7); r.notes = c.getString(8);
                r.sourceUrl = c.getString(9); candidates.add(r);
            }
        }
        if (candidates.isEmpty()) return null;
        Collections.sort(candidates, (a,b) -> Double.compare(Math.abs(a.temp-targetTemp), Math.abs(b.temp-targetTemp)));

        for (TimeRow row : candidates) {
            String raw = "120".equals(format) ? row.time120 : row.time35;
            boolean crossFormat = false;
            if (!hasTime(raw)) {
                String alt = "120".equals(format) ? row.time35 : row.time120;
                if (!hasTime(alt)) alt = row.timeSheet;
                if (hasTime(alt)) { raw = alt; crossFormat = true; }
            }
            int[] range = parseTimeRange(raw);
            if (range == null) continue;
            int baseLow = range[0], baseHigh = range[1];
            int low = baseLow, high = baseHigh;
            boolean tempConverted = Math.abs(targetTemp - row.temp) > 0.01;
            if (tempConverted) {
                low = roundTo15((int)Math.round(low * Math.pow(TEMP_FACTOR_PER_C, targetTemp-row.temp)));
                high = roundTo15((int)Math.round(high * Math.pow(TEMP_FACTOR_PER_C, targetTemp-row.temp)));
            }
            low = roundTo5((int)Math.round(low * JOBO_FACTOR));
            high = roundTo5((int)Math.round(high * JOBO_FACTOR));
            String warning = low < 300 ? "Attenzione: tempo finale sotto 5 minuti; aumenta il rischio di sviluppo non uniforme." : "";
            if (crossFormat) {
                if (!warning.isEmpty()) warning += "\n";
                warning += "Digitaltruth non riporta un tempo per questo formato: usato il tempo disponibile per un altro formato come punto di partenza.";
            }
            return new DevTimeEngine.Result(true, low, high, baseLow, baseHigh,
                    row.temp, targetTemp, SOURCE_NAME, row.sourceUrl,
                    row.film, row.developer, row.dilution, row.iso,
                    format == null ? "35" : format, tempConverted, true, warning,
                    "Dato letto dal database offline sincronizzato da Digitaltruth; nessuna ricerca web durante il calcolo.");
        }
        return null;
    }

    static void syncAsync(ProgressListener listener) {
        if (helper == null || syncing) return;
        syncing = true;
        new Thread(() -> {
            boolean ok = false;
            String message;
            int films = 0, devs = 0, rowsCount = 0;
            try {
                List<String> developers = loadDeveloperIndex();
                if (developers.size() < 150) throw new IllegalStateException("Indice rivelatori incompleto: " + developers.size());
                List<TimeRow> all = Collections.synchronizedList(new ArrayList<>());
                AtomicInteger done = new AtomicInteger(0);
                AtomicInteger failed = new AtomicInteger(0);
                ExecutorService pool = Executors.newFixedThreadPool(4);
                for (String developer : developers) {
                    pool.submit(() -> {
                        try {
                            List<TimeRow> rows = fetchDeveloperRows(developer);
                            if (rows.isEmpty()) failed.incrementAndGet();
                            else all.addAll(rows);
                        } catch (Exception e) {
                            failed.incrementAndGet();
                        }
                        int n = done.incrementAndGet();
                        if (listener != null && (n == 1 || n % 4 == 0 || n == developers.size())) {
                            listener.onProgress(n, developers.size(), "Scarico Digitaltruth " + n + "/" + developers.size());
                        }
                    });
                }
                pool.shutdown();
                if (!pool.awaitTermination(8, TimeUnit.MINUTES)) {
                    pool.shutdownNow();
                    throw new IllegalStateException("Timeout durante lo scarico.");
                }
                if (all.size() < 1000) throw new IllegalStateException("Dati insufficienti: " + all.size() + " righe");

                SQLiteDatabase db = helper.getWritableDatabase();
                db.beginTransaction();
                try {
                    db.delete("times", null, null);
                    db.delete("films", null, null);
                    db.delete("developers", null, null);
                    Set<String> filmSet = new LinkedHashSet<>();
                    Set<String> devSet = new LinkedHashSet<>();
                    for (TimeRow r : all) {
                        ContentValues cv = new ContentValues();
                        cv.put("film", r.film); cv.put("film_norm", norm(r.film));
                        cv.put("developer", r.developer); cv.put("developer_norm", norm(r.developer));
                        cv.put("dilution", r.dilution); cv.put("dilution_norm", normDilution(r.dilution));
                        cv.put("iso", r.iso); cv.put("time35", nz(r.time35)); cv.put("time120", nz(r.time120));
                        cv.put("timesheet", nz(r.timeSheet)); cv.put("temp", r.temp); cv.put("notes", nz(r.notes));
                        cv.put("source_url", nz(r.sourceUrl));
                        db.insertWithOnConflict("times", null, cv, SQLiteDatabase.CONFLICT_IGNORE);
                        filmSet.add(r.film); devSet.add(r.developer);
                    }
                    for (String f : filmSet) {
                        ContentValues cv = new ContentValues(); cv.put("name", f); cv.put("norm_name", norm(f));
                        db.insertWithOnConflict("films", null, cv, SQLiteDatabase.CONFLICT_IGNORE);
                    }
                    for (String d : devSet) {
                        ContentValues cv = new ContentValues(); cv.put("name", d); cv.put("norm_name", norm(d));
                        db.insertWithOnConflict("developers", null, cv, SQLiteDatabase.CONFLICT_IGNORE);
                    }
                    putMeta(db, "last_sync", new java.text.SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.ITALY).format(new java.util.Date()));
                    putMeta(db, "failed_pages", String.valueOf(failed.get()));
                    db.setTransactionSuccessful();
                } finally {
                    db.endTransaction();
                }
                films = filmCount(); devs = developerCount(); rowsCount = rowCount();
                ok = films >= 150 && devs >= 100 && rowsCount >= 1000;
                message = ok ? "Database offline pronto" : "Database incompleto";
                if (failed.get() > 0) message += " · " + failed.get() + " pagine senza righe";
            } catch (Exception e) {
                message = "Sincronizzazione fallita: " + e.getMessage();
            } finally {
                syncing = false;
            }
            if (listener != null) listener.onComplete(ok, message, films, devs, rowsCount);
        }).start();
    }

    private static List<String> loadDeveloperIndex() throws Exception {
        LinkedHashSet<String> names = new LinkedHashSet<>();
        String[] indexUrls = new String[]{
                "https://www.digitaltruth.com/chart/print.php",
                "https://ftp.digitaltruth.com/chart/print.php"
        };
        for (String u : indexUrls) {
            try {
                String html = fetch(u, 1600000);
                Matcher m = Pattern.compile("(?is)<a[^>]+href=[\\\"']([^\\\"']*Developer=[^\\\"']+)[\\\"'][^>]*>(.*?)</a>").matcher(html);
                while (m.find()) {
                    String title = cleanHtml(m.group(2));
                    if (title.length() > 1) names.add(title);
                }
                if (names.size() >= 150) break;
            } catch (Exception ignored) {}
        }
        // Fallback: elenco dei soli nomi, incluso nell'APK per poter sincronizzare anche se la pagina indice blocca il client.
        try (InputStream in = app.getAssets().open("mdc_developers_seed.txt");
             BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim(); if (!line.isEmpty()) names.add(line);
            }
        }
        return new ArrayList<>(names);
    }

    private static List<TimeRow> fetchDeveloperRows(String developer) throws Exception {
        String enc = URLEncoder.encode(developer, "UTF-8");
        String[] urls = new String[]{
                "https://ftp.digitaltruth.com/chart/search_text.php?Developer=" + enc,
                "https://www.digitaltruth.com/chart/search_text.php?Developer=" + enc
        };
        Exception last = null;
        for (String url : urls) {
            for (int attempt=0; attempt<2; attempt++) {
                try {
                    String html = fetch(url, 2400000);
                    List<TimeRow> rows = parseRows(html, url);
                    if (!rows.isEmpty()) return rows;
                } catch (Exception e) { last = e; }
                try { Thread.sleep(120L * (attempt + 1)); } catch (InterruptedException ignored) {}
            }
        }
        if (last != null) throw last;
        return new ArrayList<>();
    }

    private static List<TimeRow> parseRows(String html, String sourceUrl) {
        List<TimeRow> out = new ArrayList<>();
        if (html == null) return out;
        Matcher tr = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
        Pattern td = Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>");
        while (tr.find()) {
            List<String> cells = new ArrayList<>();
            Matcher cm = td.matcher(tr.group(1));
            while (cm.find()) cells.add(cleanHtml(cm.group(1)));
            if (cells.size() < 8) continue;
            String h0 = cells.get(0).toLowerCase(Locale.ROOT);
            String h1 = cells.get(1).toLowerCase(Locale.ROOT);
            if (h0.equals("film") || h1.equals("developer")) continue;
            TimeRow r = new TimeRow();
            r.film = cells.get(0).trim();
            r.developer = cells.get(1).trim();
            r.dilution = normalizeDilution(cells.get(2));
            r.iso = parseIso(cells.get(3));
            r.time35 = cleanTime(cells.get(4));
            r.time120 = cleanTime(cells.get(5));
            r.timeSheet = cleanTime(cells.get(6));
            r.temp = parseTemp(cells.get(7));
            r.notes = cells.size() > 8 ? cells.get(8).trim() : "";
            r.sourceUrl = sourceUrl;
            if (!r.film.isEmpty() && !r.developer.isEmpty() && r.iso > 0 && r.temp > 0) out.add(r);
        }
        return out;
    }

    private static String fetch(String url, int maxChars) throws Exception {
        HttpURLConnection c = (HttpURLConnection)new URL(url).openConnection();
        c.setConnectTimeout(15000); c.setReadTimeout(25000); c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36");
        c.setRequestProperty("Accept", "text/html,application/xhtml+xml");
        c.setRequestProperty("Accept-Language", "en-US,en;q=0.8");
        c.setRequestProperty("Referer", "https://www.digitaltruth.com/");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            char[] buf = new char[8192]; int n;
            while ((n = br.read(buf)) >= 0 && sb.length() < maxChars) sb.append(buf, 0, Math.min(n, maxChars-sb.length()));
        } finally { c.disconnect(); }
        return sb.toString();
    }

    private static void sortMatches(List<String> names, String q) {
        Collections.sort(names, new Comparator<String>() {
            int score(String n) {
                String x = norm(n);
                if (x.equals(q)) return 1000;
                if (x.startsWith(q)) return 950;
                for (String t : x.split(" ")) if (t.startsWith(q)) return 900;
                if (x.contains(q)) return 700;
                return 0;
            }
            @Override public int compare(String a, String b) {
                int d = Integer.compare(score(b), score(a));
                return d != 0 ? d : a.compareToIgnoreCase(b);
            }
        });
    }

    private static int scalar(SQLiteDatabase db, String sql) {
        try (Cursor c = db.rawQuery(sql, null)) { return c.moveToFirst() ? c.getInt(0) : 0; }
    }

    private static void putMeta(SQLiteDatabase db, String key, String value) {
        ContentValues cv = new ContentValues(); cv.put("key", key); cv.put("value", value);
        db.insertWithOnConflict("meta", null, cv, SQLiteDatabase.CONFLICT_REPLACE);
    }

    private static String stripFormat(String s) {
        if (s == null) return "";
        return s.replaceAll("(?i)\\s*[—-]\\s*(35\\s*mm|120)\\s*$", "").trim();
    }

    private static int isoFromName(String s) {
        Matcher m = Pattern.compile("(?<!\\d)(25|32|40|50|64|80|100|125|160|200|250|320|400|500|640|800|1000|1250|1600|3200)(?!\\d)").matcher(s == null ? "" : s);
        int last = 0; while (m.find()) last = Integer.parseInt(m.group(1)); return last;
    }

    private static int parseIso(String s) {
        try { return Integer.parseInt((s == null ? "" : s).replaceAll("[^0-9]", "")); }
        catch (Exception e) { return 0; }
    }

    private static double parseTemp(String s) {
        try { return Double.parseDouble((s == null ? "" : s).toUpperCase(Locale.ROOT).replace("°", "").replace("C", "").replace(',', '.').replaceAll("[^0-9.]", "")); }
        catch (Exception e) { return 20.0; }
    }

    private static String cleanTime(String s) {
        if (s == null) return "";
        return s.replace('\u00a0', ' ').trim().replaceAll("\\s+", "");
    }

    private static boolean hasTime(String s) { return parseTimeRange(s) != null; }

    private static int[] parseTimeRange(String raw) {
        if (raw == null) return null;
        String s = raw.trim().replace(',', '.');
        if (s.isEmpty() || s.equals("-") || s.equals("—")) return null;
        String[] parts = s.split("-");
        try {
            int a = minutesToSeconds(parts[0]);
            int b = parts.length > 1 ? minutesToSeconds(parts[1]) : a;
            if (a <= 0 || b <= 0) return null;
            return new int[]{Math.min(a,b), Math.max(a,b)};
        } catch (Exception e) { return null; }
    }

    private static int minutesToSeconds(String s) {
        s = s.trim();
        if (s.contains(":")) {
            String[] p = s.split(":"); return Integer.parseInt(p[0])*60 + Integer.parseInt(p[1]);
        }
        return (int)Math.round(Double.parseDouble(s)*60.0);
    }

    private static int roundTo15(int s) { return Math.max(15, (int)Math.round(s/15.0)*15); }
    private static int roundTo5(int s) { return Math.max(5, (int)Math.round(s/5.0)*5); }

    private static String normalizeDilution(String s) {
        if (s == null) return "";
        String x = cleanHtml(s).trim();
        if (x.equalsIgnoreCase("stock")) return "stock";
        x = x.replace(':', '+').replace(" ", "");
        return x;
    }

    private static String normDilution(String s) { return normalizeDilution(s).toLowerCase(Locale.ROOT); }

    private static String norm(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT)
                .replace('–',' ').replace('—',' ').replace('-',' ')
                .replaceAll("[^\\p{L}\\p{N}+]+", " ")
                .trim().replaceAll("\\s+", " ");
    }

    private static String nz(String s) { return s == null ? "" : s; }

    private static String cleanHtml(String s) {
        if (s == null) return "";
        String x = s.replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?is)<[^>]+>", " ");
        x = x.replace("&nbsp;", " ").replace("&#160;", " ")
                .replace("&amp;", "&").replace("&quot;", "\"")
                .replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">");
        Matcher m = Pattern.compile("&#(\\d+);").matcher(x);
        StringBuffer b = new StringBuffer();
        while (m.find()) {
            try { m.appendReplacement(b, Matcher.quoteReplacement(String.valueOf((char)Integer.parseInt(m.group(1))))); }
            catch (Exception e) { m.appendReplacement(b, " "); }
        }
        m.appendTail(b);
        return b.toString().replace('\u00a0',' ').trim().replaceAll("\\s+", " ");
    }

    private static final class Helper extends SQLiteOpenHelper {
        Helper(Context c) { super(c, DB_NAME, null, DB_VERSION); }
        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)");
            db.execSQL("CREATE TABLE films(name TEXT NOT NULL,norm_name TEXT PRIMARY KEY)");
            db.execSQL("CREATE TABLE developers(name TEXT NOT NULL,norm_name TEXT PRIMARY KEY)");
            db.execSQL("CREATE TABLE times(id INTEGER PRIMARY KEY AUTOINCREMENT,film TEXT NOT NULL,film_norm TEXT NOT NULL,developer TEXT NOT NULL,developer_norm TEXT NOT NULL,dilution TEXT,dilution_norm TEXT,iso INTEGER,time35 TEXT,time120 TEXT,timesheet TEXT,temp REAL,notes TEXT,source_url TEXT,UNIQUE(film_norm,developer_norm,dilution_norm,iso,time35,time120,timesheet,temp,notes))");
            db.execSQL("CREATE INDEX idx_times_lookup ON times(film_norm,developer_norm,dilution_norm,iso)");
            db.execSQL("CREATE INDEX idx_film_search ON films(norm_name)");
            db.execSQL("CREATE INDEX idx_dev_search ON developers(norm_name)");
        }
        @Override public void onUpgrade(SQLiteDatabase db, int oldV, int newV) {
            db.execSQL("DROP TABLE IF EXISTS times"); db.execSQL("DROP TABLE IF EXISTS films");
            db.execSQL("DROP TABLE IF EXISTS developers"); db.execSQL("DROP TABLE IF EXISTS meta"); onCreate(db);
        }
    }
}
