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
