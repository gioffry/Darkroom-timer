package it.darkroom.assistant;

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
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Broker live delle fonti per Darkroom Assistant.
 *
 * Regole:
 * - pellicole e rivelatori pellicola vengono scoperti ONLINE dall'indice live
 *   del Massive Dev Chart (Digitaltruth), non da un catalogo hardcoded;
 * - la ricerca lavora per prefisso/token (es. "rod" -> Rodinal,
 *   "superg" -> Rollei Supergrain, "fuji" -> Fuji/Fujifilm...);
 * - un elemento proveniente dall'indice Developers di Digitaltruth e' SEMPRE
 *   classificato come rivelatore pellicola: non puo' diventare fixer/stop per
 *   parole casuali trovate in una pagina;
 * - per dati di prodotto (stock, carta, stop, fix, scadenza) si cerca prima la
 *   fonte del produttore; se un dato non e' esplicito resta non determinato.
 */
final class SourceBroker {
    private static final String[] MDC_INDEXES = new String[]{
            "https://www.digitaltruth.com/chart/print.php",
            "https://ftp.digitaltruth.com/chart/print.php",
            "https://www.digitaltruth.com/devchart.php"
    };
    private static final long INDEX_TTL_MS = 15L * 60L * 1000L;

    private static final class Brand {
        final String name;
        final String[] aliases;
        final String[] domains;
        Brand(String name, String[] aliases, String[] domains) {
            this.name = name;
            this.aliases = aliases;
            this.domains = domains;
        }
    }

    // Sono fonti, non cataloghi di singoli prodotti. I prodotti vengono scoperti online.
    private static final Brand[] BRANDS = new Brand[]{
            new Brand("Ilford/Harman", new String[]{"ilford","harman","kentmere"}, new String[]{"ilfordphoto.com","harmantechnology.com"}),
            new Brand("Foma", new String[]{"foma","fomapan","fomadon","fomafix","fomaspeed"}, new String[]{"foma.cz"}),
            new Brand("Adox", new String[]{"adox","rodinal","adonal","adonal r09","fx-39","fx39","adoxal"}, new String[]{"adox.de","fotoimpex.com"}),
            new Brand("Kodak", new String[]{"kodak","d-76","d76","xtol","hc-110","hc110","t-max","tmax","tri-x","trix"}, new String[]{"kodak.com","kodakalaris.com"}),
            new Brand("Rollei", new String[]{"rollei","supergrain","rpx","retro","superpan","print neutral","print warmtone","citro stop","fix acid","fix neutral"}, new String[]{"rolleianalog.com"}),
            new Brand("Bellini", new String[]{"bellini","bell","hydrofen","ecofilm","euro hc","nucleol","gradual","bwdek","f205","fx100","aminophenol","ecostop","indexstop"}, new String[]{"bellinifoto.it"}),
            new Brand("Fujifilm", new String[]{"fuji","fujifilm","neopan","acros","microfine"}, new String[]{"fujifilm.com"}),
            new Brand("Ferrania", new String[]{"ferrania","p30","p33","orto"}, new String[]{"filmferrania.com"}),
            new Brand("AgfaPhoto", new String[]{"agfa","agfaphoto","apx"}, new String[]{"agfaphoto.com"}),
            new Brand("Bergger", new String[]{"bergger","pancro","ber49"}, new String[]{"bergger.com"}),
            new Brand("CineStill", new String[]{"cinestill","df96","d96","bwxx"}, new String[]{"cinestillfilm.com"}),
            new Brand("Ars-Imago", new String[]{"ars imago","ars-imago"}, new String[]{"ars-imago.com"}),
            new Brand("Moersch", new String[]{"moersch"}, new String[]{"moersch-photochemie.de"}),
            new Brand("Tetenal", new String[]{"tetenal"}, new String[]{"tetenal.com"})
    };

    private static final class IndexItem {
        final String name;
        final String url;
        final boolean developer;
        IndexItem(String name, String url, boolean developer) {
            this.name = name;
            this.url = url;
            this.developer = developer;
        }
    }

    private static volatile long indexLoadedAt = 0L;
    private static volatile List<IndexItem> cachedFilms = new ArrayList<>();
    private static volatile List<IndexItem> cachedDevelopers = new ArrayList<>();

    static List<OnlineCatalogSearch.SearchResult> searchChemicals(String query) {
        LinkedHashMap<String, OnlineCatalogSearch.SearchResult> out = new LinkedHashMap<>();

        // Prima fonte: indice LIVE dei rivelatori del Massive Dev Chart.
        for (IndexItem i : searchMdc(query, true, 14)) {
            put(out, new OnlineCatalogSearch.SearchResult(
                    i.name,
                    i.url,
                    "Massive Dev Chart · FILM_DEVELOPER · indice live Digitaltruth"));
        }

        // Seconda fonte: produttori, utile anche per stop/fix/rivelatori carta.
        if (out.size() < 12) {
            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, true, 14 - out.size())) {
                if (strictChemicalEntity(query, r)) put(out, r);
            }
        }

        return new ArrayList<>(out.values());
    }

    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query) {
        LinkedHashMap<String, OnlineCatalogSearch.SearchResult> out = new LinkedHashMap<>();

        for (IndexItem i : searchMdc(query, false, 16)) {
            put(out, new OnlineCatalogSearch.SearchResult(
                    i.name,
                    i.url,
                    "Massive Dev Chart · FILM · indice live Digitaltruth"));
        }

        if (out.size() < 12) {
            for (OnlineCatalogSearch.SearchResult r : officialSearch(query, false, 14 - out.size())) {
                if (strictFilmEntity(query, r)) put(out, r);
            }
        }
        return new ArrayList<>(out.values());
    }

    /**
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

    static boolean isManufacturerUrl(String url) {
        String u = norm(url);
        for (Brand b : BRANDS) {
            for (String d : b.domains) if (u.contains(norm(d))) return true;
        }
        return false;
    }

    static boolean matchesQueryDomain(String query, String url) {
        Brand b = brandForQuery(query);
        if (b == null) return false;
        String u = norm(url);
        for (String d : b.domains) if (u.contains(norm(d))) return true;
        return false;
    }

    static String resolveOfficialUrl(String productName, boolean chemical, String initialUrl) {
        if (isManufacturerUrl(initialUrl)) return initialUrl;
        List<OnlineCatalogSearch.SearchResult> candidates = officialSearch(productName, chemical, 10);
        String pn = norm(productName);
        OnlineCatalogSearch.SearchResult best = null;
        int bestScore = 0;
        for (OnlineCatalogSearch.SearchResult r : candidates) {
            if (!isManufacturerUrl(r.url)) continue;
            int s = productMatchScore(pn, norm(r.title + " " + r.url));
            if (s > bestScore) { bestScore = s; best = r; }
        }
        return best != null && bestScore >= 500 ? best.url : initialUrl;
    }

    static OnlineCatalogSearch.ChemicalData enrichChemical(OnlineCatalogSearch.SearchResult r) {
        if (r == null) return null;

        boolean mdcDeveloper = isMdcDeveloper(r);
        String official = resolveOfficialUrl(r.title, true, r.url);
        String officialText = "";
        if (isManufacturerUrl(official)) {
            try { officialText = SourceText.fetchText(official, 500000); } catch (Exception ignored) {}
        }

        if (mdcDeveloper) {
            // Questo e' il punto fondamentale: identita' dal database tecnico, non dal testo casuale.
            int roles = OnlineCatalogSearch.ROLE_FILM_DEV;
            String strict = r.title + " " + first(officialText, 12000);
            if (explicitPaperDeveloper(strict)) roles |= OnlineCatalogSearch.ROLE_PAPER_DEV;

            List<String> filmDil = extractMdcDeveloperDilutions(r.url);
            if (filmDil.isEmpty() && !officialText.isEmpty()) filmDil = extractDilutionsStrict(officialText);

            List<String> paperDil = new ArrayList<>();
            if ((roles & OnlineCatalogSearch.ROLE_PAPER_DEV) != 0) paperDil = extractDilutionsStrict(officialText);

            boolean stock = explicitStockPreparation(officialText);
            String instruction = stock ? extractInstruction(officialText) : null;
            int expiry = extractExpiryDays(officialText);
            String src = isManufacturerUrl(official) ? official : r.url;

            return new OnlineCatalogSearch.ChemicalData(
                    cleanProductTitle(r.title), roles, stock,
                    filmDil.toArray(new String[0]), paperDil.toArray(new String[0]),
                    null, instruction, expiry, src);
        }

        // Prodotto non proveniente dall'indice MDC: classificazione volutamente restrittiva.
        String page = "";
        String source = official;
        if (source == null || source.isEmpty()) source = r.url;
        try { page = SourceText.fetchText(source, 500000); } catch (Exception ignored) {}

        String evidence = r.title + " " + r.snippet + " " + first(page, 14000);
        int roles = strictRole(evidence);
        if (roles == 0) return null; // meglio non determinato che un fissaggio inventato

        List<String> dils = extractDilutionsStrict(evidence);
        boolean stock = explicitStockPreparation(evidence);
        String[] film = (roles & OnlineCatalogSearch.ROLE_FILM_DEV) != 0 ? dils.toArray(new String[0]) : new String[0];
        String[] paper = (roles & OnlineCatalogSearch.ROLE_PAPER_DEV) != 0 ? dils.toArray(new String[0]) : new String[0];
        String working = ((roles & (OnlineCatalogSearch.ROLE_STOP | OnlineCatalogSearch.ROLE_FIX)) != 0 && !dils.isEmpty()) ? dils.get(0) : null;

        return new OnlineCatalogSearch.ChemicalData(
                cleanProductTitle(r.title), roles, stock,
                film, paper, working,
                stock ? extractInstruction(evidence) : null,
                extractExpiryDays(evidence),
                source == null ? "" : source);
    }

    static OnlineCatalogSearch.FilmData enrichFilm(OnlineCatalogSearch.SearchResult r) {
        if (r == null) return null;
        boolean mdcFilm = isMdcFilm(r);
        String official = resolveOfficialUrl(r.title, false, r.url);
        String page = "";
        if (isManufacturerUrl(official)) {
            try { page = SourceText.fetchText(official, 400000); } catch (Exception ignored) {}
        }

        int iso = nominalIsoFromName(r.title);
        if (iso <= 0) iso = extractExplicitIso(r.snippet + " " + first(page, 10000));
        String format = extractFormat(r.title + " " + r.snippet + " " + first(page, 10000));

        // Per una pellicola presente nel MDC il nome e' valido anche se l'ISO nominale non e' ricavabile.
        if (!mdcFilm && iso <= 0 && page.isEmpty()) return null;
        return new OnlineCatalogSearch.FilmData(
                cleanProductTitle(r.title), iso, format,
                isManufacturerUrl(official) ? official : r.url);
    }

    // ---------------------------------------------------------------------
    // Massive Dev Chart live index
    // ---------------------------------------------------------------------

    private static List<IndexItem> searchMdc(String query, boolean developers, int max) {
        ensureMdcIndex();
        String q = norm(query);
        List<IndexItem> source = developers ? cachedDevelopers : cachedFilms;
        List<IndexItem> hits = new ArrayList<>();
        for (IndexItem i : source) {
            if (mdcMatchScore(q, norm(i.name)) > 0) hits.add(i);
        }
        Collections.sort(hits, new Comparator<IndexItem>() {
            @Override public int compare(IndexItem a, IndexItem b) {
                int sa = mdcMatchScore(q, norm(a.name));
                int sb = mdcMatchScore(q, norm(b.name));
                if (sa != sb) return Integer.compare(sb, sa);
                return a.name.compareToIgnoreCase(b.name);
            }
        });
        return hits.size() > max ? new ArrayList<>(hits.subList(0, max)) : hits;
    }

    private static synchronized void ensureMdcIndex() {
        long now = System.currentTimeMillis();
        if (!cachedFilms.isEmpty() && !cachedDevelopers.isEmpty() && now - indexLoadedAt < INDEX_TTL_MS) return;
        try {
            String html = "";
            for (String indexUrl : MDC_INDEXES) {
                try {
                    html = fetch(indexUrl, 1400000);
                    if (html != null && !html.isEmpty()) break;
                } catch (Exception ignored) {
                    html = "";
                }
            }
            if (html == null || html.isEmpty()) throw new IllegalStateException("MDC index unavailable");
            List<IndexItem> films = new ArrayList<>();
            List<IndexItem> devs = new ArrayList<>();
            Matcher a = Pattern.compile("(?is)<a[^>]+href=[\\\"']([^\\\"']+)[\\\"'][^>]*>(.*?)</a>").matcher(html);
            Set<String> seenFilms = new LinkedHashSet<>();
            Set<String> seenDevs = new LinkedHashSet<>();
            while (a.find()) {
                String href = decodeEntities(a.group(1));
                String title = clean(a.group(2));
                if (title.length() < 2) continue;
                boolean isDev = href.contains("Developer=") || href.contains("developer=");
                boolean isFilm = href.contains("Film=") || href.contains("film=");
                if (!isDev && !isFilm) continue;
                String abs = absoluteDigitaltruth(href);
                if (isDev && seenDevs.add(norm(title))) devs.add(new IndexItem(title, abs, true));
                if (isFilm && seenFilms.add(norm(title))) films.add(new IndexItem(title, abs, false));
            }
            if (!films.isEmpty()) cachedFilms = films;
            if (!devs.isEmpty()) cachedDevelopers = devs;
            if (!films.isEmpty() || !devs.isEmpty()) indexLoadedAt = now;
        } catch (Exception ignored) {
            // Mantieni l'ultima cache valida, se disponibile.
        }
    }

    private static int mdcMatchScore(String q, String name) {
        if (q == null || q.length() < 3 || name == null) return 0;
        if (name.equals(q)) return 1000;
        if (name.startsWith(q)) return 950;
        for (String token : name.split(" ")) if (token.startsWith(q)) return 900;
        if (name.contains(" " + q)) return 850;
        if (name.contains(q)) return 760;
        Set<String> qt = tokens(q);
        if (!qt.isEmpty()) {
            boolean all = true;
            for (String t : qt) {
                boolean hit = name.contains(t);
                if (!hit) { all = false; break; }
            }
            if (all) return 700;
        }
        return 0;
    }

    private static List<String> extractMdcDeveloperDilutions(String url) {
        LinkedHashSet<String> out = new LinkedHashSet<>();
        try {
            String html = fetch(url, 1200000);
            Matcher row = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
            while (row.find() && out.size() < 16) {
                List<String> c = cells(row.group(1));
                if (c.size() < 3) continue;
                String d = normalizeDilution(c.get(2));
                if (d != null) out.add(d);
            }
        } catch (Exception ignored) {}
        return new ArrayList<>(out);
    }

    // ---------------------------------------------------------------------
    // Manufacturer discovery
    // ---------------------------------------------------------------------

    private static List<OnlineCatalogSearch.SearchResult> officialSearch(String query, boolean chemical, int max) {
        LinkedHashMap<String, OnlineCatalogSearch.SearchResult> out = new LinkedHashMap<>();
        Brand b = brandForQuery(query);

        if (b != null) {
            for (String domain : b.domains) {
                for (OnlineCatalogSearch.SearchResult r : sitemapSearch(domain, query, chemical, max)) put(out, r);
                if (out.size() >= max) break;
            }
            if (out.size() < max) {
                for (String domain : b.domains) {
                    String suffix = chemical ? " photographic chemistry developer fixer stop bath" : " photographic film ISO";
                    for (OnlineCatalogSearch.SearchResult r : webSearch("site:" + domain + " \"" + query + "\"" + suffix)) {
                        if (isManufacturerUrl(r.url)) put(out, r);
                        if (out.size() >= max) break;
                    }
                    if (out.size() >= max) break;
                }
            }
        } else {
            // Nome/marca mai visti prima: ricerca aperta. Non richiede aggiornare l'app.
            String suffix = chemical
                    ? " photographic chemistry developer fixer stop bath darkroom"
                    : " photographic film ISO black white 35mm 120";
            for (OnlineCatalogSearch.SearchResult r : webSearch("\"" + query + "\"" + suffix)) {
                if (looksLikeTechnicalProductResult(query, r, chemical)) put(out, r);
                if (out.size() >= max) break;
            }
        }
        return new ArrayList<>(out.values());
    }

    private static List<OnlineCatalogSearch.SearchResult> sitemapSearch(String domain, String query, boolean chemical, int max) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        String[] roots = new String[]{
                "https://" + domain + "/wp-sitemap.xml",
                "https://" + domain + "/sitemap_index.xml",
                "https://" + domain + "/sitemap.xml"
        };
        LinkedHashSet<String> locations = new LinkedHashSet<>();
        for (String root : roots) {
            try {
                String xml = fetch(root, 700000);
                List<String> loc = xmlLocations(xml);
                if (loc.isEmpty()) continue;
                int childCount = 0;
                for (String u : loc) {
                    if (u.toLowerCase(Locale.ROOT).endsWith(".xml")) {
                        if (childCount++ >= 8) break;
                        try { locations.addAll(xmlLocations(fetch(u, 700000))); } catch (Exception ignored) {}
                    } else {
                        locations.add(u);
                    }
                }
                if (!locations.isEmpty()) break;
            } catch (Exception ignored) {}
        }

        String q = norm(query);
        for (String u : locations) {
            if (out.size() >= max) break;
            String decoded = decodeUrl(u);
            String slug = titleFromUrl(decoded);
            int score = productMatchScore(q, norm(slug + " " + decoded));
            boolean brandOnly = brandForQuery(query) != null && q.length() <= 9;
            if (score < 500 && !brandOnly) continue;
            if (!looksProductUrl(decoded)) continue;
            String snippet = "Fonte produttore · pagina prodotto";
            out.add(new OnlineCatalogSearch.SearchResult(slug, decoded, snippet));
        }
        return out;
    }

    private static boolean looksLikeTechnicalProductResult(String query, OnlineCatalogSearch.SearchResult r, boolean chemical) {
        String all = norm(r.title + " " + r.snippet + " " + r.url);
        if (productMatchScore(norm(query), all) <= 0) return false;
        if (chemical) {
            return containsAny(all, "developer","rivelatore","fixer","fixing","stop bath","chemistry","darkroom","photo chemical","safety data","data sheet");
        }
        return containsAny(all, "film","pellicola","35mm","35 mm","120","iso","asa","datasheet","data sheet");
    }

    private static boolean looksProductUrl(String u) {
        String n = norm(u);
        return containsAny(n, "/product/", "/products/", "/prodotto/", "/produkt/", "/chem", "/film", "/datasheet", "/download")
                || !n.endsWith(" xml");
    }

    // ---------------------------------------------------------------------
    // Strict type/data extraction
    // ---------------------------------------------------------------------

    private static boolean isMdcDeveloper(OnlineCatalogSearch.SearchResult r) {
        String x = (r.url + " " + r.snippet).toLowerCase(Locale.ROOT);
        return x.contains("digitaltruth.com") && (x.contains("developer=") || x.contains("film_developer"));
    }

    private static boolean isMdcFilm(OnlineCatalogSearch.SearchResult r) {
        String x = (r.url + " " + r.snippet).toLowerCase(Locale.ROOT);
        return x.contains("digitaltruth.com") && (x.contains("film=") || x.contains("· film ·"));
    }

    private static int strictRole(String evidence) {
        String s = norm(evidence);
        // Le parole devono essere esplicite. Nessuna deduzione da un generico "fix" nella pagina.
        if (containsAny(s, "stop bath", "bagno d arresto", "bagno arresto", "arresto fotografico", "stoppbad"))
            return OnlineCatalogSearch.ROLE_STOP;
        if (containsAny(s, "film fixer", "paper fixer", "universal fixer", "photographic fixer", "fixing bath", "fissaggio fotografico", "bagno di fissaggio"))
            return OnlineCatalogSearch.ROLE_FIX;

        int role = 0;
        if (containsAny(s, "film developer", "negative developer", "developer for film", "sviluppo pellicola", "rivelatore pellicola", "entwickler film"))
            role |= OnlineCatalogSearch.ROLE_FILM_DEV;
        if (containsAny(s, "paper developer", "print developer", "developer for paper", "sviluppo carta", "rivelatore carta", "papierentwickler"))
            role |= OnlineCatalogSearch.ROLE_PAPER_DEV;
        if (containsAny(s, "universal developer", "rivelatore universale") && containsAny(s, "film", "pellicola"))
            role |= OnlineCatalogSearch.ROLE_FILM_DEV;
        if (containsAny(s, "universal developer", "rivelatore universale") && containsAny(s, "paper", "carta"))
            role |= OnlineCatalogSearch.ROLE_PAPER_DEV;
        return role;
    }

    private static boolean explicitPaperDeveloper(String s) {
        String n = norm(s);
        return containsAny(n, "paper developer", "print developer", "sviluppo carta", "rivelatore carta", "papierentwickler", "universal developer");
    }

    private static List<String> extractDilutionsStrict(String text) {
        LinkedHashSet<String> out = new LinkedHashSet<>();
        if (text == null) return new ArrayList<>(out);
        Matcher m = Pattern.compile("(?i)\\b(1\\s*[+:]\\s*\\d{1,3})\\b").matcher(text);
        while (m.find() && out.size() < 12) {
            int from = Math.max(0, m.start() - 180);
            int to = Math.min(text.length(), m.end() + 180);
            String ctx = norm(text.substring(from, to));
            if (!containsAny(ctx, "dilut", "working solution", "developer", "rivelatore", "fixer", "stop bath", "mix", "miscel", "concentrate")) continue;
            out.add(m.group(1).replace(" ", "").replace(':', '+'));
        }
        return new ArrayList<>(out);
    }

    private static String normalizeDilution(String raw) {
        if (raw == null) return null;
        String s = clean(raw).toLowerCase(Locale.ROOT).replace(" ", "").replace(':', '+');
        if (s.equals("stock")) return "stock";
        if (s.matches("1\\+\\d{1,3}")) return s;
        if (s.matches("\\d+\\+\\d+\\+\\d+")) return s;
        return null;
    }

    private static boolean explicitStockPreparation(String text) {
        String s = norm(text);
        return containsAny(s, "powder", "polvere", "pulver", "dissolve", "sciogli", "stock solution", "soluzione stock")
                && containsAny(s, "water", "acqua", "litre", "liter", "litro", "ml");
    }

    private static String extractInstruction(String text) {
        if (text == null || text.isEmpty()) return null;
        String flat = text.replaceAll("\\s+", " ").trim();
        String n = norm(flat);
        String[] keys = {"preparation", "preparazione", "stock solution", "soluzione stock", "dissolve", "sciogli", "mixing instructions"};
        int best = -1;
        for (String k : keys) {
            int i = n.indexOf(norm(k));
            if (i >= 0 && (best < 0 || i < best)) best = i;
        }
        if (best < 0) return null;
        int from = Math.max(0, best - 150);
        int to = Math.min(flat.length(), best + 900);
        String chunk = flat.substring(from, to).trim();
        return chunk.length() > 750 ? chunk.substring(0, 750) + "…" : chunk;
    }

    private static int extractExpiryDays(String text) {
        if (text == null) return -1;
        Matcher m = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,80}(\\d{1,2})\\s*(months?|mesi)").matcher(text);
        if (m.find()) try { return Integer.parseInt(m.group(1)) * 30; } catch (Exception ignored) {}
        m = Pattern.compile("(?i)(?:shelf life|storage life|durata|conservazione)[^0-9]{0,80}(\\d{1,2})\\s*(years?|anni)").matcher(text);
        if (m.find()) try { return Integer.parseInt(m.group(1)) * 365; } catch (Exception ignored) {}
        return -1;
    }

    private static int extractExplicitIso(String text) {
        if (text == null) return 0;
        Matcher m = Pattern.compile("(?i)\\b(?:ISO|ASA)\\s*[:=]?\\s*(25|32|40|50|64|80|100|125|160|200|250|320|400|500|640|800|1000|1250|1600|3200)\\b").matcher(text);
        if (m.find()) try { return Integer.parseInt(m.group(1)); } catch (Exception ignored) {}
        return 0;
    }

    private static int nominalIsoFromName(String title) {
        String t = title == null ? "" : title;
        Matcher m = Pattern.compile("(?<!\\d)(25|32|40|50|64|80|100|125|160|200|250|320|400|500|640|800|1000|1250|1600|3200)(?!\\d)").matcher(t);
        int best = 0;
        while (m.find()) {
            try {
                int v = Integer.parseInt(m.group(1));
                if (best == 0 || (v >= 50 && v <= 3200)) best = v;
            } catch (Exception ignored) {}
        }
        return best;
    }

    private static String extractFormat(String text) {
        String s = norm(text);
        boolean f35 = containsAny(s, "35mm", "35 mm", "135 film", "135 format");
        boolean f120 = Pattern.compile("(?<!\\d)120(?!\\d)").matcher(s).find();
        if (f35 && !f120) return "35";
        if (f120 && !f35) return "120";
        return null;
    }

    // ---------------------------------------------------------------------
    // Search/fetch helpers
    // ---------------------------------------------------------------------

    private static Brand brandForQuery(String query) {
        String q = norm(query);
        Brand best = null;
        int score = 0;
        for (Brand b : BRANDS) {
            for (String alias : b.aliases) {
                String a = norm(alias);
                if (q.contains(a) || a.startsWith(q) || q.startsWith(a)) {
                    int s = Math.min(q.length(), a.length());
                    if (s > score) { score = s; best = b; }
                }
            }
        }
        return score >= 3 ? best : null;
    }

    private static List<OnlineCatalogSearch.SearchResult> webSearch(String query) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        try {
            String u = "https://www.bing.com/search?format=rss&setlang=en&q=" + URLEncoder.encode(query, "UTF-8");
            String xml = fetch(u, 550000);
            Matcher m = Pattern.compile("(?is)<item>(.*?)</item>").matcher(xml);
            while (m.find() && out.size() < 20) {
                String block = m.group(1);
                String title = tag(block, "title");
                String link = tag(block, "link");
                String desc = tag(block, "description");
                if (http(link) && title.length() > 2) out.add(new OnlineCatalogSearch.SearchResult(title, link, desc));
            }
        } catch (Exception ignored) {}
        if (out.size() < 5) {
            try {
                String u = "https://lite.duckduckgo.com/lite/?q=" + URLEncoder.encode(query, "UTF-8");
                String html = fetch(u, 450000);
                Matcher m = Pattern.compile("(?is)<a[^>]+href=[\\\"']([^\\\"']+)[\\\"'][^>]*>(.*?)</a>").matcher(html);
                while (m.find() && out.size() < 20) {
                    String href = decodeDuck(m.group(1));
                    String title = clean(m.group(2));
                    if (http(href) && title.length() > 2 && !href.contains("duckduckgo.com"))
                        out.add(new OnlineCatalogSearch.SearchResult(title, href, ""));
                }
            } catch (Exception ignored) {}
        }
        return out;
    }

    private static int productMatchScore(String q, String text) {
        if (q == null || q.length() < 3 || text == null) return 0;
        if (text.equals(q)) return 1000;
        if (text.startsWith(q)) return 900;
        for (String t : text.split(" ")) if (t.startsWith(q)) return 850;
        if (text.contains(q)) return 700;
        Set<String> qt = tokens(q);
        if (!qt.isEmpty()) {
            boolean all = true;
            for (String t : qt) if (!text.contains(t)) { all = false; break; }
            if (all) return 650;
        }
        return 0;
    }

    private static List<String> xmlLocations(String xml) {
        List<String> out = new ArrayList<>();
        if (xml == null) return out;
        Matcher m = Pattern.compile("(?is)<loc>\\s*(.*?)\\s*</loc>").matcher(xml);
        while (m.find() && out.size() < 5000) out.add(decodeEntities(clean(m.group(1))));
        return out;
    }

    private static String titleFromUrl(String u) {
        if (u == null) return "";
        String s = u;
        int q = s.indexOf('?'); if (q >= 0) s = s.substring(0, q);
        while (s.endsWith("/")) s = s.substring(0, s.length()-1);
        int slash = s.lastIndexOf('/');
        if (slash >= 0) s = s.substring(slash + 1);
        try { s = URLDecoder.decode(s, "UTF-8"); } catch (Exception ignored) {}
        s = s.replace('-', ' ').replace('_', ' ').replaceAll("\\s+", " ").trim();
        if (s.isEmpty()) return "Prodotto";
        StringBuilder b = new StringBuilder();
        for (String w : s.split(" ")) {
            if (w.isEmpty()) continue;
            if (b.length() > 0) b.append(' ');
            b.append(Character.toUpperCase(w.charAt(0))).append(w.substring(1));
        }
        return b.toString();
    }

    private static List<String> cells(String row) {
        List<String> out = new ArrayList<>();
        Matcher m = Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>").matcher(row);
        while (m.find()) out.add(clean(m.group(1)));
        return out;
    }

    private static String absoluteDigitaltruth(String href) {
        if (href.startsWith("http://") || href.startsWith("https://")) return href;
        if (href.startsWith("/")) return "https://www.digitaltruth.com" + href;
        return "https://www.digitaltruth.com/chart/" + href;
    }

    private static String decodeUrl(String u) {
        try { return URLDecoder.decode(u, "UTF-8"); } catch (Exception ignored) { return u; }
    }

    private static String tag(String block, String tag) {
        Matcher m = Pattern.compile("(?is)<" + tag + ">(?:<!\\[CDATA\\[)?(.*?)(?:]]>)?</" + tag + ">").matcher(block);
        return m.find() ? clean(m.group(1)) : "";
    }

    private static String decodeDuck(String href) {
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

    private static void put(LinkedHashMap<String, OnlineCatalogSearch.SearchResult> map, OnlineCatalogSearch.SearchResult r) {
        if (r == null || r.title == null || r.title.trim().length() < 2) return;
        String key = norm(r.title) + "|" + norm(r.url);
        if (!map.containsKey(key)) map.put(key, r);
    }

    private static Set<String> tokens(String s) {
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (String t : norm(s).split(" ")) if (t.length() >= 2) out.add(t);
        return out;
    }

    private static String cleanProductTitle(String s) {
        String t = clean(s);
        t = t.replaceAll("(?i)\\s*[|–—]\\s*(official.*|data sheet.*|datasheet.*)$", "").trim();
        return t.length() > 120 ? t.substring(0, 120).trim() : t;
    }

    private static String first(String s, int n) {
        if (s == null) return "";
        return s.length() > n ? s.substring(0, n) : s;
    }

    private static String norm(String s) {
        return clean(s).toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9à-ÿ+./]+", " ")
                .replaceAll("\\s+", " ").trim();
    }

    private static String clean(String s) {
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

    private static boolean containsAny(String s, String... terms) {
        if (s == null) return false;
        for (String t : terms) if (s.contains(t)) return true;
        return false;
    }

    private static boolean http(String s) {
        return s != null && (s.startsWith("https://") || s.startsWith("http://"));
    }

    private static String fetch(String urlString, int maxChars) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(urlString).openConnection();
        c.setConnectTimeout(9000);
        c.setReadTimeout(13000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36");
        c.setRequestProperty("Referer", "https://www.digitaltruth.com/");
        c.setRequestProperty("Accept", "text/html,application/xhtml+xml,application/xml,text/xml,*/*;q=0.5");
        c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
        c.setRequestProperty("Accept-Encoding", "identity");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        InputStream in = c.getInputStream();
        BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        char[] buf = new char[4096];
        int n;
        while ((n = br.read(buf)) > 0 && sb.length() < maxChars) sb.append(buf, 0, n);
        br.close();
        return sb.toString();
    }

    private SourceBroker() {}
}
