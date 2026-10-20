# Xenogears Link 2.0.0.11: playtest targets

Everything below works in the test setup (all 228 save states run without errors), but none of it has been seen in real play yet. If anything looks off, send a screenshot and, if you can, a save state.

## 1. New since 2.0.0.1: check these first

| Feature | Where to check | What should happen |
|---|---|---|
| **Follow Path** (2.0.0.2) | Any long hint step: 123, 132, 158, 228 | The hint page and guide line move on by themselves as you walk room to room. The top bar flashes "HINT 3/7", and the map's ◀ 3/7 ▶ buttons work. |
| **Missables** (2.0.0.3) | Citan's house (Midori's Ring), Mountain Path (Spider, Bird Egg), Lahan, Thames, orphanage | An orange ring on the map and a LOST: line in the treasure list. The ring disappears once taken. |
| **Room log** (2.0.0.4) | SETTINGS › DEV › ROOM LOG › VIEW after a few doors | OUT and IN show in green for doors the app knows. On Android, SHARE opens the share sheet. |
| **RPS helper** (2.0.0.5, DEV) | Lahan, the rock-paper-scissors man | The hand it shows once the menu is up matches what he throws. 5 wins in a row gives the badge. |
| **Speed helper** (2.0.0.6, DEV) | Kanna in the Snowfield hideout, or the Thames players | "Your hand" really is yours, the card values match the screen, and L/R match the piles. |
| **Walk-away talk** (2.0.0.7) | Any town | Townsfolk and shopkeepers leave the map up; cutscenes still dim the screen. |
| **Disc 1 / THE END screens** (2.0.0.8) | The disc change at Taura's, and the ending | Tiles, bars and portraits look right, and the bestiary count is not 0. |
| **Hidden pickup spots** (2.0.0.9) | 120 G stash at Citan's (upper walkway, west of the top door); Thames prizes; Shevat rocks; Shevat secret room | The dot is where pressing X works. |
| **App tour** (2.0.0.10) | First link after updating, or SETTINGS › APP TOUR | The gold frame lands on each part, and the cards are readable at your size setting. |
| **Welcome back** (2.0.0.10) | Link after 8+ hours away | One card with the chapter, the room, the party and the next hint. |
| **Boss cards on tap** (2.0.0.11) | Any boss | No pop-up at the start of the fight, and the boss row says TIP. Tap it for the card. Brigandier says "Just hit him." |
| **Pictures** (2.0.0.11) | Brigandier, Marlute (battle and bestiary) | The Gear shows properly, not as a sliver or a line. |

## 2. Hint pages that may point at the wrong room

These steps have a different number of hint sentences than rooms. Page through each and check that the green spot and line match the text:

87, 93, 138, 145, 160, 166, 171, 174, 175, 198, 205, 228, 234, 281, 303

(A step with several sentences but only one room is fine, so those are not listed.)

## 3. Spots that are best guesses

- **Midori's Ring:** the dot is behind Citan's house, taken from an unused trigger area. Check that it's on the flower bed.
- **Super Aerod:** its "wait until called in" rule comes from one save state.
- **Kelvena's tip:** it never shows, because no enemy is named Kelvena.

## 4. Known gaps (no fix expected from play)

- **Rooms with no doors in the data**, where the guide line can't route through: Thames 316 and 319, the Shevat escape route (444–450), Solaris 522, 537, 594 and 607, Sargasso 504, and Taura's hangar 612.
- **Unnamed hint rooms:** 1–4 (Lahan), 26, 251.
- **Missables not tracked:** the Wedding Dress, the Trader Card, the Mermaid Ring trade, and shop-only stock.

## 5. The two sheets

- **Room list** (`Xenogears room list 2.0.0.11.xlsx`): every room with its doors, treasure, missables, saves and shops, and the hint steps that use it. Mark **Walked** and add **Notes** as you go; the filter row helps you jump to an area. *Doors without a spot* and *Spots missing* are the numbers worth checking in play.
- **Hint list** (`Xenogears story hints 2.0.0.11.xlsx`): your 1.99.0.22 sheet updated with the current hints. Your Checked and notes columns are kept. No hint has changed since that sheet, so the *Changed since 1.99.0.22* column is empty for now; it will mark the steps that change after this round. The hidden-spot fixes are in the room list, not the hints.
