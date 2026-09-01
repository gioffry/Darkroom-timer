#!/usr/bin/env python3
"""Replace the dense development result stack with progressive disclosure."""

from pathlib import Path
import re


ACTIVITY = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
activity = ACTIVITY.read_text(encoding="utf-8")

replacement = r'''    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        filmResultBox.removeAllViews();
        String loadFormat = selectedFilm != null ? selectedFilm.format
                : (result == null ? "35" : result.format);
        String filmName = selectedFilm == null ? "Pellicola" : selectedFilm.name;

        LinearLayout summary = new LinearLayout(this);
        summary.setOrientation(LinearLayout.VERTICAL);
        summary.setPadding(dp(18), dp(16), dp(18), dp(16));
        summary.setBackground(bg(CARD, 13, BORDER, 1));
        summary.addView(label("RISULTATO SVILUPPO", 15, WHITE, true));
        addUnifiedChemicalField(summary, "TEMPO JOBO CPE2",
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");
        addUnifiedChemicalField(summary, "COMBINAZIONE",
                filmName + " · " + dev.name + " " + dilution);
        addUnifiedChemicalField(summary, "TANK / VOLUME",
                tankDisplayName(tank, loadFormat) + " · " + fmt(workingVolumeMl) +
                        " ml (minimo tank " + fmt(tank.rotaryMl) + " ml)");
        filmResultBox.addView(summary);
        filmResultBox.addView(space(10));

        LinearLayout preparation = new LinearLayout(this);
        preparation.setOrientation(LinearLayout.VERTICAL);
        preparation.setPadding(dp(18), dp(14), dp(18), dp(14));
        preparation.setBackground(bg(CARD, 13, BORDER, 1));
        preparation.addView(label("PREPARAZIONE BAGNI", 15, WHITE, true));
        addUnifiedChemicalField(preparation, "RIVELATORE · " + dev.name,
                formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl));
        addUnifiedChemicalField(preparation, "ARRESTO · " + stop.name,
                formatMix(stopMix, workingVolumeMl));
        addUnifiedChemicalField(preparation, "FISSAGGIO · " + fix.name,
                formatMix(fixMix, workingVolumeMl));
        filmResultBox.addView(preparation);
        filmResultBox.addView(space(10));

        LinearLayout calculation = accordionBody();
        if (result == null || !result.found) {
            addUnifiedChemicalField(calculation, "TEMPO NON DISPONIBILE",
                    result == null || result.diagnostic == null || result.diagnostic.isEmpty()
                            ? "Nessuna combinazione esatta trovata nel database."
                            : result.diagnostic);
        } else {
            addUnifiedChemicalField(calculation, "DATO MDC ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature) +
                            " · ISO " + result.sourceIso + " · " + formatDisplay(loadFormat));
            String conversion = result.temperatureConverted
                    ? "Temperatura compensata a " + fmtTemp(result.targetTemperature)
                    : "Temperatura: dato originale";
            conversion += "\nJOBO CPE2: rotazione continua, adattamento −15%";
            addUnifiedChemicalField(calculation, "ADATTAMENTI", conversion);
            addUnifiedChemicalField(calculation, "FONTE COMBINAZIONE",
                    result.sourceName + "\n" + result.sourceFilm + " · " +
                            result.sourceDeveloper + " · " + result.sourceDilution);
            if (result.warning != null && !result.warning.isEmpty())
                addUnifiedChemicalField(calculation, "ATTENZIONE", result.warning);
        }
        addUnifiedChemicalField(calculation, "MINIMO CHIMICO",
                fmt(chemicalMinimumMl) + " ml · volume utilizzato " +
                        fmt(workingVolumeMl) + " ml");
        if (minimum != null && !minimum.sourceTitle.isEmpty()) {
            String evidenceLabel = "CONSERVATIVE_OPERATIONAL".equals(minimum.evidenceKind)
                    ? "criterio operativo conservativo"
                    : "dato o ricetta del produttore";
            addUnifiedChemicalField(calculation, "FONTE / CRITERIO VOLUME",
                    minimum.sourceTitle + " · " + evidenceLabel);
            if (!minimum.sourceUrl.isEmpty()) {
                Button openMinimumSource = smallButton("APRI FONTE VOLUME");
                openMinimumSource.setOnClickListener(v -> openUrl(minimum.sourceUrl));
                calculation.addView(openMinimumSource);
            }
        }
        addFilmAccordion(filmResultBox, "DETTAGLI DEL CALCOLO",
                result != null && result.found ? "MDC · JOBO · minimo chimico" : "Tempo non disponibile",
                calculation);

        LinearLayout technicalBody = accordionBody();
        String technical = chemicalTechnicalSummaryIt(dev.name);
        addUnifiedChemicalField(technicalBody, dev.name,
                technical.isEmpty()
                        ? "Scheda tecnica non ancora verificata per questo prodotto."
                        : technical);
        addFilmAccordion(filmResultBox, "SCHEDA TECNICA RIVELATORE",
                "Preparazione · conservazione · capacità", technicalBody);

        LinearLayout reuseBody = accordionBody();
        filmCapacityBox = new LinearLayout(this);
        filmCapacityBox.setOrientation(LinearLayout.VERTICAL);
        reuseBody.addView(filmCapacityBox);
        renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
        addFilmAccordion(filmResultBox, "RIUTILIZZO BAGNI",
                filmReuseCompactSummary(dev, stop, fix, workingVolumeMl), reuseBody);

        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);
        register.setOnClickListener(v -> {
            double units = filmCapacityUnits(rolls, loadFormat);
            registerFilmUse(dev, workingVolumeMl, units);
            registerFilmUse(stop, workingVolumeMl, units);
            registerFilmUse(fix, workingVolumeMl, units);
            renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
            toast(developedUnitLabel(rolls, loadFormat) + " registrat" +
                    (rolls == 1 ? "a." : "e."));
        });
        filmResultBox.addView(register);
        filmResultBox.addView(space(9));

        Button fresh = smallButton("NUOVO BAGNO / AZZERA CONTATORE");
        fresh.setOnClickListener(v -> {
            resetFilmBath(dev, workingVolumeMl);
            resetFilmBath(stop, workingVolumeMl);
            resetFilmBath(fix, workingVolumeMl);
            renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
            toast("Contatori del bagno azzerati.");
        });
        filmResultBox.addView(fresh);
        filmResultBox.addView(space(20));
    }

    private LinearLayout accordionBody() {
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(16), 0, dp(16), dp(14));
        return body;
    }

    private void addFilmAccordion(LinearLayout parent, String title,
                                  String compactSummary, LinearLayout body) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setBackground(bg(CARD, 13, BORDER, 1));
        TextView header = label("▸ " + title + "\n" + compactSummary, 14, WHITE, true);
        header.setPadding(dp(16), dp(13), dp(16), dp(13));
        body.setVisibility(View.GONE);
        final boolean[] open = new boolean[]{false};
        header.setOnClickListener(v -> {
            open[0] = !open[0];
            body.setVisibility(open[0] ? View.VISIBLE : View.GONE);
            header.setText((open[0] ? "▾ " : "▸ ") + title + "\n" + compactSummary);
        });
        section.addView(header);
        section.addView(body);
        parent.addView(section);
        parent.addView(space(10));
    }

    private String filmReuseCompactSummary(Product dev, Product stop, Product fix,
                                           double volumeMl) {
        String developerState = dev != null &&
                dev.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT
                ? "rivelatore monouso" : "stato bagni disponibile";
        return developerState + " · apri per capacità e contatori";
    }

    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,
                                             double volumeMl, String format) {
        renderFilmCapacity(dev, stop, fix, volumeMl);
        if (filmCapacityBox != null && isSheetFormat(format)) {
            resultLine(filmCapacityBox, "EQUIVALENZA CAPACITÀ",
                    "Per il solo contatore chimico: 4 lastre 4×5 ≈ 1 rullo 135-36 / 120 per superficie di emulsione.");
        }
    }

    private void renderFilmCapacity'''

pattern = re.compile(
    r'''    private void showDevelopmentResult\(DevTimeEngine\.Result result,.*?\n    \}\n\n    private void renderFilmCapacity''',
    re.S,
)
activity, count = pattern.subn(lambda _m: replacement, activity, count=1)
if count != 1:
    raise SystemExit("v0.5.5 result UI replacement failed")

ACTIVITY.write_text(activity, encoding="utf-8")

for expected in (
    "RISULTATO SVILUPPO",
    "PREPARAZIONE BAGNI",
    "DETTAGLI DEL CALCOLO",
    "SCHEDA TECNICA RIVELATORE",
    "RIUTILIZZO BAGNI",
    "addFilmAccordion",
    "body.setVisibility(View.GONE)",
    "selectedFilm != null ? selectedFilm.format",
):
    if expected not in activity:
        raise SystemExit("v0.5.5 progressive UI guard failed: " + expected)

print("Darkroom v0.5.5 progressive result UI ready")
