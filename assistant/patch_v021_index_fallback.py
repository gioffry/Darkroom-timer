from pathlib import Path

p = Path('assistant/src/main/java/it/darkroom/assistant/SourceBroker.java')
s = p.read_text(encoding='utf-8')

old = '    private static final String MDC_INDEX = "https://www.digitaltruth.com/chart/print.php";'
new = '''    private static final String[] MDC_INDEXES = new String[]{
            "https://www.digitaltruth.com/chart/print.php",
            "https://ftp.digitaltruth.com/chart/print.php",
            "https://www.digitaltruth.com/devchart.php"
    };'''
if old not in s:
    raise SystemExit('MDC_INDEX declaration not found')
s = s.replace(old, new, 1)

old = '            String html = fetch(MDC_INDEX, 1400000);'
new = '''            String html = "";
            for (String indexUrl : MDC_INDEXES) {
                try {
                    html = fetch(indexUrl, 1400000);
                    if (html != null && !html.isEmpty()) break;
                } catch (Exception ignored) {
                    html = "";
                }
            }
            if (html == null || html.isEmpty()) throw new IllegalStateException("MDC index unavailable");'''
if old not in s:
    raise SystemExit('MDC fetch line not found')
s = s.replace(old, new, 1)

# More browser-like headers: Digitaltruth may reject generic bot user agents.
old = '        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36 DarkroomAssistant/0.2.1");'
new = '        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36");\n        c.setRequestProperty("Referer", "https://www.digitaltruth.com/");'
if old not in s:
    raise SystemExit('SourceBroker User-Agent line not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('v0.2.1 index fallback patch applied')
