# Xenogears Dual 3DS (proof of concept)

The same pcsx_rearmed core as the Android app, built for the New 3DS: the game on the top screen, a C version of Link on the bottom
screen. Made the same way as Shantae Dual 3DS (`Shantae\shantae-dual\native\ctr`, and its porting guide,
`docs/porting-a-dual-app.md`).

## Running it

Needs **Luma3DS** (for the recompiler; without it the core drops to its interpreter, far too slow) and a New 3DS.

Copy to `sdmc:/3ds/xenogears-dual/`:
- `Xenogears Dual 3DS.3dsx` (run from the Homebrew Launcher), or install `Xenogears Dual 3DS.cia` with FBI
- your disc images: `.cue`/`.bin`, `.chd` or `.pbp`, with "Disc 1" / "Disc 2" in the file names. No game data ships with this.
- `xenogears-link.pak` (about 100 MB): the map pictures and enemy sprites, as raw RGB565. It's made from the app's built assets by
  `make -C native/ctr pak`, and holds game graphics, so it stays on the SD card and out of the `.3dsx`, the `.cia` and git. Without it
  everything still works, but the map has no picture and enemies have no sprites.
- optional: a real BIOS (`scph*.bin`). Otherwise the core's built-in one is used, as in the app's tests.

Sound needs the usual DSP firmware dump at `sdmc:/3ds/dspfirm.cdc`, or it plays silent.

| 3DS | PlayStation |
|---|---|
| A / B / X / Y | Circle / Cross / Triangle / Square |
| L / R / ZL / ZR | L1 / R1 / L2 / R2 |
| Circle Pad / C-stick | left stick / right stick (the analog controls program is on, as in the app) |
| Select + R | R3 (camera reset) |

The bottom screen has six tabs, all reading the game's RAM directly:

- **HINT:** the story hint, one sentence and room a page, with the room's picture and green spots. No guide line, and pages don't turn by
  themselves yet.
- **MAP:** the room's picture, turned with the game's camera. Yellow box = treasure, grey = taken, blue dot = gift, orange ring = missable not
  yet taken, pink square = memory cube, orange dot = shop, green ring = hint spot. Tap an icon for its name and when it's lost, tap
  elsewhere for whole room / close-up, LIST for everything in the room. The world map has its picture, places, hint spots and the party.
- **FIGHT:** comes up by itself in a battle and goes back after. Enemies with sprites, HP and status; party; the acting member's deathblows
  with their buttons; numbers for who acts next. Tap an enemy for rewards, drops, immunities, elements and boss tip, a party member for
  their list, a deathblow for what it takes to learn. The arena mini-game gets its two bars.
- **PARTY:** HP, EP, Gear HP and fuel, chapter, gold, time.
- **BLOWS:** every deathblow for each member with progress, on foot or in the Gear.
- **SYS:** 2 state slots, frame skip 0/1/2, old-3DS speed, disc swap, quit.

`xenogears-3ds.log`, written beside the discs, has the core's start-up messages and, every 5 seconds, the frame rate and how long each
part took. That file is what's needed to judge real speed.

## Build (WSL, devkitPro at /opt/devkitpro)

```
make -C native/ctr                # -> ~/xgtmp/ctr/Xenogears Dual 3DS.3dsx
native/ctr/cia/build_cia.sh       # -> ~/xgtmp/ctr/Xenogears Dual 3DS.cia
native/ctr/test/build_test.sh [script.h]    # the build with scripted input
native/ctr/test/azahar_run.sh APP OUTDIR "w:40 s:a"    # boots it headless in Azahar; prints the game log
```

The core's sources are not changed. The Makefile compiles them with the flags of `platform ctr` in `Makefile.libretro`
(ari64 recompiler, Unai software renderer, sound on core 1, drawing on core 2).
`tools/mk_linkdata.py` turns Link's own data files and `analog.cht` into C tables at build time, so hints stay the same as the app's.

`test/linkhost.c` draws the Link screen on the PC from a RAM dump (`dumpram` in `tests/drive.c`), with taps, for quick looks. To get a battle
for it: warp to room 22 with `devwarp` (W 600, the forest rooms 23-25 have no random battles) and walk until 0x8006FAF0 reads 6.

## Things that bit us

- **The core needs `cfguInit()` first.** It counts CPU cores from the system model. Without the service it counts 1 and silently skips the
  drawing thread.
- **`__ctr_svchax` is ours to set.** It is a weak symbol the frontend must provide; if 0 the core quietly uses the interpreter (8 fps here).
  `main()` sets it when Luma answers `svcGetSystemInfo(0x10000)`, or Azahar `0x20000`.
- **Azahar has no svcCustomBackdoor (svc 0x80)**, which the core uses to flush caches. `utils.S` is built with its functions renamed to
  `hw_*`, and `main.c` calls those on hardware, and Luma's cache SVCs (0x93, 0x94) under Azahar. **So the cache path on hardware has not
  been run here.**
- **Azahar's `svcControlMemory` calls fail** where the core maps RAM to a round address. It falls back to `calloc`, so Azahar lacks that
  small speed-up; a real machine should get it.
- **Azahar can't judge speed.** Its tick counter counts instructions, and time on the other cores doesn't show in these numbers at all.
  Shantae measured 11.3 ms in Azahar against 24.0 ms on a device at old-3DS clocks.
- **Pacing:** a loop only waits for VBlank if it came in under a refresh, so a long frame runs slightly slow rather than dropping to 30.
  Sound is played at rate x 59.83/60, or the DSP runs dry every few seconds.
- **CIA:** the `.rsf` keeps the DSP memory mapping (Shantae's data abort on hardware) and has a 2 MB stack.
  `AffinityMask` is 1 as in Shantae's. If the log shows the drawing thread failing to start on core 2 (`threadCreate: pcsxt 2`) only in
  the CIA, that's the first thing to change.
