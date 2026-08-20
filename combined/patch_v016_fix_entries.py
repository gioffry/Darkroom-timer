from pathlib import Path
p=Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')
s=p.read_text(encoding='utf-8')
a='    private LinearLayout buildPrintPanel() {\n        LinearLayout box = card();'
b='    private LinearLayout buildPrintPanel() {\n        LinearLayout box = card();\n        Button resizePrint = compactButton("RIDIMENSIONA STAMPA");\n        resizePrint.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "resize")));\n        box.addView(resizePrint, margin(lp(-1, dp(46)), 0, 0, 0, 10));'
if 'RIDIMENSIONA STAMPA' not in s:
    if a not in s: raise SystemExit('print marker missing')
    s=s.replace(a,b,1)
a='    private LinearLayout buildTestPanel() {\n        LinearLayout outer = new LinearLayout(this);\n        outer.setOrientation(LinearLayout.VERTICAL);'
b='    private LinearLayout buildTestPanel() {\n        LinearLayout outer = new LinearLayout(this);\n        outer.setOrientation(LinearLayout.VERTICAL);\n        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");\n        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));\n        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));'
if 'IMPOSTA INGRANDIMENTO' not in s:
    if a not in s: raise SystemExit('test marker missing')
    s=s.replace(a,b,1)
p.write_text(s,encoding='utf-8')
