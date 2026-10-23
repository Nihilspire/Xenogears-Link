# Setting up Xenogears Link work on your own PC (Claude Code)

Everything was built and tested on Linux, and the scripts are bash and Python with Linux paths. The least-friction setup is
**WSL (Ubuntu) on Windows**, with the work folder at `/home/claude` so every path in the scripts keeps working unchanged.

## 1. WSL and the work folder
In PowerShell (as admin): `wsl --install -d Ubuntu`, restart, open Ubuntu and make your user. Then in Ubuntu:
```bash
sudo mkdir -p /home/claude && sudo chown $USER:$USER /home/claude
cd /home/claude
unzip "/mnt/c/Users/Jackson/Desktop/Claude/Xenogears/Xenogears Link handoff 2026-10-23.zip"   # after joining the parts
# the scripts use /tmp/claude-0 as scratch; point it at the saved scratch folder on every start
echo '[ -e /tmp/claude-0 ] || ln -s /home/claude/scratch /tmp/claude-0' >> ~/.bashrc && source ~/.bashrc
```
The handoff zip mirrors the cloud workspace's `/home/claude`:
| Folder | What it is |
|---|---|
| `xenogears-link/` | the git repo (app, Android, Windows, tools, docs), with history; same as GitHub plus the files built from your disc |
| `xg/fld/` | field-script toolkit (dialogue, story-step tests, actor positions, hint evidence); `xg/v/www` must link to the repo's `app/www` |
| `npc/` | the test page kit and the 228 save-state RAM dumps (`npc/bins/st`) used by the sweep |
| `pst/`, `fis/`, `st/` | more RAM dumps from your save states (Fis-6, Yggdrasil, Lahan, etc.) |
| `scratch/` | the working scripts from the cloud scratch folder: spot check, screenshots, probes, gap checks, sheet builders, and their data (exit check, hint paths) |
| `ach/`, `work/`, `hints/` | achievements mock-up, odds and ends, the hint-edits sheet data |

Then put your disc where the scripts look for it:
```bash
mkdir -p /home/claude/disc && cp "/mnt/c/path/to/Xenogears disc 1.bin" /home/claude/disc/Xenogears_PW_CD1.bin
export XG_DISC=/home/claude/disc/Xenogears_PW_CD1.bin    # also add this line to ~/.bashrc
mkdir -p /home/claude/xg/v && ln -sfn /home/claude/xenogears-link/app/www /home/claude/xg/v/www
```

## 2. Tools
```bash
sudo apt update
sudo apt install -y git zip unzip curl python3 python3-pip openjdk-17-jdk-headless \
  aapt zipalign apksigner dalvik-exchange android-sdk-platform-23
# Node 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs
# Python libraries used by the tools and tests
pip3 install --break-system-packages openpyxl playwright pypdfium2 numpy pillow
python3 -m playwright install --with-deps chromium
# the test scripts launch Chromium from /opt/pw-browsers/chromium
sudo mkdir -p /opt/pw-browsers && sudo ln -sf "$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | tail -1)" /opt/pw-browsers/chromium
# three.js for the room viewer tests (they load it from here instead of the CDN)
mkdir -p /home/claude/rv/npm && cd /home/claude/rv/npm && npm i three@0.147.0
# Windows build dependencies
cd /home/claude/xenogears-link/windows && npm i
# Claude Code
npm i -g @anthropic-ai/claude-code
```
Git: `cd /home/claude/xenogears-link && git remote -v` should show `github.com/Nihilspire/Xenogears-Link`. Sign in once with
`gh auth login` (`sudo apt install gh`) or a personal access token so pushes work.

## 3. Signing key
`android/keystore.jks` is in the handoff zip (it is never committed). Keep a copy in your Xenogears folder as well. Builds need its
password in the environment for that one command: `XG_KS_PASS='your password' ./build.sh 2.0.0.23` (or `read -s XG_KS_PASS; export XG_KS_PASS`).

## 4. Check it all works
```bash
cd /home/claude/xenogears-link
bash /home/claude/npc/mkt.sh                                   # test page
for i in 0 1 2 3; do (cd /home/claude/npc && python3 sweep.py $i 4) & done; wait; python3 /home/claude/scratch/swchk.py   # expect: 228 0
(cd tools/room_viewer && node mkdata.js && python3 mk.py)       # room viewer
(cd android && XG_KS_PASS=... ./build.sh 2.0.0.23)              # APK
windows/build.sh 2.0.0.23                                       # Windows folder zip
```
Then start Claude Code in the repo (`cd /home/claude/xenogears-link && claude`). It reads `CLAUDE.md` first.

## 5. Live testing (new on your PC)
With RetroArch (or the recomp) running on the same PC, Claude Code can read the game's memory directly over UDP 127.0.0.1:55355
(`READ_CORE_MEMORY 0x8006FAF0 4` and so on). From WSL, Windows' localhost is reachable when WSL networking is in mirrored mode:
add `[wsl2]\nnetworkingMode=mirrored` to `C:\Users\Jackson\.wslconfig` and run `wsl --shutdown` once.

## Handy checks
- Hint pages with no way through doors: `node /home/claude/scratch/gaps_check.js` (lists step, from room, to room, door counts).
- Spot check after hint edits: `node /home/claude/scratch/export_hpath.js`, then
  `cd /home/claude/xg/fld && python3 /home/claude/scratch/spotcheck.py` and copy `spotcheck.json` into `tools/room_viewer/data/`.
- Door pairs / arrival spots after exit edits: `node tools/app/exit_check.js` (writes `/tmp/claude-0/exitcheck.json`, which `mkdata.js` reads).
