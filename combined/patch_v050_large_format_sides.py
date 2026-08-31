#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
HOME = ROOT / "home/HomeActivity.java"
TARGET = ROOT / "largeformat/LargeFormatActivity.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.0 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


if not HOME.exists() or not TARGET.exists():
    raise SystemExit("v0.5.0 generated Home/LargeFormatActivity missing")

# Home: shorter label so it fits the established native card.
home = HOME.read_text(encoding="utf-8")
home = replace_once(
    home,
    'HomeCard largeFormat = new HomeCard("SCATTO GRANDE FORMATO", ICON_CHASSIS, false);',
    'HomeCard largeFormat = new HomeCard("GRANDE FORMATO", ICON_CHASSIS, false);',
    "Home label",
)
home = replace_once(
    home,
    'float nameSize = secondary ? 15f : ("SCATTO GRANDE FORMATO".equals(text) ? 16f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f));',
    'float nameSize = secondary ? 15f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f);',
    "Home label size",
)
HOME.write_text(home, encoding="utf-8")


large_format_source = r'''package it.darkroom.timer.largeformat;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** Registro 4x5: ogni chassis ha due lati indipendenti A/B. */
public final class LargeFormatActivity extends Activity {
    private static final int BG = Color.rgb(5, 6, 7);
    private static final int CARD = Color.rgb(18, 19, 20);
    private static final int IVORY = Color.rgb(235, 210, 174);
    private static final int MUTED = Color.rgb(164, 151, 133);
    private static final int BORDER = Color.rgb(164, 139, 105);

    // Vintage, deliberately muted rather than traffic-light colors.
    private static final int EMPTY_COLOR = Color.rgb(108, 105, 98);      // grigio pietra
    private static final int VIRGIN_COLOR = Color.rgb(109, 124, 94);     // verde salvia
    private static final int EXPOSED_COLOR = Color.rgb(151, 103, 66);    // ambra/cuoiato

    private static final String PREFS = "large_format_chassis";
    private static final String KEY_DATA_V2 = "chassis_json_v2";
    private static final String KEY_DATA_V1 = "chassis_json_v1";
    private static final String STATUS_EMPTY = "EMPTY";
    private static final String STATUS_UNEXPOSED = "UNEXPOSED";
    private static final String STATUS_EXPOSED = "EXPOSED";
    private static final String FILM_BRAND = "FOMAPAN";

    private static final String[] ROMAN = {"0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"};
    private static final int[] ISO_VALUES = {100, 200, 400};

    private final List<Chassis> chassis = new ArrayList<>();
    private LinearLayout body;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        load();
        buildFrame();
        showList();
    }

    private void buildFrame() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(24), dp(18), dp(28));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView back = label("‹  HOME", 14, MUTED, true);
        back.setPadding(0, dp(4), 0, dp(12));
        back.setOnClickListener(v -> finish());
        root.addView(back, lp(-1, -2));

        TextView title = label("GRANDE FORMATO", 29, IVORY, true);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        title.setLetterSpacing(0.045f);
        root.addView(title, lp(-1, -2));

        TextView sub = label("CHASSIS 4×5 · LATI A/B", 12, MUTED, true);
        sub.setGravity(Gravity.CENTER_HORIZONTAL);
        sub.setLetterSpacing(0.08f);
        root.addView(sub, margin(lp(-1, -2), 0, 5, 0, 18));

        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        root.addView(body, lp(-1, -2));
        setContentView(scroll);
    }

    private void showList() {
        body.removeAllViews();

        TextView intro = label("Ogni chassis contiene due fogli indipendenti. Tocca il lato A o B per aggiornarne stato e dati.", 14, MUTED, false);
        intro.setLineSpacing(0f, 1.15f);
        body.addView(intro, margin(lp(-1, -2), 0, 0, 0, 14));

        TextView add = action("+  NUOVO CHASSIS", true);
        add.setOnClickListener(v -> {
            Chassis c = new Chassis(nextNumber());
            chassis.add(c);
            save();
            showList();
        });
        body.addView(add, margin(lp(-1, dp(52)), 0, 0, 0, 16));

        Collections.sort(chassis, Comparator.comparingInt((Chassis a) -> a.number));
        if (chassis.isEmpty()) {
            TextView empty = label("Nessuno chassis registrato.", 15, MUTED, false);
            empty.setGravity(Gravity.CENTER);
            body.addView(empty, margin(lp(-1, dp(70)), 0, 18, 0, 0));
            return;
        }

        for (Chassis item : chassis) {
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(dp(14), dp(12), dp(14), dp(13));
            card.setBackground(cardBg());

            TextView name = label("CHASSIS " + item.number, 19, IVORY, true);
            card.addView(name, margin(lp(-1, -2), 0, 0, 0, 9));
            card.addView(sideRow(item, item.a, "A"), margin(lp(-1, dp(66)), 0, 0, 0, 8));
            card.addView(sideRow(item, item.b, "B"), lp(-1, dp(66)));
            body.addView(card, margin(lp(-1, -2), 0, 0, 0, 12));
        }
    }

    private View sideRow(Chassis chassisItem, Side side, String sideName) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(12), dp(8), dp(10), dp(8));
        row.setBackground(statusBackground(side.status, false));
        row.setClickable(true);
        row.setFocusable(true);

        TextView badge = label(chassisItem.number + sideName, 19, IVORY, true);
        badge.setGravity(Gravity.CENTER);
        row.addView(badge, new LinearLayout.LayoutParams(dp(58), -1));

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.VERTICAL);
        TextView state = label(statusLabel(side.status), 13, IVORY, true);
        info.addView(state, lp(-1, -2));
        String detail = sideSummary(side);
        if (!detail.isEmpty()) {
            TextView summary = label(detail, 12, Color.rgb(226, 211, 191), false);
            summary.setSingleLine(true);
            info.addView(summary, margin(lp(-1, -2), 0, 3, 0, 0));
        }
        LinearLayout.LayoutParams infoLp = new LinearLayout.LayoutParams(0, -1, 1f);
        infoLp.setMargins(dp(8), 0, dp(6), 0);
        row.addView(info, infoLp);

        TextView arrow = label("›", 28, IVORY, false);
        arrow.setGravity(Gravity.CENTER);
        row.addView(arrow, new LinearLayout.LayoutParams(dp(28), -1));

        row.setOnClickListener(v -> showSideEditor(chassisItem, side, sideName));
        return row;
    }

    private String sideSummary(Side side) {
        if (STATUS_EMPTY.equals(side.status)) return "";
        String base = FILM_BRAND + (side.iso > 0 ? " · ISO " + side.iso : " · ISO da scegliere");
        if (!STATUS_EXPOSED.equals(side.status)) return base;
        List<String> more = new ArrayList<>();
        if (!side.shutter.isEmpty()) more.add(side.shutter);
        if (!side.aperture.isEmpty()) more.add(side.aperture);
        if (side.shadowZone >= 0 && side.highlightZone >= 0) more.add("Δ " + zoneGap(side) + " EV");
        return more.isEmpty() ? base : base + " · " + join(more, " · ");
    }

    private void showSideEditor(Chassis chassisItem, Side side, String sideName) {
        body.removeAllViews();

        TextView heading = label("CHASSIS " + chassisItem.number + " · LATO " + sideName, 21, IVORY, true);
        body.addView(heading, margin(lp(-1, -2), 0, 0, 0, 14));

        TextView stateTitle = sectionTitle("STATO");
        body.addView(stateTitle, margin(lp(-1, -2), 0, 0, 0, 8));

        final String[] selectedStatus = {normaliseStatus(side.status)};
        LinearLayout stateRow = new LinearLayout(this);
        stateRow.setOrientation(LinearLayout.HORIZONTAL);
        TextView empty = statusButton("VUOTO", STATUS_EMPTY);
        TextView unexposed = statusButton("PIENO\nVERGINE", STATUS_UNEXPOSED);
        TextView exposed = statusButton("PIENO\nESPOSTO", STATUS_EXPOSED);
        stateRow.addView(empty, weightLp());
        stateRow.addView(unexposed, weightMarginLp());
        stateRow.addView(exposed, weightMarginLp());
        body.addView(stateRow, margin(lp(-1, dp(64)), 0, 0, 0, 17));

        LinearLayout loadedFields = new LinearLayout(this);
        loadedFields.setOrientation(LinearLayout.VERTICAL);
        TextView filmTitle = sectionTitle("PELLICOLA");
        loadedFields.addView(filmTitle, margin(lp(-1, -2), 0, 0, 0, 7));
        TextView brand = label(FILM_BRAND, 17, IVORY, true);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        brand.setPadding(dp(12), 0, dp(12), 0);
        brand.setBackground(inputBg());
        loadedFields.addView(brand, margin(lp(-1, dp(50)), 0, 0, 0, 10));

        TextView isoTitle = label("ISO", 12, MUTED, true);
        loadedFields.addView(isoTitle, margin(lp(-1, -2), 0, 0, 0, 7));
        LinearLayout isoRow = new LinearLayout(this);
        isoRow.setOrientation(LinearLayout.HORIZONTAL);
        final int[] selectedIso = {side.iso};
        List<TextView> isoButtons = new ArrayList<>();
        for (int isoValue : ISO_VALUES) {
            TextView b = choiceButton(String.valueOf(isoValue));
            b.setTag(isoValue);
            isoButtons.add(b);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(50), 1f);
            if (isoValue != ISO_VALUES[0]) p.setMargins(dp(7), 0, 0, 0);
            isoRow.addView(b, p);
        }
        loadedFields.addView(isoRow, margin(lp(-1, dp(50)), 0, 0, 0, 17));

        LinearLayout exposureFields = new LinearLayout(this);
        exposureFields.setOrientation(LinearLayout.VERTICAL);
        TextView exposureTitle = sectionTitle("DATI DI SCATTO");
        exposureFields.addView(exposureTitle, margin(lp(-1, -2), 0, 0, 0, 8));

        EditText shutter = field("Tempo", side.shutter, InputType.TYPE_CLASS_TEXT);
        EditText aperture = field("Diaframma", side.aperture, InputType.TYPE_CLASS_TEXT);
        exposureFields.addView(shutter, margin(lp(-1, dp(54)), 0, 0, 0, 10));
        exposureFields.addView(aperture, margin(lp(-1, dp(54)), 0, 0, 0, 16));

        TextView zonesTitle = sectionTitle("ZONE ANSEL ADAMS");
        exposureFields.addView(zonesTitle, margin(lp(-1, -2), 0, 0, 0, 8));

        final int[] selectedShadow = {side.shadowZone};
        final int[] selectedHighlight = {side.highlightZone};
        TextView shadowLabel = label("OMBRA", 12, MUTED, true);
        exposureFields.addView(shadowLabel, margin(lp(-1, -2), 0, 0, 0, 6));
        List<TextView> shadowButtons = new ArrayList<>();
        exposureFields.addView(zoneSelector(selectedShadow, shadowButtons), lp(-1, dp(52)));

        TextView highlightLabel = label("LUCE", 12, MUTED, true);
        exposureFields.addView(highlightLabel, margin(lp(-1, -2), 0, 12, 0, 6));
        List<TextView> highlightButtons = new ArrayList<>();
        exposureFields.addView(zoneSelector(selectedHighlight, highlightButtons), lp(-1, dp(52)));

        TextView gap = label("SCARTO: —", 16, IVORY, true);
        gap.setGravity(Gravity.CENTER);
        gap.setBackground(statusBackground(STATUS_EXPOSED, true));
        exposureFields.addView(gap, margin(lp(-1, dp(48)), 0, 13, 0, 17));

        TextView dateTitle = sectionTitle("DATA E ORA");
        exposureFields.addView(dateTitle, margin(lp(-1, -2), 0, 0, 0, 8));
        EditText shotAt = field("Data e ora scatto", side.shotAt, InputType.TYPE_CLASS_TEXT);
        LinearLayout dateRow = new LinearLayout(this);
        dateRow.setOrientation(LinearLayout.HORIZONTAL);
        dateRow.setGravity(Gravity.CENTER_VERTICAL);
        dateRow.addView(shotAt, new LinearLayout.LayoutParams(0, dp(56), 1f));
        TextView now = action("ADESSO", false);
        LinearLayout.LayoutParams nowLp = new LinearLayout.LayoutParams(dp(104), dp(56));
        nowLp.setMargins(dp(9), 0, 0, 0);
        dateRow.addView(now, nowLp);
        exposureFields.addView(dateRow, lp(-1, dp(56)));

        // Dedicated spacing fixes the previous overlap under the ADESSO button.
        View dateSpacer = new View(this);
        exposureFields.addView(dateSpacer, lp(-1, dp(15)));
        TextView exposedNote = label("Tempo, diaframma, zone e data restano associati solo al foglio esposto.", 12, MUTED, false);
        exposedNote.setLineSpacing(0f, 1.15f);
        exposureFields.addView(exposedNote, margin(lp(-1, -2), 0, 0, 0, 10));
        body.addView(loadedFields, lp(-1, -2));
        body.addView(exposureFields, lp(-1, -2));

        Runnable refreshIso = () -> {
            for (TextView b : isoButtons) {
                int value = (Integer) b.getTag();
                paintChoiceButton(b, value == selectedIso[0], STATUS_UNEXPOSED);
            }
        };
        for (TextView b : isoButtons) {
            b.setOnClickListener(v -> {
                selectedIso[0] = (Integer) v.getTag();
                refreshIso.run();
            });
        }

        Runnable refreshGap = () -> {
            paintZoneButtons(shadowButtons, selectedShadow[0]);
            paintZoneButtons(highlightButtons, selectedHighlight[0]);
            if (selectedShadow[0] >= 0 && selectedHighlight[0] >= 0) {
                int delta = Math.abs(selectedHighlight[0] - selectedShadow[0]);
                gap.setText("SCARTO: " + delta + " EV");
            } else {
                gap.setText("SCARTO: —");
            }
        };
        for (TextView b : shadowButtons) {
            b.setOnClickListener(v -> {
                selectedShadow[0] = (Integer) v.getTag();
                refreshGap.run();
            });
        }
        for (TextView b : highlightButtons) {
            b.setOnClickListener(v -> {
                selectedHighlight[0] = (Integer) v.getTag();
                refreshGap.run();
            });
        }

        Runnable refreshStatus = () -> {
            paintStatusButton(empty, STATUS_EMPTY.equals(selectedStatus[0]), STATUS_EMPTY);
            paintStatusButton(unexposed, STATUS_UNEXPOSED.equals(selectedStatus[0]), STATUS_UNEXPOSED);
            paintStatusButton(exposed, STATUS_EXPOSED.equals(selectedStatus[0]), STATUS_EXPOSED);
            loadedFields.setVisibility(STATUS_EMPTY.equals(selectedStatus[0]) ? View.GONE : View.VISIBLE);
            exposureFields.setVisibility(STATUS_EXPOSED.equals(selectedStatus[0]) ? View.VISIBLE : View.GONE);
        };
        empty.setOnClickListener(v -> { selectedStatus[0] = STATUS_EMPTY; refreshStatus.run(); });
        unexposed.setOnClickListener(v -> { selectedStatus[0] = STATUS_UNEXPOSED; refreshStatus.run(); });
        exposed.setOnClickListener(v -> { selectedStatus[0] = STATUS_EXPOSED; refreshStatus.run(); });
        now.setOnClickListener(v -> shotAt.setText(now()));

        refreshIso.run();
        refreshGap.run();
        refreshStatus.run();

        TextView saveButton = action("SALVA", true);
        saveButton.setOnClickListener(v -> {
            String newStatus = selectedStatus[0];
            if (!STATUS_EMPTY.equals(newStatus) && selectedIso[0] <= 0) {
                message("ISO da scegliere", "Seleziona l'ISO della Fomapan caricata nel lato " + sideName + ".");
                return;
            }
            side.status = newStatus;
            if (STATUS_EMPTY.equals(newStatus)) {
                side.clearAll();
            } else if (STATUS_UNEXPOSED.equals(newStatus)) {
                side.iso = selectedIso[0];
                side.clearExposure();
            } else {
                side.iso = selectedIso[0];
                side.shutter = value(shutter);
                side.aperture = value(aperture);
                side.shadowZone = selectedShadow[0];
                side.highlightZone = selectedHighlight[0];
                side.shotAt = value(shotAt);
                if (side.shotAt.isEmpty()) side.shotAt = now();
            }
            save();
            showList();
        });
        body.addView(saveButton, margin(lp(-1, dp(54)), 0, 16, 0, 9));

        TextView cancel = action("ANNULLA", false);
        cancel.setOnClickListener(v -> showList());
        body.addView(cancel, margin(lp(-1, dp(50)), 0, 0, 0, 9));

        TextView delete = action("ELIMINA CHASSIS", false);
        delete.setTextColor(Color.rgb(197, 126, 109));
        delete.setOnClickListener(v -> new AlertDialog.Builder(this)
                .setTitle("Eliminare chassis " + chassisItem.number + "?")
                .setMessage("Verranno cancellati entrambi i lati " + chassisItem.number + "A e " + chassisItem.number + "B.")
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("ELIMINA", (d, w) -> {
                    chassis.remove(chassisItem);
                    save();
                    showList();
                }).show());
        body.addView(delete, lp(-1, dp(50)));
    }

    private HorizontalScrollView zoneSelector(int[] selected, List<TextView> buttons) {
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(0, 0, dp(2), 0);
        for (int zone = 0; zone <= 10; zone++) {
            TextView b = choiceButton(ROMAN[zone]);
            b.setTag(zone);
            buttons.add(b);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(dp(54), dp(48));
            if (zone > 0) p.setMargins(dp(6), 0, 0, 0);
            row.addView(b, p);
        }
        scroll.addView(row, new HorizontalScrollView.LayoutParams(-2, -1));
        return scroll;
    }

    private void paintZoneButtons(List<TextView> buttons, int selectedZone) {
        for (TextView b : buttons) {
            int zone = (Integer) b.getTag();
            paintChoiceButton(b, zone == selectedZone, STATUS_EXPOSED);
        }
    }

    private TextView statusButton(String text, String status) {
        TextView v = label(text, 12, IVORY, true);
        v.setGravity(Gravity.CENTER);
        v.setMaxLines(2);
        v.setTag(status);
        return v;
    }

    private void paintStatusButton(TextView v, boolean active, String status) {
        v.setBackground(statusBackground(status, active));
        v.setAlpha(active ? 1f : 0.67f);
    }

    private GradientDrawable statusBackground(String status, boolean active) {
        GradientDrawable g = new GradientDrawable();
        int color = statusColor(status);
        if (active) g.setColor(color);
        else g.setColor(mixWithCard(color));
        g.setCornerRadius(dp(10));
        g.setStroke(dp(active ? 2 : 1), active ? IVORY : BORDER);
        return g;
    }

    private int mixWithCard(int color) {
        int r = (Color.red(color) + Color.red(CARD) * 2) / 3;
        int g = (Color.green(color) + Color.green(CARD) * 2) / 3;
        int b = (Color.blue(color) + Color.blue(CARD) * 2) / 3;
        return Color.rgb(r, g, b);
    }

    private int statusColor(String status) {
        if (STATUS_EXPOSED.equals(status)) return EXPOSED_COLOR;
        if (STATUS_UNEXPOSED.equals(status)) return VIRGIN_COLOR;
        return EMPTY_COLOR;
    }

    private TextView choiceButton(String text) {
        TextView v = label(text, 14, IVORY, true);
        v.setGravity(Gravity.CENTER);
        return v;
    }

    private void paintChoiceButton(TextView v, boolean active, String paletteStatus) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(active ? statusColor(paletteStatus) : CARD);
        g.setCornerRadius(dp(9));
        g.setStroke(dp(active ? 2 : 1), active ? IVORY : BORDER);
        v.setBackground(g);
    }

    private EditText field(String hint, String value, int type) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setHintTextColor(Color.rgb(118, 110, 101));
        e.setText(value == null ? "" : value);
        e.setTextColor(IVORY);
        e.setTextSize(15);
        e.setSingleLine(true);
        e.setInputType(type);
        e.setPadding(dp(12), 0, dp(12), 0);
        e.setBackground(inputBg());
        return e;
    }

    private GradientDrawable inputBg() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(CARD);
        g.setCornerRadius(dp(9));
        g.setStroke(dp(1), BORDER);
        return g;
    }

    private TextView sectionTitle(String text) {
        TextView v = label(text, 12, MUTED, true);
        v.setLetterSpacing(0.08f);
        return v;
    }

    private TextView action(String text, boolean primary) {
        TextView v = label(text, 14, IVORY, true);
        v.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setColor(primary ? Color.rgb(91, 70, 52) : CARD);
        g.setCornerRadius(dp(10));
        g.setStroke(dp(1), BORDER);
        v.setBackground(g);
        return v;
    }

    private GradientDrawable cardBg() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(CARD);
        g.setCornerRadius(dp(12));
        g.setStroke(dp(1), BORDER);
        return g;
    }

    private TextView label(String text, float sp, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setTypeface(Typeface.create(Typeface.SERIF, bold ? Typeface.BOLD : Typeface.NORMAL));
        v.setIncludeFontPadding(false);
        return v;
    }

    private String statusLabel(String status) {
        if (STATUS_EXPOSED.equals(status)) return "PIENO · ESPOSTO";
        if (STATUS_UNEXPOSED.equals(status)) return "PIENO · VERGINE";
        return "VUOTO";
    }

    private String normaliseStatus(String status) {
        if (STATUS_EXPOSED.equals(status) || STATUS_UNEXPOSED.equals(status)) return status;
        return STATUS_EMPTY;
    }

    private int zoneGap(Side side) {
        if (side.shadowZone < 0 || side.highlightZone < 0) return -1;
        return Math.abs(side.highlightZone - side.shadowZone);
    }

    private int nextNumber() {
        int max = 0;
        for (Chassis item : chassis) max = Math.max(max, item.number);
        return max + 1;
    }

    private String now() {
        return new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.ITALY).format(new Date());
    }

    private String value(EditText e) {
        return e.getText().toString().trim();
    }

    private String join(List<String> values, String separator) {
        StringBuilder out = new StringBuilder();
        for (String value : values) {
            if (out.length() > 0) out.append(separator);
            out.append(value);
        }
        return out.toString();
    }

    private void message(String title, String text) {
        new AlertDialog.Builder(this).setTitle(title).setMessage(text).setPositiveButton("OK", null).show();
    }

    private void load() {
        chassis.clear();
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        String v2 = prefs.getString(KEY_DATA_V2, "");
        if (v2 != null && !v2.trim().isEmpty()) {
            if (readV2(v2)) return;
        }
        // One-time compatibility with the first v0.4.9 model: old chassis data becomes side A,
        // while side B starts empty. No old exposure is silently discarded.
        String v1 = prefs.getString(KEY_DATA_V1, "[]");
        try {
            JSONArray array = new JSONArray(v1 == null ? "[]" : v1);
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o == null) continue;
                Chassis c = new Chassis(o.optInt("number", i + 1));
                c.a.status = normaliseStatus(o.optString("status", STATUS_EMPTY));
                c.a.iso = parseInt(o.optString("iso", ""), 0);
                if (STATUS_EXPOSED.equals(c.a.status)) {
                    c.a.shutter = o.optString("shutter", "");
                    c.a.aperture = o.optString("aperture", "");
                    c.a.shotAt = o.optString("shotAt", "");
                } else if (STATUS_EMPTY.equals(c.a.status)) {
                    c.a.clearAll();
                }
                chassis.add(c);
            }
            save();
        } catch (Exception ignored) {
            chassis.clear();
        }
    }

    private boolean readV2(String raw) {
        try {
            JSONArray array = new JSONArray(raw);
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o == null) continue;
                Chassis c = new Chassis(o.optInt("number", i + 1));
                readSide(o.optJSONObject("a"), c.a);
                readSide(o.optJSONObject("b"), c.b);
                chassis.add(c);
            }
            return true;
        } catch (Exception ignored) {
            chassis.clear();
            return false;
        }
    }

    private void readSide(JSONObject o, Side side) {
        if (o == null) return;
        side.status = normaliseStatus(o.optString("status", STATUS_EMPTY));
        side.iso = o.optInt("iso", 0);
        side.shutter = o.optString("shutter", "");
        side.aperture = o.optString("aperture", "");
        side.shadowZone = o.optInt("shadowZone", -1);
        side.highlightZone = o.optInt("highlightZone", -1);
        side.shotAt = o.optString("shotAt", "");
        if (STATUS_EMPTY.equals(side.status)) side.clearAll();
        else if (STATUS_UNEXPOSED.equals(side.status)) side.clearExposure();
    }

    private int parseInt(String value, int fallback) {
        try { return Integer.parseInt(value.trim()); }
        catch (Exception ignored) { return fallback; }
    }

    private void save() {
        Collections.sort(chassis, Comparator.comparingInt((Chassis a) -> a.number));
        JSONArray array = new JSONArray();
        try {
            for (Chassis item : chassis) {
                JSONObject o = new JSONObject();
                o.put("number", item.number);
                o.put("a", sideJson(item.a));
                o.put("b", sideJson(item.b));
                array.put(o);
            }
        } catch (Exception e) {
            message("Errore", "Non è stato possibile preparare il registro chassis.");
            return;
        }
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(KEY_DATA_V2, array.toString()).apply();
    }

    private JSONObject sideJson(Side side) throws Exception {
        JSONObject o = new JSONObject();
        o.put("status", side.status);
        o.put("iso", side.iso);
        o.put("shutter", side.shutter);
        o.put("aperture", side.aperture);
        o.put("shadowZone", side.shadowZone);
        o.put("highlightZone", side.highlightZone);
        o.put("zoneGapEv", zoneGap(side));
        o.put("shotAt", side.shotAt);
        return o;
    }

    private LinearLayout.LayoutParams lp(int w, int h) {
        return new LinearLayout.LayoutParams(w, h);
    }

    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(dp(l), dp(t), dp(r), dp(b));
        return p;
    }

    private LinearLayout.LayoutParams weightLp() {
        return new LinearLayout.LayoutParams(0, -1, 1f);
    }

    private LinearLayout.LayoutParams weightMarginLp() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -1, 1f);
        p.setMargins(dp(6), 0, 0, 0);
        return p;
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static final class Chassis {
        int number;
        final Side a = new Side();
        final Side b = new Side();
        Chassis(int number) { this.number = number; }
    }

    private static final class Side {
        String status = STATUS_EMPTY;
        int iso = 0;
        String shutter = "";
        String aperture = "";
        int shadowZone = -1;
        int highlightZone = -1;
        String shotAt = "";

        void clearExposure() {
            shutter = "";
            aperture = "";
            shadowZone = -1;
            highlightZone = -1;
            shotAt = "";
        }

        void clearAll() {
            status = STATUS_EMPTY;
            iso = 0;
            clearExposure();
        }
    }
}
'''
TARGET.write_text(large_format_source, encoding="utf-8")


# Guards for every agreed requirement.
hs = HOME.read_text(encoding="utf-8")
ls = TARGET.read_text(encoding="utf-8")
if 'new HomeCard("GRANDE FORMATO", ICON_CHASSIS, false)' not in hs:
    raise SystemExit("v0.5.0 Home label guard failed")
if "SCATTO GRANDE FORMATO" in hs:
    raise SystemExit("v0.5.0 old long Home label survived")
for marker in [
    'final Side a = new Side()', 'final Side b = new Side()',
    'chassisItem.number + "A"', 'chassisItem.number + "B"',
    'FILM_BRAND = "FOMAPAN"', 'ISO_VALUES = {100, 200, 400}',
    'EMPTY_COLOR = Color.rgb(108, 105, 98)',
    'VIRGIN_COLOR = Color.rgb(109, 124, 94)',
    'EXPOSED_COLOR = Color.rgb(151, 103, 66)',
    'ZONE ANSEL ADAMS', 'OMBRA', 'LUCE', 'Math.abs(selectedHighlight[0] - selectedShadow[0])',
    'SCARTO: ', 'zoneGapEv', 'KEY_DATA_V2 = "chassis_json_v2"',
    'Dedicated spacing fixes the previous overlap under the ADESSO button.',
    'c.a.status = normaliseStatus(o.optString("status", STATUS_EMPTY))'
]:
    if marker not in ls:
        raise SystemExit("v0.5.0 large-format guard failed: " + marker)
for forbidden in ["Obiettivo", "Filtro", "Soffietto", 'field("Pellicola"']:
    if forbidden in ls:
        raise SystemExit("v0.5.0 unwanted field survived: " + forbidden)
print("Darkroom v0.5.0 large-format A/B sides patch ready")
