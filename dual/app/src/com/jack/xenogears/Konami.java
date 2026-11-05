package com.jack.xenogears;

import android.view.KeyEvent;

/**
 * Watches controller keys for the Konami code, ↑ ↑ ↓ ↓ ← → ← → B A, which turns Link's developer options on or off
 * (MainActivity feeds it the keys pressed while the menu is open).
 *
 * In the menu B means "back", so once the eight directions are in, B is held back (HOLD) until the next key: A
 * completes the code (DONE); anything else gives B back (RELEASE: pass on the held B, then this key).
 */
final class Konami {
    static final int[] CODE = { KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_DOWN, KeyEvent.KEYCODE_DPAD_DOWN,
            KeyEvent.KEYCODE_DPAD_LEFT, KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_DPAD_LEFT, KeyEvent.KEYCODE_DPAD_RIGHT,
            KeyEvent.KEYCODE_BUTTON_B, KeyEvent.KEYCODE_BUTTON_A };
    static final int PASS = 0, HOLD = 1, DONE = 2, RELEASE = 3;
    private int at;                                  // how much of the code has been entered

    /** One key press (key down, not a repeat): what the caller should do with it. */
    int feed(int code) {
        if (code == CODE[at]) {
            if (++at == CODE.length) { at = 0; return DONE; }
            return at == CODE.length - 1 ? HOLD : PASS;
        }
        boolean held = at == CODE.length - 1;
        // a wrong key starts again; ↑ can still start the code (and ↑ ↑ ↑ keeps the last two)
        at = code == CODE[0] ? (at == 2 ? 2 : 1) : 0;
        return held ? RELEASE : PASS;
    }
}
