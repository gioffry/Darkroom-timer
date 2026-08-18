package it.darkroom.timer.assistant.data;

/** Versioned local schema for Darkroom Assistant personal data. */
public final class AssistantDataSchema {
    public static final String DB_NAME = "darkroom_assistant.db";
    public static final int VERSION = 1;

    public static final String CREATE_RECIPES =
            "CREATE TABLE IF NOT EXISTS personal_recipes (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT," +
            "combo_key TEXT NOT NULL," +
            "film TEXT NOT NULL," +
            "format TEXT NOT NULL," +
            "nominal_iso INTEGER NOT NULL," +
            "exposed_iso INTEGER NOT NULL," +
            "developer TEXT NOT NULL," +
            "dilution TEXT NOT NULL," +
            "processor TEXT NOT NULL," +
            "method TEXT NOT NULL," +
            "original_temp REAL NOT NULL," +
            "original_seconds INTEGER NOT NULL," +
            "source_name TEXT NOT NULL," +
            "data_type TEXT NOT NULL," +
            "source_data TEXT NOT NULL," +
            "calculation TEXT NOT NULL," +
            "personal_temp REAL NOT NULL," +
            "personal_seconds INTEGER NOT NULL," +
            "note TEXT NOT NULL DEFAULT ''," +
            "favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1))," +
            "created_at INTEGER NOT NULL," +
            "updated_at INTEGER NOT NULL" +
            ")";

    public static final String CREATE_LOGS =
            "CREATE TABLE IF NOT EXISTS development_logs (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT," +
            "created_at INTEGER NOT NULL," +
            "combo_key TEXT NOT NULL," +
            "film TEXT NOT NULL," +
            "format TEXT NOT NULL," +
            "nominal_iso INTEGER NOT NULL," +
            "exposed_iso INTEGER NOT NULL," +
            "developer TEXT NOT NULL," +
            "dilution TEXT NOT NULL," +
            "actual_temp REAL NOT NULL," +
            "processor TEXT NOT NULL," +
            "method TEXT NOT NULL," +
            "actual_seconds INTEGER NOT NULL," +
            "time_origin TEXT NOT NULL," +
            "source_seconds INTEGER NOT NULL," +
            "source_temp REAL NOT NULL," +
            "source_name TEXT NOT NULL," +
            "data_type TEXT NOT NULL," +
            "source_data TEXT NOT NULL," +
            "calculation TEXT NOT NULL," +
            "volume_ml REAL NOT NULL DEFAULT 0," +
            "product_ml REAL NOT NULL DEFAULT 0," +
            "water_ml REAL NOT NULL DEFAULT 0," +
            "rolls INTEGER NOT NULL DEFAULT 1," +
            "capacity_state TEXT NOT NULL DEFAULT ''," +
            "capacity_message TEXT NOT NULL DEFAULT ''," +
            "rating INTEGER NOT NULL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5)," +
            "notes TEXT NOT NULL DEFAULT ''" +
            ")";

    public static final String CREATE_FAVORITE_INDEX =
            "CREATE UNIQUE INDEX IF NOT EXISTS one_favorite_per_combo " +
            "ON personal_recipes(combo_key) WHERE favorite=1";

    public static final String CREATE_LOG_COMBO_INDEX =
            "CREATE INDEX IF NOT EXISTS logs_by_combo_date " +
            "ON development_logs(combo_key, created_at)";

    /**
     * The source snapshot is immutable by construction: any attempt to alter the
     * combination or source/original fields aborts at SQLite level.
     */
    public static final String CREATE_ORIGINAL_IMMUTABLE_TRIGGER =
            "CREATE TRIGGER IF NOT EXISTS recipes_original_immutable " +
            "BEFORE UPDATE OF combo_key,film,format,nominal_iso,exposed_iso,developer,dilution," +
            "processor,method,original_temp,original_seconds,source_name,data_type,source_data,calculation " +
            "ON personal_recipes BEGIN " +
            "SELECT RAISE(ABORT, 'ORIGINALE FONTE immutabile'); END";

    private AssistantDataSchema() {}
}
