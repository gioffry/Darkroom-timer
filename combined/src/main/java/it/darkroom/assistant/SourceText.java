package it.darkroom.assistant;

import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.text.PDFTextStripper;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Scarica una fonte ufficiale e ne restituisce testo leggibile, HTML o PDF. */
final class SourceText {
    static String fetchText(String url, int maxChars) throws Exception {
        if (url == null || !(url.startsWith("https://") || url.startsWith("http://"))) return "";
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(9000);
        c.setReadTimeout(13000);
        c.setInstanceFollowRedirects(true);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36 DarkroomAssistant/0.2.0");
        c.setRequestProperty("Accept", "text/html,application/xhtml+xml,application/pdf,text/plain,*/*;q=0.6");
        c.setRequestProperty("Accept-Language", "it-IT,it;q=0.9,en;q=0.8");
        c.setRequestProperty("Accept-Encoding", "identity");
        int code = c.getResponseCode();
        if (code < 200 || code >= 400) throw new IllegalStateException("HTTP " + code);
        String type = c.getContentType() == null ? "" : c.getContentType().toLowerCase(Locale.ROOT);
        boolean pdf = type.contains("pdf") || url.toLowerCase(Locale.ROOT).matches(".*\\.pdf(?:[?#].*)?$");
        if (pdf) return readPdf(c.getInputStream(), maxChars);
        return cleanHtml(readText(c.getInputStream(), Math.max(maxChars * 2, 200000)), maxChars);
    }

    private static String readPdf(InputStream in, int maxChars) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        int maxBytes = 12 * 1024 * 1024;
        while ((n = in.read(buf)) > 0 && out.size() < maxBytes) out.write(buf, 0, n);
        in.close();
        try (PDDocument doc = PDDocument.load(new ByteArrayInputStream(out.toByteArray()))) {
            PDFTextStripper stripper = new PDFTextStripper();
            String text = stripper.getText(doc).replaceAll("\\s+", " ").trim();
            return text.length() > maxChars ? text.substring(0, maxChars) : text;
        }
    }

    private static String readText(InputStream in, int maxChars) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        char[] buf = new char[4096];
        int n;
        while ((n = br.read(buf)) > 0 && sb.length() < maxChars) sb.append(buf, 0, n);
        br.close();
        return sb.toString();
    }

    static String cleanHtml(String s, int maxChars) {
        if (s == null) return "";
        String t = s.replaceAll("(?is)<script.*?</script>", " ")
                .replaceAll("(?is)<style.*?</style>", " ")
                .replaceAll("(?is)<noscript.*?</noscript>", " ")
                .replaceAll("(?s)<[^>]+>", " ")
                .replace("&amp;", "&").replace("&quot;", "\"")
                .replace("&#39;", "'").replace("&apos;", "'")
                .replace("&nbsp;", " ").replace("&deg;", "°")
                .replace("&ndash;", "–").replace("&mdash;", "—")
                .replaceAll("\\s+", " ").trim();
        return t.length() > maxChars ? t.substring(0, maxChars) : t;
    }

    private SourceText() {}
}
