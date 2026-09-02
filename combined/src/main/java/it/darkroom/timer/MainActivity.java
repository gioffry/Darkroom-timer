package it.darkroom.timer;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.app.NotificationManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.Uri;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.InputFilter;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.Window;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.EditText;
import android.widget.Toast;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity implements SonoffDiscovery.Listener {
    private int GREEN;
    private int BLUE;
    private int CARD;
    private int BUTTON;
    private int BORDER;
    private int MUTED;
    private int AMBER;
    private int RED;
    private int LOG_ACCENT;
    private int TEXT_PRIMARY;
    // Pantone FHI approssimati in sRGB per display. In modalità camera oscura resta RED puro.
    private static final int DODGE_BISCAY_BAY = Color.rgb(9, 121, 136);   // 18-4726 TCX
    private static final int BURN_RUST = Color.rgb(181, 90, 48);          // 18-1248 TCX
    private static final int SPLIT_VIVA_MAGENTA = Color.rgb(187, 38, 73);// 18-1750 TCX
    private boolean darkroomMode;
    private boolean feedbackBeep;
    private boolean voiceGuide;
    private boolean darkroomProtection;
    private String timingMethod = TimingMath.METHOD_SECONDS;
    private boolean safelightAuto = false;
    private boolean pendingDarkroomAfterDndPermission = false;

    private static final int MODE_PRINT = 0;
    private static final int MODE_TEST = 1;
    private static final int MODE_LOG = 2;

    private static final int PROVINO_SINGLE = 0;
    private static final int PROVINO_SPLIT_SOFT = 1;
    private static final int PROVINO_SPLIT_HARD = 2;

    private static final int REQ_EXPORT_BACKUP = 4101;
    private static final int REQ_IMPORT_BACKUP = 4102;
    private static final int REQ_EXPORT_JPG = 4103;
    private static final String APP_VERSION = "0.13.11";

    private static final class FoundDevice {
        final DeviceConfig config;
        final boolean diyCandidate;
        final String type;
        final String apiVersion;

        FoundDevice(DeviceConfig config, boolean diyCandidate, String type, String apiVersion) {
            this.config = config;
            this.diyCandidate = diyCandidate;
            this.type = type == null ? "" : type;
            this.apiVersion = apiVersion == null ? "" : apiVersion;
        }

        String modeLabel() { return diyCandidate ? "possibile DIY" : "eWeLink"; }
    }

    private static final class LogGroup {
        final String key;
        final ArrayList<LogEntry> entries = new ArrayList<>();

        LogGroup(String key) { this.key = key; }
        LogEntry latest() { return entries.get(0); }
        boolean hasFavorite() {
            for (LogEntry e : entries) if (e.favorite) return true;
            return false;
        }
    }

    private interface ChoiceAction {
        void choose(int index);
    }

    private TextView deviceStatus;
    private TextView safelightStatus;
    private TextView stateTitle;
    private TextView stateText;
    private LinearLayout stateCard;
    private TextView printTimeText;
    private TextView testTimeText;
    private TextView testCountText;
    private TextView testPauseText;
    private TextView testCumulativeText;
    private TextView printStepText;
    private TextView testPromptText;
    private TextView testStepText;
    private TextView printFStopBadge;
    private TextView testFStopBadge;
    private Button testBaseFilterButton;
    private Button testStripMethodButton;
    private Button testPendingChoiceButton;
    private Button testSingleModeButton;
    private Button testSplitModeButton;
    private TextView testSplitPhaseText;
    private TextView testContrastGuide;
    private TextView printSequenceSummary;
    private Button printSequenceButton;
    private Button actionButton;
    private Button normalButton;
    private Button selectDeviceButton;
    private Button printModeButton;
    private Button testModeButton;
    private Button logModeButton;
    private Button saveLogButton;
    private Button cancelCycleButton;
    private LinearLayout printPanel;
    private LinearLayout testPanel;
    private LinearLayout logPanel;
    private LinearLayout logListContainer;
    private EditText logSearchField;
    private Button logFilterAllButton;
    private Button logFilter35Button;
    private Button logFilter66Button;
    private Button logFilter45Button;
    private Button logFavoritesButton;
    private Button logGroupingButton;
    private String logFilter = "ALL";
    private boolean logFavoritesOnly = false;
    private boolean logGroupingEnabled = true;

    private SonoffDiscovery discovery;
    private DeviceConfig device;
    private String selectedDeviceId;
    private DeviceConfig safelightDevice;
    private String selectedSafelightDeviceId = "";
    private int mode = MODE_PRINT;
    private int printWidthMs = 8500;
    private PrintSequence printSequence = new PrintSequence();
    private ExposureRecipe exposureRecipe = new ExposureRecipe();
    private String testBaseFilterType = ExposureRecipe.FILTER_NONE;
    private int testBaseFilterValue = 0;
    private String testStripMethod = TimingMath.MASK_REVEAL;
    private int provinoFlow = PROVINO_SINGLE;
    private int splitSoftYellow = 60;
    private int splitSoftChosenMs = 0;
    private int splitSoftChosenStrip = -1;
    private int splitHardMagenta = 130;
    private int splitHardChosenMs = 0;
    private int splitHardChosenStrip = -1;
    private String splitReturnFilterType = ExposureRecipe.FILTER_NONE;
    private int splitReturnFilterValue = 0;
    private int splitReturnTestWidthMs = 2000;
    private static final int ALLUNGA_COLOR = Color.rgb(154, 119, 43);
    private int testWidthMs = 2000;
    private int testCount = 7;
    private int testPauseMs = 2000;
    private boolean armed = false;
    private LogEntry pendingJpegEntry;
    private long transientCompletionUntilMs = 0L;
    private boolean testChooserOpen = false;

    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Map<String, FoundDevice> foundDevices = new LinkedHashMap<>();
    private final Handler reconnectHandler = new Handler(Looper.getMainLooper());
    private final Handler statusResetHandler = new Handler(Looper.getMainLooper());
    private final Runnable readyResetRunnable = () -> {
        if (!armed && mode != MODE_LOG && stateCard != null) {
            if (device != null && device.isValid()) {
                setStatusPresentation("PRONTO", "Scegli il tempo e premi ARMA", GREEN);
            } else {
                setStatusPresentation("ATTESA SONOFF",
                        "RICONNESSIONE AUTOMATICA — attendo conferma dal SONOFF",
                        darkroomMode ? RED : AMBER);
            }
        }
    };
    private final AtomicBoolean validationInFlight = new AtomicBoolean(false);
    private final AtomicBoolean healthCheckInFlight = new AtomicBoolean(false);
    private int connectionFailures = 0;
    private boolean activityStarted = false;
    private final Runnable reconnectRunnable = new Runnable() {
        @Override public void run() {
            if (!activityStarted) return;
            DeviceConfig saved = DeviceConfig.load(MainActivity.this);
            if (saved.isValid() && saved.deviceId.equals(selectedDeviceId)) {
                if (armed) {
                    // During a cycle SonoffArmService already polls the MINIR2.
                    // Do not add UI heartbeat traffic to the timing path.
                } else if (device != null && device.isValid()) {
                    healthCheckSelected(saved);
                } else {
                    validateSelected(saved);
                }
            }
            if (activityStarted) reconnectHandler.postDelayed(this, 3000L);
        }
    };

    private final BroadcastReceiver stateReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            applyRuntimeState(
                    intent.getStringExtra(SonoffArmService.EXTRA_STATE),
                    intent.getStringExtra(SonoffArmService.EXTRA_MESSAGE));
        }
    };

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Lpl7451Migration.run(this);
        SharedPreferences p = getSharedPreferences("ui", MODE_PRIVATE);
        darkroomMode = p.getBoolean("darkroomMode", false);
        feedbackBeep = p.getBoolean("feedbackBeep", true);
        voiceGuide = p.getBoolean("voiceGuide", true);
        darkroomProtection = p.getBoolean("darkroomProtection", true);
        timingMethod = TimingMath.normalizeMethod(p.getString("timingMethod", TimingMath.METHOD_SECONDS));
        safelightAuto = p.getBoolean("safelightAuto", false);
        logGroupingEnabled = p.getBoolean("logGroupingEnabled", true);
        configurePalette();
        applyDarkroomWindow();
        mode = MODE_TEST;
        p.edit().putInt("mode", MODE_TEST).apply();
        printWidthMs = p.getInt("printWidthMs", 8500);
        printSequence = PrintSequence.decode(p.getString("printSequence", ""));
        exposureRecipe = ExposureRecipe.decode(p.getString("exposureRecipe", ""));
        testBaseFilterType = ExposureRecipe.normalizeFilter(p.getString("testBaseFilterType", ExposureRecipe.FILTER_NONE));
        testBaseFilterValue = ExposureRecipe.snap5(p.getInt("testBaseFilterValue", 0));
        testWidthMs = p.getInt("testWidthMs", 2000);
        testCount = p.getInt("testCount", 7);
        testPauseMs = p.getInt("testPauseMs", 2000);
        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));
        provinoFlow = Math.max(PROVINO_SINGLE, Math.min(PROVINO_SPLIT_HARD, p.getInt("provinoFlow", PROVINO_SINGLE)));
        splitSoftYellow = ExposureRecipe.snap5(p.getInt("splitProvinoSoftYellow", 60));
        splitSoftChosenMs = p.getInt("splitProvinoSoftMs", 0);
        splitSoftChosenStrip = p.getInt("splitProvinoSoftStrip", -1);
        splitHardMagenta = ExposureRecipe.snap5(p.getInt("splitProvinoHardMagenta", 130));
        splitHardChosenMs = p.getInt("splitProvinoHardMs", 0);
        splitHardChosenStrip = p.getInt("splitProvinoHardStrip", -1);
        splitReturnFilterType = ExposureRecipe.normalizeFilter(p.getString("splitProvinoReturnFilterType", testBaseFilterType));
        splitReturnFilterValue = ExposureRecipe.snap5(p.getInt("splitProvinoReturnFilterValue", testBaseFilterValue));
        splitReturnTestWidthMs = p.getInt("splitProvinoReturnTestWidthMs", testWidthMs);
        if (provinoFlow == PROVINO_SPLIT_SOFT) {
            testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
            testBaseFilterValue = splitSoftYellow;
        } else if (provinoFlow == PROVINO_SPLIT_HARD) {
            if (splitSoftChosenMs <= 0) provinoFlow = PROVINO_SPLIT_SOFT;
            testBaseFilterType = provinoFlow == PROVINO_SPLIT_HARD ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW;
            testBaseFilterValue = provinoFlow == PROVINO_SPLIT_HARD ? splitHardMagenta : splitSoftYellow;
        }

        DeviceConfig saved = DeviceConfig.load(this);
        selectedDeviceId = saved.deviceId == null ? "" : saved.deviceId.trim();
        device = null;
        DeviceConfig savedSafelight = SafelightConfig.load(this);
        selectedSafelightDeviceId = savedSafelight.deviceId == null ? "" : savedSafelight.deviceId.trim();
        safelightDevice = savedSafelight.isValid() ? savedSafelight : null;
        buildUi();
        applyModeUi();
        updateSelectionUiBeforeDiscovery();
    }

    @Override protected void onStart() {
        super.onStart();
        activityStarted = true;
        IntentFilter f = new IntentFilter(SonoffArmService.BROADCAST_STATE);
        if (Build.VERSION.SDK_INT >= 33) {
            try {
                java.lang.reflect.Method m = Context.class.getMethod("registerReceiver", BroadcastReceiver.class, IntentFilter.class, int.class);
                m.invoke(this, stateReceiver, f, 4); // RECEIVER_NOT_EXPORTED
            } catch (Exception e) {
                registerReceiver(stateReceiver, f);
            }
        } else {
            registerReceiver(stateReceiver, f);
        }
        restoreRuntimeState();
        foundDevices.clear();
        discovery = new SonoffDiscovery(this, this);
        discovery.start();

        // Do not depend only on mDNS. The selected MINIR2 was already verified in
        // previous runs, so probe the last known address immediately while NSD
        // independently searches by immutable Device ID (and can update the IP).
        DeviceConfig saved = DeviceConfig.load(this);
        if (saved.isValid() && saved.deviceId.equals(selectedDeviceId)) {
            validateSelected(saved);
        }
        reconnectHandler.removeCallbacks(reconnectRunnable);
        reconnectHandler.postDelayed(reconnectRunnable, 3000L);
        ensureSafelightIdleOn();
    }

    @Override protected void onResume() {
        super.onResume();
        SharedPreferences ep = getSharedPreferences("ui", MODE_PRIVATE);
        if (ep.getBoolean("enlargementReloadPending", false)) {
            printWidthMs = ep.getInt("printWidthMs", printWidthMs);
            exposureRecipe = ExposureRecipe.decode(ep.getString("exposureRecipe", ""));
            printSequence = PrintSequence.decode(ep.getString("printSequence", ""));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);
                testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);
            }
            mode = MODE_PRINT;
            ep.edit().remove("enlargementReloadPending").putInt("mode", MODE_PRINT).apply();
            if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));
            refreshTestBaseFilterUi();
            updatePrintSequenceUi();
            applyModeUi();
        }
        // A cycle may have completed while the screen/activity was stopped.
        // Re-read the service's durable state instead of relying on a missed broadcast.
        restoreRuntimeState();
        refreshPendingTestStripChoiceUi();
        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);

        if (pendingDarkroomAfterDndPermission) {
            pendingDarkroomAfterDndPermission = false;
            if (hasDndAccess()) {
                getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomMode", true).apply();
                recreate();
                return;
            }
            Toast.makeText(this, "Protezione notifiche non autorizzata", Toast.LENGTH_SHORT).show();
        }
        syncDarkroomProtection();
    }

    @Override protected void onStop() {
        activityStarted = false;
        reconnectHandler.removeCallbacks(reconnectRunnable);
        if (discovery != null) discovery.stop();
        discovery = null;
        try { unregisterReceiver(stateReceiver); } catch (Exception ignored) {}
        super.onStop();
    }

    @Override protected void onDestroy() {
        statusResetHandler.removeCallbacksAndMessages(null);
        io.shutdownNow();
        super.onDestroy();
    }

    private void restoreRuntimeState() {
        applyRuntimeState(
                SonoffArmService.loadLastState(this),
                SonoffArmService.loadLastMessage(this));
    }

    private void applyRuntimeState(String state, String message) {
        if (state == null || state.trim().isEmpty()) state = SonoffArmService.STATE_NORMAL;

        boolean blankNormalRefresh = SonoffArmService.STATE_NORMAL.equals(state)
                && (message == null || message.trim().isEmpty());
        if (blankNormalRefresh && android.os.SystemClock.uptimeMillis() < transientCompletionUntilMs) {
            return;
        }

        statusResetHandler.removeCallbacks(readyResetRunnable);
        if (!SonoffArmService.STATE_NORMAL.equals(state)) transientCompletionUntilMs = 0L;

        boolean cancellable = SonoffArmService.STATE_ARMED.equals(state)
                || SonoffArmService.STATE_ARMING.equals(state)
                || SonoffArmService.STATE_EXPOSING.equals(state)
                || SonoffArmService.STATE_PAUSING.equals(state)
                || SonoffArmService.STATE_WAITING_BURN.equals(state)
                || SonoffArmService.STATE_WAITING_SPLIT.equals(state);
        boolean busy = cancellable || SonoffArmService.STATE_DISARMING.equals(state);

        if (busy) {
            armed = true;
            setControlsEnabled(false);
            normalButton.setVisibility(View.GONE);
        } else if (SonoffArmService.STATE_ERROR.equals(state)) {
            armed = false;
            setControlsEnabled(device != null && device.isValid());
            normalButton.setVisibility(View.VISIBLE);
            normalButton.setEnabled(device != null && device.isValid());
            normalButton.setAlpha(normalButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
            actionButton.setVisibility(mode == MODE_LOG ? View.GONE : View.VISIBLE);
            actionButton.setText("RIPROVA");
            actionButton.setEnabled(device != null && device.isValid());
            actionButton.setAlpha(actionButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
            setStatusPresentation("ATTENZIONE", message == null ? "Errore del ciclo" : message, RED);
            cancelCycleButton.setVisibility(View.GONE);
            // An exposure error must not disable the independent manual ON/OFF safelight interlock.
            ensureSafelightIdleOn();
            return;
        } else {
            armed = false;
            normalButton.setVisibility(View.GONE);
            setControlsEnabled(device != null && device.isValid());
        }

        cancelCycleButton.setVisibility(cancellable ? View.VISIBLE : View.GONE);
        if (!SonoffArmService.STATE_DISARMING.equals(state)) cancelCycleButton.setEnabled(true);
        actionButton.setVisibility(mode == MODE_LOG || cancellable || SonoffArmService.STATE_DISARMING.equals(state) ? View.GONE : View.VISIBLE);

        String detail = message == null ? "" : message.trim();
        int accent = MUTED;
        String title = "PRONTO";
        boolean transientCompletion = false;
        if (SonoffArmService.STATE_ARMING.equals(state)) {
            title = "PREPARAZIONE";
            accent = AMBER;
        } else if (SonoffArmService.STATE_ARMED.equals(state)) {
            title = "ARMATO";
            accent = mode == MODE_TEST ? BLUE : GREEN;
        } else if (SonoffArmService.STATE_EXPOSING.equals(state)) {
            title = "ESPOSIZIONE IN CORSO";
            accent = mode == MODE_TEST ? BLUE : GREEN;
        } else if (SonoffArmService.STATE_PAUSING.equals(state)) {
            title = "PAUSA PROVINO";
            accent = BLUE;
        } else if (SonoffArmService.STATE_WAITING_SPLIT.equals(state)) {
            title = "SPLIT GRADE — CAMBIA FILTRO";
            accent = darkroomMode ? RED : SPLIT_VIVA_MAGENTA;
        } else if (SonoffArmService.STATE_WAITING_BURN.equals(state)) {
            title = "BRUCIATURA — PREPARA MASCHERA";
            accent = darkroomMode ? RED : BURN_RUST;
        } else if (SonoffArmService.STATE_DISARMING.equals(state)) {
            title = "DISARMO IN CORSO";
            accent = AMBER;
        } else if (SonoffArmService.STATE_NORMAL.equals(state)) {
            SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
            if (detail.toLowerCase(Locale.ITALY).contains("stampa conclusa")) {
                int ms = session.getInt("lastPrintMs", printWidthMs);
                title = "✓  STAMPA COMPLETATA — " + formatTime(ms);
                detail = "Inching disattivato • pronto per una nuova esposizione";
                accent = GREEN;
                transientCompletion = true;
            } else if (detail.toLowerCase(Locale.ITALY).contains("provino completato")) {
                int countDone = session.getInt("lastTestCount", testCount);
                if (provinoFlow == PROVINO_SPLIT_SOFT) {
                    title = "✓  FASE 1 COMPLETATA — MORBIDO";
                    detail = "Scegli il tempo morbido oppure reimposta la fase";
                } else if (provinoFlow == PROVINO_SPLIT_HARD) {
                    title = "✓  FASE 2 COMPLETATA — DURO";
                    detail = "Ogni striscia comprende già la base morbida scelta";
                } else {
                    title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;
                    detail = "Scegli la striscia da usare come punto di partenza per la stampa";
                }
                accent = BLUE;
                transientCompletion = true;
                new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 180L);
            } else if (detail.toLowerCase(Locale.ITALY).contains("annullato")) {
                title = "CICLO ANNULLATO";
                detail = "Uscita spenta e Inching disattivato";
                accent = RED;
                transientCompletion = true;
            } else {
                if (device != null && device.isValid()) {
                    title = "PRONTO";
                    if (detail.isEmpty()) detail = "Scegli il tempo e premi ARMA";
                    accent = GREEN;
                } else {
                    title = "ATTESA SONOFF";
                    detail = "RICONNESSIONE AUTOMATICA — attendo conferma dal SONOFF";
                    accent = darkroomMode ? RED : AMBER;
                }
            }
        }
        setStatusPresentation(title, detail, accent);
        if (transientCompletion) {
            transientCompletionUntilMs = android.os.SystemClock.uptimeMillis() + 6000L;
            statusResetHandler.postDelayed(readyResetRunnable, 6000L);
        }

        if (!busy && mode != MODE_LOG && shouldOfferQuickSave()) {
            saveLogButton.setVisibility(View.VISIBLE);
        } else if (mode == MODE_LOG || busy) {
            saveLogButton.setVisibility(View.GONE);
        }
    }

    private void setStatusPresentation(String title, String detail, int accent) {
        if (stateTitle != null) {
            stateTitle.setText(title == null || title.trim().isEmpty() ? "STATO" : title);
            stateTitle.setTextColor(accent);
        }
        if (stateText != null) {
            stateText.setText(detail == null ? "" : detail);
            stateText.setTextColor(MUTED);
        }
        if (stateCard != null) stateCard.setBackground(roundRect(CARD, 12, 1, accent));
    }

    private void buildUi() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(Color.BLACK);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(14), dp(16), dp(18));
        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        page.addView(scroll, lp(-1, 0, 1f));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        Button homeButton = new Button(this);
        homeButton.setText("⌂");
        homeButton.setAllCaps(false);
        homeButton.setTextSize(25);
        homeButton.setTextColor(TEXT_PRIMARY);
        homeButton.setPadding(0, 0, 0, 0);
        homeButton.setMinWidth(0);
        homeButton.setMinimumWidth(0);
        homeButton.setMinHeight(0);
        homeButton.setMinimumHeight(0);
        homeButton.setBackgroundColor(Color.TRANSPARENT);
        homeButton.setContentDescription("Torna alla Home");
        homeButton.setOnClickListener(v -> finish());
        topBar.addView(homeButton, lp(dp(46), dp(46)));
        TextView title = text("TIMER", 27, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
        topBar.addView(title, lp(0, dp(46), 1f));
        View navSpacer = new View(this);
        topBar.addView(navSpacer, lp(dp(46), dp(46)));
        root.addView(topBar, lp(-1, dp(46)));

        LinearLayout deviceCard = card();
        deviceCard.setPadding(dp(14), dp(9), dp(14), dp(9));
        LinearLayout deviceTop = new LinearLayout(this);
        deviceTop.setOrientation(LinearLayout.HORIZONTAL);
        deviceTop.setGravity(Gravity.CENTER_VERTICAL);
        TextView deviceName = text("INGRANDITORE", 14, TEXT_PRIMARY, true);
        deviceTop.addView(deviceName, lp(0, -2, 1f));
        selectDeviceButton = compactButton("⚙");
        selectDeviceButton.setTextSize(20);
        selectDeviceButton.setOnClickListener(v -> showSettingsDialog());
        deviceTop.addView(selectDeviceButton, lp(dp(48), dp(36)));
        deviceCard.addView(deviceTop);
        deviceStatus = text("Cerco i SONOFF sulla rete…", 13, MUTED, false);
        deviceStatus.setPadding(0, dp(4), 0, 0);
        deviceCard.addView(deviceStatus);
        safelightStatus = text("", 11, MUTED, false);
        safelightStatus.setPadding(0, dp(2), 0, 0);
        deviceCard.addView(safelightStatus);
        updateSafelightStatus();
        root.addView(deviceCard, margin(lp(-1, -2), 0, 4, 0, 10));

        LinearLayout modeRow = new LinearLayout(this);
        modeRow.setOrientation(LinearLayout.HORIZONTAL);
        modeRow.setGravity(Gravity.CENTER_VERTICAL);
        modeRow.setPadding(dp(8), dp(2), dp(8), dp(3));
        modeRow.setBackgroundColor(Color.BLACK);
        testModeButton = navButton("PROVINO", PrimaryNavButton.ICON_TEST);
        printModeButton = navButton("STAMPA", PrimaryNavButton.ICON_TIMER);
        logModeButton = navButton("LOG", PrimaryNavButton.ICON_LOG);
        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));
        printModeButton.setOnClickListener(v -> setMode(MODE_PRINT));
        logModeButton.setOnClickListener(v -> setMode(MODE_LOG));
        modeRow.addView(testModeButton, lp(0, dp(72), 1f));
        modeRow.addView(printModeButton, lp(0, dp(72), 1f));
        modeRow.addView(logModeButton, lp(0, dp(72), 1f));

        printPanel = buildPrintPanel();
        testPanel = buildTestPanel();
        logPanel = buildLogPanel();
        root.addView(printPanel, lp(-1, -2));
        root.addView(testPanel, lp(-1, -2));
        root.addView(logPanel, lp(-1, -2));

        actionButton = new Button(this);
        actionButton.setTextColor(TEXT_PRIMARY);
        actionButton.setTextSize(18);
        actionButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        actionButton.setAllCaps(false);
        actionButton.setOnClickListener(v -> arm());
        root.addView(actionButton, margin(lp(-1, dp(64)), 0, 14, 0, 0));

        cancelCycleButton = new Button(this);
        cancelCycleButton.setText("■  ANNULLA CICLO");
        cancelCycleButton.setTextSize(17);
        cancelCycleButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        cancelCycleButton.setAllCaps(false);
        cancelCycleButton.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE);
        cancelCycleButton.setBackground(roundRect(RED, 10, 0, 0));
        cancelCycleButton.setOnClickListener(v -> cancelCurrentCycle());
        cancelCycleButton.setVisibility(View.GONE);
        root.addView(cancelCycleButton, margin(lp(-1, dp(60)), 0, 14, 0, 0));

        saveLogButton = new Button(this);
        saveLogButton.setText("SALVA NEL LOG");
        saveLogButton.setTextSize(16);
        saveLogButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        saveLogButton.setAllCaps(false);
        saveLogButton.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE);
        saveLogButton.setBackground(roundRect(darkroomMode ? RED : LOG_ACCENT, 10, 0, 0));
        saveLogButton.setOnClickListener(v -> showLogEditor(newEntryFromSession(), true));
        saveLogButton.setVisibility(View.GONE);
        root.addView(saveLogButton, margin(lp(-1, dp(56)), 0, 8, 0, 0));

        stateCard = card();
        stateCard.setPadding(dp(14), dp(11), dp(14), dp(11));
        stateTitle = text("PRONTO", 14, GREEN, true);
        stateTitle.setGravity(Gravity.CENTER);
        stateCard.addView(stateTitle, lp(-1, -2));
        stateText = text("Scegli il tempo e premi ARMA", 12, MUTED, false);
        stateText.setGravity(Gravity.CENTER);
        stateText.setPadding(dp(4), dp(4), dp(4), 0);
        stateCard.addView(stateText, lp(-1, -2));
        root.addView(stateCard, margin(lp(-1, -2), 0, 10, 0, 0));

        normalButton = new Button(this);
        normalButton.setText("⚠  RIPRISTINO EMERGENZA\nSpegne l’uscita e disattiva Inching");
        normalButton.setTextColor(TEXT_PRIMARY);
        normalButton.setTextSize(14);
        normalButton.setAllCaps(false);
        normalButton.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        normalButton.setPadding(dp(20), 0, dp(12), 0);
        normalButton.setBackground(roundRect(CARD, 10, 1, BORDER));
        normalButton.setOnClickListener(v -> disarm());
        normalButton.setVisibility(View.GONE);
        root.addView(normalButton, lp(-1, dp(64)));

        View bottomNavDivider = new View(this);
        bottomNavDivider.setBackgroundColor(darkroomMode ? BORDER : Color.rgb(42, 47, 50));
        page.addView(bottomNavDivider, lp(-1, dp(1)));
        page.addView(modeRow, lp(-1, dp(78)));
        setContentView(page);
        setControlsEnabled(false);
    }

    private LinearLayout buildPrintPanel() {
        LinearLayout box = card();
        Button resizePrint = compactButton("RIDIMENSIONA STAMPA");
        resizePrint.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "resize")));
        box.addView(resizePrint, margin(lp(-1, dp(46)), 0, 0, 0, 10));
        TextView prompt = text("Tempo di stampa", 16, TEXT_PRIMARY, true);
        prompt.setGravity(Gravity.CENTER);
        box.addView(prompt);
        printStepText = text(printStepDescription(), 12, MUTED, false);
        printStepText.setGravity(Gravity.CENTER);
        box.addView(printStepText);
        printFStopBadge = addFStopBadge(box, false);
        box.addView(space(12));

        LinearLayout selector = new LinearLayout(this);
        selector.setGravity(Gravity.CENTER);
        selector.setOrientation(LinearLayout.HORIZONTAL);
        Button minus = smallButton("−");
        Button plus = smallButton("+");
        printTimeText = text(formatTime(printWidthMs), 48, GREEN, true);
        printTimeText.setGravity(Gravity.CENTER);
        selector.addView(minus, lp(dp(62), dp(58)));
        selector.addView(printTimeText, lp(0, dp(68), 1f));
        selector.addView(plus, lp(dp(62), dp(58)));
        minus.setOnClickListener(v -> adjustPrintTime(-1));
        plus.setOnClickListener(v -> adjustPrintTime(+1));
        box.addView(selector);
        box.addView(space(12));

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(4);
        int[] secs = {2, 3, 4, 5, 6, 8, 10, 15};
        for (int s : secs) {
            Button b = shortcutButton(s + " s", GREEN);
            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
            gp.width = dp(74);
            gp.height = dp(46);
            gp.setMargins(dp(4), dp(4), dp(4), dp(4));
            grid.addView(b, gp);
            b.setOnClickListener(v -> setPrintTime(s * 1000));
        }
        box.addView(grid, lp(-1, -2));

        printSequenceButton = compactButton("PIANO DI STAMPA");
        printSequenceButton.setOnClickListener(v -> showPrintSequenceDialog());
        box.addView(printSequenceButton, margin(lp(-1, dp(50)), 0, 12, 0, 0));
        printSequenceSummary = text("", 12, darkroomMode ? RED : AMBER, false);
        printSequenceSummary.setGravity(Gravity.CENTER);
        printSequenceSummary.setPadding(dp(6), dp(6), dp(6), 0);
        box.addView(printSequenceSummary, lp(-1, -2));
        updatePrintSequenceUi();
        return box;
    }

    private void updatePrintSequenceUi() {
        if (printSequenceButton == null || printSequenceSummary == null) return;
        if (printSequence == null) printSequence = new PrintSequence();
        printSequenceButton.setText("PIANO DI STAMPA");

        boolean noLocalPlan = printSequence.isEmpty();
        boolean noRecipeCorrections = exposureRecipe == null || (exposureRecipe.densityQuarterSteps == 0 && exposureRecipe.globalQuarterStops == 0);
        if (noLocalPlan && noRecipeCorrections) {
            boolean hasBase = (exposureRecipe != null && exposureRecipe.hasBase()) || printWidthMs > 0;
            if (!hasBase) { printSequenceSummary.setText(""); printSequenceSummary.setVisibility(View.GONE); return; }
            StringBuilder one = new StringBuilder("STAMPA BASE · ").append(formatTime(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                String f=exposureRecipe.filterLabel();
                if (!"NESSUNO".equals(f)) one.append(" · ").append(f);
                one.append(" · ").append(exposureRecipe.densityLabel());
            }
            printSequenceSummary.setText(one.toString());
            printSequenceSummary.setVisibility(View.VISIBLE);
            return;
        }

        String base = recipeBaseSummary();
        boolean hasRecipe = !base.isEmpty() || !printSequence.isEmpty()
                || (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0);
        if (!hasRecipe) { printSequenceSummary.setText(""); printSequenceSummary.setVisibility(View.GONE); return; }

        StringBuilder s = new StringBuilder();
        if (!base.isEmpty()) s.append(base);
        if (s.length() > 0) s.append("\n\n");
        s.append("ESPOSIZIONE\n");
        if (printSequence.hasSplit()) s.append(printSequence.split.softLine()).append('\n').append(printSequence.split.hardLine());
        else {
            s.append("SINGOLA · ").append(formatTime(printWidthMs));
            if (exposureRecipe != null && exposureRecipe.hasBase()) {
                String f=exposureRecipe.filterLabel();
                if (!"NESSUNO".equals(f)) s.append(" · ").append(f);
                s.append(" · ").append(exposureRecipe.densityLabel());
            }
        }
        if (!printSequence.corrections.isEmpty()) {
            s.append("\n\nCORREZIONI");
            for (PrintCorrection c : printSequence.corrections) {
                if (c == null) continue;
                s.append('\n').append(c.displayLine(printSequence.baseMsFor(c, printWidthMs), printSequence.hasSplit()));
            }
        }
        if (exposureRecipe != null && exposureRecipe.globalQuarterStops != 0)
            s.append("\n\nCORREZIONE GLOBALE · ").append(exposureRecipe.globalLabel());
        printSequenceSummary.setText(s.toString());
        printSequenceSummary.setVisibility(View.VISIBLE);
    }

    private void persistPrintSequence() {
        if (printSequence == null) printSequence = new PrintSequence();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("printSequence", printSequence.encode()).apply();
        updatePrintSequenceUi();
        applyModeUi();
    }

    private SharedPreferences printRevisionPrefs() {
        return getSharedPreferences("print_revision", MODE_PRIVATE);
    }

    private boolean hasPrintRevisionDraft() {
        return printRevisionPrefs().getBoolean("active", false);
    }

    private void capturePrintRevisionDraft(String reason) {
        if (hasPrintRevisionDraft()) return;
        SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);
        printRevisionPrefs().edit().clear()
                .putBoolean("active", true)
                .putString("reason", reason == null ? "" : reason)
                .putLong("sourceLogId", ui.getLong("activeSourceLogId", 0L))
                .putString("previousPrintSequence", printSequence == null ? "" : printSequence.encode())
                .putString("previousRecipeState", exposureRecipe == null ? "" : exposureRecipe.encode())
                .putInt("previousPrintMs", printWidthMs)
                .apply();
    }

    private void clearPrintRevisionDraft() {
        printRevisionPrefs().edit().clear().apply();
    }

    private void clearRevisionSessionMetadata() {
        getSharedPreferences("log_session", MODE_PRIVATE).edit()
                .remove("lastSplitTimeOrigin")
                .remove("lastSplitSoftChosenStrip")
                .remove("lastSplitHardChosenStrip")
                .remove("lastRevisionPreviousId")
                .remove("lastRevisionPreviousRecipeState")
                .remove("lastRevisionPreviousPrintSequence")
                .remove("lastRevisionReason")
                .apply();
    }

    private void commitPrintRevisionMetadata(String origin) {
        SharedPreferences r = printRevisionPrefs();
        boolean active = r.getBoolean("active", false);
        getSharedPreferences("log_session", MODE_PRIVATE).edit()
                .putString("lastSplitTimeOrigin", origin == null ? "" : origin)
                .putInt("lastSplitSoftChosenStrip", splitSoftChosenStrip)
                .putInt("lastSplitHardChosenStrip", splitHardChosenStrip)
                .putLong("lastRevisionPreviousId", active ? r.getLong("sourceLogId", 0L) : 0L)
                .putString("lastRevisionPreviousRecipeState", active ? r.getString("previousRecipeState", "") : "")
                .putString("lastRevisionPreviousPrintSequence", active ? r.getString("previousPrintSequence", "") : "")
                .putString("lastRevisionReason", active ? r.getString("reason", "") : "")
                .apply();
        clearPrintRevisionDraft();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("activeSourceLogId", 0L).apply();
    }

    private void rememberTestStateForRevision() {
        splitReturnFilterType = testBaseFilterType;
        splitReturnFilterValue = testBaseFilterValue;
        splitReturnTestWidthMs = testWidthMs;
    }

    private void persistRevisionTestSetup() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(testBaseFilterType))
                .putInt("testBaseFilterValue", ExposureRecipe.snap5(testBaseFilterValue))
                .apply();
        persistTestBaseFilter();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setMode(MODE_TEST);
    }

    private void beginSingleRevisionFromPrint() {
        if (armed) return;
        capturePrintRevisionDraft("RIFAI_PROVINO_SINGOLO");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SINGLE;
        testWidthMs = snap(printWidthMs, 500, 30_000);
        if (exposureRecipe != null && exposureRecipe.hasBase()) {
            testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);
            testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);
        }
        persistRevisionTestSetup();
        setStatusPresentation("RIFAI PROVINO SINGOLO",
                "Filtro e tempo correnti sono solo valori iniziali modificabili. La ricetta precedente resta intatta finché non scegli una nuova striscia.", BLUE);
    }

    private void beginSplitFromSingleWithProvino() {
        if (armed) return;
        capturePrintRevisionDraft("SINGOLA_A_SPLIT_PROVINO");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SPLIT_SOFT;
        splitSoftYellow = 60;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        splitHardMagenta = 130;
        invalidateSplitHardChoice();
        // T/2 is deliberately only a convenient editable starting point, never a conversion.
        testWidthMs = snap(Math.max(500, printWidthMs / 2), 500, 30_000);
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        persistRevisionTestSetup();
        setStatusPresentation("SPLIT GRADE — TROVA I TEMPI",
                "Il tempo singolo precedente è usato solo per suggerire un centro iniziale T/2, liberamente modificabile. Non è una conversione né una compensazione.", BLUE);
    }

    private void beginSplitRevisionFromPrint(boolean hardOnly) {
        if (armed || printSequence == null || !printSequence.hasSplit()) return;
        capturePrintRevisionDraft(hardOnly ? "RIFAI_SOLO_DURO" : "RIFAI_ENTRAMBI");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        splitSoftYellow = ExposureRecipe.snap5(printSequence.split.softYellow);
        splitHardMagenta = ExposureRecipe.snap5(printSequence.split.hardMagenta);
        splitSoftChosenMs = hardOnly ? snap(printSequence.split.softMs, 500, 36_000_000) : 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        if (hardOnly) {
            provinoFlow = PROVINO_SPLIT_HARD;
            testWidthMs = snap(printSequence.split.hardMs, 500, 30_000);
            testBaseFilterType = ExposureRecipe.FILTER_MAGENTA;
            testBaseFilterValue = splitHardMagenta;
        } else {
            provinoFlow = PROVINO_SPLIT_SOFT;
            testWidthMs = snap(printSequence.split.softMs, 500, 30_000);
            testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
            testBaseFilterValue = splitSoftYellow;
        }
        persistRevisionTestSetup();
        setStatusPresentation(hardOnly ? "RIFAI SOLO IL DURO" : "RIFAI ENTRAMBI",
                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                BLUE);
    }

    private void cancelPrintRevisionToPrint() {
        if (!hasPrintRevisionDraft()) return;
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SINGLE;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs = snap(splitReturnTestWidthMs, 500, 30_000);
        clearPrintRevisionDraft();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestBaseFilterUi();
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setMode(MODE_PRINT);
        setStatusPresentation("REVISIONE ANNULLATA",
                "La ricetta di stampa precedente è rimasta invariata.", GREEN);
    }

    private LinearLayout buildSplitHowToCard() {
        LinearLayout info = card();
        info.setPadding(dp(12), dp(10), dp(12), dp(10));
        info.addView(text("COME SI USA", 13, SPLIT_VIVA_MAGENTA, true), lp(-1,-2));
        TextView body = text(
                "Lo Split Grade usa due esposizioni distinte, non due filtri contemporaneamente.\n"
                        + "1. Morbido: prova Y60 / M0 e scegli il tempo che rende soprattutto i toni chiari.\n"
                        + "2. Duro: su una nuova striscia applica il morbido scelto su tutta la carta, poi prova Y0 / M130 e scegli il miglior equilibrio di ombre e neri.\n"
                        + "3. Stampa: esegui le due esposizioni una dopo l’altra. Se cambi il morbido, devi ricontrollare il duro.\n\n"
                        + "Morbido e duro sono due esposizioni consecutive. Non impostare Y e M contemporaneamente.",
                11, MUTED, false);
        body.setLineSpacing(0, 1.08f);
        body.setPadding(0, dp(5), 0, 0);
        info.addView(body, lp(-1,-2));
        return info;
    }

    private LinearLayout buildManualSplitEditor(final Dialog owner) {
        LinearLayout panel = card();
        panel.setPadding(dp(12), dp(10), dp(12), dp(10));
        panel.setVisibility(View.GONE);
        panel.addView(text("INSERISCI TEMPI GIÀ NOTI", 14, SPLIT_VIVA_MAGENTA, true), lp(-1,-2));
        TextView note = text("Inserisci indipendentemente filtro e tempo morbido e filtro e tempo duro. Nessuna divisione 50/50, nessun vincolo sulla somma e nessuna compensazione automatica.", 11, MUTED, false);
        note.setPadding(0, dp(4), 0, dp(8)); panel.addView(note, lp(-1,-2));

        final int[] sy = {printSequence != null && printSequence.hasSplit() ? ExposureRecipe.snap5(printSequence.split.softYellow) : 60};
        final int[] sm = {printSequence != null && printSequence.hasSplit() ? printSequence.split.softMs : Math.max(500, splitSoftChosenMs > 0 ? splitSoftChosenMs : 500)};
        final int[] hm = {printSequence != null && printSequence.hasSplit() ? ExposureRecipe.snap5(printSequence.split.hardMagenta) : 130};
        final int[] ht = {printSequence != null && printSequence.hasSplit() ? printSequence.split.hardMs : Math.max(500, splitHardChosenMs > 0 ? splitHardChosenMs : 500)};

        panel.addView(text("MORBIDO · GIALLO", 11, MUTED, true), margin(lp(-1,-2),0,2,0,3));
        LinearLayout yr = new LinearLayout(this); yr.setOrientation(LinearLayout.HORIZONTAL); yr.setGravity(Gravity.CENTER);
        Button ym=smallButton("−"); Button yp=smallButton("+"); TextView yv=text(sy[0]+"Y / 0M",22,SPLIT_VIVA_MAGENTA,true); yv.setGravity(Gravity.CENTER);
        yr.addView(ym,lp(dp(58),dp(52))); yr.addView(yv,lp(0,dp(56),1f)); yr.addView(yp,lp(dp(58),dp(52))); panel.addView(yr,lp(-1,-2));
        ym.setOnClickListener(v->{sy[0]=Math.max(0,sy[0]-5);yv.setText(sy[0]+"Y / 0M");});
        yp.setOnClickListener(v->{sy[0]=Math.min(200,sy[0]+5);yv.setText(sy[0]+"Y / 0M");});
        LinearLayout sr=new LinearLayout(this); sr.setOrientation(LinearLayout.HORIZONTAL); sr.setGravity(Gravity.CENTER);
        Button stm=smallButton("−"); Button stp=smallButton("+"); TextView stv=text(formatTime(sm[0]),24,SPLIT_VIVA_MAGENTA,true); stv.setGravity(Gravity.CENTER);
        sr.addView(stm,lp(dp(58),dp(52)));sr.addView(stv,lp(0,dp(56),1f));sr.addView(stp,lp(dp(58),dp(52)));panel.addView(sr,margin(lp(-1,-2),0,0,0,6));
        stm.setOnClickListener(v->{sm[0]=Math.max(500,sm[0]-500);stv.setText(formatTime(sm[0]));});
        stp.setOnClickListener(v->{sm[0]=Math.min(36_000_000,sm[0]+500);stv.setText(formatTime(sm[0]));});

        panel.addView(text("DURO · MAGENTA", 11, MUTED, true), margin(lp(-1,-2),0,2,0,3));
        LinearLayout mr = new LinearLayout(this); mr.setOrientation(LinearLayout.HORIZONTAL); mr.setGravity(Gravity.CENTER);
        Button mm=smallButton("−"); Button mp=smallButton("+"); TextView mv=text("0Y / "+hm[0]+"M",22,SPLIT_VIVA_MAGENTA,true); mv.setGravity(Gravity.CENTER);
        mr.addView(mm,lp(dp(58),dp(52))); mr.addView(mv,lp(0,dp(56),1f)); mr.addView(mp,lp(dp(58),dp(52))); panel.addView(mr,lp(-1,-2));
        mm.setOnClickListener(v->{hm[0]=Math.max(0,hm[0]-5);mv.setText("0Y / "+hm[0]+"M");});
        mp.setOnClickListener(v->{hm[0]=Math.min(200,hm[0]+5);mv.setText("0Y / "+hm[0]+"M");});
        LinearLayout hr=new LinearLayout(this); hr.setOrientation(LinearLayout.HORIZONTAL); hr.setGravity(Gravity.CENTER);
        Button htm=smallButton("−"); Button htp=smallButton("+"); TextView htv=text(formatTime(ht[0]),24,SPLIT_VIVA_MAGENTA,true); htv.setGravity(Gravity.CENTER);
        hr.addView(htm,lp(dp(58),dp(52)));hr.addView(htv,lp(0,dp(56),1f));hr.addView(htp,lp(dp(58),dp(52)));panel.addView(hr,margin(lp(-1,-2),0,0,0,8));
        htm.setOnClickListener(v->{ht[0]=Math.max(500,ht[0]-500);htv.setText(formatTime(ht[0]));});
        htp.setOnClickListener(v->{ht[0]=Math.min(36_000_000,ht[0]+500);htv.setText(formatTime(ht[0]));});

        Button save=compactButton("SALVA TEMPI SPLIT GRADE"); save.setTextColor(Color.WHITE); save.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0));
        save.setOnClickListener(v->{
            capturePrintRevisionDraft(printSequence != null && printSequence.hasSplit() ? "MODIFICA_SPLIT_MANUALE" : "SINGOLA_A_SPLIT_MANUALE");
            SplitGradePlan plan=new SplitGradePlan(); plan.enabled=true; plan.softYellow=sy[0]; plan.softMs=sm[0]; plan.hardMagenta=hm[0]; plan.hardMs=ht[0]; plan.sanitize();
            PrintSequence next=new PrintSequence(); next.split=plan;
            printSequence=next; // A new base never inherits old Dodge/Burn silently.
            splitSoftYellow=plan.softYellow; splitSoftChosenMs=plan.softMs; splitSoftChosenStrip=-1;
            splitHardMagenta=plan.hardMagenta; splitHardChosenMs=plan.hardMs; splitHardChosenStrip=-1;
            commitPrintRevisionMetadata("MANUALE");
            persistPrintSequence();
            owner.dismiss();
            setStatusPresentation("SPLIT GRADE — TEMPI INSERITI",
                    "Morbido e duro restano due esposizioni indipendenti e consecutive. Nessuna compensazione applicata.", GREEN);
        });
        panel.addView(save, lp(-1,dp(50)));
        Button hide=compactButton("ANNULLA"); hide.setOnClickListener(v->panel.setVisibility(View.GONE)); panel.addView(hide,margin(lp(-1,dp(46)),0,7,0,0));
        return panel;
    }

    private void showPrintSequenceDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));
        panel.addView(text("PIANO DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1,-2));

        String base = recipeBaseSummary();
        if (!base.isEmpty()) {
            TextView baseInfo=text(base,13,darkroomMode?RED:GREEN,true);
            baseInfo.setPadding(0,dp(6),0,dp(10));
            panel.addView(baseInfo,lp(-1,-2));
        }

        panel.addView(text("ESPOSIZIONE",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
        final LinearLayout manualEditor = buildManualSplitEditor(dialog);
        if (printSequence != null && printSequence.hasSplit()) {
            Button splitRow=compactButton("SPLIT GRADE  ·  MORBIDO "+printSequence.split.softYellow+"Y / 0M · "+formatTime(printSequence.split.softMs)+"  ·  DURO 0Y / "+printSequence.split.hardMagenta+"M · "+formatTime(printSequence.split.hardMs));
            splitRow.setTextColor(Color.WHITE); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_VIVA_MAGENTA,8,0,0)); splitRow.setEnabled(false);
            panel.addView(splitRow,margin(lp(-1,dp(62)),0,0,0,7));
            if(!darkroomMode){
                Button hard=compactButton("RIFAI SOLO IL DURO"); hard.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(true);}); panel.addView(hard,margin(lp(-1,dp(48)),0,0,0,6));
                Button both=compactButton("RIFAI ENTRAMBI"); both.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(false);}); panel.addView(both,margin(lp(-1,dp(48)),0,0,0,6));
                Button known=compactButton("MODIFICA / INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,9));
            }
        } else {
            String f=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.filterLabel():"NESSUNO";
            String d=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.densityLabel():"D0";
            String label="SINGOLA  ·  "+formatTime(printWidthMs)+("NESSUNO".equals(f)?"":" · "+f)+" · "+d;
            Button single=compactButton(label); single.setTextColor(Color.WHITE); single.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),8,0,0)); single.setEnabled(false);
            panel.addView(single,margin(lp(-1,dp(52)),0,0,0,7));
            if(!darkroomMode){
                Button guided=compactButton("TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO"); guided.setTextColor(Color.WHITE); guided.setBackground(roundRect(SPLIT_VIVA_MAGENTA,8,0,0)); guided.setOnClickListener(v->{dialog.dismiss();beginSplitFromSingleWithProvino();}); panel.addView(guided,margin(lp(-1,dp(52)),0,0,0,6));
                Button known=compactButton("INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,6));
                Button retest=compactButton("RIFAI PROVINO SINGOLO"); retest.setOnClickListener(v->{dialog.dismiss();beginSingleRevisionFromPrint();}); panel.addView(retest,margin(lp(-1,dp(48)),0,0,0,9));
            }
        }
        panel.addView(manualEditor, margin(lp(-1,-2),0,2,0,8));
        panel.addView(buildSplitHowToCard(), margin(lp(-1,-2),0,2,0,10));

        panel.addView(text("CORREZIONI LOCALI",12,MUTED,true),margin(lp(-1,-2),0,4,0,5));
        if(printSequence!=null){
            for(int x=0;x<printSequence.corrections.size();x++){
                final int index=x; PrintCorrection c=printSequence.corrections.get(x); int baseMs=printSequence.baseMsFor(c,printWidthMs);
                Button row=compactButton(c.displayLine(baseMs,printSequence.hasSplit())); int fc=c.isDodge()?DODGE_BISCAY_BAY:BURN_RUST;
                row.setTextColor(Color.WHITE); row.setBackground(roundRect(darkroomMode?RED:fc,8,0,0));
                if(!darkroomMode) row.setOnClickListener(v->{dialog.dismiss();showPrintCorrectionEditor(index);}); else row.setEnabled(false);
                panel.addView(row,margin(lp(-1,dp(50)),0,0,0,7));
            }
        }
        if(!darkroomMode){
            Button dodge=compactButton("+  DODGE"); dodge.setTextColor(Color.WHITE); dodge.setBackground(roundRect(DODGE_BISCAY_BAY,8,0,0)); dodge.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.DODGE);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            Button burn=compactButton("+  BURN"); burn.setTextColor(Color.WHITE); burn.setBackground(roundRect(BURN_RUST,8,0,0)); burn.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.BURN);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            LinearLayout addRow=new LinearLayout(this); addRow.setOrientation(LinearLayout.HORIZONTAL); addRow.addView(dodge,margin(lp(0,dp(50),1f),0,0,dp(4),0)); addRow.addView(burn,margin(lp(0,dp(50),1f),dp(4),0,0,0)); panel.addView(addRow,margin(lp(-1,-2),0,0,0,12));

            panel.addView(text("STRUMENTI",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
            boolean lengthReady=canLengthenTimes();
            Button length=compactButton(lengthReady?"ALLUNGA TEMPI":"ALLUNGA TEMPI · DOPO LA PRIMA STAMPA");
            length.setTextColor(Color.WHITE); length.setBackground(roundRect(lengthReady?ALLUNGA_COLOR:Color.rgb(55,60,64),8,0,0)); length.setEnabled(lengthReady); length.setAlpha(lengthReady?1f:0.55f);
            if(lengthReady) length.setOnClickListener(v->{dialog.dismiss();showLengthenTimesDialog();}); panel.addView(length,lp(-1,dp(52)));

            Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(Color.WHITE); global.setBackground(roundRect(Color.rgb(55,60,64),8,0,0)); global.setOnClickListener(v->{dialog.dismiss();showGlobalCorrectionDialog();}); panel.addView(global,margin(lp(-1,dp(50)),0,7,0,0));

            if((printSequence!=null&&!printSequence.isEmpty()) || (exposureRecipe!=null&&(exposureRecipe.densityQuarterSteps>0||exposureRecipe.globalQuarterStops!=0))){
                Button clear=compactButton("RIMUOVI CORREZIONI"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("RIMUOVERE LE CORREZIONI?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La stampa base trovata con il provino resta disponibile.","RIMUOVI",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA")); panel.addView(clear,margin(lp(-1,dp(46)),0,10,0,0));
            }
        } else {
            TextView darkNote=text("In modalità camera oscura il piano è consultabile ma non modificabile.",11,RED,false); darkNote.setGravity(Gravity.CENTER); panel.addView(darkNote,margin(lp(-1,-2),0,8,0,0));
        }
        Button close=compactButton("CHIUDI"); close.setTextColor(Color.WHITE); close.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),9,0,0)); close.setOnClickListener(v->dialog.dismiss()); panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(sc); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.90f));
    }

    private void showPlanTypeDialog() {
        showPrintSequenceDialog();
    }

    private void showSplitGradeEditor(final boolean creating) {
        // v0.2.6: Split Grade has one management surface only: PIANO DI STAMPA.
        // The former editor divided the single time ~50/50 and imposed a sum cap;
        // both behaviours are intentionally removed.
        if (darkroomMode) return;
        showPrintSequenceDialog();
    }

    private void showPrintCorrectionEditor(final int index) {
        if (darkroomMode || printSequence == null || index < 0 || index >= printSequence.corrections.size()) return;
        final PrintCorrection original = printSequence.corrections.get(index);
        final boolean creatingCorrection = original.label == null || original.label.trim().isEmpty();
        final PrintCorrection c = original.copy();
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));

        final int featureColor = c.isDodge() ? DODGE_BISCAY_BAY : BURN_RUST;
        panel.addView(text(c.isDodge() ? "DODGE" : "BURN", 19, featureColor, true), lp(-1, -2));
        TextView explain = text(c.isDodge()
                ? "Riduce l’esposizione durante la base. Con Split Grade scegli se applicarlo al giallo, al magenta o a entrambe le fasi."
                : "Aggiunge una nuova esposizione dopo la base. Con Split Grade scegli il filtro del BURN.", 12, MUTED, false);
        explain.setPadding(0, dp(4), 0, dp(10)); panel.addView(explain, lp(-1,-2));

        final EditText label = editField(c.isDodge() ? "Zona / maschera — es. Volto" : "Zona — es. Cielo", c.label);
        panel.addView(label, margin(lp(-1, dp(52)),0,0,0,10));

        final String[] phase = {printSequence.hasSplit()
                ? (c.isBoth() ? PrintCorrection.PHASE_BOTH : (c.isHard() ? PrintCorrection.PHASE_HARD : PrintCorrection.PHASE_SOFT))
                : PrintCorrection.PHASE_BASE};
        final String[] burnMode = {PrintCorrection.normalizeBurnFilter(c.burnFilterMode)};
        final int[] burnFilterValue = {PrintCorrection.snap5(c.burnFilterValue)};

        if (printSequence.hasSplit() && c.isDodge()) {
            panel.addView(text("APPLICA DURANTE",11,MUTED,true), margin(lp(-1,-2),0,0,0,4));
            LinearLayout phases=new LinearLayout(this); phases.setOrientation(LinearLayout.HORIZONTAL);
            final Button soft=compactButton("GIALLO");
            final Button hard=compactButton("MAGENTA");
            final Button both=compactButton("ENTRAMBE");
            final Runnable style=()->{
                boolean sft=PrintCorrection.PHASE_SOFT.equals(phase[0]);
                boolean hrd=PrintCorrection.PHASE_HARD.equals(phase[0]);
                boolean bth=PrintCorrection.PHASE_BOTH.equals(phase[0]);
                soft.setBackground(roundRect(sft?featureColor:Color.rgb(55,60,64),8,0,0));
                hard.setBackground(roundRect(hrd?featureColor:Color.rgb(55,60,64),8,0,0));
                both.setBackground(roundRect(bth?featureColor:Color.rgb(55,60,64),8,0,0));
                soft.setTextColor(Color.WHITE); hard.setTextColor(Color.WHITE); both.setTextColor(Color.WHITE);
            };
            soft.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_SOFT;style.run();});
            hard.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_HARD;style.run();});
            both.setOnClickListener(v->{phase[0]=PrintCorrection.PHASE_BOTH;style.run();});
            style.run();
            phases.addView(soft,margin(lp(0,dp(46),1f),0,0,dp(3),0));
            phases.addView(hard,margin(lp(0,dp(46),1f),dp(3),0,dp(3),0));
            phases.addView(both,margin(lp(0,dp(46),1f),dp(3),0,0,0));
            panel.addView(phases,margin(lp(-1,-2),0,0,0,10));
        }

        final LinearLayout customFilterPanel = new LinearLayout(this);
        customFilterPanel.setOrientation(LinearLayout.VERTICAL);
        if (printSequence.hasSplit() && c.isBurn()) {
            panel.addView(text("FILTRO DEL BURN",11,MUTED,true), margin(lp(-1,-2),0,0,0,4));
            LinearLayout filters=new LinearLayout(this); filters.setOrientation(LinearLayout.HORIZONTAL);
            final Button fy=compactButton("GIALLO SPLIT");
            final Button fm=compactButton("MAGENTA SPLIT");
            final Button fc=compactButton("PERSONALIZZATO");
            final Runnable[] filterStyle = new Runnable[1];
            filterStyle[0]=()->{
                String m=PrintCorrection.normalizeBurnFilter(burnMode[0]);
                boolean y=PrintCorrection.BURN_FILTER_Y_SPLIT.equals(m);
                boolean mg=PrintCorrection.BURN_FILTER_M_SPLIT.equals(m);
                boolean custom=!y&&!mg;
                fy.setBackground(roundRect(y?featureColor:Color.rgb(55,60,64),8,0,0));
                fm.setBackground(roundRect(mg?featureColor:Color.rgb(55,60,64),8,0,0));
                fc.setBackground(roundRect(custom?featureColor:Color.rgb(55,60,64),8,0,0));
                fy.setTextColor(Color.WHITE); fm.setTextColor(Color.WHITE); fc.setTextColor(Color.WHITE);
                customFilterPanel.setVisibility(custom?View.VISIBLE:View.GONE);
            };
            fy.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_Y_SPLIT;phase[0]=PrintCorrection.PHASE_SOFT;filterStyle[0].run();});
            fm.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_M_SPLIT;phase[0]=PrintCorrection.PHASE_HARD;filterStyle[0].run();});
            fc.setOnClickListener(v->{
                if(!PrintCorrection.BURN_FILTER_CUSTOM_Y.equals(burnMode[0])&&!PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0]))
                    burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_Y;
                phase[0]=PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0])?PrintCorrection.PHASE_HARD:PrintCorrection.PHASE_SOFT;
                filterStyle[0].run();
            });
            filters.addView(fy,margin(lp(0,dp(48),1f),0,0,dp(3),0));
            filters.addView(fm,margin(lp(0,dp(48),1f),dp(3),0,dp(3),0));
            filters.addView(fc,margin(lp(0,dp(48),1f),dp(3),0,0,0));
            panel.addView(filters,margin(lp(-1,-2),0,0,0,7));

            customFilterPanel.addView(text("FILTRO PERSONALIZZATO",11,MUTED,true),margin(lp(-1,-2),0,2,0,4));
            LinearLayout customType=new LinearLayout(this); customType.setOrientation(LinearLayout.HORIZONTAL);
            final Button cy=compactButton("GIALLO"); final Button cm=compactButton("MAGENTA");
            customType.addView(cy,margin(lp(0,dp(44),1f),0,0,dp(4),0));
            customType.addView(cm,margin(lp(0,dp(44),1f),dp(4),0,0,0));
            customFilterPanel.addView(customType,lp(-1,-2));
            LinearLayout customValueRow=new LinearLayout(this); customValueRow.setOrientation(LinearLayout.HORIZONTAL); customValueRow.setGravity(Gravity.CENTER);
            Button cfMinus=smallButton("−"); Button cfPlus=smallButton("+");
            final TextView cfValue=text("",28,featureColor,true); cfValue.setGravity(Gravity.CENTER);
            customValueRow.addView(cfMinus,lp(dp(62),dp(56))); customValueRow.addView(cfValue,lp(0,dp(60),1f)); customValueRow.addView(cfPlus,lp(dp(62),dp(56)));
            customFilterPanel.addView(customValueRow,lp(-1,-2));
            final Runnable customStyle=()->{
                boolean mag=PrintCorrection.BURN_FILTER_CUSTOM_M.equals(burnMode[0]);
                cy.setBackground(roundRect(!mag?featureColor:Color.rgb(55,60,64),8,0,0));
                cm.setBackground(roundRect(mag?featureColor:Color.rgb(55,60,64),8,0,0));
                cy.setTextColor(Color.WHITE);cm.setTextColor(Color.WHITE);
                cfValue.setText((mag?"M ":"Y ")+burnFilterValue[0]);
            };
            cy.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_Y;phase[0]=PrintCorrection.PHASE_SOFT;customStyle.run();filterStyle[0].run();});
            cm.setOnClickListener(v->{burnMode[0]=PrintCorrection.BURN_FILTER_CUSTOM_M;phase[0]=PrintCorrection.PHASE_HARD;customStyle.run();filterStyle[0].run();});
            cfMinus.setOnClickListener(v->{burnFilterValue[0]=Math.max(0,burnFilterValue[0]-5);customStyle.run();});
            cfPlus.setOnClickListener(v->{burnFilterValue[0]=Math.min(200,burnFilterValue[0]+5);customStyle.run();});
            customStyle.run();
            panel.addView(customFilterPanel,margin(lp(-1,-2),0,0,0,10));
            filterStyle[0].run();
        }

        final boolean[] useStops={c.quarterStops>0};
        final int[] ms={Math.max(c.isDodge()?1000:500,c.milliseconds)};
        final int[] quarters={Math.max(1,c.quarterStops>0?c.quarterStops:1)};
        LinearLayout methods=new LinearLayout(this); methods.setOrientation(LinearLayout.HORIZONTAL);
        final Button secondsMode=compactButton("SECONDI"); final Button stopMode=compactButton("F-STOP");
        methods.addView(secondsMode,margin(lp(0,dp(46),1f),0,0,dp(4),0)); methods.addView(stopMode,margin(lp(0,dp(46),1f),dp(4),0,0,0)); panel.addView(methods,margin(lp(-1,-2),0,0,0,10));
        final Runnable styleMethods=()->{
            secondsMode.setBackground(roundRect(!useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));
            stopMode.setBackground(roundRect(useStops[0]?featureColor:Color.rgb(55,60,64),8,0,0));
            secondsMode.setTextColor(Color.WHITE);stopMode.setTextColor(Color.WHITE);
        };

        LinearLayout selector=new LinearLayout(this); selector.setOrientation(LinearLayout.HORIZONTAL); selector.setGravity(Gravity.CENTER);
        Button minus=smallButton("−"); Button plus=smallButton("+"); final TextView value=text("",30,featureColor,true); value.setGravity(Gravity.CENTER); value.setSingleLine(true);
        selector.addView(minus,lp(dp(62),dp(58))); selector.addView(value,lp(0,dp(64),1f)); selector.addView(plus,lp(dp(62),dp(58))); panel.addView(selector,lp(-1,-2));
        final Runnable refresh=()->{
            if(useStops[0]) value.setText(c.isDodge()?TimingMath.dodgeStopLabel(quarters[0]):TimingMath.stopLabel(quarters[0]));
            else value.setText(formatTime(ms[0]));
        };
        secondsMode.setOnClickListener(v->{useStops[0]=false;styleMethods.run();refresh.run();});
        stopMode.setOnClickListener(v->{useStops[0]=true;styleMethods.run();refresh.run();});
        minus.setOnClickListener(v->{if(useStops[0])quarters[0]=Math.max(1,quarters[0]-1);else ms[0]=Math.max(c.isDodge()?1000:500,ms[0]-500);refresh.run();});
        plus.setOnClickListener(v->{
            if(useStops[0]) quarters[0]=Math.min(16,quarters[0]+1);
            else if(c.isDodge()){
                int baseMs;
                if(printSequence.hasSplit()&&PrintCorrection.PHASE_BOTH.equals(phase[0])) baseMs=Math.min(printSequence.split.softMs,printSequence.split.hardMs);
                else baseMs=printSequence.baseMsForPhase(phase[0],printWidthMs);
                ms[0]=Math.min(Math.max(1000,baseMs-500),ms[0]+500);
            } else ms[0]=Math.min(36000000,ms[0]+500);
            refresh.run();
        });
        styleMethods.run(); refresh.run();

        Button save=compactButton("SALVA CORREZIONE"); save.setBackground(roundRect(featureColor,9,0,0)); save.setTextColor(Color.WHITE);
        save.setOnClickListener(v->{
            String name=label.getText().toString().trim();
            c.label=name.isEmpty()?(c.isDodge()?"Zona da mascherare":"Zona da bruciare"):name;
            if(c.isDodge()){
                c.phase=printSequence.hasSplit()?phase[0]:PrintCorrection.PHASE_BASE;
                int baseMs=(printSequence.hasSplit()&&c.isBoth())?Math.min(printSequence.split.softMs,printSequence.split.hardMs):printSequence.baseMsFor(c,printWidthMs);
                if(useStops[0]){
                    c.quarterStops=quarters[0]; c.milliseconds=c.resolvedMs(baseMs);
                } else {
                    if(baseMs<=1000){Toast.makeText(this,"Il DODGE richiede una fase superiore a 1,0 s",Toast.LENGTH_LONG).show();return;}
                    c.quarterStops=0; c.milliseconds=TimingMath.snap500(ms[0],1000,Math.max(1000,baseMs-500));
                }
            } else {
                c.burnFilterMode=printSequence.hasSplit()?PrintCorrection.normalizeBurnFilter(burnMode[0]):PrintCorrection.BURN_FILTER_Y_SPLIT;
                c.burnFilterValue=PrintCorrection.snap5(burnFilterValue[0]);
                c.phase=printSequence.hasSplit()?(c.burnUsesMagenta()?PrintCorrection.PHASE_HARD:PrintCorrection.PHASE_SOFT):PrintCorrection.PHASE_BASE;
                int baseMs=printSequence.baseMsFor(c,printWidthMs);
                if(useStops[0]){c.quarterStops=quarters[0];c.milliseconds=c.resolvedMs(baseMs);}
                else{c.quarterStops=0;c.milliseconds=TimingMath.snap500(ms[0],500,36000000);}
            }
            printSequence.corrections.set(index,c);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();
        });
        panel.addView(save,margin(lp(-1,dp(52)),0,12,0,0));

        Button delete=compactButton("ELIMINA CORREZIONE");delete.setTextColor(Color.WHITE);delete.setBackground(roundRect(RED,9,0,0));
        delete.setOnClickListener(v->{printSequence.corrections.remove(index);persistPrintSequence();dialog.dismiss();showPrintSequenceDialog();});
        panel.addView(delete,margin(lp(-1,dp(48)),0,8,0,0));

        Button close=compactButton("ANNULLA");close.setTextColor(Color.WHITE);close.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
        close.setOnClickListener(v->{
            if(creatingCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index)==original){
                printSequence.corrections.remove(index); persistPrintSequence();
            }
            dialog.dismiss(); showPrintSequenceDialog();
        });
        panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel);Window w=dialog.getWindow();if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent);dialog.show();
        if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.96f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private boolean validatePrintSequenceForBase() {
        if (printSequence == null || printSequence.isEmpty()) return true;
        if (printSequence.hasSplit()) {
            // I due tempi Split Grade sono esposizioni sperimentali distinte.
            // Non esiste alcun vincolo rispetto al vecchio tempo singolo.
            printSequence.split.sanitize();
        }
        for (PrintCorrection c : printSequence.dodges()) {
            if (printSequence.hasSplit() && c.isBoth()) {
                int softCue = c.resolvedMs(printSequence.split.softMs);
                int hardCue = c.resolvedMs(printSequence.split.hardMs);
                if (softCue >= printSequence.split.softMs || hardCue >= printSequence.split.hardMs) {
                    setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": deve poter terminare prima della fine sia del giallo sia del magenta", RED);
                    return false;
                }
                continue;
            }
            int baseMs = printSequence.baseMsFor(c, printWidthMs);
            int cueMs = c.resolvedMs(baseMs);
            if (cueMs >= baseMs) {
                setStatusPresentation("ATTENZIONE", "DODGE " + c.safeLabel() + ": il cue deve avvenire prima della fine della esposizione " + (printSequence.hasSplit() ? (c.isHard() ? "magenta" : "gialla") : "base"), RED);
                return false;
            }
        }
        return true;
    }

    private String testBaseFilterButtonLabel() {
        String f = ExposureRecipe.filterLabel(testBaseFilterType, testBaseFilterValue);
        int grade = lplGradeFor(testBaseFilterType, testBaseFilterValue);
        if (provinoFlow == PROVINO_SINGLE && grade >= 0)
            return "CONTRASTO LPL · GRADO " + grade + " · " + lplGradeFilters(grade);
        return "FILTRO BASE · " + ("NESSUNO".equals(f) ? "NESSUNO" : f);
    }

    private int lplGradeFor(String type, int value) {
        int[] yellow = {60, 30, 0, 0, 0, 0};
        int[] magenta = {0, 0, 10, 40, 90, 130};
        String t = ExposureRecipe.normalizeFilter(type);
        int v = ExposureRecipe.snap5(value);
        for (int grade = 0; grade <= 5; grade++) {
            if (yellow[grade] > 0 && ExposureRecipe.FILTER_YELLOW.equals(t) && v == yellow[grade]) return grade;
            if (magenta[grade] > 0 && ExposureRecipe.FILTER_MAGENTA.equals(t) && v == magenta[grade]) return grade;
        }
        return -1;
    }

    private String lplGradeFilters(int grade) {
        String[] filters = {"Y60 / M0", "Y30 / M0", "Y0 / M10", "Y0 / M40", "Y0 / M90", "Y0 / M130"};
        return filters[Math.max(0, Math.min(5, grade))];
    }

    private void showLplGradeDialog() {
        String[] choices = {
                "GRADO 0 · Y60 / M0", "GRADO 1 · Y30 / M0", "GRADO 2 · Y0 / M10",
                "GRADO 3 · Y0 / M40", "GRADO 4 · Y0 / M90", "GRADO 5 · Y0 / M130",
                "VALORE MANUALE M/Y", "NESSUNO"
        };
        showAppChoiceDialog("CONTRASTO JOBO/LPL 7451", choices, which -> {
            if (which >= 0 && which <= 5) {
                int[] yellow = {60, 30, 0, 0, 0, 0};
                int[] magenta = {0, 0, 10, 40, 90, 130};
                testBaseFilterType = yellow[which] > 0 ? ExposureRecipe.FILTER_YELLOW : ExposureRecipe.FILTER_MAGENTA;
                testBaseFilterValue = yellow[which] > 0 ? yellow[which] : magenta[which];
                persistTestBaseFilter();
            } else if (which == 6) {
                showAppChoiceDialog("VALORE MANUALE LPL", new String[]{"MAGENTA (M)", "GIALLO (Y)"},
                        channel -> showTestBaseFilterValueDialog(channel == 0 ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW), "ANNULLA");
            } else {
                testBaseFilterType = ExposureRecipe.FILTER_NONE;
                testBaseFilterValue = 0;
                persistTestBaseFilter();
            }
        }, "ANNULLA");
    }

    private void refreshTestBaseFilterUi() {
        if (testBaseFilterButton != null) testBaseFilterButton.setText(testBaseFilterButtonLabel());
    }

    private void persistTestBaseFilter() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(testBaseFilterType))
                .putInt("testBaseFilterValue", ExposureRecipe.snap5(testBaseFilterValue))
                .apply();
        if (provinoFlow == PROVINO_SPLIT_SOFT) {
            splitSoftYellow = ExposureRecipe.snap5(testBaseFilterValue);
            invalidateSplitHardChoice();
            persistSplitProvinoState();
        } else if (provinoFlow == PROVINO_SPLIT_HARD) {
            splitHardMagenta = ExposureRecipe.snap5(testBaseFilterValue);
            persistSplitProvinoState();
        }
        refreshTestBaseFilterUi();
        refreshSplitProvinoUi();
    }

    private void showTestBaseFilterDialog() {
        if (darkroomMode || armed) return;
        if (provinoFlow == PROVINO_SPLIT_SOFT) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_YELLOW); return; }
        if (provinoFlow == PROVINO_SPLIT_HARD) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_MAGENTA); return; }
        showLplGradeDialog();
    }

    private void showTestBaseFilterValueDialog(final String type) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        int accent = ExposureRecipe.FILTER_MAGENTA.equals(type) ? SPLIT_VIVA_MAGENTA : AMBER;
        panel.addView(text("FILTRO BASE · " + (ExposureRecipe.FILTER_MAGENTA.equals(type) ? "MAGENTA" : "GIALLO"), 19, accent, true), lp(-1,-2));
        TextView note = text("Impostalo fisicamente sulla testa colore prima di iniziare il provino. Sarà associato a tutte le strisce e passerà automaticamente alla stampa e al LOG.", 12, MUTED, false);
        note.setPadding(0, dp(5), 0, dp(12)); panel.addView(note, lp(-1,-2));
        final int[] value = { ExposureRecipe.normalizeFilter(testBaseFilterType).equals(type) ? ExposureRecipe.snap5(testBaseFilterValue) : (ExposureRecipe.FILTER_MAGENTA.equals(type) ? 40 : 30) };
        LinearLayout row = new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER);
        Button minus = smallButton("−"); Button plus = smallButton("+");
        TextView number = text(type + value[0], 32, accent, true); number.setGravity(Gravity.CENTER);
        row.addView(minus, lp(dp(62),dp(58))); row.addView(number, lp(0,dp(64),1f)); row.addView(plus, lp(dp(62),dp(58))); panel.addView(row, lp(-1,-2));
        minus.setOnClickListener(v -> { value[0]=Math.max(0,value[0]-5); number.setText(type+value[0]); });
        plus.setOnClickListener(v -> { int max=ExposureRecipe.FILTER_MAGENTA.equals(type)?170:200; value[0]=Math.min(max,value[0]+5); number.setText(type+value[0]); });
        Button save = compactButton("SALVA"); save.setTextColor(Color.WHITE); save.setBackground(roundRect(accent,9,0,0));
        save.setOnClickListener(v -> { testBaseFilterType=type; testBaseFilterValue=value[0]; persistTestBaseFilter(); dialog.dismiss(); });
        panel.addView(save, margin(lp(-1,dp(52)),0,10,0,0));
        Button cancel = compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show();
        if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void ensureExposureRecipeBase() {
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        exposureRecipe.ensureBase(printWidthMs);
        exposureRecipe.operationalBaseMs = printWidthMs;
    }

    private void persistExposureRecipe() {
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).apply();
        updatePrintSequenceUi();
    }

    private boolean canLengthenTimes() {
        SharedPreferences s = getSharedPreferences("log_session", MODE_PRIVATE);
        long lastPrintAt = s.getLong("lastPrintAt", 0L);
        if (lastPrintAt <= 0L) return false;
        long chosenAt = exposureRecipe == null ? 0L : Math.max(0L, exposureRecipe.baseChosenAt);
        return chosenAt <= 0L || lastPrintAt >= chosenAt;
    }

    private void scaleWholeRecipe(int quarterStopDelta) {
        if (quarterStopDelta == 0) return;
        ensureExposureRecipeBase();
        int oldBase = printWidthMs;
        int newBase = ExposureRecipe.scaledMs(oldBase, quarterStopDelta);
        if (printSequence != null) {
            if (printSequence.hasSplit()) {
                printSequence.split.softMs = ExposureRecipe.scaledMs(printSequence.split.softMs, quarterStopDelta);
                printSequence.split.hardMs = ExposureRecipe.scaledMs(printSequence.split.hardMs, quarterStopDelta);
                printSequence.split.sanitize();
            }
            for (PrintCorrection c : printSequence.corrections) {
                if (c == null || c.quarterStops > 0) continue;
                c.milliseconds = ExposureRecipe.scaledMs(c.milliseconds, quarterStopDelta);
            }
        }
        exposureRecipe.operationalBaseMs = newBase;
        printWidthMs = newBase;
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("printWidthMs", printWidthMs)
                .putString("printSequence", printSequence == null ? "" : printSequence.encode())
                .putString("exposureRecipe", exposureRecipe.encode()).apply();
        if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));
        updatePrintSequenceUi();
        applyModeUi();
    }

    private String recipeBaseSummary() {
        if (exposureRecipe == null || !exposureRecipe.hasBase()) return "";
        if (printSequence != null && printSequence.hasSplit()) {
            return "BASE DI PARTENZA · " + exposureRecipe.originalLine()
                    + (exposureRecipe.densityQuarterSteps > 0 ? "\nDENSITÀ OPERATIVA · " + exposureRecipe.densityLabel() + " · applicata alla ricetta finale" : "");
        }
        String s = "BASE · " + exposureRecipe.operationalLine(printWidthMs);
        if (exposureRecipe.originalBaseMs > 0 && (exposureRecipe.originalBaseMs != exposureRecipe.operationalBaseMs || exposureRecipe.densityQuarterSteps > 0))
            s = "BASE ORIGINALE · " + exposureRecipe.originalLine() + "\nBASE OPERATIVA · " + exposureRecipe.operationalLine(printWidthMs);
        return s;
    }

    private void showLengthenTimesDialog() {
        if (darkroomMode || armed || !canLengthenTimes()) return;
        ensureExposureRecipeBase();
        final int currentQ = ExposureRecipe.clampDensity(exposureRecipe.densityQuarterSteps);
        final int[] targetQ = {currentQ};
        final Dialog dialog = new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("ALLUNGA TEMPI",20,ALLUNGA_COLOR,true),lp(-1,-2));
        TextView note=text("Scegli quanto tempo vuoi avere per lavorare. L’app calcola il filtro D equivalente; la filtrazione di contrasto resta invariata.",12,MUTED,false); note.setPadding(0,dp(5),0,dp(12)); panel.addView(note,lp(-1,-2));
        TextView from=text("ORA · "+formatTime(printWidthMs)+" · "+exposureRecipe.filterLabel()+" · "+exposureRecipe.densityLabel(),13,TEXT_PRIMARY,true); from.setGravity(Gravity.CENTER); panel.addView(from,margin(lp(-1,-2),0,0,0,8));
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER);
        Button minus=smallButton("−"); Button plus=smallButton("+"); TextView time=text("",34,ALLUNGA_COLOR,true); time.setGravity(Gravity.CENTER);
        row.addView(minus,lp(dp(62),dp(58))); row.addView(time,lp(0,dp(66),1f)); row.addView(plus,lp(dp(62),dp(58))); panel.addView(row,lp(-1,-2));
        TextView instruction=text("",18,TEXT_PRIMARY,true); instruction.setGravity(Gravity.CENTER); panel.addView(instruction,margin(lp(-1,-2),0,4,0,4));
        TextView contrast=text("",12,MUTED,false); contrast.setGravity(Gravity.CENTER); panel.addView(contrast,margin(lp(-1,-2),0,0,0,12));
        final Runnable refresh=()->{ int delta=targetQ[0]-currentQ; int preview=ExposureRecipe.scaledMs(printWidthMs,delta); time.setText(formatTime(preview)); instruction.setText("IMPOSTA "+ExposureRecipe.densityLabel(targetQ[0])); String f=exposureRecipe.filterLabel(); contrast.setText(("NESSUNO".equals(f)?"Nessun filtro M/Y":"Mantieni "+f)+" · esposizione equivalente nominale"); };
        minus.setOnClickListener(v->{targetQ[0]=Math.max(0,targetQ[0]-1);refresh.run();}); plus.setOnClickListener(v->{targetQ[0]=Math.min(8,targetQ[0]+1);refresh.run();}); refresh.run();
        Button apply=compactButton("APPLICA"); apply.setTextColor(Color.WHITE); apply.setBackground(roundRect(ALLUNGA_COLOR,9,0,0));
        apply.setOnClickListener(v->{ int delta=targetQ[0]-currentQ; scaleWholeRecipe(delta); exposureRecipe.densityQuarterSteps=targetQ[0]; exposureRecipe.operationalBaseMs=printWidthMs; persistExposureRecipe(); persistPrintSequence(); dialog.dismiss(); String f=exposureRecipe.filterLabel(); setStatusPresentation("ALLUNGA TEMPI — "+formatTime(printWidthMs),"IMPOSTA "+exposureRecipe.densityLabel()+("NESSUNO".equals(f)?"":" · mantieni "+f),ALLUNGA_COLOR); }); panel.addView(apply,margin(lp(-1,dp(52)),0,10,0,0));
        Button cancel=compactButton("ANNULLA"); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(BUTTON,9,0,0)); cancel.setOnClickListener(v->dialog.dismiss()); panel.addView(cancel,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void showGlobalCorrectionDialog() {
        if (darkroomMode || armed) return;
        ensureExposureRecipeBase();
        final Dialog dialog=new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel=new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("CORREZIONE GLOBALE",19,TEXT_PRIMARY,true),lp(-1,-2));
        TextView note=text("Schiarisce o scurisce l’intera ricetta mantenendo invariati i rapporti relativi tra base, DODGE, BURN e SPLIT GRADE.",12,MUTED,false); note.setPadding(0,dp(5),0,dp(12)); panel.addView(note,lp(-1,-2));
        int current=exposureRecipe.globalQuarterStops;
        int[] qs={-1,0,1}; String[] labels={"−¼ STOP","0 · NESSUNA","+¼ STOP"};
        for(int x=0;x<qs.length;x++){
            final int q=qs[x];
            Button b=compactButton((current==q?"✓  ":"")+labels[x]);
            b.setTextColor(Color.WHITE); b.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
            b.setOnClickListener(v->{
                int delta=q-exposureRecipe.globalQuarterStops;
                scaleWholeRecipe(delta);
                exposureRecipe.globalQuarterStops=q;
                exposureRecipe.operationalBaseMs=printWidthMs;
                persistExposureRecipe();
                persistPrintSequence();
                dialog.dismiss();
                showPrintSequenceDialog();
            });
            panel.addView(b,margin(lp(-1,dp(50)),0,x==0?0:7,0,0));
        }
        Button cancel=compactButton("ANNULLA");
        cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
        cancel.setOnClickListener(v->{dialog.dismiss();showPrintSequenceDialog();});
        panel.addView(cancel,margin(lp(-1,dp(48)),0,10,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private String recipeOriginalLabel(LogEntry entry, String fallback) {
        ExposureRecipe r=ExposureRecipe.decode(entry==null?"":entry.recipeState);
        return r.hasBase()?r.originalLine():fallback;
    }
    private String recipeOperationalLabel(LogEntry entry, String fallback) {
        ExposureRecipe r=ExposureRecipe.decode(entry==null?"":entry.recipeState);
        return r.hasBase()?r.operationalLine(entry.exposureMs):fallback;
    }
    private String testFilterLabel(LogEntry entry) {
        if(entry==null) return "—";
        String f=ExposureRecipe.filterLabel(entry.testBaseFilterType,entry.testBaseFilterValue);
        return "NESSUNO".equals(f)?"Nessuno":f;
    }

    private boolean isSplitProvino() {
        return provinoFlow == PROVINO_SPLIT_SOFT || provinoFlow == PROVINO_SPLIT_HARD;
    }

    private void persistSplitProvinoState() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("provinoFlow", provinoFlow)
                .putInt("splitProvinoSoftYellow", ExposureRecipe.snap5(splitSoftYellow))
                .putInt("splitProvinoSoftMs", splitSoftChosenMs <= 0 ? 0 : snap(splitSoftChosenMs, 500, 36_000_000))
                .putInt("splitProvinoSoftStrip", splitSoftChosenStrip)
                .putInt("splitProvinoHardMagenta", ExposureRecipe.snap5(splitHardMagenta))
                .putInt("splitProvinoHardMs", splitHardChosenMs <= 0 ? 0 : snap(splitHardChosenMs, 500, 36_000_000))
                .putInt("splitProvinoHardStrip", splitHardChosenStrip)
                .putString("splitProvinoReturnFilterType", ExposureRecipe.normalizeFilter(splitReturnFilterType))
                .putInt("splitProvinoReturnFilterValue", ExposureRecipe.snap5(splitReturnFilterValue))
                .putInt("splitProvinoReturnTestWidthMs", snap(splitReturnTestWidthMs, 500, 30_000))
                .apply();
    }

    private void markTestResultHandled(long testAt) {
        if (testAt > 0L) getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("lastTestChooserShownAt", testAt).apply();
        refreshPendingTestStripChoiceUi();
    }

    private void markCurrentTestResultHandled() {
        long testAt = getSharedPreferences("log_session", MODE_PRIVATE).getLong("lastTestAt", 0L);
        markTestResultHandled(testAt);
    }

    private void invalidateSplitHardChoice() {
        splitHardChosenMs = 0;
        splitHardChosenStrip = -1;
    }

    private void startSplitProvino() {
        if (armed || provinoFlow != PROVINO_SINGLE) {
            if (provinoFlow == PROVINO_SPLIT_SOFT || provinoFlow == PROVINO_SPLIT_HARD) refreshSplitProvinoUi();
            return;
        }
        clearPrintRevisionDraft();
        clearRevisionSessionMetadata();
        markCurrentTestResultHandled();
        splitReturnFilterType = testBaseFilterType;
        splitReturnFilterValue = testBaseFilterValue;
        splitReturnTestWidthMs = testWidthMs;
        provinoFlow = PROVINO_SPLIT_SOFT;
        splitSoftYellow = 60;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        splitHardMagenta = 130;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        persistTestBaseFilter();
        persistSplitProvinoState();
        refreshSplitProvinoUi();
        setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", BLUE);
    }

    private void requestSingleProvinoMode() {
        if (armed || provinoFlow == PROVINO_SINGLE) return;
        showAppConfirmDialog("ANNULLARE IL PROVINO SPLIT GRADE?",
                "La ricetta di stampa esistente non verrà modificata. Le scelte provvisorie del nuovo provino verranno abbandonate.",
                "TORNA A SINGOLO", this::cancelSplitProvino, "CONTINUA SPLIT");
    }

    private void cancelSplitProvino() {
        boolean revising = hasPrintRevisionDraft();
        provinoFlow = PROVINO_SINGLE;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs = snap(splitReturnTestWidthMs, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", testBaseFilterType)
                .putInt("testBaseFilterValue", testBaseFilterValue)
                .apply();
        if (revising) clearPrintRevisionDraft();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestBaseFilterUi();
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        if (revising) {
            setMode(MODE_PRINT);
            setStatusPresentation("REVISIONE ANNULLATA", "La ricetta precedente non è stata modificata.", GREEN);
        } else {
            setStatusPresentation("PROVINO SINGOLO", "Valori precedenti ripristinati. Nessuna ricetta di stampa modificata.", BLUE);
        }
    }

    private void prepareHardProvinoFromSoftChoice() {
        if (splitSoftChosenMs <= 0) return;
        provinoFlow = PROVINO_SPLIT_HARD;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_MAGENTA;
        testBaseFilterValue = splitHardMagenta;
        persistTestBaseFilter();
        persistSplitProvinoState();
        refreshSplitProvinoUi();
        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", BLUE);
    }

    private void reviewSoftProvino() {
        provinoFlow = PROVINO_SPLIT_SOFT;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        if (splitSoftChosenMs > 0) testWidthMs = snap(splitSoftChosenMs, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testWidthMs", testWidthMs).apply();
        persistTestBaseFilter();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", BLUE);
    }

    private void redoCurrentProvino(long testAt, boolean hard) {
        markTestResultHandled(testAt);
        if (hard) {
            invalidateSplitHardChoice();
            persistSplitProvinoState();
            setStatusPresentation("RIFAI IL DURO",
                    "Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", BLUE);
        } else {
            splitSoftChosenMs = 0;
            splitSoftChosenStrip = -1;
            invalidateSplitHardChoice();
            persistSplitProvinoState();
            setStatusPresentation("REIMPOSTA IL MORBIDO",
                    "Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", BLUE);
        }
        refreshSplitProvinoUi();
    }

    private void refreshSplitProvinoUi() {
        boolean split = isSplitProvino();
        if (testSingleModeButton != null) {
            boolean active = provinoFlow == PROVINO_SINGLE;
            testSingleModeButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            testSingleModeButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (testSplitModeButton != null) {
            boolean active = split;
            testSplitModeButton.setBackground(roundRect(active ? SPLIT_VIVA_MAGENTA : BUTTON, 9, 1, active ? SPLIT_VIVA_MAGENTA : BORDER));
            testSplitModeButton.setTextColor(active ? Color.WHITE : TEXT_PRIMARY);
        }
        if (testSplitPhaseText != null) {
            testSplitPhaseText.setVisibility(split ? View.VISIBLE : View.GONE);
            if (provinoFlow == PROVINO_SPLIT_SOFT) {
                testSplitPhaseText.setText("FASE 1 DI 2 — TROVA IL MORBIDO\nImposta Y" + splitSoftYellow + ", M0. Scegli il tempo che rende soprattutto i toni chiari.");
                testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : AMBER));
            } else if (provinoFlow == PROVINO_SPLIT_HARD) {
                testSplitPhaseText.setText("FASE 2 DI 2 — TROVA IL DURO\nNuova striscia: prima applica il morbido scelto su tutta la carta. Poi imposta Y0, M" + splitHardMagenta + ". Scegli il miglior equilibrio di ombre e neri.");
                testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : SPLIT_VIVA_MAGENTA));
            }
        }
        if (testContrastGuide != null) testContrastGuide.setVisibility(split ? View.GONE : View.VISIBLE);
        if (testPromptText != null) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) testPromptText.setText("Tempo centrale · MORBIDO");
            else if (provinoFlow == PROVINO_SPLIT_HARD) testPromptText.setText("Tempo centrale · DURO");
            else testPromptText.setText(testPromptDescription());
        }
        if (testStepText != null) {
            testStepText.setText(split ? (TimingMath.normalizeMethod(timingMethod) + " · " + TimingMath.stepLabel(timingMethod) + " · " + testCount + " strisce") : testStepDescription());
        }
        if (testPendingChoiceButton != null && hasPendingTestStripChoice()) {
            testPendingChoiceButton.setText(provinoFlow == PROVINO_SPLIT_SOFT ? "SCEGLI IL TEMPO MORBIDO"
                    : (provinoFlow == PROVINO_SPLIT_HARD ? "SCEGLI IL TEMPO DURO" : "SCEGLI STRISCIA DEL PROVINO"));
        }
        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
        refreshTestBaseFilterUi();
    }

    private String testStripMethodButtonLabel() {
        return "METODO PROVINO · " + TimingMath.normalizeMaskingMethod(testStripMethod);
    }

    private void refreshTestStripMethodUi() {
        testStripMethod = TimingMath.normalizeMaskingMethod(testStripMethod);
        if (testStripMethodButton != null) testStripMethodButton.setText(testStripMethodButtonLabel());
        updateCumulativeTimes();
    }

    private void showTestStripMethodDialog() {
        if (armed) return;
        String[] choices = {
                "SCOPRIRE — parti con 1 fascia e ne scopri una in più",
                "COPRIRE — parti tutto scoperto e copri una fascia alla volta"
        };
        showAppChoiceDialog("METODO DI PROVINATURA", choices, which -> {
            testStripMethod = which == 1 ? TimingMath.MASK_COVER : TimingMath.MASK_REVEAL;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("testStripMethod", testStripMethod).apply();
            refreshTestStripMethodUi();
        }, "ANNULLA");
    }

    private LinearLayout buildTestPanel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        LinearLayout provinoModeRow = new LinearLayout(this);
        provinoModeRow.setOrientation(LinearLayout.HORIZONTAL);
        provinoModeRow.setGravity(Gravity.CENTER);
        testSingleModeButton = compactButton("SINGOLO");
        testSplitModeButton = compactButton("SPLIT GRADE");
        testSingleModeButton.setOnClickListener(v -> requestSingleProvinoMode());
        testSplitModeButton.setOnClickListener(v -> startSplitProvino());
        provinoModeRow.addView(testSingleModeButton, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));
        provinoModeRow.addView(testSplitModeButton, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));
        outer.addView(provinoModeRow, margin(lp(-1, -2), 0, 0, 0, 10));

        testSplitPhaseText = text("", 14, BLUE, true);
        testSplitPhaseText.setGravity(Gravity.CENTER);
        testSplitPhaseText.setPadding(dp(12), dp(10), dp(12), dp(10));
        outer.addView(testSplitPhaseText, margin(lp(-1, -2), 0, 0, 0, 10));

        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");
        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));
        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));

        LinearLayout exposure = card();
        testPromptText = text(testPromptDescription(), 16, TEXT_PRIMARY, true);
        testPromptText.setGravity(Gravity.CENTER);
        exposure.addView(testPromptText);
        testStepText = text(testStepDescription(), 12, MUTED, false);
        testStepText.setGravity(Gravity.CENTER);
        exposure.addView(testStepText);
        testBaseFilterButton = compactButton(testBaseFilterButtonLabel());
        testBaseFilterButton.setOnClickListener(v -> showTestBaseFilterDialog());
        exposure.addView(testBaseFilterButton, margin(lp(-1, dp(50)), 0, 10, 0, 0));
        testStripMethodButton = compactButton(testStripMethodButtonLabel());
        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());
        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
        testPendingChoiceButton = compactButton("SCEGLI STRISCIA DEL PROVINO");
        testPendingChoiceButton.setTextColor(Color.WHITE);
        testPendingChoiceButton.setBackground(roundRect(BLUE, 9, 0, 0));
        testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser(true));
        exposure.addView(testPendingChoiceButton, margin(lp(-1, dp(52)), 0, 8, 0, 0));
        refreshPendingTestStripChoiceUi();
        testFStopBadge = addFStopBadge(exposure, false);
        testContrastGuide = text("Leggi il provino dal CHIARO allo SCURO: se trovi prima i BIANCHI giusti → AUMENTA il contrasto; se trovi prima i NERI giusti → DIMINUISCI il contrasto. Se bianchi e neri sono giusti nello stesso gradino → CONTRASTO GIUSTO.", 12, darkroomMode ? RED : TEXT_PRIMARY, false);
        testContrastGuide.setPadding(dp(12), dp(10), dp(12), dp(10));
        testContrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));
        exposure.addView(testContrastGuide, margin(lp(-1,-2), 0, 8, 0, 0));
        exposure.addView(space(10));

        LinearLayout selector = new LinearLayout(this);
        selector.setGravity(Gravity.CENTER);
        selector.setOrientation(LinearLayout.HORIZONTAL);
        Button minus = smallButton("−");
        Button plus = smallButton("+");
        testTimeText = text(formatTime(testWidthMs), 44, BLUE, true);
        testTimeText.setGravity(Gravity.CENTER);
        selector.addView(minus, lp(dp(62), dp(58)));
        selector.addView(testTimeText, lp(0, dp(64), 1f));
        selector.addView(plus, lp(dp(62), dp(58)));
        minus.setOnClickListener(v -> adjustTestTime(-1));
        plus.setOnClickListener(v -> adjustTestTime(+1));
        exposure.addView(selector);
        testCumulativeText = text(cumulativeTimes(), 13, BLUE, true);
        testCumulativeText.setGravity(Gravity.CENTER);
        testCumulativeText.setPadding(dp(6), dp(6), dp(6), 0);
        exposure.addView(testCumulativeText, lp(-1, -2));
        outer.addView(exposure, margin(lp(-1, -2), 0, 0, 0, 10));

        LinearLayout settings = card();
        settings.addView(stepperRow("NUMERO ESPOSIZIONI", true));
        settings.addView(divider());
        settings.addView(stepperRow("PAUSA TRA LE ESPOSIZIONI", false));
        outer.addView(settings, lp(-1, -2));

        TextView note = text("Una sola pressione del pulsante fisico avvia il provino. Dopo la prima esposizione, le successive partono automaticamente dopo la pausa.", 12, MUTED, false);
        note.setGravity(Gravity.CENTER);
        note.setPadding(dp(8), dp(10), dp(8), 0);
        outer.addView(note, lp(-1, -2));
        refreshSplitProvinoUi();
        return outer;
    }

    private LinearLayout buildLogPanel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);

        LinearLayout intro = card();
        TextView title = text("ARCHIVIO DI STAMPA", 18, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
        intro.addView(title);
        TextView sub = text("Schede di camera oscura • ricerca, filtri e backup", 12, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, dp(4), 0, dp(10));
        intro.addView(sub);

        Button add = compactButton("+  NUOVA SCHEDA");
        add.setOnClickListener(v -> showLogEditor(newEntryFromSession(), true));
        intro.addView(add, lp(-1, dp(50)));

        LinearLayout searchRow = new LinearLayout(this);
        searchRow.setOrientation(LinearLayout.HORIZONTAL);
        searchRow.setGravity(Gravity.CENTER_VERTICAL);
        logSearchField = editField("Cerca per titolo, carta o note…", "");
        logSearchField.setTextSize(13);
        if (darkroomMode) {
            logSearchField.setFocusable(false);
            logSearchField.setHint("Ricerca disponibile fuori modalità camera oscura");
        } else {
            logSearchField.addTextChangedListener(new TextWatcher() {
                @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
                @Override public void onTextChanged(CharSequence s, int start, int before, int count) { refreshLogList(); }
                @Override public void afterTextChanged(Editable s) {}
            });
        }
        searchRow.addView(logSearchField, margin(lp(0, dp(48), 1f), 0, 0, dp(6), 0));
        logFavoritesButton = compactButton("☆");
        logFavoritesButton.setTextSize(21);
        logFavoritesButton.setContentDescription("Mostra solo preferite");
        logFavoritesButton.setOnClickListener(v -> {
            logFavoritesOnly = !logFavoritesOnly;
            updateLogFavoriteButton();
            refreshLogList();
        });
        searchRow.addView(logFavoritesButton, lp(dp(50), dp(48)));
        intro.addView(searchRow, margin(lp(-1, -2), 0, 10, 0, 8));
        updateLogFavoriteButton();

        LinearLayout filterRow = new LinearLayout(this);
        filterRow.setOrientation(LinearLayout.HORIZONTAL);
        logFilterAllButton = compactButton("TUTTE");
        logFilter35Button = compactButton("35 mm");
        logFilter66Button = compactButton("6×6");
        logFilter45Button = compactButton("4×5");
        logFilterAllButton.setOnClickListener(v -> setLogFilter("ALL"));
        logFilter35Button.setOnClickListener(v -> setLogFilter("35mm"));
        logFilter66Button.setOnClickListener(v -> setLogFilter("6x6"));
        logFilter45Button.setOnClickListener(v -> setLogFilter("4x5"));
        filterRow.addView(logFilterAllButton, margin(lp(0, dp(43), 1f), 0, 0, dp(3), 0));
        filterRow.addView(logFilter35Button, margin(lp(0, dp(43), 1f), dp(3), 0, dp(3), 0));
        filterRow.addView(logFilter66Button, margin(lp(0, dp(43), 1f), dp(3), 0, dp(3), 0));
        filterRow.addView(logFilter45Button, margin(lp(0, dp(43), 1f), dp(3), 0, 0, 0));
        intro.addView(filterRow, margin(lp(-1, -2), 0, 0, 0, 8));
        updateLogFilterButtons();

        logGroupingButton = compactButton("");
        logGroupingButton.setTextSize(12);
        logGroupingButton.setOnClickListener(v -> {
            logGroupingEnabled = !logGroupingEnabled;
            getSharedPreferences("ui", MODE_PRIVATE).edit()
                    .putBoolean("logGroupingEnabled", logGroupingEnabled)
                    .apply();
            updateLogGroupingButton();
            refreshLogList();
        });
        intro.addView(logGroupingButton, margin(lp(-1, dp(43)), 0, 0, 0, 8));
        updateLogGroupingButton();

        LinearLayout backupRow = new LinearLayout(this);
        backupRow.setOrientation(LinearLayout.HORIZONTAL);
        Button exportBackup = compactButton("ESPORTA BACKUP");
        Button importBackup = compactButton("IMPORTA BACKUP");
        exportBackup.setOnClickListener(v -> exportLogBackup());
        importBackup.setOnClickListener(v -> importLogBackup());
        backupRow.addView(exportBackup, margin(lp(0, dp(46), 1f), 0, dp(8), dp(4), 0));
        backupRow.addView(importBackup, margin(lp(0, dp(46), 1f), dp(4), dp(8), 0, 0));
        intro.addView(backupRow, lp(-1, -2));
        outer.addView(intro, margin(lp(-1, -2), 0, 0, 0, 10));

        logListContainer = new LinearLayout(this);
        logListContainer.setOrientation(LinearLayout.VERTICAL);
        outer.addView(logListContainer, lp(-1, -2));
        refreshLogList();
        return outer;
    }

    private void setLogFilter(String filter) {
        logFilter = filter == null ? "ALL" : filter;
        updateLogFilterButtons();
        refreshLogList();
    }

    private void updateLogFilterButtons() {
        if (logFilterAllButton == null) return;
        styleLogFilterButton(logFilterAllButton, "ALL".equals(logFilter));
        styleLogFilterButton(logFilter35Button, "35mm".equals(logFilter));
        styleLogFilterButton(logFilter66Button, "6x6".equals(logFilter));
        styleLogFilterButton(logFilter45Button, "4x5".equals(logFilter));
    }

    private void updateLogFavoriteButton() {
        if (logFavoritesButton == null) return;
        int accent = darkroomMode ? RED : AMBER;
        logFavoritesButton.setText(logFavoritesOnly ? "★" : "☆");
        logFavoritesButton.setTextColor(logFavoritesOnly ? Color.BLACK : MUTED);
        logFavoritesButton.setBackground(roundRect(logFavoritesOnly ? accent : BUTTON, 8, logFavoritesOnly ? 0 : 1, BORDER));
        logFavoritesButton.setContentDescription(logFavoritesOnly ? "Mostra tutte le schede" : "Mostra solo preferite");
    }

    private void updateLogGroupingButton() {
        if (logGroupingButton == null) return;
        int accent = darkroomMode ? RED : LOG_ACCENT;
        logGroupingButton.setText("RAGGRUPPA TITOLO/GIORNO: " + (logGroupingEnabled ? "ON" : "OFF"));
        logGroupingButton.setBackground(roundRect(logGroupingEnabled ? accent : BUTTON, 8,
                logGroupingEnabled ? 0 : 1, BORDER));
        logGroupingButton.setTextColor(logGroupingEnabled
                ? (darkroomMode ? Color.BLACK : Color.WHITE)
                : MUTED);
        logGroupingButton.setContentDescription(logGroupingEnabled
                ? "Disattiva raggruppamento automatico delle schede"
                : "Attiva raggruppamento automatico delle schede");
    }

    private void styleLogFilterButton(Button b, boolean selected) {
        int accent = darkroomMode ? RED : LOG_ACCENT;
        b.setBackground(roundRect(selected ? accent : BUTTON, 8, selected ? 0 : 1, BORDER));
        b.setTextColor(selected ? (darkroomMode ? Color.BLACK : Color.WHITE) : MUTED);
    }

    private void refreshLogList() {
        if (logListContainer == null) return;
        logListContainer.removeAllViews();
        List<LogEntry> all = LogStore.load(this);
        String query = logSearchField == null ? "" : logSearchField.getText().toString().trim().toLowerCase(Locale.ITALY);

        List<LogGroup> groups = buildLogGroups(all);
        List<LogGroup> visible = new ArrayList<>();
        for (LogGroup group : groups) {
            if (logFavoritesOnly && !group.hasFavorite()) continue;
            if (!groupMatchesFormat(group)) continue;
            if (!query.isEmpty() && !groupMatchesQuery(group, query)) continue;
            visible.add(group);
        }

        if (all.isEmpty()) {
            LinearLayout empty = card();
            TextView t = text("Nessuna scheda salvata", 15, MUTED, true);
            t.setGravity(Gravity.CENTER);
            empty.addView(t);
            TextView s = text("Dopo una stampa o un provino comparirà SALVA NEL LOG.", 12, MUTED, false);
            s.setGravity(Gravity.CENTER);
            s.setPadding(0, dp(6), 0, 0);
            empty.addView(s);
            logListContainer.addView(empty, lp(-1, -2));
            return;
        }
        if (visible.isEmpty()) {
            LinearLayout empty = card();
            TextView t = text("Nessun risultato", 15, MUTED, true);
            t.setGravity(Gravity.CENTER);
            empty.addView(t);
            String why = logFavoritesOnly ? "Nessuna scheda preferita con questi criteri." : "Modifica la ricerca o scegli un altro formato.";
            TextView s = text(why, 12, MUTED, false);
            s.setGravity(Gravity.CENTER);
            s.setPadding(0, dp(6), 0, 0);
            empty.addView(s);
            logListContainer.addView(empty, lp(-1, -2));
            return;
        }

        for (LogGroup group : visible) addLogGroupCard(group);
    }

    private List<LogGroup> buildLogGroups(List<LogEntry> entries) {
        LinkedHashMap<String, LogGroup> byKey = new LinkedHashMap<>();
        if (entries == null) return new ArrayList<>();
        for (LogEntry e : entries) {
            String key = logGroupingEnabled
                    ? logGroupKey(e)
                    : "single:" + e.id + ":" + e.timestamp;
            LogGroup group = byKey.get(key);
            if (group == null) {
                group = new LogGroup(key);
                byKey.put(key, group);
            }
            group.entries.add(e);
        }
        return new ArrayList<>(byKey.values());
    }

    private String logGroupKey(LogEntry e) {
        String title = e == null || e.title == null ? "" : e.title.trim().replaceAll("\\s+", " ").toLowerCase(Locale.ITALY);
        if (title.isEmpty()) return "single:" + (e == null ? System.nanoTime() : e.id);
        String day = new SimpleDateFormat("yyyyMMdd", Locale.ITALY).format(new Date(e.timestamp));
        return day + ":" + title;
    }

    private static String canonicalLogNegative(String raw) {
        String n = raw == null ? "" : raw.trim().toLowerCase(Locale.ITALY).replace(" ", "").replace("×", "x").replace("mm", "");
        if (n.equals("35") || n.equals("24x36") || n.equals("36x24")) return "35mm";
        if (n.equals("66") || n.equals("6x6") || n.equals("56x56")) return "6x6";
        if (n.equals("45") || n.equals("4x5") || n.equals("101,6x127") || n.equals("101.6x127")) return "4x5";
        return raw == null ? "" : raw.trim();
    }

    private static String displayLogNegative(String raw) {
        String n = canonicalLogNegative(raw);
        if ("35mm".equals(n)) return "35 mm";
        if ("6x6".equals(n)) return "6×6";
        if ("4x5".equals(n)) return "4×5";
        return n;
    }

    private boolean groupMatchesFormat(LogGroup group) {
        if ("ALL".equals(logFilter)) return true;
        for (LogEntry e : group.entries) if (logFilter.equals(canonicalLogNegative(e.negative))) return true;
        return false;
    }

    private boolean groupMatchesQuery(LogGroup group, String query) {
        for (LogEntry e : group.entries) {
            String neg = e.negative == null ? "" : e.negative.trim();
            String hay = ((e.title == null ? "" : e.title) + " "
                    + (e.paper == null ? "" : e.paper) + " "
                    + (e.notes == null ? "" : e.notes) + " "
                    + neg).toLowerCase(Locale.ITALY);
            if (hay.contains(query)) return true;
        }
        return false;
    }

    private void addLogGroupCard(final LogGroup group) {
        final LogEntry e = group.latest();
        final boolean grouped = group.entries.size() > 1;
        LinearLayout row = card();
        row.setPadding(dp(16), dp(12), dp(14), dp(12));
        row.setClickable(true);
        row.setFocusable(true);
        row.setOnClickListener(v -> {
            if (grouped) showLogGroup(group);
            else showLogEditor(e, false);
        });

        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.HORIZONTAL);
        head.setGravity(Gravity.CENTER_VERTICAL);
        String name = e.title == null || e.title.trim().isEmpty() ? "Scheda senza titolo" : e.title.trim();
        TextView nameView = text(name, 16, TEXT_PRIMARY, true);
        head.addView(nameView, lp(0, -2, 1f));
        if (group.hasFavorite()) {
            TextView star = text("★", 18, darkroomMode ? RED : AMBER, true);
            star.setGravity(Gravity.CENTER);
            head.addView(star, lp(dp(28), dp(40)));
        }
        TextView arrow = text("›", 30, darkroomMode ? RED : LOG_ACCENT, false);
        arrow.setGravity(Gravity.CENTER);
        head.addView(arrow, lp(dp(34), dp(40)));
        row.addView(head, lp(-1, -2));

        String when = grouped
                ? formatDate(e.timestamp) + "  •  " + group.entries.size() + " lavorazioni"
                : formatDate(e.timestamp) + "  •  " + formatClock(e.timestamp);
        TextView date = text(when, 11, MUTED, false);
        row.addView(date, margin(lp(-1, -2), 0, 1, 0, 5));

        ArrayList<String> mainBits = new ArrayList<>();
        if (e.exposureMs > 0) mainBits.add(formatTime(e.exposureMs));
        if (e.aperture != null && !e.aperture.trim().isEmpty()) mainBits.add("f/" + e.aperture.trim());
        if (e.negative != null && !e.negative.trim().isEmpty()) mainBits.add(displayLogNegative(e.negative));
        TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? GREEN : TEXT_PRIMARY, true);
        row.addView(summary, lp(-1, -2));
        if (TimingMath.isFStop(e.exposureMethod) || TimingMath.isFStop(e.testMethod)) {
            TextView modeBadge = fStopBadge(true);
            row.addView(modeBadge, margin(lp(-2, dp(26)), 0, dp(5), 0, dp(2)));
        }
        if (e.exposureMs > 0) {
            TextView method = text("Metodo: " + TimingMath.normalizeMethod(e.exposureMethod) + " · " + (e.exposureStep == null || e.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(e.exposureMethod) : e.exposureStep), 11, MUTED, false);
            method.setPadding(0, dp(3), 0, 0);
            row.addView(method, lp(-1, -2));
        }

        ArrayList<String> filterBits = new ArrayList<>();
        if (e.magenta != null && !e.magenta.trim().isEmpty()) filterBits.add("M " + e.magenta.trim());
        if (e.yellow != null && !e.yellow.trim().isEmpty()) filterBits.add("Y " + e.yellow.trim());
        if (e.density != null && !e.density.trim().isEmpty()) filterBits.add("D " + e.density.trim());
        if (!filterBits.isEmpty()) {
            TextView filters = text(joinBits(filterBits), 11, MUTED, false);
            filters.setPadding(0, dp(3), 0, 0);
            row.addView(filters, lp(-1, -2));
        }

        if (grouped) {
            int prints = 0;
            int tests = 0;
            for (LogEntry item : group.entries) {
                if (item.exposureMs > 0) prints++;
                else if (item.testMs > 0) tests++;
            }
            ArrayList<String> bits = new ArrayList<>();
            if (tests > 0) bits.add(tests + (tests == 1 ? " provino" : " provini"));
            if (prints > 0) bits.add(prints + (prints == 1 ? " stampa" : " stampe"));
            bits.add("ultima " + formatClock(e.timestamp));
            TextView history = text(joinBits(bits), 11, darkroomMode ? RED : LOG_ACCENT, false);
            history.setPadding(0, dp(4), 0, 0);
            row.addView(history, lp(-1, -2));
        } else if (e.exposureMs > 0 && e.printSequence != null && !e.printSequence.trim().isEmpty()) {
            PrintSequence recipe = PrintSequence.decode(e.printSequence);
            if (!recipe.isEmpty()) {
                TextView plan = text("PIANO · " + recipe.summary(e.exposureMs) + "\n" + recipe.detail(e.exposureMs), 11, MUTED, false);
                plan.setPadding(0, dp(3), 0, 0);
                row.addView(plan, lp(-1, -2));
            }
        } else if (e.testMs > 0) {
            int[] strips = TimingMath.fromCsv(e.testStripTimes);
            if (strips.length != e.testCount) strips = TimingMath.cumulativeSeries(e.testMethod, e.testMs, e.testCount);
            String provino = "Provino · " + TimingMath.normalizeMethod(e.testMethod) + " · " + (e.testStep == null || e.testStep.trim().isEmpty() ? TimingMath.stepLabel(e.testMethod) : e.testStep) + " · " + TimingMath.normalizeMaskingMethod(e.testStripMethod) + "\nStrisce: " + TimingMath.seriesLabel(TimingMath.physicalTargets(strips, e.testStripMethod));
            TextView test = text(provino, 11, BLUE, false);
            test.setPadding(0, dp(3), 0, 0);
            row.addView(test, lp(-1, -2));
        }
        logListContainer.addView(row, margin(lp(-1, -2), 0, 0, 0, 8));
    }

    private void showLogGroup(final LogGroup group) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));

        LogEntry latest = group.latest();
        String name = latest.title == null || latest.title.trim().isEmpty() ? "Scheda senza titolo" : latest.title.trim();
        TextView heading = text("SESSIONE — " + name, 18, TEXT_PRIMARY, true);
        panel.addView(heading, lp(-1, -2));
        TextView sub = text(formatDate(latest.timestamp) + "  •  " + group.entries.size() + " lavorazioni", 12, MUTED, false);
        sub.setPadding(0, dp(4), 0, dp(10));
        panel.addView(sub, lp(-1, -2));

        // Storia dal primo passaggio all'ultimo: provino -> stampe successive.
        for (int i = group.entries.size() - 1; i >= 0; i--) {
            final LogEntry item = group.entries.get(i);
            LinearLayout step = card();
            step.setPadding(dp(14), dp(10), dp(12), dp(10));
            String kind;
            int accent;
            if (item.exposureMs > 0) {
                kind = "STAMPA  " + formatTime(item.exposureMs) + "  ·  " + TimingMath.normalizeMethod(item.exposureMethod) + " · " + (item.exposureStep == null || item.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(item.exposureMethod) : item.exposureStep);
                accent = GREEN;
            } else if (item.testMs > 0) {
                kind = "PROVINO  " + TimingMath.normalizeMethod(item.testMethod) + " · " + (item.testStep == null || item.testStep.trim().isEmpty() ? TimingMath.stepLabel(item.testMethod) : item.testStep);
                accent = BLUE;
            } else {
                kind = "SCHEDA";
                accent = TEXT_PRIMARY;
            }
            String top = (item.favorite ? "★  " : "") + formatClock(item.timestamp) + "  •  " + kind;
            step.addView(text(top, 14, item.favorite ? (darkroomMode ? RED : AMBER) : accent, true), lp(-1, -2));
            ArrayList<String> details = new ArrayList<>();
            if (item.aperture != null && !item.aperture.trim().isEmpty()) details.add("f/" + item.aperture.trim());
            if (item.negative != null && !item.negative.trim().isEmpty()) details.add(displayLogNegative(item.negative));
            if (!details.isEmpty()) {
                TextView d = text(joinBits(details), 11, MUTED, false);
                d.setPadding(0, dp(3), 0, 0);
                step.addView(d, lp(-1, -2));
            }
            step.setClickable(true);
            step.setFocusable(true);
            step.setOnClickListener(v -> {
                dialog.dismiss();
                showLogEditor(item, false);
            });
            panel.addView(step, margin(lp(-1, -2), 0, 0, 0, 7));
        }

        TextView note = text("Le lavorazioni vengono raggruppate automaticamente solo quando titolo e data coincidono.", 11, MUTED, false);
        note.setGravity(Gravity.CENTER);
        panel.addView(note, margin(lp(-1, -2), 0, 4, 0, 8));

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, lp(-1, dp(48)));

        dialog.setContentView(sc);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.82f));
    }

    private static String joinBits(List<String> bits) {
        if (bits == null || bits.isEmpty()) return "Dati tecnici da completare";
        StringBuilder b = new StringBuilder();
        for (String bit : bits) {
            if (bit == null || bit.trim().isEmpty()) continue;
            if (b.length() > 0) b.append("  •  ");
            b.append(bit);
        }
        return b.length() == 0 ? "Dati tecnici da completare" : b.toString();
    }

    private LogEntry newEntryFromSession() {
        SharedPreferences p = getSharedPreferences("log_session", MODE_PRIVATE);
        long now = System.currentTimeMillis();
        long cycle = p.getLong("lastCycleAt", 0L);
        long printAt = p.getLong("lastPrintAt", 0L);
        long testAt = p.getLong("lastTestAt", 0L);
        long anchor = cycle > 0 ? cycle : Math.max(printAt, testAt);
        if (anchor <= 0) anchor = now;

        LogEntry e = new LogEntry();
        e.id = now;
        e.timestamp = anchor;
        long enlargementArmAt = p.getLong("pendingEnlargementAt", 0L);
        e.enlargementMeta = (printAt > 0 && enlargementArmAt > 0 && enlargementArmAt <= printAt)
                ? p.getString("pendingEnlargementMeta", "") : "";
        applyEnlargementSnapshotToVisibleLogFields(e);
        // A print log always carries the latest completed print and the latest completed test strip.
        // No time window: the user's rule is simply "associate the last test strip to the print".
        if (printAt > 0 && printAt >= testAt) {
            e.timestamp = printAt;
            e.exposureMs = p.getInt("lastPrintMs", 0);
            e.exposureMethod = TimingMath.normalizeMethod(p.getString("lastPrintMethod", TimingMath.METHOD_SECONDS));
            e.exposureStep = p.getString("lastPrintStep", TimingMath.stepLabel(e.exposureMethod));
            e.printSequence = p.getString("lastPrintSequence", "");
            e.recipeState = p.getString("lastRecipeState", "");
            PrintSequence loggedSequence = PrintSequence.decode(e.printSequence);
            boolean loggedSplit = loggedSequence.hasSplit();
            e.exposureMode = p.getString("lastExposureMode", loggedSplit ? "SPLIT_GRADE" : "SINGLE");
            if (loggedSplit) {
                e.splitSoftYellow = p.getInt("lastSplitSoftYellow", loggedSequence.split.softYellow);
                e.splitSoftMs = p.getInt("lastSplitSoftMs", loggedSequence.split.softMs);
                e.splitHardMagenta = p.getInt("lastSplitHardMagenta", loggedSequence.split.hardMagenta);
                e.splitHardMs = p.getInt("lastSplitHardMs", loggedSequence.split.hardMs);
            }
            e.splitSoftChosenStrip = p.getInt("lastSplitSoftChosenStrip", -1);
            e.splitHardChosenStrip = p.getInt("lastSplitHardChosenStrip", -1);
            e.splitTimeOrigin = p.getString("lastSplitTimeOrigin", "");
            e.previousRevisionId = p.getLong("lastRevisionPreviousId", 0L);
            e.previousRecipeState = p.getString("lastRevisionPreviousRecipeState", "");
            e.previousPrintSequence = p.getString("lastRevisionPreviousPrintSequence", "");
            e.revisionReason = p.getString("lastRevisionReason", "");
            if (testAt > 0) {
                e.testMs = p.getInt("lastTestMs", 0);
                e.testCount = p.getInt("lastTestCount", 0);
                e.testBaseFilterType = ExposureRecipe.normalizeFilter(p.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));
                e.testBaseFilterValue = ExposureRecipe.snap5(p.getInt("lastTestBaseFilterValue", 0));
                e.testMethod = TimingMath.normalizeMethod(p.getString("lastTestMethod", TimingMath.METHOD_SECONDS));
                e.testStep = p.getString("lastTestStep", TimingMath.stepLabel(e.testMethod));
                e.testStripTimes = p.getString("lastTestStripTimes", "");
                e.testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("lastTestStripMethod", TimingMath.MASK_REVEAL));
            }
        } else if (testAt > 0) {
            // If the most recent completed cycle is only a test strip, keep the existing
            // quick-save behaviour: test data only, until a final print is made.
            e.timestamp = testAt;
            e.testMs = p.getInt("lastTestMs", 0);
            e.testCount = p.getInt("lastTestCount", 0);
            e.testMethod = TimingMath.normalizeMethod(p.getString("lastTestMethod", TimingMath.METHOD_SECONDS));
            e.testStep = p.getString("lastTestStep", TimingMath.stepLabel(e.testMethod));
            e.testStripTimes = p.getString("lastTestStripTimes", "");
            e.testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("lastTestStripMethod", TimingMath.MASK_REVEAL));
        }

        // Defaults for every new print card; all remain editable in the editor.
        e.aperture = "11,5";
        e.magenta = "0";
        e.yellow = "0";
        e.density = "0";
        e.paper = "Fomaspeed Variant 311 RC lucida";
        if (e.recipeState == null || e.recipeState.trim().isEmpty()) {
            ExposureRecipe r = new ExposureRecipe();
            if (e.exposureMs > 0) { r.originalBaseMs=e.exposureMs; r.operationalBaseMs=e.exposureMs; r.filterType=e.testBaseFilterType; r.filterValue=e.testBaseFilterValue; r.baseChosenAt=e.timestamp; e.recipeState=r.encode(); }
        }
        ExposureRecipe autoRecipe = ExposureRecipe.decode(e.recipeState);
        if (autoRecipe.hasBase()) {
            if (ExposureRecipe.FILTER_MAGENTA.equals(autoRecipe.filterType)) e.magenta=String.valueOf(autoRecipe.filterValue);
            if (ExposureRecipe.FILTER_YELLOW.equals(autoRecipe.filterType)) e.yellow=String.valueOf(autoRecipe.filterValue);
            e.density=autoRecipe.densityLabel();
        }
        applyReprintTemplate(e);
        return e;
    }

    private boolean shouldOfferQuickSave() {
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long cycle = session.getLong("lastCycleAt", 0L);
        long saved = getSharedPreferences("ui", MODE_PRIVATE).getLong("lastSavedCycleAt", 0L);
        return cycle > saved;
    }

    private void markCurrentSessionSaved(LogEntry e) {
        long cycle = getSharedPreferences("log_session", MODE_PRIVATE).getLong("lastCycleAt", 0L);
        if (cycle > 0 && e.timestamp == cycle) {
            getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("lastSavedCycleAt", cycle).apply();
        }
        if (e.exposureMs > 0) getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("activeSourceLogId", e.id).apply();
        SharedPreferences template = getSharedPreferences("log_reprint", MODE_PRIVATE);
        long activatedAt = template.getLong("activatedAt", Long.MAX_VALUE);
        if (template.getBoolean("active", false) && e.exposureMs > 0 && e.timestamp >= activatedAt) {
            template.edit().clear().apply();
        }
    }

    private void useLogEntryForPrint(LogEntry entry) {
        if (entry == null || entry.exposureMs <= 0) return;
        clearPrintRevisionDraft();
        clearRevisionSessionMetadata();
        exposureRecipe = ExposureRecipe.decode(entry.recipeState);
        if (!exposureRecipe.hasBase()) { exposureRecipe.originalBaseMs=entry.exposureMs; exposureRecipe.operationalBaseMs=entry.exposureMs; exposureRecipe.filterType=entry.testBaseFilterType; exposureRecipe.filterValue=entry.testBaseFilterValue; }
        exposureRecipe.baseChosenAt = System.currentTimeMillis();
        setPrintTime(exposureRecipe.operationalBaseMs > 0 ? exposureRecipe.operationalBaseMs : entry.exposureMs);
        printSequence = PrintSequence.decode(entry.printSequence);
        testBaseFilterType = ExposureRecipe.normalizeFilter(entry.testBaseFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(entry.testBaseFilterValue);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putString("exposureRecipe", exposureRecipe.encode())
                .putString("testBaseFilterType", testBaseFilterType)
                .putInt("testBaseFilterValue", testBaseFilterValue)
                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)
                .putLong("activeSourceLogId", entry.id)
                .apply();
        refreshTestBaseFilterUi();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putString("printSequence", printSequence.encode()).apply();
        updatePrintSequenceUi();
        getSharedPreferences("log_reprint", MODE_PRIVATE).edit()
                .clear()
                .putBoolean("active", true)
                .putLong("activatedAt", System.currentTimeMillis())
                .putString("title", entry.title == null ? "" : entry.title)
                .putString("negative", entry.negative == null ? "" : entry.negative)
                .putString("aperture", entry.aperture == null ? "" : entry.aperture)
                .putString("magenta", entry.magenta == null ? "" : entry.magenta)
                .putString("yellow", entry.yellow == null ? "" : entry.yellow)
                .putString("density", entry.density == null ? "" : entry.density)
                .putString("paper", entry.paper == null ? "" : entry.paper)
                .putString("notes", entry.notes == null ? "" : entry.notes)
                .putString("printSequence", entry.printSequence == null ? "" : entry.printSequence)
                .putString("recipeState", entry.recipeState == null ? "" : entry.recipeState)
                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)
                .putString("testBaseFilterType", entry.testBaseFilterType == null ? ExposureRecipe.FILTER_NONE : entry.testBaseFilterType)
                .putInt("testBaseFilterValue", entry.testBaseFilterValue)
                .apply();
        setMode(MODE_PRINT);
        Toast.makeText(this, printSequence.hasSplit() ? "Stampa SPLIT GRADE caricata in STAMPA" : ("Stampa " + formatTime(entry.exposureMs) + (printSequence.isEmpty() ? "" : " + piano completo") + " caricata in STAMPA"), Toast.LENGTH_SHORT).show();
    }

    private void applyReprintTemplate(LogEntry entry) {
        if (entry == null || entry.exposureMs <= 0) return;
        SharedPreferences template = getSharedPreferences("log_reprint", MODE_PRIVATE);
        if (!template.getBoolean("active", false)) return;
        long activatedAt = template.getLong("activatedAt", Long.MAX_VALUE);
        if (entry.timestamp < activatedAt) return;
        entry.title = template.getString("title", "");
        entry.negative = template.getString("negative", "");
        entry.aperture = template.getString("aperture", entry.aperture);
        entry.columnHeight = "";
        entry.magenta = template.getString("magenta", entry.magenta);
        entry.yellow = template.getString("yellow", entry.yellow);
        entry.density = template.getString("density", entry.density);
        entry.paper = template.getString("paper", entry.paper);
        entry.notes = template.getString("notes", "");
        entry.printSequence = template.getString("printSequence", "");
        if (entry.recipeState == null || entry.recipeState.trim().isEmpty()) entry.recipeState = template.getString("recipeState", "");
        if (entry.enlargementMeta == null || entry.enlargementMeta.trim().isEmpty()) entry.enlargementMeta = template.getString("enlargementMeta", "");
        if (entry.testBaseFilterType == null || ExposureRecipe.FILTER_NONE.equals(entry.testBaseFilterType)) entry.testBaseFilterType = template.getString("testBaseFilterType", ExposureRecipe.FILTER_NONE);
        if (entry.testBaseFilterValue <= 0) entry.testBaseFilterValue = template.getInt("testBaseFilterValue", 0);
    }

    private static String enlargementMetaValue(String meta, String key) {
        if (meta == null || meta.trim().isEmpty()) return "";
        for (String part : meta.split("\\|")) {
            if (part.startsWith(key + "=")) return part.substring(key.length() + 1);
        }
        return "";
    }

    private static boolean applyEnlargementSnapshotToVisibleLogFields(LogEntry entry) {
        if (entry == null || entry.enlargementMeta == null || entry.enlargementMeta.trim().isEmpty()) return false;
        boolean changed = false;
        String neg = enlargementMetaValue(entry.enlargementMeta, "neg");
        String canonical = "35".equals(neg) ? "35mm" : ("66".equals(neg) ? "6x6" : ("45".equals(neg) ? "4x5" : ""));
        if (!canonical.isEmpty() && !canonical.equals(canonicalLogNegative(entry.negative))) {
            entry.negative = canonical;
            changed = true;
        }
        if (entry.columnHeight != null && !entry.columnHeight.trim().isEmpty()) {
            entry.columnHeight = "";
            changed = true;
        }
        String paper = enlargementMetaValue(entry.enlargementMeta, "paper");
        if (!paper.isEmpty()) {
            String format = paper.replace('.', ',').replace("x", " × ") + " cm";
            String current = entry.paper == null ? "" : entry.paper.trim();
            if (current.isEmpty()) {
                entry.paper = format;
                changed = true;
            } else if (!current.contains(format) && !current.contains(paper)) {
                entry.paper = current + " · " + format;
                changed = true;
            }
        }
        return changed;
    }

    private String enlargementLogSummary(String meta) {
        if (meta == null || meta.trim().isEmpty()) return "—";
        String neg = enlargementMetaValue(meta, "neg");
        String paper = enlargementMetaValue(meta, "paper").replace('.', ',').replace("x", " × ");
        String lens = enlargementMetaValue(meta, "lens");
        String beta = enlargementMetaValue(meta, "beta");
        String columnScale = enlargementMetaValue(meta, "columnScale");
        String carrier = enlargementMetaValue(meta, "carrier");
        String fill = enlargementMetaValue(meta, "fill");
        String mode = "0".equals(fill) ? "immagine intera" : ("1".equals(fill) ? "riempi larghezza" : ("2".equals(fill) ? "riempi altezza" : ""));
        String format = "35".equals(neg) ? "35 mm" : ("66".equals(neg) ? "6×6" : ("45".equals(neg) ? "4×5" : ""));
        String carrierLabel = "35mm".equals(carrier) ? "portanegativi 35 mm" : ("6x6".equals(carrier) ? "portanegativi 6×6" : ("4x5".equals(carrier) ? "portanegativi 4×5" : ""));
        StringBuilder b = new StringBuilder();
        if (!format.isEmpty()) b.append(format);
        if (!lens.isEmpty()) b.append(b.length() > 0 ? " · " : "").append("obiettivo ").append(lens).append(" mm");
        if (!carrierLabel.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(carrierLabel);
        if (!paper.isEmpty()) b.append(b.length() > 0 ? " · " : "").append("carta ").append(paper).append(" cm");
        if (!beta.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
            catch (Exception ignored) {}
        }
        if (!columnScale.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("scala LPL ").append(String.format(Locale.ITALY, "%.1f", Double.parseDouble(columnScale))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(mode);
        return b.length() == 0 ? "—" : b.toString();
    }

    private String splitLogSummary(LogEntry entry, PrintSequence savedSequence) {
        boolean split = savedSequence != null && savedSequence.hasSplit();
        if (!split) return "SINGOLA";
        int sy = entry.splitSoftYellow > 0 ? entry.splitSoftYellow : savedSequence.split.softYellow;
        int sm = entry.splitSoftMs > 0 ? entry.splitSoftMs : savedSequence.split.softMs;
        int hm = entry.splitHardMagenta > 0 ? entry.splitHardMagenta : savedSequence.split.hardMagenta;
        int ht = entry.splitHardMs > 0 ? entry.splitHardMs : savedSequence.split.hardMs;
        String origin = entry.splitTimeOrigin == null || entry.splitTimeOrigin.trim().isEmpty() ? "—" : entry.splitTimeOrigin;
        String strips = (entry.splitSoftChosenStrip > 0 || entry.splitHardChosenStrip > 0)
                ? (" · strisce M=" + (entry.splitSoftChosenStrip > 0 ? entry.splitSoftChosenStrip : "—") + " / D=" + (entry.splitHardChosenStrip > 0 ? entry.splitHardChosenStrip : "—")) : "";
        return "SPLIT GRADE\nMORBIDO · " + sy + "Y / 0M · " + formatTime(sm)
                + "\nDURO · 0Y / " + hm + "M · " + formatTime(ht)
                + "\nOrigine tempi: " + origin + strips;
    }

    private String previousRevisionSummary(LogEntry entry) {
        PrintSequence old = PrintSequence.decode(entry == null ? "" : entry.previousPrintSequence);
        if (old.hasSplit()) return "Precedente: " + old.split.softLine() + " / " + old.split.hardLine();
        ExposureRecipe r = ExposureRecipe.decode(entry == null ? "" : entry.previousRecipeState);
        if (r.hasBase()) return "Precedente: esposizione singola · " + formatTime(r.operationalBaseMs > 0 ? r.operationalBaseMs : r.originalBaseMs) + " · " + r.filterLabel();
        return "Precedente revisione disponibile";
    }

    private void showLogEditor(final LogEntry entry, final boolean isNew) {
        if (applyEnlargementSnapshotToVisibleLogFields(entry) && !isNew) LogStore.save(this, entry);
        if (darkroomMode) {
            showAppConfirmDialog("COMPILAZIONE SCHEDA",
                    "Per scrivere nei campi manuali è meglio uscire dalla modalità camera oscura: la tastiera di Android non è inattinica. Puoi comunque consultare il LOG in rosso.",
                    "VAI ALLE IMPOSTAZIONI", this::showSettingsDialog, "ANNULLA");
            return;
        }

        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));

        LinearLayout headingRow = new LinearLayout(this);
        headingRow.setOrientation(LinearLayout.HORIZONTAL);
        headingRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView heading = text(isNew ? "NUOVA SCHEDA DI STAMPA" : "SCHEDA DI STAMPA", 19, TEXT_PRIMARY, true);
        headingRow.addView(heading, lp(0, -2, 1f));
        final boolean[] favorite = {entry.favorite};
        final Button favoriteButton = compactButton(favorite[0] ? "★" : "☆");
        favoriteButton.setTextSize(22);
        favoriteButton.setContentDescription(favorite[0] ? "Rimuovi dai preferiti" : "Aggiungi ai preferiti");
        favoriteButton.setTextColor(favorite[0] ? AMBER : MUTED);
        favoriteButton.setBackground(roundRect(BUTTON, 8, 1, BORDER));
        favoriteButton.setOnClickListener(v -> {
            favorite[0] = !favorite[0];
            favoriteButton.setText(favorite[0] ? "★" : "☆");
            favoriteButton.setTextColor(favorite[0] ? AMBER : MUTED);
            favoriteButton.setContentDescription(favorite[0] ? "Rimuovi dai preferiti" : "Aggiungi ai preferiti");
        });
        headingRow.addView(favoriteButton, lp(dp(48), dp(46)));
        panel.addView(headingRow, margin(lp(-1, -2), 0, 0, 0, 12));

        LinearLayout auto = card();
        auto.addView(text("DATI AUTOMATICI", 13, MUTED, true));
        String exposure = entry.exposureMs > 0 ? formatTime(entry.exposureMs) : "—";
        String ntest = entry.testCount > 0 ? String.valueOf(entry.testCount) : "—";
        int[] stripValues = TimingMath.fromCsv(entry.testStripTimes);
        if (entry.testMs > 0 && entry.testCount > 0 && stripValues.length != entry.testCount) stripValues = TimingMath.cumulativeSeries(entry.testMethod, entry.testMs, entry.testCount);
        String strips = entry.testMs > 0 ? TimingMath.seriesLabel(TimingMath.physicalTargets(stripValues, entry.testStripMethod)) : "—";
        String printMethod = entry.exposureMs > 0 ? TimingMath.normalizeMethod(entry.exposureMethod) + " · " + (entry.exposureStep == null || entry.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(entry.exposureMethod) : entry.exposureStep) : "—";
        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) + " · " + TimingMath.normalizeMaskingMethod(entry.testStripMethod) : "—";
        PrintSequence savedSequence = PrintSequence.decode(entry.printSequence);
        boolean savedSplit = savedSequence.hasSplit();
        String sequenceRecipe = savedSequence.isEmpty() ? "—" : ("\n" + savedSequence.detail(entry.exposureMs));
        String exposureHeader = savedSplit
                ? ("Modalità esposizione: " + splitLogSummary(entry, savedSequence))
                : ("Modalità esposizione: SINGOLA\nBase originale: " + recipeOriginalLabel(entry, exposure) + "\nBase operativa: " + recipeOperationalLabel(entry, exposure));
        TextView autoValues = text(
                exposureHeader +
                "\nFiltro provino: " + testFilterLabel(entry) +
                "\nMetodo stampa: " + printMethod +
                "\nProvino — strisce: " + ntest +
                "\nMetodo provino: " + testMethod +
                "\nTempi strisce: " + strips +
                "\nPiano di stampa: " + sequenceRecipe +
                "\nFormato e ingrandimento: " + enlargementLogSummary(entry.enlargementMeta) +
                "\nData: " + formatDate(entry.timestamp) +
                "\nOra: " + formatClock(entry.timestamp), 14, TEXT_PRIMARY, false);
        autoValues.setPadding(0, dp(6), 0, 0);
        auto.addView(autoValues);
        if (!isNew && ((entry.previousPrintSequence != null && !entry.previousPrintSequence.trim().isEmpty()) || (entry.previousRecipeState != null && !entry.previousRecipeState.trim().isEmpty()) || entry.previousRevisionId > 0)) {
            Button previous=compactButton("MOSTRA REVISIONE PRECEDENTE");
            previous.setOnClickListener(v -> showAppConfirmDialog("REVISIONE PRECEDENTE",
                    previousRevisionSummary(entry) + (entry.previousRevisionId > 0 ? ("\nScheda origine: " + entry.previousRevisionId) : "") + (entry.revisionReason == null || entry.revisionReason.trim().isEmpty() ? "" : ("\nMotivo: " + entry.revisionReason)),
                    null, null, "CHIUDI"));
            auto.addView(previous, margin(lp(-1,dp(46)),0,8,0,0));
        }
        panel.addView(auto, margin(lp(-1, -2), 0, 0, 0, 12));

        final EditText title = editField("Titolo / nome stampa", entry.title);
        panel.addView(title, margin(lp(-1, dp(52)), 0, 0, 0, 8));

        TextView negLabel = text("NEGATIVO", 12, MUTED, true);
        panel.addView(negLabel, margin(lp(-1, -2), 0, 4, 0, 4));
        LinearLayout negRow = new LinearLayout(this);
        negRow.setOrientation(LinearLayout.HORIZONTAL);
        final String[] negative = {canonicalLogNegative(entry.negative)};
        final Button b35 = compactButton("35mm");
        final Button b66 = compactButton("6×6");
        final Button b45 = compactButton("4×5");
        View.OnClickListener negRefresh = v -> {
            negative[0] = v == b35 ? "35mm" : (v == b66 ? "6x6" : "4x5");
            b35.setBackground(roundRect("35mm".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b66.setBackground(roundRect("6x6".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b45.setBackground(roundRect("4x5".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b35.setTextColor("35mm".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b66.setTextColor("6x6".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b45.setTextColor("4x5".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
        };
        b35.setOnClickListener(negRefresh);
        b66.setOnClickListener(negRefresh);
        b45.setOnClickListener(negRefresh);
        negRow.addView(b35, margin(lp(0, dp(46), 1f), 0, 0, dp(3), 0));
        negRow.addView(b66, margin(lp(0, dp(46), 1f), dp(3), 0, dp(3), 0));
        negRow.addView(b45, margin(lp(0, dp(46), 1f), dp(3), 0, 0, 0));
        panel.addView(negRow, margin(lp(-1, -2), 0, 0, 0, 8));
        if ("35mm".equals(negative[0])) b35.performClick();
        else if ("6x6".equals(negative[0])) b66.performClick();
        else if ("4x5".equals(negative[0])) b45.performClick();

        final EditText aperture = editField("Diaframma f/", entry.aperture);
        final EditText magenta = editField("Magenta", entry.magenta);
        final EditText yellow = editField("Yellow", entry.yellow);
        final EditText density = editField("Densità", entry.density);
        final EditText paper = editField("Carta", entry.paper == null || entry.paper.trim().isEmpty() ? "Fomaspeed Variant 311 RC lucida" : entry.paper);
        final EditText notes = editField("Note — max " + JpegCardRenderer.MAX_NOTES_CHARS + " caratteri", entry.notes);
        notes.setSingleLine(false);
        notes.setMinLines(2);
        notes.setMaxLines(3);
        notes.setFilters(new InputFilter[]{new InputFilter.LengthFilter(JpegCardRenderer.MAX_NOTES_CHARS)});
        if (notes.getText().length() > JpegCardRenderer.MAX_NOTES_CHARS) {
            notes.setText(notes.getText().subSequence(0, JpegCardRenderer.MAX_NOTES_CHARS));
            notes.setSelection(notes.getText().length());
        }
        panel.addView(aperture, margin(lp(-1, dp(52)), 0, 0, 0, 3));
        TextView apertureNote = text("½ stop: indicare 0,5  •  esempio: f/11½ → 11,5", 11, MUTED, false);
        apertureNote.setPadding(dp(4), 0, dp(4), dp(7));
        panel.addView(apertureNote, lp(-1, -2));
        panel.addView(magenta, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(yellow, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(density, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(paper, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(notes, margin(lp(-1, dp(84)), 0, 0, 0, 12));

        Button save = compactButton("SALVA SCHEDA");
        save.setBackground(roundRect(darkroomMode ? RED : LOG_ACCENT, 9, 0, 0));
        save.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE);
        save.setOnClickListener(v -> {
            entry.title = title.getText().toString().trim();
            entry.negative = negative[0];
            entry.aperture = aperture.getText().toString().trim();
            entry.columnHeight = "";
            entry.magenta = magenta.getText().toString().trim();
            entry.yellow = yellow.getText().toString().trim();
            entry.density = density.getText().toString().trim();
            entry.paper = paper.getText().toString().trim();
            entry.notes = trimNotes(notes.getText().toString().trim());
            entry.favorite = favorite[0];
            if (entry.id <= 0) entry.id = System.currentTimeMillis();
            if (entry.timestamp <= 0) entry.timestamp = System.currentTimeMillis();
            LogStore.save(this, entry);
            markCurrentSessionSaved(entry);
            dialog.dismiss();
            Toast.makeText(this, "Scheda salvata nel LOG", Toast.LENGTH_SHORT).show();
            setMode(MODE_LOG);
            refreshLogList();
        });
        panel.addView(save, lp(-1, dp(52)));

        if (!isNew) {
            if (entry.exposureMs > 0) {
                Button useForPrint = compactButton(PrintSequence.decode(entry.printSequence).hasSplit() ? "USA PER STAMPA  •  SPLIT GRADE" : ("USA PER STAMPA  •  " + formatTime(entry.exposureMs)));
                useForPrint.setBackground(roundRect(GREEN, 9, 0, 0));
                useForPrint.setTextColor(Color.BLACK);
                useForPrint.setOnClickListener(v -> {
                    useLogEntryForPrint(entry);
                    dialog.dismiss();
                });
                panel.addView(useForPrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));

                Button resizePrint = compactButton("RIDIMENSIONA STAMPA");
                resizePrint.setTextColor(Color.WHITE);
                resizePrint.setBackground(roundRect(Color.rgb(55,60,64), 9, 0, 0));
                resizePrint.setOnClickListener(v -> {
                    entry.title = title.getText().toString().trim();
                    entry.negative = negative[0];
                    entry.aperture = aperture.getText().toString().trim();
                    entry.columnHeight = "";
                    entry.magenta = magenta.getText().toString().trim();
                    entry.yellow = yellow.getText().toString().trim();
                    entry.density = density.getText().toString().trim();
                    entry.paper = paper.getText().toString().trim();
                    entry.notes = trimNotes(notes.getText().toString().trim());
                    entry.favorite = favorite[0];
                    LogStore.save(this, entry);
                    dialog.dismiss();
                    Intent resizeIntent = new Intent(this, EnlargementActivity.class)
                            .putExtra("mode", "resize")
                            .putExtra("originLogId", entry.id);
                    startActivity(resizeIntent);
                });
                panel.addView(resizePrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));
            }

            Button exportJpg = compactButton("ESPORTA SCHEDA JPG 9:16");
            exportJpg.setOnClickListener(v -> {
                entry.title = title.getText().toString().trim();
                entry.negative = negative[0];
                entry.aperture = aperture.getText().toString().trim();
                entry.columnHeight = "";
                entry.magenta = magenta.getText().toString().trim();
                entry.yellow = yellow.getText().toString().trim();
                entry.density = density.getText().toString().trim();
                entry.paper = paper.getText().toString().trim();
                entry.notes = trimNotes(notes.getText().toString().trim());
                exportJpeg(entry);
            });
            panel.addView(exportJpg, margin(lp(-1, dp(50)), 0, 8, 0, 0));

            Button delete = compactButton("ELIMINA SCHEDA");
            delete.setTextColor(RED);
            delete.setOnClickListener(v -> showAppConfirmDialog("ELIMINARE QUESTA SCHEDA?",
                    "L’operazione non può essere annullata.", "ELIMINA", () -> {
                        LogStore.delete(this, entry.id);
                        dialog.dismiss();
                        refreshLogList();
                    }, "ANNULLA"));
            panel.addView(delete, margin(lp(-1, dp(48)), 0, 8, 0, 0));
        }

        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        dialog.setContentView(sc);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.88f));
    }

    private EditText editField(String hint, String value) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setText(value == null ? "" : value);
        e.setTextSize(15);
        e.setTextColor(TEXT_PRIMARY);
        e.setHintTextColor(MUTED);
        e.setSingleLine(true);
        e.setPadding(dp(12), 0, dp(12), 0);
        e.setBackground(roundRect(BUTTON, 8, 1, BORDER));
        return e;
    }

    private static String trimNotes(String s) {
        String v = s == null ? "" : s;
        return v.length() <= JpegCardRenderer.MAX_NOTES_CHARS ? v : v.substring(0, JpegCardRenderer.MAX_NOTES_CHARS);
    }

    private static String formatDate(long timestamp) {
        return new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(timestamp));
    }

    private static String formatClock(long timestamp) {
        return new SimpleDateFormat("HH:mm", Locale.ITALY).format(new Date(timestamp));
    }


    private void exportLogBackup() {
        Intent i = new Intent("android.intent.action.CREATE_DOCUMENT");
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/json");
        String name = "DarkroomTimer-LOG-backup-" + new SimpleDateFormat("yyyyMMdd-HHmm", Locale.ITALY).format(new Date()) + ".json";
        i.putExtra(Intent.EXTRA_TITLE, name);
        startActivityForResult(i, REQ_EXPORT_BACKUP);
    }

    private void importLogBackup() {
        Intent i = new Intent("android.intent.action.OPEN_DOCUMENT");
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/json");
        startActivityForResult(i, REQ_IMPORT_BACKUP);
    }

    private void exportJpeg(LogEntry entry) {
        pendingJpegEntry = entry;
        Intent i = new Intent("android.intent.action.CREATE_DOCUMENT");
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("image/jpeg");
        String base = entry == null || entry.title == null || entry.title.trim().isEmpty()
                ? "Scheda-tecnica-stampa"
                : "Scheda-" + safeFileName(entry.title.trim());
        i.putExtra(Intent.EXTRA_TITLE, base + ".jpg");
        startActivityForResult(i, REQ_EXPORT_JPG);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try {
            if (requestCode == REQ_EXPORT_BACKUP) {
                String json = BackupManager.exportJson(this);
                try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                    if (out == null) throw new Exception("Impossibile aprire il file scelto");
                    out.write(json.getBytes(StandardCharsets.UTF_8));
                }
                Toast.makeText(this, "Backup LOG esportato", Toast.LENGTH_SHORT).show();
            } else if (requestCode == REQ_IMPORT_BACKUP) {
                String json = readTextUri(uri);
                final List<LogEntry> imported = BackupManager.parseJson(json);
                ThreeActionDialog.show(this, darkroomMode, "IMPORTA BACKUP LOG",
                        "Trovate " + imported.size() + " schede. Vuoi unirle al LOG attuale oppure sostituire completamente il LOG?",
                        "UNISCI", () -> {
                            LogStore.merge(this, imported);
                            refreshLogList();
                            Toast.makeText(this, "Backup unito al LOG", Toast.LENGTH_SHORT).show();
                        }, "SOSTITUISCI", () -> {
                            LogStore.replaceAll(this, imported);
                            refreshLogList();
                            Toast.makeText(this, "LOG ripristinato dal backup", Toast.LENGTH_SHORT).show();
                        }, "ANNULLA");
            } else if (requestCode == REQ_EXPORT_JPG) {
                if (pendingJpegEntry == null) throw new Exception("Nessuna scheda da esportare");
                Bitmap bitmap = JpegCardRenderer.render(pendingJpegEntry, APP_VERSION);
                try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                    if (out == null) throw new Exception("Impossibile aprire il file scelto");
                    if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 94, out)) throw new Exception("Creazione JPG non riuscita");
                } finally {
                    bitmap.recycle();
                    pendingJpegEntry = null;
                }
                Toast.makeText(this, "Scheda JPG esportata", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception e) {
            Toast.makeText(this, "Operazione non riuscita: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private String readTextUri(Uri uri) throws Exception {
        StringBuilder b = new StringBuilder();
        try (InputStream in = getContentResolver().openInputStream(uri);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line).append('\n');
        }
        return b.toString();
    }

    private static String safeFileName(String s) {
        String v = s == null ? "scheda" : s.replaceAll("[^A-Za-z0-9À-ÿ._-]+", "-");
        v = v.replaceAll("-+", "-");
        if (v.length() > 48) v = v.substring(0, 48);
        return v.isEmpty() ? "scheda" : v;
    }

    private void showAppConfirmDialog(String title, String message, String positiveLabel,
                                      Runnable positiveAction, String negativeLabel) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20), dp(18), dp(20), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        TextView heading = text(title, 19, darkroomMode ? RED : TEXT_PRIMARY, true);
        panel.addView(heading, margin(lp(-1, -2), 0, 0, 0, 12));
        if (message != null && !message.trim().isEmpty()) {
            TextView body = text(message, 14, MUTED, false);
            body.setLineSpacing(0, 1.08f);
            panel.addView(body, margin(lp(-1, -2), 0, 0, 0, 16));
        }

        if (positiveLabel != null) {
            Button positive = compactButton(positiveLabel);
            String positiveKey = positiveLabel == null ? "" : positiveLabel.toUpperCase(Locale.ITALY);
            boolean destructive = positiveKey.contains("ELIMINA") || positiveKey.contains("AZZERA") || positiveKey.contains("ANNULLA CICLO");
            int positiveAccent = darkroomMode ? RED : (destructive ? RED : BLUE);
            positive.setBackground(roundRect(positiveAccent, 9, 0, 0));
            positive.setTextColor(Color.BLACK);
            positive.setOnClickListener(v -> {
                dialog.dismiss();
                if (positiveAction != null) positiveAction.run();
            });
            panel.addView(positive, lp(-1, dp(52)));
        }
        if (negativeLabel != null) {
            Button negative = compactButton(negativeLabel);
            negative.setTextColor(darkroomMode ? RED : MUTED);
            negative.setOnClickListener(v -> dialog.dismiss());
            panel.addView(negative, margin(lp(-1, dp(48)), 0, 8, 0, 0));
        }

        dialog.setContentView(panel);
        dialog.setOnDismissListener(d -> {
            if (title != null && title.startsWith("PROVINO COMPLETATO")) {
                testChooserOpen = false;
                refreshPendingTestStripChoiceUi();
            }
        });
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.92f), ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void showAppChoiceDialog(String title, String[] choices, ChoiceAction action, String cancelLabel) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        TextView heading = text(title, 18, darkroomMode ? RED : TEXT_PRIMARY, true);
        panel.addView(heading, margin(lp(-1, -2), 0, 0, 0, 12));
        for (int i = 0; i < choices.length; i++) {
            final int index = i;
            Button option = compactButton(choices[i]);
            option.setTextColor(darkroomMode ? RED : TEXT_PRIMARY);
            option.setOnClickListener(v -> {
                dialog.dismiss();
                action.choose(index);
            });
            panel.addView(option, margin(lp(-1, dp(48)), 0, 0, 0, 7));
        }
        Button cancel = compactButton(cancelLabel);
        cancel.setTextColor(darkroomMode ? RED : MUTED);
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 6, 0, 0));

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private void showTechnicalLogDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        TextView heading = text("CRONOLOGIA TECNICA", 18, TEXT_PRIMARY, true);
        panel.addView(heading, margin(lp(-1, -2), 0, 0, 0, 6));
        TextView expl = text("Ultimi 20 cicli: eventi osservati dal MINIR2 sulla LAN. I tempi includono la latenza di rete/polling e servono alla diagnostica, non come misura metrologica.", 12, MUTED, false);
        panel.addView(expl, margin(lp(-1, -2), 0, 0, 0, 10));

        ScrollView sc = new ScrollView(this);
        TextView body = text(TechnicalLog.formatForDisplay(this), 11, TEXT_PRIMARY, false);
        body.setTypeface(Typeface.MONOSPACE);
        body.setTextIsSelectable(true);
        body.setPadding(dp(10), dp(10), dp(10), dp(10));
        body.setBackground(roundRect(BUTTON, 8, 1, BORDER));
        sc.addView(body, new ScrollView.LayoutParams(-1, -2));
        panel.addView(sc, lp(-1, dp(420)));

        Button clear = compactButton("AZZERA CRONOLOGIA TECNICA");
        clear.setTextColor(RED);
        clear.setOnClickListener(v -> showAppConfirmDialog("AZZERARE LA CRONOLOGIA TECNICA?", "",
                "AZZERA", () -> {
                    TechnicalLog.clear(this);
                    body.setText("Nessun ciclo tecnico registrato.");
                }, "ANNULLA"));
        panel.addView(clear, margin(lp(-1, dp(48)), 0, 10, 0, 0));

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.96f), (int)(getResources().getDisplayMetrics().heightPixels * 0.88f));
    }

    private LinearLayout stepperRow(String label, boolean isCount) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(5), 0, dp(5));

        TextView name = text(label, 13, MUTED, true);
        row.addView(name, lp(0, dp(54), 1f));
        Button minus = smallCompactButton("−");
        Button plus = smallCompactButton("+");
        TextView value = text(isCount ? String.valueOf(testCount) : formatTime(testPauseMs), 22, BLUE, true);
        value.setGravity(Gravity.CENTER);
        if (isCount) testCountText = value; else testPauseText = value;
        row.addView(minus, lp(dp(48), dp(46)));
        row.addView(value, lp(dp(86), dp(50)));
        row.addView(plus, lp(dp(48), dp(46)));

        if (isCount) {
            minus.setOnClickListener(v -> setTestCount(testCount - 1));
            plus.setOnClickListener(v -> setTestCount(testCount + 1));
        } else {
            minus.setOnClickListener(v -> setTestPause(testPauseMs - 500));
            plus.setOnClickListener(v -> setTestPause(testPauseMs + 500));
        }
        return row;
    }

    private void setMode(int newMode) {
        if (armed) return;
        mode = newMode;
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("mode", mode).apply();
        if (mode == MODE_LOG) refreshLogList();
        applyModeUi();
    }

    private void applyModeUi() {
        boolean print = mode == MODE_PRINT;
        boolean test = mode == MODE_TEST;
        boolean log = mode == MODE_LOG;
        printPanel.setVisibility(print ? View.VISIBLE : View.GONE);
        testPanel.setVisibility(test ? View.VISIBLE : View.GONE);
        logPanel.setVisibility(log ? View.VISIBLE : View.GONE);
        actionButton.setVisibility(log || armed ? View.GONE : View.VISIBLE);
        stateCard.setVisibility(log ? View.GONE : View.VISIBLE);
        cancelCycleButton.setVisibility(armed ? View.VISIBLE : View.GONE);
        saveLogButton.setVisibility(!log && !armed && shouldOfferQuickSave() ? View.VISIBLE : View.GONE);

        styleNavButton(printModeButton, print, GREEN);
        styleNavButton(testModeButton, test, BLUE);
        styleNavButton(logModeButton, log, LOG_ACCENT);
        actionButton.setTextColor(darkroomMode ? Color.BLACK : TEXT_PRIMARY);
        if (!log) {
            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));
            actionButton.setText(print ? (printSequence != null && !printSequence.isEmpty() ? "ARMA PIANO DI STAMPA" : "ARMA STAMPA • " + formatTime(printWidthMs))
                    : (TimingMath.isFStop(timingMethod)
                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"
                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));
        }
        refreshSplitProvinoUi();
    }

    private void arm() {
        if (mode == MODE_LOG) return;
        if (device == null || !device.isValid()) {
            stateText.setText("Il SONOFF dell’ingranditore non è ancora verificato in DIY");
            return;
        }
        if (mode == MODE_PRINT && !validatePrintSequenceForBase()) return;
        if (safelightAuto) {
            DeviceConfig safe = SafelightConfig.load(this);
            if (!safe.isValid() || safe.deviceId.equals(device.deviceId)) {
                setStatusPresentation("ATTENZIONE", "Configura un secondo SONOFF DIY dedicato alla luce rossa", RED);
                return;
            }
        }
        armed = true;
        cancelCycleButton.setEnabled(true);
        setStatusPresentation("PREPARAZIONE", mode == MODE_PRINT ? "Imposto Inching…" : "Preparo il provino…", AMBER);
        setControlsEnabled(false);

        Intent i;
        if (mode == MODE_PRINT) {
            SharedPreferences activeUi = getSharedPreferences("ui", MODE_PRIVATE);
            getSharedPreferences("log_session", MODE_PRIVATE).edit()
                    .putString("pendingEnlargementMeta", activeUi.getString("enlargementMeta", ""))
                    .putLong("pendingEnlargementAt", System.currentTimeMillis())
                    .apply();
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);
            ensureExposureRecipeBase();
            persistExposureRecipe();
            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_PRINT_SEQUENCE, printSequence == null ? "" : printSequence.encode());
            i.putExtra(SonoffArmService.EXTRA_RECIPE_STATE, exposureRecipe.encode());
        } else {
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);
            i.putExtra(SonoffArmService.EXTRA_WIDTH, testWidthMs);
            i.putExtra(SonoffArmService.EXTRA_COUNT, testCount);
            i.putExtra(SonoffArmService.EXTRA_PAUSE, testPauseMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());
            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.normalizeMaskingMethod(testStripMethod));
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.normalizeFilter(testBaseFilterType));
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, ExposureRecipe.snap5(testBaseFilterValue));
            if (provinoFlow == PROVINO_SPLIT_HARD && splitSoftChosenMs > 0) {
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_MS, snap(splitSoftChosenMs, 500, 36_000_000));
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_TYPE, ExposureRecipe.FILTER_YELLOW);
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE, ExposureRecipe.snap5(splitSoftYellow));
            }
        }
        startServiceCompat(i);
    }

    private void cancelCurrentCycle() {
        if (!armed) return;
        showAppConfirmDialog("ANNULLARE IL CICLO?",
                "L’uscita verrà spenta immediatamente e l’Inching verrà disattivato.",
                "ANNULLA CICLO", () -> {
                    setStatusPresentation("ANNULLAMENTO", "Spengo l’uscita e disattivo Inching…", RED);
                    cancelCycleButton.setEnabled(false);
                    Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_CANCEL);
                    startServiceCompat(i);
                }, "CONTINUA");
    }

    private boolean hasPendingTestStripChoice() {
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long testAt = session.getLong("lastTestAt", 0L);
        if (testAt <= 0L) return false;
        long chosenAt = getSharedPreferences("ui", MODE_PRIVATE).getLong("lastTestChooserShownAt", 0L);
        return chosenAt < testAt;
    }

    private void refreshPendingTestStripChoiceUi() {
        if (testPendingChoiceButton == null) return;
        boolean pending = hasPendingTestStripChoice();
        testPendingChoiceButton.setVisibility(pending ? View.VISIBLE : View.GONE);
        if (pending) testPendingChoiceButton.setText(provinoFlow == PROVINO_SPLIT_SOFT ? "SCEGLI IL TEMPO MORBIDO" : (provinoFlow == PROVINO_SPLIT_HARD ? "SCEGLI IL TEMPO DURO" : "SCEGLI STRISCIA DEL PROVINO"));
        testPendingChoiceButton.setEnabled(pending && !armed);
        testPendingChoiceButton.setAlpha(testPendingChoiceButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
    }

    private void maybeShowTestResultChooser() {
        maybeShowTestResultChooser(false);
    }

    private void maybeShowTestResultChooser(boolean forceManual) {
        if (armed || mode != MODE_TEST || isFinishing()) return;
        if (forceManual) testChooserOpen = false;
        else if (testChooserOpen) return;
        if (!hasWindowFocus()) {
            new Handler(Looper.getMainLooper()).postDelayed(() -> maybeShowTestResultChooser(forceManual), 450L);
            return;
        }
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long testAt = session.getLong("lastTestAt", 0L);
        if (testAt <= 0) return;
        SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);
        if (ui.getLong("lastTestChooserShownAt", 0L) >= testAt) return;

        final int step = session.getInt("lastTestMs", testWidthMs);
        final int n = Math.max(2, Math.min(20, session.getInt("lastTestCount", testCount)));
        int[] stored = TimingMath.fromCsv(session.getString("lastTestStripTimes", ""));
        final int[] ascending = stored.length == n ? stored : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);
        final String masking = TimingMath.normalizeMaskingMethod(session.getString("lastTestStripMethod", testStripMethod));
        final int[] physical = TimingMath.physicalTargets(ascending, masking);
        final String filterType = ExposureRecipe.normalizeFilter(session.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));
        final int filterValue = ExposureRecipe.snap5(session.getInt("lastTestBaseFilterValue", 0));
        testChooserOpen = true;
        showProvinoResultDialog(testAt, physical, filterType, filterValue);
    }

    private void showProvinoResultDialog(final long testAt, final int[] physical, final String filterType, final int filterValue) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        String title;
        String help;
        if (provinoFlow == PROVINO_SPLIT_SOFT) {
            title = "SCEGLI IL TEMPO MORBIDO";
            help = "Quale striscia restituisce la resa desiderata soprattutto nei toni chiari?";
        } else if (provinoFlow == PROVINO_SPLIT_HARD) {
            title = "SCEGLI IL TEMPO DURO";
            help = "Ogni striscia comprende già l’esposizione morbida scelta. Quale combinazione produce il miglior equilibrio di ombre e neri?";
        } else {
            title = "PROVINO COMPLETATO — SCEGLI LA STRISCIA";
            help = "Scegli una striscia valida oppure reimposta il provino senza creare una stampa.";
        }
        panel.addView(text(title, 18, darkroomMode ? RED : TEXT_PRIMARY, true), lp(-1,-2));
        TextView note = text(help, 13, MUTED, false);
        note.setPadding(0, dp(5), 0, dp(10)); panel.addView(note, lp(-1,-2));

        final int[] selected = {-1};
        final TextView selectedText = text("Nessuna striscia selezionata", 12, BLUE, true);
        selectedText.setGravity(Gravity.CENTER);
        selectedText.setPadding(dp(6), dp(5), dp(6), dp(8));
        panel.addView(selectedText, lp(-1,-2));
        final String filterLabel = ExposureRecipe.filterLabel(filterType, filterValue);
        for (int i=0;i<physical.length;i++) {
            final int idx=i;
            Button option=compactButton((i+1)+"ª striscia   —   "+formatTime(physical[i])+("NESSUNO".equals(filterLabel)?"":" · "+filterLabel));
            option.setOnClickListener(v -> {
                selected[0]=idx;
                selectedText.setText("SELEZIONATA · "+(idx+1)+"ª · "+formatTime(physical[idx]));
            });
            panel.addView(option, margin(lp(-1,dp(47)),0,0,0,6));
        }

        if (provinoFlow == PROVINO_SINGLE) {
            Button choose=compactButton("SCEGLI LA STRISCIA");
            choose.setBackground(roundRect(BLUE,9,0,0)); choose.setTextColor(Color.BLACK);
            choose.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima una striscia",Toast.LENGTH_SHORT).show();return;}
                int imported=snap(physical[selected[0]],500,36_000_000);
                markTestResultHandled(testAt);
                splitSoftChosenStrip=-1; splitHardChosenStrip=-1;
                commitPrintRevisionMetadata("PROVINO");
                exposureRecipe=new ExposureRecipe();
                exposureRecipe.originalBaseMs=imported;
                exposureRecipe.operationalBaseMs=imported;
                exposureRecipe.filterType=filterType;
                exposureRecipe.filterValue=filterValue;
                exposureRecipe.densityQuarterSteps=0;
                exposureRecipe.globalQuarterStops=0;
                exposureRecipe.baseChosenAt=System.currentTimeMillis();
                printSequence=new PrintSequence();
                getSharedPreferences("ui",MODE_PRIVATE).edit()
                        .putString("exposureRecipe",exposureRecipe.encode())
                        .putString("printSequence","").apply();
                dialog.dismiss();
                updatePrintSequenceUi();
                setMode(MODE_PRINT);
                setPrintTime(imported);
                setStatusPresentation("DAL PROVINO — "+formatTime(imported)+("NESSUNO".equals(filterLabel)?"":" · "+filterLabel),
                        "Tempo e filtrazione trasferiti alla stampa.",GREEN);
            });
            panel.addView(choose, margin(lp(-1,dp(52)),0,8,0,0));
            Button reset=compactButton("NESSUNA MI CONVINCE — REIMPOSTA PROVINO");
            reset.setTextColor(darkroomMode?RED:BLUE);
            reset.setOnClickListener(v -> {
                markTestResultHandled(testAt);
                dialog.dismiss();
                setStatusPresentation("REIMPOSTA PROVINO", "Modifica filtrazione, tempo, passo o numero di strisce e ripeti. Nessuna stampa è stata creata.", BLUE);
            });
            panel.addView(reset, margin(lp(-1,dp(50)),0,7,0,0));
            Button later=compactButton("NON ORA"); later.setOnClickListener(v->dialog.dismiss());
            panel.addView(later, margin(lp(-1,dp(47)),0,7,0,0));
            if(hasPrintRevisionDraft()){
                Button cancelRevision=compactButton("ANNULLA REVISIONE E TORNA ALLA STAMPA");
                cancelRevision.setOnClickListener(v->{dialog.dismiss();cancelPrintRevisionToPrint();});
                panel.addView(cancelRevision,margin(lp(-1,dp(47)),0,7,0,0));
            }
        } else if (provinoFlow == PROVINO_SPLIT_SOFT) {
            Button next=compactButton("CONTINUA AL DURO");
            next.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0)); next.setTextColor(Color.WHITE);
            next.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima il tempo morbido",Toast.LENGTH_SHORT).show();return;}
                if(!ExposureRecipe.FILTER_YELLOW.equals(filterType)){
                    Toast.makeText(this,"La fase morbida richiede il filtro giallo",Toast.LENGTH_LONG).show();return;
                }
                splitSoftChosenMs=snap(physical[selected[0]],500,36_000_000);
                splitSoftChosenStrip=selected[0]+1;
                splitSoftYellow=filterValue;
                invalidateSplitHardChoice();
                markTestResultHandled(testAt);
                persistSplitProvinoState();
                dialog.dismiss();
                prepareHardProvinoFromSoftChoice();
            });
            panel.addView(next, margin(lp(-1,dp(52)),0,8,0,0));
            Button reset=compactButton("NESSUNA MI CONVINCE — REIMPOSTA");
            reset.setOnClickListener(v->{dialog.dismiss();redoCurrentProvino(testAt,false);});
            panel.addView(reset, margin(lp(-1,dp(49)),0,7,0,0));
            Button cancel=compactButton("ANNULLA");
            cancel.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();cancelSplitProvino();});
            panel.addView(cancel, margin(lp(-1,dp(47)),0,7,0,0));
        } else {
            Button create=compactButton("CREA STAMPA SPLIT GRADE");
            create.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0)); create.setTextColor(Color.WHITE);
            create.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima il tempo duro",Toast.LENGTH_SHORT).show();return;}
                if(!ExposureRecipe.FILTER_MAGENTA.equals(filterType)){
                    Toast.makeText(this,"La fase dura richiede il filtro magenta",Toast.LENGTH_LONG).show();return;
                }
                splitHardChosenMs=snap(physical[selected[0]],500,36_000_000);
                splitHardChosenStrip=selected[0]+1;
                splitHardMagenta=filterValue;
                markTestResultHandled(testAt);
                persistSplitProvinoState();
                dialog.dismiss();
                createSplitPrintFromProvino();
            });
            panel.addView(create, margin(lp(-1,dp(52)),0,8,0,0));
            Button redo=compactButton("RIFAI IL DURO");
            redo.setOnClickListener(v->{dialog.dismiss();redoCurrentProvino(testAt,true);});
            panel.addView(redo, margin(lp(-1,dp(48)),0,7,0,0));
            Button soft=compactButton("RIVEDI IL MORBIDO");
            soft.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();reviewSoftProvino();});
            panel.addView(soft, margin(lp(-1,dp(48)),0,7,0,0));
            Button cancel=compactButton("ANNULLA");
            cancel.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();cancelSplitProvino();});
            panel.addView(cancel, margin(lp(-1,dp(47)),0,7,0,0));
        }

        dialog.setContentView(panel);
        dialog.setOnDismissListener(d->{testChooserOpen=false;refreshPendingTestStripChoiceUi();refreshSplitProvinoUi();});
        Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.88f));
    }

    private void createSplitPrintFromProvino() {
        if (splitSoftChosenMs <= 0 || splitHardChosenMs <= 0) return;
        SplitGradePlan plan=new SplitGradePlan();
        plan.enabled=true;
        plan.softYellow=ExposureRecipe.snap5(splitSoftYellow);
        plan.softMs=snap(splitSoftChosenMs,500,36_000_000);
        plan.hardMagenta=ExposureRecipe.snap5(splitHardMagenta);
        plan.hardMs=snap(splitHardChosenMs,500,36_000_000);
        plan.sanitize();
        PrintSequence next=new PrintSequence();
        next.split=plan;
        // New experimentally determined base: do not silently inherit old Dodge/Burn.
        printSequence=next;
        commitPrintRevisionMetadata("PROVINO");
        getSharedPreferences("ui",MODE_PRIVATE).edit().putString("printSequence",printSequence.encode()).apply();
        persistPrintSequence();

        int softMs=plan.softMs, hardMs=plan.hardMs, sy=plan.softYellow, hm=plan.hardMagenta;
        provinoFlow=PROVINO_SINGLE;
        testBaseFilterType=ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue=ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs=snap(splitReturnTestWidthMs,500,30_000);
        persistSplitProvinoState();
        refreshTestBaseFilterUi();
        setMode(MODE_PRINT);
        updatePrintSequenceUi();
        setStatusPresentation("SPLIT GRADE DAL PROVINO",
                "MORBIDO · "+sy+"Y / 0M · "+formatTime(softMs)+"  +  DURO · 0Y / "+hm+"M · "+formatTime(hardMs)+". Due esposizioni consecutive, tempi indipendenti.", GREEN);
    }

    private void disarm() {
        if (device == null || !device.isValid()) {
            stateText.setText("Nessun SONOFF DIY verificato");
            return;
        }
        stateText.setTextColor(MUTED);
        stateText.setText("Ripristino ON/OFF normale…");
        Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_DISARM);
        startServiceCompat(i);
    }

    private void startServiceCompat(Intent intent) {
        if (Build.VERSION.SDK_INT >= 26) {
            try {
                java.lang.reflect.Method m = Context.class.getMethod("startForegroundService", Intent.class);
                m.invoke(this, intent);
                return;
            } catch (Exception ignored) {}
        }
        startService(intent);
    }

    private void adjustPrintTime(int direction) {
        if (armed) return;
        if (TimingMath.isFStop(timingMethod)) setPrintTime(TimingMath.quarterStop(printWidthMs, direction, 500, 36_000_000));
        else setPrintTime(printWidthMs + direction * 500);
    }

    private void adjustTestTime(int direction) {
        if (armed) return;
        if (TimingMath.isFStop(timingMethod)) setTestTime(TimingMath.quarterStop(testWidthMs, direction, 500, 30_000));
        else setTestTime(testWidthMs + direction * 500);
    }

    private void setPrintTime(int ms) {
        if (armed) return;
        printWidthMs = snap(ms, 500, 36_000_000);
        if (exposureRecipe == null) exposureRecipe = new ExposureRecipe();
        if (exposureRecipe.hasBase()) exposureRecipe.operationalBaseMs = printWidthMs;
        SharedPreferences.Editor edit = getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("printWidthMs", printWidthMs);
        if (exposureRecipe.hasBase()) edit.putString("exposureRecipe", exposureRecipe.encode());
        edit.apply();
        printTimeText.setText(formatTime(printWidthMs));
        updatePrintSequenceUi();
        applyModeUi();
    }

    private void setTestTime(int ms) {
        if (armed) return;
        testWidthMs = snap(ms, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testWidthMs", testWidthMs).apply();
        testTimeText.setText(formatTime(testWidthMs));
        updateCumulativeTimes();
        applyModeUi();
    }

    private void setTestCount(int n) {
        if (armed) return;
        testCount = Math.max(2, Math.min(20, n));
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testCount", testCount).apply();
        testCountText.setText(String.valueOf(testCount));
        updateCumulativeTimes();
        applyModeUi();
    }

    private void setTestPause(int ms) {
        if (armed) return;
        testPauseMs = snap(ms, 500, 60_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testPauseMs", testPauseMs).apply();
        testPauseText.setText(formatTime(testPauseMs));
    }

    private void updateSelectionUiBeforeDiscovery() {
        if (selectedDeviceId == null || selectedDeviceId.isEmpty()) {
            deviceStatus.setText("●  SONOFF NON CONFIGURATO");
            deviceStatus.setTextColor(MUTED);
            selectDeviceButton.setText("⚙");
            stateText.setText("Apri le impostazioni e scegli il SONOFF dell’ingranditore.");
        } else {
            deviceStatus.setText("●  SONOFF — connessione…");
            deviceStatus.setTextColor(MUTED);
            selectDeviceButton.setText("⚙");
            stateText.setText("CONNESSIONE — cerco il SONOFF dell’ingranditore…");
        }
    }

    private void updateSafelightStatus() {
        if (safelightStatus == null) return;
        DeviceConfig safe = SafelightConfig.load(this);
        if (!safelightAuto) {
            safelightStatus.setText("LUCE ROSSA AUTOMATICA — OFF");
            safelightStatus.setTextColor(MUTED);
        } else if (!safe.isValid()) {
            safelightStatus.setText("LUCE ROSSA AUTOMATICA — DA CONFIGURARE");
            safelightStatus.setTextColor(RED);
        } else {
            safelightStatus.setText("LUCE ROSSA AUTOMATICA — ON");
            safelightStatus.setTextColor(darkroomMode ? RED : Color.rgb(201, 157, 70));
        }
    }

    private void showSafelightPicker() {
        ArrayList<FoundDevice> list = new ArrayList<>();
        for (FoundDevice f : foundDevices.values()) {
            if (!f.diyCandidate) continue;
            if (f.config.deviceId.equals(selectedDeviceId)) continue;
            list.add(f);
        }
        Collections.sort(list, Comparator.comparing(a -> a.config.deviceId));
        if (list.isEmpty()) {
            showAppConfirmDialog("NESSUN SECONDO SONOFF DIY TROVATO",
                    "La luce rossa richiede un secondo SONOFF in modalità DIY, diverso da quello dell'ingranditore. Attendi la ricerca di rete e riprova.",
                    "OK", null, null);
            return;
        }
        String[] labels = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            FoundDevice f = list.get(i);
            String selected = f.config.deviceId.equals(selectedSafelightDeviceId) ? "  ✓" : "";
            labels[i] = "ID " + f.config.deviceId + selected + "\n" + f.config.host + ":" + f.config.port + " • DIY";
        }
        showAppChoiceDialog("SCEGLI IL SONOFF DELLA LUCE ROSSA", labels,
                which -> selectSafelight(list.get(which)), "ANNULLA");
    }

    private void selectSafelight(FoundDevice found) {
        if (found == null || !found.diyCandidate || !found.config.isValid()) return;
        if (found.config.deviceId.equals(selectedDeviceId)) {
            Toast.makeText(this, "Scegli un SONOFF diverso da quello dell’ingranditore", Toast.LENGTH_LONG).show();
            return;
        }
        selectedSafelightDeviceId = found.config.deviceId;
        safelightDevice = found.config;
        SafelightConfig.save(this, found.config);
        updateSafelightStatus();
        if (safelightAuto) ensureSafelightIdleOn();
        Toast.makeText(this, "SONOFF luce rossa selezionato", Toast.LENGTH_SHORT).show();
    }

    private void ensureSafelightIdleOn() {
        if (!safelightAuto || armed) return;
        DeviceConfig primary = DeviceConfig.load(this);
        DeviceConfig safe = SafelightConfig.load(this);
        if (!primary.isValid() || !safe.isValid() || safe.deviceId.equals(primary.deviceId)) return;
        Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_START_INTERLOCK);
        startServiceCompat(i);
    }

    private void stopSafelightInterlock() {
        Intent i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_STOP_INTERLOCK);
        startServiceCompat(i);
    }

    private void showDevicePicker() {
        if (foundDevices.isEmpty()) {
            showAppConfirmDialog("NESSUN SONOFF TROVATO",
                    "Attendi qualche secondo con il telefono collegato alla stessa rete Wi‑Fi dei SONOFF, poi riprova.",
                    "OK", null, null);
            return;
        }

        List<FoundDevice> list = new ArrayList<>(foundDevices.values());
        Collections.sort(list, Comparator.comparing(a -> a.config.deviceId));
        String[] labels = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            FoundDevice f = list.get(i);
            String selected = f.config.deviceId.equals(selectedDeviceId) ? "  ✓" : "";
            labels[i] = "ID " + f.config.deviceId + selected + "\n" +
                    f.config.host + ":" + f.config.port + " • " + f.modeLabel();
        }

        showAppChoiceDialog("SCEGLI IL SONOFF DELL’INGRANDITORE", labels,
                which -> selectDevice(list.get(which)), "ANNULLA");
    }

    private void selectDevice(FoundDevice found) {
        selectedDeviceId = found.config.deviceId;
        found.config.save(this);
        device = null;
        setControlsEnabled(false);
        selectDeviceButton.setText("⚙");
        applySelectedFound(found);
    }

    private void applySelectedFound(FoundDevice found) {
        if (!found.config.deviceId.equals(selectedDeviceId)) return;
        if (found.diyCandidate) {
            deviceStatus.setText("●  SONOFF — verifica DIY…");
            deviceStatus.setTextColor(MUTED);
            stateText.setTextColor(MUTED);
            stateText.setText("CONNESSIONE — verifico il SONOFF…");
            validateSelected(found.config);
        } else {
            device = null;
            setControlsEnabled(false);
            deviceStatus.setText("●  SONOFF NON IN DIY");
            deviceStatus.setTextColor(AMBER);
            stateText.setTextColor(AMBER);
            stateText.setText("SONOFF NON IN DIY — controlla le impostazioni.");
        }
    }

    private void validateSelected(DeviceConfig d) {
        if (d == null || !d.isValid()) return;
        if (!d.deviceId.equals(selectedDeviceId)) return;
        if (!validationInFlight.compareAndSet(false, true)) return;

        io.execute(() -> {
            Exception last = null;
            try {
                // The DIY endpoint can occasionally miss a request while Wi-Fi/NSD is
                // settling. A single timeout must not make the UI look permanently dead.
                for (int attempt = 1; attempt <= 4; attempt++) {
                    if (!activityStarted || !d.deviceId.equals(selectedDeviceId)) return;
                    try {
                        SonoffHttp.info(d);
                        if (!d.deviceId.equals(selectedDeviceId)) return;
                        d.save(this);
                        runOnUiThread(() -> {
                            if (!d.deviceId.equals(selectedDeviceId)) return;
                            device = d;
                            connectionFailures = 0;
                            deviceStatus.setText("●  SONOFF CONNESSO");
                            deviceStatus.setTextColor(GREEN);
                            restoreRuntimeState();
                        });
                        return;
                    } catch (Exception e) {
                        last = e;
                        if (attempt < 4) {
                            try { Thread.sleep(550L); } catch (InterruptedException ie) {
                                Thread.currentThread().interrupt();
                                return;
                            }
                        }
                    }
                }

                if (!d.deviceId.equals(selectedDeviceId)) return;
                runOnUiThread(() -> {
                    if (!d.deviceId.equals(selectedDeviceId)) return;
                    // Keep retrying automatically: the selected Device ID is still the
                    // source of truth and discovery may shortly provide a new DHCP IP.
                    device = null;
                    setControlsEnabled(false);
                    deviceStatus.setText("●  SONOFF — RICONNESSIONE…");
                    deviceStatus.setTextColor(AMBER);
                    stateText.setTextColor(AMBER);
                    stateText.setText("RICONNESSIONE AUTOMATICA — nessuna azione richiesta");
                    // The periodic heartbeat/discovery loop will keep retrying.
                });
            } finally {
                validationInFlight.set(false);
            }
        });
    }

    private void healthCheckSelected(DeviceConfig d) {
        if (d == null || !d.isValid() || armed) return;
        if (!d.deviceId.equals(selectedDeviceId)) return;
        if (!healthCheckInFlight.compareAndSet(false, true)) return;

        io.execute(() -> {
            try {
                SonoffHttp.infoQuick(d, 1100);
                if (!d.deviceId.equals(selectedDeviceId)) return;
                d.save(this);
                runOnUiThread(() -> {
                    if (!d.deviceId.equals(selectedDeviceId) || armed) return;
                    connectionFailures = 0;
                    device = d;
                    deviceStatus.setText("●  SONOFF CONNESSO");
                    deviceStatus.setTextColor(GREEN);
                    restoreRuntimeState();
                });
            } catch (Exception e) {
                if (!d.deviceId.equals(selectedDeviceId)) return;
                runOnUiThread(() -> {
                    if (!d.deviceId.equals(selectedDeviceId) || armed) return;
                    connectionFailures++;
                    setControlsEnabled(false);
                    if (connectionFailures < 2) {
                        deviceStatus.setText("●  VERIFICA CONNESSIONE…");
                        deviceStatus.setTextColor(AMBER);
                        stateText.setTextColor(AMBER);
                        stateText.setText("VERIFICA CONNESSIONE — attendo il MINIR2…");
                    } else {
                        device = null;
                        deviceStatus.setText("●  SONOFF NON RAGGIUNGIBILE");
                        deviceStatus.setTextColor(RED);
                        stateText.setTextColor(RED);
                        stateText.setText("SONOFF NON RAGGIUNGIBILE — verifica la rete.");
                    }
                });
            } finally {
                healthCheckInFlight.set(false);
            }
        });
    }

    @Override public void onSearching() {
        if (selectedDeviceId == null || selectedDeviceId.isEmpty()) {
            deviceStatus.setText("●  SONOFF — ricerca…");
            deviceStatus.setTextColor(MUTED);
        } else if (device == null || !device.isValid()) {
            deviceStatus.setText("●  SONOFF — connessione…");
            deviceStatus.setTextColor(MUTED);
        }
    }

    @Override public void onDiyCandidate(DeviceConfig found, String type, String apiVersion) {
        FoundDevice f = new FoundDevice(found, true, type, apiVersion);
        foundDevices.put(found.deviceId, f);
        if (found.deviceId.equals(selectedSafelightDeviceId)) {
            SafelightConfig.save(this, found);
            safelightDevice = found;
            updateSafelightStatus();
            if (safelightAuto && !armed) ensureSafelightIdleOn();
        }
        if (found.deviceId.equals(selectedDeviceId)) {
            applySelectedFound(f);
        } else if (selectedDeviceId == null || selectedDeviceId.isEmpty()) {
            showCountWithoutSelection();
        }
    }

    @Override public void onEwelinkMode(String host, int port, String deviceId, String type) {
        DeviceConfig cfg = new DeviceConfig(host, port, deviceId);
        FoundDevice f = new FoundDevice(cfg, false, type, "");
        foundDevices.put(deviceId, f);
        if (deviceId.equals(selectedDeviceId)) {
            cfg.save(this);
            applySelectedFound(f);
        } else if (selectedDeviceId == null || selectedDeviceId.isEmpty()) {
            showCountWithoutSelection();
        }
    }

    private void showCountWithoutSelection() {
        int n = foundDevices.size();
        deviceStatus.setText("●  SONOFF DA SELEZIONARE");
        deviceStatus.setTextColor(MUTED);
        selectDeviceButton.setText("⚙");
        stateText.setTextColor(MUTED);
        stateText.setText("Apri le impostazioni per scegliere l’ingranditore.");
    }

    @Override public void onError(String message) {
        if (device == null || !device.isValid()) {
            if (foundDevices.isEmpty()) {
                deviceStatus.setText("●  SONOFF NON RAGGIUNGIBILE");
                deviceStatus.setTextColor(RED);
            }
        }
    }

    private void setControlsEnabled(boolean enabled) {
        boolean ready = enabled && device != null && device.isValid() && !armed;
        actionButton.setEnabled(ready);
        actionButton.setAlpha(ready ? 1f : (darkroomMode ? 0.62f : 0.45f));
        printModeButton.setEnabled(!armed);
        testModeButton.setEnabled(!armed);
        logModeButton.setEnabled(!armed);
        selectDeviceButton.setEnabled(!armed);
        selectDeviceButton.setAlpha(selectDeviceButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
        normalButton.setEnabled(device != null && device.isValid());
        normalButton.setAlpha(normalButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));

        // During ARMATO / ESPOSIZIONE / PAUSA / DISARMO the parameters are not only
        // ignored by setters: their controls are visibly locked to prevent accidental taps.
        setTreeEnabled(printPanel, !armed);
        setTreeEnabled(testPanel, !armed);
        if (printPanel != null) printPanel.setAlpha(armed ? 0.58f : 1f);
        if (testPanel != null) testPanel.setAlpha(armed ? 0.58f : 1f);
    }

    private void setTreeEnabled(View view, boolean enabled) {
        if (view == null) return;
        view.setEnabled(enabled);
        if (view instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) view;
            for (int i = 0; i < g.getChildCount(); i++) setTreeEnabled(g.getChildAt(i), enabled);
        }
    }


    private void configurePalette() {
        if (darkroomMode) {
            // Safelight mode: use only the red subpixel (G=B=0) for emitted light.
            // Strong contrast comes from pure-red-on-black and black-on-red, not white.
            GREEN = Color.rgb(235, 0, 0);
            BLUE = Color.rgb(235, 0, 0);
            CARD = Color.BLACK;
            BUTTON = Color.rgb(18, 0, 0);
            BORDER = Color.rgb(105, 0, 0);
            MUTED = Color.rgb(190, 0, 0);
            AMBER = Color.rgb(235, 0, 0);
            RED = Color.rgb(255, 0, 0);
            LOG_ACCENT = RED;
            TEXT_PRIMARY = Color.rgb(255, 0, 0);
        } else {
            GREEN = Color.rgb(80, 207, 70);
            BLUE = Color.rgb(63, 151, 255);
            CARD = Color.rgb(18, 21, 23);
            BUTTON = Color.rgb(31, 35, 38);
            BORDER = Color.rgb(57, 63, 68);
            MUTED = Color.rgb(169, 176, 184);
            AMBER = Color.rgb(255, 181, 71);
            RED = Color.rgb(255, 92, 92);
            LOG_ACCENT = Color.rgb(107, 114, 128);
            TEXT_PRIMARY = Color.WHITE;
        }
        try { getWindow().getClass().getMethod("setStatusBarColor", int.class).invoke(getWindow(), Color.BLACK); } catch (Exception ignored) {}
        try { getWindow().getClass().getMethod("setNavigationBarColor", int.class).invoke(getWindow(), Color.BLACK); } catch (Exception ignored) {}
    }

    private void applyDarkroomWindow() {
        Window w = getWindow();
        if (w == null) return;
        if (darkroomMode) {
            try {
                w.getDecorView().setSystemUiVisibility(
                        View.SYSTEM_UI_FLAG_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                                | 4096
                                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
            } catch (Exception ignored) {}
            try {
                android.view.WindowManager.LayoutParams lp = w.getAttributes();
                lp.screenBrightness = 0.10f;
                w.setAttributes(lp);
            } catch (Exception ignored) {}
        } else {
            try { w.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE); } catch (Exception ignored) {}
            try {
                android.view.WindowManager.LayoutParams lp = w.getAttributes();
                lp.screenBrightness = -1f;
                w.setAttributes(lp);
            } catch (Exception ignored) {}
        }
    }

    private NotificationManager notificationManager() {
        return (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
    }

    private boolean hasDndAccess() {
        if (Build.VERSION.SDK_INT < 23) return true;
        try {
            NotificationManager nm = notificationManager();
            return nm != null && nm.isNotificationPolicyAccessGranted();
        } catch (Exception ignored) {
            return false;
        }
    }

    private void openDndAccessSettings() {
        try {
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS));
        } catch (Exception e) {
            Toast.makeText(this, "Apri Android > Non disturbare e autorizza Darkroom Timer", Toast.LENGTH_LONG).show();
        }
    }

    private int darkroomSuppressedVisualEffects() {
        if (Build.VERSION.SDK_INT >= 28) {
            return NotificationManager.Policy.SUPPRESSED_EFFECT_FULL_SCREEN_INTENT
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_LIGHTS
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_PEEK
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_STATUS_BAR
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_BADGE
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_AMBIENT
                    | NotificationManager.Policy.SUPPRESSED_EFFECT_NOTIFICATION_LIST;
        }
        return NotificationManager.Policy.SUPPRESSED_EFFECT_SCREEN_ON
                | NotificationManager.Policy.SUPPRESSED_EFFECT_SCREEN_OFF;
    }

    private NotificationManager.Policy darkroomNotificationPolicy() {
        int effects = darkroomSuppressedVisualEffects();
        if (Build.VERSION.SDK_INT >= 30) {
            return new NotificationManager.Policy(
                    0,
                    NotificationManager.Policy.PRIORITY_SENDERS_ANY,
                    NotificationManager.Policy.PRIORITY_SENDERS_ANY,
                    effects,
                    NotificationManager.Policy.CONVERSATION_SENDERS_NONE);
        }
        return new NotificationManager.Policy(
                0,
                NotificationManager.Policy.PRIORITY_SENDERS_ANY,
                NotificationManager.Policy.PRIORITY_SENDERS_ANY,
                effects);
    }

    private void enableDarkroomProtection() {
        if (!darkroomProtection || !darkroomMode || !hasDndAccess()) return;
        try {
            NotificationManager nm = notificationManager();
            if (nm == null) return;
            SharedPreferences state = getSharedPreferences("darkroom_dnd", MODE_PRIVATE);
            if (!state.getBoolean("applied", false)) {
                NotificationManager.Policy old = nm.getNotificationPolicy();
                SharedPreferences.Editor ed = state.edit()
                        .putInt("previousFilter", nm.getCurrentInterruptionFilter())
                        .putInt("priorityCategories", old.priorityCategories)
                        .putInt("priorityCallSenders", old.priorityCallSenders)
                        .putInt("priorityMessageSenders", old.priorityMessageSenders)
                        .putInt("suppressedVisualEffects", old.suppressedVisualEffects);
                if (Build.VERSION.SDK_INT >= 30) {
                    ed.putInt("priorityConversationSenders", old.priorityConversationSenders);
                }
                ed.apply();
            }
            nm.setNotificationPolicy(darkroomNotificationPolicy());
            nm.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_PRIORITY);
            state.edit().putBoolean("applied", true).apply();
        } catch (Exception e) {
            Toast.makeText(this, "Protezione notifiche non attivabile: controlla l'autorizzazione Non disturbare", Toast.LENGTH_LONG).show();
        }
    }

    private void restoreDarkroomProtection() {
        SharedPreferences state = getSharedPreferences("darkroom_dnd", MODE_PRIVATE);
        if (!state.getBoolean("applied", false) || !hasDndAccess()) return;
        try {
            NotificationManager nm = notificationManager();
            if (nm == null) return;
            int categories = state.getInt("priorityCategories", 0);
            int calls = state.getInt("priorityCallSenders", NotificationManager.Policy.PRIORITY_SENDERS_ANY);
            int messages = state.getInt("priorityMessageSenders", NotificationManager.Policy.PRIORITY_SENDERS_ANY);
            int effects = state.getInt("suppressedVisualEffects", 0);
            NotificationManager.Policy old;
            if (Build.VERSION.SDK_INT >= 30) {
                int conversations = state.getInt("priorityConversationSenders", NotificationManager.Policy.CONVERSATION_SENDERS_ANYONE);
                old = new NotificationManager.Policy(categories, calls, messages, effects, conversations);
            } else {
                old = new NotificationManager.Policy(categories, calls, messages, effects);
            }
            nm.setNotificationPolicy(old);
            int previousFilter = state.getInt("previousFilter", NotificationManager.INTERRUPTION_FILTER_ALL);
            if (previousFilter == NotificationManager.INTERRUPTION_FILTER_UNKNOWN) previousFilter = NotificationManager.INTERRUPTION_FILTER_ALL;
            nm.setInterruptionFilter(previousFilter);
            state.edit().clear().apply();
        } catch (Exception ignored) {}
    }

    private void syncDarkroomProtection() {
        if (darkroomMode && darkroomProtection) enableDarkroomProtection();
        else restoreDarkroomProtection();
    }

    private void showDarkroomProtectionChoiceDialog(final Dialog settingsDialog) {
        final Dialog choice = new Dialog(this);
        choice.requestWindowFeature(Window.FEATURE_NO_TITLE);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20), dp(18), dp(20), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        TextView title = text("PROTEZIONE CAMERA OSCURA", 19, TEXT_PRIMARY, true);
        panel.addView(title, margin(lp(-1, -2), 0, 0, 0, 12));

        TextView message = text(
                "Per evitare che notifiche e chiamate illuminino il telefono, Darkroom Timer deve poter gestire Non disturbare. "
                        + "Android aprirà una schermata di sistema: autorizza Darkroom Timer e, tornando indietro, entrerai automaticamente in modalità camera oscura.\n\n"
                        + "Puoi anche entrare senza protezione.",
                14, TEXT_PRIMARY, false);
        message.setLineSpacing(0, 1.08f);
        panel.addView(message, margin(lp(-1, -2), 0, 0, 0, 16));

        Button authorize = compactButton("AUTORIZZA NON DISTURBARE");
        authorize.setBackground(roundRect(BLUE, 9, 0, 0));
        authorize.setTextColor(Color.BLACK);
        authorize.setOnClickListener(v -> {
            choice.dismiss();
            pendingDarkroomAfterDndPermission = true;
            if (settingsDialog != null) settingsDialog.dismiss();
            openDndAccessSettings();
        });
        panel.addView(authorize, lp(-1, dp(52)));

        Button without = compactButton("ENTRA SENZA PROTEZIONE");
        without.setOnClickListener(v -> {
            choice.dismiss();
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomMode", true).apply();
            if (settingsDialog != null) settingsDialog.dismiss();
            recreate();
        });
        panel.addView(without, margin(lp(-1, dp(50)), 0, 8, 0, 0));

        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> choice.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        choice.setContentView(panel);
        Window w = choice.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        choice.show();
        if (w != null) {
            int width = (int) (getResources().getDisplayMetrics().widthPixels * 0.92f);
            w.setLayout(width, ViewGroup.LayoutParams.WRAP_CONTENT);
        }
    }

    private void setDarkroomModeFromSettings(boolean enabled, Dialog settingsDialog) {
        if (!enabled) {
            restoreDarkroomProtection();
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomMode", false).apply();
            if (settingsDialog != null) settingsDialog.dismiss();
            recreate();
            return;
        }
        if (darkroomProtection && !hasDndAccess()) {
            showDarkroomProtectionChoiceDialog(settingsDialog);
            return;
        }
        getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomMode", true).apply();
        if (settingsDialog != null) settingsDialog.dismiss();
        recreate();
    }

    private int[] currentTestStripTargets() {
        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);
    }

    private String cumulativeTimes() {
        int[] physical = TimingMath.physicalTargets(currentTestStripTargets(), testStripMethod);
        return "TEMPI STRISCE · " + TimingMath.normalizeMaskingMethod(testStripMethod) + "  " + TimingMath.seriesLabel(physical);
    }

    private void updateTimingUi() {
        boolean fstop = TimingMath.isFStop(timingMethod);
        if (printStepText != null) printStepText.setText(printStepDescription());
        if (testPromptText != null) testPromptText.setText(testPromptDescription());
        if (testStepText != null) testStepText.setText(testStepDescription());
        if (printFStopBadge != null) printFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);
        if (testFStopBadge != null) testFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);
        updateCumulativeTimes();
        applyModeUi();
        refreshSplitProvinoUi();
    }

    private TextView fStopBadge(boolean compact) {
        int accent = darkroomMode ? RED : Color.rgb(201, 157, 70);
        int fill = darkroomMode ? Color.BLACK : Color.rgb(31, 29, 24);
        TextView badge = text(compact ? "F-STOP  ·  ¼" : "F-STOP  ·  ¼ stop", compact ? 10 : 12, accent, true);
        badge.setGravity(Gravity.CENTER);
        badge.setPadding(dp(compact ? 8 : 12), dp(compact ? 3 : 4), dp(compact ? 8 : 12), dp(compact ? 3 : 4));
        badge.setBackground(roundRect(fill, compact ? 10 : 13, 1, accent));
        badge.setContentDescription("Modalità F-STOP, passo un quarto di stop");
        return badge;
    }

    private TextView addFStopBadge(LinearLayout parent, boolean compact) {
        if (parent == null) return null;
        TextView badge = fStopBadge(compact);
        badge.setVisibility(TimingMath.isFStop(timingMethod) ? View.VISIBLE : View.GONE);
        parent.addView(badge, margin(lp(compact ? -2 : -1, dp(compact ? 26 : 32)), compact ? 0 : dp(36), dp(6), compact ? 0 : dp(36), dp(6)));
        return badge;
    }

    private String printStepDescription() {
        return TimingMath.isFStop(timingMethod) ? "Singola esposizione • passo ¼ stop" : "Singola esposizione • passo 0,5 s";
    }

    private String testPromptDescription() {
        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";
    }

    private String testStepDescription() {
        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";
    }

    private void updateCumulativeTimes() {
        if (testCumulativeText != null) testCumulativeText.setText(cumulativeTimes());
    }

    private LinearLayout settingsGroup(String heading) {
        LinearLayout g = card();
        g.setPadding(dp(12), dp(10), dp(12), dp(12));
        TextView h = text(heading, 11, MUTED, true);
        h.setPadding(dp(4), 0, dp(4), dp(8));
        g.addView(h, lp(-1,-2));
        return g;
    }

    private void showSettingsDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView settingsScroll = new ScrollView(this);
        settingsScroll.setFillViewport(true);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        settingsScroll.addView(panel, new ScrollView.LayoutParams(-1,-2));

        panel.addView(text("IMPOSTAZIONI", 20, TEXT_PRIMARY, true), margin(lp(-1,-2),0,0,0,12));

        LinearLayout timingGroup = settingsGroup("TEMPORIZZAZIONE");
        Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);
        timing.setOnClickListener(v -> {
            timingMethod = TimingMath.isFStop(timingMethod) ? TimingMath.METHOD_SECONDS : TimingMath.METHOD_FSTOP;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("timingMethod", timingMethod).apply();
            timing.setText("METODO DI TEMPORIZZAZIONE: " + timingMethod);
            updateTimingUi();
        });
        timingGroup.addView(timing, lp(-1,dp(50)));
        panel.addView(timingGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout darkroomGroup = settingsGroup("CAMERA OSCURA E LUCE ROSSA");
        Button safelightToggle = compactButton("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
        safelightToggle.setOnClickListener(v -> {
            if (!safelightAuto) {
                DeviceConfig safe = SafelightConfig.load(this);
                if (!safe.isValid()) { Toast.makeText(this, "Prima seleziona il SONOFF della luce rossa", Toast.LENGTH_LONG).show(); return; }
                if (safe.deviceId.equals(selectedDeviceId)) { Toast.makeText(this, "Ingranditore e luce rossa devono usare due SONOFF diversi", Toast.LENGTH_LONG).show(); return; }
                safelightAuto = true;
            } else safelightAuto = false;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("safelightAuto", safelightAuto).apply();
            safelightToggle.setText("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
            updateSafelightStatus();
            if (safelightAuto) ensureSafelightIdleOn(); else stopSafelightInterlock();
        });
        darkroomGroup.addView(safelightToggle, lp(-1,dp(50)));

        DeviceConfig safeCfg = SafelightConfig.load(this);
        String safeInfo = safeCfg.isValid()
                ? "SONOFF SAFELIGHT  •  ID " + safeCfg.deviceId + "\nStato manuale rispettato • OFF durante l’ingranditore"
                : "SONOFF SAFELIGHT  •  non configurato";
        TextView safeDetails = text(safeInfo, 12, MUTED, false);
        safeDetails.setPadding(dp(4), dp(7), dp(4), dp(5));
        darkroomGroup.addView(safeDetails, lp(-1,-2));
        Button safePick = compactButton(safeCfg.isValid() ? "CAMBIA SONOFF SAFELIGHT" : "SCEGLI SONOFF SAFELIGHT");
        safePick.setOnClickListener(v -> { dialog.dismiss(); showSafelightPicker(); });
        darkroomGroup.addView(safePick, margin(lp(-1,dp(48)),0,0,0,8));

        Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));
        dark.setOnClickListener(v -> setDarkroomModeFromSettings(!darkroomMode, dialog));
        darkroomGroup.addView(dark, margin(lp(-1,dp(50)),0,0,0,7));

        Button protection = compactButton("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
        protection.setOnClickListener(v -> {
            darkroomProtection = !darkroomProtection;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomProtection", darkroomProtection).apply();
            protection.setText("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
            syncDarkroomProtection();
        });
        darkroomGroup.addView(protection, margin(lp(-1,dp(50)),0,0,0,6));

        if (darkroomProtection && !hasDndAccess()) {
            Button authorizeDnd = compactButton("AUTORIZZA NON DISTURBARE");
            authorizeDnd.setTextColor(AMBER);
            authorizeDnd.setOnClickListener(v -> { dialog.dismiss(); openDndAccessSettings(); });
            darkroomGroup.addView(authorizeDnd, margin(lp(-1,dp(46)),0,0,0,5));
        }
        TextView protectionNote = text("Non disturbare blocca chiamate/notifiche e sopprime gli avvisi visivi durante la modalità camera oscura; tornando alla modalità normale vengono ripristinate le impostazioni precedenti.", 11, MUTED, false);
        protectionNote.setPadding(dp(4), dp(2), dp(4), 0);
        darkroomGroup.addView(protectionNote, lp(-1,-2));
        panel.addView(darkroomGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout feedbackGroup = settingsGroup("FEEDBACK DURANTE IL LAVORO");
        Button beep = compactButton("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));
        beep.setOnClickListener(v -> { feedbackBeep=!feedbackBeep; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("feedbackBeep",feedbackBeep).apply(); beep.setText("BEEP FINE CICLO: "+(feedbackBeep?"ON":"OFF")); });
        feedbackGroup.addView(beep, lp(-1,dp(50)));
        Button voice = compactButton("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));
        voice.setOnClickListener(v -> { voiceGuide=!voiceGuide; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("voiceGuide",voiceGuide).apply(); voice.setText("GUIDA VOCALE PIANO: "+(voiceGuide?"ON":"OFF")); });
        feedbackGroup.addView(voice, margin(lp(-1,dp(50)),0,7,0,0));
        panel.addView(feedbackGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout diagnosticsGroup = settingsGroup("DIAGNOSTICA");
        Button diagnostics = compactButton("CRONOLOGIA TECNICA");
        diagnostics.setOnClickListener(v -> showTechnicalLogDialog());
        diagnosticsGroup.addView(diagnostics, lp(-1,dp(50)));
        panel.addView(diagnosticsGroup, margin(lp(-1,-2),0,0,0,10));

        LinearLayout hardwareGroup = settingsGroup("HARDWARE INGRANDITORE");
        DeviceConfig saved = DeviceConfig.load(this);
        String tech = "SONOFF INGRANDITORE\n";
        if (selectedDeviceId == null || selectedDeviceId.isEmpty()) tech += "Nessun dispositivo selezionato";
        else tech += (device != null && device.isValid() ? "DIY verificata" : "non verificato")
                + "\nDevice ID: " + selectedDeviceId
                + (saved.host == null || saved.host.isEmpty() ? "" : "\nIP: " + saved.host + ":" + saved.port);
        TextView details = text(tech, 13, MUTED, false);
        details.setPadding(dp(4), dp(2), dp(4), dp(8));
        hardwareGroup.addView(details, lp(-1,-2));

        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");
        change.setOnClickListener(v -> { dialog.dismiss(); showDevicePicker(); });
        hardwareGroup.addView(change, lp(-1,dp(50)));

        TextView lplTitle = text("JOBO/LPL 7451 · CALIBRAZIONE COLONNA", 12, TEXT_PRIMARY, true);
        lplTitle.setPadding(dp(4), dp(10), dp(4), dp(4));
        hardwareGroup.addView(lplTitle, lp(-1,-2));
        TextView lplNote = text("Calibrazione attiva: scala 67, piano negativo–base 73 cm, marginatore 6 mm. Offset meccanico 6,0 cm; distanza negativo–carta = scala + 5,4 cm.", 11, MUTED, false);
        lplNote.setPadding(dp(4), dp(2), dp(4), dp(6));
        hardwareGroup.addView(lplNote, lp(-1,-2));

        panel.addView(hardwareGroup, margin(lp(-1,-2),0,0,0,10));

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, lp(-1,dp(50)));

        dialog.setContentView(settingsScroll);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), (int)(getResources().getDisplayMetrics().heightPixels * 0.90f));
    }

    private static int snap(int ms, int min, int max) {
        ms = Math.max(min, Math.min(max, ms));
        return Math.round(ms / 500f) * 500;
    }

    private static String formatTime(int ms) {
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }

    private LinearLayout card() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(15), dp(15), dp(15), dp(15));
        l.setBackground(roundRect(CARD, 12, 1, BORDER));
        return l;
    }

    private TextView text(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private Button navButton(String label, int iconKind) {
        return new PrimaryNavButton(this, label, iconKind);
    }

    private void styleNavButton(Button button, boolean selected, int normalAccent) {
        int foreground;
        if (darkroomMode) {
            foreground = selected ? RED : Color.rgb(125, 0, 0);
        } else {
            foreground = selected ? (normalAccent == LOG_ACCENT ? TEXT_PRIMARY : normalAccent) : MUTED;
        }
        button.setTextColor(foreground);
        button.setTypeface(Typeface.DEFAULT, selected ? Typeface.BOLD : Typeface.NORMAL);
        button.setBackgroundColor(Color.TRANSPARENT);
        if (button instanceof PrimaryNavButton) {
            PrimaryNavButton navButton = (PrimaryNavButton) button;
            navButton.setIconColor(foreground);
            navButton.setActiveIndicator(selected, foreground);
        }
    }

    private Button compactButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextColor(TEXT_PRIMARY);
        b.setTextSize(12);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        b.setBackground(roundRect(BUTTON, 8, 1, BORDER));
        return b;
    }

    private Button smallButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(28);
        b.setTextColor(darkroomMode ? TEXT_PRIMARY : Color.rgb(195, 204, 210));
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        b.setBackground(roundRect(BUTTON, 10, 0, 0));
        return b;
    }

    private Button smallCompactButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(23);
        b.setTextColor(darkroomMode ? TEXT_PRIMARY : Color.rgb(195, 204, 210));
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        b.setBackground(roundRect(BUTTON, 8, 0, 0));
        return b;
    }

    private Button shortcutButton(String s, int accent) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(accent);
        b.setAllCaps(false);
        b.setBackground(roundRect(BUTTON, 8, 0, 0));
        b.setPadding(0, 0, 0, 0);
        return b;
    }

    private GradientDrawable roundRect(int color, int radiusDp, int strokeDp, int strokeColor) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        if (strokeDp > 0) g.setStroke(dp(strokeDp), strokeColor);
        return g;
    }

    private View divider() {
        View v = new View(this);
        v.setBackgroundColor(darkroomMode ? BORDER : Color.rgb(42, 47, 50));
        v.setLayoutParams(new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(1)));
        return v;
    }

    private View space(int d) {
        View v = new View(this);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, dp(d)));
        return v;
    }

    private int dp(int d) { return Math.round(d * getResources().getDisplayMetrics().density); }

    private static LinearLayout.LayoutParams lp(int w, int h) { return new LinearLayout.LayoutParams(w, h); }
    private static LinearLayout.LayoutParams lp(int w, int h, float weight) { return new LinearLayout.LayoutParams(w, h, weight); }
    private static LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(l, t, r, b);
        return p;
    }
}
