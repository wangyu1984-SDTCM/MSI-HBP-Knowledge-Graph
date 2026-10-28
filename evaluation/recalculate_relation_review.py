"""Reproduce the historical and released-subset relation-review statistics.

Usage from the repository root: python evaluation/recalculate_relation_review.py
Requires NumPy. Does not modify ratings, graph files, or stored results.
"""
from pathlib import Path
from statistics import NormalDist
import csv, json, argparse
import numpy as np

SCORES={'rejected':0,'partial':1,'confirmed':2}
Z=NormalDist().inv_cdf(.975)

def wilson(k,n):
    p=k/n;den=1+Z*Z/n
    center=(p+Z*Z/(2*n))/den
    half=Z*((p*(1-p)/n+Z*Z/(4*n*n))**.5)/den
    return [max(0,center-half),min(1,center+half)]

def statistics(rows,replicates=20000,seed=20261028):
    n=len(rows);scores=np.array([[SCORES[r['rater1']],SCORES[r['rater2']]]for r in rows])
    matrix=np.bincount(scores[:,0]*3+scores[:,1],minlength=9).reshape(3,3)
    p1=matrix.sum(1)/n;p2=matrix.sum(0)/n;pm=(p1+p2)/2
    po=float(np.trace(matrix)/n);pe=float(np.sum(pm*(1-pm))/2)
    weight=(np.arange(3)[:,None]-np.arange(3)[None,:])**2/4
    obs=float(np.sum(matrix/n*weight));exp=float(np.sum(p1[:,None]*p2[None,:]*weight))
    # Resample paired relation ratings, retaining all three categories in every resample.
    rng=np.random.default_rng(seed);boot=[]
    for _ in range(replicates):
        sample=scores[rng.integers(0,n,size=n)]
        pb=np.bincount(sample.ravel(),minlength=3)/(2*n)
        peb=np.sum(pb*(1-pb))/2;pob=np.mean(sample[:,0]==sample[:,1])
        boot.append((pob-peb)/(1-peb))
    confirmed=sum(r['consensus']=='confirmed' for r in rows)
    by={}
    for pred in sorted({r['predicate']for r in rows}):
        rs=[r for r in rows if r['predicate']==pred];k=sum(r['consensus']=='confirmed'for r in rs)
        by[pred]={'n':len(rs),'confirmed':k,'wilson':wilson(k,len(rs))}
    return {'n':n,'agreement':int(np.trace(matrix)),'matrix':matrix.tolist(),'ac1':(po-pe)/(1-pe),
            'weighted_kappa':1-obs/exp if exp else None,'confirmed':confirmed,'wilson':wilson(confirmed,n),
            'ac1_ci':np.quantile(boot,[.025,.975]).tolist(),'bootstrap_replicates':replicates,
            'bootstrap_seed':seed,'by_relation':by}

def main():
    here=Path(__file__).resolve().parent
    ap=argparse.ArgumentParser();ap.add_argument('--graph',type=Path,default=here.parent/'data/triples.json')
    args=ap.parse_args()
    with (here/'relation_review_release_mapping.csv').open(encoding='utf-8-sig',newline='')as f:rows=list(csv.DictReader(f))
    graph=json.loads(args.graph.read_text(encoding='utf-8'))
    triples={(r['subject'],r.get('predicate',r.get('relation')),r['object'])for r in graph}
    assert len(graph)==312 and len(triples)==312,'Unexpected graph release: expected 312 unique relations'
    for r in rows:
        present=(r['subject'],r['predicate'],r['object'])in triples
        assert present==(r['present_in_v2.0']=='True'),f"Membership mismatch: {r['triple_id']}"
    retained=[r for r in rows if r['present_in_v2.0']=='True']
    assert len(rows)==100 and len(retained)==80
    result={'historical100':statistics(rows),'released80':statistics(retained)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
