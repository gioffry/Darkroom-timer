package it.darkroom.assistant;

import android.app.Application;
import android.content.SharedPreferences;

import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Migrazioni leggere dei dati locali tra build dell'Assistant. */
public class DarkroomAssistantApp extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        cleanupInvalidInventoryEntries();
    }

    private void cleanupInvalidInventoryEntries() {
        SharedPreferences p = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);
        Set<String> current = new HashSet<>(p.getStringSet("inventory", new HashSet<>()));
        Set<String> clean = new HashSet<>(current);
        SharedPreferences.Editor e = p.edit();
        boolean changed = false;

        for (String name : current) {
            if (!looksLikeEditorialGarbage(name)) continue;
            changed = true;
            clean.remove(name);
            String k = key(name);
            e.remove("opened_" + k)
                    .remove("prod_saved_" + k)
                    .remove("prod_name_" + k)
                    .remove("prod_roles_" + k)
                    .remove("prod_stock_" + k)
                    .remove("prod_film_" + k)
                    .remove("prod_paper_" + k)
                    .remove("prod_working_" + k)
                    .remove("prod_instructions_" + k)
                    .remove("prod_expiry_" + k)
                    .remove("prod_source_" + k)
                    .remove("prod_reuse_" + k)
                    .remove("prod_film_capacity_" + k)
                    .remove("prod_paper_capacity_" + k);
        }
        if (changed) {
            e.putStringSet("inventory", clean).apply();
        }
    }

    private boolean looksLikeEditorialGarbage(String name) {
        if (name == null || name.trim().isEmpty()) return true;
        String s = name.toLowerCase(Locale.ROOT);
        if (name.length() > 82) return true;
        String[] bad = {
                "essential guide", "camera basics", "film chemicals 20", "darkroom chemistry guide",
                "tutorial", "how to", "review", "best ", "top 10", "blog", "article", "comparison"
        };
        for (String x : bad) if (s.contains(x)) return true;
        return false;
    }

    private String key(String s) {
        return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "_");
    }
}
