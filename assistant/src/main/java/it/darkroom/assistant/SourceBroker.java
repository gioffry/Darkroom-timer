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
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Broker delle fonti. Non contiene un catalogo di singoli prodotti: risolve marca,
 * fonte ufficiale e indici tecnici (Massive Dev Chart) in modo generale.
 */
final class SourceBroker {
    private static final class Brand {
        final String name;
        final String[] aliases;
        final String[] domains;
        Brand(String name, String[] aliases, String[] domains) {
            this.name = name; this.aliases = aliases; this.domains = domains;
        }
    }

    private static final Brand[] BRANDS = new Brand[]{
            new Brand("Ilford/Harman", new String[]{"ilford","harman","kentmere"}, new String[]{"ilfordphoto.com","harmantechnology.com"}),
            new Brand("Foma", new String[]{"foma","fomapan","fomadon","fomafix","fomaspeed"}, new String[]{"foma.cz"}),
            new Brand("Adox", new String[]{"adox","rodinal","adonal","fx-39","fx39","adoxal"}, new String[]{"adox.de","fotoimpex.com"}),
            new Brand("Kodak", new String[]{"kodak","d-76","d76","xtol","hc-110","hc110","t-max","tmax","tri-x","trix"}, new String[]{"kodak.com","kodakalaris.com"}),
            new Brand("Rollei", new String[]{"rollei","supergrain","rpx","retro","superpan","low contrast","low speed","high contrast","print neutral","print warmtone"}, new String[]{"rolleianalog.com"}),
            new Brand("Bellini", new String[]{"bellini","bell","hydrofen","ecofilm","euro hc","nucleol","gradual","bwdek","f205","fx100","aminophenol"}, new String[]{"bellinifoto.it"}),
            new Brand("Fujifilm", new String[]{"fuji","fujifilm","neopan","acros"}, new String[]{"fujifilm.com"}),
            new Brand("Ferrania", new String[]{"ferrania","p30","orto"}, new String[]{"filmferrania.com"}),
            new Brand("Bergger", new String[]{"bergger","pancro","ber49"}, new String[]{"bergger.com"}),
            new Brand("CineStill", new String[]{"cinestill","df96","d96"}, new String[]{"cinestillfilm.com"}),
            new Brand("LegacyPro", new String[]{"legacypro","legacy pro"}, new String[]{"freestylephoto.com"})
    };

    static List<OnlineCatalogSearch.SearchResult> searchChemicals(String query) {
        LinkedHashMap<String, OnlineCatalogSearch.SearchResult> out = new LinkedHashMap<>();
        for (OnlineCatalogSearch.SearchResult r : digitalTruthDevelopers(query)) put(out, r);
        for (OnlineCatalogSearch.SearchResult r : officialSearch(query, true)) put(out, r);
        return new ArrayList<>(out.values());
    }

    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query) {
        LinkedHashMap<String, OnlineCatalogSearch.SearchResult> out = new LinkedHashMap<>();
        for (OnlineCatalogSearch.SearchResult r : digitalTruthFilms(query)) put(out, r);
        for (OnlineCatalogSearch.SearchResult r : officialSearch(query, false)) put(out, r);
        return new ArrayList<>(out.values());
    }

    static boolean isManufacturerUrl(String url) {
        String u = norm(url);
        for (Brand b : BRANDS) for (String d : b.domains) if (u.contains(norm(d))) return true;
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
        List<OnlineCatalogSearch.SearchResult> candidates = officialSearch(productName, chemical);
        String pn = norm(productName);
        OnlineCatalogSearch.SearchResult best = null;
        double bestScore = 0;
        for (OnlineCatalogSearch.SearchResult r : candidates) {
            if (!isManufacturerUrl(r.url)) continue;
            double score = similarity(pn, norm(r.title));
            if (score > bestScore) { bestScore = score; best = r; }
        }
        return best != null && bestScore >= 0.34 ? best.url : initialUrl;
    }

    static OnlineCatalogSearch.ChemicalData enrichChemical(OnlineCatalogSearch.SearchResult r) {
        if (r == null) return null;
        String official = resolveOfficialUrl(r.title, true, r.url);
        String text = "";
        try { text = SourceText.fetchText(official, 700000); } catch (Exception ignored) {}
        if (text.isEmpty() && r.url != null && !r.url.equals(official)) {
            try { text = SourceText.fetchText(r.url, 700000); } catch (Exception ignored) {}
        }
        String all = r.title + " " + r.snippet + " " + text;
        int roles = inferRoles(all);
        List<String> dilutions = extractDilutions(all);
        boolean stock = containsAny(norm(all), "powder", "polvere", "stock solution", "soluzione stock", "dissolve", "sciogli");
        String instructions = stock ? extractInstruction(all) : null;
        int expiry = extractExpiryDays(all);
        String[] film = (roles & OnlineCatalogSearch.ROLE_FILM_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String[] paper = (roles & OnlineCatalogSearch.ROLE_PAPER_DEV) != 0 ? dilutions.toArray(new String[0]) : new String[0];
        String working = ((roles & (OnlineCatalogSearch.ROLE_STOP | OnlineCatalogSearch.ROLE_FIX)) != 0 && !dilutions.isEmpty()) ? dilutions.get(0) : null;
        if (roles == 0 && dilutions.isEmpty() && text.isEmpty()) return null;
        return new OnlineCatalogSearch.ChemicalData(cleanProductTitle(r.title), roles, stock, film, paper,
                working, instructions, expiry, official == null ? "" : official);
    }

    static OnlineCatalogSearch.FilmData enrichFilm(OnlineCatalogSearch.SearchResult r) {
        if (r == null) return null;
        String official = resolveOfficialUrl(r.title, false, r.url);
        String text = "";
        try { text = SourceText.fetchText(official, 500000); } catch (Exception ignored) {}
        String all = r.title + " " + r.snippet + " " + text;
        int iso = extractIso(all);
        String format = extractFormat(all);
        if (iso <= 0) iso = isoFromSnippet(r.snippet);
        if (iso <= 0 && text.isEmpty()) return null;
        return new OnlineCatalogSearch.FilmData(cleanProductTitle(r.title), iso, format,
                official == null ? "" : official);
    }

    private static List<OnlineCatalogSearch.SearchResult> officialSearch(String query, boolean chemical) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        Brand b = brandForQuery(query);
        List<String> domains = new ArrayList<>();
        if (b != null) {
            for (String d : b.domains) domains.add(d);
        } else {
            for (Brand x : BRANDS) for (String d : x.domains) domains.add(d);
        }
        // Per marca nota: query mirata. Per prodotto senza marca: due cluster per non fare troppe richieste.
        if (b != null) {
            for (String d : domains) {
                out.addAll(webSearch("site:" + d + " \"" + query + "\" " + (chemical ? "developer fixer stop photographic chemistry" : "film ISO 35mm 120")));
                if (out.size() >= 14) break;
            }
        } else {
            StringBuilder c1 = new StringBuilder(), c2 = new StringBuilder();
            for (int i = 0; i < domains.size(); i++) {
                String clause = "site:" + domains.get(i);
                if (i < domains.size()/2) { if (c1.length()>0) c1.append(" OR "); c1.append(clause); }
                else { if (c2.length()>0) c2.append(" OR "); c2.append(clause); }
            }
            String suffix = chemical ? " photographic developer chemistry" : " photographic film ISO";
            out.addAll(webSearch("\"" + query + "\" (" + c1 + ")" + suffix));
            if (out.size() < 8) out.addAll(webSearch("\"" + query + "\" (" + c2 + ")" + suffix));
        }
        List<OnlineCatalogSearch.SearchResult> filtered = new ArrayList<>();
        for (OnlineCatalogSearch.SearchResult r : out) {
            if (!isManufacturerUrl(r.url)) continue;
            if (!overlap(query, r.title + " " + r.url + " " + r.snippet) && !matchesQueryDomain(query, r.url)) continue;
            filtered.add(r);
            if (filtered.size() >= 14) break;
        }
        return filtered;
    }

    private static List<OnlineCatalogSearch.SearchResult> digitalTruthDevelopers(String query) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        try {
            String url = "https://www.digitaltruth.com/chart/search_text.php?Developer=" + URLEncoder.encode(query, "UTF-8");
            String html = fetch(url, 900000);
            Matcher row = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
            Set<String> names = new LinkedHashSet<>();
            while (row.find() && names.size() < 18) {
                List<String> cells = cells(row.group(1));
                if (cells.size() < 2) continue;
                String dev = clean(cells.get(1));
                if (dev.length() < 3 || dev.toLowerCase(Locale.ROOT).contains("developer")) continue;
                if (!prefixOrOverlap(query, dev)) continue;
                names.add(dev);
            }
            for (String n : names) out.add(new OnlineCatalogSearch.SearchResult(n, url,
                    "Massive Dev Chart · developer index · technical combination data"));
        } catch (Exception ignored) {}
        return out;
    }

    private static List<OnlineCatalogSearch.SearchResult> digitalTruthFilms(String query) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        try {
            String url = "https://www.digitaltruth.com/devchart.php?Film=" + URLEncoder.encode(query, "UTF-8") + "&TempUnits=C&TimeUnits=T&mdc=Search";
            String html = fetch(url, 1100000);
            Matcher row = Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
            Map<String,Integer> films = new LinkedHashMap<>();
            while (row.find() && films.size() < 20) {
                List<String> cells = cells(row.group(1));
                if (cells.size() < 4) continue;
                String film = clean(cells.get(0));
                if (film.length() < 3 || film.toLowerCase(Locale.ROOT).contains("film")) continue;
                if (!prefixOrOverlap(query, film)) continue;
                int iso = parseInt(cells.get(3));
                if (!films.containsKey(film)) films.put(film, iso);
            }
            for (Map.Entry<String,Integer> e : films.entrySet()) {
                String sn = "Massive Dev Chart · film index" + (e.getValue()>0 ? " · ISO " + e.getValue() : "");
                out.add(new OnlineCatalogSearch.SearchResult(e.getKey(), url, sn));
            }
        } catch (Exception ignored) {}
        return out;
    }

    private static List<OnlineCatalogSearch.SearchResult> webSearch(String query) {
        List<OnlineCatalogSearch.SearchResult> out = new ArrayList<>();
        try {
            String u = "https://www.bing.com/search?format=rss&setlang=en&q=" + URLEncoder.encode(query, "UTF-8");
            String xml = fetch(u, 500000);
            Matcher m = Pattern.compile("(?is)<item>(.*?)</item>").matcher(xml);
            while (m.find() && out.size() < 20) {
                String item = m.group(1);
                String title = tag(item, "title"), link = tag(item, "link"), desc = tag(item, "description");
                if (http(link) && title.length()>2) out.add(new OnlineCatalogSearch.SearchResult(title, link, desc));
            }
        } catch (Exception ignored) {}
        if (out.size() < 5) {
            try {
                String u = "https://lite.duckduckgo.com/lite/?q=" + URLEncoder.encode(query, "UTF-8");
                String html = fetch(u, 450000);
                Matcher m = Pattern.compile("(?is)<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>").matcher(html);
                while (m.find() && out.size() < 20) {
                    String href = decodeDuck(m.group(1)), title = clean(m.group(2));
                    if (http(href) && title.length()>2 && !href.contains("duckduckgo.com"))
                        out.add(new OnlineCatalogSearch.SearchResult(title, href, ""));
                }
            } catch (Exception ignored) {}
        }
        return out;
    }

    private static Brand brandForQuery(String query) {
        String q = norm(query);
        Brand best = null; int score = 0;
        for (Brand b : BRANDS) for (String a : b.aliases) {
            String n = norm(a);
            boolean hit = q.contains(n) || n.startsWith(q) || q.startsWith(n);
            if (hit) {
                int s = Math.min(q.length(), n.length());
                if (s > score) { score = s; best = b; }
            }
        }
        return score >= 3 ? best : null;
    }

    private static int inferRoles(String text) {
        String s = norm(text);
        if (containsAny(s,"stop bath","arresto","ecostop","indexstop")) return OnlineCatalogSearch.ROLE_STOP;
        if (containsAny(s,"fixer","fixing bath","fissaggio","fomafix","fix acid","fix neutral")) return OnlineCatalogSearch.ROLE_FIX;
        int r = 0;
        if (containsAny(s,"film developer","negative developer","sviluppo pellicola","rivelatore pellicola","black white film developer")) r |= OnlineCatalogSearch.ROLE_FILM_DEV;
        if (containsAny(s,"paper developer","print developer","sviluppo carta","rivelatore carta","photographic paper developer")) r |= OnlineCatalogSearch.ROLE_PAPER_DEV;
        if (r == 0 && containsAny(s,"developer","rivelatore","entwickler")) {
            if (containsAny(s,"film","negative","pellicola")) r |= OnlineCatalogSearch.ROLE_FILM_DEV;
            if (containsAny(s,"paper","print","carta")) r |= OnlineCatalogSearch.ROLE_PAPER_DEV;
        }
        return r;
    }

    private static List<String> extractDilutions(String text) {
        LinkedHashSet<String> out = new LinkedHashSet<>();
        Matcher m = Pattern.compile("(?i)\\b1\\s*[+:]\\s*(\\d{1,3})\\b").matcher(text == null ? "" : text);
        while (m.find() && out.size()<12) {
            int from=Math.max(0,m.start()-240), to=Math.min(text.length(),m.end()+240);
            String ctx=norm(text.substring(from,to));
            if (containsAny(ctx,"dilut","working solution","developer","rivelatore","fixer","stop bath","mix","concentrate","concentrato"))
                out.add("1+"+m.group(1));
        }
        return new ArrayList<>(out);
    }

    private static String extractInstruction(String text) {
        String flat=(text==null?"":text).replaceAll("\\s+"," ").trim();
        String low=norm(flat); int best=-1;
        String[] keys={"stock solution","mixing instructions","dissolve","preparation","prepare stock","soluzione stock","sciogli","polvere"};
        for(String k:keys){int i=low.indexOf(k);if(i>=0&&(best<0||i<best))best=i;}
        if(best<0)return null;
        String chunk=flat.substring(Math.max(0,best-220),Math.min(flat.length(),best+1000));
        return Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c)").matcher(chunk).find()?chunk:null;
    }

    private static int extractExpiryDays(String text) {
        if(text==null)return -1;
        Matcher m=Pattern.compile("(?i)(?:shelf life|storage life|conservazione|durata)[^0-9]{0,80}(\\d{1,2})\\s*(months?|mesi)").matcher(text);
        if(m.find())return parseInt(m.group(1))*30;
        Matcher y=Pattern.compile("(?i)(?:shelf life|storage life|conservazione|durata)[^0-9]{0,80}(\\d{1,2})\\s*(years?|anni)").matcher(text);
        if(y.find())return parseInt(y.group(1))*365;
        return -1;
    }

    private static int extractIso(String text) {
        Matcher m=Pattern.compile("(?i)\\b(?:ISO|ASA|EI)\\s*[:=]?\\s*(\\d{2,4})\\b").matcher(text==null?"":text);
        return m.find()?parseInt(m.group(1)):0;
    }
    private static int isoFromSnippet(String s){return extractIso(s);}
    private static String extractFormat(String text){String s=norm(text);boolean a=s.contains("35mm")||s.contains("35 mm")||s.contains("135 format")||s.contains("135 film");boolean b=Pattern.compile("(?:^| )120(?: |$)").matcher(s).find();if(a&&!b)return"35";if(b&&!a)return"120";return null;}

    private static boolean overlap(String q,String t){Set<String> a=tokens(q);if(a.isEmpty())return false;String n=norm(t);int h=0;for(String x:a)if(n.contains(x))h++;return h>=Math.max(1,(int)Math.ceil(a.size()*0.5));}
    private static boolean prefixOrOverlap(String q,String t){String nq=norm(q),nt=norm(t);if(nq.length()>=3&&(nt.contains(nq)||nt.startsWith(nq)))return true;for(String x:nt.split(" "))if(x.startsWith(nq)&&nq.length()>=3)return true;return overlap(q,t);}
    private static double similarity(String a,String b){Set<String>x=tokens(a),y=tokens(b);if(x.isEmpty()||y.isEmpty())return 0;int h=0;for(String t:x)for(String z:y)if(t.equals(z)||t.startsWith(z)||z.startsWith(t)){h++;break;}return h/(double)Math.max(x.size(),y.size());}
    private static Set<String> tokens(String s){LinkedHashSet<String>o=new LinkedHashSet<>();for(String t:norm(s).split(" "))if(t.length()>=3&&!containsAny(t,"the","and","film","photo","photographic","developer","official","data","sheet"))o.add(t);return o;}
    private static void put(Map<String,OnlineCatalogSearch.SearchResult> m,OnlineCatalogSearch.SearchResult r){if(r==null)return;String k=norm(r.title);if(!m.containsKey(k))m.put(k,r);}
    private static List<String> cells(String row){List<String>o=new ArrayList<>();Matcher m=Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>").matcher(row);while(m.find())o.add(clean(m.group(1)));return o;}
    private static String tag(String block,String tag){Matcher m=Pattern.compile("(?is)<"+tag+">(?:<!\\[CDATA\\[)?(.*?)(?:]]>)?</"+tag+">").matcher(block);return m.find()?clean(m.group(1)):"";}
    private static String cleanProductTitle(String s){String t=clean(s);t=t.replaceAll("(?i)\\s*[|–—]\\s*(official|data sheet|datasheet|downloads?).*$","").trim();return t.length()>120?t.substring(0,120):t;}
    private static String clean(String s){if(s==null)return"";return s.replaceAll("(?is)<script.*?</script>"," ").replaceAll("(?is)<style.*?</style>"," ").replaceAll("(?s)<[^>]+>"," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&nbsp;"," ").replaceAll("\\s+"," ").trim();}
    private static String norm(String s){return clean(s).toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9à-ÿ+.-]+"," ").replaceAll("\\s+"," ").trim();}
    private static boolean containsAny(String s,String...x){if(s==null)return false;for(String a:x)if(s.contains(a))return true;return false;}
    private static int parseInt(String s){try{return Integer.parseInt((s==null?"":s).replaceAll("[^0-9]",""));}catch(Exception e){return 0;}}
    private static boolean http(String s){return s!=null&&(s.startsWith("http://")||s.startsWith("https://"));}
    private static String decodeDuck(String h){try{h=h.replace("&amp;","&");int i=h.indexOf("uddg=");if(i>=0){String v=h.substring(i+5);int a=v.indexOf('&');if(a>=0)v=v.substring(0,a);return URLDecoder.decode(v,"UTF-8");}if(h.startsWith("//"))return"https:"+h;}catch(Exception ignored){}return h;}
    private static String fetch(String u,int max)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(8000);c.setReadTimeout(10000);c.setInstanceFollowRedirects(true);c.setRequestProperty("User-Agent","Mozilla/5.0 (Android) DarkroomAssistant/0.2.0");c.setRequestProperty("Accept-Encoding","identity");int code=c.getResponseCode();if(code<200||code>=400)throw new IllegalStateException("HTTP "+code);InputStream in=c.getInputStream();BufferedReader br=new BufferedReader(new InputStreamReader(in));StringBuilder sb=new StringBuilder();char[]buf=new char[4096];int n;while((n=br.read(buf))>0&&sb.length()<max)sb.append(buf,0,n);br.close();return sb.toString();}
    private SourceBroker(){}
}
