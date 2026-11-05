# Xenogears Dual

One Android APK: Xenogears (PS1) running in pcsx_rearmed, with the Xenogears Link companion page on the
second screen (Surface Duo spanned, or a second display). Package `com.jack.xenogears`, app label
"Xenogears Dual", current version **0.25** (versionCode 25). Jack tests on an Android handheld/Duo; there is
no device here, so every change is checked in emulation first (see Testing) and the APK is handed over.

## Working agreements (from Jack)
- After every build, give Jack the APK as **one whole file** (he can't join split parts). Name: `Xenogears Dual <version>.apk`.
- Bump the version for every build: `app/AndroidManifest.xml` (versionCode + versionName),
  `MainActivity.VERSION`, first line of `app/README.txt`.
- Commit locally; don't ask about pushing.
- Keep `app/signing/xenogears.jks` (not in this repo; alias `xenogears`, password in `XG_DUAL_KS_PASS`). A different key means Android
  refuses the update and Jack must uninstall (losing app data). Don't publish this repo with the key in it.
- Link comes from GitHub `Nihilspire/Xenogears-Link` (public): its `app/www/*` plus `app/index.html` (copied in as
  index.html by its build). Built files (`font.js`, `bundled.js`, `img/`, `world/`, `maps/`, `plan/`, `spr/`) aren't in
  git: keep Dual's. To update: copy the changed www files; if `app/index.html` changed, apply the Dual patch to it.
  Now matches main @ bfe92a7 (2.0.0.22 + Hint 114 hsplit.js, Hint 67 hints.js, the tour wording in index.html).
- When Link's page changes, regenerate `patches/Xenogears Link 2.0.0.22 - Dual changes.patch`
  (`diff -u --label a/index.html --label b/index.html patches/link_index_2.0.0.22.orig.html app/assets/link/index.html`).

## Layout
```
app/                 the Android app (no Gradle)
  AndroidManifest.xml, res/, src/com/jack/xenogears/*.java
  jni/psxlink.c      JNI frontend for the libretro core (video, audio, input, RAM, memcard, states,
                     cheats, discs, analog-controls installer, diagnostics). Also compiled into tests/drive.c.
  assets/menu/       launcher / settings / pause menu (index.html + xgfont.js), styled like the game's menus
  assets/link/       Xenogears Link 2.0.0.22 www folder + the Dual edits (DIRECT/DUAL flag, SAVE STATES, ...)
  assets/analog.cht  Jack's analog controls (RetroArch .cht); its "code" entries are the MIPS program
  out/lib/arm64-v8a/ prebuilt libpcsx_rearmed.so (core) + libxenolink.so (jni) that build.sh packs
  build.sh           aapt -> javac (--release 8) -> dalvik-exchange -> zipalign -> apksigner
  build_jni.sh       builds libxenolink.so (and copies a newer core/pcsx_rearmed_libretro_android.so in)
core/build_core.sh   compiles pcsx_rearmed for arm64 Android with toolchain/android-clang (ari64 dynarec,
                     NDRC_THREAD, NEON GPU, async CD/GPU/SPU, CHD). psxlink-version-script = exported symbols.
toolchain/           NDK-less Android toolchain: android-clang wrapper (system clang 18 + bionic headers),
                     stub sysroot (libc/libm/libdl/liblog .so stubs from bionic .map.txt via gen_stubs.py,
                     crtbegin/crtend, libgcc.a with __clear_cache)
tests/               headless test rig (see Testing)
patches/             Link changes as a patch + the original Link 2.0.0.22 index.html
releases/            the last APK handed to Jack
docs/                CHANGELOG, technical notes, the porting guide for other games (Koudelka Dual was made from 0.13)
third_party/, work/  created by setup.sh (sources, build output, test data) — not committed
```

## Setup and build (Linux or WSL Ubuntu 24.04/26.04)
On Jack's PC the repo is `Desktop\Claude\Xenogears\xenogears-dual` (`/mnt/c/Users/Jackson/Desktop/Claude/Xenogears/xenogears-dual`
in WSL Ubuntu 26.04). sudo there needs Jack's password, so run setup.sh's apt step as root
(`wsl -u root`) and then `./setup.sh --no-apt` as the normal user. Run WSL commands from a script file: PowerShell
mangles `$` and quotes passed through `wsl -- bash -c`.
```
./setup.sh                 # apt packages, clones pcsx_rearmed@c881679 (+libpicofe) and a sparse bionic@731631f,
                           # builds the stub sysroot (toolchain/build_sysroot.sh -> toolchain/sysroot, not committed)
core/build_core.sh         # -> core/pcsx_rearmed_libretro_android.so   (only needed when the core changes)
app/build_jni.sh           # -> app/out/lib/arm64-v8a/libxenolink.so (+ copies the new core in)
app/build.sh               # -> app/Xenogears Dual <version>.apk
```
Java/menu/Link-only changes need just `app/build.sh`. psxlink.c changes need `build_jni.sh` first.
Builds are reproducible: on 26.04 (clang 18.1.8) the 0.17 sources rebuild to an APK whose files are all byte-identical
to the shipped 0.17; libxenolink.so `.text` is identical, and the core differs only in its build-time and compiler
strings. That relies on `android-clang` calling `clang-18` with `--build-id=fast` and on build_core.sh's
`-ffile-prefix-map` (keep both).
The core is used unmodified; anything extra the frontend needs is exported through
`core/psxlink-version-script` (currently `retro_*`, `CdromId`, `CdromLabel`, `padToggleAnalog`, `psxCpu`, `McdFlag`).
Don't run pcsx_rearmed's own Makefiles (an earlier environment blocked running third-party build scripts);
the build_*.sh scripts list the sources and flags themselves.

## Testing (no phone needed)
Game files are not in the bundle. Put Jack's Disc 1 CHD at `work/host/xg/disc1.chd`
(on his PC: `Desktop\Claude\Xenogears Decomp\Xenogears (USA) (Disc 1).chd`; Disc 2 is beside it).
```
tests/build_host.sh        # x86-64 core (interpreter) -> work/host/libpcsx_rearmed.so
tests/build_arm.sh         # aarch64 core with the same ari64 dynarec as the phone -> work/arm/ (run under qemu-aarch64)
tests/build_drivers.sh     # links tests/drive.c (includes app/jni/psxlink.c) into work/host/drive and work/arm/drive
tests/build_debug.sh       # optional: x86 core with HLE BIOS call logging (run with DBG=1 BIOSLOG=1 ERRF=log)
tests/build_openbios.sh    # optional: OpenBIOS from pcsx-redux/nugget (clone to third_party/nugget) as a real-BIOS stand-in
```
`drive` reads line commands on stdin: `init sys save`, `var key value`, `load disc.chd card.srm padType`,
`run N`, `btn mask`, `axes lx ly rx ry`, `analog 0|1`, `cheat i en code`, `xga on opts prog.bin`, `xgastate`,
`read addr len`, `save/loadstate path`, `shot file.ppm`, `cardstatus`, `diag`, `quit`.
`tests/scripts/xg.py` wraps it (`D()`; `ARM=1` uses the qemu ARM build, `DBG=1` the BIOS-logging build).
Useful scripts: `xg_nat6.py natob_room.state` (camera/L1 with the analog installer, Fei's room),
`xg_native.py auto|HLE tag` (boot to Fei's room with analog on), `xg_sv.py HLE tag "[...]"` (save at a save
point from `lh_loaded.state` with `real.srm`), `xg_real.py`/`xg_del.py` (Continue screen load/delete),
`epsx_scan.py` (scan ePSXe states' RAM), `ui18.py`/`link_*_test.py` (render the menu/Link in headless Chromium
with a mock bridge; needs `pip install playwright`; `ui18.py` uses `thumbs.py`'s pictures and checks controller
navigation reaches every button), `disc2_test.py` (needs `work/host/xg/disc2.chd`). Scripts find the repo via
`XGROOT` or their own location. `drive` also has `appenddisc path`, `setdisc i`, `discs`, `reset`, `gameid`.
States in `tests/data/` were made with this core: `natob_room.state` (Fei's room, player control),
`lh_loaded.state` (real save loaded, standing at a save point), `newgame.state`, `boot2400.state`, `clean_field.state`.

Hints: `hint_walk.py ~/xgtmp/walk 16` warps to every room every hint names and dumps RAM (about 9 minutes; `drive` has `devstory`, `devwarp`,
`devstate`, `devcan`, `dumpram`). `hint_sweep.py ~/xgtmp/walk ~/xgtmp/sweep 3` shows those and the Link repo's saved dumps (`~/xghandoff/x`, from its
handoff zip) to Link headless, and carries on if run again after dying. `hint_report.py ~/xgtmp/sweep OUTDIR` makes the page.

## Things that bit us (read before changing these areas)
- **Memory card + built-in (HLE) BIOS:** the core marks cards "new" at power-on, reset and every state load;
  the HLE BIOS then reports EvSpNEW and Xenogears' save menu says "not formatted". `runFrame` clears
  `McdFlag` bit 8 every frame. Card *loading* worked even before the fix, so test *saving*.
- **Analog controls:** installed by `xga_tick()` in psxlink.c, not the cheat engine: only after the exe's
  VSync code at 0x80036388 matches, only into an empty (or same-program) block at 0x80017400, then
  `psxCpu->Clear()`, hook slot 0x800501FC set while 0, option bytes 0x80017F04..08 topped up, pad switched to
  analog once. The program's camera check read the 16-bit camera mode at 0x800AF934 with `lw`, picking up
  0x800AF936 too, so the right stick never worked in rooms like Fei's; `setAnalogMod` patches the word at
  program offset 0x45C (`8D4DF934` -> `954DF934`). User mods that write into 0x80017400-0x80017FFF or the hook
  slot are skipped while analog is on.
- **Frame pacing:** the emulator is driven from the GL vsync (`GameView.onDrawFrame -> Emu.vsync`), audio is
  non-blocking with ±0.5% dynamic rate control. Don't go back to audio-paced or timer-paced loops.
- **Second screen:** `LinkPresentation` must stay non-cancelable/non-focusable and forward keys, or the
  B/back button closes Link.
- **Right stick input:** Z/RZ, falling back to RX/RY only when the pad has no Z axis (DualShock 4 puts its
  triggers on RX/RY).
- **JNI strings:** `NewStringUTF` aborts on invalid UTF-8 on Android; sanitise anything from game RAM/cards.
- **Link polling:** in DUAL, the map polls every 20 ms moving / 80 ms still (`pollGap` in Link's index.html).
- **Saving in onPause:** `gameView.onPause()` stops the GL thread, so `emu.post()` from onPause only queues (until the
  app returns). Anything that must happen as the app leaves goes through `emu.runNow()` (see `saveOnLeave`).
- **Disc swaps:** the core clears `CdromId` on every image switch and only a game load sets it again, so don't use
  the ID to tell which disc is in. `retro_unserialize` switches to the disc a state was saved on by itself.
- **Menu font:** the game font has no `;` (it draws a gap). `cut()` trims labels to 24 characters.
- **WSL temp:** `/tmp` is a 3.8 GB RAM disk; disc-image work goes in `~/xgtmp` (TMPDIR).
- **Save states differ by one byte:** two saves at the same frame differ at offset 0x298049 (a counter the core bumps on
  every save), so compare states apart from that byte (state_bytes_test.py does).
- **Link's DEV options in Dual:** the Konami code with the menu open (Konami.java, MainActivity.toggleDev), not
  Link's five version taps (devTap returns early when DIRECT). Test the sequence with `tests/konami/run.sh`.
- **After a warp, the room number lies:** 0x8006F94E changes at once, the old room stays on screen for a few seconds and the game briefly looks
  ready. Arrival is the load flag 0x800AFD04 going up and down, then `dev_can_warp` (hint_walk.py `arrive`).
- **Heavy parallel work can end the WSL session:** 6 or 10 headless browsers, and build_arm.sh's 8 compiles, each died with `wsl` exiting 1 and no message
  (cause not found). 3 browsers and 3 compiles ran through (hint_sweep.py; `sed 's/-ge 8/-ge 3/'` on build_arm.sh).
- **Single-screen layout (rails):** Link's page covers the whole screen and is see-through over the game (`html.rail`, `railDraw`), with `RailPane` passing touches there
  to the touch pad. One Link pixel is 1/360 of the screen's height; the bars are 80 wide on 16:9 (8 letters) and the panel 320, so `remSize` says 320 wide in this mode.
  The small map copies `#mapcv`, so the page keeps the MAP tab underneath while the panel is shut.
  Panel only (0.24, `PANEL`, `html.panelonly`, `railMode` 1): the same panel and arrow with no bars; one Link pixel is 1/320 of the shorter side. Link's sizes snap to whole pixels, so it reports them to RailPane (`railGeom`). The choice is the `layout` setting (`layoutChoice`): 16:9, 4:3 or second screen; the first two override a second display.
- **Resume files have one writer at a time:** the safety save (saveIo thread) and saveOnLeave both take `resumeIo`.

## Open items / ideas
- Fixed 23 Oct (0.18): Jack's `.cht`, codes list and both xdelta disc patches in `Xenogears Decomp\Recomp\retroarch`
  had the camera-mode `lw` bug; `tests/scripts/fix_analog_camera.py` rebuilt them (originals in `old (camera bug)`),
  checked with `disc_camera_test.py` (boots the patched disc to Fei's room).
- Disc 2: `tests/scripts/disc2_test.py` covers boot + installer, swap, and continue. Not covered: playing from a
  real Disc 2 save (none here), e.g. saving to the card on Disc 2.
- Not device-tested yet: CONTINUE/thumbnails (`writeThumb` uses Bitmap; the headless driver can't run Java).
- `Settings > Diagnostics` UI was removed in 0.17; `Native.diagnostics()` / `App.diagnostics()` still exist
  if a report is needed again.
