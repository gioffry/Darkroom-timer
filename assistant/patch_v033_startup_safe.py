from pathlib import Path
import re

# v0.3.3
# - startup robusto: il DB incluso non puo' piu' far crashare l'Activity
# - niente migrazione pesante del magazzino durante onCreate
# - nuovo nome DB per ignorare qualsiasi file 0.3.2 parziale/corrotto
# - retry locale una volta se apertura/copia SQLite fallisce

p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')
s = s.replace('private static final String DB_NAME = "mdc_offline_v032.sqlite";',
              'private static final String DB_NAME = "mdc_offline_v033.sqlite";', 1)

old = '    private static volatile boolean syncing = false;'
new = '    private static volatile boolean syncing = false;\n    private static volatile String initError = "";'
if old not in s: raise SystemExit('initError field marker missing')
s = s.replace(old, new, 1)

start = s.find('    static synchronized void init(Context context) {')
end = s.find('\n    private static void installBundledDatabase()', start)
if start < 0 or end < 0: raise SystemExit('init boundaries missing')
init_method = r'''    static synchronized void init(Context context) {
        if (helper != null) return;
        app = context.getApplicationContext();
        initError = "";
        try {
            openBundledDatabase();
            return;
        } catch (Throwable first) {
            initError = first.getClass().getSimpleName() + ": " + String.valueOf(first.getMessage());
        }
        try {
            helper = null;
            File target = app.getDatabasePath(DB_NAME);
            File tmp = new File(target.getAbsolutePath() + ".tmp");
            if (tmp.exists()) tmp.delete();
            if (target.exists()) target.delete();
            openBundledDatabase();
            initError = "";
        } catch (Throwable second) {
            helper = null;
            initError = second.getClass().getSimpleName() + ": " + String.valueOf(second.getMessage());
        }
    }

    private static void openBundledDatabase() {
        installBundledDatabase();
        Helper h = new Helper(app);
        SQLiteDatabase db = h.getReadableDatabase();
        int rows = scalar(db, "SELECT COUNT(*) FROM times");
        int films = scalar(db, "SELECT COUNT(*) FROM films");
        int devs = scalar(db, "SELECT COUNT(*) FROM developers");
        if (rows < 3000 || films < 250 || devs < 180) {
            try { h.close(); } catch (Exception ignored) {}
            throw new IllegalStateException("Database incluso incompleto: " + films + "/" + devs + "/" + rows);
        }
        helper = h;
    }

    static String initError() {
        return initError == null ? "" : initError;
    }
'''
s = s[:start] + init_method + s[end:]
p.write_text(s, encoding='utf-8')

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')
s = s.replace('''        MdcOfflineStore.init(getApplicationContext());
        repairLegacyInventoryFromOfflineDb();
        showHome();
        ensureOfflineDatabase();''',
'''        MdcOfflineStore.init(getApplicationContext());
        showHome();
        ensureOfflineDatabase();''', 1)

pattern = re.compile(r'''    private void ensureOfflineDatabase\(\) \{.*?\n    \}\n\n    @Override\n    public void onBackPressed\(\) \{''', re.S)
replacement = '''    private void ensureOfflineDatabase() {
        if (MdcOfflineStore.isReady()) return;
        String detail = MdcOfflineStore.initError();
        new AlertDialog.Builder(this)
                .setTitle("Database offline non disponibile")
                .setMessage("L'app si è aperta, ma il database incluso non è leggibile." +
                        (detail == null || detail.isEmpty() ? "" : " - Dettaglio: " + detail))
                .setPositiveButton("CHIUDI", null)
                .show();
    }

    @Override
    public void onBackPressed() {'''
s, n = pattern.subn(lambda m: replacement, s, count=1)
if n != 1: raise SystemExit('ensureOfflineDatabase v033 replacement failed')
p.write_text(s, encoding='utf-8')
print('v0.3.3 startup-safe patch applied')
