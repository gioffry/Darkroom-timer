#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path("combined/src/main/java/it/darkroom")
FULL = ROOT / "assistant/FullCatalogStore.java"
MDC = ROOT / "assistant/MdcOfflineStore.java"
MAIN = ROOT / "timer/MainActivity.java"

def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f"{label}: expected 1 anchor, found {n}")
    return text.replace(old,new,1)

def volume_fingerprint(text):
    keys=("VOLUME_","VOL+","VOL-","KEYCODE_VOLUME","dispatchKeyEvent",
          "toggleFocusFromVolume","screenOffFocusBridgeRequested",
          "ACTION_ENABLE_SCREEN_OFF_FOCUS","ACTION_DISABLE_SCREEN_OFF_FOCUS")
    lines=[line for line in text.splitlines() if any(k in line for k in keys)]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

full=FULL.read_text(encoding="utf-8")
mdc=MDC.read_text(encoding="utf-8")
main=MAIN.read_text(encoding="utf-8")
vol_before=volume_fingerprint(main)

old_search_dev='''    static List<OnlineCatalogSearch.SearchResult> searchFilmDevelopers(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name FROM developers",null)){
            while(c.moveToNext()) {
                String name=c.getString(0);
                add(map,q,name,developerAliases(name),"MDC_OFFLINE_DEVELOPER|"+developerManufacturer(name));
            }
        }
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM_DEV)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"LOCAL_CATALOG_DEVELOPER|"+nz(c.getString(2)));
        }
        return results(map,max);
    }
'''
new_search_dev='''    static List<OnlineCatalogSearch.SearchResult> searchFilmDevelopers(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        // MacoDirect is the admission gate: MDC is specialist timing data, never
        // an independent source of user-visible products.
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM_DEV)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"MACODIRECT_CATALOG_DEVELOPER|"+nz(c.getString(2)));
        }
        addCatalogAliasesForRole(map,q,ROLE_FILM_DEV,"MACODIRECT_CATALOG_DEVELOPER");
        return results(map,max);
    }
'''
full=replace_once(full,old_search_dev,new_search_dev,"film developer Maco gate")

old_search_film='''    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name FROM films",null)){
            while(c.moveToNext()) add(map,q,c.getString(0),"","MDC_OFFLINE_FILM");
        }
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"LOCAL_CATALOG_FILM|"+nz(c.getString(2)));
        }
        return results(map,max);
    }
'''
new_search_film='''    static List<OnlineCatalogSearch.SearchResult> searchFilms(String query, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        // Same admission rule as chemistry: only film families listed by MacoDirect
        // are visible. The large MDC film table remains available behind the scenes.
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(ROLE_FILM)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),"MACODIRECT_CATALOG_FILM|"+nz(c.getString(2)));
        }
        addCatalogAliasesForRole(map,q,ROLE_FILM,"MACODIRECT_CATALOG_FILM");
        return results(map,max);
    }
'''
full=replace_once(full,old_search_film,new_search_film,"film Maco gate")

old_search_chem='''    static List<String> searchChemicalNames(String query, int role, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(role)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),nz(c.getString(2)));
        }
        List<Candidate> cs=sorted(map);
        List<String> out=new ArrayList<>(); for(Candidate c:cs){out.add(c.name); if(out.size()>=max)break;} return out;
    }
'''
new_search_chem='''    static List<String> searchChemicalNames(String query, int role, int max) {
        String q=norm(query); if(q.length()<3) return new ArrayList<>();
        Map<String,Candidate> map=new LinkedHashMap<>();
        SQLiteDatabase d=db(); if(d==null) return new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT name,aliases,manufacturer FROM catalog_products WHERE (roles & ?)<>0",new String[]{String.valueOf(role)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),nz(c.getString(2)));
        }
        addCatalogAliasesForRole(map,q,role,"MACODIRECT_CATALOG_CHEMICAL");
        List<Candidate> cs=sorted(map);
        List<String> out=new ArrayList<>(); for(Candidate c:cs){out.add(c.name); if(out.size()>=max)break;} return out;
    }
'''
full=replace_once(full,old_search_chem,new_search_chem,"chemical alias search")

old_canonical='''    static String canonicalDeveloper(String name) {
        return canonicalFromTable("developers",name);
    }
    static String canonicalFilm(String name) {
        String direct=canonicalFromTable("films",stripFormat(name));
        if(direct!=null) return direct;
        FilmInfo fi=filmInfo(stripFormat(name));
        if(fi!=null) return canonicalFromTable("films",fi.displayName);
        return null;
    }

    private static String catalogCanonical(String name) {
'''
new_canonical='''    static String canonicalDeveloper(String name) {
        String linked=specialistLink(name,"developer");
        if(linked!=null) return linked;
        // A Maco-listed product without an audited specialist link must NOT be
        // guessed into another formula merely because its name looks similar.
        if(catalogCanonical(name)!=null) return null;
        // Legacy inventory/internal compatibility only.
        return canonicalFromTable("developers",name);
    }
    static String canonicalFilm(String name) {
        String wanted=stripFormat(name);
        String linked=specialistLink(wanted,"film");
        if(linked!=null) return linked;
        if(catalogCanonical(wanted)!=null) return null;
        // Legacy inventory/internal compatibility only.
        return canonicalFromTable("films",wanted);
    }

    private static String specialistLink(String name,String kind) {
        SQLiteDatabase d=db(); if(d==null||name==null) return null;
        String canonical=catalogCanonical(name);
        if(canonical==null) return null;
        try(Cursor c=d.rawQuery(
                "SELECT l.specialist_name FROM catalog_specialist_links l " +
                "JOIN catalog_products p ON p.id=l.product_id " +
                "WHERE p.norm_name=? AND l.specialist_kind=? LIMIT 1",
                new String[]{norm(canonical),kind})){
            if(c.moveToFirst()) return c.getString(0);
        }
        return null;
    }

    private static void addCatalogAliasesForRole(Map<String,Candidate> map,String q,int role,String snippet) {
        SQLiteDatabase d=db(); if(d==null) return;
        try(Cursor c=d.rawQuery(
                "SELECT p.name,a.alias,p.manufacturer FROM catalog_aliases a " +
                "JOIN catalog_products p ON p.id=a.product_id WHERE (p.roles & ?)<>0",
                new String[]{String.valueOf(role)})){
            while(c.moveToNext()) add(map,q,c.getString(0),c.getString(1),snippet+"|"+nz(c.getString(2)));
        }
    }

    private static String catalogCanonical(String name) {
'''
full=replace_once(full,old_canonical,new_canonical,"specialist link routing")

# Force the updated bundled SQLite onto devices that already have v0.7.12 installed.
mdc=replace_once(mdc,
    'private static final String DB_NAME = "mdc_offline_darkroom_v071.sqlite";',
    'private static final String DB_NAME = "mdc_offline_darkroom_v0713.sqlite";',
    "database refresh filename")

# Internal build marker only. No timer / Sonoff logic touched.
main=replace_once(main,'private static final String APP_VERSION = "0.13.25";',
                       'private static final String APP_VERSION = "0.13.26";',
                       "internal version marker")

if volume_fingerprint(main)!=vol_before:
    raise SystemExit("VOL+/VOL- guard failed: volume/focus logic changed")

# Source assertions
assert 'SELECT name FROM developers",null' not in full
assert 'SELECT name FROM films",null' not in full
assert 'MACODIRECT_CATALOG_DEVELOPER' in full
assert 'MACODIRECT_CATALOG_FILM' in full
assert 'addCatalogAliasesForRole' in full
assert 'catalog_specialist_links' in full
assert 'if(catalogCanonical(name)!=null) return null;' in full
assert 'mdc_offline_darkroom_v0713.sqlite' in mdc
assert 'APP_VERSION = "0.13.26"' in main

FULL.write_text(full,encoding="utf-8")
MDC.write_text(mdc,encoding="utf-8")
MAIN.write_text(main,encoding="utf-8")

print("v0713_macodirect_catalog_gate=PASS")
print("film_search_macodirect_only=PASS")
print("film_developer_search_macodirect_only=PASS")
print("chemical_alias_table_search=PASS")
print("specialist_links_explicit=PASS")
print("database_refresh_v0713=PASS")
print("sonoff_vol_plus_minus_changes=ZERO")
