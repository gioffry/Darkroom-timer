package it.darkroom.assistant;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.MotionEvent;
import android.view.View;

public class DarkroomView extends View {
    private static final int SCREEN_HOME = 0;
    private static final int SCREEN_PRODUCTS = 1;
    private static final int SCREEN_FILM = 2;
    private static final int SCREEN_PAPER = 3;

    private static final int BG = Color.rgb(0, 0, 0);
    private static final int WHITE = Color.rgb(246, 243, 238);
    private static final int MUTED = Color.rgb(166, 162, 157);
    private static final int BURGUNDY = Color.rgb(105, 29, 29);
    private static final int BURGUNDY_BRIGHT = Color.rgb(154, 37, 32);
    private static final int CHARCOAL = Color.rgb(39, 39, 39);
    private static final int CARD = Color.rgb(22, 22, 22);
    private static final int CARD_2 = Color.rgb(31, 31, 31);
    private static final int TAUPE = Color.rgb(91, 84, 78);
    private static final int BORDER = Color.rgb(61, 61, 61);

    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Typeface serif = Typeface.create("serif", Typeface.BOLD);
    private final Typeface sans = Typeface.create("sans", Typeface.NORMAL);
    private final Typeface sansBold = Typeface.create("sans", Typeface.BOLD);

    private int screen = SCREEN_HOME;
    private float scrollY = 0f;
    private float maxScroll = 0f;
    private float downX, downY, lastY;
    private boolean dragging;

    private final RectF homeProducts = new RectF();
    private final RectF homeFilm = new RectF();
    private final RectF homePaper = new RectF();

    public DarkroomView(Context context) {
        super(context);
        setBackgroundColor(BG);
        setLayerType(LAYER_TYPE_SOFTWARE, null);
        stroke.setStyle(Paint.Style.STROKE);
        stroke.setStrokeWidth(dp(1.4f));
        stroke.setStrokeCap(Paint.Cap.ROUND);
        stroke.setStrokeJoin(Paint.Join.ROUND);
    }

    public boolean goHome() {
        if (screen == SCREEN_HOME) return false;
        screen = SCREEN_HOME;
        scrollY = 0f;
        invalidate();
        return true;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        canvas.drawColor(BG);
        maxScroll = 0f;
        if (screen == SCREEN_HOME) {
            drawHome(canvas);
        } else {
            canvas.save();
            canvas.translate(0, -scrollY);
            float bottom;
            if (screen == SCREEN_PRODUCTS) bottom = drawProducts(canvas);
            else if (screen == SCREEN_FILM) bottom = drawFilm(canvas);
            else bottom = drawPaper(canvas);
            canvas.restore();
            maxScroll = Math.max(0f, bottom - getHeight() + dp(18));
            if (scrollY > maxScroll) scrollY = maxScroll;
        }
    }

    private void drawHome(Canvas c) {
        final float m = dp(18);
        final float w = getWidth();
        float y = dp(38);
        drawMenu(c, m, y, WHITE);
        drawDots(c, w - m - dp(4), y, MUTED);

        y = dp(98);
        drawText(c, "Darkroom Assistant", m, y, sp(31), WHITE, serif);
        y += dp(42);
        drawText(c, "Camera oscura, semplice.", m, y, sp(16), MUTED, sans);
        y += dp(28);
        drawAccent(c, m, y);

        y += dp(34);
        float cardH = dp(142);
        float gap = dp(20);
        homeProducts.set(m, y, w - m, y + cardH);
        drawHomeCard(c, homeProducts, BURGUNDY, 0, "PRODOTTI", "CHIMICI");
        y += cardH + gap;
        homeFilm.set(m, y, w - m, y + cardH);
        drawHomeCard(c, homeFilm, CHARCOAL, 1, "SVILUPPO", "PELLICOLA");
        y += cardH + gap;
        homePaper.set(m, y, w - m, y + cardH);
        drawHomeCard(c, homePaper, TAUPE, 2, "STAMPA", "CARTA");

        drawBottomNav(c);
    }

    private float drawProducts(Canvas c) {
        float m = dp(18), w = getWidth(), y = dp(38);
        drawMenu(c, m, y, WHITE);
        drawDots(c, w - m - dp(4), y, MUTED);
        y = dp(96);
        drawText(c, "Prodotti chimici", m, y, sp(31), WHITE, serif);
        y += dp(40);
        drawText(c, "Gestisci il tuo magazzino.", m, y, sp(16), MUTED, sans);
        y += dp(28);
        drawAccent(c, m, y);
        y += dp(30);

        RectF add = new RectF(m, y, w - m, y + dp(58));
        drawRounded(c, add, BURGUNDY, dp(14), dp(5));
        float cx = add.centerX() - dp(52);
        float cy = add.centerY();
        stroke.setColor(WHITE); stroke.setStrokeWidth(dp(2));
        c.drawCircle(cx, cy, dp(12), stroke);
        c.drawLine(cx - dp(6), cy, cx + dp(6), cy, stroke);
        c.drawLine(cx, cy - dp(6), cx, cy + dp(6), stroke);
        drawText(c, "AGGIUNGI", cx + dp(28), cy + dp(6), sp(17), WHITE, sansBold);

        y = add.bottom + dp(34);
        drawText(c, "MAGAZZINO", m, y, sp(16), WHITE, sansBold);
        y += dp(14);
        String[] products = {"Foma Universal", "Adox Adostop ECO", "Compard Fix Ag Plus", "Ilford ID-11"};
        for (int i = 0; i < products.length; i++) {
            RectF row = new RectF(m, y, w - m, y + dp(61));
            drawRounded(c, row, CARD, dp(12), dp(2));
            if (i == 0) {
                stroke.setColor(BURGUNDY_BRIGHT); stroke.setStrokeWidth(dp(1.4f));
                c.drawRoundRect(row, dp(12), dp(12), stroke);
            }
            drawBottle(c, row.left + dp(26), row.centerY(), i == 0 ? BURGUNDY_BRIGHT : MUTED, dp(1));
            drawText(c, products[i], row.left + dp(58), row.centerY() + dp(6), sp(15), WHITE, sansBold);
            drawChevron(c, row.right - dp(22), row.centerY(), i == 0 ? BURGUNDY_BRIGHT : MUTED);
            y = row.bottom + dp(9);
        }

        y += dp(14);
        RectF detail = new RectF(m, y, w - m, y + dp(145));
        drawRounded(c, detail, CARD, dp(14), dp(3));
        drawBottle(c, detail.left + dp(42), detail.top + dp(45), BURGUNDY_BRIGHT, dp(1.25f));
        drawText(c, "Foma Universal", detail.left + dp(85), detail.top + dp(42), sp(17), WHITE, sansBold);
        drawText(c, "Scadenza: 19/08/2027", detail.left + dp(85), detail.top + dp(66), sp(13), MUTED, sans);
        RectF del = new RectF(detail.left + dp(23), detail.bottom - dp(56), detail.right - dp(23), detail.bottom - dp(14));
        stroke.setColor(BURGUNDY_BRIGHT); stroke.setStrokeWidth(dp(1.2f));
        c.drawRoundRect(del, dp(10), dp(10), stroke);
        drawTrash(c, del.centerX() - dp(41), del.centerY(), BURGUNDY_BRIGHT);
        drawText(c, "ELIMINA", del.centerX() - dp(16), del.centerY() + dp(6), sp(15), BURGUNDY_BRIGHT, sansBold);
        y = detail.bottom + dp(88);
        drawBottomNav(c);
        return Math.max(y, getHeight());
    }

    private float drawFilm(Canvas c) {
        float m = dp(18), w = getWidth(), y = dp(38);
        drawMenu(c, m, y, WHITE);
        drawDots(c, w - m - dp(4), y, MUTED);
        y = dp(91);
        drawText(c, "Sviluppo pellicola", m, y, sp(29), WHITE, serif);
        y += dp(38);
        drawText(c, "Configura lo sviluppo in JOBO CPE2.", m, y, sp(15), MUTED, sans);
        y += dp(26);
        drawAccent(c, m, y);
        y += dp(24);

        String[][] rows = {
            {"Pellicola", "Ilford HP5 Plus 400", "film"},
            {"ISO esposto", "400", "iso"},
            {"Numero rulli", "1", "rolls"},
            {"Tank JOBO", "2520", "tank"},
            {"Rivelatore", "Foma Universal", "flask"},
            {"Diluizione", "1+3", "drop"},
            {"Temperatura", "20 °C", "temp"},
            {"Arresto", "Adox Adostop ECO", "stop"},
            {"Fissaggio", "Compard Fix Ag Plus", "bottle"}
        };
        for (String[] row : rows) {
            RectF r = new RectF(m, y, w - m, y + dp(48));
            drawInputRow(c, r, row[0], row[1], row[2]);
            y = r.bottom + dp(7);
        }

        RectF calc = new RectF(m, y + dp(2), w - m, y + dp(55));
        drawRounded(c, calc, CHARCOAL, dp(12), dp(4));
        drawCenteredText(c, "CALCOLA", calc.centerX(), calc.centerY() + dp(6), sp(17), WHITE, sansBold);
        y = calc.bottom + dp(12);

        RectF result = new RectF(m, y, w - m, y + dp(205));
        drawRounded(c, result, CARD_2, dp(13), dp(4));
        float rowH = result.height() / 4f;
        drawResultRow(c, result.left, result.top, result.right, rowH, "Tempo JOBO CPE2", "7 min 45 s", "clock", true);
        drawResultRow(c, result.left, result.top + rowH, result.right, rowH, "Rivelatore", "67,5 ml + 202,5 ml acqua", "flask", false);
        drawResultRow(c, result.left, result.top + rowH * 2, result.right, rowH, "Arresto", "13,5 ml + 256,5 ml acqua", "stop", false);
        drawResultRow(c, result.left, result.top + rowH * 3, result.right, rowH, "Fissaggio", "27 ml + 243 ml acqua", "bottle", false);
        y = result.bottom + dp(28);
        drawCenteredText(c, "Fonte: produttore / Dev Chart", w / 2f, y, sp(11), MUTED, sans);
        return y + dp(28);
    }

    private float drawPaper(Canvas c) {
        float m = dp(18), w = getWidth(), y = dp(38);
        drawMenu(c, m, y, WHITE);
        drawDots(c, w - m - dp(4), y, MUTED);
        y = dp(91);
        drawText(c, "Stampa carta", m, y, sp(30), WHITE, serif);
        y += dp(39);
        drawText(c, "Prepara i bagni per la stampa.", m, y, sp(15), MUTED, sans);
        y += dp(26);
        drawAccent(c, m, y);
        y += dp(26);

        String[][] rows = {
            {"Rivelatore carta", "Foma Universal", "bottle"},
            {"Arresto", "Adox Adostop ECO", "stop"},
            {"Fissaggio", "Compard Fix Ag Plus", "bottle"},
            {"Volume da preparare", "1000 ml", "beaker"}
        };
        for (String[] row : rows) {
            RectF r = new RectF(m, y, w - m, y + dp(62));
            drawPaperInput(c, r, row[0], row[1], row[2]);
            y = r.bottom + dp(9);
        }
        RectF calc = new RectF(m, y + dp(2), w - m, y + dp(58));
        drawRounded(c, calc, BURGUNDY, dp(12), dp(4));
        drawCenteredText(c, "CALCOLA", calc.centerX(), calc.centerY() + dp(6), sp(18), WHITE, sansBold);
        y = calc.bottom + dp(16);

        String[][] out = {
            {"Rivelatore", "250 ml + 750 ml acqua", "bottle"},
            {"Arresto", "50 ml + 950 ml acqua", "stop"},
            {"Fissaggio", "100 ml + 900 ml acqua", "bottle"}
        };
        for (String[] row : out) {
            RectF r = new RectF(m, y, w - m, y + dp(70));
            drawPaperResult(c, r, row[0], row[1], row[2]);
            y = r.bottom + dp(9);
        }
        y += dp(18);
        stroke.setColor(BORDER); stroke.setStrokeWidth(dp(1));
        c.drawLine(m, y, w - m, y, stroke);
        y += dp(30);
        drawText(c, "Fine sessione", m, y, sp(17), WHITE, sansBold);
        y += dp(18);
        float half = (w - m * 2 - dp(10)) / 2f;
        RectF fmt = new RectF(m, y, m + half, y + dp(66));
        RectF sheets = new RectF(fmt.right + dp(10), y, w - m, y + dp(66));
        drawSmallField(c, fmt, "Formato carta", "24×30 cm", "paper");
        drawSmallField(c, sheets, "Numero fogli", "12", "sheets");
        y = fmt.bottom + dp(28);
        drawCheck(c, m + dp(10), y - dp(4), MUTED);
        drawText(c, "Capacità residua aggiornata", m + dp(31), y, sp(12), MUTED, sans);
        return y + dp(32);
    }

    private void drawHomeCard(Canvas c, RectF r, int color, int icon, String line1, String line2) {
        drawRounded(c, r, color, dp(16), dp(7));
        float iconCx = r.left + dp(57);
        float iconCy = r.centerY();
        if (icon == 0) {
            drawBottle(c, iconCx - dp(12), iconCy, WHITE, dp(1.5f));
            drawBottle(c, iconCx + dp(22), iconCy + dp(8), WHITE, dp(0.9f));
        } else if (icon == 1) {
            drawFilm(c, iconCx, iconCy, WHITE);
        } else {
            drawPaperIcon(c, iconCx, iconCy, WHITE);
        }
        stroke.setColor(Color.argb(90,255,255,255)); stroke.setStrokeWidth(dp(1));
        float divider = r.left + dp(116);
        c.drawLine(divider, r.top + dp(26), divider, r.bottom - dp(26), stroke);
        drawText(c, line1, divider + dp(24), r.centerY() - dp(5), sp(20), WHITE, sansBold);
        drawText(c, line2, divider + dp(24), r.centerY() + dp(25), sp(20), WHITE, sansBold);
        drawChevron(c, r.right - dp(25), r.centerY(), WHITE);
    }

    private void drawInputRow(Canvas c, RectF r, String label, String value, String icon) {
        drawRounded(c, r, CARD, dp(10), dp(2));
        drawIconByName(c, icon, r.left + dp(24), r.centerY(), MUTED);
        drawText(c, label, r.left + dp(48), r.centerY() + dp(6), sp(13.5f), WHITE, sans);
        float valWidth = measure(value, sp(13.5f), sans);
        drawText(c, value, r.right - dp(28) - valWidth, r.centerY() + dp(6), sp(13.5f), WHITE, sans);
        drawDown(c, r.right - dp(14), r.centerY(), MUTED);
    }

    private void drawPaperInput(Canvas c, RectF r, String label, String value, String icon) {
        drawRounded(c, r, TAUPE, dp(12), dp(4));
        drawIconByName(c, icon, r.left + dp(27), r.centerY(), WHITE);
        drawText(c, label, r.left + dp(58), r.centerY() - dp(3), sp(13), Color.rgb(224,220,216), sans);
        drawText(c, value, r.left + dp(58), r.centerY() + dp(22), sp(16), WHITE, sansBold);
        drawDown(c, r.right - dp(20), r.centerY(), WHITE);
    }

    private void drawPaperResult(Canvas c, RectF r, String label, String value, String icon) {
        drawRounded(c, r, CARD, dp(11), dp(2));
        drawIconByName(c, icon, r.left + dp(28), r.centerY(), BURGUNDY_BRIGHT);
        drawText(c, label, r.left + dp(60), r.centerY() - dp(4), sp(13), MUTED, sans);
        drawText(c, value, r.left + dp(60), r.centerY() + dp(22), sp(16), WHITE, sansBold);
    }

    private void drawSmallField(Canvas c, RectF r, String label, String value, String icon) {
        fill.setColor(CARD); fill.setStyle(Paint.Style.FILL);
        c.drawRoundRect(r, dp(10), dp(10), fill);
        stroke.setColor(BORDER); stroke.setStrokeWidth(dp(1));
        c.drawRoundRect(r, dp(10), dp(10), stroke);
        drawIconByName(c, icon, r.left + dp(24), r.centerY(), BURGUNDY_BRIGHT);
        drawText(c, label, r.left + dp(50), r.centerY() - dp(4), sp(11), MUTED, sans);
        drawText(c, value, r.left + dp(50), r.centerY() + dp(19), sp(14), WHITE, sansBold);
        drawDown(c, r.right - dp(14), r.centerY(), MUTED);
    }

    private void drawResultRow(Canvas c, float left, float top, float right, float h, String label, String value, String icon, boolean strong) {
        if (top > 0) {
            stroke.setColor(BORDER); stroke.setStrokeWidth(dp(.7f));
            c.drawLine(left + dp(10), top, right - dp(10), top, stroke);
        }
        float cy = top + h / 2f;
        drawIconByName(c, icon, left + dp(27), cy, WHITE);
        drawText(c, label, left + dp(53), cy + dp(5), sp(12.5f), WHITE, sans);
        float valW = measure(value, strong ? sp(16) : sp(12.5f), strong ? sansBold : sans);
        drawText(c, value, right - dp(16) - valW, cy + dp(5), strong ? sp(16) : sp(12.5f), WHITE, strong ? sansBold : sans);
    }

    private void drawBottomNav(Canvas c) {
        float h = getHeight();
        float top = h - dp(92);
        fill.setColor(BG); fill.setStyle(Paint.Style.FILL);
        c.drawRect(0, top, getWidth(), h, fill);
        stroke.setColor(BORDER); stroke.setStrokeWidth(dp(1));
        c.drawLine(0, top, getWidth(), top, stroke);
        float third = getWidth() / 3f;
        fill.setColor(BURGUNDY_BRIGHT);
        c.drawRoundRect(new RectF(third * .28f, top - dp(2), third * .72f, top + dp(1)), dp(2), dp(2), fill);
        drawHomeIcon(c, third * .5f, top + dp(29), BURGUNDY_BRIGHT);
        drawBook(c, third * 1.5f, top + dp(29), MUTED);
        drawGear(c, third * 2.5f, top + dp(29), MUTED);
        drawCenteredText(c, "Home", third * .5f, top + dp(62), sp(11), BURGUNDY_BRIGHT, sans);
        drawCenteredText(c, "Guide", third * 1.5f, top + dp(62), sp(11), MUTED, sans);
        drawCenteredText(c, "Impostazioni", third * 2.5f, top + dp(62), sp(10.5f), MUTED, sans);
    }

    private void drawRounded(Canvas c, RectF r, int color, float radius, float shadowRadius) {
        fill.setStyle(Paint.Style.FILL);
        fill.setColor(color);
        if (shadowRadius > 0) fill.setShadowLayer(shadowRadius, 0, dp(2), Color.argb(120, 0, 0, 0));
        c.drawRoundRect(r, radius, radius, fill);
        fill.clearShadowLayer();
    }

    private void drawAccent(Canvas c, float x, float y) {
        fill.setColor(BURGUNDY_BRIGHT); fill.setStyle(Paint.Style.FILL);
        c.drawRoundRect(new RectF(x, y, x + dp(32), y + dp(2.5f)), dp(2), dp(2), fill);
    }

    private void drawText(Canvas c, String s, float x, float baseline, float size, int color, Typeface face) {
        text.setStyle(Paint.Style.FILL);
        text.setColor(color);
        text.setTypeface(face);
        text.setTextSize(size);
        c.drawText(s, x, baseline, text);
    }

    private void drawCenteredText(Canvas c, String s, float cx, float baseline, float size, int color, Typeface face) {
        text.setTypeface(face); text.setTextSize(size); text.setColor(color); text.setStyle(Paint.Style.FILL);
        c.drawText(s, cx - text.measureText(s) / 2f, baseline, text);
    }

    private float measure(String s, float size, Typeface face) {
        text.setTypeface(face); text.setTextSize(size);
        return text.measureText(s);
    }

    private void drawMenu(Canvas c, float x, float y, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(2));
        for (int i = 0; i < 3; i++) c.drawLine(x, y + dp(i * 6), x + dp(18), y + dp(i * 6), stroke);
    }

    private void drawDots(Canvas c, float x, float y, int color) {
        fill.setColor(color); fill.setStyle(Paint.Style.FILL);
        for (int i = 0; i < 3; i++) c.drawCircle(x, y + dp(i * 6), dp(1.5f), fill);
    }

    private void drawChevron(Canvas c, float x, float y, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(2));
        c.drawLine(x - dp(4), y - dp(7), x + dp(2), y, stroke);
        c.drawLine(x + dp(2), y, x - dp(4), y + dp(7), stroke);
    }

    private void drawDown(Canvas c, float x, float y, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.6f));
        c.drawLine(x - dp(4), y - dp(2), x, y + dp(2), stroke);
        c.drawLine(x, y + dp(2), x + dp(4), y - dp(2), stroke);
    }

    private void drawBottle(Canvas c, float cx, float cy, int color, float scale) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        float w = dp(22) * scale, h = dp(38) * scale;
        RectF body = new RectF(cx - w/2, cy - h/2 + dp(3)*scale, cx + w/2, cy + h/2);
        c.drawRoundRect(body, dp(2)*scale, dp(2)*scale, stroke);
        RectF neck = new RectF(cx - dp(6)*scale, cy - h/2 - dp(5)*scale, cx + dp(6)*scale, cy - h/2 + dp(4)*scale);
        c.drawRect(neck, stroke);
        c.drawLine(body.left + dp(3)*scale, cy, body.right - dp(3)*scale, cy, stroke);
    }

    private void drawFilm(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.5f));
        RectF can = new RectF(cx - dp(24), cy - dp(27), cx, cy + dp(27));
        c.drawRoundRect(can, dp(3), dp(3), stroke);
        RectF film = new RectF(cx, cy - dp(14), cx + dp(29), cy + dp(14));
        c.drawRect(film, stroke);
        for (int i = 0; i < 4; i++) {
            float xx = film.left + dp(4 + i*7);
            c.drawRect(xx, film.top + dp(3), xx + dp(3), film.top + dp(6), stroke);
            c.drawRect(xx, film.bottom - dp(6), xx + dp(3), film.bottom - dp(3), stroke);
        }
    }

    private void drawPaperIcon(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.5f));
        RectF r = new RectF(cx - dp(28), cy - dp(28), cx + dp(28), cy + dp(28));
        c.drawRect(r, stroke);
        Path p = new Path();
        p.moveTo(r.left + dp(7), r.bottom - dp(9));
        p.lineTo(cx - dp(8), cy + dp(3));
        p.lineTo(cx + dp(2), cy + dp(12));
        p.lineTo(cx + dp(11), cy + dp(4));
        p.lineTo(r.right - dp(6), r.bottom - dp(9));
        c.drawPath(p, stroke);
        fill.setColor(BURGUNDY_BRIGHT); fill.setStyle(Paint.Style.FILL);
        c.drawCircle(cx + dp(8), cy - dp(8), dp(4), fill);
    }

    private void drawFlask(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        Path p = new Path();
        p.moveTo(cx - dp(5), cy - dp(15));
        p.lineTo(cx + dp(5), cy - dp(15));
        p.lineTo(cx + dp(4), cy - dp(4));
        p.lineTo(cx + dp(13), cy + dp(14));
        p.lineTo(cx - dp(13), cy + dp(14));
        p.lineTo(cx - dp(4), cy - dp(4));
        p.close();
        c.drawPath(p, stroke);
        c.drawLine(cx - dp(7), cy + dp(5), cx + dp(7), cy + dp(5), stroke);
    }

    private void drawDrop(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        Path p = new Path();
        p.moveTo(cx, cy - dp(15));
        p.cubicTo(cx + dp(15), cy + dp(1), cx + dp(9), cy + dp(15), cx, cy + dp(16));
        p.cubicTo(cx - dp(9), cy + dp(15), cx - dp(15), cy + dp(1), cx, cy - dp(15));
        c.drawPath(p, stroke);
    }

    private void drawThermometer(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        c.drawCircle(cx, cy + dp(10), dp(5), stroke);
        RectF stem = new RectF(cx - dp(3), cy - dp(15), cx + dp(3), cy + dp(10));
        c.drawRoundRect(stem, dp(3), dp(3), stroke);
        c.drawLine(cx, cy - dp(8), cx, cy + dp(9), stroke);
    }

    private void drawStop(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.3f));
        float r = dp(14);
        Path p = new Path();
        for (int i=0;i<8;i++) {
            double a = Math.PI/8 + i*Math.PI/4;
            float x = cx + (float)Math.cos(a)*r;
            float y = cy + (float)Math.sin(a)*r;
            if (i==0) p.moveTo(x,y); else p.lineTo(x,y);
        }
        p.close(); c.drawPath(p, stroke);
        drawCenteredText(c, "STOP", cx, cy + dp(3), sp(6.8f), color, sansBold);
    }

    private void drawBeaker(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.3f));
        Path p = new Path();
        p.moveTo(cx - dp(11), cy - dp(15)); p.lineTo(cx + dp(11), cy - dp(15));
        p.lineTo(cx + dp(8), cy + dp(15)); p.lineTo(cx - dp(8), cy + dp(15)); p.close();
        c.drawPath(p, stroke);
        for(int i=0;i<3;i++) c.drawLine(cx + dp(2), cy - dp(7) + dp(i*7), cx + dp(7), cy - dp(7) + dp(i*7), stroke);
    }

    private void drawTank(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        RectF r = new RectF(cx - dp(11), cy - dp(16), cx + dp(11), cy + dp(16));
        c.drawRoundRect(r, dp(2), dp(2), stroke);
        c.drawLine(r.left - dp(2), r.top, r.right + dp(2), r.top, stroke);
    }

    private void drawRolls(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.2f));
        for (int i=0;i<3;i++) {
            float yy = cy - dp(10) + dp(i*10);
            c.drawCircle(cx - dp(5), yy, dp(5), stroke);
            c.drawCircle(cx + dp(5), yy, dp(5), stroke);
        }
    }

    private void drawIso(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.2f));
        RectF r = new RectF(cx - dp(14), cy - dp(11), cx + dp(14), cy + dp(11));
        c.drawRoundRect(r, dp(2), dp(2), stroke);
        drawCenteredText(c, "ISO", cx, cy + dp(4), sp(8), color, sansBold);
    }

    private void drawClock(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.3f));
        c.drawCircle(cx, cy, dp(13), stroke);
        c.drawLine(cx, cy, cx, cy - dp(7), stroke);
        c.drawLine(cx, cy, cx + dp(6), cy + dp(4), stroke);
    }

    private void drawTrash(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.5f));
        RectF r = new RectF(cx - dp(6), cy - dp(5), cx + dp(6), cy + dp(10));
        c.drawRect(r, stroke);
        c.drawLine(cx - dp(9), cy - dp(8), cx + dp(9), cy - dp(8), stroke);
        c.drawLine(cx - dp(3), cy - dp(11), cx + dp(3), cy - dp(11), stroke);
    }

    private void drawHomeIcon(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.5f));
        Path p = new Path();
        p.moveTo(cx - dp(12), cy); p.lineTo(cx, cy - dp(11)); p.lineTo(cx + dp(12), cy); p.lineTo(cx + dp(9), cy);
        p.lineTo(cx + dp(9), cy + dp(11)); p.lineTo(cx + dp(2), cy + dp(11)); p.lineTo(cx + dp(2), cy + dp(3));
        p.lineTo(cx - dp(2), cy + dp(3)); p.lineTo(cx - dp(2), cy + dp(11)); p.lineTo(cx - dp(9), cy + dp(11)); p.lineTo(cx - dp(9), cy);
        c.drawPath(p, stroke);
    }

    private void drawBook(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.3f));
        Path p = new Path();
        p.moveTo(cx, cy + dp(11)); p.lineTo(cx, cy - dp(9)); p.cubicTo(cx-dp(6),cy-dp(13),cx-dp(14),cy-dp(11),cx-dp(14),cy-dp(5));
        p.lineTo(cx-dp(14),cy+dp(10)); p.cubicTo(cx-dp(7),cy+dp(7),cx-dp(3),cy+dp(8),cx,cy+dp(11));
        p.moveTo(cx, cy + dp(11)); p.lineTo(cx, cy - dp(9)); p.cubicTo(cx+dp(6),cy-dp(13),cx+dp(14),cy-dp(11),cx+dp(14),cy-dp(5));
        p.lineTo(cx+dp(14),cy+dp(10)); p.cubicTo(cx+dp(7),cy+dp(7),cx+dp(3),cy+dp(8),cx,cy+dp(11));
        c.drawPath(p, stroke);
    }

    private void drawGear(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        c.drawCircle(cx, cy, dp(10), stroke); c.drawCircle(cx, cy, dp(4), stroke);
        for(int i=0;i<8;i++) {
            double a=i*Math.PI/4; float x1=cx+(float)Math.cos(a)*dp(11); float y1=cy+(float)Math.sin(a)*dp(11);
            float x2=cx+(float)Math.cos(a)*dp(15); float y2=cy+(float)Math.sin(a)*dp(15); c.drawLine(x1,y1,x2,y2,stroke);
        }
    }

    private void drawCheck(Canvas c, float cx, float cy, int color) {
        stroke.setColor(color); stroke.setStrokeWidth(dp(1.4f));
        c.drawCircle(cx, cy, dp(9), stroke);
        c.drawLine(cx-dp(4),cy,cx-dp(1),cy+dp(3),stroke);
        c.drawLine(cx-dp(1),cy+dp(3),cx+dp(5),cy-dp(4),stroke);
    }

    private void drawIconByName(Canvas c, String icon, float cx, float cy, int color) {
        switch (icon) {
            case "film": drawFilm(c, cx, cy, color); break;
            case "iso": drawIso(c, cx, cy, color); break;
            case "rolls": drawRolls(c, cx, cy, color); break;
            case "tank": drawTank(c, cx, cy, color); break;
            case "flask": drawFlask(c, cx, cy, color); break;
            case "drop": drawDrop(c, cx, cy, color); break;
            case "temp": drawThermometer(c, cx, cy, color); break;
            case "stop": drawStop(c, cx, cy, color); break;
            case "beaker": drawBeaker(c, cx, cy, color); break;
            case "clock": drawClock(c, cx, cy, color); break;
            case "paper": drawPaperIcon(c, cx, cy, color); break;
            case "sheets": drawPaperIcon(c, cx, cy, color); break;
            default: drawBottle(c, cx, cy, color, .72f); break;
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        float x = e.getX(), y = e.getY();
        if (e.getAction() == MotionEvent.ACTION_DOWN) {
            downX = x; downY = y; lastY = y; dragging = false;
            return true;
        }
        if (e.getAction() == MotionEvent.ACTION_MOVE) {
            float dy = y - lastY;
            if (Math.abs(y - downY) > dp(6)) dragging = true;
            if (screen != SCREEN_HOME && maxScroll > 0) {
                scrollY = clamp(scrollY - dy, 0, maxScroll);
                invalidate();
            }
            lastY = y;
            return true;
        }
        if (e.getAction() == MotionEvent.ACTION_UP && !dragging) {
            if (screen == SCREEN_HOME) {
                if (homeProducts.contains(x, y)) open(SCREEN_PRODUCTS);
                else if (homeFilm.contains(x, y)) open(SCREEN_FILM);
                else if (homePaper.contains(x, y)) open(SCREEN_PAPER);
            } else {
                if (x < dp(64) && y < dp(90)) goHome();
            }
            return true;
        }
        return true;
    }

    private void open(int target) {
        screen = target;
        scrollY = 0f;
        invalidate();
    }

    private float clamp(float v, float min, float max) {
        return Math.max(min, Math.min(max, v));
    }

    private float dp(float v) {
        return v * getResources().getDisplayMetrics().density;
    }

    private float sp(float v) {
        return v * getResources().getDisplayMetrics().scaledDensity;
    }
}
