package org.campanario.mobile;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.content.Context;
import android.os.Looper;
import android.os.SystemClock;
import android.webkit.JavascriptInterface;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.graphics.Insets;
import android.view.WindowInsets;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.webkit.WebViewAssetLoader;
import java.io.ByteArrayInputStream;
import org.json.JSONObject;

/** Native Android host. Only bundled UI receives the bridge. No downloaded HTML/JS is loaded. */
public final class MainActivity extends Activity {
    private static final String ORIGIN = "appassets.androidplatform.net";
    private WebView web;
    private SecureStore store;
    private static final int GPS_PERMISSION_REQUEST = 602;
    private boolean gpsPending = false;
    private String pendingGpx = null;
    private static final int GPS_EXPORT_REQUEST = 603;
    private long lastGpsRequest = 0L;
    private boolean allowed(Uri uri) { return "https".equals(uri.getScheme()) && ORIGIN.equals(uri.getHost()) && uri.getPath() != null && uri.getPath().startsWith("/assets/www/"); }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved); store = new SecureStore(this);
        web = new WebView(this); web.setBackgroundColor(Color.rgb(14,15,18));
        web.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true); settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false); settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false); settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false); settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setSafeBrowsingEnabled(true);
        WebView.setWebContentsDebuggingEnabled(false);
        final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this)).build();
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) { return !allowed(req.getUrl()); }
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
                WebResourceResponse response = loader.shouldInterceptRequest(req.getUrl());
                if (response == null && ORIGIN.equals(req.getUrl().getHost()))
                    return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", null, new ByteArrayInputStream(new byte[0]));
                return response;
            }
            // Default onReceivedSslError cancels. Never call handler.proceed().
        });
        web.addJavascriptInterface(new LocalBridge(), "CampanarioNative");
        web.setOnApplyWindowInsetsListener((view, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets safe = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                view.setPadding(safe.left, safe.top, safe.right, safe.bottom);
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        setContentView(web);
        web.requestApplyInsets();
        web.loadUrl("https://appassets.androidplatform.net/assets/www/index.html");
    }
    private void gpsResult(String status, Location location) {
        try {
            JSONObject result = new JSONObject(); result.put("status", status);
            if (location != null) {
                result.put("lat", location.getLatitude()); result.put("lon", location.getLongitude());
                result.put("accuracy", location.hasAccuracy() ? location.getAccuracy() : JSONObject.NULL);
                result.put("timestamp", location.getTime());
                result.put("provider", location.getProvider());
                result.put("mock", Build.VERSION.SDK_INT >= 31 ? location.isMock() : location.isFromMockProvider());
            }
            final String encoded = JSONObject.quote(result.toString());
            runOnUiThread(() -> web.evaluateJavascript("window.CampanarioGpsResult && window.CampanarioGpsResult(" + encoded + ")", null));
        } catch (Exception ignored) {}
    }
    private void requestGps() {
        if (gpsPending) return;
        if (SystemClock.elapsedRealtime() - lastGpsRequest < 1200) { gpsResult("aguarde", null); return; }
        lastGpsRequest = SystemClock.elapsedRealtime();
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED &&
            checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, GPS_PERMISSION_REQUEST);
            return;
        }
        LocationManager manager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        if (manager == null) { gpsResult("indisponivel", null); return; }
        String provider = manager.isProviderEnabled(LocationManager.GPS_PROVIDER) ? LocationManager.GPS_PROVIDER :
            (manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) ? LocationManager.NETWORK_PROVIDER : null);
        if (provider == null) { gpsResult("gps_desligado", null); return; }
        gpsPending = true;
        try {
            if (Build.VERSION.SDK_INT >= 30) {
                manager.getCurrentLocation(provider, null, getMainExecutor(), location -> {
                    gpsPending = false;
                    gpsResult(location == null ? "sem_fix" : "ok", location);
                });
            } else {
                Location last = manager.getLastKnownLocation(provider);
                gpsPending = false;
                if (last != null && System.currentTimeMillis() - last.getTime() <= 30000) gpsResult("ok", last);
                else gpsResult("sem_fix", null);
            }
        } catch (SecurityException ex) { gpsPending = false; gpsResult("sem_permissao", null); }
        catch (Exception ex) { gpsPending = false; gpsResult("erro", null); }
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(requestCode, permissions, grants);
        if (requestCode != GPS_PERMISSION_REQUEST) return;
        boolean granted = false;
        for (int grant : grants) if (grant == PackageManager.PERMISSION_GRANTED) granted = true;
        if (granted) requestGps(); else gpsResult("sem_permissao", null);
    }
    public final class LocalBridge {
        @JavascriptInterface public void requestGpsOnce() { runOnUiThread(() -> requestGps()); }
        @JavascriptInterface public void exportGpx(String xml) {
            if (xml == null || xml.length() > 500000 || !xml.startsWith("<?xml") || !xml.contains("<gpx")) return;
            runOnUiThread(() -> {
                pendingGpx = xml;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/gpx+xml");
                intent.putExtra(Intent.EXTRA_TITLE, "campanario-trilha.gpx");
                try { startActivityForResult(intent, GPS_EXPORT_REQUEST); }
                catch (Exception ignored) { pendingGpx = null; }
            });
        }

        @JavascriptInterface public String loadState() { try { return store.read(); } catch (Exception ex) { return "!ERROR"; } }
        @JavascriptInterface public boolean saveState(String value) {
            try { JSONObject json = new JSONObject(value); if (json.getInt("schema") != 1) return false; store.write(value); return true; }
            catch (Exception ex) { return false; }
        }
        @JavascriptInterface public boolean clearState() { try { store.clear(); return true; } catch (Exception ex) { return false; } }
        @JavascriptInterface public void openRelease(String value) {
            Uri uri = Uri.parse(value);
            if (!"https".equals(uri.getScheme()) || !"github.com".equals(uri.getHost()) || uri.getUserInfo() != null || uri.getPath() == null || !uri.getPath().contains("/releases/")) return;
            runOnUiThread(() -> { try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (Exception ignored) {} });
        }
    }
    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != GPS_EXPORT_REQUEST) return;
        String xml = pendingGpx; pendingGpx = null;
        if (resultCode != RESULT_OK || data == null || data.getData() == null || xml == null) return;
        try (java.io.OutputStream out = getContentResolver().openOutputStream(data.getData())) {
            if (out != null) out.write(xml.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        } catch (Exception ignored) {}
    }
    @Override public void onBackPressed() {
        web.evaluateJavascript("(function(){var d=document.querySelector('dialog[open]');if(d){d.close();return true;}return false;})()", result -> { if (!"true".equals(result)) MainActivity.super.onBackPressed(); });
    }
    @Override protected void onDestroy() { web.removeJavascriptInterface("CampanarioNative"); web.destroy(); super.onDestroy(); }
}
