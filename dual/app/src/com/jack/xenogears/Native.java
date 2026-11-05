package com.jack.xenogears;

import java.nio.ByteBuffer;

/** JNI surface of libxenolink.so (see jni/psxlink.c), which hosts the pcsx_rearmed core (libpcsx_rearmed.so). */
final class Native {
    static {
        System.loadLibrary("pcsx_rearmed");
        System.loadLibrary("xenolink");
    }
    private Native() {}

    // ---- start-up and core options
    static native void init(String systemDir, String saveDir);
    static native void setVariable(String key, String value);

    // ---- the game: load, run one frame, timing, picture, sound
    static native boolean loadGame(String path, String memcardPath, int padType);
    static native void setPadType(int padType);
    static native void runFrame();
    static native double fps();
    static native double sampleRate();
    static native float aspect();
    static native int copyFrame(ByteBuffer dst, int lastSeq, int[] seqOut);
    static native int readAudio(short[] out);
    static native void unload();

    // ---- input (port 0 and 1): buttons as a bit mask, sticks -32767..32767
    static native void setButtons(int port, int mask);
    static native void setAxes(int port, int lx, int ly, int rx, int ry);
    static native void setStickDpad(boolean on, int threshold);

    // ---- RAM for Link, the disc's ID, the core's on-screen messages
    static native byte[] readRam(int addr, int len);
    static native boolean writeRam(int addr, byte[] data);
    static native String gameId();
    static native String pollMessage(int[] seq);

    // ---- developer tools: story step, warp (see psxlink.c); devWarpState 0 idle, 1 waiting, 2 done, 3 gave up
    static native void devStory(int step);
    static native void devWarp(int room, int door);
    static native int devWarpState();

    // ---- memory card and save states
    static native boolean saveMemcard();
    static native long memcardHash();
    static native int cardStatus();
    static native byte[] readMemcard();
    static native boolean writeMemcard(byte[] data);
    static native boolean saveState(String path);
    /** The state as bytes (same contents saveState writes), for writing on another thread; null on failure. */
    static native byte[] stateBytes();
    static native boolean loadState(String path);
    static native void reset();

    // ---- GameShark codes (mods)
    static native void setCheat(int index, boolean enabled, String code);
    static native void clearCheats();

    // ---- discs: queued with appendDisc at start, swapped with setDisc
    static native int discCount();
    static native int discIndex();
    static native boolean setDisc(int index);
    static native int appendDisc(String path);

    // ---- analog controls
    /** Analog controls program (bytes from 0x80017400), master switch and option bits; installed by the frontend. */
    static native void setAnalogMod(byte[] program, boolean on, int options);
    /** 0 off, 1 waiting for the game, 2 running, 3 stood down (the game had data where the program goes) */
    static native int analogModState();
    /** Plain-text report of the emulator, the analog installer and the card (MainActivity.diagnosticsReport). */
    static native String diagnostics();

    // ---- in the library but not used by the app (tests/drive.c uses some of them)
    static native int audioQueued();
    static native String gameLabel();
    static native boolean addDisc(String path);
    static native void setAnalogMode(boolean on);

    // libretro joypad bit ids
    static final int B = 0, Y = 1, SELECT = 2, START = 3, UP = 4, DOWN = 5, LEFT = 6, RIGHT = 7,
            A = 8, X = 9, L = 10, R = 11, L2 = 12, R2 = 13, L3 = 14, R3 = 15;
    // PlayStation names for the same bits
    static final int CROSS = B, SQUARE = Y, CIRCLE = A, TRIANGLE = X;
}
