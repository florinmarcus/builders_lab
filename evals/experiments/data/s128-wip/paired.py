"""paired.py BEFORE.json AFTER.json [--list]: paired before/after on units whose key changed."""
import json, sys
from math import comb
def high(v):
    return v is not None and any(f['severity'] == 'high' and (f.get('settled') or {}).get('as') != 'model-wrong' for f in v.get('findings') or [])
def mcnemar(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)
B = {(r['source_id'], r['version_id'], r['unit']): r for r in json.load(open(sys.argv[1]))}
A = {(r['source_id'], r['version_id'], r['unit']): r for r in json.load(open(sys.argv[2]))}
ch = [k for k in A if k in B and A[k]['key'] != B[k]['key']]
nj = [k for k in ch if A[k]['verdict'] is None]
hb = [k for k in ch if high(B[k]['verdict'])]
fixed = [k for k in ch if high(B[k]['verdict']) and A[k]['verdict'] and not high(A[k]['verdict'])]
broken = [k for k in ch if not high(B[k]['verdict']) and high(A[k]['verdict'])]
ha = [k for k in ch if high(A[k]['verdict'])]
print(f"units changed {len(ch)} (not judged {len(nj)}); high before {len(hb)} / after {len(ha)}; fixed {len(fixed)}; broken {len(broken)}; "
      f"McNemar p {mcnemar(len(fixed), len(broken)):.2g}; noise would give fixed {0.13*len(hb):.1f} / broken {0.025*(len(ch)-len(hb)):.1f}")
fams = sorted({A[k]['family'] for k in ch})
for f in fams:
    c = [k for k in ch if A[k]['family'] == f]
    print(f"  {f}: changed {len(c)}, high before {sum(high(B[k]['verdict']) for k in c)} after {sum(high(A[k]['verdict']) for k in c)}, "
          f"fixed {sum(k in fixed for k in c)}, broken {sum(k in broken for k in c)}")
if '--list' in sys.argv:
    for k in broken:
        print('BROKEN', k[0], k[1][:60], k[2])
        for f in A[k]['verdict']['findings']:
            if f['severity'] == 'high': print('    ', f['kind'], f['problem'][:220], '|', f['evidence'][:200])
