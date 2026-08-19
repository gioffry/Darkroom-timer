package it.darkroom.timer.assistant.equipment;

import java.util.ArrayList;
import java.util.List;

import it.darkroom.timer.assistant.chemistry.ChemistryCalculator;
import it.darkroom.timer.assistant.data.AssistantDatabase;

/** R6 planner: chooses only valid configurations and explains every decision. */
public final class TankPlanner {
    public static final class Cycle {
        public int index, rolls; public double volumeMl,productMl,waterMl; public boolean dilutionKnown; public String capacityMessage="";
    }
    public static final class Plan {
        public boolean ok; public AssistantDatabase.TankItem tank; public int cycles,batchSize; public double totalVolumeMl,totalProductMl; public boolean productKnown; public String reason="",problem=""; public final List<Cycle> cycleList=new ArrayList<>();
        public String summary(){if(!ok)return problem;StringBuilder b=new StringBuilder();b.append(tank.displayName()).append(" consigliata: ").append(reason).append("\n");b.append(cycles).append(cycles==1?" ciclo":" cicli").append(" · ");for(int i=0;i<cycleList.size();i++){Cycle c=cycleList.get(i);if(i>0)b.append(" | ");b.append(c.rolls).append(" rulli · ").append(ChemistryCalculator.formatMl(c.volumeMl)).append(" ml");}return b.toString();}
    }

    private TankPlanner(){}

    public static Plan chooseBest(List<AssistantDatabase.TankItem> tanks,String format,int rolls,double requestedTotalMl,String developer,String dilution,AssistantDatabase.ChemicalItem inventory){
        Plan best=null; double bestWaste=Double.MAX_VALUE; int bestCycles=Integer.MAX_VALUE; StringBuilder rejected=new StringBuilder();
        if(rolls<=0){Plan p=new Plan();p.problem="Numero rulli non valido.";return p;}
        if(tanks==null||tanks.isEmpty()){Plan p=new Plan();p.problem="Nessuna tank personale configurata. Il flusso può continuare con volume manuale.";return p;}
        for(AssistantDatabase.TankItem t:tanks){
            int cap=t.capacityFor(format); if(cap<=0){append(rejected,t.displayName()+": formato non supportato");continue;}
            if(!t.cpe2Compatible){append(rejected,t.displayName()+": non compatibile con JOBO CPE2");continue;}
            int maxBatch=Math.min(cap,rolls); Plan candidate=null;
            for(int batch=maxBatch;batch>=1;batch--){candidate=planFor(t,format,rolls,batch,requestedTotalMl,developer,dilution,inventory);if(candidate.ok)break;}
            if(candidate==null||!candidate.ok){append(rejected,t.displayName()+": "+(candidate==null?"nessuna configurazione valida":candidate.problem));continue;}
            double waste=candidate.totalVolumeMl;
            if(best==null||waste<bestWaste-0.1||(Math.abs(waste-bestWaste)<0.1&&candidate.cycles<bestCycles)){best=candidate;bestWaste=waste;bestCycles=candidate.cycles;}
        }
        if(best==null){Plan p=new Plan();p.problem="Nessuna tank adeguata. "+(rejected.length()==0?"NON DETERMINABILE CON I DATI DISPONIBILI":rejected.toString());return p;}
        best.reason="compatibile con "+rolls+" × "+format+" e usa il minor volume valido tra le tank disponibili";
        return best;
    }

    public static Plan planFor(AssistantDatabase.TankItem t,String format,int rolls,int batchSize,double requestedTotalMl,String developer,String dilution,AssistantDatabase.ChemicalItem inventory){
        Plan p=new Plan();p.tank=t;p.batchSize=batchSize;
        int cap=t.capacityFor(format);if(cap<=0||batchSize<=0||batchSize>cap){p.problem="capacità tank insufficiente";return p;}
        p.cycles=(int)Math.ceil(rolls/(double)batchSize);
        double perRoll=requestedTotalMl>0?requestedTotalMl/Math.max(1,rolls):0;
        int remaining=rolls; double totalProduct=0,totalVolume=0; boolean allProductKnown=true;
        for(int n=1;n<=p.cycles;n++){
            int inCycle=Math.min(batchSize,remaining); remaining-=inCycle;
            double target=Math.max(t.minRotationMl,perRoll>0?perRoll*inCycle:t.minRotationMl);
            if(!(target>0)){p.problem="volume minimo di rotazione non documentato";return p;}
            ChemistryCalculator.Result c=ChemistryCalculator.calculate(developer,dilution,target,format,inCycle);
            if(!c.inputValid){p.problem=c.error;return p;}
            if(ChemistryCalculator.CAPACITY_INSUFFICIENT.equals(c.capacityState)){
                if(c.canAdoptMinimum){target=Math.max(target,c.minimumVolumeMl);c=ChemistryCalculator.calculate(developer,dilution,target,format,inCycle);}else{p.problem=c.capacityMessage;return p;}
            }
            if(target>ChemistryCalculator.CPE2_MAX_ML+0.0001){p.problem="volume richiesto "+ChemistryCalculator.formatMl(target)+" ml > limite CPE2 600 ml";return p;}
            if(t.maxVolumeMl>0&&target>t.maxVolumeMl+0.0001){p.problem="volume richiesto superiore al massimo documentato della tank";return p;}
            Cycle cycle=new Cycle();cycle.index=n;cycle.rolls=inCycle;cycle.volumeMl=target;cycle.dilutionKnown=c.dilutionKnown;cycle.productMl=c.productMl;cycle.waterMl=c.waterMl;cycle.capacityMessage=c.capacityMessage;p.cycleList.add(cycle);totalVolume+=target;if(c.dilutionKnown)totalProduct+=c.productMl;else allProductKnown=false;
        }
        p.totalVolumeMl=totalVolume;p.totalProductMl=totalProduct;p.productKnown=allProductKnown;
        if(inventory!=null&&allProductKnown){double available=toMl(inventory.remainingAmount,inventory.unit);if(available>=0&&available+0.0001<totalProduct){p.problem="chimica insufficiente: servono "+ChemistryCalculator.formatMl(totalProduct)+" ml, disponibili "+ChemistryCalculator.formatMl(available)+" ml";return p;}}
        p.ok=true;return p;
    }

    private static double toMl(double q,String unit){if(unit==null)return-1;if("ml".equalsIgnoreCase(unit))return q;if("litri".equalsIgnoreCase(unit)||"l".equalsIgnoreCase(unit))return q*1000.0;return-1;}
    private static void append(StringBuilder b,String s){if(b.length()>0)b.append("; ");b.append(s);}
}
