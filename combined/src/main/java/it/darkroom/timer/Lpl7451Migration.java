package it.darkroom.timer;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;

/** One-time migration from the previous enlarger-specific print state to JOBO/LPL 7451. */
public final class Lpl7451Migration {
    private static final String KEY_DONE = "lpl7451MigrationV046Done";

    private Lpl7451Migration() {}

    public static boolean run(Context context) {
        if (context == null) return false;
        SharedPreferences ui = context.getSharedPreferences("ui", Context.MODE_PRIVATE);
        if (ui.getBoolean(KEY_DONE, false)) return false;

        // All existing print cards and recipes were tied to the previous enlarger.
        LogStore.replaceAll(context, new ArrayList<LogEntry>());
        context.getSharedPreferences("log_reprint", Context.MODE_PRIVATE).edit().clear().apply();
        context.getSharedPreferences("log_session", Context.MODE_PRIVATE).edit().clear().apply();
        context.getSharedPreferences("print_revision", Context.MODE_PRIVATE).edit().clear().apply();

        ui.edit()
                .remove("exposureRecipe")
                .remove("printSequence")
                .remove("enlargementMeta")
                .remove("enlargementLastLog")
                .remove("enlargementReloadPending")
                .remove("enlargementPaperPlaneHeightMm")
                .remove("activeSourceLogId")
                .remove("lastSavedCycleAt")
                .remove("testBaseFilterType")
                .remove("testBaseFilterValue")
                .remove("splitProvinoReturnFilterType")
                .remove("splitProvinoReturnFilterValue")
                .remove("provinoFlow")
                .remove("splitProvinoSoftMs")
                .remove("splitProvinoSoftStrip")
                .remove("splitProvinoHardMs")
                .remove("splitProvinoHardStrip")
                .remove("splitProvinoReturnTestWidthMs")
                .putInt("splitProvinoSoftYellow", 60)
                .putInt("splitProvinoHardMagenta", 130)
                .putInt("enlargementUiNeg", 0)
                .putInt("enlargementUiFill", 0)
                .putInt("printWidthMs", 8500)
                .putInt("mode", 0)
                .putBoolean(KEY_DONE, true)
                .apply();
        return true;
    }
}
