#!/usr/bin/env python3
"""Patch the generated v0.5.1 source with sourced chemistry-volume limits."""

from pathlib import Path
import re


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"

for path in (STORE, ACTIVITY):
    if not path.exists():
        raise SystemExit("v0.5.2 generated source missing: " + str(path))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.2 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# A new database filename is intentional: an installed v0.5.1 must not keep the
# old copied asset, which does not have the three minimum-volume columns.
store = STORE.read_text(encoding="utf-8")
store = replace_once(
    store,
    '    private static final String DB_NAME = "mdc_offline_darkroom_v037.sqlite";',
    '    private static final String DB_NAME = "mdc_offline_darkroom_v052.sqlite";',
    "database filename",
)
store = replace_once(
    store,
    "    private static final int DB_VERSION = 3;",
    "    private static final int DB_VERSION = 4;",
    "database version",
)

minimum_lookup = r'''    static final class DeveloperMinimumVolume {
        final double for500Cm2;
        final double forOne4x5;
        final double forTwo4x5;
        final String sourceTitle;
        final String sourceUrl;

        DeveloperMinimumVolume(double for500Cm2, double forOne4x5, double forTwo4x5,
                               String sourceTitle, String sourceUrl) {
            this.for500Cm2 = for500Cm2;
            this.forOne4x5 = forOne4x5;
            this.forTwo4x5 = forTwo4x5;
            this.sourceTitle = sourceTitle == null ? "" : sourceTitle;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    static DeveloperMinimumVolume minimumWorkingVolume(String developer, String dilution) {
        if (!isReady() || developer == null || dilution == null) return null;
        String canonical = FullCatalogStore.canonicalDeveloper(developer);
        String developerNorm = norm(canonical == null ? developer : canonical);
        String dilutionNorm = normDilution(dilution);
        SQLiteDatabase db = helper.getReadableDatabase();
        try (Cursor c = db.rawQuery(
                "SELECT d.min_working_ml_500cm2,d.min_working_ml_4x5_1," +
                        "d.min_working_ml_4x5_2,s.source_title,s.source_url " +
                        "FROM developer_dilutions d " +
                        "LEFT JOIN developer_minimum_volume_sources s " +
                        "ON s.developer_norm=d.developer_norm AND s.dilution_norm=d.dilution_norm " +
                        "WHERE d.developer_norm=? AND d.dilution_norm=? LIMIT 1",
                new String[]{developerNorm, dilutionNorm})) {
            if (!c.moveToFirst() || c.isNull(0) || c.isNull(1) || c.isNull(2)) return null;
            double for500 = c.getDouble(0);
            double forOne = c.getDouble(1);
            double forTwo = c.getDouble(2);
            if (for500 <= 0 || forOne <= 0 || forTwo <= 0) return null;
            return new DeveloperMinimumVolume(for500, forOne, forTwo,
                    c.isNull(3) ? "" : c.getString(3),
                    c.isNull(4) ? "" : c.getString(4));
        }
    }

'''
marker = "    static int nominalIsoForFilm(String film) {"
if marker not in store:
    raise SystemExit("v0.5.2 minimum-volume lookup insertion marker missing")
store = store.replace(marker, minimum_lookup + marker, 1)
STORE.write_text(store, encoding="utf-8")


activity = ACTIVITY.read_text(encoding="utf-8")
activity = replace_once(
    activity,
    '            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "3", "4", "5", "6"});',
    '            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "4"});',
    "supported sheet counts",
)

volume_helper = r'''    private double chemicalMinimumForLoad(
            MdcOfflineStore.DeveloperMinimumVolume minimum, String format, int count) {
        if (minimum == null || count <= 0) return -1;
        if (!isSheetFormat(format)) return minimum.for500Cm2 * count;
        if (count == 1) return minimum.forOne4x5;
        if (count == 2) return minimum.forTwo4x5;
        if (count == 4) return minimum.for500Cm2;
        return -1;
    }

'''
marker = "    private Tank selectedTank() {"
if marker not in activity:
    raise SystemExit("v0.5.2 chemical minimum helper marker missing")
activity = activity.replace(marker, volume_helper + marker, 1)

calculate_method = r'''    private void calculateFilmOnline() {
        if (selectedFilm == null) selectedFilm = findFilm(filmField.getText().toString().trim());
        if (selectedFilm == null) { toast("Seleziona una pellicola."); return; }
        if (selectedFilmDeveloper == null) { toast("Seleziona un rivelatore dal magazzino."); return; }
        if (selectedStop == null || selectedFix == null) {
            toast("Aggiungi arresto e fissaggio al magazzino."); return;
        }
        Tank tank = selectedTank();
        if (tank == null) { resultFilmError("Nessuna tank compatibile."); return; }

        int iso;
        double temp;
        int rolls;
        try {
            iso = Integer.parseInt(isoField.getText().toString().trim());
            temp = Double.parseDouble(temperatureField.getText().toString().trim().replace(',', '.'));
            rolls = Integer.parseInt(String.valueOf(rollsSpinner.getSelectedItem()));
        } catch (Exception e) {
            toast(isSheetFormat(selectedFilm.format)
                    ? "Controlla ISO, temperatura e numero lastre."
                    : "Controlla ISO, temperatura e rulli.");
            return;
        }

        String dilution = String.valueOf(dilutionSpinner.getSelectedItem());
        if ("—".equals(dilution)) { toast("Diluizione rivelatore non disponibile."); return; }
        MdcOfflineStore.DeveloperMinimumVolume minimum =
                MdcOfflineStore.minimumWorkingVolume(selectedFilmDeveloper.name, dilution);
        if (minimum == null) {
            resultFilmError("Volume minimo chimico non verificato per " +
                    selectedFilmDeveloper.name + " " + dilution +
                    ". Calcolo bloccato: nessuna stima viene applicata.");
            return;
        }
        double chemicalMinimumMl = chemicalMinimumForLoad(minimum, selectedFilm.format, rolls);
        if (chemicalMinimumMl <= 0) {
            resultFilmError("Numero di lastre non supportato. Seleziona 1, 2 oppure 4 lastre 4×5.");
            return;
        }
        double workingVolumeMl = Math.max(tank.rotaryMl, Math.ceil(chemicalMinimumMl));
        if (workingVolumeMl > 600) {
            resultFilmError("Servono " + fmt(workingVolumeMl) +
                    " ml: supera il limite 600 ml della JOBO CPE2 (minimo tank " +
                    tank.rotaryMl + " ml, minimo chimico " + fmt(chemicalMinimumMl) + " ml).");
            return;
        }

        double[] devMix = mix(workingVolumeMl, dilution);
        String stopDilution = filmAuxDilution(selectedStop);
        String fixDilution = filmAuxDilution(selectedFix);
        double[] stopMix = mix(workingVolumeMl, stopDilution);
        double[] fixMix = mix(workingVolumeMl, fixDilution);
        if (devMix == null || stopMix == null || fixMix == null) {
            resultFilmError("Una diluizione non è calcolabile: modifica la scheda prodotto.");
            return;
        }

        lastFilmTank = tank;
        lastFilmRolls = rolls;
        filmResultBox.removeAllViews();
        resultLine(filmResultBox, "RICERCA TEMPO", "Cerco la combinazione nel database offline…");
        final Product dev = selectedFilmDeveloper;
        final Product stop = selectedStop;
        final Product fix = selectedFix;
        new Thread(() -> {
            DevTimeEngine.Result result = MdcOfflineStore.lookup(
                    selectedFilm.name, selectedFilm.format, dev.name, dilution, iso, temp);
            runOnUiThread(() -> showDevelopmentResult(result, tank, rolls,
                    dev, stop, fix, devMix, stopMix, fixMix,
                    workingVolumeMl, chemicalMinimumMl, minimum));
        }).start();
    }

'''
activity, count = re.subn(
    r"    private void calculateFilmOnline\(\) \{.*?\n    \}\n\n(?=    private void showDevelopmentResult)",
    lambda _match: calculate_method,
    activity,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("v0.5.2 calculateFilmOnline replacement failed")

activity = replace_once(
    activity,
    '''    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix) {''',
    '''    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum) {''',
    "development result signature",
)
activity = replace_once(
    activity,
    '        resultLine(filmResultBox, "TANK", tankDisplayName(tank, result.format) + " · volume rotazione " + tank.rotaryMl + " ml");',
    '''        resultLine(filmResultBox, "TANK",
                tankDisplayName(tank, result.format) + " · minimo rotazione " + tank.rotaryMl + " ml");
        resultLine(filmResultBox, "VOLUME DI LAVORO",
                fmt(workingVolumeMl) + " ml · minimo chimico " + fmt(chemicalMinimumMl) + " ml");
        if (!minimum.sourceTitle.isEmpty()) {
            resultLine(filmResultBox, "FONTE VOLUME", minimum.sourceTitle);
            if (!minimum.sourceUrl.isEmpty()) {
                Button openMinimumSource = smallButton("APRI FONTE VOLUME");
                openMinimumSource.setOnClickListener(v -> openUrl(minimum.sourceUrl));
                filmResultBox.addView(openMinimumSource);
                filmResultBox.addView(space(10));
            }
        }''',
    "volume result lines",
)
for chemical in ("dev", "stop", "fix"):
    activity = activity.replace(
        f"formatMix({chemical}Mix, tank.rotaryMl)",
        f"formatMix({chemical}Mix, workingVolumeMl)",
    )
activity = activity.replace(
    "renderFilmCapacity(dev, stop, fix, tank.rotaryMl)",
    "renderFilmCapacity(dev, stop, fix, workingVolumeMl)",
)
for chemical in ("dev", "stop", "fix"):
    activity = activity.replace(
        f"registerFilmUse({chemical}, tank.rotaryMl, units)",
        f"registerFilmUse({chemical}, workingVolumeMl, units)",
    )
    activity = activity.replace(
        f"resetFilmBath({chemical}, tank.rotaryMl)",
        f"resetFilmBath({chemical}, workingVolumeMl)",
    )

ACTIVITY.write_text(activity, encoding="utf-8")


store = STORE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")
for expected in (
    'DB_NAME = "mdc_offline_darkroom_v052.sqlite"',
    "DB_VERSION = 4",
    "static DeveloperMinimumVolume minimumWorkingVolume",
    "min_working_ml_500cm2",
    "developer_minimum_volume_sources",
):
    if expected not in store:
        raise SystemExit("v0.5.2 store guard failed: " + expected)
for expected in (
    'new String[]{"1", "2", "4"}',
    "chemicalMinimumForLoad",
    "Math.max(tank.rotaryMl, Math.ceil(chemicalMinimumMl))",
    "Volume minimo chimico non verificato",
    '"VOLUME DI LAVORO"',
    "workingVolumeMl, chemicalMinimumMl, minimum",
    "renderFilmCapacity(dev, stop, fix, workingVolumeMl)",
):
    if expected not in activity:
        raise SystemExit("v0.5.2 activity guard failed: " + expected)
if "renderFilmCapacity(dev, stop, fix, tank.rotaryMl)" in activity:
    raise SystemExit("v0.5.2 stale tank-only capacity volume remains")

print("Darkroom v0.5.2 chemistry minimum-volume patch ready")
