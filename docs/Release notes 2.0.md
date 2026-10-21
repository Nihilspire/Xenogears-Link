# Xenogears Link 2.0 (18 Oct 2026)

A second screen for Xenogears (PS1): it reads the game from RetroArch (Android, Windows) or XenogearsRecomp while you play.

## New since 1.99
- **Start screen**: what each part of the app does, and every main switch, including the new ones.
- **Journal tab** (LOG on 4:3 screens): story progress with a chapter log (play time and level when each chapter began), and a bestiary of every enemy fought.
- **Boss cards**: pop up at boss fights with HP, rewards, drops and a short tip (80 tips, picked by story step for repeat bosses).
- **Shop advisor**: each piece of gear in a shop shows what it adds over what the party has on.
- **Guide line**: a green line to the next hint spot or the door that leads there, on the 2D map as well as the 3D map; ends on the floor.
- **THE END** summary screen at the credits; movie mode.
- **Enemy list**: the real "not drawn yet" rule (helpers called in mid-fight wait until they appear), enemies keep their names when they change mid-fight (Rankar Dragon).
- **Story hints**: Jack's edited hint sheet (62 steps), the hint pop-up keeps the last page read, step 38/39 workshop page, step 219 room.
- **Maps**: doors, chests, gifts, saves and shops at their floor height in 3D; six more entrances; 73 room names added or corrected.
- **3D map and EYE (experimental)**: smooth camera, sky and backdrops, lighter route line on the handheld.

## 2.0.0.2

- **Follow the path** (SETTINGS > HINTS, on by default): the story hint moves to its next page by itself, so the guide line points on to the next room without opening the hint.
  - A page with no green spot is done when you walk into its room.
  - A page with a spot is done after a talk or scene near the spot, or when you have been at the spot and leave the room.
  - Walking into a room that one of the next three pages names jumps straight to that page.
  - A page picked by hand is kept until you change room.
- The top bar flashes HINT 3/7 for a moment when the page moves.
- The room map has a small < 3/7 > in the corner to change the page without opening the hint.

## 2.0.0.3

- **Missables on the map.** 58 pickups that can be lost for good are marked: an orange ring on the map while not yet taken, the name in orange in the treasure list, and a LOST: line saying when it goes (for example "Leaving Lahan").
- New pickups the treasure list did not have: Midori's Ring (Outside Citan's house), the Spider (Mountain Path) and the Shevat secret room (Power Crisis, Yamato Belt and 12 more).

## 2.0.0.4

- **Room log** (SETTINGS > DEV OPTIONS, was the Windows exit log): like the PC recomp's room exporter, every room change records where you left the old room and where you arrived in the new one, with height and floor layer.
  - Windows writes Documents\Xenogears Link\Exit log\exit log.jsonl (FOLDER opens it).
  - Android writes Android/data/com.dualscreen.xenogears/files/Room log/room log.jsonl; SHARE sends it.
  - VIEW checks the last 14 against the app's door data: OUT = distance from where you left to the door, IN = distance from where you arrived to the door back. Green is close, orange is a bit off, red (or NONE) means the door data is wrong or missing.

## 2.0.0.5

- **RPS helper** (SETTINGS > DEV OPTIONS, off by default): while you talk to the rock-paper-scissors man in Lahan, the screen shows his hand (rolled just before the hand menu opens) and the pick that beats it, your wins in a row out of 5, and when the badge is ready. If the winning pick would be the same hand four times running (a forced loss in his script) it tells you to draw instead.

## 2.0.0.6

- **Speed helper** (SETTINGS > DEV OPTIONS, off by default): during a game of Speed (Kanna in the Snowfield hideout, or the Thames players) the screen shows the two pile cards, your hand with the cards that can be played now lit and marked L or R, your next 6 cards and how many are left, the same for your opponent, and against Kanna your wins in a row out of 5 (five gives the Elly Jr. Doll).

## 2.0.0.7

- **Walk-away talk keeps the screen.** Only text shown while the game has locked you (cutscenes and story talks) switches the app to its quiet title screen. Ordinary chatter you can walk away from (townsfolk, shopkeepers) now leaves the map and tabs up.

## 2.0.0.8

- **Disc 1 and THE END screens redone.** The logo with the play time and gold (THE END splits the time by disc), a tile each for treasure, missables, bestiary and deathblows with counts, bars and percentages, and the party as portrait cards with levels. Disc 1 counts cover disc 1 rooms only. The screens now scroll, work in portrait, and Citan is no longer listed twice on the disc 1 screen.

## 2.0.0.9

- **15 hidden pickups now have a spot on the map**, among them the 120 G "secret stash" outside Citan's house, the Thames Speed prizes and the Shevat rocks. These are invisible objects that the game places with a command the treasure scan did not read before; they also get their floor height for the 3D map.

## 2.0.0.10

- **App tour.** The first time the app links to the game it walks you round the screen in ten short cards (chapter name and hints, play time, settings, each tab, FF, and what happens in fights and cutscenes), framing each part in gold. Replay it from SETTINGS > GENERAL > APP TOUR.
- **Welcome back.** When you link again after 8 hours or more, one card shows how long you were away, the chapter, where you are, play time, your party and the next hint, with SHOW THE HINT.

## 2.0.0.11

- **Boss cards only open when tapped.** The boss's row shows TIP; tap any enemy for its card (HP, tip, rewards, drops).
- Brigandier (Bart's first fight): tip "Just hit him."
- Brigandier's picture fixed (two long hanging cables shrank the gear to a sliver); Marlute's picture is drawn from above (it is a flat model and showed as a line).

## 2.0.0.12

- **The tour and welcome-back card wait for play.** They used to open as soon as the app linked, which could be the title screen or a dimmed cutscene. Now they wait until you are free to walk on the map or world map (no talk, cutscene, battle, shop or menu) for 3 seconds.
- Hint step 57 (Bart's Hideout): follow Maison, visit the planning room, then talk to Bart at the dock, with a spot in each of the three rooms.

## 2.0.0.14 (polish)

- **Smoother screens.** The main area fades in when the screen changes (map, fight, cutscene, tab). In fights, HP bars leave a pale trail where they were after a hit, which slides down after a moment.
- **Font: < > [ ] =** added, so tab brackets like [PROGRESS] and arrows show; the comma has a tail now, so it no longer looks like a full stop.
- **Commas in big numbers:** gold, prices, EXP and rewards (1,501,802 G).
- **No link help.** If the game does not answer at start, or the link drops for more than 3 seconds, a card lists what to check (game running, Network Commands, port; recomp Link on) with SETTINGS and TRY NOW.
- **Settings tidied.** Each group folds when you tap its heading. GENERAL has RESET TO DEFAULTS (keeps the link, journal and bestiary). DEVELOPER is hidden until DEV OPTIONS is on: tap the version line at the bottom five times.
- **Empty screens** (no party, no items, a shop without a list, no deathblows yet, a fight still loading, the Battle Arena waiting) show an icon and a line on what fills them.
- **Android:** a round launcher icon (Fei on the menu blue), and the title logo while the app starts instead of a black screen.

## 2.0.0.15

- **Guide line fix: a tapped door no longer follows you into the next room.** The app remembered a tapped door by its place in the room's list, so in the next room the line went to whichever door had that place (Jack: in Lahan it pointed at the RPS Maniac's house instead of the Mountain Path). A tapped door now only counts in the room it was tapped in.
- **Lahan to the Mountain Path:** Lahan (rooms 1 and 2) had no door to the Mountain Path in the data, so the line had nowhere to go for "Climb the Mountain Path" and "Head back down". Added at the spot where you arrive from the path.

## 2.0.0.16

- **Jack's room viewer edits imported (21 Oct).** 19 hint steps: new or moved spots (Mountain Path page for Citan's yard, the forest, the Dazil workshop/bar/rental shop, the sinking ship and crane, the cave sensors and Bal, the excavation exit, the docks, the mechanic, the tournament, the mountain top, Goliath Factory pages), a world-map spot for step 27, and text for steps 56 and 84. Doors in 21 rooms: the Aveh transport, the Stalactite Cave, Bart's hideout, Nisan, Bledavik streets, outskirts and the rooms off them, Fatima Castle and the bottom of the mountain. Two chest spots (rooms 58 and 65).
- Step 58 (mechanic) uses Jack's spot.

## 2.0.0.17

- **3D map froze in rooms 164 and 165** (Gebler airship corridor, Elly's room). One of their sprite sheets is stored in a different layout; the app read its picture count as about 3.7 billion and kept looping. Bad counts are now skipped (the room viewer had the same freeze and the same fix).
