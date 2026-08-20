package it.darkroom.timer;

import android.content.Context;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Small self-contained JSON backup for the photographic LOG only. */
public final class BackupManager {
    private static final Pattern FORMAT = Pattern.compile("\\\"format\\\"\\s*:\\s*\\\"darkroom-timer-log\\\"");
    private static final Pattern PAYLOAD = Pattern.compile("\\\"payload\\\"\\s*:\\s*\\\"([^\\\"]*)\\\"");

    private BackupManager() {}

    public static String exportJson(Context context) {
        String raw = LogStore.exportPayload(context);
        String encoded = Base64.getEncoder().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
        return "{\n" +
                "  \"format\": \"darkroom-timer-log\",\n" +
                "  \"version\": 1,\n" +
                "  \"exportedAt\": " + System.currentTimeMillis() + ",\n" +
                "  \"payload\": \"" + encoded + "\"\n" +
                "}\n";
    }

    public static List<LogEntry> parseJson(String json) throws Exception {
        String raw = json == null ? "" : json;
        if (!FORMAT.matcher(raw).find()) throw new Exception("File non riconosciuto come backup Darkroom Timer");
        Matcher m = PAYLOAD.matcher(raw);
        if (!m.find()) throw new Exception("Backup privo di dati LOG");
        String payload;
        try {
            payload = new String(Base64.getDecoder().decode(m.group(1)), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new Exception("Backup danneggiato");
        }
        return LogStore.parsePayload(payload);
    }
}
