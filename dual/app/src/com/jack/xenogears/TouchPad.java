package com.jack.xenogears;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

/**
 * On-screen PlayStation pad. Portrait panes put the controls under the picture;
 * landscape panes overlay them on the sides. Supports multi-touch, an 8-way
 * d-pad and an optional left analog stick. Dragging on the picture (or any free space) works as
 * the right stick, for the analog camera; a double tap there presses R3 (camera reset).
 */
final class TouchPad extends View {
    interface Listener {
        void onPadChanged(int mask, int lx, int ly, int rx, int ry);
        void onMenu();
    }

    private static final int MENU = -1;
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), line = new Paint(Paint.ANTI_ALIAS_FLAG),
            text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Listener listener;
    boolean showStick = true;
    float opacity = 0.55f;
    int gameBottom = 0;    // in portrait, controls start below the picture

    // layout (computed in onSizeChanged)
    private float dpadX, dpadY, dpadR, faceX, faceY, faceR, btnR, stickX, stickY, stickR;
    private final RectF rL1 = new RectF(), rL2 = new RectF(), rR1 = new RectF(), rR2 = new RectF(),
            rSel = new RectF(), rStart = new RectF(), rMenu = new RectF();

    // pointer tracking
    private final int[] ptrId = new int[10];
    private final int[] ptrRole = new int[10];   // 0 none, 1 dpad, 2 face/buttons, 3 stick
    private int lastMask = 0, stickLx = 0, stickLy = 0, camRx = 0, camRy = 0, r3Pulse = 0;
    private final float[] downX = new float[10], downY = new float[10];
    private long lastCamTap = 0;
    private float camR = 1;
    private int stickPtr = -1;
    private float stickDx, stickDy;

    TouchPad(Context c) {
        super(c);
        line.setStyle(Paint.Style.STROKE);
        text.setTextAlign(Paint.Align.CENTER);
        text.setTypeface(Typeface.DEFAULT_BOLD);
        for (int i = 0; i < ptrId.length; i++) ptrId[i] = -1;
        setHapticFeedbackEnabled(true);
    }

    void setListener(Listener l) { listener = l; }

    // ---- layout: portrait puts the pad under the picture, landscape on its sides (sizes in 1/100 of the short side)
    @Override protected void onSizeChanged(int w, int h, int ow, int oh) { relayout(); }

    void relayout() {
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0) return;
        float u = Math.min(w, h) / 100f;
        boolean portrait = h > w * 1.15f;
        float top = portrait ? Math.max(gameBottom, h * 0.42f) : 0;
        float area = h - top;
        btnR = (portrait ? 7.5f : 6.5f) * u;
        dpadR = (portrait ? 17f : 15f) * u;
        faceR = dpadR;
        float sidePad = dpadR + 4 * u;
        if (portrait) {
            float shY = top + 6 * u;
            dpadX = sidePad; faceX = w - sidePad;
            dpadY = faceY = Math.min(shY + 6 * u + dpadR, h - 10 * u - dpadR);
            stickR = Math.min(10 * u, (faceX - dpadX) / 2 - dpadR - 1 * u);
            stickX = w * 0.5f; stickY = dpadY + dpadR * 0.45f;
            float bw = 17 * u, bh = 8 * u;
            rL2.set(4 * u, shY - bh / 2, 4 * u + bw, shY + bh / 2);
            rL1.set(rL2.right + 3 * u, rL2.top, rL2.right + 3 * u + bw, rL2.bottom);
            rR2.set(w - 4 * u - bw, rL2.top, w - 4 * u, rL2.bottom);
            rR1.set(rR2.left - 3 * u - bw, rL2.top, rR2.left - 3 * u, rL2.bottom);
            float sy = h - 5.5f * u;
            rSel.set(w / 2f - 21 * u, sy - 4 * u, w / 2f - 3 * u, sy + 4 * u);
            rStart.set(w / 2f + 3 * u, sy - 4 * u, w / 2f + 21 * u, sy + 4 * u);
            rMenu.set(w / 2f - 7 * u, shY - 4 * u, w / 2f + 7 * u, shY + 4 * u);
        } else {
            dpadX = sidePad; faceX = w - sidePad;
            dpadY = faceY = h * 0.62f;
            stickR = 11 * u; stickX = sidePad + 6 * u; stickY = h - stickR - 3 * u;
            if (stickY - stickR < dpadY + dpadR) { dpadY = h * 0.5f; faceY = h * 0.55f; }
            float bw = 18 * u, bh = 7 * u;
            rL2.set(3 * u, 3 * u, 3 * u + bw, 3 * u + bh);
            rL1.set(3 * u, rL2.bottom + 2 * u, 3 * u + bw, rL2.bottom + 2 * u + bh);
            rR2.set(w - 3 * u - bw, 3 * u, w - 3 * u, 3 * u + bh);
            rR1.set(w - 3 * u - bw, rR2.bottom + 2 * u, w - 3 * u, rR2.bottom + 2 * u + bh);
            rSel.set(w / 2f - 19 * u, h - 9 * u, w / 2f - 3 * u, h - 3 * u);
            rStart.set(w / 2f + 3 * u, h - 9 * u, w / 2f + 19 * u, h - 3 * u);
            rMenu.set(w / 2f - 6 * u, 2 * u, w / 2f + 6 * u, 8 * u);
        }
        camR = 14 * u;
        text.setTextSize(4.2f * u);
        line.setStrokeWidth(Math.max(2, 0.5f * u));
        invalidate();
    }

    // ---- drawing: pressed buttons light up
    @Override protected void onDraw(Canvas c) {
        int a = (int) (255 * opacity);
        // d-pad
        drawDpad(c, a);
        // face buttons (triangle top, circle right, cross bottom, square left)
        float o = faceR * 0.6f;
        face(c, faceX, faceY - o, "△", 0x4FD8B0, Native.TRIANGLE, a);
        face(c, faceX + o, faceY, "○", 0xFF6B7A, Native.CIRCLE, a);
        face(c, faceX, faceY + o, "✕", 0x7FA8FF, Native.CROSS, a);
        face(c, faceX - o, faceY, "□", 0xF59BD6, Native.SQUARE, a);
        pill(c, rL1, "L1", Native.L, a); pill(c, rL2, "L2", Native.L2, a);
        pill(c, rR1, "R1", Native.R, a); pill(c, rR2, "R2", Native.R2, a);
        pill(c, rSel, "SELECT", Native.SELECT, a); pill(c, rStart, "START", Native.START, a);
        pill(c, rMenu, "≡", -1, a);
        if (showStick) {
            fill.setColor(0x202833); fill.setAlpha(a);
            c.drawCircle(stickX, stickY, stickR, fill);
            line.setColor(0xFFFFFF); line.setAlpha(a / 2);
            c.drawCircle(stickX, stickY, stickR, line);
            fill.setColor(0x9AA7B8); fill.setAlpha(a);
            c.drawCircle(stickX + stickDx * stickR * 0.6f, stickY + stickDy * stickR * 0.6f, stickR * 0.45f, fill);
        }
    }

    private void drawDpad(Canvas c, int a) {
        float s = dpadR * 0.36f;
        int[][] dirs = { {0, -1, Native.UP}, {0, 1, Native.DOWN}, {-1, 0, Native.LEFT}, {1, 0, Native.RIGHT} };
        for (int[] d : dirs) {
            boolean on = (lastMask & (1 << d[2])) != 0;
            fill.setColor(on ? 0x6E7C90 : 0x2A313C); fill.setAlpha(a);
            float cx = dpadX + d[0] * dpadR * 0.62f, cy = dpadY + d[1] * dpadR * 0.62f;
            c.drawRoundRect(new RectF(cx - s, cy - s, cx + s, cy + s), s * 0.3f, s * 0.3f, fill);
        }
        fill.setColor(0x2A313C); fill.setAlpha(a);
        c.drawRect(dpadX - s, dpadY - s, dpadX + s, dpadY + s, fill);
    }

    private void face(Canvas c, float x, float y, String glyph, int color, int bit, int a) {
        boolean on = (lastMask & (1 << bit)) != 0;
        fill.setColor(on ? 0x58657A : 0x22293A); fill.setAlpha(a);
        c.drawCircle(x, y, btnR, fill);
        text.setColor(color); text.setAlpha(Math.min(255, a + 60));
        c.drawText(glyph, x, y + text.getTextSize() * 0.36f, text);
    }

    private void pill(Canvas c, RectF r, String label, int bit, int a) {
        boolean on = bit >= 0 && (lastMask & (1 << bit)) != 0;
        fill.setColor(on ? 0x58657A : 0x22293A); fill.setAlpha(a);
        c.drawRoundRect(r, r.height() / 2, r.height() / 2, fill);
        text.setColor(0xDDE6F2); text.setAlpha(Math.min(255, a + 60));
        float ts = text.getTextSize();
        if (label.length() > 3) text.setTextSize(ts * 0.75f);
        c.drawText(label, r.centerX(), r.centerY() + text.getTextSize() * 0.36f, text);
        text.setTextSize(ts);
    }

    // ---- hit testing: which part a finger went down on (1 d-pad, 2 buttons, 3 stick, 4 camera)
    private int hit(float x, float y) {
        float dx = x - dpadX, dy = y - dpadY;
        if (dx * dx + dy * dy < dpadR * dpadR * 1.3f) return 1;
        if (showStick) { dx = x - stickX; dy = y - stickY; if (dx * dx + dy * dy < stickR * stickR * 1.6f) return 3; }
        if (gameBottom > 0 && y < gameBottom - 4) return 4;           // on the picture: camera
        if (buttonsAt(x, y) != 0 || near(x, y, faceX, faceY, faceR * 1.3f)) return 2;
        return 4;                                                      // free space: camera
    }

    private int buttonsAt(float x, float y) {
        int m = 0;
        float o = faceR * 0.6f, rr = btnR * 1.35f;
        if (near(x, y, faceX, faceY - o, rr)) m |= 1 << Native.TRIANGLE;
        if (near(x, y, faceX + o, faceY, rr)) m |= 1 << Native.CIRCLE;
        if (near(x, y, faceX, faceY + o, rr)) m |= 1 << Native.CROSS;
        if (near(x, y, faceX - o, faceY, rr)) m |= 1 << Native.SQUARE;
        if (grow(rL1).contains(x, y)) m |= 1 << Native.L;
        if (grow(rL2).contains(x, y)) m |= 1 << Native.L2;
        if (grow(rR1).contains(x, y)) m |= 1 << Native.R;
        if (grow(rR2).contains(x, y)) m |= 1 << Native.R2;
        if (grow(rSel).contains(x, y)) m |= 1 << Native.SELECT;
        if (grow(rStart).contains(x, y)) m |= 1 << Native.START;
        return m;
    }

    private RectF grow(RectF r) { float g = r.height() * 0.3f; return new RectF(r.left - g, r.top - g, r.right + g, r.bottom + g); }
    private static boolean near(float x, float y, float cx, float cy, float r) { float dx = x - cx, dy = y - cy; return dx * dx + dy * dy < r * r; }

    private int dpadAt(float x, float y) {
        float dx = (x - dpadX) / dpadR, dy = (y - dpadY) / dpadR, t = 0.3f;
        int m = 0;
        if (dx < -t) m |= 1 << Native.LEFT;
        if (dx > t) m |= 1 << Native.RIGHT;
        if (dy < -t) m |= 1 << Native.UP;
        if (dy > t) m |= 1 << Native.DOWN;
        return m;
    }

    // ---- touches: each finger keeps the part it went down on until it lifts; the result goes to the listener
    @Override public boolean onTouchEvent(MotionEvent e) {
        int act = e.getActionMasked();
        int idx = e.getActionIndex();
        if (act == MotionEvent.ACTION_DOWN || act == MotionEvent.ACTION_POINTER_DOWN) {
            float x = e.getX(idx), y = e.getY(idx);
            if (grow(rMenu).contains(x, y)) { if (listener != null) listener.onMenu(); return true; }
            int slot = freeSlot();
            if (slot >= 0) {
                ptrId[slot] = e.getPointerId(idx);
                ptrRole[slot] = hit(x, y);
                downX[slot] = x; downY[slot] = y;
                if (ptrRole[slot] == 3) stickPtr = ptrId[slot];
                if (ptrRole[slot] == 4) {
                    long now = System.currentTimeMillis();
                    if (now - lastCamTap < 300) pulseR3();
                    lastCamTap = now;
                }
            }
        } else if (act == MotionEvent.ACTION_UP || act == MotionEvent.ACTION_POINTER_UP || act == MotionEvent.ACTION_CANCEL) {
            int id = e.getPointerId(idx);
            for (int i = 0; i < ptrId.length; i++) {
                if (act == MotionEvent.ACTION_CANCEL || ptrId[i] == id) {
                    if (ptrId[i] == stickPtr) { stickPtr = -1; stickDx = stickDy = 0; }
                    ptrId[i] = -1; ptrRole[i] = 0;
                }
            }
        }
        int mask = r3Pulse;
        int lx = 0, ly = 0, rx = 0, ry = 0;
        for (int i = 0; i < ptrId.length; i++) {
            if (ptrId[i] < 0) continue;
            int pi = e.findPointerIndex(ptrId[i]);
            if (pi < 0) continue;
            if ((act == MotionEvent.ACTION_UP || act == MotionEvent.ACTION_POINTER_UP) && pi == idx) continue;
            float x = e.getX(pi), y = e.getY(pi);
            if (ptrRole[i] == 1) mask |= dpadAt(x, y);
            else if (ptrRole[i] == 2) mask |= buttonsAt(x, y);
            else if (ptrRole[i] == 3) {
                float dx = (x - stickX) / stickR, dy = (y - stickY) / stickR;
                float len = (float) Math.sqrt(dx * dx + dy * dy);
                if (len > 1) { dx /= len; dy /= len; }
                stickDx = dx; stickDy = dy;
                lx = Math.round(dx * 32767); ly = Math.round(dy * 32767);
            } else if (ptrRole[i] == 4) {
                float dx = (x - downX[i]) / camR, dy = (y - downY[i]) / camR;
                float len = (float) Math.sqrt(dx * dx + dy * dy);
                if (len > 1) { dx /= len; dy /= len; }
                rx = Math.round(dx * 32767); ry = Math.round(dy * 32767);
            }
        }
        if ((mask & ~lastMask) != 0) performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY);
        boolean changed = mask != lastMask || lx != stickLx || ly != stickLy || rx != camRx || ry != camRy;
        lastMask = mask; stickLx = lx; stickLy = ly; camRx = rx; camRy = ry;
        if (changed) {
            if (listener != null) listener.onPadChanged(mask, lx, ly, rx, ry);
            invalidate();
        }
        return true;
    }

    /** Holds R3 for a few frames: a tap of R3 puts the room's camera tilt and zoom back. */
    private void pulseR3() {
        r3Pulse = 1 << Native.R3;
        if (listener != null) listener.onPadChanged(lastMask | r3Pulse, stickLx, stickLy, camRx, camRy);
        postDelayed(new Runnable() { public void run() {
            r3Pulse = 0;
            if (listener != null) listener.onPadChanged(lastMask & ~(1 << Native.R3), stickLx, stickLy, camRx, camRy);
        }}, 120);
    }

    private int freeSlot() { for (int i = 0; i < ptrId.length; i++) if (ptrId[i] < 0) return i; return -1; }
}
