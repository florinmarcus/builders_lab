import json,re,sys
from collections import Counter,defaultdict
S='/tmp/claude-0/-home-user-builders-lab/279fdd82-bd2a-51a0-938e-fb1a2ec03a4d/scratchpad/s128'
rows=json.load(open(sys.argv[1] if len(sys.argv)>1 else S+'/status-base.json'))
fam=sys.argv[2] if len(sys.argv)>2 else 'guidance-pdf'
C=[
 ('script', r'arabic|urdu|bangla|bengali|punjabi|presentation-form|broken character|replacement character|visual\) order|visual order|reverse'),
 ('xpage-table', r'continu|page before|previous page|from page \d|separate table|invented column|made-up column|column names are invented|Column 2|tail of a cell|end of the last table row|cut mid-sentence at the page|stops in the middle of a sentence at the page'),
 ('after-table', r"inside the text of table|only inside|table's text|table text|as if (it|they) were (a )?table note|text of table|notes text of table|inside table \S+'s text|in table-\S+ text"),
 ('formula', r'subscript|superscript|formula|fraction'),
 ('footnote-num', r'footnote marker|note numbers? (is|are) joined|joined to the standard|reference note'),
 ('script2', r'xx'),
 ('table-as-text', r'read as (one )?(running|loose running) text|kept as (one )?running text|as running text|repeats .*rows|rows .* as running text|kept a second time'),
 ('two-col', r'two columns|columns (are|is) mixed|left and right|left column|right column|mixed line by line|other column|side by side'),
 ('heading-body', r'heading.*(read as|kept as|as) body text|headings? .*(run into|joined to|merged)|read as body text|heading .* not kept as heading|run into the body'),
 ('para-merge', r'merged into|are merged|one (very )?(long|huge)|paragraph numbered|whole document|not sections of their own|not a section of its own|not a paragraph'),
 ('flowchart', r'flow ?chart|decision tree|branch|arrow'),
 ('spaces', r'spaces|run together'),
 ('group-head', r'group heading'),
]
units=defaultdict(set); allk=Counter(); sole=Counter(); per_src=defaultdict(Counter)
unc=[]
for r in rows:
    if r['family']!=fam or not r['verdict']: continue
    fs=[f for f in r['verdict']['findings'] if f['severity']=='high' and (f.get('settled') or {}).get('as')!='model-wrong']
    if not fs: continue
    u=(r['source_id'],r['version_id'],r['unit'])
    for f in fs:
        t=f['problem']+' '+f['evidence']
        hit=None
        for name,rx in C:
            if re.search(rx,t,re.I): hit=name;break
        if not hit: hit='other'; unc.append(f"{r['source_id']}|{r['unit']}|{f['problem'][:200]}")
        units[u].add(hit)
for u,cs in units.items():
    for c in cs: allk[c]+=1; per_src[c][u[0]]+=1
    if len(cs)==1: sole[next(iter(cs))]+=1
print('units',len(units))
for c,n in allk.most_common(): print(f"{c:15} any {n:4}  only {sole[c]:4}  ", per_src[c].most_common(6))
if '-v' in sys.argv: print('\n'.join(unc))
if '--list' in sys.argv:
    want=sys.argv[sys.argv.index('--list')+1]
    for u,cs in sorted(units.items()):
        if want in cs: print(u, sorted(cs))
