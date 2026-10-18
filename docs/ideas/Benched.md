# Benched ideas

## Achievements (benched 17 Oct 2026, Jack: revisit once bug testing is solid)
Mockup: three screenshots (list, list with progress bars, unlock pop-up), drawn in the app with the game font by
`achievements_mock.py` (playwright, test page in /home/claude/npc/t). Plan if picked up:
- 30-40 achievements: story steps/rooms, Disc 1 end and THE END, treasure flags (all / per area), deathblows, levels, gold,
  party joined, named boss wins, biggest hit, Battle Arena wins, play-time challenges.
- Harder: "no items used" (item count diff per fight), rooms visited (app keeps a list), Fis-6 before the Mechanics (new enemy rule).
- Saves have no ID, so unlocks live in the app (localStorage), never re-lock, and only unlock while linked; a "check now" pass
  could grant what the current save already qualifies for.
- List behind a button on the Status tab; pop-up window at the top of any screen.

## Missables page (removed from the Journal 18 Oct 2026, Jack: needs too much play-testing)
Was in 1.99.0.16-1.99.0.19: chests not yet opened (TREASURE flags, gifts left out) in places assumed to close: Lahan rooms 1-14
before step 21, rooms 1-505 before the point of no return (step 210), Solaris rooms 509-611 before step 243; grouped by area, tap
for items and rooms. The closing points were guesses and need checking in play. Code: git show 1.99.0.19 (journalView, missables, missPop).
