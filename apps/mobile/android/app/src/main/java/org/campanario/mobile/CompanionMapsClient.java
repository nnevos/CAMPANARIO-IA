package org.campanario.mobile;

import android.content.Context;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Native, versioned peer API. Only the already paired HTTPS origin is contacted. */
final class CompanionMapsClient {
    private final String base;
    private final String token;
    CompanionMapsClient(Context context) throws Exception {
        JSONObject state = new JSONObject(new SecureStore(context).read());
        JSONObject connection = state.getJSONObject("connection");
        String server = connection.getString("server");
        URL parsed = new URL(server);
        if (!"https".equals(parsed.getProtocol()) || parsed.getUserInfo() != null ||
                !parsed.getPath().matches("/?") || parsed.getQuery() != null || parsed.getRef() != null ||
                parsed.getHost() == null || parsed.getHost().isEmpty()) {
            throw new IllegalArgumentException("O pareamento exige endereco HTTPS valido");
        }
        base = server.replaceAll("/$", "");
        token = connection.getString("token");
        if (token.isEmpty() || token.length() > 8192) throw new IllegalArgumentException("Dispositivo nao pareado");
    }
    JSONObject call(String action, JSONObject input) throws Exception {
        // Never take endpoint paths from user input or from a server response.
        if (!action.matches("maps/v2/(resolve|route|status|fix|recalculate|command/(start|pause|resume|stop))"))
            throw new IllegalArgumentException("Operacao nao permitida");
        HttpURLConnection conn = (HttpURLConnection)new URL(base + "/api/companion/v1/" + action).openConnection();
        try {
            conn.setInstanceFollowRedirects(false);
            conn.setConnectTimeout(10000); conn.setReadTimeout(20000);
            conn.setRequestProperty("Authorization", "Bearer " + token);
            conn.setRequestProperty("Accept", "application/json");
            if (input != null) {
                conn.setRequestMethod("POST"); conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                byte[] bytes=input.toString().getBytes(StandardCharsets.UTF_8);
                if(bytes.length>16384)throw new IllegalArgumentException("Payload grande demais");
                try(OutputStream stream=conn.getOutputStream()){stream.write(bytes);}
            }
            int status=conn.getResponseCode();
            InputStream stream=status>=400?conn.getErrorStream():conn.getInputStream();
            if(stream==null)throw new IllegalStateException("Servidor sem resposta");
            byte[] bytes;
            try(InputStream open=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] buffer=new byte[8192];int n;
                while((n=open.read(buffer))!=-1){if(out.size()+n>5000000)throw new IllegalStateException("Resposta maior que limite");out.write(buffer,0,n);}
                bytes=out.toByteArray();
            }
            if(bytes.length>200000)throw new IllegalStateException("Resposta maior que limite");
            JSONObject result=new JSONObject(new String(bytes,StandardCharsets.UTF_8));
            if(status<200||status>=300)throw new IllegalStateException(result.optString("detail","Falha HTTP "+status));
            return result;
        }finally{conn.disconnect();}
    }
}
