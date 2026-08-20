package it.darkroom.timer.assistant.chemistry;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Darkroom Assistant R3 — calcolo matematico della diluizione e verifica
 * della capacità solo quando esiste un dato sorgente esplicito.
 */
public final class ChemistryCalculator {
    public static final double CPE2_MAX_ML = 600.0;
    public static final String CPE2_LIMIT_SOURCE =
            "JOBO CPE instruction manual — original CPE-2: maximum 600 ml of chemicals/water";

    public static final String CAPACITY_VERIFIED = "VERIFIED";
    public static final String CAPACITY_INSUFFICIENT = "INSUFFICIENT";
    public static final String CAPACITY_UNKNOWN = "UNKNOWN";
    public static final String CAPACITY_NOT_REQUESTED = "NOT_REQUESTED";

    private static final String FOMA_UNIVERSAL_CAPACITY_SOURCE =
            "FOMA — B&W Photo Materials and Developing Information §1.9: "
            + "Universal developer, 4000 ml working solution → 12 perforated or roll films";

    private static final Pattern NUMERIC_DILUTION = Pattern.compile(
            "^\\s*(\\d+(?:[\\.,]\\d+)?)\\s*\\+\\s*(\\d+(?:[\\.,]\\d+)?)\\s*$");

    public static final class Result {
        public final boolean inputValid;
        public final String error;
        public final boolean dilutionKnown;
        public final double productMl;
        public final double waterMl;
        public final double totalMl;
        public final String dilutionMessage;
        public final String capacityState;
        public final String capacityMessage;
        public final String capacitySource;
        public final double minimumVolumeMl;
        public final boolean canAdoptMinimum;
        public final boolean cpe2Compatible;
        public final String cpe2Message;

        private Result(boolean inputValid, String error, boolean dilutionKnown,
                       double productMl, double waterMl, double totalMl, String dilutionMessage,
                       String capacityState, String capacityMessage, String capacitySource,
                       double minimumVolumeMl, boolean canAdoptMinimum,
                       boolean cpe2Compatible, String cpe2Message) {
            this.inputValid = inputValid;
            this.error = error;
            this.dilutionKnown = dilutionKnown;
            this.productMl = productMl;
            this.waterMl = waterMl;
            this.totalMl = totalMl;
            this.dilutionMessage = dilutionMessage;
            this.capacityState = capacityState;
            this.capacityMessage = capacityMessage;
            this.capacitySource = capacitySource;
            this.minimumVolumeMl = minimumVolumeMl;
            this.canAdoptMinimum = canAdoptMinimum;
            this.cpe2Compatible = cpe2Compatible;
            this.cpe2Message = cpe2Message;
        }

        private static Result invalid(String error) {
            return new Result(false, error, false, 0, 0, 0, "",
                    CAPACITY_UNKNOWN, "", "", 0, false, true, "");
        }
    }

    private ChemistryCalculator() {}

    public static Result calculate(String developer, String dilution, double totalMl,
                                   String format, int rolls) {
        if (developer == null || developer.trim().isEmpty())
            return Result.invalid("Seleziona un rivelatore/prodotto.");
        if (dilution == null || dilution.trim().isEmpty())
            return Result.invalid("Seleziona una diluizione.");
        if (!(totalMl > 0.0) || Double.isInfinite(totalMl) || Double.isNaN(totalMl))
            return Result.invalid("Inserisci un volume totale valido in ml.");
        if (rolls < 0) return Result.invalid("Numero rulli non valido.");
        if (rolls > 0 && !("35 mm".equals(format) || "120".equals(format)))
            return Result.invalid("Formato pellicola non valido.");

        String d = dilution.trim();
        boolean known = false;
        double product = 0.0;
        double water = 0.0;
        String dilutionMessage;

        if ("stock".equalsIgnoreCase(d) || "1+0".equalsIgnoreCase(d)) {
            known = true;
            product = totalMl;
            water = 0.0;
            dilutionMessage = "Diluizione calcolata: stock non diluito.";
        } else {
            Matcher m = NUMERIC_DILUTION.matcher(d);
            if (m.matches()) {
                double a = parsePart(m.group(1));
                double b = parsePart(m.group(2));
                if (a > 0.0 && b >= 0.0 && a + b > 0.0) {
                    known = true;
                    product = totalMl * a / (a + b);
                    water = totalMl - product;
                    dilutionMessage = "Diluizione calcolata matematicamente dal rapporto " + d + ".";
                } else {
                    dilutionMessage = "Rapporto di diluizione non valido.";
                }
            } else {
                // Sigle tipo "B" non vengono convertite senza metadata documentati.
                dilutionMessage = "Rapporto di diluizione non ancora disponibile dalla fonte.";
            }
        }

        boolean cpe2Compatible = totalMl <= CPE2_MAX_ML + 0.0001;
        String cpe2Message = cpe2Compatible
                ? "Volume compatibile con il limite documentato della JOBO CPE2 (max 600 ml)."
                : "Volume inserito superiore al limite documentato della JOBO CPE2 (600 ml).";

        String capacityState = rolls > 0 ? CAPACITY_UNKNOWN : CAPACITY_NOT_REQUESTED;
        String capacityMessage = rolls > 0
                ? "Capacità minima: non specificata dalla fonte."
                : "Capacità: non verificata (numero rulli non indicato).";
        String capacitySource = "";
        double minimumVolumeMl = 0.0;
        boolean canAdoptMinimum = false;

        // FOMA Universal: la fonte dichiara 4000 ml di working solution per 12
        // pellicole perforate o roll. Il rapporto film è documentato 1+3.
        if (known && rolls > 0 && same(developer, "FOMA Universal") && same(d, "1+3")) {
            minimumVolumeMl = rolls * (4000.0 / 12.0);
            capacitySource = FOMA_UNIVERSAL_CAPACITY_SOURCE;
            if (totalMl + 0.0001 >= minimumVolumeMl) {
                capacityState = CAPACITY_VERIFIED;
                capacityMessage = "Capacità: verificata per " + rolls + " × " + format + ".";
            } else {
                capacityState = CAPACITY_INSUFFICIENT;
                capacityMessage = "Capacità: insufficiente. Per " + rolls + " × " + format
                        + " servono almeno " + formatMl(minimumVolumeMl) + " ml di soluzione.";
                canAdoptMinimum = minimumVolumeMl <= CPE2_MAX_ML + 0.0001;
                if (!canAdoptMinimum) {
                    capacityMessage += " Il minimo richiesto supera il limite CPE2 di 600 ml.";
                }
            }
        } else if (!known && rolls > 0) {
            capacityState = CAPACITY_UNKNOWN;
            capacityMessage = "Capacità non verificabile finché il rapporto di diluizione non è documentato.";
        }

        return new Result(true, "", known, product, water, totalMl, dilutionMessage,
                capacityState, capacityMessage, capacitySource, minimumVolumeMl,
                canAdoptMinimum, cpe2Compatible, cpe2Message);
    }

    private static double parsePart(String s) {
        try { return Double.parseDouble(s.replace(',', '.')); }
        catch (Exception e) { return Double.NaN; }
    }

    private static boolean same(String a, String b) {
        return a != null && b != null && a.trim().equalsIgnoreCase(b.trim());
    }

    public static String formatMl(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.05)
            return String.format(Locale.ITALY, "%.0f", value);
        return String.format(Locale.ITALY, "%.1f", value);
    }
}
