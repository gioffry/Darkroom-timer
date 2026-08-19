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
    public static final String ACTION_START_INTERLOCK = "it.darkroom.timer.START_SAFELIGHT_INTERLOCK";
    public static final String ACTION_STOP_INTERLOCK = "it.darkroom.timer.STOP_SAFELIGHT_INTERLOCK";
    public static final String BROADCAST_STATE = "it.darkroom.timer.STATE";
    public static final String EXTRA_WIDTH = "width_ms";
    public static final String EXTRA_COUNT = "count";
    public static final String EXTRA_PAUSE = "pause_ms";
    public static final String EXTRA_TIMING_METHOD = "timing_method";
    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";
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
    private ScheduledFuture<?> interlockTask;
    private final AtomicBoolean seenOn = new AtomicBoolean(false);
    private final AtomicBoolean completing = new AtomicBoolean(false);
    private PowerManager.WakeLock wakeLock;
    private volatile DeviceConfig device;
    private volatile DeviceConfig safelight;
    private volatile boolean safelightAuto = false;
    private volatile boolean interlockActive = false;
    private volatile String lastInterlockPrimaryState = "";
    private volatile boolean interlockRestoreSafelight = false;
    private volatile boolean cycleSafelightCaptured = false;
    private volatile boolean restoreSafelightAfterCycle = false;
    private volatile int mode = MODE_PRINT;
    private volatile int widthMs = 8500;
    private volatile int count = 7;
    private volatile int pauseMs = 2000;
    private volatile String timingMethod = TimingMath.METHOD_SECONDS;
    private volatile int[] testTargetsMs = new int[0];
    private volatile int[] testPulsesMs = new int[0];
    private volatile int currentPulseWidthMs = 8500;
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
            interlockActive = false;
            cancelInterlockMonitor();
            interlockRestoreSafelight = false;
            cycleSafelightCaptured = false;
            restoreSafelightAfterCycle = false;
            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;
            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));
            count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));
            pauseMs = sanitizePause(intent.getIntExtra(EXTRA_PAUSE, 2000));
            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));
            if (mode == MODE_TEST) {
                int[] requested = intent.getIntArrayExtra(EXTRA_TEST_TARGETS);
                if (requested != null && requested.length == count) {
                    testTargetsMs = new int[count];
                    for (int x = 0; x < count; x++) testTargetsMs[x] = sanitizeWidth(requested[x]);
                } else testTargetsMs = TimingMath.cumulativeSeries(timingMethod, widthMs, count);
                testPulsesMs = TimingMath.incrementalPulses(testTargetsMs);
                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;
            } else {
                testTargetsMs = new int[0];
                testPulsesMs = new int[0];
                currentPulseWidthMs = widthMs;
            }
            device = DeviceConfig.load(this);
            loadSafelightConfig();
            techSessionId = TechnicalLog.startSession(this, mode == MODE_PRINT
                    ? "STAMPA richiesta " + seconds(widthMs) + " • " + timingMethod + " · " + TimingMath.stepLabel(timingMethod)
                    : (TimingMath.isFStop(timingMethod) ? "PROVINO F-STOP · ¼ stop • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs) : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs)));
            lastObservedOnAt = 0L;
            lastObservedOffAt = 0L;
            startForeground(NOTIFICATION_ID, notification("Preparazione…"));
            acquireWakeLock();
            broadcast(STATE_ARMING, mode == MODE_PRINT
                    ? "Imposto Inching a " + seconds(widthMs)
                    : (TimingMath.isFStop(timingMethod) ? "Preparo provino: " + count + " strisce • ¼ stop" : "Preparo provino: " + count + " × " + seconds(widthMs)));
            io.execute(this::armInternal);
        } else if (ACTION_START_INTERLOCK.equals(action)) {
            device = DeviceConfig.load(this);
            loadSafelightConfig();
            if (!safelightAuto || device == null || !device.isValid() || safelight == null || !safelight.isValid()
                    || safelight.deviceId.equals(device.deviceId)) {
                interlockActive = false;
                cancelInterlockMonitor();
                releaseWakeLock();
                stopForeground(true);
                stopSelf();
                return START_NOT_STICKY;
            }
            interlockActive = true;
            completing.set(false);
            startForeground(NOTIFICATION_ID, notification("Interblocco luce rossa attivo"));
            acquireWakeLock();
            startInterlockMonitor();
        } else if (ACTION_STOP_INTERLOCK.equals(action)) {
            interlockActive = false;
            cancelInterlockMonitor();
            interlockRestoreSafelight = false;
            releaseWakeLock();
            stopForeground(true);
            stopSelf();
        } else if (ACTION_CANCEL.equals(action)) {
            interlockActive = false;
            cancelInterlockMonitor();
            // Stop any pending automatic test-strip step immediately on receipt.
            // The actual relay OFF + pulse OFF commands are serialized on the same
            // executor used by the timing state machine.
            completing.set(true);
            cancelTimers();
            device = DeviceConfig.load(this);
            loadSafelightConfig();
            if (techSessionId > 0L) {
                TechnicalLog.add(this, techSessionId, "ANNULLAMENTO CICLO richiesto dall’utente");
            } else {
                techSessionId = TechnicalLog.startSession(this, "ANNULLAMENTO CICLO");
            }
            startForeground(NOTIFICATION_ID, notification("Annullamento ciclo…"));
            acquireWakeLock();
            io.execute(() -> disarmInternal(true, "ANNULLATO — ciclo interrotto, Inching disattivato"));
        } else if (ACTION_DISARM.equals(action)) {
            interlockActive = false;
            cancelInterlockMonitor();
            completing.set(true);
            cancelTimers();
            device = DeviceConfig.load(this);
            loadSafelightConfig();
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
            SonoffHttp.pulseOn(device, currentPulseWidthMs);
            TechnicalLog.add(this, techSessionId, "COMANDO pulse=on accettato • " + seconds(currentPulseWidthMs));
            if (safelightAuto) TechnicalLog.add(this, techSessionId, "SAFELIGHT non modificata durante ARMATO");

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
                    if (safelightAuto && completed == 0) {
                        try {
                            captureAndDimSafelightForCycle();
                        } catch (Exception e) {
                            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: stato iniziale non acquisito — " + readable(e));
                        }
                    }
                    lastObservedOnAt = observedAt;
                    if (lastObservedOffAt > 0 && mode == MODE_TEST && completed > 0) {
                        TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON • pausa osservata via rete " + secondsLong(lastObservedOnAt - lastObservedOffAt));
                    } else {
                        TechnicalLog.add(this, techSessionId, "OSSERVATO switch=ON");
                    }
                    int current = completed + 1;
                    String msg = mode == MODE_PRINT
                            ? "ESPOSIZIONE IN CORSO — " + seconds(widthMs)
                            : (TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));
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
                long minimumCredibleMs = Math.max(250L, Math.round(currentPulseWidthMs * 0.75));
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
            restoreSafelightBestEffort();
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
                if (TimingMath.isFStop(timingMethod) && testPulsesMs.length == count) {
                    currentPulseWidthMs = testPulsesMs[completed];
                    SonoffHttp.pulseOn(device, currentPulseWidthMs);
                    TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • cumulativo " + seconds(testTargetsMs[completed]));
                } else currentPulseWidthMs = widthMs;
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
                String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — striscia " + seconds(testTargetsMs[current - 1]) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);
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
        long timeoutMs = Math.max(900L, Math.min(3000L, (long) currentPulseWidthMs + 500L));
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
            e.putString("lastPrintMethod", timingMethod);
            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));
            e.putLong("lastPrintAt", now);
        } else {
            e.putInt("lastTestMs", widthMs);
            e.putInt("lastTestCount", count);
            e.putString("lastTestMethod", timingMethod);
            e.putString("lastTestStep", TimingMath.stepLabel(timingMethod));
            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));
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
            if (safelightAuto) {
                setSafelightConfirmed(true);
                TechnicalLog.add(this, techSessionId, "SAFELIGHT ON confermata durante ripristino");
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
    private void startInterlockMonitor() {
        cancelInterlockMonitor();
        if (!interlockActive || !safelightAuto || device == null || !device.isValid()
                || safelight == null || !safelight.isValid() || safelight.deviceId.equals(device.deviceId)) return;
        lastInterlockPrimaryState = "";
        interlockRestoreSafelight = false;
        interlockTask = io.scheduleWithFixedDelay(this::interlockPollOnce, 0, 500, TimeUnit.MILLISECONDS);
    }

    private void interlockPollOnce() {
        if (!interlockActive || !safelightAuto) return;
        try {
            String primary = SonoffHttp.infoQuick(device, 1400);
            if (lastInterlockPrimaryState.isEmpty()) {
                lastInterlockPrimaryState = primary;
                updateNotification("Interblocco attivo • stato manuale luce rossa rispettato");
                TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline " + primary.toUpperCase(Locale.ITALY) + " • nessun comando safelight");
                return;
            }
            if (primary.equals(lastInterlockPrimaryState)) return;

            if ("on".equals(primary)) {
                String safeState = SonoffHttp.infoQuick(safelight, 1400);
                interlockRestoreSafelight = "on".equals(safeState);
                if (interlockRestoreSafelight) {
                    setSafelightConfirmed(false);
                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — rossa era ON, spenta con ingranditore");
                } else {
                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — rossa era già OFF, nessun comando");
                }
                updateNotification("Ingranditore ON • luce rossa " + (interlockRestoreSafelight ? "spenta automaticamente" : "già OFF"));
            } else {
                if (interlockRestoreSafelight) {
                    setSafelightConfirmed(true);
                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO — ripristinata rossa ON");
                    updateNotification("Ingranditore OFF • luce rossa ripristinata ON");
                } else {
                    updateNotification("Ingranditore OFF • stato manuale luce rossa invariato");
                }
                interlockRestoreSafelight = false;
            }
            lastInterlockPrimaryState = primary;
        } catch (Exception e) {
            updateNotification("Interblocco: attendo i SONOFF…");
        }
    }

    private void cancelInterlockMonitor() {
        if (interlockTask != null) {
            interlockTask.cancel(false);
            interlockTask = null;
        }
        lastInterlockPrimaryState = "";
        interlockRestoreSafelight = false;
    }

    private void loadSafelightConfig() {
        safelightAuto = getSharedPreferences("ui", MODE_PRIVATE).getBoolean("safelightAuto", false);
        safelight = SafelightConfig.load(this);
        if (safelightAuto && (safelight == null || !safelight.isValid())) {
            safelight = null;
        }
    }

    private void captureAndDimSafelightForCycle() throws Exception {
        if (!safelightAuto) return;
        if (safelight == null || !safelight.isValid()) throw new Exception("SONOFF safelight non configurato");
        String observed = SonoffHttp.infoQuick(safelight, 1800);
        if (!"on".equals(observed) && !"off".equals(observed)) throw new Exception("stato safelight non leggibile");
        cycleSafelightCaptured = true;
        restoreSafelightAfterCycle = "on".equals(observed);
        if (restoreSafelightAfterCycle) {
            setSafelightConfirmed(false);
            TechnicalLog.add(this, techSessionId, "SAFELIGHT era ON • spenta per il ciclo");
        } else {
            TechnicalLog.add(this, techSessionId, "SAFELIGHT era già OFF • nessun comando");
        }
    }

    private void setSafelightConfirmed(boolean on) throws Exception {
        if (!safelightAuto) return;
        if (safelight == null || !safelight.isValid()) throw new Exception("SONOFF safelight non configurato");
        if (device != null && device.isValid() && safelight.deviceId.equals(device.deviceId)) {
            throw new Exception("il SONOFF safelight coincide con l’ingranditore");
        }
        String wanted = on ? "on" : "off";
        Exception last = null;
        for (int attempt = 1; attempt <= 4; attempt++) {
            try {
                if (on) SonoffHttp.switchOn(safelight); else SonoffHttp.switchOff(safelight);
                TechnicalLog.add(this, techSessionId, "SAFELIGHT comando " + wanted.toUpperCase(Locale.ITALY) + " • tentativo " + attempt + "/4");
                for (int check = 0; check < 3; check++) {
                    String observed = SonoffHttp.infoQuick(safelight, 1800);
                    if (wanted.equals(observed)) {
                        TechnicalLog.add(this, techSessionId, "SAFELIGHT osservata " + wanted.toUpperCase(Locale.ITALY));
                        return;
                    }
                    try { Thread.sleep(120L); } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw ie;
                    }
                }
                last = new Exception("stato " + wanted + " non confermato");
            } catch (Exception e) {
                last = e;
            }
        }
        throw new Exception("safelight " + wanted.toUpperCase(Locale.ITALY) + " non confermata: " + readable(last));
    }

    private void restoreSafelightBestEffort() {
        boolean captured = cycleSafelightCaptured;
        boolean restore = restoreSafelightAfterCycle;
        cycleSafelightCaptured = false;
        restoreSafelightAfterCycle = false;
        if (!captured || !restore) {
            if (captured) TechnicalLog.add(this, techSessionId, "SAFELIGHT era OFF prima del ciclo • stato lasciato OFF");
            return;
        }
        try {
            setSafelightConfirmed(true);
            TechnicalLog.add(this, techSessionId, "SAFELIGHT ripristinata ON perché era ON prima del ciclo");
        } catch (Exception e) {
            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: ripristino stato iniziale fallito — " + readable(e));
        }
    }

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
        completing.set(true);
        try {
            if (device != null && device.isValid()) {
                try { SonoffHttp.switchOff(device); } catch (Exception ignored) {}
                try { SonoffHttp.pulseOff(device); } catch (Exception ignored) {}
            }
        } finally {
            restoreSafelightBestEffort();
        }
        broadcast(STATE_ERROR, message);
        updateNotification("ATTENZIONE — " + message);
        releaseWakeLock();
    }

    private void stopCleanly() {
        cancelTimers();
        if (safelightAuto && device != null && device.isValid() && safelight != null && safelight.isValid()
                && !safelight.deviceId.equals(device.deviceId)) {
            completing.set(false);
            interlockActive = true;
            startForeground(NOTIFICATION_ID, notification("Interblocco luce rossa attivo"));
            startInterlockMonitor();
            return;
        }
        interlockActive = false;
        cancelInterlockMonitor();
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
        String title = interlockActive
                ? "Darkroom Timer — Luce rossa automatica"
                : (mode == MODE_TEST ? "Darkroom Timer — Provino " + count + " × " + seconds(widthMs) : "Darkroom Timer — " + seconds(widthMs));
        Notification.Builder b = notificationBuilder()
                .setContentTitle(title)
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setContentIntent(content);
        if (!interlockActive) {
            Intent disarm = new Intent(this, SonoffArmService.class).setAction(ACTION_CANCEL);
            PendingIntent disarmPi = PendingIntent.getService(this, 2, disarm, PendingIntent.FLAG_UPDATE_CURRENT | immutableFlag());
            b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "ANNULLA", disarmPi);
        }
        return b.build();
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
        cancelInterlockMonitor();
        releaseWakeLock();
        io.shutdownNow();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
