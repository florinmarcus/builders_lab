import sys,json,pickle,glob
sys.path.insert(0,'/home/user/builders_lab')
C='/tmp/claude-0/-home-user-builders-lab/279fdd82-bd2a-51a0-938e-fb1a2ec03a4d/scratchpad/s128/cache'
def load(sid, vsub, mod='parse_pdf'):
    for p in glob.glob(f'/home/user/builders_lab/corpus/versions/{sid}/*.json'):
        r=json.load(open(p))
        if vsub in r['version_id'] and r['valid_to'] is None and r['media_type']=='application/pdf':
            return r, pickle.load(open(f"{C}/{mod}-{r['sha256'][:20]}.pkl",'rb'))
def tables(doc, pages):
    for t in doc['tables']:
        if t['page'] in pages:
            print('p',t['page'],'top',round(t['top']),'bot',round(t['bottom']),'x',round(t['x0']),round(t['x1']),'rows',len(t['rows']),'cols',len(t['rows'][0]), [ (c or '')[:25] for c in t['rows'][0]])
def lines(doc, page, n=60):
    for l in [l for l in doc['lines'] if l['page']==page][:n]:
        print(round(l['top']),round(l['x0']),l['size'],l['font'][-12:],l['text'][:90])
