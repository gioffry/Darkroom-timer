package it.darkroom.timer.home;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import it.darkroom.assistant.AssistantActivityV2;
import it.darkroom.timer.MainActivity;
import it.darkroom.timer.Lpl7451Migration;
import it.darkroom.timer.maintenance.UseMaintenanceActivity;
import it.darkroom.timer.largeformat.LargeFormatActivity;

/** Final native Home: no decorative bitmap dependency. */
public final class HomeActivity extends Activity {
    private static final int BG = Color.rgb(5, 6, 7);
    private static final int CARD = Color.rgb(18, 19, 20);
    private static final int IVORY = Color.rgb(235, 210, 174);
    private static final int MUTED = Color.rgb(164, 151, 133);
    private static final int BORDER = Color.rgb(164, 139, 105);

    private static final int ICON_CHEM = 1;
    private static final int ICON_FILM = 2;
    private static final int ICON_TRAY = 3;
    private static final int ICON_TIMER = 4;
    private static final int ICON_WRENCH = 5;
    private static final int ICON_CHASSIS = 6;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Lpl7451Migration.run(this);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        buildUi();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(22), dp(30), dp(22), dp(22));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView title = label("CAMERA OSCURA", 35, IVORY, true, true);
        title.setGravity(Gravity.CENTER);
        title.setLetterSpacing(0.045f);
        root.addView(title, lp(-1, -2));

        TextView sub = label("di Federico e Francesco", 16, IVORY, false, true);
        sub.setGravity(Gravity.CENTER);
        sub.setLetterSpacing(0.05f);
        root.addView(sub, margin(lp(-1, -2), 0, 3, 0, 10));

        View rule = new View(this);
        rule.setBackgroundColor(Color.rgb(91, 76, 59));
        LinearLayout.LayoutParams ruleLp = lp(dp(230), dp(1));
        ruleLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(rule, margin(ruleLp, 0, 0, 0, 22));

        HomeCard products = new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, false);
        products.setOnClickListener(v -> openAssistant("products"));
        root.addView(products, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard film = new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false);
        film.setOnClickListener(v -> openAssistant("film"));
        root.addView(film, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard largeFormat = new HomeCard("GRANDE FORMATO", ICON_CHASSIS, false);
        largeFormat.setOnClickListener(v -> startActivity(new Intent(this, LargeFormatActivity.class)));
        root.addView(largeFormat, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard paper = new HomeCard("BAGNI STAMPA", ICON_TRAY, false);
        paper.setOnClickListener(v -> openAssistant("paper"));
        root.addView(paper, margin(lp(-1, dp(88)), 0, 0, 0, 12));

        HomeCard timer = new HomeCard("TIMER STAMPA", ICON_TIMER, false);
        timer.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        root.addView(timer, margin(lp(-1, dp(88)), 0, 0, 0, 18));

        HomeCard maintenance = new HomeCard("USO E MANUTENZIONE", ICON_WRENCH, true);
        maintenance.setOnClickListener(v -> startActivity(new Intent(this, UseMaintenanceActivity.class)));
        LinearLayout.LayoutParams mLp = lp(dp(294), dp(62));
        mLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(maintenance, margin(mLp, 0, 0, 0, 26));

        TextView motto = label("LA PAZIENZA È PARTE DEL PROCESSO", 11, IVORY, true, true);
        motto.setGravity(Gravity.CENTER);
        motto.setLetterSpacing(0.12f);
        root.addView(motto, margin(lp(-1, -2), 0, 4, 0, 14));

        TextView version = label(readInstalledVersion(), 11, Color.rgb(104, 100, 96), false, true);
        version.setGravity(Gravity.CENTER);
        version.setLetterSpacing(0.06f);
        root.addView(version, margin(lp(-1, dp(30)), 0, 0, 0, 8));

        setContentView(scroll);
    }

    private void openAssistant(String target) {
        Intent i = new Intent(this, AssistantActivityV2.class);
        i.putExtra("darkroom_target", target);
        startActivity(i);
    }

    private String readInstalledVersion() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return "v" + info.versionName;
        } catch (Exception ignored) { return "v—"; }
    }

    private TextView label(String value, float sp, int color, boolean bold, boolean serif) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setTypeface(Typeface.create(serif ? Typeface.SERIF : Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL));
        v.setIncludeFontPadding(false);
        return v;
    }

    private GradientDrawable cardBg(boolean secondary) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(secondary ? Color.rgb(15, 16, 17) : CARD);
        g.setCornerRadius(dp(13));
        g.setStroke(dp(1), BORDER);
        return g;
    }

    private final class HomeCard extends LinearLayout {
        HomeCard(String text, int icon, boolean secondary) {
            super(HomeActivity.this);
            setOrientation(HORIZONTAL);
            setGravity(Gravity.CENTER_VERTICAL);
            setPadding(dp(14), dp(8), dp(12), dp(8));
            setBackground(cardBg(secondary));
            setClickable(true);
            setFocusable(true);

            LineIcon iconView = new LineIcon(HomeActivity.this, icon);
            addView(iconView, new LinearLayout.LayoutParams(dp(secondary ? 42 : 54), dp(secondary ? 42 : 54)));

            float nameSize = secondary ? 15f : ("SVILUPPO PELLICOLA".equals(text) ? 18f : 20f);
            TextView name = label(text, nameSize, IVORY, true, true);
            name.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
            name.setSingleLine(true);
            LinearLayout.LayoutParams nameLp = new LinearLayout.LayoutParams(0, -1, 1f);
            nameLp.setMargins(dp(13), 0, dp(8), 0);
            addView(name, nameLp);

            TextView arrow = label("›", secondary ? 27 : 32, IVORY, false, true);
            arrow.setGravity(Gravity.CENTER);
            addView(arrow, new LinearLayout.LayoutParams(dp(26), -1));
        }
    }

    private static final class LineIcon extends View {
        private final int kind;
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path path = new Path();
        LineIcon(android.content.Context c, int kind) { super(c); this.kind=kind; p.setStyle(Paint.Style.STROKE); p.setStrokeCap(Paint.Cap.ROUND); p.setStrokeJoin(Paint.Join.ROUND); }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            float w=getWidth(), h=getHeight(), cx=w/2f, cy=h/2f, s=Math.min(w,h);
            p.setColor(IVORY); p.setStrokeWidth(Math.max(1.6f,s*.035f)); p.setStyle(Paint.Style.STROKE);
            c.drawCircle(cx,cy,s*.44f,p);
            path.reset();
            if(kind==ICON_CHEM){
                path.moveTo(cx-s*.10f,cy-s*.23f);path.lineTo(cx+s*.10f,cy-s*.23f);path.moveTo(cx-s*.05f,cy-s*.23f);path.lineTo(cx-s*.05f,cy-s*.05f);path.lineTo(cx-s*.18f,cy+s*.22f);path.quadTo(cx,cy+s*.31f,cx+s*.18f,cy+s*.22f);path.lineTo(cx+s*.05f,cy-s*.05f);path.lineTo(cx+s*.05f,cy-s*.23f);c.drawPath(path,p);c.drawLine(cx-s*.12f,cy+s*.13f,cx+s*.12f,cy+s*.13f,p);
            } else if(kind==ICON_FILM){
                RectF r=new RectF(cx-s*.16f,cy-s*.27f,cx+s*.16f,cy+s*.27f);c.drawRect(r,p);c.drawLine(cx-s*.08f,cy-s*.13f,cx+s*.08f,cy-s*.13f,p);c.drawLine(cx-s*.08f,cy+s*.02f,cx+s*.08f,cy+s*.02f,p);c.drawLine(cx-s*.08f,cy+s*.17f,cx+s*.08f,cy+s*.17f,p);for(int i=-2;i<=2;i++){float y=cy+i*s*.105f;c.drawCircle(cx-s*.13f,y,s*.012f,p);c.drawCircle(cx+s*.13f,y,s*.012f,p);}
            } else if(kind==ICON_TRAY){
                path.moveTo(cx-s*.25f,cy-s*.09f);path.lineTo(cx+s*.25f,cy-s*.09f);path.lineTo(cx+s*.18f,cy+s*.18f);path.lineTo(cx-s*.18f,cy+s*.18f);path.close();c.drawPath(path,p);c.drawLine(cx-s*.19f,cy+s*.02f,cx+s*.19f,cy+s*.02f,p);
            } else if(kind==ICON_TIMER){
                c.drawCircle(cx,cy+s*.04f,s*.24f,p);c.drawLine(cx,cy-s*.20f,cx,cy-s*.30f,p);c.drawLine(cx-s*.07f,cy-s*.30f,cx+s*.07f,cy-s*.30f,p);c.drawLine(cx,cy+s*.04f,cx+s*.10f,cy-s*.07f,p);c.drawLine(cx+s*.17f,cy-s*.17f,cx+s*.23f,cy-s*.23f,p);
            } else if(kind==ICON_CHASSIS){
                RectF outer=new RectF(cx-s*.24f,cy-s*.27f,cx+s*.24f,cy+s*.27f);c.drawRoundRect(outer,s*.03f,s*.03f,p);
                RectF inner=new RectF(cx-s*.16f,cy-s*.18f,cx+s*.16f,cy+s*.18f);c.drawRect(inner,p);
                c.drawLine(cx-s*.08f,cy-s*.31f,cx+s*.08f,cy-s*.31f,p);c.drawLine(cx,cy-s*.31f,cx,cy-s*.27f,p);
            } else {
                path.moveTo(cx-s*.23f,cy+s*.20f);path.lineTo(cx-s*.03f,cy);path.cubicTo(cx-s*.10f,cy-s*.19f,cx+s*.05f,cy-s*.30f,cx+s*.20f,cy-s*.23f);path.lineTo(cx+s*.08f,cy-s*.11f);path.lineTo(cx+s*.17f,cy-s*.02f);path.lineTo(cx+s*.28f,cy-s*.14f);path.cubicTo(cx+s*.33f,cy+s*.03f,cx+s*.20f,cy+s*.16f,cx+s*.04f,cy+s*.08f);path.lineTo(cx-s*.16f,cy+s*.27f);c.drawPath(path,p);
            }
        }
    }

    private LinearLayout.LayoutParams lp(int w,int h){return new LinearLayout.LayoutParams(w,h);}
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p,int l,int t,int r,int b){p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(float v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
