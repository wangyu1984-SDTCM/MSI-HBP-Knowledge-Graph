#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieval_ablation.py — retrieval-strategy ablation

Implements the six retrieval configurations reported in the manuscript and
reproduces the graph-level statistics on which the failure analysis rests.

Design: hub suppression (none / soft / hard) x predicate constraint (absent / present),
plus a combined configuration with low-confidence abstention.

    A0    no hub suppression, no predicate constraint          (baseline)
    D1    soft hub suppression (weight x0.3)
    D1.5  soft hub suppression + predicate constraint
    D2    hard hub suppression (hub-directed relations excluded)
    D3    predicate constraint only
    D4    hard suppression + predicate constraint + abstention

Hub nodes are defined as terms whose degree exceeds five times the mean degree of
the connected subgraph. The threshold derives from graph statistics alone; no
evaluation data were used to set it.

Usage:
    python retrieval_ablation.py [repo_root]

Outputs a report to stdout. Requires only the released data files.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
RELATIONS = ROOT / 'data' / 'triples.json'
ENTITIES = ROOT / 'data' / 'entities.json'

HUB_MULTIPLIER = 5.0
SOFT_WEIGHT = 0.3
TOP_K = 20

# question type -> permitted predicates (D3 / D4)
PREDICATE_MAP = {
    'Formula composition': {'组成'},
    'Treatment-principle selection': {'使用'},
    'Pathogenesis identification': {'引起'},
    'Formula selection': {'治疗', '使用'},
    'Pattern differentiation': None,      # None = unrestricted
    'Multi-step reasoning': None,
    'Comorbidity management': None,
}


def load():
    rels = json.loads(RELATIONS.read_text(encoding='utf-8'))
    ents = json.loads(ENTITIES.read_text(encoding='utf-8'))
    return rels, ents


def degrees(rels):
    d = Counter()
    for r in rels:
        d[r['subject']] += 1
        d[r['object']] += 1
    return d


def hub_nodes(deg):
    """Hub = degree >= HUB_MULTIPLIER * mean degree of the connected subgraph."""
    n = len(deg)
    mean = sum(deg.values()) / n
    threshold = HUB_MULTIPLIER * mean
    hubs = {e for e, k in deg.items() if k >= threshold}
    return hubs, mean, threshold


def retrieve(rels, seeds, hubs, mode='none', predicates=None, top_k=TOP_K):
    """Return up to top_k relations touching any seed term, under the given strategy.

    mode: 'none' | 'soft' | 'hard'
    predicates: set of permitted predicate strings, or None for unrestricted
    """
    cand = []
    for r in rels:
        if r['subject'] not in seeds and r['object'] not in seeds:
            continue
        if predicates is not None and r['predicate'] not in predicates:
            continue
        if mode == 'hard' and r['object'] in hubs:
            continue
        score = 1.0
        if mode == 'soft' and r['object'] in hubs:
            score *= SOFT_WEIGHT
        cand.append((score, r))
    cand.sort(key=lambda x: -x[0])
    return [r for _, r in cand[:top_k]]


def abstain(hits, hubs):
    """D4 abstention rule: empty retrieval, or every hit points at a hub."""
    if not hits:
        return True
    return all(r['object'] in hubs for r in hits)


CONFIGS = {
    'A0':   dict(mode='none', predicate=False, abstention=False),
    'D1':   dict(mode='soft', predicate=False, abstention=False),
    'D1.5': dict(mode='soft', predicate=True,  abstention=False),
    'D2':   dict(mode='hard', predicate=False, abstention=False),
    'D3':   dict(mode='none', predicate=True,  abstention=False),
    'D4':   dict(mode='hard', predicate=True,  abstention=True),
}


def main():
    rels, ents = load()
    deg = degrees(rels)
    hubs, mean, threshold = hub_nodes(deg)

    names = {e['name'] for e in ents}
    connected = set(deg)

    print('=' * 68)
    print('Graph statistics')
    print('=' * 68)
    print(f'  entity index          {len(names)} unique terms '
          f'({len(ents)} term-type assignments)')
    print(f'  graph nodes           {len(connected)}')
    print(f'  relations             {len(rels)}')
    print(f'  relation types        {dict(Counter(r["predicate"] for r in rels))}')
    print(f'  evidence levels       {dict(Counter(r.get("evidence_level") for r in rels))}')
    print(f'  mean degree           {mean:.2f}')
    print(f'  hub threshold         {HUB_MULTIPLIER} x mean = {threshold:.1f}')
    print(f'  hub nodes             {sorted(((e, deg[e]) for e in hubs), key=lambda x: -x[1])}')

    ordered = sorted(deg.values(), reverse=True)
    gap_lo, gap_hi = ordered[len(hubs)], ordered[len(hubs) - 1]
    print(f'  degree gap            rank {len(hubs)} = {gap_hi}, '
          f'rank {len(hubs)+1} = {gap_lo}; any threshold in '
          f'[{gap_lo+1}, {gap_hi}] selects the same nodes')

    hub_directed = [r for r in rels if r['object'] in hubs]
    print(f'  hub-directed          {len(hub_directed)}/{len(rels)} '
          f'({len(hub_directed)/len(rels)*100:.1f}%)')
    by_pred = Counter(r['predicate'] for r in hub_directed)
    print(f'  hub-directed by type  {dict(by_pred)}')

    print()
    print('=' * 68)
    print('Topological indistinguishability of generic and specific knowledge')
    print('=' * 68)
    cov = defaultdict(set)
    typ = {}
    for r in rels:
        if r['object'] in hubs:
            cov[r['subject']].add(r['object'])
            typ[r['subject']] = r['subject_type']
    dist = Counter(len(v) for v in cov.values())
    print(f'  subjects connected to a hub          {len(cov)}')
    for k in sorted(dist, reverse=True):
        print(f'    connected to {k} hub(s)              {dist[k]}')
    ge2 = sum(v for k, v in dist.items() if k >= 2)
    print(f'  connected to >=2 hubs                 {ge2}/{len(cov)} '
          f'({ge2/len(cov)*100:.0f}%)')
    treat = [s for s in cov if typ[s] in ('治则治法', '方剂', '中药')]
    single = [s for s in treat if len(cov[s]) == 1]
    print(f'  treatment-side subjects               {len(treat)}')
    print(f'    of which single-hub                 {len(single)}')
    only1 = [(s, typ[s]) for s in cov if len(cov[s]) == 1]
    print(f'  all single-hub subjects               {only1}')

    print()
    print('=' * 68)
    print('Retrieval reach by configuration')
    print('=' * 68)
    print('  Reported as the number of relations retrievable under each strategy')
    print('  when every graph node is used as a seed in turn.')
    print()
    print(f'  {"config":<7}{"mode":<7}{"pred":<7}{"reachable":>10}{"abstain":>9}')
    for name, cfg in CONFIGS.items():
        reach, abst = 0, 0
        for seed in connected:
            preds = None
            if cfg['predicate']:
                preds = {'治疗', '组成', '引起', '使用'}
            hits = retrieve(rels, {seed}, hubs, cfg['mode'], preds)
            if cfg['abstention'] and abstain(hits, hubs):
                abst += 1
            else:
                reach += len(hits)
        print(f'  {name:<7}{cfg["mode"]:<7}{str(cfg["predicate"]):<7}'
              f'{reach:>10}{abst:>9}')

    print()
    print('Note: end-to-end accuracy for each configuration was obtained by running the')
    print('question-answering pipeline on the 73-question independent set and rating the')
    print('responses under blinding; those results are in Table 4 of the manuscript and')
    print('the item-level ratings are in this directory.')


if __name__ == '__main__':
    main()
