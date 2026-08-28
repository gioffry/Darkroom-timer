#!/usr/bin/env python3
from pathlib import Path
import re


p = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java')
if not p.exists():
    raise SystemExit('v0.4.7: UseMaintenanceActivity missing')
s = p.read_text(encoding='utf-8')

table_question = 'Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?'

# The searchable FAQ answer remains useful as plain language, while the opened
# answer is now rendered from native Android cells instead of an ASCII block.
answer_marker = '    private static final String[] A_MINOLTA = {\n'
answer_re = re.compile(
    re.escape(answer_marker) + r'\s*"(?:\\.|[^"\\])*",',
    re.DOTALL,
)
native_answer = (
    answer_marker
    + '            "Tabella grafica dei valori EV per le coppie tempo/diaframma delle Rolleiflex 2.8 E2 e 3.5 Tessar MX. '
      'La colonna Tempo resta fissa; i diaframmi scorrono orizzontalmente. Gli EV dipendono esclusivamente dalla coppia '
      'tempo/diaframma e non dagli ISO.",'
)
s, n = answer_re.subn(native_answer, s, count=1)
if n != 1:
    raise SystemExit('v0.4.7: Minolta EV answer replacement failed')

color_marker = '    private static final int RED = Color.rgb(124, 31, 31);\n'
constants = '''

    private static final String EV_TABLE_QUESTION = "Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?";
    private static final String[] EV_APERTURES = {"f/2,8", "f/3,5", "f/4", "f/5,6", "f/8", "f/11", "f/16", "f/22"};
    private static final String[] EV_TIMES = {
            "1 s ★●", "1/2 ★●", "1/4 ★", "1/5 ●", "1/8 ★", "1/10 ●", "1/15 ★", "1/25 ●",
            "1/30 ★", "1/50 ●", "1/60 ★", "1/100 ●", "1/125 ★", "1/250 ★●", "1/500 ★●"
    };
    private static final String[][] EV_VALUES = {
            {"3,0", "3,6", "4,0", "5,0", "6,0", "6,9", "8,0", "8,9"},
            {"4,0", "4,6", "5,0", "6,0", "7,0", "7,9", "9,0", "9,9"},
            {"5,0", "—", "6,0", "7,0", "8,0", "8,9", "10,0", "10,9"},
            {"—", "5,9", "6,3", "7,3", "8,3", "9,2", "10,3", "11,2"},
            {"6,0", "—", "7,0", "8,0", "9,0", "9,9", "11,0", "11,9"},
            {"—", "6,9", "7,3", "8,3", "9,3", "10,2", "11,3", "12,2"},
            {"6,9", "—", "7,9", "8,9", "9,9", "10,8", "11,9", "12,8"},
            {"—", "8,3", "8,6", "9,6", "10,6", "11,6", "12,6", "13,6"},
            {"7,9", "—", "8,9", "9,9", "10,9", "11,8", "12,9", "13,8"},
            {"—", "9,3", "9,6", "10,6", "11,6", "12,6", "13,6", "14,6"},
            {"8,9", "—", "9,9", "10,9", "11,9", "12,8", "13,9", "14,8"},
            {"—", "10,3", "10,6", "11,6", "12,6", "13,6", "14,6", "15,6"},
            {"9,9", "—", "11,0", "11,9", "13,0", "13,9", "15,0", "15,9"},
            {"10,9", "11,6", "12,0", "12,9", "14,0", "14,9", "16,0", "16,9"},
            {"11,9", "12,6", "13,0", "13,9", "15,0", "15,9", "17,0", "17,9"}
    };
'''
if color_marker not in s:
    raise SystemExit('v0.4.7: color constants marker missing')
s = s.replace(color_marker, color_marker + constants, 1)

old_faq = '''    private LinearLayout faqCard(String question,String answerText){ LinearLayout c=card(); c.setPadding(dp(14),dp(8),dp(14),dp(8)); TextView q=text("›  "+question,16,WARM,true); q.setPadding(0,dp(9),0,dp(9)); if("''' + table_question + '''".equals(question)){ TextView a=text(answerText,11,Color.rgb(218,207,190),false); a.setTypeface(Typeface.MONOSPACE); a.setLineSpacing(0f,1.15f); a.setPadding(dp(2),dp(4),dp(8),dp(12)); a.setHorizontallyScrolling(true); a.setTextIsSelectable(true); HorizontalScrollView hs=new HorizontalScrollView(this); hs.setFillViewport(false); hs.setHorizontalScrollBarEnabled(true); hs.addView(a); hs.setVisibility(View.GONE); q.setOnClickListener(v->{ boolean open=hs.getVisibility()==View.VISIBLE; hs.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); }); c.addView(q); c.addView(hs); return c; } TextView a=text(answerText,14,Color.rgb(218,207,190),false); a.setLineSpacing(0f,1.12f); a.setPadding(dp(2),dp(4),dp(2),dp(12)); a.setVisibility(View.GONE); q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); }); c.addView(q); c.addView(a); return c; }'''

new_faq = '''    private LinearLayout faqCard(String question,String answerText){
        LinearLayout c=card();
        c.setPadding(dp(14),dp(8),dp(14),dp(8));
        TextView q=text("›  "+question,16,WARM,true);
        q.setPadding(0,dp(9),0,dp(9));
        if(EV_TABLE_QUESTION.equals(question)){
            LinearLayout a=evTableView();
            a.setVisibility(View.GONE);
            q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
            c.addView(q);
            c.addView(a);
            return c;
        }
        TextView a=text(answerText,14,Color.rgb(218,207,190),false);
        a.setLineSpacing(0f,1.12f);
        a.setPadding(dp(2),dp(4),dp(2),dp(12));
        a.setVisibility(View.GONE);
        q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
        c.addView(q);
        c.addView(a);
        return c;
    }

    private LinearLayout evTableView(){
        if(EV_TIMES.length!=EV_VALUES.length) throw new IllegalStateException("EV table row mismatch");
        LinearLayout answer=new LinearLayout(this);
        answer.setOrientation(LinearLayout.VERTICAL);
        answer.setPadding(dp(2),dp(3),dp(2),dp(12));

        TextView hint=text("VALORI EV · scorri i diaframmi  →",12,MUTED,true);
        hint.setPadding(0,0,0,dp(8));
        answer.addView(hint);

        LinearLayout table=new LinearLayout(this);
        table.setOrientation(LinearLayout.HORIZONTAL);
        table.setBaselineAligned(false);

        LinearLayout fixedColumn=new LinearLayout(this);
        fixedColumn.setOrientation(LinearLayout.VERTICAL);
        fixedColumn.addView(evCell("Tempo",88,42,true,false));
        for(int i=0;i<EV_TIMES.length;i++) fixedColumn.addView(evCell(EV_TIMES[i],88,40,false,(i&1)==1));
        table.addView(fixedColumn,new LinearLayout.LayoutParams(dp(88),ViewGroup.LayoutParams.WRAP_CONTENT));

        HorizontalScrollView apertureScroller=new HorizontalScrollView(this);
        apertureScroller.setFillViewport(false);
        apertureScroller.setHorizontalScrollBarEnabled(true);
        apertureScroller.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);

        LinearLayout movingGrid=new LinearLayout(this);
        movingGrid.setOrientation(LinearLayout.VERTICAL);
        movingGrid.addView(evRow(EV_APERTURES,true,false));
        for(int i=0;i<EV_VALUES.length;i++){
            if(EV_VALUES[i].length!=EV_APERTURES.length) throw new IllegalStateException("EV table column mismatch at row "+i);
            movingGrid.addView(evRow(EV_VALUES[i],false,(i&1)==1));
        }
        apertureScroller.addView(movingGrid,new ViewGroup.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        table.addView(apertureScroller,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        answer.addView(table,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView legend=text("★  Rolleiflex 2.8 E2\\n●  Rolleiflex 3.5 Tessar MX\\n\\nGli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.",13,Color.rgb(218,207,190),false);
        legend.setLineSpacing(0f,1.15f);
        legend.setPadding(0,dp(11),0,0);
        answer.addView(legend);
        return answer;
    }

    private LinearLayout evRow(String[] values,boolean header,boolean alternate){
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        int height=header?42:40;
        for(String value:values) row.addView(evCell(value,60,height,header,alternate));
        return row;
    }

    private TextView evCell(String value,int widthDp,int heightDp,boolean header,boolean alternate){
        TextView cell=text(value,header?12:12,header?Color.rgb(241,220,187):WARM,header);
        cell.setGravity(Gravity.CENTER);
        cell.setPadding(dp(4),0,dp(4),0);
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(header?Color.rgb(53,42,30):(alternate?Color.rgb(31,31,31):Color.rgb(23,23,23)));
        bg.setStroke(dp(1),Color.rgb(75,70,63));
        cell.setBackground(bg);
        cell.setLayoutParams(new LinearLayout.LayoutParams(dp(widthDp),dp(heightDp)));
        return cell;
    }'''

if old_faq not in s:
    raise SystemExit('v0.4.7: ASCII faqCard marker missing')
s = s.replace(old_faq, new_faq, 1)

p.write_text(s, encoding='utf-8')
out = p.read_text(encoding='utf-8')

for marker in (
    'private static final String[][] EV_VALUES',
    'private LinearLayout evTableView()',
    'LinearLayout fixedColumn',
    'HorizontalScrollView apertureScroller',
    'VALORI EV · scorri i diaframmi  →',
    '★  Rolleiflex 2.8 E2',
    '●  Rolleiflex 3.5 Tessar MX',
    'EV_TABLE_QUESTION.equals(question)',
):
    if marker not in out:
        raise SystemExit('v0.4.7 guard missing: ' + marker)

if 'Typeface.MONOSPACE' in out or '| Tempo | f/2,8 |' in out:
    raise SystemExit('v0.4.7: ASCII EV table renderer survived')
if out.count('private LinearLayout evTableView()') != 1:
    raise SystemExit('v0.4.7: native EV table method count invalid')

print('Darkroom v0.4.7 native EV table patch ready')
print('ev_table_renderer=NATIVE_ANDROID_GRID')
print('fixed_time_column=PASS')
print('horizontal_aperture_scroll=PASS')
print('ascii_table_removed=PASS')
