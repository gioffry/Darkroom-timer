package it.darkroom.timer.assistant.search;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Live web resolver used only when the structured local/remote catalog has no match.
 * It performs an actual Internet search, ranks likely manufacturer/technical pages,
 * follows HTML result pages, extracts documented dilutions, and keeps source URLs.
 * No value is invented when it cannot be extracted from the retrieved pages/snippets.
 */
public final class WebProductResolver {
    public interface Callback { void done(List<SmartSearchEngine.Item> items,String error); }
    private static final int CONNECT_MS=5000,READ_MS=6000,MAX_BYTES=900000;
    private WebProductResolver(){}

    public static void resolve(Context c,String query,Set<String> categories,Callback cb){
        final Context app=c.getApplicationContext();final String q=query==null?"":query.trim();final Set<String> cats=categories==null?new LinkedHashSet<String>():new LinkedHashSet<>(categories);
        if(q.length()<2){post(cb,new ArrayList<>(),"query troppo breve");return;}
        new Thread(()->{
            ArrayList<SmartSearchEngine.Item> out=new ArrayList<>();String error=null;
            try{
                String searchQuery=q+" fotografia photographic developer diluizione dilution scheda tecnica data sheet";
                List<WebSearchParser.Hit> hits=new ArrayList<>();
                try{hits.addAll(WebSearchParser.parseDuckHtml(get("https://html.duckduckgo.com/html/?q="+enc(searchQuery),"text/html")));}catch(Exception ignored){}
                if(hits.isEmpty())try{hits.addAll(WebSearchParser.parseBingHtml(get("https://www.bing.com/search?q="+enc(searchQuery),"text/html")));}catch(Exception ignored){}
                if(hits.isEmpty())throw new Exception("motore di ricerca non raggiungibile o nessun risultato");
                WebSearchParser.Hit best=WebSearchParser.bestHit(hits,q);if(best==null)throw new Exception("nessuna fonte candidata");
                StringBuilder evidence=new StringBuilder();for(WebSearchParser.Hit h:hits){evidence.append(h.title).append(' ').append(h.snippet).append('\n');}
                // Follow the strongest few HTML pages so dilution/category data come from the page, not only a snippet.
                int followed=0;for(WebSearchParser.Hit h:rank(hits,q)){if(followed>=3)break;try{String page=get(h.url,"text/html");if(!page.isEmpty()){evidence.append('\n').append(strip(page));followed++;}}catch(Exception ignored){}}
                List<String> dilutions=WebSearchParser.extractDilutions(evidence.toString());
                JSONObject record=buildRecord(q,cats,best,dilutions,evidence.toString());
                out.add(itemFromRecord(record));
            }catch(Exception ex){error=ex.getMessage();}
            post(cb,out,error);
        },"darkroom-live-web-search").start();
    }

    private static JSONObject buildRecord(String query,Set<String> cats,WebSearchParser.Hit best,List<String> dilutions,String evidence)throws Exception{
        JSONObject r=new JSONObject();String maker=inferManufacturer(query,best.url,best.title);String name=humanName(query);
        r.put("id","web-"+slug(name)+"-"+Integer.toHexString(best.url.hashCode()));r.put("name",name);r.put("manufacturer",maker);
        JSONArray categories=new JSONArray();for(String c:normalizedCategories(cats))categories.put(c);r.put("categories",categories);JSONArray aliases=new JSONArray();aliases.put(query);r.put("aliases",aliases);
        r.put("subtitle","Trovato automaticamente sul Web · controlla la fonte");r.put("verificationStatus","DA VERIFICARE");r.put("dataDate",new SimpleDateFormat("yyyy-MM-dd",Locale.US).format(new Date()));
        JSONObject tech=new JSONObject();JSONArray ds=new JSONArray();for(String d:dilutions)ds.put(d);if(ds.length()>0)tech.put("dilutions",ds);tech.put("dataType","DATO WEB ESTRATTO AUTOMATICAMENTE");if(ds.length()==0)tech.put("note","Nessuna diluizione leggibile estratta: il prodotto è stato trovato, ma il dato non viene inventato.");r.put("technical",tech);
        JSONObject src=new JSONObject();src.put("sourceType","RICERCA WEB AUTOMATICA");src.put("author",maker.isEmpty()?WebSearchParser.host(best.url):maker);src.put("title",best.title);src.put("url",best.url);src.put("reference","Pagina trovata tramite ricerca Internet live");src.put("verificationStatus","DA VERIFICARE");r.put("_source",src);r.put("_origin","RICERCA WEB LIVE");
        // Keep a compact evidence excerpt so a later correction can always preserve what was originally found.
        String ev=evidence==null?"":evidence.replaceAll("\\s+"," ").trim();if(ev.length()>1800)ev=ev.substring(0,1800);r.put("_webEvidence",ev);return r;
    }

    public static SmartSearchEngine.Item itemFromRecord(JSONObject r){
        ArrayList<String> cats=list(r.optJSONArray("categories")),aliases=list(r.optJSONArray("aliases"));String maker=r.optString("manufacturer","");String subtitle=r.optString("subtitle","");String origin="RICERCA WEB LIVE · FONTE DA VERIFICARE";return new SmartSearchEngine.Item(r.optString("id","web"),r.optString("name",""),maker,cats,aliases,subtitle,origin,r.toString(),true);
    }

    public static JSONObject correctedCopy(SmartSearchEngine.Item original,String name,String manufacturer,String dilutionCsv)throws Exception{
        JSONObject before=new JSONObject(original.recordJson);JSONObject r=new JSONObject(before.toString());r.put("_originalRecord",before.toString());r.put("_userCorrected",true);if(name!=null&&!name.trim().isEmpty())r.put("name",name.trim());if(manufacturer!=null&&!manufacturer.trim().isEmpty())r.put("manufacturer",manufacturer.trim());
        JSONObject t=r.optJSONObject("technical");if(t==null){t=new JSONObject();r.put("technical",t);}JSONArray ds=new JSONArray();if(dilutionCsv!=null)for(String x:dilutionCsv.split("[,;]")){x=x.trim();if(!x.isEmpty())ds.put(x);}if(ds.length()>0)t.put("dilutions",ds);return r;
    }

    public static String dilutionCsv(SmartSearchEngine.Item item){try{JSONArray a=new JSONObject(item.recordJson).optJSONObject("technical").optJSONArray("dilutions");if(a==null)return "";StringBuilder b=new StringBuilder();for(int i=0;i<a.length();i++){if(b.length()>0)b.append(", ");b.append(a.optString(i));}return b.toString();}catch(Exception e){return "";}}
    public static String sourceUrl(SmartSearchEngine.Item item){try{return new JSONObject(item.recordJson).optJSONObject("_source").optString("url","");}catch(Exception e){return "";}}

    private static List<WebSearchParser.Hit> rank(List<WebSearchParser.Hit> hits,String q){ArrayList<WebSearchParser.Hit> x=new ArrayList<>(hits);final String maker=q.trim().split("\\s+")[0].toLowerCase(Locale.ROOT);java.util.Collections.sort(x,(a,b)->Integer.compare(score(b,maker),score(a,maker)));return x;}
    private static int score(WebSearchParser.Hit h,String maker){int s=0;String host=WebSearchParser.host(h.url);if(!maker.isEmpty()&&host.contains(maker))s+=100;if(h.snippet.toLowerCase(Locale.ROOT).contains("dilu"))s+=30;if(h.title.toLowerCase(Locale.ROOT).contains(maker))s+=20;if(h.url.toLowerCase(Locale.ROOT).endsWith(".pdf"))s-=4;return s;}
    private static Set<String> normalizedCategories(Set<String> input){LinkedHashSet<String> out=new LinkedHashSet<>();if(input!=null)out.addAll(input);if(out.isEmpty())out.add("CHEMISTRY");if(out.contains("FILM_DEVELOPER")||out.contains("PAPER_DEVELOPER")||out.contains("STOP_BATH")||out.contains("FIXER")||out.contains("WETTING_AGENT"))out.add("CHEMISTRY");return out;}
    private static String inferManufacturer(String q,String url,String title){String host=WebSearchParser.host(url);String first=q.trim().split("\\s+")[0];if(!first.isEmpty()&&host.contains(first.toLowerCase(Locale.ROOT)))return first.toUpperCase(Locale.ROOT);if(host.contains("bellini"))return "BELLINI";if(host.contains("ilford"))return "ILFORD";if(host.contains("kodak"))return "KODAK";if(host.contains("foma"))return "FOMA";if(first.length()>2)return first.toUpperCase(Locale.ROOT);return "";}
    private static String humanName(String q){String s=q.trim().replaceAll("\\s+"," ");if(s.isEmpty())return s;StringBuilder b=new StringBuilder();for(String x:s.split(" ")){if(b.length()>0)b.append(' ');if(x.length()<=3&&x.equals(x.toUpperCase(Locale.ROOT)))b.append(x);else b.append(Character.toUpperCase(x.charAt(0))).append(x.substring(1));}return b.toString();}
    private static String slug(String s){String x=s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","-").replaceAll("^-|-$","");return x.isEmpty()?"product":x;}
    private static String enc(String s)throws Exception{return URLEncoder.encode(s,"UTF-8");}
    private static String get(String u,String accept)throws Exception{HttpURLConnection c=null;try{c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(CONNECT_MS);c.setReadTimeout(READ_MS);c.setInstanceFollowRedirects(true);c.setRequestProperty("User-Agent","Mozilla/5.0 (Android) DarkroomAssistant/0.12.3");c.setRequestProperty("Accept",accept+",application/xhtml+xml;q=0.9,*/*;q=0.5");int code=c.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);String ct=c.getContentType();if(ct!=null&&ct.toLowerCase(Locale.ROOT).contains("pdf"))return "";return read(c.getInputStream());}finally{if(c!=null)c.disconnect();}}
    private static String read(InputStream in)throws Exception{try(InputStream x=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n,total=0;while((n=x.read(b))!=-1){int use=Math.min(n,MAX_BYTES-total);if(use>0)out.write(b,0,use);total+=use;if(total>=MAX_BYTES)break;}return out.toString("UTF-8");}}
    private static String strip(String html){return html==null?"":html.replaceAll("(?is)<script.*?</script>"," ").replaceAll("(?is)<style.*?</style>"," ").replaceAll("(?is)<[^>]+>"," ").replace("&nbsp;"," ").replace("&amp;","&").replaceAll("\\s+"," ");}
    private static ArrayList<String> list(JSONArray a){ArrayList<String> out=new ArrayList<>();if(a!=null)for(int i=0;i<a.length();i++){String x=a.optString(i,"");if(!x.isEmpty())out.add(x);}return out;}
    private static void post(Callback cb,List<SmartSearchEngine.Item> items,String error){new Handler(Looper.getMainLooper()).post(()->cb.done(items,error));}
}
