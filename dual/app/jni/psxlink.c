/*
 * Xenogears Dual's native frontend (libxenolink.so): a small libretro host for the bundled pcsx_rearmed core
 * (libpcsx_rearmed.so, unmodified). Java drives the frame loop (Emu.vsync -> runFrame); this file owns:
 *   - the libretro callbacks: core options, log, video and audio hand-off buffers, input
 *   - helpers: memory card format, writing files safely, Java strings
 *   - JNI, in this order: start-up and options; loading a game and the pad type; the analog controls installer;
 *     the diagnostics report; developer tools (warp, story step); running a frame, timing, picture and sound; input; RAM for Link and the core's
 *     messages; memory card and save states; reset and GameShark codes; discs; analog mode and card status;
 *     the live memory card; unloading.
 * It's also compiled into tests/drive.c, which drives the same functions headless.
 * Anything extra it needs from the core is exported by core/psxlink-version-script (CdromId, padToggleAnalog, ...).
 */
#include <jni.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <pthread.h>
#include <time.h>
#include "libretro.h"

extern int __android_log_print(int prio, const char *tag, const char *fmt, ...);
extern int __android_log_vprint(int prio, const char *tag, const char *fmt, va_list ap);
#define LOGI(...) __android_log_print(4, "XenoLink", __VA_ARGS__)
#define LOGE(...) __android_log_print(6, "XenoLink", __VA_ARGS__)

/* ---------- what we use from inside the core (exported by core/psxlink-version-script) ---------- */
extern char CdromId[10];
extern char CdromLabel[33];
extern int padToggleAnalog(unsigned int index);
/* the core's CPU interface (exported for us): Clear() tells the recompiler that RAM it may have compiled changed */
typedef struct { int (*Init)(); void (*Reset)(); void (*Execute)(void *); void (*ExecuteBlock)(void *, int);
                 void (*Clear)(uint32_t addr, uint32_t words); } core_cpu_t;
extern core_cpu_t *psxCpu;
/* The core marks memory cards "new" at power-on, reset and every state load. The built-in BIOS then answers the
 * game's card check with "new card" until something is written, and Xenogears' save menu takes that as
 * "not formatted" (loading still works). The card in the slot never changes behind the game's back here,
 * so the flag is cleared after every frame. */
extern unsigned char McdFlag[2];
/* analog installer state (see "Analog controls" below) and how many GameShark codes are set (for the report) */
static int g_xga_pad;
static int g_cheats_set = 0;
static volatile int g_xga_state;

/* ---------- paths / options ---------- */
static char g_sys_dir[512] = "", g_save_dir[512] = "", g_srm_path[600] = "";
#define MAX_VARS 64
static char g_var_key[MAX_VARS][64], g_var_val[MAX_VARS][64];
static int g_var_count = 0, g_var_dirty = 0;
static pthread_mutex_t g_var_lock = PTHREAD_MUTEX_INITIALIZER;

/* ---------- video ---------- */
#define FB_MAX (2048 * 1024)
static uint16_t g_fb[FB_MAX];          /* latest frame, RGB565, tightly packed */
static int g_fb_w = 0, g_fb_h = 0, g_fb_seq = 0;
static pthread_mutex_t g_fb_lock = PTHREAD_MUTEX_INITIALIZER;
static enum retro_pixel_format g_pixfmt = RETRO_PIXEL_FORMAT_0RGB1555;
static struct retro_system_av_info g_av;

/* ---------- audio ring (stereo int16 frames) ---------- */
#define AR_FRAMES 16384
static int16_t g_ar[AR_FRAMES * 2];
static volatile int g_ar_r = 0, g_ar_w = 0;
static pthread_mutex_t g_ar_lock = PTHREAD_MUTEX_INITIALIZER;

/* ---------- input ---------- */
static volatile uint32_t g_btn[2];          /* retro joypad bitmask per port */
static volatile int16_t g_axis[2][4];       /* lx, ly, rx, ry */
static volatile int g_stick_dpad = 0;       /* left stick also drives the d-pad */
static volatile int g_stick_dpad_thresh = 12000;

/* ---------- misc state ---------- */
static struct retro_disk_control_ext_callback g_disk;
static int g_disk_ext = 0, g_disk_have = 0;
static int g_loaded = 0, g_inited = 0;
static char g_msg[256];
static volatile int g_msg_seq = 0;

/* ================= libretro callbacks =================
 * The core calls these: environment (settings and capabilities), log, video, audio and input. */
/* the core's last log lines, for the diagnostics report */
#define LOGRING 48
static char g_logring[LOGRING][160];
static int g_loghead = 0;
static pthread_mutex_t g_log_lock = PTHREAD_MUTEX_INITIALIZER;
static void log_cb(enum retro_log_level level, const char *fmt, ...)
{
   va_list ap; char line[160]; size_t n;
   va_start(ap, fmt);
   __android_log_vprint(level >= RETRO_LOG_ERROR ? 6 : level >= RETRO_LOG_WARN ? 5 : 4, "pcsx", fmt, ap);
   va_end(ap);
   va_start(ap, fmt); vsnprintf(line, sizeof(line), fmt, ap); va_end(ap);
   n = strlen(line); while (n && (line[n - 1] == '\n' || line[n - 1] == '\r')) line[--n] = 0;
   if (!n) return;
   pthread_mutex_lock(&g_log_lock);
   snprintf(g_logring[g_loghead % LOGRING], 160, "%s", line); g_loghead++;
   pthread_mutex_unlock(&g_log_lock);
}

/* a core option's value as Java set it (setVariable), or NULL for the core's default; call with g_var_lock held */
static const char *var_get(const char *key)
{
   int i;
   for (i = 0; i < g_var_count; i++)
      if (!strcmp(g_var_key[i], key)) return g_var_val[i];
   return NULL;
}

/* the environment callback: folders, pixel format, options, the disc-control interface, messages; the rest is
 * acknowledged and ignored */
static bool env_cb(unsigned cmd, void *data)
{
   switch (cmd & ~RETRO_ENVIRONMENT_EXPERIMENTAL) {
   case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY: *(const char **)data = g_sys_dir; return true;
   case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:   *(const char **)data = g_save_dir; return true;
   case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
      enum retro_pixel_format f = *(const enum retro_pixel_format *)data;
      if (f == RETRO_PIXEL_FORMAT_RGB565 || f == RETRO_PIXEL_FORMAT_XRGB8888 || f == RETRO_PIXEL_FORMAT_0RGB1555) { g_pixfmt = f; return true; }
      return false;
   }
   case RETRO_ENVIRONMENT_GET_VARIABLE: {
      struct retro_variable *v = data; const char *val;
      pthread_mutex_lock(&g_var_lock);
      val = var_get(v->key);
      v->value = val;
      pthread_mutex_unlock(&g_var_lock);
      return val != NULL;
   }
   case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
      *(bool *)data = g_var_dirty; g_var_dirty = 0; return true;
   case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
      ((struct retro_log_callback *)data)->log = log_cb; return true;
   case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
   case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS: return true;
   case RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE:
      memcpy(&g_disk, data, sizeof(g_disk)); g_disk_ext = 1; g_disk_have = 1; return true;
   case RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE:
      if (!g_disk_ext) { memset(&g_disk, 0, sizeof(g_disk)); memcpy(&g_disk, data, sizeof(struct retro_disk_control_callback)); g_disk_have = 1; }
      return true;
   case RETRO_ENVIRONMENT_GET_DISK_CONTROL_INTERFACE_VERSION: *(unsigned *)data = 1; return true;
   case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO: memcpy(&g_av, data, sizeof(g_av)); return true;
   case RETRO_ENVIRONMENT_SET_GEOMETRY: memcpy(&g_av.geometry, data, sizeof(g_av.geometry)); return true;
   case RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION: *(unsigned *)data = 1; return true;
   case RETRO_ENVIRONMENT_SET_MESSAGE: {
      const struct retro_message *m = data;
      if (m && m->msg) { snprintf(g_msg, sizeof(g_msg), "%s", m->msg); g_msg_seq++; }
      return true;
   }
   case RETRO_ENVIRONMENT_SET_MESSAGE_EXT: {
      const struct retro_message_ext *m = data;
      if (m && m->msg && m->target != RETRO_MESSAGE_TARGET_LOG) { snprintf(g_msg, sizeof(g_msg), "%s", m->msg); g_msg_seq++; }
      return true;
   }
   case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION: *(unsigned *)data = 0; return true;
   case RETRO_ENVIRONMENT_SET_VARIABLES:
   case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_DISPLAY:
   case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
   case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
   case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:
   case RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
   case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
      return true;
   }
   return false;
}

/* a new frame: converted to RGB565 into g_fb for GameView (copyFrame) */
static void video_cb(const void *data, unsigned w, unsigned h, size_t pitch)
{
   unsigned x, y;
   if (!data || w == 0 || h == 0) return;                /* dupe: keep last frame */
   if ((size_t)w * h > FB_MAX) return;
   pthread_mutex_lock(&g_fb_lock);
   if (g_pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
      for (y = 0; y < h; y++)
         memcpy(g_fb + y * w, (const uint8_t *)data + y * pitch, w * 2);
   } else if (g_pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) {
      for (y = 0; y < h; y++) {
         const uint32_t *s = (const uint32_t *)((const uint8_t *)data + y * pitch);
         uint16_t *d = g_fb + y * w;
         for (x = 0; x < w; x++) { uint32_t p = s[x]; d[x] = ((p >> 8) & 0xF800) | ((p >> 5) & 0x07E0) | ((p >> 3) & 0x1F); }
      }
   } else { /* 0RGB1555 */
      for (y = 0; y < h; y++) {
         const uint16_t *s = (const uint16_t *)((const uint8_t *)data + y * pitch);
         uint16_t *d = g_fb + y * w;
         for (x = 0; x < w; x++) { uint16_t p = s[x]; d[x] = ((p & 0x7FE0) << 1) | (p & 0x1F); }
      }
   }
   g_fb_w = w; g_fb_h = h; g_fb_seq++;
   pthread_mutex_unlock(&g_fb_lock);
}

/* sound into the ring buffer Emu reads with readAudio; when it's full, the oldest is dropped */
static size_t audio_batch_cb(const int16_t *data, size_t frames)
{
   size_t i;
   pthread_mutex_lock(&g_ar_lock);
   for (i = 0; i < frames; i++) {
      int nw = (g_ar_w + 1) % AR_FRAMES;
      if (nw == g_ar_r) g_ar_r = (g_ar_r + 1) % AR_FRAMES;    /* overrun: drop oldest */
      g_ar[g_ar_w * 2] = data[i * 2]; g_ar[g_ar_w * 2 + 1] = data[i * 2 + 1];
      g_ar_w = nw;
   }
   pthread_mutex_unlock(&g_ar_lock);
   return frames;
}
static void audio_cb(int16_t l, int16_t r) { int16_t s[2] = { l, r }; audio_batch_cb(s, 1); }

static void input_poll_cb(void) {}

/* input: buttons as Java set them, plus the d-pad from the left stick when "Stick also moves D-pad" is on */
static uint32_t port_mask(unsigned port)
{
   uint32_t m = g_btn[port];
   if (g_stick_dpad) {
      int t = g_stick_dpad_thresh;
      if (g_axis[port][0] < -t) m |= 1u << RETRO_DEVICE_ID_JOYPAD_LEFT;
      if (g_axis[port][0] >  t) m |= 1u << RETRO_DEVICE_ID_JOYPAD_RIGHT;
      if (g_axis[port][1] < -t) m |= 1u << RETRO_DEVICE_ID_JOYPAD_UP;
      if (g_axis[port][1] >  t) m |= 1u << RETRO_DEVICE_ID_JOYPAD_DOWN;
   }
   return m;
}

static int16_t input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id)
{
   if (port > 1) return 0;
   switch (device & RETRO_DEVICE_MASK) {
   case RETRO_DEVICE_JOYPAD:
      if (id == RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)port_mask(port);
      return (port_mask(port) >> id) & 1;
   case RETRO_DEVICE_ANALOG:
      if (index == RETRO_DEVICE_INDEX_ANALOG_BUTTON) {
         if (id == RETRO_DEVICE_ID_JOYPAD_L2 || id == RETRO_DEVICE_ID_JOYPAD_R2)
            return ((port_mask(port) >> id) & 1) ? 0x7fff : 0;
         return 0;
      }
      if (index > 1 || id > 1) return 0;
      return g_axis[port][index * 2 + id];
   }
   return 0;
}

/* ================= helpers ================= */
#define MCD_BYTES 131072
/* a freshly formatted PS1 memory card: header frame, 15 free directory entries, 20 unused broken-sector entries */
static void format_card(uint8_t *d)
{
   unsigned off = 0, i;
   memset(d, 0, MCD_BYTES);
   d[off++] = 'M'; d[off++] = 'C'; off += 0x7d; d[off++] = 0x0e;
   for (i = 0; i < 15; i++) { d[off++] = 0xa0; off += 0x07; d[off++] = 0xff; d[off++] = 0xff; off += 0x75; d[off++] = 0xa0; }
   for (i = 0; i < 20; i++) { d[off++] = 0xff; d[off++] = 0xff; d[off++] = 0xff; d[off++] = 0xff; off += 0x04; d[off++] = 0xff; d[off++] = 0xff; off += 0x76; }
}
static int card_formatted(const uint8_t *d) { return d[0] == 'M' && d[1] == 'C'; }
static int g_card_status = 0;   /* after loadGame: 0 = card loaded, 1 = no file yet (blank card), 2 = file was not a formatted card (backed up, blank card used) */
/* writes path.tmp, then renames it over path, so a crash mid-write never leaves half a card or state */
static int save_file(const char *path, const void *buf, size_t size)
{
   char tmp[700]; FILE *f;
   snprintf(tmp, sizeof(tmp), "%s.tmp", path);
   f = fopen(tmp, "wb");
   if (!f) return 0;
   if (fwrite(buf, 1, size, f) != size) { fclose(f); remove(tmp); return 0; }
   fclose(f);
   return rename(tmp, path) == 0;
}

/* a Java string into a C buffer (cut to fit) */
static const char *jstr(JNIEnv *e, jstring s, char *out, size_t n)
{
   const char *c = (*e)->GetStringUTFChars(e, s, NULL);
   snprintf(out, n, "%s", c ? c : "");
   if (c) (*e)->ReleaseStringUTFChars(e, s, c);
   return out;
}

#define J(name) Java_com_jack_xenogears_Native_##name

/* ================= JNI (Native.java) ================= */

/* ---- start-up and core options ---- */
JNIEXPORT void JNICALL J(init)(JNIEnv *e, jclass c, jstring sys, jstring save)
{
   jstr(e, sys, g_sys_dir, sizeof(g_sys_dir));
   jstr(e, save, g_save_dir, sizeof(g_save_dir));
   if (g_inited) return;
   retro_set_environment(env_cb);
   retro_set_video_refresh(video_cb);
   retro_set_audio_sample(audio_cb);
   retro_set_audio_sample_batch(audio_batch_cb);
   retro_set_input_poll(input_poll_cb);
   retro_set_input_state(input_state_cb);
   retro_init();
   g_inited = 1;
   LOGI("core initialised, sys=%s save=%s", g_sys_dir, g_save_dir);
}

JNIEXPORT void JNICALL J(setVariable)(JNIEnv *e, jclass c, jstring k, jstring v)
{
   char key[64], val[64]; int i;
   jstr(e, k, key, sizeof(key)); jstr(e, v, val, sizeof(val));
   pthread_mutex_lock(&g_var_lock);
   for (i = 0; i < g_var_count; i++) if (!strcmp(g_var_key[i], key)) break;
   if (i == g_var_count && g_var_count < MAX_VARS) g_var_count++;
   if (i < MAX_VARS) { strcpy(g_var_key[i], key); strcpy(g_var_val[i], val); g_var_dirty = 1; }
   pthread_mutex_unlock(&g_var_lock);
}

/* ---- loading a game and the pad type ----
 * loadGame also loads the memory card file: a file that isn't a formatted card is kept aside as .bad-<time> and a
 * fresh card is used (cardStatus tells Java which happened). */
JNIEXPORT jboolean JNICALL J(loadGame)(JNIEnv *e, jclass c, jstring jpath, jstring jsrm, jint padType)
{
   char path[600]; struct retro_game_info gi; void *sram; size_t sz;
   jstr(e, jpath, path, sizeof(path));
   jstr(e, jsrm, g_srm_path, sizeof(g_srm_path));
   memset(&gi, 0, sizeof(gi)); gi.path = path;
   if (!retro_load_game(&gi)) { LOGE("load failed: %s", path); return JNI_FALSE; }
   retro_get_system_av_info(&g_av);
   /* padType: 0 = standard, 1 = analog (dual analog), 2 = DualShock */
   {
      unsigned dev = padType == 2 ? RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_ANALOG, 1)
                   : padType == 1 ? RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_ANALOG, 0)
                   : RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0);
      retro_set_controller_port_device(0, dev);
      retro_set_controller_port_device(1, RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0));
   }
   sram = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
   sz = retro_get_memory_size(RETRO_MEMORY_SAVE_RAM);
   g_card_status = 1;
   if (sram && sz == MCD_BYTES && g_srm_path[0]) {
      static uint8_t tmp[MCD_BYTES];
      FILE *f = fopen(g_srm_path, "rb");
      if (f) {
         size_t n = fread(tmp, 1, MCD_BYTES, f); fclose(f);
         if (n == MCD_BYTES && card_formatted(tmp)) { memcpy(sram, tmp, MCD_BYTES); g_card_status = 0; LOGI("memory card loaded: %s", g_srm_path); }
         else {
            /* blank, cut short or not a card: keep it aside and start from a formatted card */
            char bad[700]; snprintf(bad, sizeof(bad), "%s.bad-%ld", g_srm_path, (long)time(NULL));
            rename(g_srm_path, bad);
            format_card(sram);
            save_file(g_srm_path, sram, MCD_BYTES);
            g_card_status = 2;
            LOGE("memory card %s was not a formatted card (%zu bytes); kept as %s, using a new formatted card", g_srm_path, n, bad);
         }
      } else if (!card_formatted(sram)) format_card(sram);
   }
   g_loaded = 1;
   g_xga_pad = 0; g_xga_state = 0;
   LOGI("loaded %s id=%s fps=%f", path, CdromId, g_av.timing.fps);
   return JNI_TRUE;
}

JNIEXPORT void JNICALL J(setPadType)(JNIEnv *e, jclass c, jint padType)
{
   unsigned dev = padType == 2 ? RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_ANALOG, 1)
                : padType == 1 ? RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_ANALOG, 0)
                : RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0);
   if (g_loaded) retro_set_controller_port_device(0, dev);
   g_xga_pad = 0;                         /* a new pad starts digital: the analog installer switches it again */
}

/* ---- Analog controls (Jack's xg_analog program), installed by the frontend ----
 * The program and hook are the same as in "Xenogears (USA) - Analog Controls.cht", but instead of the cheat
 * engine rewriting 2.3 KB of RAM every frame from power-on, this writes them only once the Xenogears
 * executable is in RAM, only into a block that is still empty (or already holds the program), tells the
 * recompiler about the write, and takes the hook out again if the game ever puts something else there. */
#define XGA_ADDR   0x17400u                 /* program, 0x80017400 */
#define XGA_SLOT   0x501FCu                 /* game's per-vblank hook pointer, 0x800501FC */
#define XGA_OPTS   0x17F04u                 /* option countdown bytes 0x80017F04..08 */
static uint8_t g_xga_prog[0xC00];
static int g_xga_len = 0;
static volatile int g_xga_on = 0, g_xga_opts = 0;   /* g_xga_state: 0 off, 1 waiting, 2 running, 3 blocked */
/* g_xga_pad: analog mode already switched on for this run */
static const uint8_t XGA_SIG[8] = { 0x05,0x80,0x02,0x3c, 0xfc,0x01,0x42,0x8c };   /* lui v0,0x8005; lw v0,0x1fc(v0) at 0x80036388 */

static void xga_set_analog(int on)
{
   int r = padToggleAnalog(0);
   if ((r != 0) != (on != 0)) padToggleAnalog(0);
}

static void xga_tick(void)
{
   uint8_t *ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
   uint32_t slot, mine = 0x80000000u | XGA_ADDR;
   int i;
   if (!ram || !g_xga_len) return;
   memcpy(&slot, ram + XGA_SLOT, 4);
   if (!g_xga_on) {
      if (slot == mine) { slot = 0; memcpy(ram + XGA_SLOT, &slot, 4); }
      g_xga_state = 0; return;
   }
   if (memcmp(ram + 0x36388, XGA_SIG, 8)) { g_xga_state = 1; return; }      /* Xenogears isn't running (yet) */
   if (memcmp(ram + XGA_ADDR, g_xga_prog, g_xga_len)) {
      for (i = 0; i < g_xga_len; i++) if (ram[XGA_ADDR + i]) break;
      /* another copy of the same program (e.g. the .cht entered as a mod) starts with the same code: replace it */
      if (i < g_xga_len && g_xga_len >= 16 && !memcmp(ram + XGA_ADDR, g_xga_prog, 16)) i = g_xga_len;
      if (i < g_xga_len) {                                                    /* the game is using that block: stay out */
         if (slot == mine) { slot = 0; memcpy(ram + XGA_SLOT, &slot, 4); }
         if (g_xga_state != 3) LOGI("analog controls: 0x80017400 holds game data, hook removed");
         g_xga_state = 3; return;
      }
      memcpy(ram + XGA_ADDR, g_xga_prog, g_xga_len);
      if (psxCpu && psxCpu->Clear) psxCpu->Clear(0x80000000u | XGA_ADDR, (g_xga_len + 3) / 4);
   }
   for (i = 0; i < 5; i++) if (g_xga_opts & (1 << i)) ram[XGA_OPTS + i] = 0x10;
   if (slot == 0) { memcpy(ram + XGA_SLOT, &mine, 4); }
   if (!g_xga_pad) { xga_set_analog(1); g_xga_pad = 1; }
   if (g_xga_state != 2) LOGI("analog controls running");
   g_xga_state = 2;
}

/* prog = the program's bytes from 0x80017400; opts = bit per option (walk, run, camera, invert, smooth) */
JNIEXPORT void JNICALL J(setAnalogMod)(JNIEnv *e, jclass c, jbyteArray prog, jboolean on, jint opts)
{
   if (prog) {
      jsize n = (*e)->GetArrayLength(e, prog);
      if (n > (jsize)sizeof(g_xga_prog)) n = sizeof(g_xga_prog);
      (*e)->GetByteArrayRegion(e, prog, 0, n, (jbyte *)g_xga_prog);
      g_xga_len = n;
      /* Fix: the camera check read the field's camera mode (a 16-bit value at 0x800AF934) with lw, which also took in
       * the next halfword (0x800AF936, e.g. 0x0019 in Fei's room), so the right stick and smooth L1/R1 never ran
       * there. lw t5,-0x6cc(t2) -> lhu t5,-0x6cc(t2). */
      if (n >= 0x460) {
         uint32_t w; memcpy(&w, g_xga_prog + 0x45C, 4);
         if (w == 0x8D4DF934u) { w = 0x954DF934u; memcpy(g_xga_prog + 0x45C, &w, 4); }
      }
   }
   if (g_xga_on && !on && g_loaded && g_xga_pad) { xga_set_analog(0); }
   if (!on) g_xga_pad = 0;
   g_xga_on = on; g_xga_opts = opts;
   if (g_loaded) xga_tick();
}
JNIEXPORT jint JNICALL J(analogModState)(JNIEnv *e, jclass c) { return g_xga_state; }

/* ---- the diagnostics report ----
 * A plain-text report of what the emulator and the analog installer see (MainActivity.diagnosticsReport; no menu
 * entry since 0.17). */
JNIEXPORT jstring JNICALL J(diagnostics)(JNIEnv *e, jclass c)
{
   static char out[12000];
   size_t o = 0; int i;
   uint8_t *ram = g_loaded ? (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM) : NULL;
   uint8_t *card = g_loaded ? (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SAVE_RAM) : NULL;
#define P(...) do { if (o < sizeof(out)) o += snprintf(out + o, sizeof(out) - o, __VA_ARGS__); } while (0)
   P("loaded %d  game %s  cheats %d\n", g_loaded, g_loaded ? CdromId : "-", g_cheats_set);
   if (ram) {
      uint32_t slot, w; int first = -1, nz = 0;
      memcpy(&slot, ram + XGA_SLOT, 4);
      for (i = 0; i < g_xga_len; i++) { if (ram[XGA_ADDR + i] != g_xga_prog[i] && first < 0) first = i; if (ram[XGA_ADDR + i]) nz++; }
      P("analog: on %d state %d pad %d opts %x len %d | sig ", g_xga_on, g_xga_state, g_xga_pad, g_xga_opts, g_xga_len);
      for (i = 0; i < 8; i++) P("%02x", ram[0x36388 + i]);
      P(" | slot %08x | block nonzero %d, first diff %s", slot, nz, first < 0 ? "none" : "");
      if (first >= 0) {
         P("%08x\n  ram ", 0x80000000u | (XGA_ADDR + first));
         for (i = 0; i < 16 && first + i < g_xga_len; i++) P("%02x", ram[XGA_ADDR + first + i]);
         P("\n  want");
         for (i = 0; i < 16 && first + i < g_xga_len; i++) P("%02x", g_xga_prog[first + i]);
      }
      P("\n  block 80017400: ");
      for (i = 0; i < 32; i++) P("%02x", ram[XGA_ADDR + i]);
      P("\n  state 80017F00: ");
      for (i = 0; i < 32; i++) P("%02x", ram[0x17F00 + i]);
      memcpy(&w, ram + 0x6FAF0, 4);
      P("\n  program %08x room %04x lock %02x%02x pad rx %02x%02x%02x%02x%02x%02x%02x%02x\n", w, ram[0x6F94E] | ram[0x6F94F] << 8,
        ram[0xB2177], ram[0xB2176], ram[0x625FC], ram[0x625FD], ram[0x625FE], ram[0x625FF], ram[0x62600], ram[0x62601], ram[0x62602], ram[0x62603]);
   }
   if (card) {
      int used = 0, x = 0;
      for (i = 0; i < 127; i++) x ^= card[i];
      P("card: status %d size %u hdr %c%c chk %02x/%02x formatted %d |", g_card_status, (unsigned)retro_get_memory_size(RETRO_MEMORY_SAVE_RAM),
        card[0] >= 32 ? card[0] : '?', card[1] >= 32 ? card[1] : '?', card[127], x, card_formatted(card));
      for (i = 1; i < 16; i++) {
         const uint8_t *d = card + i * 128;
         if ((d[0] & 0xF0) == 0x50) { used++; P(" %d:%02x %.20s", i, d[0], (const char *)d + 10); }
         else if (d[0] != 0xA0) P(" %d:%02x", i, d[0]);
      }
      P(" | used %d\n", used);
   }
   P("core log:\n");
   pthread_mutex_lock(&g_log_lock);
   for (i = g_loghead > LOGRING ? g_loghead - LOGRING : 0; i < g_loghead; i++) P("  %s\n", g_logring[i % LOGRING]);
   pthread_mutex_unlock(&g_log_lock);
#undef P
   for (i = 0; out[i]; i++) if (out[i] != '\n' && ((unsigned char)out[i] < 0x20 || (unsigned char)out[i] > 0x7e)) out[i] = '?';   /* JNI wants plain text */
   return (*e)->NewStringUTF(e, out);
}

/* ---- developer tools: warp to a room, set the story step ----
 * For checking hints without playing to them (Link's DEV section, tests/scripts/hint_walk.py). The warp does what the
 * field script's change-room command does (opcode 0x98, routine 0x800932D8), and only when that command itself would go
 * ahead and the player has control; a request waits up to 10 s for that. Same writes as the recomp's dev warp.
 * The room goes in without the gear bits, so the party arrives on foot. The story step is script variable 0: the field's
 * variable block and the game state's copy are both written. Room scripts read it when a room loads. */
#define DEV_PATIENCE 600                    /* frames a warp waits for the player to have control */
#define DEV_TITLE_ROOM 490
#define DEV_FIELD_VARS 0xC3A68u             /* field script variables (u16, by byte offset) */
static volatile int g_dev_room = -1, g_dev_door = 0, g_dev_story = -1;
static int g_dev_wait = 0;
static volatile int g_dev_state = 0;        /* 0 idle, 1 waiting, 2 done, 3 gave up */

static uint32_t dev_r32(const uint8_t *ram, uint32_t a) { uint32_t v; memcpy(&v, ram + (a & 0x1FFFFF), 4); return v; }
static unsigned dev_r16(const uint8_t *ram, uint32_t a) { uint16_t v; memcpy(&v, ram + (a & 0x1FFFFF), 2); return v; }
static void dev_w32(uint8_t *ram, uint32_t a, uint32_t v) { memcpy(ram + (a & 0x1FFFFF), &v, 4); }
static void dev_w16(uint8_t *ram, uint32_t a, unsigned v) { uint16_t h = (uint16_t)v; memcpy(ram + (a & 0x1FFFFF), &h, 2); }

/* the checks opcode 0x98 makes before it changes room, plus: the player has control, nothing else in flight */
static int dev_can_warp(const uint8_t *ram)
{
   return (dev_r32(ram, 0x6FAF0) & 0xFF) == 4 && (dev_r16(ram, 0x6F94E) & 0xFFF) != DEV_TITLE_ROOM &&
          dev_r16(ram, 0xB2176) != 0xFFFF && dev_r32(ram, 0xADBDC) != 0 && dev_r32(ram, 0xADBE4) != 0 &&
          dev_r32(ram, 0xADB2C) == 0 && dev_r32(ram, 0x4F308) != 0xFFFFFFFFu && dev_r32(ram, 0xADB90) == 0 &&
          dev_r32(ram, 0xADB70) == 0 && dev_r32(ram, 0xADBEC) != 0 && dev_r32(ram, 0xAFD04) == 0 &&
          (dev_r32(ram, 0xADB64) & 0xFF) == 0xFF;
}

/* the player's facing in eighths (field routine 0x8009744C) */
static unsigned dev_player_direction(const uint8_t *ram)
{
   uint32_t actors = dev_r32(ram, 0xAFB10), i = dev_r32(ram, 0xB226C), ent;
   if ((actors >> 24) != 0x80 || i > 255) return 0;
   ent = dev_r32(ram, actors + i * 0x5C + 0x4C);
   if ((ent >> 24) != 0x80) return 0;
   return (unsigned)((((int16_t)dev_r16(ram, ent + 0x106) + 0x100) >> 9) + 2) & 7;
}

static void dev_apply_warp(uint8_t *ram, int room, int door)
{
   int16_t yaw = (int16_t)dev_r16(ram, 0xAF98C);
   dev_w16(ram, DEV_FIELD_VARS + 4, dev_r32(ram, 0x4F34C) & 0x3FFF);      /* where we came from, as the opcode saves it */
   dev_w16(ram, DEV_FIELD_VARS + 6, dev_player_direction(ram));
   dev_w16(ram, DEV_FIELD_VARS + 8, (unsigned)(7 - ((yaw - 0x100) >> 9)) & 7);   /* camera direction, field routine 0x8009A514 */
   dev_w16(ram, DEV_FIELD_VARS + 0x12, dev_r16(ram, DEV_FIELD_VARS + 0x12) + 1);
   dev_w16(ram, 0xB2176, 0xFFFF);                                          /* player lock */
   dev_w16(ram, DEV_FIELD_VARS + 2, (unsigned)door);                       /* entrance */
   dev_w32(ram, 0x4F34C, (uint32_t)room & 0xFFF);                          /* g_GameSceneMapNum */
   dev_w32(ram, 0xADBEC, 0);                                               /* last: the field loop acts on this */
}

/* after each frame: any waiting story step or warp */
static void dev_tick(void)
{
   uint8_t *ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
   int story = g_dev_story, room = g_dev_room;
   if (!ram) return;
   if (story >= 0) {
      g_dev_story = -1;
      dev_w16(ram, 0x6EF64, (unsigned)story);
      if ((dev_r32(ram, 0x6FAF0) & 0xFF) == 4) dev_w16(ram, DEV_FIELD_VARS, (unsigned)story);
   }
   if (room >= 0) {
      if (g_dev_state != 1) { g_dev_state = 1; g_dev_wait = 0; }
      if (dev_can_warp(ram)) { g_dev_room = -1; dev_apply_warp(ram, room, g_dev_door); g_dev_state = 2; }
      else if (++g_dev_wait > DEV_PATIENCE) { g_dev_room = -1; g_dev_state = 3; }
   }
}

JNIEXPORT void JNICALL J(devStory)(JNIEnv *e, jclass c, jint step) { if (step >= 0 && step <= 0xFFFF) g_dev_story = step; }
JNIEXPORT void JNICALL J(devWarp)(JNIEnv *e, jclass c, jint room, jint door)
{
   if (room < 0 || room > 0xFFF) return;
   g_dev_door = door < 0 ? 0 : door & 0xFF;
   g_dev_state = 0;
   g_dev_room = room;
}
JNIEXPORT jint JNICALL J(devWarpState)(JNIEnv *e, jclass c) { return g_dev_state; }

/* ---- running a frame, timing, picture and sound ----
 * runFrame clears the cards' "new card" flag first (see McdFlag above), runs one frame, then lets the analog
 * installer check its program and the developer tools act. */
JNIEXPORT void JNICALL J(runFrame)(JNIEnv *e, jclass c) { if (g_loaded) { McdFlag[0] &= ~8; McdFlag[1] &= ~8; retro_run(); xga_tick(); dev_tick(); } }

JNIEXPORT jdouble JNICALL J(fps)(JNIEnv *e, jclass c) { return g_av.timing.fps > 1 ? g_av.timing.fps : 59.94; }
JNIEXPORT jdouble JNICALL J(sampleRate)(JNIEnv *e, jclass c) { return g_av.timing.sample_rate > 1 ? g_av.timing.sample_rate : 44100; }
JNIEXPORT jfloat JNICALL J(aspect)(JNIEnv *e, jclass c) { return g_av.geometry.aspect_ratio > 0 ? g_av.geometry.aspect_ratio : 4.0f / 3.0f; }

/* Copies the newest frame into a direct ByteBuffer if it changed since lastSeq.
 * Returns packed (w << 16 | h), or 0 if nothing new. */
JNIEXPORT jint JNICALL J(copyFrame)(JNIEnv *e, jclass c, jobject buf, jint lastSeq, jintArray seqOut)
{
   uint16_t *dst = (*e)->GetDirectBufferAddress(e, buf);
   jlong cap = (*e)->GetDirectBufferCapacity(e, buf);
   jint r = 0, seq;
   if (!dst) return 0;
   pthread_mutex_lock(&g_fb_lock);
   seq = g_fb_seq;
   if (seq != lastSeq && g_fb_w && (jlong)g_fb_w * g_fb_h * 2 <= cap) {
      memcpy(dst, g_fb, (size_t)g_fb_w * g_fb_h * 2);
      r = (g_fb_w << 16) | g_fb_h;
   }
   pthread_mutex_unlock(&g_fb_lock);
   (*e)->SetIntArrayRegion(e, seqOut, 0, 1, &seq);
   return r;
}

JNIEXPORT jint JNICALL J(readAudio)(JNIEnv *e, jclass c, jshortArray out)
{
   jint max = (*e)->GetArrayLength(e, out) / 2, n = 0;
   jshort *o = (*e)->GetShortArrayElements(e, out, NULL);
   pthread_mutex_lock(&g_ar_lock);
   while (n < max && g_ar_r != g_ar_w) {
      o[n * 2] = g_ar[g_ar_r * 2]; o[n * 2 + 1] = g_ar[g_ar_r * 2 + 1];
      g_ar_r = (g_ar_r + 1) % AR_FRAMES; n++;
   }
   pthread_mutex_unlock(&g_ar_lock);
   (*e)->ReleaseShortArrayElements(e, out, o, 0);
   return n * 2;
}

JNIEXPORT jint JNICALL J(audioQueued)(JNIEnv *e, jclass c)
{
   int w = g_ar_w, r = g_ar_r;
   return (w - r + AR_FRAMES) % AR_FRAMES;
}

/* ---- input (ports 0 and 1) ---- */
JNIEXPORT void JNICALL J(setButtons)(JNIEnv *e, jclass c, jint port, jint mask) { if (port >= 0 && port < 2) g_btn[port] = (uint32_t)mask; }
JNIEXPORT void JNICALL J(setAxes)(JNIEnv *e, jclass c, jint port, jint lx, jint ly, jint rx, jint ry)
{
   if (port < 0 || port > 1) return;
   g_axis[port][0] = lx; g_axis[port][1] = ly; g_axis[port][2] = rx; g_axis[port][3] = ry;
}
JNIEXPORT void JNICALL J(setStickDpad)(JNIEnv *e, jclass c, jboolean on, jint thresh) { g_stick_dpad = on; g_stick_dpad_thresh = thresh; }

/* ---- RAM for Link, the disc's ID, the core's messages ----
 * Link reads and writes main RAM by its PS1 address (any of the three mirrors). */
static uint8_t *ram_ptr(uint32_t addr, uint32_t len)
{
   uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
   uint32_t a;
   if (!ram || !g_loaded) return NULL;
   /* KUSEG / KSEG0 / KSEG1 mirrors of the 2MB main RAM */
   a = addr & 0x1FFFFFFF;
   if (a >= 0x00800000) return NULL;
   a &= 0x1FFFFF;
   if (a + len > 0x200000) return NULL;
   return ram + a;
}

JNIEXPORT jbyteArray JNICALL J(readRam)(JNIEnv *e, jclass c, jint addr, jint len)
{
   uint8_t *p; jbyteArray out;
   if (len <= 0 || len > 0x200000) return NULL;
   p = ram_ptr((uint32_t)addr, (uint32_t)len);
   if (!p) return NULL;
   out = (*e)->NewByteArray(e, len);
   (*e)->SetByteArrayRegion(e, out, 0, len, (const jbyte *)p);
   return out;
}

JNIEXPORT jboolean JNICALL J(writeRam)(JNIEnv *e, jclass c, jint addr, jbyteArray data)
{
   jint len = (*e)->GetArrayLength(e, data);
   uint8_t *p = ram_ptr((uint32_t)addr, (uint32_t)len);
   if (!p) return JNI_FALSE;
   (*e)->GetByteArrayRegion(e, data, 0, len, (jbyte *)p);
   return JNI_TRUE;
}

JNIEXPORT jstring JNICALL J(gameId)(JNIEnv *e, jclass c) { return (*e)->NewStringUTF(e, CdromId); }
JNIEXPORT jstring JNICALL J(gameLabel)(JNIEnv *e, jclass c) { return (*e)->NewStringUTF(e, CdromLabel); }

/* the core's newest on-screen message, if it's newer than the one Java last saw (seq) */
JNIEXPORT jstring JNICALL J(pollMessage)(JNIEnv *e, jclass c, jintArray seqInOut)
{
   jint seq; (*e)->GetIntArrayRegion(e, seqInOut, 0, 1, &seq);
   if (seq == g_msg_seq) return NULL;
   seq = g_msg_seq; (*e)->SetIntArrayRegion(e, seqInOut, 0, 1, &seq);
   return (*e)->NewStringUTF(e, g_msg);
}

/* ---- memory card and save states ----
 * Save states are the core's own serialization; two saves at the same frame differ in one byte (a counter the core
 * bumps on every save). */
JNIEXPORT jboolean JNICALL J(saveMemcard)(JNIEnv *e, jclass c)
{
   void *sram = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
   size_t sz = retro_get_memory_size(RETRO_MEMORY_SAVE_RAM);
   if (!g_loaded || !sram || !sz || !g_srm_path[0]) return JNI_FALSE;
   return save_file(g_srm_path, sram, sz) ? JNI_TRUE : JNI_FALSE;
}

/* cheap change detector so Java only writes the card when it changed */
JNIEXPORT jlong JNICALL J(memcardHash)(JNIEnv *e, jclass c)
{
   const uint8_t *p = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
   size_t sz = retro_get_memory_size(RETRO_MEMORY_SAVE_RAM), i;
   uint64_t h = 1469598103934665603ULL;
   if (!g_loaded || !p) return 0;
   for (i = 0; i < sz; i++) { h ^= p[i]; h *= 1099511628211ULL; }
   return (jlong)h;
}

JNIEXPORT jboolean JNICALL J(saveState)(JNIEnv *e, jclass c, jstring jpath)
{
   char path[600]; size_t sz; void *buf; jboolean ok = JNI_FALSE;
   if (!g_loaded) return JNI_FALSE;
   jstr(e, jpath, path, sizeof(path));
   sz = retro_serialize_size();
   if (!sz || !(buf = malloc(sz))) return JNI_FALSE;
   if (retro_serialize(buf, sz) && save_file(path, buf, sz)) ok = JNI_TRUE;
   free(buf);
   return ok;
}

/* The state as bytes, so a save can be written to disk off the emulator thread (the safety save while playing):
 * serializing takes a few ms, writing 4 MB to storage much longer. NULL if there is no game or no memory. */
JNIEXPORT jbyteArray JNICALL J(stateBytes)(JNIEnv *e, jclass c)
{
   size_t sz; void *buf; jbyteArray out = NULL;
   if (!g_loaded) return NULL;
   sz = retro_serialize_size();
   if (!sz || !(buf = malloc(sz))) return NULL;
   if (retro_serialize(buf, sz) && (out = (*e)->NewByteArray(e, (jsize)sz)) != NULL)
      (*e)->SetByteArrayRegion(e, out, 0, (jsize)sz, (const jbyte *)buf);
   free(buf);
   return out;
}

/* loads a state (and, if it was saved on the other disc, the core switches to it); the analog installer switches the
 * pad to analog again afterwards */
JNIEXPORT jboolean JNICALL J(loadState)(JNIEnv *e, jclass c, jstring jpath)
{
   char path[600]; size_t sz; void *buf; FILE *f; long fl; jboolean ok = JNI_FALSE;
   if (!g_loaded) return JNI_FALSE;
   jstr(e, jpath, path, sizeof(path));
   f = fopen(path, "rb");
   if (!f) return JNI_FALSE;
   fseek(f, 0, SEEK_END); fl = ftell(f); fseek(f, 0, SEEK_SET);
   sz = retro_serialize_size();
   if (fl > 0 && (size_t)fl <= sz + 4096 && (buf = calloc(1, sz > (size_t)fl ? sz : (size_t)fl))) {
      if (fread(buf, 1, fl, f) == (size_t)fl && retro_unserialize(buf, fl)) { ok = JNI_TRUE; g_xga_pad = 0; }
      free(buf);
   }
   fclose(f);
   return ok;
}

/* ---- reset and GameShark codes (mods) ---- */
JNIEXPORT void JNICALL J(reset)(JNIEnv *e, jclass c) { if (g_loaded) { retro_reset(); g_xga_pad = 0; } }

JNIEXPORT void JNICALL J(setCheat)(JNIEnv *e, jclass c, jint index, jboolean enabled, jstring code)
{
   char buf[2048];
   if (!g_loaded) return;
   jstr(e, code, buf, sizeof(buf));
   retro_cheat_set((unsigned)index, enabled, buf);
   if (index + 1 > g_cheats_set) g_cheats_set = index + 1;
}
JNIEXPORT void JNICALL J(clearCheats)(JNIEnv *e, jclass c) { if (g_loaded) retro_cheat_reset(); g_cheats_set = 0; }

/* ---- discs ----
 * The boot disc is image 0; the other disc is queued with appendDisc and swapped in with setDisc (Pause > DISC).
 * Switching clears CdromId; only a game load sets it again. */
JNIEXPORT jint JNICALL J(discCount)(JNIEnv *e, jclass c) { return g_disk_have && g_disk.get_num_images ? (jint)g_disk.get_num_images() : 0; }
JNIEXPORT jint JNICALL J(discIndex)(JNIEnv *e, jclass c) { return g_disk_have && g_disk.get_image_index ? (jint)g_disk.get_image_index() : 0; }

JNIEXPORT jboolean JNICALL J(setDisc)(JNIEnv *e, jclass c, jint idx)
{
   bool ok;
   if (!g_disk_have || !g_disk.set_eject_state || !g_disk.set_image_index) return JNI_FALSE;
   g_disk.set_eject_state(true);
   ok = g_disk.set_image_index((unsigned)idx);
   g_disk.set_eject_state(false);
   return ok ? JNI_TRUE : JNI_FALSE;
}

/* Adds a disc image (e.g. disc 2) and switches to it. */
JNIEXPORT jboolean JNICALL J(addDisc)(JNIEnv *e, jclass c, jstring jpath)
{
   char path[600]; struct retro_game_info gi; unsigned idx; bool ok;
   if (!g_disk_have || !g_disk.add_image_index || !g_disk.replace_image_index) return JNI_FALSE;
   jstr(e, jpath, path, sizeof(path));
   memset(&gi, 0, sizeof(gi)); gi.path = path;
   g_disk.set_eject_state(true);
   idx = g_disk.get_num_images();
   ok = g_disk.add_image_index() && g_disk.replace_image_index(idx, &gi) && g_disk.set_image_index(idx);
   g_disk.set_eject_state(false);
   return ok ? JNI_TRUE : JNI_FALSE;
}

/* Queues another disc image (e.g. disc 2) without inserting it. Returns its index or -1. */
JNIEXPORT jint JNICALL J(appendDisc)(JNIEnv *e, jclass c, jstring jpath)
{
   char path[600]; struct retro_game_info gi; unsigned idx;
   if (!g_disk_have || !g_disk.add_image_index || !g_disk.replace_image_index || !g_disk.get_num_images) return -1;
   jstr(e, jpath, path, sizeof(path));
   memset(&gi, 0, sizeof(gi)); gi.path = path;
   idx = g_disk.get_num_images();
   if (!g_disk.add_image_index() || !g_disk.replace_image_index(idx, &gi)) return -1;
   return (jint)idx;
}

/* ---- analog mode, card status, the live memory card ---- */
/* Puts port 1 in DualShock analog mode (on) or digital mode. Xenogears never switches the pad itself.
 * (The app lets the analog installer do this; tests/drive.c calls it directly.) */
JNIEXPORT void JNICALL J(setAnalogMode)(JNIEnv *e, jclass c, jboolean on)
{
   int r;
   if (!g_loaded) return;
   r = padToggleAnalog(0);
   if ((r != 0) != (on != 0)) padToggleAnalog(0);
}

JNIEXPORT jint JNICALL J(cardStatus)(JNIEnv *e, jclass c) { return g_card_status; }

/* the live memory card (card 1) while a game is loaded */
JNIEXPORT jbyteArray JNICALL J(readMemcard)(JNIEnv *e, jclass c)
{
   void *sram = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
   jbyteArray out;
   if (!g_loaded || !sram || retro_get_memory_size(RETRO_MEMORY_SAVE_RAM) != MCD_BYTES) return NULL;
   out = (*e)->NewByteArray(e, MCD_BYTES);
   (*e)->SetByteArrayRegion(e, out, 0, MCD_BYTES, (const jbyte *)sram);
   return out;
}

JNIEXPORT jboolean JNICALL J(writeMemcard)(JNIEnv *e, jclass c, jbyteArray data)
{
   void *sram = retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
   if (!g_loaded || !sram || (*e)->GetArrayLength(e, data) != MCD_BYTES) return JNI_FALSE;
   (*e)->GetByteArrayRegion(e, data, 0, MCD_BYTES, (jbyte *)sram);
   return save_file(g_srm_path, sram, MCD_BYTES) ? JNI_TRUE : JNI_FALSE;
}

/* ---- unloading: save the card, then unload the disc ---- */
JNIEXPORT void JNICALL J(unload)(JNIEnv *e, jclass c)
{
   if (!g_loaded) return;
   J(saveMemcard)(e, c);
   retro_unload_game();
   g_loaded = 0;
}
