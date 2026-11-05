/* linkfight.c - the FIGHT and BLOWS tabs. FIGHT is battleView in Link's index.html on a smaller screen: the enemies with their sprites,
 * names and HP, the party, the acting member's deathblows, the order they act in (numbers, in place of the sprite strip). The names come
 * from the fight's line-up record or, failing that, a search of every monster bank, as lineup / enemyNames. Tap an enemy: rewards, drops,
 * status, immunities, elements, boss tip. Tap a party member: their deathblows. Tap a deathblow: what it takes to learn. BLOWS is the
 * same list outside a fight. The arena mini-game gets its two bars. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "linkint.h"
#include "linkdata.h"

#define A_BFORM 0x6F9DC
#define A_BSLOT 0xCCCE8
#define A_BPID  0xD2D24
#define A_BLIVE 0xD2DCC
#define A_BGONE 0xD2DE4
#define A_BTURN 0xC4922
#define A_BTIME 0xD2E06
#define A_BACT  0xCCB3C
#define A_BTLP  0x987E0
#define A_BTLE  0x970C4
#define A_BTLIX 0x92700
#define BREC    0x170
#define SLOTB(s) (A_BSLOT + (s) * BREC)

/* ------------------------------------------------------------------ who's in the fight */
typedef struct { int m, g, x, gd, on, has; uint8_t d[6], st[8]; } Slot;
typedef struct { const char *n; int st, spr, hide, join; } Name;
static Slot sl[8];
static Name names[8], slotMem[11];
static uint32_t namesKey; static int namesOk;
static int hpSeen[11]; static uint32_t hpKey[11];
static int enemyId[11];
static uint32_t bstart, seenOut[11]; static uint8_t startOut[11];
static unsigned sigWas;
static int dbSel, lastAct = -1;

static const char *okName(const char *n) { return n && n[0] ? n : NULL; }
static int recMatch(const ERec *e, const Slot *s) {
    if (!e->h0 && !e->h1) return 0;
    int hp = s->m == e->h0 && s->g == e->h1, rw = s->x > 0 && s->x == e->x && s->gd == e->g;
    if (!hp && !rw) return 0;
    return (hp ? 2 : 0) + (rw ? 3 : 0) + (rw && !memcmp(s->d, e->d, 6) ? 1 : 0) + (!memcmp(s->st, e->s, 8) ? 1 : 0);
}
static int bestRec(const ERec *bank, int i, const Slot *s, int named, int *value) {
    int bv = 0, bk = -1;
    for (int k = 0; k < 8; k++) {
        if (named && !okName(bank[k].n)) continue;
        int v = recMatch(&bank[k], s) * 2 + (k == i ? 1 : 0);
        if (v > 1 && v > bv) { bv = v; bk = k; }
    }
    if (value) *value = bv;
    return bk;
}
/* lineup in Link: the fight's own record gives every enemy's exact record. 1 when it fits. */
static int lineup(Name *out) {
    int k = u8at(A_BFORM);
    if (k == 52 || k == 68) return 0;
    k = k - (k > 52 ? 1 : 0) - (k > 68 ? 1 : 0);
    if (k < 0 || k >= NBANK) return 0;
    const ERec *e = ENEMY[k]; int n = 0, late[8], nl = 0;
    for (int i = 0; i < 8; i++) {
        int v = u8at(A_BFORM + 8 + i); const Slot *s = &sl[i]; int has = s->m || s->g;
        memset(&out[i], 0, sizeof out[i]); out[i].spr = -1;
        if (v != 255 && has) {
            int r = v & 127;
            if (r < 8 && (e[r].h0 || e[r].h1) && ((e[r].h0 && s->m == e[r].h0) || (e[r].h1 && s->g == e[r].h1))) {
                out[i].n = okName(e[r].n); out[i].st = s->g > 0 ? e[r].l1 : e[r].l0; out[i].spr = e[r].spr;
                out[i].hide = !out[i].n && (u8at(A_BFORM + 16 + i) & 0x80); n++;
                continue;
            }
        }
        if (has && s->on) late[nl++] = i;
    }
    if (!n) return 0;
    for (int j = 0; j < nl; j++) {                                 /* enemies that joined later come from the same bank */
        int i = late[j], r = bestRec(e, i, &sl[i], 1, NULL);
        if (r < 0) r = bestRec(e, i, &sl[i], 0, NULL);
        if (r < 0) return 0;                                       /* a joiner from another bank: search them all */
        out[i].n = okName(e[r].n); out[i].st = sl[i].g > 0 ? e[r].l1 : e[r].l0; out[i].spr = e[r].spr;
    }
    return 1;
}
/* enemyNames in Link, worked out only when something about the fight changes */
static void enemyNames(void) {
    uint32_t key = 2166136261u;
#define MIX(v) (key = (key ^ (uint32_t)(v)) * 16777619u)
    for (int i = 0; i < 8; i++) { MIX(sl[i].m); MIX(sl[i].g); MIX(sl[i].x); MIX(sl[i].gd); MIX(sl[i].on); for (int k = 0; k < 6; k++) MIX(sl[i].d[k]); for (int k = 0; k < 8; k++) MIX(sl[i].st[k]); }
    for (int i = 0; i < 0x20; i++) MIX(u8at(A_BFORM + i));
    if (namesOk && key == namesKey) return;
    namesKey = key; namesOk = 1;
    if (lineup(names)) return;
    int best = -1, bs = 0;
    for (int b = 0; b < NBANK; b++) {
        int sc = 0;
        for (int i = 0; i < 8; i++) {
            const Slot *s = &sl[i]; if (!s->on || !(s->m || s->g)) continue;
            int v, r = bestRec(ENEMY[b], i, s, 0, &v); sc += r >= 0 ? v : -8;
        }
        if (sc > bs) { bs = sc; best = b; }
    }
    for (int i = 0; i < 8; i++) {
        const Slot *s = &sl[i]; Name *o = &names[i]; memset(o, 0, sizeof *o); o->spr = -1;
        if (!(s->m || s->g)) continue;
        const ERec *e = best >= 0 ? ENEMY[best] : NULL;
        int r = e ? bestRec(e, i, s, 1, NULL) : -1, any = e ? bestRec(e, i, s, 0, NULL) : -1;
        if (r >= 0) { o->n = okName(e[r].n); o->spr = e[r].spr; } else if (any >= 0) o->spr = e[any].spr;
        if (any >= 0) o->st = s->g > 0 ? e[any].l1 : e[any].l0;
        if (!o->n) {                                               /* one name fits best over every bank */
            int top = 0, sst = 0, sp = -1; const char *only = NULL; int many = 0;
            for (int b = 0; b < NBANK; b++) for (int k = 0; k < 8; k++) {
                int v = recMatch(&ENEMY[b][k], s); const char *nm = okName(ENEMY[b][k].n);
                if (!v || !nm) continue;
                if (v > top) { top = v; only = nm; many = 0; sst = s->g > 0 ? ENEMY[b][k].l1 : ENEMY[b][k].l0; sp = ENEMY[b][k].spr; }
                else if (v == top && only && strcmp(only, nm)) many = 1;
            }
            if (only && !many) { o->n = only; if (!o->st) o->st = sst; if (o->spr < 0) o->spr = sp; }
        }
    }
}
void fight_tick(void) {
    unsigned sig = u32at(A_SIG);
    if (sig == 6 && sigWas != 6) {                                 /* a new fight */
        memset(slotMem, 0, sizeof slotMem); memset(hpSeen, 0, sizeof hpSeen); memset(hpKey, 0, sizeof hpKey); memset(enemyId, 0, sizeof enemyId);
        memset(seenOut, 0, sizeof seenOut); memset(startOut, 0, sizeof startOut); namesOk = 0; bstart = IN->nowMs; dbSel = 0; lastAct = -1;
        for (int i = 0; i < 11; i++) slotMem[i].spr = -1;
    }
    sigWas = sig;
}

/* ---- enemies not out yet (actorHidden / offField in Link) ---- */
static int actorObj(int s) { return ptrOf(u32at(A_BACT + 4 * s)); }
static int actorHidden(int s, const char *name) {
    int a = actorObj(s); if (a < 0) return 0;
    unsigned ac = u32at(a + 0xAC), c = u32at(a + 0x3C);
    if (ac & 0x01000000) return (c & 0x40000000) != 0;
    if (!name || strcmp(name, "Super Aerod")) return 0;
    int y = s16at(a + 6), top = 0, have = 0;
    for (int p = 0; p < 3; p++) { int pa = actorObj(p); if (pa >= 0) { int py = s16at(pa + 6); if (!have || py < top) { top = py; have = 1; } } }
    return have && y < top - 3000;
}
static int offField(int s, int hp, const char *name) {
    if (!actorHidden(s, name)) { seenOut[s] = IN->nowMs + 1; if (IN->nowMs - bstart < 3000 && actorObj(s) >= 0) startOut[s] = 1; return 0; }
    if (startOut[s] && hp > 0) return 0;
    return !(seenOut[s] && IN->nowMs - seenOut[s] < 1000);
}

/* ---- status effects (ST_FOOT / ST_GEAR) ---- */
typedef struct { uint16_t mask; const char *tag, *name; uint8_t bad; } StE;
typedef struct { uint16_t w0, w1; const StE *e; int n; } StW;
static const StE F0[] = { {0x2000,"STOP","Stop",1},{0x1000,"SLOW","Slow",1},{0x0800,"PSN","Poison",1},{0x0400,"ACC-","ACC DOWN",1},{0x0200,"ATK-","Atk DOWN",1},{0x0100,"DEF-","Def DOWN",1} };
static const StE F1[] = { {0x2000,"CONF","Confusion",1},{0x1000,"SLP","Sleep",1},{0x0800,"MUTE","Can't use Ether",1},{0x0400,"ETH-","Eth effect DOWN",1},{0x0020,"LURE","Taunt",1} };
static const StE F2[] = { {0x8000,"SPD+","Speed UP",0},{0x4000,"DEF+","Def UP",0},{0x2000,"ATK+","Atk UP",0},{0x1000,"ACC+","ACC UP",0},{0x0800,"EV+","EV UP",0} };
static const StE F3[] = { {0x8000,"ETH+","Eth effect UP",0},{0x4000,"EDF+","Eth Def UP",0},{0x1000,"CNTR","Counter UP",0},{0x000A,"ATK+","Atk UP/Def DOWN",0},{0x0005,"DEF+","Def UP/Atk DOWN",0} };
static const StE F4[] = { {0x8000,"WIND","Wind attacks",0},{0x4000,"ERTH","Earth attacks",0},{0x2000,"FIRE","Fire attacks",0},{0x1000,"WATR","Water attacks",0} };
static const StE G0[] = { {0x0400,"STOP","Stop",1},{0x0200,"EP-","EP DOWN",1},{0x0100,"MUTE","Ether engine stopped",1},{0x0080,"LEAK","Fuel leak",1},{0x0040,"DEF-","Def DOWN",1},{0x0020,"SLOW","Slow",1},{0x0010,"ACC-","ACC/EV DOWN",1},{0x0004,"PWR-","Power loss",1} };
static const StE G1[] = { {0x1000,"PWR+","Power UP",0},{0x0800,"ACC+","ACC UP",0},{0x0400,"EV+","EV UP",0},{0x0040,"ETH+","Eth effect UP",0},{0x0020,"EDF+","Eth Def UP",0},{0x000A,"ATK+","Atk UP/Def DOWN",0},{0x0005,"DEF+","Def UP/Atk DOWN",0} };
#define N(a) (int)(sizeof a / sizeof a[0])
static const StW ST_FOOT[] = { {0x7C,0,F0,N(F0)},{0x80,0,F1,N(F1)},{0x84,0x86,F2,N(F2)},{0x88,0x8A,F3,N(F3)},{0x8C,0x8E,F4,N(F4)} };
static const StW ST_GEAR[] = { {0x120,0,G0,N(G0)},{0x124,0,G1,N(G1)} };
/* the status effects on slot s, ailments first; returns how many */
static int statusList(int s, const StE **out, int cap) {
    unsigned b = SLOTB(s); int gear = u8at(b + 0x15A) & 0x80, n = 0;
    const StW *w = gear ? ST_GEAR : ST_FOOT; int nw = gear ? N(ST_GEAR) : N(ST_FOOT);
    for (int pass = 1; pass >= 0; pass--) for (int i = 0; i < nw; i++) {
        unsigned v = u16at(b + w[i].w0) | (w[i].w1 ? u16at(b + w[i].w1) : 0);
        for (int k = 0; k < w[i].n; k++) if ((v & w[i].e[k].mask) && w[i].e[k].bad == pass && n < cap) out[n++] = &w[i].e[k];
    }
    return n;
}
/* the tag after an HP bar: the first status, + if there are more */
static int statusTag(int s, char *t) {
    const StE *l[16]; int n = statusList(s, l, 16);
    if (!n) { t[0] = 0; return 0; }
    snprintf(t, 8, "%s%s", l[0]->tag, n > 1 ? "+" : "");
    return l[0]->bad ? RED : GREEN;
}
static int hpCol(int hp, int m) { return hp * 4 <= m ? RED : hp * 2 <= m ? YELLOW : WHITE; }

/* ---- pictures of the buttons ---- */
static const char *const BTNPX[3][7] = {
    { "...#...", "...#...", "..#.#..", "..#.#..", ".#...#.", ".#...#.", "#######" },
    { "#######", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#######" },
    { "#.....#", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "#.....#" } };
static void btnPic(char b, int x, int y) {
    int k = b == 'T' ? 0 : b == 'S' ? 1 : 2; uint16_t c = k == 0 ? RGB(85, 221, 153) : k == 1 ? RGB(238, 136, 170) : RGB(119, 170, 255);
    for (int j = 0; j < 7; j++) for (int i = 0; i < 7; i++) if (BTNPX[k][j][i] == '#' && (unsigned)(x + i) < LINK_W && (unsigned)(y + j) < LINK_H) fb[(y + j) * LINK_W + x + i] = c;
}
static const char *const COMBO[] = { "TX","TTX","SX","TTTX","TSX","STX","XX","TTTTX","TTSX","TSTX","STTX","SSX","TXX","XTX" };
#define NCOMBO N(COMBO)
static int comboAP(int i) { int ap = 0; if (i < NCOMBO) for (const char *c = COMBO[i]; *c; c++) ap += *c == 'T' ? 1 : *c == 'S' ? 2 : 3; return ap; }
/* draws it ending at x; returns the x it starts at */
static int comboPic(const char *c, int xr, int y) { int n = (int)strlen(c), x = xr - n * 8; for (int i = 0; i < n; i++) btnPic(c[i], x + i * 8, y); return x; }

/* ------------------------------------------------------------------ deathblows */
typedef struct { int i, got, need, have, lock, lv; const Blow *b; } Row;
static int dbRows(int id, Row *out) {                              /* dbRows in Link */
    if (id < 0 || id >= N(DBLOW)) return 0;
    unsigned b = A_CHAR + id * REC, mask = u16at(A_SKILL + id * 0x20 + 4); int lv = u8at(b + 0x62), n = 0;
    for (int i = 0; i < DBLOW[id].n && i < 16; i++) {
        const Blow *q = &DBLOW[id].b[i]; if (!q->n) continue;
        int need = 0, have = 0;
        for (int k = 0; k < 7; k++) { int p = u16at(b + 0x90 + k * 2); need += q->r[k]; have += q->r[k] < p ? q->r[k] : p; }
        if (!need) continue;
        out[n].i = i; out[n].b = q; out[n].need = need; out[n].have = have; out[n].got = (mask >> (15 - i)) & 1;
        out[n].lv = q->lv; out[n].lock = !out[n].got && q->lv > lv; n++;
    }
    return n;
}
static int gdbGot(int id, int i) { return (u16at(A_SKILL + id * 0x20 + 8) >> (12 - i)) & 1; }

/* the pop-up: which, and for whom. It's rebuilt each draw, so the numbers stay live. */
enum { POP_NONE, POP_ENEMY, POP_BLOW, POP_GBLOW };
static int popKind, popA, popB, popC_; static const char *popName; static int popMhp;
int fight_popClose(void) { if (!popKind) return 0; popKind = POP_NONE; return 1; }
static void gdbKeys(int i, char *t) { static const char B[] = "TSX"; t[0] = B[i / 3]; t[1] = B[i % 3]; t[2] = 0; }

static void popBlow(int id, int i) {
    Row r[16]; int n = dbRows(id, r); const Row *d = NULL; char s[48];
    for (int k = 0; k < n; k++) if (r[k].i == i) d = &r[k];
    if (!d) { popKind = POP_NONE; return; }
    int pc = d->have * 100 / d->need; if (pc > 99) pc = 99;
    popLine(d->b->n, YELLOW);
    snprintf(s, sizeof s, "%s  %s  AP %d", charName(id), i < NCOMBO ? COMBO[i] : "", comboAP(i)); popLine(s, CYAN);
    if (d->got) popLine("LEARNED", GREEN);
    else if (d->lock) popLine("LOCKED", RED);
    else { snprintf(s, sizeof s, "LEARNING %d%%", pc); popLine(s, YELLOW); }
    popLine("TO LEARN", CYAN);
    unsigned b = A_CHAR + id * REC; int clv = u8at(b + 0x62);
    if (d->lv && d->lv < 255) { snprintf(s, sizeof s, "LEVEL %d   NOW %d", d->lv, clv); popLine(s, d->got || clv >= d->lv ? GREEN : RED); }
    static const char *const AT[7] = { "Triangle 1st", "Triangle 2nd", "Triangle 3rd", "Triangle 4th", "Square 1st", "Square 2nd", "Cross" };
    for (int k = 0; k < 7; k++) {
        if (!d->b->r[k]) continue;
        int p = u16at(b + 0x90 + k * 2), hv = d->got ? d->b->r[k] : p < d->b->r[k] ? p : d->b->r[k];
        snprintf(s, sizeof s, "%-13s %3d/%3d", AT[k], hv, d->b->r[k]); popLine(s, hv >= d->b->r[k] ? GREEN : WHITE);
    }
    popLine("Points come from using each attack.", GREY);
}
static void popGBlow(int g, int id, int i) {
    if (g < 0 || g >= N(GDBLOW) || !GDBLOW[g][i]) { popKind = POP_NONE; return; }
    char s[48], k[3]; int got = gdbGot(id, i), lv = i / 3 + 1;
    popLine(GDBLOW[g][i], YELLOW);
    if (i < 9) { gdbKeys(i, k); snprintf(s, sizeof s, "%s  %s  LV %d", gearName(g), k, lv); } else snprintf(s, sizeof s, "%s  INFINITY", gearName(g));
    popLine(s, CYAN);
    popLine(got ? "UNLOCKED" : "LOCKED", got ? GREEN : RED);
    if (i < 9) { snprintf(s, sizeof s, "Needs attack level %d in the fight.", lv); popLine(s, WHITE); }
    popLine("TO UNLOCK", CYAN);
    const char *src = NULL;
    if (i < 9 && i % 3 < 2 && id < N(DBLOW) && (lv - 1) * 2 + i % 3 < DBLOW[id].n) src = DBLOW[id].b[(lv - 1) * 2 + i % 3].n;
    Row r[16]; int n = src ? dbRows(id, r) : 0; const Row *d = NULL;
    for (int q = 0; q < n; q++) if (!strcmp(r[q].b->n, src)) d = &r[q];
    if (d) { snprintf(s, sizeof s, "%s learns %s", charName(id), src); popLine(s, WHITE);
             if (d->got) popLine("DONE", GREEN); else if (d->lock) { snprintf(s, sizeof s, "needs level %d", d->lv); popLine(s, YELLOW); } else { snprintf(s, sizeof s, "%d%%", d->have * 100 / d->need); popLine(s, YELLOW); } }
    else popLine(i < 9 ? "Not known for this move." : "Not known for infinity moves.", GREY);
}
/* showEnemy in Link */
static const char *bossTip(const char *name) {
    int st = u16at(A_STORY);
    if (!name) return NULL;
    for (int i = 0; i < N(BOSSTIP); i++) if (!strcasecmp(BOSSTIP[i].n, name) && (BOSSTIP[i].a < 0 || (st >= BOSSTIP[i].a && st <= BOSSTIP[i].b))) return BOSSTIP[i].tip;
    return NULL;
}
static const char *dropName(int bag, int id) {
    const char *const *t = NULL; int n = 0;
    if (bag == 1) { t = NAMES_equipment; n = N(NAMES_equipment); } else if (bag == 2) { t = NAMES_items; n = N(NAMES_items); }
    else if (bag == 3) { t = NAMES_gear_weapons; n = N(NAMES_gear_weapons); } else if (bag == 4) { t = NAMES_gear_parts; n = N(NAMES_gear_parts); }
    return t && id < n ? t[id] : NULL;
}
static void popEnemy(int s) {
    unsigned b = SLOTB(s); char t[48];
    popLine(popName ? popName : "Enemy", RED);
    int hp = u16at(b + 0x4C), gm = (int)u32at(b + REC + 0x64); if (gm > 0) hp = (int)u32at(b + REC + 0x60);
    if (popMhp) { snprintf(t, sizeof t, "HP %d / %d", hp, popMhp); popLine(t, WHITE); }
    const char *tip = bossTip(popName); if (tip) popWrap(tip, 36, GREEN);
    snprintf(t, sizeof t, "EXP %d   GOLD %d", (int)u32at(b + 0x14C), u16at(b + 0x156)); popLine(t, CYAN);
    int drops = 0;
    for (int k = 0; k < 2; k++) {
        int ch = u8at(b + 0x150 + k), id = u8at(b + 0x152 + k), li = u8at(b + 0x154 + k); const char *n = id ? dropName(li, id) : NULL;
        if (n) { snprintf(t, sizeof t, "%-24s %3d%%", n, ch); popLine(t, WHITE); drops++; }
    }
    if (!drops) popLine("No drops.", GREY);
    const StE *l[16]; int ns = statusList(s, l, 16);
    if (ns) { popLine("STATUS", CYAN); for (int i = 0; i < ns; i++) popLine(l[i]->name, l[i]->bad ? RED : GREEN); }
    /* immune */
    { int gear = u8at(b + 0x15A) & 0x80, all = 1, n = 0; char im[200] = "";
      for (int w = 0; w < (gear ? 1 : 2); w++) {
          unsigned v = u16at(b + (gear ? 0x122 : w ? 0x82 : 0x7E)); const StW *sw = gear ? &ST_GEAR[0] : &ST_FOOT[w];
          for (int k = 0; k < sw->n; k++) { if (v & sw->e[k].mask) { if (n++) strncat(im, ", ", sizeof im - strlen(im) - 1); strncat(im, sw->e[k].name, sizeof im - strlen(im) - 1); } else all = 0; }
      }
      if (n) { popLine("IMMUNE TO", CYAN); popWrap(all ? "All ailments" : im, 36, ORANGE); } }
    /* elements */
    { static const struct { int bit; const char *n; int opp; } EL[] = { {1,"Water",2},{2,"Fire",1},{4,"Earth",8},{8,"Wind",4},{16,"Dark",0},{32,"Light",0} };
      int wk = u8at(b + 0x38), fl = u8at(b + 0x15A), o = fl & 0x80 ? 0x128 : 0x8C; unsigned d = u16at(b + o) | u16at(b + o + 2); int def = (d >> 8) & 15, head = 0;
      for (int i = 0; i < 6; i++) {
          int m = wk & EL[i].bit ? (wk & 0x40 ? 18 : 15) : 10, ab = 0;
          if (def & EL[i].bit) { m -= d & 4 ? 6 : 3; ab = (d & 8) != 0; }
          if (EL[i].opp && (def & EL[i].opp)) m += 3;
          if (m < 1) m = 1;
          if (m == 10 && !ab) continue;
          if (!head++) popLine("ELEMENTS", CYAN);
          if (ab) snprintf(t, sizeof t, "%-6s ABSORBS", EL[i].n); else snprintf(t, sizeof t, "%-6s x%d.%d", EL[i].n, m / 10, m % 10);
          popLine(t, m > 10 && !ab ? GREEN : RED);
      } }
}
void fight_popup(void) {
    if (!popKind) return;
    popReset();
    if (popKind == POP_ENEMY) popEnemy(popA);
    else if (popKind == POP_BLOW) popBlow(popA, popB);
    else if (popKind == POP_GBLOW) popGBlow(popA, popB, popC_);
    if (popKind) popDraw();
}

/* ------------------------------------------------------------------ FIGHT */
#define FY0 20
#define FY1 (LINK_H - 14)
#define COLX 160
static struct { short y0, y1, s, mhp; const char *name; } enemyRow[8]; static int nEnemyRow;
static struct { short y0, y1, s; } partyRow[3]; static int nPartyRow;
static struct { short y0, i, gear; } blowRow[20]; static int nBlowRow, blowId, blowG;

static void sprite(int spr, int x, int y, int boxW, int boxH) {    /* fitted to a box, nearest pixel; 0 is see-through */
    int w, h; const uint16_t *p = pak_sprite(spr, &w, &h); if (!p) return;
    int dw = w, dh = h;
    if (dw > boxW) { dh = dh * boxW / dw; dw = boxW; }
    if (dh > boxH) { dw = dw * boxH / dh; dh = boxH; }
    if (dw < 1) dw = 1;
    if (dh < 1) dh = 1;
    int ox = x + (boxW - dw) / 2, oy = y + (boxH - dh) / 2;
    for (int j = 0; j < dh; j++) { const uint16_t *row = p + (j * h / dh) * w; uint16_t *q = fb + (oy + j) * LINK_W + ox; for (int i = 0; i < dw; i++) { uint16_t v = row[i * w / dw]; if (v) q[i] = v; } }
}
/* the deathblow list at (x, y) in a column ending at xr */
static void blowList(int id, int gear, int x, int y, int xr, int maxY, int all) {
    nBlowRow = 0; blowId = id; blowG = gear;
    if (gear >= 0 && gear < N(GDBLOW)) {
        textn(gearName(gear), x, y, (xr - x) / 8 - 3, GREEN); text("LV", xr - 16, y, CYAN); y += 10;
        int n = 0;
        for (int i = 0; i < 14 && y < maxY; i++) {
            const char *nm = GDBLOW[gear][i]; if (!nm) continue;
            int g = gdbGot(id, i); if (!g && !all) continue;
            textn(nm, x, y, (xr - x) / 8 - 5, g ? WHITE : GREY);
            if (i < 9) { char k[3]; gdbKeys(i, k); comboPic(k, xr - 10, y); textf(xr - 8, y, CYAN, "%d", i / 3 + 1, 0); } else text("INF", xr - 24, y, YELLOW);
            if (nBlowRow < 20) { blowRow[nBlowRow].y0 = (short)y; blowRow[nBlowRow].i = (short)i; blowRow[nBlowRow].gear = 1; nBlowRow++; }
            y += 10; n++;
        }
        if (!n) text("No gear deathblows.", x, y, GREY);
        return;
    }
    Row r[16]; int n = dbRows(id, r), shown = 0;
    for (int i = 0; i < n && y < maxY; i++) {
        const Row *d = &r[i]; if (!d->got && !all) continue;
        int pc = d->have * 100 / d->need; if (pc > 99) pc = 99;
        textn(d->b->n, x, y, (xr - x) / 8 - (all ? 10 : 8), d->got ? WHITE : GREY);
        char t[8];
        if (d->got) { snprintf(t, sizeof t, "%d", comboAP(d->i)); text(t, xr - 8, y, CYAN); }
        else if (d->lock) { snprintf(t, sizeof t, "L%d", d->lv); text(t, xr - 8 * (int)strlen(t), y, GREY); }
        else { snprintf(t, sizeof t, "%d%%", pc); text(t, xr - 8 * (int)strlen(t), y, YELLOW); }
        if (d->i < NCOMBO) comboPic(COMBO[d->i], xr - 26, y);
        if (nBlowRow < 20) { blowRow[nBlowRow].y0 = (short)y; blowRow[nBlowRow].i = (short)d->i; blowRow[nBlowRow].gear = 0; nBlowRow++; }
        y += 10; shown++;
    }
    if (!shown) wrap(all ? "No deathblows." : "None yet. Keep using attack combos: BLOWS shows how far along.", x, y, (xr - x) / 8, GREY);
}
static void battlerPage(void) {
    static const char *const BTLN[] = {"WELTALL","VIERGE","HEIMDAL","BRIGANDIER","RENMAZUO","STIER","BLADEGASH","SIEBZEHN","CRESCENS","CHU-CHU","WELTALL-2","XENOGEARS","EL-REGRS","EL-FENRIR","EL-ANDVARI","EL-RENMAZUO","EL-STIER","GANADOR","TITAN","W-SHAVER","FIREWHEEL","SILVERSTAR","ARGENTO","MUSHA","HATAMOTO","BACKFIRER","SHINOBI","WYRM","TIN ROBO","RANKAR","ETONE1","ETONE2","GOLEM","FIXBOT","WORKER","DOZER","DEATH","MERMAN","SALVAGER","TROOPER","TWINBURNER","S-TROOPER","S-TRIPPER","SUFAL","EG-GUNNER","EG-ARMOR","PEDESTAL","EDIN","EG-BLADE"};
    int y = 30;
    text("BATTLE ARENA", 4, 22, YELLOW);
    for (int k = 0; k < 2; k++) {
        unsigned base = k ? A_BTLE : A_BTLP; int hp = s16at(base), mh = s16at(base + 8), ht = s16at(base + 2); unsigned ix = u32at(A_BTLIX + k * 4);
        if (mh <= 0 || mh > 9999) { text("Waiting for the match to start.", 4, 40, GREY); return; }
        if (hp < 0) hp = 0;
        if (ht < 0) ht = 0;
        y += 6;
        text(k ? "OPPONENT" : "YOU", 4, y, GREY); text(ix < N(BTLN) ? BTLN[ix] : "?", 80, y, k ? RED : CYAN); y += 12;
        meter(4, y, 312, hp, mh, GREEN); y += 8;
        textf(4, y, hp * 4 <= mh ? RED : WHITE, "%d / %d", hp, mh); y += 12;
        text("HEAT", 4, y, GREY); meter(44, y + 2, 240, ht > 3264 ? 3264 : ht, 3264, ORANGE); if (ht >= 3264) text("MAX", 290, y, RED);
        y += 18;
    }
}
void fight_page(void) {
    unsigned sig = u32at(A_SIG);
    nEnemyRow = nPartyRow = nBlowRow = 0;
    if (sig == 7) { battlerPage(); return; }
    if (sig != 6) { text("No fight right now.", 4, 40, GREY); wrap("In a battle this page shows the enemies, the party and their deathblows.", 4, 56, 38, GREY); return; }
    /* the eight enemy slots */
    int anyLive = 0, s;
    for (s = 3; s < 11; s++) if (u8at(A_BLIVE + s)) anyLive = 1;
    int hps[11], mhps[11], gearE[11];
    for (s = 3; s < 11; s++) {
        unsigned b = SLOTB(s); int hp = u16at(b + 0x4C), mhp = u16at(b + 0x4E), ghp = (int)u32at(b + REC + 0x60), gm = (int)u32at(b + REC + 0x64);
        Slot *q = &sl[s - 3];
        q->m = mhp; q->g = gm; q->x = (int)u32at(b + 0x14C); q->gd = u16at(b + 0x156); q->on = !anyLive || u8at(A_BLIVE + s); q->has = 1;
        for (int k = 0; k < 6; k++) q->d[k] = (uint8_t)u8at(b + 0x150 + k);
        for (int k = 0; k < 8; k++) q->st[k] = (uint8_t)u8at(b + 0x58 + k);
        if (gm > 0) { hp = ghp; mhp = gm; }
        hps[s] = hp; mhps[s] = mhp; gearE[s] = gm > 0;
    }
    enemyNames();
    /* an enemy keeps the name and picture it had earlier in the fight */
    Name nm[8];
    for (int i = 0; i < 8; i++) { int k = i + 3; nm[i] = names[i]; if (nm[i].n) slotMem[k] = nm[i]; else if (slotMem[k].n) { nm[i].n = slotMem[k].n; if (nm[i].spr < 0) nm[i].spr = slotMem[k].spr; } }
    /* who to list */
    typedef struct { int s, hp, mhp, ko, off, wait; const char *name; char own[12]; int spr; } En;
    static En ens[8]; int ne = 0, pty[3], np = 0;
    for (int i = 0; i < 3; i++) { int p = u8at(A_BPID + i); if (p <= 10) pty[np++] = p; }
    for (s = 3; s < 11; s++) {
        if (!mhps[s] || (anyLive && !u8at(A_BLIVE + s))) continue;
        Name *n = &nm[s - 3];
        if (n->hide || (n->n && !strcmp(n->n, "Margie"))) continue;
        En *e = &ens[ne]; e->s = s; e->hp = hps[s]; e->spr = n->spr;
        /* fixFoe: Bart's unwinnable fight with Grahf uses the Rankar's record */
        const char *name = n->n;
        if (name && !strcmp(name, "Rankar Dragon") && mhps[s] >= 99000) { int bart = 0, fei = 0; for (int i = 0; i < np; i++) { if (pty[i] == 3) bart = 1; if (!pty[i]) fei = 1; } if (bart && !fei) { name = "Grahf"; e->spr = SPR_GRAHF; } }
        if (name) e->name = name; else { snprintf(e->own, sizeof e->own, "Enemy %d", s - 2); e->name = e->own; }
        /* full HP = the enemy's starting HP, and never less than the most HP seen on it this fight */
        uint32_t fk = (uint32_t)s * 1000003u ^ (uint32_t)mhps[s] * 31u ^ (uint32_t)sl[s - 3].x;
        if (hpKey[s] != fk) { hpKey[s] = fk; hpSeen[s] = 0; }
        if (e->hp > hpSeen[s]) hpSeen[s] = e->hp;
        int top = hpSeen[s] > n->st ? hpSeen[s] : n->st;
        e->mhp = mhps[s] < top ? mhps[s] : top; if (!e->mhp) e->mhp = mhps[s];
        e->ko = (u16at(SLOTB(s) + 0x7C) & 0x8000) != 0;
        e->off = offField(s, e->hp, e->name);
        (void)gearE;
        ne++;
    }
    for (int i = 0; i < ne; i++) { int same = 0; for (int j = 0; j < ne; j++) if (!ens[j].off && !strcmp(ens[j].name, ens[i].name)) same = 1; ens[i].wait = ens[i].off && !same; }
    { int allOut = ne > 0, someHp = 0; for (int i = 0; i < ne; i++) { if (!(ens[i].wait || !ens[i].hp)) allOut = 0; if (ens[i].hp > 0) someHp = 1; } if (allOut && someHp) for (int i = 0; i < ne; i++) if (ens[i].hp > 0) ens[i].wait = 0; }
    int shown = 0, tx = 0, tg = 0, needNum = 0;
    for (int i = 0; i < ne; i++) if (!ens[i].wait) { shown++; tx += (int)u32at(SLOTB(ens[i].s) + 0x14C); tg += u16at(SLOTB(ens[i].s) + 0x156); if (!enemyId[ens[i].s]) needNum = 1; }
    if (needNum) { memset(enemyId, 0, sizeof enemyId); int n = 1; for (int i = 0; i < ne; i++) if (!ens[i].wait) enemyId[ens[i].s] = n++; }
    /* the order they act in (turnRanks): by countdown; 1 = now or next */
    int rank[11]; memset(rank, 0, sizeof rank);
    { struct { int s, v; } l[11]; int n = 0, any = 0, act = u8at(A_BTURN);
      for (int i = 0; i < 3; i++) { int p = u8at(A_BPID + i); if (p > 10) continue; unsigned b = SLOTB(i); int alive = (u8at(b + 0x15A) & 0x80) ? u32at(b + REC + 0x60) > 0 : u16at(b + 0x4C) > 0; if (alive && u8at(A_BGONE + i) != 0xFF) { int v = u16at(A_BTIME + i * 2), rd = u8at(A_BGONE + i) == 1; if (v || rd) any = 1; l[n].s = i; l[n].v = i == act && rd ? -1 : rd ? 0 : v; n++; } }
      for (int i = 0; i < ne; i++) { int q = ens[i].s; if (ens[i].ko || ens[i].wait || u8at(A_BGONE + q) == 0xFF) continue; int v = u16at(A_BTIME + q * 2), rd = u8at(A_BGONE + q) == 1; if (v || rd) any = 1; l[n].s = q; l[n].v = q == act && rd ? -1 : rd ? 0 : v; n++; }
      if (any && n >= 2) { for (int i = 1; i < n; i++) { int j = i; while (j > 0 && (l[j - 1].v > l[j].v || (l[j - 1].v == l[j].v && l[j - 1].s > l[j].s))) { int ts = l[j].s, tv = l[j].v; l[j].s = l[j - 1].s; l[j].v = l[j - 1].v; l[j - 1].s = ts; l[j - 1].v = tv; j--; } } for (int i = 0; i < n; i++) rank[l[i].s] = i + 1; } }

    /* left: the enemies */
    rect(COLX - 1, FY0, 1, FY1 - FY0, BAR);
    int area = FY1 - FY0 - (shown <= 5 ? 12 : 0), ch = shown ? area / shown : area; if (ch > 38) ch = 38;
    int y = FY0 + 1;
    if (!shown) wrap("Reading the fight...", 4, y + 4, 19, GREY);
    for (int i = 0; i < ne; i++) {
        En *e = &ens[i]; if (e->wait) continue;
        int w0 = 30;
        if (e->spr >= 0) sprite(e->spr, 1, y, 28, ch - 1); else w0 = 2;
        int ty = y + (ch - 18) / 2; if (ty < y) ty = y;
        int tip = bossTip(e->name) != NULL;
        textn(e->name, w0, ty, (COLX - w0 - 2 - (tip ? 8 : 0)) / 8, e->ko ? GREY : RED);
        if (tip) text("!", COLX - 10, ty, YELLOW);
        char t[8], hp[10];
        int tc = e->ko ? 0 : statusTag(e->s, t); if (e->ko) t[0] = 0;
        snprintf(hp, sizeof hp, "%d", e->hp);
        int x = w0, xr = COLX - 3 - 8 * (int)strlen(hp);
        if (rank[e->s]) { textf(x, ty + 10, CYAN, "%d", rank[e->s], 0); x += rank[e->s] > 9 ? 18 : 10; }
        if (t[0]) { xr -= 8 * (int)strlen(t) + 2; text(t, xr + 1, ty + 10, tc); }
        meter(x, ty + 11, xr - x - 2 > 8 ? xr - x - 2 : 8, e->hp, e->mhp, RED);
        text(hp, COLX - 3 - 8 * (int)strlen(hp), ty + 10, e->ko ? GREY : hpCol(e->hp, e->mhp));
        if (nEnemyRow < 8) { enemyRow[nEnemyRow].y0 = (short)y; enemyRow[nEnemyRow].y1 = (short)(y + ch); enemyRow[nEnemyRow].s = (short)e->s; enemyRow[nEnemyRow].mhp = (short)(e->mhp > 32000 ? 32000 : e->mhp); enemyRow[nEnemyRow].name = e->name; nEnemyRow++; }
        y += ch;
    }
    if (shown && shown <= 5) { char t[32]; snprintf(t, sizeof t, "%d EXP  %d G", tx, tg); textn(t, 2, FY1 - 10, 19, YELLOW); }

    /* right: the party, then the deathblows of the one acting (or tapped) */
    int act = u8at(A_BTURN); if (act > 2) act = -1;
    if (act >= 0 && act != lastAct) dbSel = act;
    lastAct = act;
    { int id0 = u8at(A_BPID + dbSel); if (id0 > 10) for (int i = 2; i >= 0; i--) if (u8at(A_BPID + i) <= 10) dbSel = i; }
    y = FY0 + 1; int selGear = -1, selId = -1;
    for (int i = 0; i < 3; i++) {
        int id = u8at(A_BPID + i); if (id > 10) continue;
        unsigned b = SLOTB(i); int ing = (u8at(b + 0x15A) & 0x80) != 0, gr = b + REC, x = COLX + 1, sel = i == dbSel;
        int hp = u16at(b + 0x4C), mh = u16at(b + 0x4E), ep = u16at(b + 0x50), mep = u16at(b + 0x52);
        if (ing) { hp = (int)u32at(gr + 0x60); mh = (int)u32at(gr + 0x64); }
        int ko = hp == 0;
        if (sel) { selId = id; selGear = ing ? (int)u8at(b + 0xA0) : -1; rect(x - 1, y - 1, LINK_W - x + 1, 21, BAR); }
        if (rank[i]) { textf(x, y, CYAN, "%d", rank[i], 0); x += 9; }
        textn(charName(id), x, y, 7, ko ? GREY : sel ? WHITE : YELLOW);
        { char t[16]; snprintf(t, sizeof t, "%d/%d", hp, mh); if (strlen(t) > 11) snprintf(t, sizeof t, "%d", hp); text(t, LINK_W - 2 - 8 * (int)strlen(t), y, ko ? GREY : hpCol(hp, mh)); }
        char tg2[8]; int tc = ko ? 0 : statusTag(i, tg2); if (ko) tg2[0] = 0;
        int xr = LINK_W - 2;
        if (ing) { char t[12]; snprintf(t, sizeof t, "F%d", u16at(gr + 0x38)); xr -= 8 * (int)strlen(t); text(t, xr, y + 10, ORANGE); }
        else { char t[12]; snprintf(t, sizeof t, "E%d", ep); xr -= 8 * (int)strlen(t); text(t, xr, y + 10, CYAN); (void)mep; }
        if (tg2[0]) { xr -= 8 * (int)strlen(tg2) + 2; text(tg2, xr, y + 10, tc); }
        meter(COLX + 1, y + 11, xr - COLX - 3, hp, mh, GREEN);
        if (nPartyRow < 3) { partyRow[nPartyRow].y0 = (short)y; partyRow[nPartyRow].y1 = (short)(y + 21); partyRow[nPartyRow].s = (short)i; nPartyRow++; }
        y += 22;
    }
    rect(COLX, y, LINK_W - COLX, 1, BAR);
    if (selId >= 0) blowList(selId, selGear, COLX + 1, y + 3, LINK_W - 1, FY1 - 8, 0);
}
int fight_tap(int x, int y) {
    if (u32at(A_SIG) != 6) return 0;
    if (x < COLX) {
        for (int i = 0; i < nEnemyRow; i++) if (y >= enemyRow[i].y0 && y < enemyRow[i].y1) { popKind = POP_ENEMY; popA = enemyRow[i].s; popName = enemyRow[i].name; popMhp = enemyRow[i].mhp; return 1; }
        return 0;
    }
    for (int i = 0; i < nPartyRow; i++) if (y >= partyRow[i].y0 && y < partyRow[i].y1) { dbSel = partyRow[i].s; return 1; }
    for (int i = 0; i < nBlowRow; i++) if (y >= blowRow[i].y0 && y < blowRow[i].y0 + 10) {
        if (blowRow[i].gear) { popKind = POP_GBLOW; popA = blowG; popB = blowId; popC_ = blowRow[i].i; }
        else { popKind = POP_BLOW; popA = blowId; popB = blowRow[i].i; }
        return 1;
    }
    return 0;
}

/* ------------------------------------------------------------------ BLOWS: the same list at any time, with what's still to learn */
static int blowsWho, blowsGear;
static struct { short x0, x1, i; } chip[3]; static int nChip; static short gearChip;
void blows_page(void) {
    int y = 22, x = 2; nChip = 0; nBlowRow = 0;
    int ids[3], n = 0;
    for (int i = 0; i < 3; i++) { int id = u8at(A_PARTY + i); if (id <= 10) ids[n++] = id; }
    if (!n) { text("The party isn't known yet.", 4, 40, GREY); return; }
    if (blowsWho >= n) blowsWho = 0;
    for (int i = 0; i < n; i++) {
        const char *nm = charName(ids[i]); int w = 8 * ((int)strlen(nm) > 7 ? 7 : (int)strlen(nm)) + 8;
        rect(x, y, w, 14, i == blowsWho ? CYAN : BAR); textn(nm, x + 4, y + 3, 7, i == blowsWho ? DARK : WHITE);
        chip[nChip].x0 = (short)x; chip[nChip].x1 = (short)(x + w); chip[nChip].i = (short)i; nChip++;
        x += w + 2;
    }
    int id = ids[blowsWho], g = u8at(A_CHAR + id * REC + 0xA0);
    gearChip = -1;
    if (g < 20) { gearChip = LINK_W - 44; rect(gearChip, y, 42, 14, blowsGear ? CYAN : BAR); text("GEAR", gearChip + 5, y + 3, blowsGear ? DARK : WHITE); }
    y += 18;
    if (!blowsGear || g >= 20) { textf(4, y, GREY, "AP per turn %d", u8at(A_SKILL + id * 0x20 + 0x1B), 0); y += 12; }
    blowList(id, blowsGear && g < 20 ? g : -1, 4, y, LINK_W - 4, FY1 - 8, 1);
}
int blows_tap(int x, int y) {
    if (y < 38) {
        for (int i = 0; i < nChip; i++) if (x >= chip[i].x0 && x < chip[i].x1) { blowsWho = chip[i].i; return 1; }
        if (gearChip >= 0 && x >= gearChip) { blowsGear = !blowsGear; return 1; }
        return 0;
    }
    for (int i = 0; i < nBlowRow; i++) if (y >= blowRow[i].y0 && y < blowRow[i].y0 + 10) {
        if (blowRow[i].gear) { popKind = POP_GBLOW; popA = blowG; popB = blowId; popC_ = blowRow[i].i; }
        else { popKind = POP_BLOW; popA = blowId; popB = blowRow[i].i; }
        return 1;
    }
    return 0;
}
