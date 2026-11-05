/* linkscr.c - the 3DS Link screen. There is no web view for homebrew, so this is C, drawn into a 320x240 RGB565 buffer. It is a slice of
 * Link: the same story hints (rules as hintNext / hintAt / hintParts / hintRooms in Link's index.html, data from the same files by
 * tools/mk_linkdata.py), read from the same RAM addresses. This file has the drawing, the tabs and the HINT, PARTY and SYSTEM pages;
 * linkmap.c has MAP, linkfight.c has FIGHT and BLOWS. No guide line: green spots mark the hint's places, as on the phone. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "linkint.h"
#include "linkdata.h"
#ifdef __3DS__
#include <3ds.h>
#else
extern const uint8_t *host_font;
#endif

uint16_t COL[NCOL];
uint16_t *fb;
const uint8_t *ram;
const LinkIn *IN;

/* ------------------------------------------------------------------ drawing */
void rect(int x, int y, int w, int h, int c) {
    uint16_t v = COL[c];
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > LINK_W) w = LINK_W - x;
    if (y + h > LINK_H) h = LINK_H - y;
    for (int j = 0; j < h; j++) { uint16_t *p = fb + (y + j) * LINK_W + x; for (int i = 0; i < w; i++) p[i] = v; }
}
void pix(int x, int y, int c) { if ((unsigned)x < LINK_W && (unsigned)y < LINK_H) fb[y * LINK_W + x] = COL[c]; }
void line(int x0, int y0, int x1, int y1, int c) {
    int dx = abs(x1 - x0), dy = -abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, e = dx + dy, n = 0;
    while (n++ < 2000) {
        pix(x0, y0, c);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * e;
        if (e2 >= dy) { e += dy; x0 += sx; }
        if (e2 <= dx) { e += dx; y0 += sy; }
    }
}
void ring(int cx, int cy, int r, int c) {
    int x = r, y = 0, e = 1 - r;
    while (x >= y) {
        pix(cx + x, cy + y, c); pix(cx - x, cy + y, c); pix(cx + x, cy - y, c); pix(cx - x, cy - y, c);
        pix(cx + y, cy + x, c); pix(cx - y, cy + x, c); pix(cx + y, cy - x, c); pix(cx - y, cy - x, c);
        y++;
        if (e < 0) e += 2 * y + 1; else { x--; e += 2 * (y - x) + 1; }
    }
}
void disc(int cx, int cy, int r, int c) {
    for (int y = -r; y <= r; y++) { int w = 0; while ((w + 1) * (w + 1) + y * y <= r * r) w++; rect(cx - w, cy + y, 2 * w + 1, 1, c); }
}
static const uint8_t *fontBits(void) {
#ifdef __3DS__
    static const uint8_t *f; if (!f) f = (const uint8_t *)consoleGetDefault()->font.gfx;
    return f;
#else
    return host_font;
#endif
}
static void glyph(int ch, int x, int y, int c) {
    const uint8_t *g = fontBits() + (ch & 255) * 8; uint16_t v = COL[c];
    for (int j = 0; j < 8; j++) {
        uint8_t b = g[j]; if (!b || y + j >= LINK_H || y + j < 0) continue;
        uint16_t *p = fb + (y + j) * LINK_W + x;
        for (int i = 0; i < 8; i++) if ((b & (0x80 >> i)) && x + i < LINK_W && x + i >= 0) p[i] = v;
    }
}
void text(const char *s, int x, int y, int c) { for (; *s && x < LINK_W; s++, x += 8) if (*s > ' ') glyph(*s, x, y, c); }
void textn(const char *s, int x, int y, int maxChars, int c) { for (; *s && maxChars > 0; s++, x += 8, maxChars--) if (*s > ' ') glyph(*s, x, y, c); }
void textf(int x, int y, int c, const char *f, int a, int b) { char t[48]; snprintf(t, sizeof t, f, a, b); text(t, x, y, c); }
int wrap(const char *s, int x, int y, int cols, int c) {
    while (*s) {
        while (*s == ' ') s++;
        int n = (int)strlen(s), cut = n;
        if (n > cols) { cut = cols; while (cut > 0 && s[cut] != ' ') cut--; if (!cut) cut = cols; }
        char t[48]; memcpy(t, s, cut); t[cut] = 0;
        text(t, x, y, c);
        s += cut; y += 10;
        if (y > LINK_H - 40) break;
    }
    return y;
}
void button(int x, int y, int w, const char *s, int on) {
    rect(x, y, w, 20, on ? CYAN : BAR);
    text(s, x + (w - 8 * (int)strlen(s)) / 2, y + 6, on ? DARK : WHITE);
}
void meter(int x, int y, int w, int val, int max, int c) {
    rect(x, y, w, 5, DARK);
    if (max > 0 && val > 0) rect(x, y, val >= max ? w : (int)((int64_t)val * w / max), 5, c);
}

/* ---- the pop-up box ---- */
#define POP_MAX 21
static char popT[POP_MAX][40]; static uint8_t popC[POP_MAX]; static int popN;
void popReset(void) { popN = 0; }
void popLine(const char *s, int c) { if (popN < POP_MAX) { snprintf(popT[popN], 40, "%s", s); popC[popN++] = (uint8_t)c; } }
void popWrap(const char *s, int cols, int c) {
    while (*s) {
        while (*s == ' ') s++;
        int n = (int)strlen(s), cut = n;
        if (n > cols) { cut = cols; while (cut > 0 && s[cut] != ' ') cut--; if (!cut) cut = cols; }
        char t[40]; memcpy(t, s, cut); t[cut] = 0; popLine(t, c);
        s += cut;
    }
}
void popDraw(void) {
    int h = popN * 10 + 8, y = (LINK_H - 14 - h) / 2; if (y < 0) y = 0;
    rect(6, y, LINK_W - 12, h, WHITE); rect(7, y + 1, LINK_W - 14, h - 2, DARK);
    for (int i = 0; i < popN; i++) text(popT[i], 10, y + 5 + i * 10, popC[i]);
}

/* ------------------------------------------------------------------ names */
const char *roomName(int id) {
    static char t[40];
    if (id < 0) return "World map";
    int lo = 0, hi = (int)(sizeof ROOMNAME / sizeof ROOMNAME[0]) - 1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (ROOMNAME[m].id == id) return ROOMNAME[m].n; if (ROOMNAME[m].id < id) lo = m + 1; else hi = m - 1; }
    for (size_t i = 0; i < sizeof AREA / sizeof AREA[0]; i++) if (id >= AREA[i].a && id <= AREA[i].b) { snprintf(t, sizeof t, "%s %d", AREA[i].s, id); return t; }
    snprintf(t, sizeof t, "Room %d", id); return t;
}
const char *areaName(int id) {
    for (size_t i = 0; i < sizeof AREA / sizeof AREA[0]; i++) if (id >= AREA[i].a && id <= AREA[i].b) return AREA[i].n;
    return NULL;
}
const char *chapterName(int step) {
    const char *n = NULL;
    if (step > 353) return NULL;
    for (size_t i = 0; i < sizeof CHAPTER / sizeof CHAPTER[0] && CHAPTER[i].step <= step; i++) n = CHAPTER[i].n;
    return n;
}
const char *charName(int id) { return id >= 0 && id < (int)(sizeof CHARNAME / sizeof CHARNAME[0]) ? CHARNAME[id] : "???"; }
const char *gearName(int g) { return g >= 0 && g < (int)(sizeof GEARNAME / sizeof GEARNAME[0]) ? GEARNAME[g] : "???"; }

/* ------------------------------------------------------------------ the story hint */
#define MAXPART 24
typedef struct { int step, done, unv, nparts, nrooms; char *part[MAXPART]; int room[16]; const int16_t *spot[16]; int nspot[16]; } Cur;
static Cur cur;
static char curText[2048];

static int flagOn(int v, unsigned m) { unsigned b = u32at(A_SIG) == 4 ? A_SVAR : A_STORY; return (u16at(b + v) & m) != 0; }
/* split at each full stop followed by a space, as hintParts */
static int splitParts(const char *s, char *buf, size_t cap, char **part, uint32_t drop) {
    int n = 0, kept = 0; size_t w = 0;
    while (*s == ' ') s++;
    while (*s && n < MAXPART) {
        const char *e = s;
        while (*e && !(e[0] == '.' && (e[1] == ' ' || !e[1]))) e++;
        if (*e == '.') e++;
        size_t l = (size_t)(e - s);
        if (!(drop >> n & 1) && w + l + 1 < cap) { memcpy(buf + w, s, l); buf[w + l] = 0; part[kept++] = buf + w; w += l + 1; }
        n++;
        s = e; while (*s == ' ') s++;
    }
    return kept;
}
/* a hint's rooms are stored flat: room, number of spots, x, z, x, z...; skip marks ones already done */
static void takeRooms(const int16_t *q, int n, uint32_t skip) {
    cur.nrooms = 0;
    for (int k = 0; k < n; k++) {
        int room = q[0], ns = q[1];
        if (!(skip >> k & 1) && cur.nrooms < 16) { cur.room[cur.nrooms] = room; cur.spot[cur.nrooms] = q + 2; cur.nspot[cur.nrooms] = ns; cur.nrooms++; }
        q += 2 + ns * 2;
    }
}
/* hintNext + hintAt: the first hint above the story step, with the parts already done taken out. 0 when there's none. */
static int hintNow(void) {
    int s = (int)u16at(A_STORY);
    for (int i = 0; i < NHINT; i++) {
        const Hint *h = &HINT[i];
        if (h->step <= s) continue;
        uint32_t dS = 0, dP = 0; const HSplit *rep = NULL; int done = 0;
        if (h->note[0]) for (int j = 0; j < h->nsp; j++) {
            const HSplit *r = &h->sp[j]; int all = 1;
            for (int f = 0; f < r->nflags; f++) if (!flagOn(r->flags[f].v, r->flags[f].m)) all = 0;
            if (!all) continue;
            done = j + 1; dS |= r->dropS; dP |= r->dropP; if (r->text) rep = r;
        }
        const char *nt = rep ? rep->text : h->note;
        cur.unv = nt[0] == '?'; if (cur.unv) nt++;
        cur.nparts = splitParts(nt, curText, sizeof curText, cur.part, rep ? 0 : dS);
        if (done && !rep && !cur.nparts) continue;                 /* all of it done: the next step's hint */
        cur.step = h->step; cur.done = done;
        if (rep) takeRooms(rep->rooms, rep->nrooms, 0);
        else takeRooms(h->rooms, h->nrooms, h->hasPath ? dP : 0);
        return 1;
    }
    return 0;
}
void hintSpots(int room, void (*cb)(int x, int z)) {
    if (!hintNow()) return;
    for (int k = 0; k < cur.nrooms; k++) if (cur.room[k] == room) for (int j = 0; j < cur.nspot[k]; j++) cb(cur.spot[k][j * 2], cur.spot[k][j * 2 + 1]);
}
void map_hroom(int room, float *l, float *t, float *s) {
    *l = 0; *t = 0; *s = 1;
    for (size_t i = 0; i < sizeof HROOMTAB / sizeof HROOMTAB[0]; i++) if (HROOMTAB[i].room == room) { *l = HROOMTAB[i].l; *t = HROOMTAB[i].t; *s = HROOMTAB[i].s; return; }
}

/* ------------------------------------------------------------------ the pages */
enum { TAB_HINT, TAB_MAP, TAB_FIGHT, TAB_PARTY, TAB_BLOWS, TAB_SYS, NTAB };
static int tab = TAB_HINT, page, lastKey = -1, tabBeforeFight = -1;
static const char *const TABN[NTAB] = { "HINT", "MAP", "FIGHT", "PARTY", "BLOWS", "SYS" };
static int inRoom(void) { return u32at(A_SIG) == 4; }
static int here(void) { return inRoom() ? (int)(u16at(A_FIELD) & 0x7FF) : u32at(A_SIG) == 5 ? -1 : -2; }

static int pagesOf(void) { int n = cur.nparts > cur.nrooms ? cur.nparts : cur.nrooms; return n < 1 ? 1 : n; }
#define THUMB 108
static void pageHint(void) {
    int y = 24;
    text("THE STORY GOES ON IN", 4, y, CYAN);
    if (!hintNow()) { text("Nothing more to point to.", 4, y + 16, GREY); return; }
    int key = cur.step * 8 + cur.done;
    if (key != lastKey) { lastKey = key; page = 0; }                /* a new hint starts at its first page */
    int n = pagesOf(); if (page >= n) page = n - 1;
    y += 14;
    int cols = 38;
    if (cur.nrooms) {
        int k = page < cur.nrooms ? page : cur.nrooms - 1, r = cur.room[k];
        const char *a = r >= 0 ? areaName(r) : NULL;
        if (a) { text(a, 4, y, YELLOW); y += 10; }
        textn(roomName(r), 4, y, 38, WHITE); y += 10;
        text(here() == r ? "YOU ARE HERE" : "Not where you are now.", 4, y, here() == r ? GREEN : GREY); y += 16;
        if (map_havePak()) { map_thumb(r, cur.spot[k], cur.nspot[k], LINK_W - THUMB - 4, y - 2, THUMB); cols = 25; }
    }
    if (cur.nparts) wrap(cur.part[page < cur.nparts ? page : cur.nparts - 1], 4, y, cols, cur.unv ? GREY : WHITE);
    if (n > 1) {
        button(4, LINK_H - 38, 60, "BACK", 0);
        button(LINK_W - 64, LINK_H - 38, 60, "NEXT", 0);
        textf(LINK_W / 2 - 16, LINK_H - 32, GREY, "%d/%d", page + 1, n);
    }
}
static void pageParty(void) {
    int y = 24, sig = u32at(A_SIG);
    for (int i = 0; i < 3; i++) {
        int id = u8at(A_PARTY + i);
        if (id > 10) continue;
        unsigned b = A_CHAR + id * REC;
        text(charName(id), 4, y, YELLOW);
        textf(200, y, WHITE, "LV %d", u8at(b + 0x62), 0);
        y += 11;
        int hp = u16at(b + 0x4C), mhp = u16at(b + 0x4E), ep = u16at(b + 0x50), mep = u16at(b + 0x52);
        textf(4, y, WHITE, "HP %4d/%4d", hp, mhp); meter(100, y + 2, 216, hp, mhp, GREEN); y += 10;
        textf(4, y, WHITE, "EP %4d/%4d", ep, mep); meter(100, y + 2, 216, ep, mep, CYAN); y += 11;
        int g = u8at(b + 0xA0);
        if ((sig == 4 || sig == 5) && u8at(A_RIDE + i) == 1 && g < 20) {     /* in a Gear: its HP and fuel too */
            unsigned gb = A_GEAR + g * REC;
            text(gearName(g), 4, y, CYAN); y += 10;
            int ghp = (int)u32at(gb + 0x60), gmhp = (int)u32at(gb + 0x64), fu = u16at(gb + 0x38), mfu = u16at(gb + 0x3A);
            textf(4, y, WHITE, "HP %6d/%6d", ghp, gmhp); meter(148, y + 2, 168, ghp, gmhp, GREEN); y += 10;
            textf(4, y, WHITE, "FU %6d/%6d", fu, mfu); meter(148, y + 2, 168, fu, mfu, ORANGE); y += 11;
        }
        y += 4;
    }
    int step = u16at(A_STORY);
    const char *c = chapterName(step);
    unsigned pt = u32at(A_PTIME) / 60;
    text(c ? c : "-", 4, LINK_H - 44, CYAN);
    textf(4, LINK_H - 32, WHITE, "GOLD %d", (int)u32at(A_GOLD), 0);
    textf(200, LINK_H - 32, WHITE, "TIME %d:%02d", pt / 3600, pt / 60 % 60);
}
static void pageSys(const LinkIn *in) {
    int y = 24;
    text(in->n3ds ? "NEW 3DS" : "OLD 3DS", 4, y, CYAN);
    text(in->dynarec ? "RECOMPILER" : "INTERPRETER", 80, y, in->dynarec ? GREEN : RED);
    text(in->gputhread ? "GPU THREAD" : "GPU MAIN", 200, y, WHITE); y += 12;
    text("analog controls:", 4, y, WHITE);
    { static const char *const AN[] = { "off", "waiting", "running", "stood down" }; text(AN[in->analog & 3], 4 + 8 * 17, y, in->analog == 2 ? GREEN : GREY); }
    y += 16;
    for (int i = 0; i < 2; i++) {
        char t[12]; snprintf(t, sizeof t, "SAVE %d", i + 1); button(4, y, 64, t, 0);
        snprintf(t, sizeof t, "LOAD %d", i + 1); button(72, y, 64, t, 0);
        text(in->state[i] ? in->state[i] : "", 142, y + 6, GREY);
        y += 24;
    }
    { char t[16]; snprintf(t, sizeof t, "SKIP %d", in->frameskip); button(4, y, 64, t, in->frameskip != 0); }
    button(72, y, 64, "OLD3DS", in->old3ds);
    { char t[12]; snprintf(t, sizeof t, "DISC %d", in->disc + 1); button(140, y, 64, t, 0); }
    button(LINK_W - 64, y, 60, "QUIT", 0);
    y += 26;
    textf(4, y, GREY, "field %d  story step %d", u16at(A_FIELD) & 0x7FF, u16at(A_STORY)); y += 10;
    { char t[40]; snprintf(t, sizeof t, "mode %d  link %d.%d ms", (int)u32at(A_SIG), in->msLink / 10, in->msLink % 10); text(t, 4, y, GREY); } y += 10;
    text(map_havePak() ? "pictures: xenogears-link.pak" : "pictures: no xenogears-link.pak", 4, y, map_havePak() ? GREY : ORANGE); y += 12;
    if (in->msg) text(in->msg, 4, y, YELLOW);
}

void link_init(const char *pakPath) { map_open(pakPath); }

void link_draw(uint16_t *px, const LinkIn *in) {
    if (!COL[WHITE]) {
        COL[WHITE] = RGB(240, 240, 240); COL[GREY] = RGB(140, 150, 170); COL[CYAN] = RGB(90, 210, 230); COL[YELLOW] = RGB(240, 210, 90);
        COL[GREEN] = RGB(90, 220, 110); COL[RED] = RGB(230, 90, 80); COL[ORANGE] = RGB(255, 154, 60); COL[BLUE] = RGB(102, 204, 255);
        COL[PINK] = RGB(255, 106, 208); COL[DARK] = RGB(6, 8, 20); COL[PANEL] = RGB(14, 22, 58); COL[BAR] = RGB(40, 56, 110);
    }
    fb = px; ram = in->ram; IN = in;
    fight_tick();
    /* a fight brings up its page, and the end of it goes back */
    { static unsigned was; unsigned sig = u32at(A_SIG), fight = sig == 6 || sig == 7, wasF = was == 6 || was == 7;
      if (fight && !wasF && tab != TAB_FIGHT) { tabBeforeFight = tab; tab = TAB_FIGHT; }
      if (!fight && wasF && tabBeforeFight >= 0) { tab = tabBeforeFight; tabBeforeFight = -1; }
      was = sig; }
    rect(0, 0, LINK_W, LINK_H, PANEL);
    for (int i = 0; i < NTAB; i++) {
        int w = LINK_W / NTAB, on = i == tab;
        rect(i * w, 0, w - 1, 18, on ? CYAN : BAR);
        text(TABN[i], i * w + (w - 8 * (int)strlen(TABN[i])) / 2, 5, on ? DARK : WHITE);
    }
    if (tab == TAB_HINT) pageHint();
    else if (tab == TAB_MAP) map_page();
    else if (tab == TAB_FIGHT) fight_page();
    else if (tab == TAB_PARTY) pageParty();
    else if (tab == TAB_BLOWS) blows_page();
    else pageSys(in);
    fight_popup();
    /* the status line: what this proof of concept is here to measure */
    rect(0, LINK_H - 14, LINK_W, 14, DARK);
    { char t[48];
      snprintf(t, sizeof t, "%2d/%2dfps emu%3d.%d top%2d.%d max%3d", in->fps, in->drawn, in->msEmu / 10, in->msEmu % 10, in->msTop / 10, in->msTop % 10, in->msMax / 10);
      text(t, 2, LINK_H - 11, in->fps >= 58 ? GREEN : in->fps >= 45 ? YELLOW : RED); }
}

int link_interval(void) { return tab == TAB_MAP ? 6 : tab == TAB_FIGHT ? 10 : 20; }

int link_tap(int x, int y, const LinkIn *in) {
    ram = in->ram; IN = in;
    if (fight_popClose()) return LINK_REDRAW;
    if (y < 20) { int t = x / (LINK_W / NTAB); if (t < NTAB) { tab = t; tabBeforeFight = -1; } return LINK_REDRAW; }
    if (tab == TAB_MAP) return map_tap(x, y) ? LINK_REDRAW : LINK_NONE;
    if (tab == TAB_FIGHT) return fight_tap(x, y) ? LINK_REDRAW : LINK_NONE;
    if (tab == TAB_BLOWS) return blows_tap(x, y) ? LINK_REDRAW : LINK_NONE;
    if (tab == TAB_HINT && y >= LINK_H - 38 && y < LINK_H - 18) {
        if (!hintNow()) return LINK_NONE;
        int n = pagesOf();
        if (x < 80 && page > 0) { page--; return LINK_REDRAW; }
        if (x > LINK_W - 80 && page + 1 < n) { page++; return LINK_REDRAW; }
    }
    if (tab == TAB_SYS) {
        int r0 = 24 + 12 + 16;
        for (int i = 0; i < 2; i++) if (y >= r0 + i * 24 && y < r0 + i * 24 + 20) {
            if (x >= 4 && x < 68) return i ? LINK_SAVE1 : LINK_SAVE0;
            if (x >= 72 && x < 136) return i ? LINK_LOAD1 : LINK_LOAD0;
        }
        int r2 = r0 + 48;
        if (y >= r2 && y < r2 + 20) {
            if (x >= 4 && x < 68) return LINK_FRAMESKIP;
            if (x >= 72 && x < 136) return LINK_OLD3DS;
            if (x >= 140 && x < 204) return LINK_DISC;
            if (x >= LINK_W - 64) return LINK_QUIT;
        }
    }
    return LINK_NONE;
}

const uint8_t *link_prog(int *len, int *opts) { *len = (int)sizeof XGA_PROG; *opts = XGA_OPTS_DEFAULT; return XGA_PROG; }
