/* linkint.h - what linkscr.c, linkmap.c and linkfight.c share: RAM, drawing, names, the pages. */
#ifndef LINKINT_H
#define LINKINT_H
#include "linkscr.h"

/* RAM offsets, Link's table A (address minus 0x80000000) */
#define A_SIG    0x6FAF0   /* 4 room, 5 world map, 6 battle, 7 arena */
#define A_FIELD  0x6F94E
#define A_STORY  0x6EF64   /* script variables, saved copy; variable 0 is the story step */
#define A_SVAR   0xC3A68   /* script variables, live copy while in a room */
#define A_PARTY  0x6F368
#define A_RIDE   0x6F8E5
#define A_GOLD   0x6EF58
#define A_PTIME  0x59488
#define A_CHAR   0x6D8A0
#define A_GEAR   0x6DFAC
#define A_SKILL  0x6ECF0
#define REC      0xA4

#define RGB(r, g, b) (uint16_t)((((r) >> 3) << 11) | (((g) >> 2) << 5) | ((b) >> 3))
enum { WHITE, GREY, CYAN, YELLOW, GREEN, RED, ORANGE, BLUE, PINK, DARK, PANEL, BAR, NCOL };
extern uint16_t COL[NCOL];
extern uint16_t *fb;
extern const uint8_t *ram;
extern const LinkIn *IN;

static inline unsigned u8at(unsigned a) { return a < 0x200000 ? ram[a] : 0; }
static inline unsigned u16at(unsigned a) { return u8at(a) | u8at(a + 1) << 8; }
static inline unsigned u32at(unsigned a) { return u16at(a) | (unsigned)u16at(a + 2) << 16; }
static inline int s16at(unsigned a) { return (int16_t)u16at(a); }
static inline int s32at(unsigned a) { return (int32_t)u32at(a); }
/* a game pointer as a RAM offset, or -1 */
static inline int ptrOf(unsigned v) { return (v >> 24) == 0x80 && (v & 0xFFFFFF) < 0x200000 ? (int)(v & 0x1FFFFF) : -1; }

/* drawing: everything is clipped to the screen */
void rect(int x, int y, int w, int h, int c);
void pix(int x, int y, int c);
void line(int x0, int y0, int x1, int y1, int c);
void ring(int cx, int cy, int r, int c);
void disc(int cx, int cy, int r, int c);
void text(const char *s, int x, int y, int c);
void textn(const char *s, int x, int y, int maxChars, int c);    /* cut to fit */
void textf(int x, int y, int c, const char *f, int a, int b);
int  wrap(const char *s, int x, int y, int cols, int c);         /* word wrap; returns the y below the text */
void button(int x, int y, int w, const char *s, int on);
void meter(int x, int y, int w, int val, int max, int c);
/* a pop-up text box over the page: lines, in colours; it stays until a tap */
void popReset(void);
void popLine(const char *s, int c);
void popWrap(const char *s, int cols, int c);
void popDraw(void);

const char *roomName(int id);
const char *areaName(int id);
const char *chapterName(int step);
const char *charName(int id);
const char *gearName(int g);

/* linkscr.c: the hint on show; spots for the map (-1 = the world map): calls back with each x, z */
void hintSpots(int room, void (*cb)(int x, int z));
void map_hroom(int room, float *l, float *t, float *s);          /* the part of a room's picture its hint thumbnail shows */

/* linkmap.c */
void map_open(const char *pakPath);
int  map_havePak(void);
void map_page(void);
int  map_tap(int x, int y);
void map_thumb(int room, const int16_t *spots, int nspots, int x, int y, int size);   /* a hint's room picture */
/* the pack's pictures: a pointer valid until the next call of the same kind, or NULL */
const uint16_t *pak_sprite(int n, int *w, int *h);

/* linkfight.c */
void fight_tick(void);                                           /* each draw: notices a fight starting */
void fight_page(void);
int  fight_tap(int x, int y);
void blows_page(void);
int  blows_tap(int x, int y);
void fight_popup(void);                                          /* draws the fight or deathblow pop-up, if one is open */
int  fight_popClose(void);                                       /* closes it; 1 if one was open */

#endif
