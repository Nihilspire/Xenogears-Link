XENOGEARS DUAL 0.25 — Xenogears with Xenogears Link 2.0.0.22 on the second screen (test build)

  Built on the pcsx_rearmed core (GPL, libretro/pcsx_rearmed @ c881679).

LAUNCHER
  CONTINUE (from 0.18): leaving the game (app to the background, Pause > LAUNCHER, closing it) saves where you
  are to states/Xenogears.resume.state with a picture; the launcher shows it and CONTINUE starts the disc it was
  on and loads it. From 0.20 it's also saved every 5 minutes of play (the state is copied on the emulator thread,
  Native.stateBytes, and written in the background), in case the app never gets to leave. A fresh START played under two minutes doesn't replace it. Settings > System > Remember my
  place turns it off. With SHOW AT START off, the app continues straight away.
  Disc 1 / Disc 2: choose the .cue, .chd or .pbp for each; with both chosen, "Boot" picks which one START boots.
  The other disc is queued so you can swap from the pause menu when the game asks.
  Mods (their own screen from 0.18, from the launcher or the pause menu): Analog controls (Jack's xg_analog
  program from assets/analog.cht, on by default, with its five option switches) plus GameShark codes you add.
  Since 0.14 the analog program isn't sent through the cheat engine. jni/psxlink.c installs it after each
  frame, and only when: the Xenogears executable is in RAM (VSync hook at 0x80036388 matches), and the
  block at 0x80017400 is empty or already holds the program. It then tells the recompiler about the write,
  sets the hook slot 0x800501FC while it is 0, tops up the option bytes, and switches the pad to analog
  mode once the game is running (not before the first frame). If the game ever has other data in that
  block, the hook is removed and a note appears under the Analog controls switch.
  0.16 also patches the program's camera-mode check (lw -> lhu at 0x8001785C) so the right stick works;
  from 0.18 assets/analog.cht carries that fix itself (the runtime patch only acts on the old word).
  Touch: drag on the picture = right stick (camera); double-tap the picture = R3 (camera reset).
  Gear icon (top right): settings in tabs: Controls (incl. Controller buttons > REBIND), Screens, Picture,
  Card, System (BIOS, sound, launcher). SHOW AT START off = later launches go straight into the game.
  Pause menu: ≡ on the touch pad, Back, or Select+Start on a controller. Save states with a picture and time
  each: QUICK (states/Xenogears.quick.state, the hotkeys' slot) and slots 1-8 (Xenogears.slotN.state + .jpg;
  Link's SAVE STATES shows 1-4), DEL asks first. Disc swap, fast forward, mods, RESET (asks first), settings,
  LAUNCHER.
  Hotkeys (0.20, Settings > Controls > Hotkeys): quick save, quick load, fast forward, each on a controller
  button you pick (prefs "hotkeys"). That button stops pressing its PlayStation button; rebinding it to a
  game button takes it off the hotkey. Off until set.
  Memory card: Settings > Card > EXPORT CARD writes saves/export/Xenogears-<date>.srm (0.20).

SCREENS
  Surface Duo spanned: game on one half, Xenogears Link on the other (Swap screens flips them).
  A real second display: Link opens there.

FRAME PACING
  The emulator runs from the display's vsync (GameView.onDrawFrame -> Emu.vsync): one game frame per
  refresh on ~60 Hz screens, a time accumulator on others. Audio is written without blocking and
  resampled by up to 0.5% to hold ~64 ms of buffer (dynamic rate control). Before 0.13 the audio
  buffer set the pace, which made frames arrive in bursts.

FOLDER  /sdcard/Xenogears
  saves/Xenogears.srm  memory card (shared by both discs). At START a file that isn't a formatted card is
                       kept as Xenogears.srm.bad-<time> and a fresh formatted card is used.
                       Settings > Memory card: status, saves on it, FORMAT, IMPORT (.srm .mcr .mcd .gme);
                       both keep the old card in saves/backup/.   states/  4 save-state slots
  link/index.html      a Xenogears Link page to use instead of the built-in 2.0.0.22 one
  bezels/*.png         your own bezels: a PNG with a see-through middle, stretched to the game screen;
                       the see-through part becomes the picture. Pick it in Settings > Picture > Bezel.
  mods.txt             extra mods, one per line:  Name | 80012345 0001

LINK
  assets/link/ is the www folder of Xenogears Link 2.0.0.22, updated in 0.18 to GitHub Nihilspire/Xenogears-Link
  main, now @ bfe92a7 (hsplit.js: Hint 114 sewer walkthrough order; hints.js: Hint 67 grates; index.html: tour wording). It talks to window.Native exactly as in its own
  APK; here poll() answers from emulator RAM (no UDP), FF toggles fast-forward, and the room-map builder
  reads Disc 1 from the launcher instead of asking for a file. Changed from 2.0.0.22 (shown as
  "2.0.0.22 DUAL"): Link's SETTINGS has a SAVE STATES group (4 slots, the same ones as the pause menu),
  through Native.stateInfo / stateSave / stateLoad and the onStateDone(slot, ok, what) callback; from 0.18
  each slot shows its picture (Native.stateThumb). From 0.21 Link's developer options are turned on and off with
  the Konami code on a controller (↑ ↑ ↓ ↓ ← → ← → B A, with Dual's menu open; Konami.java), not five taps on
  Link's version line. From 0.19 the RPS and Speed helpers (DEV-only in Link) are
  on by default and switched under SETTINGS > MINIGAMES; each shows only during its minigame.
  Link has no start screen here: it links as soon as it opens, shows the title logo until the game
  is running, and its START SCREEN switch and RetroArch help are hidden.
  The map (2D and 3D) polls every 20 ms while moving (80 ms still) on this direct link; RetroArch keeps 50 / 200 ms.

EXTRA API  (window.XenoLink)
  running(), disc(), gameId(), frame(), u8/u16/u32(addr), readHex(addr,len), writeHex(addr,hex)
  command("READ_CORE_MEMORY 8007f0c0 16") answers exactly like RetroArch's UDP command;
  window.RetroArch.send(cmd) is a shim over it.

REBUILD   core/build_core.sh, then app/build_jni.sh, then app/build.sh -> "Xenogears Dual <version>.apk" (see CLAUDE.md)
SIGNING   keep signing/xenogears.jks  (not in this repo; alias xenogears, password in XG_DUAL_KS_PASS)
GPL       fine for personal use; if you share the APK, share this source with it.
