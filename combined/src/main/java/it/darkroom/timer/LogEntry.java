package it.darkroom.timer;

public final class LogEntry {
    public long id;
    public long timestamp;
    public String title = "";
    public String negative = "";
    public String aperture = "";
    public String columnHeight = "";
    public String magenta = "";
    public String yellow = "";
    public String density = "";
    public String paper = "";
    public String notes = "";
    public int exposureMs = 0;
    public int testMs = 0;
    public int testCount = 0;
    public boolean favorite = false;
    public String exposureMethod = TimingMath.METHOD_SECONDS;
    public String exposureStep = TimingMath.STEP_SECONDS;
    public String testMethod = TimingMath.METHOD_SECONDS;
    public String testStep = TimingMath.STEP_SECONDS;
    public String testStripTimes = "";
    public String testStripMethod = TimingMath.MASK_REVEAL;
    /** Sequenza completa DODGE/BURN codificata da PrintSequence. */
    public String printSequence = "";
    /** Filtro M/Y realmente usato durante il provino. */
    public String testBaseFilterType = ExposureRecipe.FILTER_NONE;
    public int testBaseFilterValue = 0;
    /** Base originale/operativa, D e correzione globale. */
    public String recipeState = "";
    /** Snapshot dell’ingrandimento associato a questa specifica stampa. */
    public String enlargementMeta = "";

    /** Metadati revisione / Split Grade v0.2.6. Defaults keep old logs compatible. */
    public String exposureMode = "SINGLE";
    public int splitSoftYellow = 0;
    public int splitSoftMs = 0;
    public int splitHardMagenta = 0;
    public int splitHardMs = 0;
    public int splitSoftChosenStrip = -1;
    public int splitHardChosenStrip = -1;
    public String splitTimeOrigin = "";
    public long previousRevisionId = 0L;
    public String previousRecipeState = "";
    public String previousPrintSequence = "";
    public String revisionReason = "";
}
