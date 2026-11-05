/* linkmap.c - the MAP tab and the picture pack. A room's overhead picture (from xenogears-link.pak) turned so that up is the way the
 * game's camera looks, as drawMap in Link's index.html; on it the treasure (yellow box, grey once taken), gifts (blue dot), missables
 * not yet taken (orange ring), memory cubes and shops, the story hint's green spots, and the party. Tap: an icon's name, or whole room /
 * close-up. LIST: everything in the room. On the world map: the map, places, spots and the party. No guide line, exits or 3D. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "linkint.h"
#include "linkdata.h"

/* Link's addresses for the map */
#define A_ACTORS 0xAFB10
#define A_PIDX   0xB226C
#define A_CAMEYE 0xAF880
#define A_CAMAT  0xAF890
#define A_WPOS   0x9D55C
#define A_WSTART 0x9C5AC
#define A_WLOC   0x9BD00
#define A_WCHUNK 0x9C184
#define A_IQTY   0x6F5C4
#define A_IID    0x6F65A
#define AREC     0x5C

/* the map's part of the screen */
#define MY0 20
#define MH  204
#define MW  LINK_W

/* ------------------------------------------------------------------ the pack */
typedef struct { uint32_t key, off; uint16_t w, h; } PakEnt;
static FILE *pak; static PakEnt *pakIx; static uint32_t pakN;
#define NROOMTEX 3
static uint16_t roomTex[NROOMTEX][256 * 256]; static int roomKey[NROOMTEX] = { -1, -1, -1 }, roomAge[NROOMTEX], ageNow;
static uint16_t worldTex[512 * 512]; static int worldKey = -1;
#define NSPR 16
static uint16_t sprTex[NSPR][28 * 36]; static int sprKey[NSPR] = { -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 }, sprW[NSPR], sprH[NSPR], sprNext;

void map_open(const char *path) {
    FILE *f = fopen(path, "rb"); char m[4]; uint32_t n;
    if (!f) return;
    if (fread(m, 1, 4, f) != 4 || memcmp(m, "XGPK", 4) || fread(&n, 4, 1, f) != 1 || !n || n > 4096) { fclose(f); return; }
    pakIx = malloc(n * sizeof(PakEnt));
    if (!pakIx || fread(pakIx, sizeof(PakEnt), n, f) != n) { free(pakIx); pakIx = NULL; fclose(f); return; }
    pak = f; pakN = n;
}
int map_havePak(void) { return pak != NULL; }
static const PakEnt *pakFind(uint32_t key) {
    int lo = 0, hi = (int)pakN - 1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (pakIx[m].key == key) return &pakIx[m]; if (pakIx[m].key < key) lo = m + 1; else hi = m - 1; }
    return NULL;
}
static int pakRead(const PakEnt *e, uint16_t *to, size_t cap) {
    size_t n = (size_t)e->w * e->h;
    return n <= cap && !fseek(pak, (long)e->off, SEEK_SET) && fread(to, 2, n, pak) == n;
}
static const uint16_t *roomPic(int room, int level) {
    if (!pak) return NULL;
    int key = (room << 2) | (level + 1);
    const PakEnt *e = pakFind((uint32_t)key);
    if (!e && level >= 0) { key = room << 2; e = pakFind((uint32_t)key); }
    if (!e) return NULL;
    int old = 0;
    for (int i = 0; i < NROOMTEX; i++) {
        if (roomKey[i] == key) { roomAge[i] = ++ageNow; return roomTex[i]; }
        if (roomAge[i] < roomAge[old]) old = i;
    }
    roomKey[old] = -1;
    if (!pakRead(e, roomTex[old], 256 * 256)) return NULL;
    roomKey[old] = key; roomAge[old] = ++ageNow;
    return roomTex[old];
}
static const uint16_t *worldPic(int which) {
    if (!pak) return NULL;
    if (worldKey == which) return worldTex;
    const PakEnt *e = pakFind(0x10000u + which);
    worldKey = -1;
    if (!e || !pakRead(e, worldTex, 512 * 512)) return NULL;
    worldKey = which;
    return worldTex;
}
const uint16_t *pak_sprite(int n, int *w, int *h) {
    if (!pak || n < 0) return NULL;
    for (int i = 0; i < NSPR; i++) if (sprKey[i] == n) { *w = sprW[i]; *h = sprH[i]; return sprTex[i]; }
    const PakEnt *e = pakFind(0x20000u + n);
    if (!e) return NULL;
    int i = sprNext; sprNext = (sprNext + 1) % NSPR;
    sprKey[i] = -1;
    if (!pakRead(e, sprTex[i], 28 * 36)) return NULL;
    sprKey[i] = n; sprW[i] = *w = e->w; sprH[i] = *h = e->h;
    return sprTex[i];
}

/* ------------------------------------------------------------------ what's in the room */
static const Tre *treOf(int room, int *n) {
    int lo = 0, hi = (int)(sizeof TRETAB / sizeof TRETAB[0]) - 1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (TRETAB[m].room == room) { *n = TRETAB[m].n; return TRETAB[m].t; } if (TRETAB[m].room < room) lo = m + 1; else hi = m - 1; }
    *n = 0; return NULL;
}
static const float *planOf(int room) {
    int lo = 0, hi = (int)(sizeof PLANTAB / sizeof PLANTAB[0]) - 1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (PLANTAB[m].room == room) return &PLANTAB[m].x; if (PLANTAB[m].room < room) lo = m + 1; else hi = m - 1; }
    return NULL;
}
static int treGot(const Tre *t) {                                  /* treGot / haveItem in Link */
    if (t->v < 0) { for (int i = 0; i < 150; i++) if (u8at(A_IID + i) == (unsigned)t->bit && u8at(A_IQTY + i) > 0) return 1; return 0; }
    unsigned x = u16at(A_SVAR + t->v);
    return t->bit >= 100 ? x >= (unsigned)(t->bit - 100) : (x >> t->bit & 1);
}
static int playerBlock(void) {                                     /* playerData in Link: the party's movement block, or -1 */
    if (u32at(A_SIG) != 4) return -1;
    int l = ptrOf(u32at(A_ACTORS)); unsigned i = u32at(A_PIDX);
    if (l < 0 || i > 255) return -1;
    return ptrOf(u32at(l + i * AREC + 0x4C));
}
/* the walk layer's own picture, when it has one (mapLevel) */
static int levelNow(int room) {
    int d = playerBlock(); unsigned v = d >= 0 ? u16at(d + 0x10) : 9;
    if (v >= 4) return -1;
    for (size_t i = 0; i < sizeof LEVELTAB / sizeof LEVELTAB[0]; i++) if (LEVELTAB[i].room == room) return LEVELTAB[i].mask >> v & 1 ? (int)v : -1;
    return -1;
}

/* ------------------------------------------------------------------ the view */
static int zoom, showList, capRoom = -1, capIcon = -1;
static float heading[2]; static int headOk, prevX, prevZ, prevRoom = -1;
/* where the icons ended up, for taps */
#define MAXICON 48
static struct { short x, y; short t; } icon[MAXICON]; static int nIcon;
/* the view: screen = centre + (project(world) - c) * sc */
static float vFx, vFz, vCx, vCy, vSc; static int vWorld;
static void toScreen(float x, float z, int *sx, int *sy) {
    if (vWorld) { *sx = (int)(MW / 2 + (x / 32 - vCx) * vSc); *sy = (int)(MY0 + MH / 2 + (z / 32 - vCy) * vSc); return; }
    float u = x * vFz - z * vFx, v = -(x * vFx + z * vFz);
    *sx = (int)(MW / 2 + (u - vCx) * vSc); *sy = (int)(MY0 + MH / 2 + (v - vCy) * vSc);
}
/* a turned nearest-pixel copy of the room's picture into the map area. Fixed point, set up once a draw. */
static void drawRoomPic(const uint16_t *tex, const float *pm) {
    float T = 256.0f / pm[2], inv = 1.0f / vSc;
    /* per screen pixel, in world units: x = u*fz - v*fx, z = -u*fx - v*fz */
    float dxX = vFz * inv * T, dzX = -vFx * inv * T, dxY = -vFx * inv * T, dzY = -vFz * inv * T;
    float u0 = vCx - (MW / 2) * inv, v0 = vCy - (MH / 2) * inv;
    float wx = u0 * vFz - v0 * vFx, wz = -u0 * vFx - v0 * vFz;
    int32_t tx0 = (int32_t)(((wx - pm[0]) * T + 128) * 65536.0f), tz0 = (int32_t)(((wz - pm[1]) * T + 128) * 65536.0f);
    int32_t ax = (int32_t)(dxX * 65536.0f), az = (int32_t)(dzX * 65536.0f), bx = (int32_t)(dxY * 65536.0f), bz = (int32_t)(dzY * 65536.0f);
    uint16_t bg = COL[DARK];
    for (int y = 0; y < MH; y++) {
        uint16_t *p = fb + (MY0 + y) * LINK_W; int32_t tx = tx0, tz = tz0;
        for (int x = 0; x < MW; x++) {
            unsigned ux = (unsigned)tx >> 16, uz = (unsigned)tz >> 16;
            p[x] = (ux | uz) < 256 ? tex[uz << 8 | ux] : bg;
            tx += ax; tz += az;
        }
        tx0 += bx; tz0 += bz;
    }
}
static void spotCb(int x, int z) {
    int sx, sy; toScreen((float)x, (float)z, &sx, &sy);
    if (sy < MY0 || sy >= MY0 + MH) return;
    ring(sx, sy, 6, WHITE); ring(sx, sy, 5, GREEN); ring(sx, sy, 4, WHITE); disc(sx, sy, 2, GREEN);
}
static void marker(int sx, int sy, float hx, float hy) {           /* the party: a white dot with a red point the way they last moved */
    if (hx != 0 || hy != 0) {
        int tx = sx + (int)(hx * 11), ty = sy + (int)(hy * 11), lx = sx - (int)(hy * 4), ly = sy + (int)(hx * 4), rx = sx + (int)(hy * 4), ry = sy - (int)(hx * 4);
        for (int i = 0; i <= 8; i++) { int ax = lx + (rx - lx) * i / 8, ay = ly + (ry - ly) * i / 8; line(ax, ay, tx, ty, RED); }
    }
    ring(sx, sy, 6, DARK); ring(sx, sy, 5, WHITE); disc(sx, sy, 3, WHITE); ring(sx, sy, 3, DARK);
}
static void drawIcons(int room, const Tre *t, int nt) {
    nIcon = 0;
    /* memory cubes and shops */
    for (size_t i = 0; i < sizeof MARKTAB / sizeof MARKTAB[0]; i++) if (MARKTAB[i].room == room) for (int k = 0; k < MARKTAB[i].n; k++) {
        const Mark *m = &MARKTAB[i].m[k]; int sx, sy; toScreen(m->x, m->z, &sx, &sy);
        if (sy < MY0 || sy >= MY0 + MH) continue;
        if (m->kind == 's') { rect(sx - 4, sy - 4, 9, 9, DARK); rect(sx - 3, sy - 3, 7, 7, WHITE); rect(sx - 2, sy - 2, 5, 5, PINK); }
        else { disc(sx, sy, 4, m->kind == 'g' ? GREY : DARK); disc(sx, sy, 3, ORANGE); }
    }
    for (int i = 0; i < nt; i++) {
        if (!t[i].hasPos) continue;
        int sx, sy, got = treGot(&t[i]); toScreen(t[i].x, t[i].z, &sx, &sy);
        if (sy < MY0 + 2 || sy >= MY0 + MH - 2 || sx < 0 || sx >= MW) continue;
        if (nIcon < MAXICON) { icon[nIcon].x = (short)sx; icon[nIcon].y = (short)sy; icon[nIcon].t = (short)i; nIcon++; }
        if (t[i].miss && !got) { ring(sx, sy, 7, ORANGE); ring(sx, sy, 6, ORANGE); }
        if (t[i].gift) {
            if (got) ring(sx, sy, 3, GREY);
            else { disc(sx, sy, 4, DARK); disc(sx, sy, 3, BLUE); }
        } else if (got) {
            rect(sx - 4, sy - 3, 9, 7, DARK); rect(sx - 3, sy - 2, 7, 5, GREY); rect(sx - 2, sy - 1, 5, 3, DARK);
        } else {
            rect(sx - 5, sy - 4, 11, 9, DARK); rect(sx - 4, sy - 3, 9, 7, YELLOW); rect(sx - 4, sy, 9, 1, DARK);
        }
    }
}
static void drawList(const Tre *t, int nt) {
    rect(0, MY0, MW, MH, PANEL);
    int got = 0; for (int i = 0; i < nt; i++) got += treGot(&t[i]);
    textf(4, MY0 + 2, YELLOW, "TREASURE %d/%d", got, nt);
    text("TAP TO CLOSE", MW - 100, MY0 + 2, GREY);
    int y = MY0 + 14;
    for (int i = 0; i < nt && y < MY0 + MH - 8; i++) {
        int g = treGot(&t[i]);
        rect(4, y + 1, 6, 6, g ? GREY : t[i].gift ? BLUE : YELLOW);
        textn(t[i].n, 14, y, 37, g ? GREY : WHITE); y += 10;
        if (t[i].miss && !g && y < MY0 + MH - 8) { char s[48]; snprintf(s, sizeof s, "lost: %s", t[i].miss); textn(s, 22, y, 36, ORANGE); y += 10; }
    }
}
static void drawCaption(const Tre *t, int nt, int room) {
    if (capIcon < 0 || capRoom != room || capIcon >= nt) return;
    const Tre *e = &t[capIcon]; int g = treGot(e), h = e->miss && !g ? 24 : 14;
    rect(0, MY0 + MH - h, MW, h, DARK);
    textn(e->n, 4, MY0 + MH - h + 3, g ? 32 : 39, g ? GREY : YELLOW);
    if (g) text("TAKEN", MW - 44, MY0 + MH - h + 3, GREEN);
    if (e->miss && !g) { char s[48]; snprintf(s, sizeof s, "lost: %s", e->miss); textn(s, 4, MY0 + MH - h + 13, 39, ORANGE); }
}
static const Tre *pageTre; static int pageNt;

static void roomPage(void) {
    int room = u16at(A_FIELD) & 0x7FF, nt, d = playerBlock();
    const Tre *t = treOf(room, &nt); pageTre = t; pageNt = nt;
    const float *pm = planOf(room);
    int level = levelNow(room);
    const uint16_t *tex = pm ? roomPic(room, level) : NULL;
    /* camera (camForward) */
    float dx = (float)(s32at(A_CAMAT) - s32at(A_CAMEYE)), dz = (float)(s32at(A_CAMAT + 8) - s32at(A_CAMEYE + 8)), l = sqrtf(dx * dx + dz * dz);
    vFx = l > 0 ? dx / l : 0; vFz = l > 0 ? dz / l : 1; vWorld = 0;
    int px = 0, pz = 0, have = d >= 0;
    if (have) { px = s32at(d + 0x20) >> 16; pz = s32at(d + 0x28) >> 16; }
    if (room != prevRoom) { prevRoom = room; headOk = 0; prevX = px; prevZ = pz; capIcon = -1; }
    if (have && abs(px - prevX) + abs(pz - prevZ) > 6) {
        float ax = (float)(px - prevX), az = (float)(pz - prevZ), al = sqrtf(ax * ax + az * az);
        if (al < 800) { heading[0] = ax / al; heading[1] = az / al; headOk = 1; }
        prevX = px; prevZ = pz;
    }
    /* the view fits the walkable floor's outline (Link fits the walk mesh), turned with the camera */
    float x0 = 1e9f, x1 = -1e9f, y0 = 1e9f, y1 = -1e9f; int fit = 0;
    for (size_t i = 0; i < sizeof HULLTAB / sizeof HULLTAB[0]; i++) if (HULLTAB[i].room == room) {
        const int16_t *q = HULLTAB[i].p;
        for (int k = 0; k < HULLTAB[i].n; k++) { float u = q[k * 2] * vFz - q[k * 2 + 1] * vFx, v = -(q[k * 2] * vFx + q[k * 2 + 1] * vFz); if (u < x0) x0 = u; if (u > x1) x1 = u; if (v < y0) y0 = v; if (v > y1) y1 = v; fit = 1; }
        break;
    }
    if (!fit) {                                                    /* no outline: the picture's square, or the things we know of */
        float cx = pm ? pm[0] : (float)px, cz = pm ? pm[1] : (float)pz, w = pm ? pm[2] / 2 : 600;
        float u = cx * vFz - cz * vFx, v = -(cx * vFx + cz * vFz);
        x0 = u - w; x1 = u + w; y0 = v - w; y1 = v + w;
    }
    float wa = x1 - x0 < 1 ? 1 : x1 - x0, ha = y1 - y0 < 1 ? 1 : y1 - y0, sa = (MW - 24) / wa, sb = (MH - 24) / ha;
    vSc = sa < sb ? sa : sb; vCx = (x0 + x1) / 2; vCy = (y0 + y1) / 2;
    if (zoom && have) { vSc *= 3; vCx = px * vFz - pz * vFx; vCy = -(px * vFx + pz * vFz); }
    if (tex) drawRoomPic(tex, pm);
    else rect(0, MY0, MW, MH, DARK);
    drawIcons(room, t, nt);
    hintSpots(room, spotCb);
    if (have) {
        int sx, sy; toScreen((float)px, (float)pz, &sx, &sy);
        float hu = headOk ? heading[0] * vFz - heading[1] * vFx : 0, hv = headOk ? -(heading[0] * vFx + heading[1] * vFz) : 0;
        marker(sx, sy, hu, hv);
    }
    /* the name along the top, the button, the message */
    rect(0, MY0, MW, 10, DARK);
    textn(roomName(room), 2, MY0 + 1, 28, WHITE);
    if (nt) {
        int got = 0, ms = 0; for (int i = 0; i < nt; i++) { int g = treGot(&t[i]); got += g; if (t[i].miss && !g) ms++; }
        char s[16]; snprintf(s, sizeof s, "%d/%d", got, nt);
        rect(MW - 72, MY0 + 10, 72, 14, BAR);
        text("LIST", MW - 70, MY0 + 13, WHITE); text(s, MW - 8 * (int)strlen(s) - 2, MY0 + 13, ms ? ORANGE : got == nt ? GREY : YELLOW);
    }
    if (!tex && !showList) {
        text(pak ? "NO PICTURE OF THIS ROOM" : "COPY xenogears-link.pak", 60, MY0 + MH / 2 - 4, GREY);
        if (!pak) text("BESIDE YOUR DISCS", 84, MY0 + MH / 2 + 8, GREY);
    }
    drawCaption(t, nt, room);
    if (showList) drawList(t, nt);
}

/* ---- the world map ---- */
static int wSel, wChunkWas = -1;
static void worldDetect(int x, int z) {                            /* worldDetect in Link: which picture, from the terrain under the party */
    int ci = (z >> 11) * 16 + (x >> 11);
    if (ci == wChunkWas || ci < 0 || ci >= 256) return;
    wChunkWas = ci;
    int q = ptrOf(u32at(A_WCHUNK + ci * 4)); if (q < 0) return;
    uint32_t c = 0; for (int i = 0; i < 1296; i++) c = (c * 31 + u8at(q + i)) & 0xFFFFFF;
    int ia = 0, ib = 0;
    for (int i = WSIX_a[ci]; i < WSIX_a[ci + 1]; i++) if (WSIG_a[i] == c) ia = 1;
    for (int i = WSIX_b[ci]; i < WSIX_b[ci + 1]; i++) if (WSIG_b[i] == c) ib = 1;
    if (ia && !ib) wSel = 0; else if (ib && !ia) wSel = 1;
}
static int worldPos(int *x, int *z) {
    static const unsigned A[2] = { A_WPOS, A_WSTART };
    for (int i = 0; i < 2; i++) {
        int a = s32at(A[i]) >> 12, b = s32at(A[i] + 8) >> 12;
        if (a < 0 || b < 0 || a > 32767 || b > 32767 || (!a && !b)) continue;
        *x = a; *z = b; return 1;
    }
    return 0;
}
static void diamond(int x, int y, int r) {
    for (int j = -r; j <= r; j++) { int w = r - abs(j); rect(x - w, y + j, 2 * w + 1, 1, BLUE); }
    line(x - r - 1, y, x, y - r - 1, DARK); line(x, y - r - 1, x + r + 1, y, DARK); line(x + r + 1, y, x, y + r + 1, DARK); line(x, y + r + 1, x - r - 1, y, DARK);
}
static void worldPlaces(void) {                                    /* worldPlaces in Link: read live from the program's table */
    int l = ptrOf(u32at(A_WLOC)); if (l < 0) return;
    for (int k = 0; k < 3; k += 2) {
        int t = ptrOf(u32at(l + k * 4)); if (t < 0) { if (!k) return; continue; }
        for (int i = 0; i < 40; i++) {
            unsigned b = t + i * 16, x = u16at(b), z = u16at(b + 2), w = u16at(b + 4), h = u16at(b + 6), room = u16at(b + 8), ty = u16at(b + 14);
            if (room == 0xFFFF || x > 32767 || z > 32767 || !w || !h || w > 6000 || h > 6000 || room >= 730 || ty > 8) break;
            if (ty == 4) continue;
            int sx, sy; toScreen((float)x + w / 2, (float)z + h / 2, &sx, &sy);
            if (sy >= MY0 && sy < MY0 + MH) diamond(sx, sy, 3);
        }
    }
}
static void worldPage(void) {
    int x = 0, z = 0, have = worldPos(&x, &z);
    static int wpx, wpz; static float whx, why;
    if (have) {
        worldDetect(x, z);
        if (abs(x - wpx) > 24 || abs(z - wpz) > 24) { float ax = (float)(x - wpx), az = (float)(z - wpz), al = sqrtf(ax * ax + az * az); if (al < 4000) { whx = ax / al; why = az / al; } wpx = x; wpz = z; }
    }
    const uint16_t *tex = worldPic(wSel);
    float fitS = (float)MH / 1024, sc = fitS, cx = 512, cy = 512;
    if (zoom && have) {
        sc = fitS * 4; float hw = (MW / 2) / sc, hh = (MH / 2) / sc, a = x / 32.0f, b = z / 32.0f;
        cx = a < hw ? hw : a > 1024 - hw ? 1024 - hw : a; cy = b < hh ? hh : b > 1024 - hh ? 1024 - hh : b;
    }
    vWorld = 1; vCx = cx; vCy = cy; vSc = sc;
    if (tex) {
        float inv = 0.5f / sc;                                     /* the picture is 512 across a 1024-unit map */
        int32_t step = (int32_t)(inv * 65536.0f);
        int32_t tz = (int32_t)((cy / 2 - (MH / 2) * inv) * 65536.0f), tx0 = (int32_t)((cx / 2 - (MW / 2) * inv) * 65536.0f);
        uint16_t bg = COL[DARK];
        for (int yy = 0; yy < MH; yy++) {
            uint16_t *p = fb + (MY0 + yy) * LINK_W; int32_t tx = tx0; unsigned uz = (unsigned)tz >> 16;
            for (int xx = 0; xx < MW; xx++) { unsigned ux = (unsigned)tx >> 16; p[xx] = (ux | uz) < 512 ? tex[uz << 9 | ux] : bg; tx += step; }
            tz += step;
        }
    } else rect(0, MY0, MW, MH, DARK);
    worldPlaces();
    hintSpots(-1, spotCb);
    if (have) { int sx, sy; toScreen((float)x, (float)z, &sx, &sy); marker(sx, sy, whx, why); }
    rect(0, MY0, MW, 10, DARK);
    text("World map", 2, MY0 + 1, WHITE);
    text(zoom ? "TAP: WHOLE" : "TAP: ZOOM", MW - 84, MY0 + 1, GREY);
    if (!tex) text("COPY xenogears-link.pak", 60, MY0 + MH / 2 - 4, GREY);
}

void map_page(void) {
    unsigned s = u32at(A_SIG); nIcon = 0; pageTre = NULL; pageNt = 0;
    if (s == 5) worldPage();
    else if (s == 4) roomPage();
    else text("The map shows in rooms and on the world map.", 4, 40, GREY);
}
int map_tap(int x, int y) {
    if (showList) { showList = 0; return 1; }
    if (pageNt && x >= MW - 72 && y >= MY0 + 10 && y < MY0 + 24) { showList = 1; return 1; }
    int best = -1, bd = 14 * 14;
    for (int i = 0; i < nIcon; i++) { int d = (icon[i].x - x) * (icon[i].x - x) + (icon[i].y - y) * (icon[i].y - y); if (d < bd) { bd = d; best = icon[i].t; } }
    if (best >= 0) { capRoom = u16at(A_FIELD) & 0x7FF; capIcon = capIcon == best ? -1 : best; return 1; }
    capIcon = -1; zoom = !zoom; return 1;
}

/* ---- a hint's picture: the part of the room's picture Link's pop-up shows, with the green spots ---- */
void map_thumb(int room, const int16_t *spots, int nspots, int x, int y, int size) {
    uint16_t *base = fb + y * LINK_W + x;
    rect(x - 1, y - 1, size + 2, size + 2, WHITE);
    if (room < 0) {
        const uint16_t *tex = worldPic(wSel); if (!tex) { rect(x, y, size, size, DARK); return; }
        /* the whole map, or 128 units around the first spot, as in Link */
        float V = nspots ? 128.0f : 1024.0f, wx = 512, wz = 512;
        if (nspots) { wx = spots[0] / 32.0f; wz = spots[1] / 32.0f; wx = wx < V / 2 ? V / 2 : wx > 1024 - V / 2 ? 1024 - V / 2 : wx; wz = wz < V / 2 ? V / 2 : wz > 1024 - V / 2 ? 1024 - V / 2 : wz; }
        float s = V / 2 / size, l = (wx - V / 2) / 2, t = (wz - V / 2) / 2;
        for (int j = 0; j < size; j++) for (int i = 0; i < size; i++) { unsigned ux = (unsigned)(l + i * s), uz = (unsigned)(t + j * s); base[j * LINK_W + i] = (ux | uz) < 512 ? tex[uz << 9 | ux] : COL[DARK]; }
        for (int k = 0; k < nspots; k++) { int sx = x + (int)((spots[k * 2] / 32.0f - (wx - V / 2)) / V * size), sy = y + (int)((spots[k * 2 + 1] / 32.0f - (wz - V / 2)) / V * size); if (sx >= x && sx < x + size && sy >= y && sy < y + size) { ring(sx, sy, 4, WHITE); ring(sx, sy, 3, GREEN); disc(sx, sy, 1, GREEN); } }
        return;
    }
    const float *pm = planOf(room);
    const uint16_t *tex = pm ? roomPic(room, -1) : NULL;
    if (!tex) { rect(x, y, size, size, DARK); text("NO", x + size / 2 - 8, y + size / 2 - 8, GREY); text("PICTURE", x + size / 2 - 28, y + size / 2 + 2, GREY); return; }
    float hl, ht, hs; map_hroom(room, &hl, &ht, &hs);
    float st = hs * 256 / size, l = hl * 256, t = ht * 256;
    for (int j = 0; j < size; j++) {
        unsigned uz = (unsigned)(t + j * st); uint16_t *p = base + j * LINK_W;
        for (int i = 0; i < size; i++) { unsigned ux = (unsigned)(l + i * st); p[i] = (ux | uz) < 256 ? tex[uz << 8 | ux] : COL[DARK]; }
    }
    for (int k = 0; k < nspots; k++) {
        float fx = (((spots[k * 2] - pm[0]) / pm[2] + 0.5f) - hl) / hs, fz = (((spots[k * 2 + 1] - pm[1]) / pm[2] + 0.5f) - ht) / hs;
        int sx = x + (int)(fx * size), sy = y + (int)(fz * size);
        if (sx >= x && sx < x + size && sy >= y && sy < y + size) { ring(sx, sy, 4, WHITE); ring(sx, sy, 3, GREEN); disc(sx, sy, 1, GREEN); }
    }
}
