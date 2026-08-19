from pathlib import Path
import re

# v0.3.1: il database completo viene generato in CI e incluso come asset SQLite.
# Sul telefono non avviene più alcuno scarico iniziale: il DB viene copiato
# dall'APK nella directory databases e poi usato interamente offline.

p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')

s = s.replace('private static final String DB_NAME = "mdc_offline.sqlite";',
              'private static final String DB_NAME = "mdc_offline_v031.sqlite";', 1)

# imports needed for copying packaged DB
if 'import java.io.File;' not in s:
    s = s.replace('import java.io.BufferedReader;','import java.io.BufferedReader;\nimport java.io.File;\nimport java.io.FileOutputStream;\nimport java.io.OutputStream;')

old = '''    static synchronized void init(Context context) {
        if (helper != null) return;
        app = context.getApplicationContext();
        helper = new Helper(app);
        helper.getWritableDatabase();
    }'''
new = '''    static synchronized void init(Context context) {
        if (helper != null) return;
        app = context.getApplicationContext();
        installBundledDatabase();
        helper = new Helper(app);
        helper.getReadableDatabase();
    }

    private static void installBundledDatabase() {
        File target = app.getDatabasePath(DB_NAME);
        try {
            if (target.exists() && target.length() > 250000L) return;
            File parent = target.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();
            File tmp = new File(target.getAbsolutePath() + ".tmp");
            if (tmp.exists()) tmp.delete();
            try (InputStream in = app.getAssets().open("mdc_full.sqlite");
                 OutputStream out = new FileOutputStream(tmp)) {
                byte[] buf = new byte[65536];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                out.flush();
            }
            if (target.exists()) target.delete();
            if (!tmp.renameTo(target)) {
                throw new IllegalStateException("Impossibile installare il database incluso nell'APK");
            }
        } catch (Exception e) {
            throw new IllegalStateException("Database offline incluso non disponibile: " + e.getMessage(), e);
        }
    }'''
if old not in s:
    raise SystemExit('MdcOfflineStore init marker not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')

# Activity: nessun popup di sincronizzazione, perché il database è già nell'APK.
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

pattern = re.compile(r'''    private void ensureOfflineDatabase\(\) \{.*?\n    \}\n\n    @Override\n    public void onBackPressed\(\) \{''', re.S)
replacement = '''    private void ensureOfflineDatabase() {
        if (MdcOfflineStore.isReady()) return;
        new AlertDialog.Builder(this)
                .setTitle("Database offline non disponibile")
                .setMessage("Il database incluso nell'APK non risulta leggibile. Reinstalla questa versione dell'app.")
                .setPositiveButton("CHIUDI", null)
                .show();
    }

    @Override
    public void onBackPressed() {'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('ensureOfflineDatabase replacement failed')

# Wording coherent with bundled DB
s = s.replace('Database offline pronto', 'Database offline incluso pronto')
s = s.replace('copia offline personale', 'database offline incluso')

p.write_text(s, encoding='utf-8')
print('v0.3.1 bundled SQLite patch applied')
