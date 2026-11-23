#!/bin/bash
# saveall.sh SRC...: gather valid answer lines and save
cd /home/user/builders_lab
for s in "$@"; do
python - "$s" <<'PY'
import json,sys,glob
s=sys.argv[1]; good=[]
for f in sorted(glob.glob(f'corpus/parsed/{s}/answers/batch_*.jsonl')):
    for l in open(f):
        try: json.loads(l); good.append(l)
        except Exception: print(s,'bad json line')
open(f'corpus/parsed/{s}/answers.jsonl','w').writelines(good)
PY
python -m system.rag.checks save --source $s --answers corpus/parsed/$s/answers.jsonl --by "model check, Fable 5.2, Claude Code headless (packet)" 2>&1 | tail -3 | sed "s/^/$s: /"
done
