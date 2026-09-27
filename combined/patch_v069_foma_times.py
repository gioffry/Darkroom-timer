#!/usr/bin/env python3
"""Darkroom 0.6.9: use direct FOMA FP4+/Excel times and remove blanket JOBO -15%."""

from pathlib import Path
import sqlite3

MDC = Path("combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
DEV = Path("combined/src/main/java/it/darkroom/assistant/DevTimeEngine.java")
ACT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
DB = Path("combined/src/main/assets/mdc_full.sqlite")

mdc = MDC.read_text(encoding="utf-8")
dev = DEV.read_text(encoding="utf-8")
act = ACT.read_text(encoding="utf-8")

if "FOMA_TIMES_069" in mdc:
    print("foma_times_069=ALREADY_APPLIED")
    raise SystemExit(0)

# Remove the universal rotary reduction. Source/manufacturer time is the baseline.
mdc = mdc.replace(
    '    private static final double JOBO_FACTOR = 0.85;\n',
    '    // FOMA_TIMES_069 — no universal rotary correction is applied automatically.\n'
    '    private static final double JOBO_FACTOR = 1.0;\n',
    1,
)
dev = dev.replace(
    '    private static final double JOBO_FACTOR = 0.85;\n',
    '    // FOMA_TIMES_069 — keep source time; rotary calibration is combination-specific.\n'
    '    private static final double JOBO_FACTOR = 1.0;\n',
    1,
)

# Mark lookup results as not universally JOBO-adjusted.
mdc = mdc.replace(
    'format == null ? "35" : format, tempConverted, true, warning,\n',
    'format == null ? "35" : format, tempConverted, false, warning,\n',
    1,
)
dev = dev.replace(
    'row.film, row.developer, row.dilution, row.iso, format,\n'
    '                 tempConverted, true, warning, diagnostic);',
    'row.film, row.developer, row.dilution, row.iso, format,\n'
    '                 tempConverted, false, warning, diagnostic);',
    1,
)

# Give direct FOMA rows their own source label/diagnostic.
old = '''            return new DevTimeEngine.Result(true, low, high, baseLow, baseHigh,
                    row.temp, targetTemp, SOURCE_NAME, row.sourceUrl,
                    row.film, row.developer, row.dilution, row.iso,
                    format == null ? "35" : format, tempConverted, false, warning,
                    "Dato letto dal database offline sincronizzato da Digitaltruth; nessuna ricerca web durante il calcolo.");'''
new = '''            boolean directFoma = row.sourceUrl != null && row.sourceUrl.contains("foma.cz/");
            String sourceName = directFoma
                    ? "FOMA BOHEMIA · tabella ufficiale"
                    : SOURCE_NAME;
            String diagnostic = directFoma
                    ? "Dato diretto FOMA per pellicola, rivelatore, diluizione, ISO e temperatura selezionati."
                    : "Dato letto dal database offline sincronizzato da Digitaltruth; nessuna ricerca web durante il calcolo.";
            return new DevTimeEngine.Result(true, low, high, baseLow, baseHigh,
                    row.temp, targetTemp, sourceName, row.sourceUrl,
                    row.film, row.developer, row.dilution, row.iso,
                    format == null ? "35" : format, tempConverted, false, warning,
                    diagnostic);'''
if old not in mdc:
    raise SystemExit("v0.6.9 FOMA source return marker missing")
mdc = mdc.replace(old, new, 1)

# UI must no longer present a generic -15% as an exact JOBO time.
act = act.replace(
    'addFilmTimeField(summary, "TEMPO JOBO CPE2 · " + dilution,',
    'addFilmTimeField(summary, "TEMPO CPE2 DI PARTENZA · " + dilution,',
    1,
)
act = act.replace(
    'resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());',
    'resultLine(filmResultBox, "TEMPO CPE2 DI PARTENZA", result.finalDisplay());',
    1,
)
act = act.replace(
    'resultLine(filmResultBox, "TEMPO JOBO CPE2", "Tempo non disponibile");',
    'resultLine(filmResultBox, "TEMPO CPE2 DI PARTENZA", "Tempo non disponibile");',
    1,
)
old_adapt = '''            conversion += "\\nJOBO CPE2: rotazione continua, adattamento −15%";'''
new_adapt = '''            conversion += "\\nJOBO CPE2: rotazione continua; nessuna riduzione percentuale universale applicata. Il tempo fonte è usato come punto di partenza." ;'''
if old_adapt not in act:
    raise SystemExit("v0.6.9 JOBO adaptation text marker missing")
act = act.replace(old_adapt, new_adapt, 1)

MDC.write_text(mdc, encoding="utf-8")
DEV.write_text(dev, encoding="utf-8")
ACT.write_text(act, encoding="utf-8")

# Authoritative FOMA table:
# Ilford FP4 Plus 125 @ 20 C + Fomadon Excel: stock 10 min, 1+1 14 min.
FOMA_URL = "https://www.foma.cz/ew/33a06207-643b-4282-94ff-2c1953493fcd-en"
con = sqlite3.connect(DB)
try:
    cur = con.cursor()
    stock = cur.execute(
        "SELECT id FROM times WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso=?",
        ("ilford fp4+", "fomadon excel", "stock", 125)
    ).fetchall()
    if len(stock) != 1:
        raise SystemExit(f"v0.6.9 expected one FP4+/Excel stock row, got {len(stock)}")
    cur.execute(
        """UPDATE times
           SET time35='10',time120='10',timesheet='10',temp=20.0,
               notes='FOMA official table: FP4 Plus 125, Fomadon Excel stock, 20 C.',
               source_url=?
           WHERE id=?""",
        (FOMA_URL, stock[0][0])
    )

    cur.execute(
        "DELETE FROM times WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso=?",
        ("ilford fp4+", "fomadon excel", "1+1", 125)
    )
    cur.execute(
        """INSERT INTO times(
             film,film_norm,developer,developer_norm,dilution,dilution_norm,iso,
             time35,time120,timesheet,temp,notes,source_url
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "Ilford FP4+", "ilford fp4+", "Fomadon Excel", "fomadon excel",
            "1+1", "1+1", 125, "14", "14", "14", 20.0,
            "FOMA official table: FP4 Plus 125, Fomadon Excel 1+1, 20 C.",
            FOMA_URL
        )
    )
    con.commit()

    got = cur.execute(
        """SELECT dilution_norm,time35,time120,timesheet,temp,source_url
           FROM times
           WHERE film_norm='ilford fp4+' AND developer_norm='fomadon excel' AND iso=125
           ORDER BY dilution_norm"""
    ).fetchall()
    expected = [
        ("1+1", "14", "14", "14", 20.0, FOMA_URL),
        ("stock", "10", "10", "10", 20.0, FOMA_URL),
    ]
    if got != expected:
        raise SystemExit(f"v0.6.9 FOMA rows mismatch: {got!r}")
finally:
    con.close()

for marker in [
    "FOMA_TIMES_069",
    "JOBO_FACTOR = 1.0",
    "FOMA BOHEMIA · tabella ufficiale",
]:
    if marker not in mdc:
        raise SystemExit("v0.6.9 Mdc guardrail missing: " + marker)
if 'TEMPO CPE2 DI PARTENZA · " + dilution' not in act:
    raise SystemExit("v0.6.9 UI time heading guardrail missing")
if "nessuna riduzione percentuale universale applicata" not in act:
    raise SystemExit("v0.6.9 UI JOBO note guardrail missing")

print("foma_times_069=APPLIED")
print("fp4_excel_stock_20c=10_MIN_DIRECT_FOMA")
print("fp4_excel_1plus1_20c=14_MIN_DIRECT_FOMA")
print("universal_jobo_minus15=REMOVED")
print("primary_time=SOURCE_BASELINE")
