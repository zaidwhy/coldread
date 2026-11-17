import json, math, sys, collections
from pathlib import Path
R = Path(sys.argv[1])
def wil(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h
def load(f): return [json.loads(l) for l in (R/"out"/f).read_text(encoding="utf-8").splitlines() if l.strip()]
def nrm(v): return None if v is None else str(v).strip().lower()
STEPS=[25,50,100,200,400,800,1600]
def flipf(a): return sum(ord(c) for c in str(a))%2==1
def fisher(a,b,c,d):
    # two-sided Fisher exact for [[a,b],[c,d]]
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): return math.comb(r1,x)*math.comb(n-r1,c1-x)/math.comb(n,c1)
    p0=p(a); return sum(p(x) for x in range(max(0,c1-(n-r1)),min(r1,c1)+1) if p(x)<=p0*(1+1e-9))
M={"qwen":"results-qwen2.5_7b-instruct.jsonl","llama8":"results-llama3.1_8b.jsonl","mistral":"results-mistral_7b.jsonl","llama3b":"results-llama3.2_latest.jsonl"}
D={m:load(f) for m,f in M.items()}
for m in M:
    print("==",m)
    for n in STEPS:
        cell={}
        for fl in (False,True):
            rr=[r for r in D[m] if r["n_words"]==n and r["pred"] and flipf(r["author_id"])==fl]
            c=collections.Counter((r["truth"]["gender"][0],(nrm(r["pred"].get("gender")) or "?")[0]) for r in rr)
            k=sum(nrm(r["pred"].get("gender"))==r["truth"]["gender"] for r in rr)
            cell[fl]=(k,len(rr),c)
        (k0,n0,c0),(k1,n1,c1)=cell[False],cell[True]
        print("  %4d maleFirst %d/%d (lo %.3f) [truth,pred] %s | femFirst %d/%d (lo %.3f) %s | Fisher p=%.4f"%(n,k0,n0,wil(k0,n0),dict(sorted(c0.items())),k1,n1,wil(k1,n1),dict(sorted(c1.items())),fisher(k0,n0-k0,k1,n1-k1)))
# between-reader comparison restricted to each listing order, 1600 and 800 words
for fl,name in ((False,"male listed first (38 authors: 16 male, 22 female)"),(True,"female listed first (34 authors: 20 male, 14 female)")):
    print(name)
    for n in STEPS:
        print("   ",n," ".join("%s %d"%(m,sum(nrm(r["pred"].get("gender"))==r["truth"]["gender"] for r in D[m] if r["n_words"]==n and r["pred"] and flipf(r["author_id"])==fl)) for m in M))
# age band by order
for m in M:
    print(m,"age acc by order"," ".join("%d:%d/38,%d/34"%(n,sum(nrm(r["pred"].get("age_band"))==r["truth"]["age_band"] for r in D[m] if r["n_words"]==n and r["pred"] and not flipf(r["author_id"])),sum(nrm(r["pred"].get("age_band"))==r["truth"]["age_band"] for r in D[m] if r["n_words"]==n and r["pred"] and flipf(r["author_id"]))) for n in STEPS))
