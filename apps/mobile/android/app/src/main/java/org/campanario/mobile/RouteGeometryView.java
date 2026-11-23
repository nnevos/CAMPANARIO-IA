package org.campanario.mobile;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.json.JSONArray;
import org.json.JSONObject;

/** Native route geometry, never a simulated street basemap. */
final class RouteGeometryView extends View {
    private JSONArray points;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    RouteGeometryView(Context context){super(context);setMinimumHeight(350);}
    void show(JSONObject status){
        JSONObject route=status==null?null:status.optJSONObject("route");
        points=route==null?null:route.optJSONArray("points");invalidate();
    }
    @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);
        canvas.drawColor(0xff101317);paint.setColor(0xffb2b9bf);paint.setTextSize(30);
        if(points==null||points.length()<2){canvas.drawText("Sem geometria de rota",24,getHeight()/2f,paint);return;}
        int limit=Math.min(points.length(),50000);double minX=180,maxX=-180,minY=90,maxY=-90;
        for(int i=0;i<limit;i++){JSONObject p=points.optJSONObject(i);if(p==null)continue;
            double x=p.optDouble("lon",Double.NaN),y=p.optDouble("lat",Double.NaN);
            if(!Double.isFinite(x)||!Double.isFinite(y))continue;
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
        }
        double rangeX=Math.max(0.00001,maxX-minX),rangeY=Math.max(0.00001,maxY-minY);
        float scale=(float)Math.min((getWidth()-50)/rangeX,(getHeight()-75)/rangeY);
        paint.setColor(0xff31d9de);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(6f);
        android.graphics.Path path=new android.graphics.Path();boolean started=false;
        int stride=Math.max(1,limit/2000);
        for(int i=0;i<limit;i+=stride){JSONObject p=points.optJSONObject(i);if(p==null)continue;
            double lon=p.optDouble("lon",Double.NaN),lat=p.optDouble("lat",Double.NaN);
            if(!Double.isFinite(lon)||!Double.isFinite(lat))continue;
            float x=(float)(25+(lon-minX)*scale),y=(float)(getHeight()-40-(lat-minY)*scale);
            if(!started){path.moveTo(x,y);started=true;}else path.lineTo(x,y);
        }
        canvas.drawPath(path,paint);paint.setStyle(Paint.Style.FILL);
        paint.setTextSize(21);paint.setColor(0xffb2b9bf);
        canvas.drawText("Traçado da rota, sem mapa-base de ruas",16,getHeight()-12,paint);
    }
}
