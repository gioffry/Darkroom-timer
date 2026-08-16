package it.darkroom.timer;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.IBinder;
import android.os.PowerManager;

import java.util.Locale;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Foreground service used while the phone screen may be off.
 * Exposure duration is always enforced by MINIR2 Inching, never by Android.
 */
public final class SonoffArmService extends Service {
    public static final String ACTION_ARM_PRINT = "it.darkroom.timer.ARM_PRINT";
    public static final String ACTION_ARM_TEST = "it.darkroom.timer.ARM_TEST";
    public static final String ACTION_DISARM = "it.darkroom.timer.DISARM";
    public static final String ACTION_CANCEL = "it.darkroom.timer.CANCEL";
    public static final String BROADCAST_STATE = "it.darkroom.timer.STATE";
    public static final String EXTRA_WIDTH = "width_ms";
    public static final String EXTRA_COUNT = "count";
    public static final String EXTRA_PAUSE = "pause_ms";
    public static final String EXTRA_STATE = "state";
    public static final String EXTRA_MESSAGE = "message";

    public static final String STATE_ARMING = "ARMING";
    public static final String STATE_ARMED = "ARMED";
    public static final String STATE_EXPOSING = "EXPOSING";
    public static final String STATE_PAUSING = "PAUSING";
    public static final String STATE_DISARMING = "DISARMING";
    public static final String STATE_NORMAL = "NORMAL";
    public static final String STATE_ERROR = "ERROR";

    private static final int MODE_PRINT = 0;
    private static final int MODE_TEST = 1;
    private static final String CHANNEL = "darkroom_timer_armed";
    private static final int NOTIFICATION_ID = 8501;
    private static final String STATE_PREFS = "runtime_state";
    private static final String KEY_STATE = "state";
    private static final String KEY_MESSAGE = "message";
    private static final String SESSION_PREFS = "log_session";

    private final ScheduledExecutorService io = Executors.newSingleThreadScheduledExecutor();
    private ScheduledFuture<?> pollTask;
    private ScheduledFuture<?> nextTask;
    private final AtomicBoolean seenOn = new AtomicBoolean(false);
    private final AtomicBoolean completing = new AtomicBoolean(false);
    private PowerManager.WakeLock wakeLock;
    private volatile DeviceConfig device;
    private volatile int mode = MODE_PRINT;
    private volatile int widthMs = 8500;
    private volatile int count = 7;
    private volatile int pauseMs = 2000;
    private volatile int completed = 0;
    private volatile long techSessionId = 0L;
    private volatile long lastObservedOnAt = 0L;
    private volatile long lastObservedOffAt = 0L;

    @Override public void onCreate() {
        super.onCreate();
        ensureNotificationChannel();
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_NOT_STICKY;
        String action = intent.getAction();
        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {
            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;
            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));
            count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));
            pauseMs = sanitizePause(intent.getIntExtra(EXTRA_PAUSE, 2000));
            device = DeviceConfig.load(this);
            techSessionId = TechnicalLog.startSession(this, mode == MODE_PRINT
                    ? "STAMPA richiesta " + seconds(widthMs)
                    : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs));
            lastObservedOnAt = 0L;
            lastObservedOffAt = 0L;
            startForeground(NOTIFICATION_ID, notification("Preparazione…"));
            acquireWakeLock();
            broadcast(STATE_ARMING, mode == MODE_PRINT
                    ? "Imposto Inching a " + seconds(widthMs)
                    : "Preparo provino: " + count + " × " + seconds(widthMs));
            io.execute(this::armInternal);
        } else if (ACTION_CANCEL.equals(action)) {
            // Stop any pending automatic test-strip step immediately on receipt.
            // The actual relay OFF + pulse OFF commands are serialized on the same
            // executor used by the timing state machine.
            completing.set(true);
            cancelTimers();
            device = DeviceConfig.load(this);
            if (techSessionId > 0L) {
                TechnicalLog.add(this, techSessionId, "ANNULLAMENTO CICLO richiesto dall’utente");
            } else {
                techSessionId = TechnicalLog.startSession(this, "ANNULLAMENTO CICLO");
            }
            startForeground(NOTIFICATION_ID, notification("Annullamento ciclo…"));
            acquireWakeLock();
            io.execute(() -> disarmInternal(true, "ANNULLATO — ciclo interrotto, Inching disattivato"));
        } else if (ACTION_DISARM.equals(action)) {
            completing.set(true);
            cancelTimers();
            device = DeviceConfig.load(this);
            techSessionId = TechnicalLog.startSession(this, "RIPRISTINO EMERGENZA");
            startForeground(NOTIFICATION_ID, notification("Ripristino ON/OFF…"));
            acquireWakeLock();
            io.execute(() -> disarmInternal(true, "PRONTO — Inching disattivato"));
        }
        return START_NOT_STICKY;
    }

    private void armInternal() {
        if (device == null || !device.isValid()) {
            fail("MINIR2 non trovato sulla LAN");
            return;
        }
        try {
            cancelTimers();
            completed = 0;
            seenOn.set(false);
            completing.set(false);

            String switchState = SonoffHttp.info(device);
            TechnicalLog.add(this, techSessionId, "OSSERVATO switch=" + switchState + " prima dell’armamento");
            if ("on".equals(switchState)) {
                SonoffHttp.switchOff(device);
                TechnicalLog.add(this, techSessionId, "COMANDO switch=off accettato prima dell’armamento");
            }
            SonoffHttp.pulseOn(device, widthMs);
            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(widthMs));

            String msg = mode == MODE_PRINT
                    ? "ARMATO — premi il pulsante fisico"
                    : "PROVINO ARMATO — premi il pulsante fisico una volta";
            broadcast(STATE_ARMED, msg);
            updateNotification(msg);
            startPolling(250);
        } catch (Exception e) {
            fail("Impossibile armare: " + readable(e));
        }
    }

    private void startPolling(long initialDelayMs) {
        cancelPoll();
        pollTask = io.scheduleWithFixedDelay(this::pollOnce, initialDelayMs, 275, TimeUnit.MILLISECONDS);
    }

    private void pollOnce() {
        if (completing.get()) return;
        try {
            SonoffHttp.TimedStatus status = SonoffHttp.infoStatusTimed(device);
            String sw = status.switchState;
            long observedAt = status.midpointAt();
            if ("on".equals(sw)) {
                if (seenOn.compareAndSet(false, true)) {
                    lastObservedOnAt = observedAt;
                    if (lastObservedOffAt > 0 && mode == MODE_TEST && completed > 0) {
                        TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON • pausa osservata via rete " + secondsLong(lastObservedOnAt - lastObservedOffAt));
                    } else {
                        TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON");
                    }
                    int current = completed + 1;
                    String msg = mode == MODE_PRINT
                            ? "ESPOSIZIONE IN CORSO — " + seconds(widthMs)
                            : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);
                    broadcast(STATE_EXPOSING, msg);
                    updateNotification(msg);
                }
            } else if ("off".equals(sw) && seenOn.get()) {
                long offAt = observedAt;
                long observed = lastObservedOnAt > 0 ? offAt - lastObservedOnAt : -1L;

                // v0.5.8: /zeroconf/info can occasionally return one stale OFF while an
                // automatic test-strip exposure is still running.  In v0.5.7 that false
                // edge could immediately start pulse=off and truncate the final strip.
                // The MINIR2 owns the Inching timer, so an OFF far earlier than the
                // configured width is not a credible end-of-exposure observation.
                long minimumCredibleMs = Math.max(250L, Math.round(widthMs * 0.75));
                if (observed > 0 && observed < minimumCredibleMs) {
                    TechnicalLog.add(this, techSessionId,
                            "IGNORATO switch=OFF prematuro • " + secondsLong(observed)
                                    + " < soglia " + secondsLong(minimumCredibleMs));
                    return;
                }

                lastObservedOffAt = offAt;
                TechnicalLog.add(this, techSessionId, "OSSERVATO switch=OFF" + (observed > 0 ? " • esposizione osservata via rete " + secondsLong(observed) : ""));
                onExposureFinished();
            }
        } catch (Exception e) {
            // A missed poll cannot change exposure duration: MINIR2 owns the Inching timer.
            updateNotification("Attendo il MINIR2…");
        }
    }

    private void onExposureFinished() {
        if (completing.get()) return;
        seenOn.set(false);
        completed++;

        if (mode == MODE_PRINT || completed >= count) {
            if (!completing.compareAndSet(false, true)) return;
            cancelTimers();
            try {
                String disarmMsg = "DISARMO IN CORSO — verifico Inching OFF…";
                broadcast(STATE_DISARMING, disarmMsg);
                updateNotification(disarmMsg);
                pulseOffWithWatchdog();
                persistCompletedCycle();
                String msg = mode == MODE_PRINT
                        ? "PRONTO — stampa conclusa, Inching disattivato"
                        : "PRONTO — provino completato, Inching disattivato";
                broadcast(STATE_NORMAL, msg);
                // The completion banner is transient UI feedback. Keep durable runtime
                // state clean so reopening the app starts from PRONTO, not the old result.
                persistState(STATE_NORMAL, "");
                completionFeedback();
                stopCleanly();
            } catch (Exception e) {
                completing.set(false);
                fail("Esposizione finita, ma disarmo fallito: " + readable(e));
            }
            return;
        }

        cancelPoll();
        int next = completed + 1;
        String msg = "PAUSA — " + completed + "/" + count + " completate • prossima " + next + "/" + count + " tra " + seconds(pauseMs);
        broadcast(STATE_PAUSING, msg);
        updateNotification(msg);

        nextTask = io.schedule(() -> {
            if (completing.get()) return;
            try {
                // Pulse is still enabled: this ON command asks the MINIR2 to start the next
                // locally-timed exposure.  IMPORTANT: command acknowledgement is not the
                // same thing as a confirmed relay state.  We do not arm the OFF detector
                // until /zeroconf/info has actually reported switch=on.
                SonoffHttp.switchOn(device);
                TechnicalLog.add(this, techSessionId, "COMANDO switch=on accettato per esposizione " + (completed + 1) + "/" + count);
                long confirmedOnAt = waitForConfirmedSwitchOn();

                if (completing.get()) return;
                lastObservedOnAt = confirmedOnAt;
                if (lastObservedOffAt > 0) {
                    TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON confermato • pausa osservata via rete " + secondsLong(confirmedOnAt - lastObservedOffAt));
                } else {
                    TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON confermato");
                }
                seenOn.set(true);
                int current = completed + 1;
                String exposing = "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);
                broadcast(STATE_EXPOSING, exposing);
                updateNotification(exposing);
                startPolling(120);
            } catch (Exception e) {
                fail("Provino interrotto alla esposizione " + (completed + 1) + ": " + readable(e));
            }
        }, pauseMs, TimeUnit.MILLISECONDS);
    }


    /**
     * Wait until the relay is really ON before allowing a later OFF to count as
     * "exposure finished".  This closes a race where an immediately-read stale
     * OFF could truncate an automatic test-strip exposure.
     */
    private long waitForConfirmedSwitchOn() throws Exception {
        long timeoutMs = Math.max(900L, Math.min(3000L, (long) widthMs + 500L));
        long deadline = System.currentTimeMillis() + timeoutMs;
        Exception last = null;

        while (System.currentTimeMillis() < deadline && !completing.get()) {
            try {
                SonoffHttp.TimedStatus status = SonoffHttp.infoStatusTimed(device, 2500);
                if ("on".equals(status.switchState)) return status.midpointAt();
            } catch (Exception e) {
                last = e;
            }
        }

        String suffix = last == null ? "" : ": " + readable(last);
        throw new Exception("accensione non confermata dal MINIR2" + suffix);
    }

    private void persistCompletedCycle() {
        android.content.SharedPreferences.Editor e = getSharedPreferences(SESSION_PREFS, MODE_PRIVATE).edit();
        long now = System.currentTimeMillis();
        if (mode == MODE_PRINT) {
            e.putInt("lastPrintMs", widthMs);
            e.putLong("lastPrintAt", now);
        } else {
            e.putInt("lastTestMs", widthMs);
            e.putInt("lastTestCount", count);
            e.putLong("lastTestAt", now);
        }
        e.putLong("lastCycleAt", now);
        e.apply();
    }

    private void disarmInternal(boolean forceLampOff, String doneMessage) {
        cancelTimers();
        completing.set(true);
        try {
            if (device == null || !device.isValid()) throw new Exception("MINIR2 non trovato");
            String disarmMsg = "DISARMO IN CORSO — verifico Inching OFF…";
            broadcast(STATE_DISARMING, disarmMsg);
            updateNotification(disarmMsg);
            if (forceLampOff) {
                SonoffHttp.switchOff(device);
                TechnicalLog.add(this, techSessionId, "COMANDO switch=off accettato (annullamento/ripristino)");
            }
            pulseOffWithWatchdog();
            TechnicalLog.add(this, techSessionId, doneMessage != null && doneMessage.toLowerCase(Locale.ITALY).contains("annullato")
                    ? "CICLO ANNULLATO — uscita OFF e Inching OFF confermati"
                    : "RIPRISTINO completato");
            String finalMessage = doneMessage == null ? "PRONTO — Inching disattivato" : doneMessage;
            broadcast(STATE_NORMAL, finalMessage);
            // Cancellation confirmation is also transient and must not survive restart.
            if (finalMessage.toLowerCase(Locale.ITALY).contains("annullato")) {
                persistState(STATE_NORMAL, "");
            }
            stopCleanly();
        } catch (Exception e) {
            fail("Disarmo non riuscito: " + readable(e));
        }
    }


    /**
     * Safety watchdog: the exposure has already ended in the MINIR2.  This only
     * ensures that Inching is disabled for the next physical-button press.
     * A temporary Wi-Fi hiccup must not leave the device armed indefinitely.
     */
    private void pulseOffWithWatchdog() throws Exception {
        Exception last = null;
        for (int attempt = 1; attempt <= 5; attempt++) {
            try {
                SonoffHttp.pulseOff(device);
                TechnicalLog.add(this, techSessionId, "COMANDO pulse=off accettato • tentativo " + attempt + "/5");

                // A successful HTTP command only means "accepted".  PRONTO is
                // allowed only after the MINIR2 itself reports pulse=off twice
                // consecutively, closing the short post-cycle armed window.
                int confirmations = 0;
                for (int check = 0; check < 4; check++) {
                    SonoffHttp.TimedStatus status = SonoffHttp.infoStatusTimed(device, 2500);
                    if ("off".equals(status.pulseState)) {
                        confirmations++;
                        TechnicalLog.add(this, techSessionId, "OSSERVATO pulse=off • conferma " + confirmations + "/2");
                        if (confirmations >= 2) {
                            TechnicalLog.add(this, techSessionId, "DISARMO REALE CONFERMATO");
                            return;
                        }
                    } else {
                        if (confirmations > 0 || check == 0) TechnicalLog.add(this, techSessionId, "OSSERVATO pulse=" + status.pulseState);
                        confirmations = 0;
                    }
                }

                last = new Exception("MINIR2 non ha ancora confermato pulse=off");
            } catch (Exception e) {
                last = e;
            }

            updateNotification("DISARMO — verifica " + attempt + "/5");
            try { Thread.sleep(250); } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw ie;
            }
        }
        throw new Exception("watchdog disarmo fallito dopo 5 tentativi: " + readable(last));
    }

    private void completionFeedback() {
        android.content.SharedPreferences p = getSharedPreferences("ui", MODE_PRIVATE);
        if (p.getBoolean("feedbackBeep", true)) {
            try {
                ToneGenerator tone = new ToneGenerator(AudioManager.STREAM_NOTIFICATION, 45);
                tone.startTone(ToneGenerator.TONE_PROP_BEEP, 110);
                try { Thread.sleep(140); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
                tone.release();
            } catch (Exception ignored) {}
        }
    }

    private void fail(String message) {
        TechnicalLog.add(this, techSessionId, "ERRORE — " + message);
        cancelTimers();
        broadcast(STATE_ERROR, message);
        updateNotification("ATTENZIONE — " + message);
        releaseWakeLock();
        // Keep the notification visible: the user can reopen the app and force NORMAL.
    }

    private void stopCleanly() {
        cancelTimers();
        releaseWakeLock();
        stopForeground(true);
        stopSelf();
    }

    private void cancelTimers() {
        cancelPoll();
        if (nextTask != null) {
            nextTask.cancel(false);
            nextTask = null;
        }
    }

    private void cancelPoll() {
        if (pollTask != null) {
            pollTask.cancel(false);
            pollTask = null;
        }
    }

    private void broadcast(String state, String message) {
        persistState(state, message);
        Intent i = new Intent(BROADCAST_STATE);
        i.setPackage(getPackageName());
        i.putExtra(EXTRA_STATE, state);
        i.putExtra(EXTRA_MESSAGE, message);
        sendBroadcast(i);
    }

    private void persistState(String state, String message) {
        getSharedPreferences(STATE_PREFS, MODE_PRIVATE).edit()
                .putString(KEY_STATE, state == null ? STATE_NORMAL : state)
                .putString(KEY_MESSAGE, message == null ? "" : message)
                .apply();
    }

    public static String loadLastState(android.content.Context context) {
        return context.getSharedPreferences(STATE_PREFS, android.content.Context.MODE_PRIVATE)
                .getString(KEY_STATE, STATE_NORMAL);
    }

    public static String loadLastMessage(android.content.Context context) {
        return context.getSharedPreferences(STATE_PREFS, android.content.Context.MODE_PRIVATE)
                .getString(KEY_MESSAGE, "");
    }

    private void ensureNotificationChannel() {
        if (android.os.Build.VERSION.SDK_INT < 26) return;
        try {
            Class<?> channelClass = Class.forName("android.app.NotificationChannel");
            java.lang.reflect.Constructor<?> ctor = channelClass.getConstructor(String.class, CharSequence.class, int.class);
            Object channel = ctor.newInstance(CHANNEL, "Darkroom Timer armato", 2);
            try {
                channelClass.getMethod("setDescription", String.class)
                        .invoke(channel, "Mantiene il controllo locale del MINIR2 con lo schermo spento");
            } catch (Exception ignored) {}
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            java.lang.reflect.Method create = NotificationManager.class.getMethod("createNotificationChannel", channelClass);
            create.invoke(nm, channel);
        } catch (Exception ignored) {}
    }

    private static int immutableFlag() {
        return android.os.Build.VERSION.SDK_INT >= 23 ? 0x04000000 : 0;
    }

    private Notification.Builder notificationBuilder() {
        if (android.os.Build.VERSION.SDK_INT >= 26) {
            try {
                java.lang.reflect.Constructor<?> ctor = Notification.Builder.class.getConstructor(android.content.Context.class, String.class);
                return (Notification.Builder) ctor.newInstance(this, CHANNEL);
            } catch (Exception ignored) {}
        }
        Notification.Builder b = new Notification.Builder(this);
        if (android.os.Build.VERSION.SDK_INT >= 26) {
            try { b.getClass().getMethod("setChannelId", String.class).invoke(b, CHANNEL); } catch (Exception ignored) {}
        }
        return b;
    }

    private Notification notification(String text) {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent content = PendingIntent.getActivity(this, 1, open, PendingIntent.FLAG_UPDATE_CURRENT | immutableFlag());
        Intent disarm = new Intent(this, SonoffArmService.class).setAction(ACTION_CANCEL);
        PendingIntent disarmPi = PendingIntent.getService(this, 2, disarm, PendingIntent.FLAG_UPDATE_CURRENT | immutableFlag());

        String title = mode == MODE_TEST
                ? "Darkroom Timer — Provino " + count + " × " + seconds(widthMs)
                : "Darkroom Timer — " + seconds(widthMs);
        return notificationBuilder()
                .setContentTitle(title)
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setContentIntent(content)
                .addAction(android.R.drawable.ic_menu_close_clear_cancel, "ANNULLA", disarmPi)
                .build();
    }

    private void updateNotification(String text) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify(NOTIFICATION_ID, notification(text));
    }

    private void acquireWakeLock() {
        if (wakeLock != null && wakeLock.isHeld()) return;
        PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "DarkroomTimer::Armed");
        wakeLock.setReferenceCounted(false);
        wakeLock.acquire();
    }

    private void releaseWakeLock() {
        try { if (wakeLock != null && wakeLock.isHeld()) wakeLock.release(); } catch (Exception ignored) {}
        wakeLock = null;
    }

    private static int sanitizeWidth(int ms) {
        ms = Math.max(500, Math.min(36_000_000, ms));
        return Math.round(ms / 500f) * 500;
    }

    private static int sanitizePause(int ms) {
        ms = Math.max(500, Math.min(60_000, ms));
        return Math.round(ms / 500f) * 500;
    }

    private static String seconds(int ms) {
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }

    private static String secondsLong(long ms) {
        return String.format(Locale.ITALY, "%.3f s", ms / 1000.0);
    }

    private static String readable(Exception e) {
        String m = e.getMessage();
        return (m == null || m.trim().isEmpty()) ? e.getClass().getSimpleName() : m;
    }

    @Override public void onDestroy() {
        cancelTimers();
        releaseWakeLock();
        io.shutdownNow();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
