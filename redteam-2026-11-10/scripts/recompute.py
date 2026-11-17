import json, math, sys, collections
from pathlib import Path
R = Path(sys.argv[1])
def wil(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h,c+h
def load(f): return [json.loads(l) for l in (R/'out'/f).read_text(encoding='utf-8').splitlines() if l.strip()]
def nrm(v): return None if v is None else str(v).strip().lower()
files = sorted(p.name for p in (R/'out').glob('*.jsonl'))
for f in files:
    rows = load(f)
    attrs = [a for a in ['gender','age_band','industry','sign'] if a in rows[0]['truth']]
    authors = {r['author_id']:r['truth'] for r in rows}
    print('\n==', f, 'rows', len(rows), 'authors', len(authors), 'errors', sum(1 for r in rows if r['error']), 'nopred', sum(1 for r in rows if not r['pred']))
    bar = {}
    for a in attrs:
        c = collections.Counter(nrm(t[a]) for t in authors.values())
        bar[a] = max(c.values())/len(authors)
        print('  truth dist', a, dict(c.most_common(4)), 'bar %.4f' % bar[a])
    steps = sorted({r['n_words'] for r in rows})
    for a in attrs:
        out=[]; hl=None; cleared=[]
        for n in steps:
            rr=[r for r in rows if r['n_words']==n and r['pred']]
            k=sum(nrm(r['pred'].get(a))==nrm(r['truth'][a]) for r in rr)
            lo,hi=wil(k,len(rr))
            cl = lo>bar[a]
            cleared.append(cl)
            if cl and hl is None: hl=n
            out.append('%d:%d/%d lo%.4f%s'%(n,k,len(rr),lo,'*' if cl else ''))
        print('  ',a,'HL',hl,'|',' '.join(out))
    # prediction distributions
    for a in attrs:
        if a=='sign': 
            c=collections.Counter(nrm(r['pred'].get(a)) for r in rows if r['pred'])
            print('   sign preds top', c.most_common(5), 'distinct', len(c)); continue
        for n in (25,1600):
            c=collections.Counter(nrm(r['pred'].get(a)) for r in rows if r['pred'] and r['n_words']==n)
            print('   pred', a, n, dict(c))
