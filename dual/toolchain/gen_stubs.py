import re,sys
def parse(path, api=30):
    funcs, vars_ = [], []
    for line in open(path):
        s=line.strip()
        if not s or s.startswith('#') or s.endswith('{') or s.startswith('}') or s.startswith('global:') or s.startswith('local:'): continue
        m=re.match(r'([A-Za-z_][\w]*)\s*;\s*(#.*)?$', s)
        if not m: continue
        name, tags = m.group(1), (m.group(2) or '').lstrip('#').split()
        archs=[t for t in tags if t in ('arm','arm64','x86','x86_64','riscv64')]
        if archs and 'arm64' not in archs: continue
        if any(t in ('platform-only','apex','llndk','systemapi') for t in tags) and not any(t.startswith('introduced') for t in tags): 
            pass
        intro=[int(t.split('=')[1]) for t in tags if t.startswith('introduced=') and t.split('=')[1].isdigit()]
        if intro and intro[0]>api: continue
        (vars_ if 'var' in tags else funcs).append(name)
    return sorted(set(funcs)), sorted(set(vars_))
path,out=sys.argv[1],sys.argv[2]
f,v=parse(path)
with open(out,'w') as o:
    for n in f: o.write(f'void {n}(void){{}}\n')
    for n in v: o.write(f'char {n}[8];\n')
print(out,len(f),len(v))
