# Xenogears Link: notes for Claude Code

Jack's second-screen companion app for Xenogears (PS1, US disc 1). One page (`app/index.html` plus data files in `app/www/`)
runs in two wrappers:
- an Android WebView app (`android/`);
- a Windows Electron app (`windows/`).

Both read the game's RAM live, either from RetroArch's network commands (UDP 127.0.0.1:55355, `READ_CORE_MEMORY`, 256-byte pages)
or from XenogearsRecomp. Setup on a new machine: `docs/SETUP.md`. RAM addresses and how they were found: `docs/RAM_map.md`.
What changed in each build: `docs/Release notes 2.0.md`.

## The page is shared with Xenogears Dual
Xenogears Dual (`Desktop\Claude\Xenogears\xenogears-dual`: the game and this page in one Android app) runs these same files. Its
`app/assets/link` is a plain copy of `app/index.html` and `app/www/*`, made by its `app/link_sync.sh` from this repo's last commit.
- Dual's parts are in the page behind feature detection of Dual's bridge, so Link's apps never see them:
  - `DIRECT` (`Native.stateInfo`, save states): no start screen, SAVE STATES and MINIGAMES in SETTINGS, faster map polls, DEV from
    the Konami code, the story jump in DEV, its own tour wording;
  - `RAIL` and `PANEL` (Dual's single-screen layouts: `html.rail`, `html.panelonly`, `railDraw`; `#rail` / `#panel` on the URL
    shows them in a browser);
  - in `map3d.js`, `HOST.room3d` and `HOST.room3dReady` (Dual's first-boot copy of the 3D rooms).
- Don't give Link's Android or Windows bridge a `stateInfo`, `railOn`, `panelOn`, `room3d` or `room3dReady` method.
- Change the page here, never in Dual's copy; anything only Dual should do goes behind those flags. Dual's sync stops if its copy was edited.
- After a page change, check both: this repo's sweep and screenshots, and Dual's page tests (`tests/scripts/link_*_test.py`,
  `maps3d_test.py`; see Dual's CLAUDE.md).

## Builds
- Android: `cd android && XG_KS_PASS=<password> ./build.sh 2.0.0.N`
  - Gives `android/Xenogears Link 2.0.0.N.apk`.
  - Never write the keystore password to a file; Jack types it or keeps it in his own password manager.
- Windows: `windows/build.sh 2.0.0.N`
  - Gives `windows/dist/Xenogears Link 2.0.0.N (folder).zip`, the unpacked app zipped.
  - Hand Jack the folder zip, not the portable exe: Windows Defender flags the exe.
- Versions have four parts and keep rising (latest shipped: 2.0.0.22). Version code = A·1e6 + B·1e4 + C·100 + D (`build.sh` works it out).
- Every build:
  - add an entry to `docs/Release notes 2.0.md`;
  - commit with a clear message and push to `origin main` (github.com/Nihilspire/Xenogears-Link);
  - put the APK and the Windows zip in Jack's Xenogears folder, with a preview image of what changed when it's visible.
- "Move old builds to _to_delete.bat" in Jack's Xenogears folder lists every older version. When adding a version, add the previous
  one to its list and update the "newest one" and "Kept:" lines.

## Testing (before every build)
- The test page feeds a save state's 2 MB RAM to the app in headless Chromium:
  - `bash /home/claude/npc/mkt.sh` rebuilds it;
  - `cd /home/claude/npc && python3 sweep.py <part> 4` runs four parts in parallel over the 228 states in `/home/claude/npc/bins/st`;
  - `python3 /home/claude/scratch/swchk.py` sums up (expect `228 0`).
- Screenshots: `/home/claude/scratch/ui.py <outdir>/ [state]`, which takes the start screen, map and settings.
- Room viewer: `cd tools/room_viewer && node mkdata.js && python3 mk.py` builds `xenogears-room-viewer.html`. Jack's published copy is the
  claude.ai artifact "Xenogears Room Viewer"; he also keeps `Xenogears Room Viewer.html` in his folder.
- Nothing is "working" until Jack sees it in the live game. Mark new things "not yet seen live" in the release notes.

## Data files Jack edits
- **Hints:**
  - `app/www/hints.js` (HNOTE text, HPATH rooms and green spots per story step; a "?" in front means not yet checked in game);
  - `app/www/hsplit.js` (later parts of a hint, started by game switches, e.g. 114 Kislev sewers).
- **Doors, treasure, marks:** `app/www/exits.js`, `treasure.js`, `marks.js`.
- **Importers:**
  - `tools/app/import_exits.js <viewer exit edits.json>`;
  - `tools/app/import_hints.js <viewer hint edits.json>`;
  - `tools/sheets/import_edit_sheet.py <story hints edit sheet.xlsx>`; `tools/sheets/mk_edit_sheet.py` makes the sheet.
- After importing, rebuild the room viewer and refresh its derived data:
  - `node tools/app/exit_check.js` (arrival spots, door pairs);
  - the spot check (`/home/claude/scratch/spotcheck.py`), copying its output to `tools/room_viewer/data/spotcheck.json`.

## Disc and script tools
- `/home/claude/xg/fld` is the field-script toolkit (dialogue, story-step tests, who sets what, actor positions). Start with `hintkit.py`.
- `tools/disc` holds the disc readers.
- They need `XG_DISC=<path to Xenogears disc 1 .bin>`.
- Several scripts still have the cloud workspace's absolute paths (`/home/claude/...`, `/tmp/claude-0/...`); see `docs/SETUP.md`.

## Open items (23 Oct 2026)
- Android "not responding" when used with XenogearsRecomp during the first Lahan Gear fight:
  - 2.0.0.18+ records a freeze report;
  - still waiting on a photo of the "THE APP FROZE LAST TIME" card or a save state.
- Hint 114's sewer part was reordered to the walkthrough order after 2.0.0.22. It's committed and in the room viewer, but not in an APK yet.
- App tour wording tidied (2 Nov: CHAPTER, SETTINGS, STATUS, JOURNAL, and BY ITSELF renamed ON ITS OWN). Committed, not in an APK yet.
- The page shared with Xenogears Dual (8 Nov), which brings two fixes from Dual 0.26: the 3D map's error loop (a disc it can't read
  froze the page) and wrapped map messages. Committed, not in an APK yet (see the release notes' "Next build").
- The start screen says "USE RETROARCH NIGHTLY". Stable works too, but its Network Commands setting doesn't stick on restart for
  Jack, so Nightly stays the advice.
- 34 hint page breaks with no way through doors. Run the gap check in `docs/SETUP.md` to list them.
  - From 25 Oct the room viewer's Check list has them as two lists, worked out live from the doors as edited: "Route: world-map
    ways out with no place" (25 rooms, Lahan among them) and "Route: hint pages with no way through doors" (32: 17 no door,
    9 only through a one-way door, 6 no world-map way out with a place). Add door puts the door where the game lands the party
    coming from that room (ARR). Same rules as Xenogears Dual's `tests/scripts/route_audit.py`; `tools/room_viewer/test_route_lists.py`
    checks the lists headless with a disc.
  - Real missing doors in rooms: 134, 199, 262, 297, 319, 312, Babel 411/408, Shevat 423/449/450/445, 504, 537, 529.
  - The rest are world-map/ship links or cutscene rooms.

## Working with Jack
- Keep messages plain and short. Jack reads on his phone as often as at the desk.
- Name and messages come from the game's own data, never from memory; say when something is a guess.
- When he asks to remove a feature, keep its data and tools in files.
