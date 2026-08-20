package it.darkroom.timer.assistant.data;

/** Darkroom Assistant R7+R8+R9 schema. Upgrade from v2 is additive only. */
public final class AssistantDataSchema {
    public static final String DB_NAME = "darkroom_assistant.db";
    public static final int VERSION = 3;

    public static final String CREATE_RECIPES =
            "CREATE TABLE IF NOT EXISTS personal_recipes (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,combo_key TEXT NOT NULL,film TEXT NOT NULL,format TEXT NOT NULL," +
            "nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL,dilution TEXT NOT NULL," +
            "processor TEXT NOT NULL,method TEXT NOT NULL,original_temp REAL NOT NULL,original_seconds INTEGER NOT NULL," +
            "source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL," +
            "personal_temp REAL NOT NULL,personal_seconds INTEGER NOT NULL,note TEXT NOT NULL DEFAULT ''," +
            "favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1)),created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)";

    public static final String CREATE_LOGS =
            "CREATE TABLE IF NOT EXISTS development_logs (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,combo_key TEXT NOT NULL,film TEXT NOT NULL," +
            "format TEXT NOT NULL,nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL," +
            "dilution TEXT NOT NULL,actual_temp REAL NOT NULL,processor TEXT NOT NULL,method TEXT NOT NULL," +
            "actual_seconds INTEGER NOT NULL,time_origin TEXT NOT NULL,source_seconds INTEGER NOT NULL,source_temp REAL NOT NULL," +
            "source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL," +
            "volume_ml REAL NOT NULL DEFAULT 0,product_ml REAL NOT NULL DEFAULT 0,water_ml REAL NOT NULL DEFAULT 0," +
            "product_known INTEGER NOT NULL DEFAULT 0 CHECK(product_known IN (0,1))," +
            "water_known INTEGER NOT NULL DEFAULT 0 CHECK(water_known IN (0,1))," +
            "rolls INTEGER NOT NULL DEFAULT 1,capacity_state TEXT NOT NULL DEFAULT '',capacity_message TEXT NOT NULL DEFAULT ''," +
            "rating INTEGER NOT NULL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5),notes TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_CHEMICALS =
            "CREATE TABLE IF NOT EXISTS chemical_inventory (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL," +
            "source_type TEXT NOT NULL,source_product_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT ''," +
            "name TEXT NOT NULL,category TEXT NOT NULL,physical_state TEXT NOT NULL,solution_type TEXT NOT NULL," +
            "initial_amount REAL NOT NULL DEFAULT 0,remaining_amount REAL NOT NULL DEFAULT 0,unit TEXT NOT NULL," +
            "purchase_date TEXT NOT NULL DEFAULT '',open_date TEXT NOT NULL DEFAULT '',prepared_date TEXT NOT NULL DEFAULT ''," +
            "expiry_date TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',storage TEXT NOT NULL DEFAULT ''," +
            "personal_dilution TEXT NOT NULL DEFAULT '',documented_dilutions TEXT NOT NULL DEFAULT ''," +
            "capacity_value REAL NOT NULL DEFAULT 0,capacity_unit TEXT NOT NULL DEFAULT '',capacity_source TEXT NOT NULL DEFAULT ''," +
            "source_name TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '',archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)))";

    public static final String CREATE_CHEMICAL_USAGE =
            "CREATE TABLE IF NOT EXISTS chemical_usage (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,chemical_id INTEGER NOT NULL," +
            "development_log_id INTEGER NOT NULL DEFAULT 0,product_name TEXT NOT NULL,developer TEXT NOT NULL DEFAULT ''," +
            "dilution TEXT NOT NULL DEFAULT '',film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0," +
            "quantity_used REAL NOT NULL,unit TEXT NOT NULL,remaining_after REAL NOT NULL,note TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_EQUIPMENT =
            "CREATE TABLE IF NOT EXISTS personal_equipment (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL," +
            "category TEXT NOT NULL,source_type TEXT NOT NULL,source_model_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT ''," +
            "model TEXT NOT NULL,personal_name TEXT NOT NULL DEFAULT '',quantity_owned INTEGER NOT NULL DEFAULT 1,notes TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_TANKS =
            "CREATE TABLE IF NOT EXISTS personal_tanks (" +
            "equipment_id INTEGER PRIMARY KEY,system TEXT NOT NULL DEFAULT '',tank_type TEXT NOT NULL DEFAULT ''," +
            "capacity_35 INTEGER NOT NULL DEFAULT 0,capacity_120 INTEGER NOT NULL DEFAULT 0," +
            "min_inversion_ml REAL NOT NULL DEFAULT 0,min_rotation_ml REAL NOT NULL DEFAULT 0,max_volume_ml REAL NOT NULL DEFAULT 0," +
            "cpe2_compatible INTEGER NOT NULL DEFAULT 0,lift_compatible INTEGER NOT NULL DEFAULT 0," +
            "technical_source TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_ASSISTANT_SESSIONS =
            "CREATE TABLE IF NOT EXISTS assistant_sessions (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL," +
            "session_key TEXT NOT NULL UNIQUE,film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0," +
            "cycle_index INTEGER NOT NULL DEFAULT 0,phase_index INTEGER NOT NULL DEFAULT 0,planned_seconds INTEGER," +
            "actual_seconds INTEGER,temperature REAL,tank_snapshot TEXT NOT NULL DEFAULT '',chemistry_snapshot TEXT NOT NULL DEFAULT ''," +
            "state TEXT NOT NULL DEFAULT '',personal_phase_times TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_PAPER_SESSIONS =
            "CREATE TABLE IF NOT EXISTS paper_chemistry_sessions (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1))," +
            "paper TEXT NOT NULL DEFAULT '',developer TEXT NOT NULL DEFAULT '',developer_dilution TEXT NOT NULL DEFAULT ''," +
            "stop_product TEXT NOT NULL DEFAULT '',stop_dilution TEXT NOT NULL DEFAULT '',fixer TEXT NOT NULL DEFAULT '',fixer_dilution TEXT NOT NULL DEFAULT ''," +
            "volume_ml REAL,capacity_state TEXT NOT NULL DEFAULT '',source_snapshot TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '')";

    public static final String CREATE_TECHNICAL_SOURCE_CACHE =
            "CREATE TABLE IF NOT EXISTS technical_source_cache (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT,catalog_version INTEGER NOT NULL,source_key TEXT NOT NULL UNIQUE," +
            "origin_type TEXT NOT NULL,title TEXT NOT NULL DEFAULT '',author TEXT NOT NULL DEFAULT '',reference TEXT NOT NULL DEFAULT ''," +
            "url TEXT NOT NULL DEFAULT '',document_version TEXT NOT NULL DEFAULT '',adaptation_note TEXT NOT NULL DEFAULT ''," +
            "payload TEXT NOT NULL DEFAULT '',updated_at INTEGER NOT NULL)";

    public static final String CREATE_FAVORITE_INDEX =
            "CREATE UNIQUE INDEX IF NOT EXISTS one_favorite_per_combo ON personal_recipes(combo_key) WHERE favorite=1";
    public static final String CREATE_LOG_COMBO_INDEX =
            "CREATE INDEX IF NOT EXISTS logs_by_combo_date ON development_logs(combo_key, created_at)";
    public static final String CREATE_CHEM_NAME_INDEX =
            "CREATE INDEX IF NOT EXISTS chemistry_by_name ON chemical_inventory(name, archived)";
    public static final String CREATE_USAGE_INDEX =
            "CREATE INDEX IF NOT EXISTS chemistry_usage_by_item ON chemical_usage(chemical_id, created_at)";
    public static final String CREATE_TANK_INDEX =
            "CREATE INDEX IF NOT EXISTS equipment_by_category ON personal_equipment(category, updated_at)";
    public static final String CREATE_SESSION_INDEX =
            "CREATE INDEX IF NOT EXISTS assistant_sessions_by_updated ON assistant_sessions(updated_at)";
    public static final String CREATE_PAPER_SESSION_INDEX =
            "CREATE INDEX IF NOT EXISTS paper_sessions_by_date ON paper_chemistry_sessions(created_at)";
    public static final String CREATE_SOURCE_CACHE_INDEX =
            "CREATE INDEX IF NOT EXISTS technical_sources_by_catalog ON technical_source_cache(catalog_version, source_key)";

    public static final String CREATE_ORIGINAL_IMMUTABLE_TRIGGER =
            "CREATE TRIGGER IF NOT EXISTS recipes_original_immutable BEFORE UPDATE OF combo_key,film,format,nominal_iso,exposed_iso,developer,dilution," +
            "processor,method,original_temp,original_seconds,source_name,data_type,source_data,calculation ON personal_recipes BEGIN " +
            "SELECT RAISE(ABORT, 'ORIGINALE FONTE immutabile'); END";

    private AssistantDataSchema() {}
}
