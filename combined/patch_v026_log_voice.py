#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
java = root / 'src/main/java/it/darkroom/timer'
service = java / 'SonoffArmService.java'
logentry = java / 'LogEntry.java'
logstore = java / 'LogStore.java'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.2.6 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.2.6 OK', label, flush=True)

for p, needle in [
    (service, 'private String testPreExposurePrompt()'),
    (service, 'private String splitPhasePrompt(String phase)'),
    (service, 'Mantieni il cyan a zero'),
    (logentry, 'public String enlargementMeta = "";'),
    (logstore, 'enc("ENL|" + (e.enlargementMeta == null ? "" : e.enlargementMeta))'),
]:
    if needle not in rd(p):
        raise SystemExit('v0.2.6 base v0.2.5 non riconosciuta: ' + needle)

# -----------------------------------------------------------------------------
# LOG: explicit exposure mode, four Split Grade fields, chosen strips, origin,
# and a non-destructive pointer/snapshot of the previous revision.
# -----------------------------------------------------------------------------
rep(logentry,
'''    /** Snapshot dell’ingrandimento associato a questa specifica stampa. */\n    public String enlargementMeta = "";\n}''',
'''    /** Snapshot dell’ingrandimento associato a questa specifica stampa. */\n    public String enlargementMeta = "";\n\n    /** Metadati revisione / Split Grade v0.2.6. Defaults keep old logs compatible. */\n    public String exposureMode = "SINGLE";\n    public int splitSoftYellow = 0;\n    public int splitSoftMs = 0;\n    public int splitHardMagenta = 0;\n    public int splitHardMs = 0;\n    public int splitSoftChosenStrip = -1;\n    public int splitHardChosenStrip = -1;\n    public String splitTimeOrigin = "";\n    public long previousRevisionId = 0L;\n    public String previousRecipeState = "";\n    public String previousPrintSequence = "";\n    public String revisionReason = "";\n}''','LogEntry revision fields')

old_tag_parse = '''                if (f.length > 0) {\n                    try {\n                        String tagged = dec(f[f.length - 1]);\n                        if (tagged.startsWith("ENL|")) e.enlargementMeta = tagged.substring(4);\n                    } catch (Exception ignored) {}\n                }'''
new_tag_parse = '''                // Tagged extension fields: old payloads remain valid and ENL stays readable.\n                for (int i = 25; i < f.length; i++) {\n                    try {\n                        String tagged = dec(f[i]);\n                        if (tagged.startsWith("ENL|")) {\n                            e.enlargementMeta = tagged.substring(4);\n                        } else if (tagged.startsWith("REV2|")) {\n                            String[] r = tagged.split("\\\\|", -1);\n                            if (r.length >= 13) {\n                                e.exposureMode = textOr(dec(r[1]), "SINGLE");\n                                try { e.splitSoftYellow = Integer.parseInt(r[2]); } catch (Exception ignored) {}\n                                try { e.splitSoftMs = Integer.parseInt(r[3]); } catch (Exception ignored) {}\n                                try { e.splitHardMagenta = Integer.parseInt(r[4]); } catch (Exception ignored) {}\n                                try { e.splitHardMs = Integer.parseInt(r[5]); } catch (Exception ignored) {}\n                                try { e.splitSoftChosenStrip = Integer.parseInt(r[6]); } catch (Exception ignored) {}\n                                try { e.splitHardChosenStrip = Integer.parseInt(r[7]); } catch (Exception ignored) {}\n                                e.splitTimeOrigin = dec(r[8]);\n                                try { e.previousRevisionId = Long.parseLong(r[9]); } catch (Exception ignored) {}\n                                e.previousRecipeState = dec(r[10]);\n                                e.previousPrintSequence = dec(r[11]);\n                                e.revisionReason = dec(r[12]);\n                            }\n                        }\n                    } catch (Exception ignored) {}\n                }'''
rep(logstore, old_tag_parse, new_tag_parse, 'parse tagged revision metadata')

old_write_tag = '''            out.append('\\t').append(enc("ENL|" + (e.enlargementMeta == null ? "" : e.enlargementMeta)));'''
new_write_tag = '''            out.append('\\t').append(enc("ENL|" + (e.enlargementMeta == null ? "" : e.enlargementMeta)));\n            String revisionTag = "REV2|"\n                    + enc(textOr(e.exposureMode, "SINGLE")) + "|"\n                    + e.splitSoftYellow + "|" + e.splitSoftMs + "|"\n                    + e.splitHardMagenta + "|" + e.splitHardMs + "|"\n                    + e.splitSoftChosenStrip + "|" + e.splitHardChosenStrip + "|"\n                    + enc(e.splitTimeOrigin) + "|" + e.previousRevisionId + "|"\n                    + enc(e.previousRecipeState) + "|" + enc(e.previousPrintSequence) + "|"\n                    + enc(e.revisionReason);\n            out.append('\\t').append(enc(revisionTag));'''
rep(logstore, old_write_tag, new_write_tag, 'write tagged revision metadata')

# -----------------------------------------------------------------------------
# Service persistence: the legacy aggregate remains only for old consumers;
# the real Split recipe is always stored as four distinct fields.
# -----------------------------------------------------------------------------
old_print_persist = '''        if (mode == MODE_PRINT) {\n            e.putInt("lastPrintMs", printSequence != null && printSequence.hasSplit() ? printSequence.split.totalMs() : widthMs);\n            e.putString("lastPrintMethod", timingMethod);\n            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));\n            e.putString("lastPrintSequence", printSequence == null ? "" : printSequence.encode());\n            e.putString("lastRecipeState", recipeState == null ? "" : recipeState);\n            e.putLong("lastPrintAt", now);\n        } else {'''
new_print_persist = '''        if (mode == MODE_PRINT) {\n            boolean split = printSequence != null && printSequence.hasSplit();\n            // lastPrintMs is retained as a legacy aggregate only. Split logic never uses it\n            // to reconstruct or constrain the two experimentally found exposures.\n            e.putInt("lastPrintMs", split ? printSequence.split.totalMs() : widthMs);\n            e.putString("lastExposureMode", split ? "SPLIT_GRADE" : "SINGLE");\n            if (split) {\n                e.putInt("lastSplitSoftYellow", printSequence.split.softYellow);\n                e.putInt("lastSplitSoftMs", printSequence.split.softMs);\n                e.putInt("lastSplitHardMagenta", printSequence.split.hardMagenta);\n                e.putInt("lastSplitHardMs", printSequence.split.hardMs);\n            } else {\n                e.remove("lastSplitSoftYellow").remove("lastSplitSoftMs")\n                        .remove("lastSplitHardMagenta").remove("lastSplitHardMs");\n            }\n            e.putString("lastPrintMethod", timingMethod);\n            e.putString("lastPrintStep", TimingMath.stepLabel(timingMethod));\n            e.putString("lastPrintSequence", printSequence == null ? "" : printSequence.encode());\n            e.putString("lastRecipeState", recipeState == null ? "" : recipeState);\n            e.putLong("lastPrintAt", now);\n        } else {'''
rep(service, old_print_persist, new_print_persist, 'persist four Split fields')

# -----------------------------------------------------------------------------
# VOICE: no cyan references; spoken durations use the word "secondi", never "s".
# -----------------------------------------------------------------------------
voice_helper_anchor = '''    private String testPreExposurePrompt() {\n'''
voice_helper = '''    private static String voiceSeconds(int ms) {\n        int safe = Math.max(0, ms);\n        if (safe % 1000 == 0) return (safe / 1000) + " secondi";\n        return String.format(Locale.ITALY, "%.1f secondi", safe / 1000.0);\n    }\n\n'''
rep(service, voice_helper_anchor, voice_helper + voice_helper_anchor, 'voice seconds helper')

rep(service,
'''    private String testPreExposurePrompt() {\n        return "Esposizione morbida su tutta la nuova striscia. Imposta giallo " + testPreExposureFilterValue\n                + ". Azzera il magenta. Mantieni il cyan a zero. Tempo morbido: " + seconds(testPreExposureMs) + ".";\n    }\n\n    private String testHardTransitionPrompt() {\n        return "Esposizione morbida completata. Azzera il giallo. Imposta magenta " + testBaseFilterValue\n                + ". Mantieni il cyan a zero. Premi il pulsante fisico per iniziare il provino duro.";\n    }''',
'''    private String testPreExposurePrompt() {\n        return "Esposizione morbida su tutta la nuova striscia. Imposta giallo " + testPreExposureFilterValue\n                + ". Azzera il magenta. Tempo morbido: " + voiceSeconds(testPreExposureMs) + ".";\n    }\n\n    private String testHardTransitionPrompt() {\n        return "Esposizione morbida completata. Azzera il giallo. Imposta magenta " + testBaseFilterValue\n                + ". Primo impulso duro: " + voiceSeconds(currentPulseWidthMs)\n                + ". Premi il pulsante fisico per iniziare il provino duro.";\n    }''','Split provino voice without cyan')

rep(service,
'''    private String splitPhasePrompt(String phase) {\n        boolean hard = PrintCorrection.PHASE_HARD.equals(phase);\n        String d = dodgePreparationText(phase);\n        StringBuilder b = new StringBuilder();\n        b.append(hard ? "Magenta " : "Giallo ")\n                .append(hard ? printSequence.split.hardMagenta : printSequence.split.softYellow).append(".");\n        if (!d.isEmpty()) b.append(" Prepara il dodge ").append(d).append(".");\n        b.append(" Premi il pulsante.");\n        return b.toString();\n    }''',
'''    private String splitPhasePrompt(String phase) {\n        boolean hard = PrintCorrection.PHASE_HARD.equals(phase);\n        String d = dodgePreparationText(phase);\n        StringBuilder b = new StringBuilder();\n        if (hard) {\n            b.append("Esposizione due di due. Azzera il giallo. Imposta magenta ")\n                    .append(printSequence.split.hardMagenta).append(". Tempo duro: ")\n                    .append(voiceSeconds(printSequence.split.hardMs)).append(".");\n        } else {\n            b.append("Esposizione uno di due. Imposta giallo ")\n                    .append(printSequence.split.softYellow).append(". Azzera il magenta. Tempo morbido: ")\n                    .append(voiceSeconds(printSequence.split.softMs)).append(".");\n        }\n        if (!d.isEmpty()) b.append(" Prepara il dodge ").append(d).append(".");\n        b.append(" Premi il pulsante.");\n        return b.toString();\n    }''','complete Split print voice sequence')

rep(service,
'''    private String burnFilterInstruction(PrintCorrection burn) {\n        if (burn == null || printSequence == null || !printSequence.hasSplit()) return "";\n        String mode = PrintCorrection.normalizeBurnFilter(burn.burnFilterMode);\n        if (PrintCorrection.BURN_FILTER_M_SPLIT.equals(mode)) return "Imposta Magenta " + printSequence.split.hardMagenta;\n        if (PrintCorrection.BURN_FILTER_CUSTOM_Y.equals(mode)) return "Imposta Giallo " + PrintCorrection.snap5(burn.burnFilterValue);\n        if (PrintCorrection.BURN_FILTER_CUSTOM_M.equals(mode)) return "Imposta Magenta " + PrintCorrection.snap5(burn.burnFilterValue);\n        return "Imposta Giallo " + printSequence.split.softYellow;\n    }''',
'''    private String burnFilterInstruction(PrintCorrection burn) {\n        if (burn == null || printSequence == null || !printSequence.hasSplit()) return "";\n        String mode = PrintCorrection.normalizeBurnFilter(burn.burnFilterMode);\n        if (PrintCorrection.BURN_FILTER_M_SPLIT.equals(mode)) return "Azzera il giallo e imposta Magenta " + printSequence.split.hardMagenta;\n        if (PrintCorrection.BURN_FILTER_CUSTOM_Y.equals(mode)) return "Azzera il magenta e imposta Giallo " + PrintCorrection.snap5(burn.burnFilterValue);\n        if (PrintCorrection.BURN_FILTER_CUSTOM_M.equals(mode)) return "Azzera il giallo e imposta Magenta " + PrintCorrection.snap5(burn.burnFilterValue);\n        return "Azzera il magenta e imposta Giallo " + printSequence.split.softYellow;\n    }''','burn filter change reminds zeroing')

# Hard guards.
sv = rd(service)
le = rd(logentry)
ls = rd(logstore)
for needle in [
    'voiceSeconds(printSequence.split.softMs)',
    'voiceSeconds(printSequence.split.hardMs)',
    'Esposizione uno di due',
    'Esposizione due di due',
    'Azzera il magenta',
    'Azzera il giallo',
    'lastSplitSoftYellow',
    'lastSplitHardMs',
]:
    if needle not in sv: raise SystemExit('v0.2.6 service guard missing: ' + needle)
if 'cyan' in sv.lower() or 'ciano' in sv.lower():
    raise SystemExit('v0.2.6 voice guard: riferimento cyan/ciano ancora presente nel service')
for needle in ['exposureMode', 'splitSoftChosenStrip', 'previousRevisionId', 'previousPrintSequence']:
    if needle not in le: raise SystemExit('v0.2.6 LogEntry guard missing: ' + needle)
for needle in ['REV2|', 'previousRecipeState', 'previousPrintSequence', 'revisionReason']:
    if needle not in ls: raise SystemExit('v0.2.6 LogStore guard missing: ' + needle)
print('v0.2.6 LOG/VOICE TRANSFORM OK', flush=True)
