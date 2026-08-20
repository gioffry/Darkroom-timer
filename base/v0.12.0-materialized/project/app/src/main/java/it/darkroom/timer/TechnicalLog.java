package it.darkroom.timer;

import android.content.Context;

import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Small local black-box log of actual MINIR2 observations. Keeps the latest 20 sessions. */
public final class TechnicalLog {
    private static final String PREFS = "technical_log";
    private static final String KEY = "events_v1";
    private static final int MAX_SESSIONS = 20;
    private static final Object LOCK = new Object();
    private static final ExecutorService WRITER = Executors.newSingleThreadExecutor();

    private TechnicalLog() {}

    public static long startSession(Context context, String description) {
        long id = System.currentTimeMillis();
        add(context, id, "SESSIONE — " + (description == null ? "" : description));
        return id;
    }

    public static void add(Context context, long sessionId, String message) {
        if (context == null || sessionId <= 0) return;
        final Context app = context.getApplicationContext();
        final long when = System.currentTimeMillis();
        final String msg = message == null ? "" : message;
        WRITER.execute(() -> {
            synchronized (LOCK) {
                List<Event> events = loadEvents(app);
                events.add(new Event(sessionId, when, msg));
                pruneAndWrite(app, events);
            }
        });
    }

    public static String formatForDisplay(Context context) {
        synchronized (LOCK) {
            List<Event> events = loadEvents(context);
            if (events.isEmpty()) return "Nessun ciclo tecnico registrato.";

            ArrayList<Long> sessions = new ArrayList<>();
            HashSet<Long> seen = new HashSet<>();
            for (int i = events.size() - 1; i >= 0; i--) {
                long id = events.get(i).sessionId;
                if (seen.add(id)) sessions.add(id);
            }

            StringBuilder out = new StringBuilder();
            SimpleDateFormat day = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.ITALY);
            SimpleDateFormat time = new SimpleDateFormat("HH:mm:ss.SSS", Locale.ITALY);
            for (long id : sessions) {
                if (out.length() > 0) out.append("\n\n");
                out.append("SESSIONE ").append(day.format(new Date(id))).append('\n');
                for (Event e : events) {
                    if (e.sessionId != id) continue;
                    out.append(time.format(new Date(e.timestamp))).append("  ").append(e.message).append('\n');
                }
            }
            return out.toString().trim();
        }
    }

    public static void clear(Context context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().remove(KEY).apply();
    }

    private static void pruneAndWrite(Context context, List<Event> events) {
        Set<Long> keep = new HashSet<>();
        for (int i = events.size() - 1; i >= 0 && keep.size() < MAX_SESSIONS; i--) {
            keep.add(events.get(i).sessionId);
        }
        ArrayList<Event> pruned = new ArrayList<>();
        for (Event e : events) if (keep.contains(e.sessionId)) pruned.add(e);

        StringBuilder raw = new StringBuilder();
        for (Event e : pruned) {
            if (raw.length() > 0) raw.append('\n');
            raw.append(e.sessionId).append('\t').append(e.timestamp).append('\t').append(enc(e.message));
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, raw.toString()).apply();
    }

    private static List<Event> loadEvents(Context context) {
        ArrayList<Event> result = new ArrayList<>();
        String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, "");
        if (raw == null || raw.isEmpty()) return result;
        for (String row : raw.split("\\n")) {
            try {
                String[] f = row.split("\\t", 3);
                if (f.length != 3) continue;
                result.add(new Event(Long.parseLong(f[0]), Long.parseLong(f[1]), dec(f[2])));
            } catch (Exception ignored) {}
        }
        return result;
    }

    private static String enc(String value) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString((value == null ? "" : value).getBytes(StandardCharsets.UTF_8));
    }

    private static String dec(String value) {
        if (value == null || value.isEmpty()) return "";
        return new String(Base64.getUrlDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static final class Event {
        final long sessionId;
        final long timestamp;
        final String message;
        Event(long sessionId, long timestamp, String message) {
            this.sessionId = sessionId;
            this.timestamp = timestamp;
            this.message = message;
        }
    }
}
