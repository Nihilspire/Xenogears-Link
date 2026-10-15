# Xenogears-Link
A vibe coded dual screen android application for use in the game Xenogears. Program will link with Retroarch to display relevant data such as HP, Gold, Mini-map and more. Vibe coded but playtested throughly with love.

Xenogears Link features

# Connection

Reads the game live from RetroArch Nightly via Network Commands over on Android or Windows.
The FF button turns RetroArch’s fast-forward on and off.
The screen dims during dialogue and story scenes with a fast forward button always availible.
The top bar shows the chapter, play time and gold, plus WORLD MAP, BATTLE or BATTLER when you’re in one.

#Party

Status:
HP, EP, level, experience to next level and stats for the party, with portraits.
Equip: each pilot’s equipment, plus their Gear’s frame, engine, armor, parts, HP and fuel.
Items: the whole inventory with counts. Tap an item for its description.

# Mini Map

Picture of each room drawn from the game’s own 3D geometry, with the walkable area outline. It turns with the camera or can be set to stay fixed.
Rooms with several floors get a picture per floor that switches as you change floors.Treasure:
Chests and gifts marked; greyed out once obtained in-game.
“x / y found” count and a list of what’s left.
Exits marked with where they lead, and an arrow for the way you came in.
Memory cubes and shops marked.
Enemy list for the rooms with encounters.
3D map with an EYE view, under Experimental, off by default.
EYE view shows the room's people as their own sprites from the disc, standing where they are in the game right now and turning to face the way they do.

# Story hints

A picture of the rooms to visit, in order, with green spots and “you are here”. Can cycle steps via arrows.
Green waypoints can be toggled on and off for those wanting more/less direction.

# Battle

Enemies by name with HP bars, and the party’s HP, EP or Gear fuel.
Turn-order timeline showing who acts next.
Enemy pop-up: EXP, gold and drops, plus element weaknesses, status immunities and status effects.
Deathblows: list with progress toward each one, combo key inputs, AP, and Gear attack level and infinity moves. Can be set to all or just learned ones.
Battle countdown bar for random encounters, in rooms and on the world map.

# Shops

Item and Gear shop stock while you shop, with what you already own highlighted.

# Source layout

- `app/`: the companion page itself (`index.html` and its scripts in `www/`). The same page runs on Android (WebView) and Windows (Electron).
- `android/`: the Java wrapper (WebView, RetroArch UDP link, disc reading) and `build.sh`, which builds the APK without Gradle. Signing needs your own `keystore.jks` beside the script and its password in `XG_KS_PASS`.
- `windows/`: the Electron wrapper and `build.sh` for the portable exe.
- `tools/`: Python scripts that read the game disc (room scripts, maps, sprites, shops, treasure, hints) and generate the data tables in `app/www`.
- `docs/RAM_map.md`: the full RAM map the app reads. `docs/save-editor.html` is the testing save editor, and `docs/Xenogears (USA) Link testing.cht` the RetroArch testing cheats (fast text, no encounters, party and Gear invincibility, fuel, level ups).

No game data is included. The room maps and pictures are built on the device from your own copy of the disc (`discbuild.js`). The game's graphics, font and portraits (`img/`, `spr/`, `world/`, `font.js`) are also left out of the repository and come from the disc with the tools.
