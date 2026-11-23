"""runchecks.py SRC [SRC...]: run open model-check packets with Fable (runbook prompt), batches of 6, 8 at a time."""
import sys, subprocess, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
REPO = Path('/home/user/builders_lab')
PROMPT = """You are doing model checks for a regulations corpus. Work in the repo at `{repo}`. Do not change any file except the one answers file named below.

For EACH packet below, separately and in order:
1. Read the JSON packet at `{repo}/corpus/parsed/{sid}/checks/<name>`.
2. Open every image listed in its `images` (paths are relative to `{repo}`) with the Read tool.
3. Follow the packet's `instructions` exactly, and use `template` if there is one.
4. Produce one line of JSON in the shape of `answer_format` (copy `key` and `kind` exactly from the packet; `value` as the format shows; `reason`, `evidence`, `confidence`).

Packets: {names}

Write all answers, one JSON object per line, in packet order, to `{repo}/corpus/parsed/{sid}/answers/batch_{nn}.jsonl` with the Write tool. Each line must be valid JSON on a single line. Then reply only with "done" and the number of lines written.{extra}"""
def jobs(sids, extra=''):
    out = []
    for sid in sids:
        names = sorted(p.name for p in (REPO / 'corpus/parsed' / sid / 'checks').glob('*.json'))
        (REPO / 'corpus/parsed' / sid / 'answers').mkdir(parents=True, exist_ok=True)
        for old in (REPO / 'corpus/parsed' / sid / 'answers').glob('batch_*.jsonl'): old.unlink()
        for i in range(0, len(names), 6):
            out.append((sid, names[i:i+6], f"{i//6+1:02d}", extra))
    return out
def one(j):
    sid, names, nn, extra = j
    p = PROMPT.format(repo=REPO, sid=sid, names=', '.join(f'`{n}`' for n in names), nn=nn, extra=extra)
    ans = REPO / 'corpus/parsed' / sid / 'answers' / f'batch_{nn}.jsonl'
    for attempt in range(2):
        try:
            subprocess.run(['claude', '-p', p, '--model', 'claude-fable-5-2', '--allowedTools', 'Read,Write'],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=2400, cwd=REPO)
        except subprocess.TimeoutExpired:
            pass
        if ans.exists(): break
    return sid, nn, ans.exists(), len(ans.read_text().splitlines()) if ans.exists() else 0, len(names)
if __name__ == '__main__':
    extra = ''
    args = sys.argv[1:]
    if args and args[0] == '--extra': extra = '\n\n' + args[1]; args = args[2:]
    js = jobs(args, extra)
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(one, js): print(*r, flush=True)
