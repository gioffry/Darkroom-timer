from pathlib import Path

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '    private TextView filmSearchStatus;\n    private EditText isoField;',
    '    private TextView filmSearchStatus;\n    private LinearLayout filmSuggestionsBox;\n    private EditText isoField;'
)

s = s.replace(
    '        Map<String, OnlineCatalogSearch.SearchResult> online = new HashMap<>();\n        final Runnable[] pending = new Runnable[1];',
    '        Map<String, OnlineCatalogSearch.SearchResult> online = new HashMap<>();\n        final String[] chosen = new String[1];\n        LinearLayout resultsBox = new LinearLayout(this);\n        resultsBox.setOrientation(LinearLayout.VERTICAL);\n        resultsBox.setPadding(0, dp(6), 0, 0);\n        wrap.addView(resultsBox);\n        final Runnable[] pending = new Runnable[1];'
)
s = s.replace(
    '                    adapter.clear();\n                    online.clear();\n                    status.setText("Ricerca online dopo 3 lettere.");',
    '                    adapter.clear();\n                    online.clear();\n                    resultsBox.removeAllViews();\n                    chosen[0] = null;\n                    status.setText("Ricerca online dopo 3 lettere.");',
    1
)
s = s.replace(
    '                        replaceSuggestions(adapter, new ArrayList<>(merged));\n                        status.setText(results.isEmpty()\n                                ? "Online: nessun risultato. Mostro i dati locali disponibili."\n                                : "Online: " + results.size() + " risultati trovati.");\n                        search.showDropDown();',
    '''                        List<String> visible = new ArrayList<>(merged);\n                        replaceSuggestions(adapter, visible);\n                        resultsBox.removeAllViews();\n                        for (String item : visible) {\n                            TextView option = row(item + "    ›");\n                            option.setTextSize(15);\n                            option.setOnClickListener(v -> {\n                                chosen[0] = item;\n                                search.setText(item, false);\n                                search.dismissDropDown();\n                                resultsBox.removeAllViews();\n                                status.setText("Selezionato: " + item);\n                            });\n                            resultsBox.addView(option);\n                            resultsBox.addView(space(5));\n                        }\n                        status.setText(results.isEmpty()\n                                ? "Online: nessun risultato. Mostro i dati locali disponibili."\n                                : "Online: " + results.size() + " risultati trovati. Tocca un risultato.");\n                        search.showDropDown();''',
    1
)
s = s.replace(
    '        final String[] chosen = new String[1];\n        search.setOnItemClickListener((parent, view, position, id) ->\n                chosen[0] = String.valueOf(parent.getItemAtPosition(position)));',
    '        search.setOnItemClickListener((parent, view, position, id) -> {\n            chosen[0] = String.valueOf(parent.getItemAtPosition(position));\n            resultsBox.removeAllViews();\n            status.setText("Selezionato: " + chosen[0]);\n        });',
    1
)

s = s.replace(
    '        filmSearchStatus.setPadding(dp(4), 0, dp(4), dp(10));\n        page.addView(filmSearchStatus);\n\n        isoField = edit',
    '        filmSearchStatus.setPadding(dp(4), 0, dp(4), dp(10));\n        page.addView(filmSearchStatus);\n        filmSuggestionsBox = new LinearLayout(this);\n        filmSuggestionsBox.setOrientation(LinearLayout.VERTICAL);\n        page.addView(filmSuggestionsBox);\n\n        isoField = edit'
)
s = s.replace(
    '                    adapter.clear(); online.clear();\n                    filmSearchStatus.setText("Ricerca online dopo 3 lettere.");',
    '                    adapter.clear(); online.clear();\n                    if (filmSuggestionsBox != null) filmSuggestionsBox.removeAllViews();\n                    filmSearchStatus.setText("Ricerca online dopo 3 lettere.");',
    1
)
s = s.replace(
    '                        replaceSuggestions(adapter, new ArrayList<>(merged));\n                        filmSearchStatus.setText(results.isEmpty()\n                                ? "Online: nessun risultato; mostro i dati locali."\n                                : "Online: " + results.size() + " risultati trovati.");\n                        field.showDropDown();',
    '''                        List<String> visible = new ArrayList<>(merged);\n                        replaceSuggestions(adapter, visible);\n                        if (filmSuggestionsBox != null) {\n                            filmSuggestionsBox.removeAllViews();\n                            for (String item : visible) {\n                                TextView option = row(item + "    ›");\n                                option.setTextSize(15);\n                                option.setOnClickListener(v -> {\n                                    filmSuggestionsBox.removeAllViews();\n                                    FilmStock local = findFilm(item);\n                                    if (local != null) { selectFilm(local); return; }\n                                    OnlineCatalogSearch.SearchResult rr = online.get(item.toLowerCase(Locale.ROOT));\n                                    if (rr == null) return;\n                                    filmSearchStatus.setText("Recupero ISO e formato…");\n                                    field.setText(item, false);\n                                    new Thread(() -> {\n                                        OnlineCatalogSearch.FilmData fd = OnlineCatalogSearch.enrichFilm(rr);\n                                        runOnUiThread(() -> finishOnlineFilmSelection(fd));\n                                    }).start();\n                                });\n                                filmSuggestionsBox.addView(option);\n                                filmSuggestionsBox.addView(space(5));\n                            }\n                        }\n                        filmSearchStatus.setText(results.isEmpty()\n                                ? "Online: nessun risultato; mostro i dati locali."\n                                : "Online: " + results.size() + " risultati trovati. Tocca un risultato.");\n                        field.showDropDown();''',
    1
)
s = s.replace(
    '            String display = String.valueOf(parent.getItemAtPosition(position));',
    '            if (filmSuggestionsBox != null) filmSuggestionsBox.removeAllViews();\n            String display = String.valueOf(parent.getItemAtPosition(position));',
    1
)

required = [
    'private LinearLayout filmSuggestionsBox;',
    'Tocca un risultato.',
    'resultsBox.addView(option)',
    'filmSuggestionsBox.addView(option)'
]
for marker in required:
    if marker not in s:
        raise SystemExit(f'patch marker missing: {marker}')

p.write_text(s, encoding='utf-8')
print('v0.1.8 visible-results patch applied')
