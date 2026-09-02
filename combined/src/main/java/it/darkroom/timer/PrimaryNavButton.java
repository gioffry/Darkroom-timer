package it.darkroom.timer;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.view.Gravity;
import android.widget.Button;

public final class PrimaryNavButton extends Button {
    public static final int ICON_TIMER = 0;
    public static final int ICON_TEST = 1;
    public static final int ICON_LOG = 2;

    private final int iconKind;
    private int iconColor = Color.WHITE;
    private boolean activeIndicator = false;
    private int activeColor = Color.WHITE;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;

    public PrimaryNavButton(Context context, String label, int iconKind) {
        super(context);
        this.iconKind = iconKind;
        this.density = getResources().getDisplayMetrics().density;
        setText(label);
        setTextSize(12);
        setTypeface(Typeface.DEFAULT, Typeface.NORMAL);
        setAllCaps(false);
        setGravity(Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        setPadding(d(4), d(6), d(4), d(7));
        setMinHeight(0);
        setMinimumHeight(0);
    }

    public void setIconColor(int color) {
        iconColor = color;
        invalidate();
    }

    public void setActiveIndicator(boolean active, int color) {
        activeIndicator = active;
        activeColor = color;
        invalidate();
    }

    private int d(float dp) {
        return Math.round(dp * density);
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float cx = getWidth() / 2f;
        if (activeIndicator) {
            paint.setColor(activeColor);
            paint.setStrokeWidth(d(3));
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setStyle(Paint.Style.STROKE);
            canvas.drawLine(cx - d(18), d(2), cx + d(18), d(2), paint);
        }
        float cy = d(25);
        paint.setColor(iconColor);
        paint.setStrokeWidth(d(2));
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStyle(Paint.Style.STROKE);

        if (iconKind == ICON_TIMER) {
            float r = d(10);
            canvas.drawCircle(cx, cy, r, paint);
            canvas.drawLine(cx, cy, cx, cy - d(6), paint);
            canvas.drawLine(cx, cy, cx + d(5), cy + d(2), paint);
            canvas.drawLine(cx - d(3), cy - d(14), cx + d(3), cy - d(14), paint);
            canvas.drawLine(cx, cy - d(14), cx, cy - d(11), paint);
        } else if (iconKind == ICON_TEST) {
            paint.setStyle(Paint.Style.FILL);
            float cell = d(5);
            float gap = d(3);
            float total = cell * 3 + gap * 2;
            float left = cx - total / 2f;
            float top = cy - (cell * 2 + gap) / 2f;
            for (int row = 0; row < 2; row++) {
                for (int col = 0; col < 3; col++) {
                    float x = left + col * (cell + gap);
                    float y = top + row * (cell + gap);
                    canvas.drawRect(x, y, x + cell, y + cell, paint);
                }
            }
        } else {
            for (int row = -1; row <= 1; row++) {
                float y = cy + row * d(7);
                canvas.drawLine(cx - d(12), y, cx + d(12), y, paint);
            }
        }
    }
}
