package it.darkroom.timer;

/** Geometry and measured column-scale offset for the JOBO/LPL 7451. */
public final class Lpl7451Geometry {
    /** Scale index read during the mechanical measurement. */
    public static final double MEASURED_SCALE = 67.0;
    /** Distance from the negative plane to the bare baseboard at the measured index. */
    public static final double MEASURED_NEGATIVE_TO_BASEBOARD_CM = 73.0;
    /** Height of the easel used for printing: 6 mm. */
    public static final double EASEL_HEIGHT_CM = 0.6;
    /** Fixed distance added by the LPL geometry between scale index and bare baseboard. */
    public static final double NEGATIVE_PLANE_OFFSET_CM =
            MEASURED_NEGATIVE_TO_BASEBOARD_CM - MEASURED_SCALE;
    /** Fixed distance added by the LPL geometry between scale index and paper plane. */
    public static final double SCALE_TO_PAPER_OFFSET_CM =
            NEGATIVE_PLANE_OFFSET_CM - EASEL_HEIGHT_CM;

    private Lpl7451Geometry() {}

    /** Thin-lens negative-to-paper distance for magnification beta and nominal focal length. */
    public static double negativeToPaperCm(double beta, int lensMm) {
        if (!(beta > 0.0) || lensMm <= 0 || Double.isInfinite(beta) || Double.isNaN(beta)) {
            throw new IllegalArgumentException("Invalid enlargement geometry");
        }
        double focalCm = lensMm / 10.0;
        return focalCm * (beta + 1.0 / beta + 2.0);
    }

    /** LPL column-scale index corresponding to the requested paper-plane distance. */
    public static double scaleFor(double beta, int lensMm) {
        return negativeToPaperCm(beta, lensMm) - SCALE_TO_PAPER_OFFSET_CM;
    }

    /** Paper-plane distance represented by a physical LPL scale reading. */
    public static double paperDistanceForScale(double scale) {
        return scale + SCALE_TO_PAPER_OFFSET_CM;
    }
}
