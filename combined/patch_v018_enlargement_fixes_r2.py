from pathlib import Path

root = Path('combined/src/main/java/it/darkroom/timer')
main = root / 'MainActivity.java'
enlargement = root / 'EnlargementActivity.java'
log_entry = root / 'LogEntry.java'
log_store = root / 'LogStore.java'

# -----------------------------------------------------------------------------
# MAIN ACTIVITY
# -----------------------------------------------------------------------------
s = main.read_text(encoding='utf-8')

# CREA must refresh the active plan in place and explicitly select STAMPA.
old = '''        SharedPreferences ep = getSharedPreferences("ui", MODE_PRIVATE);
        if (ep.getBoolean("enlargementReloadPending", false)) {
            ep.edit().remove("enlargementReloadPending").apply();
            printWidthMs = ep.getInt("printWidthMs", printWidthMs);
            exposureRecipe = ExposureRecipe.decode(ep.getString("exposureRecipe", ""));
            printSequence = PrintSequence.decode(ep.getString("printSequence", ""));
            recreate();
            return;
        }'''
new = '''        SharedPreferences ep = getSharedPreferences("ui", MODE_PRIVATE);
        if (ep.getBoolean("enlargementReloadPending", false)) {
            printWidthMs = ep.getInt("printWidthMs", printWidthMs);
            exposureRecipe = ExposureRecipe.decode(ep.getString("exposureRecipe", ""));
            printSequence = PrintSequence.decode(ep.getString("printSequence", ""));
            mode = MODE_PRINT;
            ep.edit().remove("enlargementReloadPending").putInt("mode", MODE_PRINT).apply();
            if (printTimeText != null) printTimeText.setText(formatTime(printWidthMs));
            updatePrintSequenceUi();
            applyModeUi();
        }'''
if old not in s:
    raise SystemExit('v018 r2: enlargement onResume block not found')
s = s.replace(old, new, 1)

# Remove the v0.1.7 generic/global resize box from the LOG page.
start = s.find('        LinearLayout enlargementLogBox = card();')
if start < 0:
    raise SystemExit('v018 r2: global resize box start not found')
end_marker = '        if (!enlargementNote.isEmpty()) enlargementLogBox.addView(text(enlargementNote, 12, MUTED, false));\n'
end = s.find(end_marker, start)
if end < 0:
    raise SystemExit('v018 r2: global resize box end not found')
s = s[:start] + s[end + len(end_marker):]
s = s.replace('        outer.addView(enlargementLogBox, margin(lp(-1,-2),0,0,0,10));\n', '', 1)
s = s.replace('        logPanel.addView(enlargementLogBox, margin(lp(-1,-2),0,0,0,10));\n', '', 1)

# Snapshot the enlargement data whenever a LogEntry is created.
# Use a stable marker that survives the Timer-only cleanup of paper chemistry fields.
log_marker = '        e.timestamp = anchor;'
if log_marker not in s:
    raise SystemExit('v018 r2: log timestamp marker not found')
s = s.replace(log_marker, log_marker + '\n        e.enlargementMeta = p.getString("enlargementMeta", "");', 1)

# Put RIDIMENSIONA STAMPA inside each individual STAMPA entry in the session dialog.
sg = s.find('    private void showLogGroup(final LogGroup group) {')
if sg < 0:
    raise SystemExit('v018 r2: showLogGroup not found')
sg_end = s.find('\n    private ', sg + 20)
if sg_end < 0:
    raise SystemExit('v018 r2: showLogGroup end not found')
seg = s[sg:sg_end]
needle = '''            step.setClickable(true);
            step.setFocusable(true);'''
insert = '''            if (item.exposureMs > 0) {
                Button resizeEntry = compactButton("RIDIMENSIONA STAMPA");
                resizeEntry.setTextColor(Color.WHITE);
                resizeEntry.setBackground(roundRect(darkroomMode ? Color.rgb(45,0,0) : Color.rgb(55,60,64), 8, 0, 0));
                resizeEntry.setOnClickListener(v -> {
                    SharedPreferences.Editor edit = getSharedPreferences("ui", MODE_PRIVATE).edit()
                            .putInt("printWidthMs", item.exposureMs)
                            .putString("printSequence", item.printSequence == null ? "" : item.printSequence)
                            .putString("exposureRecipe", item.recipeState == null ? "" : item.recipeState)
                            .putInt("mode", MODE_PRINT);
                    if (item.enlargementMeta != null && !item.enlargementMeta.trim().isEmpty()) {
                        edit.putString("enlargementMeta", item.enlargementMeta);
                    } else {
                        edit.remove("enlargementMeta");
                    }
                    edit.apply();
                    dialog.dismiss();
                    startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "resize"));
                });
                step.addView(resizeEntry, margin(lp(-1, dp(44)), 0, dp(8), 0, 0));
            }
            step.setClickable(true);
            step.setFocusable(true);'''
if needle not in seg:
    raise SystemExit('v018 r2: individual log entry marker not found')
seg = seg.replace(needle, insert, 1)
s = s[:sg] + seg + s[sg_end:]
main.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# LOG MODEL / STORE
# Add one final tagged column. Old rows remain readable regardless of their
# historical column count (including Timer versions that removed chemistry).
# -----------------------------------------------------------------------------
s = log_entry.read_text(encoding='utf-8')
if 'public String enlargementMeta' not in s:
    pos = s.rfind('\n}')
    if pos < 0:
        raise SystemExit('v018 r2: LogEntry closing brace not found')
    field = '''\n    /** Snapshot dell’ingrandimento associato a questa specifica stampa. */
    public String enlargementMeta = "";'''
    s = s[:pos] + field + s[pos:]
log_entry.write_text(s, encoding='utf-8')

s = log_store.read_text(encoding='utf-8')

# Parse the optional tagged last column without relying on a fixed schema index.
parse_marker = '                result.add(e);'
if parse_marker not in s:
    raise SystemExit('v018 r2: LogStore result.add marker not found')
parse_code = '''                if (f.length > 0) {
                    try {
                        String tagged = dec(f[f.length - 1]);
                        if (tagged.startsWith("ENL|")) e.enlargementMeta = tagged.substring(4);
                    } catch (Exception ignored) {}
                }
                result.add(e);'''
s = s.replace(parse_marker, parse_code, 1)

# Append the tagged enlargement column at the end of every newly serialized row.
loop_start = s.find('        for (LogEntry e : list) {')
if loop_start < 0:
    raise SystemExit('v018 r2: LogStore write loop not found')
loop_end_marker = '\n        }\n        context.getSharedPreferences'
loop_end = s.find(loop_end_marker, loop_start)
if loop_end < 0:
    raise SystemExit('v018 r2: LogStore write loop end not found')
append_code = '''
            out.append('\\t').append(enc("ENL|" + (e.enlargementMeta == null ? "" : e.enlargementMeta)));'''
s = s[:loop_end] + append_code + s[loop_end:]
log_store.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# ENLARGEMENT ACTIVITY
# -----------------------------------------------------------------------------
s = enlargement.read_text(encoding='utf-8')

# User always prints landscape: explicit dimensions, no invert control.
old_fields = '''r.addView(w);r.addView(h);Button rotate=b("↔ INVERTI LARGHEZZA / ALTEZZA");rotate.setOnClickListener(v->{String x=w.getText().toString();w.setText(h.getText().toString());h.setText(x);});r.addView(rotate,new LinearLayout.LayoutParams(-1,dp(46)));'''
new_fields = '''r.addView(t("LARGHEZZA CARTA (cm)",13));r.addView(w);r.addView(t("ALTEZZA CARTA (cm)",13));r.addView(h);TextView landscape=t("ORIENTAMENTO · ORIZZONTALE",12);landscape.setTextColor(Color.rgb(155,155,155));r.addView(landscape);'''
if old_fields not in s:
    raise SystemExit('v018 r2: invert control not found')
s = s.replace(old_fields, new_fields, 1)

preset = 'w.setText(fmt(PD[pos][0]));h.setText(fmt(PD[pos][1]));'
if preset not in s:
    raise SystemExit('v018 r2: paper preset marker not found')
s = s.replace(preset, 'w.setText(fmt(Math.max(PD[pos][0],PD[pos][1])));h.setText(fmt(Math.min(PD[pos][0],PD[pos][1])));', 1)

calc = '''double W=Double.parseDouble(w.getText().toString().replace(',','.'))*10,H=Double.parseDouble(h.getText().toString().replace(',','.'))*10;'''
if calc not in s:
    raise SystemExit('v018 r2: calculation marker not found')
s = s.replace(calc, '''double aw=Double.parseDouble(w.getText().toString().replace(',','.'))*10,ah=Double.parseDouble(h.getText().toString().replace(',','.'))*10;double W=Math.max(aw,ah),H=Math.min(aw,ah);''', 1)

# Confirmation dialog: same visual language as the established Timer cards.
start = s.find(' void confirmDerived(String msg,final Runnable yes){')
if start < 0:
    raise SystemExit('v018 r2: confirmDerived start not found')
end = s.find('\n void derive(', start)
if end < 0:
    raise SystemExit('v018 r2: confirmDerived end not found')
confirm = r''' void confirmDerived(String msg,final Runnable yes){
  final Dialog d=new Dialog(this);d.requestWindowFeature(Window.FEATURE_NO_TITLE);
  ScrollView sc=new ScrollView(this);sc.setFillViewport(true);
  LinearLayout q=new LinearLayout(this);q.setOrientation(LinearLayout.VERTICAL);q.setPadding(dp(20),dp(18),dp(20),dp(20));q.setBackground(bg(Color.rgb(18,22,24),14));sc.addView(q,new ScrollView.LayoutParams(-1,-2));
  TextView title=t("RIDIMENSIONA STAMPA",22);title.setTypeface(null,android.graphics.Typeface.BOLD);q.addView(title);
  TextView lead=t("NUOVA STAMPA DERIVATA",13);lead.setTextColor(Color.rgb(82,190,82));lead.setTypeface(null,android.graphics.Typeface.BOLD);lead.setPadding(0,dp(2),0,dp(12));q.addView(lead);
  String[] blocks=msg.split("\\n\\n",2);
  TextView l1=t("INGRANDIMENTO",12);l1.setTextColor(Color.rgb(180,180,180));l1.setTypeface(null,android.graphics.Typeface.BOLD);q.addView(l1);
  LinearLayout c1=new LinearLayout(this);c1.setOrientation(LinearLayout.VERTICAL);c1.setPadding(dp(14),dp(10),dp(14),dp(10));c1.setBackground(bg(Color.rgb(48,53,56),10));c1.addView(t(blocks.length>0?blocks[0]:msg,14));q.addView(c1,new LinearLayout.LayoutParams(-1,-2));
  if(blocks.length>1){TextView l2=t("TEMPI E COMPENSAZIONE",12);l2.setTextColor(Color.rgb(180,180,180));l2.setTypeface(null,android.graphics.Typeface.BOLD);l2.setPadding(0,dp(12),0,0);q.addView(l2);LinearLayout c2=new LinearLayout(this);c2.setOrientation(LinearLayout.VERTICAL);c2.setPadding(dp(14),dp(10),dp(14),dp(10));c2.setBackground(bg(Color.rgb(48,53,56),10));c2.addView(t(blocks[1],14));q.addView(c2,new LinearLayout.LayoutParams(-1,-2));}
  Button ok=b("CREA");ok.setTextColor(Color.WHITE);ok.setBackground(bg(Color.rgb(32,104,43),10));
  Button no=b("ANNULLA");no.setTextColor(Color.WHITE);no.setBackground(bg(Color.rgb(55,60,64),10));
  ok.setOnClickListener(v->{d.dismiss();yes.run();});no.setOnClickListener(v->d.dismiss());q.addView(ok,new LinearLayout.LayoutParams(-1,dp(54)));q.addView(no,new LinearLayout.LayoutParams(-1,dp(48)));
  d.setContentView(sc);d.show();Window ww=d.getWindow();if(ww!=null){ww.setBackgroundDrawableResource(android.R.color.transparent);ww.setLayout((int)(getResources().getDisplayMetrics().widthPixels*.94f),ViewGroup.LayoutParams.WRAP_CONTENT);}
 }'''
s = s[:start] + confirm + s[end:]

# Derived plan becomes the active STAMPA plan; no navigation reset to PROVINO.
old_chain = '.putString("enlargementLastLog",note).putBoolean("enlargementReloadPending",true).apply();'
if old_chain not in s:
    raise SystemExit('v018 r2: derive preference chain marker not found')
s = s.replace(old_chain, '.putString("enlargementLastLog",note).putInt("mode",0).putBoolean("enlargementReloadPending",true).apply();', 1)
s = s.replace('Toast.makeText(this,"Ricetta derivata creata · tempi a 0,5 s",Toast.LENGTH_LONG).show();', 'Toast.makeText(this,"Stampa ridimensionata · tempi a 0,5 s",Toast.LENGTH_LONG).show();', 1)

enlargement.write_text(s, encoding='utf-8')
print('v018 r2 enlargement fixes applied')
