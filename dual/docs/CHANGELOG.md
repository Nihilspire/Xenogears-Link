# Xenogears Dual — changelog

Early entries are reconstructed from the conversation, so their version boundaries are approximate.

- **0.25** — One setting for the layouts, Settings > SCREENS > Layout: 16:9, 4:3 or SECOND SCREEN (the default, as before). 16:9 and 4:3 stay on one screen even with a second
  display connected or the Duo spanned. 16:9 on a screen narrower than 3:2 uses the 4:3 layout. Fixed from 0.24, which was built with failing tests and never handed over: the
  panel's shadow fell on the game's right edge while shut, and the page's sizes snap to whole pixels, so the app could disagree with it about where the panel and arrow are; the
  page now reports them (railGeom). Tested: link_rail_test.py, menu_layout_test.py. Not tested on a device.
- **0.24** — Link panel button, for a 4:3 screen (Settings > SCREENS): the game fills the screen with just a part see-through arrow on its right edge, which slides the
  whole Link page in over 3/4 of the screen and keeps the tab you left it on. The "Link panel" hotkey works here too. Tested: link_rail_test.py. Not tested on a device.
- **0.23** — A layout for one wide screen (Settings > SCREENS > Quick info beside game, held sideways, 3:2 or wider). The game is 4:3 in the middle, with
  Link's quick info in the bars either side: the party, time and money on the left; the place, a small map, the hint, chests and battle countdown on the right;
  in a fight, the enemies and who's next. An arrow, or a new "Link panel" hotkey, slides the whole Link page in over the right half. Tested: link_rail_test.py
  (the page, with real field and battle RAM). Not tested on a device: the page over the game, and touches passing through to the touch pad.
- **0.22** — Story jump for checking hints, in Link's DEV section (Konami code): set the story step, or step to the previous or next
  hint, warp to a room and door or to the current hint page's room. Same writes as the recomp's dev warp, in psxlink.c (devStory, devWarp,
  devWarpState). After a jump CONTINUE isn't updated, and the room and progress logs stop, until a state is loaded or a game started.
  New tests: dev_warp_test.py (real game), link_jump_test.py. New tools: hint_walk.py (warps to every room every hint names and dumps
  RAM), hint_sweep.py (runs those and the Link repo's saved dumps through Link), hint_report.py (the page).
- **0.21** — Link's developer options unlock with the Konami code (↑↑↓↓←→←→ B A on a controller with the menu open;
  again turns them off) instead of five taps on Link's version line. After the eight directions B is held back
  until the next key, so B still means "back" when the code isn't finished. Code tidied and every section commented
  (no behaviour change: native .text byte-identical, bytecode the same). Tested: tests/konami (7 cases),
  link_dev_test.py (Dual and standalone Link).
- **0.20** — Controller hotkeys (quick save, quick load, fast forward; Settings > Controls > Hotkeys). A QUICK save
  slot for them and 8 numbered slots, each with DEL (asks first). EXPORT CARD (saves/export/*.srm). Safety save for
  CONTINUE every 5 minutes of play, written off the emulator thread (new JNI stateBytes). Link's app tour reworded:
  no emulator/RetroArch in Dual, plainer English (same fixes in the Link repo). Tested: state_bytes_test.py (stateBytes
  equals saveState apart from the core's save counter, loads back pixel-identical, both discs), ui20.py.
- **0.19** — Link's RPS helper (Lahan rock-paper-scissors man) and Speed helper (card game) out of DEV OPTIONS:
  on by default, switches under SETTINGS > MINIGAMES, no DEV tag on the card. Checked with link_rps_test.py.
- **0.18** — CONTINUE: leaving the game saves where you are (resume state + picture + disc) and the launcher
  picks it up; a fresh START under 2 minutes doesn't replace it; Settings > System > Remember my place. Save-state
  pictures and readable times (TODAY 14:05) in the pause menu and Link's SAVE STATES. The memory card is now saved
  straight away when the app goes to the background (it used to wait for the app to come back: `Emu.runNow`).
  Menu cleanup: Mods on their own screen, settings in tabs, one settings button, RESET asks first, disc BOOT
  chips only with two discs, shorter notes. analog.cht carries the camera-mode lhu fix. Tested: Disc 2 boots
  with the analog installer, disc swap reaches Disc 2, a Disc 2 state continues pixel-identical.
- **0.17** — Link map polls every 20 ms moving / 80 ms still in DUAL (was 40/150, 3D only). Controller
  rebinding (Settings > Controls > Controller buttons > REBIND; keycode -> button map in prefs `keyBinds`,
  setting a used key swaps). Diagnostics section and the RUNNING/WAITING analog label removed from the menu.
- **0.16** — In-game saving with the built-in BIOS fixed (clear `McdFlag` "new card" bit every frame).
  Analog right-stick camera / smooth L1-R1 fixed (program's camera-mode check lw -> lhu). Right stick read
  from RX/RY on pads without AXIS_Z. Diagnostics lists controller axes.
- **0.15** — Settings > Diagnostics (report + diagnostics.txt). User mods that write over the analog program
  are skipped; another copy of the same program in RAM is replaced instead of standing down.
- **0.14** — Analog controls back on, installed by the frontend instead of the cheat engine (exe-signature
  check, empty-block check, dynarec Clear, analog mode set after the game starts, STOOD DOWN guard).
- **0.13** — Frame pacing rewritten: emulator driven from the display vsync, non-blocking audio with dynamic
  rate control (±0.5%).
- **0.12 / 0.11** — Link minimap polling eased back down twice for low-end devices (33/100 ms, then 40/150 ms
  for the 3D map). Link's start screen removed in DUAL.
- **0.9 – 0.10** — Memory card validation (bad files kept as `.bad-<time>`, fresh formatted card), card tools
  (format/import). Save-state buttons in Link's SETTINGS (stateInfo/stateSave/stateLoad).
- **0.5 – 0.8** — Bezels. Bottom screen locked to Link (Presentation non-cancelable; B no longer closes it).
  Analog mod removed after it froze on Jack's device. 3D minimap polling raised.
- **0.4** — Named "Xenogears Dual"; launcher themed like the game's menus (Link's frame, font, title art).
- **0.3** — Xenogears-only launcher: disc pick (Disc 1/2), mods, settings, START, skip-launcher option;
  first analog mod test.
- **0.2 and before** — "PSX Link" generic single-APK prototype (pcsx_rearmed + Link WebView).
