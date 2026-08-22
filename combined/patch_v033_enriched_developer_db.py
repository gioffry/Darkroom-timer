from pathlib import Path
import glob, re, sqlite3, subprocess, sys

ROOT = Path('.')
DB = ROOT / 'assistant/src/main/assets/mdc_full.sqlite'
if not DB.exists():
    raise SystemExit('v033: MDC database missing')

# Rebuild the technical layer in the strict hierarchy requested by the project:
# MDC first, manufacturer only fills fields that are still empty.
subprocess.run([sys.executable, 'assistant/db/enrich_developer_profiles.py'], check=True)
for path in sorted(glob.glob('assistant/db/producer_enrichment_batch*.json')):
    subprocess.run([sys.executable, 'assistant/db/apply_manufacturer_batch.py', path], check=True)
for path in sorted(glob.glob('assistant/db/macodirect_enrichment_batch*.json')):
    subprocess.run([sys.executable, 'assistant/db/apply_macodirect_scoped_batch.py', path], check=True)
subprocess.run([sys.executable, 'assistant/db/audit_developer_profiles.py'], check=True)
subprocess.run([sys.executable, 'assistant/db/audit_macodirect_scope.py'], check=True)

con = sqlite3.connect(DB)
cur = con.cursor()
profiles = cur.execute('SELECT COUNT(*) FROM developer_profiles').fetchone()[0]
combinations = cur.execute('SELECT COUNT(*) FROM times').fetchone()[0]
mdc_dils = cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]
supergrain = cur.execute("SELECT manufacturer,physical_state,preparation,reuse_mode,capacity_text,shelf_life_unopened FROM developer_profiles WHERE developer_norm='rollei supergrain'").fetchone()
excel = cur.execute("SELECT manufacturer,physical_state,preparation,reuse_mode,capacity_text FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
excel_dils = [r[0] for r in cur.execute("SELECT dilution FROM developer_dilutions WHERE developer_norm='fomadon excel' ORDER BY dilution_norm")]
quick = cur.execute('PRAGMA quick_check').fetchone()[0]
con.close()
if profiles != 232 or combinations != 14504 or mdc_dils < 700 or quick != 'ok':
    raise SystemExit(f'v033: enriched DB integrity failed profiles={profiles} combinations={combinations} mdc_dils={mdc_dils} quick={quick}')
if not supergrain or not all(str(x or '').strip() for x in supergrain):
    raise SystemExit('v033: Rollei Supergrain profile is not complete')
if not excel or not str(excel[2] or '').strip() or not str(excel[4] or '').strip():
    raise SystemExit('v033: FOMADON Excel technical profile incomplete')
if not {'stock','1+1','1+2','1+3'}.issubset(set(excel_dils)):
    raise SystemExit('v033: FOMADON Excel MDC dilutions missing')

# FullCatalogStore: expose the enriched developer profile to the Android UI.
p = ROOT / 'assistant/src/main/java/it/darkroom/assistant/FullCatalogStore.java'
s = p.read_text(encoding='utf-8')
marker = '    static final class FilmInfo {'
if marker not in s:
    raise SystemExit('v033: FullCatalogStore FilmInfo marker missing')
profile_class = r'''    static final class DeveloperProfile {
        final String developerName, productName, manufacturer, physicalState, preparation;
        final String reuseMode, reuseInstructions, capacityText;
        final String shelfLifeUnopened, shelfLifeOpened, shelfLifeStock, shelfLifeWorking;
        final String storageNotes, exhaustionNotes, sourceUrl;
        final String[] dilutions;
        DeveloperProfile(String developerName,String productName,String manufacturer,String physicalState,
                         String preparation,String reuseMode,String reuseInstructions,String capacityText,
                         String shelfLifeUnopened,String shelfLifeOpened,String shelfLifeStock,
                         String shelfLifeWorking,String storageNotes,String exhaustionNotes,
                         String sourceUrl,String[] dilutions) {
            this.developerName=developerName; this.productName=productName; this.manufacturer=manufacturer;
            this.physicalState=physicalState; this.preparation=preparation; this.reuseMode=reuseMode;
            this.reuseInstructions=reuseInstructions; this.capacityText=capacityText;
            this.shelfLifeUnopened=shelfLifeUnopened; this.shelfLifeOpened=shelfLifeOpened;
            this.shelfLifeStock=shelfLifeStock; this.shelfLifeWorking=shelfLifeWorking;
            this.storageNotes=storageNotes; this.exhaustionNotes=exhaustionNotes;
            this.sourceUrl=sourceUrl; this.dilutions=dilutions;
        }
    }

'''
s = s.replace(marker, profile_class + marker, 1)

method_marker = '    static FilmInfo filmInfo(String name) {'
if method_marker not in s:
    raise SystemExit('v033: FullCatalogStore filmInfo marker missing')
profile_methods = r'''    static DeveloperProfile developerProfile(String name) {
        if(name==null) return null; SQLiteDatabase d=db(); if(d==null) return null;
        String canonical=canonicalDeveloper(name); if(canonical==null) return null;
        String dn=norm(canonical);
        String devName="", productName="", manufacturer="", physical="", preparation="";
        String reuseMode="", reuseInstructions="", capacity="";
        String lifeUnopened="", lifeOpened="", lifeStock="", lifeWorking="";
        String storage="", exhaustion="", source="";
        try(Cursor c=d.rawQuery("SELECT developer_name,product_name,manufacturer,physical_state,preparation,reuse_mode,reuse_instructions,capacity_text,shelf_life_unopened,shelf_life_opened,shelf_life_stock,shelf_life_working,storage_notes,exhaustion_notes FROM developer_profiles WHERE developer_norm=? LIMIT 1",new String[]{dn})){
            if(!c.moveToFirst()) return null;
            devName=nz(c.getString(0)); productName=nz(c.getString(1)); manufacturer=nz(c.getString(2));
            physical=nz(c.getString(3)); preparation=nz(c.getString(4)); reuseMode=nz(c.getString(5));
            reuseInstructions=nz(c.getString(6)); capacity=nz(c.getString(7)); lifeUnopened=nz(c.getString(8));
            lifeOpened=nz(c.getString(9)); lifeStock=nz(c.getString(10)); lifeWorking=nz(c.getString(11));
            storage=nz(c.getString(12)); exhaustion=nz(c.getString(13));
        }
        List<String> ds=new ArrayList<>();
        try(Cursor c=d.rawQuery("SELECT dilution FROM developer_dilutions WHERE developer_norm=? ORDER BY CASE WHEN source_kind='MDC' THEN 0 ELSE 1 END,dilution_norm",new String[]{dn})){
            while(c.moveToNext()){String v=nz(c.getString(0)); if(!v.isEmpty()&&!ds.contains(v))ds.add(v);}
        }
        try(Cursor c=d.rawQuery("SELECT source_url FROM developer_profile_sources WHERE developer_norm=? AND source_kind='MANUFACTURER' ORDER BY checked_at DESC LIMIT 1",new String[]{dn})){
            if(c.moveToFirst())source=nz(c.getString(0));
        }
        return new DeveloperProfile(devName,productName,manufacturer,physical,preparation,reuseMode,
                reuseInstructions,capacity,lifeUnopened,lifeOpened,lifeStock,lifeWorking,storage,exhaustion,
                source,ds.toArray(new String[0]));
    }

    static double capacityRollsPerLiter(String text) {
        if(text==null||text.trim().isEmpty())return -1;
        java.util.regex.Pattern[] ps=new java.util.regex.Pattern[]{
            java.util.regex.Pattern.compile("(?i)1\\s*(?:litre|liter|litro|l\\b)[^0-9]{0,120}(\\d+(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)"),
            java.util.regex.Pattern.compile("(?i)(\\d+(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,100}(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)")
        };
        for(java.util.regex.Pattern p:ps){java.util.regex.Matcher m=p.matcher(text);if(m.find())try{return Double.parseDouble(m.group(1).replace(',','.'));}catch(Exception ignored){}}
        return -1;
    }

'''
s = s.replace(method_marker, profile_methods + method_marker, 1)
p.write_text(s, encoding='utf-8')

# AssistantActivityV2: developer_profiles is now the authoritative operational sheet
# for film developers.  It provides the correct type, preparation, reuse and capacity.
p = ROOT / 'assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java'
s = p.read_text(encoding='utf-8')
pat = re.compile(r'    private Product findProduct\(String name\) \{.*?\n    \}\n\n    private FilmStock findFilm', re.S)
replacement = r'''    private int reuseModeFromProfile(String mode) {
        String m = mode == null ? "" : mode.toLowerCase(Locale.ROOT);
        if (m.contains("one_shot") || m.contains("one-shot") || m.equals("one shot")) return ChemistrySpecEngine.REUSE_ONE_SHOT;
        if (m.contains("reusable") || m.contains("replenish") || m.contains("reuse")) return ChemistrySpecEngine.REUSE_REUSABLE;
        return ChemistrySpecEngine.REUSE_UNKNOWN;
    }

    private Product productFromDeveloperProfile(FullCatalogStore.DeveloperProfile p) {
        String display = p.productName == null || p.productName.trim().isEmpty() ? p.developerName : p.productName;
        boolean stock = false;
        for (String d : p.dilutions) if ("stock".equalsIgnoreCase(d)) { stock = true; break; }
        double capacity = FullCatalogStore.capacityRollsPerLiter(p.capacityText);
        return new Product(display, ROLE_FILM_DEV, stock, p.dilutions, new String[0], null,
                p.preparation == null || p.preparation.trim().isEmpty() ? null : p.preparation,
                -1, p.sourceUrl, reuseModeFromProfile(p.reuseMode), capacity, -1);
    }

    private Product findProduct(String name) {
        if (name == null) return null;
        String wanted = name.trim();
        FullCatalogStore.DeveloperProfile profile = FullCatalogStore.developerProfile(wanted);
        Product saved = loadSavedProduct(wanted);
        if (saved != null && profile == null) return saved;
        if (profile != null) return productFromDeveloperProfile(profile);

        FullCatalogStore.Chemical cat = FullCatalogStore.chemical(wanted);
        if (cat != null && (cat.roles & ~128) != 0) {
            return new Product(cat.name, cat.roles, cat.stockPrep,
                    cat.filmDilutions, cat.paperDilutions, cat.workingDilution, null, -1, cat.sourceUrl,
                    ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);
        }
        String canonical = FullCatalogStore.canonicalDeveloper(wanted);
        if (canonical != null) return offlineDeveloperProduct(canonical);
        Product curated = curatedAuxByName(wanted);
        if (curated != null) return curated;
        for (Product x : fallbackProducts) if (x.name.equalsIgnoreCase(wanted)) return x;
        return null;
    }

    private FilmStock findFilm'''
s, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('v033: AssistantActivityV2 findProduct replacement failed')

# Add the technical profile to the product detail popup.  Shelf life remains contextual
# (concentrate/stock/working) instead of being flattened into a guessed expiry date.
needle = '        FullCatalogStore.Chemical catalogInfo = FullCatalogStore.chemical(p.name);'
if needle not in s:
    raise SystemExit('v033: product detail catalog marker missing')
profile_detail = r'''        FullCatalogStore.DeveloperProfile technicalProfile = FullCatalogStore.developerProfile(p.name);
        if (technicalProfile != null) {
            msg.append("\n\nSCHEDA TECNICA");
            if (!technicalProfile.manufacturer.isEmpty()) msg.append("\nProduttore: ").append(technicalProfile.manufacturer);
            if (!technicalProfile.physicalState.isEmpty()) msg.append("\nStato: ").append(technicalProfile.physicalState);
            if (!technicalProfile.preparation.isEmpty()) msg.append("\nPreparazione: ").append(technicalProfile.preparation);
            if (!technicalProfile.reuseInstructions.isEmpty()) msg.append("\nRiutilizzo: ").append(technicalProfile.reuseInstructions);
            else if (!technicalProfile.reuseMode.isEmpty()) msg.append("\nRiutilizzo: ").append(technicalProfile.reuseMode.replace('_',' '));
            if (!technicalProfile.capacityText.isEmpty()) msg.append("\nCapacità: ").append(technicalProfile.capacityText);
            if (!technicalProfile.shelfLifeUnopened.isEmpty()) msg.append("\nConservabilità non aperto: ").append(technicalProfile.shelfLifeUnopened);
            if (!technicalProfile.shelfLifeOpened.isEmpty()) msg.append("\nConservabilità aperto: ").append(technicalProfile.shelfLifeOpened);
            if (!technicalProfile.shelfLifeStock.isEmpty()) msg.append("\nConservabilità stock: ").append(technicalProfile.shelfLifeStock);
            if (!technicalProfile.shelfLifeWorking.isEmpty()) msg.append("\nConservabilità soluzione di lavoro: ").append(technicalProfile.shelfLifeWorking);
            if (!technicalProfile.storageNotes.isEmpty()) msg.append("\nConservazione: ").append(technicalProfile.storageNotes);
        }
'''
s = s.replace(needle, profile_detail + needle, 1)
p.write_text(s, encoding='utf-8')

# Force a fresh copy of the bundled read-only catalog on upgrade from v0.3.2.
# SharedPreferences/inventory/recipes/logs are untouched.
p = ROOT / 'assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java'
s = p.read_text(encoding='utf-8')
s = s.replace('private static final int DB_VERSION = 3;', 'private static final int DB_VERSION = 4;', 1)
s = s.replace('private static final String DB_NAME = "mdc_offline_darkroom_v029.sqlite";', 'private static final String DB_NAME = "mdc_offline_darkroom_v033.sqlite";', 1)
p.write_text(s, encoding='utf-8')

Path('validation-v033-enriched-db.txt').write_text(
    'developer_db_runtime=PASS\n'
    'hierarchy=MDC_FIRST_MANUFACTURER_FILL_ONLY\n'
    f'profiles={profiles}\n'
    f'combinations={combinations}\n'
    f'mdc_dilutions={mdc_dils}\n'
    'rollei_supergrain=PASS\n'
    'fomadon_excel_runtime=PASS\n'
    'catalog_cache_refresh=v033_schema4\n'
    'personal_data_migration=NO_DESTRUCTIVE_RESET\n', encoding='utf-8')
print('v033 enriched developer DB runtime patch applied')
