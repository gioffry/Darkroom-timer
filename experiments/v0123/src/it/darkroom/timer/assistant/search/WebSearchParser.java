package it.darkroom.timer.assistant.search;

import java.net.URI;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Pure-Java parser/ranker for live web search results. */
public final class WebSearchParser {
    public static final class Hit {
        public final String url,title,snippet;
        public Hit(String url,String title,String snippet){this.url=safe(url);this.title=safe(title);this.snippet=safe(snippet);}
    }
    private WebSearchParser(){}

    public static List<Hit> parseDuckHtml(String html){
        ArrayList<Hit> out=new ArrayList<>();if(html==null)return out;
        Pattern a=Pattern.compile("(?is)<a[^>]*class=\\\"[^\\\"]*result__a[^\\\"]*\\\"[^>]*href=\\\"([^\\\"]+)\\\"[^>]*>(.*?)</a>");
        Matcher m=a.matcher(html);while(m.find()&&out.size()<12){String href=decodeDuckHref(unescape(m.group(1)));String title=clean(m.group(2));int from=m.end(),to=Math.min(html.length(),from+1800);String block=html.substring(from,to);String snippet="";Matcher s=Pattern.compile("(?is)class=\\\"[^\\\"]*result__snippet[^\\\"]*\\\"[^>]*>(.*?)</(?:a|div)>").matcher(block);if(s.find())snippet=clean(s.group(1));if(!href.isEmpty()&&!title.isEmpty())out.add(new Hit(href,title,snippet));}return out;
    }

    public static List<Hit> parseBingHtml(String html){
        ArrayList<Hit> out=new ArrayList<>();if(html==null)return out;
        Matcher m=Pattern.compile("(?is)<li[^>]*class=\\\"[^\\\"]*b_algo[^\\\"]*\\\"[^>]*>(.*?)</li>").matcher(html);while(m.find()&&out.size()<12){String block=m.group(1);Matcher a=Pattern.compile("(?is)<h2[^>]*>.*?<a[^>]*href=\\\"([^\\\"]+)\\\"[^>]*>(.*?)</a>").matcher(block);if(!a.find())continue;String url=unescape(a.group(1)),title=clean(a.group(2)),snippet="";Matcher p=Pattern.compile("(?is)<p[^>]*>(.*?)</p>").matcher(block);if(p.find())snippet=clean(p.group(1));if(!url.isEmpty()&&!title.isEmpty())out.add(new Hit(url,title,snippet));}return out;
    }

    public static Hit bestHit(List<Hit> hits,String query){Hit best=null;int bestScore=Integer.MIN_VALUE;for(Hit h:hits){int score=score(h,query);if(score>bestScore){bestScore=score;best=h;}}return best;}
    public static List<String> extractDilutions(String text){LinkedHashSet<String> set=new LinkedHashSet<>();Matcher m=Pattern.compile("(?i)(?:1\\s*\\+\\s*[0-9]{1,3}|stock)").matcher(safe(text));while(m.find()&&set.size()<8){String x=m.group().replaceAll("\\s+","");if("stock".equalsIgnoreCase(x))x="stock";set.add(x);}return new ArrayList<>(set);}

    public static String host(String url){try{return new URI(url).getHost()==null?"":new URI(url).getHost().toLowerCase(Locale.ROOT).replaceFirst("^www\\.","");}catch(Exception e){return "";}}
    private static int score(Hit h,String query){String q=normalize(query),hay=normalize(h.title+" "+h.snippet+" "+h.url),host=host(h.url);int s=0;String[] tok=q.split(" ");for(String t:tok)if(t.length()>1&&hay.contains(t))s+=35;if(!q.isEmpty()&&hay.contains(q))s+=80;if(tok.length>0&&host.contains(tok[0]))s+=120;if(host.endsWith(".com")||host.endsWith(".it")||host.endsWith(".de")||host.endsWith(".co.uk"))s+=5;if(h.url.toLowerCase(Locale.ROOT).contains("pdf"))s+=8;if(h.snippet.toLowerCase(Locale.ROOT).contains("dilu")||h.snippet.toLowerCase(Locale.ROOT).contains("developer"))s+=20;return s;}
    private static String decodeDuckHref(String href){try{String h=href;if(h.startsWith("//"))h="https:"+h;int p=h.indexOf("uddg=");if(p>=0){String x=h.substring(p+5);int amp=x.indexOf('&');if(amp>=0)x=x.substring(0,amp);return URLDecoder.decode(x,"UTF-8");}return h;}catch(Exception e){return href;}}
    private static String clean(String x){return unescape(safe(x).replaceAll("(?is)<[^>]+>"," ")).replaceAll("\\s+"," ").trim();}
    private static String unescape(String x){return safe(x).replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&lt;","<").replace("&gt;",">");}
    private static String normalize(String x){return safe(x).toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+"," ").trim().replaceAll("\\s+"," ");}
    private static String safe(String x){return x==null?"":x;}
}
