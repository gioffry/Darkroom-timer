package it.darkroom.timer;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Minimal implementation of the SONOFF DIY REST API used by this app. */
public final class SonoffHttp {
    private static final Object RATE_LOCK = new Object();
    private static long lastRequestAt = 0L;
    private static final long MIN_REQUEST_GAP_MS = 225L;
    private static final Pattern ERROR = Pattern.compile("\\\"error\\\"\\s*:\\s*(-?\\d+)");
    private static final Pattern SWITCH = Pattern.compile("\\\"switch\\\"\\s*:\\s*\\\"(on|off)\\\"");
    private static final Pattern PULSE = Pattern.compile("\\\"pulse\\\"\\s*:\\s*\\\"(on|off)\\\"");
    private static final Pattern PULSE_WIDTH = Pattern.compile("\\\"pulseWidth\\\"\\s*:\\s*(\\d+)");

    private SonoffHttp() {}

    public static String info(DeviceConfig d) throws Exception {
        return infoWithTimeout(d, 5000);
    }

    /** Short probe used only by the idle UI heartbeat; exposure timing never depends on it. */
    public static String infoQuick(DeviceConfig d, int timeoutMs) throws Exception {
        return infoWithTimeout(d, Math.max(500, timeoutMs));
    }

    public static class Status {
        public final String switchState;
        public final String pulseState;
        public final int pulseWidthMs;

        Status(String switchState, String pulseState, int pulseWidthMs) {
            this.switchState = switchState;
            this.pulseState = pulseState;
            this.pulseWidthMs = pulseWidthMs;
        }
    }

    public static final class TimedStatus extends Status {
        public final long requestStartedAt;
        public final long responseReceivedAt;

        TimedStatus(String switchState, String pulseState, int pulseWidthMs, long requestStartedAt, long responseReceivedAt) {
            super(switchState, pulseState, pulseWidthMs);
            this.requestStartedAt = requestStartedAt;
            this.responseReceivedAt = responseReceivedAt;
        }

        public long midpointAt() {
            if (requestStartedAt <= 0L || responseReceivedAt <= 0L) return System.currentTimeMillis();
            return requestStartedAt + Math.max(0L, (responseReceivedAt - requestStartedAt) / 2L);
        }
    }

    private static String infoWithTimeout(DeviceConfig d, int timeoutMs) throws Exception {
        String response = post(d, "/zeroconf/info", "{}", timeoutMs);
        Matcher sw = SWITCH.matcher(response);
        if (!sw.find()) throw new Exception("Stato switch non presente nella risposta SONOFF");
        return sw.group(1);
    }

    public static Status infoStatus(DeviceConfig d) throws Exception {
        return infoStatusWithTimeout(d, 5000);
    }

    public static TimedStatus infoStatusTimed(DeviceConfig d) throws Exception {
        return infoStatusTimed(d, 5000);
    }

    public static TimedStatus infoStatusTimed(DeviceConfig d, int timeoutMs) throws Exception {
        return infoStatusWithTimeout(d, timeoutMs);
    }

    private static TimedStatus infoStatusWithTimeout(DeviceConfig d, int timeoutMs) throws Exception {
        TimedResponse timed = postTimed(d, "/zeroconf/info", "{}", timeoutMs);
        String response = timed.body;

        Matcher sw = SWITCH.matcher(response);
        if (!sw.find()) throw new Exception("Stato switch non presente nella risposta SONOFF");

        Matcher pulse = PULSE.matcher(response);
        if (!pulse.find()) throw new Exception("Stato Inching non presente nella risposta SONOFF");

        int pulseWidth = -1;
        Matcher width = PULSE_WIDTH.matcher(response);
        if (width.find()) {
            try { pulseWidth = Integer.parseInt(width.group(1)); } catch (Exception ignored) {}
        }

        return new TimedStatus(sw.group(1), pulse.group(1), pulseWidth, timed.startedAt, timed.endedAt);
    }

    public static void pulseOn(DeviceConfig d, int widthMs) throws Exception {
        post(d, "/zeroconf/pulse", "{\"pulse\":\"on\",\"pulseWidth\":" + widthMs + "}", 5000);
    }

    public static void pulseOff(DeviceConfig d) throws Exception {
        post(d, "/zeroconf/pulse", "{\"pulse\":\"off\"}", 5000);
    }

    public static void switchOn(DeviceConfig d) throws Exception {
        post(d, "/zeroconf/switch", "{\"switch\":\"on\"}", 5000);
    }

    public static void switchOff(DeviceConfig d) throws Exception {
        post(d, "/zeroconf/switch", "{\"switch\":\"off\"}", 5000);
    }

    private static String post(DeviceConfig d, String path, String dataJson, int timeoutMs) throws Exception {
        return postTimed(d, path, dataJson, timeoutMs).body;
    }

    private static TimedResponse postTimed(DeviceConfig d, String path, String dataJson, int timeoutMs) throws Exception {
        synchronized (RATE_LOCK) {
            long now = System.currentTimeMillis();
            long wait = MIN_REQUEST_GAP_MS - (now - lastRequestAt);
            if (wait > 0) Thread.sleep(wait);
            lastRequestAt = System.currentTimeMillis();

            String host = d.host.contains(":") ? "[" + d.host + "]" : d.host;
            URL url = new URL("http://" + host + ":" + d.port + path);
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setRequestMethod("POST");
            c.setConnectTimeout(timeoutMs);
            c.setReadTimeout(timeoutMs);
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            c.setRequestProperty("Connection", "close");

            String body = "{\"deviceid\":\"" + escape(d.deviceId) + "\",\"data\":" + dataJson + "}";
            byte[] bytes = body.getBytes("UTF-8");
            c.setFixedLengthStreamingMode(bytes.length);
            long startedAt = System.currentTimeMillis();
            try (OutputStream os = c.getOutputStream()) {
                os.write(bytes);
            }

            int code = c.getResponseCode();
            InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
            String text = readAll(in);
            long endedAt = System.currentTimeMillis();
            c.disconnect();
            if (code != 200) throw new Exception("HTTP " + code + (text.isEmpty() ? "" : ": " + text));

            Matcher error = ERROR.matcher(text);
            if (!error.find()) throw new Exception("Risposta SONOFF non valida");
            int value = Integer.parseInt(error.group(1));
            if (value != 0) throw new Exception("SONOFF error " + value);
            return new TimedResponse(text, startedAt, endedAt);
        }
    }

    private static String escape(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static String readAll(InputStream in) throws Exception {
        if (in == null) return "";
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        }
        return b.toString();
    }

    private static final class TimedResponse {
        final String body;
        final long startedAt;
        final long endedAt;

        TimedResponse(String body, long startedAt, long endedAt) {
            this.body = body == null ? "" : body;
            this.startedAt = startedAt;
            this.endedAt = endedAt;
        }
    }
}
