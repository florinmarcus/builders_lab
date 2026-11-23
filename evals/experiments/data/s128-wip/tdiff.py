import json,glob,sys
from pathlib import Path
B='/home/user/builders_lab/corpus/parsed'
for f in sorted(glob.glob(B+'/_dev/*/*.json')):
    rel=f[len(B)+6:]
    new=json.load(open(f)); old=json.load(open(B+'/'+rel))
    os_={s['id']:s for s in old['sections']}; ns={s['id']:s for s in new['sections']}
    out=[]
    for i in ns:
        if i not in os_: out.append(f"  + {i} {ns[i]['type']} {ns[i].get('spans')}")
        elif ns[i]!=os_[i]:
            a,b=os_[i],ns[i]
            ks=[k for k in set(a)|set(b) if a.get(k)!=b.get(k) and k not in ('page_images','image_path')]
            if ks: out.append(f"  ~ {i} {a['type']} {ks} {a.get('spans')} -> {b.get('spans')}")
    for i in os_:
        if i not in ns: out.append(f"  - {i} {os_[i]['type']} {os_[i].get('spans')}")
    print(rel[:110]); print('\n'.join(out))
