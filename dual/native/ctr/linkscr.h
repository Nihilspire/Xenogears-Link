/* linkscr.h - the 3DS Link screen: hints, map, fight, party, deathblows, read live from the game's RAM, plus a system page. */
#ifndef LINKSCR_H
#define LINKSCR_H
#include <stdint.h>

#define LINK_W 320
#define LINK_H 240

typedef struct {
    const uint8_t *ram;            /* the PS1's 2 MB of main RAM */
    uint32_t nowMs;                /* a clock in ms */
    /* what the system page and the status line show */
    int fps, drawn;                /* game frames and pictures in the last second */
    int msEmu, msTop, msLink, msMax;   /* average tenths of a ms a frame, and the longest loop */
    int n3ds, dynarec, gputhread, frameskip, analog, disc, discs, old3ds;
    const char *msg;               /* "SAVED TO SLOT 1", ... */
    const char *state[2];          /* a line about each save-state slot */
} LinkIn;

/* what a tap asks main.c to do */
enum { LINK_NONE, LINK_REDRAW, LINK_SAVE0, LINK_SAVE1, LINK_LOAD0, LINK_LOAD1, LINK_FRAMESKIP, LINK_OLD3DS, LINK_DISC, LINK_QUIT };

void link_init(const char *pakPath);               /* opens the picture pack, if it's there */
void link_draw(uint16_t *px, const LinkIn *in);    /* px: LINK_W x LINK_H, row by row */
int  link_tap(int x, int y, const LinkIn *in);
int  link_interval(void);                          /* game frames between redraws, for what's showing now */
const uint8_t *link_prog(int *len, int *opts);     /* the analog controls program */

#endif
