package com.dualscreen.xenogears;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Full-screen WebView showing the companion UI, plus a UDP bridge to RetroArch's network command port, plus (from v1.65)
 * read access to the player's own disc image and a folder for the room maps and pictures the page builds from it.
 */
public class MainActivity extends Activity {
    private static final int PICK_DISC = 7;
    private WebView web;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private DatagramSocket sock;
    private final Object discLock = new Object();
    private ParcelFileDescriptor discPfd;   // guarded by discLock
    private FileChannel discCh;
    private String discOpenFor = "";

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        // Never take input focus: touches still reach this window, but controller and key input stay with the emulator.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE);
        web = new WebView(this);
        web.setBackgroundColor(0xFF000000);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);   // the page loads the built maps and pictures from the app's own folder
        s.setTextZoom(100);
        s.setSupportZoom(false);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setWebViewClient(new WebViewClient());
        web.addJavascriptInterface(new Bridge(), "Native");
        setContentView(web);
        web.loadUrl("file:///android_asset/www/index.html");
        immersive();
    }

    @Override public void onWindowFocusChanged(boolean f) { super.onWindowFocusChanged(f); if (f) immersive(); }

    private void immersive() {
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    @Override protected void onDestroy() { io.shutdownNow(); if (sock != null) sock.close(); closeDisc(); super.onDestroy(); }

    private DatagramSocket socket() throws Exception {
        if (sock == null || sock.isClosed()) sock = new DatagramSocket();
        return sock;
    }

    private void js(final String code) {
        runOnUiThread(new Runnable() { public void run() { web.evaluateJavascript(code, null); } });
    }

    private SharedPreferences prefs() { return getSharedPreferences("disc", MODE_PRIVATE); }

    private File genDir() { File d = new File(getFilesDir(), "gen"); d.mkdirs(); return d; }

    /** a path inside the gen folder, refusing anything that would leave it */
    private File genFile(String path) throws Exception {
        if (path == null || path.contains("..") || path.startsWith("/")) throw new Exception("bad path");
        File f = new File(genDir(), path);
        return f;
    }

    private void closeDisc() {
        synchronized (discLock) {
            try { if (discCh != null) discCh.close(); } catch (Exception e) { }
            try { if (discPfd != null) discPfd.close(); } catch (Exception e) { }
            discCh = null; discPfd = null; discOpenFor = "";
        }
    }

    private FileChannel disc() throws Exception {
        String u = prefs().getString("uri", "");
        if (u.isEmpty()) throw new Exception("no disc chosen");
        if (discCh == null || !u.equals(discOpenFor)) {
            closeDisc();
            discPfd = getContentResolver().openFileDescriptor(Uri.parse(u), "r");
            if (discPfd == null) throw new Exception("could not open the disc file");
            discCh = new FileInputStream(discPfd.getFileDescriptor()).getChannel();
            discOpenFor = u;
        }
        return discCh;
    }

    private static String q(String s) { return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"; }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != PICK_DISC) return;
        if (res != RESULT_OK || data == null || data.getData() == null) { js("window.onDiscPicked&&onDiscPicked(null)"); return; }
        Uri uri = data.getData();
        try { getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception e) { }
        String name = "disc", size = "0";
        Cursor c = null;
        try {
            c = getContentResolver().query(uri, new String[] { OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE }, null, null, null);
            if (c != null && c.moveToFirst()) { if (c.getString(0) != null) name = c.getString(0); size = String.valueOf(c.getLong(1)); }
        } catch (Exception e) { } finally { if (c != null) c.close(); }
        prefs().edit().putString("uri", uri.toString()).putString("name", name).putString("size", size).apply();
        closeDisc();
        js("window.onDiscPicked&&onDiscPicked(" + q(name) + "," + size + ")");
    }

    private class Bridge {
        /** Temporarily allow focus so the on-screen keyboard can open for the host/port boxes; false hands focus back. */
        @JavascriptInterface public void focusable(final boolean on) {
            runOnUiThread(new Runnable() { public void run() {
                if (on) getWindow().clearFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE);
                else { web.clearFocus(); getWindow().addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE); }
            } });
        }
        /** Fire-and-forget command such as FAST_FORWARD. */
        @JavascriptInterface public void send(final String host, final int port, final String cmd) {
            io.execute(new Runnable() { public void run() {
                try {
                    byte[] d = cmd.getBytes("US-ASCII");
                    socket().send(new DatagramPacket(d, d.length, InetAddress.getByName(host), port));
                } catch (Exception e) { /* ignored: nothing useful to show */ }
            } });
        }

        /**
         * Read a set of 256-byte memory pages. mode: m80 = READ_CORE_MEMORY at 0x80000000+offset,
         * m00 = READ_CORE_MEMORY at offset, ram = READ_CORE_RAM at offset. pagesCsv = hex page numbers.
         * All requests are sent first, then replies are collected, so a poll costs about one emulator frame.
         */
        @JavascriptInterface public void poll(final String host, final int port, final String mode, final String pagesCsv, final int seq) {
            io.execute(new Runnable() { public void run() {
                String r;
                try { r = Link.poll(socket(), host, port, mode, pagesCsv, seq); }
                catch (Exception ex) { if (sock != null) { sock.close(); sock = null; } r = Link.fail(seq, ex.getClass().getSimpleName()); }
                js("window.onMem&&onMem(" + r + ")");
            } });
        }

        /* ---- the player's disc image ---- */
        /** Opens the system file picker; the answer comes back through window.onDiscPicked(name, size) or onDiscPicked(null). */
        @JavascriptInterface public void discPick() {
            runOnUiThread(new Runnable() { public void run() {
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                try { startActivityForResult(i, PICK_DISC); } catch (Exception e) { js("window.onDiscPicked&&onDiscPicked(null)"); }
            } });
        }
        @JavascriptInterface public String discName() { return prefs().getString("name", ""); }
        @JavascriptInterface public double discSize() {
            synchronized (discLock) { try { return disc().size(); } catch (Exception e) { return Double.parseDouble(prefs().getString("size", "0")); } }
        }
        /** length bytes at offset, base64, or "ERR:reason" */
        @JavascriptInterface public String discRead(double offset, int length) {
            synchronized (discLock) {
                try {
                    if (length <= 0 || length > (8 << 20)) return "ERR:bad length";
                    FileChannel ch = disc();
                    ByteBuffer bb = ByteBuffer.allocate(length);
                    long pos = (long) offset;
                    while (bb.hasRemaining()) { int n = ch.read(bb, pos + bb.position()); if (n <= 0) break; }
                    return Base64.encodeToString(bb.array(), 0, bb.position(), Base64.NO_WRAP);
                } catch (Exception e) { closeDisc(); return "ERR:" + e.getClass().getSimpleName() + ": " + e.getMessage(); }
            }
        }

        /* ---- the folder the built maps and pictures go in ---- */
        @JavascriptInterface public String genDir() { return MainActivity.this.genDir().getAbsolutePath(); }
        @JavascriptInterface public String genWrite(String path, String b64) {
            try {
                File f = genFile(path); f.getParentFile().mkdirs();
                File tmp = new File(f.getPath() + ".part");
                FileOutputStream o = new FileOutputStream(tmp);
                try { o.write(Base64.decode(b64, Base64.DEFAULT)); } finally { o.close(); }
                if (!tmp.renameTo(f)) { f.delete(); if (!tmp.renameTo(f)) return "ERR:rename"; }
                return "ok";
            } catch (Exception e) { return "ERR:" + e.getMessage(); }
        }
        @JavascriptInterface public boolean genHas(String path) { try { return genFile(path).isFile(); } catch (Exception e) { return false; } }
        /** a small text file from the folder (the manifest), "" when missing */
        @JavascriptInterface public String genRead(String path) {
            try {
                File f = genFile(path); if (!f.isFile() || f.length() > (1 << 20)) return "";
                byte[] d = new byte[(int) f.length()]; FileInputStream in = new FileInputStream(f);
                try { int p = 0; while (p < d.length) { int n = in.read(d, p, d.length - p); if (n <= 0) break; p += n; } } finally { in.close(); }
                return new String(d, "UTF-8");
            } catch (Exception e) { return ""; }
        }
        @JavascriptInterface public void genClear() { del(MainActivity.this.genDir()); }

        /* ---- room log (DEV): one line of JSON per room change, in the app's own files folder
           (Android/data/com.dualscreen.xenogears/files/Room log/room log.jsonl, reachable over USB); SHARE sends the text ---- */
        private File roomLog() { File d = new File(getExternalFilesDir(null) != null ? getExternalFilesDir(null) : getFilesDir(), "Room log"); d.mkdirs(); return new File(d, "room log.jsonl"); }
        @JavascriptInterface public String exitLog(String line) {
            try { FileOutputStream o = new FileOutputStream(roomLog(), true); try { o.write((line + "\r\n").getBytes("UTF-8")); } finally { o.close(); } return "ok"; }
            catch (Exception e) { return "ERR:" + e.getMessage(); }
        }
        @JavascriptInterface public void exitLogShare() {
            runOnUiThread(new Runnable() { public void run() {
                try {
                    File f = roomLog(); byte[] d = new byte[(int) Math.min(f.length(), 900000)]; FileInputStream in = new FileInputStream(f);
                    try { int p = 0; while (p < d.length) { int n = in.read(d, p, d.length - p); if (n <= 0) break; p += n; } } finally { in.close(); }
                    Intent i = new Intent(Intent.ACTION_SEND); i.setType("text/plain");
                    i.putExtra(Intent.EXTRA_SUBJECT, "room log.jsonl"); i.putExtra(Intent.EXTRA_TEXT, new String(d, "UTF-8"));
                    startActivity(Intent.createChooser(i, "Share the room log"));
                } catch (Exception e) { }
            }});
        }
        @JavascriptInterface public void exitLogClear() { roomLog().delete(); }
        private void del(File f) { File[] k = f.listFiles(); if (k != null) for (File c : k) { if (c.isDirectory()) del(c); c.delete(); } }
    }
}
