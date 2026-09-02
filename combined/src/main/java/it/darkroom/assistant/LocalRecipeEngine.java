package it.darkroom.assistant;

import java.util.Locale;

/**
 * Piccolo livello locale per ricette approvate quando Massive Dev Chart non
 * contiene la combinazione esatta. Non sostituisce Digitaltruth: viene usato
 * soltanto dopo un lookup offline fallito ed e' sempre etichettato come stima.
 */
final class LocalRecipeEngine {
    private static final double JOBO_FACTOR = 0.85;
    private static final double TEMP_FACTOR_PER_C = 0.91;

    private LocalRecipeEngine() {}

    static DevTimeEngine.Result lookup(String filmName, String format, String developer,
                                       String dilution, int iso, double targetTemp) {
        String film = norm(filmName);
        String dev = norm(developer);
        String dil = normDilution(dilution);

        // Ricetta locale gia' usata nel progetto: FP4+ @125 con Foma Universal 1+3.
        // Base manuale 20 °C = 9:30. La app applica poi compensazione temperatura
        // e -15% per JOBO CPE2 a rotazione continua.
        if ((film.equals("ilford fp4") || film.equals("ilford fp4 plus") || film.equals("fp4") || film.equals("fp4 plus"))
                && dev.equals("foma universal") && dil.equals("1+3") && iso == 125) {
            int base = 9 * 60 + 30;
            int adjusted = temperatureConvert(base, 20.0, targetTemp);
            int finalSeconds = roundTo5((int) Math.round(adjusted * JOBO_FACTOR));
            String warning = "STIMA LOCALE: questa combinazione non e' presente come riga esatta in Digitaltruth. " +
                    "Base 9:30 a 20 °C; poi compensazione temperatura e JOBO CPE2 -15%.";
            if (finalSeconds < 300) warning += " Tempo finale sotto 5 minuti.";
            return new DevTimeEngine.Result(true,
                    finalSeconds, finalSeconds,
                    base, base,
                    20.0, targetTemp,
                    "Ricetta locale approvata", "",
                    "Ilford FP4+", "Foma Universal", "1+3", 125,
                    format == null || format.isEmpty() ? "35" : format,
                    Math.abs(targetTemp - 20.0) > 0.01, true,
                    warning,
                    "Digitaltruth non contiene la combinazione esatta; usata la ricetta locale esplicitamente marcata come stima.");
        }
        return null;
    }

    private static int temperatureConvert(int seconds, double fromC, double toC) {
        double adjusted = seconds * Math.pow(TEMP_FACTOR_PER_C, toC - fromC);
        return roundTo15((int) Math.round(adjusted));
    }

    private static int roundTo15(int seconds) {
        return Math.max(15, (int) Math.round(seconds / 15.0) * 15);
    }

    private static int roundTo5(int seconds) {
        return Math.max(5, (int) Math.round(seconds / 5.0) * 5);
    }

    private static String norm(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT)
                .replace("+", " plus ")
                .replaceAll("[^a-z0-9]+", " ").trim();
    }

    private static String normDilution(String s) {
        if (s == null) return "";
        String x = s.toLowerCase(Locale.ROOT).replaceAll("\\s+", "");
        if (x.equals("stock")) return "stock";
        return x.replace(':', '+');
    }
}
