package com.jack.xenogears;

import android.content.Context;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** Draws the newest core frame as a textured quad, aspect-correct. */
final class GameView extends GLSurfaceView implements GLSurfaceView.Renderer {
    private final ByteBuffer frame = ByteBuffer.allocateDirect(2048 * 1024 * 2).order(ByteOrder.nativeOrder());
    private final int[] seq = new int[1];
    private int lastSeq = -1;
    private int tex, prog, aPos, aUv, texW, texH, frameW = 0, frameH = 0;
    private int viewW, viewH;
    private FloatBuffer quad;
    volatile boolean smooth = true;
    volatile boolean alignTop = false;    // portrait pane: game at top, touch controls below
    volatile boolean integerScale = false;
    /** Where the picture may go (a bezel leaves room for its frame); null = the whole view. */
    volatile android.graphics.Rect fitArea = null;
    /** Told when the picture size or shape changes, so the bezel can follow it. */
    volatile Runnable onPictureChanged = null;

    GameView(Context c) {
        super(c);
        setEGLContextClientVersion(2);
        setRenderer(this);
        setRenderMode(RENDERMODE_CONTINUOUSLY);
        float[] v = { -1, -1, 0, 1,   1, -1, 1, 1,   -1, 1, 0, 0,   1, 1, 1, 0 };
        quad = ByteBuffer.allocateDirect(v.length * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
        quad.put(v).position(0);
    }

    // ---- GL set-up: one textured quad, RGB565 frames from the core
    @Override public void onSurfaceCreated(GL10 gl, EGLConfig cfg) {
        String vs = "attribute vec2 p; attribute vec2 t; varying vec2 v; void main(){ v=t; gl_Position=vec4(p,0.,1.); }";
        String fs = "precision mediump float; varying vec2 v; uniform sampler2D s; void main(){ gl_FragColor=texture2D(s,v); }";
        prog = GLES20.glCreateProgram();
        GLES20.glAttachShader(prog, shader(GLES20.GL_VERTEX_SHADER, vs));
        GLES20.glAttachShader(prog, shader(GLES20.GL_FRAGMENT_SHADER, fs));
        GLES20.glLinkProgram(prog);
        aPos = GLES20.glGetAttribLocation(prog, "p");
        aUv = GLES20.glGetAttribLocation(prog, "t");
        int[] t = new int[1];
        GLES20.glGenTextures(1, t, 0);
        tex = t[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tex);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT, 2);
        texW = texH = 0;
        lastSeq = -1;
    }

    private static int shader(int type, String src) {
        int s = GLES20.glCreateShader(type);
        GLES20.glShaderSource(s, src);
        GLES20.glCompileShader(s);
        return s;
    }

    @Override public void onSurfaceChanged(GL10 gl, int w, int h) { viewW = w; viewH = h; }

    // ---- drawing: the emulator runs from here
    /** The emulator runs from here: one call per screen refresh, then the frame it just made is drawn. */
    volatile Emu emu;

    @Override public void onDrawFrame(GL10 gl) {
        Emu e = emu;
        if (e != null) e.vsync();
        int wh = Native.copyFrame(frame, lastSeq, seq);
        lastSeq = seq[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tex);
        if (wh != 0) {
            int w = wh >>> 16, h = wh & 0xffff;
            frame.position(0);
            if (w != texW || h != texH) {
                GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGB, w, h, 0, GLES20.GL_RGB, GLES20.GL_UNSIGNED_SHORT_5_6_5, frame);
                texW = w; texH = h;
            } else {
                GLES20.glTexSubImage2D(GLES20.GL_TEXTURE_2D, 0, 0, 0, w, h, GLES20.GL_RGB, GLES20.GL_UNSIGNED_SHORT_5_6_5, frame);
            }
            if (w != frameW || h != frameH) { Runnable r = onPictureChanged; if (r != null) post(r); }
            frameW = w; frameH = h;
        }
        int filt = smooth ? GLES20.GL_LINEAR : GLES20.GL_NEAREST;
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, filt);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, filt);

        GLES20.glViewport(0, 0, viewW, viewH);
        GLES20.glClearColor(0, 0, 0, 1);
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
        if (texW == 0) return;

        int[] r = gameRect(viewW, viewH);
        // GL viewport origin is bottom-left
        GLES20.glViewport(r[0], viewH - r[1] - r[3], r[2], r[3]);
        GLES20.glUseProgram(prog);
        quad.position(0);
        GLES20.glVertexAttribPointer(aPos, 2, GLES20.GL_FLOAT, false, 16, quad);
        GLES20.glEnableVertexAttribArray(aPos);
        quad.position(2);
        GLES20.glVertexAttribPointer(aUv, 2, GLES20.GL_FLOAT, false, 16, quad);
        GLES20.glEnableVertexAttribArray(aUv);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
    }

    // ---- where the picture goes: aspect-correct, inside the bezel's area, optionally whole-number scaled
    /** x, y (from top), w, h of the picture inside a view of the given size. */
    int[] gameRect(int vw, int vh) {
        android.graphics.Rect a = fitArea;
        if (a != null && a.width() > 0 && a.height() > 0) {
            int[] r = fit(a.width(), a.height());
            r[0] += a.left; r[1] += a.top;
            return r;
        }
        return fit(vw, vh);
    }

    private int[] fit(int vw, int vh) {
        float aspect = Native.aspect();
        if (aspect <= 0) aspect = 4f / 3f;
        int w = vw, h = Math.round(vw / aspect);
        if (h > vh) { h = vh; w = Math.round(vh * aspect); }
        if (integerScale && frameH > 0) {
            int k = Math.max(1, h / frameH);
            if (k * frameH <= vh) { h = k * frameH; w = Math.round(h * aspect); }
        }
        int x = (vw - w) / 2;
        int y = alignTop ? 0 : (vh - h) / 2;
        return new int[] { x, y, w, h };
    }
}
