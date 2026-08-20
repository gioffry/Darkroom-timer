package it.darkroom.timer;

import android.content.Context;
import android.content.SharedPreferences;

public final class SafelightConfig {
    private static final String PREFS = "safelight_diy";
    private SafelightConfig() {}

    public static DeviceConfig load(Context c) {
        SharedPreferences p = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return new DeviceConfig(p.getString("host", ""), p.getInt("port", 0), p.getString("deviceId", ""));
    }

    public static void save(Context c, DeviceConfig d) {
        if (d == null) { clear(c); return; }
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("host", d.host == null ? "" : d.host)
                .putInt("port", d.port)
                .putString("deviceId", d.deviceId == null ? "" : d.deviceId)
                .apply();
    }

    public static void clear(Context c) {
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply();
    }
}
