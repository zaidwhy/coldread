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
M={"qwen":"results-qwen2.5_7b-instruct.jsonl","llama8":"results-llama3.1_8b.jsonl","mistral":"results-mistral_7b.jsonl","llama3b":"results-llama3.2_latest.jsonl"}
D={m:load(f) for m,f in M.items()}
# sample order = file order; first 20 authors (contamination_check uses authors[:20])
seen=[]
for r in D["qwen"]:
    if r["author_id"] not in seen: seen.append(r["author_id"])
tr={r["author_id"]:r["truth"] for r in D["qwen"]}
print("first 20 authors in sample order:", collections.Counter((tr[a]["age_band"],tr[a]["gender"]) for a in seen[:20]))
print("truth is first-listed gender for", sum(tr[a]["gender"]==("female" if flipf(a) else "male") for a in seen), "of", len(seen), "authors -> an always-first-listed predictor scores this")
# gender accuracy split by flip group
for m in M:
    out=[]
    for n in STEPS:
        res=[]
        for fl in (False,True):
            rr=[r for r in D[m] if r["n_words"]==n and r["pred"] and flipf(r["author_id"])==fl]
            res.append("%d/%d"%(sum(nrm(r["pred"].get("gender"))==r["truth"]["gender"] for r in rr),len(rr)))
        out.append("%d: maleFirst %s femFirst %s"%(n,res[0],res[1]))
    print(m,"gender acc by listing order |"," ; ".join(out))
# balanced-order reweighting: accuracy when each (truth gender x order) cell weighted equally
for m in M:
    out=[]
    for n in STEPS:
        accs=[]
        for g in ("male","female"):
            for fl in (False,True):
                rr=[r for r in D[m] if r["n_words"]==n and r["pred"] and flipf(r["author_id"])==fl and r["truth"]["gender"]==g]
                accs.append(sum(nrm(r["pred"].get("gender"))==g for r in rr)/len(rr))
        out.append("%d:%.3f"%(n,sum(accs)/4))
    print(m,"order-balanced gender accuracy (4 cells equal weight) |"," ".join(out))
# age: first-listed
BANDS=["13-17","23-27","33-47"]
for m in M:
    out=[]
    for n in (25,1600):
        rr=[r for r in D[m] if r["n_words"]==n and r["pred"]]
        first=sum(nrm(r["pred"].get("age_band"))==(BANDS[2] if flipf(r["author_id"]) else BANDS[0]) for r in rr)
        last=sum(nrm(r["pred"].get("age_band"))==(BANDS[0] if flipf(r["author_id"]) else BANDS[2]) for r in rr)
        out.append("%d: first %d mid %d last %d"%(n,first,sum(nrm(r["pred"].get("age_band"))==BANDS[1] for r in rr),last))
    print(m,"age position |"," ; ".join(out))
# industry
I={"qwen":"results-industry-qwen2.5_7b-instruct.jsonl","llama8":"results-industry-llama3.1_8b.jsonl","mistral":"results-industry-mistral_7b.jsonl","llama3b":"results-industry-llama3.2_latest.jsonl","qwen_m":"results-industry-masked-qwen2.5_7b-instruct.jsonl","llama8_m":"results-industry-masked-llama3.1_8b.jsonl"}
ID={m:load(f) for m,f in I.items()}
IND=["education","technology","arts","communications-media"]
ti={r["author_id"]:nrm(r["truth"]["industry"]) for r in ID["qwen"]}
print("industry flip x truth", sorted(collections.Counter((flipf(a),ti[a]) for a in ti).items()))
def pos(a,ind):
    order=list(reversed(IND)) if flipf(a) else IND
    return order.index(ind) if ind in order else -1
print("truth position distribution (0=first listed):", sorted(collections.Counter(pos(a,ti[a]) for a in ti).items()))
for m in I:
    out=[]
    for n in STEPS:
        rr=[r for r in ID[m] if r["n_words"]==n and r["pred"]]
        c=collections.Counter(pos(r["author_id"],nrm(r["pred"].get("industry"))) for r in rr)
        out.append("%d:%s"%(n,[c.get(i,0) for i in (0,1,2,3)]))
    print(m,"pred position counts [1st,2nd,3rd,4th] |"," ".join(out))
# position-only predictor expected accuracy: P(pred pos)=empirical, independent of text
for m in ["qwen","llama8","mistral"]:
    for n in (25,50,1600):
        rr=[r for r in ID[m] if r["n_words"]==n and r["pred"]]
        pc=collections.Counter(pos(r["author_id"],nrm(r["pred"].get("industry"))) for r in rr)
        tc=collections.Counter(pos(r["author_id"],nrm(r["truth"]["industry"])) for r in rr)
        exp=sum(pc[i]/len(rr)*tc[i] for i in range(4))
        # label-only predictor: marginal over labels
        lc=collections.Counter(nrm(r["pred"].get("industry")) for r in rr)
        expl=sum(lc[i]/len(rr)*18 for i in IND)
        hits=sum(nrm(r["pred"].get("industry"))==nrm(r["truth"]["industry"]) for r in rr)
        print(" ",m,n,"hits",hits,"| expected hits from position marginal alone %.1f, from label marginal alone %.1f"%(exp,expl))
# 3B industry unparsed by truth
rr=[r for r in ID["llama3b"] if not r["pred"]]
print("3B unparsed by step",sorted(collections.Counter(r["n_words"] for r in rr).items()),"by truth",collections.Counter(r["truth"]["industry"] for r in rr),"err kinds",collections.Counter((r["error"] or "")[:12] for r in rr))
for n in STEPS:
    a=[r for r in ID["llama3b"] if r["n_words"]==n]
    k=sum(1 for r in a if r["pred"] and nrm(r["pred"].get("industry"))==nrm(r["truth"]["industry"]))
    print("  3B",n,"hits",k,"parsed",sum(1 for r in a if r["pred"]),"lo(excl) %.4f lo(miss) %.4f"%(wil(k,sum(1 for r in a if r["pred"])),wil(k,72)))
