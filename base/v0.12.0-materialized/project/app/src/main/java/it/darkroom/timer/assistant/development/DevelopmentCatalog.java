package it.darkroom.timer.assistant.development;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Catalogo iniziale source-backed per Darkroom Assistant R2.
 * Nessun tempo viene stimato quando manca un dato sorgente compatibile.
 */
public final class DevelopmentCatalog {
    public static final String PROCESSOR = "JOBO CPE2";
    public static final String PROCESS_METHOD = "rotazione continua";

    private static final String MANUAL = "manuale/intermittente";
    private static final String ROTARY = "rotary/continua";
    private static final String SRC_FOMA = "FOMA — B&W Photo Materials and Developing Information / FOMA 04/23";
    private static final String SRC_ILFORD_HP5 = "ILFORD — HP5 PLUS Technical Information, Nov 2018";
    private static final String SRC_KODAK_TRIX = "KODAK — TRI-X 320/400 Technical Data F-4017, Oct 2021";
    private static final String TEMP_METHOD = "FOMA — tabella ufficiale di correzione temperatura 16–26 °C";
    private static final String ROTARY_METHOD = "ILFORD — guida rotary processor: fino a −15% senza pre-rinse";

    public static final class Film {
        public final String name;
        public final int nominalIso;
        public final boolean format35;
        public final boolean format120;
        Film(String name, int nominalIso, boolean format35, boolean format120) {
            this.name = name; this.nominalIso = nominalIso;
            this.format35 = format35; this.format120 = format120;
        }
    }

    private static final class Recipe {
        final String film;
        final int ei;
        final String developer;
        final String dilution;
        final double tempC;
        final int minSeconds;
        final int maxSeconds;
        final String method;
        final String source;
        final String sourceNote;

        Recipe(String film, int ei, String developer, String dilution, double tempC,
               int minSeconds, int maxSeconds, String method, String source, String sourceNote) {
            this.film = film; this.ei = ei; this.developer = developer; this.dilution = dilution;
            this.tempC = tempC; this.minSeconds = minSeconds; this.maxSeconds = maxSeconds;
            this.method = method; this.source = source; this.sourceNote = sourceNote;
        }
        boolean range() { return minSeconds != maxSeconds; }
        int midpoint() { return (int) Math.round((minSeconds + maxSeconds) / 2.0); }
    }

    public static final class Result {
        public final boolean ok;
        public final String error;
        public final String film;
        public final String format;
        public final int nominalIso;
        public final int exposedIso;
        public final String developer;
        public final String dilution;
        public final double temperature;
        public final int finalSeconds;
        public final String source;
        public final String dataType;
        public final String sourceData;
        public final String calculation;
        public final String alternatives;

        private Result(boolean ok, String error, String film, String format, int nominalIso, int exposedIso,
                       String developer, String dilution, double temperature, int finalSeconds,
                       String source, String dataType, String sourceData, String calculation, String alternatives) {
            this.ok = ok; this.error = error; this.film = film; this.format = format;
            this.nominalIso = nominalIso; this.exposedIso = exposedIso; this.developer = developer;
            this.dilution = dilution; this.temperature = temperature; this.finalSeconds = finalSeconds;
            this.source = source; this.dataType = dataType; this.sourceData = sourceData;
            this.calculation = calculation; this.alternatives = alternatives;
        }

        static Result error(String message) {
            return new Result(false, message, "", "", 0, 0, "", "", 0, 0, "", "", "", "", "");
        }
    }

    private static final class Candidate {
        int seconds;
        int score;
        boolean adapted;
        String source;
        String sourceData;
        String calculation;
    }

    private static final List<Film> FILMS = new ArrayList<>();
    private static final List<Recipe> RECIPES = new ArrayList<>();

    static {
        FILMS.add(new Film("Fomapan 100 Classic", 100, true, true));
        FILMS.add(new Film("Fomapan 200 Creative", 200, true, true));
        FILMS.add(new Film("Fomapan 400 Action", 400, true, true));
        FILMS.add(new Film("ILFORD HP5 PLUS", 400, true, true));
        FILMS.add(new Film("KODAK TRI-X 400", 400, true, true));

        // FOMA official 20 °C manual/intermittent data. Ranges are preserved;
        // when one final timer value is required, the app transparently uses the midpoint.
        addManual("Fomapan 100 Classic",100,"FOMA Universal","1+3",300,SRC_FOMA,"5 min @20 °C");
        addManual("Fomapan 100 Classic",100,"FOMADON R09","1+25",240,SRC_FOMA,"4 min @20 °C");
        addManual("Fomapan 100 Classic",100,"FOMADON R09","1+50",540,SRC_FOMA,"9 min @20 °C");
        addRange("Fomapan 100 Classic",100,"KODAK D-76","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","1+1",480,600,SRC_FOMA,"8–10 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD ID-11","1+3",900,960,SRC_FOMA,"15–16 min @20 °C");
        addRange("Fomapan 100 Classic",100,"KODAK XTOL","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","stock",300,420,SRC_FOMA,"5–7 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","1+1",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 100 Classic",100,"ILFORD MICROPHEN","1+3",780,840,SRC_FOMA,"13–14 min @20 °C");

        addManual("Fomapan 200 Creative",200,"FOMA Universal","1+3",210,SRC_FOMA,"3 min 30 s @20 °C");
        addManual("Fomapan 200 Creative",200,"FOMADON R09","1+25",300,SRC_FOMA,"5 min @20 °C");
        addManual("Fomapan 200 Creative",200,"FOMADON R09","1+50",600,SRC_FOMA,"10 min @20 °C");
        addRange("Fomapan 200 Creative",200,"KODAK D-76","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","stock",300,360,SRC_FOMA,"5–6 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","1+1",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD ID-11","1+3",720,780,SRC_FOMA,"12–13 min @20 °C");
        addRange("Fomapan 200 Creative",200,"KODAK XTOL","stock",360,420,SRC_FOMA,"6–7 min @20 °C");
        addRange("Fomapan 200 Creative",200,"ILFORD MICROPHEN","stock",300,360,SRC_FOMA,"5–6 min @20 °C");

        addManual("Fomapan 400 Action",400,"FOMA Universal","1+3",450,SRC_FOMA,"7 min 30 s @20 °C");
        addManual("Fomapan 400 Action",400,"FOMADON R09","1+25",360,SRC_FOMA,"6 min @20 °C");
        addManual("Fomapan 400 Action",400,"FOMADON R09","1+50",720,SRC_FOMA,"12 min @20 °C");
        addRange("Fomapan 400 Action",400,"KODAK D-76","stock",420,480,SRC_FOMA,"7–8 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","stock",420,480,SRC_FOMA,"7–8 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","1+1",720,780,SRC_FOMA,"12–13 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD ID-11","1+3",1320,1380,SRC_FOMA,"22–23 min @20 °C");
        addManual("Fomapan 400 Action",400,"KODAK XTOL","stock",420,SRC_FOMA,"7 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD MICROPHEN","stock",480,540,SRC_FOMA,"8–9 min @20 °C");
        addRange("Fomapan 400 Action",400,"ILFORD MICROPHEN","1+1",720,780,SRC_FOMA,"12–13 min @20 °C");

        // ILFORD HP5 PLUS official 20 °C spiral-tank data, including non-ILFORD developers.
        hp5(400,"ILFORD ILFOTEC DD-X","1+4",540); hp5(800,"ILFORD ILFOTEC DD-X","1+4",600);
        hp5(1600,"ILFORD ILFOTEC DD-X","1+4",780); hp5(3200,"ILFORD ILFOTEC DD-X","1+4",1200);
        hp5(400,"ILFORD ID-11","stock",450); hp5(800,"ILFORD ID-11","stock",630); hp5(1600,"ILFORD ID-11","stock",840);
        hp5(400,"ILFORD ID-11","1+1",780); hp5(800,"ILFORD ID-11","1+1",990);
        hp5(400,"ILFORD ID-11","1+3",1200);
        hp5(400,"ILFORD MICROPHEN","stock",390); hp5(800,"ILFORD MICROPHEN","stock",480);
        hp5(1600,"ILFORD MICROPHEN","stock",660); hp5(3200,"ILFORD MICROPHEN","stock",960);
        hp5(400,"KODAK D-76","stock",450); hp5(800,"KODAK D-76","stock",570); hp5(1600,"KODAK D-76","stock",750);
        hp5(400,"KODAK D-76","1+1",660); hp5(800,"KODAK D-76","1+1",780);
        hp5(400,"KODAK D-76","1+3",1320);
        hp5(400,"AGFA RODINAL","1+25",360); hp5(800,"AGFA RODINAL","1+25",480);
        hp5(400,"AGFA RODINAL","1+50",660);
        hp5(400,"KODAK XTOL","stock",480); hp5(800,"KODAK XTOL","stock",660);
        hp5(1600,"KODAK XTOL","stock",840); hp5(3200,"KODAK XTOL","stock",1140);

        // KODAK TRI-X 400 official Rotary-Tube / continuous agitation tables.
        addTrixRotarySet(400,"KODAK T-MAX","stock", new int[]{405,360,345,330,285});
        addTrixRotarySet(400,"KODAK T-MAX RS","stock", new int[]{285,270,255,240,210});
        addTrixRotarySet(400,"KODAK HC-110","B", new int[]{270,225,210,180,150});
        addTrixRotarySet(400,"KODAK D-76","stock", new int[]{480,405,375,330,285});
        addTrixRotarySet(400,"KODAK D-76","1+1", new int[]{645,585,540,510,465});
        addTrixRotarySet(400,"KODAK XTOL","stock", new int[]{480,420,375,345,285});
        addTrixRotarySet(400,"KODAK XTOL","1+1", new int[]{600,540,510,480,435});

        addTrixRotarySet(1600,"KODAK T-MAX","stock", new int[]{570,525,495,465,420});
        addTrixRotarySet(1600,"KODAK T-MAX RS","stock", new int[]{510,465,435,405,360});
        addTrixRotarySet(1600,"KODAK HC-110","B", new int[]{420,360,330,300,255});
        addTrixRotarySet(1600,"KODAK D-76","stock", new int[]{675,570,525,465,390});
        addTrixRotarySet(1600,"KODAK D-76","1+1", new int[]{885,795,750,705,645});
        addTrixRotarySet(1600,"KODAK XTOL","stock", new int[]{675,585,525,480,405});
        addTrixRotarySet(1600,"KODAK XTOL","1+1", new int[]{870,795,735,690,630});

        addTrixRotarySetPartial(3200,"KODAK T-MAX RS","stock", new double[]{20,21,22,24}, new int[]{570,540,495,450});
        addTrixRotarySet(3200,"KODAK D-76","stock", new int[]{765,660,585,540,450});
        addTrixRotarySet(3200,"KODAK D-76","1+1", new int[]{1050,960,900,855,765});
        addTrixRotarySetPartial(3200,"KODAK XTOL","stock", new double[]{20,21,22,24}, new int[]{690,630,570,480});
        addTrixRotarySetPartial(3200,"KODAK XTOL","1+1", new double[]{20,21,22,24}, new int[]{930,870,825,735});
    }

    private DevelopmentCatalog() {}

    private static void addManual(String film, int ei, String dev, String dilution, int seconds, String source, String note) {
        RECIPES.add(new Recipe(film,ei,dev,dilution,20.0,seconds,seconds,MANUAL,source,note));
    }
    private static void addRange(String film, int ei, String dev, String dilution, int min, int max, String source, String note) {
        RECIPES.add(new Recipe(film,ei,dev,dilution,20.0,min,max,MANUAL,source,note));
    }
    private static void hp5(int ei, String dev, String dilution, int seconds) {
        addManual("ILFORD HP5 PLUS",ei,dev,dilution,seconds,SRC_ILFORD_HP5,formatTime(seconds)+" @20 °C — spiral tank");
    }
    private static void addTrixRotarySet(int ei, String dev, String dilution, int[] seconds) {
        double[] temps = {18,20,21,22,24};
        addTrixRotarySetPartial(ei,dev,dilution,temps,seconds);
    }
    private static void addTrixRotarySetPartial(int ei, String dev, String dilution, double[] temps, int[] seconds) {
        for (int i=0;i<temps.length;i++) {
            RECIPES.add(new Recipe("KODAK TRI-X 400",ei,dev,dilution,temps[i],seconds[i],seconds[i],ROTARY,
                    SRC_KODAK_TRIX,formatTime(seconds[i])+" @"+trimTemp(temps[i])+" °C — Rotary Tube / continuous agitation"));
        }
    }

    public static String[] filmNames() {
        String[] out = new String[FILMS.size()];
        for (int i=0;i<FILMS.size();i++) out[i] = FILMS.get(i).name;
        return out;
    }

    public static Film findFilm(String name) {
        if (name == null) return null;
        for (Film f : FILMS) if (f.name.equalsIgnoreCase(name.trim())) return f;
        return null;
    }

    public static String[] developerNames() {
        Set<String> names = new LinkedHashSet<>();
        for (Recipe r : RECIPES) names.add(r.developer);
        ArrayList<String> out = new ArrayList<>(names);
        Collections.sort(out);
        return out.toArray(new String[0]);
    }

    public static String[] developerDilutions(String developer) {
        LinkedHashSet<String> values = new LinkedHashSet<>();
        for (Recipe r : RECIPES) if (same(r.developer, developer)) values.add(r.dilution);
        return values.toArray(new String[0]);
    }

    public static String[] availableDilutions(String film, int ei, String developer) {
        LinkedHashSet<String> exact = new LinkedHashSet<>();
        LinkedHashSet<String> fallback = new LinkedHashSet<>();
        for (Recipe r : RECIPES) {
            if (!same(r.film,film) || !same(r.developer,developer)) continue;
            fallback.add(r.dilution);
            if (r.ei == ei) exact.add(r.dilution);
        }
        Set<String> selected = exact.isEmpty() ? fallback : exact;
        return selected.toArray(new String[0]);
    }

    public static Result calculate(String filmName, String format, int exposedIso, String developer, String dilution, double temperature) {
        Film film = findFilm(filmName);
        if (film == null) return Result.error("Seleziona una pellicola presente nel catalogo.");
        if (!("35 mm".equals(format) || "120".equals(format))) return Result.error("Formato non valido.");
        if ("35 mm".equals(format) && !film.format35) return Result.error("Questa pellicola non è disponibile in 35 mm nel profilo dati.");
        if ("120".equals(format) && !film.format120) return Result.error("Questa pellicola non è disponibile in 120 nel profilo dati.");
        if (exposedIso <= 0) return Result.error("ISO esposto non valido.");
        if (temperature < 16.0 || temperature > 26.0)
            return Result.error("Per la Release 2 l’adattamento affidabile è limitato a 16–26 °C.");

        ArrayList<Recipe> matches = new ArrayList<>();
        for (Recipe r : RECIPES) {
            if (same(r.film, film.name) && r.ei == exposedIso && same(r.developer,developer) && same(r.dilution,dilution))
                matches.add(r);
        }
        if (matches.isEmpty()) {
            return Result.error("Nessun tempo sorgente verificato per questa combinazione a ISO " + exposedIso
                    + ". Darkroom Assistant non inventa un tempo: prova un’altra diluizione/rivelatore oppure un EI documentato.");
        }

        Map<String,List<Recipe>> groups = new LinkedHashMap<>();
        for (Recipe r : matches) {
            String key = r.source + "|" + r.method;
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(r);
        }
        ArrayList<Candidate> candidates = new ArrayList<>();
        for (List<Recipe> group : groups.values()) {
            Candidate c = computeCandidate(group, temperature);
            if (c != null) candidates.add(c);
        }
        if (candidates.isEmpty()) return Result.error("Esistono dati sorgente, ma non un adattamento affidabile alla temperatura indicata.");
        candidates.sort((a,b) -> Integer.compare(b.score,a.score));
        Candidate best = candidates.get(0);

        StringBuilder alternatives = new StringBuilder();
        for (int i=1;i<candidates.size();i++) {
            Candidate c = candidates.get(i);
            if (alternatives.length() > 0) alternatives.append("\n\n");
            alternatives.append("• ").append(c.source).append(" — ").append(formatTime(c.seconds))
                    .append(c.adapted ? " (adattato)" : " (diretto)");
        }

        return new Result(true,"",film.name,format,film.nominalIso,exposedIso,developer,dilution,temperature,
                best.seconds,best.source,best.adapted ? "DATO ADATTATO / CALCOLATO" : "DATO DIRETTO",
                best.sourceData,best.calculation,alternatives.toString());
    }

    private static Candidate computeCandidate(List<Recipe> group, double temp) {
        if (group.isEmpty()) return null;
        Recipe first = group.get(0);
        if (ROTARY.equals(first.method)) return rotaryCandidate(group,temp);
        return manualCandidate(first,temp);
    }

    private static Candidate rotaryCandidate(List<Recipe> group, double temp) {
        Recipe first = group.get(0);
        group.sort(Comparator.comparingDouble(r -> r.tempC));
        for (Recipe r : group) {
            if (Math.abs(r.tempC-temp) < 0.051) {
                Candidate c = new Candidate();
                c.seconds = r.midpoint(); c.score = 1000; c.adapted = false; c.source = r.source;
                c.sourceData = r.sourceNote;
                c.calculation = "Dato già pubblicato per Rotary Tube / agitazione continua; usato direttamente nel profilo "
                        + PROCESSOR + " — " + PROCESS_METHOD + ".";
                return c;
            }
        }
        Recipe lo = null, hi = null;
        for (Recipe r : group) {
            if (r.tempC < temp) lo = r;
            if (r.tempC > temp) { hi = r; break; }
        }
        if (lo != null && hi != null) {
            double ratio = (temp-lo.tempC)/(hi.tempC-lo.tempC);
            int seconds = (int)Math.round(lo.midpoint() + ratio*(hi.midpoint()-lo.midpoint()));
            Candidate c = new Candidate();
            c.seconds = seconds; c.score = 950; c.adapted = true; c.source = first.source;
            c.sourceData = "Tabella rotary: " + trimTemp(lo.tempC) + " °C → " + formatTime(lo.midpoint())
                    + "; " + trimTemp(hi.tempC) + " °C → " + formatTime(hi.midpoint());
            c.calculation = "Interpolazione lineare fra due temperature pubblicate dalla stessa fonte; nessuna correzione di agitazione aggiuntiva.";
            return c;
        }
        Recipe at20 = null;
        for (Recipe r : group) if (Math.abs(r.tempC-20.0)<0.01) at20=r;
        if (at20 == null) return null;
        double factor = tempFactor(temp);
        if (Double.isNaN(factor)) return null;
        Candidate c = new Candidate();
        c.seconds = (int)Math.round(at20.midpoint()*factor); c.score = 900; c.adapted = true; c.source = first.source;
        c.sourceData = at20.sourceNote;
        c.calculation = "Temperatura fuori dai punti tabellati della fonte rotary: applicato fattore "
                + String.format(Locale.ITALY,"%.3f",factor) + " da " + TEMP_METHOD + ".";
        return c;
    }

    private static Candidate manualCandidate(Recipe r, double temp) {
        double factor = tempFactor(temp);
        if (Double.isNaN(factor)) return null;
        int base = r.midpoint();
        double tempAdjusted = base * factor;
        int finalSeconds = (int)Math.round(tempAdjusted * 0.85);
        Candidate c = new Candidate();
        c.seconds = finalSeconds;
        c.score = r.range() ? 710 : 760;
        c.adapted = true;
        c.source = r.source;
        c.sourceData = r.sourceNote + (r.range() ? " (punto medio usato: " + formatTime(base) + ")" : "");
        c.calculation = (r.range() ? "Intervallo fonte → punto medio; " : "")
                + "temperatura: fattore " + String.format(Locale.ITALY,"%.3f",factor) + " secondo " + TEMP_METHOD
                + "; rotazione continua: −15% come valore iniziale secondo " + ROTARY_METHOD
                + ". Risultato esplicitamente adattato, non pubblicato come tempo CPE2 dalla fonte.";
        return c;
    }

    private static double tempFactor(double t) {
        double[] temp = {16,18,20,22,24,26};
        double[] factor = {1.45,1.20,1.00,0.85,0.75,0.60};
        if (t < 16 || t > 26) return Double.NaN;
        for (int i=0;i<temp.length;i++) if (Math.abs(t-temp[i])<0.0001) return factor[i];
        for (int i=0;i<temp.length-1;i++) {
            if (t>temp[i] && t<temp[i+1]) {
                double x=(t-temp[i])/(temp[i+1]-temp[i]);
                return factor[i]+x*(factor[i+1]-factor[i]);
            }
        }
        return Double.NaN;
    }

    public static String formatTime(int seconds) {
        int m = seconds/60, s = seconds%60;
        if (m == 0) return s + " s";
        if (s == 0) return m + " min";
        return m + " min " + s + " s";
    }

    private static String trimTemp(double t) {
        if (Math.abs(t-Math.rint(t)) < 0.001) return Integer.toString((int)Math.rint(t));
        return String.format(Locale.ITALY,"%.1f",t);
    }
    private static boolean same(String a, String b) {
        return a != null && b != null && a.trim().equalsIgnoreCase(b.trim());
    }
}
