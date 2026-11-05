package com.jack.xenogears;

import android.app.Activity;
import android.content.Context;
import android.graphics.Rect;
import android.os.Build;
import android.view.View;

import java.util.List;

/** Finds the Surface Duo hinge in window coordinates, or null when the window isn't spanned. */
final class Duo {
    private Duo() {}

    /** A Surface Duo (or Duo 2), by its maker and model name. */
    static boolean isDuo() {
        return Build.MANUFACTURER != null && Build.MANUFACTURER.toLowerCase().contains("microsoft")
                && Build.MODEL != null && Build.MODEL.toLowerCase().contains("duo");
    }

    /** The hinge from Microsoft's DisplayMask library (by reflection, as it's only on Duos), else a centred guess on a Duo. */
    @SuppressWarnings("unchecked")
    static Rect hingeInWindow(Activity a) {
        View root = a.getWindow().getDecorView();
        int w = root.getWidth(), h = root.getHeight();
        if (w == 0 || h == 0) return null;
        int[] loc = new int[2];
        root.getLocationOnScreen(loc);
        Rect win = new Rect(loc[0], loc[1], loc[0] + w, loc[1] + h);

        Rect hinge = null;
        try {
            Class<?> dm = Class.forName("com.microsoft.device.display.DisplayMask");
            Object mask = dm.getMethod("fromResourcesRect", Context.class).invoke(null, a);
            int rot = a.getWindowManager().getDefaultDisplay().getRotation();
            List<Rect> rects = (List<Rect>) dm.getMethod("getBoundingRectsForRotation", int.class).invoke(mask, rot);
            if (rects != null && !rects.isEmpty()) hinge = new Rect(rects.get(0));
        } catch (Throwable ignored) { }

        if (hinge == null && isDuo()) {
            // Fallback for builds without the DisplayMask library: assume a centred hinge.
            int gap = Build.MODEL.contains("2") ? 66 : 84;
            android.util.DisplayMetrics dmx = new android.util.DisplayMetrics();
            a.getWindowManager().getDefaultDisplay().getRealMetrics(dmx);
            int sw = dmx.widthPixels, sh = dmx.heightPixels;
            if (sw > sh) hinge = new Rect((sw - gap) / 2, 0, (sw + gap) / 2, sh);
            else hinge = new Rect(0, (sh - gap) / 2, sw, (sh + gap) / 2);
        }
        if (hinge == null || !Rect.intersects(hinge, win)) return null;
        // window must reach across the hinge on both sides to count as spanned
        boolean vertical = hinge.height() >= hinge.width();
        if (vertical && !(win.left < hinge.left && win.right > hinge.right)) return null;
        if (!vertical && !(win.top < hinge.top && win.bottom > hinge.bottom)) return null;
        hinge.offset(-loc[0], -loc[1]);
        return hinge;
    }
}
