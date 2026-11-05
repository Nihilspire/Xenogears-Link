# Porting a PS1 Link app to a "Dual" APK

How Koudelka Dual 0.1 was made from Xenogears Dual 0.13 (Oct 22 2026). Use the same steps for the next game.
(Copy of the claude.ai Project doc `claude/porting-a-dual-app.md`, with paths adjusted to this repo.)

## What a Dual app is
One APK: pcsx_rearmed (libretro core, GPL, @ c881679) + a small JNI layer (app/jni/psxlink.c) + a Java host
(game view, touch pad, bezel, screens) + two WebViews: the launcher/pause menu (assets/menu) and the game's
Link page (assets/link = the Link APK's assets/www). Link pages call `window.Native.poll(host, port, mode,
pagesCsv, seq)` and get `onMem({seq,sent,got,err,ok:{page:hex}})` back; Dual answers that from emulator RAM.

## Steps
1. Toolchain (fresh machine): `./setup.sh` (apt packages, bionic headers, pcsx_rearmed, work folders; the stub
   sysroot and clang wrapper are already in toolchain/). Keep `app/out/lib/arm64-v8a` committed so the core
   doesn't need rebuilding.
2. Copy the source tree; rename the package everywhere (Java `package`, manifest, and the JNI prefix in
   psxlink.c's `J()` macro, e.g. `Java_com_jack_koudelka_Native_`); rename the native lib in Native.java.
3. MainActivity: VERSION, game IDs (check them with the test driver), prefs name, /sdcard/<Game> folder,
   card and state file names, number of discs (DISCS + the disc queue in startGame), app label, new signing key.
4. Check the Link page's Native calls (`grep -o 'Native\.[a-zA-Z_]*'`) and give LinkNative each one
   (Koudelka needed version(), focusable(), poll(), send()). Drop the previous game's extras.
5. Link page changes, all behind a `DUAL` flag (`window.Native && Native.stateInfo`): skip its start screen,
   move any switches that lived only on the start screen into its settings, add SAVE STATES
   (stateInfo/stateSave/stateLoad + onStateDone), hide host/port/link mode. Ship a .patch against the original.
6. Launcher: rebuild assets/menu from the Link page's own font/panels/art (Koudelka: font extracted to kfont.js).
   Restyle BezelView's "window" frame the same way. New icon.
7. Test: build the core for the desktop (`tests/build_host.sh`; with the upstream Makefile pass
   LIGHTREC_CUSTOM_MAP=0 — the custom map puts RAM at address 0, which readRam treats as missing), link
   tests/drive.c, boot the real disc, dump RAM, and render the Link page in headless Chromium with a mock Native
   that answers poll() from the dump. Compare Native.java's native methods with the .so's exported Java_ symbols.

## Fixes made in Xenogears Dual after 0.13 — carry these into other Dual apps
- **Memory card "not formatted" with the built-in BIOS (0.16, affects every game).** The core flags cards as
  "new" (`McdFlag |= 8`) at power-on, reset and every state load. The HLE BIOS answers `_card_info` with
  EvSpNEW until something is written, and save menus read that as "not formatted" (loading still works).
  Fix: export `McdFlag` in the core's version script and clear bit 8 of both slots in `runFrame` before
  `retro_run`. Check: load a state at a save point, save into a free block.
- **Controller rebinding (0.17).** Settings > Controls > Controller buttons > REBIND. Bindings are a
  keycode -> button map in prefs `keyBinds` (JSON); setting a key that's already used swaps the two.
  The key is captured on ACTION_DOWN and its ACTION_UP is swallowed so it doesn't also press a menu item.
- **Right stick on pads without AXIS_Z (0.16):** read RX/RY instead. Only when Z is missing, because the
  DualShock 4 puts its analog triggers on RX/RY.
- **Link map polling (0.17):** in DUAL the MAP tab polls every 20 ms while moving and 80 ms when still
  (was 40/150, 3D only). Fine since 0.13's vsync-driven pacing.
- Xenogears only: the analog controls program is installed by psxlink.c instead of the cheat engine
  (writes it once into empty RAM after the exe signature matches, calls psxCpu->Clear, stands down if
  the block holds something else), and patches a lw -> lhu bug in its camera-mode check (0x8001785C).

## Koudelka specifics
- Disc IDs (USA): SLUS01051, SLUS01100, SLUS01101, SLUS01102. Boots on the built-in BIOS.
- Koudelka Link roots: A 0x800AF470 (scene at A+0x368: 1 field, 2 battle, 3/4 movie), G 0x800B4DD0.
- Battle menu opens on Triangle; Circle confirms.
