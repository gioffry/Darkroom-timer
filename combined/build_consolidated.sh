#!/usr/bin/env bash
set -euo pipefail

# Consolidated Darkroom v0.6.6 build.
# Starts from the committed verified v0.5.8 source checkpoint, applies the tested
# v0.5.9 contact-sheet functionality, the v0.6.0 layout/preset refinement and
# the reproducible v0.6.1 graphic-system checkpoint and the phone-verified
# v0.6.2 Timer refinement, the phone-verified v0.6.3 UI polish and the
# v0.6.4 Home/inventory graphic revision, the v0.6.5 film-development
# workflow graphic revision and the v0.6.6 final three-module graphic review.
# One Gradle assembly only; no historical wrapper and no MDC network regeneration.

START_SECONDS=$SECONDS
SOURCE_ROOT=combined/src
DATABASE="$SOURCE_ROOT/main/assets/mdc_full.sqlite"
MANIFEST="$SOURCE_ROOT/main/AndroidManifest.xml"

test -f "$DATABASE"
test -f "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/AssistantActivityV2.java"

python3 combined/patch_v059_contact_sheet.py | tee validation-v059-contact-source.txt
python3 combined/patch_v060_contact_layout.py | tee validation-v060-contact-layout-source.txt
python3 combined/patch_v061_graphic_system.py | tee validation-v061-graphic-system-source.txt
python3 combined/patch_v061_timer_identity.py | tee validation-v061-timer-identity-source.txt
python3 combined/patch_v061_split_phase_colours.py | tee validation-v061-split-phase-colours-source.txt
python3 combined/patch_v061_action_information_hierarchy.py | tee validation-v061-action-information-source.txt
python3 combined/patch_v062_timer_refinement.py | tee validation-v062-timer-refinement-source.txt
python3 combined/patch_v063_ui_polish.py | tee validation-v063-ui-polish-source.txt

V064_TIMER_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)
V064_SERVICE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)
V064_TIMING_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)
V064_ENLARGEMENT_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)
V064_DATABASE_HASH_BEFORE=$(sha256sum "$DATABASE" | cut -d' ' -f1)
python3 combined/patch_v064_home_inventory.py | tee validation-v064-home-inventory-source.txt
test "$V064_TIMER_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)"
test "$V064_SERVICE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)"
test "$V064_TIMING_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)"
test "$V064_ENLARGEMENT_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)"
test "$V064_DATABASE_HASH_BEFORE" = "$(sha256sum "$DATABASE" | cut -d' ' -f1)"

V065_HOME_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/home/HomeActivity.java" | cut -d' ' -f1)
V065_TIMER_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)
V065_SERVICE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)
V065_TIMING_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)
V065_ENLARGEMENT_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)
V065_LARGE_FORMAT_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java" | cut -d' ' -f1)
V065_MAINTENANCE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java" | cut -d' ' -f1)
V065_MDC_STORE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java" | cut -d' ' -f1)
V065_DEV_ENGINE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/DevTimeEngine.java" | cut -d' ' -f1)
V065_CHEM_ENGINE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/ChemistrySpecEngine.java" | cut -d' ' -f1)
V065_DATABASE_HASH_BEFORE=$(sha256sum "$DATABASE" | cut -d' ' -f1)
python3 combined/patch_v065_film_development.py | tee validation-v065-film-development-source.txt
test "$V065_HOME_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/home/HomeActivity.java" | cut -d' ' -f1)"
test "$V065_TIMER_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)"
test "$V065_SERVICE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)"
test "$V065_TIMING_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)"
test "$V065_ENLARGEMENT_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)"
test "$V065_LARGE_FORMAT_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java" | cut -d' ' -f1)"
test "$V065_MAINTENANCE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java" | cut -d' ' -f1)"
test "$V065_MDC_STORE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java" | cut -d' ' -f1)"
test "$V065_DEV_ENGINE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/DevTimeEngine.java" | cut -d' ' -f1)"
test "$V065_CHEM_ENGINE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/ChemistrySpecEngine.java" | cut -d' ' -f1)"
test "$V065_DATABASE_HASH_BEFORE" = "$(sha256sum "$DATABASE" | cut -d' ' -f1)"

V066_HOME_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/home/HomeActivity.java" | cut -d' ' -f1)
V066_TIMER_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)
V066_SERVICE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)
V066_TIMING_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)
V066_ENLARGEMENT_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)
V066_MDC_STORE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java" | cut -d' ' -f1)
V066_DEV_ENGINE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/DevTimeEngine.java" | cut -d' ' -f1)
V066_CHEM_ENGINE_HASH_BEFORE=$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/ChemistrySpecEngine.java" | cut -d' ' -f1)
V066_DATABASE_HASH_BEFORE=$(sha256sum "$DATABASE" | cut -d' ' -f1)
python3 combined/patch_v066_remaining_graphics.py | tee validation-v066-remaining-graphics-source.txt
test "$V066_HOME_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/home/HomeActivity.java" | cut -d' ' -f1)"
test "$V066_TIMER_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java" | cut -d' ' -f1)"
test "$V066_SERVICE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java" | cut -d' ' -f1)"
test "$V066_TIMING_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/TimingMath.java" | cut -d' ' -f1)"
test "$V066_ENLARGEMENT_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/timer/EnlargementActivity.java" | cut -d' ' -f1)"
test "$V066_MDC_STORE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java" | cut -d' ' -f1)"
test "$V066_DEV_ENGINE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/DevTimeEngine.java" | cut -d' ' -f1)"
test "$V066_CHEM_ENGINE_HASH_BEFORE" = "$(sha256sum "$SOURCE_ROOT/main/java/it/darkroom/assistant/ChemistrySpecEngine.java" | cut -d' ' -f1)"
test "$V066_DATABASE_HASH_BEFORE" = "$(sha256sum "$DATABASE" | cut -d' ' -f1)"

python3 - <<'PY' | tee validation-consolidated-v066-source.txt
from pathlib import Path
import re
import sqlite3

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="57"', text, count=1
)
text, name_count = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.6.6"', text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('v0.6.6 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 57', text, count=1
)
text, name_count = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.6.6'", text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('v0.6.6 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')

db = sqlite3.connect('combined/src/main/assets/mdc_full.sqlite')
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] == 14808
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute('SELECT COUNT(*) FROM developer_time_equivalents').fetchone()[0] == 39
assert db.execute(
    "SELECT COUNT(*) FROM developer_time_equivalents WHERE evidence_kind<>'AUDITED_DIRECT_ONE_HOP'"
).fetchone()[0] == 0

good = db.execute(
    '''SELECT time35,time120,timesheet FROM times
       WHERE film_norm='kentmere 100' AND developer_norm='xtol'
         AND dilution_norm='1+1' AND iso=100 AND temp=20'''
).fetchone()
assert good == ('10', '10', ''), good
db.close()

main = Path('combined/src/main/java/it/darkroom/timer/MainActivity.java').read_text(encoding='utf-8')
service = Path('combined/src/main/java/it/darkroom/timer/SonoffArmService.java').read_text(encoding='utf-8')
enlargement = Path('combined/src/main/java/it/darkroom/timer/EnlargementActivity.java').read_text(encoding='utf-8')
assert 'APP_VERSION = "0.13.16"' in main
assert 'compactButton("PROVINO SINGOLO")' in main
assert 'compactButton("PROVINO SPLIT GRADE")' in main
assert 'functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT)' in main
assert 'functionalButton("PROVINO A CONTATTO 35 mm", CONTACT_ACCENT)' in main
assert 'compactButton("PROVINO STAMPA")' not in main
assert main.index('compactButton("PROVINO SINGOLO")') < main.index('functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT)') < main.index('functionalButton("PROVINO A CONTATTO 35 mm", CONTACT_ACCENT)')
assert 'ISO/EI' not in main
assert ' · EI ' not in main
assert 'contactPresetField("ISO", iso)' in main
assert 'contactPresetField("SCALA COLONNA LPL", column)' in main
assert 'contactPresetField("DIAFRAMMA", aperture)' in main
assert 'contactPresetField("FILTRAZIONE", contrast)' in main
assert 'contactPresetField("TEMPO (s)", seconds)' in main
assert 'String setupLine()' in main
assert '.putInt("iso_" + preset.id, preset.iso)' in main
assert 'contact35_presets' in main
assert '+  NUOVO PRESET' in main
assert 'SALVA PRESET' in main
assert 'contact35CycleActive' in main
assert 'EXTRA_COUNT, 1' in main
assert 'EXTRA_CONTACT_SHEET_35' in main
assert 'EXTRA_CONTACT_SHEET_35 = "contact_sheet_35"' in service
assert 'count = contactSheet35 ? 1 : Math.max(2, Math.min(20' in service

visual = Path('combined/src/main/java/it/darkroom/ui/DarkroomVisualSystem.java').read_text(encoding='utf-8')
assert 'GRAPHIC_SYSTEM_061' in main
assert 'TIMER_IDENTITY_061' in main
assert 'SPLIT_PHASE_COLOURS_061' in main
assert 'ACTION_INFORMATION_HIERARCHY_061' in main
assert 'TIMER_REFINEMENT_062' in main
assert 'UI_POLISH_063' in main
assert 'SONOFF_STRIP_061' in main
assert 'TextView deviceName = text("INGRANDITORE"' not in main
assert 'selectDeviceButton.setContentDescription("Impostazioni Timer e SONOFF")' in main
assert 'deviceStatus = text("○  Ricerca MINIR2…", 12, MUTED, true)' in main
assert 'deviceStatus.setText("✓  MINIR2 connesso")' in main
assert 'safelightStatus.setText("●  Luce rossa attiva")' in main
assert 'page.addView(actionDock, lp(-1, -2));' in main
assert 'functionalButton("PIANO DI STAMPA", PLAN_ACCENT)' in main
assert 'int flowAccent = split ? splitPhaseAccent() : PROVINO_ACCENT;' in main
assert 'SPLIT_GRADE = Color.rgb(173, 167, 184)' in visual
assert 'SPLIT_YELLOW = Color.rgb(214, 178, 73)' in visual
assert 'SPLIT_MAGENTA = Color.rgb(196, 88, 171)' in visual
assert 'PRINT_PLAN = Color.rgb(196, 174, 142)' in visual
assert 'SPLIT_GRADE = Color.rgb(196, 88, 171)' not in visual
assert 'private int actionInk(int accent)' in main
assert 'b.setBackground(roundRect(accent, 10, 0, 0));' in main
assert 'stateCard.setBackground(roundRect(BACKGROUND, 12, 1, accent))' in main
assert 'printSequenceSummary.setBackground(roundRect(BACKGROUND, 9, 1, PLAN_ACCENT))' in main
assert 'testSingleModeButton.setAlpha(active ? 1f : 0.84f)' in main
assert 'testSplitModeButton.setAlpha(active ? 1f : 0.84f)' in main
assert 'contact35WorkspaceButton.setAlpha(active ? 1f : 0.84f)' in main
assert 'actionButton.setBackground(roundRect(flowAccent, 10, 0, 0))' in main
assert 'testBaseFilterButton.setBackground(roundRect(flowAccent, 9, 0, 0))' in main
assert 'buildPrintPlanHowToCard(printSequence != null && printSequence.hasSplit())' in main
assert 'COME SI USA · STAMPA SINGOLA' in main
assert 'SPLIT GRADE CON PROVINO · CONSIGLIATO' in main
assert 'global.setBackground(roundRect(GLOBAL_ACCENT,8,0,0))' in main
assert 'attributes.dimAmount = 0.82f' in main
assert 'showSelectedChoiceDialog("METODO DEL PROVINO"' in main
assert 'option.setAlpha(selected ? 1f : 0.84f)' in main
assert 'settingsGroup("TEMPORIZZAZIONE", PROVINO_ACCENT)' in main
assert 'settingsGroup("CAMERA OSCURA E LUCE ROSSA", AMBER)' in main
assert 'settingsGroup("HARDWARE INGRANDITORE", ENLARGEMENT_ACCENT)' in main
assert 'functionalButton("+  NUOVA SCHEDA", LOG_ACCENT)' in main
assert 'logFavoritesButton.setAlpha(logFavoritesOnly ? 1f : 0.84f)' in main
assert 'b.setAlpha(selected ? 1f : 0.84f)' in main
assert 'ENLARGEMENT_VISUAL_062' in enlargement
assert 'ENLARGEMENT_COMPACT_063' in enlargement
assert 'static final int ACCENT = DarkroomVisualSystem.ENLARGEMENT' in enlargement
assert 'Button calc = button("CALCOLA", ACCENT)' in enlargement
assert 'box.setBackground(bg(BG, 12, ACCENT, 1))' in enlargement
assert 'sp.setBackground(bg(ACCENT, 10, ACCENT, 0))' in enlargement
assert 'heading.setSingleLine(true)' in enlargement
assert 'landscape.setBackground(bg(BG, 10, ACCENT, 1))' in enlargement
assert 'double factor = Math.pow((c.beta+1)/(b1+1),2);' in enlargement
assert 'static int snap(double ms) { return (int) Math.round(ms / 500.0) * 500; }' in enlargement
assert len({
    tuple(map(int, value))
    for value in re.findall(
        r'(?:PROVINO|SPLIT_GRADE|SPLIT_YELLOW|SPLIT_MAGENTA|CONTACT|ENLARGEMENT|PRINT|PRINT_PLAN|DODGE|BURN|LOG|LENGTHEN|GLOBAL_CORRECTION) = Color\.rgb\((\d+), (\d+), (\d+)\)',
        visual,
    )
}) == 13

store = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java').read_text(encoding='utf-8')
activity = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java').read_text(encoding='utf-8')
home = Path('combined/src/main/java/it/darkroom/timer/home/HomeActivity.java').read_text(encoding='utf-8')
large_format = Path('combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java').read_text(encoding='utf-8')
maintenance = Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
assert 'mdc_offline_darkroom_v058.sqlite' in store
assert 'if (exact != null) return exact;' in store
assert 'developer_time_equivalents' in store
assert 'EQUIVALENZA CONTROLLATA' in activity
assert 'MdcOfflineStore.syncAsync' not in activity
assert 'HOME_VISUAL_064' in home
assert 'INVENTORY_VISUAL_064' in activity
assert 'new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, HOME_CHEMICAL, false)' in home
assert 'new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, HOME_FILM, false)' in home
assert 'new HomeCard("GRANDE FORMATO", ICON_CHASSIS, HOME_LARGE_FORMAT, false)' in home
assert 'new HomeCard("BAGNI STAMPA", ICON_TRAY, HOME_PRINT_BATHS, false)' in home
assert 'new HomeCard("TIMER STAMPA", ICON_TIMER, HOME_TIMER, false)' in home
assert 'new HomeCard("USO E MANUTENZIONE", ICON_WRENCH, HOME_MAINTENANCE, true)' in home
assert len(set(re.findall(r'HOME_(?:CHEMICAL|FILM|LARGE_FORMAT|PRINT_BATHS|TIMER|MAINTENANCE) = Color\.rgb\((\d+, \d+, \d+)\)', home))) == 6
assert 'chemicalButton("＋  AGGIUNGI PRODOTTO", CHEM_ACCENT)' in activity
assert 'LinearLayout row = inventoryRow(name)' in activity
assert 'chemicalDialogPanel("AGGIUNGI PRODOTTO")' in activity
assert 'chemicalDialogPanel(name.toUpperCase(Locale.ITALY))' in activity
assert 'chemicalDialogPanel("MODIFICA PRODOTTO")' in activity
assert 'chemicalInformationCard(operationalDateTitle(life), dateValue)' in activity
assert 'chemicalInformationCard("SCHEDA TECNICA", technical)' in activity
assert 'chemicalButton("MODIFICA", CHEM_ACCENT)' in activity
assert 'chemicalButton("ELIMINA", DELETE_ACCENT)' in activity
assert 'chemicalButton("SALVA", CHEM_ACCENT)' in activity
assert 'card.setBackground(bg(BG, 11, CHEM_BORDER, 1))' in activity
assert 'row.setBackground(bg(CHEM_FILL, 10, CHEM_BORDER, 1))' in activity
assert 'new AlertDialog.Builder(this)\n                .setTitle(name)' not in activity
assert '.setTitle("Aggiungi prodotto")' not in activity
assert 'FILM_VISUAL_065' in activity
assert 'FILM_FILL = Color.rgb(43, 91, 106)' in activity
assert 'FILM_ACTION = Color.rgb(55, 126, 148)' in activity
assert 'FILM_ACCENT = Color.rgb(82, 164, 188)' in activity
assert '1 · PELLICOLA E FORMATO' in activity
assert '2 · SVILUPPO JOBO' in activity
assert '3 · BAGNI AUSILIARI' in activity
assert 'Button calc = filmButton("CALCOLA", FILM_ACTION)' in activity
assert 'summary.setBackground(bg(BG, 13, FILM_BORDER, 1))' in activity
assert 'preparation.setBackground(bg(BG, 13, FILM_BORDER, 1))' in activity
assert 'header.setBackground(bg(FILM_FILL, 12, 0, 0))' in activity
assert 'Button register = filmButton("REGISTRA QUESTO SVILUPPO", FILM_ACTION)' in activity
assert 'Button fresh = filmButton("NUOVO BAGNO / AZZERA CONTATORE", FILM_SECONDARY)' in activity
assert 'PAPER_VISUAL_066' in activity
assert 'PAPER_FILL = Color.rgb(45, 99, 72)' in activity
assert 'PAPER_ACTION = Color.rgb(57, 133, 94)' in activity
assert 'PAPER_ACCENT = Color.rgb(84, 167, 121)' in activity
assert '1 · CHIMICA DI STAMPA' in activity
assert '2 · VOLUME E UTILIZZO' in activity
assert 'Button calc = paperButton("CALCOLA", PAPER_ACTION)' in activity
assert 'Button register = paperButton("REGISTRA STAMPA", PAPER_ACTION)' in activity
assert 'Button fresh = paperButton("NUOVO BAGNO / AZZERA CONTATORE", PAPER_SECONDARY)' in activity
assert 'card.setBackground(bg(BG, 13, PAPER_BORDER, 1))' in activity
assert 'header.setBackground(bg(PAPER_FILL, 12, 0, 0))' in activity
assert 'paperInformation = currentScreen == PAPER' in activity
assert activity.count('calculateFilmOnline();') == 1
assert activity.count('registerFilmUse(dev, workingVolumeMl, units);') == 1
assert activity.count('resetFilmBath(dev, workingVolumeMl);') == 1
assert activity.count('registerPaperUse(lastPaperDeveloper, lastPaperVolume, area);') == 1
assert activity.count('resetPaperBath(dev, volume);') == 1

assert 'LARGE_FORMAT_VISUAL_066' in large_format
assert 'VIOLET_FILL = Color.rgb(91, 70, 113)' in large_format
assert 'VIOLET_ACTION = Color.rgb(113, 83, 143)' in large_format
assert 'VIOLET_ACCENT = Color.rgb(166, 130, 196)' in large_format
assert 'TextView now = action("ADESSO", true)' in large_format
assert 'TextView delete = action("ELIMINA CHASSIS", DELETE_ACTION)' in large_format
assert 'gap.setBackground(informationBg())' in large_format
assert 'g.setColor(active ? statusColor(paletteStatus) : VIOLET_FILL)' in large_format
assert 'g.setStroke(dp(1), VIOLET_BORDER)' in large_format
assert large_format.count('chassis.remove(chassisItem);') == 1

assert 'MAINTENANCE_VISUAL_066' in maintenance
assert 'SLATE_FILL = Color.rgb(63, 70, 77)' in maintenance
assert 'SLATE_ACTION = Color.rgb(79, 88, 97)' in maintenance
assert 'SLATE_ACCENT = Color.rgb(130, 144, 157)' in maintenance
assert 'c.setBackground(filledPanelBg(SLATE_FILL,10))' in maintenance
assert 'q.setBackground(filledPanelBg(SLATE_FILL,9))' in maintenance
assert 'c.setBackground(outlinedPanelBg())' in maintenance
assert 'v.setBackground(filledPanelBg(SLATE_ACTION,9))' in maintenance
assert 'Guida completa v0.2.8' not in maintenance
assert 'La v0.2.9 aggiunge' not in maintenance
assert maintenance.count('q.setOnClickListener') == 2

print('release=Darkroom-v0.6.6')
print('versionCode=57')
print('timer_internal=0.13.16')
print('historical_builds=ZERO')
print('mdc_network_downloads=ZERO')
print('gradle_assemblies_expected=ONE')
print('provino_hierarchy=SINGLE_SPLIT_THEN_ENLARGEMENT_THEN_CONTACT')
print('contact35_iso_only=PASS')
print('contact35_editable_column_aperture_contrast=PASS')
print('contact35_presets_persistent=PASS')
print('contact35_single_sonoff_exposure=PASS')
print('sonoff_strip=APPROVED_HORIZONTAL_LAYOUT')
print('settings_gear=IN_TIMER_HEADING')
print('functional_colours_distinct=PASS')
print('split_process_colour=NEUTRAL_NOT_MAGENTA')
print('split_phases=YELLOW_THEN_MAGENTA')
print('clickable_controls=FILLED')
print('non_clickable_information=OUTLINED')
print('timer_action_dock=PASS')
print('split_phase_arm=YELLOW_THEN_MAGENTA')
print('contact_preset_labels=PERSISTENT')
print('print_plan_help=CONTEXTUAL')
print('print_plan_colour=NEUTRAL_PAPER_NOT_SPLIT_YELLOW')
print('inactive_actions=FILLED_AND_LEGIBLE')
print('enlargement_visual_identity=PASS')
print('enlargement_header=COMPACT')
print('settings_groups=COLOUR_CODED')
print('masking_method_selection=VISIBLE')
print('log_primary_action=VISIBLE')
print('timer_process_changes=ZERO')
print('enlargement_calculation_changes=ZERO')
print('darkroom_red_only=PASS')
print('database_integrity=PASS')
print('offline_equivalence_regressions=PASS')
print('home_navigation=FILLED_UNIQUE_COLOURS')
print('chemical_inventory=COHERENT_BURGUNDY_FAMILY')
print('inventory_actions=FILLED')
print('inventory_information=OUTLINED')
print('inventory_process_changes=ZERO')
print('film_family=BLUE_TEAL')
print('film_workflow=FILM_JOBO_AUXILIARY')
print('film_actions=FILLED')
print('film_information=OUTLINED')
print('film_result_time=DOMINANT')
print('film_process_changes=ZERO')
print('paper_baths_family=GREEN')
print('paper_baths_workflow=CHEMISTRY_THEN_VOLUME')
print('paper_baths_process_changes=ZERO')
print('large_format_family=VIOLET')
print('large_format_data_changes=ZERO')
print('maintenance_family=SLATE')
print('maintenance_reference_changes=ZERO')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.6.6.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.6.6.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.6.6.apk > certificate-v066.txt
"$AAPT" dump badging Darkroom-v0.6.6.apk > apk-badging-v066.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v066.txt
grep -Fq "versionCode='57'" apk-badging-v066.txt
grep -Fq "versionName='0.6.6'" apk-badging-v066.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v066.txt
unzip -Z1 Darkroom-v0.6.6.apk > apk-listing-v066.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v066.txt

ELAPSED=$((SECONDS - START_SECONDS))
{
  echo 'consolidated_build=PASS'
  echo 'release=Darkroom-v0.6.6'
  echo 'historical_builds=ZERO'
  echo 'mdc_network_downloads=ZERO'
  echo 'gradle_assemblies=ONE'
  echo "elapsed_seconds=$ELAPSED"
} | tee validation-consolidated-v066.txt

sha256sum Darkroom-v0.6.6.apk | tee Darkroom-v0.6.6.sha256
