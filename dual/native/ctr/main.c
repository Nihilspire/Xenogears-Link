/* main.c - Xenogears Dual 3DS (proof of concept): the pcsx_rearmed core on the top screen, the Link screen (linkscr.c) on the
 * bottom touch screen. libctru only: both screens are RGB565 framebuffers. It is a libretro host like app/jni/psxlink.c (same
 * memory card fix, same analog controls installer), with the 3DS's screens, sound and buttons in place of Android's.
 *
 * The player's discs go in the same folder as the .3dsx (a .cia looks in sdmc:/3ds/xenogears-dual, then sdmc:/3ds): .cue, .chd or
 * .pbp, with "disc 1" / "disc 2" in the names. A real BIOS (scph*.bin) beside them is used if there is one. The memory card and the
 * states are written beside them too, and so is xenogears-3ds.log, the numbers to read back after a run on the real machine.
 *
 * Buttons: A circle, B cross, X triangle, Y square, L/R L1/R1, ZL/ZR L2/R2, Circle Pad left stick, C-stick right stick,
 * Select+R R3 (camera reset). The bottom screen's SYSTEM page has the states, frame skip and quit. */
#include <3ds.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <stdarg.h>
#include <dirent.h>
#include "libretro.h"
#include "linkscr.h"
#ifdef CTR_TEST
#include "test_script.h"     /* written by test/build_test.sh: #define TEST_SCRIPT {...}, {...} and maybe TEST_STATE, TEST_QUIT */
#endif

/* ---------- what the core expects of the program it's linked into ---------- */
u32 __stacksize__ = 2 * 1024 * 1024;   /* the recompiler keeps large tables on the stack */
int __ctr_svchax;                      /* 1 = the recompiler may run: main() sets it (see "the recompiler's cache") */

/* what we use from inside the core, as in psxlink.c */
extern char CdromId[10];
extern int padToggleAnalog(unsigned int index);
typedef struct { int (*Init)(); void (*Reset)(); void (*Execute)(void *); void (*ExecuteBlock)(void *, int);
                 void (*Clear)(uint32_t addr, uint32_t words); } core_cpu_t;
extern core_cpu_t *psxCpu;
extern unsigned char McdFlag[2];

/* ------------------------------------------------------------------ the recompiler's cache
 * The recompiler must flush the CPU's caches after writing code. The core does that through Luma3DS's svcCustomBackdoor (svc 0x80),
 * which a real console with Luma has and Azahar doesn't. Azahar has Luma's newer cache calls, and those tell its own recompiler to
 * throw away what it compiled from the changed memory. The Makefile renames the core's versions to hw_*. */
extern void hw_clear_cache(void);
extern void hw_clear_cache_range(void *start, void *end);
extern void hw_invalidate_icache(void);
static int onEmulator;
static inline void emuInvalidateAll(void) { __asm__ volatile("svc 0x94" ::: "r0", "r1", "r2", "r3", "r12", "lr", "memory"); }
static inline void emuInvalidate(void *p, u32 n) {
    register void *a __asm__("r0") = p; register u32 b __asm__("r1") = n;
    __asm__ volatile("svc 0x93" : "+r"(a), "+r"(b) :: "r2", "r3", "r12", "lr", "memory");
}
void ctr_clear_cache(void) { if (onEmulator) emuInvalidateAll(); else hw_clear_cache(); }
void ctr_clear_cache_range(void *s, void *e) { if (onEmulator) emuInvalidate(s, (u32)((char *)e - (char *)s)); else hw_clear_cache_range(s, e); }
void ctr_invalidate_icache(void) { if (onEmulator) emuInvalidateAll(); else hw_invalidate_icache(); }
void wait_for_input(void) {}

/* ------------------------------------------------------------------ the log */
static char DIRP[256];
static FILE *logf; static int logLines;
static void logs(const char *s) {
    if (!logf || logLines > 4000) return;
    fputs(s, logf); fputc('\n', logf); fflush(logf); logLines++;
}
static void logp(const char *fmt, ...) {
    char t[240]; va_list ap; va_start(ap, fmt); vsnprintf(t, sizeof t, fmt, ap); va_end(ap); logs(t);
}
static void log_cb(enum retro_log_level level, const char *fmt, ...) {
    char t[240]; va_list ap; va_start(ap, fmt); vsnprintf(t, sizeof t, fmt, ap); va_end(ap);
    size_t n = strlen(t); while (n && (t[n - 1] == '\n' || t[n - 1] == '\r')) t[--n] = 0;
    if (n) logs(t);
}

/* ------------------------------------------------------------------ libretro callbacks */
/* The settings a phone gets from MainActivity, with Unai's choices for this machine. */
#ifndef XG_SPU_THREAD
#define XG_SPU_THREAD "enabled"     /* the sound on the second core */
#endif
#ifndef XG_GPU_THREAD
#define XG_GPU_THREAD "auto"        /* New 3DS: the drawing on the third core */
#endif
#ifndef XG_UNAI_OLD
#define XG_UNAI_OLD "disabled"
#endif
static const char *const VARS[][2] = {
    { "pcsx_rearmed_bios", "auto" }, { "pcsx_rearmed_drc", "enabled" },
    { "pcsx_rearmed_memcard1", "libretro" }, { "pcsx_rearmed_memcard2", "disabled" },
    { "pcsx_rearmed_display_fps_v2", "disabled" }, { "pcsx_rearmed_show_bios_bootlogo", "disabled" },
    { "pcsx_rearmed_spu_interpolation", "simple" }, { "pcsx_rearmed_analog_combo", "l3+r3" },
    { "pcsx_rearmed_dithering", "disabled" }, { "pcsx_rearmed_spu_thread", XG_SPU_THREAD },
    { "pcsx_rearmed_gpu_thread_rendering", XG_GPU_THREAD }, { "pcsx_rearmed_cd_readahead", "12" },
    { "pcsx_rearmed_3ds_appcputime", "35" },
    { "pcsx_rearmed_gpu_unai_old_renderer", XG_UNAI_OLD }, { "pcsx_rearmed_gpu_unai_skipline", "disabled" },
    { "pcsx_rearmed_gpu_unai_lighting", "enabled" }, { "pcsx_rearmed_gpu_unai_fast_lighting", "disabled" },
    { "pcsx_rearmed_gpu_unai_blending", "enabled" },
};
static int frameskip, varsDirty;
static char skipVal[8] = "0";
static struct retro_disk_control_ext_callback disk;
static int diskExt, diskHave;
static struct retro_system_av_info av;
static char sysDir[256];

static bool env_cb(unsigned cmd, void *data) {
    switch (cmd & ~RETRO_ENVIRONMENT_EXPERIMENTAL) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = sysDir; return true;
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return *(const enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v = data;
        if (!strcmp(v->key, "pcsx_rearmed_frameskip_type")) { v->value = frameskip ? "fixed_interval" : "disabled"; return true; }
        if (!strcmp(v->key, "pcsx_rearmed_frameskip_interval")) { snprintf(skipVal, sizeof skipVal, "%d", frameskip ? frameskip : 1); v->value = skipVal; return true; }
        for (size_t i = 0; i < sizeof VARS / sizeof VARS[0]; i++) if (!strcmp(v->key, VARS[i][0])) { v->value = VARS[i][1]; return true; }
        v->value = NULL; return false;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = varsDirty; varsDirty = 0; return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: ((struct retro_log_callback *)data)->log = log_cb; return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS: return true;
    case RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE: memcpy(&disk, data, sizeof disk); diskExt = diskHave = 1; return true;
    case RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE:
        if (!diskExt) { memset(&disk, 0, sizeof disk); memcpy(&disk, data, sizeof(struct retro_disk_control_callback)); diskHave = 1; }
        return true;
    case RETRO_ENVIRONMENT_GET_DISK_CONTROL_INTERFACE_VERSION: *(unsigned *)data = 1; return true;
    case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO: memcpy(&av, data, sizeof av); return true;
    case RETRO_ENVIRONMENT_SET_GEOMETRY: memcpy(&av.geometry, data, sizeof av.geometry); return true;
    case RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION: *(unsigned *)data = 0; return true;
    case RETRO_ENVIRONMENT_SET_MESSAGE: { const struct retro_message *m = data; if (m && m->msg) logs(m->msg); return true; }
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION: *(unsigned *)data = 0; return true;
    case RETRO_ENVIRONMENT_SET_VARIABLES: case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_DISPLAY: case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO: case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: case RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
    case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
        return true;
    }
    return false;
}

/* ---- the picture: 3DS framebuffers are stored rotated, pixel (x, y) of the 400x240 screen at fb[x * 240 + 239 - y] ---- */
static int freshFrame, lastW = -1, lastH = -1, clearTop;
static void video_cb(const void *data, unsigned w, unsigned h, size_t pitch) {
    static int colOf[400], rowOf[240], dw, dh, ox, oy;
    if (!data || !w || !h) return;                                 /* a repeat: keep the last picture */
    if ((int)w != lastW || (int)h != lastH) {                      /* worked out once: the ARM11 has no divide instruction */
        lastW = w; lastH = h; clearTop = 2;
        dw = w > 400 ? 400 : w; dh = h > 240 ? 240 : h;            /* wider or taller modes: nearest pixel down to the screen */
        ox = (400 - dw) / 2; oy = (240 - dh) / 2;
        for (int x = 0; x < dw; x++) colOf[x] = x * w / dw;
        for (int y = 0; y < dh; y++) rowOf[y] = y * h / dh;
    }
    uint16_t *fb = (uint16_t *)gfxGetFramebuffer(GFX_TOP, GFX_LEFT, NULL, NULL);
    if (clearTop) { memset(fb, 0, 400 * 240 * 2); clearTop--; }
    const uint16_t *src = data; int pp = (int)(pitch / 2);
    for (int x = 0; x < dw; x++) {
        const uint16_t *col = src + colOf[x];
        uint16_t *dst = fb + (ox + x) * 240 + 239 - oy;
        if (dh == (int)h) { for (int y = 0; y < dh; y++) { dst[-y] = *col; col += pp; } }
        else for (int y = 0; y < dh; y++) dst[-y] = col[rowOf[y] * pp];
    }
    freshFrame = 1;
}

/* ---- sound through NDSP; silent when the DSP firmware dump is missing ---- */
#define NBUF 8
#define BUFSAMP 1024                          /* stereo frames per buffer, ~23 ms at 44100 Hz */
static ndspWaveBuf wb[NBUF];
static int16_t *sbuf; static int sfill, scur, haveSound;
static void soundInit(double rate) {
    if (R_FAILED(ndspInit())) { logs("no NDSP (dump the DSP firmware for sound)"); return; }
    ndspSetOutputMode(NDSP_OUTPUT_STEREO);
    ndspChnSetInterp(0, NDSP_INTERP_LINEAR);
    ndspChnSetRate(0, (float)rate);
    ndspChnSetFormat(0, NDSP_FORMAT_STEREO_PCM16);
    sbuf = (int16_t *)linearAlloc(NBUF * BUFSAMP * 4);
    if (!sbuf) { ndspExit(); return; }
    memset(wb, 0, sizeof wb);
    for (int i = 0; i < NBUF; i++) { wb[i].data_vaddr = sbuf + i * BUFSAMP * 2; wb[i].nsamples = BUFSAMP; wb[i].status = NDSP_WBUF_DONE; }
    haveSound = 1;
}
static size_t audio_batch_cb(const int16_t *s, size_t frames) {
    if (!haveSound) return frames;
    for (size_t i = 0; i < frames; i++) {
        if (wb[scur].status != NDSP_WBUF_DONE && wb[scur].status != NDSP_WBUF_FREE) return frames;   /* the DSP is behind: drop */
        int16_t *d = (int16_t *)wb[scur].data_vaddr;
        d[sfill * 2] = s[i * 2]; d[sfill * 2 + 1] = s[i * 2 + 1];
        if (++sfill == BUFSAMP) {
            DSP_FlushDataCache(d, BUFSAMP * 4);
            ndspChnWaveBufAdd(0, &wb[scur]);
            scur = (scur + 1) % NBUF; sfill = 0;
        }
    }
    return frames;
}
static void audio_cb(int16_t l, int16_t r) { int16_t s[2] = { l, r }; audio_batch_cb(s, 1); }

/* ---- input ---- */
static uint32_t padBits; static int16_t axes[4];
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id) {
    if (port) return 0;
    switch (device & RETRO_DEVICE_MASK) {
    case RETRO_DEVICE_JOYPAD: return id == RETRO_DEVICE_ID_JOYPAD_MASK ? (int16_t)padBits : (padBits >> id) & 1;
    case RETRO_DEVICE_ANALOG:
        if (index == RETRO_DEVICE_INDEX_ANALOG_BUTTON) {
            if (id == RETRO_DEVICE_ID_JOYPAD_L2 || id == RETRO_DEVICE_ID_JOYPAD_R2) return (padBits >> id) & 1 ? 0x7fff : 0;
            return 0;
        }
        if (index > 1 || id > 1) return 0;
        return axes[index * 2 + id];
    }
    return 0;
}
static int16_t stick(int v) { v *= 210; return (int16_t)(v > 32767 ? 32767 : v < -32767 ? -32767 : v); }   /* the 3DS's sticks read about +-156 */

/* ------------------------------------------------------------------ analog controls, as xga_tick in psxlink.c */
#define XGA_ADDR 0x17400u
#define XGA_SLOT 0x501FCu
#define XGA_OPT  0x17F04u
static const uint8_t XGA_SIG[8] = { 0x05,0x80,0x02,0x3c, 0xfc,0x01,0x42,0x8c };   /* lui v0,0x8005; lw v0,0x1fc(v0) at 0x80036388 */
static const uint8_t *xgaProg; static int xgaLen, xgaOpts, xgaPad, xgaState;
static void xgaTick(uint8_t *ram) {
    uint32_t slot, mine = 0x80000000u | XGA_ADDR;
    memcpy(&slot, ram + XGA_SLOT, 4);
    if (memcmp(ram + 0x36388, XGA_SIG, 8)) { xgaState = 1; return; }          /* Xenogears isn't running (yet) */
    if (memcmp(ram + XGA_ADDR, xgaProg, xgaLen)) {
        int i; for (i = 0; i < xgaLen; i++) if (ram[XGA_ADDR + i]) break;
        if (i < xgaLen && !memcmp(ram + XGA_ADDR, xgaProg, 16)) i = xgaLen;
        if (i < xgaLen) {                                                     /* the game is using that block: stay out */
            if (slot == mine) { slot = 0; memcpy(ram + XGA_SLOT, &slot, 4); }
            xgaState = 3; return;
        }
        memcpy(ram + XGA_ADDR, xgaProg, xgaLen);
        if (psxCpu && psxCpu->Clear) psxCpu->Clear(0x80000000u | XGA_ADDR, (xgaLen + 3) / 4);
    }
    for (int i = 0; i < 5; i++) if (xgaOpts & (1 << i)) ram[XGA_OPT + i] = 0x10;
    if (slot == 0) memcpy(ram + XGA_SLOT, &mine, 4);
    if (!xgaPad) { int r = padToggleAnalog(0); if (!r) padToggleAnalog(0); xgaPad = 1; }
    xgaState = 2;
}

/* ------------------------------------------------------------------ files */
#define MCD_BYTES 131072
static char SRM[320], STATE0[320], STATE1[320], DISC[2][320];
static void formatCard(uint8_t *d) {                               /* as format_card in psxlink.c */
    unsigned off = 0, i;
    memset(d, 0, MCD_BYTES);
    d[off++] = 'M'; d[off++] = 'C'; off += 0x7d; d[off++] = 0x0e;
    for (i = 0; i < 15; i++) { d[off++] = 0xa0; off += 0x07; d[off++] = 0xff; d[off++] = 0xff; off += 0x75; d[off++] = 0xa0; }
    for (i = 0; i < 20; i++) { d[off++] = 0xff; d[off++] = 0xff; d[off++] = 0xff; d[off++] = 0xff; off += 0x04; d[off++] = 0xff; d[off++] = 0xff; off += 0x76; }
}
static int saveFile(const char *path, const void *b, size_t n) {   /* .tmp then rename: a crash never leaves half a file */
    char tmp[340]; snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "wb"); if (!f) return 0;
    int ok = fwrite(b, 1, n, f) == n; fclose(f);
    if (!ok) { remove(tmp); return 0; }
    remove(path);
    return rename(tmp, path) == 0;
}
static int saveState(const char *p) {
    size_t n = retro_serialize_size(); void *b = n ? malloc(n) : NULL; int ok = 0;
    if (b && retro_serialize(b, n)) ok = saveFile(p, b, n);
    free(b); return ok;
}
static int loadState(const char *p) {
    FILE *f = fopen(p, "rb"); if (!f) return 0;
    fseek(f, 0, SEEK_END); size_t n = ftell(f); fseek(f, 0, SEEK_SET);
    void *b = malloc(n); int ok = b && fread(b, 1, n, f) == n && retro_unserialize(b, n);
    free(b); fclose(f);
    if (ok) xgaPad = 0;                                            /* the pad comes back digital: the installer switches it again */
    return ok;
}
static const char *const DISCEXT[] = { ".cue", ".chd", ".pbp", NULL };
static int isDisc(const char *n) {
    size_t l = strlen(n); if (l < 5) return 0;
    for (int i = 0; DISCEXT[i]; i++) if (!strcasecmp(n + l - 4, DISCEXT[i])) return i + 1;
    return 0;
}
/* which disc a file name says: 1, 2 or 0 */
static int discNum(const char *n) {
    for (const char *p = n; *p; p++) if (!strncasecmp(p, "disc", 4)) { const char *q = p + 4; while (*q == ' ' || *q == '_' || *q == '-') q++; if (*q == '1') return 1; if (*q == '2') return 2; }
    return 0;
}
static int scanDir(const char *dir) {
    DIR *d = opendir(dir); struct dirent *e; int rank[2] = { 99, 99 };
    if (!d) return 0;
    while ((e = readdir(d))) {
        int k = isDisc(e->d_name); if (!k) continue;
        int w = discNum(e->d_name) == 2 ? 1 : 0;                   /* no number: taken as disc 1 */
        if (k < rank[w]) { rank[w] = k; snprintf(DISC[w], sizeof DISC[w], "%s/%s", dir, e->d_name); }
    }
    closedir(d);
    if (rank[0] == 99 && rank[1] != 99) { memcpy(DISC[0], DISC[1], sizeof DISC[0]); DISC[1][0] = 0; rank[0] = 0; }
    return rank[0] != 99;
}
static int findDiscs(int argc, char **argv) {
    char dir[256] = "";
    if (argc > 0 && argv && argv[0] && strchr(argv[0], '/')) {     /* the Homebrew Launcher: "sdmc:/3ds/Xenogears Dual 3DS.3dsx" */
        snprintf(dir, sizeof dir, "%s", argv[0]); *strrchr(dir, '/') = 0;
        if (!strchr(dir, '/')) strcat(dir, "/");
        if (scanDir(dir)) { snprintf(DIRP, sizeof DIRP, "%s", dir); return 1; }
    }
    static const char *const TRY[] = { "sdmc:/3ds/xenogears-dual", "sdmc:/3ds" };   /* a .cia has no folder of its own */
    for (int i = 0; i < 2; i++) if (scanDir(TRY[i])) { snprintf(DIRP, sizeof DIRP, "%s", TRY[i]); return 1; }
    snprintf(DIRP, sizeof DIRP, "%s", dir[0] ? dir : TRY[0]);
    return 0;
}
static void waitExit(const char *msg) {
    consoleInit(GFX_BOTTOM, NULL);
    printf("\n  XENOGEARS DUAL 3DS (alpha)\n\n%s\n\n  Press START to quit.\n", msg);
    while (aptMainLoop()) { hidScanInput(); if (hidKeysDown() & KEY_START) break; gspWaitForVBlank(); }
}

/* ------------------------------------------------------------------ */
#define SCREEN_HZ 59.83                                            /* the 3DS screen's refresh */
#define BTN(x) (1u << (x))

int main(int argc, char **argv) {
    gfxInitDefault();
    osSetSpeedupEnable(true);                                      /* New 3DS: 804 MHz and the L2 cache */
    bool n3ds = false; APT_CheckNew3DS(&n3ds);

    /* The recompiler needs Luma3DS's calls on a real machine. Without them the core falls back to its (very slow) interpreter. */
    s64 v = 0, ve = 0;
    Result re = svcGetSystemInfo(&ve, 0x20000, 0);
    onEmulator = R_SUCCEEDED(re) && ve != 0;
    Result rl = svcGetSystemInfo(&v, 0x10000, 0);
    int luma = R_SUCCEEDED(rl) && v != 0;
    __ctr_svchax = onEmulator || luma;
    cfguInit();                                                    /* the core counts the CPU's cores from the system model */

    int haveDisc = findDiscs(argc, argv);
    { char p[320]; snprintf(p, sizeof p, "%s/xenogears-3ds.log", DIRP); logf = fopen(p, "w"); }
    logp("Xenogears Dual 3DS: %s, %s, luma %d (%08lx %lld) emulator %d (%08lx %lld), folder %s", n3ds ? "new 3ds" : "old 3ds", __ctr_svchax ? "recompiler" : "interpreter", luma, rl, v, onEmulator, re, ve, DIRP);
    if (!haveDisc) {
        char msg[400];
        snprintf(msg, sizeof msg, "  Put your Xenogears disc images\n  (.cue .chd .pbp) in this folder:\n  %s\n  (no game data ships with this app)", DIRP);
        waitExit(msg); gfxExit(); return 0;
    }
    snprintf(sysDir, sizeof sysDir, "%s", DIRP);
    snprintf(SRM, sizeof SRM, "%s/xenogears.srm", DIRP);
    snprintf(STATE0, sizeof STATE0, "%s/xenogears.st1", DIRP);
    snprintf(STATE1, sizeof STATE1, "%s/xenogears.st2", DIRP);

    gfxSetScreenFormat(GFX_TOP, GSP_RGB565_OES);
    gfxSetScreenFormat(GFX_BOTTOM, GSP_RGB565_OES);
    gfxSetDoubleBuffering(GFX_TOP, true);
    gfxSetDoubleBuffering(GFX_BOTTOM, false);

    retro_set_environment(env_cb);
    retro_set_video_refresh(video_cb);
    retro_set_audio_sample(audio_cb);
    retro_set_audio_sample_batch(audio_batch_cb);
    retro_set_input_poll(input_poll_cb);
    retro_set_input_state(input_state_cb);
    retro_init();
    logs("core initialised");

    struct retro_game_info gi; memset(&gi, 0, sizeof gi); gi.path = DISC[0];
    logp("loading %s", DISC[0]);
    if (!retro_load_game(&gi)) { waitExit("  The core could not load the disc."); gfxExit(); return 0; }
    retro_get_system_av_info(&av);
    retro_set_controller_port_device(0, RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_ANALOG, 1));   /* DualShock */
    retro_set_controller_port_device(1, RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0));
    logp("loaded id %s, %.2f fps, %.0f Hz", CdromId, av.timing.fps, av.timing.sample_rate);
    if (DISC[1][0] && diskHave && disk.add_image_index && disk.replace_image_index) {
        struct retro_game_info g2; memset(&g2, 0, sizeof g2); g2.path = DISC[1];
        unsigned idx = disk.get_num_images();
        if (disk.add_image_index() && disk.replace_image_index(idx, &g2)) logp("disc 2: %s", DISC[1]);
    }
    /* the memory card */
    uint8_t *card = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
    static uint8_t cardCopy[MCD_BYTES];
    if (card && retro_get_memory_size(RETRO_MEMORY_SAVE_RAM) == MCD_BYTES) {
        FILE *f = fopen(SRM, "rb"); size_t n = 0;
        if (f) { n = fread(cardCopy, 1, MCD_BYTES, f); fclose(f); }
        if (n == MCD_BYTES && cardCopy[0] == 'M' && cardCopy[1] == 'C') memcpy(card, cardCopy, MCD_BYTES);
        else if (!(card[0] == 'M' && card[1] == 'C')) formatCard(card);
        memcpy(cardCopy, card, MCD_BYTES);
    } else card = NULL;
    xgaProg = link_prog(&xgaLen, &xgaOpts);
    /* the game runs a frame per refresh of the 3DS's slightly slower screen, so its sound is played that much slower too (0.3%,
       too little to hear) or the DSP would run out every few seconds */
    { double fps = av.timing.fps > 1 ? av.timing.fps : 60.0, rate = av.timing.sample_rate > 1 ? av.timing.sample_rate : 44100;
      soundInit(rate * SCREEN_HZ / fps); }
    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    { char p[320]; snprintf(p, sizeof p, "%s/xenogears-link.pak", DIRP); link_init(p); }

    static uint16_t link[LINK_W * LINK_H];
    LinkIn in; memset(&in, 0, sizeof in);
    in.ram = ram; in.n3ds = n3ds; in.dynarec = __ctr_svchax; in.gputhread = n3ds; in.discs = DISC[1][0] ? 2 : 1;
    static char msgbuf[40], st0[32], st1[32];
    in.state[0] = st0; in.state[1] = st1;
#define HAS(p) ({ FILE *t_ = fopen(p, "rb"); int r_ = t_ != NULL; if (t_) fclose(t_); r_; })
    snprintf(st0, sizeof st0, "%s", HAS(STATE0) ? "saved" : "empty"); snprintf(st1, sizeof st1, "%s", HAS(STATE1) ? "saved" : "empty");

    const u64 FRAME = (u64)(SYSCLOCK_ARM11 / SCREEN_HZ);
    struct { u64 emu, top, link, max; int n, drawn; } tm; memset(&tm, 0, sizeof tm);
    u64 secAt = osGetTime(); int frames = 0, frame = 0, drawn = 0, quit = 0, linkDirty = 1;
    static int tDown, tX0, tY0;
    const char *msgNow = NULL; int msgT = 0;

    while (!quit && aptMainLoop()) {
        u64 t0 = svcGetSystemTick();
        hidScanInput();
        u32 held = hidKeysHeld();
        unsigned pad = 0;
        int sel = (held & KEY_SELECT) != 0;
        if (held & KEY_A) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_A);
        if (held & KEY_B) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_B);
        if (held & KEY_X) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_X);
        if (held & KEY_Y) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_Y);
        if (held & KEY_L) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_L);
        if ((held & KEY_R) && !sel) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_R);
        if ((held & KEY_R) && sel) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_R3);
        if (held & KEY_ZL) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_L2);
        if (held & KEY_ZR) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_R2);
        if (held & KEY_START) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_START);
        if (sel && !(held & KEY_R)) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_SELECT);
        if (held & KEY_DUP) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_UP);
        if (held & KEY_DDOWN) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_DOWN);
        if (held & KEY_DLEFT) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_LEFT);
        if (held & KEY_DRIGHT) pad |= BTN(RETRO_DEVICE_ID_JOYPAD_RIGHT);
        circlePosition cp, cs; hidCircleRead(&cp); hidCstickRead(&cs);
        axes[0] = stick(cp.dx); axes[1] = stick(-cp.dy); axes[2] = stick(cs.dx); axes[3] = stick(-cs.dy);
        int tapX = -1, tapY = -1;
        if (held & KEY_TOUCH) { touchPosition t; hidTouchRead(&t); if (!tDown) { tDown = 1; tX0 = t.px; tY0 = t.py; } }
        else if (tDown) { tDown = 0; tapX = tX0; tapY = tY0; }
#ifdef CTR_TEST
        {   /* test build only (test/build_test.sh): buttons, sticks and taps by frame, because an emulator's input can't be driven
               headless. { frame, frames, pad bits, tap x, tap y, left x, left y, right x, right y } */
            static const struct { int at, len; unsigned pad; int tx, ty, lx, ly, rx, ry; } S[] = { TEST_SCRIPT };
            for (size_t i = 0; i < sizeof S / sizeof S[0]; i++) {
                if (frame < S[i].at || frame >= S[i].at + S[i].len) continue;
                pad |= S[i].pad;
                if (S[i].lx | S[i].ly | S[i].rx | S[i].ry) { axes[0] = S[i].lx; axes[1] = S[i].ly; axes[2] = S[i].rx; axes[3] = S[i].ry; }
                if (S[i].tx >= 0 && frame == S[i].at) { tapX = S[i].tx; tapY = S[i].ty; }
            }
# ifdef TEST_STATE
            if (frame == 2) logp("test state %s: %d", TEST_STATE, loadState(TEST_STATE));
# endif
# ifdef TEST_QUIT
            if (frame == TEST_QUIT) quit = 1;
# endif
        }
#endif
        padBits = pad;
        if (tapX >= 0) {
            int act = link_tap(tapX, tapY, &in);
            linkDirty = 1;
            if (act == LINK_QUIT) quit = 1;
            else if (act == LINK_SAVE0 || act == LINK_SAVE1) {
                int ok = saveState(act == LINK_SAVE0 ? STATE0 : STATE1), s = act == LINK_SAVE1;
                snprintf(msgbuf, sizeof msgbuf, ok ? "SAVED TO SLOT %d" : "COULD NOT SAVE SLOT %d", s + 1); msgNow = msgbuf; msgT = 240;
                if (ok) snprintf(s ? st1 : st0, 32, "saved");
            } else if (act == LINK_LOAD0 || act == LINK_LOAD1) {
                int ok = loadState(act == LINK_LOAD0 ? STATE0 : STATE1), s = act == LINK_LOAD1;
                snprintf(msgbuf, sizeof msgbuf, ok ? "LOADED SLOT %d" : "COULD NOT LOAD SLOT %d", s + 1); msgNow = msgbuf; msgT = 240;
            } else if (act == LINK_FRAMESKIP) { frameskip = (frameskip + 1) % 3; varsDirty = 1; in.frameskip = frameskip; }
            else if (act == LINK_OLD3DS) { in.old3ds = !in.old3ds; osSetSpeedupEnable(!in.old3ds); }
            else if (act == LINK_DISC && in.discs > 1 && diskHave && disk.set_eject_state && disk.set_image_index) {
                in.disc = !in.disc;
                disk.set_eject_state(true); disk.set_image_index(in.disc); disk.set_eject_state(false);
            }
        }

        McdFlag[0] &= ~8; McdFlag[1] &= ~8;                        /* see "Memory card + built-in BIOS" in CLAUDE.md */
        freshFrame = 0;
        retro_run();                                               /* video_cb draws into the top screen's back buffer */
        xgaTick(ram);
        frames++;
        u64 t1 = svcGetSystemTick();
        if (freshFrame) { gfxFlushBuffers(); gfxSwapBuffers(); drawn++; }
        u64 t2 = svcGetSystemTick();

        frame++;
        if (msgT && --msgT == 0) msgNow = NULL;
        in.msg = msgNow;
        in.nowMs = (uint32_t)osGetTime();
        if (frame % link_interval() == 0 || linkDirty) {           /* the Link screen: 3 to 10 times a second by page, or after a tap */
            static uint16_t shown[LINK_W * LINK_H];
            link_draw(link, &in);
            linkDirty = 0;
            if (memcmp(link, shown, sizeof link)) {
                memcpy(shown, link, sizeof link);
                uint16_t *fb = (uint16_t *)gfxGetFramebuffer(GFX_BOTTOM, GFX_LEFT, NULL, NULL);
                for (int x = 0; x < LINK_W; x++) {
                    uint16_t *dst = fb + x * 240 + 239; const uint16_t *s = link + x;
                    for (int y = 0; y < LINK_H; y++) { dst[-y] = *s; s += LINK_W; }
                }
                gfxFlushBuffers();
            }
        }
        if (card && frame % 300 == 0 && memcmp(card, cardCopy, MCD_BYTES)) {   /* the memory card: written when it changed */
            memcpy(cardCopy, card, MCD_BYTES);
            logp("card written: %d", saveFile(SRM, cardCopy, MCD_BYTES));
        }
        u64 t3 = svcGetSystemTick();
        tm.emu += t1 - t0; tm.top += t2 - t1; tm.link += t3 - t2; tm.n++;
        if (t3 - t0 > tm.max) tm.max = t3 - t0;
        if (osGetTime() - secAt >= 1000) {
            const double tenth = SYSCLOCK_ARM11 / 10000.0;
            in.fps = frames; in.drawn = drawn; frames = drawn = 0; secAt = osGetTime();
            in.msEmu = (int)(tm.emu / tenth / tm.n + 0.5);
            in.msTop = (int)(tm.top / tenth / tm.n + 0.5);
            in.msLink = (int)(tm.link / tenth / tm.n + 0.5);
            in.msMax = (int)(tm.max / tenth + 0.5);
            in.analog = xgaState;
            static int logTick;
            if (++logTick % 5 == 0)                                /* the numbers to read back after a run on the real machine */
                logp("f%d fps %d/%d emu %d.%d top %d.%d link %d.%d max %d.%d sig %u field %u step %u analog %d", frame, in.fps, in.drawn,
                     in.msEmu / 10, in.msEmu % 10, in.msTop / 10, in.msTop % 10, in.msLink / 10, in.msLink % 10, in.msMax / 10, in.msMax % 10,
                     *(uint32_t *)(ram + 0x6FAF0), (unsigned)(*(uint16_t *)(ram + 0x6F94E) & 0x7FF), (unsigned)*(uint16_t *)(ram + 0x6EF64), xgaState);
            memset(&tm, 0, sizeof tm);
        }
        /* Only a loop that came in under a refresh waits for the next one. A locked loop would drop to 30 the moment a frame runs a
           little long (Shantae's lesson), where this one just runs a little slow. */
        if (svcGetSystemTick() - t0 < FRAME) gspWaitForVBlank();
    }
    if (card && memcmp(card, cardCopy, MCD_BYTES)) saveFile(SRM, card, MCD_BYTES);
    logp("quit at frame %d", frame);
    retro_unload_game();
    retro_deinit();
    if (haveSound) ndspExit();
    if (logf) fclose(logf);
    cfguExit();
    gfxExit();
    return 0;
}
