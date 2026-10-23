# Xenogears Link: notes for Claude Code

Jack's second-screen companion app for Xenogears (PS1, US disc 1). One page (`app/index.html` plus data files in `app/www/`)
runs in two wrappers:
- an Android WebView app (`android/`);
- a Windows Electron app (`windows/`).

Both read the game's RAM live, either from RetroArch's network commands (UDP 127.0.0.1:55355, `READ_CORE_MEMORY`, 256-byte pages)
or from XenogearsRecomp. Setup on a new machine: `docs/SETUP.md`. RAM addresses and how they were found: `docs/RAM_map.md`.
What changed in each build: `docs/Release notes 2.0.md`.

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
- The start screen says "USE RETROARCH NIGHTLY". Stable works too, but its Network Commands setting doesn't stick on restart for
  Jack, so Nightly stays the advice.
- 34 hint page breaks with no way through doors. Run the gap check in `docs/SETUP.md` to list them.
  - Real missing doors in rooms: 134, 199, 262, 297, 319, 312, Babel 411/408, Shevat 423/449/450/445, 504, 537, 529.
  - The rest are world-map/ship links or cutscene rooms.

## Working with Jack
- Keep messages plain and short. Jack reads on his phone as often as at the desk.
- Name and messages come from the game's own data, never from memory; say when something is a guess.
- When he asks to remove a feature, keep its data and tools in files.
