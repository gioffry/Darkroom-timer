#!/usr/bin/env python3
"""Prefer Digitaltruth's current public dataset while building the offline DB."""

from pathlib import Path


BUILDER = Path("assistant/build_mdc_sqlite_asset_v032.py")
source = BUILDER.read_text(encoding="utf-8")

old = """    urls=[f'https://ftp.digitaltruth.com/chart/search_text.php?Developer={enc}',
          f'https://www.digitaltruth.com/chart/search_text.php?Developer={enc}']"""
new = """    # devchart.php is the current public dataset. Both search_text mirrors
    # can lag behind and omit newer format rows, so they are fallbacks only.
    urls=[f'https://www.digitaltruth.com/devchart.php?Developer={enc}&Film=&mdc=Search',
          f'https://www.digitaltruth.com/chart/search_text.php?Developer={enc}',
          f'https://ftp.digitaltruth.com/chart/search_text.php?Developer={enc}']"""
if source.count(old) != 1:
    raise SystemExit("v0.5.6 MDC source-order marker missing")
source = source.replace(old, new, 1)

# The main chart displays a generic [notes] label, but its link contains the
# stable devrow identifier. Preserve that identifier and make the row source
# open the exact MDC note instead of the whole developer listing.
old_notes = """            'timesheet':clean_time(cells[6]),'temp':parse_temp(cells[7]),
            'notes':cells[8].strip() if len(cells)>8 else '', 'source_url':url
        })"""
new_notes = """            'timesheet':clean_time(cells[6]),'temp':parse_temp(cells[7]),
            'notes':((cells[8].strip() + ' ') if len(cells)>8 else '') +
                    (('[devrow:' + query_value(raw_cells[8],'devrow') + ']')
                     if len(raw_cells)>8 and query_value(raw_cells[8],'devrow') else ''),
            'source_url':(('https://www.digitaltruth.com/devchart.php?devrow=' +
                           query_value(raw_cells[8],'devrow'))
                          if len(raw_cells)>8 and query_value(raw_cells[8],'devrow') else url)
        })"""
if source.count(old_notes) != 1:
    raise SystemExit("v0.5.6 MDC devrow preservation marker missing")
source = source.replace(old_notes, new_notes, 1)
BUILDER.write_text(source, encoding="utf-8")

# Keep the dormant synchronizer consistent. Runtime synchronization remains
# disabled; all calculations use the database bundled into the APK.
store = Path("assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
java = store.read_text(encoding="utf-8")
old_java = """        String[] urls = new String[]{
                \"https://ftp.digitaltruth.com/chart/search_text.php?Developer=\" + enc,
                \"https://www.digitaltruth.com/chart/search_text.php?Developer=\" + enc
        };"""
new_java = """        String[] urls = new String[]{
                \"https://www.digitaltruth.com/chart/search_text.php?Developer=\" + enc,
                \"https://ftp.digitaltruth.com/chart/search_text.php?Developer=\" + enc
        };"""
if java.count(old_java) != 1:
    raise SystemExit("v0.5.6 runtime source-order marker missing")
store.write_text(java.replace(old_java, new_java, 1), encoding="utf-8")

print("Darkroom v0.5.6 MDC build source: current www, FTP fallback")
