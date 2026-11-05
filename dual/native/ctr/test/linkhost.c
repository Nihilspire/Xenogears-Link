/* linkhost.c - the Link screen on the PC, from a RAM dump, for quick looks without Azahar (linkhost_build.sh).
 *   linkhost RAM.bin PAK FONT.bin OUT.ppm [tap x y]...   each tap redraws; a tap on a tab picks that page
 * The screen shows game graphics: keep OUT outside the repo. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../linkscr.h"
const uint8_t *host_font;
static uint8_t RAM[0x200000], FONT[2048]; static uint16_t px[LINK_W * LINK_H];
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb"); if (!f || fread(RAM, 1, sizeof RAM, f) != sizeof RAM) { fprintf(stderr, "ram?\n"); return 1; } fclose(f);
    f = fopen(argv[3], "rb"); if (!f) { fprintf(stderr, "font?\n"); return 1; } if (!fread(FONT, 1, sizeof FONT, f)) return 1; fclose(f); host_font = FONT;
    link_init(argv[2]);
    LinkIn in; memset(&in, 0, sizeof in); in.ram = RAM; in.fps = 60; in.drawn = 30; in.n3ds = 1; in.dynarec = 1; in.nowMs = 10000;
    link_draw(px, &in);
    for (int i = 5; i + 2 < argc + 0; i += 3) { if (strcmp(argv[i], "tap")) break; in.nowMs += 5000; link_tap(atoi(argv[i + 1]), atoi(argv[i + 2]), &in); link_draw(px, &in); }
    in.nowMs += 5000; link_draw(px, &in);
    f = fopen(argv[4], "wb"); fprintf(f, "P6 %d %d 255\n", LINK_W, LINK_H);
    for (int i = 0; i < LINK_W * LINK_H; i++) { unsigned p = px[i]; unsigned char c[3] = { (unsigned char)((p >> 11) << 3), (unsigned char)(((p >> 5) & 63) << 2), (unsigned char)((p & 31) << 3) }; fwrite(c, 1, 3, f); }
    fclose(f);
    return 0;
}
