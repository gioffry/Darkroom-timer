#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
HOME = ROOT / "home/HomeActivity.java"
MANIFEST = Path("combined/src/main/AndroidManifest.xml")
TARGET = ROOT / "largeformat/LargeFormatActivity.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.4.9 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


if not HOME.exists() or not MANIFEST.exists():
    raise SystemExit("v0.4.9 generated Home/Manifest missing")

TARGET.parent.mkdir(parents=True, exist_ok=True)
large_format_source = r"""package it.darkroom.timer.largeformat;

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

/** Registro essenziale degli chassis 4x5 e dei fogli esposti. */
public final class LargeFormatActivity extends Activity {
    private static final int BG = Color.rgb(5, 6, 7);
    private static final int CARD = Color.rgb(18, 19, 20);
    private static final int IVORY = Color.rgb(235, 210, 174);
    private static final int MUTED = Color.rgb(164, 151, 133);
    private static final int BORDER = Color.rgb(164, 139, 105);
    private static final int ACTIVE = Color.rgb(77, 65, 49);

    private static final String PREFS = "large_format_chassis";
    private static final String KEY_DATA = "chassis_json_v1";
    private static final String STATUS_EMPTY = "EMPTY";
    private static final String STATUS_UNEXPOSED = "UNEXPOSED";
    private static final String STATUS_EXPOSED = "EXPOSED";

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

        TextView title = label("SCATTO GRANDE FORMATO", 27, IVORY, true);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        title.setLetterSpacing(0.035f);
        root.addView(title, lp(-1, -2));

        TextView sub = label("CHASSIS 4×5 · REGISTRO FOGLI", 12, MUTED, true);
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

        TextView intro = label("Numera gli chassis e aggiorna il loro stato. I dati di scatto compaiono solo per i fogli esposti e restano pronti per lo sviluppo.", 14, MUTED, false);
        intro.setLineSpacing(0f, 1.15f);
        body.addView(intro, margin(lp(-1, -2), 0, 0, 0, 14));

        TextView add = action("+  NUOVO CHASSIS", true);
        add.setOnClickListener(v -> showEditor(new Chassis(nextNumber()), true));
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
            card.setPadding(dp(16), dp(13), dp(16), dp(13));
            card.setBackground(cardBg());
            card.setClickable(true);
            card.setFocusable(true);

            TextView name = label("CHASSIS " + item.number, 19, IVORY, true);
            card.addView(name, lp(-1, -2));

            TextView state = label(statusLabel(item.status), 13, stateColor(item.status), true);
            card.addView(state, margin(lp(-1, -2), 0, 4, 0, 0));

            if (STATUS_EXPOSED.equals(item.status)) {
                TextView summary = label(exposureSummary(item), 13, MUTED, false);
                summary.setLineSpacing(0f, 1.12f);
                card.addView(summary, margin(lp(-1, -2), 0, 8, 0, 0));
            }

            card.setOnClickListener(v -> showEditor(item, false));
            body.addView(card, margin(lp(-1, -2), 0, 0, 0, 11));
        }
    }

    private void showEditor(Chassis item, boolean isNew) {
        body.removeAllViews();

        TextView heading = label(isNew ? "NUOVO CHASSIS" : "CHASSIS " + item.number, 21, IVORY, true);
        body.addView(heading, margin(lp(-1, -2), 0, 0, 0, 14));

        EditText number = field("Numero chassis", String.valueOf(item.number), InputType.TYPE_CLASS_NUMBER);
        body.addView(number, margin(lp(-1, dp(54)), 0, 0, 0, 14));

        TextView stateTitle = label("STATO", 12, MUTED, true);
        stateTitle.setLetterSpacing(0.08f);
        body.addView(stateTitle, margin(lp(-1, -2), 0, 0, 0, 8));

        LinearLayout stateRow = new LinearLayout(this);
        stateRow.setOrientation(LinearLayout.HORIZONTAL);
        final String[] selected = {normaliseStatus(item.status)};
        TextView empty = statusButton("VUOTO", STATUS_EMPTY, selected);
        TextView unexposed = statusButton("PIENO\nVERGINE", STATUS_UNEXPOSED, selected);
        TextView exposed = statusButton("PIENO\nESPOSTO", STATUS_EXPOSED, selected);
        stateRow.addView(empty, weightLp());
        stateRow.addView(unexposed, weightMarginLp());
        stateRow.addView(exposed, weightMarginLp());
        body.addView(stateRow, margin(lp(-1, dp(62)), 0, 0, 0, 16));

        LinearLayout exposedFields = new LinearLayout(this);
        exposedFields.setOrientation(LinearLayout.VERTICAL);

        EditText film = field("Pellicola", item.film, InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        EditText iso = field("ISO", item.iso, InputType.TYPE_CLASS_NUMBER);
        EditText shutter = field("Tempo", item.shutter, InputType.TYPE_CLASS_TEXT);
        EditText aperture = field("Diaframma", item.aperture, InputType.TYPE_CLASS_TEXT);
        EditText zones = field("Zone Ansel Adams · es. ombre III / luci VIII", item.zones, InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        EditText shotAt = field("Data e ora scatto", item.shotAt, InputType.TYPE_CLASS_TEXT);

        exposedFields.addView(film, margin(lp(-1, dp(54)), 0, 0, 0, 10));
        exposedFields.addView(iso, margin(lp(-1, dp(54)), 0, 0, 0, 10));
        exposedFields.addView(shutter, margin(lp(-1, dp(54)), 0, 0, 0, 10));
        exposedFields.addView(aperture, margin(lp(-1, dp(54)), 0, 0, 0, 10));
        exposedFields.addView(zones, margin(lp(-1, dp(58)), 0, 0, 0, 10));

        LinearLayout dateRow = new LinearLayout(this);
        dateRow.setOrientation(LinearLayout.HORIZONTAL);
        dateRow.addView(shotAt, new LinearLayout.LayoutParams(0, dp(54), 1f));
        TextView now = action("ADESSO", false);
        LinearLayout.LayoutParams nowLp = new LinearLayout.LayoutParams(dp(92), dp(54));
        nowLp.setMargins(dp(8), 0, 0, 0);
        dateRow.addView(now, nowLp);
        now.setOnClickListener(v -> shotAt.setText(now()));
        exposedFields.addView(dateRow, margin(lp(-1, dp(54)), 0, 0, 0, 8));

        TextView exposedNote = label("Questi dati restano associati al foglio finché lo chassis non viene riportato a VUOTO o PIENO VERGINE.", 12, MUTED, false);
        exposedFields.addView(exposedNote, margin(lp(-1, -2), 0, 0, 0, 8));
        body.addView(exposedFields, lp(-1, -2));

        Runnable refreshState = () -> {
            paintStatusButton(empty, STATUS_EMPTY.equals(selected[0]));
            paintStatusButton(unexposed, STATUS_UNEXPOSED.equals(selected[0]));
            paintStatusButton(exposed, STATUS_EXPOSED.equals(selected[0]));
            exposedFields.setVisibility(STATUS_EXPOSED.equals(selected[0]) ? View.VISIBLE : View.GONE);
        };
        empty.setOnClickListener(v -> { selected[0] = STATUS_EMPTY; refreshState.run(); });
        unexposed.setOnClickListener(v -> { selected[0] = STATUS_UNEXPOSED; refreshState.run(); });
        exposed.setOnClickListener(v -> { selected[0] = STATUS_EXPOSED; refreshState.run(); });
        refreshState.run();

        TextView save = action("SALVA", true);
        save.setOnClickListener(v -> {
            int parsed;
            try { parsed = Integer.parseInt(number.getText().toString().trim()); }
            catch (Exception e) { message("Numero non valido", "Inserisci un numero intero positivo per lo chassis."); return; }
            if (parsed <= 0) { message("Numero non valido", "Il numero dello chassis deve essere maggiore di zero."); return; }
            for (Chassis other : chassis) {
                if (other != item && other.number == parsed) {
                    message("Numero già usato", "Esiste già lo chassis " + parsed + ".");
                    return;
                }
            }

            item.number = parsed;
            item.status = selected[0];
            if (STATUS_EXPOSED.equals(item.status)) {
                item.film = value(film);
                item.iso = value(iso);
                item.shutter = value(shutter);
                item.aperture = value(aperture);
                item.zones = value(zones);
                item.shotAt = value(shotAt);
                if (item.shotAt.isEmpty()) item.shotAt = now();
            } else {
                item.clearExposure();
            }
            if (isNew) chassis.add(item);
            save();
            showList();
        });
        body.addView(save, margin(lp(-1, dp(54)), 0, 16, 0, 9));

        TextView cancel = action("ANNULLA", false);
        cancel.setOnClickListener(v -> showList());
        body.addView(cancel, margin(lp(-1, dp(50)), 0, 0, 0, 9));

        if (!isNew) {
            TextView delete = action("ELIMINA CHASSIS", false);
            delete.setTextColor(Color.rgb(208, 126, 113));
            delete.setOnClickListener(v -> new AlertDialog.Builder(this)
                    .setTitle("Eliminare chassis " + item.number + "?")
                    .setMessage("Verranno cancellati anche gli eventuali dati del foglio registrato.")
                    .setNegativeButton("ANNULLA", null)
                    .setPositiveButton("ELIMINA", (d, w) -> {
                        chassis.remove(item);
                        save();
                        showList();
                    }).show());
            body.addView(delete, lp(-1, dp(50)));
        }
    }

    private TextView statusButton(String label, String status, String[] selected) {
        TextView v = label(label, 12, IVORY, true);
        v.setGravity(Gravity.CENTER);
        v.setMaxLines(2);
        v.setTag(status);
        return v;
    }

    private void paintStatusButton(TextView v, boolean active) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(active ? ACTIVE : CARD);
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
        GradientDrawable g = new GradientDrawable();
        g.setColor(CARD);
        g.setCornerRadius(dp(9));
        g.setStroke(dp(1), BORDER);
        e.setBackground(g);
        return e;
    }

    private TextView action(String text, boolean primary) {
        TextView v = label(text, 14, IVORY, true);
        v.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setColor(primary ? ACTIVE : CARD);
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

    private String exposureSummary(Chassis item) {
        List<String> first = new ArrayList<>();
        if (!item.film.isEmpty()) first.add(item.film);
        if (!item.iso.isEmpty()) first.add("ISO " + item.iso);
        if (!item.shutter.isEmpty()) first.add(item.shutter);
        if (!item.aperture.isEmpty()) first.add(item.aperture);
        StringBuilder out = new StringBuilder(join(first, " · "));
        if (!item.zones.isEmpty()) appendLine(out, "Zone: " + item.zones);
        if (!item.shotAt.isEmpty()) appendLine(out, item.shotAt);
        return out.length() == 0 ? "Dati di scatto da completare" : out.toString();
    }

    private void appendLine(StringBuilder out, String value) {
        if (out.length() > 0) out.append('\n');
        out.append(value);
    }

    private String join(List<String> values, String separator) {
        StringBuilder out = new StringBuilder();
        for (String value : values) {
            if (out.length() > 0) out.append(separator);
            out.append(value);
        }
        return out.toString();
    }

    private int stateColor(String status) {
        if (STATUS_EXPOSED.equals(status)) return Color.rgb(224, 173, 111);
        if (STATUS_UNEXPOSED.equals(status)) return Color.rgb(186, 206, 159);
        return MUTED;
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

    private void message(String title, String text) {
        new AlertDialog.Builder(this).setTitle(title).setMessage(text).setPositiveButton("OK", null).show();
    }

    private void load() {
        chassis.clear();
        String raw = getSharedPreferences(PREFS, MODE_PRIVATE).getString(KEY_DATA, "[]");
        try {
            JSONArray array = new JSONArray(raw == null ? "[]" : raw);
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.optJSONObject(i);
                if (o == null) continue;
                Chassis item = new Chassis(o.optInt("number", i + 1));
                item.status = normaliseStatus(o.optString("status", STATUS_EMPTY));
                item.film = o.optString("film", "");
                item.iso = o.optString("iso", "");
                item.shutter = o.optString("shutter", "");
                item.aperture = o.optString("aperture", "");
                item.zones = o.optString("zones", "");
                item.shotAt = o.optString("shotAt", "");
                if (!STATUS_EXPOSED.equals(item.status)) item.clearExposure();
                chassis.add(item);
            }
        } catch (Exception ignored) {
            chassis.clear();
        }
    }

    private void save() {
        Collections.sort(chassis, Comparator.comparingInt((Chassis a) -> a.number));
        JSONArray array = new JSONArray();
        try {
            for (Chassis item : chassis) {
                JSONObject o = new JSONObject();
                o.put("number", item.number);
                o.put("status", item.status);
                o.put("film", item.film);
                o.put("iso", item.iso);
                o.put("shutter", item.shutter);
                o.put("aperture", item.aperture);
                o.put("zones", item.zones);
                o.put("shotAt", item.shotAt);
                array.put(o);
            }
        } catch (Exception e) {
            message("Errore", "Non è stato possibile preparare il registro chassis.");
            return;
        }
        SharedPreferences.Editor editor = getSharedPreferences(PREFS, MODE_PRIVATE).edit();
        editor.putString(KEY_DATA, array.toString()).apply();
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
        String status = STATUS_EMPTY;
        String film = "";
        String iso = "";
        String shutter = "";
        String aperture = "";
        String zones = "";
        String shotAt = "";

        Chassis(int number) { this.number = number; }

        void clearExposure() {
            film = "";
            iso = "";
            shutter = "";
            aperture = "";
            zones = "";
            shotAt = "";
        }
    }
}
"""
TARGET.write_text(large_format_source, encoding="utf-8")


home = HOME.read_text(encoding="utf-8")
home = replace_once(
    home,
    "import it.darkroom.timer.maintenance.UseMaintenanceActivity;\n",
    "import it.darkroom.timer.maintenance.UseMaintenanceActivity;\nimport it.darkroom.timer.largeformat.LargeFormatActivity;\n",
    "Home large-format import",
)
home = replace_once(
    home,
    "    private static final int ICON_WRENCH = 5;\n",
    "    private static final int ICON_WRENCH = 5;\n    private static final int ICON_CHASSIS = 6;\n",
    "Home chassis icon constant",
)
home = replace_once(
    home,
    '''        HomeCard film = new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false);\n        film.setOnClickListener(v -> openAssistant("film"));\n        root.addView(film, margin(lp(-1, dp(88)), 0, 0, 0, 12));\n\n        HomeCard paper = new HomeCard("BAGNI STAMPA", ICON_TRAY, false);''',
    '''        HomeCard film = new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false);\n        film.setOnClickListener(v -> openAssistant("film"));\n        root.addView(film, margin(lp(-1, dp(88)), 0, 0, 0, 12));\n\n        HomeCard largeFormat = new HomeCard("SCATTO GRANDE FORMATO", ICON_CHASSIS, false);\n        largeFormat.setOnClickListener(v -> startActivity(new Intent(this, LargeFormatActivity.class)));\n        root.addView(largeFormat, margin(lp(-1, dp(88)), 0, 0, 0, 12));\n\n        HomeCard paper = new HomeCard("BAGNI STAMPA", ICON_TRAY, false);''',
    "Home large-format card",
)
home = replace_once(
    home,
    '            float nameSize = secondary ? 15f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f);\n',
    '            float nameSize = secondary ? 15f : ("SCATTO GRANDE FORMATO".equals(text) ? 16f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f));\n',
    "Home large-format label fit",
)
home = replace_once(
    home,
    '''            } else {\n                path.moveTo(cx-s*.23f,cy+s*.20f);path.lineTo(cx-s*.03f,cy);path.cubicTo(cx-s*.10f,cy-s*.19f,cx+s*.05f,cy-s*.30f,cx+s*.20f,cy-s*.23f);''',
    '''            } else if(kind==ICON_CHASSIS){\n                RectF outer=new RectF(cx-s*.24f,cy-s*.27f,cx+s*.24f,cy+s*.27f);c.drawRoundRect(outer,s*.03f,s*.03f,p);\n                RectF inner=new RectF(cx-s*.16f,cy-s*.18f,cx+s*.16f,cy+s*.18f);c.drawRect(inner,p);\n                c.drawLine(cx-s*.08f,cy-s*.31f,cx+s*.08f,cy-s*.31f,p);c.drawLine(cx,cy-s*.31f,cx,cy-s*.27f,p);\n            } else {\n                path.moveTo(cx-s*.23f,cy+s*.20f);path.lineTo(cx-s*.03f,cy);path.cubicTo(cx-s*.10f,cy-s*.19f,cx+s*.05f,cy-s*.30f,cx+s*.20f,cy-s*.23f);''',
    "Home chassis icon drawing",
)
HOME.write_text(home, encoding="utf-8")


manifest = MANIFEST.read_text(encoding="utf-8")
manifest = replace_once(
    manifest,
    "    </application>",
    '        <activity android:name="it.darkroom.timer.largeformat.LargeFormatActivity" android:screenOrientation="portrait" />\n    </application>',
    "large-format manifest activity",
)
MANIFEST.write_text(manifest, encoding="utf-8")


# Fail loudly if any requested part did not make it into the generated sources.
hs = HOME.read_text(encoding="utf-8")
ls = TARGET.read_text(encoding="utf-8")
ms = MANIFEST.read_text(encoding="utf-8")
for marker in [
    "SCATTO GRANDE FORMATO", "ICON_CHASSIS", "LargeFormatActivity.class",
    "Lpl7451Migration.run(this)"
]:
    if marker not in hs:
        raise SystemExit("v0.4.9 Home guard failed: " + marker)
for marker in [
    'STATUS_EMPTY = "EMPTY"', 'STATUS_UNEXPOSED = "UNEXPOSED"', 'STATUS_EXPOSED = "EXPOSED"',
    '"Pellicola"', '"ISO"', '"Tempo"', '"Diaframma"', '"Zone Ansel Adams', '"Data e ora scatto"',
    'SharedPreferences.Editor', 'chassis_json_v1', 'item.clearExposure()', 'new SimpleDateFormat("dd/MM/yyyy HH:mm"'
]:
    if marker not in ls:
        raise SystemExit("v0.4.9 large-format guard failed: " + marker)
for forbidden in ["Obiettivo", "Filtro", "Soffietto"]:
    if forbidden in ls:
        raise SystemExit("v0.4.9 unwanted field survived: " + forbidden)
if 'it.darkroom.timer.largeformat.LargeFormatActivity' not in ms:
    raise SystemExit("v0.4.9 manifest guard failed")

print("Darkroom v0.4.9 large-format chassis patch ready")
