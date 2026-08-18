package app.diariopercorsi.stabile;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                    "(function(){" +
                    "if(document.getElementById('diario-v13'))return;" +
                    "var s=document.createElement('script');s.id='diario-v13';s.src='file:///android_asset/ui-v13.js';" +
                    "s.onload=function(){" +
                    " var n=document.createElement('script');n.id='diario-v14';n.src='file:///android_asset/ui-v14.js';" +
                    " n.onload=function(){" +
                    "  var p=document.createElement('script');p.id='diario-v15';p.src='file:///android_asset/ui-v15.js';" +
                    "  p.onload=function(){if(document.getElementById('diario-v16'))return;var q=document.createElement('script');q.id='diario-v16';q.src='file:///android_asset/ui-v16.js';document.body.appendChild(q);};" +
                    "  document.body.appendChild(p);" +
                    " };" +
                    " document.body.appendChild(n);" +
                    "};" +
                    "document.body.appendChild(s);" +
                    "})();",
                    null
                );
            }
        });
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
