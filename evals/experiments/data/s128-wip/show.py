"""show.py SOURCE VERSION_SUBSTR PAGE [raw]: tree content of a PDF page as semcheck sees it."""
import json,sys
sys.path.insert(0,'/home/user/builders_lab')
from system.rag import semcheck as S
from system.rag import coverage as C
sid,vsub,page=sys.argv[1],sys.argv[2],int(sys.argv[3])
for rec,tp in S.in_scope_versions([sid]):
    if vsub not in rec['version_id']: continue
    tree=json.loads(tp.read_text())
    raw=C.raw_doc(rec)
    pages=C.section_pages(tree['sections'],len(raw['pages']))
    print('##',rec['version_id'],tp)
    for e in S.pdf_page_content(tree,page,raw['pages'][page-1],pages):
        print(json.dumps(e,ensure_ascii=False)[:1800])
    if 'raw' in sys.argv:
        print('--- raw words'); print(' '.join(w[0] for w in raw['pages'][page-1]['words'])[:3000])
