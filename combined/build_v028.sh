#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.8 — graphical refresh.
# Base: user-tested Darkroom v0.2.7. Functional Split Grade / SONOFF logic preserved.

git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets=Path('combined/v012_assets/home_mockup')
parts=sorted(assets.glob('*.part'))
if len(parts)!=9: raise SystemExit(f'v0.2.8: expected 9 compatibility Home parts, found {len(parts)}')
encoded=''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw=base64.b64decode(encoded + '=' * (-len(encoded)%4), validate=True)
if len(raw)<50000 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WEBP': raise SystemExit('v0.2.8: compatibility Home payload invalid')
for p in parts: p.unlink()
cut=(len(encoded)+1)//2
(assets/'00.part').write_text(encoded[:cut],encoding='utf-8')
(assets/'01.part').write_text(encoded[cut:],encoding='utf-8')
PY

sed -i 's/len(raw) < 150_000/len(raw) < 40_000/' combined/patch_v021_home_font_log_fix.py
python3 -m py_compile \
  combined/patch_v025_split_grade_provino.py \
  combined/patch_v026_log_voice.py \
  combined/patch_v026_print_integration.py \
  combined/patch_v027_split_provino_safelight_pause.py \
  combined/patch_v028_graphic_refresh.py

python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v018.sh').read_text(encoding='utf-8')
required=['Darkroom-v0.1.8','versionCode="9"','versionName="0.1.8"','python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n']
for marker in required:
    if marker not in s: raise SystemExit('v0.2.8 build wrapper missing base marker: '+marker)
s=s.replace('Darkroom-v0.1.8','Darkroom-v0.2.8')
s=s.replace('versionCode="9"','versionCode="19"').replace('versionCode 9','versionCode 19').replace("versionCode='9'","versionCode='19'")
s=s.replace('versionName="0.1.8"','versionName="0.2.8"').replace("versionName '0.1.8'","versionName '0.2.8'").replace("versionName='0.1.8'","versionName='0.2.8'")
needle='python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement=(needle
    + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
    + 'python3 combined/patch_v020_enlargement_log_flow.py\\\\n'
    + 'python3 combined/patch_v020_enlargement_legacy_recipe.py\\\\n'
    + 'python3 combined/patch_v020_visual_coherence.py\\\\n'
    + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n'
    + 'python3 combined/patch_v024_home_safe_buttons.py\\\\n'
    + 'python3 combined/patch_v025_split_grade_provino.py\\\\n'
    + 'python3 combined/patch_v026_log_voice.py\\\\n'
    + 'python3 combined/patch_v026_print_integration.py\\\\n'
    + 'python3 combined/patch_v027_split_provino_safelight_pause.py\\\\n'
    + 'python3 combined/patch_v028_graphic_refresh.py\\\\n')
if s.count(needle)!=1: raise SystemExit('v0.2.8 patch insertion ambiguous')
s=s.replace(needle,replacement,1)
Path('/tmp/build_v028_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v028_generated.sh

python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists(): raise SystemExit('v0.2.8 validation file missing')
lines=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='): line='versionName=0.2.8'
    elif line.startswith('versionCode='): line='versionCode=19'
    elif line.startswith('timer_version='): line='timer_version=0.13.11'
    elif line in ('build=SUCCESS','timer_runtime_logic_unchanged=PASS','timer_source_unchanged=PASS'): continue
    if line.startswith('home_jpeg_') or line.startswith('home_bottom_') or line.startswith('home_webp_') \
            or line.startswith('home_mockup_approved=') or line.startswith('home_asset_') \
            or line.startswith('home_source_full_decode=') or line.startswith('home_packaged_full_decode=') \
            or line.startswith('home_black_screen_fix=') or line.startswith('home_no_duplicate_maintenance_overlay='):
        continue
    lines.append(line)
extras=[
'home_mode=native_final',
'home_artwork_dependency=NONE',
'home_five_visible_buttons=PASS',
'graphic_home_native_final=PASS',
'graphic_home_no_artwork=PASS',
'graphic_home_five_routes=PASS',
'graphic_home_motto=PASS',
'graphic_home_version_only=PASS',
'graphic_home_icons_native=PASS',
'graphic_home_button_size_uniform=PASS',
'graphic_timer_title=PASS',
'graphic_timer_footer_removed=PASS',
'graphic_settings_grouped_scroll=PASS',
'graphic_enlarger_card_compact=PASS',
'graphic_remove_corrections_label=PASS',
'graphic_print_summary_deduplicated=PASS',
'graphic_enlargement_setup_close_bottom=PASS',
'graphic_enlargement_resize_back_top=PASS',
'graphic_launcher_icon_darkroom_scope=PASS',
'provino_split_piece2_preserved=PASS',
'print_split_piece3_preserved=PASS',
'print_revision_piece3_preserved=PASS',
'voice_no_cyan=PASS',
'voice_seconds_word=PASS',
'provino_split_safelight_on_filter_change=PASS',
'provino_split_safelight_off_first_hard=PASS',
'provino_split_safelight_off_between_hard_strips=PASS',
'provino_single_safelight_behavior_unchanged=PASS',
'print_split_safelight_behavior_unchanged=PASS',
'sonoff_rounding_500ms=PASS',
'build=SUCCESS']
for x in extras:
    if x not in lines: lines.append(x)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
PY

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
SERVICE=combined/src/main/java/it/darkroom/timer/SonoffArmService.java
LOGENTRY=combined/src/main/java/it/darkroom/timer/LogEntry.java
LOGSTORE=combined/src/main/java/it/darkroom/timer/LogStore.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MANIFEST=combined/src/main/AndroidManifest.xml
ICON=combined/src/main/res/drawable/ic_launcher.xml

# Final native Home.
grep -q 'CAMERA OSCURA' "$HOME"
grep -q 'di Federico e Francesco' "$HOME"
grep -q 'PRODOTTI CHIMICI' "$HOME"
grep -q 'SVILUPPO PELLICOLA' "$HOME"
grep -q 'BAGNI STAMPA' "$HOME"
grep -q 'TIMER STAMPA' "$HOME"
grep -q 'USO E MANUTENZIONE' "$HOME"
grep -q 'LA PAZIENZA È PARTE DEL PROCESSO' "$HOME"
grep -q 'openAssistant("products")' "$HOME"
grep -q 'openAssistant("film")' "$HOME"
grep -q 'openAssistant("paper")' "$HOME"
grep -q 'new Intent(this, MainActivity.class)' "$HOME"
grep -q 'new Intent(this, UseMaintenanceActivity.class)' "$HOME"
grep -q 'LineIcon' "$HOME"
grep -q 'getPackageInfo(getPackageName(), 0)' "$HOME"
! grep -q 'ImageView' "$HOME"
! grep -q 'home_vintage' "$HOME"
! grep -q 'HOME PROVVISORIA' "$HOME"
! find combined/src/main/res -type f \( -name 'home_vintage.jpg' -o -name 'home_vintage.jpeg' -o -name 'home_vintage.png' -o -name 'home_vintage.webp' \) | grep -q .

# Shared top chrome and Timer graphical corrections.
grep -q 'topBar.addView(homeButton, lp(dp(46), dp(46)))' "$MAIN"
grep -q 'TextView title = text("TIMER", 27' "$MAIN"
grep -q 'label("⌂", 25, WHITE, true)' "$ASSIST"
grep -q 'new LinearLayout.LayoutParams(dp(46), dp(46))' "$ASSIST"
grep -q 'back.setTextSize(25);' "$MAINT"
grep -q 'new LinearLayout.LayoutParams(dp(46),dp(46))' "$MAINT"
! grep -q 'Darkroom Timer di F.G. - v' "$MAIN"
grep -q 'deviceCard.setPadding(dp(14), dp(9), dp(14), dp(9))' "$MAIN"
grep -q 'deviceTop.addView(selectDeviceButton, lp(dp(48), dp(36)))' "$MAIN"

# Settings grouped in one scrolling dialog.
for x in 'TEMPORIZZAZIONE' 'CAMERA OSCURA E LUCE ROSSA' 'FEEDBACK DURANTE IL LAVORO' 'DIAGNOSTICA' 'HARDWARE INGRANDITORE'; do grep -q "$x" "$MAIN"; done
grep -q 'settingsScroll.setFillViewport(true)' "$MAIN"
grep -q 'AUTORIZZA NON DISTURBARE' "$MAIN"
grep -q 'CAMBIA SONOFF SAFELIGHT' "$MAIN"

# Print plan language and compact summary.
grep -q 'RIMUOVI CORREZIONI' "$MAIN"
grep -q 'RIMUOVERE LE CORREZIONI?' "$MAIN"
grep -q 'STAMPA BASE · ' "$MAIN"
! grep -q 'AZZERA PIANO' "$MAIN"

# Enlargement navigation semantics.
grep -q 'if("resize".equals(mode)){Button back=button("←  INDIETRO"' "$ENL"
grep -q 'Button close=button("CHIUDI",BUTTON)' "$ENL"
grep -q 'Registrato nella ricetta corrente.' "$ENL"

# New whole-darkroom launcher icon.
test -s "$ICON"
grep -q '#E8CAA0' "$ICON"
grep -q '#7E231E' "$ICON"
grep -q 'android:icon="@drawable/ic_launcher"' "$MANIFEST"
! find combined/src/main/res -type f -name 'ic_launcher.png' | grep -q .

# Functional pieces 2/3/v0.2.7 must remain intact.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -q 'PROVINO_SPLIT_SOFT' "$MAIN"
grep -q 'FASE 1 DI 2 — TROVA IL MORBIDO' "$MAIN"
grep -q 'FASE 2 DI 2 — TROVA IL DURO' "$MAIN"
grep -q 'TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO' "$MAIN"
grep -q 'RIFAI SOLO IL DURO' "$MAIN"
grep -q 'RIFAI ENTRAMBI' "$MAIN"
grep -q 'public String exposureMode = "SINGLE";' "$LOGENTRY"
grep -q 'REV2|' "$LOGSTORE"
grep -q 'testSplitFilterPauseSafelightOn' "$SERVICE"
grep -q 'SPLIT PROVINO • SAFELIGHT ON per cambio filtro morbido → duro' "$SERVICE"
grep -q "SPLIT PROVINO • SAFELIGHT OFF all'avvio del provino duro; resta OFF tra le strisce" "$SERVICE"
grep -q 'Esposizione uno di due' "$SERVICE"
grep -q 'Esposizione due di due' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.softMs)' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.hardMs)' "$SERVICE"
! grep -Eiq 'cyan|ciano' "$SERVICE"
! grep -q 'Somma massima delle due esposizioni' "$MAIN"
! grep -q 'La somma dello Split Grade non può superare' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"

test -f Darkroom-v0.2.8.apk
test -f Darkroom-v0.2.8.sha256
grep -Fq "versionCode='19'" apk-badging-v015.txt
grep -Fq "versionName='0.2.8'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -Z1 Darkroom-v0.2.8.apk > apk-listing-v028.txt
! grep -Eiq '(^|/)home_vintage\.(jpg|jpeg|png|webp)$' apk-listing-v028.txt
grep -Eiq '(^|/)res/.*/?ic_launcher.*' apk-listing-v028.txt || true
sha256sum Darkroom-v0.2.8.apk | tee Darkroom-v0.2.8.sha256
