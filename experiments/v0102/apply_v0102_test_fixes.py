#!/usr/bin/env python3
from pathlib import Path
import re, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.10.2 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count)); print('v0.10.2 OK', label, flush=True)
def rrep(p, pattern, replacement, label):
    s=rd(p); out,n=re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
    if n != 1: raise SystemExit(f'v0.10.2 {label}: regex trovata {n} volte')
    wr(p,out); print('v0.10.2 OK',label,flush=True)

# -----------------------------------------------------------------------------
# Versione 0.10.2 / code 47
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.10.1"', 'VERSION_NAME = "0.10.2"', 'version name build')
rep(build, 'VERSION_CODE = "46"', 'VERSION_CODE = "47"', 'version code build')
rep(build, '[Darkroom v0.10.1]', '[Darkroom v0.10.2]', 'build log tag')
rep(build, r'versionCode\s+46\b', r'versionCode\s+47\b', 'preflight code regex')
rep(build, r'0\.10\.1', r'0\.10\.2', 'preflight name regex')
rep(build, 'versionCode 46 / versionName 0.10.1', 'versionCode 47 / versionName 0.10.2', 'preflight message')
rep(build, 'Preflight v0.10.1 OK', 'Preflight v0.10.2 OK', 'preflight log')
rep(gradle, "versionCode 46\n        versionName '0.10.1'", "versionCode 47\n        versionName '0.10.2'", 'gradle version')
rep(manifest, 'android:versionCode="46"\n    android:versionName="0.10.1"', 'android:versionCode="47"\n    android:versionName="0.10.2"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.1";', 'private static final String APP_VERSION = "0.10.2";', 'UI version')

# -----------------------------------------------------------------------------
# 1) CORREZIONE GLOBALE: sia scelta sia ANNULLA tornano al PIANO DI STAMPA.
# -----------------------------------------------------------------------------
global_dialog = r'''    private void showGlobalCorrectionDialog() {
        if (darkroomMode || armed) return;
        ensureExposureRecipeBase();
        final Dialog dialog=new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel=new LinearLayout(this); panel.setOrientation(LinearLayout.VERTICAL); panel.setPadding(dp(18),dp(16),dp(18),dp(18)); panel.setBackground(roundRect(CARD,14,1,BORDER));
        panel.addView(text("CORREZIONE GLOBALE",19,TEXT_PRIMARY,true),lp(-1,-2));
        TextView note=text("Schiarisce o scurisce l’intera ricetta mantenendo invariati i rapporti relativi tra base, DODGE, BURN e SPLIT GRADE.",12,MUTED,false); note.setPadding(0,dp(5),0,dp(12)); panel.addView(note,lp(-1,-2));
        int current=exposureRecipe.globalQuarterStops;
        int[] qs={-1,0,1}; String[] labels={"−¼ STOP","0 · NESSUNA","+¼ STOP"};
        for(int x=0;x<qs.length;x++){
            final int q=qs[x];
            Button b=compactButton((current==q?"✓  ":"")+labels[x]);
            b.setTextColor(Color.WHITE); b.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
            b.setOnClickListener(v->{
                int delta=q-exposureRecipe.globalQuarterStops;
                scaleWholeRecipe(delta);
                exposureRecipe.globalQuarterStops=q;
                exposureRecipe.operationalBaseMs=printWidthMs;
                persistExposureRecipe();
                persistPrintSequence();
                dialog.dismiss();
                showPrintSequenceDialog();
            });
            panel.addView(b,margin(lp(-1,dp(50)),0,x==0?0:7,0,0));
        }
        Button cancel=compactButton("ANNULLA");
        cancel.setTextColor(Color.WHITE); cancel.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));
        cancel.setOnClickListener(v->{dialog.dismiss();showPrintSequenceDialog();});
        panel.addView(cancel,margin(lp(-1,dp(48)),0,10,0,0));
        dialog.setContentView(panel); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.92f),ViewGroup.LayoutParams.WRAP_CONTENT);
    }

'''
rrep(main, r'    private void showGlobalCorrectionDialog\(\) \{.*?(?=    private String recipeOriginalLabel\()', global_dialog, 'global correction returns to plan')

# -----------------------------------------------------------------------------
# 2) PROVINO CON DISPLAY SPENTO: la scelta striscia resta pendente fino alla scelta vera.
# -----------------------------------------------------------------------------
rep(main, '    private long transientCompletionUntilMs = 0L;\n', '    private long transientCompletionUntilMs = 0L;\n    private boolean testChooserOpen = false;\n', 'test chooser runtime guard')

# Ogni ritorno in primo piano verifica un provino completato mentre lo schermo era spento.
rrep(main,
     r'(@Override protected void onResume\(\) \{\n        super\.onResume\(\);.*?        restoreRuntimeState\(\);)',
     r'''\1
        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);''',
     'resume pending test chooser')

rep(main,
'''        if (armed || mode != MODE_TEST || isFinishing()) return;''',
'''        if (armed || mode != MODE_TEST || isFinishing() || !hasWindowFocus() || testChooserOpen) return;''',
    'chooser only when visible')

rep(main,
'''        if (ui.getLong("lastTestChooserShownAt", 0L) >= testAt) return;\n        ui.edit().putLong("lastTestChooserShownAt", testAt).apply();''',
'''        // Il timestamp viene marcato solo quando l'utente sceglie davvero una striscia.\n        // Se il provino finisce con display spento o si sceglie NON ORA, resta pendente.\n        if (ui.getLong("lastTestChooserShownAt", 0L) >= testAt) return;''',
    'chooser pending until actual choice')

rep(main,
'''        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {\n            int imported = strips[which];''',
'''        testChooserOpen = true;\n        showAppChoiceDialog("PROVINO COMPLETATO — SCEGLI LA STRISCIA", choices, which -> {\n            int imported = strips[which];\n            ui.edit().putLong("lastTestChooserShownAt", testAt).apply();''',
    'chooser marks actual selection')

# Il dialog generico libera il guard anche con NON ORA / back.
rep(main,
'''        dialog.setContentView(panel);\n        Window w = dialog.getWindow();''',
'''        dialog.setContentView(panel);\n        dialog.setOnDismissListener(d -> {\n            if (title != null && title.startsWith("PROVINO COMPLETATO")) testChooserOpen = false;\n        });\n        Window w = dialog.getWindow();''',
    'chooser dismiss guard', count=1)

# -----------------------------------------------------------------------------
# 3) SAFELIGHT PROVINO: OFF al primo avvio, resta OFF in tutte le pause, ON solo a fine provino.
# -----------------------------------------------------------------------------
old_cycle_safe = '''                            if (mode == MODE_PRINT && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) dimSafelightForExposure();
                            else if (!cycleSafelightCaptured) captureAndDimSafelightForCycle();'''
new_cycle_safe = '''                            if (mode == MODE_TEST && !cycleSafelightCaptured) {
                                // Il provino è un unico ciclo operativo: rossa OFF dalla prima
                                // esposizione fino all'ultima, senza lampeggiare durante le pause.
                                cycleSafelightCaptured = true;
                                restoreSafelightAfterCycle = true;
                                setSafelightConfirmed(false);
                                TechnicalLog.add(this, techSessionId, "PROVINO — SAFELIGHT OFF dalla prima striscia fino a fine provino");
                            } else if (mode == MODE_PRINT && (printBaseDone || (printSequence != null && printSequence.hasSplit() && splitStage > 0))) {
                                dimSafelightForExposure();
                            } else if (!cycleSafelightCaptured) {
                                captureAndDimSafelightForCycle();
                            }'''
rep(service, old_cycle_safe, new_cycle_safe, 'test safelight one continuous OFF cycle')

rep(service,
'''            TechnicalLog.add(this, techSessionId, "SAFELIGHT ripristinata ON perché era ON prima del ciclo");''',
'''            TechnicalLog.add(this, techSessionId, mode == MODE_TEST\n                    ? "PROVINO concluso — SAFELIGHT ripristinata ON"\n                    : "SAFELIGHT ripristinata ON perché era ON prima del ciclo");''',
    'test safelight final ON log')

# -----------------------------------------------------------------------------
# 4) SAFELIGHT ON/OFF MANUALE: elimina la finestra intermittente all'avvio interblocco.
# Se il monitor parte mentre l'ingranditore è già ON, la rossa viene gestita subito.
# -----------------------------------------------------------------------------
rep(service,
'''        interlockTask = io.scheduleWithFixedDelay(this::interlockPollOnce, 0, 500, TimeUnit.MILLISECONDS);''',
'''        interlockTask = io.scheduleWithFixedDelay(this::interlockPollOnce, 0, 300, TimeUnit.MILLISECONDS);''',
    'manual interlock faster polling')

old_baseline = '''            if (lastInterlockPrimaryState.isEmpty()) {
                lastInterlockPrimaryState = primary;
                updateNotification("Interblocco attivo • stato manuale luce rossa rispettato");
                TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline " + primary.toUpperCase(Locale.ITALY) + " • nessun comando safelight");
                return;
            }'''
new_baseline = '''            if (lastInterlockPrimaryState.isEmpty()) {
                lastInterlockPrimaryState = primary;
                if ("on".equals(primary)) {
                    // Prima il baseline ON veniva ignorato: se il monitor si avviava proprio
                    // mentre l'utente premeva il pulsante fisico, la rossa poteva restare ON.
                    String safeState = SonoffHttp.infoQuick(safelight, 1400);
                    interlockRestoreSafelight = "on".equals(safeState);
                    if (interlockRestoreSafelight) {
                        setSafelightConfirmed(false);
                        TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline ON — rossa spenta immediatamente");
                    } else {
                        TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline ON — rossa già OFF");
                    }
                    updateNotification("Ingranditore ON • luce rossa " + (interlockRestoreSafelight ? "spenta automaticamente" : "già OFF"));
                } else {
                    interlockRestoreSafelight = false;
                    updateNotification("Interblocco attivo • ingranditore OFF");
                    TechnicalLog.add(this, techSessionId, "INTERBLOCCO baseline " + primary.toUpperCase(Locale.ITALY) + " • nessun comando safelight");
                }
                return;
            }'''
rep(service, old_baseline, new_baseline, 'manual interlock baseline ON handled')

# -----------------------------------------------------------------------------
# Verifiche sorgente
# -----------------------------------------------------------------------------
checks = {
    build:['VERSION_NAME = "0.10.2"','VERSION_CODE = "47"'],
    main:['private static final String APP_VERSION = "0.10.2"','testChooserOpen','lastTestChooserShownAt','showPrintSequenceDialog();'],
    service:['PROVINO — SAFELIGHT OFF dalla prima striscia fino a fine provino','PROVINO concluso — SAFELIGHT ripristinata ON','INTERBLOCCO baseline ON — rossa spenta immediatamente','scheduleWithFixedDelay(this::interlockPollOnce, 0, 300']
}
for p,needles in checks.items():
    t=rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.2 verifica fallita: {needle} in {p}')
print('v0.10.2 TUTTE LE VERIFICHE SORGENTE OK', flush=True)
