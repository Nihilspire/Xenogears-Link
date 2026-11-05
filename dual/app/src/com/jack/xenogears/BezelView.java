package com.jack.xenogears;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Region;
import android.graphics.Shader;
import android.view.View;

import java.io.File;
import java.io.InputStream;

/**
 * Bezel around the game picture, drawn over the GL view with a hole where the picture is.
 *  - "window": the game's own menu window frame (Link's img/frame.png, nine-sliced like its CSS
 *    border-image: 64px slices, border 10 game pixels) on Link's dark backdrop.
 *  - any other value: a PNG from the Xenogears/bezels folder, stretched to the screen; its transparent
 *    middle becomes the picture area.
 */
final class BezelView extends View {
    private final GameView game;
    private String style = "off";
    private Bitmap frame, custom;
    private Rect customHole;               // in bitmap pixels
    private final Paint paint = new Paint(Paint.FILTER_BITMAP_FLAG);
    private final Paint back = new Paint();
    private File folder;

    BezelView(Context c, GameView game) {
        super(c);
        this.game = game;
        setWillNotDraw(false);
        try (InputStream in = c.getAssets().open("link/img/frame.png")) { frame = BitmapFactory.decodeStream(in); } catch (Exception ignored) {}
    }

    void setFolder(File f) { folder = f; }
    String style() { return style; }

    /** off | window | <file name in the bezels folder> */
    void setStyle(String s) {
        style = s == null ? "off" : s;
        custom = null; customHole = null;
        if (!style.equals("off") && !style.equals("window") && folder != null) {
            File f = new File(folder, style);
            Bitmap b = f.isFile() ? BitmapFactory.decodeFile(f.getAbsolutePath()) : null;
            if (b != null) { custom = b; customHole = findHole(b); } else style = "window";
        }
        setVisibility(style.equals("off") ? GONE : VISIBLE);
        requestLayout();
        invalidate();
    }

    // ---- the picture's area inside the bezel
    /** Border thickness for the window frame: 10 game pixels at the picture's scale. */
    int border(int w, int h) {
        float scale = Math.min(w / 320f, h / 240f);
        return Math.max(6, Math.round(10 * scale));
    }

    /** The area the picture may use inside a pane of this size (null = whole pane). */
    Rect pictureArea(int w, int h, boolean alignTop) {
        if (style.equals("off") || w <= 0 || h <= 0) return null;
        if (custom != null && customHole != null) {
            float sx = w / (float) custom.getWidth(), sy = h / (float) custom.getHeight();
            return new Rect(Math.round(customHole.left * sx), Math.round(customHole.top * sy),
                    Math.round(customHole.right * sx), Math.round(customHole.bottom * sy));
        }
        int b = border(w, h);
        return new Rect(b, b, w - b, h - b);
    }

    /** Bounding box of the transparent middle of a bezel PNG. */
    private static Rect findHole(Bitmap b) {
        int w = b.getWidth(), h = b.getHeight(), cx = w / 2, cy = h / 2;
        if (Color.alpha(b.getPixel(cx, cy)) > 64) return null;
        int l = cx, r = cx, t = cy, d = cy;
        while (l > 0 && Color.alpha(b.getPixel(l - 1, cy)) <= 64) l--;
        while (r < w - 1 && Color.alpha(b.getPixel(r + 1, cy)) <= 64) r++;
        while (t > 0 && Color.alpha(b.getPixel(cx, t - 1)) <= 64) t--;
        while (d < h - 1 && Color.alpha(b.getPixel(cx, d + 1)) <= 64) d++;
        return new Rect(l, t, r + 1, d + 1);
    }

    // ---- drawing: a custom PNG stretched over the pane, or the backdrop plus the game's window frame (nine-sliced)
    @SuppressWarnings("deprecation")
    @Override protected void onDraw(Canvas c) {
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0 || style.equals("off")) return;
        if (custom != null) {
            c.drawBitmap(custom, null, new Rect(0, 0, w, h), paint);
            return;
        }
        int[] g = game.gameRect(w, h);
        Rect pic = new Rect(g[0], g[1], g[0] + g[2], g[1] + g[3]);
        // backdrop everywhere except the picture
        c.save();
        c.clipRect(pic, Region.Op.DIFFERENCE);
        back.setShader(new RadialGradient(w * 0.5f, h * 0.3f, Math.max(w, h) * 0.8f,
                new int[] { 0xFF1A1A3A, 0xFF0B0B1C, 0xFF050509 }, new float[] { 0f, 0.55f, 1f }, Shader.TileMode.CLAMP));
        c.drawRect(0, 0, w, h, back);
        c.restore();
        if (frame == null) return;
        // the game's window frame around the picture (border-image: 64px slices, no fill)
        int b = border(w, h), s = 64, fw = frame.getWidth(), fh = frame.getHeight();
        int L = pic.left - b, T = pic.top - b, R = pic.right + b, B = pic.bottom + b;
        int over = Math.max(1, b / 5);                       // like Link's -2rem inset: frame edge laps the picture slightly
        L += over; T += over; R -= over; B -= over;
        drawPart(c, 0, 0, s, s, L, T, L + b, T + b);
        drawPart(c, fw - s, 0, fw, s, R - b, T, R, T + b);
        drawPart(c, 0, fh - s, s, fh, L, B - b, L + b, B);
        drawPart(c, fw - s, fh - s, fw, fh, R - b, B - b, R, B);
        drawPart(c, s, 0, fw - s, s, L + b, T, R - b, T + b);
        drawPart(c, s, fh - s, fw - s, fh, L + b, B - b, R - b, B);
        drawPart(c, 0, s, s, fh - s, L, T + b, L + b, B - b);
        drawPart(c, fw - s, s, fw, fh - s, R - b, T + b, R, B - b);
    }

    private void drawPart(Canvas c, int sl, int st, int sr, int sb, int dl, int dt, int dr, int db) {
        if (dr <= dl || db <= dt) return;
        c.drawBitmap(frame, new Rect(sl, st, sr, sb), new RectF(dl, dt, dr, db), null);
    }
}
