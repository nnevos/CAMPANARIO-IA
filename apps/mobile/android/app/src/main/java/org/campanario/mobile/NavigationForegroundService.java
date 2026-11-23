package org.campanario.mobile;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.location.*;
import android.os.*;
import android.speech.tts.TextToSpeech;
import java.util.Locale;
import java.util.concurrent.*;
import org.json.JSONObject;
import org.json.JSONArray;

/** Foreground GPS and voice service, independent of WebView and of visible map screen. */
public final class NavigationForegroundService extends Service {
    static final String ACTION_START="org.campanario.mobile.navigation.START";
    static final String ACTION_STOP="org.campanario.mobile.navigation.STOP";
    static final String EVENT="org.campanario.mobile.navigation.STATE";
    private final ExecutorService requests=Executors.newSingleThreadExecutor();
    private LocationManager locationManager;
    private LocationListener listener;
    private TextToSpeech speech;
    private boolean speechReady=false;
    private volatile boolean running=false;
    private volatile long lastUpload=0;
    private int lastVoiceSequence=-1;
    private String lastSession="";
    private static final String CHANNEL="campanario_navigation_v1";
    private CompanionMapsClient client;
    @Override public void onCreate(){super.onCreate();
        NotificationChannel channel=new NotificationChannel(CHANNEL,"Navegacao Campanario",NotificationManager.IMPORTANCE_LOW);
        ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        speech=new TextToSpeech(this,status->{if(status==TextToSpeech.SUCCESS && speech!=null){int r=speech.setLanguage(new Locale("pt","BR"));speechReady=r!=TextToSpeech.LANG_MISSING_DATA&&r!=TextToSpeech.LANG_NOT_SUPPORTED;}});
    }
    private Notification notification(String status){
        Intent open=new Intent(this,NativeNavigationActivity.class);
        PendingIntent content=PendingIntent.getActivity(this,1,open,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Intent stop=new Intent(this,NavigationForegroundService.class).setAction(ACTION_STOP);
        PendingIntent end=PendingIntent.getService(this,2,stop,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_dialog_map)
                .setContentTitle("Campanario Maps").setContentText(status).setOngoing(true)
                .setContentIntent(content).addAction(android.R.drawable.ic_menu_close_clear_cancel,"Encerrar",end).build();
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent==null)return START_NOT_STICKY;
        if(ACTION_STOP.equals(intent.getAction())){stopSession();return START_NOT_STICKY;}
        if(!ACTION_START.equals(intent.getAction()))return START_NOT_STICKY;
        if(running)return START_NOT_STICKY;
        if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED &&
           checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED){publish("Permissao de GPS ausente",null);stopSelf();return START_NOT_STICKY;}
        try {
            client=new CompanionMapsClient(this);
            startForeground(1701,notification("Acompanhando rota pelo GPS"));
            locationManager=(LocationManager)getSystemService(LOCATION_SERVICE);
            if(locationManager==null)throw new IllegalStateException("GPS indisponivel");
            running=true;
            listener=new LocationListener(){@Override public void onLocationChanged(Location fix){uploadFix(fix);}
                @Override public void onProviderDisabled(String provider){publish("GPS desativado",null);}};
            if(locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER))
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER,2000,3f,listener,Looper.getMainLooper());
            if(locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER))
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER,5000,10f,listener,Looper.getMainLooper());
            publish("Navegacao em primeiro plano ativada",null);
        }catch(Exception error){publish("Nao foi possivel iniciar: "+error.getMessage(),null);stopSession();}
        return START_NOT_STICKY;
    }
    private void uploadFix(Location fix){
        if(!running || fix==null || !fix.hasAccuracy() || fix.getAccuracy()>100 ||
           Math.abs(System.currentTimeMillis()-fix.getTime())>15000)return;
        long now=SystemClock.elapsedRealtime();
        if(now-lastUpload<3000)return;
        lastUpload=now;
        JSONObject body=new JSONObject();
        try{body.put("lat",fix.getLatitude());body.put("lon",fix.getLongitude());body.put("accuracy",fix.getAccuracy());body.put("timestamp",fix.getTime()/1000.0);}catch(Exception ignored){return;}
        requests.execute(()->{if(!running)return;
            try{JSONObject state=client.call("maps/v2/fix",body);
                if("RECALCULATING".equals(state.optString("state"))){publish("Recalculando rota...",state);state=client.call("maps/v2/recalculate",new JSONObject());}
                publish(null,state);String session=state.optString("id","");
                if(!session.equals(lastSession)){lastSession=session;lastVoiceSequence=-1;}
                int seq=state.optInt("voice_event_seq",-1);
                if(seq>=0&&seq!=lastVoiceSequence && "NAVIGATING".equals(state.optString("state"))){
                    lastVoiceSequence=seq;
                    JSONArray instructions=state.optJSONArray("instructions");
                    if(instructions!=null&&instructions.length()>0){
                        JSONObject instruction=instructions.optJSONObject(instructions.length()-1);
                        if(instruction!=null)announce(instruction);
                    }
                }
                if("IDLE".equals(state.optString("state"))||"STOPPED".equals(state.optString("state"))){stopSession();return;}
                if("ARRIVED".equals(state.optString("state"))){publish("Destino alcancado",state);finishLocal(false);}
            }catch(Exception e){publish("Servidor indisponivel; rota nao atualizada: "+e.getMessage(),null);}
        });
    }
    private void announce(JSONObject instruction){
        JSONObject maneuver=instruction.optJSONObject("maneuver");if(maneuver==null)return;
        String type=maneuver.optString("type","");String modifier=maneuver.optString("modifier","");
        String command;
        if("arrive".equals(type))command="Voce chegou ao destino";
        else if("turn".equals(type)||"fork".equals(type)||"end of road".equals(type)){
            String dir=modifier.contains("left")?"esquerda":modifier.contains("right")?"direita":"frente";
            command="Em "+Math.max(0,instruction.optInt("meters",0))+" metros, "+("frente".equals(dir)?"siga em frente":"vire a "+dir);
        }else return;
        if(speechReady&&speech!=null){String message=command;
            new Handler(Looper.getMainLooper()).post(()->{if(speech!=null&&running)speech.speak(message,TextToSpeech.QUEUE_FLUSH,null,"campanario-nav-instruction");});}
    }
    private void publish(String message,JSONObject state){
        Intent update=new Intent(EVENT).setPackage(getPackageName());
        if(message!=null)update.putExtra("message",message);
        if(state!=null){
            // Large route geometries do not fit Android's Binder broadcast limit.
            JSONObject brief=new JSONObject();
            try{for(String key:new String[]{"id","state","reason","step_index","voice_event_seq","instructions"}){
                if(state.has(key))brief.put(key,state.get(key));
            }}catch(Exception ignored){}
            update.putExtra("state",brief.toString());
        }
        sendBroadcast(update);
    }
    private void stopSession(){finishLocal(true);}
    private void finishLocal(boolean stopServer){
        running=false;
        if(locationManager!=null&&listener!=null){try{locationManager.removeUpdates(listener);}catch(SecurityException ignored){}}
        if(speech!=null)speech.stop();
        if(stopServer&&client!=null)requests.execute(()->{try{client.call("maps/v2/command/stop",new JSONObject());}catch(Exception ignored){}});
        stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();
        publish("Navegacao encerrada",null);
    }
    @Override public void onDestroy(){running=false;
        if(locationManager!=null&&listener!=null){try{locationManager.removeUpdates(listener);}catch(SecurityException ignored){}}
        requests.shutdown();if(speech!=null){speech.stop();speech.shutdown();speech=null;}super.onDestroy();}
    @Override public IBinder onBind(Intent intent){return null;}
}
