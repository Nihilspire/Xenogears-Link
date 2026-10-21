package com.dualscreen.xenogears;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

/** RetroArch network-command reader. Plain Java so it can be tested off-device. */
public final class Link {
    private Link() {}

    public static String fail(int seq, String err) {
        return "{seq:" + seq + ",sent:0,got:0,err:\"" + err + "\",ok:{}}";
    }

    /**
     * Reads 256-byte memory pages. mode: m80 = READ_CORE_MEMORY at 0x80000000+offset, m00 = READ_CORE_MEMORY
     * at offset, ram = READ_CORE_RAM at offset. All requests go out first and replies are collected after,
     * so one poll costs about one emulator frame. Returns a JS object literal for onMem().
     */
    public static String poll(DatagramSocket s, String host, int port, String mode, String pagesCsv, int seq) throws Exception {
        StringBuilder ok = new StringBuilder();
        int sent = 0, got = 0; String err = "";
        InetAddress a = InetAddress.getByName(host);
        byte[] buf = new byte[4096];
        s.setSoTimeout(1); // drop stale replies from an earlier poll
        try { for (int drain = 0; drain < 500; drain++) s.receive(new DatagramPacket(buf, buf.length)); } catch (java.net.SocketTimeoutException e) { }   // at most 500, in case something keeps sending
        String cmd = mode.equals("ram") ? "READ_CORE_RAM" : "READ_CORE_MEMORY";
        long base = mode.equals("m80") ? 0x80000000L : 0L;
        String[] pages = pagesCsv.length() == 0 ? new String[0] : pagesCsv.split(",");
        for (String p : pages) {
            long addr = base + (Long.parseLong(p, 16) << 8);
            byte[] d = (cmd + " " + Long.toHexString(addr) + " 256\n").getBytes("US-ASCII");
            s.send(new DatagramPacket(d, d.length, a, port));
            sent++;
        }
        long deadline = System.currentTimeMillis() + 400;
        while (got < sent) {
            long left = deadline - System.currentTimeMillis();
            if (left <= 0) break;
            s.setSoTimeout((int) left);
            DatagramPacket r = new DatagramPacket(buf, buf.length);
            try { s.receive(r); } catch (java.net.SocketTimeoutException e) { break; }
            String t = new String(r.getData(), 0, r.getLength(), "US-ASCII").trim();
            String[] f = t.split("\\s+");
            if (f.length < 3 || !f[0].equals(cmd)) continue;
            if (f[2].equals("-1")) { err = "refused"; got++; continue; }
            long addr;
            try { addr = Long.parseLong(f[1], 16); } catch (NumberFormatException e) { continue; }
            long page = ((addr - base) & 0x1FFFFFL) >> 8;
            StringBuilder hex = new StringBuilder(512);
            for (int i = 2; i < f.length; i++) { if (f[i].length() == 1) hex.append('0'); hex.append(f[i]); }
            if (hex.length() != 512) { err = "short"; got++; continue; }
            if (ok.length() > 0) ok.append(',');
            ok.append('"').append(Long.toHexString(page)).append("\":\"").append(hex).append('"');
            got++;
        }
        if (got == 0 && sent > 0) err = "timeout";
        return "{seq:" + seq + ",sent:" + sent + ",got:" + got + ",err:\"" + err + "\",ok:{" + ok + "}}";
    }
}
