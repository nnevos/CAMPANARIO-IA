package org.campanario.mobile;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.location.Location;
import android.location.LocationManager;
import android.os.*;
import android.view.View;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.*;

/** Native Maps V2 screen. Chat remains in MainActivity, GPS continues in FGS. */
public final class NativeNavigationActivity extends Activity {
    private final ExecutorService requests=Executors.newSingleThreadExecutor();
    private TextView status,next,metrics;
    private EditText search;
    private Spinner mode;
    private RouteGeometryView diagram;
    private JSONObject selected,lastState;
    private boolean autoStart=false;
    private Location fix;
    private CompanionMapsClient client;
    private static final int PERMISSION=705;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final Runnable poll=new Runnable(){@Override public void run(){
        call("maps/v2/status",null,result->{display(result);},false);
        main.postDelayed(this,6500);
    }};
    private final BroadcastReceiver updates=new BroadcastReceiver(){@Override public void onReceive(Context context,Intent intent){
        String message=intent.getStringExtra("message");if(message!=null)status.setText(message);
        String body=intent.getStringExtra("state");if(body!=null)try{display(new JSONObject(body));}catch(Exception ignored){}
    }};
    private void text(String value){status.setText(value);}
    @Override public void onCreate(Bundle saved){super.onCreate(saved);
        getWindow().setStatusBarColor(0xff101317);getWindow().setNavigationBarColor(0xff101317);
        try{client=new CompanionMapsClient(this);}catch(Exception ex){client=null;}
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},706);
        }
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(20,20,20,12);layout.setBackgroundColor(0xff101317);
        ScrollView scroll=new ScrollView(this);scroll.addView(layout);setContentView(scroll);
        Button back=button("Voltar ao chat (manter rota)");back.setOnClickListener(v->finish());layout.addView(back);
        TextView heading=label("CAMPANARIO FIELD / MAPS V2",24);heading.setTextColor(0xff31d9de);layout.addView(heading);
        status=label(client==null?"Pareie o aparelho com PC por HTTPS no chat":"Navegacao ainda nao iniciada",16);layout.addView(status);
        search=new EditText(this);search.setTextColor(Color.WHITE);search.setHintTextColor(0xffaab3bc);search.setHint("Mercado proximo, endereco...");search.setSingleLine(true);layout.addView(search);
        mode=new Spinner(this);ArrayAdapter<String> profiles=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Carro","Caminhada"});mode.setAdapter(profiles);layout.addView(mode);
        String requested=getIntent()==null?null:getIntent().getStringExtra("query");
        if(requested!=null && requested.length()>=3 && requested.length()<=140){
            autoStart=true;search.setText(requested);main.postDelayed(this::findDestination,400);
        }
        Button find=button("1. Buscar destino");layout.addView(find);find.setOnClickListener(v->findDestination());
        Button calculate=button("2. Calcular rota");layout.addView(calculate);calculate.setOnClickListener(v->calculate());
        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
        Button start=button("Iniciar GPS");Button pause=button("Pausar");Button end=button("Encerrar");
        actions.addView(start,new LinearLayout.LayoutParams(0,-2,1));actions.addView(pause,new LinearLayout.LayoutParams(0,-2,1));actions.addView(end,new LinearLayout.LayoutParams(0,-2,1));layout.addView(actions);
        start.setOnClickListener(v->begin());pause.setOnClickListener(v->call("maps/v2/command/pause",new JSONObject(),result->{display(result);stopService(new Intent(this,NavigationForegroundService.class));},true));
        end.setOnClickListener(v->{stopService(new Intent(this,NavigationForegroundService.class));call("maps/v2/command/stop",new JSONObject(),this::display,true);});
        next=label("Proxima manobra: indisponivel",20);next.setTextColor(0xffffd075);layout.addView(next);
        metrics=label("Distancia e duracao dependem do OSRM no PC",16);layout.addView(metrics);
        diagram=new RouteGeometryView(this);layout.addView(diagram,new LinearLayout.LayoutParams(-1,420));
        layout.addView(label("Traçado de rota real, SEM mapa de ruas. OSRM/Nominatim/Overpass devem estar instalados no PC; GPS e TTS usam Android. Nao utilize como unica fonte de orientacao viaria.",14));
    }
    private TextView label(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(4,14,4,14);return t;}
    private Button button(String value){Button b=new Button(this);b.setText(value);b.setAllCaps(false);return b;}
    interface Callback{void success(JSONObject result);}
    private void call(String endpoint,JSONObject body,Callback callback,boolean reportError){
        if(client==null){text("Pareamento HTTPS nao configurado");return;}
        requests.execute(()->{try{JSONObject data=client.call(endpoint,body);
            runOnUiThread(()->{if(!isFinishing()&&!isDestroyed())callback.success(data);});
        }catch(Exception error){if(reportError)runOnUiThread(()->text("Servico indisponivel: "+error.getMessage()));}});
    }
    private void gps(java.util.function.Consumer<Location> consumer){
        if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED &&
           checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION,Manifest.permission.ACCESS_FINE_LOCATION},PERMISSION);
            text("Autorize o GPS e tente novamente");return;
        }
        LocationManager lm=(LocationManager)getSystemService(LOCATION_SERVICE);
        if(lm==null){text("Sensor GPS indisponivel");return;}
        String provider=lm.isProviderEnabled(LocationManager.GPS_PROVIDER)?LocationManager.GPS_PROVIDER:
                lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER)?LocationManager.NETWORK_PROVIDER:null;
        if(provider==null){text("Ative a localizacao do Android");return;}
        text("Obtendo GPS recente...");
        try{
            if(Build.VERSION.SDK_INT>=30){
                lm.getCurrentLocation(provider,null,getMainExecutor(),p->acceptFix(p,consumer));
            }else{
                Location cached=lm.getLastKnownLocation(provider);
                if(cached!=null&&Math.abs(System.currentTimeMillis()-cached.getTime())<20000){acceptFix(cached,consumer);return;}
                final LocationListener[] listener=new LocationListener[1];
                Runnable timeout=()->{if(listener[0]!=null){lm.removeUpdates(listener[0]);listener[0]=null;text("GPS sem leitura recente");}};
                listener[0]=new LocationListener(){@Override public void onLocationChanged(Location value){if(listener[0]!=null){lm.removeUpdates(listener[0]);listener[0]=null;main.removeCallbacks(timeout);acceptFix(value,consumer);}}};
                lm.requestLocationUpdates(provider,0,0f,listener[0],Looper.getMainLooper());main.postDelayed(timeout,12000);
            }
        }catch(SecurityException e){text("GPS sem permissao");}
    }
    private void acceptFix(Location p,java.util.function.Consumer<Location> consumer){
        if(p==null||!p.hasAccuracy()||p.getAccuracy()>100||Math.abs(System.currentTimeMillis()-p.getTime())>20000){
            text("GPS sem posicao recente ou com precisao insuficiente");return;
        }
        fix=p;consumer.accept(p);
    }
    private void findDestination(){String q=search.getText().toString().trim();if(q.length()<3||q.length()>140){text("Informe destino com 3 a 140 caracteres");return;}
        gps(loc->{JSONObject body=new JSONObject();try{body.put("query",q);body.put("lat",loc.getLatitude());body.put("lon",loc.getLongitude());}catch(Exception ignored){}
            text("Consultando estabelecimentos e enderecos no PC...");
            call("maps/v2/resolve",body,result->{JSONArray places=result.optJSONArray("candidates");
                if(places==null||places.length()==0){text("Nenhum destino encontrado no indice local");return;}
                JSONObject unique=result.optJSONObject("selected");
                if(unique!=null&&!result.optBoolean("ambiguous")){selected=unique;text("Destino: "+unique.optString("name"));if(autoStart)calculate();return;}
                String[] names=new String[places.length()];for(int i=0;i<names.length;i++){
                    JSONObject p=places.optJSONObject(i);names[i]=p==null?"Desconhecido":p.optString("name","")+" / "+p.optString("route_distance_m","distancia indisponivel")+" m";
                }
                new AlertDialog.Builder(this).setTitle("Escolha o destino correto").setItems(names,(d,index)->{
                    selected=places.optJSONObject(index);text("Selecionado: "+(selected==null?"":selected.optString("name")));if(autoStart&&selected!=null)calculate();
                }).setNegativeButton("Cancelar",null).show();
            },true);
        });
    }
    private void calculate(){if(selected==null){text("Busque e selecione um destino primeiro");return;}
        gps(loc->{JSONObject data=new JSONObject();try{
            data.put("start_lat",loc.getLatitude());data.put("start_lon",loc.getLongitude());
            data.put("end_lat",selected.getDouble("lat"));data.put("end_lon",selected.getDouble("lon"));
            data.put("mode",mode.getSelectedItemPosition()==0?"driving":"walking");data.put("name",selected.optString("name"));
        }catch(Exception ex){text("Destino invalido");return;}
            text("Calculando rota no OSRM local do PC...");call("maps/v2/route",data,result->{display(result);if(autoStart&&"READY".equals(result.optString("state")))begin();},true);
        });
    }
    private void begin(){if(lastState==null||!("READY".equals(lastState.optString("state"))||"PAUSED".equals(lastState.optString("state")))){
            text("Calcule uma rota primeiro");return;}
        gps(loc->{autoStart=false;String command="PAUSED".equals(lastState.optString("state"))?"resume":"start";
            call("maps/v2/command/"+command,new JSONObject(),result->{display(result);
                if("NAVIGATING".equals(result.optString("state"))){
                    Intent intent=new Intent(this,NavigationForegroundService.class).setAction(NavigationForegroundService.ACTION_START);
                    try{startForegroundService(intent);}catch(Exception ex){text("Servico em primeiro plano nao iniciou: "+ex.getMessage());}
                }
            },true);
        });
    }
    private void display(JSONObject value){
        if(value.optJSONObject("route")==null&&lastState!=null&&lastState.optJSONObject("route")!=null){
            try{value.put("route",lastState.getJSONObject("route"));}catch(Exception ignored){}
        }
        lastState=value;String state=value.optString("state","IDLE");text("Navegacao: "+state+(value.optString("reason").isEmpty()?"":" / "+value.optString("reason")));
        JSONObject route=value.optJSONObject("route");diagram.show(value);
        if(route!=null)metrics.setText(String.format(java.util.Locale.forLanguageTag("pt-BR"),"Rota: %.1f km, aproximadamente %.0f min (sem transito ao vivo)",route.optDouble("distance")/1000,route.optDouble("duration")/60));
        JSONArray instructions=value.optJSONArray("instructions");if(instructions!=null&&instructions.length()>0){JSONObject i=instructions.optJSONObject(instructions.length()-1);
            if(i!=null){JSONObject m=i.optJSONObject("maneuver");next.setText("Proxima manobra: "+(m==null?"":m.optString("type")+" / "+m.optString("modifier"))+" a "+i.optInt("meters")+" m");}
        }
    }
    @Override protected void onResume(){super.onResume();
        IntentFilter filter=new IntentFilter(NavigationForegroundService.EVENT);
        if(Build.VERSION.SDK_INT>=33)registerReceiver(updates,filter,Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(updates,filter);
        main.post(poll);
    }
    @Override protected void onPause(){main.removeCallbacks(poll);unregisterReceiver(updates);super.onPause();}
    @Override protected void onDestroy(){requests.shutdownNow();super.onDestroy();}
}
