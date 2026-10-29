"""Check formula coverage and candidate-fusion counts against released files.

Run from the repository root: python evaluation/check_reported_counts.py
Optionally provide a local original source-record export with --source-records.
Only counts are emitted; source abstracts and credentials are never printed.
"""
import argparse
import json
from pathlib import Path


FORMULAS = {
    'Q012': '柴胡加龙骨牡蛎汤', 'Q013': '苓桂术甘汤', 'Q014': '大定风珠',
    'Q038': '黄连温胆汤', 'Q039': '血府逐瘀汤', 'Q040': '安神定志丸',
    'Q062': '甘麦大枣汤', 'Q063': '朱砂安神丸',
}


def check(root, source_records=None):
    read = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
    entities = read('data/entities.json')
    triples = read('data/triples.json')
    questions = read('evaluation/question_set_73.json')
    names = {e['name'] for e in entities}
    nodes = {t[k] for t in triples for k in ('subject', 'object')}
    indexed_formulas = {e['name'] for e in entities if e['type'] == '方剂'}
    rows = []
    for q in questions:
        if q['question_type'] != 'Formula composition':
            continue
        formula = FORMULAS[q['id']]
        assert formula in q['question_zh'], q['id']
        rows.append({
            'id': q['id'], 'formula_as_asked': formula,
            'exact_name_in_index': formula in names,
            'exact_name_in_graph': formula in nodes,
            'exact_composition_relations': sum(t['subject'] == formula and t['predicate'] == '组成' for t in triples),
            'other_indexed_formula_substrings': sorted(n for n in indexed_formulas if n != formula and n in q['question_zh']),
        })
    assert len(rows) == len(FORMULAS)
    original = read('data/processed/extracted_triples/msi_hbp_triples.json')
    fused = read('data/processed/fused_knowledge/msi_hbp_fused.json')
    reduction = len(original['entities']) - len(fused['entities'])
    assert reduction == fused['fusion_info']['merged_entities']
    result = {
        'formula_composition_questions': rows,
        'exact_formulas_absent_from_both': sum(not r['exact_name_in_index'] and not r['exact_name_in_graph'] for r in rows),
        'candidate_fusion': {'original_entity_records': len(original['entities']), 'fused_entity_records': len(fused['entities']), 'merged_entity_records': reduction},
        'interpretation': 'Exact formula-name coverage is distinct from partial string matching. Q038 asks about 黄连温胆汤; matching 温胆汤 does not establish coverage of the requested formula.',
    }
    if source_records is not None:
        records = json.loads(source_records.read_text(encoding='utf-8'))
        counts = {'title': 0, 'keywords': 0, 'abstract': 0}
        for row in records:
            for field in counts:
                value = row.get(field, '') or ''
                if isinstance(value, list):
                    value = ''.join(value)
                counts[field] += len(value)
        result['source_character_audit'] = {
            'records': len(records),
            'nonempty_abstracts': sum(bool(row.get('abstract')) for row in records),
            'method': 'Unicode code points in stored title, keyword strings and abstract; no added labels, separators or list syntax',
            'field_characters': counts, 'total_characters': sum(counts.values()),
            'mean_per_record': sum(counts.values()) / len(records) if records else None,
        }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-records', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.root, args.source_records), ensure_ascii=False, indent=2))
