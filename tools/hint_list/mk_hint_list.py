"""Builds the Story Hints page (one interactive HTML file) from the app's own tables in app/www:
chapters.js (story step -> chapter), hints.js (HNOTE text, HPATH rooms and green spots, HINTS where the scripts set the step),
hsplit.js (later parts of a hint), rooms.js and areas.js (names).
  python3 mk_hint_list.py [out.html]      (default: xenogears-story-hints.html next to this script)
The page applies the app's rules: the hint shown at story step s is the first hint step above s (hintNext), and page n of a hint
shows sentence n of its text and room n of its path, the last one carrying on when either runs out (showHint)."""
import json, os, re, subprocess, sys, datetime
H = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(H, '..', '..', 'app', 'www')
def load(fn):
    t = open(os.path.join(W, fn), encoding='utf-8').read(); o = {}
    for m in re.finditer(r'window\.(\w+)\s*=\s*([\[{].*?[\]}]);?\s*$', t, re.M): o[m.group(1)] = json.loads(m.group(2))
    return o
C = load('chapters.js')['CHAPTERS']; Hn = load('hints.js'); SP = load('hsplit.js').get('HSPLIT', {})
ROOMS = load('rooms.js')['ROOMS']; AREAS = load('areas.js')['AREAS']
def area(f):
    for a in AREAS:
        if a[0] <= f <= a[1]: return a[2]
    return ''
def parts(t):   # index.html hintParts: split at each full stop followed by a space
    out, cur = [], ''
    for x in re.split(r'(\.\s+)', t):
        cur += x
        if re.search(r'\.\s+$', x): out.append(cur.strip()); cur = ''
    if cur.strip(): out.append(cur.strip())
    return out
def pages(text, path):   # showHint: page n = sentence n and room n, the last of either carrying on
    s = parts(text); n = max(len(s), len(path), 1)
    return [[s[min(i, len(s) - 1)] if s else '', path[min(i, len(path) - 1)][0] if path else None,
             path[min(i, len(path) - 1)][1] if path else [], i < len(s), i < len(path)] for i in range(n)]
hints, used = [], set()
for k in sorted(map(int, Hn['HINTS'])):
    s = str(k); note = Hn['HNOTE'].get(s, ''); unchecked = note.startswith('?'); text = note[1:] if unchecked else note
    path = Hn['HPATH'].get(s) or []
    for r in path: used.add(r[0])
    for r in Hn['HINTS'][s]: used.add(r[0])
    splits = []
    for sp in SP.get(s, []):
        e = {'when': sp[0], 'dropS': sp[1], 'dropP': sp[2]}
        if len(sp) > 3:
            t2 = sp[3]; e['unchecked'] = t2.startswith('?'); e['text'] = t2[1:] if e['unchecked'] else t2; e['path'] = sp[4] if len(sp) > 4 else []
            for r in e['path']: used.add(r[0])
            e['pages'] = pages(e['text'], e['path'])
        splits.append(e)
    hints.append({'k': k, 'text': text, 'unchecked': unchecked, 'pages': pages(text, path),
                  'set': [[r[0], r[1]] + ([r[2], r[3]] if len(r) > 3 else []) for r in Hn['HINTS'][s]], 'splits': splits})
rooms = {f: [ROOMS.get(str(f)) or '', area(f)] for f in sorted(used) if f >= 0}
try:
    rev = subprocess.run(['git', '-C', H, 'log', '-1', '--format=%h %cs', '--', '../../app/www'], capture_output=True, text=True).stdout.strip()
except Exception: rev = ''
D = {'chapters': C, 'hints': hints, 'rooms': rooms, 'steps': 354, 'source': rev, 'built': datetime.date.today().isoformat()}
src = open(os.path.join(H, 'hint_list_src.html'), encoding='utf-8').read()
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, 'xenogears-story-hints.html')
js = json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
open(out, 'w', encoding='utf-8').write(src.replace('/*HINT_DATA*/null', js))
np = sum(len(h['pages']) for h in hints); ns = sum(1 for h in hints for p in h['pages'] if p[4] and p[2])
print('hints', len(hints), 'pages', np, 'pages with a spot', ns, 'unchecked', sum(h['unchecked'] for h in hints), 'rooms', len(rooms), '->', out, os.path.getsize(out), 'bytes')
