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

/** Recupera dati tecnici solo da pagine che corrispondono davvero al prodotto. */
final class ChemistrySpecEngine {
    static final int REUSE_UNKNOWN = 0;
    static final int REUSE_ONE_SHOT = 1;
    static final int REUSE_REUSABLE = 2;

    static final class Spec {
        final String stockInstructions; final int reuseMode;
        final double filmCapacityPerLiter; final double paperCapacitySqMPerLiter;
        final String sourceUrl;
        Spec(String stockInstructions, int reuseMode, double filmCapacityPerLiter,
             double paperCapacitySqMPerLiter, String sourceUrl) {
            this.stockInstructions = stockInstructions; this.reuseMode = reuseMode;
            this.filmCapacityPerLiter = filmCapacityPerLiter;
            this.paperCapacitySqMPerLiter = paperCapacitySqMPerLiter;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static Spec enrich(String productName, String initialSourceUrl, String fallbackInstructions) {
        List<Candidate> candidates = new ArrayList<>();
        if (isHttp(initialSourceUrl)) candidates.add(new Candidate(initialSourceUrl, productName));
        candidates.addAll(searchCandidateUrls(productName));
        Set<String> seen = new LinkedHashSet<>(); StringBuilder all = new StringBuilder(); String bestSource = "";
        int tried = 0;
        for (Candidate c : candidates) {
            if (!isHttp(c.url) || !seen.add(c.url) || tried++ >= 5) continue;
            if (looksEditorial(c.title, c.url)) continue;
            try {
                String text = cleanText(fetch(c.url, 600000));
                if (!pageMatchesProduct(productName, c.title + " " + text)) continue;
                all.append("\n").append(text);
                if (bestSource.isEmpty() || scoreDomain(c.url) > scoreDomain(bestSource)) bestSource = c.url;
            } catch (Exception ignored) {}
        }
        String text = all.toString(), low = text.toLowerCase(Locale.ROOT);
        String instructions = extractStockInstructions(text);
        if (!isUsefulInstruction(instructions) && isUsefulInstruction(fallbackInstructions)) instructions = fallbackInstructions;
        double filmCapacity = extractFilmCapacityPerLiter(low);
        double paperCapacity = extractPaperCapacitySqMPerLiter(low);
        int reuse = REUSE_UNKNOWN;
        String reuseContext = contextAroundProduct(low, productName, 3500);
        if (containsAny(reuseContext, "one shot", "one-shot", "single use", "single-use", "discard after use", "use once", "monouso", "usa e getta")) reuse = REUSE_ONE_SHOT;
        else if (filmCapacity > 0 || paperCapacity > 0 || containsAny(reuseContext, "reusable", "re-use", "can be reused", "can be re-used", "riutilizz", "capacity", "capacità")) reuse = REUSE_REUSABLE;
        return new Spec(instructions, reuse, filmCapacity, paperCapacity, bestSource);
    }

    private static final class Candidate { final String url, title; Candidate(String u, String t) { url=u==null?"":u; title=t==null?"":t; } }

    private static List<Candidate> searchCandidateUrls(String productName) {
        List<Candidate> out = new ArrayList<>();
        try {
            String q = "\"" + productName + "\" photographic chemistry datasheet product";
            String url = "https://html.duckduckgo.com/html/?q=" + URLEncoder.encode(q, "UTF-8");
            String html = fetch(url, 350000);
            Matcher m = Pattern.compile("(?is)<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>").matcher(html);
            while (m.find() && out.size() < 12) {
                String u = decodeDuckUrl(m.group(1)), title = cleanText(m.group(2));
                if (!isHttp(u) || looksEditorial(title, u) || !queryOverlap(productName, title + " " + u) || scoreDomain(u) < 70) continue;
                out.add(new Candidate(u, title));
            }
        } catch (Exception ignored) {}
        out.sort((a,b)->Integer.compare(scoreDomain(b.url), scoreDomain(a.url)));
        return out;
    }

    private static boolean pageMatchesProduct(String productName, String text) {
        Set<String> tokens = significantTokens(productName); if (tokens.isEmpty()) return false;
        String n = normalize(text); int hits = 0; for (String t : tokens) if (n.contains(t)) hits++;
        return hits >= Math.max(1, (int)Math.ceil(tokens.size() * 0.6));
    }

    private static boolean queryOverlap(String query, String text) {
        Set<String> q = significantTokens(query); if (q.isEmpty()) return false; String n = normalize(text); int hits=0;
        for (String t : q) if (n.contains(t)) hits++;
        return hits >= Math.max(1, (int)Math.ceil(q.size()*0.5));
    }

    private static Set<String> significantTokens(String s) {
        Set<String> out = new LinkedHashSet<>();
        for (String t : normalize(s).split("\\s+")) if (t.length() >= 3 && !t.equals("developer") && !t.equals("fixer") && !t.equals("photo") && !t.equals("film") && !t.equals("plus") && !t.equals("eco")) out.add(t);
        return out;
    }

    private static String contextAroundProduct(String text, String productName, int radius) {
        if (text == null || text.isEmpty()) return ""; String first="";
        for (String t : normalize(productName).split("\\s+")) if (t.length()>=3) { first=t; break; }
        if (first.isEmpty()) return text.substring(0, Math.min(text.length(), radius*2));
        int i=text.indexOf(first); if (i<0) return text.substring(0, Math.min(text.length(), radius*2));
        return text.substring(Math.max(0,i-radius), Math.min(text.length(),i+radius));
    }

    private static int scoreDomain(String url) {
        if (url==null) return 0; String s=url.toLowerCase(Locale.ROOT);
        if (containsAny(s,"foma.cz","ilfordphoto.com","harmantechnology.com","adox.de","bellinifoto.it","kodakalaris.com","kodak.com","ferrania.it","bergger.com","cinestillfilm.com")) return 100;
        if (containsAny(s,"fotoimpex.com","macodirect.de","ars-imago.com","puntofotoroma.it","pfg.it")) return 70;
        if (s.contains("digitaltruth.com")) return 40; return 10;
    }

    private static boolean looksEditorial(String title, String url) {
        String s=(title+" "+url).toLowerCase(Locale.ROOT);
        return containsAny(s,"guide","basics","tutorial","how to","review","blog","/blog/","/article/","article","forum","reddit","youtube","facebook","instagram","best ","top 10","essential guide","camera basics","film chemicals 20");
    }

    private static String extractStockInstructions(String text) {
        if (text==null || text.length()<20) return null; String normalized=text.replace('\n',' ').replaceAll("\\s+"," ").trim(); String low=normalized.toLowerCase(Locale.ROOT);
        String[] keys={"stock solution","dissolve","dissolving","mix the powder","mixing instructions","preparation","prepare","polvere","sciogli","soluzione stock","water at","acqua a"};
        int best=-1; for (String key:keys){int i=low.indexOf(key); if(i>=0&&(best<0||i<best))best=i;} if(best<0)return null;
        String chunk=normalized.substring(Math.max(0,best-220),Math.min(normalized.length(),best+850));
        if(!Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c)").matcher(chunk).find())return null;
        if(chunk.length()>700)chunk=chunk.substring(0,700).trim()+"…"; return chunk.trim();
    }

    private static boolean isUsefulInstruction(String s) { return s!=null && s.trim().length()>=20 && Pattern.compile("(?i)\\d+(?:[.,]\\d+)?\\s*(?:ml|l|litre|liter|litro|litri|°c)").matcher(s).find(); }

    private static double extractFilmCapacityPerLiter(String text) {
        if(text==null)return -1; Pattern[] ps={Pattern.compile("(?i)(\\d{1,3}(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)"),Pattern.compile("(?i)(?:capacity|capacità)[^.;]{0,90}?(\\d{1,3}(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,60}?(?:litre|liter|litro|l\\b)")};
        for(Pattern p:ps){Matcher m=p.matcher(text); if(m.find()){double v=parseNum(m.group(1)); if(v>0&&v<=500)return v;}} return -1;
    }

    private static double extractPaperCapacitySqMPerLiter(String text) {
        if(text==null)return -1; Matcher area=Pattern.compile("(?i)(\\d+(?:[.,]\\d+)?)\\s*m(?:2|²)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)").matcher(text);
        if(area.find()){double v=parseNum(area.group(1)); if(v>0&&v<200)return v;}
        Matcher sheets=Pattern.compile("(?i)(\\d{1,4})\\s*(?:sheets?|prints?|fogli)[^.;]{0,90}?(\\d+(?:[.,]\\d+)?)\\s*[x×]\\s*(\\d+(?:[.,]\\d+)?)\\s*(cm|in|inch|inches)[^.;]{0,70}?(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)").matcher(text);
        if(sheets.find()){double n=parseNum(sheets.group(1)),w=parseNum(sheets.group(2)),h=parseNum(sheets.group(3)); String unit=sheets.group(4).toLowerCase(Locale.ROOT); if(!unit.equals("cm")){w*=2.54;h*=2.54;} double sqm=n*(w/100.0)*(h/100.0); if(sqm>0&&sqm<200)return sqm;} return -1;
    }

    private static double parseNum(String s){try{return Double.parseDouble(s.replace(',','.'));}catch(Exception e){return -1;}}
    private static String fetch(String urlString,int maxChars)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(urlString).openConnection();c.setConnectTimeout(7000);c.setReadTimeout(9000);c.setInstanceFollowRedirects(true);c.setRequestProperty("User-Agent","Mozilla/5.0 (Android) DarkroomAssistant/0.1.6");c.setRequestProperty("Accept-Language","it-IT,it;q=0.9,en;q=0.8");int code=c.getResponseCode();if(code<200||code>=400)throw new IllegalStateException("HTTP "+code);InputStream in=c.getInputStream();BufferedReader br=new BufferedReader(new InputStreamReader(in));StringBuilder sb=new StringBuilder();char[] buf=new char[4096];int n;while((n=br.read(buf))>0&&sb.length()<maxChars)sb.append(buf,0,n);br.close();return sb.toString();}
    private static String decodeDuckUrl(String href){try{int i=href.indexOf("uddg=");if(i>=0){String v=href.substring(i+5);int amp=v.indexOf('&');if(amp>=0)v=v.substring(0,amp);return URLDecoder.decode(v,"UTF-8");}}catch(Exception ignored){}return href.replace("&amp;","&");}
    private static String cleanText(String s){if(s==null)return "";return s.replaceAll("(?is)<script.*?</script>"," ").replaceAll("(?is)<style.*?</style>"," ").replaceAll("(?s)<[^>]+>"," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&apos;","'").replace("&nbsp;"," ").replace("&deg;","°").replaceAll("\\s+"," ").trim();}
    private static boolean containsAny(String text,String...terms){if(text==null)return false;for(String t:terms)if(text.contains(t))return true;return false;}
    private static String normalize(String s){if(s==null)return "";return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+"," ").replaceAll("\\s+"," ").trim();}
    private static boolean isHttp(String s){return s!=null&&(s.startsWith("https://")||s.startsWith("http://"));}
    private ChemistrySpecEngine(){}
}
