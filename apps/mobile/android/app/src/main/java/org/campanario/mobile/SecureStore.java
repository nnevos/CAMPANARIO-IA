package org.campanario.mobile;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** One encrypted state file, atomic replacement, key never stored beside the ciphertext. */
final class SecureStore {
    private static final String ALIAS = "campanario.local.state.v1";
    private static final int MAX = 8000000;
    private final AtomicFile file;
    SecureStore(Context context) { file = new AtomicFile(new File(context.getFilesDir(), "state.v1.enc")); }
    private SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).setUserAuthenticationRequired(false).build());
        return generator.generateKey();
    }
    synchronized String read() throws Exception {
        if (!file.getBaseFile().exists()) return "";
        if (file.getBaseFile().length() > MAX + 128) throw new IllegalStateException("State too large");
        byte[] sealed = file.readFully();
        if (sealed.length < 32 || sealed[0] != 1) throw new IllegalStateException("Unknown format");
        ByteBuffer buf = ByteBuffer.wrap(sealed); buf.get();
        byte[] nonce = new byte[12]; buf.get(nonce); byte[] cipherText = new byte[buf.remaining()]; buf.get(cipherText);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, nonce));
        cipher.updateAAD("Campanario/state/v1".getBytes(StandardCharsets.UTF_8));
        return new String(cipher.doFinal(cipherText), StandardCharsets.UTF_8);
    }
    synchronized void write(String json) throws Exception {
        byte[] plain = json.getBytes(StandardCharsets.UTF_8);
        if (plain.length > MAX) throw new IllegalArgumentException("State too large");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key());
        cipher.updateAAD("Campanario/state/v1".getBytes(StandardCharsets.UTF_8));
        byte[] encrypted = cipher.doFinal(plain);
        ByteBuffer buffer = ByteBuffer.allocate(1 + 12 + encrypted.length);
        buffer.put((byte)1); buffer.put(cipher.getIV()); buffer.put(encrypted);
        FileOutputStream output = null;
        try { output = file.startWrite(); output.write(buffer.array()); file.finishWrite(output); }
        catch (Exception ex) { if (output != null) file.failWrite(output); throw ex; }
    }
    synchronized void clear() throws Exception {
        file.delete();
        if (file.getBaseFile().exists()) throw new IllegalStateException("Delete failed");
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(ALIAS)) store.deleteEntry(ALIAS);
    }
}
