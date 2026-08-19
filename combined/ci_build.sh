#!/usr/bin/env bash
set -euo pipefail

rm -rf work && mkdir -p work
cp -a base/v0.7.7/project work/project
cp base/v0.7.7/build_darkroom.py work/build_darkroom.py
cp base/v0.7.7/v064_icon.py work/v064_icon.py

python3 experiments/v080/prepare_v080_transform.py
python3 experiments/v080/apply_v080_print_sequence.py work
python3 experiments/v080/apply_v080_fixups.py work
python3 experiments/v081/prepare_v081_transform.py
python3 experiments/v081/apply_v081_print_plan_polish.py work
python3 experiments/v090/prepare_v090_transform.py
python3 experiments/v090/apply_v090_split_grade.py work
python3 experiments/v090/apply_v090_fixups.py work
python3 experiments/v091/prepare_v091_transform.py
python3 experiments/v091/apply_v091_timing_voice_polish.py work
python3 experiments/v0100/prepare_v0100_transform.py
python3 experiments/v0100/apply_v0100_pro_recipe.py work
python3 experiments/v0101/prepare_v0101_transform.py
python3 experiments/v0101/apply_v0101_stability_ux.py work
python3 experiments/v0102/prepare_v0102_transform.py
python3 experiments/v0102/apply_v0102_test_fixes.py work
python3 experiments/v0103/prepare_v0103_transform.py
python3 experiments/v0103/apply_v0103_split_short_exposure.py work
python3 experiments/v0104/prepare_v0104_transform.py
python3 experiments/v0104/apply_v0104_dodge_burn_voice.py work
python3 experiments/v0105/apply_v0105_premature_off_failsafe.py work
python3 experiments/v0106/apply_v0106_darkroom_assistant_r1.py work
python3 experiments/v0107/apply_v0107_darkroom_assistant_r2.py work
python3 experiments/v0108/apply_v0108_darkroom_assistant_r3.py work
python3 experiments/v0109/apply_v0109_darkroom_assistant_r4.py work
python3 experiments/v01010/prepare_v01010_transform.py
python3 experiments/v01010/apply_v01010_timer_splitgrade_provini.py work
python3 experiments/v0110/apply_v0110_darkroom_assistant_r5_r6.py work

grep -q 'homeButton.setText("←")' work/project/app/src/main/java/it/darkroom/timer/MainActivity.java

python3 assistant/build_mdc_sqlite_asset_v032.py
python3 assistant/patch_v018_visible_results.py
python3 assistant/patch_v019_search_enrichment.py
python3 assistant/patch_v020_source_brain.py
python3 assistant/patch_v021_index_fallback.py
python3 assistant/patch_v022_strict_entities.py
python3 assistant/patch_v030_offline_mdc.py
python3 assistant/patch_v031_bundled_db.py
python3 assistant/patch_v032_pure_offline.py
python3 assistant/patch_v033_startup_safe.py
python3 assistant/patch_v034_db_schema_match.py

python3 - <<'PY'
from pathlib import Path
p=Path('assistant/patch_v035_format_stop_fix.py')
s=p.read_text()
start=s.index('# Nel flusso pellicola aggiungi FORMATO')
end=s.index('# Listener formato:', start)
block=r'''# Nel flusso pellicola aggiungi FORMATO prima del campo ISO.
needle = '        isoField = edit("", InputType.TYPE_CLASS_NUMBER);'
repl = ''' + "'''" + '''        formatSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        page.addView(fieldBlock("FORMATO", formatSpinner));

        isoField = edit("", InputType.TYPE_CLASS_NUMBER);''' + "'''" + r'''
if needle not in s:
    raise SystemExit('film ISO insertion marker missing')
s = s.replace(needle, repl, 1)

'''
s=s[:start]+block+s[end:]
p.write_text(s)
PY
python3 assistant/patch_v035_format_stop_fix.py
python3 assistant/patch_v036_inline_results.py
python3 assistant/patch_v037_time_search_capacity.py
python3 assistant/patch_v038_edit_persistence_simplify.py

python3 - <<'PY'
from pathlib import Path
p=Path('combined/prepare_combined.py')
s=p.read_text()
old='''ts = ts.replace('compactButton("← HOME")', 'compactButton("⌂")')
ts = ts.replace('margin(lp(dp(94), dp(38)), 0, 0, 0, 4)',
                'margin(lp(dp(52), dp(38)), 0, 0, 0, 4)')'''
new='''ts = ts.replace('homeButton.setText("←");', 'homeButton.setText("⌂");')'''
if old not in s:
    raise SystemExit('Timer home patch marker missing')
s=s.replace(old,new,1)
s=s.replace("assert 'compactButton(\"⌂\")' in ts", "assert 'homeButton.setText(\"⌂\")' in ts")
p.write_text(s)
PY
python3 combined/prepare_combined.py

test -f combined/src/main/assets/mdc_full.sqlite
grep -q 'PRODOTTI CHIMICI' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'SVILUPPO PELLICOLA' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'BAGNI STAMPA' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'TIMER STAMPA' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'new Tank("JOBO 2520", 270, 2, 1)' combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'new Tank("JOBO 2563", 850, 6, 8)' combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'restoreFilmUiState' combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'restorePaperUiState' combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'homeButton.setText("⌂")' combined/src/main/java/it/darkroom/timer/MainActivity.java

gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.1.0.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.1.0.apk
BADGING=$("$AAPT" dump badging Darkroom-v0.1.0.apk)
echo "$BADGING" | grep -q "package: name='it.darkroom.darkroom' versionCode='1' versionName='0.1.0'"
echo "$BADGING" | grep -q "launchable-activity: name='it.darkroom.timer.home.HomeActivity'"
unzip -l Darkroom-v0.1.0.apk | grep -q 'assets/mdc_full.sqlite'
sha256sum Darkroom-v0.1.0.apk > Darkroom-v0.1.0.sha256
