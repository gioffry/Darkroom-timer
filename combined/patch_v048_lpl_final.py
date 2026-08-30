#!/usr/bin/env python3
from pathlib import Path
import math
import re
import shutil


ROOT = Path("combined/src/main/java/it/darkroom/timer")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.4.8 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# Keep the measured geometry in a small, testable source file shared by all formats.
geometry_asset = Path("combined/v048_assets/Lpl7451Geometry.java")
geometry_target = ROOT / "Lpl7451Geometry.java"
if not geometry_asset.exists():
    raise SystemExit("v0.4.8 geometry asset missing")
shutil.copyfile(geometry_asset, geometry_target)


enlargement_path = ROOT / "EnlargementActivity.java"
enlargement = enlargement_path.read_text(encoding="utf-8")
enlargement = replace_once(
    enlargement,
    "/** JOBO/LPL 7451 enlargement helper. Physical column calibration is intentionally deferred. */",
    "/** JOBO/LPL 7451 enlargement helper using the measured 67/73 cm column offset and a 6 mm easel. */",
    "enlargement documentation",
)
enlargement = replace_once(
    enlargement,
    "        double W, H, b1, b2, factor, stops, pw, ph;",
    "        double W, H, b1, b2, factor, stops, pw, ph, negativeToPaperCm, columnScale;",
    "pending geometry fields",
)
enlargement = replace_once(
    enlargement,
    '''    void addCalibrationNotice() {
        root.addView(section("CONFIGURAZIONE ATTIVA",
                "Ingranditore JOBO/LPL 7451. Il calcolo usa il rapporto d’ingrandimento β. "
                        + "La corrispondenza con la scala fisica della colonna verrà aggiunta solo dopo la misura dell’offset reale."));
    }''',
    '''    void addCalibrationNotice() {
        root.addView(section("CONFIGURAZIONE ATTIVA",
                "JOBO/LPL 7451 calibrato con misura meccanica: scala 67, piano negativo–base 73 cm, marginatore 6 mm. "
                        + "La distanza negativo–carta è scala + 5,4 cm; il valore calcolato è il punto iniziale per la messa a fuoco fine."));
    }''',
    "active calibration notice",
)
enlargement = replace_once(
    enlargement,
    "            x.pw = c.pw;\n            x.ph = c.ph;",
    "            x.pw = c.pw;\n            x.ph = c.ph;\n            x.negativeToPaperCm = c.negativeToPaperCm;\n            x.columnScale = c.columnScale;",
    "resize geometry assignment",
)
enlargement = replace_once(
    enlargement,
    '''                        "%s · obiettivo %d mm\\n%s\\nβ finale %.3f\\nImmagine proiettata %.1f × %.1f cm\\nCrop: %s\\nScala colonna: calibrazione fisica rinviata",
                        formatLabel(x.negativeCode), lensMm(x.negativeCode), carrierLabel(x.negativeCode),
                        x.b2, x.pw, x.ph, cropLabel(x.crop))))''',
    '''                        "%s · obiettivo %d mm\\n%s\\nβ finale %.3f\\nImmagine proiettata %.1f × %.1f cm\\nCrop: %s\\nDistanza negativo–carta %.1f cm\\nScala colonna LPL %.1f",
                        formatLabel(x.negativeCode), lensMm(x.negativeCode), carrierLabel(x.negativeCode),
                        x.b2, x.pw, x.ph, cropLabel(x.crop), x.negativeToPaperCm, x.columnScale)))''',
    "resize result",
)
enlargement = replace_once(
    enlargement,
    '''    static final class Calc {
        double beta, pw, ph;
        String crop;
    }''',
    '''    static final class Calc {
        double beta, pw, ph, negativeToPaperCm, columnScale;
        String crop;
    }''',
    "calculation geometry fields",
)
enlargement = replace_once(
    enlargement,
    '''        c.pw = beta * nw / 10.0;
        c.ph = beta * nh / 10.0;
        c.crop = (c.pw > W / 10.0 + .001 || c.ph > H / 10.0 + .001) ? "SI" : "NO";''',
    '''        c.pw = beta * nw / 10.0;
        c.ph = beta * nh / 10.0;
        c.negativeToPaperCm = Lpl7451Geometry.negativeToPaperCm(beta, lensMm(format));
        c.columnScale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        c.crop = (c.pw > W / 10.0 + .001 || c.ph > H / 10.0 + .001) ? "SI" : "NO";''',
    "calculation formula",
)
enlargement = replace_once(
    enlargement,
    '''        String base = String.format(Locale.US,
                "enlarger=LPL7451|neg=%s|negativeMm=%s|lens=%d|carrier=%s|paper=%.1fx%.1f|w=%.1f|h=%.1f|orientation=LANDSCAPE|fill=%d|beta=%.8f|proj=%.2fx%.2f|crop=%s|columnCalibration=PENDING",
                format, negativeSizeMeta(format), lensMm(format), carrierCode(format),
                W / 10.0, H / 10.0, W / 10.0, H / 10.0, fillIndex, beta, pw, ph, crop);''',
    '''        double negativeToPaperCm = Lpl7451Geometry.negativeToPaperCm(beta, lensMm(format));
        double columnScale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        String base = String.format(Locale.US,
                "enlarger=LPL7451|neg=%s|negativeMm=%s|lens=%d|carrier=%s|paper=%.1fx%.1f|w=%.1f|h=%.1f|orientation=LANDSCAPE|fill=%d|beta=%.8f|proj=%.2fx%.2f|crop=%s|columnCalibration=MEASURED_67_73_6MM|columnScale=%.2f|negativePaperCm=%.2f|scaleOffsetCm=5.40|easelHeightMm=6.0",
                format, negativeSizeMeta(format), lensMm(format), carrierCode(format),
                W / 10.0, H / 10.0, W / 10.0, H / 10.0, fillIndex, beta, pw, ph, crop,
                columnScale, negativeToPaperCm);''',
    "metadata calibration",
)
enlargement = replace_once(
    enlargement,
    '''        return String.format(Locale.ITALY,
                "%s · negativo %s\\nObiettivo automatico %d mm\\n%s\\nβ %.3f\\nImmagine proiettata %.1f × %.1f cm\\nCrop: %s\\nScala colonna: calibrazione fisica rinviata",
                formatLabel(format), negativeSizeLabel(format), lensMm(format), carrierLabel(format),
                c.beta, c.pw, c.ph, cropLabel(c.crop));''',
    '''        return String.format(Locale.ITALY,
                "%s · negativo %s\\nObiettivo automatico %d mm\\n%s\\nβ %.3f\\nImmagine proiettata %.1f × %.1f cm\\nCrop: %s\\nDistanza negativo–carta %.1f cm\\nScala colonna LPL %.1f",
                formatLabel(format), negativeSizeLabel(format), lensMm(format), carrierLabel(format),
                c.beta, c.pw, c.ph, cropLabel(c.crop), c.negativeToPaperCm, c.columnScale);''',
    "setup result",
)
enlargement = replace_once(
    enlargement,
    '''    String originSummary(String meta, String format) {
        return paperDisplay(meta) + " · " + formatLabel(format) + " / " + lensMm(format) + " mm"
                + "\\n" + carrierLabel(format)
                + String.format(Locale.ITALY, "\\nβ %.3f · scala fisica non calibrata", num(meta, "beta"));
    }''',
    '''    String originSummary(String meta, String format) {
        double beta = num(meta, "beta");
        double scale = num(meta, "columnScale");
        if (Double.isNaN(scale) && beta > 0.0) scale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        return paperDisplay(meta) + " · " + formatLabel(format) + " / " + lensMm(format) + " mm"
                + "\\n" + carrierLabel(format)
                + String.format(Locale.ITALY, "\\nβ %.3f · scala LPL %.1f", beta, scale);
    }''',
    "origin summary",
)
enlargement_path.write_text(enlargement, encoding="utf-8")


main_path = ROOT / "MainActivity.java"
main = main_path.read_text(encoding="utf-8")
main = replace_once(
    main,
    '        String beta = enlargementMetaValue(meta, "beta");\n        String carrier = enlargementMetaValue(meta, "carrier");',
    '        String beta = enlargementMetaValue(meta, "beta");\n        String columnScale = enlargementMetaValue(meta, "columnScale");\n        String carrier = enlargementMetaValue(meta, "carrier");',
    "LOG scale extraction",
)
main = replace_once(
    main,
    '''        if (!beta.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty())''',
    '''        if (!beta.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
            catch (Exception ignored) {}
        }
        if (!columnScale.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("scala LPL ").append(String.format(Locale.ITALY, "%.1f", Double.parseDouble(columnScale))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty())''',
    "LOG scale summary",
)
main = replace_once(
    main,
    '        TextView lplNote = text("Il calcolo usa il rapporto β. La scala fisica e l’eventuale offset rispetto al piano del negativo verranno attivati solo dopo una misura reale dell’ingranditore.", 11, MUTED, false);',
    '        TextView lplNote = text("Calibrazione attiva: scala 67, piano negativo–base 73 cm, marginatore 6 mm. Offset meccanico 6,0 cm; distanza negativo–carta = scala + 5,4 cm.", 11, MUTED, false);',
    "settings calibration note",
)
main_path.write_text(main, encoding="utf-8")


jpeg_path = ROOT / "JpegCardRenderer.java"
jpeg = jpeg_path.read_text(encoding="utf-8")
jpeg = replace_once(
    jpeg,
    '"Titolo", "Negativo", "Diaframma", "Ingrandimento β", "Magenta", "Yellow",',
    '"Titolo", "Negativo", "Diaframma", "β / Scala LPL", "Magenta", "Yellow",',
    "JPG scale label",
)
jpeg = replace_once(
    jpeg,
    '''    private static String enlargementBeta(LogEntry e) {
        String meta = e == null ? "" : e.enlargementMeta;
        if (meta == null || meta.trim().isEmpty()) return "—";
        String raw = "";
        for (String part : meta.split("\\\\|")) if (part.startsWith("beta=")) raw = part.substring(5);
        try { return "β " + String.format(Locale.ITALY, "%.3f", Double.parseDouble(raw)); }
        catch (Exception ignored) { return "—"; }
    }''',
    '''    private static String enlargementBeta(LogEntry e) {
        String meta = e == null ? "" : e.enlargementMeta;
        if (meta == null || meta.trim().isEmpty()) return "—";
        String beta = "", scale = "";
        for (String part : meta.split("\\\\|")) {
            if (part.startsWith("beta=")) beta = part.substring(5);
            if (part.startsWith("columnScale=")) scale = part.substring(12);
        }
        StringBuilder out = new StringBuilder();
        try { out.append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
        catch (Exception ignored) {}
        try { out.append(out.length() > 0 ? " · " : "").append("scala ").append(String.format(Locale.ITALY, "%.1f", Double.parseDouble(scale))); }
        catch (Exception ignored) {}
        return out.length() == 0 ? "—" : out.toString();
    }''',
    "JPG beta and scale value",
)
jpeg_path.write_text(jpeg, encoding="utf-8")


maintenance_path = ROOT / "maintenance/UseMaintenanceActivity.java"
maintenance = maintenance_path.read_text(encoding="utf-8")
maintenance = replace_once(
    maintenance,
    '''            "Quando va controllata la camera di diffusione?"
    };''',
    '''            "Quando va controllata la camera di diffusione?",
            "Le manopole del modulo colore e del blocco colonna sono fragili: come si riparano o sostituiscono?"
    };''',
    "LPL knob FAQ question",
)
maintenance = replace_once(
    maintenance,
    '''            "Dopo molte ore il rivestimento in materiale espanso può ingiallire. Il manuale descrive la rimozione della piastra superiore e l’estrazione della camera di diffusione; esegui l’intervento a macchina spenta e fredda."
    };''',
    '''            "Dopo molte ore il rivestimento in materiale espanso può ingiallire. Il manuale descrive la rimozione della piastra superiore e l’estrazione della camera di diffusione; esegui l’intervento a macchina spenta e fredda.",
            "Le tre manopole Ciano, Magenta e Giallo usano lo stesso ricambio LPL 3281-282 e sono intercambiabili tra loro. Se una non entra, verifica a macchina spenta che sul perno non sia rimasta la clip metallica della manopola rotta, senza fare leva sul pannello. Una riparazione con pochissimo adesivo cianoacrilato può reggere sui comandi colore solo se il selettore ruota libero: lavora sulla manopola smontata, perché l’adesivo colato lungo l’alberino può bloccare o danneggiare il meccanismo. La manopola del blocco colonna è invece il ricambio distinto LPL 3481-257 e sopporta molta più coppia: l’incollaggio è solo provvisorio. Prima dell’acquisto misura diametro, lunghezza e profondità utile dell’alberino e distingui 6,00 da 6,35 mm. Se c’è spazio, scegli una manopola robusta da circa 30–35 mm, in alluminio o con boccola metallica, con foro adatto e grano laterale serrato moderatamente sul lato piatto della D. Non forzare il blocco: una manopola più grande aumenta la leva sul meccanismo."
    };''',
    "LPL knob FAQ answer",
)
maintenance = replace_once(
    maintenance,
    '        card.addView(section("CALIBRAZIONE SCALA","La 0.4.6 calcola β e i tempi ma non converte ancora il risultato nella scala fisica della colonna. L’unico offset verrà aggiunto dopo una misura reale riferita al piano del negativo."));',
    '        card.addView(section("CALIBRAZIONE SCALA","Misura acquisita: indice scala 67, distanza piano negativo–base 73 cm, marginatore 6 mm. L’offset meccanico è 6,0 cm e la distanza negativo–carta è scala + 5,4 cm. Darkroom usa D = f × (β + 1/β + 2), con f in centimetri, e mostra scala LPL = D − 5,4. Il valore è un punto iniziale: completa sempre la messa a fuoco fine sul piano carta."));\n        card.addView(section("MANOPOLE","Ciano, Magenta e Giallo: ricambio comune LPL 3281-282. Blocco colonna: ricambio distinto LPL 3481-257; una riparazione incollata è solo provvisoria. Prima di comprare un sostituto distingui alberino a D da 6,00 e 6,35 mm; preferisci, se c’è spazio, una manopola robusta da 30–35 mm con boccola metallica e grano sul lato piatto."));',
    "maintenance calibration and knobs",
)
maintenance_path.write_text(maintenance, encoding="utf-8")


# Static and numerical acceptance for the materialized v0.4.8 sources.
geometry = geometry_target.read_text(encoding="utf-8")
enlargement = enlargement_path.read_text(encoding="utf-8")
main = main_path.read_text(encoding="utf-8")
jpeg = jpeg_path.read_text(encoding="utf-8")
maintenance = maintenance_path.read_text(encoding="utf-8")
active = "\n".join((geometry, enlargement, main, jpeg, maintenance))


def assert_balanced_java(source, label):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    state = "code"
    escaped = False
    i = 0
    while i < len(source):
        char = source[i]
        following = source[i + 1] if i + 1 < len(source) else ""
        if state == "line_comment":
            if char == "\n":
                state = "code"
        elif state == "block_comment":
            if char == '*' and following == '/':
                state = "code"
                i += 1
        elif state in ("string", "char"):
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif (state == "string" and char == '"') or (state == "char" and char == "'"):
                state = "code"
        elif char == '/' and following == '/':
            state = "line_comment"
            i += 1
        elif char == '/' and following == '*':
            state = "block_comment"
            i += 1
        elif char == '"':
            state = "string"
        elif char == "'":
            state = "char"
        elif char in "([{":
            stack.append((char, i))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                raise SystemExit(f"v0.4.8 unbalanced Java delimiter in {label} at offset {i}: {char}")
            stack.pop()
        i += 1
    if state in ("string", "char", "block_comment"):
        raise SystemExit(f"v0.4.8 unterminated Java token in {label}: {state}")
    if stack:
        raise SystemExit(f"v0.4.8 unclosed Java delimiter in {label}: {stack[-1][0]}")


for label, source in (
    ("Lpl7451Geometry", geometry),
    ("EnlargementActivity", enlargement),
    ("MainActivity", main),
    ("JpegCardRenderer", jpeg),
    ("UseMaintenanceActivity", maintenance),
):
    assert_balanced_java(source, label)

for marker in (
    "MEASURED_SCALE = 67.0",
    "MEASURED_NEGATIVE_TO_BASEBOARD_CM = 73.0",
    "EASEL_HEIGHT_CM = 0.6",
    "focalCm * (beta + 1.0 / beta + 2.0)",
    "columnCalibration=MEASURED_67_73_6MM",
    "scaleOffsetCm=5.40",
    "easelHeightMm=6.0",
    "Scala colonna LPL %.1f",
    "scala LPL %.1f",
    "LPL 3281-282",
    "LPL 3481-257",
    "6,00 da 6,35 mm",
    "30–35 mm",
    "private LinearLayout evTableView()",
    "EV_TABLE_QUESTION.equals(question)",
):
    if marker not in active:
        raise SystemExit("v0.4.8 required marker missing: " + marker)

for obsolete in (
    "columnCalibration=PENDING",
    "calibrazione fisica rinviata",
    "scala fisica non calibrata",
    "non converte ancora il risultato",
    "verranno attivati solo dopo una misura reale",
):
    if obsolete in active:
        raise SystemExit("v0.4.8 obsolete pending-calibration marker survives: " + obsolete)


def array_body(name):
    marker = "private static final String[] " + name + " = {"
    start = maintenance.index(marker)
    body_start = maintenance.index("{", start) + 1
    end = maintenance.index("\n    };", body_start)
    return maintenance[body_start:end]


def count_strings(name):
    return len(re.findall(r'"(?:\\.|[^"\\])*"', array_body(name)))


if count_strings("Q_LPL7451") != 11 or count_strings("A_LPL7451") != 11:
    raise SystemExit("v0.4.8 LPL FAQ arrays are not aligned at 11 entries")

measured_scale = 67.0
negative_to_baseboard = 73.0
easel_height = 0.6
mechanical_offset = negative_to_baseboard - measured_scale
paper_offset = mechanical_offset - easel_height
paper_distance = negative_to_baseboard - easel_height
round_trip_scale = paper_distance - paper_offset
if abs(mechanical_offset - 6.0) > 1e-9:
    raise SystemExit("v0.4.8 mechanical offset verification failed")
if abs(paper_offset - 5.4) > 1e-9:
    raise SystemExit("v0.4.8 paper-plane offset verification failed")
if abs(paper_distance - 72.4) > 1e-9 or abs(round_trip_scale - 67.0) > 1e-9:
    raise SystemExit("v0.4.8 calibration round trip failed")
for lens_mm in (50, 75, 150):
    focal_cm = lens_mm / 10.0
    sum_beta_inverse = paper_distance / focal_cm - 2.0
    discriminant = sum_beta_inverse * sum_beta_inverse - 4.0
    if discriminant < 0.0:
        raise SystemExit(f"v0.4.8 measured point is impossible for {lens_mm} mm")
    beta = (sum_beta_inverse + math.sqrt(discriminant)) / 2.0
    reconstructed_distance = focal_cm * (beta + 1.0 / beta + 2.0)
    reconstructed_scale = reconstructed_distance - paper_offset
    if abs(reconstructed_scale - measured_scale) > 1e-9:
        raise SystemExit(f"v0.4.8 {lens_mm} mm calibration round trip failed")

print("Darkroom v0.4.8 final LPL patch ready")
print("mechanical_measurement=scale_67,negative_to_baseboard_73cm,easel_6mm")
print("negative_plane_offset_cm=6.0")
print("scale_to_paper_offset_cm=5.4")
print("calibration_round_trip=67.0")
print("lenses_50_75_150_round_trip=PASS")
print("lpl_knob_faq_entries=11")
print("native_ev_table_preserved=PASS")
