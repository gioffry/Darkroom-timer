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
}
