# Xenogears Dual, in the Xenogears Link repo

A snapshot of Xenogears Dual 0.25 (one Android APK: the game on one screen, Link on the other, or both on one). This repo is public, so it has no game-derived files and no signing key, and **it won't build from here alone**. To build it, add:

| Put | Where | From |
|---|---|---|
| Link's data files | `app/assets/link/` | `../app/www/*`, all but `index.html`, which is Dual's own here |
| Link's built files (`font.js`, `bundled.js`, `img/`, `world/`, `maps/`, `plan/`, `spr/`) | `app/assets/link/` | Link's disc build, see `../docs/SETUP.md` |
| `xgfont.js` | `app/assets/menu/` | The game's font, built by you |
| `icon.png`, `icon-512.png` | `app/res/drawable/`, `app/` | Your own icon |
| Your own signing key | `app/signing/xenogears.jks` | Made for you on the first build, using `XG_DUAL_KS_PASS` |
| Save states and a card for the tests | `tests/data/` | Your own, from your own disc |

`setup.sh` fetches the core's sources and makes the toolchain. No game data ships with any of this: you supply your own discs.

---

# Xenogears Dual

Xenogears + Xenogears Link in one Android APK (pcsx_rearmed core, Link companion on the second screen).
Start with `CLAUDE.md` (build, test, working agreements, pitfalls), then `docs/`.

- Latest build: `releases/Xenogears Dual 0.17.apk` (not inside the zip; it was sent separately)
- First time in Claude Code: `git init && git add -A && git commit -m "Xenogears Dual 0.17"` if there's no .git yet
- On Windows, use WSL (Ubuntu 24.04): the toolchain scripts are bash and use Linux packages.
- `app/signing/xenogears.jks` is the signing key for the installed app; keep this repo private.
- GPL: pcsx_rearmed is GPL-2.0; if you share the APK, share this source with it.
