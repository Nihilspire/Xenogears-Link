# Xenogears companion — RAM map and asset reference

Last updated 7 Oct 2026.

Source: `Xenogears (USA) (Undub) (v1.01) (RyleFury) (Disc 1)`, executable `SLUS_006.64` (SHA-1 `1e21636bc067bd3873b78be3d72978c8038daca0`).

**How these were found:** static analysis — disassembly of the kernel and overlays, the new-game save image on the disc (file 2595), published cheat codes as anchors, and, since 7 Oct 2026, the public decompilation project `ladysilverberg/xenogears-decomp`, whose symbol names and structure layouts were checked against this disc's code and data before being used here. A few rows are confirmed on device and say so. Confidence is marked per row:

- **A** = confirmed by game code and data agreeing (and usually a cheat code)
- **B** = clear from the new-game data, meaning inferred
- **C** = educated guess, check on device first

Addresses are PS1 addresses. RAM offset = address minus `0x80000000` (e.g. gold = `0x06EF58`).

## Program layout

| Region | What |
|---|---|
| `0x80010000–0x80059800` | Kernel (always loaded) |
| `0x8006D634–0x8006F98C` | Save block (9,048 bytes) — everything persistent lives here |
| `0x8006FAF0+` | Current overlay: field, battle, world map or movie |
| `0x801C5000+` | Menu screen program (loaded beside the field program, which stays in memory) |

## Game mode

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x800592C0` | s32 | `g_CurGameStateOverlayID` in the decomp: the menu overlay loaded on the heap, −1 when none. **Not** the running program (corrected 14 Oct 2026; use `0x8006FAF0`) | A |
| `0x8006FAF0` | u32 | First word of loaded overlay = the running program: 4 field, 5 world map, 6 battle, 7 Battle Arena (overlay file 35; was listed as movie until 14 Oct 2026) | A |
| `0x8006F94E` | u16 | Field map ID (`& 0x7FF`; below 0x400 = field). 730 fields on disc | A |
| `0x80059484` / `0x80059420` / `0x80059418` | u8 each | Clock hours / minutes / seconds, worked out from `0x80059488`. Right after power-on they track it exactly, but after a save is loaded they were seen stale (0:06:44 while the menu showed 3:09:31), so read `0x80059488` instead (emulator, 14 Oct) | B |
| `0x8006EF64` | u16 | Story step (script variable 0). Read 70 in the emulator on Jack's "The Tournament" save, matching its save title | A |

## Party, gold, inventory

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x8006F368` | u8 × 3 | Party slots: character ID 0–10, `0xFF` = empty | A |
| `0x8006EF58` | u32 | Gold | A |
| `0x8006F5C4` | u8 × 150 | Item quantity per inventory slot | A |
| `0x8006F65A` | u8 × 150 | Item ID per inventory slot (index into `items`) | A |
| `0x8006F36C` / `0x8006F3D0` | u8 × 100 each | Weapon inventory, quantity / ID | A |
| `0x8006F434` / `0x8006F4FC` | u8 × 200 each | Accessory inventory, quantity / ID | A |
| `0x8006F6F0` / `0x8006F754` | u8 × 100 each | Gear weapon inventory, quantity / ID (`gear_weapons`) | A |
| `0x8006F7B8` / `0x8006F84E` | u8 × 150 each | Gear parts inventory, quantity / ID (`gear_parts`) | A |
| `0x8006F366` | u16 | Mask named `FrMask` in the game's source; `0xFFFF` at new game | B |
| `0x8006F8E5` | u8 × 3 | Whether each party slot is riding its gear | B |
| `0x8006D634` | 31 × 20 bytes | Names: 11 characters then 20 gears, 10 × u16 each, `0x0F` padded | A |

Character IDs: 0 Fei, 1 Elly, 2 Citan, 3 Bart, 4 Billy, 5 Rico, 6 Emeralda, 7 Chu-Chu, 8 Maria, 9 Citan (sword), 10 Emeralda (adult).

## Character record — `0x8006D8A0 + id × 0xA4`

| Offset | Type | Meaning | Conf. |
|---|---|---|---|
| `+0x3C` | u32 | Experience. Emulator, 14 Oct: Bart killed four Forest Elves (21 EXP each in slot `+0x14C`); `+0x3C` and `+0x40` rose by 84 and `+0x44` / `+0x48` fell by 84, and the menu's "Next LV" showed the new `+0x44` | A |
| `+0x44` | u32 | Experience **still to earn** for the next level (remaining, not a running total; `+0x40` is a second copy of current experience, `+0x48` a copy of this). Confirmed on two late-game saves: characters at the same level have the same `+0x3C` + `+0x44` | A |
| `+0x4C` / `+0x4E` | u16 | HP / max HP | A |
| `+0x50` / `+0x52` | u16 | EP / max EP | A |
| `+0x56` | u8 | Character ID; the battle code uses it to pick the command set (Noah: `battleCommandLoadout`). Equal to the record number in all 22 records of the two test saves | A |
| `+0x58` `+0x59` `+0x5A` `+0x5B` `+0x5C` | u8 | Attack, Defense, Agility, Ether, Ether Defense | B |
| `+0x5E` / `+0x5F` | u8 | Hit / Evade | B |
| `+0x62` | u8 | Level | B |
| `+0x63` | u8 | Second copy of the level (Noah: `m63_Level2`); equal to `+0x62` in all 22 records of the test saves | A |
| `+0x74` `+0x75` `+0x76` | u8 | Three equipment slots (index into `equipment`); Fei starts Martial Wear / Martial Cap / Stamina Ring | A |
| `+0x2C` | u8 | Ether defense granted by equipment | B |
| `+0x6A` … `+0x73` | u8 × 10 | Two 5-byte blocks the game's source marks as equipped weapons; all zero at new game | C |
| `+0x7A` | u16 | **Battle commands switched on**, a bit field (Noah: `m7A_commandEnabledBF`). Not a weapon ID. 0 for most; Elly `0x1001`, Citan `0x1003` (both saves), sword Citan `0x1003` once he has it (save b; 0 in save a); 3 for Citan at new game. Which bit is which command is not worked out | B |
| `+0xA0` | u8 | Gear index this character pilots | A |

Example: Fei's HP is `0x8006D8EC`, matching the published "infinite HP" code.

## Gear record — `0x8006DFAC + gear × 0xA4` (20 gears)

Corrected 7 Oct 2026 against the game's own source layout and the new-game save image on disc (file 2595). Weltall starts with frame 1 (`WELT-01800`, 1800 HP), engine 3 (`G4-1200`, output 4, fuel 1200) and armor 3 (`MS 3`), and its HP, output and fuel fields match those parts exactly.

| Offset | Type | Meaning | Conf. |
|---|---|---|---|
| `+0x02` | u8 | Frame ID (gear frame list, disc file 2594 sub-file 45) | A |
| `+0x03` | u8 | Engine ID (engine list, sub-file 46) | A |
| `+0x08` | u8 | Armor ID (gear armor list, sub-file 44 — **not** the `gear_parts` table) | A |
| `+0x09` … `+0x0B` | u8 × 3 | Accessory slots (`gear_parts`) | A |
| `+0x0C` … `+0x0F` | u8 × 4 | Weapon slots (`gear_weapons`) | A |
| `+0x10` | 3 × 12 bytes | Per-weapon data (ammo and so on; fields not worked out) | C |
| `+0x38` / `+0x3A` | u16 | **Fuel / max fuel** | A |
| `+0x3C` | u8 | Engine output | A |
| `+0x40` / `+0x42` / `+0x44` | u16 | Defense, ether defense and weight added by equipment | B |
| `+0x4D` | u8 | Responsiveness | B |
| `+0x60` / `+0x64` | u32 | HP / max HP | A |
| `+0x68` | u16 | **Weight** (not fuel — the earlier note was wrong) | A |
| `+0x70` / `+0x72` | u16 | Base defense / base ether defense | B |
| `+0x74` | u8 | Attack power | B |
| `+0x98` | u8 | Agility | B |
| `+0x9E` | u8 | Ether amplification | B |
| `+0x02` | u8 | Engine or weapon ID | C |
| `+0x08` | u8 | Armor (index into `gear_parts`) | C |
| `+0x09` `+0x0A` `+0x0B` | u8 | Accessory slots (index into `gear_parts`) | C |

Gear order: 0 Weltall, 1 Weltall-2, 2 Vierge, 3 Heimdal, 4 Brigandier, 5 Renmazuo, 6 Stier, 7 Chu-Chu, 8 Seibzehn, 9 Crescens, 10 Regurus, 11 Fenrir, 12 Andvari, 13 Renmazuo, 14 Stier, 15 Xenogears, 16 Heimdal, 17 BARTHOS, 18 Yggdra.

## Battle (only valid while mode = 2)

Combatant array: `0x800CCCE8 + slot × 0x170`, 11 slots. Slots 0–2 are the party, 3–10 are enemies.

| Offset in slot | Meaning | Conf. |
|---|---|---|
| `+0x000…0x0A3` | Copy of the character record, same layout — live HP at `+0x4C`, max `+0x4E`, EP `+0x50` | A |
| `+0x0A4…0x147` | Copy of the gear record — live gear HP at `+0x104`, max `+0x108`, fuel `+0x10C` | A |
| `+0x07C…0x08F` | five pairs of u16 status words — see "Status words" below | B |
| `+0x15A` | u8, bit `0x80` = fighting in gear | A |

| Address | Meaning | Conf. |
|---|---|---|
| `0x800D2D24 + slot` | Character ID in each party battle slot, `0x7F` = empty | A |
| `0x800D2C88 + slot` | Per-combatant state byte (0 = normal) | B |
| `0x800D2DE4 + slot` | Turn-ready byte: 0 waiting, 1 ready to act, `0xFF` removed from the fight — see "Turn timers". Emulator: 1 exactly while that fighter's command menu is up; an enemy killed goes to `0xFF` | A |
| **`0x800D32A0 + slot × 8`** | **AP (deathblow points) of party slot 0-2**, u8; `+4` = combo points a turn (5 at these levels), `+5`/`+6` two more bytes not worked out (0x10-0x12). Emulator, 14 Oct: three fighters ending their turns with 4, 3 and 2 points unused read 4, 3, 2, as the battle screen's Ap numbers showed; Bart alone read 4 then 8 over two turns. A fixed array: the battle program reads it as `lbu 0x32A0(slot × 8 + 0x800D0000)` | A |
| `0x800C3CFC` | AP of the fighter whose turn it is (or was last), u32; a display copy | B |
| main block `+0x2D4` (pointer at `0x800C3EAC`) | Combo points left in the current turn (5 at the start, minus 1 / 2 / 3 per △ / □ / ✕ attack). Emulator: 5 → 2 → 0 over ✕ then □ | A |

Enemies use the same 0x170-byte block, loaded straight from the encounter files, so enemy HP should be at `+0x4C` on foot and `+0x104` for gear-scale enemies. Enemy names are not in this block; they sit in the encounter files on disc and need a lookup table (not built yet).

The game writes battle HP/EP back to the save block when the fight ends, so during a battle read the battle array, not the save block.

## Confirmed on device (v0.1 test, Oct 2026)

Gold, clock, party slot, HP/EP, level, experience and the five stats all matched the running game (new game, Fei alone). RetroArch link works.

- **Names in a running game are one byte per letter**, zero-terminated, at the same `0x8006D634 + i × 20` slots. The two-byte form only exists in the disc's new-game image. Letters use the same codes; digits are `0x16–0x1F` in the one-byte form.
- **Enemy slots 3–10 are a whole monster bank, not the fight's line-up.** Each encounter data file holds 8 monster stat blocks (0x170 each, at file offset 0x32) and 8 names (section pointed to by the u16 at 0x30; name offsets start 6 bytes in). All 8 are loaded, so slots can hold enemies that are not in the fight.
- `0x800D2DCC + slot` (u8): slot takes part in the fight, non-zero = yes. Every battle loop skips slots where this is 0. Confidence B until checked on device.
- Enemy names: 74 banks on each disc (identical sets). The app identifies the loaded bank by its 8 max-HP values.
- Field map IDs are not useful to show (generic numbers).
- No fixed address for "text box open" was found by static analysis. The app learns it on device by comparing field working memory (`0x800AD000–0x800C5000` and `0x80059000–0x8005A000`) while walking and in dialogue.

## Disc 2

Checked against `Xenogears (USA) (Undub) (v1.01) (RyleFury) (Disc 2)`, executable `SLUS_006.69`. **All addresses in this file are the same on both discs.**

- The two executables differ only in `0x80010004–0x8001807C`, which is the disc's file-location table embedded at the start of the program. Everything from `0x80018080` to the end (268,160 bytes, all code and fixed data) is byte-identical.
- The field, world map, battle, menu and movie overlays are byte-identical, so the battle addresses match too.
- The new-game save image is byte-identical, so the save block layout matches.
- The menu text, menu atlas, gear atlas and system UI files are byte-identical, so the asset pack covers both discs.
- Only the disc file numbers shift: disc 2 has five fewer entries near the start, so file N on disc 1 is file N−5 on disc 2 (e.g. battle overlay 38 → 33, save image 2595 → 2590).

## Assets (in the zip)

| Folder | Contents | Disc source |
|---|---|---|
| `ui/` | Menu atlas pieces: font (128×112), menu labels, cursor, L1/R1, HP bar, card text | file 2593, sub-file 1 (LZSS) |
| `ui_system/` | Bronze window frame (16 palettes) and corner, cursors, compass, gear HUD | files 589, 592 |
| `ui_gear/` | Gear menu atlas and small gear icons | file 2607 |
| `portraits_menu48/` | 48×48 menu portraits, named by character ID | file 2593, sub-file 4 |
| `portraits_small24/` | 24×24 party icons | file 2593, sub-file 1 |
| `portraits_dialog64/` | 91 dialogue portraits, 64×64 | files 492–582 |
| `data/xenogears_tables.json` | Items, equipment, weapons, gear parts, ether and deathblow names, by ID | file 2609 |

Window frame colours: `#100808 #211810 #312918 #423929 #524a31 #635a39 #73634a #8c7352`, highlight `#efefef`, accent `#393963`.

## Disc format notes

- File table at sector 24, 7 bytes per entry (3-byte sector, 4-byte size; negative size = directory). The undub patch stores code in entries 280–389.
- Compression: 4-byte length, then LZSS with flag bytes (LSB first), 12-bit offset and 4-bit length + 3.
- Overlays: files 35 (movie), 36 (field), 37 (world map), 38 (battle), 39 (menu). New-game save image: file 2595.

## Save block layout

The whole save block is one structure starting at `0x8006D634` (the game's source calls it `GameState`, 0x2300 bytes; the block written to a memory card is 9,048 bytes). A pointer to it sits at `0x8005A39C`, and the active party's character IDs are mirrored at `0x80062590` (3 × s32). Offsets inside it:

| Offset | Address | Contents |
|---|---|---|
| `0x0000` | `0x8006D634` | Names: 11 characters then 20 gears, 20 bytes each |
| `0x026C` | `0x8006D8A0` | 11 character records, 0xA4 each |
| `0x0978` | `0x8006DFAC` | 20 gear records, 0xA4 each |
| `0x1924` | `0x8006EF58` | Gold |
| `0x1D32` | `0x8006F366` | `FrMask` |
| `0x1D34` | `0x8006F368` | Party slots (3) |
| `0x1D38` / `0x1D9C` | `0x8006F36C` / `0x8006F3D0` | Weapon inventory, quantity / ID (100) |
| `0x1E00` / `0x1EC8` | `0x8006F434` / `0x8006F4FC` | Accessory inventory, quantity / ID (200) |
| `0x1F90` / `0x2026` | `0x8006F5C4` / `0x8006F65A` | Item inventory, quantity / ID (150) |
| `0x20BC` / `0x2120` | `0x8006F6F0` / `0x8006F754` | Gear weapon inventory (100) |
| `0x2184` / `0x221A` | `0x8006F7B8` / `0x8006F84E` | Gear parts inventory (150) |
| `0x22B1` | `0x8006F8E5` | Gear ride flags (3) |
| `0x231A` | `0x8006F94E` | Field map ID |

Ceilings the game enforces: 99 per item stack, 9,999,999 gold, 3 party members, 6 on the bench.

## Kernel addresses (always loaded)

Verified present in this disc's `SLUS_006.64` by the code that reads them.

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x80018088` | u32 | Current game state (which overlay the main loop wants) | B |
| `0x8004F34C` | s32 | Scene/map number used when loading; the published debug-room code writes 0 here | A |
| `0x80059178` | s32 | Debug menu enabled flag | B |
| `0x80059570` / `0x80059574` | u32 | Controller 1 / 2 buttons held | B |
| `0x800594A4` / `0x800594A8` | u32 | Controller 1 / 2 buttons pressed this frame | B |
| `0x8005948C` / `0x80059490` | u32 | Controller 1 / 2 buttons released | B |
| `0x80059430` / `0x80059438` | s32 | Controller 1 left stick X / Y | C |
| `0x80059444` / `0x8005944C` | s32 | Controller 1 right stick X / Y | C |
| `0x8005A39C` | pointer | Pointer to the save block | B |
| `0x80062590` | s32 × 3 | Active party character IDs (mirror of the save block's party slots) | B |

The controller words are a possible route to a button-press display, or to knowing when the player is holding a direction.

## Field program addresses (added 7 Oct 2026, v0.5)

Taken from the public decompilation project `ladysilverberg/xenogears-decomp` (symbol list for the field overlay) and checked against this disc's field overlay code: the functions sit at the listed addresses and read these globals. Text box flag, player position and field ID confirmed on device (v0.5); facing and camera angle not yet checked. Only valid while the field overlay is loaded (`0x8006FAF0` = 4).

| Address | Type | Meaning |
|---|---|---|
| `0x800AFB0C` | s32 | Number of actors in the room |
| `0x800AFB10` | pointer | Actor list; entries are `0x5C` bytes |
| `0x800B226C` | s32 | Index of the player's actor in that list |
| actor entry `+0x4C` | pointer | That actor's data block |
| data block `+0x20` | 3 × s32 (+pad) | Position x, y, z in 16.16 fixed point (whole units = value >> 16) |
| data block `+0x104` | 3 × s16 | Rotation; `+0x106` is facing, 0–4095 per turn (low 12 bits; bit `0x8000` is set while standing still after loading). Emulator, 14 Oct: walking down / left / up / right on screen gave 3072 / 0 / 1024 / 2048 with the camera at its default angle |
| data block `+0x08` / `+0x10` | u16 × 4 / s16 | Walkmesh triangle IDs / walkmesh ID the actor stands on |
| `0x800AF880` / `0x800AF890` | VECTOR | Camera eye / camera target |
| `0x800ADBF4` | pointer | Trigger zone list for the current room (see below) |
| `0x800AF990` | 0x134 bytes | Scene block: view matrix, camera rotation matrix and angles, scene scale |
| `0x800AFAC4` | s32 | World scale |
| `0x800B2176` | 3 × s16 | Field control: random encounters enabled (0 off, −1 on), an angle, and a controller button mask the scripts set to take buttons away from the player |
| `0x800ADBA4` | s32 | Frame delta time |
| `0x800C3A68` | — | Script memory (story and room flags the field scripts read and write) |
| `0x800AF98C` | s16 | Camera angle used for the 8-way camera direction, 0–4095 per turn. Emulator: L1 / R1 turn it; the save block's camera yaw (`+0x231C`, `0x8006F950`) follows it as 4096 − angle |
| `0x800C2698 + n × 0x498` | 4 text boxes | `+0x410` u16 order (`0xFFFF` = not in use), `+0x40E` s16 visibility (0 = shown), `+0x416` owner actor, `+0x418` talking actor, `+0x42C…` portrait (`shouldRender`, portrait ID) |

"Text box open" = any of the four boxes with order ≠ `0xFFFF` and visibility = 0. This replaces the taught dialogue signals as the main check.

Player position = read pointer at `0x800AFB10`, add index × `0x5C` + `0x4C`, read the pointer there, then read `+0x20`.

## Description text (added v0.5)

File 2594 is a pack of 56 LZSS sub-files. String tables in it (u32 count, u16 offsets, zero-terminated game-code strings), index-aligned with the name tables in file 2609:

| Sub-file | Contents | Entries |
|---|---|---|
| 14 | Item descriptions | 264 |
| 40 | Equipment (accessory) descriptions | 149 |
| 39 | Weapon descriptions | 99 |
| 51 | Gear part descriptions | 104 |
| 50 | Gear weapon descriptions | 99 |
| 44–49 | Gear frame / engine / armor names and descriptions | — |

Battle ether descriptions are in files 3091 (on foot), 3097 (gear) and 3098 (specials), two lines per ether.

Extra text codes: `0x11` +, `0x12` comma, `0x13` -, `0x14` ., `0x15` /, `0x57` !, `0x5A` %, `0x5B` &, `0x5C` ', `0x5D` (, `0x5E` ), `0x60` ?, `0x01` = empty entry.

The overlays (files 35–39) are LZSS-compressed on disc; decompressed field overlay is 260,859 bytes loaded at `0x8006FAF0`.

Field map IDs: the "dokodemo door" list in the RPGClassics Debug Room FAQ numbers rooms 000–729 with locations; confirmed equal to the field ID at `0x8006F94E` (Lahan village reads 1).

## Trigger zones

`0x800ADBF4` points at the current room's trigger zones, 0x18 bytes each: four corner points as (s16 x, s16 y, s16 z). Only the first `y` is used, as a floor height; the four x/z pairs are the corners of a quad, which may be rotated rather than axis-aligned. The game tests whether the player's position is inside the quad and within height of `y0`.

The same list is stored in each room file (block 9), so the zones can be read off the disc without the game running. Across disc 1's 730 rooms there are 765 zones, but 521 rooms have none — so these are not simply "every exit". They look like script-driven areas (Lahan has 12, Fei's house 2, Citan's house 5). Which zone does what is in the room's scripts, which I have not decoded.

## Field program: counts

| Address | Meaning |
|---|---|
| `0x800AFB0C` | Number of actors in the room |
| `0x800B0078` | Pointer to the actor the running script belongs to |
| `0x800AFC7C` | Script instruction budget per frame |

**EYE people (v1.94):** the app reads every actor's entry `+0x4C` / `+0x58` and block `+0x20` / `+0x106` to draw the room's NPCs in the EYE view, taking actor *i* in this list to be script entity *i* (the sprite each one wears comes from running the room's set-up scripts, `npc.js`). Checked off-device only: the list index matching the script entity, and `+0x58` bit `0x20` hiding an actor, are not yet seen on the handheld.

Actor data block fields beyond position (same block as `+0x20` position): `+0x18`/`+0x1A`/`+0x1C` are the actor's width, height and depth, `+0x1E` a solid range, `+0x30` and `+0x40` movement vectors, `+0x50` the surface normal under the actor, `+0x68` the previous position, `+0x74` whether the actor can be interacted with, `+0x76` move speed, `+0x80` the portrait ID used when it talks. Actor entries in the list (0x5C each) hold a transform matrix at `+0x00`, the data pointer at `+0x4C`, rotation at `+0x50` and a status word at `+0x58` (bit `0x20` = invisible).

## Field room files and walkmesh (added v0.8)

- Field ID `f` is disc 1 file `606 + 2 × f` (the room data; the next file is its textures). All 730 are present on disc 1.
- Room file header: decompressed sizes at `0x10C` (9 × u32) and offsets at `0x130` (9 × u32) for: textures, walkmesh, models, sprites, palettes, scripts, battle line-ups (see "Room battle line-ups"), dialogue, triggers. Each block is LZSS.
- Walkmesh block: u32 layer count `n` (1-4); 4 × u32 triangle-data size per layer; u32 offset of the surface table; then `n` pairs of u32 (triangle offset, vertex offset). Triangles are 14 bytes: 3 × u16 vertex index, 3 × u16 neighbour triangle (`0xFFFF` = none), u8 surface type, u8 unused. Vertices are 8 bytes: s16 x, y, z, pad. The surface table is 256 × u32 flags indexed by surface type.
- Layer 0 is the detailed floor; higher layers are large simplified meshes. Surface flags seen: `0` plain floor, `0x800000` blocked areas such as building footprints (inferred from the shapes), `0x400000` and small values = other surfaces (meaning not worked out).
- Walkmesh x/z are in the same units as the player position's whole part (assumed; check on device).
- The app's map files hold layer 0 only: vertices merged on x/z, triangles with a tone (floor / other / blocked) and outline-edge bits.

## Room 3D geometry (added v1.0)

Block 3 of the room file (offset at header `0x138`, size at `0x114`) is the room's models, LZSS compressed. Decompressed: u32 object count, then that many u32 offsets.

Each object has a 0x48-byte header: u16 vertex count at `0x12`, u16 face count at `0x14`, u16 group count at `0x16`, then four u32 offsets at `0x18` (vertices, normals, face indices, primitive data). Vertices are 8 bytes (s16 x, y, z, pad); y is negative upwards.

Face index groups: u16 type, u16 count, then **four u16 vertex indices per face regardless of shape** — a triangle uses the first three and leaves the fourth zero. Type bit `0x08` set means quad (`0x770D`), clear means triangle (`0x7705`). A quad's four corners are in Z order, so it splits into triangles 0-1-2 and 1-3-2, not a fan.

Primitive data starts with 8 bytes: u16 palette id, u16 `0xC400`, u16 texture page id, u16 `0xC800`. Then per face: quads 12 bytes (4-byte tag `0x2D000000`, then 4 u, v pairs), triangles 8 bytes (u, v pairs, no tag).

**Correction (v1.1):** objects are in model space and are placed by the entity table at `0x190` (count at `0x18C`), 16 bytes each: s16 flags, rotation X, Y, Z (4096 per turn), position x, y, z, model ID. An entry with flag bit `0x40` clear places one model (flags seen: `0x000`, `0x010`, `0x280`, `0x290`, `0x8010`); entries with `0x40` set (`0x1E0`, `0x241`) are sprites/actors and carry no model. One model can be placed many times (Lahan's trees). Rotation about Y is x' = x cos + z sin, z' = -x sin + z cos; checked against the walkmesh in rooms 5 (2560), 13 (3072) and 17. Many outdoor rooms use zero rotation, which is why Lahan looked right without this.

Outdoor rooms include a sky dome that wraps the whole room and hides everything from above; the renderer drops any object that encloses the walkable area and is more than 2.5x its height.

**Room textures (solved, v1.19).** The earlier note here said textures were not solved; the missing piece was the layout of the companion file (`607 + 2 x field`). It is a chain of upload blocks, each a 0x800-byte header sector followed by one 0x800-byte sector per chunk:

| Header offset | Type | Meaning |
|---|---|---|
| `0x00` | u16 | `0x1201` = palettes, `0x1200` = texture pixels |
| `0x04` / `0x06` | u16 | Base position in texture memory, x / y (palettes `0, 480` or `0, 481`; textures `320, 0`) |
| `0x08` / `0x0A` | u16 | Offset added to the base, x / y |
| `0x0C` | u16 | Width in 16-bit words |
| `0x0E` | u16 | Rows per full chunk |
| `0x12` (and `0x18`) | u16 | Chunk count |
| `0x1C` | u16 x count | Rows in each chunk (the last is usually short) |

Each chunk sector holds width x rows 16-bit words, copied to texture memory at (base + offset), one chunk under the other. The next block starts after the last chunk. Rebuilding a 1024 x 512 texture memory this way makes the page and palette ids in the models resolve correctly.

Models: every object is `u32 part count` then 0x38-byte part headers (the "0x48 header" above is the count plus one part; all rooms checked use one part). The primitive data is the same stream as the battle models: words with a top byte of `0x80` or more are state (`0xC4` = texture page word, `0xC8` = palette word); a textured triangle is 8 bytes (u2 v2, 2 bytes with the draw command in the top byte, then u0 v0 u1 v1), a textured quad 12 bytes (command word, then four u v pairs), an untextured face one colour word with the command in the top byte. Commands are the console's own: `0x20`/`0x28` flat triangle/quad, `0x25`/`0x2D` textured, bit `0x02` = see-through, with the blend mode in bits 5-6 of the texture page word (0 average, 1 add, 2 subtract, 3 add a quarter). Texture page word: bits 0-3 x / 64, bit 4 y / 256, bits 7-8 depth (0 = 16 colours, 1 = 256 colours). Palette word: bits 0-5 x / 16, bits 6-14 y. Texel 0 is transparent. Every face in the five rooms spot-checked (1, 50, 100, 300, 600) parses with at most 3 bytes of padding left over, and all 711 rooms render.

## Deathblows and skills (added v1.2)

Anchor: the published "all deathblows" code writes `0xFFFF` to `0x8006ECF4 + n × 0x20` and `7` to `0x8006ED0B + n × 0x20` for 11 characters. Checked against the new-game save: Bart (starts with one deathblow) has `0x8000`, Emeralda `0xFE00`, Fei and Citan `0`.

Skill record — `0x8006ECF0 + character × 0x20` (11 records, save block offset `0x16BC`):

| Offset | Type | Meaning | Conf. |
|---|---|---|---|
| `+0x04` | u16 | Learned deathblows, top bit = first deathblow | A |
| `+0x06` | u16 | Another learned-ability mask (Fei `0x8000`, Elly `0xF000` at new game) — probably ethers | C |
| `+0x08`, `+0x0A` | u16 | Further masks, meaning not worked out | C |
| `+0x1B` | u8 | AP per turn (3 at new game; the code sets 7) | B |

Attack points — character record `+0x90`, 7 × u16, in the order T1 T2 T3 T4 S1 S2 X (weak 1-4, strong 1-2, fierce). Emeralda is the only character with non-zero values at new game (230, 180, 90, 40, 150, 80, 195), which matches what players report.

Requirement table — disc file 2594 sub-file 43, one 0x110-byte block per character ID. Each block starts with 13 rows of 7 × u16: the points a deathblow needs in the same T1…X order (`0xFFFF` row = slot not used). Fei's first row is 30, 0, 0, 0, 0, 0, 10 — the "30 weak, 10 fierce" for Raijin that guides quote. The rest of each block (level requirements and so on) is not decoded.

Deathblow names — file 2609, sections 0-10, one per character ID (u32 count, u16 offsets, strings).

The app's percentage is points earned towards the row divided by points needed. Whether the game's own skill screen uses the same formula, and how level gates apply, is unchecked.

## World map (found 8 Oct 2026, from the code; not yet read on device)

Overlay file 37 (signature word 5) is the world map program. Its start-up routine at `0x80073398` loads the player's position from the save block into three words, which the rest of the program then reads about 30 times each.

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| **`0x8009D55C`** | 3 x s32 | **Live position on the world map**: x, height, z in 20.12 fixed point (whole units = value >> 12). Every travel mode's movement routine copies its actor's position (actor `+0x28`…`+0x30`) here each frame (`0x8008AB24` on foot, `0x8008CC5C`, `0x8008ECF4`). Found 10 Oct after the handheld showed the marker frozen. Emulator, 14 Oct: follows the party on foot (z 10852 → 11092 → 11332 walking up) while `0x8009C5AC` stays put | A |
| `0x8009D52C` | u16 | Live heading, copied from the actor's `+0x48` at the same time. Emulator: 2048 walking up the screen, 1024 left, 0 down (4096 a turn) | A |
| `0x8009CEC4` | 32 x 20 bytes | Ring of recent positions (x, height, z, a fourth word, heading), written while moving; index at `0x8009D154` | code |
| `0x8009C5AC` | s32 | **Starting** X on the world map, 20.12 fixed point: where the party is put when the world map starts or a script moves it (`0x80076C3C`). It is copied into the actor once (`0x8008A3E0`) and does not follow movement (confirmed on the handheld) | A |
| `0x8009C5B0` | s32 | Starting height | B |
| `0x8009C5B4` | s32 | Starting Z, same scale as X | B |
| `0x8009C584` | s32 | Heading or angle loaded alongside the position | C |
| `0x8009BE10` | s32 | Travel mode, 1-7 (on foot and the various vehicles); selects where the saved position comes from. 1 on foot (emulator) | B |
| `0x8009D3F4` | pointer | Table of entry points, 8 bytes each: s16 x, s16 location ID, s16 z, s16 — ends with ID -1. Where you appear when leaving a town; usable as a list of world map locations. | B |
| `0x8009D64C` | s32 | World map battle window counter (see "Random battles"); the published "no random encounters on world map" code holds it at `0x10`, which keeps the window from ever restarting | A |
| `0x8006EE54` / `0x8006EE56` / `0x8006EE58` | u16 | Saved world X / Z / heading for modes 1 and 2 (save block). Emulator: updated every frame while walking (same whole units as `0x8009D55C`) | A |
| `0x8006EE66` | u16 | Saved heading for modes 4, 5 and 7 | C |
| `0x8006EE68` | u16 | Flags; bit `0x2000` forces a reload of the saved position | C |
| `0x8006EF8E` … `0x8006EF9E` | nine s16 | Script variables `0x2A`-`0x3A` (see "Script variables"); the world map program reads and writes them, meaning not worked out | C |
| `0x8006F950`, `0x8006F952`, `0x8006F954` | s16 | Set to `0xC00`, `0xFFF`, 1 on first start-up. `F950` is the saved camera angle (see "Save block tail") | B |

The SET panel shows position, heading, mode and the saved pair on its "world" line while on the world map.

## Title logo

Disc file 594 is an 8-bit image sheet (128 × 256) with the title screen pieces. The Xenogears wordmark is three strips: (0,48)-(128,80), (0,80)-(128,112), (0,112)-(32,144), joined left to right into 284 × 32.

## More addresses from published codes, checked against the code (8 Oct 2026)

Each address below comes from a published GameShark code; I confirmed the program actually reads or writes it (count of code references in brackets) and worked out where it sits in structures already mapped.

**Battle slots.** `0x800CCCE8 + slot × 0x170` (slots 0-2 are the party). A slot is a character record followed by a gear record, both in the save-block layouts:

| Address (slot 0) | Offset in slot | Meaning | Conf. |
|---|---|---|---|
| `0x800CCD34` | `+0x4C` | HP (character layout `+0x4C`) [17 references] | A |
| `0x800CCD38` | `+0x50` | EP | A |
| `0x800CCDC4` | `+0xDC` | Gear fuel (gear record starts at `+0xA4`; fuel is gear `+0x38`) | A |
| `0x800CCDEC` | `+0x104` | Gear HP (gear `+0x60`) | A |

So everything in the character and gear tables above can be read for a combatant at slot + offset (character) or slot + `0xA4` + offset (gear).

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x800D32A0 + slot × 8` | u8 | AP for the current turn [11 references] | B |
| `0x800D2C34` | bytes | Gear attack-level state; the "always infinity mode" code writes `04 08` here [19 references] | C |
| `0x800987E0` / `0x800987E2` | u16 | Battle arena (gear duel mini-game): your HP / heat | C |

**Kernel.**

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x80059171` | u8 | Saving allowed (the "save anywhere" code sets 1) | B |
| `0x80059488` | u32 | **Play time in vertical blanks** (60 a second). Emulator, 14 Oct: counts up one per frame; after loading a save it equals the save's play time (memory-card block `0x100`, u32) and the menu's clock is this ÷ 60 | A |

**Skill record.** `+0x06` (u16 at `0x8006ECF6 + n × 0x20`) is the learned-abilities mask — the "all abilities" code writes `0xFFFF` there — so ethers learned are readable the same way as deathblows. Confidence B.

**Menu program.** The "infinite items" code patches an instruction at `0x801DBC32`, so the menu program runs from around `0x801D0000`, outside the range the app normally reads.

## More field-program addresses (from the decompilation project's symbols)

| Address | Meaning | Use |
|---|---|---|
| `0x800ADC04` | Screen fade status | Scene transitions |
| `0x800ADBF8` | Pointer to the current room's script file | — |
| `0x800AF934` | Camera mode | — |
| `0x800AF93C` | Camera movement flags; `0x800AF93E` / `0x800AF960` are the durations of a scripted move of the camera target / eye | A scripted camera move is a likely sign of an in-engine cutscene |
| `0x800AF8F0` – `0x800AF920` | Scripted camera move: target from/to, eye from/to | — |
| `0x800AEA2C` | Four masks used by scripts that depend on party size | — |
| `0x800C268C` | System mode (0 on console) | — |
| `0x800B0054` / `0x800B0058` | Pointers to the controller buffers the field reads | — |

## Script variables (found 8 Oct 2026, from the field program's save routine at `0x800A30FC`)

Field scripts keep their variables in a 0x400-byte bank at `0x800C3A68`; variable N (a byte offset, even for 16-bit values) is at `0x800C3A68 + N`. When the game stores its state, the routine copies the whole bank into the save block at offset `0x1930`. So every script variable has two addresses:

- live, while a room is loaded: `0x800C3A68 + N`
- saved copy, always readable: `0x8006EF64 + N`

This explains the "story counter" at `0x8006EF64`: it is **script variable 0**. The bank ends at `0x8006F364`, right before the joined-characters mask.

Variables the engine itself fills in just before saving (so their meaning is certain):

| Variable | Live address | Saved address | Contents |
|---|---|---|---|
| `0x00` | `0x800C3A68` | `0x8006EF64` | Story progress (inferred from use, not from this routine) |
| `0x06` | `0x800C3A6E` | `0x8006EF6A` | Player facing, 0-7 |
| `0x08` | `0x800C3A70` | `0x8006EF6C` | Camera direction, 0-7 |
| `0x24` | `0x800C3A8C` | `0x8006EF88` | A scene value copied from `0x800AF9FC` |
| `0x3C` | `0x800C3AA4` | `0x8006EFA0` | Current scene / room number (same as `0x8004F34C`) |
| `0x3E`, `0x40`, `0x42` | `0x800C3AA6`… | `0x8006EFA2`… | Party slot 1, 2, 3 character IDs |
| `0x44` | `0x800C3AAC` | `0x8006EFA8` | Copy of the u16 at `0x8005941C` |
| `0x46` | `0x800C3AAE` | `0x8006EFAA` | Copy of the byte at `0x800594D0` |

Everything else in the bank is set by room scripts (story flags, chest flags, counters). Variable `0xE6` (`0x8006F04A`) is referenced directly by the field program five times, so it is engine-level too, meaning unknown.

## Save block tail and party flags

| Address | Save offset | Type | Meaning | Conf. |
|---|---|---|---|---|
| `0x8006F364` | `0x1D30` | u16 | **Characters who have joined**, one bit per character ID. New game = `0x0005` (Fei and Citan). The field program sets bits with `1 << id` (13 references); the world map reads it. | A |
| `0x8006F366` | `0x1D32` | u16 | `FrMask` (`0xFFFF` at new game) | B |
| `0x8006F94E` | `0x231A` | u16 | Room number at the time of saving | A |
| `0x8006F950` | `0x231C` | u16 | Saved camera angle = camera direction × 512 | B |
| `0x8006F954` | `0x2320` | u16 | Copy of script variable 2 | C |
| `0x8006F956` | `0x2322` | u16 | Copy of `0x8004F324` (a scene parameter next to the room number — probably the entry point within the room) | C |
| `0x8006EE60` … `0x8006EE68` | `0x182C`… | five u16 | Written by the field program in pairs; `EE66`/`EE68` are the world map's saved heading and reload flag, so this block is where a room hands the world map its return position | C |

## Ethers and gear skills (name tables in disc file 2609)

Ethers learned are the u16 at skill record `+0x06` (`0x8006ECF6 + character × 0x20`), top bit = first ether — the same scheme as deathblows. Checked against the new-game save: Fei has one bit set and one starting ether; Elly has four.

| Section of file 2609 | Contents | Layout |
|---|---|---|
| 0-10 | Deathblow names | one section per character ID |
| 20 | Ether names on foot | 176 = 11 characters × 16; entry = character × 16 + bit number. Fei: Guided Shot, InnerHealing, Iron Valor, CounterForce, Yang Power, Yin Power, Radiance, Big Bang |
| 48 | Ether names in gear | 304 = 19 × 16, same idea per gear |
| 28-46 | Gear deathblow names | one section per gear ID 0-18, 15 entries: three unused, then nine level-1/2/3 moves and three infinity-mode moves |
| 52 | Gear special options | 76 = 19 gears × 4 |
| 23 | Character weapon names (rods and so on) | index = weapon ID |
| 18 | Menu words (Accept, Cancel, AP, HP…) | — |

Battle descriptions for ethers are in files 3091 / 3097 / 3098 (see "Description text").

## Battle work areas (pointers)

Most of the battle program's state is not at fixed addresses: it allocates blocks at the start of each fight and keeps pointers to them. The pointers are fixed.

| Pointer at | Block size | Used | Notes |
|---|---|---|---|
| `0x800C3EAC` | 0x2F8 | 456 references | Main battle control block |
| `0x800C3EA4` | 0xA2B4 | 357 | Large per-fight data block |
| `0x800D2D28` | 0x10C | 272 | Turn state; holds per-combatant bytes at `+0x7C + slot`, `+0x97`, `+0xB5` |
| `0x800D2DB4` | 0x5DA4 | 162 | Battle menus and on-screen elements |
| `0x800CCB34` | — | 337 | Fixed table just before the combatant slots (`0x800CCCE8`) |

What the individual fields mean is not worked out. This is where AP gauges, turn order, status ailments and battle rewards will be; the battle program never writes gold, so rewards are paid out by a different program after the fight.

## Enemy records and battle rewards (found 8 Oct 2026)

A monster bank file (for example disc file 2620: Jackal, Hobgob, Lucre Bug…) starts with eight u16 offsets, then at `0x32` holds eight enemy records of **0x170 bytes each — the same layout as a battle slot** (character record, then gear record, then 0x28 extra bytes). The bank record is what gets copied into the enemy's slot, so all of this is readable live at `0x800CCCE8 + slot × 0x170 + offset` during a fight.

The extra bytes at slot `+0x148` are the reward block:

| Offset in slot | Type | Meaning | Conf. |
|---|---|---|---|
| `+0x14C` | u32 | Experience for defeating it (Jackal 3, Hobgob 2, big Hobgob 490) | B |
| `+0x150` | u8 | Chance (%) of the first drop | B |
| `+0x151` | u8 | Chance (%) of the second drop | B |
| `+0x152` | u8 | First drop, item ID | A |
| `+0x153` | u8 | Second drop, item ID | A |
| `+0x154`, `+0x155` | u8 | Which inventory each drop belongs to: 0 none, 1 equipment, 2 items, 3 gear weapons, 4 gear parts — the same order as the inventories in the save block. Across all 76 banks on disc 1 only these five values occur. | B |
| `+0x156` | u16 | Gold | A |
| `+0x15A` | u8 | `0x40` for an enemy on foot, `0x80` for a gear-sized enemy (the same bit the party uses for "in gear") | B |

Checks: Hobgob's two drops decode to Hob-Jerky and Hob-Meat, Armor Grub's to Bizfruit, Lucre Bug's to Gold Nugget; Lucre Bug carries 500 G and Nolucre Bug 0; the animals carry 0 G.

Other enemy fields follow the character layout, with one difference in meaning. **`+0x4C` is the enemy's real starting HP and `+0x4E` is only a ceiling**: 30 of the 281 records have the first below the second (Hobgob 15 / 30, gear-sized ones too, e.g. 5000 / 8000). Seen on device: a Hobgob read 15 / 30 at the start of a fight (whether a 16-damage hit then removed it is the open question further down). Show enemy HP against the starting figure, not `+0x4E`.

**Slot order (confirmed on device):** a fight's enemies are copied into slots 3, 4, 5… in formation order — a fight of Jackal, Hobgob, Hobgob fills three consecutive slots — not into the slot matching the record's position in its bank. Each slot is an unchanged copy of the record, reward block included (experience total on screen matched the three enemies' records).

## Per-character growth block (disc file 2594, sub-file 43)

Each character's 0x110-byte block, after the 13 deathblow requirement rows (0xB6 bytes):

| Block offset | Type | Contents | Conf. |
|---|---|---|---|
| `0xB8` | u16 | 950 for Fei, 750 Elly, 880 Citan, 820 Bart, 666 Emeralda — looks like an HP ceiling or growth target | C |
| `0xBA` | u16 | 999 for everyone | C |
| `0xBC` | 7 × (u8, u8) | Seven low/high pairs (Fei: 90-200, 80-175, 42-80, 40-75, 52-75, 55-100, 100-130) — stat growth ranges, order not worked out | C |
| `0xCC` | bytes | `5 10 22`, then `1 2 15`, `3 4 15`, `5 6 15`, `255` — same for every character; probably gear attack-level thresholds | C |
| `0xE0` | 16 × u8 | Ether numbers this character can learn (Fei: 1, 2, 5, 6, 7, 8) | B |
| `0xF0` | 16 × u8 | Level at which each ether is learned (Elly: 1, 1, 1, 1, 20, 20, 20, 20, 55, 55, 55, 55 — four at level 1 matches her four starting ethers) | B |
| `0x100` | 13 × u8 | **Level each deathblow needs** (Fei: 5, 10, 16, 22, 30, 38, 46, 50, 50, 50, 50, 70, 80; 255 = slot unused) | A |

The deathblow levels match the published learn levels for the first seven and for Fei's last two (70 and 80). The four elemental ones read 50 here where guides say 59; guides also say those need a story event.

The monster banks are the 76 even-numbered disc files 2618-2768 whose first u16 is `0x0BB2`. Largest rewards on disc 1: 363,345 experience and 50,000 G.

## Stat and price tables (disc file 2594; found 8 Oct 2026)

These are fixed tables on the disc rather than RAM, but they give the numbers behind every ID the RAM map exposes. Record sizes were found from the data's own repeat length and checked against known items.

| Sub-file | Records | Contents | Fields worked out |
|---|---|---|---|
| 0 | 150 × 16 | Items | `+0x00` u16 who can use it; `+0x02` u16 price; `+0x08` u16 strength — HP items heal strength × 50 (Aquasol 1 → 50, Aquasol S 3 → 150, Aquasol DX 10 → 500); `+0x0B` target/kind flags; `+0x0E` effect number |
| 1 | 100 × 16 | Character weapons | `+0x00` u16 who can equip (Elly's rods = bit 1); `+0x04` u16 price; `+0x0C` u8 attack |
| 2 | 200 × 16 | Equipment | `+0x00` u16 who can equip, one bit per character ID (`0x07FF` = everyone; Mermaid Ring `0x0440` = Emeralda only); `+0x02` u16 price; `+0x08` u8 defense; `+0x0C`/`+0x0D` effect kind and amount for accessories; `+0x0E` slot (1 body, 2 head, 0 accessory) |
| 16 | 180 × 24 | Gear frames | `+0x00` u32 which gears; `+0x04` u16 HP; `+0x08` u16 weight; `+0x0A` u16 price. WELT-01800 = 1800 HP, weight 3500, matching Weltall's record. |
| 17 | 150 × 20 | Gear armor | `+0x04` u16 price; `+0x06` u16 weight; `+0x08` u16 armor value (10, 20, 30… matching "Ar value" in the descriptions) |
| 18 | 150 × 16 | Gear engines | `+0x04` / `+0x06` u16 fuel / max fuel; `+0x0A` u16 price; `+0x0C` u8 probably output (matches for G2 and G4, not for G3 — unsure) |
| 19 | 150 × 28 | Gear parts | `+0x00` u32 which gears; `+0x04` u16 price; `+0x06` u16 weight; `+0x0D` u8 defense; `+0x14` u8 ether defense |
| 42 | 100 × 20 | Gear weapons | `+0x00` u16 which gears; `+0x08` u16 price; `+0x0E` u8 attack |
| 43 | 11 × 0x110 | Per-character growth (see above) | — |

Prices are what the fields look like (Martial Wear 50, Fencing Wear 80, Metal Jacket 550, Mermaid Ring 10,000); I have not compared them with a shop on screen.

## More kernel variables (named by the decompilation project; not individually checked)

| Address | Meaning |
|---|---|
| `0x800625A0` | Pointer to the menu's working data (`g_Menu`) — a likely "main menu is open" signal |
| `0x800592D0` | Kernel menu running flag |
| `0x8005A1FC` | Random number seed |
| `0x80059388` | Controller type |
| `0x8006258C` | Currently loaded sound bank |
| `0x8006FABC` | Party member skins (just before the overlay signature word) |
| `0x80059374` / `0x80059378` | Controller 1 / 2 buttons on the previous frame |
| `0x8004F374` | Party data still streaming from disc |

## Attack tables (disc file 2594, sub-files 3-13 and 22-38; found 8 Oct 2026)

Sub-files 3-13 are one table per character ID; sub-files 22-38 are the same thing per gear. Each is a list of 40-byte records (38 per character, 41 per gear), one per attack the combatant can perform:

| Records | What they are |
|---|---|
| 0-6 | The seven basic attacks in the order T1 T2 T3 T4 S1 S2 X — the same order as the attack-point counters at character record `+0x90`. Fei's strengths: 5, 5, 6, 7, 10, 12, 20. |
| 7-13 | The seven 4-6 AP deathblows (Fei: strength 26 rising to 50) |
| 14-19 | The 7 AP deathblows (Fei: 76, 78, 80, 82, then 120 and 250) |
| 22 onward | Ethers |

Fields in a record:

| Offset | Type | Meaning | Conf. |
|---|---|---|---|
| `+0x02` | u8 | Animation / move number | C |
| `+0x11` | u8 | Strength | B |
| `+0x15` | u8 | Accuracy (60 for weak attacks, 80 for elemental deathblows) | C |
| `+0x1A` | u8 | Kind: 0 basic attack, 2 deathblow, 1 ether | B |
| `+0x20` | u8 | Category flag: `0x80` basic, `0x40` deathblow, `0x20` elemental deathblow, `0x10` ether | B |
| `+0x22` | u8 | Element bits | B |

**No deathblow carries a status effect (16 Oct 2026).** Across all 143 on-foot deathblow records (11 characters) and 181 gear deathblow and infinity records (17 gears), the fields the ethers use for their effects are all zero: `+0x13` effect type, `+0x14` chance (ethers: 100, 80, 30, 20), `+0x16` duration, `+0x1B`-`+0x1F` (status bits and masks), `+0x21`, `+0x23`, `+0x25`, `+0x26`. Deathblows are damage plus an element and nothing else. The deathblow fields that do vary follow the character, not the move: `+0x0A` (0/1/32/33/64/65; 1 = elemental, 32 Billy, 64 Rico and some Emeralda/Citan moves), `+0x0B` (4, 8, 12, 140), `+0x10` (0, 128 Elly/Bart/sword Citan, 144 Billy) look like weapon or range type; `+0x17` is 4, 5, 5, 6, 6, 6, 6 for the seven basic deathblows and 1 for elemental ones (meaning not worked out). Gear records: `+0x24` rises 10, 20, 30 … (fuel cost, by the look of it) and `+0x27` is the attack level 1-3.

**Element bits**, read off Fei's four elemental deathblows and his last two: `0x08` wind (Fukei), `0x04` earth (Chikei), `0x02` fire (Kakei), `0x01` water (Suikei), `0x20` on Kokei and `0x10` on Yamikei (light and dark, going by the names). Elly's ethers repeat the same four low bits in the same order.

## Scripted scenes: the player lock (corrected 8 Oct 2026; was "Random encounters in rooms")

Room scripts bracket a scripted scene with two commands that set a group of flags together. Field script opcode `0xFE54` (handler `0x80093B10`) locks the player; `0xFE53` (`0x80093AC8`) frees them.

| Address | Free | Locked (in a scene) | What the code does with it |
|---|---|---|---|
| `0x800B21D0` (u8) | 0 | 1 | **Menu lock**: the triangle-button check at `0x80078A5C` only opens the menu when this is 0 |
| `0x800B21D1` (u8) | 0 | 1 | Compass hidden (drawing skipped at `0x80074360`) |
| `0x800B2176` (s16) | 0 | −1 | The decompilation project calls this "random encounters enabled", but it is −1 in the locked state; code at `0x80081534` only runs when it is 0 |
| `0x800AF9D8` (scene flags, u32) | bits `0xC000` clear | bits `0xC000` set | `0x8000` stops L1 / R1 turning the camera (`0x8007286C`) |

Single-purpose commands: `0xFE50` / `0xFE4F` set and clear the menu lock alone (`0x80093BD4` / `0x80093BB0`); `0x77` / `0x76` set and clear camera flag `0x8000`; `0x15` / `0x14` set `0x800B2176` to −1 / 0. All four values are zeroed when the field program starts.

Across the 730 rooms on disc 1 the lock command appears about 2,500 times in 624 rooms and the free command about 2,000 times in 387, lock nearly always first: a room locks while it sets up and frees the player afterwards, and about 240 rooms never free the player at all (scene-only rooms).

The app (v1.17) treats `0x800B21D0 == 1` held for 0.6 s as "in a scene". Not yet seen on the handheld.

Other things found on the way: `0x800B217A` is the button mask scripts can set (`0xD5`); `0x800ADB00` is a second mask the collision code sets to `0x0FFF` (directions off) for the player; `0x800ADC18` counts down frames after a room loads (input is zeroed and angles snap while it is non-zero); `0x800AFE9C` is the field's held-buttons word after both masks.

## How the battle program changes HP (from its code, 8 Oct 2026)

Read from the damage/heal routine at `0x8008570C` in the battle overlay. Slot = `0x800CCCE8 + n × 0x170`.

| What | Code | Meaning |
|---|---|---|
| Damage on foot | `0x8008571C` | HP (`+0x4C`, signed) minus damage; if the result is above 0 it is stored |
| Defeat | `0x80085754` | otherwise HP is set to 0, the slot's bit is added to a "defeated in this action" mask, and **bit `0x8000` of the status word at `+0x7C` is set** — so `+0x7C & 0x8000` = defeated |
| Damage in gear | `0x800857A4` | same, on gear HP (`+0x104`, u32) |
| Healing | `0x800858B4` | HP plus the amount, capped at `+0x4E` — so `+0x4E` is the healing ceiling, which is why an enemy can start below it |
| Full restore | `0x80085AC4` | sets HP to `+0x4E` |
| Removal | `0x8007257C` | a combatant with `+0x7C & 0x8000` has HP forced to 0 and `0x800D2DE4 + slot` set to `0xFF` |

Removal is deferred (enemy sweep `0x8007262C`): an enemy with `+0x7C & 0xC000` is only removed when its slot bit (`u16[0x800C3448 + slot × 2]`) is clear in the mask at `0x800C3608`; while that bit is set it stays in the "still present" mask `0x800D39DC`. The bit is cleared at `0x800B8A84` (end of an animation step). The fight is won when `0x800D39DC & 0x7F8` is 0 (`0x800C48EA` = 1). The routine skips any target that already has `+0x7C & 0x8000`.

Revive path: action-queue entries are 8 bytes from `0x800D2E5C` (kind `+0`, sub-type `+4`, target mask `+6`), dispatched by kind through the 17-entry table at `0x8006FB38` (`0x800793F0`). Kind 5 (`0x80078D48`) copies the target mask to `0x800D39E0`; `0x80072324` then gives every enemy in that mask a full restore (HP = `+0x4E`, KO word cleared). Nothing found yet that queues it for ordinary enemies.

Which HP an enemy uses (on foot `+0x4C` or gear `+0x104`) is chosen by the byte at `0x800C3EB8 + slot × 0x1C`, not by which maximum is non-zero.

Hobgob HP, cross-checked: the disc records give start 15 / max 30 (Lahan mountain path, exp 2) and start 15 / max 30 (Blackmoon Forest, exp 13); the Xeno Series Wiki lists the same "Initial HP 15, Maximum HP 30". The second number exists so its HP-absorbing attack has room to heal.

Open question from the handheld: a Hobgob whose slot went 15 → 0 after a combo showing 16 total damage was reported to keep fighting. Neither this code nor the published stats allow that, so it is not explained. v1.10 adds a fight log (every change to HP, the KO word `+0x7C` and the removal byte `0x800D2DE4 + slot`, per slot, with a time) to capture exactly what the game writes the next time it happens. Not resolved.

## Battle data block (third battle pass, 8 Oct 2026 — all from the code, nothing here read on device yet)

The pointer at `0x800C34B0` (255 references) is the base of one big block whose first bytes are the combatant slots, so it equals `0x800CCCE8` and every offset from it is a fixed address. The addresses already in this map (`0x800D2C88`, `0x800D2D24`…) are all inside it.

| Address | Offset in block | Meaning |
|---|---|---|
| `0x800CCCE8` | `+0x0000` | 11 combatant slots × 0x170 |
| `0x800CDD40 + party slot × 0x5F0` | `+0x1058` | The acting character's attack table in RAM: 38 records × 40 bytes, same layout as disc file 2594 sub-files 3-13 |
| `0x800CEF10 + party slot × 0x668` | `+0x2228` | The same for the gear: 41 × 40 bytes |
| `0x800D02C0` | `+0x35D8` | Enemy attack records, 40 bytes each |
| `0x800D2C94` | `+0x5FAC` | u16 mask of slots (bit per slot) |
| `0x800D2CA9` | `+0x5FC1` | **Slot of the fighter whose action is being worked out** |
| `0x800D2CAA` | `+0x5FC2` | **Index of the attack being used** (into that fighter's attack table) |

While an action is worked out the code keeps pointers: `0x800C3E00` attacker's slot, `0x800D2D6C` attacker's gear record (slot `+0xA4`), `0x800C3DFC` the attack record, `0x800C3E34` target's slot, `0x800D2DC8` target's gear record.

Slot bit masks: `u16[0x800C3448 + slot × 2]` is the bit for a slot; `0x800C3468` is a second copy used for the inverse.

## Turn timers (the hidden turn order)

Each fighter has a countdown. The tick routine at `0x80071720` runs while the byte at `0x800D3298` is non-zero.

| Address | Type | Meaning |
|---|---|---|
| `0x800D2E06 + slot × 2` | u16 | **Countdown to this fighter's next turn** |
| `0x800D2DF0 + slot × 2` | u16 | The value the countdown was last started from (so progress = 1 − countdown ÷ this) |
| `0x800D2DE4 + slot` | u8 | 0 counting, 1 ready, `0xFF` removed |
| `0x800D2DD8 + n` | u8 × 11 | Order list of slots, used to pick between fighters that are ready at once |
| `0x800D2DD7` | u8 | Position reached in that list |
| `0x800D2DC0` | u8 | Slot + 1 of a fighter forced to act next (0 = none) |
| `0x800D2E1C + slot × 2` | u16 | Alternates 0/1 each tick for a slowed fighter |
| `0x800C4922` | u8 | Turn slot, 0-based: 0-2 party, 3+ enemies. Written by the turn routine at `0x80071BF8`. This is what the app reads (v1.18). Emulator: changed to each fighter as its ready byte went to 1 |
| main block `+0x2D3` (pointer at `0x800C3EAC`) | u8 | Slot + 1 of the fighter whose turn is starting; the turn routine takes one off as it begins, so during the turn it is not reliable. Do not use |

Each tick, for every fighter in the fight that is not ready: the countdown drops by 1, or by 2 with the speed-up status; a slowed fighter only counts every other tick; a stopped or sleeping fighter does not count. At zero the ready byte becomes 1. After acting (`0x800718BC`) the countdown is restarted from the wait formula at `0x80098AF8`:

`wait = 165 − 9 × agility`, then minus a random −4…+3. For a party member the attack just used takes its speed cost (attack record `+0x27`) off agility first; a gear uses the gear's agility (slot `+0x13C`). `9 × agility` above 165 is treated as 160. Examples: agility 3 (Hobgob) about 138 ticks, agility 8 (Jackal) about 93, agility 10 about 75.

So the next few turns can be predicted by sorting fighters by countdown ÷ step.

Checked in the emulator, 14 Oct (Fei, Citan and Bart against Forest Elves): every countdown dropped by one per vertical blank while `0x800D3298` was 1 and froze while it was 0 (during actions and menus); a fighter reaching 0 got ready byte 1; after acting, its restart value at `0x800D2DF0` was rewritten (an elf 57 → 61) and the countdown began again from it. A dead enemy's countdown stays where it was.

## Status words (slot `+0x7C…+0x8F`; gear copy at `+0x120…`)

Ten u16, five pairs. The enemy script reader numbers them 2-11 (see field tables below). An accessory's effect is a (pair number, mask) written into the second word of a pair, which is how the bits get their names: equipment record `+0x09` = pair number, `+0x0A` = u16 mask.

| Pair | Words | First word | Second word |
|---|---|---|---|
| 1 | `+0x7C` / `+0x7E` | Physical ailments now | Physical ailments blocked |
| 2 | `+0x80` / `+0x82` | Mental ailments now | Mental ailments blocked |
| 3 | `+0x84` / `+0x86` | Support effects, timed | Support effects, permanent (the two are OR-ed) |
| 4 | `+0x88` / `+0x8A` | Attack/defense changes, timed | permanent (OR-ed) |
| 5 | `+0x8C` / `+0x8E` | Elements, timed | Elements, permanent (OR-ed) |

Bits with a known meaning:

| Word | Bit | Meaning | From |
|---|---|---|---|
| `+0x7C` | `0x8000` | Defeated | damage routine |
| `+0x7C` | `0x4000` | Also counted as out of the fight | sweep (`& 0xC000`) |
| `+0x7C` | `0x2000` | Timed stop: countdown byte at slot `+0x15C`, cleared when it reaches 0 | tick routine |
| `+0x7C` | `0x1000` | Slow (turn timer at half speed) | tick routine |
| `+0x7C` | `0x0800` | Poison | Poison Guard blocks `0x0800` |
| `+0x7C` | `0x0080` | Turn timer does not run | tick routine |
| `+0x7C` | `0x0002`, `0x0001` | Cannot be chosen / cannot act (tests `& 0xC002`, `& 0xC001`) | targeting helpers |
| `+0x7E` | `0x3F7C` | All "physical" ailments (Body Guard) | accessory table |
| `+0x80` | `0x2000` | Confusion | Cool Shades blocks `0x2000` |
| `+0x80` | `0x1000` | Sleep (turn timer does not run) | Sleep Guard + tick routine |
| `+0x80` | `0x0800` | Forget | Brain Guard |
| `+0x82` | `0xFFFE` | All "mental" ailments (Mind Guard) | accessory table |
| `+0x84/86` | `0x8000` | Speed up: turn timer counts double (Speed Shoes) | accessory + tick routine |
| `+0x84/86` | `0x4000` | Defense up (Muscle Belt) | accessory table |
| `+0x84/86` | `0x0400` | Attack rises as HP falls (Power Crisis) | accessory table |
| `+0x84/86` | `0x0080` | HP restoring doubled (Life Stone) | accessory table |
| `+0x84/86` | `0x0040` | Defense up (Guardian Ring) | accessory table |
| `+0x84/86` | `0x0020` | Evasion up (Evasion Ring); also tested by the targeting helpers | accessory table |
| `+0x88/8A` | `0x2000` | Ether Doubler | accessory table |
| `+0x88/8A` | `0x0200` | Blocks EP-absorbing attacks (Ether Guard) | accessory table |
| `+0x88/8A` | `0x0008`, `0x0002` | Attacker: attack +20% / +10%. As the target: defense −20% / −10% | damage code `0x80094F8C` |
| `+0x88/8A` | `0x0004`, `0x0001` | Attacker: attack −20% / −10%. As the target: defense +20% / +10% | damage code |
| `+0x8C/8E` | `0x0F00` | Elements defended against (same bit order as attack elements, shifted up 8) | `0x800965F8` |
| `+0x8C/8E` | `0xF000` | Element added to the fighter's own attacks | `0x80096528` |
| `+0x8C/8E` | `0x0008` | Absorbs a defended element as HP (Ether Reversa) | accessory table |
| `+0x8C/8E` | `0x0004` | Doubles elemental defense (Ether Veiler) | accessory table |
| `+0x8C/8E` | `0x0002` | Elemental defense also blocks ether weapons (Ether Maxer) | accessory table |

**The game's own names (10 Oct, v1.43).** The battle program turns an effect (kind, mask) into a message number, stores it at **`0x800D2CAF`** (battle block `+0x5FC7`) and shows the text from disc file 2614 sub-file 37 (62 strings). The two routines that do it are explicit switch tables, so they name the bits:

On foot (`0x8009B684`, jump table `0x80070478`; kind 0 = `+0x7C`, 2 = `+0x80`, 5 = support, 7 = power, 9 = elements):

| Word | Mask | Message |
|---|---|---|
| `+0x7C` | `0x2000` / `0x1000` / `0x0800` / `0x0400` / `0x0200` | Stop / Slow / Poison / ACC DOWN / Atk DOWN |
| `+0x7C` | `0x0001` | "Block PHY effects" (Igissol) |
| `+0x80` | `0x2000` / `0x1000` / `0x0800` / `0x0400` | Confusion / Sleep / Can't use Eth Ability / Eth effect DOWN |
| `+0x80` | `0x0020` | "Bart taunts enemy" |
| `+0x80` | `0x0001` | "Block ETH effects" (Aegissol) |
| support (`+0x84` / `+0x86`) | `0x8000` / `0x4000` / `0x2000` / `0x1000` / `0x0800` | Speed UP / Def UP / Atk UP / ACC UP / EV UP (`0x1800` together: "ACC/EV UP") |
| power (`+0x88` / `+0x8A`) | `0x8000` / `0x4000` / `0x1000` | Eth effect UP / Eth Def UP / Counter UP |
| power | `0x0008` or `0x0002` | "Atk UP/Def DOWN" |
| power | `0x0004` or `0x0001` | "Def UP/Atk DOWN" |
| elements (`+0x8C` / `+0x8E`) | `0x8000` / `0x4000` / `0x2000` / `0x1000` | Add Wind / Earth / Fire / Water to Atk |
| elements | `0x0400` | **"Block Earth/Weak point Wind"** |
| elements | `0x0800` | **"Block Wind/Weak point Earth"** |
| elements | `0x0100` | **"Block Water/Weak point Fire"** |
| elements | `0x0200` | **"Block Fire/Weak point Water"** |

The four element messages are the game stating the rule found above in its own words: a defence bit blocks one element and makes its opposite a weak point.

In a gear (`0x8009E868`; the words are in the gear copy, kind 0 = slot `+0x120`, kind 1 = `+0x124`, kind 3 = `+0x128` elements with the same messages as on foot):

| Word | Mask | Message |
|---|---|---|
| `+0x120` | `0x0400` / `0x0200` / `0x0100` / `0x0080` | Stop / EP DOWN / Stop Eth Engine / Fuel leak |
| `+0x120` | `0x0040` / `0x0020` / `0x0010` / `0x0004` | Def DOWN / Slow / ACC/EV DOWN / PWR loss |
| `+0x124` | `0x1000` / `0x0800` / `0x0400` | PWR UP / ACC UP / EV UP |
| `+0x124` | `0x0040` / `0x0020` | Eth effect UP / Eth Def UP |
| `+0x124` | `0x000A` / `0x0005` | Atk UP/Def DOWN / Def UP/Atk DOWN |

Other messages in the list: 49 Play Dead, 50 "You're the last one", 51 No effect, 52 Counterattack!, 53-55 Stop PHY / MNT / EQP effects (the Rose items), 57 Can't add Elem, 58 Stop all effects (effect kind `0x6E`, which zeroes `+0x84`…`+0x8E` by flag, `0x80095934`), 59-60 no ammo, 61 "Charge fuel at 10x".

**Countdowns.** `0x800995A0` picks a countdown for an effect it applies: Stop 0, Slow 1, Sleep 2, Can't use Eth 3, Speed UP 4, Def UP 5, Eth effect UP 9, Eth Def UP 10, Counter UP 11 (bytes from slot `+0x15C`; the units are not worked out).

An earlier note called `+0x7C` bit `0x0080` the taunt; the code puts the taunt at `+0x80` bit `0x0020`. The app shows these live from v1.43.

## Elements and enemy weaknesses

The element check is at `0x80096500`. Bit order for an attack's element (attack record `+0x22`): `0x01` water, `0x02` fire, `0x04` earth, `0x08` wind, `0x10` dark, `0x20` light.

| Field | Meaning |
|---|---|
| slot `+0x38` low 6 bits | **Elements this fighter is weak to**: a matching attack is ×1.5 |
| slot `+0x38` bit `0x40` | Very weak: ×1.8 instead |
| slot `+0x8E` bits `0x0F00` | Elements defended against; with `0x0008` they are absorbed |
| attacker `+0x8C/8E` bits `0xF000` | If the attack has no element it takes this one; if it matches, another +0.2 |

Checked against the Xeno Series Wiki: Rain Frog `+0x38 = 0x08`, `+0x8C = 0x0108` reads as weak to wind, absorbs water, and the wiki lists exactly that; Mullet reads weak to and absorbing water, as listed. Wels reads `0x62`: very weak to fire and light. Fuel Tank is weak to bit `0x01` (water) and defends the other three.

**The rings question, settled (10 Oct).** The element names above are right, and the check compares the same bit on both sides (`0x80096590`-`0x80096690`; the attack's element is attack record `+0x22` unchanged). Three attack-side tables agree on the bit order (Fei's elemental deathblows, Elly's twelve ethers in Anemo / Terra / Thermo / Aqua order, Bart's Wind / Earth / Fire / Water Mode at `0x8000`, `0x4000`, `0x2000`, `0x1000`, and the element rods). Three player-side defence tables agree with each other but are swapped in pairs: the rings (Wind `0x0400`, Earth `0x0800`, Fire `0x0100`, Water `0x0200`), the four Stars, and Billy's shields (attack records 27-30, effect word 9, the same four masks). The game's own text for the shields explains it: the Xeno Series Wiki lists them as Wind Shield "Blocks Earth Attack", Earth Shield "Blocks Wind Attack", Fire Shield "Blocks Water Attack", Water Shield "Blocks Fire Attack". So a "Fire" defence bit means fire-aligned: it blocks water and takes more from fire. The rings carry exactly those masks, so by the code the **Fire Ring blocks water ethers and takes +30% from fire**, whatever its one-line description says; likewise for the other three. The Stars' text ("Fire UP/Water DOWN") reads correctly as damage taken. Not tried in the game.

**The second half of the check** (`0x800966C0`): whatever the target defends, an attack of the *opposite* element gets +0.3: attack water against a fire defender (`0x0200`), fire against water (`0x0100`), earth against wind (`0x0800`), wind against earth (`0x0400`). The reduction for a defended element (-0.3, another -0.3 with flag `0x0004`, absorbed with `0x0008`) applies only when the attack record has flag `0x0100` at `+0x0A` (ethers) or the target has flag `0x0002` (Ether Maxer). A gear-sized target is checked through its gear copy (`+0x128` / `+0x12A`) instead of `+0x8C` / `+0x8E`; the weak byte `+0x38` is used for both. A multiplier that would fall to 0 or less becomes 0.1.

Enemies on disc 1 with any of this set (29 names): Rain Frog and Acid Frog (weak wind, absorb water), Mullet (absorbs water), Pecking Duck and Lil'Allemange (absorb fire), Wels and Neo Wels (badly weak to fire and light), Carrier and Pedestal (weak fire), Rhino (weak earth), Medusoid (weak wind), Grahf, Death Scythe and Etone (badly weak to wind), Fuel Tank (weak water, absorbs the other three), Hammer and Bot (weak earth, absorb the rest), Sword Seraph and Heal Seraph, and nine that absorb all four (Hammerhead, Alkanshel, Forbidden, Tears, Gimmick and their Neo forms, Sufal Mass, Urobolus). The app shows this live per enemy from v1.42.

Enemy immunities read straight from the record: `+0x7E = 0x0800` (most human enemies) is poison-proof; `+0x82 = 0x1000` sleep-proof; `0xFFFF` in both (Wels, Phobia, Abandon, Orphan) is immune to everything.

**Monster bank file layout, completed (10 Oct).** Header: 25 u16; the first eight are the offsets of the eight enemies' behaviour scripts, the last is the offset of a string table. Then the eight 0x170-byte records at `0x32`, the scripts (4-byte instructions; blocks end with `FD FF FF FF`, a script with `FF FF FF FF`), and the string table (u32 count, usually 63, u16 offsets, game-code strings): entries 0-8 are enemy names, the rest the bank's special attack names. **Shared attack templates:** disc file 2614 (the battle program's own archive, 38 sub-files) sub-file 3 holds 98 attack records of 40 bytes in the party's layout: plain hits of several strengths, the four elemental attacks (13-16), the four element shields (18-21, effect word 9), and one record per status (for example 23 Sleep, 24 Confusion, 47 Can't use Eth, 48 Speed UP, 46 Slow). Sub-files 4-14 and 16-34 are the party and gear attack tables again, 37 is the status message list. Which templates an enemy uses is decided by its script, which is not decoded.

## Accessory effect table (disc file 2594 sub-file 2, 16-byte records)

| Offset | Meaning |
|---|---|
| `+0x09` | Effect kind (applied by the menu program at `0x801E376C`, jump table `0x801C5204`: 1 ORs the mask into character record `+0x7E`, 2 `+0x82`, 3 `+0x86`, 4 `+0x8A`, 7 `+0x8E`, 5 `+0x32`, 8 and 9 add to `+0x30`, 10 adds to `+0xA1`): 1-4 and 7 are status pairs 1-4 and 5; 5 = passive flags (Economether `0x4000`, Hercules Ring `0x2000`, Trader Card `0x0800`, Holy Pendant `0x0040`, the dolls); 8 = max HP up (`+0x0A` = 2 for 10%, 5 for 25%); 10 = deathblow learning rate |
| `+0x0A` | u16 mask for that kind |
| `+0x0C` | Stat bonus amount |
| `+0x0D` | Which stats get it: `0x80` attack, `0x40` defense, `0x20` agility, `0x10` ether, `0x08` ether defense, `0x04` hit, `0x02` evade |

## Applying an action's results

Results wait in a queue of 0x48-byte records at `0x800C3FE8 + n × 0x48` (32 entries; the count is main block `+0x2DA`). `0x80085618` applies record n to every slot:

| Offset in record | Meaning |
|---|---|
| `+0x00 + slot × 2` | s16 amount for that slot |
| `+0x18 + slot` | What to do with it: 0, 5, 7, 8 HP damage; 2 HP restore; 1, 9 EP loss; 3 EP restore; 10 fuel loss; 11 fuel restore; 4, 6 nothing |
| `+0x3A` | u16 action code |

A slot whose HP changed gets main block `+0x2EB + slot` set to 1. So the last damage dealt to each fighter is readable.

## Per-fighter table at `0x800C3EB4 + slot × 0x1C`

| Offset | Meaning |
|---|---|
| `+0x00`, `+0x01` | Row / position index on the battlefield |
| `+0x03` | Non-zero = cannot be targeted or act |
| `+0x04` | Non-zero = HP is the gear's (`+0x104`), not the body's (`+0x4C`) |
| `+0x0A`, `+0x0C`, `+0x0E` | u16 screen position (used by the drawing code) |

## Field numbers used by enemy scripts

Enemy behaviour scripts read and write fighter fields by number through two tables (`0x80079ED8` bytes, `0x8007A280` words). The numbering confirms which fields the game treats as stats:

- Bytes 0-23: `+0x04`, `+0x56`, gear `+0x3C`, gear `+0x3F`, `+0x58` attack, `+0x59` defense, `+0x5A` agility, `+0x2D`, `+0x5D`, `+0x5B` ether, `+0x5C` ether defense, `+0x5E` hit, `+0x5F` evade, `+0x60`, `+0x61`, `+0x64`-`+0x67`, `+0x13C` gear agility, `+0xB6`, `+0x140`-`+0x142`.
- Words 0-23: `+0x4E` max HP, `+0x4C` HP, the ten status words `+0x7C`…`+0x8E`, gear `+0x110`, `+0x114`, `+0x116`, gear status words `+0x120`…`+0x12A`, `+0x34`, `+0x36`, `+0x38` weaknesses.

Enemy stats in a record therefore sit exactly where a character's do (checked: mountain-path Hobgob bytes give attack 10, defense 10, agility 3, ether 5, hit 10, evade 1, as the wiki lists).

## Enemy battle graphics (disc files 2619-2769, odd numbers; decoded 8 Oct 2026)

Each monster bank (even file, stats) is followed by its graphics pack (odd file). Pack header: u32 count, u32, then one 12-byte entry per enemy record, **in the same order as the records**: u32 A, u32 B, u32 C.

- `C & 0xFFFFFF`: 0 = 2D sprite (enemies on foot), 1 = 3D model (gear-sized enemies). `C >> 24` = colour variant.
- A = offset of the sprite definition, B = offset of its texture block. A value smaller than the header is a reference: a small A means "same as entry A"; a small B means "use entry B's textures" (recolours and repeats).

Sprite definition = archive (u32 count, u32 offsets) of three blocks:

| Block | Contents |
|---|---|
| 0 | Animations: u16 count, u16 offsets, a 56-byte table, then per animation `u16 flags, u16 offset to script, u16 offset to data` (offsets relative to their own position). Script opcode `0xBE nn` shows frame nn − 1; the first one in animation 0 is the idle stance. |
| 1 | Frames: u8 count (high bits of the u16 are flags), u16 offsets. A frame = u8 tile count (bit `0x80`: coordinates are s16 instead of s8), 3 bytes, u16 tile offsets, then one placement per tile. Before a placement there may be marker bytes: `0xC0-0xDF` (no operand) and `0xE0-0xFF` (two operand bytes — attachment points). Placement = flags, [one extra byte if flags & `0x80`], x, y relative to the feet. Flags low nibble = palette number; `0x10` / `0x20` flip. Tiles are listed front first. Tile = 5 bytes: sheet selector (`>> 1` = sheet number), u, v, width, height. |
| 2 | Palettes: u16 palettes per variant, u16 variants − 1, then 16-colour palettes (15-bit, colour 0 clear) — variant × per-variant + palette number. |

Texture block = archive of sheets: u16 width in 16-bit words (so × 4 pixels), u16 height, then 4 bits per pixel, low nibble first.

Checked by rendering all 85 distinct sprites; 84 come out clean (the exception is an unnamed four-block entry in Ramsus's bank). 4,109 of 4,279 frames parse to the exact length.

Gear-sized enemies are jointed 3D models; see the next section.

The tools are in `xenogears_sprite_py.txt`.

## Gear-sized enemy models (pack entries with type 1; decoded 8 Oct 2026)

For a type 1 entry, A points at the animation block and B at the model block.

**Block A** = archive of two: [0] an archive whose first entry is the list of skeletal animations (27 for a Gigafoot) and whose other entries are move scripts; [1] sound data (`seds`).
Animation 0 is always the base pose: a 0x18-byte header (u16 bone count first) followed by 12 bytes per bone — s16 rotation x, y, z (4096 = full turn) and s16 translation x, y, z, relative to the parent bone. The other animations are keyframe tracks and are not decoded.

**Block B** = archive of four:

| Sub-block | Contents |
|---|---|
| 0 | Textures: an archive of images, each with a 16-byte header (u32 flags, u16 VRAM x, y, u16 offset x, y, u16 width in 16-bit words, u16 height) placed at VRAM (x + offset x, y + offset y). The first is the palette strip (128 colours at 0, 496); the rest are 4-bit images that tile one 256 × 256 texture page. |
| 1 | Meshes: u32 part count, then a 0x38-byte header per part (`+0x0E` u16 vertices, faces, face groups; `+0x14` u32 offsets of vertices, normals, faces, primitive stream), then the data. Vertex = 3 × s16 + pad. A face group = u8 type, u8, u16 count, then count × four u16 vertex indices. |
| 2 | Skeleton: one (s16 mesh part or −1, s16 parent bone) pair per bone, ended by −2, −2. The same part can hang off several bones (both feet share one mesh). |
| 3 | Small header (unknown) |

Face group type bits: `1` textured, `2` lit (the part then has normals), `8` quad. The primitive stream runs alongside the faces in order: a word whose top byte is `0x80` or more is a status word (`0xC4` = texture page, `0xC8` = palette); otherwise it is one face's record — a textured triangle is 8 bytes (UV of the third vertex with the GPU command in the top bytes, then the UVs of the first two), a textured quad 12 bytes (command word, then four UVs), an untextured face one colour word. Quads split 0-1-2, 1-3-2.

A bone's matrix is its parent's × translate × rotate X × rotate Y × rotate Z. With that, all 113 distinct gear models on disc 1 parse with every stream consumed exactly, and render recognisably (Weltall, Vierge, the Seraphs…). Colour variants of a model (the entry's top byte) are not applied.

## World map terrain and the map picture (decoded 8 Oct 2026; nothing here read on device yet)

The disc has 17 world map sets, one directory each (files 3963 + 11 × n … ), chosen by story progress. In a set: `+1` LZSS archive of scripts and tables, `+2` LZSS archive of six 256 × 256 8-bit terrain texture pages (TIM, identical in every set), `+3` LZSS archive of small TIMs (clouds, effects, and the 128 × 128 grey in-game minimap as entry 6), `+9` and `+10` two 524,288-byte terrain grids.

**Terrain grid** = 256 chunks of 2048 bytes (one CD sector each), 16 × 16, row = z. A chunk covers 2048 world units and holds four blocks of 9 × 9 cells (x half in bit 0 of the block number, z half in bit 1; the ninth row and column repeat the neighbour), 4 bytes a cell, then a 16 × 16 array of u16 zone values, then padding. So the world is 256 × 256 tiles of 128 units: **world X and Z run 0-32767**, not 0-65535 as first noted.

| Cell byte | Meaning |
|---|---|
| 0 | Height |
| 1 | Low nibble = texture page (0, 1, 2 → pages 0-2; 11, 12, 13 → pages 3-5); bit `0x80` = sloped cell (tested at `0x8009379C`) |
| 2 | Tile within the page: 16 × 16-pixel tiles, 16 to a row |
| 3 | `>> 2` = terrain type 0-14 (5 = sea); `0x80094028` returns it for a position |

Lookup routine `0x80093660(x, z)`: chunk = (z >> 23) × stride (`0x8009D160`) + (x >> 23) on the raw 20.12 values; pointer to the loaded chunk from the table at **`0x8009C184` + chunk × 4**; cell = block × 324 + ((z & 0x3FF) >> 7) × 36 + ((x & 0x3FF) >> 7) × 4.

Sets: 0-7 and 14 are the normal world (set 0 differs from 1 only at Lahan; the others differ in a few tiles), 8, 15 and 16 are the changed late-game world, 9-13 are a different map altogether. Each set's entry-point table (first table of `+1` entry 0: u16 x, s16 location number, u16 z, s16) lists where towns put you; location numbers are world-map numbers, not room numbers.

The app's picture is this grid drawn top-down with its own tiles at 4 pixels a tile (1024 × 1024), so a position maps on directly: pixel = (X >> 12) / 32, x right, z down. The tools are in `xenogears_world_py.txt`.

## Skill record, more fields (`0x8006ECF0 + character × 0x20`; from the battle code, 8 Oct 2026)

| Offset | Type | Meaning |
|---|---|---|
| `+0x04` | u16 | On-foot deathblows learned (top bit first) |
| `+0x06` | u16 | Ethers learned |
| `+0x08` | u16 | **Gear deathblows unlocked**, top bit first, bit = entry in the gear's name table: `0x1000` `0x0800` `0x0400` level 1, `0x0200` `0x0100` `0x0080` level 2, `0x0040` `0x0020` `0x0010` level 3, `0x0008` `0x0004` infinity mode. Tested as `& 0x1C00`, `& 0x0380`, `& 0x0070` at `0x800983D8`. |
| `+0x0A` | u16 | Probably gear ethers / options unlocked (read next to `+0x06`) |
| `+0x1B` | u8 | AP |
| `+0x1E` | u16 | Unknown, read and written by the battle program |


## Random battles (decoded 8 Oct 2026 from the room and world-map programs; confirmed in the emulator 14 Oct)

Emulator, 14 Oct: Blackmoon Forest room 23 had W 600, N 1, one timer at 96; walking took the timer down one per game frame (one per two vertical blanks) and the fight started about 64 blanks after it reached 0, with line-up 11 in `0x80059508`. On the world map (on foot) W was 384, N 1 and the timer counted the same way. Rooms 130 and 147 (Bledavik waterways) had W 0.

Rooms and the world map use the same scheme. There is a **window** of W frames of movement with N battles in it. When the window counter reaches 0 it is reset to W and each of the N timers is given a different random frame inside the window. On every frame in which the player is moving, the counter and every live timer drop by one; a timer reaching 0 starts a battle. Nothing is rolled per step, so the smallest live timer is exactly the number of frames of movement left before the next battle.

| | Room program | World map program |
|---|---|---|
| Tick routine | `0x80079288` (called from the player-control routine at `0x8009F68C` while a direction is held) | `0x8007528C` (called from the three movement routines) |
| Refill routine | `0x8008E718` | inside the tick routine |
| Window counter (s32) | `0x800B2294` | `0x8009D64C` |
| Window length W (s32) | `0x800B2298` (0 = no random battles in this room) | `0x8009BE40` (`0x180`, or `0x300` when bit `0x4000` of `0x8006EE68` is set) |
| Battles per window N (s32) | `0x800B229C` (up to 32) | `0x8009BCC4` (1 at start-up) |
| Timers (u16 each) | `0x800B22A0` x 32; `0xFFFF` = not in use or already spent | `0x8009C854` x 16; a spent timer keeps counting down past 0 |
| Other gates | not while the player lock `0x800B2176` is -1 | "battles allowed" `0x8009D554` must be non-zero; no battle if the area's weights are all 0 |

Room: W and N are set by a script command (handler `0x8008E85C`). When a timer fires, the room picks one of its 16 line-ups by weight and stores the index in `0x80059508`; the battle program then copies that 0x20-byte record from `0x800658DC + index x 0x20`.

World map: when a timer fires, routine `0x80075E7C` finds the terrain zone under the player (`0x80094028`), picks a story bracket by comparing script variable 0 with the u16 thresholds at `0x8009B578`, and reads 16 weights from the zone's table (pointer array `0x8009D73C[zone]`, at `+0x200 + bracket x 0x10`). All weights 0 = safe area. Otherwise it picks a line-up by weight, stores the index in `0x80059508` and copies the zone's 0x200 bytes of line-ups to `0x800658DC`.

## Room battle line-ups (room file block 7; in memory at `0x800658DC`)

Block 7 of every room file (offset at header `0x148`, listed as "unknown" before) is 0x210 bytes: 16 line-up records of 0x20 bytes, then 16 one-byte weights (in memory at `0x80065ADC`). A weight of 0 means the line-up is never picked at random; scripted fights name their line-up directly.

| Record offset | Meaning | Conf. |
|---|---|---|
| `+0x00` | Monster bank: disc file `2618 + 2 x value` | A (Blackmoon Forest rooms 22-23 give Jackal/Hobgob; Lahan's line-up 0 gives four Musha Mk100, as seen on the handheld) |
| `+0x01` | Flags (`0x40`, `0xA3`... not worked out) | C |
| `+0x02`, `+0x03` | Probably the battle background and music (same value across a whole area) | C |
| `+0x04` - `+0x06` | Three bytes, one per party member (`0x80` seen in gear fights) | C |
| `+0x08` - `+0x0F` | Up to eight enemies: `0xFF` = none, low 7 bits = record number in the bank, bit `0x80` = gear-sized | B |
| `+0x10` - `+0x17`, `+0x18` - `+0x1F` | One byte per enemy each: flags and what looks like a position or group number | C |

The app's enemy table is indexed by bank file with two files skipped: table index = bank - 1 if bank > 52, - 1 more if bank > 68 (banks 52 and 68 are not in the table).

## Room scripts (room file block 6; decoded 9 Oct 2026 for the treasure tracker)

Layout: 0x80 bytes of header, u32 actor count at `0x80`, then 32 u16 routine offsets per actor at `0x84` (routine 0 = set-up; pickups happen in routine 1 or 2, which run when the actor is touched or spoken to - which is which is not confirmed), then the bytecode; offsets are relative to the start of the bytecode. Actor 0 is the room itself.

Instructions are one opcode byte plus fixed arguments; opcode `0xFE` is a prefix for a second table (handler tables at `0x800AE2A0` and `0x800AE6A0`). Lengths were taken from each handler's own "advance the script pointer by N" code and, for a dozen handlers with more than one path, fitted to the data; with that table 77,303 of 78,095 routines on disc 1 decode to exactly the start of the next routine. The table is in `xenogears_script_py.txt`. A u16 argument with bit `0x8000` set is a literal (low 15 bits); otherwise it is a variable number. Variable numbers are byte offsets into the script bank at `0x800C3A68`; numbers of `0x400` and up are scratch variables that are not saved.

| Opcode | Length | Meaning |
|---|---|---|
| `00` | 1 | end of routine |
| `01 addr` | 3 | jump |
| `02 a b flags addr` | 8 | compare and jump to `addr` when the test fails. `flags` high nibble: `0x40` = b is a literal, `0x80` = a is, `0xC0` both; low nibble: 0 equal, 1 not equal, ... 6 = `a AND b` non-zero |
| `05` / `06` / `0D` | 3 / 5 / 1 | call / call / return |
| `19 x z flags` | 6 | put the actor at x, z (`flags 0xC0` = both literal) |
| `34 item var` | 5 | number of `item` held into `var` |
| `35 var value flags` | 6 | set a variable (`flags 0x40` = literal value) |
| `36 var` / `37 var` | 3 | set a variable to 1 / 0 |
| `3A var n flags` / `3B` | 6 | set / clear bit n of a variable |
| `8B item addr` | 5 | jump to `addr` if the item is not held |
| `8C item` | 3 | **give an item** (up to 99) |
| `8D item` | 3 | take an item away |
| `8E` / `8F amount` / `90 amount` | 7 / 3 / 3 | gold: check / **add** / take |
| `F7 w n` | 5 | set the random-battle window and battles per window (see "Random battles") |
| `FB flag addr` | 5 | jump to `addr` if the flag is **not** set; flag = variable x 16 + bit |
| `FE 0A flag` / `FE 0B flag` | 4 | set / clear a flag (same numbering) |
| `FE 53` / `FE 54` | 2 | free / lock the player (see "Scripted scenes") |

Item numbers are 16-bit: high byte = inventory (0 items, 1 weapons, 2 equipment, 3 gear weapons, 4 gear parts; the handlers index the five inventories at save offsets `0x1F90`, `0x1D38`, `0x1E00`, `0x20BC`, `0x2184`), low byte = id.

**Chests.** A chest is a stock actor driven by six scratch variables that the room's set-up routine fills in: kind, x, z, two more, the item (call it V), and "already opened" at V + 2. The set-up routine tests the chest's flag (`FB`, or `02` with test 6) and sets V + 2 when it is set; the chest's routine 2 gives the item with `8C V` and calls a room routine that sets the flag. Other pickups name the item directly (`8C` with a literal) and set a flag with `3A` or `FE 0A` in the same routine.

Flags used by chests and pickups sit in script variables `0x82`-`0x2CE` (for example Blackmoon Forest: variable `0x98` bits 0-3; Stalactite Cave: `0xCA` bits 0-1; Lahan gifts: `0x2C0` and `0x2C8`). Live address = `0x800C3A68` + variable; the saved copy is at `0x8006EF64` + variable.

## Room sprites and shared field graphics (9 Oct 2026)

- Room file block 4 (offset at header `0x13C`) is the room's sprites: u32 count, that many u32 offsets (no end offset), each entry an archive of three parts (animations, frames, palettes) in the same format as the battle sprites. Block 5 (`0x140`, listed as "palettes" before) is their pixel sheets: u32 count, offsets, each an archive of sheets (u16 width in words, u16 height, 4-bit pixels). Script command `0B n` gives the actor room sprite `n`.
- Disc file 589 is eight TIM images shared by every room: 0 compass ring, 1 pointer and markers, 2 the N/E/S/W strip, 3 a corner piece, 4 text-box frame pieces, 5 the effect sheet (smoke, lightning, star, sparkle, heart, rings; three palettes), 6-7 red arrows.
- Treasure pickups use a placeholder sprite (one 4 x 4 frame) and no model; no chest picture has been found.


## Memory-card save layout (from two DexDrive saves, 9 Oct 2026)

A `.gme` file is a 3,904-byte DexDrive header followed by the raw 128 KB card. Xenogears uses one 8 KB block (`BASLUS-00664…`): 0x80-byte `SC` header (title in Shift-JIS: `XENOGEARS/No.01` + chapter title), 0x80 icon, a 0x24-byte summary at 0x100 (load-screen levels and so on, not decoded), then the game data at block offset **0x124**.

**Checksum (found 14 Oct 2026):** the block's last byte (offset `0x1FFF`) is the sum of bytes `0x100`–`0x1FFE` (summary plus game data), low 8 bits. It matched all three saves on hand (Jack's RetroArch card and both DexDrive saves) and no other simple sum or XOR did. Change anything from `0x100` on without fixing it and the game reports the save as corrupted (Jack, 14 Oct, with a card from the save editor). The title and icon (before `0x100`) are not covered. Found from the saves, not yet traced in the game's code.

**Where a loaded save puts you (found 14 Oct 2026, tested in an emulator):** not `+0x2320`. When a save is loaded, the load menu sets script variable `0x46` to 2 and copies script variable **`0x54`** (save block `+0x1984`, card offset `0x1164` from 0x124) into `+0x2320` (Noah's menu code, then checked: a save whose `+0x2320` was 1 or 0 still arrived with `+0x2320` = 2, its variable `0x54`). The field program then places the player with entry record [var 2] of the room's **entrance table**: when the room's script code (block 6, after the 0x84 header and actors × 0x40 routine table) starts with `0xFF`, 7-byte records follow: s16 x, s16 z, u8 walkmesh, u8 direction (0xFF = keep camera direction), u8 rotation. The table ends where the first routine starts, so a room has (first routine offset − 1) / 7 entrances (1 to about 10 in most rooms; 29 scene rooms have none). An index past the table reads code bytes as a position: the player lands far outside the room (room 124 with index 2: x −17220), nothing is drawn and the game hangs, or crashes on some emulators. A save point's own position is usually the last entry (room 147: entry 2 = the save point).

Emulator test setup (14 Oct 2026): pcsx_rearmed libretro core built from GitHub (HLE BIOS) driven by a small Python libretro front end (`/home/claude/emu/run/lr.py`, `load.py` boots and loads card slot 1, `dbg.py` prints the player actor). Use the interpreter (`pcsx_rearmed_drc` = disabled): with the recompiler a bad save made the emulator itself crash.

The data is the in-memory save block (`0x8006D634`, 0x2358 bytes) with one change: **each of the 20 gear records is cut from 0xA4 to 0x3C bytes**, so the card form is 0x820 bytes shorter and everything after the gears sits 0x820 lower.

| Card offset (from 0x124) | In memory | What |
|---|---|---|
| `0x0000` | `0x0000` | Names (two bytes per letter here, zero padded) |
| `0x026C` | `0x026C` | 11 character records x 0xA4, unchanged |
| `0x0978` | `0x0978` | 20 gear records x **0x3C** (memory: x 0xA4) |
| `0x0E28`–`0x1B38` | `0x1648`–`0x2358` | Everything else, unchanged (skills `0x16BC`, gold `0x1924`, script variables `0x1930`, party `0x1D34`, items `0x1F90` / `0x2026`, room `0x231A`) |

Short gear record: bytes `0x00`–`0x2B` are the first 0x2C bytes of the memory record (frame +2, engine +3, armor +8, accessories +9..+11); `+0x2C` u32 current HP (memory `+0x60`); `+0x34` u32 current fuel (memory `+0x38`); `+0x38` four bytes not decoded. Maximum HP and fuel are not stored: they come from the frame and the engine (checked: in both saves every gear's HP equals the number in its frame's name and fuel the engine's, for all 19 gears). `saves/mk.js` does the conversion.

**Story step and chapter titles.** Script variable 0 (`0x8006EF64`) is the story step. The save title's second half is entry [step] of a table of 354 Shift-JIS strings, 32 bytes each, on the disc (first entry "Lahan Village" at raw image offset `0x2199F0D8`; e.g. 0-7 Lahan Village, 169-174 Babel Tower, 298-309 Merkava Calls, 340-353 First and Last). Both saves match (169 and 350). These are chapter names, not places: the Babel Tower save was made aboard the Yggdrasil.

**Treasure flags on real data.** Applying `treasure.js` to the saved script variables gives 43 of 257 taken at story step 169, with none in Babel Tower or any later area, and 137 of 257 at step 350 with the earlier areas unchanged. No flag reads "taken" for a place the story has not reached.

**Text code 0x59 is `#`** (Seibzehn's frames, "#17-18000" and so on).


## Save block, second pass (9 Oct 2026, from the two late-game saves plus the code that touches each field)

How each line was established is in the last column: **saves** = the value in both saves (and the new-game image) fits; **code** = read off the routine named.

### Memory-card summary (block offset `0x100`, 0x24 bytes, before the game data)

| Offset | Type | Meaning | How |
|---|---|---|---|
| `0x100` | u32 | Play time in frames (60 a second): 5,321,113 = 24 h 38 m; 10,971,448 = 50 h 47 m | saves (levels 45 and 73) |
| `0x104` | 3 x u16 | Party members' HP | saves |
| `0x10A` | 3 x u16 | Party members' max HP | saves |
| `0x110` / `0x113` | 3 x u8 each | Party EP / max EP | saves |
| `0x116` / `0x119` | 3 x u8 each | Party levels, twice | saves |
| `0x11C` | 3 x u8 | Party character IDs | saves |

The play time is not inside the save block itself: it is the first u32 of the card block's summary (block offset `0x100`, in vertical blanks; 659,788 = 3:03:16 on Jack's save), loaded into `0x80059488`.

### Character record additions

| Offset | Type | Meaning | How |
|---|---|---|---|
| `+0x40` | u32 | Second copy of experience | saves |
| `+0x44` / `+0x48` | u32 | Experience still needed for the next level (two copies) | saves |
| `+0x68` / `+0x69` | u8 | Two fixed per-character numbers that add up to 10 (Elly 3/7, Citan 5/5, Bart 6/4, Billy 8/2, Emeralda 2/8; Fei 0/0). Not identified | saves |
| `+0x6A` | u8 | **Equipped weapon** (weapon table ID) for characters who carry one: Elly's rod, Bart's whip, sword Citan's sword. 0 for bare-handed fighters | saves |
| `+0x6A`..`+0x6D` | 4 x u8 | Billy: his guns (two B&J revolvers / Ether Pistols and a shotgun) | saves |
| `+0x6F`..`+0x72` | 4 x u8 | Billy: the ammunition loaded in each gun (weapon table IDs 50-72) | saves |
| `+0x77` | u8 | Fixed per-character value (Fei 26, Rico 43, Chu-Chu 12). Not identified | saves |

### Gear record additions

| Offset | Type | Meaning | How |
|---|---|---|---|
| `+0x04`..`+0x07` | 4 x u8 | **Ammunition loaded** for each weapon slot (gear weapon table ID, 50 and up; 0 = weapon needs none) | code: battle `0x8009E7D8`-`0x8009E85C` reads `+4` and `+7` and uses them to index the rounds table |
| `+0x0C`..`+0x0F` | 4 x u8 | Weapons fitted (gear weapon table ID): Vierge's rod, Brigandier's whip, Fenrir's sword, Renmazuo's guns | saves |
| `+0x5C`..`+0x5F` | 4 x u8 | Small per-gear counters that grow through the game (Vierge 1 -> 2 -> 4). Not identified | saves |
| `+0x74` / `+0x75` | u8 | Two fixed per-gear values (Weltall 10/5, Vierge 7/3, Seibzehn 12/10) | saves |

Memory-card short gear record (0x3C bytes), complete: `+0x00`-`+0x27` = memory `+0x00`-`+0x27`; `+0x28` = memory `+0x5C` (4 bytes); `+0x2C` = HP (memory `+0x60`); `+0x30` = 0; `+0x34` = fuel (memory `+0x38`); `+0x39`, `+0x3A` = memory `+0x74`, `+0x75`. Checked byte for byte against the new-game image for the first 0x28 bytes.

### Rounds left for gear ammunition

`0x8006F8EA + ID` (save block `0x22B6 + ID`), one byte per gear weapon ID, 100 when full. Firing takes one off and it stops at 0 (battle `0x8009E7F0`-`0x8009E808`); the battle program refuses the shot when it reads 0 (`0x8008043C`). Final save: G-M10A Ammo 33, G-M686A Ammo 93, G-GG060 Ammo 86. IDs 0 and 1 are not rounds: those two bytes are the flag word below.

### Flag words

| Address | Block | Type | Meaning | How |
|---|---|---|---|---|
| `0x8006F364` | `0x1D30` | u16 | Characters who have joined (already listed). Values: new game `0x0005`; Babel Tower `0x083F` (Fei, Elly, Citan, Bart, Billy, Rico + bit 11); final save `0x0BF9` (Elly and the first Citan gone; Emeralda, Chu-Chu, Maria and sword Citan in). Bit 11 is set in both saves and is not a character | saves; script commands B9/BA/BB, FE18, FE1A, FEC6 write it |
| `0x8006F366` | `0x1D32` | u16 | `FrMask`: one bit per character, set by script command FE3A and cleared by FE3B (`0x8008CED0` / `0x8008CE64`). `0xFFFF` at new game, `0xF7FF` in both saves | code |
| | | | What it is for (10 Oct): the party screen offers only characters whose bit is set in both this word and the joined mask (`joined & FrMask & 0x7FF`, `0x801C5600`). So it is **who is available right now** | code |
| `0x8006F8EA` | `0x22B6` | u16 | Progress flags: `0x8000` from the start; `0x4000` set by script command FED1; `0x2000` / `0x1000` set by FED0 when it hands over gear 9 / gear 10 (`0x80087798`, `0x800877C0`). Final save `0xE000` | code |
| `0x8006F94C` | `0x2318` | u16 | One bit per character, set or cleared by script command FE9F (`0x800883D4`). Babel Tower `0x0001` (Fei), final save `0x0081` (Fei, Chu-Chu). **Locked party members**: the party screen refuses to swap a character whose bit is set, in or out (`0x801CABC0`, `0x801CAC00` in the party screen program) | code |
| `0x8006F8E5` | `0x22B1` | 3 x u8 | Gear ride flags, one per party slot: 0/0/0 aboard the Yggdrasil, 1/1/1 in Merkava | saves |

### World map block (`0x8006EE54`, save block `0x1820`), raw values

All u16, written by the world map program. Meanings other than the first pair are read off the two saves only.

| Block | Babel Tower save | Final save | Reading |
|---|---|---|---|
| `0x1820`, `0x1822` | 3585, 24562 | 9142, 12315 | Party position x, z (world units >> 12): what the app's world marker uses when a save is loaded |
| `0x1824`..`0x182A` | 2048, 2048, 0, 3584 | 957, 957, 957, 957 | Headings (4096 a turn) |
| `0x182C`, `0x1830` | 4288, 25169 | 9142, 12315 | A second position: differs from the party's on the Babel Tower save, equal on the final save, so most likely where the ship is parked |
| `0x182E`, `0x1832` | -65, 3072 | -151, 957 | Its height and heading |
| `0x1844`, `0x1846` | 3456, 29312 | 21865, 21723 | A third position (not identified) |
| `0x184C`..`0x1852` | 31840, 10455, 31840, 28887 | 8080, 17121, 8080, 2785 | Two more x, z pairs (not identified) |

### Inventories, checked

The four other inventories (weapons `0x1D38`/`0x1D9C`, equipment `0x1E00`/`0x1EC8`, gear weapons `0x20BC`/`0x2120`, gear parts `0x2184`/`0x221A`) decode to sensible lists on both saves with the app's name tables (final save: 28 weapon kinds, 42 equipment, 24 gear weapons, 48 gear parts). The app reads none of them yet.

### Text codes

`0x57` is `!` and `0x5B` is `&` (as well as `0x59` = `#`). Names that had been dropped for containing them: items 39 "Stop!", 40 "Sleep!", 77 "H&S Badge"; weapons 31-32 "B&J M10 Gun", "B&J M686 Gun" and 50-55 "B&JM10A Ammo" … "B&JM686XAmmo". Fixed in `tables.js` for v1.32.

### Script commands identified in passing

FE3A / FE3B set / clear a `FrMask` bit; FE9F sets or clears a bit of `0x8006F94C`; FED0 hands over a gear (and flags gears 9 and 10); FED1 sets flag `0x4000`; B9, BA, BB, FE18, FE1A and FEC6 change the joined-characters mask.


## Room exits (decoded 9 Oct 2026 from the room scripts; shown by the app in v1.34 to v1.38, kept as data only from v1.39)

How a room hands over to another room, all read from the field program's command handlers:

| Script command | Bytes | What it does | Where found |
|---|---|---|---|
| `98` | 5 | **Go to room**: u16 room, u16 entry point. Writes the room to the scene number `0x8004F34C` | handler `0x80093364`-`0x800933B4` |
| `47` | 6 | **Door destination**: flag byte, u16 room, u16 entry point. Sits in a door actor's routine; the 1-byte command `46` in the same actor does the hand-over when the player walks into it | handler `0x80092EA0`; `46` at `0x80092808` |
| `C9`, `CB`, `CC`, `0A` | 4 | **Trigger zone test**: zone number, then a jump taken when the player is *not* in that zone. The commands between the test and its jump target are what the zone does (usually a `98`) | all four read the zone list pointer `0x800ADBF4` |
| `FE84`, `FECF` | 10 / 6 | Also write the scene number (scene changes with more arguments); not decoded | handlers `0x80093520`, `0x800938D0` |

Arguments are read by `0x800ACDEC`: a u16 with bit `0x8000` set is a plain number (low 15 bits), otherwise it names a script variable. A destination's low 10 bits are the room; the bits above are flags (for example `0x4043` = room 67).

**Where an actor stands.** Script actor *i* is entry *i* of the room file's object placement table (`0x18C`: count, then 16-byte records: flags, three rotations, x, y, z, model). Door actors have their position there (flags `0x290`); actors that place themselves with command `19` have a zero position and flags `0x1E0`.

**Trigger zones** are room file block 9 (index 8): 24 bytes each, four corners of (x, y, z) s16. Their job is now known for the ones scripts test: 254 of them are walk-off exits.

**The data file (`exits.js`, room -> [x, z, destination room]; not shipped in the app since v1.39)**: 1,137 exits in 444 rooms.
- 247 zone exits: place = centre of the zone.
- 890 door exits: a `47` door, or a `98` in an actor's talk or touch routine where the actor has a position and either the destination room also leads back (which doors do and story scenes do not) or the actor is an invisible trigger.
- Left out (1,516 room changes): ones with no fixed place (run from a controller actor's main routine on story conditions), ones whose destination is in a variable, and one-way jumps from visible characters, which are story scenes rather than exits. About 120 rooms with room changes therefore show no exits, and towns laid out as several joined rooms may be missing some walk-off edges.
- Checked by drawing the exits over the map picture for 20 rooms (Lahan's house doors, Blackmoon Forest's path ends, Stalactite Cave's tunnel mouths, Bledavik's street doors, Nortune's alleys): all sit on doors or path ends. Tools: `fld/exits.py`, `fld/mkexits.py`.


## World map places (decoded 9 Oct 2026; read live by the app from v1.35, not yet seen on the handheld)

The world map program decides whether the party is standing on an enterable place by walking a table (routines `0x80094248` and `0x80094364`: position against x .. x + width and z .. z + depth).

| What | Where |
|---|---|
| Pointer to the list of place tables | **`0x8009BD00`** (set at `0x80073640`) |
| List | u32 pointers, four tables (10 Oct, from the callers of `0x80094238`): **0 on foot** (called with a 0x10 x 0x20 collision box, `0x8008AB10`), **1 the larger vehicle** (0x18 x 0x30 box, `0x8008CC48`; same places as table 0 in every set checked), **2 the ship** (three callers; adds the places only a ship reaches, such as Duneman Isle 36 and place 37, both type 2), **3 linked exits** (searched by `0x80094364` when the record stood on has type 3). The app merges tables 0 and 2 (v1.40) |
| Table | 16-byte records, ended by room = -1 |
| Record | s16 x, s16 z, s16 width, s16 depth (world units >> 12, the same units as the position at `0x8009C5AC`), s16 room, s16 entry point, s16 place number, s16 type |
| Record type | 0 ordinary place; 2 reached by ship; 3 linked exit; **4 a trigger strip, not a place** (for example 2816 x 640 with place number 40): standing in one sets `0x8009CE68` instead of the current-place pointer (`0x800942D4`) |
| Record the party is on | pointer at `0x8009D7D8` (-1 when not on a place); entering copies room and entry to the save block (`0x80071170`-`0x8007118C`) |

On the disc the tables are at the start of each world set's script file (file `3963 + 11 x set + 1`, sub-file 0: two offsets, then at the second a short pointer list and the tables). Disc-1 sets, place number: place:
1 Lahan, 2 Mountain Path, 4 and 5 Blackmoon Forest (east and west ends), 6 and 7 Dazil, 9 Stalactite Cave, 10 Nisan, 11 Bledavik, 12 Nortune, 13 Goliath Factory, 15 Orphanage, 16 Ethos HQ, 17 Ethos Dig Site, 18 Babel Tower, 19 Lighthouse, 20 Taura's House, 23 Snowfield Hideout, 32 and 33 the Anima Relics, 36 Duneman Isle. Place numbers and positions stay the same from set to set; the room behind a place changes with the story.

Not settled: in the late sets (14-16) the room column does not match the place at the same coordinates in earlier sets (for example the Stalactite Cave rectangle gives room 135), so either those rooms really change or the late tables are laid out differently. The app therefore names places by place number and position only, never by the room column, and leaves unnamed any number not in the list above (0, 3, 8, 21, 24, 26, 27, 31, 35).

Check: drawn on the app's world picture, the early-game places fall where they should (Blackmoon Forest and the Mountain Path in the wooded north-east peninsula, Dazil on the edge of the desert), which also confirms the world picture's scale and orientation.

Also settled this pass: the second position in the world block (`0x8006EE60`, save block `0x182C`-`0x1832`) is written by script command FEBA (x, y, z, heading), which only five rooms use, all aboard ships (Yggdrasil 288 and 290, Thames 312, 73, 687). So it is where the ship will be put on the world map, as guessed. FEB9 reads it back; FEBB / FEBC read and write the word after it (`0x1834`).

How a room hands over to the world map: script command `56` (see the next section).


## Field program: leaving for another program, and more script commands (9 Oct 2026, from the code; corrected the same evening)

**Programs.** The kernel's table at `0x8001808C` (16 bytes each: entry point, start and end of the program's own memory, "load from disc" flag) numbers them, and `0x8001996C(program)` writes the choice to the game state word `0x80018088`:

| Program | Entry | Its memory | What |
|---|---|---|---|
| 0 | `0x8001A4B4` | kernel | Start-up |
| 5 | `0x8001C634` | kernel | Menu runner: sets up the menu's work block (`0x800625A0`, 0x1E98 bytes) and runs whichever screen program the caller loaded at `0x801C5000` (see "Menu screens opened by scripts") |
| 1 | `0x80077E88` | `0x800AF5E4`-`0x800C426C` | Field (rooms) |
| 2 | `0x8001B6C4` | `0x800C3A6C`-`0x800D39F0` | Battle |
| 3 | `0x80070CFC` | `0x8009BBB0`-`0x8009D80C` | World map |
| 4 | `0x80088E90` | `0x800925D0`-`0x8009B554` | Battling (the arena game), not the menu (corrected 10 Oct) |
| 6 | `0x800737EC` | `0x80076F38`-`0x80077454` | Movie |

**How the field program leaves.** Script commands do not switch program themselves; each clears a request word (all are -1 when idle, set at `0x80077FC4`-`0x80077FE8`) and the main loop acts on it at the end of the frame through `0x8007954C(kind)`:

| Request word | Cleared by | Kind | Result |
|---|---|---|---|
| `0x800ADBEC` | command `98` (and door command `46`) | - | Another room: scene number `0x8004F34C` is loaded |
| `0x800ADBDC`, `0x800ADBE0` | command `71`, and the random battle check | 0 | Program 2, battle (script variables are saved first, `0x800A30FC`) |
| `0x800ADBE4` | **command `56`** | 1 | **Program 3, world map** |
| `0x800ADBE8` | command FEBF | 2 | Program 4, Battling. (The Triangle button does not use this word: it writes `0x80` to `0x800ADB64`, see the menu section) |
| `0x800B0064` | command FE83 | 3 | Any program (used in three rooms) |

`0x800ADB08` is only the display buffer index (alternates 0 / 1 each frame). (An earlier version of this section had kinds 0 and 1 the wrong way round and listed the world map hand-over as not found.)

**Command `56` (10 bytes): out to the world map.** Its second u16 is the **place number** the party comes out at, the same number as in the world map's place table. That ties every place number to a room: 1 Lahan (rooms 1, 3), 2 Mountain Path (15), 3 Citan's House (17), 4 and 5 Blackmoon Forest (22, 24), 6 and 7 Dazil (35), 8 Aveh Desert (53), 9 Stalactite Cave (74), 10 Nisan (94), 11 Bledavik (101), 12 Nortune (194, 198), 13 Goliath Factory (262), 15 Orphanage (326), 16 Ethos HQ (339), 17 Ethos Dig Site (361), 18 Babel Tower (405, 411), 19 Lighthouse (402), 20 Taura's House (614), 23 Snowfield Hideout (695), 26 Gate Generator (494), 31 Merkava (702, 716), 32 and 33 Anima Relics (628, 642), 36 Duneman Isle (47), 38 Fort Jasper (483); 0 and 37 are used from ships. 43 rooms have the command; 29 of the uses have a fixed place (a trigger zone or a positioned actor) and are in `exits.js` with destination -1.

Script commands identified this pass:

| Command | Bytes | What it does | Evidence |
|---|---|---|---|
| `71` | 3 | **Start a scripted fight** with the room's line-up number given (writes it to the chosen line-up byte `0x80059508`). These are the line-ups with weight 0 in the room's line-up table, which the app leaves out of its enemy list | handler `0x80093568` |
| `FE83` | 4 | Switch to another program (kind 3 above) | handler `0x80092FB4` |
| `FE68` | 7 | Walk the player to a point (x, z, flags); it comes just before a door's room change | 223 uses, 188 of them in talk routines, followed by `98` |
| `FE69` | 6 | Load a party member's field model from disc; `0x800ADBC4` is its "loading" flag (the menu is refused while it is not `0xFF`) | handler `0x8008A6E0` |
| `A0` | 7 | Camera set-up: direction (argument + 4) & 7, written to the camera direction word | handler `0x8009BA7C` |


## Menu screens opened by scripts: memory cubes and shops (9 Oct 2026; found from Jack's pointer to the Lahan memory cube; second pass 10 Oct)

**How a menu screen runs.** The field program stays loaded. A script command (or the Triangle button) writes a screen number to `0x800ADB64` (-1 when idle) and an argument byte to `0x80059171`; at the end of the frame `0x800799D4` loads that screen's program from the disc to `0x801C5000`, stores the number in **`0x80059460`** (u8, `& 0x7F`) and calls the kernel's menu runner `0x8001C634`. `0x800ADB64` goes back to -1 when the screen closes. So while a menu is up: `0x800ADB64` is not -1, `0x80059460` says which screen, `0x80059171` holds its argument.

The screen programs are in the menu directory (directory 16 in the disc's directory list at sector 40; tool file numbers 2593 on). The game's file k of that directory is tool file 2592 + k, and screen n loads file 5 + n:

| Screen | Command | Bytes | Tool file | What | Argument (`0x80059171`) | Used in |
|---|---|---|---|---|---|---|
| 0 | `FE55`, Triangle (`0x80`) | 2 | 2597 (the main menu program, same bytes as file 39) | **The main menu.** A memory cube is just the main menu opened with saving allowed | 1 = Save can be chosen, 0 = Save greyed out (`0x801DA7D8`) | 111 rooms, 127 uses |
| 1 | `FE56` (also `FECF`) | 4 | 2598 | **Party screen** (choose who is in the party). Reads the joined mask, `FrMask` and the locked mask, writes the party slots `0x8006F368` | the command's number goes to script variable 1 (`0x8006EF66`) and its saved copy `0x8006F954` instead | 22 rooms: Nortune, Goliath Factory, Yggdrasil, Shevat, Solaris, Krelian's Lab, Mahanon, the Anima Relics, Merkava |
| 2 | `FE57` | 2 | 2599 (main program again) | Probably the **load screen** of the title: the main program runs with a cut-down set-up, and if it comes back with nothing loaded the field program starts in room 4 (`0x80079EC4`). **Seen running 14 Oct** (emulator): New Game / Continue / Sound, then the memory card's file list and "Load this file?". The code it runs is not the main program's: it matches disc file 900 from offset 0x6FC, loaded at `0x801C5000` | - | room 490 and debug rooms |
| 3 | `FE58` | 4 | 2600 | **Name entry**: 0-10 renames that character, 11-26 renames gear (number - 11) | who to rename | Yggdrasil rooms 292, 293, 296, 301 and debug |
| 4 | `FE59` | 4 | 2601 | **Item shop** | shop number | 31 rooms |
| 5 | `FE5A` | 4 | 2602, plus 2604 loaded at `0x801DC000` | **Gear shop** | shop number | 25 rooms |
| 6 | `FEDA` | 2 | 2603 (main program again) | Probably the **save before changing disc**: same cut-down set-up as screen 2, used once, in the room where disc 1 ends. **Seen running 14 Oct** (emulator): "Save?" Yes / No, then "INSERT DISC 2". Runs the same file 900 code as screen 2 | 1 | room 612, Taura's House |

**Saving allowed: `0x800B236C`** (u16, field memory). Script command `FE99 n` writes `n XOR 1` here, and both Triangle and `FE55` pass it on as the menu's argument. 0 at room start, so Save is greyed out; a memory cube's talk routine is `FE99 00` (allow), `FE55` (open the menu), `FE87` (wait for it to close). 166 uses allow, 90 forbid again. Not read on the handheld yet.

**Shop stock (10 Oct; confirmed on the handheld the same day: the Mountain Path shop showed exactly the four items and prices of shop 1).** The tables are in tool file 2593 (the game's file 1 of the menu directory, an LZSS pack of 8):

| Sub-file | Size | Layout |
|---|---|---|
| 6 | 40 x 92 | **Item shops.** Record = shop number x 92: 30 weapon IDs, 30 equipment IDs, 30 item IDs (one byte each, 0 = empty slot), 2 spare. Read at `0x801C6A6C` in the item shop program through the pointer at menu block `+0x1E2C` |
| 7 | 30 x 100 | **Gear shops.** Record = shop number x 100: five lists of 20 one-byte IDs: frames `+0x00`, armor `+0x14`, engines `+0x28`, gear weapons and ammo `+0x3C`, gear parts `+0x50`. Read at `0x801C6E74` in the gear shop program through menu block `+0x1E90` |

35 item shops and 19 gear shops have stock. Item shops come in pairs: an even number sells items, the odd number after it sells weapons and equipment, and a shopkeeper's script offers both (Dazil 2 and 3, Nisan 6 and 7, Nortune 10 to 13). Prices are the price fields already listed under "Stat and price tables", and the well-known ones match (Nisan sells the Ether Doubler at 38,000 and the Life Stone at 20,000; Lahan sells Aquasol 20, Rosesol 100, Omegasol 50, Survival Tent 150). 10 item shop numbers and 4 gear shop numbers have stock but no script that names them with a plain number (rooms pass those through a variable). Gear shop 15's weapon list repeats its parts list, so that list is wrong on the disc or the shop is unused. Full list with names, prices and rooms: `xenogears_shops.json`; tool `xenogears_shops_py.txt`. The app shows the open shop's stock from v1.40 (`shops.js`).

**Shops checked in the emulator (14 Oct 2026).** Jack's Tournament save, shops opened by writing the screen number to `0x800ADB64` and the shop number to `0x80059171` (the same two bytes a shopkeeper's `FE59` / `FE5A` sets), which works from any room:

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x800ADB64` | u8 | Screen requested, `0xFF` idle (a byte: the three bytes after it stay 0). 4 item shop, 5 gear shop, stays set while the screen is open | A |
| `0x80059460` | u8 | Screen running; it still held the last screen (2) for about 40 frames while the shop program loaded, then 4 or 5 | A |
| `0x800625A0` | pointer | **Menu block** (0x800CB210 for the main menu and both shops). The screen programs reach everything through it | A |
| block `+0x1E2C` | pointer | Item shop stock table (all 40 records of 92 bytes); record [shop] read live for Nisan's shop 6 = Aquasol … Survival Tent, the disc list | A |
| block `+0x1E90` | pointer | Gear shop stock table (30 records of 100 bytes); record 1 read live = frames 2, 3, 42, 62, 63, armor 7, 8, engine 8, parts 47 … 88, the disc list | A |
| block `+0x336` (and `+0x337`) | u8 | Top-level menu cursor counted from the bottom: options below the arrow. Item shop Buy / Sell / Exit = 2 / 1 / 0; gear shop Tune up / Buy / Sell / Exit = 3 / 2 / 1 / 0 (opens on Buy); main menu Status = 6 … Exit = 0. So the option is (number of options − 1) − value | A |

Not at a fixed address: the cursor inside the Buy and Sell lists and the quantity being chosen. They live in the shop program's own registers and stack (`0x801FFDB4` held the list row and `0x801FFDD0` the total in this emulator, but stack and thread areas depend on the call path and the BIOS, so the app should not read them). The arrow sprite's screen y (13 pixels a row) is in a heap buffer, also not fixed.

Buying and selling, checked:
- Buying 2 Rosesol S at 300 took 600 G off gold (`0x8006EF58`, save `+0x1924`: 6431 → 5831) and put ID 7 with quantity 2 into the first empty item slot (slot 7: `0x8006F5CB` = 2, `0x8006F661` = 7). The screen asks "Total 600 G. Is that okay?" with No selected first.
- Selling one Hob-Jerky (price field 10) gave 5 G and took the slot's quantity from 3 to 2: **selling pays half the price** (one sample, rounding not checked).
- The gear shop opened on Weltall with the frame's HP 1800, fuel 1200 and weight 3500 shown.

**The shops with no room on disc 1** (item shops 16, 17, 20-25, 29, 33; gear shops 4, 12, 13, 15): on disc 1 the only script that opens them is the debug shop picker in room 488 (actor 56: a window lets you step a shop number in variable `0x16` up and down with `3C` / `3D`, then `FE59 0016` or `FE5A 0016`) and its copy in debug room 723. Their stock (Wonder Whip, King's Helm, Death Adder, `#17` frames, RX Metal 90…) is late-game, so they are most likely the disc 2 shops, whose rooms are only on disc 2.

Other files in the menu directory: 2594 (the game's file 2) is the big table pack described under "Stat and price tables"; 2605 is 354 x 32 bytes of place names in full-width letters, one per story step (the place line of a save file); 2606 is the debug room's text.

A memory cube is a shared script template: its set-up routine is `0B` (sprite from a variable), `19` (position from two variables, flag byte 0), and its talk routine is `FE99 00, FE55, FE87`. The room's controller fills the variables first with `35` (set variable). So an actor's place can come from three sources: a `19` with numbers, a `19` with variables that a `35` elsewhere in the room sets, or the room's object placement table.

`marks.js` (room -> [x, z, kind]; s = memory cube, i = item shop, g = gear shop) holds 76 memory cubes, 24 item shops and 16 gear shops in 94 rooms. Not placed: 47 save uses, 23 item-shop and 14 gear-shop uses whose actor has no fixed place (many are second routines of an actor already listed). Tools: the scan is in `fld/` alongside `exits.py`.

## Party battle sprites (10 Oct 2026)

The party's on-foot battle sprites are tool files **2988-2998**, one per character (directory 45 of the sector-40 table). The files are **not** in character-ID order: 2988 Fei, 2989 Elly, 2990 Bart, 2991 Citan, 2992 Billy, 2993 Rico, 2994 Emeralda, 2995 Chu-Chu, 2996 Maria, 2997 Citan with sword, 2998 adult Emeralda (IDs 0, 1, 3, 2, 4-10). 2999-3004 are copies of Elly's file; 3005-3007 are five-block files (they draw as Fei, Elly and Bart in other poses; not looked at further).

Each file is an archive (u32 count, u32 offsets) of three blocks, like an enemy sprite definition, but there is no separate texture block: every tile carries its own pixels.

- Block 0: animations (not decoded; same style as the enemy sprites).
- Block 1: frames and tiles.
  - u8 frame count, u8 `0x14`, then one u16 offset per frame.
  - Frame: u8 tile count (low 6 bits), 5 more header bytes (look like the frame's size and origin; not needed to draw it), then per tile two u16: **A** = where the tile is, in 4-byte units from the start of block 1; **B** = where the game puts it in video memory (low bits a size class; not needed). After the pairs, one placement per tile: any bytes `C0-DF` (1 byte) or `E0-FF` (3 bytes) are control codes and are skipped, then u8 flags (low 4 bits = palette number; `0x10` / `0x20` are taken as mirror bits as in the enemy sprites, not checked here; `0x40` also occurs, meaning unknown), s8 x, s8 y. Tiles are drawn last to first.
  - Tile at A x 4: u8 width, u8 height, 2 zero bytes, then height rows of width / 2 bytes, 4 bits per pixel, low nibble first. Colour 0 is see-through.
- Block 2: u16 palette count, u16 zero, then 16-colour palettes (15-bit).

Frame 0 is the standing pose for all eleven. Checked by drawing all 130 of Fei's frames and frame 0 of every file; all come out clean. Sizes of frame 0 (width x height, in character-ID order): 31x47, 23x51, 25x54, 23x55, 23x49, 40x64, 23x39, 26x33, 22x41, 30x55, 25x54. The app uses these as `img/pb/<id>.png` for the turn timeline. Tools: `pbr.py` and `mkpb.py` at the end of `xenogears_sprite_py.txt`.

## The fight's line-up copy (10 Oct 2026)

When a battle starts, the battle program (`0x80071130`) copies the room's chosen line-up record, 0x20 bytes from `0x800658DC + 0x20 x index` (index = u8 at `0x80059508`), to **`0x8006F9DC`**, where it stays for the fight:

- `+0x00` monster bank (disc file 2618 + 2 x bank); `+0x01..` not decoded.
- `+0x08` eight bytes, one per enemy slot (battle slots 3-10 in order): the bank record of that enemy, `0xFF` = none, `0x80` = gear-sized.
- `+0x10` eight flag bytes. `0x80` marks an enemy that is not on the field at the start: 99 named cases (for example Forbidden) and the unnamed record 2 of the Aveh soldier bank (bank 4), which is in every soldier line-up of rooms 57 and 58 and is never fought.
- `+0x18` eight more bytes (values 0-4), not decoded.

Since v1.52 the app names enemies from this copy instead of guessing from HP and rewards. Bank 4's records: 0 Aveh Corporal, 1 Aveh Soldier, 2 unnamed (Corporal's numbers), 3 Aveh Corporal (37 EXP, no gold), 4 Aveh Soldier (no gold), 5-6 Aveh Guard, 7 ShakhanGuard. The bank's string table has nine name entries because entry 0 repeats the first name; entries 1-8 are records 0-7. Not yet checked on the device.

The enemy removal loop at `0x80072610` also reads a per-slot table of 0x1C-byte entries at `0x800C3E64 + slot x 0x1C` (byte `+0x54` chooses the gear path, byte `+0x53` skips the slot); not decoded further.

## Gear deathblow unlocks (10 Oct 2026)

Skill record `+0x08` (u16, top bit first): bits 3-11 are the nine gear moves (three per attack level), bits 12-14 infinity moves. Compared with the learned on-foot deathblows (`+0x04`, top bit first) for every pilot in the two save files:

- on-foot deathblow 1 and 2 learned -> gear bits 3 and 4 (level 1, first and second move); 3 and 4 -> bits 6 and 7 (level 2); 5 and 6 -> bits 9 and 10 (level 3). Examples: Fei with 3 learned has bits 3, 4, 6; Billy with 4 has 3, 4, 6, 7 and with 5 adds 9; Emeralda with 7 has 3, 4, 6, 7, 9, 10.
- The third move of each level (bits 5, 8, 11) is set only for adult Emeralda in these saves; rule unknown. Citan with sword also has bits 0 and 1.
- Maria has bits 3, 4, 6, 7, 9, 10 with no on-foot deathblows; Chu-Chu none early, 12-13 later. Infinity bits appear only in the later save (Fei 12-14, others 12 or 12-13).

Button pairs in the game's list: attack level button first (triangle 1, square 2, cross 3), then the move (triangle, square, cross); Reppu = triangle, square confirmed on Jack's game.

## Rock-paper-scissors in Lahan (room 7, actor 3) (11 Oct 2026)

Read off the room script (talk routine at script offset `0x015A`). Script command `A8 var, N` = random: var = (rand() x (N + 1)) >> 15, so 0..N evenly (handler `0x8009D1F0`). Command `02 var, value, op, target` runs the next block when the test holds and jumps to target when it does not; op `0x40` = equal, `0x42` = greater than, `0x46` = bit test.

- The man's hand is `A8 0x408, 2` (0 Rock, 1 Scissors, 2 Paper), rolled **before** the player's choice comes up, fresh every throw and again after a draw. It does not look at the player's choice or at earlier rounds.
- The player's choice (variable `0x14`: 1 Rock, 2 Scissors, 3 Paper) has a counter each (`0x40C`, `0x40E`, `0x410`). Choosing a hand adds one to its counter and clears the other two. **If the counter is above 3 (the same hand four or more times running, draws included) the script skips the comparison and goes straight to the losing branch**; at 8 the counter is cleared (that throw still loses).
- Win: +50 G, streak `0x412` + 1; at 4 he remarks on it, at 5 the streak is cleared and saved variable `0x2DE` is set to 30. Loss: -50 G, streak cleared. A draw is thrown again and changes neither. One decided throw per conversation; needs 50 G.
- Next time he is spoken to, `0x2DE` > 29 gives the RPS Badge (item 76) and sets flag variable 718 bit 15. `0x2DE` is cleared by a later win.
- Re-checked 13 Oct against Noah (`OP_A8` = `xenoRand() * (N + 1) >> 15`) and a full listing of routine 2: `0x408` is written only by that roll (offsets 562, after the intro and again after every draw); nothing reads the player's past hands except the three repeat counters. The counters are scratch variables reset by his set-up routine (room load), not by ending the conversation. In a forced loss the script jumps into the branch where his hand beats yours, so he is shown throwing the winning hand. Cancelling the hand menu takes 15 G (lines 48-50). After the badge (`0x2CE` bit 15) he only says line 5.

## Story step commands (11 Oct 2026)

The story step (script variable 0) is not written with the ordinary set-variable commands. Script command **`87 n`** sets it (handler `0x80096790`: value operand, then write to variable 0). Commands `84`, `85`, `86` (4 bytes of operands: a value and a jump) and `88` branch on it (handlers `0x80096644`-`0x800967E8`, each reads variable 0); which comparison each one makes is not decoded yet.

Scan of all 730 rooms: `87` sets 145 different step values in rooms 0-719 (the 354-entry chapter-name table has room for more than are used: steps jump, e.g. 1, 3, 6, 7, 8, 9, 10, 12, 13, 15, 16), 134 of them from a single room. The debug rooms 720-726 also set most values. The step is tested about 2,940 times across the rooms (`85` 1,221, `86` 1,199, `84` 520, `88` 9). The list of where each step is set is `fld/story_sets.json` (step -> [room, actor, routine]). This is the basis for a "where next" hint: the next step's room and actor.


## From the Noah decompile (github.com/yaz0r/Noah, read 13 Oct 2026)
Noah is a partial C++ decompile of the US release (field, walkmesh, menus, some battle). What it settled for this project:
- **Game state `0x8006D634`**: `+0x231A` field id (`&0x3FFF`; >= 0x400 is the world map), `+0x231C` camera yaw, **`+0x2320` entry index** (which entrance the player arrives by), `+0x2322` music. No player position is saved; the room script places the player from the entry table. Gold `+0x1924`. Menu EXP display uses character `+0x44`/`+0x48`; our map has `+0x3C` as EXP and `+0x44` as to-next: unresolved, check on device.
- **Memory card**: `.srm` (RetroArch) and `.mcr` (ePSXe) are the same raw 128 KB card. Directory frame status 0x51 = live save, 0xA1 = deleted. Save data at block offset 0x124; card offset = RAM-form offset - 0x820 + 0x124 (room 0x1C1E, entry 0x1C24, story step 0x1234). Title at block +0x04 in Shift-JIS fullwidth. No checksum code found in Noah, and edited saves with only room/entry/step/title changed are expected to load (not yet confirmed in game).
- **Entry table**: when a room's script bytecode starts with 0xFF, it begins with 7-byte records {s16 x, s16 z, u8 layer, u8 camera dir, u8 facing}, one per entrance; opcode `0x16` (INIT_ENTITY_PC) places the player from it using the entry index.
- **Script opcodes** (names from `fieldDebugger/atelOpcodes.cpp`): `84/85/86` step <, >, == (fall through, else jump); `87` set step; `FB` test flag bit (`fieldVars[X>>5]`, bit `X&0xF`), `FE0A` set it; `07/08/09` run another entity's script (param&0x1F = script, param>>5 = mode); `D2/D4/FC` dialogue; `98` CHANGE_FIELD (field, entrance); `47` walk and change field; `19` SET_ACTOR_POSITION_2D; `1A` SET_ENTITY_WALKMESH_LAYER; `1D` 3D position; `FE1C` x, z, y + control byte; `0B` INIT_ENTITY_NPC; `BC` INIT_ENTITY_SCRIPT; `F7` SET_ENCOUNTER_DATA; `14` enable battles; `15` sets `fieldRandomBattleVar` to -1. Args with bit 0x8000 are literals; s16 args take a control byte. Variables are byte offsets into `fieldVars` (live `0x800C3A68`, saved copy at gameState `+0x1930`).
- **Walkmesh triangle flags**: `0x800000` blocked (layer 0, never chosen from other layers), `0x400000` steep slide, `0x200000` ladder, `0x20000` slope, `0x80` blocks the party on foot, `0x40` blocks gears, `0x20` blocks NPCs, `0x10`/`0x08` block jumps only, `0x04` layer switch, `0x02` no shadow. **The last walkmesh layer of every room (rooms have 2-4) is the camera-bounds mesh**, not floor.
- **Script entity** (pointer at actor `+0x4C`, 0x138 bytes): walkmesh layer `+0x10` (matches the app's player layer), position `+0x20/+0x24/+0x28` (16.16).
- **Encounters**: Noah's validator writes 0 to `0x800B2298` to switch off field encounters, the same address as the GameShark code (`800B2298 0000`, or with `D0` conditions on their own lines).
- **Room names**: `fieldNames.cpp` has 697 `{id, "name"}` pairs taken from the debug-room list (copy in `fld/faq_room_names.json`).
- Not covered by Noah: battle EXP/gold reward code, item use, save checksum.

## More addresses, 14 Oct 2026 (Noah's validation code and the matching decomp's symbol list)

Sources: Noah's validator (`NoahLib/validation/*`) reads these addresses from a real emulator every frame and compares them with its own state, so they are confirmed by a running game (A). The matching decomp (github.com/ladysilverberg/xenogears-decomp, `config/symbol_addrs.*.txt`, pulled 14 Oct, commit e748b43) names the kernel and field globals; a matching decomp only builds when the names sit at the right addresses (A for the address, B for what the name says the value means). Checked against the two late-game test saves where a save holds the value.

**Field program (room loaded)**

| Address | Type | Meaning | Source | Conf. |
|---|---|---|---|---|
| `0x800AFD04` | u32 | **Room change in progress**: 1 from the moment a new room starts loading until its set-up is done, then 0 | Noah validator (`fieldTransitionInProgress`) | A |
| `0x800B21CF` | s8 | Party does not follow the leader (1 = the other two stay put) | Noah validator | A |
| `0x800C3900` | u16 | Buttons the field uses this frame (same bits as the controller table below) | Noah validator (`g_padButtonForField`) | A |
| `0x800C2694` | u16 | Buttons the text boxes use this frame (talk / advance) | Noah validator (`padButtonForDialogs`) | A |
| `0x800AFE9C` / `0x800AFEA0` | u16 each | Buttons room scripts test, controllers 1 / 2 (the first was already listed) | Noah validator | A |
| `0x800ADC00` | pointer | Script data of the entity whose script is running | decomp (`g_FieldScriptVMCurScriptData`) | A |
| `0x800AFB18` | pointer | **The loaded room's walkmesh block** (room file block 1 as decompressed: u32 layers, 4 x u32 triangle bytes, u32 surface table offset, then per layer u32 triangle offset, u32 vertex offset). Field code `0x800711B4` reads the layer count through it and fills the four entries below from its header. The app reads the floor from here since v1.87 | field code | A |
| `0x800AFB20` | pointer | That block's surface flag table (32-bit flags, one per surface index) | field code `0x80071200` | A |
| `0x800AFB54` | s16 | Number of walk layers in the loaded room | Noah validator (`g_numWalkMesh`) | A |
| `0x800AFB44` | 4 x s32 | Triangles in each walk layer | Noah validator | A |
| `0x800AFB24` | 4 x pointer | Each layer's triangles, 14 bytes each: three s16 vertex indices, three s16 neighbour triangles (-1 = edge), u8 surface index, u8 | Noah validator | A |
| `0x800AFB34` | 4 x pointer | Each layer's vertices, 8 bytes each (SVECTOR x, y, z) | Noah validator | A |

The walk mesh pointers mean the live room's walkable floor can be read straight from memory, the same data the app builds from the disc.

**Field camera** (next to the eye `0x800AF880` and target `0x800AF890` already listed; all from Noah's validator unless marked)

| Address | Type | Meaning |
|---|---|---|
| `0x800AF8A0` | VECTOR | Camera up vector |
| `0x800AF8B0` / `0x800AF8C0` | VECTOR | Second eye / target pair (the one being blended toward) |
| `0x800AF8E0` | VECTOR | Field camera offset |
| `0x800AFA54` | | Projection angles |
| `0x800AFA5C` | | Camera rotation |
| `0x800AFA64` | MATRIX | Current projection matrix |
| `0x800AF85C` | MATRIX | Second camera matrix (the first, `0x800AF990`, was already listed) |
| `0x800AF900`, `0x800AF910` | VECTOR | Scripted camera move: target to, eye from (decomp) |
| `0x800AF940`, `0x800AF950` | VECTOR | Scripted move: target now, target step per frame (decomp) |
| `0x800AF964`, `0x800AF974` | VECTOR | Scripted move: eye now, eye step per frame (decomp) |
| `0x800AF984` | 12 bytes | Camera interpolation state (decomp) |

**Battle program**

| Address | Type | Meaning | Source | Conf. |
|---|---|---|---|---|
| `0x800C3E4C` | s8 | **Battle mode**: 2 while a battle's opening scene or battle event plays (no player input), 1 once the fight proper runs, 0 a third input mode (text-window battles) | Noah validator + `battleUpdateInputs` | A |
| `0x800D3354` / `0x800D335C` | SVECTOR | Battle camera eye / target now | Noah validator | A |
| `0x800D30A0` / `0x800D30A8` | SVECTOR | Battle camera eye / target it is moving toward | Noah validator | A |
| `0x800D30BC` | MATRIX | Battle rendering matrix | Noah validator | A |
| `0x800CCB3C` | 11 x pointer | Sprite actor of each battle slot (position, facing, current frame) | Noah validator | A |
| actor `+0xAC` | u16 flags | **Bit 0 set = the fighter is not drawn**: a boss's helpers waiting to be called in (Super Aerod before Hecht's move, Fis-6's Mechanics) sit in the slots with turn timers but have this bit set; clear on every fighter on the field. Two save states, 12 actors (15 Oct 2026). The Super Aerod's actor is also parked about 5,800 units above the field while it waits; the Mechanics stand at normal places | B |
| `0x800C35D4` | | Battle music override flag (set by some deathblow sequences) | Noah comment | B |

**Kernel (always loaded)**

| Address | Type | Meaning | Source | Conf. |
|---|---|---|---|---|
| `0x80058960` | s32 | **Frames since power-on** (vertical blank count, +60 a second at full speed). Two readings and the time between them give the game's real speed, so the app can tell normal play from fast-forward or a pause | decomp (`g_VsyncInterruptCount`) Emulator, 14 Oct: equals the vertical-blank count from power-on and keeps counting through a save load (unlike the play time `0x80059488`, which jumps to the save's time) | A |
| `0x80059570` / `0x80059574` | u16 | Buttons held, controllers 1 / 2 (already listed; bit list below) | decomp | A |
| `0x80059374` / `0x80059378` | s32 | Buttons held last frame | decomp | A |
| `0x80059388` | u8 | Controller type: 1 digital pad, 2 mouse, 3 analog pad, 4 analog stick, -1 error | decomp | A |
| `0x8005A0FC`, `0x8005A13C`, `0x8005A17C` | 16 x u16 each | Controller 1 queue of held / released / just-pressed states (controller 2: `+0x20`); the "always run" code writes `0x40` into the first | decomp | A |
| `0x800625FC` / `0x8006261E` | 0x22 bytes | Raw controller buffers 1 / 2 (status, type, two button bytes, sticks) | decomp | A |

Button bits (held, released and pressed words): L2 `0x0001`, R2 `0x0002`, L1 `0x0004`, R1 `0x0008`, Triangle `0x0010`, Circle `0x0020`, Cross `0x0040`, Square `0x0080`, Select `0x0100`, L3 `0x0200`, R3 `0x0400`, Start `0x0800`, Up `0x1000`, Right `0x2000`, Down `0x4000`, Left `0x8000`.

**Save block (game state `0x8006D634` + offset)**

| Address | Offset | Type | Meaning | Conf. |
|---|---|---|---|---|
| `0x8006EE76` | `0x1842` | s16 | World map: minimap switched off when non-zero (Noah); 0 in both saves | B |

Noah's names agree with rows already in this map: `0x2318` (`0x8006F94C`) is its `partyFrameLock` (the locked-members mask above), `0x231E` (`0x8006F952`) its world map start-position index (`0xFFF` = none, as set at start-up), `0x22B1` (`0x8006F8E5`) its `isOnGear` (the gear ride flags).

**Gear-shop menu (only while that menu runs, `0x801D....`)** (decomp names)

| Address | Type | Meaning |
|---|---|---|
| `0x801D9084` | | Gear being looked at |
| `0x801D904C` | u16 | How many of the item under the cursor the party already has |
| `0x801D6FDC` | | Character whose Gear is shown |
| `0x801D6FD8` | s32 | Characters to choose from |
| `0x801D908C` | 20 x s32 | Inventory counts for the list on screen |

**Corrections and confirmations from the test saves**
- Gear fuel is two u16 at gear `+0x38` (fuel) and `+0x3A` (maximum), as already listed. Noah reads one s32 at `+0x38` and another at `+0x3C`, which gives nonsense on real saves (2500 / 2500 reads as 163842500), so Noah's names there are not used.
- Gear `+0x10`-`+0x33` stays "per-weapon data": Noah calls `+0x10` / `+0x12` ether / max ether, but the saves hold weapon-like values there only for gears with ranged weapons (Vierge, Brigandier, Renmazuo, Fenrir, Andvari, Heimdal 2).
- Skill record `+0x1B` (AP gained per turn, Noah `m17_energyPerTurn` counted from `0x16C0`): 6 for everyone in save a (levels 41-45), 7 in save b (levels 65-73).
- Character `+0x44` and `+0x48` are equal in all 22 records (two copies of experience still needed).

## Battle Arena (Battling mini-game), from a save state of a match (14 Oct 2026)

Jack's DuckStation save state inside a match (Weltall vs Ganador, from the Battle Arena hangar, room 223). The program running is **overlay file 35** (first word 7 at `0x8006FAF0`); earlier rows that call file 35 / word 7 the movie program are wrong, it is the Battle Arena. `0x800592C0` is `g_CurGameStateOverlayID` in the decomp (the menu overlay loaded on the heap, -1 when none), not the running program.

| Address | Type | Meaning | Conf. |
|---|---|---|---|
| `0x800987E0` | s16 | Your Gear's HP (the published "Battle Arena infinite HP" address) | A |
| `0x800987E8` | s16 | Your Gear's maximum HP (300) | B |
| `0x800987E2` | s16 | Your Gear's **heat** (the red tube): 1 gauge pixel = 64 heat, full tube 51 px ≈ 3264. Samples: 1548 = 24 px, 3288 = full (outer gauge turns yellow), 0, 36. Opponent's at `0x800970C6` (1254 = 19 px, 312 = 4 px, 220 = 3 px). `+0x0A` holds 1152 for both fighters | A |
| `0x80098798` / `0x8009879C` / `0x800987A0` | s16 | Your Gear's x / height / z (record `-0x48` / `-0x44` / `-0x40`) | C |
| `0x800970C4` | | **Opponent's record**, same layout as yours (0x171C earlier): HP 175 / max 300 in the sample | B |
| `0x80092700` / `0x80092704` | u32 | Place of you / the opponent in the fighter table (0 = Weltall; opponent 17 = Ganador and 19 = W-SHAVER in two matches) | B |
| `0x80091968` | 49 x 12 bytes | Fighter table: model file name pointer (`ply_01`...), display name pointer, number (1-49). Names: WELTALL, VIERGE, HEIMDAL, BRIGANDIER, RENMAZUO, STIER, BLADEGASH, SIEBZEHN, CRESCENS, CHU-CHU, WELTALL-2, XENOGEARS, EL-REGRS, EL-FENRIR, EL-ANDVARI, EL-RENMAZUO, EL-STIER, GANADOR, TITAN, WSHAVER, FIREWHEEL, SILVERSTAR, ARGENTO, MUSHA, HATAMOTO, BACKFIRER, SHINOBI, WYRM, TIN ROBO, RANKAR, ETONE1, ETONE2, GOLEM, FIXBOT, WORKER, DOZER, DEATH, MERMAN, SALVAGER, TROOPER, TWINBURNER, S-TROOPER, S-TRIPPER, SUFAL, EG-GUNNER, EG-ARMOR, PEDESTAL, EDIN, EG-BLADE | A |

Heat was matched to the screen from four save states (14 Oct): the game frames were rendered from each state's VRAM (around rows 290-560, columns 660-1010) and the red tube's height measured in pixels. The outer gauge around the tube (blue, yellow when heat is full) is not tied to a field yet. When a fighter's HP reaches 0 the match ends on the REPLAY screen with the records still in place.


## Checked in an emulator, 14 Oct 2026

The game now runs here: the pcsx_rearmed libretro core (built from GitHub, with its built-in BIOS) driven by a small Python front end that loads a memory card, presses buttons, saves states and reads RAM (`claude/xenogears_emu_lr_py.txt`; run with the interpreter, `pcsx_rearmed_drc` = disabled). Saves were made from Jack's "The Tournament" card with the save editor's method (room + entrance variable 0x54 + checksum), so any room can be started. Rows marked "Emulator, 14 Oct" above were checked this way. Summary:

- **Field:** player actor index, position and facing; camera angle and the saved yaw; story step; random battle window and timers (room and world map).
- **World map:** live position and heading, saved position block; loading a save with field ID `0x400`, `+0x2320` = 1 (on foot) and `+0x231E` = `0xFFF` starts on the world map.
- **Battle:** party IDs per slot; HP live at slot `+0x4C` for enemies (an elf went 41 → 0 and its ready byte to `0xFF`); turn countdowns, restart values, ready bytes and the turn slot; **AP per party slot** (new) and combo points left (new); experience per enemy (`+0x14C`) paid in full to the character record at the end.
- **Play time:** `0x80059488` and the card summary's first word; the clock bytes are a display copy that can be stale.
- **Main menu:** opens without changing `0x800592C0` (stays −1) or the program word (stays 4); no single reliable "menu open" byte found yet.
- **Shops:** item and gear shops opened, stock pointers, top-level cursor, buying and selling (see "Shops checked in the emulator" under the menu screens).
- Not done: text boxes (already confirmed on the handheld in v0.5), status ailments, gear fights.

## Nortune sewer milestones between story steps 111 and 114 (14 Oct 2026, from the room scripts; not yet seen live)

Step 114 is only set by the cutscene in the sewers (room 239, actor 31, `87 72`), so the hint for 114 stays up from registering Weltall onward. Two flags in between:

| Address | Script variable | Set when | Set by |
|---|---|---|---|
| `0x8006F1A8` bit `0x0001` | `0x244` bit 0 | Rico has decided to search the sewers and Fei and Citan go with him ("For the sake of my men too, I am about to check out the sewers") | room 213 controller (`3A 0244 0`), then the party moves to room 211 |
| `0x8006F164` bit `0x0001` | `0x200` bit 0 | The scene the first time the party enters the sewers with Rico has finished | room 239, actor 34 routine 1 (`3A 0200 0`), which only runs while `0x244` bit 0 is set and this bit is clear |

The sewer watchman in D Block (room 196, actor 37 routine 5: Rico "Thanks for watching the sewers. I'm going down there now!", watchman "Yes sir, Champ") sets nothing of its own: it clears bits 2 and 4 of variable `0x24A` (as every way into the sewers from room 196 does) and moves the party to room 239. It plays when the party walks into the entrance zone (trigger zone 0) while `0x244` bit 0 is set (room 196 actor 56 routine 1).

Variable `0x244` holds the Nortune story bits (bit 1 set in Rico's room 218, bits 2 and 9 by the sewer entrance, 3/4/10 in room 211, 6/7 at the Battling arena, 8/11-15 in room 213), and `0x200` / `0x202` hold the sewer search bits (slime spots, rooms 239-242).


## Checked in the emulator, second pass (14 Oct 2026)

| Address | Size | Meaning | Grade |
|---|---|---|---|
| `0x8001808C` | 7 × 16 bytes | `g_MainGameStates`: entry, memory start, heap start, has-overlay. States: 0 start-up, 1 field, 2 battle, 3 world map, 4 Battle Arena, 5 menu runner, 6 movie (the program table above) | A |
| `0x80018088` | u32 | `g_CurGameState`: 0 while a program runs (the main loop calls `ChangeGameState(0)` before starting it); holds the next state only while switching. Writing 4 here at a battle start crashes, because the arena needs the field's hand-over | A |
| `0x800ADBE8` | u32 | Field's arena request word (-1 idle). **Writing 0 in any room opens the Battle Arena** ("Bonus Battling": Practice, Tutorial, Exit; then Player 1 vs COM / Player 1 vs Player 2 / COM vs COM, number of matches, COM level, rubber band; Gear choice). The field leaves through kind 2 (`0x80079654`), which also adds 1 to `0x8004F30C` | A |
| `0x8006F8E5`-`0x8006F8E7` | 3 × u8 | `gearRide` (game state `+0x22B1`), one per party slot: 1 = in a Gear. Written by the field commands "ride Gear" (`0x8009FC48`) and "get out" (`0x8009FCAC`). Setting them to 1 and starting a random fight gives a Gear fight (Weltall, fuel 1200, against the room's on-foot enemies) | A |
| `0x800658DC` | 16 × 32 bytes | Room line-up table (as before). Writing a line-up whose bank has Gear enemies (bank 2: Gigafoot, Trooper) gives Gear-vs-Gear fights | A |
| `0x800B0064` + `0x800ADBD8` | u32 | Field exit kind 3: write a program number to `0x800B0064` and 0 to `0x800ADBD8`. Program 6 plays the intro movie (Squaresoft logo, Xenogears title), then returns to the field. FE83 is used only in debug rooms 488 and 723 and in room 490, always to programs 1 or 3 | A |

- **Story FMV in rooms** is played by the field program itself, through the module at `0x801D3000` (disc file 19; the field calls `0x801D3538`, `0x801D37CC`, `0x801D3F7C`, `0x801D43B0`), not by switching to program 6.
- Recomp data second pass (Battle Arena, Gear fights, gear shop screens, party / name / load / disc-change screens, every room entrance, story set-ups): `xenogears_recomp_data.md`.

**Script notes from the 1.91 hint work (14 Oct 2026, from reading room scripts):** script variable 2 is the entrance number the party came in by (rooms branch on it: the Thames Beer Hall only plays Bart's drinking scene for entrances 8 and 3). Commands `12 <room | 0x8000> <entrance>` and `FE84` are room changes that the exit scan (`exits_raw`) does not list. `46` is a bit-set test; `42` / `43` compare >= / <=. The story counter does not always go up: in Nortune waking sets 99, the start of the Baptism sets 105, meeting Hammer sets 102, the Special Pardon sets 108. Hint tools: `fld/hintkit.py`, `fld/dossier.py`.

## Exit, treasure and save heights; flag numbering; exit log (16 Oct 2026, v1.99.0.4)

- **Flag numbers** (`FB flag addr`, `FE0A`/`FE0B flag`): variable byte offset = `flag >> 4`, bit = `flag & 15`. Checked against the treasure table: Blackmoon Forest (room 22) tests `FB 0983` = variable `0x98` (152) bit 3, the same flag its chest sets. `3A var n flags` / `3B` name the variable by byte offset and the bit as `n` (Lahan gifts: `3A C802 0800 40` = variable 712 bit 8).
- **Heights** (`tools/app/exit_heights.js`): each exit's y is the floor under it on the walk layer of its paired arrival spot (the entrance-table record the way back from the destination uses: 7-byte records {x, z, layer, camera, facing}); exits without a way back use the floor under them when every level there agrees within 40 units. Walk triangles with surface bit `0x800000` (blocked) and the room's last layer (camera bounds) are skipped, which matters: counting them made 939 of 1,340 exits look multi-level, without them 205. Result: 1,292 exits with a height (1,175 from arrival spots, 117 single-floor), 48 without; treasure 179 of 239, memory cubes and shops 98 of 116 (single-floor only; script actors carry no usable y). Not yet seen live.
- **Exit log** (Windows DEV, SETTINGS > DEV OPTIONS > EXIT LOG): the app writes the party's last spot (x, z, y, layer) before each room change to `Documents\Xenogears Link\Exit log\exit log.jsonl`, only when the party was walking in the 2 s before (scene warps are left out); a change undone within 3 s writes `{"undo":1}`. The room viewer's Import (or `tools/app/import_exit_log.js`) averages walks through the same door and moves the matching exit. Not yet used live.
- **Variable index** (`tools/app/var_index.js`): rooms whose scripts set (`35`, `36`, `37`, `34`, `A8`, `87`, `3A`/`3B`, `FE0A`/`FE0B`) and check (`02`, `FB`, `84`-`86`) each variable, with bits where the command names one; 207 variables over 730 rooms. Used by the room viewer's snapshot comparison.
- **Route on the handheld (v1.99.0.6)**, measured in Chromium at 6x CPU slow-down with the app's handheld settings: the first route in a room used to stall 58-161 ms (floor graph built in one go) and each recompute took 3-17 ms. Now the graph is built in steps of at most about 5-12 ms after the room appears (numeric edge keys, typed arrays), A* uses a binary heap and typed arrays, the corner path is straightened with the funnel method in one pass, and while the party stays on the found corridor only the straightening is redone (0.1-0.7 ms). A full recompute is 1.4-10 ms. The line's shader compile (about 150-250 ms at 6x on SwiftShader) is moved to room entry by making the line, drawing nothing, while the graph is built.

## Movie program and the ending (16 Oct 2026)

- **Program 6 (movie) is overlay file 40**, first word **8** at `0x8006FAF0` (29,779 bytes decompressed; its debug text: "MOVIE NUMBER", "START FRAME", "MOVIE CD-ROM MODE1/2 DISK", "DISC CHANGE TEST"). Overlay files on disc 1 by first word: 35 = 7 (Battle Arena), 36 = 4 (field), 37 = 5 (world map), 38 = 6 (battle), 39 = menu, 40 = 8 (movie). The app now treats word 8 as a movie (quiet screen with FF).
- **The ending is room 41 at story step 350** (field program, word 4). Checked against a set of ePSXe save states for every cutscene of disc 2 (Jack's "Save States For All Cutscenes", ePSXe .000-.004 files: gzip, "ePSXe" header, main RAM at offset 0x1BA): Deus fight = battle program in room 717 at step 350; Krelian's scene = room 718, step 350; then the ending, both "Ending" states and the last Krelian one, in **room 41** (a 205-byte script that only stages the movies; no script sends the party there by a literal room number), step 350, script variable 4 = 719. No earlier cutscene state is in room 41 (Grahf's sacrifice, Merkava, Deus emerging and Zeboim are rooms 666, 294, 618, 700, 290, 392, 389 at steps 330-340). Script variable 12 counts up through these states (1077, 2836, 3876, 3896). The movie program (word 8) only plays the intro. The app's THE END screen opens in room 41 at step 350 or more. Disc 2's room files are not needed: disc 1 holds every room.

- **Battle actor +0xAC bit 0 ("not drawn") is also set on enemies already fighting** (16 Oct 2026, Jack, PC recomp): in the generator defence after Maria joins (Billy alone vs three White Knights, bank 35 with Citadel 6000 HP and Avalanche 5000 HP; a timer and a total-damage count on screen) all three White Knights are drawn when the battle opens and then flagged by the event. The app (v1.99.0.9) keeps any enemy that was on the field in the battle's first 3 s while it has HP; helpers flagged from the start (Super Aerod, Fis-6's Mechanics) still wait. Checked both ways on the two save states.
