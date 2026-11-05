package com.jack.xenogears;

/** Plain-Java test of Konami (no device): tests/konami/run.sh compiles it against android.jar and runs it. */
public class KonamiTest {
    static final int U = 19, D = 20, L = 21, R = 22, A = 96, B = 97, X = 99;
    static int fails = 0;
    static void check(String name, int[] keys, int[] want) {
        Konami k = new Konami(); int[] got = new int[keys.length];
        for (int i = 0; i < keys.length; i++) got[i] = k.feed(keys[i]);
        boolean ok = java.util.Arrays.equals(got, want);
        if (!ok) fails++;
        System.out.println((ok ? "PASS " : "FAIL ") + name + (ok ? "" : "  got " + java.util.Arrays.toString(got) + " want " + java.util.Arrays.toString(want)));
    }
    public static void main(String[] a) {
        int P = Konami.PASS, H = Konami.HOLD, Dn = Konami.DONE, Rl = Konami.RELEASE;
        check("the code", new int[] { U, U, D, D, L, R, L, R, B, A }, new int[] { P, P, P, P, P, P, P, P, H, Dn });
        check("an extra up first still works", new int[] { U, U, U, D, D, L, R, L, R, B, A }, new int[] { P, P, P, P, P, P, P, P, P, H, Dn });
        check("B then not A gives B back", new int[] { U, U, D, D, L, R, L, R, B, X }, new int[] { P, P, P, P, P, P, P, P, H, Rl });
        check("B then up gives B back and starts again", new int[] { U, U, D, D, L, R, L, R, B, U, U, D, D, L, R, L, R, B, A },
              new int[] { P, P, P, P, P, P, P, P, H, Rl, P, P, P, P, P, P, P, H, Dn });
        check("a wrong key part way resets", new int[] { U, U, D, X, U, U, D, D, L, R, L, R, B, A }, new int[] { P, P, P, P, P, P, P, P, P, P, P, P, H, Dn });
        check("plain B in the menu is never held", new int[] { B, B, A }, new int[] { P, P, P });
        check("twice in a row", new int[] { U, U, D, D, L, R, L, R, B, A, U, U, D, D, L, R, L, R, B, A },
              new int[] { P, P, P, P, P, P, P, P, H, Dn, P, P, P, P, P, P, P, P, H, Dn });
        System.out.println(fails == 0 ? "ALL PASS" : fails + " FAILED");
        System.exit(fails == 0 ? 0 : 1);
    }
}
