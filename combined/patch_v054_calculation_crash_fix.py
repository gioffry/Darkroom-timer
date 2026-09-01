#!/usr/bin/env python3
"""Harden the v0.5.3 film calculation path against runtime crashes."""

from pathlib import Path


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.4 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# Always install a clean copy of the v0.5.4 bundled database. This also repairs
# an incomplete/corrupt first copy made by v0.5.3 on a real device.
store = STORE.read_text(encoding="utf-8")
store = replace_once(
    store,
    '    private static final String DB_NAME = "mdc_offline_darkroom_v053.sqlite";',
    '    private static final String DB_NAME = "mdc_offline_darkroom_v054.sqlite";',
    "database filename",
)
STORE.write_text(store, encoding="utf-8")


activity = ACTIVITY.read_text(encoding="utf-8")

# Catch failures that happen before the asynchronous MDC lookup (database,
# selected dilution, auxiliary chemistry or volume preparation).
activity = replace_once(
    activity,
    '        calc.setOnClickListener(v -> calculateFilmOnline());',
    '''        calc.setOnClickListener(v -> {
            try {
                calculateFilmOnline();
            } catch (Throwable error) {
                showFilmCalculationFailure(error);
            }
        });''',
    "calculate click guard",
)

# Rendering happens later on the UI thread, so it needs its own boundary.
activity = replace_once(
    activity,
    'runOnUiThread(() -> showDevelopmentResult(result, tank, rolls,',
    'runOnUiThread(() -> showDevelopmentResultSafely(result, tank, rolls,',
    "asynchronous result guard",
)

safe_result = r'''    private void showFilmCalculationFailure(Throwable error) {
        String type = error == null ? "Errore sconosciuto" : error.getClass().getSimpleName();
        String message = error == null || error.getMessage() == null
                ? "" : error.getMessage().trim();
        android.util.Log.e("DarkroomFilm", "Errore calcolo sviluppo", error);
        resultFilmError("Errore interno nel calcolo sviluppo: " + type +
                (message.isEmpty() ? "" : " · " + message) +
                ". L'app è rimasta aperta.");
    }

    private void showDevelopmentResultSafely(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        try {
            showDevelopmentResult(result, tank, rolls, dev, stop, fix,
                    devMix, stopMix, fixMix, workingVolumeMl, chemicalMinimumMl,
                    minimum, dilution);
        } catch (Throwable primary) {
            android.util.Log.e("DarkroomFilm", "Errore scheda completa; uso risultato essenziale", primary);
            try {
                showDevelopmentResultEssential(result, tank, dev, stop, fix,
                        devMix, stopMix, fixMix, workingVolumeMl, chemicalMinimumMl,
                        minimum, dilution);
            } catch (Throwable fallback) {
                showFilmCalculationFailure(fallback);
            }
        }
    }

    private void showDevelopmentResultEssential(DevTimeEngine.Result result,
                                       Tank tank,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        filmResultBox.removeAllViews();
        if (result == null || !result.found) {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", "Tempo non disponibile");
            if (result != null && result.diagnostic != null && !result.diagnostic.isEmpty())
                resultLine(filmResultBox, "DIAGNOSTICA", result.diagnostic);
        } else {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());
            resultLine(filmResultBox, "DATO ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature));
        }
        resultLine(filmResultBox, "TANK",
                tank.name + " · minimo rotazione " + fmt(tank.rotaryMl) + " ml");
        resultLine(filmResultBox, "VOLUME DI LAVORO",
                fmt(workingVolumeMl) + " ml · minimo chimico " +
                        fmt(chemicalMinimumMl) + " ml");
        resultLine(filmResultBox, "RIVELATORE",
                dev.name + "\n" +
                        formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl));
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, workingVolumeMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, workingVolumeMl));
        if (minimum != null && !minimum.sourceTitle.isEmpty())
            resultLine(filmResultBox, "FONTE / CRITERIO VOLUME", minimum.sourceTitle);
    }

'''
marker = "    private void showDevelopmentResult(DevTimeEngine.Result result,"
if marker not in activity:
    raise SystemExit("v0.5.4 result guard insertion marker missing")
activity = activity.replace(marker, safe_result + marker, 1)

ACTIVITY.write_text(activity, encoding="utf-8")

for expected in (
    'DB_NAME = "mdc_offline_darkroom_v054.sqlite"',
):
    if expected not in STORE.read_text(encoding="utf-8"):
        raise SystemExit("v0.5.4 store guard failed: " + expected)
for expected in (
    "showFilmCalculationFailure",
    "showDevelopmentResultSafely",
    "showDevelopmentResultEssential",
    "L'app è rimasta aperta",
    'android.util.Log.e("DarkroomFilm"',
):
    if expected not in activity:
        raise SystemExit("v0.5.4 activity guard failed: " + expected)

print("Darkroom v0.5.4 film-calculation crash fix ready")
