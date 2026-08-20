package it.darkroom.timer.assistant.equipment;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;

import java.util.List;

import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** Small modern picker for tanks already owned by the user. */
public final class OwnedTankPickerActivity extends Activity {
    public static final String RESULT_ID="tank.id",RESULT_NAME="tank.name";
    private AssistantDatabase db;
    @Override protected void onCreate(Bundle state){super.onCreate(state);db=new AssistantDatabase(this);LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · ATTREZZATURA","SCEGLI TANK","Solo le tank già aggiunte a La mia attrezzatura.");List<AssistantDatabase.TankItem> rows=db.listTanks();if(rows.isEmpty())root.addView(AssistantUi.emptyState(this,"NESSUNA TANK PERSONALE","Aggiungila da LA MIA ATTREZZATURA oppure usa il volume manuale."));for(AssistantDatabase.TankItem t:rows){Button b=AssistantUi.resultRow(this,t.displayName(),"35 mm "+known(t.capacity35)+" · 120 "+known(t.capacity120),AssistantDatabase.SOURCE_CATALOG.equals(t.sourceType)?"CATALOGO VERIFICATO":"DATO PERSONALE");b.setOnClickListener(v->{Intent out=new Intent();out.putExtra(RESULT_ID,t.id);out.putExtra(RESULT_NAME,t.displayName());setResult(RESULT_OK,out);finish();});root.addView(b,AssistantUi.margin(this,-1,AssistantUi.dp(this,76),0,0,0,7));}Button back=AssistantUi.secondaryButton(this,"← INDIETRO");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,12,0,0));}
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
    private static String known(int v){return v>0?Integer.toString(v):"NON DOCUMENTATA";}
}
