package it.darkroom.timer.assistant.search;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Pure-Java ranked search used by every Assistant catalog picker. */
public final class SmartSearchEngine {
    public static final int DEFAULT_LIMIT = 8;

    public static final class Item {
        public final String id;
        public final String name;
        public final String manufacturer;
        public final List<String> categories;
        public final List<String> aliases;
        public final String subtitle;
        public final String origin;
        public final String recordJson;
        public final boolean remote;

        public Item(String id,String name,String manufacturer,List<String> categories,List<String> aliases,
                    String subtitle,String origin,String recordJson,boolean remote){
            this.id=safe(id);this.name=safe(name);this.manufacturer=safe(manufacturer);
            this.categories=categories==null?Collections.<String>emptyList():new ArrayList<>(categories);
            this.aliases=aliases==null?Collections.<String>emptyList():new ArrayList<>(aliases);
            this.subtitle=safe(subtitle);this.origin=safe(origin);this.recordJson=safe(recordJson);this.remote=remote;
        }
        public boolean hasCategory(String category){
            if(category==null||category.trim().isEmpty())return true;
            for(String c:categories)if(category.equalsIgnoreCase(c))return true;
            return false;
        }
    }

    public static final class Result {
        public final Item item;
        public final int score;
        public final String reason;
        Result(Item item,int score,String reason){this.item=item;this.score=score;this.reason=reason;}
    }

    private SmartSearchEngine(){}

    public static List<Result> search(List<Item> all,String query,Set<String> categories,int limit){
        ArrayList<Result> out=new ArrayList<>();
        if(all==null)return out;
        String q=normalize(query);String qc=compact(query);
        for(Item item:all){
            if(!allowed(item,categories))continue;
            Match m=match(item,q,qc);
            if(m.score>0)out.add(new Result(item,m.score,m.reason));
        }
        Collections.sort(out,new Comparator<Result>(){
            @Override public int compare(Result a,Result b){
                if(a.item.remote!=b.item.remote)return a.item.remote?1:-1; // local/cache always before network
                int byScore=Integer.compare(b.score,a.score);if(byScore!=0)return byScore;
                int byName=a.item.name.compareToIgnoreCase(b.item.name);if(byName!=0)return byName;
                return a.item.id.compareTo(b.item.id);
            }
        });
        int cap=limit<=0?DEFAULT_LIMIT:limit;
        if(out.size()>cap)return new ArrayList<>(out.subList(0,cap));
        return out;
    }

    public static List<Result> search(List<Item> all,String query,String category,int limit){
        Set<String> cats=new LinkedHashSet<>();if(category!=null&&!category.trim().isEmpty())cats.add(category);
        return search(all,query,cats,limit);
    }

    public static String canonicalName(List<Item> all,String query,String category){
        List<Result> r=search(all,query,category,1);
        return r.isEmpty()?safe(query).trim():r.get(0).item.name;
    }

    private static boolean allowed(Item i,Set<String> categories){
        if(categories==null||categories.isEmpty())return true;
        for(String c:categories)if(i.hasCategory(c))return true;
        return false;
    }

    private static final class Match { int score;String reason; Match(int s,String r){score=s;reason=r;} }
    private static Match match(Item item,String q,String qc){
        // Ranking contract tested independently: exact name > exact alias > startsWith prefix > allWords > partial; local before remote.
        if(q.isEmpty())return new Match(80,"catalogo");
        String name=normalize(item.name), nameCompact=compact(item.name);
        if(q.equals(name)||(!qc.isEmpty()&&qc.equals(nameCompact)))return new Match(600,"nome esatto");
        for(String alias:item.aliases){String a=normalize(alias);String ac=compact(alias);if(q.equals(a)||(!qc.isEmpty()&&qc.equals(ac)))return new Match(560,"alias esatto");}
        if(name.startsWith(q)||nameCompact.startsWith(qc))return new Match(500,"inizio nome");
        for(String alias:item.aliases){String a=normalize(alias);String ac=compact(alias);if(a.startsWith(q)||(!qc.isEmpty()&&ac.startsWith(qc)))return new Match(470,"inizio alias");}
        String hay=name+" "+normalize(item.manufacturer)+" "+joinNormalized(item.aliases);
        boolean allWords=true;for(String token:q.split(" "))if(!token.isEmpty()&&!hay.contains(token)){allWords=false;break;}
        if(allWords)return new Match(400,"tutte le parole");
        String hc=compact(hay);
        if((!q.isEmpty()&&hay.contains(q))||(!qc.isEmpty()&&hc.contains(qc)))return new Match(320,"match parziale");
        return new Match(0,"");
    }

    public static String normalize(String value){
        String raw=safe(value).toLowerCase(Locale.ROOT);
        raw=Normalizer.normalize(raw,Normalizer.Form.NFD).replaceAll("\\p{M}+","");
        raw=raw.replace('+',' ');
        raw=raw.replaceAll("[^a-z0-9]+"," ").trim().replaceAll("\\s+"," ");
        return raw;
    }
    public static String compact(String value){return normalize(value).replace(" ","");}
    private static String joinNormalized(List<String> values){StringBuilder b=new StringBuilder();for(String v:values){if(b.length()>0)b.append(' ');b.append(normalize(v));}return b.toString();}
    private static String safe(String x){return x==null?"":x;}
}
