// Xenogears Link for Windows: the Android app's page in a window, reading RetroArch over UDP network commands.
const { app, BrowserWindow, ipcMain, Menu, screen, dialog } = require('electron');
const path = require('path'), fs = require('fs');
const Link = require('./link');

const link = new Link();
let win = null;
const stateFile = () => path.join(app.getPath('userData'), 'window.json');
function loadState() { try { return JSON.parse(fs.readFileSync(stateFile(), 'utf8')); } catch (e) { return {}; } }
function saveState() {
  if (!win || win.isDestroyed()) return;
  try { fs.writeFileSync(stateFile(), JSON.stringify({ bounds: win.getNormalBounds(), max: win.isMaximized(), top: win.isAlwaysOnTop() })); } catch (e) {}
}
function onScreen(b) {
  return b && screen.getAllDisplays().some(d => { const a = d.workArea; return b.x < a.x + a.width - 40 && b.x + b.width > a.x + 40 && b.y >= a.y - 10 && b.y < a.y + a.height - 40; });
}

function create() {
  const st = loadState(), b = onScreen(st.bounds) ? st.bounds : { width: 960, height: 720 };
  win = new BrowserWindow({
    ...b, minWidth: 480, minHeight: 360, title: 'Xenogears Link', backgroundColor: '#000000', alwaysOnTop: !!st.top,
    icon: path.join(__dirname, 'icon.png'), autoHideMenuBar: true, show: false,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: false, nodeIntegration: false, sandbox: false, spellcheck: false },
  });
  Menu.setApplicationMenu(null);
  if (st.max) win.maximize();
  win.loadFile(path.join(__dirname, 'www', 'index.html'));
  const shot = process.env.XG_SHOT;   // test hook: capture the window after a few seconds, then quit
  if (shot) setTimeout(() => win.webContents.capturePage().then(img => { fs.writeFileSync(shot, img.toPNG()); app.quit(); }), 6000);
  win.once('ready-to-show', () => win.show());
  // F11 full screen (for a second monitor), F12 dev tools, Ctrl+T always on top
  win.webContents.on('before-input-event', (e, i) => {
    if (i.type !== 'keyDown') return;
    if (i.key === 'F11') { win.setFullScreen(!win.isFullScreen()); e.preventDefault(); }
    else if (i.key === 'F12') { win.webContents.toggleDevTools(); e.preventDefault(); }
    else if (i.control && i.key.toLowerCase() === 't') { win.setAlwaysOnTop(!win.isAlwaysOnTop()); saveState(); e.preventDefault(); }
  });
  win.on('close', saveState);
  win.on('closed', () => { win = null; link.close(); });
}

// the player's disc image (picked once, remembered) and the folder the page builds the room maps into
const discFile = () => path.join(app.getPath('userData'), 'disc.json');
ipcMain.on('user-data', e => { e.returnValue = app.getPath('userData'); });
ipcMain.on('docs-dir', e => { e.returnValue = app.getPath('documents'); });
ipcMain.handle('disc-pick', async () => {
  const r = await dialog.showOpenDialog(win, { title: 'Choose your Xenogears disc 1 image', properties: ['openFile'],
    filters: [{ name: 'Disc image (.chd, .bin, .iso)', extensions: ['chd', 'bin', 'iso', 'img'] }, { name: 'All files', extensions: ['*'] }] });
  if (r.canceled || !r.filePaths.length) return null;
  const p = r.filePaths[0], size = fs.statSync(p).size;
  fs.writeFileSync(discFile(), JSON.stringify({ path: p, size: size }));
  return { name: path.basename(p), size: size };
});
ipcMain.handle('ra-poll', (e, h, p, mode, pages, seq) => link.poll(String(h || '127.0.0.1'), p | 0 || 55355, String(mode || 'm80'), String(pages || ''), seq | 0));
ipcMain.on('ra-send', (e, h, p, cmd) => link.send(String(h || '127.0.0.1'), p | 0 || 55355, String(cmd)));

if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
  app.whenReady().then(create);
  app.on('window-all-closed', () => app.quit());
}
