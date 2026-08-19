package it.darkroom.timer.assistant.search;

import android.app.Activity;
import android.database.DataSetObserver;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AutoCompleteTextView;
import android.widget.BaseAdapter;
import android.widget.Filter;
import android.widget.Filterable;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;

import it.darkroom.timer.assistant.ui.AssistantUi;

/** Alias-aware live suggestions for existing AutoCompleteTextView forms. Local lookup is immediate. */
public final class SmartSearchBinder {
    public interface OnSelected { void selected(SmartSearchEngine.Item item); }
    private SmartSearchBinder(){}

    public static void attach(Activity a,AutoCompleteTextView field,String category,OnSelected callback){
        final List<SmartSearchEngine.Item> source=SmartCatalog.localItems(a);final RankedAdapter adapter=new RankedAdapter(a);field.setThreshold(0);field.setAdapter(adapter);
        final boolean[] internal={false};
        Runnable refresh=()->{if(internal[0])return;List<SmartSearchEngine.Result> r=SmartSearchEngine.search(source,field.getText().toString(),category,7);ArrayList<SmartSearchEngine.Item> rows=new ArrayList<>();for(SmartSearchEngine.Result x:r)rows.add(x.item);adapter.setRows(rows);if(field.hasFocus()&&!rows.isEmpty())field.showDropDown();};
        field.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int a2){}public void onTextChanged(CharSequence s,int st,int b,int c){refresh.run();}public void afterTextChanged(Editable e){}});
        field.setOnFocusChangeListener((v,has)->{if(has)refresh.run();});
        field.setOnItemClickListener((p,v,pos,id)->{SmartSearchEngine.Item item=adapter.getItem(pos);if(item==null)return;internal[0]=true;field.setText(item.name,false);internal[0]=false;if(callback!=null)callback.selected(item);});
        refresh.run();
    }

    public static String canonical(Activity a,String query,String category){return SmartCatalog.canonicalName(a,query,category);}

    private static final class RankedAdapter extends BaseAdapter implements Filterable {
        private final Activity activity;private final ArrayList<SmartSearchEngine.Item> rows=new ArrayList<>();
        RankedAdapter(Activity a){activity=a;}
        void setRows(List<SmartSearchEngine.Item> next){rows.clear();if(next!=null)rows.addAll(next);notifyDataSetChanged();}
        @Override public int getCount(){return rows.size();}
        @Override public SmartSearchEngine.Item getItem(int p){return p>=0&&p<rows.size()?rows.get(p):null;}
        @Override public long getItemId(int p){return p;}
        @Override public View getView(int p,View convert,ViewGroup parent){SmartSearchEngine.Item i=getItem(p);TextView t=convert instanceof TextView?(TextView)convert:AssistantUi.text(activity,"",14,AssistantUi.palette(activity).primary,false);t.setPadding(AssistantUi.dp(activity,14),AssistantUi.dp(activity,9),AssistantUi.dp(activity,14),AssistantUi.dp(activity,9));t.setText(i==null?"":i.name+"\n"+i.manufacturer+" · "+SmartCatalog.categoryLabel(i));return t;}
        @Override public Filter getFilter(){return new Filter(){@Override protected FilterResults performFiltering(CharSequence constraint){FilterResults r=new FilterResults();r.values=new ArrayList<>(rows);r.count=rows.size();return r;}@Override protected void publishResults(CharSequence constraint,FilterResults results){notifyDataSetChanged();}};}
    }
}
