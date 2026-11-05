package com.jack.xenogears;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.Presentation;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Rect;
import android.hardware.display.DisplayManager;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.view.Display;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Xenogears Dual: the game on one screen, Xenogears Link on the other.
 *
 * The one activity. In file order:
 *   start-up                 onCreate, the WebViews
 *   storage and options      the Xenogears folder, core and input settings
 *   layout                   where the game, Link and the menu go (Duo halves, a second display, or split)
 *   Link's dev options       the Konami code turns them on and off
 *   Link on a second display LinkPresentation
 *   window events            displays coming and going, rotation, immersive mode
 *   game                     starting a disc (fresh or CONTINUE)
 *   continue + pictures      the place to CONTINUE from, the 5-minute safety save, save-state pictures
 *   stopping the game
 *   analog controls + mods   the analog program from analog.cht, GameShark codes, the diagnostics report
 *   menu and life cycle      showing the menu, pause/resume/destroy
 *   input                    touch pad, controller buttons and sticks, rebinding, hotkeys
 *   helpers, memory card     toasts, the menu's JavaScript, card files, save-state files
 *   bridges                  window.App for the menu, window.XenoLink and window.Native for Link
 * The emulator itself runs on the GL thread (Emu, GameView); jni/psxlink.c is the native side.
 */
public class MainActivity extends Activity implements TouchPad.Listener, Emu.Listener, DisplayManager.DisplayListener {
    static final String VERSION = "0.25";
    /** Disc IDs the core reports for Xenogears (US, then Japan). */
    private static final String[] XENO_IDS = { "SLUS00664", "SLUS00669", "SLPS01160", "SLPS01161" };
    /** Files the disc picker offers. */
    private static final String[] DISC_EXT = { ".cue", ".chd", ".pbp", ".m3u", ".iso", ".bin", ".img", ".ccd", ".ecm" };

    // views and screens
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final Emu emu = new Emu();
    private SharedPreferences prefs;
    private FrameLayout root, gamePane;
    private RailPane linkPane;
    private GameView gameView;
    private TouchPad pad;
    private BezelView bezel;
    private WebView menu, link;
    private LinkPresentation presentation;
    private DisplayManager displays;
    // folders: the Xenogears folder (saves, states, link, bezels, mods.txt) and the app's own system folder (BIOS)
    private File baseDir, sysDir, saveDir, stateDir;
    // where things stand
    private boolean running = false, menuVisible = true, linkOnPhone = false;
    private volatile boolean spanned = false;
    private boolean resumed = false;
    private String gameId = "";
    /** discSlot[i] = which disc (0 = Disc 1, 1 = Disc 2) sits at core image index i */
    private int[] discSlot = { 0, 1 };
    /** frame count when this game started, and whether it picked up from a save (CONTINUE or a loaded slot) */
    private long sessionStart;
    private volatile boolean sessionFromSave;
    /** Link's DEV section warped or set the story step since the last state load or start: this game isn't real progress, so CONTINUE keeps its old place */
    private volatile boolean devJumped;
    /** a fresh boot played for less than this doesn't replace the place to CONTINUE from (2 minutes) */
    private static final long RESUME_MIN_FRAMES = 60 * 120;
    // save-state pictures: a buffer for the newest frame
    private ByteBuffer shotBuf;
    private final int[] shotSeq = new int[1];

    // input from each source; pushInput() combines them
    private int touchMask, touchLx, touchLy, touchRx, touchRy, keyMask, hatMask, trigMask, padLx, padLy, padRx, padRy;
    /** Analog Controls.cht entries: {description, code, defaultOn} */
    private final List<String[]> cht = new ArrayList<>();
    /** Link's RAM polls run here, off the UI thread. */
    private final ExecutorService linkIo = Executors.newSingleThreadExecutor();

    // ---------------------------------------------------------------- start-up
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON | WindowManager.LayoutParams.FLAG_FULLSCREEN);
        prefs = getSharedPreferences("xenogears", MODE_PRIVATE);
        loadCht();

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        gamePane = new FrameLayout(this);
        linkPane = new RailPane(this);
        linkPane.setBackgroundColor(Color.BLACK);
        gameView = new GameView(this);
        pad = new TouchPad(this);
        pad.setListener(this);
        gamePane.addView(gameView, match());
        bezel = new BezelView(this, gameView);
        gamePane.addView(bezel, match());
        gamePane.addView(pad, match());
        gameView.onPictureChanged = new Runnable() { public void run() { applyLayout(); } };
        root.addView(gamePane, new FrameLayout.LayoutParams(0, 0));
        root.addView(linkPane, new FrameLayout.LayoutParams(0, 0));
        menu = makeWebView(this);
        menu.addJavascriptInterface(new MenuBridge(), "App");
        root.addView(menu, new FrameLayout.LayoutParams(0, 0));
        setContentView(root);
        root.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
            public void onLayoutChange(View v, int l, int t, int r, int bt, int ol, int ot, int or, int ob) {
                if (r - l != or - ol || bt - t != ob - ot) ui.post(new Runnable() { public void run() { applyLayout(); } });
            }
        });
        hideSystemUi();

        displays = (DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
        displays.registerDisplayListener(this, ui);

        setupDirs();
        Native.init(sysDir.getAbsolutePath(), saveDir.getAbsolutePath());
        bezel.setFolder(new File(baseDir, "bezels"));
        bezel.setStyle(prefs.getString("bezel", "window"));
        applyCoreOptions();
        applyInputOptions();
        emu.setListener(this);
        gameView.emu = emu;
        emu.displayHz = getWindowManager().getDefaultDisplay().getRefreshRate();

        menu.loadUrl("file:///android_asset/menu/index.html");

        ui.postDelayed(safetyTick, 30000);
        if (!hasStorage()) requestStorage();
        else maybeSkipLauncher();
    }

    /** Fills its parent. */
    private static FrameLayout.LayoutParams match() {
        return new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
    }

    /** A WebView for the menu or Link: JavaScript and file access on (both pages load other local files), black behind. */
    @SuppressLint("SetJavaScriptEnabled")
    static WebView makeWebView(Context c) {
        WebView w = new WebView(c);
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setTextZoom(100);
        w.setWebViewClient(new WebViewClient());
        w.setWebChromeClient(new WebChromeClient());
        w.setBackgroundColor(Color.BLACK);
        return w;
    }

    // ---------------------------------------------------------------- storage
    // The Xenogears folder on shared storage when the app may write there (Android 10 and earlier, permission given),
    // else the app's own external files folder. Disc paths are kept in prefs ("disc1", "disc2").
    private boolean hasStorage() {
        return checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestStorage() {
        requestPermissions(new String[] { Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE }, 1);
    }

    @Override public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        setupDirs();
        Native.init(sysDir.getAbsolutePath(), saveDir.getAbsolutePath());
        bezel.setFolder(new File(baseDir, "bezels"));
        bezel.setStyle(prefs.getString("bezel", "window"));
        applyLayout();
        menuJs("refresh()");
        maybeSkipLauncher();
    }

    private void setupDirs() {
        File ext = new File(Environment.getExternalStorageDirectory(), "Xenogears");
        if (hasStorage() && (ext.isDirectory() || ext.mkdirs()) && ext.canWrite()) baseDir = ext;
        else baseDir = getExternalFilesDir(null) != null ? getExternalFilesDir(null) : getFilesDir();
        sysDir = new File(getFilesDir(), "system");
        saveDir = new File(baseDir, "saves");
        stateDir = new File(baseDir, "states");
        File[] mk = { sysDir, saveDir, stateDir, new File(baseDir, "link"), new File(baseDir, "bezels") };
        for (File f : mk) f.mkdirs();
        File readme = new File(baseDir, "README.txt");
        if (!readme.exists()) {
            try (OutputStream o = new FileOutputStream(readme)) {
                o.write(("Xenogears folder\n\nsaves/    memory card\nstates/   save states\n"
                        + "link/index.html   Xenogears Link page shown on the second screen (replaces the built-in one)\n"
                        + "mods.txt  extra mods, one per line:  Name | 80012345 0001\n").getBytes("UTF-8"));
            } catch (Exception ignored) {}
        }
    }

    private String discPath(int slot) { return prefs.getString(slot == 0 ? "disc1" : "disc2", ""); }
    private boolean discOk(int slot) { String p = discPath(slot); return !p.isEmpty() && new File(p).isFile(); }

    /** Subsequent boots: go straight into the game when the launcher is switched off (picking up where you left off, if on). */
    private void maybeSkipLauncher() {
        if (running || prefs.getBoolean("showAtStart", true)) return;
        if (resumeOn() && resumeInfo() != null) { continueGame(); return; }
        int boot = prefs.getInt("bootDisc", 0);
        if (discOk(boot)) startGame();
    }

    // ---------------------------------------------------------------- options
    /** The core's settings (pcsx_rearmed_* variables); BIOS and high-res 3D come from Settings, the rest is fixed. */
    private void applyCoreOptions() {
        Native.setVariable("pcsx_rearmed_bios", prefs.getBoolean("hleBios", false) ? "HLE" : "auto");
        Native.setVariable("pcsx_rearmed_drc", "enabled");
        Native.setVariable("pcsx_rearmed_frameskip_type", "disabled");
        Native.setVariable("pcsx_rearmed_neon_enhancement_enable", prefs.getBoolean("hires", false) ? "enabled" : "disabled");
        Native.setVariable("pcsx_rearmed_neon_enhancement_no_main", "disabled");
        Native.setVariable("pcsx_rearmed_memcard1", "libretro");
        Native.setVariable("pcsx_rearmed_memcard2", "disabled");
        Native.setVariable("pcsx_rearmed_display_fps_v2", "disabled");
        Native.setVariable("pcsx_rearmed_show_bios_bootlogo", "disabled");
        Native.setVariable("pcsx_rearmed_spu_interpolation", "simple");
        Native.setVariable("pcsx_rearmed_analog_combo", "l3+r3");
    }

    /** Touch pad, picture and stick settings from prefs (called whenever Settings changes one). */
    private void applyInputOptions() {
        pad.setVisibility(prefs.getBoolean("touch", true) ? View.VISIBLE : View.GONE);
        pad.opacity = prefs.getInt("opacity", 55) / 100f;
        pad.showStick = prefs.getBoolean("stick", true);
        pad.relayout();
        gameView.smooth = prefs.getBoolean("smooth", true);
        gameView.integerScale = prefs.getBoolean("integer", false);
        Native.setStickDpad(prefs.getBoolean("stickDpad", true), prefs.getInt("stickThreshold", 40) * 32767 / 100);
        emu.muted = prefs.getBoolean("muted", false);
    }

    // ---------------------------------------------------------------- layout
    /**
     * Places the game pane, Link and the menu. Duo spanned: game on one half, Link on the other (Swap screens flips them).
     * A real second display: Link opens there (LinkPresentation). Otherwise the game fills the screen, or shares it with
     * Link when "Link on this screen" is on. Also works out the bezel's picture area and where the touch pad starts.
     */
    void applyLayout() {
        int w = root.getWidth(), h = root.getHeight();
        if (w == 0 || h == 0) return;
        int mode = 0;
        Rect hinge = Duo.hingeInWindow(this);
        spanned = hinge != null;
        boolean swap = prefs.getBoolean("swapScreens", false);
        boolean wantLink = prefs.getBoolean("link", true);
        Rect g, l = null;
        Rect a = null, bb = null;
        if (hinge != null) {
            boolean vertical = hinge.height() >= hinge.width();
            a = vertical ? new Rect(0, 0, hinge.left, h) : new Rect(0, 0, w, hinge.top);
            bb = vertical ? new Rect(hinge.right, 0, w, h) : new Rect(0, hinge.bottom, w, h);
        }
        // the one screen a single-screen layout has: the whole window, or the chosen half of a spanned Duo
        Rect one = hinge != null ? (swap ? bb : a) : new Rect(0, 0, w, h);
        wideScreen = one.width() >= one.height() * 1.5f;
        int want = wantLink ? layoutChoice() : LAYOUT_SECOND;
        if (want != LAYOUT_SECOND) {                       // chosen, so it applies even with a second display connected
            closePresentation();
            mode = want == LAYOUT_16_9 && wideScreen ? 2 : 1;
            int gw = Math.min(one.width(), Math.round(one.height() * 4f / 3f)), gh = Math.min(one.height(), gw * 3 / 4);
            g = new Rect(one.centerX() - gw / 2, one.centerY() - gh / 2, one.centerX() + gw / 2, one.centerY() + gh / 2);
            l = one;                                       // the game in the middle at 4:3, Link's page over everything and see-through there
        } else if (hinge != null) {
            g = swap ? bb : a;
            l = swap ? a : bb;
            closePresentation();
        } else {
            g = new Rect(0, 0, w, h);
            Display second = secondDisplay();
            if (wantLink && second != null) openPresentation(second);
            else closePresentation();
            if (linkOnPhone && presentation == null) {
                if (h > w) { g = new Rect(0, 0, w, h / 2); l = new Rect(0, h / 2, w, h); }
                else { g = new Rect(0, 0, w / 2, h); l = new Rect(w / 2, 0, w, h); }
            }
        }
        if (!wantLink) l = null;
        setRailMode(mode);
        place(gamePane, g);
        if (l != null) { place(linkPane, l); linkPane.setVisibility(View.VISIBLE); ensureLink(linkPane); }
        else { linkPane.setVisibility(View.GONE); if (link != null && link.getParent() == linkPane) linkPane.removeView(link); }
        place(menu, g);
        boolean portrait = g.height() > g.width() * 1.15f;
        gameView.alignTop = portrait && pad.getVisibility() == View.VISIBLE;
        bezel.setVisibility(railMode != 0 ? View.GONE : View.VISIBLE);
        Rect area = railMode != 0 ? null : bezel.pictureArea(g.width(), g.height(), gameView.alignTop);
        gameView.fitArea = area;
        int[] pic = gameView.gameRect(g.width(), g.height());
        int frameB = area != null && "window".equals(bezel.style()) ? bezel.border(g.width(), g.height()) : 0;
        pad.gameBottom = portrait ? pic[1] + pic[3] + frameB : 0;
        bezel.invalidate();
        pad.relayout();
        menuJs("layoutChanged()");
    }

    // ---------------------------------------------------------------- the single-screen layouts (0.23, 0.24)
    // Link's whole page in a panel that slides in from the right. Mode 2: quick info either side of the game too (Link's railDraw).
    // Mode 1: nothing but a see-through arrow on the game's right edge, for a 4:3 screen.
    /** Settings > SCREENS > Layout */
    static final int LAYOUT_SECOND = 0, LAYOUT_4_3 = 1, LAYOUT_16_9 = 2;
    private int layoutChoice() { return prefs.getInt("layout", prefs.getBoolean("rails", false) ? LAYOUT_16_9 : prefs.getBoolean("linkPanel", false) ? LAYOUT_4_3 : LAYOUT_SECOND); }
    /** what's showing: 0 off, 1 panel only, 2 quick info (a 16:9 choice on a narrow screen gets 1); read by Link's page and by RailPane */
    private volatile int railMode;
    /** the page's panel width and arrow size, as fractions of the screen: its sizes snap to whole pixels, so it reports what they came to */
    private volatile double railPanelW = 2 / 3.0, railArrowW = 0.06, railArrowH = 0.14;
    /** Link's panel is out */
    private volatile boolean railDrawerOpen;
    private boolean wideScreen;

    /** Link's page picks its layout when it loads, so a change reloads it. */
    private void setRailMode(int mode) {
        if (mode == railMode) return;
        boolean on = mode != 0;
        railMode = mode;
        railDrawerOpen = false;
        linkPane.setBackgroundColor(on ? Color.TRANSPARENT : Color.BLACK);
        if (link != null) { link.setBackgroundColor(on ? Color.TRANSPARENT : Color.BLACK); link.loadUrl(linkUrl()); }
    }

    /**
     * Holds Link's page. Over the game, touches pass through to the touch pad beneath; the page only takes them on the bars and arrow
     * and, when it's out, on the panel.
     */
    private final class RailPane extends FrameLayout {
        RailPane(Context c) { super(c); }
        @Override public boolean dispatchTouchEvent(MotionEvent e) {
            if (railMode != 0 && e.getActionMasked() == MotionEvent.ACTION_DOWN) {
                int w = getWidth(), h = getHeight();
                float x = e.getX(), y = e.getY();
                if (railMode == 2) {
                    int gw = Math.round(h * 4f / 3f), right = railDrawerOpen ? (int) (w - w * railPanelW - w * railArrowW) : (w + gw) / 2;
                    if (x >= (w - gw) / 2 && x < right) return false;
                } else {
                    int edge = railDrawerOpen ? (int) (w - w * railPanelW) : w;     // Link's #railBtn sits against this edge, half way up
                    boolean onArrow = Math.abs(y - h / 2f) <= h * railArrowH / 2 && x >= edge - w * railArrowW && x < edge;
                    if (!onArrow && x < edge) return false;
                }
            }
            return super.dispatchTouchEvent(e);
        }
    }

    private static void place(View v, Rect r) {
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(r.width(), r.height());
        lp.leftMargin = r.left; lp.topMargin = r.top;
        v.setLayoutParams(lp);
    }

    private Display secondDisplay() {
        for (Display d : displays.getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION))
            if (d.getDisplayId() != Display.DEFAULT_DISPLAY) return d;
        return null;
    }

    private void openPresentation(Display d) {
        if (presentation != null && presentation.getDisplay().getDisplayId() == d.getDisplayId()) return;
        closePresentation();
        try {
            presentation = new LinkPresentation(this, d);
            final LinkPresentation mine = presentation;
            presentation.setOnDismissListener(new android.content.DialogInterface.OnDismissListener() {
                public void onDismiss(android.content.DialogInterface di) {
                    // closed by something other than us (system, other app): put Link back on the bottom screen
                    if (presentation == mine) {
                        if (link != null && link.getParent() == mine.host) mine.host.removeView(link);
                        presentation = null;
                        if (!isFinishing() && resumed) ui.postDelayed(new Runnable() { public void run() { applyLayout(); } }, 400);
                    }
                }
            });
            presentation.show();
            ensureLink(presentation.host);
        } catch (Throwable t) {
            presentation = null;
            toast("Couldn't open the second screen: " + t.getMessage());
        }
    }

    private void closePresentation() {
        if (presentation == null) return;
        LinkPresentation p = presentation;
        presentation = null;                     // first, so onDismiss knows we closed it on purpose
        if (link != null && link.getParent() == p.host) p.host.removeView(link);
        try { p.dismiss(); } catch (Throwable ignored) {}
    }

    private void ensureLink(FrameLayout host) {
        if (link != null && link.getParent() == host) return;
        if (link != null) {
            ViewGroup p = (ViewGroup) link.getParent();
            if (p != null) p.removeView(link);
            if (link.getContext() != host.getContext()) { link.destroy(); link = null; }
        }
        if (link == null) {
            link = makeWebView(host.getContext());
            link.addJavascriptInterface(new LinkBridge(), "XenoLink");
            link.addJavascriptInterface(new LinkNative(), "Native");   // what Xenogears Link's web app talks to
            if (railMode != 0) link.setBackgroundColor(Color.TRANSPARENT);
            link.loadUrl(linkUrl());
        }
        host.addView(link, match());
    }

    /** Xenogears/link/index.html if the player put their own Link page there, else the built-in one. */
    private String linkUrl() {
        File user = new File(baseDir, "link/index.html");
        return user.isFile() ? "file://" + user.getAbsolutePath() : "file:///android_asset/link/index.html";
    }

    // ---------------------------------------------------------------- Link's developer options (Konami code)
    private final Konami konami = new Konami();

    /**
     * ↑↑↓↓←→←→ B A on a controller with the menu open turns Link's developer options on or off. They're Link's own
     * setting (CFG.dev, kept in its page storage), so the page sets it with its own sv(); in Dual the version line's
     * five taps no longer do it.
     */
    private void toggleDev() {
        if (link == null) { toast("Open Xenogears Link first (Settings > Screens)"); return; }
        link.evaluateJavascript("(function(){if(!window.sv||!window.CFG)return '';var on=!CFG.dev;sv('dev',on?'1':'0');return on?'on':'off'})()",
                new android.webkit.ValueCallback<String>() { public void onReceiveValue(String v) {
                    toast("\"on\"".equals(v) ? "Developer options on: Link > SETTINGS > DEVELOPER"
                            : "\"off\"".equals(v) ? "Developer options off" : "Link isn't ready yet. Try again in a moment.");
                }});
    }

    // ---------------------------------------------------------------- Link on a second display
    /** Link's window on a second display. It can't be closed by B/BACK and never takes the controller from the game. */
    class LinkPresentation extends Presentation {
        final FrameLayout host;
        LinkPresentation(Context c, Display d) {
            super(c, d);
            host = new FrameLayout(getContext());
            host.setBackgroundColor(Color.BLACK);
        }
        @Override protected void onCreate(Bundle b) {
            super.onCreate(b);
            setCancelable(false);
            setCanceledOnTouchOutside(false);
            // Touch still works on the Link screen, but it never takes keyboard/controller focus from the game,
            // so B (which Android falls back to BACK when nothing handles it) can't close it.
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                    | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                    | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL);
            setContentView(host);
        }
        // if it does get focus anyway, every button goes to the game
        @Override public boolean dispatchKeyEvent(KeyEvent e) { return MainActivity.this.dispatchKeyEvent(e); }
        @Override public boolean dispatchGenericMotionEvent(MotionEvent e) {
            return MainActivity.this.dispatchGenericMotionEvent(e) || super.dispatchGenericMotionEvent(e);
        }
        @Override public void onBackPressed() { }
    }

    // ---------------------------------------------------------------- window events
    // Displays coming and going, rotation and folding, and keeping the app full screen (immersive).
    @Override public void onDisplayAdded(int id) { applyLayout(); }
    @Override public void onDisplayRemoved(int id) { applyLayout(); }
    @Override public void onDisplayChanged(int id) { }

    @Override public void onConfigurationChanged(Configuration c) {
        super.onConfigurationChanged(c);
        hideSystemUi();
        ui.postDelayed(new Runnable() { public void run() { applyLayout(); } }, 150);
    }

    private void hideSystemUi() {
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
    }

    @Override public void onWindowFocusChanged(boolean f) {
        super.onWindowFocusChanged(f);
        if (f) { hideSystemUi(); if (presentation == null && secondDisplay() != null && prefs.getBoolean("link", true)) applyLayout(); }
    }

    // ---------------------------------------------------------------- game
    /** START: boots the disc picked as "Boot" in the launcher. */
    void startGame() { startGame(prefs.getInt("bootDisc", 0), null); }

    /** Boots disc `boot` (0 or 1); with a state file, jumps straight into it (CONTINUE). */
    void startGame(int boot, File state) {
        if (running) { showMenu(false); return; }
        if (!discOk(boot)) { toast("Pick Disc " + (boot + 1) + " first"); return; }
        int other = 1 - boot;
        String path = discPath(boot);
        File srm = cardFile();                             // one memory card shared by both discs
        applyCoreOptions();
        int padType = analogOn() ? 2 : prefs.getInt("padType", 0);
        if (!Native.loadGame(path, srm.getAbsolutePath(), padType)) {
            toast("Couldn't load " + new File(path).getName());
            return;
        }
        discSlot = new int[] { boot, other };
        if (discOk(other) && !discPath(other).toLowerCase(Locale.US).endsWith(".m3u")) Native.appendDisc(discPath(other));
        running = true;
        gameId = Native.gameId();
        if (Native.cardStatus() == 2) toast("The memory card file wasn't a formatted card. Kept a copy in saves/ and started a fresh card.");
        boolean xeno = false;
        for (String id : XENO_IDS) if (id.equalsIgnoreCase(gameId)) xeno = true;
        if (!xeno) toast("That disc reports " + (gameId.isEmpty() ? "no ID" : gameId) + ", not Xenogears. Running it anyway.");
        applyMods();
        sessionFromSave = false;
        devJumped = false;
        if (state != null) {
            if (Native.loadState(state.getAbsolutePath())) sessionFromSave = true;
            else toast("Couldn't pick up where you left off. Starting the disc instead.");
        }
        sessionStart = emu.frameCount;
        lastSafety = emu.frameCount;
        emu.paused = false;
        emu.start();
        showMenu(false);
        applyLayout();
        if (link != null) link.loadUrl(linkUrl());
    }

    // ---------------------------------------------------------------- continue + save-state pictures
    // The place to CONTINUE from is a save state plus its picture and a small file naming the disc it was on. It's
    // written when the app leaves the game (saveOnLeave) and every 5 minutes of play (safetySave).
    File resumeState() { return new File(stateDir, "Xenogears.resume.state"); }
    private File resumeMeta() { return new File(stateDir, "Xenogears.resume.json"); }
    boolean resumeOn() { return prefs.getBoolean("resume", true); }

    /** {disc, t} for the place to CONTINUE from, or null if there isn't one. */
    JSONObject resumeInfo() {
        File f = resumeState();
        if (!f.isFile()) return null;
        JSONObject o;
        try { o = new JSONObject(new String(readAll(resumeMeta()), "UTF-8")); } catch (Exception e) { o = new JSONObject(); }
        try { o.put("t", f.lastModified()); o.put("img", thumbUrl(f)); o.put("disc", o.optInt("disc", 0)); } catch (Exception ignored) {}
        return o;
    }

    void continueGame() {
        JSONObject r = resumeInfo();
        if (r == null) { startGame(); return; }
        int disc = r.optInt("disc", 0);
        if (!discOk(disc)) { toast("Disc " + (disc + 1) + " isn't where it was. Choose it again in the launcher."); return; }
        startGame(disc, resumeState());
    }

    /** Which disc (0/1) is in the drive now. */
    private int currentDisc() {
        int idx = running ? Native.discIndex() : 0;
        return idx >= 0 && idx < discSlot.length ? discSlot[idx] : 0;
    }

    /**
     * The app is going to the background, back to the launcher or closing: save the memory card, and where you are
     * for CONTINUE. Runs at once (see Emu.runNow). A fresh boot played under two minutes doesn't replace an existing
     * place to continue from, so starting the disc by mistake can't lose it.
     */
    private void saveOnLeave() {
        if (!running) return;
        final boolean resume = !devJumped && resumeOn() && (sessionFromSave || emu.frameCount - sessionStart >= RESUME_MIN_FRAMES || !resumeState().isFile());
        final int disc = currentDisc();
        emu.runNow(new Runnable() { public void run() {
            if (resume) synchronized (resumeIo) { if (saveSlot(resumeState())) writeResumeMeta(disc); }
            Native.saveMemcard();
        }});
    }

    /** Xenogears.resume.json: which disc (0/1) the CONTINUE state was saved on. */
    private void writeResumeMeta(int disc) {
        try (OutputStream o = new FileOutputStream(resumeMeta())) { o.write(("{\"disc\":" + disc + "}").getBytes("UTF-8")); }
        catch (Exception ignored) {}
    }

    /**
     * Safety save (0.20): every 5 minutes of play, where you are is saved for CONTINUE as it is on leaving, in case the app
     * never gets to leave (a crash, a flat battery). Same rules as saveOnLeave. The emulator thread only copies the state and
     * the frame (a few ms); the 4 MB file and the picture are written on saveIo, so the game doesn't hitch.
     */
    private static final long SAFETY_FRAMES = 60 * 60 * 5;
    private long lastSafety;
    private final Object resumeIo = new Object();              // one writer of the resume files at a time
    private final ExecutorService saveIo = Executors.newSingleThreadExecutor();
    private final Runnable safetyTick = new Runnable() { public void run() { ui.postDelayed(this, 30000); safetySave(); } };

    private void safetySave() {
        if (!running || emu.paused || menuVisible || !resumeOn() || devJumped) return;
        if (!(sessionFromSave || emu.frameCount - sessionStart >= RESUME_MIN_FRAMES)) return;
        if (emu.frameCount - lastSafety < SAFETY_FRAMES) return;
        lastSafety = emu.frameCount;
        final int disc = currentDisc();
        emu.post(new Runnable() { public void run() {
            final byte[] st = Native.stateBytes();
            if (st == null) return;
            final Bitmap shot = grabFrame();
            saveIo.execute(new Runnable() { public void run() {
                synchronized (resumeIo) {
                    File f = resumeState(), part = new File(f.getPath() + ".part");
                    try (OutputStream o = new FileOutputStream(part)) { o.write(st); }
                    catch (Exception e) { part.delete(); return; }
                    if (!part.renameTo(f)) { f.delete(); if (!part.renameTo(f)) return; }
                    if (shot != null) writeJpeg(shot, thumbFile(f));
                    writeResumeMeta(disc);
                }
            }});
        }});
    }

    /** Saves a state and a picture of the current frame beside it (emulator thread). */
    boolean saveSlot(File f) {
        if (!Native.saveState(f.getAbsolutePath())) return false;
        writeThumb(thumbFile(f));
        return true;
    }

    static File thumbFile(File state) { return new File(state.getPath().replaceAll("\\.state$", "") + ".jpg"); }

    /** file:// address of a state's picture for the menu and Link ("" if none); the time stops the WebView reusing an old one. */
    static String thumbUrl(File state) {
        File t = thumbFile(state);
        return t.isFile() ? "file://" + t.getAbsolutePath() + "?" + t.lastModified() : "";
    }

    /** Save-state slots in the pause menu (Link's SAVE STATES shows 1-4); slot 0 is QUICK, used by the hotkeys. */
    static final int SLOTS = 8;

    private JSONObject slotJson(File f) {
        JSONObject s = new JSONObject();
        try { s.put("t", f.isFile() ? f.lastModified() : 0); s.put("img", f.isFile() ? thumbUrl(f) : ""); } catch (Exception ignored) {}
        return s;
    }

    /** {t, img} per slot 1-SLOTS: when it was saved (0 = empty) and its picture. */
    JSONArray slotList() {
        JSONArray a = new JSONArray();
        for (int i = 1; i <= SLOTS; i++) a.put(slotJson(statePath(i)));
        return a;
    }

    /** The game's newest frame as a 192-pixel-wide picture, or null (emulator thread; the frame is the game, never the menu). */
    private Bitmap grabFrame() {
        try {
            if (shotBuf == null) shotBuf = ByteBuffer.allocateDirect(2048 * 1024 * 2).order(ByteOrder.nativeOrder());
            int wh = Native.copyFrame(shotBuf, Integer.MIN_VALUE, shotSeq);
            if (wh == 0) return null;
            int w = wh >>> 16, h = wh & 0xffff;
            shotBuf.position(0);
            Bitmap src = Bitmap.createBitmap(w, h, Bitmap.Config.RGB_565);
            src.copyPixelsFromBuffer(shotBuf);
            float aspect = Native.aspect();
            if (aspect <= 0) aspect = 4f / 3f;
            Bitmap t = Bitmap.createScaledBitmap(src, 192, Math.round(192 / aspect), true);
            src.recycle();
            return t;
        } catch (Throwable e) { return null; }
    }

    /** Writes a picture as JPEG (any thread) and frees it. */
    private static void writeJpeg(Bitmap b, File out) {
        try (OutputStream o = new FileOutputStream(out)) { b.compress(Bitmap.CompressFormat.JPEG, 85, o); }
        catch (Throwable e) { out.delete(); }
        b.recycle();
    }

    /** A save state's picture, from the newest frame (emulator thread); no frame, no picture. */
    private void writeThumb(File out) {
        Bitmap b = grabFrame();
        if (b == null) out.delete(); else writeJpeg(b, out);
    }

    // ---------------------------------------------------------------- stopping the game
    /** Stops the emulator (which saves the memory card) and unloads the disc. Link goes back to waiting. */

    void stopGame() {
        if (!running) return;
        emu.stop();
        Native.unload();
        running = false;
        gameId = "";
        if (link != null) link.loadUrl(linkUrl());
    }

    // ---------------------------------------------------------------- analog controls + mods
    // The analog controls are Jack's program in assets/analog.cht: its "code" entries are the program's bytes, its
    // "Analog:" entries the five option switches. psxlink.c installs it (not the cheat engine). Mods are GameShark
    // codes from mods.txt or added in the Mods screen; they go to the core's cheat list.
    /** Reads assets/analog.cht (RetroArch format): the analog controls program, its hook and its option switches. */
    private void loadCht() {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(getAssets().open("analog.cht"), "UTF-8"))) {
            java.util.Map<Integer, String[]> m = new java.util.TreeMap<>();
            String line;
            while ((line = r.readLine()) != null) {
                java.util.regex.Matcher x = java.util.regex.Pattern.compile("^cheat(\\d+)_(desc|code|enable)\\s*=\\s*\"?(.*?)\"?\\s*$").matcher(line.trim());
                if (!x.find()) continue;
                int i = Integer.parseInt(x.group(1));
                String[] e = m.get(i);
                if (e == null) { e = new String[] { "", "", "false" }; m.put(i, e); }
                String k = x.group(2);
                e[k.equals("desc") ? 0 : k.equals("code") ? 1 : 2] = x.group(3);
            }
            cht.clear();
            cht.addAll(m.values());
        } catch (Exception e) { toast("Couldn't read the analog controls: " + e.getMessage()); }
    }

    private static boolean isOption(String[] e) { return e[0].startsWith("Analog:"); }
    boolean analogOn() { return prefs.getBoolean("analogOn", true); }
    private boolean optionOn(int i) { return prefs.getBoolean("cht:" + i, "true".equals(cht.get(i)[2])); }

    /** What the launcher shows: the analog controls (one switch plus its options), then any extra codes. */
    JSONArray modList() {
        JSONArray out = new JSONArray();
        try {
            for (int i = 0; i < cht.size(); i++) {
                String[] e = cht.get(i);
                if (!isOption(e)) continue;
                JSONObject m = new JSONObject();
                m.put("id", "cht:" + i);
                m.put("name", e[0].substring("Analog:".length()).trim());
                m.put("group", "analog");
                m.put("on", optionOn(i));
                out.put(m);
            }
            readMods(new FileInputStream(new File(baseDir, "mods.txt")), "mods.txt", out);
        } catch (Exception ignored) {}
        try {
            JSONArray user = new JSONArray(prefs.getString("userMods", "[]"));
            for (int i = 0; i < user.length(); i++) {
                JSONObject m = user.getJSONObject(i);
                m.put("id", "mod:" + m.optString("name"));
                m.put("source", "Added here"); m.put("removable", true);
                m.put("on", prefs.getBoolean("mod:" + m.optString("name"), false));
                out.put(m);
            }
        } catch (Exception ignored) {}
        return out;
    }

    private void readMods(InputStream in, String src, JSONArray out) {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                int bar = line.indexOf('|');
                String name = bar > 0 ? line.substring(0, bar).trim() : "Mod " + (out.length() + 1);
                String code = bar > 0 ? line.substring(bar + 1).trim() : line;
                JSONObject m = new JSONObject();
                m.put("id", "mod:" + name); m.put("name", name); m.put("code", code); m.put("source", src);
                m.put("on", prefs.getBoolean("mod:" + name, false));
                out.put(m);
            }
        } catch (Exception ignored) {}
    }

    /** The analog program's bytes from 0x80017400, built from the .cht's "code" entries (zero where the .cht writes nothing). */
    private byte[] analogProgram() {
        byte[] mem = new byte[0xC00];
        int hi = 0;
        for (String[] e : cht) {
            if (isOption(e) || !e[0].toLowerCase(Locale.US).contains("- code")) continue;
            for (String part : e[1].split("\\+")) {
                String[] av = part.trim().split("\\s+");
                if (av.length != 2) continue;
                long a = Long.parseLong(av[0], 16); int v = Integer.parseInt(av[1], 16);
                if ((a >>> 24) != 0x80) continue;
                int o = (int) (a & 0x1fffff) - 0x17400;
                if (o < 0 || o + 2 > mem.length) continue;
                mem[o] = (byte) v; mem[o + 1] = (byte) (v >> 8);
                hi = Math.max(hi, o + 2);
            }
        }
        return Arrays.copyOf(mem, hi);
    }

    /** Option switches as bits: the .cht's "30017F0n 0010" entries, bit n-4. */
    private int analogOptions() {
        int bits = 0;
        for (int i = 0; i < cht.size(); i++) {
            String[] e = cht.get(i);
            if (!isOption(e) || !optionOn(i)) continue;
            java.util.regex.Matcher m = java.util.regex.Pattern.compile("30017F0([4-8])").matcher(e[1].toUpperCase(Locale.US));
            if (m.find()) bits |= 1 << (m.group(1).charAt(0) - '4');
        }
        return bits;
    }

    /** Codes that write into the analog program's block or its hook slot would fight the built-in copy. */
    final List<String> skippedMods = new ArrayList<>();
    static boolean touchesAnalog(String code) {
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("(?i)\\b[0-9a-f]{2}(0[0-9a-f]{5})\\b").matcher(code == null ? "" : code);
        while (m.find()) {
            int a = Integer.parseInt(m.group(1), 16);
            if ((a >= 0x17400 && a < 0x18000) || (a >= 0x501fc && a < 0x50200)) return true;
        }
        return false;
    }

    /**
     * What the emulator, the analog installer and the memory card look like right now, also written to diagnostics.txt.
     * Settings > Diagnostics showed it up to 0.16; it has no menu entry since 0.17, but App.diagnostics() still returns
     * it for when a report is needed again.
     */
    String diagnosticsReport() {
        StringBuilder r = new StringBuilder();
        r.append("Xenogears Dual ").append(VERSION).append("  ").append(new java.util.Date()).append('\n');
        r.append("device ").append(android.os.Build.MANUFACTURER).append(' ').append(android.os.Build.MODEL).append("  Android ").append(android.os.Build.VERSION.RELEASE).append('\n');
        File[] bs = sysDir.listFiles();
        r.append("system folder ").append(sysDir).append(": ");
        if (bs != null) for (File f : bs) r.append(f.getName()).append(" (").append(f.length()).append(") ");
        r.append("\nbuilt-in BIOS only ").append(prefs.getBoolean("hleBios", false)).append("  running ").append(running).append("  disc ").append(discOk(0) ? new File(discPath(0)).getName() : "-").append('\n');
        File cf = cardFile();
        r.append("card file ").append(cf).append(" exists ").append(cf.isFile()).append(" size ").append(cf.length()).append('\n');
        try { r.append("card info ").append(cardInfo().toString()).append('\n'); } catch (Exception e) { r.append("card info error ").append(e).append('\n'); }
        r.append("analog on ").append(analogOn()).append(" options ").append(Integer.toHexString(analogOptions())).append(" program bytes ").append(analogProgram().length).append('\n');
        JSONArray mods = modList();
        for (int i = 0; i < mods.length(); i++) {
            JSONObject m = mods.optJSONObject(i);
            if (m == null || "analog".equals(m.optString("group")) || !m.optBoolean("on")) continue;
            String c = m.optString("code");
            r.append("mod on: ").append(m.optString("name")).append(" [").append(m.optString("source")).append("] ").append(c.length() > 60 ? c.substring(0, 60) + "..." : c).append('\n');
        }
        for (String n : skippedMods) r.append("mod skipped (writes where the analog program lives): ").append(n).append('\n');
        r.append("sticks now: L ").append(padLx).append(',').append(padLy).append("  R ").append(padRx).append(',').append(padRy).append('\n');
        for (int id : InputDevice.getDeviceIds()) {
            InputDevice d = InputDevice.getDevice(id);
            if (d == null || (d.getSources() & InputDevice.SOURCE_JOYSTICK) != InputDevice.SOURCE_JOYSTICK) continue;
            r.append("pad ").append(d.getName()).append(" axes:");
            for (InputDevice.MotionRange mr : d.getMotionRanges()) r.append(' ').append(MotionEvent.axisToString(mr.getAxis()).replace("AXIS_", ""));
            r.append('\n');
        }
        r.append(Native.diagnostics());
        try (FileOutputStream o = new FileOutputStream(new File(baseDir, "diagnostics.txt"))) { o.write(r.toString().getBytes("UTF-8")); }
        catch (Exception e) { r.append("\n(couldn't write diagnostics.txt: ").append(e.getMessage()).append(")"); }
        return r.toString();
    }

    /** Analog controls go to the frontend's installer (see psxlink.c); extra GameShark codes go to the core's cheat list. */
    private void applyMods() {
        if (!running) return;
        final byte[] prog = analogProgram();
        final boolean master = analogOn();
        final int opts = analogOptions();
        final List<String> codes = new ArrayList<>();
        skippedMods.clear();
        JSONArray extra = modList();
        for (int i = 0; i < extra.length(); i++) {
            JSONObject m = extra.optJSONObject(i);
            if (m == null || "analog".equals(m.optString("group"))) continue;
            if (!m.optBoolean("on")) continue;
            if (master && touchesAnalog(m.optString("code"))) { skippedMods.add(m.optString("name")); continue; }
            codes.add(m.optString("code"));
        }
        emu.post(new Runnable() { public void run() {
            Native.setAnalogMod(prog, master, opts);
            Native.clearCheats();
            for (int i = 0; i < codes.size(); i++) Native.setCheat(i, true, codes.get(i));
        }});
    }

    /** Analog controls need a DualShock on port 1; the installer switches it into analog mode once the game is running. */
    private void applyAnalogMode() {
        if (!running) return;
        final int type = analogOn() ? 2 : prefs.getInt("padType", 0);
        emu.post(new Runnable() { public void run() { Native.setPadType(type); } });
    }

    // ---------------------------------------------------------------- menu and life cycle
    /** Shows or hides the menu page (launcher, settings, pause); the game is paused while it's up. */
    void showMenu(boolean show) {
        menuVisible = show;
        if (!show) bindWait = -1;
        menu.setVisibility(show ? View.VISIBLE : View.GONE);
        if (running) emu.paused = show;
        if (show) { menu.requestFocus(); menuJs("refresh()"); }
        else gameView.requestFocus();
        applyLayout();
    }

    @Override public void onMenu() { showMenu(true); menuJs("openPause()"); }
    @Override public void onCoreMessage(String msg) { toast(msg); }

    /** Leaving the app: pause, then save the memory card and where you are, at once (see saveOnLeave). */
    @Override protected void onPause() {
        super.onPause();
        resumed = false;
        gameView.onPause();
        if (running) { emu.paused = true; saveOnLeave(); }
    }

    @Override protected void onResume() {
        super.onResume();
        resumed = true;
        gameView.onResume();
        hideSystemUi();
        if (running && !menuVisible) emu.paused = false;
        ui.postDelayed(new Runnable() { public void run() { applyLayout(); } }, 200);
    }

    @Override protected void onDestroy() {
        displays.unregisterDisplayListener(this);
        closePresentation();
        stopGame();
        super.onDestroy();
    }

    // ---------------------------------------------------------------- input
    // Port 1 gets the touch pad, controller buttons, the d-pad hat, analog triggers and both sticks, combined in
    // pushInput(). A controller stick that's pushed wins over the touch stick.
    @Override public void onPadChanged(int mask, int lx, int ly, int rx, int ry) {
        touchMask = mask; touchLx = lx; touchLy = ly; touchRx = rx; touchRy = ry; pushInput();
    }

    private void pushInput() {
        Native.setButtons(0, touchMask | keyMask | hatMask | trigMask);
        boolean padStick = Math.abs(padLx) > 3000 || Math.abs(padLy) > 3000;
        boolean padR = Math.abs(padRx) > 3000 || Math.abs(padRy) > 3000;
        Native.setAxes(0, padStick ? padLx : touchLx, padStick ? padLy : touchLy, padR ? padRx : touchRx, padR ? padRy : touchRy);
    }

    // ---------------------------------------------------------------- button rebinding
    // keycode -> PlayStation button, kept in prefs "keyBinds"; Settings > Controls > Controller buttons > REBIND.
    static final int[] BIND_BITS = { Native.CROSS, Native.CIRCLE, Native.SQUARE, Native.TRIANGLE, Native.L, Native.R, Native.L2, Native.R2,
            Native.L3, Native.R3, Native.START, Native.SELECT, Native.UP, Native.DOWN, Native.LEFT, Native.RIGHT };
    static final String[] BIND_NAMES = { "Cross", "Circle", "Square", "Triangle", "L1", "R1", "L2", "R2",
            "L3", "R3", "Start", "Select", "Up", "Down", "Left", "Right" };
    private android.util.SparseIntArray binds;    // keycode -> button bit
    volatile int bindWait = -1;                   // button waiting for a key press in Settings, or -1
    private int swallowUp = -1;                   // the key that was just captured: its release is not a menu press

    private android.util.SparseIntArray defaultBinds() {
        android.util.SparseIntArray m = new android.util.SparseIntArray();
        for (int code = 0; code <= KeyEvent.getMaxKeyCode(); code++) { int b = keyBit(code); if (b >= 0) m.put(code, b); }
        return m;
    }
    private android.util.SparseIntArray binds() {
        if (binds != null) return binds;
        binds = defaultBinds();
        try {
            String js = prefs.getString("keyBinds", "");
            if (!js.isEmpty()) {
                JSONObject o = new JSONObject(js);
                android.util.SparseIntArray m = new android.util.SparseIntArray();
                java.util.Iterator<String> it = o.keys();
                while (it.hasNext()) { String k = it.next(); m.put(Integer.parseInt(k), o.getInt(k)); }
                binds = m;
            }
        } catch (Exception ignored) {}
        return binds;
    }
    private void saveBinds() {
        try {
            JSONObject o = new JSONObject();
            for (int i = 0; i < binds.size(); i++) o.put(String.valueOf(binds.keyAt(i)), binds.valueAt(i));
            prefs.edit().putString("keyBinds", o.toString()).apply();
        } catch (Exception ignored) {}
    }
    /** Gives button `bit` to key `code`. The key's old button takes over this button's old key, so nothing is lost. */
    void bindKey(int bit, int code) {
        android.util.SparseIntArray m = binds();
        int oldBit = m.get(code, -1);
        int oldKey = -1;
        for (int i = m.size() - 1; i >= 0; i--) if (m.valueAt(i) == bit) { if (oldKey < 0) oldKey = m.keyAt(i); m.removeAt(i); }
        m.put(code, bit);
        if (oldBit >= 0 && oldBit != bit && oldKey >= 0 && oldKey != code) m.put(oldKey, oldBit);
        saveBinds();
        int hi = hot().indexOfKey(code);                      // a key does one job: it stops being a hotkey
        if (hi >= 0) { hot.removeAt(hi); saveHot(); }
    }

    // ---------------------------------------------------------------- hotkeys (0.20): a controller button each, off until set
    static final String[] HOT_NAMES = { "Quick save", "Quick load", "Fast forward", "Link panel" };
    static final int HOT_WAIT = 100;                         // bindWait 100+i: Settings waits for hotkey i's button
    private android.util.SparseIntArray hot;                 // keycode -> hotkey index

    private android.util.SparseIntArray hot() {
        if (hot != null) return hot;
        hot = new android.util.SparseIntArray();
        try {
            JSONObject o = new JSONObject(prefs.getString("hotkeys", "{}"));
            java.util.Iterator<String> it = o.keys();
            while (it.hasNext()) { String k = it.next(); hot.put(Integer.parseInt(k), o.getInt(k)); }
        } catch (Exception ignored) {}
        return hot;
    }
    private void saveHot() {
        try {
            JSONObject o = new JSONObject();
            for (int i = 0; i < hot.size(); i++) o.put(String.valueOf(hot.keyAt(i)), hot.valueAt(i));
            prefs.edit().putString("hotkeys", o.toString()).apply();
        } catch (Exception ignored) {}
    }
    /** Gives hotkey i to key `code`. The key stops pressing its PlayStation button (one key, one job). */
    void bindHot(int i, int code) {
        android.util.SparseIntArray h = hot();
        for (int j = h.size() - 1; j >= 0; j--) if (h.valueAt(j) == i) h.removeAt(j);
        h.put(code, i);
        saveHot();
        int bi = binds().indexOfKey(code);
        if (bi >= 0) { binds.removeAt(bi); saveBinds(); }
    }
    void clearHot(int i) {
        android.util.SparseIntArray h = hot();
        for (int j = h.size() - 1; j >= 0; j--) if (h.valueAt(j) == i) h.removeAt(j);
        saveHot();
    }
    JSONArray hotList() throws Exception {
        JSONArray out = new JSONArray();
        for (int i = 0; i < HOT_NAMES.length; i++) {
            String key = "";
            for (int k = 0; k < hot().size(); k++) if (hot.valueAt(k) == i) key = keyLabel(hot.keyAt(k));
            JSONObject b = new JSONObject();
            b.put("i", i); b.put("name", HOT_NAMES[i]); b.put("key", key);
            out.put(b);
        }
        return out;
    }
    private void doHotkey(int i) {
        if (!running) return;
        final File q = quickState();
        if (i == 0) emu.post(new Runnable() { public void run() { toast(saveSlot(q) ? "Quick saved" : "Quick save failed"); menuJs("refresh()"); } });
        else if (i == 1) {
            if (!q.isFile()) { toast("No quick save yet"); return; }
            emu.post(new Runnable() { public void run() {
                boolean ok = Native.loadState(q.getAbsolutePath());
                if (ok) { sessionFromSave = true; devJumped = false; }
                toast(ok ? "Quick loaded" : "Quick load failed");
            }});
        } else if (i == 2) { emu.fastForward = !emu.fastForward; toast(emu.fastForward ? "Fast forward on" : "Fast forward off"); }
        else if (i == 3 && railMode != 0) ui.post(new Runnable() { public void run() { if (link != null) link.evaluateJavascript("window.railToggle&&railToggle()", null); } });
    }
    static String keyLabel(int code) {
        String n = KeyEvent.keyCodeToString(code);
        return n.replace("KEYCODE_BUTTON_", "").replace("KEYCODE_DPAD_", "DPAD ").replace("KEYCODE_", "").replace('_', ' ');
    }
    JSONArray bindList() throws Exception {
        android.util.SparseIntArray m = binds();
        JSONArray out = new JSONArray();
        for (int i = 0; i < BIND_BITS.length; i++) {
            StringBuilder keys = new StringBuilder();
            for (int k = 0; k < m.size(); k++) if (m.valueAt(k) == BIND_BITS[i]) { if (keys.length() > 0) keys.append(" + "); keys.append(keyLabel(m.keyAt(k))); }
            JSONObject b = new JSONObject();
            b.put("bit", BIND_BITS[i]); b.put("name", BIND_NAMES[i]); b.put("key", keys.toString());
            out.put(b);
        }
        return out;
    }

    /** The default binding: Android's gamepad keycodes to PlayStation buttons (A = Cross, B = Circle, ...). */
    private static int keyBit(int code) {
        switch (code) {
            case KeyEvent.KEYCODE_BUTTON_A: return Native.CROSS;
            case KeyEvent.KEYCODE_BUTTON_B: return Native.CIRCLE;
            case KeyEvent.KEYCODE_BUTTON_X: return Native.SQUARE;
            case KeyEvent.KEYCODE_BUTTON_Y: return Native.TRIANGLE;
            case KeyEvent.KEYCODE_BUTTON_L1: return Native.L;
            case KeyEvent.KEYCODE_BUTTON_R1: return Native.R;
            case KeyEvent.KEYCODE_BUTTON_L2: return Native.L2;
            case KeyEvent.KEYCODE_BUTTON_R2: return Native.R2;
            case KeyEvent.KEYCODE_BUTTON_THUMBL: return Native.L3;
            case KeyEvent.KEYCODE_BUTTON_THUMBR: return Native.R3;
            case KeyEvent.KEYCODE_BUTTON_START: return Native.START;
            case KeyEvent.KEYCODE_BUTTON_SELECT: return Native.SELECT;
            case KeyEvent.KEYCODE_DPAD_UP: return Native.UP;
            case KeyEvent.KEYCODE_DPAD_DOWN: return Native.DOWN;
            case KeyEvent.KEYCODE_DPAD_LEFT: return Native.LEFT;
            case KeyEvent.KEYCODE_DPAD_RIGHT: return Native.RIGHT;
        }
        return -1;
    }

    // ---------------------------------------------------------------- controller and keyboard events
    /**
     * Every key, in this order: a key Settings is waiting for (rebinding, hotkeys); with the menu open, the Konami code
     * check; BACK / the controller's home button (menu back, or open the pause menu); while the menu is up, the d-pad and
     * A/B/START move around it; in the game, a hotkey, else the bound PlayStation button. SELECT + START together open
     * the pause menu.
     */
    @Override public boolean dispatchKeyEvent(KeyEvent e) {
        int code = e.getKeyCode();
        if (bindWait >= 0 && menuVisible && e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0) {
            // Settings > Controller buttons / Hotkeys > SET: the next key pressed becomes the binding (BACK cancels)
            if (code != KeyEvent.KEYCODE_BACK && code != KeyEvent.KEYCODE_BUTTON_MODE) {
                if (bindWait >= HOT_WAIT) bindHot(bindWait - HOT_WAIT, code); else bindKey(bindWait, code);
            }
            bindWait = -1;
            swallowUp = code;
            menuJs("refresh()");
            return true;
        }
        if (code == swallowUp) { if (e.getAction() == KeyEvent.ACTION_UP) swallowUp = -1; return true; }
        if (menuVisible && e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0) {
            int kc = konami.feed(code);                      // ↑↑↓↓←→←→ B A with the menu open: Link's developer options
            if (kc == Konami.HOLD) return true;
            if (kc == Konami.DONE) { toggleDev(); return true; }
            if (kc == Konami.RELEASE) menuJs("navKey('back')");
        }
        if (code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_BUTTON_MODE) {
            if (e.getAction() == KeyEvent.ACTION_UP) { if (menuVisible) menuJs("back()"); else onMenu(); }
            return true;
        }
        if (menuVisible) {
            String k = null;
            switch (code) {
                case KeyEvent.KEYCODE_DPAD_UP: k = "up"; break;
                case KeyEvent.KEYCODE_DPAD_DOWN: k = "down"; break;
                case KeyEvent.KEYCODE_DPAD_LEFT: k = "left"; break;
                case KeyEvent.KEYCODE_DPAD_RIGHT: k = "right"; break;
                case KeyEvent.KEYCODE_BUTTON_A: case KeyEvent.KEYCODE_DPAD_CENTER: case KeyEvent.KEYCODE_ENTER: k = "ok"; break;
                case KeyEvent.KEYCODE_BUTTON_B: k = "back"; break;
                case KeyEvent.KEYCODE_BUTTON_START: k = "start"; break;
            }
            if (k == null) return super.dispatchKeyEvent(e);
            if (e.getAction() == KeyEvent.ACTION_DOWN) menuJs("navKey('" + k + "')");
            return true;
        }
        int hk = hot().get(code, -1);
        if (hk >= 0) { if (e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0) doHotkey(hk); return true; }
        int bit = binds().get(code, -1);
        if (bit < 0) return super.dispatchKeyEvent(e);
        if (e.getAction() == KeyEvent.ACTION_DOWN) keyMask |= 1 << bit;
        else if (e.getAction() == KeyEvent.ACTION_UP) keyMask &= ~(1 << bit);
        int both = (1 << Native.SELECT) | (1 << Native.START);
        if ((keyMask & both) == both) { keyMask = 0; pushInput(); onMenu(); return true; }
        pushInput();
        return true;
    }

    /** Controller sticks, the d-pad hat and analog triggers (L2/R2 past half way), while playing. */
    @Override public boolean dispatchGenericMotionEvent(MotionEvent e) {
        if (!menuVisible && (e.getSource() & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK
                && e.getAction() == MotionEvent.ACTION_MOVE) {
            padLx = axis(e, MotionEvent.AXIS_X); padLy = axis(e, MotionEvent.AXIS_Y);
            InputDevice dev = e.getDevice();
            // right stick: Z/RZ on most pads; some report it on RX/RY instead (only used when the pad has no Z axis,
            // because pads like the DualShock 4 put their analog triggers on RX/RY)
            boolean zr = dev == null || dev.getMotionRange(MotionEvent.AXIS_Z, e.getSource()) != null;
            padRx = axis(e, zr ? MotionEvent.AXIS_Z : MotionEvent.AXIS_RX); padRy = axis(e, zr ? MotionEvent.AXIS_RZ : MotionEvent.AXIS_RY);
            float hx = e.getAxisValue(MotionEvent.AXIS_HAT_X), hy = e.getAxisValue(MotionEvent.AXIS_HAT_Y);
            hatMask = (hx < -0.5f ? 1 << Native.LEFT : 0) | (hx > 0.5f ? 1 << Native.RIGHT : 0)
                    | (hy < -0.5f ? 1 << Native.UP : 0) | (hy > 0.5f ? 1 << Native.DOWN : 0);
            float lt = Math.max(e.getAxisValue(MotionEvent.AXIS_LTRIGGER), e.getAxisValue(MotionEvent.AXIS_BRAKE));
            float rt = Math.max(e.getAxisValue(MotionEvent.AXIS_RTRIGGER), e.getAxisValue(MotionEvent.AXIS_GAS));
            trigMask = (lt > 0.5f ? 1 << Native.L2 : 0) | (rt > 0.5f ? 1 << Native.R2 : 0);
            pushInput();
            return true;
        }
        return super.dispatchGenericMotionEvent(e);
    }

    private static int axis(MotionEvent e, int a) {
        float v = e.getAxisValue(a);
        if (Math.abs(v) < 0.12f) v = 0;
        return Math.max(-32767, Math.min(32767, Math.round(v * 32767)));
    }

    // ---------------------------------------------------------------- helpers
    /** A short message, from any thread. */
    void toast(final String s) {
        ui.post(new Runnable() { public void run() { Toast.makeText(MainActivity.this, s, Toast.LENGTH_SHORT).show(); } });
    }

    /** Calls a function on the menu page, e.g. menuJs("refresh()"), only if the page has it (it may still be loading). */
    void menuJs(final String js) {
        ui.post(new Runnable() { public void run() {
            if (menu != null) menu.evaluateJavascript("window." + js.replaceAll("\\(.*", "") + "&&" + js, null);
        }});
    }

    // ---------------------------------------------------------------- memory card
    // One card, saves/Xenogears.srm, shared by both discs. Settings > Card shows it and can format, import and export.
    File cardFile() { return new File(saveDir, "Xenogears.srm"); }

    /** Accepts raw cards (.srm/.mcr/.mcd, 128 KB) and the two common headered ones (.gme / DexDrive, VGS). */
    static byte[] normalizeCard(byte[] raw) {
        if (raw == null) return null;
        int n = 131072, off = raw.length == n ? 0 : raw.length == n + 64 ? 64 : raw.length == n + 3904 ? 3904 : -1;
        if (off < 0) return null;
        byte[] b = Arrays.copyOfRange(raw, off, off + n);
        return b[0] == 'M' && b[1] == 'C' ? b : null;
    }

    /** A freshly formatted card (the same layout psxlink.c's format_card writes). */
    static byte[] blankCard() {
        byte[] d = new byte[131072];
        int off = 0;
        d[off++] = 'M'; d[off++] = 'C'; off += 0x7d; d[off++] = 0x0e;
        for (int i = 0; i < 15; i++) { d[off++] = (byte) 0xa0; off += 7; d[off++] = (byte) 0xff; d[off++] = (byte) 0xff; off += 0x75; d[off++] = (byte) 0xa0; }
        for (int i = 0; i < 20; i++) { for (int k = 0; k < 4; k++) d[off++] = (byte) 0xff; off += 4; d[off++] = (byte) 0xff; d[off++] = (byte) 0xff; off += 0x76; }
        return d;
    }

    /** A small file's bytes (up to 1 MB), or null. */
    private static byte[] readAll(File f) {
        if (!f.isFile() || f.length() > (1 << 20)) return null;
        byte[] b = new byte[(int) f.length()];
        try (FileInputStream in = new FileInputStream(f)) { int n = 0, r; while (n < b.length && (r = in.read(b, n, b.length - n)) > 0) n += r; return b; }
        catch (Exception e) { return null; }
    }

    /** The card as the game sees it right now (live while playing, otherwise the file). */
    byte[] currentCard() {
        byte[] live = running ? Native.readMemcard() : null;
        if (live != null) return live;
        return readAll(cardFile());
    }

    /** Puts a new card in place: backs the old file up to saves/backup/, writes the file, and swaps it into a running game. */
    boolean installCard(byte[] card, String why) {
        try {
            File f = cardFile(), dir = new File(saveDir, "backup");
            dir.mkdirs();
            if (f.isFile()) {
                String ts = new java.text.SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(new java.util.Date());
                byte[] old = readAll(f);
                if (old != null) try (OutputStream o = new FileOutputStream(new File(dir, "Xenogears-" + ts + ".srm"))) { o.write(old); }
            }
            if (running) {
                final byte[] c = card;
                final boolean[] ok = { false };
                final Object lock = new Object();
                emu.post(new Runnable() { public void run() { ok[0] = Native.writeMemcard(c); synchronized (lock) { lock.notifyAll(); } } });
                synchronized (lock) { lock.wait(2000); }
                if (!ok[0]) return false;
            } else {
                try (OutputStream o = new FileOutputStream(f)) { o.write(card); }
            }
            return true;
        } catch (Exception e) { return false; }
    }

    /** For Settings > Card: whether the card exists and is formatted, blocks used, and the saves' names. */
    JSONObject cardInfo() throws Exception {
        JSONObject o = new JSONObject();
        byte[] b = currentCard();
        o.put("exists", b != null);
        boolean fmt = b != null && b.length == 131072 && b[0] == 'M' && b[1] == 'C';
        o.put("formatted", fmt);
        JSONArray saves = new JSONArray();
        int used = 0;
        if (fmt) for (int i = 1; i <= 15; i++) {
            int base = i * 128, st = b[base] & 0xff;
            if (st >= 0x51 && st <= 0x53) used++;
            if (st == 0x51) {
                StringBuilder nm = new StringBuilder();
                for (int k = 0x0a; k < 0x1e && b[base + k] != 0; k++) nm.append((char) (b[base + k] & 0x7f));
                saves.put(nm.toString());
            }
        }
        o.put("blocksUsed", used);
        o.put("saves", saves);
        o.put("file", cardFile().getAbsolutePath());
        return o;
    }

    // ---------------------------------------------------------------- save-state files
    /** states/Xenogears.slotN.state for slots 1-8; slot 0 is QUICK. Each has a .jpg picture beside it. */
    private File statePath(int slot) { return slot == 0 ? quickState() : new File(stateDir, "Xenogears.slot" + slot + ".state"); }
    File quickState() { return new File(stateDir, "Xenogears.quick.state"); }

    // ---------------------------------------------------------------- bridges
    // The two pages talk to the app through JavaScript interfaces: the menu through window.App (MenuBridge), Link through
    // window.XenoLink (LinkBridge, this app's own API) and window.Native (LinkNative, the API Link's own app gives it).
    /** window.App — launcher, settings and pause menu (assets/menu/index.html). */
    final class MenuBridge {
        // ---- what the menu shows: everything in one JSON object, re-read on every refresh()
        @JavascriptInterface public String state() {
            try {
                JSONObject o = new JSONObject();
                o.put("version", VERSION);
                o.put("storage", hasStorage());
                o.put("folder", baseDir.getAbsolutePath());
                o.put("running", running);
                o.put("gameId", gameId);
                JSONArray discs = new JSONArray();
                for (int s = 0; s < 2; s++) {
                    JSONObject d = new JSONObject();
                    String p = discPath(s);
                    d.put("path", p); d.put("name", p.isEmpty() ? "" : new File(p).getName()); d.put("ok", discOk(s));
                    discs.put(d);
                }
                o.put("discs", discs);
                o.put("bootDisc", prefs.getInt("bootDisc", 0));
                int idx = running ? Native.discIndex() : 0;
                o.put("inserted", running && idx < discSlot.length ? discSlot[idx] : -1);
                o.put("discCount", running ? Native.discCount() : 0);
                JSONArray bios = new JSONArray();
                File[] bs = sysDir.listFiles();
                if (bs != null) for (File f : bs) if (f.length() == 524288) bios.put(f.getName());
                o.put("bios", bios);
                o.put("spanned", spanned);
                o.put("secondScreen", secondDisplay() != null);
                o.put("wideScreen", wideScreen);
                o.put("linkOnPhone", linkOnPhone);
                o.put("customLink", new File(baseDir, "link/index.html").isFile());
                o.put("fastForward", emu.fastForward);
                JSONObject opts = new JSONObject();
                String[] bools = { "showAtStart:true", "touch:true", "stick:true", "stickDpad:true", "smooth:true", "integer:false",
                        "hires:false", "hleBios:false", "link:true", "swapScreens:false", "muted:false", "resume:true" };
                for (String bb : bools) { String[] kv = bb.split(":"); opts.put(kv[0], prefs.getBoolean(kv[0], Boolean.parseBoolean(kv[1]))); }
                opts.put("opacity", prefs.getInt("opacity", 55));
                opts.put("padType", prefs.getInt("padType", 0));
                opts.put("layout", layoutChoice());
                opts.put("stickThreshold", prefs.getInt("stickThreshold", 40));
                o.put("opts", opts);
                o.put("mods", modList());
                o.put("analogOn", analogOn());
                o.put("analogState", running ? Native.analogModState() : -1);
                o.put("binds", bindList());
                o.put("hotkeys", hotList());
                o.put("bindWait", bindWait);
                try { o.put("card", cardInfo()); } catch (Exception ignored) {}
                o.put("bezel", bezel.style());
                JSONArray bz = new JSONArray();
                File[] bf = new File(baseDir, "bezels").listFiles();
                if (bf != null) { Arrays.sort(bf); for (File f : bf) if (f.getName().toLowerCase(Locale.US).endsWith(".png")) bz.put(f.getName()); }
                o.put("bezels", bz);
                o.put("slots", slotList());
                o.put("quick", slotJson(quickState()));
                JSONObject r = resumeInfo();
                if (r != null) o.put("resume", r);
                return o.toString();
            } catch (Exception e) { return "{}"; }
        }

        // ---- the file picker (discs, BIOS, memory cards), storage permission, discs and BIOS
        @JavascriptInterface public String listDir(String path) {
            try {
                File dir = path == null || path.isEmpty() ? Environment.getExternalStorageDirectory() : new File(path);
                if (!dir.isDirectory()) dir = Environment.getExternalStorageDirectory();
                JSONObject o = new JSONObject();
                o.put("path", dir.getAbsolutePath());
                File parent = dir.getParentFile();
                o.put("parent", parent != null && parent.canRead() ? parent.getAbsolutePath() : "");
                File[] fs = dir.listFiles();
                JSONArray arr = new JSONArray();
                if (fs != null) {
                    Arrays.sort(fs, new Comparator<File>() { public int compare(File a, File b) {
                        if (a.isDirectory() != b.isDirectory()) return a.isDirectory() ? -1 : 1;
                        return a.getName().compareToIgnoreCase(b.getName()); } });
                    for (File f : fs) {
                        if (f.getName().startsWith(".")) continue;
                        JSONObject e = new JSONObject();
                        e.put("name", f.getName()); e.put("path", f.getAbsolutePath());
                        e.put("dir", f.isDirectory()); e.put("size", f.isDirectory() ? 0 : f.length());
                        String n = f.getName().toLowerCase(Locale.US);
                        boolean disc = false;
                        for (String x : DISC_EXT) if (n.endsWith(x)) disc = true;
                        e.put("disc", disc);
                        e.put("bios", !f.isDirectory() && f.length() == 524288);
                        long L = f.length();
                        e.put("card", !f.isDirectory() && (L == 131072 || L == 131072 + 64 || L == 131072 + 3904));
                        arr.put(e);
                    }
                }
                o.put("entries", arr);
                return o.toString();
            } catch (Exception e) { return "{\"entries\":[]}"; }
        }

        @JavascriptInterface public void requestStorage() { ui.post(new Runnable() { public void run() { MainActivity.this.requestStorage(); } }); }

        @JavascriptInterface public void setDisc(int slot, String path) {
            prefs.edit().putString(slot == 0 ? "disc1" : "disc2", path == null ? "" : path).apply();
        }

        @JavascriptInterface public void setBootDisc(int slot) { prefs.edit().putInt("bootDisc", slot).apply(); }

        @JavascriptInterface public boolean importBios(String path) {
            File src = new File(path);
            if (!src.isFile() || src.length() != 524288) return false;
            try (InputStream in = new FileInputStream(src); OutputStream out = new FileOutputStream(new File(sysDir, src.getName()))) {
                byte[] buf = new byte[65536]; int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                return true;
            } catch (Exception e) { return false; }
        }

        @JavascriptInterface public void removeBios(String name) { new File(sysDir, new File(name).getName()).delete(); }

        // ---- playing: START / CONTINUE / RESUME, back to the launcher, reset, save states, disc swap
        @JavascriptInterface public void start() { ui.post(new Runnable() { public void run() { startGame(); } }); }
        @JavascriptInterface public void continueGame() { ui.post(new Runnable() { public void run() { MainActivity.this.continueGame(); } }); }
        @JavascriptInterface public void resume() { ui.post(new Runnable() { public void run() { if (running) showMenu(false); } }); }
        @JavascriptInterface public void toLauncher() { ui.post(new Runnable() { public void run() { saveOnLeave(); stopGame(); showMenu(true); menuJs("openLauncher()"); } }); }
        @JavascriptInterface public void reset() { emu.post(new Runnable() { public void run() { Native.reset(); } }); resume(); }

        @JavascriptInterface public void saveState(final int slot) {
            emu.post(new Runnable() { public void run() {
                toast(saveSlot(statePath(slot)) ? "Saved to slot " + slot : "Save state failed");
                menuJs("refresh()");
            }});
        }

        @JavascriptInterface public void loadState(final int slot) {
            final File f = statePath(slot);
            if (!f.isFile()) { toast("Slot " + slot + " is empty"); return; }
            emu.post(new Runnable() { public void run() {
                boolean ok = Native.loadState(f.getAbsolutePath());
                if (ok) { sessionFromSave = true; devJumped = false; }
                toast(ok ? "Loaded slot " + slot : "Load state failed");
            }});
            resume();
        }

        /** Swap to Disc 1 or Disc 2 while playing. */
        @JavascriptInterface public void insertDisc(final int slot) {
            emu.post(new Runnable() { public void run() {
                int idx = discSlot[0] == slot ? 0 : 1;
                boolean ok = idx < Native.discCount() && Native.setDisc(idx);
                toast(ok ? "Disc " + (slot + 1) + " inserted" : "Pick Disc " + (slot + 1) + " in the launcher first");
                menuJs("refresh()");
            }});
        }

        // ---- settings (prefs), fast forward, rebinding and hotkeys, deleting a save state
        @JavascriptInterface public void setBool(final String key, final boolean v) {
            prefs.edit().putBoolean(key, v).apply();
            ui.post(new Runnable() { public void run() {
                applyInputOptions();
                if (key.equals("hires") || key.equals("hleBios")) applyCoreOptions();
                if (key.equals("link") || key.equals("swapScreens") || key.equals("touch")) applyLayout();
                if (key.equals("analogOn")) { applyAnalogMode(); applyMods(); }
            }});
        }

        @JavascriptInterface public void setInt(final String key, final int v) {
            prefs.edit().putInt(key, v).apply();
            ui.post(new Runnable() { public void run() {
                applyInputOptions();
                if (key.equals("padType") && running && !analogOn()) Native.setPadType(v);
                if (key.equals("layout")) applyLayout();
            }});
        }

        @JavascriptInterface public void setFastForward(boolean on) { emu.fastForward = on; }

        @JavascriptInterface public void bindStart(int bit) { bindWait = bit; }
        @JavascriptInterface public void bindCancel() { bindWait = -1; }
        @JavascriptInterface public void hotStart(int i) { bindWait = HOT_WAIT + i; }
        @JavascriptInterface public void hotClear(final int i) { ui.post(new Runnable() { public void run() { bindWait = -1; clearHot(i); menuJs("refresh()"); } }); }

        /** Deletes a save state and its picture (the pause menu asks first). 0 = QUICK. */
        @JavascriptInterface public void deleteState(final int slot) {
            ui.post(new Runnable() { public void run() {
                if (slot < 0 || slot > SLOTS) return;
                File f = statePath(slot);
                boolean ok = !f.isFile() || f.delete();
                thumbFile(f).delete();
                toast(ok ? (slot == 0 ? "Quick save deleted" : "Slot " + slot + " deleted") : "Couldn't delete that save state");
                menuJs("refresh()");
            }});
        }

        /** Settings > Card > EXPORT: the card as the game has it now, as a .srm in saves/export/ (RetroArch, DuckStation and others read it). */
        @JavascriptInterface public void exportCard() {
            ui.post(new Runnable() { public void run() {
                byte[] c = currentCard();
                if (c == null) { toast("There's no memory card yet. It's made the first time the game starts."); return; }
                try {
                    File dir = new File(saveDir, "export");
                    dir.mkdirs();
                    File f = new File(dir, "Xenogears-" + new java.text.SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(new java.util.Date()) + ".srm");
                    try (OutputStream o = new FileOutputStream(f)) { o.write(c); }
                    toast("Memory card saved as " + baseDir.getName() + "/saves/export/" + f.getName());
                } catch (Exception e) { toast("Couldn't save the memory card: " + e.getMessage()); }
            }});
        }
        @JavascriptInterface public void bindReset() { ui.post(new Runnable() { public void run() {
            bindWait = -1; binds = defaultBinds(); prefs.edit().remove("keyBinds").apply(); menuJs("refresh()"); } }); }

        // ---- the diagnostics report, memory card tools, bezels, Link on this screen, mods, quitting
        @JavascriptInterface public String diagnostics() { try { return diagnosticsReport(); } catch (Throwable t) { return "report failed: " + t; } }

        /** Memory card tools (Settings > Memory card). */
        @JavascriptInterface public void formatCard() {
            ui.post(new Runnable() { public void run() {
                toast(installCard(blankCard(), "format") ? "Memory card formatted. The old card is in saves/backup." : "Couldn't format the memory card");
                menuJs("refresh()");
            }});
        }
        @JavascriptInterface public void importCard(final String path) {
            ui.post(new Runnable() { public void run() {
                byte[] c = normalizeCard(readAll(new File(path)));
                if (c == null) { toast("That file isn't a PS1 memory card (128 KB .srm / .mcr / .mcd / .gme)"); return; }
                toast(installCard(c, "import") ? "Memory card imported. The old card is in saves/backup." : "Couldn't import the memory card");
                menuJs("refresh()");
            }});
        }

        /** off | window | a PNG in the bezels folder */
        @JavascriptInterface public void setBezel(final String style) {
            prefs.edit().putString("bezel", style).apply();
            ui.post(new Runnable() { public void run() { bezel.setStyle(style); applyLayout(); menuJs("refresh()"); } });
        }

        @JavascriptInterface public void toggleLinkOnPhone() {
            ui.post(new Runnable() { public void run() { linkOnPhone = !linkOnPhone; applyLayout(); menuJs("refresh()"); } });
        }

        @JavascriptInterface public void setMod(String id, boolean on) {
            prefs.edit().putBoolean(id, on).apply();
            ui.post(new Runnable() { public void run() { applyMods(); } });
        }

        @JavascriptInterface public boolean addMod(String name, String code) {
            try {
                if (name == null || name.trim().isEmpty() || code == null || code.trim().isEmpty()) return false;
                JSONArray user = new JSONArray(prefs.getString("userMods", "[]"));
                JSONObject m = new JSONObject();
                m.put("name", name.trim()); m.put("code", code.trim());
                user.put(m);
                prefs.edit().putString("userMods", user.toString()).putBoolean("mod:" + name.trim(), true).apply();
                ui.post(new Runnable() { public void run() { applyMods(); } });
                return true;
            } catch (Exception e) { return false; }
        }

        @JavascriptInterface public void removeMod(String name) {
            try {
                JSONArray user = new JSONArray(prefs.getString("userMods", "[]")), keep = new JSONArray();
                for (int i = 0; i < user.length(); i++) if (!user.getJSONObject(i).optString("name").equals(name)) keep.put(user.get(i));
                prefs.edit().putString("userMods", keep.toString()).remove("mod:" + name).apply();
                ui.post(new Runnable() { public void run() { applyMods(); } });
            } catch (Exception ignored) {}
        }

        @JavascriptInterface public void exitApp() { ui.post(new Runnable() { public void run() { saveOnLeave(); stopGame(); finish(); } }); }
        @JavascriptInterface public void toast(String s) { MainActivity.this.toast(s); }
    }

    /** window.XenoLink — live RAM for the Xenogears Link screen. */
    final class LinkBridge {
        @JavascriptInterface public String gameId() { return gameId; }
        @JavascriptInterface public boolean running() { return running && !emu.paused; }
        @JavascriptInterface public int disc() {
            if (!running) return 0;
            int idx = Native.discIndex();
            return (idx < discSlot.length ? discSlot[idx] : 0) + 1;
        }
        @JavascriptInterface public double frame() { return emu.frameCount; }
        @JavascriptInterface public String version() { return VERSION; }

        @JavascriptInterface public String readHex(int addr, int len) {
            byte[] b = running ? Native.readRam(addr, len) : null;
            if (b == null) return "";
            StringBuilder sb = new StringBuilder(len * 2);
            for (byte x : b) sb.append(Character.forDigit((x >> 4) & 15, 16)).append(Character.forDigit(x & 15, 16));
            return sb.toString();
        }
        @JavascriptInterface public int u8(int addr) { byte[] b = running ? Native.readRam(addr, 1) : null; return b == null ? -1 : b[0] & 0xff; }
        @JavascriptInterface public int u16(int addr) { byte[] b = running ? Native.readRam(addr, 2) : null; return b == null ? -1 : (b[0] & 0xff) | (b[1] & 0xff) << 8; }
        @JavascriptInterface public double u32(int addr) {
            byte[] b = running ? Native.readRam(addr, 4) : null;
            if (b == null) return -1;
            return (double) (((long) (b[0] & 0xff)) | ((long) (b[1] & 0xff) << 8) | ((long) (b[2] & 0xff) << 16) | ((long) (b[3] & 0xff) << 24));
        }
        @JavascriptInterface public boolean writeHex(int addr, String hex) {
            if (!running || hex == null || (hex.length() & 1) != 0) return false;
            byte[] b = new byte[hex.length() / 2];
            for (int i = 0; i < b.length; i++) b[i] = (byte) Integer.parseInt(hex.substring(i * 2, i * 2 + 2), 16);
            return Native.writeRam(addr, b);
        }

        /** Same reply text as RetroArch's UDP commands, so existing Link code keeps working. */
        @JavascriptInterface public String command(String cmd) {
            if (cmd == null) return "";
            String[] p = cmd.trim().split("\\s+");
            if (p.length == 0) return "";
            String c = p[0].toUpperCase(Locale.US);
            try {
                if ((c.equals("READ_CORE_MEMORY") || c.equals("READ_CORE_RAM")) && p.length >= 3) {
                    int addr = (int) Long.parseLong(p[1].replace("0x", ""), 16);
                    byte[] b = running ? Native.readRam(addr, Integer.parseInt(p[2])) : null;
                    if (b == null) return c + " " + p[1] + " -1";
                    StringBuilder sb = new StringBuilder(c).append(' ').append(p[1]);
                    for (byte x : b) sb.append(' ').append(Character.forDigit((x >> 4) & 15, 16)).append(Character.forDigit(x & 15, 16));
                    return sb.toString();
                }
                if ((c.equals("WRITE_CORE_MEMORY") || c.equals("WRITE_CORE_RAM")) && p.length >= 3) {
                    int addr = (int) Long.parseLong(p[1].replace("0x", ""), 16);
                    byte[] b = new byte[p.length - 2];
                    for (int i = 2; i < p.length; i++) b[i - 2] = (byte) Integer.parseInt(p[i], 16);
                    return c + " " + p[1] + " " + (running && Native.writeRam(addr, b) ? b.length : -1);
                }
                if (c.equals("GET_STATUS")) {
                    if (!running) return "GET_STATUS CONTENTLESS";
                    return "GET_STATUS " + (emu.paused ? "PAUSED" : "PLAYING") + " playstation,Xenogears,crc32=0";
                }
                if (c.equals("VERSION")) return "1.19.1";
            } catch (Exception ignored) {}
            return "";
        }
    }

    /**
     * window.Native — the same bridge Xenogears Link's Android app gives its web page, answered from the
     * emulator instead of RetroArch's UDP port. poll() replies through onMem() in the exact format of Link's
     * own Link.poll: {seq, sent, got, err, ok: {pageHex: 512 hex chars}}.
     */
    final class LinkNative {
        private File gen() { File d = new File(getFilesDir(), "gen"); d.mkdirs(); return d; }
        private File genFile(String p) throws Exception {
            if (p == null || p.contains("..") || p.startsWith("/")) throw new Exception("bad path");
            return new File(gen(), p);
        }
        private void js(final String code) {
            ui.post(new Runnable() { public void run() { if (link != null) link.evaluateJavascript(code, null); } });
        }
        private String q(String v) { return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"; }

        // ---- the single-screen layouts: which the page should draw, and its panel going in and out
        @JavascriptInterface public boolean railOn() { return railMode == 2; }
        @JavascriptInterface public boolean panelOn() { return railMode == 1; }
        @JavascriptInterface public void railDrawer(boolean open) { railDrawerOpen = open; }
        @JavascriptInterface public void railGeom(double panelW, double arrowW, double arrowH) { railPanelW = panelW; railArrowW = arrowW; railArrowH = arrowH; }

        // ---- developer tools (Link's DEV section): set the story step, warp to a room. After either, CONTINUE isn't updated (devJumped)
        @JavascriptInterface public void devStory(int step) { if (running) { devJumped = true; Native.devStory(step); } }
        @JavascriptInterface public void devWarp(int room, int door) { if (running) { devJumped = true; Native.devWarp(room, door); } }
        @JavascriptInterface public int devWarpState() { return Native.devWarpState(); }
        @JavascriptInterface public boolean devJumped() { return devJumped; }

        // ---- RAM polls and commands: what Link's own app does over RetroArch's UDP port, answered from the emulator
        @JavascriptInterface public void poll(String host, int port, final String mode, final String pagesCsv, final int seq) {
            linkIo.execute(new Runnable() { public void run() {
                String[] pages = pagesCsv == null || pagesCsv.isEmpty() ? new String[0] : pagesCsv.split(",");
                StringBuilder ok = new StringBuilder();
                int got = 0;
                String err = "";
                for (String ph : pages) {
                    try {
                        long page = Long.parseLong(ph.trim(), 16) & 0x1FFF;
                        byte[] b = running ? Native.readRam((int) (0x80000000L + (page << 8)), 256) : null;
                        if (b == null) { err = "timeout"; continue; }
                        if (ok.length() > 0) ok.append(',');
                        ok.append('"').append(Long.toHexString(page)).append("\":\"");
                        for (byte x : b) ok.append(Character.forDigit((x >> 4) & 15, 16)).append(Character.forDigit(x & 15, 16));
                        ok.append('"');
                        got++;
                    } catch (Exception e) { err = "short"; }
                }
                if (!running && pages.length > 0) {      // like a link with nothing on the other end
                    try { Thread.sleep(400); } catch (InterruptedException ignored) {}
                    err = "timeout"; got = 0; ok.setLength(0);
                }
                js("window.onMem&&onMem({seq:" + seq + ",sent:" + pages.length + ",got:" + got + ",err:\"" + err + "\",ok:{" + ok + "}})");
            }});
        }

        /** Link's FF button and other RetroArch commands. */
        @JavascriptInterface public void send(String host, int port, String cmd) {
            String c = cmd == null ? "" : cmd.trim().toUpperCase(Locale.US);
            if (c.equals("FAST_FORWARD")) emu.fastForward = !emu.fastForward;
            else if (c.equals("PAUSE_TOGGLE")) ui.post(new Runnable() { public void run() { if (running) { if (menuVisible) showMenu(false); else onMenu(); } } });
            else if (c.equals("RESET")) emu.post(new Runnable() { public void run() { Native.reset(); } });
        }

        // ---- Disc 1 for Link's room-map builder (discbuild.js): this app already knows where it is, so no file picker
        @JavascriptInterface public String discName() { return discOk(0) ? new File(discPath(0)).getName() : ""; }
        @JavascriptInterface public double discSize() { return discOk(0) ? new File(discPath(0)).length() : 0; }
        @JavascriptInterface public void discPick() {
            if (!discOk(0)) { toast("Choose Disc 1 in the launcher first"); js("window.onDiscPicked&&onDiscPicked(null)"); return; }
            File f = new File(discPath(0));
            js("window.onDiscPicked&&onDiscPicked(" + q(f.getName()) + "," + f.length() + ")");
        }
        @JavascriptInterface public String discRead(double off, int len) {
            if (len <= 0 || len > (16 << 20)) return "ERR:bad length";
            try (RandomAccessFile f = new RandomAccessFile(discPath(0), "r")) {
                byte[] b = new byte[len];
                f.seek((long) off);
                int n = 0, r;
                while (n < len && (r = f.read(b, n, len - n)) > 0) n += r;
                return Base64.encodeToString(b, 0, n, Base64.NO_WRAP);
            } catch (Exception e) { return "ERR:" + e.getClass().getSimpleName() + ": " + e.getMessage(); }
        }

        // ---- files Link builds from the disc (room maps and pictures), kept in the app's files/gen folder
        @JavascriptInterface public String genDir() { return gen().getAbsolutePath(); }
        @JavascriptInterface public boolean genHas(String p) { try { return genFile(p).isFile(); } catch (Exception e) { return false; } }
        @JavascriptInterface public String genRead(String p) {
            try {
                File f = genFile(p);
                if (!f.isFile() || f.length() > (1 << 20)) return "";
                byte[] b = new byte[(int) f.length()];
                try (FileInputStream in = new FileInputStream(f)) { int n = 0, r; while (n < b.length && (r = in.read(b, n, b.length - n)) > 0) n += r; }
                return new String(b, "UTF-8");
            } catch (Exception e) { return ""; }
        }
        @JavascriptInterface public String genWrite(String p, String b64) {
            try {
                File f = genFile(p), part = new File(f.getPath() + ".part");
                f.getParentFile().mkdirs();
                try (FileOutputStream o = new FileOutputStream(part)) { o.write(Base64.decode(b64, Base64.DEFAULT)); }
                if (!part.renameTo(f)) { f.delete(); if (!part.renameTo(f)) return "ERR:rename"; }
                return "ok";
            } catch (Exception e) { return "ERR:" + e.getMessage(); }
        }
        @JavascriptInterface public void genClear() { del(gen()); }
        private void del(File f) { File[] k = f.listFiles(); if (k != null) for (File x : k) del(x); f.delete(); }

        // ---- Link's room log (SETTINGS > DEV > ROOM LOG), and keyboard focus for its text fields
        private File roomLog() { return new File(baseDir, "link/room log.jsonl"); }
        @JavascriptInterface public String exitLog(String line) {
            try (FileOutputStream o = new FileOutputStream(roomLog(), true)) { o.write((line + "\r\n").getBytes("UTF-8")); return "ok"; }
            catch (Exception e) { return "ERR:" + e.getMessage(); }
        }
        @JavascriptInterface public void exitLogClear() { roomLog().delete(); }
        @JavascriptInterface public void exitLogShare() {
            ui.post(new Runnable() { public void run() {
                try {
                    File f = roomLog();
                    byte[] b = new byte[(int) Math.min(f.length(), 900000)];
                    try (FileInputStream in = new FileInputStream(f)) { in.read(b); }
                    Intent i = new Intent(Intent.ACTION_SEND).setType("text/plain")
                            .putExtra(Intent.EXTRA_SUBJECT, "room log.jsonl").putExtra(Intent.EXTRA_TEXT, new String(b, "UTF-8"));
                    startActivity(Intent.createChooser(i, "Share the room log"));
                } catch (Exception e) { toast("No room log yet"); }
            }});
        }
        @JavascriptInterface public void focusable(final boolean on) {
            ui.post(new Runnable() { public void run() { if (link != null && on) link.requestFocus(); } });
        }
        // ---- save states from Link's settings panel (same 4 slots as the pause menu) ----
        @JavascriptInterface public String stateInfo() {
            JSONArray a = new JSONArray();
            for (int i = 1; i <= 4; i++) { File f = statePath(i); a.put(f.isFile() ? f.lastModified() : 0); }
            return a.toString();
        }
        /** the slot's picture ("" if none), from 0.18 */
        @JavascriptInterface public String stateThumb(int slot) { return slot >= 1 && slot <= 4 && statePath(slot).isFile() ? thumbUrl(statePath(slot)) : ""; }
        @JavascriptInterface public void stateSave(final int slot) { stateOp(slot, false); }
        @JavascriptInterface public void stateLoad(final int slot) { stateOp(slot, true); }
        private void stateOp(final int slot, final boolean load) {
            if (!running || slot < 1 || slot > 4) { js("window.onStateDone&&onStateDone(" + slot + ",false,'" + (load ? "load" : "save") + "')"); return; }
            final File f = statePath(slot);
            emu.post(new Runnable() { public void run() {
                boolean ok = load ? f.isFile() && Native.loadState(f.getAbsolutePath()) : saveSlot(f);
                if (ok && load) { sessionFromSave = true; devJumped = false; }
                js("window.onStateDone&&onStateDone(" + slot + "," + ok + ",'" + (load ? "load" : "save") + "')");
                menuJs("refresh()");
            }});
        }

        // ---- Link's app watches for freezes with these; nothing to do here
        @JavascriptInterface public void beat(String stage) { }
        @JavascriptInterface public String lastHang() { return ""; }
    }
}
