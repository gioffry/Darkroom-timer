#!/usr/bin/env python3
"""Patch v0.5.2 for the complete Maco-scoped v0.5.3 volume dataset."""

from pathlib import Path


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"

for path in (STORE, ACTIVITY):
    if not path.exists():
        raise SystemExit("v0.5.3 generated source missing: " + str(path))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.3 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


store = STORE.read_text(encoding="utf-8")
store = replace_once(
    store,
    '    private static final String DB_NAME = "mdc_offline_darkroom_v052.sqlite";',
    '    private static final String DB_NAME = "mdc_offline_darkroom_v053.sqlite";',
    "database filename",
)
store = replace_once(
    store,
    "    private static final int DB_VERSION = 4;",
    "    private static final int DB_VERSION = 5;",
    "database version",
)
store = replace_once(
    store,
    '''        final String sourceTitle;
        final String sourceUrl;

        DeveloperMinimumVolume(double for500Cm2, double forOne4x5, double forTwo4x5,
                               String sourceTitle, String sourceUrl) {''',
    '''        final String sourceTitle;
        final String sourceUrl;
        final String evidenceKind;

        DeveloperMinimumVolume(double for500Cm2, double forOne4x5, double forTwo4x5,
                               String sourceTitle, String sourceUrl, String evidenceKind) {''',
    "minimum evidence fields",
)
store = replace_once(
    store,
    '''            this.sourceTitle = sourceTitle == null ? "" : sourceTitle;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;''',
    '''            this.sourceTitle = sourceTitle == null ? "" : sourceTitle;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
            this.evidenceKind = evidenceKind == null ? "UNKNOWN" : evidenceKind;''',
    "minimum evidence constructor",
)
store = replace_once(
    store,
    '''                        "d.min_working_ml_4x5_2,s.source_title,s.source_url " +''',
    '''                        "d.min_working_ml_4x5_2,s.source_title,s.source_url,s.evidence_kind " +''',
    "minimum evidence query",
)
store = replace_once(
    store,
    '''                    c.isNull(3) ? "" : c.getString(3),
                    c.isNull(4) ? "" : c.getString(4));''',
    '''                    c.isNull(3) ? "" : c.getString(3),
                    c.isNull(4) ? "" : c.getString(4),
                    c.isNull(5) ? "UNKNOWN" : c.getString(5));''',
    "minimum evidence result",
)
STORE.write_text(store, encoding="utf-8")


activity = ACTIVITY.read_text(encoding="utf-8")
activity = replace_once(
    activity,
    '''            resultFilmError("Volume minimo chimico non verificato per " +
                    selectedFilmDeveloper.name + " " + dilution +
                    ". Calcolo bloccato: nessuna stima viene applicata.");''',
    '''            resultFilmError("Rivelatore non incluso nel catalogo Maco Direct censito, " +
                    "oppure volume minimo non disponibile per " +
                    selectedFilmDeveloper.name + " " + dilution + ". Calcolo bloccato.");''',
    "outside-scope error",
)
activity = replace_once(
    activity,
    '''                    workingVolumeMl, chemicalMinimumMl, minimum));''',
    '''                    workingVolumeMl, chemicalMinimumMl, minimum, dilution));''',
    "selected dilution result argument",
)
activity = replace_once(
    activity,
    '''                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum) {''',
    '''                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {''',
    "selected dilution result signature",
)
activity = replace_once(
    activity,
    '''            resultLine(filmResultBox, "FONTE VOLUME", minimum.sourceTitle);''',
    '''            String evidenceLabel = "CONSERVATIVE_OPERATIONAL".equals(minimum.evidenceKind)
                    ? "criterio operativo conservativo"
                    : "dato o ricetta del produttore";
            resultLine(filmResultBox, "FONTE / CRITERIO VOLUME",
                    minimum.sourceTitle + " · " + evidenceLabel);''',
    "minimum evidence display",
)
activity = replace_once(
    activity,
    '''        resultLine(filmResultBox, "RIVELATORE",
                dev.name + "\\n" + formatMix(devMix, workingVolumeMl));''',
    '''        resultLine(filmResultBox, "RIVELATORE",
                dev.name + "\\n" +
                        formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl));''',
    "multi-component developer display",
)

old_mix = r'''    private double[] mix(double total, String dilution) {
        if (dilution == null) return null;
        String d = dilution.trim().toLowerCase(Locale.ROOT);
        if ("stock".equals(d)) return new double[]{total, 0};
        String[] parts = d.split("\\+");
        if (parts.length != 2) return null;
        try {
            double a = Double.parseDouble(parts[0].trim());
            double b = Double.parseDouble(parts[1].trim());
            if (a <= 0 || b < 0) return null;
            double c = total * a / (a + b);
            return new double[]{c, total - c};
        } catch (Exception e) { return null; }
    }
'''
new_mix = r'''    private String normalizedMixDilution(String dilution) {
        if (dilution == null) return "";
        String d = dilution.trim().toLowerCase(Locale.ROOT)
                .replace(":", "+").replace(" ", "");
        if ("a".equals(d)) return "1+15";
        if ("b".equals(d)) return "1+31";
        if ("c".equals(d)) return "1+19";
        if ("d".equals(d)) return "1+39";
        if ("e".equals(d)) return "1+47";
        if ("f".equals(d)) return "1+79";
        if ("g".equals(d)) return "1+119";
        if ("h".equals(d)) return "1+63";
        if ("j".equals(d)) return "1+150";
        if (d.matches("[0-9]+")) return "1+" + d;
        return d;
    }

    private double[] mix(double total, String dilution) {
        String d = normalizedMixDilution(dilution);
        if (d.isEmpty()) return null;
        if ("stock".equals(d)) return new double[]{total, 0};
        String[] parts = d.split("\\+");
        if (parts.length < 2) return null;
        try {
            double sum = 0;
            double developerParts = 0;
            for (int i = 0; i < parts.length; i++) {
                double value = Double.parseDouble(parts[i].trim());
                if (value <= 0) return null;
                sum += value;
                if (i < parts.length - 1) developerParts += value;
            }
            if (developerParts <= 0 || sum <= developerParts) return null;
            double concentrate = total * developerParts / sum;
            return new double[]{concentrate, total - concentrate};
        } catch (Exception e) { return null; }
    }

    private String formatDeveloperMix(String developerName, String dilution,
                                      double[] mixed, double total) {
        boolean twoPart = developerName != null &&
                (developerName.toLowerCase(Locale.ROOT).contains("moersch eco") ||
                 developerName.toLowerCase(Locale.ROOT).contains("jobo alpha"));
        String d = normalizedMixDilution(dilution);
        String[] parts = d.split("\\+");
        if (!twoPart || parts.length != 3) return formatMix(mixed, total);
        try {
            double a = Double.parseDouble(parts[0]);
            double b = Double.parseDouble(parts[1]);
            double water = Double.parseDouble(parts[2]);
            double scale = total / (a + b + water);
            return "Parte A " + fmt(a * scale) + " ml + Parte B " + fmt(b * scale) +
                    " ml + " + fmt(water * scale) + " ml acqua · totale " +
                    fmt(total) + " ml";
        } catch (Exception e) { return formatMix(mixed, total); }
    }
'''
activity = replace_once(activity, old_mix, new_mix, "multi-part dilution calculator")
ACTIVITY.write_text(activity, encoding="utf-8")


store = STORE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")
for expected in (
    'DB_NAME = "mdc_offline_darkroom_v053.sqlite"',
    "DB_VERSION = 5",
    "s.evidence_kind",
    "final String evidenceKind",
):
    if expected not in store:
        raise SystemExit("v0.5.3 store guard failed: " + expected)
for expected in (
    "normalizedMixDilution",
    "parts.length < 2",
    "formatDeveloperMix",
    "Parte A",
    "FONTE / CRITERIO VOLUME",
    "catalogo Maco Direct censito",
):
    if expected not in activity:
        raise SystemExit("v0.5.3 activity guard failed: " + expected)

print("Darkroom v0.5.3 Maco minimum-volume patch ready")
