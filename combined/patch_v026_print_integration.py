#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
main = root / 'src/main/java/it/darkroom/timer/MainActivity.java'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.2.6 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.2.6 OK', label, flush=True)
def replace_method(p, start, end, new_block, label):
    s = rd(p)
    a = s.find(start)
    if a < 0: raise SystemExit(f'v0.2.6 {label}: inizio non trovato')
    b = s.find(end, a)
    if b < 0: raise SystemExit(f'v0.2.6 {label}: fine non trovata')
    wr(p, s[:a] + new_block + s[b:])
    print('v0.2.6 OK', label, flush=True)

s0 = rd(main)
for needle in [
    'private static final String APP_VERSION = "0.13.8";',
    'private void showPrintSequenceDialog()',
    'private void showSplitGradeEditor(final boolean creating)',
    'private void createSplitPrintFromProvino()',
    'private LogEntry newEntryFromSession()',
    'private void useLogEntryForPrint(LogEntry entry)',
]:
    if needle not in s0:
        raise SystemExit('v0.2.6 base v0.2.5 non riconosciuta: ' + needle)

rep(main, 'private static final String APP_VERSION = "0.13.8";',
          'private static final String APP_VERSION = "0.13.9";', 'Timer footer version')

# -----------------------------------------------------------------------------
# Revision-safe navigation helpers and the only Split Grade management surface.
# ----------------------------------------------------------------------------
helpers = r'''    private SharedPreferences printRevisionPrefs() {
        return getSharedPreferences("print_revision", MODE_PRIVATE);
    }

    private boolean hasPrintRevisionDraft() {
        return printRevisionPrefs().getBoolean("active", false);
    }

    private void capturePrintRevisionDraft(String reason) {
        if (hasPrintRevisionDraft()) return;
        SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);
        printRevisionPrefs().edit().clear()
                .putBoolean("active", true)
                .putString("reason", reason == null ? "" : reason)
                .putLong("sourceLogId", ui.getLong("activeSourceLogId", 0L))
                .putString("previousPrintSequence", printSequence == null ? "" : printSequence.encode())
                .putString("previousRecipeState", exposureRecipe == null ? "" : exposureRecipe.encode())
                .putInt("previousPrintMs", printWidthMs)
                .apply();
    }

    private void clearPrintRevisionDraft() {
        printRevisionPrefs().edit().clear().apply();
    }

    private void clearRevisionSessionMetadata() {
        getSharedPreferences("log_session", MODE_PRIVATE).edit()
                .remove("lastSplitTimeOrigin")
                .remove("lastSplitSoftChosenStrip")
                .remove("lastSplitHardChosenStrip")
                .remove("lastRevisionPreviousId")
                .remove("lastRevisionPreviousRecipeState")
                .remove("lastRevisionPreviousPrintSequence")
                .remove("lastRevisionReason")
                .apply();
    }

    private void commitPrintRevisionMetadata(String origin) {
        SharedPreferences r = printRevisionPrefs();
        boolean active = r.getBoolean("active", false);
        getSharedPreferences("log_session", MODE_PRIVATE).edit()
                .putString("lastSplitTimeOrigin", origin == null ? "" : origin)
                .putInt("lastSplitSoftChosenStrip", splitSoftChosenStrip)
                .putInt("lastSplitHardChosenStrip", splitHardChosenStrip)
                .putLong("lastRevisionPreviousId", active ? r.getLong("sourceLogId", 0L) : 0L)
                .putString("lastRevisionPreviousRecipeState", active ? r.getString("previousRecipeState", "") : "")
                .putString("lastRevisionPreviousPrintSequence", active ? r.getString("previousPrintSequence", "") : "")
                .putString("lastRevisionReason", active ? r.getString("reason", "") : "")
                .apply();
        clearPrintRevisionDraft();
        getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("activeSourceLogId", 0L).apply();
    }

    private void rememberTestStateForRevision() {
        splitReturnFilterType = testBaseFilterType;
        splitReturnFilterValue = testBaseFilterValue;
        splitReturnTestWidthMs = testWidthMs;
    }

    private void persistRevisionTestSetup() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(testBaseFilterType))
                .putInt("testBaseFilterValue", ExposureRecipe.snap5(testBaseFilterValue))
                .apply();
        persistTestBaseFilter();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setMode(MODE_TEST);
    }

    private void beginSingleRevisionFromPrint() {
        if (armed) return;
        capturePrintRevisionDraft("RIFAI_PROVINO_SINGOLO");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SINGLE;
        testWidthMs = snap(printWidthMs, 500, 30_000);
        if (exposureRecipe != null && exposureRecipe.hasBase()) {
            testBaseFilterType = ExposureRecipe.normalizeFilter(exposureRecipe.filterType);
            testBaseFilterValue = ExposureRecipe.snap5(exposureRecipe.filterValue);
        }
        persistRevisionTestSetup();
        setStatusPresentation("RIFAI PROVINO SINGOLO",
                "Filtro e tempo correnti sono solo valori iniziali modificabili. La ricetta precedente resta intatta finché non scegli una nuova striscia.", BLUE);
    }

    private void beginSplitFromSingleWithProvino() {
        if (armed) return;
        capturePrintRevisionDraft("SINGOLA_A_SPLIT_PROVINO");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SPLIT_SOFT;
        splitSoftYellow = 60;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        splitHardMagenta = 180;
        invalidateSplitHardChoice();
        // T/2 is deliberately only a convenient editable starting point, never a conversion.
        testWidthMs = snap(Math.max(500, printWidthMs / 2), 500, 30_000);
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        persistRevisionTestSetup();
        setStatusPresentation("SPLIT GRADE — TROVA I TEMPI",
                "Il tempo singolo precedente è usato solo per suggerire un centro iniziale T/2, liberamente modificabile. Non è una conversione né una compensazione.", BLUE);
    }

    private void beginSplitRevisionFromPrint(boolean hardOnly) {
        if (armed || printSequence == null || !printSequence.hasSplit()) return;
        capturePrintRevisionDraft(hardOnly ? "RIFAI_SOLO_DURO" : "RIFAI_ENTRAMBI");
        rememberTestStateForRevision();
        markCurrentTestResultHandled();
        splitSoftYellow = ExposureRecipe.snap5(printSequence.split.softYellow);
        splitHardMagenta = ExposureRecipe.snap5(printSequence.split.hardMagenta);
        splitSoftChosenMs = hardOnly ? snap(printSequence.split.softMs, 500, 36_000_000) : 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        if (hardOnly) {
            provinoFlow = PROVINO_SPLIT_HARD;
            testWidthMs = snap(printSequence.split.hardMs, 500, 30_000);
            testBaseFilterType = ExposureRecipe.FILTER_MAGENTA;
            testBaseFilterValue = splitHardMagenta;
        } else {
            provinoFlow = PROVINO_SPLIT_SOFT;
            testWidthMs = snap(printSequence.split.softMs, 500, 30_000);
            testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
            testBaseFilterValue = splitSoftYellow;
        }
        persistRevisionTestSetup();
        setStatusPresentation(hardOnly ? "RIFAI SOLO IL DURO" : "RIFAI ENTRAMBI",
                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                BLUE);
    }

    private void cancelPrintRevisionToPrint() {
        if (!hasPrintRevisionDraft()) return;
        markCurrentTestResultHandled();
        provinoFlow = PROVINO_SINGLE;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs = snap(splitReturnTestWidthMs, 500, 30_000);
        clearPrintRevisionDraft();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestBaseFilterUi();
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setMode(MODE_PRINT);
        setStatusPresentation("REVISIONE ANNULLATA",
                "La ricetta di stampa precedente è rimasta invariata.", GREEN);
    }

    private LinearLayout buildSplitHowToCard() {
        LinearLayout info = card();
        info.setPadding(dp(12), dp(10), dp(12), dp(10));
        info.addView(text("COME SI USA", 13, SPLIT_VIVA_MAGENTA, true), lp(-1,-2));
        TextView body = text(
                "Lo Split Grade usa due esposizioni distinte, non due filtri contemporaneamente.\n"
                        + "1. Morbido: prova Y60 / M0 e scegli il tempo che rende soprattutto i toni chiari.\n"
                        + "2. Duro: su una nuova striscia applica il morbido scelto su tutta la carta, poi prova Y0 / M180 e scegli il miglior equilibrio di ombre e neri.\n"
                        + "3. Stampa: esegui le due esposizioni una dopo l’altra. Se cambi il morbido, devi ricontrollare il duro.\n\n"
                        + "Morbido e duro sono due esposizioni consecutive. Non impostare Y e M contemporaneamente.",
                11, MUTED, false);
        body.setLineSpacing(0, 1.08f);
        body.setPadding(0, dp(5), 0, 0);
        info.addView(body, lp(-1,-2));
        return info;
    }

    private LinearLayout buildManualSplitEditor(final Dialog owner) {
        LinearLayout panel = card();
        panel.setPadding(dp(12), dp(10), dp(12), dp(10));
        panel.setVisibility(View.GONE);
        panel.addView(text("INSERISCI TEMPI GIÀ NOTI", 14, SPLIT_VIVA_MAGENTA, true), lp(-1,-2));
        TextView note = text("Inserisci indipendentemente filtro e tempo morbido e filtro e tempo duro. Nessuna divisione 50/50, nessun vincolo sulla somma e nessuna compensazione automatica.", 11, MUTED, false);
        note.setPadding(0, dp(4), 0, dp(8)); panel.addView(note, lp(-1,-2));

        final int[] sy = {printSequence != null && printSequence.hasSplit() ? ExposureRecipe.snap5(printSequence.split.softYellow) : 60};
        final int[] sm = {printSequence != null && printSequence.hasSplit() ? printSequence.split.softMs : Math.max(500, splitSoftChosenMs > 0 ? splitSoftChosenMs : 500)};
        final int[] hm = {printSequence != null && printSequence.hasSplit() ? ExposureRecipe.snap5(printSequence.split.hardMagenta) : 180};
        final int[] ht = {printSequence != null && printSequence.hasSplit() ? printSequence.split.hardMs : Math.max(500, splitHardChosenMs > 0 ? splitHardChosenMs : 500)};

        panel.addView(text("MORBIDO · GIALLO", 11, MUTED, true), margin(lp(-1,-2),0,2,0,3));
        LinearLayout yr = new LinearLayout(this); yr.setOrientation(LinearLayout.HORIZONTAL); yr.setGravity(Gravity.CENTER);
        Button ym=smallButton("−"); Button yp=smallButton("+"); TextView yv=text(sy[0]+"Y / 0M",22,SPLIT_VIVA_MAGENTA,true); yv.setGravity(Gravity.CENTER);
        yr.addView(ym,lp(dp(58),dp(52))); yr.addView(yv,lp(0,dp(56),1f)); yr.addView(yp,lp(dp(58),dp(52))); panel.addView(yr,lp(-1,-2));
        ym.setOnClickListener(v->{sy[0]=Math.max(0,sy[0]-5);yv.setText(sy[0]+"Y / 0M");});
        yp.setOnClickListener(v->{sy[0]=Math.min(200,sy[0]+5);yv.setText(sy[0]+"Y / 0M");});
        LinearLayout sr=new LinearLayout(this); sr.setOrientation(LinearLayout.HORIZONTAL); sr.setGravity(Gravity.CENTER);
        Button stm=smallButton("−"); Button stp=smallButton("+"); TextView stv=text(formatTime(sm[0]),24,SPLIT_VIVA_MAGENTA,true); stv.setGravity(Gravity.CENTER);
        sr.addView(stm,lp(dp(58),dp(52)));sr.addView(stv,lp(0,dp(56),1f));sr.addView(stp,lp(dp(58),dp(52)));panel.addView(sr,margin(lp(-1,-2),0,0,0,6));
        stm.setOnClickListener(v->{sm[0]=Math.max(500,sm[0]-500);stv.setText(formatTime(sm[0]));});
        stp.setOnClickListener(v->{sm[0]=Math.min(36_000_000,sm[0]+500);stv.setText(formatTime(sm[0]));});

        panel.addView(text("DURO · MAGENTA", 11, MUTED, true), margin(lp(-1,-2),0,2,0,3));
        LinearLayout mr = new LinearLayout(this); mr.setOrientation(LinearLayout.HORIZONTAL); mr.setGravity(Gravity.CENTER);
        Button mm=smallButton("−"); Button mp=smallButton("+"); TextView mv=text("0Y / "+hm[0]+"M",22,SPLIT_VIVA_MAGENTA,true); mv.setGravity(Gravity.CENTER);
        mr.addView(mm,lp(dp(58),dp(52))); mr.addView(mv,lp(0,dp(56),1f)); mr.addView(mp,lp(dp(58),dp(52))); panel.addView(mr,lp(-1,-2));
        mm.setOnClickListener(v->{hm[0]=Math.max(0,hm[0]-5);mv.setText("0Y / "+hm[0]+"M");});
        mp.setOnClickListener(v->{hm[0]=Math.min(200,hm[0]+5);mv.setText("0Y / "+hm[0]+"M");});
        LinearLayout hr=new LinearLayout(this); hr.setOrientation(LinearLayout.HORIZONTAL); hr.setGravity(Gravity.CENTER);
        Button htm=smallButton("−"); Button htp=smallButton("+"); TextView htv=text(formatTime(ht[0]),24,SPLIT_VIVA_MAGENTA,true); htv.setGravity(Gravity.CENTER);
        hr.addView(htm,lp(dp(58),dp(52)));hr.addView(htv,lp(0,dp(56),1f));hr.addView(htp,lp(dp(58),dp(52)));panel.addView(hr,margin(lp(-1,-2),0,0,0,8));
        htm.setOnClickListener(v->{ht[0]=Math.max(500,ht[0]-500);htv.setText(formatTime(ht[0]));});
        htp.setOnClickListener(v->{ht[0]=Math.min(36_000_000,ht[0]+500);htv.setText(formatTime(ht[0]));});

        Button save=compactButton("SALVA TEMPI SPLIT GRADE"); save.setTextColor(Color.WHITE); save.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0));
        save.setOnClickListener(v->{
            capturePrintRevisionDraft(printSequence != null && printSequence.hasSplit() ? "MODIFICA_SPLIT_MANUALE" : "SINGOLA_A_SPLIT_MANUALE");
            SplitGradePlan plan=new SplitGradePlan(); plan.enabled=true; plan.softYellow=sy[0]; plan.softMs=sm[0]; plan.hardMagenta=hm[0]; plan.hardMs=ht[0]; plan.sanitize();
            PrintSequence next=new PrintSequence(); next.split=plan;
            printSequence=next; // A new base never inherits old Dodge/Burn silently.
            splitSoftYellow=plan.softYellow; splitSoftChosenMs=plan.softMs; splitSoftChosenStrip=-1;
            splitHardMagenta=plan.hardMagenta; splitHardChosenMs=plan.hardMs; splitHardChosenStrip=-1;
            commitPrintRevisionMetadata("MANUALE");
            persistPrintSequence();
            owner.dismiss();
            setStatusPresentation("SPLIT GRADE — TEMPI INSERITI",
                    "Morbido e duro restano due esposizioni indipendenti e consecutive. Nessuna compensazione applicata.", GREEN);
        });
        panel.addView(save, lp(-1,dp(50)));
        Button hide=compactButton("ANNULLA"); hide.setOnClickListener(v->panel.setVisibility(View.GONE)); panel.addView(hide,margin(lp(-1,dp(46)),0,7,0,0));
        return panel;
    }

'''
rep(main, '    private void showPrintSequenceDialog() {\n', helpers + '    private void showPrintSequenceDialog() {\n', 'revision/print helpers')

# -----------------------------------------------------------------------------
# One PIANO STAMPA popup: exposure mode + Split management + local corrections.
# -----------------------------------------------------------------------------
new_plan_dialog = r'''    private void showPrintSequenceDialog() {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));
        panel.addView(text("PIANO DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1,-2));

        String base = recipeBaseSummary();
        if (!base.isEmpty()) {
            TextView baseInfo=text(base,13,darkroomMode?RED:GREEN,true);
            baseInfo.setPadding(0,dp(6),0,dp(10));
            panel.addView(baseInfo,lp(-1,-2));
        }

        panel.addView(text("ESPOSIZIONE",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
        final LinearLayout manualEditor = buildManualSplitEditor(dialog);
        if (printSequence != null && printSequence.hasSplit()) {
            Button splitRow=compactButton("SPLIT GRADE  ·  MORBIDO "+printSequence.split.softYellow+"Y / 0M · "+formatTime(printSequence.split.softMs)+"  ·  DURO 0Y / "+printSequence.split.hardMagenta+"M · "+formatTime(printSequence.split.hardMs));
            splitRow.setTextColor(Color.WHITE); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_VIVA_MAGENTA,8,0,0)); splitRow.setEnabled(false);
            panel.addView(splitRow,margin(lp(-1,dp(62)),0,0,0,7));
            if(!darkroomMode){
                Button hard=compactButton("RIFAI SOLO IL DURO"); hard.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(true);}); panel.addView(hard,margin(lp(-1,dp(48)),0,0,0,6));
                Button both=compactButton("RIFAI ENTRAMBI"); both.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(false);}); panel.addView(both,margin(lp(-1,dp(48)),0,0,0,6));
                Button known=compactButton("MODIFICA / INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,9));
            }
        } else {
            String f=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.filterLabel():"NESSUNO";
            String d=(exposureRecipe!=null&&exposureRecipe.hasBase())?exposureRecipe.densityLabel():"D0";
            String label="SINGOLA  ·  "+formatTime(printWidthMs)+("NESSUNO".equals(f)?"":" · "+f)+" · "+d;
            Button single=compactButton(label); single.setTextColor(Color.WHITE); single.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),8,0,0)); single.setEnabled(false);
            panel.addView(single,margin(lp(-1,dp(52)),0,0,0,7));
            if(!darkroomMode){
                Button guided=compactButton("TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO"); guided.setTextColor(Color.WHITE); guided.setBackground(roundRect(SPLIT_VIVA_MAGENTA,8,0,0)); guided.setOnClickListener(v->{dialog.dismiss();beginSplitFromSingleWithProvino();}); panel.addView(guided,margin(lp(-1,dp(52)),0,0,0,6));
                Button known=compactButton("INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,6));
                Button retest=compactButton("RIFAI PROVINO SINGOLO"); retest.setOnClickListener(v->{dialog.dismiss();beginSingleRevisionFromPrint();}); panel.addView(retest,margin(lp(-1,dp(48)),0,0,0,9));
            }
        }
        panel.addView(manualEditor, margin(lp(-1,-2),0,2,0,8));
        panel.addView(buildSplitHowToCard(), margin(lp(-1,-2),0,2,0,10));

        panel.addView(text("CORREZIONI LOCALI",12,MUTED,true),margin(lp(-1,-2),0,4,0,5));
        if(printSequence!=null){
            for(int x=0;x<printSequence.corrections.size();x++){
                final int index=x; PrintCorrection c=printSequence.corrections.get(x); int baseMs=printSequence.baseMsFor(c,printWidthMs);
                Button row=compactButton(c.displayLine(baseMs,printSequence.hasSplit())); int fc=c.isDodge()?DODGE_BISCAY_BAY:BURN_RUST;
                row.setTextColor(Color.WHITE); row.setBackground(roundRect(darkroomMode?RED:fc,8,0,0));
                if(!darkroomMode) row.setOnClickListener(v->{dialog.dismiss();showPrintCorrectionEditor(index);}); else row.setEnabled(false);
                panel.addView(row,margin(lp(-1,dp(50)),0,0,0,7));
            }
        }
        if(!darkroomMode){
            Button dodge=compactButton("+  DODGE"); dodge.setTextColor(Color.WHITE); dodge.setBackground(roundRect(DODGE_BISCAY_BAY,8,0,0)); dodge.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.DODGE);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            Button burn=compactButton("+  BURN"); burn.setTextColor(Color.WHITE); burn.setBackground(roundRect(BURN_RUST,8,0,0)); burn.setOnClickListener(v->{dialog.dismiss();PrintCorrection c=new PrintCorrection(PrintCorrection.BURN);c.phase=printSequence.hasSplit()?PrintCorrection.PHASE_SOFT:PrintCorrection.PHASE_BASE;printSequence.corrections.add(c);showPrintCorrectionEditor(printSequence.corrections.size()-1);});
            LinearLayout addRow=new LinearLayout(this); addRow.setOrientation(LinearLayout.HORIZONTAL); addRow.addView(dodge,margin(lp(0,dp(50),1f),0,0,dp(4),0)); addRow.addView(burn,margin(lp(0,dp(50),1f),dp(4),0,0,0)); panel.addView(addRow,margin(lp(-1,-2),0,0,0,12));

            panel.addView(text("STRUMENTI",12,MUTED,true),margin(lp(-1,-2),0,2,0,5));
            boolean lengthReady=canLengthenTimes();
            Button length=compactButton(lengthReady?"ALLUNGA TEMPI":"ALLUNGA TEMPI · DOPO LA PRIMA STAMPA");
            length.setTextColor(Color.WHITE); length.setBackground(roundRect(lengthReady?ALLUNGA_COLOR:Color.rgb(55,60,64),8,0,0)); length.setEnabled(lengthReady); length.setAlpha(lengthReady?1f:0.55f);
            if(lengthReady) length.setOnClickListener(v->{dialog.dismiss();showLengthenTimesDialog();}); panel.addView(length,lp(-1,dp(52)));

            Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(Color.WHITE); global.setBackground(roundRect(Color.rgb(55,60,64),8,0,0)); global.setOnClickListener(v->{dialog.dismiss();showGlobalCorrectionDialog();}); panel.addView(global,margin(lp(-1,dp(50)),0,7,0,0));

            if((printSequence!=null&&!printSequence.isEmpty()) || (exposureRecipe!=null&&(exposureRecipe.densityQuarterSteps>0||exposureRecipe.globalQuarterStops!=0))){
                Button clear=compactButton("AZZERA PIANO"); clear.setTextColor(Color.WHITE); clear.setBackground(roundRect(RED,9,0,0)); clear.setOnClickListener(v->showAppConfirmDialog("AZZERARE IL PIANO DI STAMPA?","Verranno eliminati Split Grade, DODGE, BURN, densità D e correzione globale. La base originale resta disponibile.","AZZERA",()->{printSequence=new PrintSequence(); if(exposureRecipe==null)exposureRecipe=new ExposureRecipe(); exposureRecipe.densityQuarterSteps=0; exposureRecipe.globalQuarterStops=0; if(exposureRecipe.originalBaseMs>0){exposureRecipe.operationalBaseMs=exposureRecipe.originalBaseMs; printWidthMs=exposureRecipe.originalBaseMs; if(printTimeText!=null)printTimeText.setText(formatTime(printWidthMs));} persistPrintSequence();persistExposureRecipe();dialog.dismiss();},"ANNULLA")); panel.addView(clear,margin(lp(-1,dp(46)),0,10,0,0));
            }
        } else {
            TextView darkNote=text("In modalità camera oscura il piano è consultabile ma non modificabile.",11,RED,false); darkNote.setGravity(Gravity.CENTER); panel.addView(darkNote,margin(lp(-1,-2),0,8,0,0));
        }
        Button close=compactButton("CHIUDI"); close.setTextColor(Color.WHITE); close.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),9,0,0)); close.setOnClickListener(v->dialog.dismiss()); panel.addView(close,margin(lp(-1,dp(48)),0,8,0,0));
        dialog.setContentView(sc); Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent); dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.90f));
    }

'''
replace_method(main, '    private void showPrintSequenceDialog() {\n', '    private void showPlanTypeDialog() {\n', new_plan_dialog, 'single PIANO STAMPA Split management')

# Legacy entry point can no longer open a competing Split popup.
new_type_dialog = r'''    private void showPlanTypeDialog() {
        showPrintSequenceDialog();
    }

'''
replace_method(main, '    private void showPlanTypeDialog() {\n', '    private void showSplitGradeEditor(final boolean creating) {\n', new_type_dialog, 'route legacy add-plan entry to PIANO STAMPA')

new_old_editor = r'''    private void showSplitGradeEditor(final boolean creating) {
        // v0.2.6: Split Grade has one management surface only: PIANO DI STAMPA.
        // The former editor divided the single time ~50/50 and imposed a sum cap;
        // both behaviours are intentionally removed.
        if (darkroomMode) return;
        showPrintSequenceDialog();
    }

'''
replace_method(main, '    private void showSplitGradeEditor(final boolean creating) {\n', '    private void showPrintCorrectionEditor(final int index) {\n', new_old_editor, 'remove old 50/50 Split editor')

# Direct PROVINO Split starts a fresh experimental workflow, not a revision of STAMPA.
rep(main,
'''    private void startSplitProvino() {\n        if (armed || provinoFlow != PROVINO_SINGLE) {''',
'''    private void startSplitProvino() {\n        if (armed || provinoFlow != PROVINO_SINGLE) {''', 'locate direct Split start')
rep(main,
'''        markCurrentTestResultHandled();\n        splitReturnFilterType = testBaseFilterType;''',
'''        clearPrintRevisionDraft();\n        clearRevisionSessionMetadata();\n        markCurrentTestResultHandled();\n        splitReturnFilterType = testBaseFilterType;''','direct Split clears revision context')

# Cancellation from a revision returns to STAMPA and leaves old recipe untouched.
new_cancel_split = r'''    private void cancelSplitProvino() {
        boolean revising = hasPrintRevisionDraft();
        provinoFlow = PROVINO_SINGLE;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs = snap(splitReturnTestWidthMs, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", testBaseFilterType)
                .putInt("testBaseFilterValue", testBaseFilterValue)
                .apply();
        if (revising) clearPrintRevisionDraft();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestBaseFilterUi();
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        if (revising) {
            setMode(MODE_PRINT);
            setStatusPresentation("REVISIONE ANNULLATA", "La ricetta precedente non è stata modificata.", GREEN);
        } else {
            setStatusPresentation("PROVINO SINGOLO", "Valori precedenti ripristinati. Nessuna ricetta di stampa modificata.", BLUE);
        }
    }

'''
replace_method(main, '    private void cancelSplitProvino() {\n', '    private void prepareHardProvinoFromSoftChoice() {\n', new_cancel_split, 'cancel revision without overwriting print')

# Single result finalizes a revision only when an actual strip is selected.
rep(main,
'''                int imported=snap(physical[selected[0]],500,36_000_000);\n                markTestResultHandled(testAt);\n                exposureRecipe=new ExposureRecipe();''',
'''                int imported=snap(physical[selected[0]],500,36_000_000);\n                markTestResultHandled(testAt);\n                splitSoftChosenStrip=-1; splitHardChosenStrip=-1;\n                commitPrintRevisionMetadata("PROVINO");\n                exposureRecipe=new ExposureRecipe();''','commit single revision only after strip choice')

rep(main,
'''            Button later=compactButton("NON ORA"); later.setOnClickListener(v->dialog.dismiss());\n            panel.addView(later, margin(lp(-1,dp(47)),0,7,0,0));''',
'''            Button later=compactButton("NON ORA"); later.setOnClickListener(v->dialog.dismiss());\n            panel.addView(later, margin(lp(-1,dp(47)),0,7,0,0));\n            if(hasPrintRevisionDraft()){\n                Button cancelRevision=compactButton("ANNULLA REVISIONE E TORNA ALLA STAMPA");\n                cancelRevision.setOnClickListener(v->{dialog.dismiss();cancelPrintRevisionToPrint();});\n                panel.addView(cancelRevision,margin(lp(-1,dp(47)),0,7,0,0));\n            }''','single revision cancel action')

# Completing Split from the guided provino creates the new revision and no old D/B.
rep(main,
'''        // New experimentally determined base: do not silently inherit old Dodge/Burn.\n        printSequence=next;\n        getSharedPreferences("ui",MODE_PRIVATE).edit().putString("printSequence",printSequence.encode()).apply();''',
'''        // New experimentally determined base: do not silently inherit old Dodge/Burn.\n        printSequence=next;\n        commitPrintRevisionMetadata("PROVINO");\n        getSharedPreferences("ui",MODE_PRIVATE).edit().putString("printSequence",printSequence.encode()).apply();''','commit guided Split revision')

# -----------------------------------------------------------------------------
# LOG / revision metadata: no total-time masquerading as a Split recipe.
# -----------------------------------------------------------------------------
rep(main,
'''            e.printSequence = p.getString("lastPrintSequence", "");\n            e.recipeState = p.getString("lastRecipeState", "");\n            if (testAt > 0) {''',
'''            e.printSequence = p.getString("lastPrintSequence", "");\n            e.recipeState = p.getString("lastRecipeState", "");\n            PrintSequence loggedSequence = PrintSequence.decode(e.printSequence);\n            boolean loggedSplit = loggedSequence.hasSplit();\n            e.exposureMode = p.getString("lastExposureMode", loggedSplit ? "SPLIT_GRADE" : "SINGLE");\n            if (loggedSplit) {\n                e.splitSoftYellow = p.getInt("lastSplitSoftYellow", loggedSequence.split.softYellow);\n                e.splitSoftMs = p.getInt("lastSplitSoftMs", loggedSequence.split.softMs);\n                e.splitHardMagenta = p.getInt("lastSplitHardMagenta", loggedSequence.split.hardMagenta);\n                e.splitHardMs = p.getInt("lastSplitHardMs", loggedSequence.split.hardMs);\n            }\n            e.splitSoftChosenStrip = p.getInt("lastSplitSoftChosenStrip", -1);\n            e.splitHardChosenStrip = p.getInt("lastSplitHardChosenStrip", -1);\n            e.splitTimeOrigin = p.getString("lastSplitTimeOrigin", "");\n            e.previousRevisionId = p.getLong("lastRevisionPreviousId", 0L);\n            e.previousRecipeState = p.getString("lastRevisionPreviousRecipeState", "");\n            e.previousPrintSequence = p.getString("lastRevisionPreviousPrintSequence", "");\n            e.revisionReason = p.getString("lastRevisionReason", "");\n            if (testAt > 0) {''','new log carries Split/revision fields')

rep(main,
'''        if (cycle > 0 && e.timestamp == cycle) {\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("lastSavedCycleAt", cycle).apply();\n        }''',
'''        if (cycle > 0 && e.timestamp == cycle) {\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("lastSavedCycleAt", cycle).apply();\n        }\n        if (e.exposureMs > 0) getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("activeSourceLogId", e.id).apply();''','remember source log revision id')

rep(main,
'''    private void useLogEntryForPrint(LogEntry entry) {\n        if (entry == null || entry.exposureMs <= 0) return;\n        exposureRecipe = ExposureRecipe.decode(entry.recipeState);''',
'''    private void useLogEntryForPrint(LogEntry entry) {\n        if (entry == null || entry.exposureMs <= 0) return;\n        clearPrintRevisionDraft();\n        clearRevisionSessionMetadata();\n        exposureRecipe = ExposureRecipe.decode(entry.recipeState);''','loading log clears stale revision draft')
rep(main,
'''                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n                .apply();''',
'''                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n                .putLong("activeSourceLogId", entry.id)\n                .apply();''','loading log stores active source id')
rep(main,
'''        Toast.makeText(this, "Stampa " + formatTime(entry.exposureMs) + (printSequence.isEmpty() ? "" : " + piano completo") + " caricata in STAMPA", Toast.LENGTH_SHORT).show();''',
'''        Toast.makeText(this, printSequence.hasSplit() ? "Stampa SPLIT GRADE caricata in STAMPA" : ("Stampa " + formatTime(entry.exposureMs) + (printSequence.isEmpty() ? "" : " + piano completo") + " caricata in STAMPA"), Toast.LENGTH_SHORT).show();''','Split log load avoids total-time label')

log_helpers = r'''    private String splitLogSummary(LogEntry entry, PrintSequence savedSequence) {
        boolean split = savedSequence != null && savedSequence.hasSplit();
        if (!split) return "SINGOLA";
        int sy = entry.splitSoftYellow > 0 ? entry.splitSoftYellow : savedSequence.split.softYellow;
        int sm = entry.splitSoftMs > 0 ? entry.splitSoftMs : savedSequence.split.softMs;
        int hm = entry.splitHardMagenta > 0 ? entry.splitHardMagenta : savedSequence.split.hardMagenta;
        int ht = entry.splitHardMs > 0 ? entry.splitHardMs : savedSequence.split.hardMs;
        String origin = entry.splitTimeOrigin == null || entry.splitTimeOrigin.trim().isEmpty() ? "—" : entry.splitTimeOrigin;
        String strips = (entry.splitSoftChosenStrip > 0 || entry.splitHardChosenStrip > 0)
                ? (" · strisce M=" + (entry.splitSoftChosenStrip > 0 ? entry.splitSoftChosenStrip : "—") + " / D=" + (entry.splitHardChosenStrip > 0 ? entry.splitHardChosenStrip : "—")) : "";
        return "SPLIT GRADE\nMORBIDO · " + sy + "Y / 0M · " + formatTime(sm)
                + "\nDURO · 0Y / " + hm + "M · " + formatTime(ht)
                + "\nOrigine tempi: " + origin + strips;
    }

    private String previousRevisionSummary(LogEntry entry) {
        PrintSequence old = PrintSequence.decode(entry == null ? "" : entry.previousPrintSequence);
        if (old.hasSplit()) return "Precedente: " + old.split.softLine() + " / " + old.split.hardLine();
        ExposureRecipe r = ExposureRecipe.decode(entry == null ? "" : entry.previousRecipeState);
        if (r.hasBase()) return "Precedente: esposizione singola · " + formatTime(r.operationalBaseMs > 0 ? r.operationalBaseMs : r.originalBaseMs) + " · " + r.filterLabel();
        return "Precedente revisione disponibile";
    }

'''
rep(main, '    private void showLogEditor(final LogEntry entry, final boolean isNew) {\n', log_helpers + '    private void showLogEditor(final LogEntry entry, final boolean isNew) {\n', 'log revision display helpers')

# Replace automatic log block strings to expose four Split fields rather than one total.
rep(main,
'''        String printMethod = entry.exposureMs > 0 ? TimingMath.normalizeMethod(entry.exposureMethod) + " · " + (entry.exposureStep == null || entry.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(entry.exposureMethod) : entry.exposureStep) : "—";\n        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) + " · " + TimingMath.normalizeMaskingMethod(entry.testStripMethod) : "—";\n        PrintSequence savedSequence = PrintSequence.decode(entry.printSequence);\n        String sequenceRecipe = savedSequence.isEmpty() ? "—" : ("\\n" + savedSequence.detail(entry.exposureMs));\n        TextView autoValues = text(\n                "Base originale: " + recipeOriginalLabel(entry, exposure) +\n                "\\nBase operativa: " + recipeOperationalLabel(entry, exposure) +\n                "\\nFiltro provino: " + testFilterLabel(entry) +\n                "\\nMetodo stampa: " + printMethod +\n                "\\nProvino — strisce: " + ntest +\n                "\\nMetodo provino: " + testMethod +\n                "\\nTempi strisce: " + strips +\n                "\\nPiano di stampa: " + sequenceRecipe +''',
'''        String printMethod = entry.exposureMs > 0 ? TimingMath.normalizeMethod(entry.exposureMethod) + " · " + (entry.exposureStep == null || entry.exposureStep.trim().isEmpty() ? TimingMath.stepLabel(entry.exposureMethod) : entry.exposureStep) : "—";\n        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) + " · " + TimingMath.normalizeMaskingMethod(entry.testStripMethod) : "—";\n        PrintSequence savedSequence = PrintSequence.decode(entry.printSequence);\n        boolean savedSplit = savedSequence.hasSplit();\n        String sequenceRecipe = savedSequence.isEmpty() ? "—" : ("\\n" + savedSequence.detail(entry.exposureMs));\n        String exposureHeader = savedSplit\n                ? ("Modalità esposizione: " + splitLogSummary(entry, savedSequence))\n                : ("Modalità esposizione: SINGOLA\\nBase originale: " + recipeOriginalLabel(entry, exposure) + "\\nBase operativa: " + recipeOperationalLabel(entry, exposure));\n        TextView autoValues = text(\n                exposureHeader +\n                "\\nFiltro provino: " + testFilterLabel(entry) +\n                "\\nMetodo stampa: " + printMethod +\n                "\\nProvino — strisce: " + ntest +\n                "\\nMetodo provino: " + testMethod +\n                "\\nTempi strisce: " + strips +\n                "\\nPiano di stampa: " + sequenceRecipe +''','automatic log Split fields')

rep(main,
'''        autoValues.setPadding(0, dp(6), 0, 0);\n        auto.addView(autoValues);\n        panel.addView(auto, margin(lp(-1, -2), 0, 0, 0, 12));''',
'''        autoValues.setPadding(0, dp(6), 0, 0);\n        auto.addView(autoValues);\n        if (!isNew && ((entry.previousPrintSequence != null && !entry.previousPrintSequence.trim().isEmpty()) || (entry.previousRecipeState != null && !entry.previousRecipeState.trim().isEmpty()) || entry.previousRevisionId > 0)) {\n            Button previous=compactButton("MOSTRA REVISIONE PRECEDENTE");\n            previous.setOnClickListener(v -> showAppConfirmDialog("REVISIONE PRECEDENTE",\n                    previousRevisionSummary(entry) + (entry.previousRevisionId > 0 ? ("\\nScheda origine: " + entry.previousRevisionId) : "") + (entry.revisionReason == null || entry.revisionReason.trim().isEmpty() ? "" : ("\\nMotivo: " + entry.revisionReason)),\n                    null, null, "CHIUDI"));\n            auto.addView(previous, margin(lp(-1,dp(46)),0,8,0,0));\n        }\n        panel.addView(auto, margin(lp(-1, -2), 0, 0, 0, 12));''','previous revision consultable from log')

rep(main,
'''                Button useForPrint = compactButton("USA PER STAMPA  •  " + formatTime(entry.exposureMs));''',
'''                Button useForPrint = compactButton(PrintSequence.decode(entry.printSequence).hasSplit() ? "USA PER STAMPA  •  SPLIT GRADE" : ("USA PER STAMPA  •  " + formatTime(entry.exposureMs)));''','log use-for-print Split label')

# Static guards.
mt = rd(main)
required = [
    'private static final String APP_VERSION = "0.13.9";',
    'TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO',
    'INSERISCI TEMPI GIÀ NOTI',
    'RIFAI PROVINO SINGOLO',
    'RIFAI SOLO IL DURO',
    'RIFAI ENTRAMBI',
    'CORREZIONI LOCALI',
    'Morbido e duro sono due esposizioni consecutive. Non impostare Y e M contemporaneamente.',
    'T/2 is deliberately only a convenient editable starting point',
    'commitPrintRevisionMetadata("PROVINO")',
    'commitPrintRevisionMetadata("MANUALE")',
    'previousPrintSequence',
    'MOSTRA REVISIONE PRECEDENTE',
    'activeSourceLogId',
    'splitSoftChosenStrip',
    'splitHardChosenStrip',
]
for needle in required:
    if needle not in mt: raise SystemExit('v0.2.6 Main guard missing: ' + needle)
for forbidden in [
    'PASSA A SPLIT GRADE',
    'Somma massima delle due esposizioni',
    'La somma dello Split Grade non può superare',
    'int softUnits =',
]:
    if forbidden in mt: raise SystemExit('v0.2.6 forbidden old Split behaviour remains: ' + forbidden)
if 'color3' in mt.lower() or 'color 3' in mt.lower() or 'color_3' in mt.lower():
    raise SystemExit('v0.2.6 Color 3 must remain frozen')
for needle in ['DODGE', 'BURN', 'ALLUNGA TEMPI', 'CORREZIONE GLOBALE', 'RIDIMENSIONA STAMPA']:
    if needle not in mt: raise SystemExit('v0.2.6 regression guard missing: ' + needle)
print('v0.2.6 PRINT/REVISION TRANSFORM OK', flush=True)
