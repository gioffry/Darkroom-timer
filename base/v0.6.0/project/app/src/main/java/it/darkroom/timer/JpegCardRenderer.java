package it.darkroom.timer;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Renders a vertical 9:16 archival-style technical print sheet as a JPG-ready bitmap. */
public final class JpegCardRenderer {
    public static final int MAX_NOTES_CHARS = 84;
    public static final int WIDTH = 1080;
    public static final int HEIGHT = 1920;

    private static final int PAPER = Color.rgb(245, 238, 220);
    private static final int INK = Color.rgb(47, 39, 31);
    private static final int ACCENT = Color.rgb(126, 44, 31);
    private static final int RULE = Color.rgb(105, 94, 78);

    private JpegCardRenderer() {}

    public static Bitmap render(LogEntry e, String version) {
        Bitmap b = Bitmap.createBitmap(WIDTH, HEIGHT, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        c.drawColor(PAPER);

        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(4f);
        p.setColor(INK);
        c.drawRoundRect(new RectF(24, 24, WIDTH - 24, HEIGHT - 24), 32, 32, p);
        p.setStrokeWidth(1.6f);
        c.drawRoundRect(new RectF(40, 40, WIDTH - 40, HEIGHT - 40), 26, 26, p);

        drawEnlargerBadge(c, 128, 145, 76);

        p.setStyle(Paint.Style.FILL);
        p.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(48);
        p.setColor(INK);
        c.drawText("SCHEDA TECNICA", 550, 118, p);
        c.drawText("DI STAMPA", 550, 174, p);
        p.setTextSize(24);
        p.setColor(ACCENT);
        c.drawText("REGISTRO DI CAMERA OSCURA", 550, 220, p);

        drawDateBox(c, e.timestamp);

        p.setColor(ACCENT);
        p.setStrokeWidth(2f);
        c.drawLine(355, 255, 485, 255, p);
        c.drawCircle(540, 255, 6, p);
        c.drawLine(595, 255, 725, 255, p);

        float top = 310f;
        float rowH = 104f;
        float labelDividerX = 354f;
        float valueStartX = 392f;
        String[] labels = {
                "Titolo", "Negativo", "Diaframma", "Altezza colonna", "Magenta", "Yellow",
                "Densità", "Esposizione finale", "Provino", "N. esposizioni provino", "Carta"
        };
        String[] values = {
                text(e.title, "—"),
                negativeLabel(e.negative),
                apertureLabel(e.aperture),
                unitLabel(e.columnHeight, "cm"),
                text(e.magenta, "0"),
                text(e.yellow, "0"),
                text(e.density, "0"),
                seconds(e.exposureMs),
                e.testMs > 0 ? seconds(e.testMs) + " per striscia" : "—",
                e.testCount > 0 ? String.valueOf(e.testCount) : "—",
                text(e.paper, "Fomaspeed Variant 311 RC lucida")
        };

        Paint label = new Paint(Paint.ANTI_ALIAS_FLAG);
        label.setColor(ACCENT);
        label.setTypeface(Typeface.create("sans-serif-condensed", Typeface.NORMAL));
        label.setTextSize(30);
        Paint value = new Paint(Paint.ANTI_ALIAS_FLAG);
        value.setColor(INK);
        value.setTypeface(Typeface.create("cursive", Typeface.NORMAL));
        value.setTextSize(37);

        p.setColor(RULE);
        p.setStrokeWidth(1.3f);
        c.drawLine(76, top, WIDTH - 76, top, p);
        c.drawLine(labelDividerX, top, labelDividerX, top + rowH * labels.length, p);
        for (int i = 0; i < labels.length; i++) {
            float yTop = top + i * rowH;
            float base = yTop + 66;
            if (i == 9) {
                float old = label.getTextSize();
                label.setTextSize(28);
                c.drawText(labels[i], 94, base, label);
                label.setTextSize(old);
            } else {
                c.drawText(labels[i], 94, base, label);
            }
            drawValueFitted(c, values[i], valueStartX, base, WIDTH - 452, value);
            p.setColor(RULE);
            c.drawLine(76, yTop + rowH, WIDTH - 76, yTop + rowH, p);
        }

        float noteTop = top + rowH * labels.length + 26;
        label.setTextSize(31);
        c.drawText("Note", 94, noteTop + 46, label);
        String note = text(e.notes, "");
        if (note.length() > MAX_NOTES_CHARS) note = note.substring(0, MAX_NOTES_CHARS);
        drawNotes(c, note, 210, (int)(noteTop + 10), WIDTH - 300, 112);

        p.setStyle(Paint.Style.FILL);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
        p.setTextSize(22);
        p.setColor(ACCENT);
        String footer = "Darkroom Timer di F.G. - v" + (version == null ? "X.X.X" : version);
        c.drawText(footer, WIDTH / 2f, 1856, p);
        p.setStrokeWidth(1.5f);
        c.drawLine(215, 1848, 340, 1848, p);
        c.drawLine(740, 1848, 865, 1848, p);
        return b;
    }

    private static void drawDateBox(Canvas c, long ts) {
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(RULE);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.5f);
        RectF box = new RectF(760, 78, 1002, 224);
        c.drawRoundRect(box, 7, 7, p);
        c.drawLine(760, 151, 1002, 151, p);
        c.drawLine(830, 78, 830, 224, p);

        p.setStyle(Paint.Style.FILL);
        p.setTypeface(Typeface.create("sans-serif-condensed", Typeface.NORMAL));
        p.setTextSize(25);
        p.setColor(ACCENT);
        c.drawText("Data", 775, 124, p);
        c.drawText("Ora", 775, 197, p);
        p.setColor(INK);
        p.setTextSize(24);
        long t = ts > 0 ? ts : System.currentTimeMillis();
        c.drawText(new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(t)), 850, 124, p);
        c.drawText(new SimpleDateFormat("HH:mm", Locale.ITALY).format(new Date(t)), 850, 197, p);
    }

    private static void drawEnlargerBadge(Canvas c, float cx, float cy, float r) {
        Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        fill.setColor(ACCENT);
        fill.setStyle(Paint.Style.FILL);
        c.drawCircle(cx, cy, r, fill);

        Paint s = new Paint(Paint.ANTI_ALIAS_FLAG);
        s.setColor(PAPER);
        s.setStyle(Paint.Style.STROKE);
        s.setStrokeWidth(6.5f);
        s.setStrokeCap(Paint.Cap.ROUND);
        s.setStrokeJoin(Paint.Join.ROUND);

        // column and baseboard
        c.drawLine(cx - 36, cy - 44, cx - 36, cy + 34, s);
        c.drawLine(cx - 53, cy + 36, cx + 30, cy + 36, s);
        c.drawLine(cx - 4, cy + 36, cx + 36, cy + 24, s);

        // carriage and arm
        c.drawLine(cx - 36, cy - 10, cx - 2, cy - 10, s);
        c.drawLine(cx - 12, cy - 26, cx - 12, cy + 8, s);

        // head
        RectF head = new RectF(cx - 2, cy - 42, cx + 24, cy - 12);
        c.drawRect(head, s);
        c.drawLine(cx + 24, cy - 36, cx + 34, cy - 36, s);

        // bellows and lens
        Path bellows = new Path();
        bellows.moveTo(cx + 4, cy - 12);
        bellows.lineTo(cx + 18, cy - 12);
        bellows.lineTo(cx + 20, cy - 2);
        bellows.lineTo(cx + 2, cy - 2);
        bellows.close();
        c.drawPath(bellows, s);
        c.drawLine(cx + 5, cy - 9, cx + 17, cy - 9, s);
        c.drawLine(cx + 4, cy - 5, cx + 18, cy - 5, s);
        c.drawLine(cx + 11, cy - 2, cx + 11, cy + 14, s);
        c.drawCircle(cx + 11, cy + 18, 5.5f, s);
    }

    private static void drawNotes(Canvas c, String s, int x, int y, int width, int height) {
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(INK);
        p.setTypeface(Typeface.create("cursive", Typeface.NORMAL));
        p.setTextSize(34);
        String text = s == null ? "" : s.trim();
        if (text.length() > MAX_NOTES_CHARS) text = text.substring(0, MAX_NOTES_CHARS);
        if (text.isEmpty()) return;

        int firstCount = p.breakText(text, true, width, null);
        int breakAt = Math.min(firstCount, text.length());
        if (breakAt < text.length()) {
            int space = text.lastIndexOf(' ', breakAt);
            if (space > 0) breakAt = space;
        }
        String line1 = text.substring(0, breakAt).trim();
        String remain = text.substring(Math.min(text.length(), breakAt)).trim();
        int secondCount = remain.isEmpty() ? 0 : p.breakText(remain, true, width, null);
        String line2 = secondCount <= 0 ? "" : remain.substring(0, Math.min(secondCount, remain.length())).trim();
        c.drawText(line1, x, y + 38, p);
        if (!line2.isEmpty()) c.drawText(line2, x, y + 82, p);
    }

    private static void drawValueFitted(Canvas c, String s, float x, float baseline, float maxWidth, Paint p) {
        float original = p.getTextSize();
        while (p.measureText(s) > maxWidth && p.getTextSize() > 24f) p.setTextSize(p.getTextSize() - 1f);
        c.drawText(s, x, baseline, p);
        p.setTextSize(original);
    }

    private static String text(String s, String fallback) {
        return s == null || s.trim().isEmpty() ? fallback : s.trim();
    }

    private static String negativeLabel(String s) {
        String v = text(s, "—");
        if ("35mm".equalsIgnoreCase(v)) return "35 mm";
        if ("6x6".equalsIgnoreCase(v)) return "6×6";
        return v;
    }

    private static String apertureLabel(String s) {
        String v = text(s, "—");
        if ("—".equals(v) || v.toLowerCase(Locale.ITALY).startsWith("f/")) return v;
        return "f/" + v;
    }

    private static String unitLabel(String s, String unit) {
        String v = text(s, "—");
        if ("—".equals(v) || v.toLowerCase(Locale.ITALY).contains(unit.toLowerCase(Locale.ITALY))) return v;
        return v + " " + unit;
    }

    private static String seconds(int ms) {
        if (ms <= 0) return "—";
        if (ms % 1000 == 0) return (ms / 1000) + " s";
        return String.format(Locale.ITALY, "%.1f s", ms / 1000.0);
    }
}
