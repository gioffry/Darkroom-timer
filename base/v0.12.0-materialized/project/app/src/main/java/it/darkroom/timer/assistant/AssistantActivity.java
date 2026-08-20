package it.darkroom.timer.assistant;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import it.darkroom.timer.assistant.development.NewDevelopmentActivity;
import it.darkroom.timer.assistant.chemistry.PrepareChemistryActivity;
import it.darkroom.timer.assistant.recipes.MyRecipesActivity;
import it.darkroom.timer.assistant.log.DevelopmentLogActivity;
import it.darkroom.timer.assistant.chemistry.inventory.MyChemistryActivity;
import it.darkroom.timer.assistant.equipment.MyEquipmentActivity;

/** Darkroom Assistant — Release 2/9. */
public final class AssistantActivity extends Activity {
    private int primary;
    private int muted;
    private int border;
    private int card;
    private int accent;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean darkroomMode = getSharedPreferences("ui", MODE_PRIVATE)
                .getBoolean("darkroomMode", false);
        configurePalette(darkroomMode);
        buildUi();
    }

    private void configurePalette(boolean darkroomMode) {
        if (darkroomMode) {
            primary = Color.rgb(255, 42, 42);
            muted = Color.rgb(145, 34, 34);
            border = Color.rgb(112, 20, 20);
            card = Color.rgb(18, 0, 0);
            accent = Color.rgb(255, 42, 42);
        } else {
            primary = Color.rgb(238, 240, 242);
            muted = Color.rgb(145, 151, 158);
            border = Color.rgb(60, 64, 70);
            card = Color.rgb(24, 26, 30);
            accent = Color.rgb(197, 54, 58);
        }
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.BLACK);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView eyebrow = text("DARKROOM ASSISTANT", 12, accent, true);
        eyebrow.setGravity(Gravity.CENTER);
        root.addView(eyebrow, lp(-1, -2));
        TextView title = text("SVILUPPO & CHIMICA", 25, primary, true);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(5), 0, dp(18));
        root.addView(title, lp(-1, -2));

        Button newDevelopment = entry("NUOVO SVILUPPO", "Pellicola, ISO, rivelatore, temperatura e tempo JOBO CPE2", true);
        newDevelopment.setOnClickListener(v -> startActivity(new Intent(this, NewDevelopmentActivity.class)));
        root.addView(newDevelopment, margin(lp(-1, dp(78)), 0, 0, 0, 9));

        Button prepareChemistry = entry("PREPARA CHIMICA", "Diluizioni, volumi e capacità documentata", true);
        prepareChemistry.setOnClickListener(v -> startActivity(new Intent(this, PrepareChemistryActivity.class)));
        root.addView(prepareChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));
        Button myChemistry = entry("LA MIA CHIMICA", "Inventario, residui, capacità e utilizzi", true);
        myChemistry.setOnClickListener(v -> startActivity(new Intent(this, MyChemistryActivity.class)));
        root.addView(myChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));
        Button myRecipes = entry("LE MIE RICETTE", "Tempi personali, preferite e originale fonte", true);
        myRecipes.setOnClickListener(v -> startActivity(new Intent(this, MyRecipesActivity.class)));
        root.addView(myRecipes, margin(lp(-1, dp(78)), 0, 0, 0, 9));
        Button developmentLog = entry("LOG SVILUPPI", "Storico, valutazioni, confronto e ripeti", true);
        developmentLog.setOnClickListener(v -> startActivity(new Intent(this, DevelopmentLogActivity.class)));
        root.addView(developmentLog, margin(lp(-1, dp(78)), 0, 0, 0, 9));
        Button myEquipment = entry("LA MIA ATTREZZATURA", "Tank personali e scelta intelligente", true);
        myEquipment.setOnClickListener(v -> startActivity(new Intent(this, MyEquipmentActivity.class)));
        root.addView(myEquipment, margin(lp(-1, dp(78)), 0, 0, 0, 9));

        Button paperChemistry = entry("CHIMICA CARTA", "Sessione opzionale, preparazione e inventario", true);
        paperChemistry.setOnClickListener(v -> startActivity(new Intent(this, it.darkroom.timer.assistant.paper.PaperChemistryActivity.class)));
        root.addView(paperChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));

        Button dataSystem = entry("FONTI · OFFLINE · BACKUP", "Catalogo dati, provenienza, aggiornamenti e ripristino", true);
        dataSystem.setOnClickListener(v -> startActivity(new Intent(this, it.darkroom.timer.assistant.system.DataManagementActivity.class)));
        root.addView(dataSystem, margin(lp(-1, dp(78)), 0, 0, 0, 9));

        TextView completeBadge = text("DARKROOM ASSISTANT 9/9 COMPLETATO", 12, accent, true);
        completeBadge.setGravity(Gravity.CENTER);
        completeBadge.setPadding(dp(4), dp(8), dp(4), dp(10));
        root.addView(completeBadge, lp(-1, -2));

        Button back = entry("←  TORNA ALLA HOME", "", false);
        back.setOnClickListener(v -> finish());
        root.addView(back, margin(lp(-1, dp(58)), 0, 14, 0, 0));
        setContentView(scroll);
    }

    private void addPlaceholder(LinearLayout root, String label) {
        Button b = entry(label, "Prossimamente", false);
        b.setEnabled(false);
        b.setAlpha(0.58f);
        root.addView(b, margin(lp(-1, dp(68)), 0, 0, 0, 8));
    }

    private Button entry(String title, String subtitle, boolean emphasized) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(subtitle.isEmpty() ? title : title + "\n" + subtitle);
        b.setTextSize(emphasized ? 16 : 15);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(primary);
        b.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        b.setPadding(dp(16), dp(8), dp(14), dp(8));
        b.setBackground(roundRect(card, 11, 1, emphasized ? accent : border));
        return b;
    }

    private TextView text(String value, float size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private GradientDrawable roundRect(int color, int radius, int stroke, int strokeColor) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        if (stroke > 0) d.setStroke(dp(stroke), strokeColor);
        return d;
    }

    private LinearLayout.LayoutParams lp(int w, int h) { return new LinearLayout.LayoutParams(w, h); }
    private LinearLayout.LayoutParams margin(LinearLayout.LayoutParams p, int l, int t, int r, int b) {
        p.setMargins(dp(l), dp(t), dp(r), dp(b)); return p;
    }
    private int dp(int v) { return (int) (v * getResources().getDisplayMetrics().density + 0.5f); }
}
