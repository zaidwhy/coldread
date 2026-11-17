import json, math, sys, collections, random
from pathlib import Path
R = Path(sys.argv[1])
def wil(k,n,z=1.96):
    if n==0: return 0
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h
def load(f): return [json.loads(l) for l in (R/"out"/f).read_text(encoding="utf-8").splitlines() if l.strip()]
def nrm(v): return None if v is None else str(v).strip().lower()
STEPS=[25,50,100,200,400,800,1600]
def binom_tail(k,n,p):
    return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
M={"qwen":"results-qwen2.5_7b-instruct.jsonl","llama8":"results-llama3.1_8b.jsonl","mistral":"results-mistral_7b.jsonl","llama3b":"results-llama3.2_latest.jsonl"}
D={m:load(f) for m,f in M.items()}
def hit(m,a):
    return {(r["author_id"],r["n_words"]): int(nrm(r["pred"].get(a))==nrm(r["truth"][a])) for r in D[m] if r["pred"]}
H={(m,a):hit(m,a) for m in M for a in ["gender","age_band","sign"]}
authors=sorted({r["author_id"] for r in D["qwen"]})
def cells(m): return {(r["author_id"],r["n_words"],json.dumps(r["truth"],sort_keys=True)) for r in D[m]}
print("same cells/truth across 3 runs:", all(cells("qwen")==cells(m) for m in ["llama8","mistral"]))
truth={r["author_id"]:r["truth"] for r in D["qwen"]}
flip={a: sum(ord(c) for c in str(a))%2==1 for a in authors}
print("flip count", sum(flip.values()), "of", len(authors))
print("flip x gender", sorted(collections.Counter((flip[a],truth[a]["gender"]) for a in authors).items()))
print("flip x age", sorted(collections.Counter((flip[a],truth[a]["age_band"]) for a in authors).items()))
for m in M:
    out=[]
    for n in STEPS:
        rr=[r for r in D[m] if r["n_words"]==n and r["pred"]]
        first=sum(nrm(r["pred"].get("gender"))==("female" if flip[r["author_id"]] else "male") for r in rr)
        fem=sum(nrm(r["pred"].get("gender"))=="female" for r in rr)
        out.append("%d: first-listed %d/%d, female %d"%(n,first,len(rr),fem))
    print(m,"|"," ; ".join(out))
for m in M:
    for n in (25,800,1600):
        c=collections.Counter((r["truth"]["gender"],nrm(r["pred"].get("gender"))) for r in D[m] if r["n_words"]==n and r["pred"])
        print(" confusion (truth,pred)",m,n,sorted(c.items()))
def mcnemar(m1,m2,a,n):
    b=c=0
    for au in authors:
        k=(au,n)
        if k in H[(m1,a)] and k in H[(m2,a)]:
            x,y=H[(m1,a)][k],H[(m2,a)][k]
            if x and not y: b+=1
            if y and not x: c+=1
    nn=b+c; p=min(1,2*binom_tail(max(b,c),nn,0.5)) if nn else 1
    return b,c,p
for a in ["gender","age_band"]:
    for pair in [("llama8","qwen"),("llama8","mistral"),("qwen","mistral"),("llama8","llama3b")]:
        print("McNemar",a,pair," ".join("%d:(%d,%d)p=%.3f"%((n,)+mcnemar(pair[0],pair[1],a,n)) for n in STEPS))
bars={"gender":0.5,"age_band":1/3}
for m in ["qwen","llama8","mistral","llama3b"]:
    for a in ["gender","age_band"]:
        ks=[(n,sum(v for (au,nn),v in H[(m,a)].items() if nn==n),sum(1 for (au,nn) in H[(m,a)] if nn==n)) for n in STEPS]
        def hl(delta,sustained=False):
            cl=[wil(k+delta,t)>bars[a] for n,k,t in ks]
            if sustained:
                for i in range(len(ks)):
                    if all(cl[i:]): return ks[i][0]
                return None
            return next((n for (n,k,t),c in zip(ks,cl) if c),None)
        ps=" ".join("%d:%.4f"%(n,binom_tail(k,t,bars[a])) for n,k,t in ks)
        print(m,a,"HL",hl(0),"sustainedHL",hl(0,True),"| -1hit",hl(-1),"-2",hl(-2),"-3",hl(-3),"+1",hl(1),"+2",hl(2),"+3",hl(3),"| exact one-sided p",ps)
random.seed(0)
def hl_bs(m,a,samp,bar):
    for n in STEPS:
        ks=[H[(m,a)][(au,n)] for au in samp if (au,n) in H[(m,a)]]
        if wil(sum(ks),len(ks))>bar: return n
    return None
res=collections.Counter(); order=collections.Counter(); B=5000
for _ in range(B):
    samp=[random.choice(authors) for _ in authors]
    g={m:hl_bs(m,"gender",samp,0.5) for m in ["qwen","llama8","mistral"]}
    a={m:hl_bs(m,"age_band",samp,1/3) for m in ["qwen","llama8","mistral"]}
    vals=list(g.values())
    if None in vals: res["some reader never"]+=1
    else: res["ratio %d"%(max(vals)//min(vals))]+=1
    order["age<gender all3"]+= all((a[m] is not None) and (g[m] is None or a[m]<g[m]) for m in g)
    order["llama8 age<gender"]+= (a["llama8"] is not None) and (g["llama8"] is None or a["llama8"]<g["llama8"])
    for m in g: order["%s gender HL %s"%(m,g[m])]+=1
    order["llama8 fastest gender (strict)"]+= g["llama8"] is not None and all(g[x] is None or g[x]>g["llama8"] for x in ["qwen","mistral"])
print("bootstrap (author resample, B=%d, bars fixed at 0.5 and 1/3) gender HL max/min ratio:"%B, sorted(res.items(), key=lambda x:-x[1]))
for k,v in sorted(order.items()): print("  ",k,v)
I={"qwen":"results-industry-qwen2.5_7b-instruct.jsonl","llama8":"results-industry-llama3.1_8b.jsonl","mistral":"results-industry-mistral_7b.jsonl","llama3b":"results-industry-llama3.2_latest.jsonl","qwen_m":"results-industry-masked-qwen2.5_7b-instruct.jsonl","llama8_m":"results-industry-masked-llama3.1_8b.jsonl","qwen_r":"replicate-industry-qwen2.5_7b-instruct.jsonl","llama8_r":"replicate-industry-llama3.1_8b.jsonl"}
ID={m:load(f) for m,f in I.items()}
def ih(r): return bool(r["pred"]) and nrm(r["pred"].get("industry"))==nrm(r["truth"]["industry"])
for m in I:
    ks=[]
    for n in STEPS:
        rr=[r for r in ID[m] if r["n_words"]==n]
        ks.append((n,sum(ih(r) for r in rr),len(rr),sum(1 for r in rr if r["pred"])))
    def hl(delta,miss=True,sustained=False):
        cl=[wil(k+delta,(t if miss else tp))>0.25 for n,k,t,tp in ks]
        if sustained:
            for i in range(len(ks)):
                if all(cl[i:]): return ks[i][0]
            return None
        return next((n for (n,k,t,tp),c in zip(ks,cl) if c),None)
    print("industry",m,"HL(excl unparsed)",hl(0,False),"HL(unparsed=miss)",hl(0,True),"sustained",hl(0,False,True),"| -1hit",hl(-1,False),"-2",hl(-2,False),"+1",hl(1,False),"| exact p:"," ".join("%d:%.4f"%(n,binom_tail(k,tp,0.25)) for n,k,t,tp in ks))
for a,b in [("qwen","qwen_r"),("llama8","llama8_r")]:
    A={(r["author_id"],r["n_words"]):r["pred"] for r in ID[a]}; Bb={(r["author_id"],r["n_words"]):r["pred"] for r in ID[b]}
    print("replicate diff",a,"industry",sum(nrm(A[k].get("industry"))!=nrm(Bb[k].get("industry")) for k in A),"sign",sum(nrm(A[k].get("sign"))!=nrm(Bb[k].get("sign")) for k in A),"either",sum(A[k]!=Bb[k] for k in A))
for m in ["qwen_m","llama8_m"]:
    print("masked frac at 1600",m,sum(r.get("n_masked",0) for r in ID[m] if r["n_words"]==1600)/(72*1600),"at 25",sum(r.get("n_masked",0) for r in ID[m] if r["n_words"]==25)/(72*25))
for a,b in [("qwen","qwen_m"),("llama8","llama8_m")]:
    for n in STEPS:
        A={r["author_id"]:r for r in ID[a] if r["n_words"]==n}; Bb={r["author_id"]:r for r in ID[b] if r["n_words"]==n}
        print(" mask paired",a,n,"unmasked-only-hit",sum(ih(A[k]) and not ih(Bb[k]) for k in A),"masked-only-hit",sum(ih(Bb[k]) and not ih(A[k]) for k in A),"pred changed",sum(nrm(A[k]["pred"].get("industry"))!=nrm(Bb[k]["pred"].get("industry")) for k in A))
for m in ["qwen","llama8","mistral"]:
    for n in (50,1600):
        c=collections.Counter()
        for r in ID[m]:
            if r["n_words"]==n: c[r["truth"]["industry"]]+=ih(r)
        print(" per-industry hits of 18",m,n,dict(c))
ar=[json.loads(l) for l in (R/"out"/"archive"/"results-qwen2.5_3b-instruct-PREBALANCE.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("archive rows",len(ar),"authors",len({r["author_id"] for r in ar}),"nopred",sum(1 for r in ar if not r["pred"]),"gender preds",collections.Counter(nrm(r["pred"].get("gender")) for r in ar if r["pred"]),"truth gender",collections.Counter(r["truth"]["gender"] for r in ar),"errors",collections.Counter((r["error"] or "")[:40] for r in ar))
print("archive steps",collections.Counter(r["n_words"] for r in ar))
