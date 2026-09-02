package it.darkroom.timer;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.Locale;

/** JOBO/LPL 7451 enlargement helper using the measured 67/73 cm column offset and a 6 mm easel. */
public final class EnlargementActivity extends Activity {
    static final String LPL_MODEL = "LPL7451";
    static final String[] NEGATIVE_CODES = {"35", "66", "45"};
    static final String[] NEGATIVE_CHOICES = {
            "35 mm · 24 × 36 mm · obiettivo 50 mm",
            "6×6 · 56 × 56 mm · obiettivo 75 mm",
            "4×5 · 101,6 × 127 mm · obiettivo 150 mm"
    };

    static final String[] PAPERS = {
            "8,9 × 12,7", "10,5 × 14,8", "12,7 × 17,8", "17,8 × 24,0", "20,3 × 25,4",
            "24,0 × 30,5", "27,9 × 35,6", "30,5 × 40,6", "40,6 × 50,8", "50,8 × 61,0", "PERSONALIZZATO"
    };
    static final double[][] PD = {
            {8.9, 12.7}, {10.5, 14.8}, {12.7, 17.8}, {17.8, 24.0}, {20.3, 25.4},
            {24.0, 30.5}, {27.9, 35.6}, {30.5, 40.6}, {40.6, 50.8}, {50.8, 61.0}
    };
    static final String[] FILLS = {"IMMAGINE INTERA", "RIEMPI LARGHEZZA", "RIEMPI ALTEZZA"};

    static final int BG = Color.BLACK;
    static final int PANEL = Color.rgb(24, 24, 24);
    static final int BUTTON = Color.rgb(55, 60, 64);
    static final int BORDER = Color.rgb(67, 67, 67);
    static final int MUTED = Color.rgb(170, 166, 162);
    static final int GREEN = Color.rgb(82, 190, 82);
    static final int TEXT = Color.rgb(246, 243, 238);

    SharedPreferences p;
    String mode;
    long originLogId;
    LogEntry originEntry;
    LinearLayout root;
    Spinner paper, fill, neg;
    EditText w, h;
    LinearLayout resultBox;
    Pending pending;

    static final class Pending {
        String negativeCode, crop, oldMeta, newMeta, note;
        double W, H, b1, b2, factor, stops, pw, ph, negativeToPaperCm, columnScale;
        int oldBase, newBase;
        ExposureRecipe oldRecipe, newRecipe;
        PrintSequence oldSequence, newSequence;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        p = getSharedPreferences("ui", MODE_PRIVATE);
        mode = getIntent().getStringExtra("mode");
        if (mode == null) mode = "setup";
        originLogId = getIntent().getLongExtra("originLogId", 0L);
        originEntry = originLogId > 0 ? findLogEntry(originLogId) : null;
        if ("resize".equals(mode) && originEntry != null && !hasUsableMeta(originEntry)) renderLegacyOrigin();
        else renderMain();
    }

    LogEntry findLogEntry(long id) {
        for (LogEntry e : LogStore.load(this)) if (e != null && e.id == id) return e;
        return null;
    }

    boolean hasUsableMeta(LogEntry e) {
        if (e == null || e.enlargementMeta == null || e.enlargementMeta.trim().isEmpty()) return false;
        if (!LPL_MODEL.equals(val(e.enlargementMeta, "enlarger"))) return false;
        double beta = num(e.enlargementMeta, "beta");
        return beta > 0.0 && !Double.isInfinite(beta) && !negativeFromEntry(e).isEmpty();
    }

    String negativeFromEntry(LogEntry e) {
        if (e == null) return "";
        String fromMeta = normalizeNegative(val(e.enlargementMeta, "neg"));
        if (!fromMeta.isEmpty()) return fromMeta;
        return normalizeNegative(e.negative);
    }

    String sourceNegative() {
        if (originEntry != null) {
            String n = negativeFromEntry(originEntry);
            if (!n.isEmpty()) return n;
        }
        return normalizeNegative(val(sourceMeta(), "neg"));
    }

    String sourceMeta() {
        return originEntry != null ? (originEntry.enlargementMeta == null ? "" : originEntry.enlargementMeta) : p.getString("enlargementMeta", "");
    }

    String sourceRecipe() {
        return originEntry != null ? (originEntry.recipeState == null ? "" : originEntry.recipeState) : p.getString("exposureRecipe", "");
    }

    String sourceSequence() {
        return originEntry != null ? (originEntry.printSequence == null ? "" : originEntry.printSequence) : p.getString("printSequence", "");
    }

    int sourceBase() {
        ExposureRecipe r = ExposureRecipe.decode(sourceRecipe());
        if (r != null && r.operationalBaseMs > 0) return r.operationalBaseMs;
        if (originEntry != null && originEntry.exposureMs > 0) return originEntry.exposureMs;
        return p.getInt("printWidthMs", 8500);
    }

    void renderMain() {
        boolean resize = "resize".equals(mode);
        begin(resize ? "RIDIMENSIONA STAMPA · JOBO/LPL 7451" : "IMPOSTA INGRANDIMENTO · JOBO/LPL 7451",
                resize ? "Trasforma una stampa mantenendo ricetta, filtri e rapporti temporali."
                        : "Scegli il formato: obiettivo e portanegativi vengono associati automaticamente.");
        addCalibrationNotice();
        if (resize) {
            String format = sourceNegative();
            String sm = sourceMeta();
            if (format.isEmpty() || Double.isNaN(num(sm, "beta"))) {
                info("Mancano i dati necessari della stampa origine.");
                return;
            }
            root.addView(section("ORIGINE", originSummary(sm, format)));
            addFixedNegative(format);
            addPaperFields(sm);
            fill = spinner(FILLS);
            int fi = intVal(sm, "fill", 0);
            fill.setSelection(Math.max(0, Math.min(2, fi)));
            root.addView(label("MODALITÀ FINALE", 12, MUTED, true));
            root.addView(fill, lp(-1, dp(50)));
            Button calc = button("CALCOLA", BUTTON);
            calc.setOnClickListener(v -> calculateResize(format));
            root.addView(calc, margin(lp(-1, dp(52)), 0, dp(12), 0, dp(10)));
            resultBox = new LinearLayout(this);
            resultBox.setOrientation(LinearLayout.VERTICAL);
            root.addView(resultBox, lp(-1, -2));
        } else {
            neg = spinner(NEGATIVE_CHOICES);
            neg.setSelection(Math.max(0, Math.min(2, p.getInt("enlargementUiNeg", 0))));
            root.addView(label("NEGATIVO · OBIETTIVO AUTOMATICO", 12, MUTED, true));
            root.addView(neg, lp(-1, dp(50)));
            addPaperFields(p.getString("enlargementMeta", ""));
            fill = spinner(FILLS);
            fill.setSelection(Math.max(0, Math.min(2, p.getInt("enlargementUiFill", 0))));
            root.addView(label("MODALITÀ", 12, MUTED, true));
            root.addView(fill, lp(-1, dp(50)));
            Button calc = button("CALCOLA", BUTTON);
            calc.setOnClickListener(v -> calculateSetup());
            root.addView(calc, margin(lp(-1, dp(52)), 0, dp(12), 0, dp(10)));
            resultBox = new LinearLayout(this);
            resultBox.setOrientation(LinearLayout.VERTICAL);
            root.addView(resultBox, lp(-1, -2));
        }
    }

    void addCalibrationNotice() {
        root.addView(section("CONFIGURAZIONE ATTIVA",
                "JOBO/LPL 7451 calibrato con misura meccanica: scala 67, piano negativo–base 73 cm, marginatore 6 mm. "
                        + "La distanza negativo–carta è scala + 5,4 cm; il valore calcolato è il punto iniziale per la messa a fuoco fine."));
    }

    void renderLegacyOrigin() {
        begin("RIDIMENSIONA STAMPA · JOBO/LPL 7451",
                "Questa scheda non contiene ancora dati LPL compatibili. Registrali una sola volta.");
        addCalibrationNotice();
        String format = negativeFromEntry(originEntry);
        if (format.isEmpty()) {
            info("Completa prima il campo NEGATIVO della scheda LOG (35 mm, 6×6 oppure 4×5), poi riprova.");
            return;
        }
        addFixedNegative(format);
        root.addView(label("FORMATO ORIGINALE DELLA STAMPA", 13, TEXT, true));
        addPaperFields("");
        fill = spinner(FILLS);
        root.addView(label("MODALITÀ ORIGINALE", 12, MUTED, true));
        root.addView(fill, lp(-1, dp(50)));
        Button save = button("SALVA E CONTINUA", GREEN);
        save.setTextColor(Color.BLACK);
        save.setOnClickListener(v -> saveLegacyAndContinue(format));
        root.addView(save, margin(lp(-1, dp(54)), 0, dp(14), 0, 0));
    }

    void saveLegacyAndContinue(String format) {
        try {
            Dims d = readDims();
            Calc c = calc(format, d.W, d.H, fill.getSelectedItemPosition());
            String meta = buildMeta(format, d.W, d.H, fill.getSelectedItemPosition(), c.beta, c.pw, c.ph, c.crop, 0L, "");
            originEntry.enlargementMeta = meta;
            syncLogDisplayFields(originEntry, meta);
            LogStore.save(this, originEntry);
            Toast.makeText(this, "Dati JOBO/LPL 7451 registrati nel LOG", Toast.LENGTH_SHORT).show();
            renderMain();
        } catch (Exception e) {
            info("Inserisci dimensioni carta valide.");
        }
    }

    void calculateSetup() {
        try {
            clearResult();
            String format = NEGATIVE_CODES[neg.getSelectedItemPosition()];
            Dims d = readDims();
            Calc c = calc(format, d.W, d.H, fill.getSelectedItemPosition());
            String meta = buildMeta(format, d.W, d.H, fill.getSelectedItemPosition(), c.beta, c.pw, c.ph, c.crop, 0L, "");
            p.edit().putString("enlargementMeta", meta)
                    .putString("enlargementLastLog", "IMPOSTA INGRANDIMENTO · " + meta)
                    .putInt("enlargementUiNeg", neg.getSelectedItemPosition())
                    .putInt("enlargementUiFill", fill.getSelectedItemPosition()).apply();
            resultBox.addView(section("RISULTATO", resultText(c, format)));
            TextView ok = label("Registrato nella ricetta corrente.", 13, GREEN, true);
            ok.setGravity(Gravity.CENTER);
            resultBox.addView(ok, margin(lp(-1, -2), 0, dp(8), 0, 0));
            Button close = button("CHIUDI", BUTTON);
            close.setOnClickListener(v -> finish());
            resultBox.addView(close, margin(lp(-1, dp(50)), 0, dp(12), 0, dp(4)));
        } catch (Exception e) {
            clearResult();
            infoInto(resultBox, "Inserisci dimensioni carta valide.");
        }
    }

    void calculateResize(String format) {
        try {
            clearResult();
            Dims d = readDims();
            Calc c = calc(format, d.W, d.H, fill.getSelectedItemPosition());
            String old = sourceMeta();
            double b1 = num(old, "beta");
            if (Double.isNaN(b1) || b1 <= 0.0) {
                if (originEntry != null) {
                    renderLegacyOrigin();
                    return;
                }
                infoInto(resultBox, "Mancano i dati dell’ingrandimento iniziale.");
                return;
            }
            double factor = Math.pow((c.beta+1)/(b1+1),2);
            double stops = Math.log(factor) / Math.log(2);
            int oldBase = sourceBase();
            int newBase = snap(oldBase * factor);
            ExposureRecipe oldR = sourceRecipeForResize(oldBase);
            ExposureRecipe newR = scaleRecipe(oldR, oldBase, factor);
            PrintSequence oldQ = PrintSequence.decode(sourceSequence());
            PrintSequence newQ = scaleSequence(oldQ, factor);
            String from = paperDisplay(old);
            String to = paperDisplay(d.W, d.H);
            String note = "Derivata da " + from + " → " + to;
            String nm = buildMeta(format, d.W, d.H, fill.getSelectedItemPosition(), c.beta, c.pw, c.ph, c.crop, originLogId, from);
            Pending x = new Pending();
            x.negativeCode = format;
            x.W = d.W;
            x.H = d.H;
            x.b1 = b1;
            x.b2 = c.beta;
            x.factor = factor;
            x.stops = stops;
            x.pw = c.pw;
            x.ph = c.ph;
            x.negativeToPaperCm = c.negativeToPaperCm;
            x.columnScale = c.columnScale;
            x.crop = c.crop;
            x.oldMeta = old;
            x.newMeta = nm;
            x.note = note;
            x.oldBase = oldBase;
            x.newBase = newBase;
            x.oldRecipe = oldR;
            x.newRecipe = newR;
            x.oldSequence = oldQ;
            x.newSequence = newQ;
            showPending(x);
        } catch (Exception e) {
            clearResult();
            infoInto(resultBox, "Inserisci dimensioni carta valide.");
        }
    }

    void showPending(Pending x) {
        clearResult();
        pending = x;
        resultBox.addView(section("RISULTATO",
                String.format(Locale.ITALY,
                        "%s · obiettivo %d mm\n%s\nβ finale %.3f\nImmagine proiettata %.1f × %.1f cm\nCrop: %s\nDistanza negativo–carta %.1f cm\nScala colonna LPL %.1f",
                        formatLabel(x.negativeCode), lensMm(x.negativeCode), carrierLabel(x.negativeCode),
                        x.b2, x.pw, x.ph, cropLabel(x.crop), x.negativeToPaperCm, x.columnScale)));
        StringBuilder comp = new StringBuilder();
        comp.append(String.format(Locale.ITALY,
                "β %.3f → %.3f\nFattore ×%.2f\nVariazione %+.2f stop\nTempo base %.1f s → %.1f s",
                x.b1, x.b2, x.factor, x.stops, x.oldBase / 1000.0, x.newBase / 1000.0));
        String timed = timedChanges(x);
        if (!timed.isEmpty()) comp.append('\n').append(timed);
        resultBox.addView(section("COMPENSAZIONE", comp.toString()));
        Button create = button("CREA", GREEN);
        create.setTextColor(Color.BLACK);
        create.setOnClickListener(v -> {
            v.setEnabled(false);
            createDerived(x);
        });
        Button cancel = button("ANNULLA", BUTTON);
        cancel.setOnClickListener(v -> {
            pending = null;
            clearResult();
        });
        resultBox.addView(create, margin(lp(-1, dp(54)), 0, dp(12), 0, 0));
        resultBox.addView(cancel, margin(lp(-1, dp(48)), 0, dp(8), 0, dp(14)));
    }

    String timedChanges(Pending x) {
        StringBuilder b = new StringBuilder();
        if (x.oldSequence.hasSplit() && x.newSequence.hasSplit()) {
            b.append(String.format(Locale.ITALY, "Split Grade morbido %.1f s → %.1f s",
                    x.oldSequence.split.softMs / 1000.0, x.newSequence.split.softMs / 1000.0));
            b.append(String.format(Locale.ITALY, "\nSplit Grade duro %.1f s → %.1f s",
                    x.oldSequence.split.hardMs / 1000.0, x.newSequence.split.hardMs / 1000.0));
        }
        int n = Math.min(x.oldSequence.corrections.size(), x.newSequence.corrections.size());
        for (int i = 0; i < n; i++) {
            PrintCorrection o = x.oldSequence.corrections.get(i);
            PrintCorrection nn = x.newSequence.corrections.get(i);
            if (o == null || nn == null) continue;
            int ob = x.oldSequence.baseMsFor(o, x.oldBase);
            int nb = x.newSequence.baseMsFor(nn, x.newBase);
            int om = o.resolvedMs(ob);
            int nm = nn.resolvedMs(nb);
            if (b.length() > 0) b.append('\n');
            b.append(o.isDodge() ? "Dodge · " : "Burn · ").append(o.safeLabel())
                    .append(String.format(Locale.ITALY, " %.1f s → %.1f s", om / 1000.0, nm / 1000.0));
        }
        return b.toString();
    }

    ExposureRecipe sourceRecipeForResize(int base) {
        ExposureRecipe r = ExposureRecipe.decode(sourceRecipe());
        if (r.hasBase()) return r;
        r.originalBaseMs = base;
        r.operationalBaseMs = base;
        r.baseChosenAt = System.currentTimeMillis();
        if (originEntry != null) {
            String ft = ExposureRecipe.normalizeFilter(originEntry.testBaseFilterType);
            int fv = ExposureRecipe.snap5(originEntry.testBaseFilterValue);
            if (!ExposureRecipe.FILTER_NONE.equals(ft)) {
                r.filterType = ft;
                r.filterValue = fv;
            } else {
                int m = parseFilterNumber(originEntry.magenta);
                int y = parseFilterNumber(originEntry.yellow);
                if (m > 0 && y <= 0) {
                    r.filterType = ExposureRecipe.FILTER_MAGENTA;
                    r.filterValue = ExposureRecipe.snap5(m);
                } else if (y > 0 && m <= 0) {
                    r.filterType = ExposureRecipe.FILTER_YELLOW;
                    r.filterValue = ExposureRecipe.snap5(y);
                }
            }
            int dq = parseDensityQuarterSteps(originEntry.density);
            if (dq >= 0) r.densityQuarterSteps = dq;
        }
        return r;
    }

    int parseFilterNumber(String value) {
        if (value == null) return 0;
        try {
            return (int) Math.round(Double.parseDouble(value.trim().replace(',', '.')));
        } catch (Exception e) {
            return 0;
        }
    }

    int parseDensityQuarterSteps(String value) {
        if (value == null || value.trim().isEmpty()) return -1;
        String v = value.trim().toUpperCase(Locale.ITALY).replace("D", "").replace(',', '.');
        try {
            double density = Double.parseDouble(v);
            if (density <= 8 && !value.toUpperCase(Locale.ITALY).contains("D"))
                return ExposureRecipe.clampDensity((int) Math.round(density));
            return ExposureRecipe.clampDensity((int) Math.round(density / 7.5));
        } catch (Exception e) {
            return -1;
        }
    }

    ExposureRecipe scaleRecipe(ExposureRecipe r, int oldBase, double factor) {
        if (r == null) r = new ExposureRecipe();
        ExposureRecipe n = ExposureRecipe.decode(r.encode());
        if (n.originalBaseMs > 0) n.originalBaseMs = snap(n.originalBaseMs * factor);
        n.operationalBaseMs = snap((n.operationalBaseMs > 0 ? n.operationalBaseMs : oldBase) * factor);
        n.baseChosenAt = System.currentTimeMillis();
        return n;
    }

    PrintSequence scaleSequence(PrintSequence q, double factor) {
        PrintSequence n = PrintSequence.decode(q == null ? "" : q.encode());
        if (n.hasSplit()) {
            n.split.softMs = snap(n.split.softMs * factor);
            n.split.hardMs = snap(n.split.hardMs * factor);
            n.split.sanitize();
        }
        for (PrintCorrection c : n.corrections) if (c != null && c.milliseconds > 0) c.milliseconds = snap(c.milliseconds * factor);
        return n;
    }

    void createDerived(Pending x) {
        p.edit().putString("exposureRecipe", x.newRecipe.encode())
                .putString("printSequence", x.newSequence.encode())
                .putInt("printWidthMs", x.newBase)
                .putString("enlargementMeta", x.newMeta)
                .putString("enlargementLastLog", x.note)
                .putInt("enlargementUiNeg", formatIndex(x.negativeCode))
                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(x.newRecipe.filterType))
                .putInt("testBaseFilterValue", ExposureRecipe.snap5(x.newRecipe.filterValue))
                .putInt("mode", 0)
                .putBoolean("enlargementReloadPending", true).apply();
        saveDerivedLog(x);
        Toast.makeText(this, "Stampa ridimensionata · tempi a 0,5 s", Toast.LENGTH_LONG).show();
        finish();
    }

    void syncLogDisplayFields(LogEntry entry, String meta) {
        if (entry == null || meta == null || meta.trim().isEmpty()) return;
        String format = normalizeNegative(val(meta, "neg"));
        if (!format.isEmpty()) entry.negative = logNegative(format);
        entry.columnHeight = "";
        String paperValue = val(meta, "paper");
        if (!paperValue.isEmpty()) {
            String display = paperValue.replace('.', ',').replace("x", " × ") + " cm";
            String current = entry.paper == null ? "" : entry.paper.trim();
            if (current.isEmpty()) entry.paper = display;
            else if (!current.contains(display) && !current.contains(paperValue)) entry.paper = current + " · " + display;
        }
    }

    void saveDerivedLog(Pending x) {
        long now = System.currentTimeMillis();
        LogEntry d = new LogEntry();
        if (originEntry != null) {
            d.title = originEntry.title;
            d.negative = originEntry.negative;
            d.aperture = originEntry.aperture;
            d.magenta = originEntry.magenta;
            d.yellow = originEntry.yellow;
            d.density = originEntry.density;
            d.paper = originEntry.paper;
            d.notes = originEntry.notes;
            d.exposureMethod = originEntry.exposureMethod;
            d.exposureStep = originEntry.exposureStep;
            d.testMs = originEntry.testMs;
            d.testCount = originEntry.testCount;
            d.testMethod = originEntry.testMethod;
            d.testStep = originEntry.testStep;
            d.testStripTimes = originEntry.testStripTimes;
            d.testBaseFilterType = originEntry.testBaseFilterType;
            d.testBaseFilterValue = originEntry.testBaseFilterValue;
        } else {
            d.title = "Stampa ridimensionata";
            d.negative = logNegative(x.negativeCode);
            d.paper = "Fomaspeed Variant 311 RC lucida";
            d.exposureMethod = TimingMath.normalizeMethod(p.getString("timingMethod", TimingMath.METHOD_SECONDS));
            d.exposureStep = TimingMath.stepLabel(d.exposureMethod);
            d.testBaseFilterType = ExposureRecipe.normalizeFilter(x.newRecipe.filterType);
            d.testBaseFilterValue = ExposureRecipe.snap5(x.newRecipe.filterValue);
            if (ExposureRecipe.FILTER_MAGENTA.equals(x.newRecipe.filterType)) d.magenta = String.valueOf(x.newRecipe.filterValue);
            if (ExposureRecipe.FILTER_YELLOW.equals(x.newRecipe.filterType)) d.yellow = String.valueOf(x.newRecipe.filterValue);
            d.density = x.newRecipe.densityLabel();
        }
        d.id = now;
        d.timestamp = now;
        d.favorite = false;
        d.columnHeight = "";
        d.exposureMs = x.newSequence.hasSplit() ? x.newSequence.split.totalMs() : x.newBase;
        d.printSequence = x.newSequence.encode();
        d.recipeState = x.newRecipe.encode();
        d.enlargementMeta = x.newMeta;
        syncLogDisplayFields(d, x.newMeta);
        String oldNotes = d.notes == null ? "" : d.notes.trim();
        d.notes = oldNotes.isEmpty() ? x.note : (oldNotes + " · " + x.note);
        LogStore.save(this, d);
    }

    void addFixedNegative(String format) {
        root.addView(label("NEGATIVO / OBIETTIVO / PORTANEGATIVI", 12, MUTED, true));
        String body = formatLabel(format) + " · negativo " + negativeSizeLabel(format)
                + "\nObiettivo automatico " + lensMm(format) + " mm"
                + "\n" + carrierLabel(format);
        TextView fixed = label(body, 15, TEXT, true);
        fixed.setPadding(dp(13), dp(12), dp(13), dp(12));
        fixed.setBackground(bg(PANEL, 10, BORDER, 1));
        root.addView(fixed, margin(lp(-1, -2), 0, 0, 0, dp(10)));
    }

    void addPaperFields(String meta) {
        paper = spinner(PAPERS);
        w = input("Larghezza carta cm");
        h = input("Altezza carta cm");
        root.addView(label("FORMATO CARTA FOMA", 12, MUTED, true));
        root.addView(paper, lp(-1, dp(50)));
        root.addView(label("LARGHEZZA CARTA (cm)", 12, MUTED, true));
        root.addView(w, lp(-1, dp(50)));
        root.addView(label("ALTEZZA CARTA (cm)", 12, MUTED, true));
        root.addView(h, lp(-1, dp(50)));
        TextView landscape = label("ORIENTAMENTO · ORIZZONTALE", 12, MUTED, true);
        root.addView(landscape, margin(lp(-1, -2), 0, dp(5), 0, dp(10)));
        paper.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onNothingSelected(AdapterView<?> a) {}
            public void onItemSelected(AdapterView<?> a, View v, int pos, long id) {
                if (pos < PD.length) {
                    w.setText(fmt(Math.max(PD[pos][0], PD[pos][1])));
                    h.setText(fmt(Math.min(PD[pos][0], PD[pos][1])));
                    w.setEnabled(false);
                    h.setEnabled(false);
                } else {
                    w.setEnabled(true);
                    h.setEnabled(true);
                }
            }
        });
        double[] dims = metaDims(meta);
        int pi = presetIndex(dims[0], dims[1]);
        if (pi >= 0) paper.setSelection(pi);
        else if (dims[0] > 0 && dims[1] > 0) {
            paper.setSelection(PAPERS.length - 1);
            w.setText(fmt(Math.max(dims[0], dims[1])));
            h.setText(fmt(Math.min(dims[0], dims[1])));
        } else paper.setSelection(2);
    }

    static final class Dims {
        double W, H;
        Dims(double W, double H) { this.W = W; this.H = H; }
    }

    static final class Calc {
        double beta, pw, ph, negativeToPaperCm, columnScale;
        String crop;
    }

    Dims readDims() {
        double aw = Double.parseDouble(w.getText().toString().replace(',', '.')) * 10;
        double ah = Double.parseDouble(h.getText().toString().replace(',', '.')) * 10;
        if (!(aw > 0.0) || !(ah > 0.0)) throw new IllegalArgumentException("invalid paper size");
        return new Dims(Math.max(aw, ah), Math.min(aw, ah));
    }

    Calc calc(String format, double W, double H, int fillIndex) {
        double nw = negativeWidthMm(format);
        double nh = negativeHeightMm(format);
        double beta = fillIndex == 1 ? W / nw : fillIndex == 2 ? H / nh : Math.min(W / nw, H / nh);
        if (!(beta > 0.0) || Double.isInfinite(beta)) throw new IllegalArgumentException("invalid beta");
        Calc c = new Calc();
        c.beta = beta;
        c.pw = beta * nw / 10.0;
        c.ph = beta * nh / 10.0;
        c.negativeToPaperCm = Lpl7451Geometry.negativeToPaperCm(beta, lensMm(format));
        c.columnScale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        c.crop = (c.pw > W / 10.0 + .001 || c.ph > H / 10.0 + .001) ? "SI" : "NO";
        return c;
    }

    String buildMeta(String format, double W, double H, int fillIndex, double beta,
                     double pw, double ph, String crop, long sourceId, String from) {
        double negativeToPaperCm = Lpl7451Geometry.negativeToPaperCm(beta, lensMm(format));
        double columnScale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        String base = String.format(Locale.US,
                "enlarger=LPL7451|neg=%s|negativeMm=%s|lens=%d|carrier=%s|paper=%.1fx%.1f|w=%.1f|h=%.1f|orientation=LANDSCAPE|fill=%d|beta=%.8f|proj=%.2fx%.2f|crop=%s|columnCalibration=MEASURED_67_73_6MM|columnScale=%.2f|negativePaperCm=%.2f|scaleOffsetCm=5.40|easelHeightMm=6.0",
                format, negativeSizeMeta(format), lensMm(format), carrierCode(format),
                W / 10.0, H / 10.0, W / 10.0, H / 10.0, fillIndex, beta, pw, ph, crop,
                columnScale, negativeToPaperCm);
        if (sourceId > 0) base += "|sourceId=" + sourceId;
        if (from != null && !from.isEmpty()) base += "|derivedFrom=" + from.replace(" × ", "x").replace(',', '.');
        return base;
    }

    String resultText(Calc c, String format) {
        return String.format(Locale.ITALY,
                "%s · negativo %s\nObiettivo automatico %d mm\n%s\nβ %.3f\nImmagine proiettata %.1f × %.1f cm\nCrop: %s\nDistanza negativo–carta %.1f cm\nScala colonna LPL %.1f",
                formatLabel(format), negativeSizeLabel(format), lensMm(format), carrierLabel(format),
                c.beta, c.pw, c.ph, cropLabel(c.crop), c.negativeToPaperCm, c.columnScale);
    }

    String originSummary(String meta, String format) {
        double beta = num(meta, "beta");
        double scale = num(meta, "columnScale");
        if (Double.isNaN(scale) && beta > 0.0) scale = Lpl7451Geometry.scaleFor(beta, lensMm(format));
        return paperDisplay(meta) + " · " + formatLabel(format) + " / " + lensMm(format) + " mm"
                + "\n" + carrierLabel(format)
                + String.format(Locale.ITALY, "\nβ %.3f · scala LPL %.1f", beta, scale);
    }

    String paperDisplay(String meta) {
        double[] d = metaDims(meta);
        return paperDisplay(d[0] * 10, d[1] * 10);
    }

    String paperDisplay(double W, double H) {
        if (W <= 0 || H <= 0) return "formato non registrato";
        double wcm = W / 10, hcm = H / 10;
        return String.format(Locale.ITALY, "%.1f×%.1f", Math.min(wcm, hcm), Math.max(wcm, hcm));
    }

    double[] metaDims(String meta) {
        double ww = num(meta, "w"), hh = num(meta, "h");
        if (!Double.isNaN(ww) && !Double.isNaN(hh)) return new double[]{ww, hh};
        String pp = val(meta, "paper");
        try {
            String[] x = pp.split("x");
            if (x.length == 2) return new double[]{Double.parseDouble(x[0]), Double.parseDouble(x[1])};
        } catch (Exception ignored) {}
        return new double[]{-1, -1};
    }

    int presetIndex(double a, double b) {
        if (a <= 0 || b <= 0) return -1;
        double hi = Math.max(a, b), lo = Math.min(a, b);
        for (int i = 0; i < PD.length; i++) {
            double ph = Math.max(PD[i][0], PD[i][1]), pl = Math.min(PD[i][0], PD[i][1]);
            if (Math.abs(ph - hi) < .06 && Math.abs(pl - lo) < .06) return i;
        }
        return -1;
    }

    void begin(String title, String subtitle) {
        ScrollView sc = new ScrollView(this);
        sc.setFillViewport(true);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(14), dp(18), dp(30));
        root.setBackgroundColor(BG);
        sc.addView(root, new ScrollView.LayoutParams(-1, -2));
        if ("resize".equals(mode)) {
            Button back = button("←  INDIETRO", BUTTON);
            back.setOnClickListener(v -> finish());
            root.addView(back, lp(-1, dp(46)));
        }
        TextView heading = label(title, 24, TEXT, true);
        heading.setGravity(Gravity.CENTER);
        root.addView(heading, margin(lp(-1, -2), 0, dp(10), 0, dp(3)));
        TextView sub = label(subtitle, 12, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        root.addView(sub, margin(lp(-1, -2), 0, 0, 0, dp(16)));
        setContentView(sc);
    }

    LinearLayout section(String title, String body) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(0, dp(8), 0, dp(8));
        box.addView(label(title, 12, MUTED, true));
        TextView v = label(body, 15, TEXT, false);
        v.setLineSpacing(0, 1.12f);
        v.setPadding(0, dp(5), 0, 0);
        box.addView(v);
        return box;
    }

    void info(String x) {
        TextView v = label(x, 14, Color.rgb(230, 196, 150), false);
        v.setGravity(Gravity.CENTER);
        root.addView(v, margin(lp(-1, -2), 0, dp(18), 0, 0));
    }

    void infoInto(LinearLayout parent, String x) {
        TextView v = label(x, 14, Color.rgb(230, 196, 150), false);
        v.setGravity(Gravity.CENTER);
        parent.addView(v, margin(lp(-1, -2), 0, dp(10), 0, 0));
    }

    void clearResult() {
        pending = null;
        if (resultBox != null) resultBox.removeAllViews();
    }

    EditText input(String hint) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setTextColor(TEXT);
        e.setHintTextColor(MUTED);
        e.setTextSize(15);
        e.setInputType(2 | 8192);
        e.setPadding(dp(13), 0, dp(13), 0);
        e.setBackground(bg(PANEL, 10, BORDER, 1));
        return e;
    }

    Spinner spinner(String[] items) {
        Spinner sp = new Spinner(this);
        ArrayAdapter<String> a = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, items) {
            @Override public View getView(int pos, View cv, ViewGroup parent) {
                TextView t = (TextView) super.getView(pos, cv, parent);
                t.setTextColor(TEXT);
                t.setTextSize(15);
                t.setPadding(dp(10), dp(9), dp(10), dp(9));
                return t;
            }
            @Override public View getDropDownView(int pos, View cv, ViewGroup parent) {
                TextView t = (TextView) super.getDropDownView(pos, cv, parent);
                t.setTextColor(Color.WHITE);
                t.setBackgroundColor(Color.rgb(38, 38, 38));
                t.setPadding(dp(12), dp(12), dp(12), dp(12));
                return t;
            }
        };
        a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        sp.setAdapter(a);
        sp.setBackground(bg(PANEL, 10, BORDER, 1));
        return sp;
    }

    Button button(String text, int color) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        b.setTextColor(TEXT);
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setBackground(bg(color, 10, BORDER, 1));
        return b;
    }

    TextView label(String x, float z, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(x);
        v.setTextSize(z);
        v.setTextColor(color);
        v.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL);
        return v;
    }

    GradientDrawable bg(int c, int r, int stroke, int sw) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(c);
        g.setCornerRadius(dp(r));
        if (sw > 0) g.setStroke(dp(sw), stroke);
        return g;
    }

    LinearLayout.LayoutParams lp(int width, int height) { return new LinearLayout.LayoutParams(width, height); }
    LinearLayout.LayoutParams margin(LinearLayout.LayoutParams x, int l, int t, int r, int b) {
        x.setMargins(dp(l), dp(t), dp(r), dp(b));
        return x;
    }
    int dp(int v) { return (int) (v * getResources().getDisplayMetrics().density + .5f); }

    static String normalizeNegative(String raw) {
        String n = raw == null ? "" : raw.trim().toLowerCase(Locale.ITALY)
                .replace(" ", "").replace("×", "x").replace("mm", "");
        if (n.equals("35") || n.equals("24x36") || n.equals("36x24")) return "35";
        if (n.equals("66") || n.equals("6x6") || n.equals("56x56")) return "66";
        if (n.equals("45") || n.equals("4x5") || n.equals("101,6x127") || n.equals("101.6x127") || n.equals("127x101,6") || n.equals("127x101.6")) return "45";
        return "";
    }

    static int formatIndex(String format) { return "66".equals(format) ? 1 : "45".equals(format) ? 2 : 0; }
    static String formatLabel(String format) { return "66".equals(format) ? "6×6" : "45".equals(format) ? "4×5" : "35 mm"; }
    static String logNegative(String format) { return "66".equals(format) ? "6x6" : "45".equals(format) ? "4x5" : "35mm"; }
    static int lensMm(String format) { return "66".equals(format) ? 75 : "45".equals(format) ? 150 : 50; }
    static double negativeWidthMm(String format) { return "66".equals(format) ? 56.0 : "45".equals(format) ? 127.0 : 36.0; }
    static double negativeHeightMm(String format) { return "66".equals(format) ? 56.0 : "45".equals(format) ? 101.6 : 24.0; }
    static String negativeSizeLabel(String format) { return "66".equals(format) ? "56×56 mm" : "45".equals(format) ? "101,6×127 mm" : "24×36 mm"; }
    static String negativeSizeMeta(String format) { return "66".equals(format) ? "56x56" : "45".equals(format) ? "101.6x127" : "24x36"; }
    static String carrierCode(String format) { return "66".equals(format) ? "6x6" : "45".equals(format) ? "4x5" : "35mm"; }
    static String carrierLabel(String format) { return "Portanegativi " + formatLabel(format) + " (" + negativeSizeLabel(format) + ")"; }
    static int snap(double ms) { return (int) Math.round(ms / 500.0) * 500; }
    static String val(String m, String k) {
        if (m == null) return "";
        for (String x : m.split("\\|")) if (x.startsWith(k + "=")) return x.substring(k.length() + 1);
        return "";
    }
    static double num(String m, String k) {
        try { return Double.parseDouble(val(m, k)); }
        catch (Exception e) { return Double.NaN; }
    }
    static int intVal(String m, String k, int fallback) {
        try { return Integer.parseInt(val(m, k)); }
        catch (Exception e) { return fallback; }
    }
    static String fmt(double x) { return String.format(Locale.ITALY, "%.1f", x); }
    static String cropLabel(String c) { return "SI".equals(c) ? "SÌ" : "NO"; }
}
