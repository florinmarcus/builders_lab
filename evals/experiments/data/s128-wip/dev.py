"""dev.py [--only SRC,...] [--out DIR] [--write]: rebuild parse_pdf and parse_guide trees from cached reads;
list trees that differ from corpus/parsed. --write also writes changed trees (and renders images) into corpus/parsed."""
import sys, json, pickle, glob, hashlib, argparse, importlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/builders_lab')
import yaml
from system.rag.corpus import CORPUS_DIR, parser_for
from system.rag.fixes import load_fixes
import os
CACHE = Path(os.environ.get('DEV_CACHE', '/tmp/claude-0/-home-user-builders-lab/279fdd82-bd2a-51a0-938e-fb1a2ec03a4d/scratchpad/s128/cache'))
CACHE.mkdir(exist_ok=True)
ROOT = CORPUS_DIR.parent

def jobs(only=None):
    d = yaml.safe_load((CORPUS_DIR / 'sources.yaml').read_text())
    out = []
    for s in d['sources']:
        mods = [(s.get('parser') or {}).get('module'), *((s.get('parser') or {}).get('files') or {})]
        if not ({'parse_pdf', 'parse_guide'} & set(mods)): continue
        if only and s['id'] not in only: continue
        for p in sorted(glob.glob(f"{CORPUS_DIR}/versions/{s['id']}/*.json")):
            r = json.load(open(p))
            if r['valid_to'] is not None or r['media_type'] != 'application/pdf': continue
            m = parser_for(s, r['version_id'])
            if m in (None, 'parse_pdf', 'parse_guide'):
                out.append((s, r, m or 'parse_pdf'))
    return out

def strip(t):
    t = json.loads(json.dumps(t))
    for x in t.get('sections', []):
        x.pop('page_images', None); x.pop('image_path', None)
    return t

def one(arg):
    s, r, m, write = arg
    import system.rag.parse_pdf as P, system.rag.parse_guide as G
    raw = ROOT / r['raw_path']
    if not raw.exists(): return (s['id'], r['version_id'], 'missing')
    cp = CACHE / f"{m}-{r['sha256'][:20]}.pkl"
    if cp.exists():
        doc = pickle.loads(cp.read_bytes())
    else:
        doc = P.read_guidance(raw) if m == 'parse_pdf' else G.read_guide(raw)
        cp.write_bytes(pickle.dumps(doc))
    fixes = load_fixes(s['id'])
    if m == 'parse_pdf':
        tree = P.build_tree(doc, {**r, 'title': s['title']}, fixes=fixes)
    else:
        tree = G.build_tree(doc, {**r, 'title': r.get('part_title') or s['id']}, fixes=fixes)
    out = CORPUS_DIR / 'parsed' / s['id'] / f"{r['version_id']}.json"
    old = out.read_text() if out.exists() else None
    if write:
        P.render_images(raw, tree, out.parent / r['version_id'])
        txt = json.dumps(tree, ensure_ascii=False, indent=1)
        same = old == txt
        if not same: out.write_text(txt)
    else:
        dev = CORPUS_DIR / 'parsed' / '_dev' / s['id'] / r['version_id']
        P.render_images(raw, tree, dev)
        txt = json.dumps(tree, ensure_ascii=False, indent=1).replace('corpus/parsed/_dev/', 'corpus/parsed/')
        same = old == txt
        if not same:
            (CORPUS_DIR / 'parsed' / '_dev' / s['id'] / f"{r['version_id']}.json").write_text(txt)
    return (s['id'], r['version_id'], 'same' if same else f"CHANGED checks={len(tree['checks'])}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--write', action='store_true'); ap.add_argument('-j', type=int, default=8)
    a = ap.parse_args()
    js = jobs(set(a.only.split(',')) if a.only else None)
    with ProcessPoolExecutor(a.j) as ex:
        res = list(ex.map(one, [(s, r, m, a.write) for s, r, m in js]))
    ch = [x for x in res if x[2] != 'same']
    for x in ch: print(*x)
    print(f"{len(res)} trees, {len(res)-len(ch)} same, {len(ch)} changed/missing")
