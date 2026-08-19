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
    private boolean darkroomMode;
    private boolean feedbackBeep;
    private boolean darkroomProtection;
    private String timingMethod = TimingMath.METHOD_SECONDS;
    private boolean safelightAuto = false;
    private boolean pendingDarkroomAfterDndPermission = false;

    private static final int MODE_PRINT = 0;
    private static final int MODE_TEST = 1;
    private static final int MODE_LOG = 2;

    private static final int REQ_EXPORT_BACKUP = 4101;
    private static final int REQ_IMPORT_BACKUP = 4102;
    private static final int REQ_EXPORT_JPG = 4103;
    private static final String APP_VERSION = "0.7.7";

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
    private int testWidthMs = 2000;
    private int testCount = 7;
    private int testPauseMs = 2000;
    private boolean armed = false;
    private LogEntry pendingJpegEntry;
    private long transientCompletionUntilMs = 0L;

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
        SharedPreferences p = getSharedPreferences("ui", MODE_PRIVATE);
        darkroomMode = p.getBoolean("darkroomMode", false);
        feedbackBeep = p.getBoolean("feedbackBeep", true);
        darkroomProtection = p.getBoolean("darkroomProtection", true);
        timingMethod = TimingMath.normalizeMethod(p.getString("timingMethod", TimingMath.METHOD_SECONDS));
        safelightAuto = p.getBoolean("safelightAuto", false);
        logGroupingEnabled = p.getBoolean("logGroupingEnabled", true);
        configurePalette();
        applyDarkroomWindow();
        mode = p.getInt("mode", MODE_PRINT);
        printWidthMs = p.getInt("printWidthMs", 8500);
        testWidthMs = p.getInt("testWidthMs", 2000);
        testCount = p.getInt("testCount", 7);
        testPauseMs = p.getInt("testPauseMs", 2000);

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
        // A cycle may have completed while the screen/activity was stopped.
        // Re-read the service's durable state instead of relying on a missed broadcast.
        restoreRuntimeState();

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
                || SonoffArmService.STATE_PAUSING.equals(state);
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
            setStatusPresentation("ATTENZIONE", message == null ? "Errore del ciclo" : message, RED);
            cancelCycleButton.setVisibility(View.GONE);
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
                title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;
                detail = "Scegli la striscia da usare come punto di partenza per la stampa";
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
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(14), dp(16), dp(28));
        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
        root.addView(title, lp(-1, dp(48)));

        LinearLayout deviceCard = card();
        LinearLayout deviceTop = new LinearLayout(this);
        deviceTop.setOrientation(LinearLayout.HORIZONTAL);
        deviceTop.setGravity(Gravity.CENTER_VERTICAL);
        TextView deviceName = text("INGRANDITORE", 14, TEXT_PRIMARY, true);
        deviceTop.addView(deviceName, lp(0, -2, 1f));
        selectDeviceButton = compactButton("⚙");
        selectDeviceButton.setTextSize(20);
        selectDeviceButton.setOnClickListener(v -> showSettingsDialog());
        deviceTop.addView(selectDeviceButton, lp(dp(56), dp(40)));
        deviceCard.addView(deviceTop);
        deviceStatus = text("Cerco i SONOFF sulla rete…", 13, MUTED, false);
        deviceStatus.setPadding(0, dp(8), 0, 0);
        deviceCard.addView(deviceStatus);
        safelightStatus = text("", 11, MUTED, false);
        safelightStatus.setPadding(0, dp(4), 0, 0);
        deviceCard.addView(safelightStatus);
        updateSafelightStatus();
        root.addView(deviceCard, margin(lp(-1, -2), 0, 4, 0, 14));

        LinearLayout modeRow = new LinearLayout(this);
        modeRow.setOrientation(LinearLayout.HORIZONTAL);
        printModeButton = navButton("STAMPA", PrimaryNavButton.ICON_TIMER);
        testModeButton = navButton("PROVINO", PrimaryNavButton.ICON_TEST);
        logModeButton = navButton("LOG", PrimaryNavButton.ICON_LOG);
        printModeButton.setOnClickListener(v -> setMode(MODE_PRINT));
        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));
        logModeButton.setOnClickListener(v -> setMode(MODE_LOG));
        modeRow.addView(printModeButton, margin(lp(0, dp(88), 1f), 0, 0, dp(5), 0));
        modeRow.addView(testModeButton, margin(lp(0, dp(88), 1f), dp(5), 0, dp(5), 0));
        modeRow.addView(logModeButton, margin(lp(0, dp(88), 1f), dp(5), 0, 0, 0));
        root.addView(modeRow, margin(lp(-1, -2), 0, 0, 0, 14));

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

        TextView footer = text("Darkroom Timer di F.G. - v" + APP_VERSION, 12, darkroomMode ? Color.rgb(92, 18, 18) : Color.rgb(105, 112, 118), false);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 0));

        setContentView(scroll);
        setControlsEnabled(false);
    }

    private LinearLayout buildPrintPanel() {
        LinearLayout box = card();
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
        return box;
    }

    private LinearLayout buildTestPanel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);

        LinearLayout exposure = card();
        testPromptText = text(testPromptDescription(), 16, TEXT_PRIMARY, true);
        testPromptText.setGravity(Gravity.CENTER);
        exposure.addView(testPromptText);
        testStepText = text(testStepDescription(), 12, MUTED, false);
        testStepText.setGravity(Gravity.CENTER);
        exposure.addView(testStepText);
        testFStopBadge = addFStopBadge(exposure, false);
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
        logFilterAllButton.setOnClickListener(v -> setLogFilter("ALL"));
        logFilter35Button.setOnClickListener(v -> setLogFilter("35mm"));
        logFilter66Button.setOnClickListener(v -> setLogFilter("6x6"));
        filterRow.addView(logFilterAllButton, margin(lp(0, dp(43), 1f), 0, 0, dp(4), 0));
        filterRow.addView(logFilter35Button, margin(lp(0, dp(43), 1f), dp(4), 0, dp(4), 0));
        filterRow.addView(logFilter66Button, margin(lp(0, dp(43), 1f), dp(4), 0, 0, 0));
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

    private boolean groupMatchesFormat(LogGroup group) {
        if ("ALL".equals(logFilter)) return true;
        for (LogEntry e : group.entries) {
            String neg = e.negative == null ? "" : e.negative.trim();
            if ("35mm".equals(logFilter) && "35mm".equalsIgnoreCase(neg)) return true;
            if ("6x6".equals(logFilter) && "6x6".equalsIgnoreCase(neg)) return true;
        }
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
        if (e.negative != null && !e.negative.trim().isEmpty()) mainBits.add("6x6".equals(e.negative) ? "6×6" : e.negative);
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
        } else if (e.testMs > 0) {
            int[] strips = TimingMath.fromCsv(e.testStripTimes);
            if (strips.length != e.testCount) strips = TimingMath.cumulativeSeries(e.testMethod, e.testMs, e.testCount);
            String provino = "Provino · " + TimingMath.normalizeMethod(e.testMethod) + " · " + (e.testStep == null || e.testStep.trim().isEmpty() ? TimingMath.stepLabel(e.testMethod) : e.testStep) + "\nStrisce: " + TimingMath.seriesLabel(strips);
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
            if (item.negative != null && !item.negative.trim().isEmpty()) details.add("6x6".equals(item.negative) ? "6×6" : item.negative);
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
        // A print log always carries the latest completed print and the latest completed test strip.
        // No time window: the user's rule is simply "associate the last test strip to the print".
        if (printAt > 0 && printAt >= testAt) {
            e.timestamp = printAt;
            e.exposureMs = p.getInt("lastPrintMs", 0);
            e.exposureMethod = TimingMath.normalizeMethod(p.getString("lastPrintMethod", TimingMath.METHOD_SECONDS));
            e.exposureStep = p.getString("lastPrintStep", TimingMath.stepLabel(e.exposureMethod));
            if (testAt > 0) {
                e.testMs = p.getInt("lastTestMs", 0);
                e.testCount = p.getInt("lastTestCount", 0);
                e.testMethod = TimingMath.normalizeMethod(p.getString("lastTestMethod", TimingMath.METHOD_SECONDS));
                e.testStep = p.getString("lastTestStep", TimingMath.stepLabel(e.testMethod));
                e.testStripTimes = p.getString("lastTestStripTimes", "");
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
        }

        // Defaults for every new print card; all remain editable in the editor.
        e.aperture = "11,5";
        e.magenta = "0";
        e.yellow = "0";
        e.density = "0";
        e.paper = "Fomaspeed Variant 311 RC lucida";
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
        SharedPreferences template = getSharedPreferences("log_reprint", MODE_PRIVATE);
        long activatedAt = template.getLong("activatedAt", Long.MAX_VALUE);
        if (template.getBoolean("active", false) && e.exposureMs > 0 && e.timestamp >= activatedAt) {
            template.edit().clear().apply();
        }
    }

    private void useLogEntryForPrint(LogEntry entry) {
        if (entry == null || entry.exposureMs <= 0) return;
        setPrintTime(entry.exposureMs);
        getSharedPreferences("log_reprint", MODE_PRIVATE).edit()
                .clear()
                .putBoolean("active", true)
                .putLong("activatedAt", System.currentTimeMillis())
                .putString("title", entry.title == null ? "" : entry.title)
                .putString("negative", entry.negative == null ? "" : entry.negative)
                .putString("aperture", entry.aperture == null ? "" : entry.aperture)
                .putString("columnHeight", entry.columnHeight == null ? "" : entry.columnHeight)
                .putString("magenta", entry.magenta == null ? "" : entry.magenta)
                .putString("yellow", entry.yellow == null ? "" : entry.yellow)
                .putString("density", entry.density == null ? "" : entry.density)
                .putString("paper", entry.paper == null ? "" : entry.paper)
                .putString("notes", entry.notes == null ? "" : entry.notes)
                .apply();
        setMode(MODE_PRINT);
        Toast.makeText(this, "Tempo " + formatTime(entry.exposureMs) + " caricato in STAMPA", Toast.LENGTH_SHORT).show();
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
        entry.columnHeight = template.getString("columnHeight", "");
        entry.magenta = template.getString("magenta", entry.magenta);
        entry.yellow = template.getString("yellow", entry.yellow);
        entry.density = template.getString("density", entry.density);
        entry.paper = template.getString("paper", entry.paper);
        entry.notes = template.getString("notes", "");
    }

    private void showLogEditor(final LogEntry entry, final boolean isNew) {
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
        String strips = entry.testMs > 0 ? TimingMath.seriesLabel(stripValues) : "—";
        String printMethod = entry.exposureMs > 0 ? TimingMath.normalizeMethod(entry.exposureMethod) + " · " + (entry.exposureStep == null || entry.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(entry.exposureMethod) : entry.exposureStep) : "—";
        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) : "—";
        TextView autoValues = text(
                "Esposizione finale: " + exposure +
                "\nMetodo stampa: " + printMethod +
                "\nProvino — strisce: " + ntest +
                "\nMetodo provino: " + testMethod +
                "\nTempi strisce: " + strips +
                "\nData: " + formatDate(entry.timestamp) +
                "\nOra: " + formatClock(entry.timestamp), 14, TEXT_PRIMARY, false);
        autoValues.setPadding(0, dp(6), 0, 0);
        auto.addView(autoValues);
        panel.addView(auto, margin(lp(-1, -2), 0, 0, 0, 12));

        final EditText title = editField("Titolo / nome stampa", entry.title);
        panel.addView(title, margin(lp(-1, dp(52)), 0, 0, 0, 8));

        TextView negLabel = text("NEGATIVO", 12, MUTED, true);
        panel.addView(negLabel, margin(lp(-1, -2), 0, 4, 0, 4));
        LinearLayout negRow = new LinearLayout(this);
        negRow.setOrientation(LinearLayout.HORIZONTAL);
        final String[] negative = {entry.negative == null ? "" : entry.negative};
        final Button b35 = compactButton("35mm");
        final Button b66 = compactButton("6×6");
        View.OnClickListener negRefresh = v -> {
            negative[0] = v == b35 ? "35mm" : "6x6";
            b35.setBackground(roundRect("35mm".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b66.setBackground(roundRect("6x6".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b35.setTextColor("35mm".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b66.setTextColor("6x6".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
        };
        b35.setOnClickListener(negRefresh);
        b66.setOnClickListener(negRefresh);
        negRow.addView(b35, margin(lp(0, dp(46), 1f), 0, 0, dp(4), 0));
        negRow.addView(b66, margin(lp(0, dp(46), 1f), dp(4), 0, 0, 0));
        panel.addView(negRow, margin(lp(-1, -2), 0, 0, 0, 8));
        if ("35mm".equals(negative[0])) b35.performClick();
        else if ("6x6".equals(negative[0])) b66.performClick();

        final EditText aperture = editField("Diaframma f/", entry.aperture);
        final EditText column = editField("Altezza colonna cm", entry.columnHeight);
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
        panel.addView(column, margin(lp(-1, dp(52)), 0, 0, 0, 8));
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
            entry.columnHeight = column.getText().toString().trim();
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
                Button useForPrint = compactButton("USA PER STAMPA  •  " + formatTime(entry.exposureMs));
                useForPrint.setBackground(roundRect(GREEN, 9, 0, 0));
                useForPrint.setTextColor(Color.BLACK);
                useForPrint.setOnClickListener(v -> {
                    useLogEntryForPrint(entry);
                    dialog.dismiss();
                });
                panel.addView(useForPrint, margin(lp(-1, dp(50)), 0, 8, 0, 0));
            }

            Button exportJpg = compactButton("ESPORTA SCHEDA JPG 9:16");
            exportJpg.setOnClickListener(v -> {
                entry.title = title.getText().toString().trim();
                entry.negative = negative[0];
                entry.aperture = aperture.getText().toString().trim();
                entry.columnHeight = column.getText().toString().trim();
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
            actionButton.setText(print ? "ARMA STAMPA • " + formatTime(printWidthMs)
                    : (TimingMath.isFStop(timingMethod)
                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"
                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));
        }
    }

    private void arm() {
        if (mode == MODE_LOG) return;
        if (device == null || !device.isValid()) {
            stateText.setText("Il SONOFF dell’ingranditore non è ancora verificato in DIY");
            return;
        }
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
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);
            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
        } else {
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);
            i.putExtra(SonoffArmService.EXTRA_WIDTH, testWidthMs);
            i.putExtra(SonoffArmService.EXTRA_COUNT, testCount);
            i.putExtra(SonoffArmService.EXTRA_PAUSE, testPauseMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());
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

    private void maybeShowTestResultChooser() {
        if (armed || mode != MODE_TEST || isFinishing()) return;
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long testAt = session.getLong("lastTestAt", 0L);
        if (testAt <= 0) return;
        SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);
        if (ui.getLong("lastTestChooserShownAt", 0L) >= testAt) return;
        ui.edit().putLong("lastTestChooserShownAt", testAt).apply();

        final int step = session.getInt("lastTestMs", testWidthMs);
        final int n = Math.max(2, Math.min(20, session.getInt("lastTestCount", testCount)));
        int[] storedStrips = TimingMath.fromCsv(session.getString("lastTestStripTimes", ""));
        final int[] strips = storedStrips.length == n ? storedStrips : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);
        String[] choices = new String[n];
        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(strips[i]);
        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {
            int imported = strips[which];
            setMode(MODE_PRINT);
            setPrintTime(imported);
            setStatusPresentation("DAL PROVINO — " + formatTime(imported),
                    "Tempo precompilato e ancora modificabile con + / − o scorciatoie prima di armare.", GREEN);
        }, "NON ORA");
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
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("printWidthMs", printWidthMs).apply();
        printTimeText.setText(formatTime(printWidthMs));
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
            new AlertDialog.Builder(this)
                    .setTitle("Nessun secondo SONOFF DIY trovato")
                    .setMessage("La luce rossa richiede un secondo SONOFF in modalità DIY, diverso da quello dell’ingranditore. Attendi la ricerca di rete e riprova.")
                    .setPositiveButton("OK", null)
                    .show();
            return;
        }
        String[] labels = new String[list.size()];
        for (int i = 0; i < list.size(); i++) {
            FoundDevice f = list.get(i);
            String selected = f.config.deviceId.equals(selectedSafelightDeviceId) ? "  ✓" : "";
            labels[i] = "ID " + f.config.deviceId + selected + "\n" + f.config.host + ":" + f.config.port + " • DIY";
        }
        new AlertDialog.Builder(this)
                .setTitle("Scegli il SONOFF della luce rossa")
                .setItems(labels, (d, which) -> selectSafelight(list.get(which)))
                .setNegativeButton("ANNULLA", null)
                .show();
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
        return "TEMPI CUMULATIVI  " + TimingMath.seriesLabel(currentTestStripTargets());
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

    private void showSettingsDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20), dp(18), dp(20), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        TextView title = text("IMPOSTAZIONI", 20, TEXT_PRIMARY, true);
        panel.addView(title, margin(lp(-1, -2), 0, 0, 0, 14));

        Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);
        timing.setOnClickListener(v -> {
            timingMethod = TimingMath.isFStop(timingMethod) ? TimingMath.METHOD_SECONDS : TimingMath.METHOD_FSTOP;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("timingMethod", timingMethod).apply();
            timing.setText("METODO DI TEMPORIZZAZIONE: " + timingMethod);
            updateTimingUi();
        });
        panel.addView(timing, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        Button safelightToggle = compactButton("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
        safelightToggle.setOnClickListener(v -> {
            if (!safelightAuto) {
                DeviceConfig safe = SafelightConfig.load(this);
                if (!safe.isValid()) {
                    Toast.makeText(this, "Prima seleziona il SONOFF della luce rossa", Toast.LENGTH_LONG).show();
                    return;
                }
                if (safe.deviceId.equals(selectedDeviceId)) {
                    Toast.makeText(this, "Ingranditore e luce rossa devono usare due SONOFF diversi", Toast.LENGTH_LONG).show();
                    return;
                }
                safelightAuto = true;
            } else {
                safelightAuto = false;
            }
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("safelightAuto", safelightAuto).apply();
            safelightToggle.setText("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));
            updateSafelightStatus();
            if (safelightAuto) ensureSafelightIdleOn(); else stopSafelightInterlock();
        });
        panel.addView(safelightToggle, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        DeviceConfig safeCfg = SafelightConfig.load(this);
        String safeInfo = safeCfg.isValid()
                ? "SONOFF SAFELIGHT  •  ID " + safeCfg.deviceId + "\nStato manuale rispettato • OFF durante l’ingranditore"
                : "SONOFF SAFELIGHT  •  non configurato";
        TextView safeDetails = text(safeInfo, 12, MUTED, false);
        safeDetails.setPadding(dp(4), dp(2), dp(4), dp(6));
        panel.addView(safeDetails);
        Button safePick = compactButton(safeCfg.isValid() ? "CAMBIA SONOFF SAFELIGHT" : "SCEGLI SONOFF SAFELIGHT");
        safePick.setOnClickListener(v -> { dialog.dismiss(); showSafelightPicker(); });
        panel.addView(safePick, margin(lp(-1, dp(50)), 0, 0, 0, 12));

        Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));
        dark.setOnClickListener(v -> setDarkroomModeFromSettings(!darkroomMode, dialog));
        panel.addView(dark, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        Button protection = compactButton("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
        protection.setOnClickListener(v -> {
            darkroomProtection = !darkroomProtection;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("darkroomProtection", darkroomProtection).apply();
            protection.setText("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));
            syncDarkroomProtection();
        });
        panel.addView(protection, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        if (darkroomProtection && !hasDndAccess()) {
            Button authorizeDnd = compactButton("AUTORIZZA NON DISTURBARE");
            authorizeDnd.setTextColor(AMBER);
            authorizeDnd.setOnClickListener(v -> {
                dialog.dismiss();
                openDndAccessSettings();
            });
            panel.addView(authorizeDnd, margin(lp(-1, dp(48)), 0, 0, 0, 8));
        }

        TextView protectionNote = text("La protezione usa Non disturbare per bloccare chiamate/notifiche e sopprimere gli avvisi visivi mentre la modalità camera oscura è attiva; al ritorno alla modalità normale ripristina le impostazioni precedenti.", 11, MUTED, false);
        protectionNote.setPadding(dp(4), 0, dp(4), dp(8));
        panel.addView(protectionNote, lp(-1, -2));

        Button beep = compactButton("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));
        beep.setOnClickListener(v -> {
            feedbackBeep = !feedbackBeep;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("feedbackBeep", feedbackBeep).apply();
            beep.setText("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));
        });
        panel.addView(beep, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        Button diagnostics = compactButton("CRONOLOGIA TECNICA");
        diagnostics.setOnClickListener(v -> showTechnicalLogDialog());
        panel.addView(diagnostics, margin(lp(-1, dp(50)), 0, 0, 0, 14));

        DeviceConfig saved = DeviceConfig.load(this);
        String tech = "SONOFF INGRANDITORE\n";
        if (selectedDeviceId == null || selectedDeviceId.isEmpty()) {
            tech += "Nessun dispositivo selezionato";
        } else {
            tech += (device != null && device.isValid() ? "DIY verificata" : "non verificato")
                    + "\nDevice ID: " + selectedDeviceId
                    + (saved.host == null || saved.host.isEmpty() ? "" : "\nIP: " + saved.host + ":" + saved.port);
        }
        TextView details = text(tech, 13, MUTED, false);
        details.setPadding(dp(4), dp(2), dp(4), dp(10));
        panel.addView(details);

        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");
        change.setOnClickListener(v -> { dialog.dismiss(); showDevicePicker(); });
        panel.addView(change, margin(lp(-1, dp(50)), 0, 0, 0, 8));

        Button close = compactButton("CHIUDI");
        close.setOnClickListener(v -> dialog.dismiss());
        panel.addView(close, lp(-1, dp(50)));

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) {
            w.setBackgroundDrawableResource(android.R.color.transparent);
            w.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        }
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.92f), ViewGroup.LayoutParams.WRAP_CONTENT);
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
        int background;
        if (darkroomMode) {
            foreground = selected ? Color.BLACK : RED;
            background = selected ? RED : BUTTON;
        } else {
            foreground = selected ? Color.WHITE : MUTED;
            background = selected ? normalAccent : BUTTON;
        }
        button.setTextColor(foreground);
        button.setBackground(roundRect(background, 12, selected ? 0 : 1, BORDER));
        if (button instanceof PrimaryNavButton) {
            ((PrimaryNavButton) button).setIconColor(foreground);
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
