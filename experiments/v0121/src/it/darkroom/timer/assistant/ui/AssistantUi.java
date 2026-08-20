package it.darkroom.timer.assistant.ui;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Small shared design system for Assistant screens. Timer UI is intentionally untouched. */
public final class AssistantUi {
    public static final class Palette {
        public final int primary,muted,border,card,accent,background;
        Palette(int p,int m,int b,int c,int a){primary=p;muted=m;border=b;card=c;accent=a;background=Color.BLACK;}
    }
    private AssistantUi(){}

    public static Palette palette(Context c){
        boolean red=c.getSharedPreferences("ui",Context.MODE_PRIVATE).getBoolean("darkroomMode",false);
        return red?new Palette(Color.rgb(255,42,42),Color.rgb(145,34,34),Color.rgb(112,20,20),Color.rgb(18,0,0),Color.rgb(255,42,42)):
                new Palette(Color.rgb(238,240,242),Color.rgb(145,151,158),Color.rgb(60,64,70),Color.rgb(24,26,30),Color.rgb(197,54,58));
    }

    public static LinearLayout screen(Activity a,String eyebrow,String title,String subtitle){
        Palette p=palette(a);ScrollView scroll=new ScrollView(a);scroll.setFillViewport(true);scroll.setBackgroundColor(p.background);
        LinearLayout root=new LinearLayout(a);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(a,18),dp(a,16),dp(a,18),dp(a,30));
        scroll.addView(root,new ScrollView.LayoutParams(-1,-2));
        TextView eye=text(a,eyebrow,12,p.accent,true);eye.setGravity(Gravity.CENTER);root.addView(eye,lp(-1,-2));
        TextView h=text(a,title,25,p.primary,true);h.setGravity(Gravity.CENTER);h.setPadding(0,dp(a,4),0,0);root.addView(h,lp(-1,-2));
        if(subtitle!=null&&!subtitle.trim().isEmpty()){TextView s=text(a,subtitle,12,p.muted,false);s.setGravity(Gravity.CENTER);s.setPadding(dp(a,5),dp(a,6),dp(a,5),dp(a,16));root.addView(s,lp(-1,-2));}
        else root.addView(space(a,12));
        a.setContentView(scroll);return root;
    }

    public static TextView section(Context c,String label){Palette p=palette(c);TextView t=text(c,label,11,p.muted,true);t.setLetterSpacing(.08f);t.setPadding(dp(c,2),dp(c,14),dp(c,2),dp(c,6));return t;}
    public static LinearLayout card(Context c){Palette p=palette(c);LinearLayout box=new LinearLayout(c);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(c,14),dp(c,12),dp(c,14),dp(c,12));box.setBackground(round(c,p.card,12,1,p.border));return box;}
    public static TextView cardTitle(Context c,String value){Palette p=palette(c);return text(c,value,16,p.primary,true);}
    public static TextView body(Context c,String value){Palette p=palette(c);TextView t=text(c,value,13,p.primary,false);t.setLineSpacing(0,1.12f);return t;}
    public static TextView secondary(Context c,String value){Palette p=palette(c);TextView t=text(c,value,12,p.muted,false);t.setLineSpacing(0,1.1f);return t;}
    public static TextView badge(Context c,String value,boolean verified){Palette p=palette(c);TextView t=text(c,value,10,verified?p.accent:p.muted,true);t.setPadding(dp(c,8),dp(c,4),dp(c,8),dp(c,4));t.setBackground(round(c,p.card,8,1,verified?p.accent:p.border));return t;}

    public static Button primaryButton(Context c,String label){Palette p=palette(c);Button b=baseButton(c,label,p.primary);b.setBackground(round(c,p.card,11,2,p.accent));b.setTextColor(p.primary);return b;}
    public static Button secondaryButton(Context c,String label){Palette p=palette(c);Button b=baseButton(c,label,p.primary);b.setBackground(round(c,p.card,11,1,p.border));return b;}
    public static Button ghostButton(Context c,String label){Palette p=palette(c);Button b=baseButton(c,label,p.muted);b.setBackground(round(c,Color.TRANSPARENT,11,1,p.border));return b;}
    private static Button baseButton(Context c,String label,int color){Button b=new Button(c);b.setText(label);b.setAllCaps(false);b.setTextSize(14);b.setTextColor(color);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setGravity(Gravity.CENTER);b.setPadding(dp(c,12),0,dp(c,12),0);b.setMinHeight(0);b.setMinimumHeight(0);return b;}

    public static EditText searchField(Context c,String hint){Palette p=palette(c);EditText e=new EditText(c);e.setHint(hint);e.setHintTextColor(p.muted);e.setTextColor(p.primary);e.setTextSize(16);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);e.setPadding(dp(c,14),0,dp(c,14),0);e.setBackground(round(c,p.card,11,1,p.border));return e;}
    public static EditText field(Context c,String hint){return searchField(c,hint);}
    public static EditText numberField(Context c,String hint){EditText e=field(c,hint);e.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);return e;}

    public static Button resultRow(Context c,String title,String subtitle,String origin){
        Palette p=palette(c);Button b=new Button(c);String text=title;
        if(subtitle!=null&&!subtitle.trim().isEmpty())text+="\n"+subtitle;
        if(origin!=null&&!origin.trim().isEmpty())text+="\n"+origin;
        b.setText(text);b.setAllCaps(false);b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);b.setTextSize(14);b.setTextColor(p.primary);b.setTypeface(Typeface.DEFAULT,Typeface.NORMAL);b.setPadding(dp(c,14),dp(c,8),dp(c,14),dp(c,8));b.setBackground(round(c,p.card,10,1,p.border));return b;
    }
    public static TextView emptyState(Context c,String title,String detail){Palette p=palette(c);TextView t=text(c,title+(detail==null||detail.isEmpty()?"":"\n"+detail),13,p.muted,false);t.setGravity(Gravity.CENTER);t.setPadding(dp(c,14),dp(c,20),dp(c,14),dp(c,20));t.setBackground(round(c,p.card,10,1,p.border));return t;}
    public static View divider(Context c){Palette p=palette(c);View v=new View(c);v.setBackgroundColor(p.border);return v;}

    public static TextView text(Context c,String value,float size,int color,boolean bold){TextView t=new TextView(c);t.setText(value==null?"":value);t.setTextSize(size);t.setTextColor(color);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    public static GradientDrawable round(Context c,int fill,int radius,int stroke,int strokeColor){GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(c,radius));if(stroke>0)d.setStroke(dp(c,stroke),strokeColor);return d;}
    public static LinearLayout.LayoutParams lp(int w,int h){return new LinearLayout.LayoutParams(w,h);}
    public static LinearLayout.LayoutParams weight(int h,float weight){return new LinearLayout.LayoutParams(0,h,weight);}
    public static LinearLayout.LayoutParams margin(Context c,int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(c,l),dp(c,t),dp(c,r),dp(c,b));return p;}
    public static View space(Context c,int h){View v=new View(c);v.setLayoutParams(lp(1,dp(c,h)));return v;}
    public static int dp(Context c,int value){return(int)(value*c.getResources().getDisplayMetrics().density+.5f);}
}
