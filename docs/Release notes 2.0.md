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
