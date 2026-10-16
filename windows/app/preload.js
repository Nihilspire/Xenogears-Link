// Gives the page the same window.Native bridge the Android app has (poll / send / focusable).
const { ipcRenderer } = require('electron');
window.Native = {
  platform: 'win32',
  poll(h, p, mode, pages, seq) { ipcRenderer.invoke('ra-poll', h, p, mode, pages, seq).then(r => window.onMem && window.onMem(r)); },
  send(h, p, cmd) { ipcRenderer.send('ra-send', h, p, cmd); },
  focusable(on) {},          // on Windows the window takes focus normally; RetroArch keeps the controller
};
// The player's disc and the folder the room maps are built into (same calls as the Android bridge).
const fs = require('fs'), path = require('path');
const userData = ipcRenderer.sendSync('user-data'), gen = path.join(userData, 'gen');
function discInfo() { try { return JSON.parse(fs.readFileSync(path.join(userData, 'disc.json'), 'utf8')); } catch (e) { return null; } }
function genPath(p) { if (!p || p.includes('..') || path.isAbsolute(p)) throw new Error('bad path'); return path.join(gen, p); }
let fd = null, fdFor = '';
Object.assign(window.Native, {
  discPick() { ipcRenderer.invoke('disc-pick').then(r => { fd && fs.closeSync(fd); fd = null; window.onDiscPicked && window.onDiscPicked(r ? r.name : null, r ? r.size : 0); }); },
  discName() { const d = discInfo(); return d ? path.basename(d.path) : ''; },
  discSize() { const d = discInfo(); try { return d ? fs.statSync(d.path).size : 0; } catch (e) { return 0; } },
  discRead(offset, length) {
    try {
      const d = discInfo(); if (!d) return 'ERR:no disc chosen';
      if (!fd || fdFor !== d.path) { if (fd) fs.closeSync(fd); fd = fs.openSync(d.path, 'r'); fdFor = d.path; }
      const b = Buffer.alloc(length), n = fs.readSync(fd, b, 0, length, offset);
      return new Uint8Array(b.buffer, b.byteOffset, n);   // the page takes bytes or base64
    } catch (e) { fd = null; return 'ERR:' + e.message; }
  },
  genDir() { fs.mkdirSync(gen, { recursive: true }); return gen; },
  genWrite(p, b64) { try { const f = genPath(p); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f + '.part', Buffer.from(b64, 'base64')); fs.renameSync(f + '.part', f); return 'ok'; } catch (e) { return 'ERR:' + e.message; } },
  genHas(p) { try { return fs.statSync(genPath(p)).isFile(); } catch (e) { return false; } },
  genRead(p) { try { return fs.readFileSync(genPath(p), 'utf8'); } catch (e) { return ''; } },
  genClear() { try { fs.rmSync(gen, { recursive: true, force: true }); } catch (e) {} },
  // DEV story snapshots (Windows only): text + JSON files in Documents\Xenogears Link\Story snapshots
  snapDir() { return path.join(ipcRenderer.sendSync('docs-dir'), 'Xenogears Link', 'Story snapshots'); },
  snapSave(base, txt, json) {
    try { const d = window.Native.snapDir(); fs.mkdirSync(d, { recursive: true }); const b = path.join(d, String(base).replace(/[<>:"/\\|?*]/g, '-'));
      fs.writeFileSync(b + '.txt', txt); fs.writeFileSync(b + '.json', json); return b + '.txt'; } catch (e) { return 'ERR:' + e.message; } },
  // DEV exit log (Windows only): one JSON line per room change, Documents\Xenogears Link\Exit log\exit log.jsonl
  exitLogDir() { return path.join(ipcRenderer.sendSync('docs-dir'), 'Xenogears Link', 'Exit log'); },
  exitLog(line) { try { const d = window.Native.exitLogDir(); fs.mkdirSync(d, { recursive: true }); fs.appendFileSync(path.join(d, 'exit log.jsonl'), String(line) + '\r\n'); return 'ok'; } catch (e) { return 'ERR:' + e.message; } },
  exitLogOpen() { const d = window.Native.exitLogDir(); try { fs.mkdirSync(d, { recursive: true }); } catch (e) {} require('electron').shell.openPath(d); },
  snapOpen() { const d = window.Native.snapDir(); try { fs.mkdirSync(d, { recursive: true }); } catch (e) {} require('electron').shell.openPath(d); },
});
