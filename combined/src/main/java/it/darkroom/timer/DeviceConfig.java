package it.darkroom.timer;

import android.content.Context;
import android.content.SharedPreferences;

public final class DeviceConfig {
    private static final String PREFS = "sonoff_diy";
    public final String host;
    public final int port;
    public final String deviceId;

    public DeviceConfig(String host, int port, String deviceId) {
        this.host = host;
        this.port = port;
        this.deviceId = deviceId;
    }

    public boolean isValid() {
        return host != null && !host.trim().isEmpty() && port > 0 && deviceId != null && !deviceId.trim().isEmpty();
    }

    public void save(Context c) {
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("host", host)
                .putInt("port", port)
                .putString("deviceId", deviceId)
                .apply();
    }

    public static DeviceConfig load(Context c) {
        SharedPreferences p = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return new DeviceConfig(p.getString("host", ""), p.getInt("port", 0), p.getString("deviceId", ""));
    }
}
