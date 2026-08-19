package it.darkroom.timer.assistant.system;

import java.util.Locale;

/** Consistent R9 provenance vocabulary. Calculated/personal/unknown data are never presented as source facts. */
public final class DataProvenance {
    public static final String OFFICIAL="FONTE UFFICIALE";
    public static final String SECONDARY="FONTE SECONDARIA";
    public static final String INTERNAL_VERIFIED="DATO INTERNO VERIFICATO";
    public static final String CALCULATION="CALCOLO";
    public static final String ADAPTATION="ADATTAMENTO";
    public static final String PERSONAL="DATO PERSONALE";
    public static final String UNDOCUMENTED="NON DOCUMENTATO";
    private DataProvenance(){}

    public static String classify(String dataType,String sourceName,String calculation){
        String d=safe(dataType).toUpperCase(Locale.ITALY);String s=safe(sourceName).toUpperCase(Locale.ITALY);String c=safe(calculation).trim();
        if(d.contains("PERSON")||d.contains("UTENTE")||d.contains("USER"))return PERSONAL;
        if(d.contains("NON DOCUMENT")||d.contains("UNKNOWN")||d.contains("SCONOSCI"))return UNDOCUMENTED;
        if(d.contains("ADATT")||(!c.isEmpty()&&d.contains("CALCOL")))return ADAPTATION;
        if(d.contains("CALCOL"))return CALCULATION;
        if(d.contains("SECONDAR"))return SECONDARY;
        if(d.contains("VERIFIC"))return INTERNAL_VERIFIED;
        if(d.contains("DIRETTO")||d.contains("FONTE")||s.contains("FOMA")||s.contains("ILFORD")||s.contains("JOBO"))return OFFICIAL;
        if(!c.isEmpty())return CALCULATION;
        if(!safe(sourceName).trim().isEmpty())return SECONDARY;
        return UNDOCUMENTED;
    }

    public static String detail(String dataType,String sourceName,String sourceData,String calculation){
        StringBuilder b=new StringBuilder();b.append("Origine: ").append(classify(dataType,sourceName,calculation));
        if(!safe(sourceName).trim().isEmpty())b.append("\nProduttore/autore/riferimento: ").append(sourceName.trim());
        if(!safe(sourceData).trim().isEmpty())b.append("\nDato sorgente: ").append(sourceData.trim());
        if(!safe(calculation).trim().isEmpty())b.append("\nRegola / adattamento: ").append(calculation.trim());
        if(UNDOCUMENTED.equals(classify(dataType,sourceName,calculation)))b.append("\nNessuna fonte tecnica viene inventata.");
        return b.toString();
    }
    private static String safe(String s){return s==null?"":s;}
}
