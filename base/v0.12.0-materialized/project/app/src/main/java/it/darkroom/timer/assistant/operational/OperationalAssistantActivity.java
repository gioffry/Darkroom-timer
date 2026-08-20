package it.darkroom.timer.assistant.operational;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.speech.tts.TextToSpeech;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import it.darkroom.timer.assistant.chemistry.ChemistryCalculator;
import it.darkroom.timer.assistant.data.AssistantDatabase;
import it.darkroom.timer.assistant.development.DevelopmentCatalog;
import it.darkroom.timer.assistant.equipment.TankPlanner;

/**
 * Darkroom Assistant R7. Dedicated film-development process runner.
 * Deliberately has no dependency on the enlarger controller or MainActivity and never controls the enlarger.
 */
public final class OperationalAssistantActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String PREF="assistant_operational";
    private static final int OK=0, WARNING=1, UNKNOWN=2, BLOCKING=3;
    private static final String[] PHASE_NAMES={"PREPARAZIONE","SVILUPPO","ARRESTO","FISSAGGIO","LAVAGGIO","IMBIBENTE","CONCLUSIONE"};
    private static final String[] PERSONAL_KEYS={"","","stop_seconds","fix_seconds","wash_seconds","wetting_seconds",""};

    private int primary,muted,accent,border,card;
    private Bundle e;
    private AssistantDatabase db;
    private TextToSpeech tts;
    private boolean ttsReady,voiceEnabled;
    private TankPlanner.Plan plan;
    private AssistantDatabase.ChemicalItem inventory;
    private final List<Check> checks=new ArrayList<>();
    private boolean blocked;

    private LinearLayout root,preflightBox,runnerBox,endBox;
    private TextView phaseTitle,phaseInstruction,timerText,nextText,cycleText,statusText;
    private Button startButton,pauseButton,nextButton,resetButton,customTimeButton,logButton,usageButton,voiceButton;
    private CountDownTimer countDown;
    private int cycleIndex,phaseIndex;
    private long remainingMs,deadlineMs;
    private boolean running,paused,complete;
    private int actualDevelopmentSeconds;
    private String sessionKey;

    private static final class Check { int level; String label,detail; Check(int l,String a,String b){level=l;label=a;detail=b;} }

    @Override protected void onCreate(Bundle state){
        super.onCreate(state); palette(); e=getIntent().getExtras(); if(e==null){finish();return;}
        db=new AssistantDatabase(this); tts=new TextToSpeech(this,this);
        sessionKey=buildSessionKey();
        voiceEnabled=getSharedPreferences(PREF,MODE_PRIVATE).getBoolean("voice_enabled",true);
        buildPlanAndPreflight(); restoreState(); buildUi(); render();
        if(running&&!paused&&!complete) resumeCountdownFromDeadline();
    }

    @Override protected void onDestroy(){ persistState(); if(countDown!=null)countDown.cancel(); if(tts!=null){tts.stop();tts.shutdown();} if(db!=null)db.close(); super.onDestroy(); }
    @Override public void onInit(int status){ttsReady=status==TextToSpeech.SUCCESS;if(ttsReady)tts.setLanguage(Locale.ITALIAN);}

    private void palette(){boolean dark=getSharedPreferences("ui",MODE_PRIVATE).getBoolean("darkroomMode",false);if(dark){primary=Color.rgb(255,42,42);muted=Color.rgb(145,34,34);accent=Color.rgb(255,42,42);border=Color.rgb(112,20,20);card=Color.rgb(18,0,0);}else{primary=Color.rgb(238,240,242);muted=Color.rgb(145,151,158);accent=Color.rgb(197,54,58);border=Color.rgb(60,64,70);card=Color.rgb(24,26,30);}}

    private void buildPlanAndPreflight(){
        checks.clear(); blocked=false;
        String format=e.getString("format",""); int rolls=e.getInt("rolls",1); double volume=e.getDouble("volumeMl",0);
        String developer=e.getString("developer",""); String dilution=e.getString("dilution","");
        double temp=e.getDouble("temperature",Double.NaN); int planned=e.getInt("plannedSeconds",e.getInt("seconds",0));
        long tankId=e.getLong("selectedTankId",0); inventory=db.findChemicalForDeveloper(developer);

        if(rolls<=0) add(BLOCKING,"Numero rulli","Configurazione impossibile: numero rulli non valido."); else add(OK,"Numero rulli",rolls+" × "+format);
        if(!(volume>0)) add(BLOCKING,"Volume","Volume non valido."); else if(volume>ChemistryCalculator.CPE2_MAX_ML) add(BLOCKING,"Limite JOBO CPE2",fmt(volume)+" ml > 600 ml"); else add(OK,"Limite JOBO CPE2",fmt(volume)+" ml ≤ 600 ml");
        if(Double.isNaN(temp)||temp<=0) add(UNKNOWN,"Temperatura","VERIFICA MANUALE NECESSARIA"); else add(OK,"Temperatura",String.format(Locale.ITALY,"%.1f °C",temp));
        if(planned<=0) add(UNKNOWN,"Tempo sviluppo","TEMPO NON DOCUMENTATO · inserimento personale possibile"); else add(OK,"Tempo sviluppo",DevelopmentCatalog.formatTime(planned)+" · "+e.getString("timeOrigin",e.getString("dataType","")));

        ChemistryCalculator.Result chemistry=ChemistryCalculator.calculate(developer,dilution,volume,format,rolls);
        if(!chemistry.dilutionKnown) add(UNKNOWN,"Diluizione","NON DETERMINABILE · "+chemistry.dilutionMessage); else add(OK,"Diluizione",fmt(chemistry.productMl)+" ml prodotto + "+fmt(chemistry.waterMl)+" ml acqua");
        if(ChemistryCalculator.CAPACITY_INSUFFICIENT.equals(chemistry.capacityState)) add(BLOCKING,"Capacità chimica",chemistry.capacityMessage);
        else if(ChemistryCalculator.CAPACITY_UNKNOWN.equals(chemistry.capacityState)) add(UNKNOWN,"Capacità chimica","CAPACITÀ NON DOCUMENTATA · VERIFICA MANUALE NECESSARIA");
        else add(OK,"Capacità chimica",chemistry.capacityMessage);

        if(tankId>0){
            AssistantDatabase.TankItem tank=db.getTank(tankId);
            if(tank==null){add(UNKNOWN,"Tank","Tank selezionata non più disponibile · VERIFICA MANUALE NECESSARIA");}
            else if(!tank.cpe2Compatible){add(BLOCKING,"Tank",tank.displayName()+" dichiarata non compatibile con JOBO CPE2");}
            else {
                int cap=tank.capacityFor(format);
                if(cap<=0) add(BLOCKING,"Tank",tank.displayName()+" non supporta "+format);
                else {
                    int batch=Math.min(cap,rolls);
                    plan=TankPlanner.planFor(tank,format,rolls,batch,volume,developer,dilution,inventory);
                    if(plan.ok) add(OK,"Tank / cicli",plan.summary()); else add(BLOCKING,"Tank / cicli",plan.problem);
                }
            }
        } else {
            plan=TankPlanner.chooseBest(db.listTanks(),format,rolls,volume,developer,dilution,inventory);
            if(plan.ok) add(OK,"Tank / cicli",plan.summary());
            else add(WARNING,"Tank","Nessuna pianificazione automatica valida. Puoi procedere solo con il volume manuale già verificato. "+plan.problem);
        }

        if(inventory==null) add(UNKNOWN,"Disponibilità chimica","Prodotto non presente in inventario · VERIFICA MANUALE NECESSARIA");
        else if(plan!=null&&plan.ok&&plan.productKnown){
            double available=toMl(inventory.remainingAmount,inventory.unit);
            if(available>=0&&available+0.001<plan.totalProductMl) add(BLOCKING,"Disponibilità chimica","Servono "+fmt(plan.totalProductMl)+" ml, disponibili "+fmt(available)+" ml");
            else if(available>=0) add(OK,"Disponibilità chimica",fmt(available)+" ml disponibili");
            else add(UNKNOWN,"Disponibilità chimica","Unità inventario non convertibile automaticamente");
        } else add(UNKNOWN,"Disponibilità chimica","Consumo esatto NON DETERMINABILE");
    }

    private void add(int level,String label,String detail){checks.add(new Check(level,label,detail));if(level==BLOCKING)blocked=true;}

    private void buildUi(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(Color.BLACK);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(18),dp(18),dp(18),dp(28));scroll.addView(root);
        TextView eye=text("DARKROOM ASSISTANT · 9/9",12,accent,true);eye.setGravity(Gravity.CENTER);root.addView(eye);
        TextView title=text("ASSISTENTE OPERATIVO",25,primary,true);title.setGravity(Gravity.CENTER);root.addView(title);
        TextView summary=text(e.getString("film","")+" · "+e.getString("format","")+" · ISO "+e.getInt("exposedIso")+"\n"+e.getString("developer","")+" · "+e.getString("dilution","")+" · "+String.format(Locale.ITALY,"%.1f °C",e.getDouble("temperature")),13,muted,true);summary.setGravity(Gravity.CENTER);summary.setPadding(0,dp(5),0,dp(14));root.addView(summary);

        preflightBox=box();preflightBox.addView(text("CONTROLLO PRE-SVILUPPO",15,accent,true));for(Check c:checks){int color=c.level==BLOCKING?accent:(c.level==OK?primary:muted);preflightBox.addView(text(level(c.level)+" · "+c.label+"\n"+c.detail,12,color,c.level==BLOCKING));}root.addView(preflightBox);
        statusText=text(blocked?"AVVIO BLOCCATO: correggi solo le configurazioni oggettivamente impossibili.":"Le informazioni mancanti restano esplicitamente NON DETERMINABILI e non vengono trasformate in zero.",12,blocked?accent:muted,true);statusText.setPadding(dp(4),dp(10),dp(4),dp(10));root.addView(statusText);
        startButton=button("AVVIA SVILUPPO");startButton.setEnabled(!blocked);startButton.setOnClickListener(v->startSession());root.addView(startButton,margin(-1,dp(54),0,4,0,12));

        runnerBox=box();cycleText=text("",13,muted,true);phaseTitle=text("",23,primary,true);phaseInstruction=text("",13,primary,false);timerText=text("",38,accent,true);timerText.setGravity(Gravity.CENTER);nextText=text("",12,muted,true);runnerBox.addView(cycleText);runnerBox.addView(phaseTitle);runnerBox.addView(phaseInstruction);runnerBox.addView(timerText);runnerBox.addView(nextText);
        customTimeButton=button("IMPOSTA TEMPO PERSONALE");customTimeButton.setOnClickListener(v->setPersonalPhaseTime());runnerBox.addView(customTimeButton);
        pauseButton=button("PAUSA");pauseButton.setOnClickListener(v->togglePause());runnerBox.addView(pauseButton);
        nextButton=button("FASE SUCCESSIVA");nextButton.setOnClickListener(v->nextPhase());runnerBox.addView(nextButton);
        resetButton=button("RESET SESSIONE");resetButton.setOnClickListener(v->confirmReset());runnerBox.addView(resetButton);
        voiceButton=button(voiceEnabled?"GUIDA VOCALE · ON":"GUIDA VOCALE · OFF");voiceButton.setOnClickListener(v->{voiceEnabled=!voiceEnabled;getSharedPreferences(PREF,MODE_PRIVATE).edit().putBoolean("voice_enabled",voiceEnabled).apply();voiceButton.setText(voiceEnabled?"GUIDA VOCALE · ON":"GUIDA VOCALE · OFF");});runnerBox.addView(voiceButton);root.addView(runnerBox);

        endBox=box();endBox.addView(text("SVILUPPO CONCLUSO",20,accent,true));endBox.addView(text("Il Log e il consumo chimica NON vengono registrati automaticamente.",12,muted,true));logButton=button("SALVA SVILUPPO NEL LOG");logButton.setOnClickListener(v->saveLogDialog());endBox.addView(logButton);usageButton=button("REGISTRA UTILIZZO CHIMICA");usageButton.setOnClickListener(v->registerUsageDialog());endBox.addView(usageButton);Button close=button("CHIUDI");close.setOnClickListener(v->finish());endBox.addView(close);root.addView(endBox);
        setContentView(scroll);
    }

    private void render(){
        preflightBox.setVisibility((running||complete)?View.GONE:View.VISIBLE);statusText.setVisibility((running||complete)?View.GONE:View.VISIBLE);startButton.setVisibility((running||complete)?View.GONE:View.VISIBLE);
        runnerBox.setVisibility(running&&!complete?View.VISIBLE:View.GONE);endBox.setVisibility(complete?View.VISIBLE:View.GONE);
        if(!running||complete)return;
        int cycles=cycleCount();cycleText.setText("CICLO "+(cycleIndex+1)+" DI "+cycles+" · "+cycleSummary(cycleIndex));
        phaseTitle.setText(PHASE_NAMES[phaseIndex]);phaseInstruction.setText(instructionForPhase());
        long sec=phaseSeconds(phaseIndex); if(remainingMs<=0&&sec>0)remainingMs=sec*1000L;
        if(sec<=0){timerText.setText("TEMPO NON DOCUMENTATO");customTimeButton.setVisibility(personalPhase(phaseIndex)?View.VISIBLE:View.GONE);pauseButton.setVisibility(View.GONE);}else{timerText.setText(formatRemaining(remainingMs));customTimeButton.setVisibility(personalPhase(phaseIndex)?View.VISIBLE:View.GONE);pauseButton.setVisibility(View.VISIBLE);pauseButton.setText(paused?"RIPRENDI":"PAUSA");}
        nextText.setText(phaseIndex+1<PHASE_NAMES.length?"Successiva: "+PHASE_NAMES[phaseIndex+1]:(cycleIndex+1<cycles?"Successivo: CICLO "+(cycleIndex+2):"Ultima fase"));
    }

    private void startSession(){if(blocked)return;running=true;paused=true;complete=false;cycleIndex=0;phaseIndex=0;remainingMs=0;actualDevelopmentSeconds=0;persistState();announcePhase();render();}

    private void nextPhase(){
        if(!running||complete)return;
        if(phaseIndex==1){int planned=e.getInt("plannedSeconds",e.getInt("seconds",0));if(planned>0){actualDevelopmentSeconds=(int)Math.max(0,planned-Math.max(0,remainingMs/1000L));if(remainingMs<=1000)actualDevelopmentSeconds=planned;}}
        cancelTimer();paused=true;remainingMs=0;deadlineMs=0;
        if(phaseIndex<PHASE_NAMES.length-1){phaseIndex++;}
        else if(cycleIndex+1<cycleCount()){cycleIndex++;phaseIndex=0;}
        else{complete=true;running=false;speak("Sviluppo concluso.");persistState();render();return;}
        persistState();announcePhase();render();
    }

    private void togglePause(){long sec=phaseSeconds(phaseIndex);if(sec<=0)return;if(paused){if(remainingMs<=0)remainingMs=sec*1000L;startCountdown();}else{pauseCountdown();}render();}
    private void startCountdown(){cancelTimer();paused=false;deadlineMs=System.currentTimeMillis()+remainingMs;countDown=new CountDownTimer(remainingMs,250){public void onTick(long m){remainingMs=m;if(timerText!=null)timerText.setText(formatRemaining(m));persistState();}public void onFinish(){remainingMs=0;paused=true;deadlineMs=0;if(timerText!=null)timerText.setText("0:00");speak("Fase "+PHASE_NAMES[phaseIndex].toLowerCase(Locale.ITALY)+" completata. Passa alla fase successiva.");persistState();render();}}.start();persistState();}
    private void pauseCountdown(){if(!paused){remainingMs=Math.max(0,deadlineMs-System.currentTimeMillis());paused=true;deadlineMs=0;cancelTimer();persistState();}}
    private void resumeCountdownFromDeadline(){remainingMs=Math.max(0,deadlineMs-System.currentTimeMillis());if(remainingMs<=0){paused=true;running=true;deadlineMs=0;persistState();render();}else startCountdown();}
    private void cancelTimer(){if(countDown!=null){countDown.cancel();countDown=null;}}

    private void setPersonalPhaseTime(){if(!personalPhase(phaseIndex))return;final EditText f=new EditText(this);f.setHint("m:ss");f.setInputType(InputType.TYPE_CLASS_TEXT);int existing=getSharedPreferences(PREF,MODE_PRIVATE).getInt(PERSONAL_KEYS[phaseIndex],0);if(existing>0)f.setText(timeText(existing));new AlertDialog.Builder(this).setTitle(PHASE_NAMES[phaseIndex]+" · DATO PERSONALE").setMessage("Il valore sarà marcato come personale, non come fonte tecnica.").setView(f).setPositiveButton("SALVA",(d,w)->{int s=parseTime(f.getText().toString());if(s<=0){toast("Tempo non valido");return;}getSharedPreferences(PREF,MODE_PRIVATE).edit().putInt(PERSONAL_KEYS[phaseIndex],s).apply();remainingMs=s*1000L;paused=true;persistState();render();}).setNegativeButton("ANNULLA",null).show();}

    private long phaseSeconds(int index){if(index==1)return e.getInt("plannedSeconds",e.getInt("seconds",0));if(personalPhase(index))return getSharedPreferences(PREF,MODE_PRIVATE).getInt(PERSONAL_KEYS[index],0);return 0;}
    private boolean personalPhase(int i){return i>=2&&i<=5;}
    private String instructionForPhase(){String name=PHASE_NAMES[phaseIndex];if(phaseIndex==0)return "Prepara tank e soluzioni secondo lo snapshot del ciclo. Controlla temperatura e quantità prima di procedere.";if(phaseIndex==1)return "Inizia lo sviluppo in JOBO CPE2 a rotazione continua. Questo timer è separato dal Timer STAMPA e non comanda SONOFF.";if(phaseIndex==6)return "Concludi il ciclo e verifica il materiale prima di salvare Log o consumo chimica.";return "Esegui la fase "+name.toLowerCase(Locale.ITALY)+". Se il catalogo non documenta un tempo, puoi inserirne uno personale.";}

    private void announcePhase(){long s=phaseSeconds(phaseIndex);String msg="Inizia "+PHASE_NAMES[phaseIndex].toLowerCase(Locale.ITALY)+"."+(s>0?" Tempo "+spokenTime((int)s)+".":" Tempo non documentato.");speak(msg);}
    private void speak(String s){if(voiceEnabled&&ttsReady&&tts!=null)tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"assistant_phase");}
    private String spokenTime(int s){int m=s/60,r=s%60;if(m>0&&r>0)return m+(m==1?" minuto e ":" minuti e ")+r+(r==1?" secondo":" secondi");if(m>0)return m+(m==1?" minuto":" minuti");return r+(r==1?" secondo":" secondi");}

    private int cycleCount(){return plan!=null&&plan.ok&&plan.cycles>0?plan.cycles:1;}
    private String cycleSummary(int idx){if(plan!=null&&plan.ok&&idx<plan.cycleList.size()){TankPlanner.Cycle c=plan.cycleList.get(idx);String q=c.dilutionKnown?fmt(c.productMl)+" ml prodotto + "+fmt(c.waterMl)+" ml acqua":"quantità prodotto NON DETERMINABILE";return c.rolls+" rulli · "+fmt(c.volumeMl)+" ml · "+q;}return e.getInt("rolls",1)+" rulli · "+fmt(e.getDouble("volumeMl",0))+" ml · piano manuale";}

    private void saveLogDialog(){
        LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);final EditText actual=new EditText(this);actual.setHint("Tempo effettivo m:ss");int a=actualDevelopmentSeconds>0?actualDevelopmentSeconds:e.getInt("plannedSeconds",e.getInt("seconds",0));actual.setText(timeText(a));final EditText note=new EditText(this);note.setHint("Note operative / deviazioni");b.addView(actual);b.addView(note);
        new AlertDialog.Builder(this).setTitle("SALVA SVILUPPO NEL LOG").setMessage("Salvataggio esplicito. Nessun Log è stato creato automaticamente.").setView(b).setPositiveButton("SALVA",(d,w)->{int sec=parseTime(actual.getText().toString());if(sec<=0){toast("Tempo effettivo non valido");return;}AssistantDatabase.LogEntry l=new AssistantDatabase.LogEntry();AssistantDatabase.SourceSnapshot s=new AssistantDatabase.SourceSnapshot();s.film=e.getString("film","");s.format=e.getString("format","");s.nominalIso=e.getInt("nominalIso");s.exposedIso=e.getInt("exposedIso");s.developer=e.getString("developer","");s.dilution=e.getString("dilution","");s.originalTemp=e.getDouble("temperature");s.originalSeconds=e.getInt("seconds");s.sourceName=e.getString("source","");s.dataType=e.getString("dataType","");s.sourceData=e.getString("sourceData","");s.calculation=e.getString("calculation","");l.source=s;l.actualTemp=e.getDouble("temperature");l.actualSeconds=sec;l.timeOrigin="ASSISTENTE OPERATIVO · previsto "+DevelopmentCatalog.formatTime(e.getInt("plannedSeconds",e.getInt("seconds",0)))+" · "+e.getString("timeOrigin","");l.volumeMl=e.getDouble("volumeMl",0);ChemistryCalculator.Result c=ChemistryCalculator.calculate(s.developer,s.dilution,l.volumeMl,s.format,e.getInt("rolls",1));l.productKnown=c.dilutionKnown;l.waterKnown=c.dilutionKnown;l.productMl=c.dilutionKnown?c.productMl:0;l.waterMl=c.dilutionKnown?c.waterMl:0;l.rolls=e.getInt("rolls",1);l.capacityState=c.capacityState;l.capacityMessage=c.capacityMessage;l.notes=note.getText().toString()+"\nTank/cicli: "+(plan!=null&&plan.ok?plan.summary():"piano manuale");db.saveLog(l);toast("Sviluppo salvato nel Log");}).setNegativeButton("ANNULLA",null).show();
    }

    private void registerUsageDialog(){
        inventory=db.findChemicalForDeveloper(e.getString("developer",""));if(inventory==null){toast("Prodotto non presente in inventario: nessuna sottrazione eseguita.");return;}
        double known=-1;if(plan!=null&&plan.ok&&plan.productKnown)known=plan.totalProductMl;else{ChemistryCalculator.Result c=ChemistryCalculator.calculate(e.getString("developer",""),e.getString("dilution",""),e.getDouble("volumeMl",0),e.getString("format",""),e.getInt("rolls",1));if(c.dilutionKnown)known=c.productMl;}
        final double suggested=known;LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);final EditText q=new EditText(this);q.setHint("Quantità usata · "+inventory.unit);q.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);if(suggested>=0){double u=fromMl(suggested,inventory.unit);if(u>=0)q.setText(String.format(Locale.ITALY,"%.2f",u));}b.addView(q);String msg=suggested>=0?"Consumo calcolato: "+fmt(suggested)+" ml. Residuo prima: "+inventory.remainingAmount+" "+inventory.unit+". La sottrazione avverrà solo confermando.":"Consumo NON DETERMINABILE. Inserisci manualmente la quantità realmente usata; non verrà sottratto zero.";
        new AlertDialog.Builder(this).setTitle("REGISTRA UTILIZZO CHIMICA").setMessage(msg).setView(b).setPositiveButton("CONFERMA",(d,w)->{double used=parseDouble(q.getText().toString());if(Double.isNaN(used)||used<0){toast("Quantità non valida");return;}AssistantDatabase.LogEntry dummy=new AssistantDatabase.LogEntry();dummy.source.developer=e.getString("developer","");dummy.source.dilution=e.getString("dilution","");dummy.source.film=e.getString("film","");dummy.source.format=e.getString("format","");dummy.rolls=e.getInt("rolls",1);db.registerChemicalUsage(inventory.id,0,used,inventory.unit,dummy,suggested<0?"Quantità inserita manualmente da Assistente operativo":"Consumo confermato da Assistente operativo");toast("Utilizzo chimica registrato");}).setNegativeButton("NON REGISTRARE",null).show();
    }

    private void confirmReset(){new AlertDialog.Builder(this).setTitle("RESET SESSIONE?").setMessage("Verranno azzerati fase, ciclo e timer della sessione corrente. Ricette, Log e inventario non vengono cancellati.").setPositiveButton("RESET",(d,w)->resetSession()).setNegativeButton("ANNULLA",null).show();}
    private void resetSession(){cancelTimer();running=false;paused=true;complete=false;cycleIndex=0;phaseIndex=0;remainingMs=0;deadlineMs=0;actualDevelopmentSeconds=0;getSharedPreferences(PREF,MODE_PRIVATE).edit().remove("session_key").remove("running").remove("paused").remove("complete").remove("cycle").remove("phase").remove("remaining").remove("deadline").remove("actual_dev").apply();render();}

    private void persistState(){getSharedPreferences(PREF,MODE_PRIVATE).edit().putString("session_key",sessionKey).putBoolean("running",running).putBoolean("paused",paused).putBoolean("complete",complete).putInt("cycle",cycleIndex).putInt("phase",phaseIndex).putLong("remaining",remainingMs).putLong("deadline",deadlineMs).putInt("actual_dev",actualDevelopmentSeconds).apply();}
    private void restoreState(){String old=getSharedPreferences(PREF,MODE_PRIVATE).getString("session_key","");if(!sessionKey.equals(old)){running=false;paused=true;complete=false;cycleIndex=0;phaseIndex=0;remainingMs=0;deadlineMs=0;actualDevelopmentSeconds=0;return;}running=getSharedPreferences(PREF,MODE_PRIVATE).getBoolean("running",false);paused=getSharedPreferences(PREF,MODE_PRIVATE).getBoolean("paused",true);complete=getSharedPreferences(PREF,MODE_PRIVATE).getBoolean("complete",false);cycleIndex=Math.max(0,Math.min(cycleCount()-1,getSharedPreferences(PREF,MODE_PRIVATE).getInt("cycle",0)));phaseIndex=Math.max(0,Math.min(PHASE_NAMES.length-1,getSharedPreferences(PREF,MODE_PRIVATE).getInt("phase",0)));remainingMs=getSharedPreferences(PREF,MODE_PRIVATE).getLong("remaining",0);deadlineMs=getSharedPreferences(PREF,MODE_PRIVATE).getLong("deadline",0);actualDevelopmentSeconds=getSharedPreferences(PREF,MODE_PRIVATE).getInt("actual_dev",0);}
    private String buildSessionKey(){return e.getString("film","")+"|"+e.getString("format","")+"|"+e.getInt("exposedIso")+"|"+e.getString("developer","")+"|"+e.getString("dilution","")+"|"+e.getDouble("temperature")+"|"+e.getInt("plannedSeconds",e.getInt("seconds",0))+"|"+e.getInt("rolls",1)+"|"+e.getDouble("volumeMl",0);}

    private String level(int l){return l==OK?"OK":l==WARNING?"ATTENZIONE":l==UNKNOWN?"NON DETERMINABILE":"BLOCCANTE";}
    private LinearLayout box(){LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);b.setPadding(dp(14),dp(12),dp(14),dp(12));b.setBackgroundColor(card);return b;}
    private TextView text(String s,float z,int c,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(z);t.setTextColor(c);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setTextColor(primary);return b;}
    private LinearLayout.LayoutParams margin(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(int v){return(int)(v*getResources().getDisplayMetrics().density+.5f);}private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
    private static String fmt(double v){return Math.abs(v-Math.rint(v))<0.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.1f",v);}private static String timeText(int s){return String.format(Locale.ITALY,"%d:%02d",s/60,s%60);}private static String formatRemaining(long ms){long s=(ms+999)/1000;return String.format(Locale.ITALY,"%d:%02d",s/60,s%60);}private static int parseTime(String s){try{String x=s.trim();if(x.contains(":")){String[] p=x.split(":");return Integer.parseInt(p[0].trim())*60+Integer.parseInt(p[1].trim());}return Integer.parseInt(x);}catch(Exception ex){return-1;}}private static double parseDouble(String s){try{return Double.parseDouble(s.trim().replace(',','.'));}catch(Exception ex){return Double.NaN;}}
    private static double toMl(double q,String unit){if("ml".equalsIgnoreCase(unit))return q;if("l".equalsIgnoreCase(unit)||"litri".equalsIgnoreCase(unit))return q*1000.0;return-1;}private static double fromMl(double q,String unit){if("ml".equalsIgnoreCase(unit))return q;if("l".equalsIgnoreCase(unit)||"litri".equalsIgnoreCase(unit))return q/1000.0;return-1;}
}
