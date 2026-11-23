"""Static contract tests; NOT substitutes for an Android build or device validation."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'apps/mobile/android/app/src/main/java/org/campanario/mobile'
ANDROID=ROOT/'apps/mobile/android/app'

def source(name):return (JAVA/name).read_text(encoding='utf-8')

def test_native_activity_declared_without_replacing_existing_chat():
    manifest=ET.parse(ANDROID/'src/main/AndroidManifest.xml').getroot()
    ns='{http://schemas.android.com/apk/res/android}'
    activities=[a.attrib.get(ns+'name') for a in manifest.iter('activity')]
    assert '.MainActivity' in activities
    assert '.NativeNavigationActivity' in activities
    assert 'new Intent(MainActivity.this, NativeNavigationActivity.class)' in source('MainActivity.java')

def test_foreground_navigation_location_type_and_notification():
    root=ET.parse(ANDROID/'src/main/AndroidManifest.xml').getroot()
    ns='{http://schemas.android.com/apk/res/android}'
    permissions={p.get(ns+'name') for p in root.iter('uses-permission')}
    assert {'android.permission.FOREGROUND_SERVICE_LOCATION','android.permission.ACCESS_FINE_LOCATION','android.permission.POST_NOTIFICATIONS'}<=permissions
    service=[s for s in root.iter('service') if s.get(ns+'name')=='.NavigationForegroundService']
    assert len(service)==1 and service[0].get(ns+'foregroundServiceType')=='location'
    code=source('NavigationForegroundService.java')
    assert all(x in code for x in ('startForeground(', 'requestLocationUpdates(', 'lastUpload', 'stopForeground(', 'TextToSpeech', 'maps/v2/recalculate'))
    assert 'setPackage(getPackageName())' in code
    assert 'JSONObject brief=' in code  # no route geometry in Binder event

def test_app_has_native_navigator_entry_without_remote_html():
    html=(ROOT/'apps/mobile/www/index.html').read_text()
    app=(ROOT/'apps/mobile/www/app.mjs').read_text()
    assert 'id="openNativeMaps"' in html
    assert 'id="emergencyDial"' in html
    assert 'openEmergencyDialer()' in app
    assert "$('openNativeMaps').onclick" in app
    assert 'openNativeNavigation(query)' in app
    java=source('MainActivity.java')
    assert 'appassets.androidplatform.net/assets/www/index.html' in java
    assert 'setAllowUniversalAccessFromFileURLs(false)' in java

def test_allowlisted_paired_transport_only():
    java=source('CompanionMapsClient.java')
    assert '"https".equals(parsed.getProtocol())' in java
    assert 'setInstanceFollowRedirects(false)' in java
    assert 'Authorization' in java and 'Bearer ' in java
    assert 'new SecureStore(context).read()' in java
    assert 'matches("maps/v2/' in java
    assert 'http://127.0.0.1' not in java
    assert 'readNBytes' not in java  # Android API 26 compatibility

def test_api_endpoints_consumed_exist():
    api=(ROOT/'src/campanario/companion/api.py').read_text()
    for endpoint in ('/maps/v2/resolve','/maps/v2/route','/maps/v2/fix','/maps/v2/recalculate','/maps/v2/status','/maps/v2/command/{action}'):
        assert endpoint in api

def test_no_embedded_keys_and_no_false_apk_claim():
    for name in ('CompanionMapsClient.java','NavigationForegroundService.java','NativeNavigationActivity.java','RouteGeometryView.java'):
        code=source(name)
        assert not re.search(r'(?:sk-[A-Za-z0-9]{20,}|-----BEGIN PRIVATE KEY-----)',code)
    readme=(ROOT/'docs/operations/ANDROID_FIELD_V1_BUILD_E_NAV.md').read_text()
    assert 'não um APK' in readme
    assert 'não implementa ainda' in readme
