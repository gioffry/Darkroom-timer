package it.darkroom.timer.assistant.paper;

/**
 * R8 paper-product metadata. Optional technical fields are nullable/empty: unknown is not zero.
 * Catalog records and user records use the same shape but retain distinct provenance.
 */
public final class PaperProductData {
    public String name="";
    public String manufacturer="";
    public String category="";
    public String concentration="";
    public String dilution="";
    public Double temperatureC=null;
    public Integer timeSeconds=null;
    public Double capacityValue=null;
    public String capacityUnit="";
    public String solutionLife="";
    public String useMode="";
    public String sourceType="NON DOCUMENTATO";
    public String sourceTitle="";
    public String sourceReference="";
    public String sourceUrl="";
    public String sourceDocumentVersion="";
    public String adaptationNote="";

    public boolean hasTemperature(){return temperatureC!=null;}
    public boolean hasTime(){return timeSeconds!=null;}
    public boolean hasCapacity(){return capacityValue!=null;}
    public boolean documented(){return !"DATO PERSONALE".equals(sourceType)&&!"NON DOCUMENTATO".equals(sourceType);}
}
