package it.darkroom.assistant;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.text.Normalizer;
import java.util.Locale;

/**
 * Database tecnico SEPARATO da Massive Dev Chart.
 *
 * Contratto v0.3.9:
 * - qui vivono solo fatti generali del prodotto: preparazione, durata,
 *   conservazione, capacita' e note in italiano;
 * - NON contiene tempi, ISO, temperatura o diluizione della combinazione
 *   pellicola/rivelatore;
 * - la combinazione di sviluppo resta di esclusiva competenza di
 *   MdcOfflineStore / DevTimeEngine.
 */
final class ChemicalTechnicalStore {
    private static final String ASSET_NAME = "chemical_specs.sqlite";
    private static final String DB_NAME = "chemical_specs_v039.sqlite";
    private static SQLiteDatabase db;
    private static String initError = "";

    static final class Sheet {
        final String name;
        final String manufacturer;
        final String productTypeIt;
        final String formIt;
        final String preparationIt;
        final String shelfUnopenedIt;
        final String shelfOpenedIt;
        final String shelfStockIt;
        final String shelfWorkingIt;
        final String storageIt;
        final String capacityIt;
        final String notesIt;
        final String sourceName;
        final String sourceUrl;
        final String sourceDate;
        final boolean verified;

        Sheet(String name, String manufacturer, String productTypeIt, String formIt,
              String preparationIt, String shelfUnopenedIt, String shelfOpenedIt,
              String shelfStockIt, String shelfWorkingIt, String storageIt,
              String capacityIt, String notesIt, String sourceName, String sourceUrl,
              String sourceDate, boolean verified) {
            this.name = nz(name);
            this.manufacturer = nz(manufacturer);
            this.productTypeIt = nz(productTypeIt);
            this.formIt = nz(formIt);
            this.preparationIt = nz(preparationIt);
            this.shelfUnopenedIt = nz(shelfUnopenedIt);
            this.shelfOpenedIt = nz(shelfOpenedIt);
            this.shelfStockIt = nz(shelfStockIt);
            this.shelfWorkingIt = nz(shelfWorkingIt);
            this.storageIt = nz(storageIt);
            this.capacityIt = nz(capacityIt);
            this.notesIt = nz(notesIt);
            this.sourceName = nz(sourceName);
            this.sourceUrl = nz(sourceUrl);
            this.sourceDate = nz(sourceDate);
            this.verified = verified;
        }

        boolean hasTechnicalDetails() {
            return verified && (!preparationIt.isEmpty() || !shelfUnopenedIt.isEmpty() ||
                    !shelfWorkingIt.isEmpty() || !storageIt.isEmpty() ||
                    !capacityIt.isEmpty() || !notesIt.isEmpty());
        }
    }

    private ChemicalTechnicalStore() {}

    static synchronized void init(Context context) {
        if (db != null && db.isOpen()) return;
        initError = "";
        try {
            File target = context.getDatabasePath(DB_NAME);
            File parent = target.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs())
                throw new IllegalStateException("Impossibile creare directory database");
            if (!target.exists() || target.length() < 4096) copyAsset(context, target);
            db = SQLiteDatabase.openDatabase(target.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY);
            if (!isValid(db)) {
                try { db.close(); } catch (Exception ignored) {}
                db = null;
                if (target.exists()) target.delete();
                copyAsset(context, target);
                db = SQLiteDatabase.openDatabase(target.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY);
                if (!isValid(db)) throw new IllegalStateException("Database tecnico non valido");
            }
        } catch (Throwable t) {
            if (db != null) try { db.close(); } catch (Exception ignored) {}
            db = null;
            initError = t.getClass().getSimpleName() + ": " + String.valueOf(t.getMessage());
        }
    }

    static String initError() {
        return initError == null ? "" : initError;
    }

    static Sheet lookup(Context context, String productName) {
        if (productName == null || productName.trim().isEmpty()) return null;
        init(context.getApplicationContext());
        if (db == null || !db.isOpen()) return null;
        String n = norm(productName);
        String productNorm = null;
        try (Cursor c = db.rawQuery(
                "SELECT product_norm FROM aliases WHERE alias_norm=? LIMIT 1",
                new String[]{n})) {
            if (c.moveToFirst()) productNorm = c.getString(0);
        }
        if (productNorm == null || productNorm.isEmpty()) productNorm = n;
        try (Cursor c = db.rawQuery(
                "SELECT name,manufacturer,product_type_it,form_it,preparation_it," +
                        "shelf_unopened_it,shelf_opened_it,shelf_stock_it,shelf_working_it," +
                        "storage_it,capacity_it,notes_it,source_name,source_url,source_date,verified " +
                        "FROM products WHERE norm_name=? LIMIT 1",
                new String[]{productNorm})) {
            if (!c.moveToFirst()) return null;
            return new Sheet(
                    c.getString(0), c.getString(1), c.getString(2), c.getString(3),
                    c.getString(4), c.getString(5), c.getString(6), c.getString(7),
                    c.getString(8), c.getString(9), c.getString(10), c.getString(11),
                    c.getString(12), c.getString(13), c.getString(14), c.getInt(15) == 1);
        } catch (Exception e) {
            return null;
        }
    }

    private static boolean isValid(SQLiteDatabase candidate) {
        if (candidate == null || !candidate.isOpen()) return false;
        try (Cursor c = candidate.rawQuery("SELECT COUNT(*) FROM products", null)) {
            if (!c.moveToFirst() || c.getInt(0) < 180) return false;
        }
        try (Cursor c = candidate.rawQuery("SELECT COUNT(*) FROM products WHERE verified=1", null)) {
            return c.moveToFirst() && c.getInt(0) >= 8;
        }
    }

    private static void copyAsset(Context context, File target) throws Exception {
        File tmp = new File(target.getAbsolutePath() + ".tmp");
        if (tmp.exists()) tmp.delete();
        try (InputStream in = context.getAssets().open(ASSET_NAME);
             FileOutputStream out = new FileOutputStream(tmp)) {
            byte[] buf = new byte[32768];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            out.getFD().sync();
        }
        if (target.exists() && !target.delete())
            throw new IllegalStateException("Impossibile sostituire database tecnico");
        if (!tmp.renameTo(target))
            throw new IllegalStateException("Impossibile installare database tecnico");
    }

    private static String norm(String value) {
        String s = Normalizer.normalize(value == null ? "" : value, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT)
                .replace('–', ' ').replace('—', ' ').replace('-', ' ');
        return s.replaceAll("[^\\p{L}\\p{N}_+]+", " ").replaceAll("\\s+", " ").trim();
    }

    private static String nz(String s) { return s == null ? "" : s; }
}
