// Puts the Xenogears Link icon and version text into the Windows exe without Wine (pure-JS PE resource editing).
const fs = require('fs'), ResEdit = require('resedit'), pngToIco = require('png-to-ico');
const [exe, png, ver] = process.argv.slice(2);
(async () => {
  const ico = await pngToIco(png);
  fs.writeFileSync(require('path').join(require('path').dirname(png), 'icon.ico'), ico);
  const data = fs.readFileSync(exe);
  const pe = ResEdit.NtExecutable.from(data, { ignoreCert: true });
  const res = ResEdit.NtExecutableResource.from(pe);
  const iconFile = ResEdit.Data.IconFile.from(ico);
  const groups = ResEdit.Resource.IconGroupEntry.fromEntries(res.entries);
  const gid = groups.length ? groups[0].id : 1, lang = groups.length ? groups[0].lang : 1033;
  ResEdit.Resource.IconGroupEntry.replaceIconsForResource(res.entries, gid, lang, iconFile.icons.map(i => i.data));
  const vi = ResEdit.Resource.VersionInfo.fromEntries(res.entries)[0];
  const [a, b, c, d] = ver.split('.').map(Number);   // up to four parts: 1.99.0.1
  vi.setFileVersion(a, b || 0, c || 0, d || 0, 1033); vi.setProductVersion(a, b || 0, c || 0, d || 0, 1033);
  vi.setStringValues({ lang: 1033, codepage: 1200 }, { FileDescription: 'Xenogears Link', ProductName: 'Xenogears Link', OriginalFilename: 'Xenogears Link.exe', InternalName: 'Xenogears Link', CompanyName: 'Dual Screen', FileVersion: ver, ProductVersion: ver, LegalCopyright: '' });
  vi.outputToResourceEntries(res.entries);
  res.outputResource(pe);
  fs.writeFileSync(exe, Buffer.from(pe.generate()));
  console.log('icon + version set');
})().catch(e => { console.error(e); process.exit(1); });
