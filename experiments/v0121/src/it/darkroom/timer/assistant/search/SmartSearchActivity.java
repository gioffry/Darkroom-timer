package it.darkroom.timer.assistant.search;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import it.darkroom.timer.assistant.system.CatalogManager;
import it.darkroom.timer.assistant.ui.AssistantUi;

/** Modern reusable picker: instant local results + debounced optional online enrichment. */
public final class SmartSearchActivity extends Activity {
    public static final String EXTRA_CATEGORIES="smart.categories";
    public static final String EXTRA_TITLE="smart.title";
    public static final String EXTRA_HINT="smart.hint";
    public static final String EXTRA_QUERY="smart.query";
    public static final String EXTRA_ALLOW_MANUAL="smart.allowManual";
    public static final String RESULT_RECORD="smart.record";
    public static final String RESULT_NAME="smart.name";
    public static final String RESULT_ID="smart.id";
    public static final String RESULT_ORIGIN="smart.origin";
    public static final String RESULT_MANUAL="smart.manual";
    private static final long DEBOUNCE_MS=350;

    private final Handler handler=new Handler(Looper.getMainLooper());
    private final Runnable remoteRunnable=new Runnable(){@Override public void run(){requestRemote();}};
    private EditText search;
    private LinearLayout localBox,onlineBox;
    private TextView status,onlineTitle;
    private List<SmartSearchEngine.Item> localItems=new ArrayList<>();
    private Set<String> categories=new HashSet<>();
    private int generation=0;
    private boolean allowManual=true;

    @Override protected void onCreate(Bundle state){super.onCreate(state);build();}
    @Override protected void onDestroy(){handler.removeCallbacksAndMessages(null);super.onDestroy();}

    private void build(){
        String title=getIntent().getStringExtra(EXTRA_TITLE);if(title==null||title.trim().isEmpty())title="CERCA NEL CATALOGO";
        String hint=getIntent().getStringExtra(EXTRA_HINT);if(hint==null||hint.trim().isEmpty())hint="Cerca marca o modello...";
        categories.addAll(SmartCatalog.categories(getIntent().getStringExtra(EXTRA_CATEGORIES)));
        allowManual=getIntent().getBooleanExtra(EXTRA_ALLOW_MANUAL,true);
        LinearLayout root=AssistantUi.screen(this,"DARKROOM ASSISTANT · SMART SEARCH",title,"Risultati locali immediati · catalogo online opzionale");
        search=AssistantUi.searchField(this,hint);root.addView(search,AssistantUi.margin(this,-1,AssistantUi.dp(this,54),0,0,0,10));
        status=AssistantUi.secondary(this,"Risultati locali · offline-first");root.addView(status);
        root.addView(AssistantUi.section(this,"RISULTATI LOCALI"));localBox=new LinearLayout(this);localBox.setOrientation(LinearLayout.VERTICAL);root.addView(localBox);
        onlineTitle=AssistantUi.section(this,"RISULTATI ONLINE");onlineTitle.setVisibility(View.GONE);root.addView(onlineTitle);onlineBox=new LinearLayout(this);onlineBox.setOrientation(LinearLayout.VERTICAL);root.addView(onlineBox);
        if(allowManual){Button manual=AssistantUi.ghostButton(this,"NON TROVI QUELLO CHE CERCHI? INSERISCI MANUALMENTE");manual.setOnClickListener(v->returnManual());root.addView(manual,AssistantUi.margin(this,-1,AssistantUi.dp(this,54),0,16,0,8));}
        Button back=AssistantUi.secondaryButton(this,"← INDIETRO");back.setOnClickListener(v->finish());root.addView(back,AssistantUi.margin(this,-1,AssistantUi.dp(this,50),0,8,0,0));
        localItems=SmartCatalog.localItems(this);
        search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int a){}public void onTextChanged(CharSequence s,int st,int b,int c){onQueryChanged();}public void afterTextChanged(Editable e){}});
        String q=getIntent().getStringExtra(EXTRA_QUERY);if(q!=null)search.setText(q);else onQueryChanged();search.requestFocus();
    }

    private void onQueryChanged(){
        generation++;handler.removeCallbacks(remoteRunnable);renderLocal();onlineBox.removeAllViews();onlineTitle.setVisibility(View.GONE);
        String q=query();if(q.isEmpty()){status.setText("Risultati locali · inizia a scrivere per filtrare");return;}
        status.setText("Risultati locali · ricerca online fra "+DEBOUNCE_MS+" ms se la rete è disponibile");handler.postDelayed(remoteRunnable,DEBOUNCE_MS);
    }

    private void renderLocal(){
        localBox.removeAllViews();List<SmartSearchEngine.Result> rows=SmartSearchEngine.search(localItems,query(),categories,6);
        if(rows.isEmpty()){localBox.addView(AssistantUi.emptyState(this,"NESSUN RISULTATO LOCALE","Puoi continuare a scrivere; il catalogo online verrà controllato senza bloccare la schermata."));return;}
        for(SmartSearchEngine.Result r:rows)addResult(localBox,r.item);
    }

    private void requestRemote(){
        final int token=generation;final String q=query();if(q.isEmpty())return;status.setText("Risultati locali · controllo catalogo online…");
        CatalogManager.fetchRemoteForSearch(this,(raw,error)->{
            if(token!=generation||!q.equals(query()))return;
            if(error!=null||raw==null){status.setText("Risultati locali · offline");return;}
            List<SmartSearchEngine.Item> remote=SmartCatalog.onlineItems(raw);HashSet<String> localIds=new HashSet<>();for(SmartSearchEngine.Item i:localItems)localIds.add(i.id);ArrayList<SmartSearchEngine.Item> extra=new ArrayList<>();for(SmartSearchEngine.Item i:remote)if(!localIds.contains(i.id))extra.add(i);
            List<SmartSearchEngine.Result> rows=SmartSearchEngine.search(extra,q,categories,5);onlineBox.removeAllViews();if(!rows.isEmpty()){onlineTitle.setVisibility(View.VISIBLE);for(SmartSearchEngine.Result r:rows)addResult(onlineBox,r.item);}else onlineTitle.setVisibility(View.GONE);
            status.setText(rows.isEmpty()?"Catalogo locale · nessun risultato online aggiuntivo":"Catalogo locale + risultati online");
        });
    }

    private void addResult(LinearLayout box,SmartSearchEngine.Item item){Button row=AssistantUi.resultRow(this,item.name,item.manufacturer+" · "+SmartCatalog.categoryLabel(item),item.origin);row.setOnClickListener(v->returnItem(item));box.addView(row,AssistantUi.margin(this,-1,AssistantUi.dp(this,76),0,0,0,7));}
    private void returnItem(SmartSearchEngine.Item item){if(item.remote)try{CatalogManager.cacheSelectedRecord(this,new JSONObject(item.recordJson));}catch(Exception ignored){}Intent out=new Intent();out.putExtra(RESULT_RECORD,item.recordJson);out.putExtra(RESULT_NAME,item.name);out.putExtra(RESULT_ID,item.id);out.putExtra(RESULT_ORIGIN,item.origin);setResult(RESULT_OK,out);finish();}
    private void returnManual(){Intent out=new Intent();out.putExtra(RESULT_MANUAL,true);setResult(RESULT_OK,out);finish();}
    private String query(){return search==null?"":search.getText().toString().trim();}
}
