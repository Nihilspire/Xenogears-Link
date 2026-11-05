package com.jack.xenogears;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * Drives the core from the display's vsync (GameView.onDrawFrame calls vsync() once per screen refresh).
 *
 * On a ~60 Hz screen exactly one emulated frame runs per refresh and is drawn straight away, so every
 * frame is shown for the same time. Sound never sets the pace: it is written without blocking and
 * resampled by a fraction of a percent (dynamic rate control, like RetroArch) to keep the audio buffer
 * near its target, which hides the 59.94 vs 60 Hz difference without crackles or drift.
 * On screens that aren't ~60 Hz, a time accumulator decides how many frames to run per refresh.
 */
final class Emu {
    interface Listener { void onCoreMessage(String msg); }

    private final ConcurrentLinkedQueue<Runnable> queue = new ConcurrentLinkedQueue<>();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final Object lock = new Object();
    private volatile boolean active;
    volatile boolean paused;
    volatile boolean fastForward;
    volatile boolean muted;
    volatile long frameCount;
    volatile float displayHz = 60f;
    private Listener listener;

    // pacing
    private double frameNs = 1e9 / 59.94;
    private long lastVsync = 0;
    private double acc = 0;
    // audio
    private AudioTrack track;
    private int rate = 44100;
    private long written = 0;          // frames handed to the AudioTrack
    private int targetFill;            // frames we try to keep queued (~64 ms)
    private final short[] in = new short[16384];
    private short[] out = new short[24000];
    private double resPos = 0;         // resampler phase carried between chunks
    private short lastL, lastR;
    // misc
    private final int[] msgSeq = new int[1];
    private long lastHash;
    private int hashStable;

    // ---- running work between frames
    void setListener(Listener l) { listener = l; }
    boolean isRunning() { return active; }

    /** Runs r between frames; runs it at once when the frame loop isn't ticking (stopped, or the screen is off). */
    void post(Runnable r) {
        if (active && now() - lastVsync < 150_000_000L) { queue.add(r); return; }
        synchronized (lock) { safeRun(r); }
    }

    /** Runs r now, between frames, and returns once it's done. For onPause: the GL thread has just stopped,
     *  so anything post() queued wouldn't run until the app came back (or never, if Android kills it). */
    void runNow(Runnable r) {
        synchronized (lock) {
            Runnable q;
            while ((q = queue.poll()) != null) safeRun(q);
            safeRun(r);
        }
    }

    private static void safeRun(Runnable r) {
        try { r.run(); } catch (Throwable t) { Log.e("XenoLink", "emu task failed", t); }
    }

    // ---- starting and stopping (sound output, pacing, the card's change check)
    void start() {
        synchronized (lock) {
            if (active) return;
            frameNs = 1e9 / Native.fps();
            rate = (int) Math.round(Native.sampleRate());
            int min = AudioTrack.getMinBufferSize(rate, AudioFormat.CHANNEL_OUT_STEREO, AudioFormat.ENCODING_PCM_16BIT);
            int bufFrames = Math.max(min / 4, rate / 8);                 // ~125 ms of room
            targetFill = Math.max(rate * 64 / 1000, min / 4 / 2 + rate / 100);
            try {
                track = new AudioTrack(AudioManager.STREAM_MUSIC, rate, AudioFormat.CHANNEL_OUT_STEREO,
                        AudioFormat.ENCODING_PCM_16BIT, bufFrames * 4, AudioTrack.MODE_STREAM);
                track.play();
            } catch (Throwable t) { Log.e("XenoLink", "audio init failed", t); track = null; }
            written = 0; resPos = 0; acc = 0; lastVsync = 0;
            lastHash = Native.memcardHash(); hashStable = 0;
            active = true;
        }
    }

    void stop() {
        synchronized (lock) {
            active = false;
            Runnable r;
            while ((r = queue.poll()) != null) safeRun(r);
            if (track != null) { try { track.pause(); track.flush(); track.release(); } catch (Throwable ignored) {} track = null; }
            Native.saveMemcard();
        }
    }

    /** Tests can drive time themselves; -1 = real clock. */
    static volatile long testClockNs = -1;
    private static long now() { long t = testClockNs; return t >= 0 ? t : System.nanoTime(); }

    // ---- the frame loop
    /** Called on the GL thread once per screen refresh, just before the newest frame is drawn. */
    void vsync() {
        long now = now();
        synchronized (lock) {
            long prev = lastVsync;
            lastVsync = now;
            if (!active) return;
            Runnable r;
            while ((r = queue.poll()) != null) safeRun(r);
            if (paused) {
                if (track != null && track.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) { track.pause(); track.flush(); written = 0; }
                Native.readAudio(in);                                   // keep the core's buffer from filling up
                acc = 0;
                return;
            }
            if (track != null && track.getPlayState() != AudioTrack.PLAYSTATE_PLAYING) { track.play(); written = 0; }

            int frames;
            if (fastForward) frames = 3;
            else if (displayHz > 58f && displayHz < 62f) frames = 1;    // one game frame per refresh
            else {
                double dt = prev == 0 ? frameNs : Math.min(now - prev, 4 * frameNs);
                acc += dt;
                frames = 0;
                while (acc >= frameNs && frames < 4) { acc -= frameNs; frames++; }
            }
            for (int i = 0; i < frames; i++) {
                Native.runFrame();
                frameCount++;
                pumpAudio(!fastForward && !muted);
            }
            housekeeping();
        }
    }

    // ---- sound and housekeeping
    /** Moves this frame's sound to the AudioTrack, nudging the playback rate to hold the buffer near its target. */
    private void pumpAudio(boolean play) {
        int n = Native.readAudio(in);                                   // interleaved stereo shorts
        if (n <= 0) return;
        if (!play || track == null) return;
        int inFrames = n / 2;
        long head = track.getPlaybackHeadPosition() & 0xffffffffL;
        long fill = written - head;
        if (fill < 0) { fill = 0; written = head; }
        if (fill > targetFill * 3L) return;                              // way ahead (after a stall): drop this chunk
        // > 1 when the buffer is low (make a little more sound), < 1 when it's high; at most +/-0.5%
        double ratio = 1.0 + 0.005 * Math.max(-1.0, Math.min(1.0, (targetFill - fill) / (double) targetFill));
        double step = 1.0 / ratio;
        int maxOut = (int) (inFrames * ratio) + 4;
        if (out.length < maxOut * 2) out = new short[maxOut * 2];
        int o = 0;
        double pos = resPos;
        while (pos < inFrames && o < maxOut) {
            int i0 = (int) Math.floor(pos);                             // -1 = last sample of the previous chunk
            double f = pos - i0;
            short l0 = i0 < 0 ? lastL : in[i0 * 2], r0 = i0 < 0 ? lastR : in[i0 * 2 + 1];
            int i1 = Math.min(i0 + 1, inFrames - 1);
            short l1 = in[i1 * 2], r1 = in[i1 * 2 + 1];
            out[o * 2] = (short) (l0 + (l1 - l0) * f);
            out[o * 2 + 1] = (short) (r0 + (r1 - r0) * f);
            o++;
            pos += step;
        }
        resPos = pos - inFrames;
        lastL = in[(inFrames - 1) * 2]; lastR = in[(inFrames - 1) * 2 + 1];
        int w = track.write(out, 0, o * 2, AudioTrack.WRITE_NON_BLOCKING);
        if (w > 0) written += w / 2;
    }

    /** Every 30 frames: pass on the core's messages. Every 180: save the memory card once its writes have settled. */
    private void housekeeping() {
        if ((frameCount % 30) == 0 && listener != null) {
            final String m = Native.pollMessage(msgSeq);
            if (m != null) ui.post(new Runnable() { public void run() { listener.onCoreMessage(m); } });
        }
        if ((frameCount % 180) == 0) {                                  // memory card autosave once writes settle
            long h = Native.memcardHash();
            if (h != lastHash) { lastHash = h; hashStable = 0; }
            else if (hashStable == 0 && h != 0) { Native.saveMemcard(); hashStable = 1; }
        }
    }
}
