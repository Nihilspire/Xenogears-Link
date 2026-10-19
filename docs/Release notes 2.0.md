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
