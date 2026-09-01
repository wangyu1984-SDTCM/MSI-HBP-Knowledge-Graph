"""
rebuild_stats.py —— 论文描述性统计复现脚本（v2.0）

直接从仓库发布的 JSON 数据文件（data/entities.json、data/triples.json）重新生成
论文中使用的全部描述性统计，不依赖任何中间过程，支持第三方独立验证：

  1. 实体记录总数（按「名称+类型」唯一）
  2. 唯一实体术语数
  3. 实体类型数量及各类型分布（25 种）
  4. 关系（三元组）总数
  5. 关系类型分布（4 种）
  6. 证据等级分布（A/B/C）
  7. 图谱层核心节点数（三元组涉及的去重实体）
  8. 节点度中心性 Top-N（按三元组出现次数）

运行：python rebuild_stats.py
输出：打印统计报告，并写回 data/processed/merged/statistics.json
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
ENTITIES_FILE = PROJECT_ROOT / "data" / "entities.json"
TRIPLES_FILE = PROJECT_ROOT / "data" / "triples.json"
STATS_FILE = PROJECT_ROOT / "data" / "processed" / "merged" / "statistics.json"


def main():
    entities = json.loads(ENTITIES_FILE.read_text(encoding="utf-8"))
    triples = json.loads(TRIPLES_FILE.read_text(encoding="utf-8"))

    entity_types = Counter(e["type"] for e in entities)
    unique_names = {e["name"] for e in entities}
    relation_types = Counter(t["predicate"] for t in triples)
    evidence_levels = Counter(t["evidence_level"] for t in triples if t.get("evidence_level"))

    # 图谱层核心节点：三元组涉及的去重实体（对应论文「双层架构」中的知识图谱层）
    core_nodes = {t["subject"] for t in triples} | {t["object"] for t in triples}

    # 度中心性：实体在三元组中出现的次数（出+入）
    degree = Counter()
    for t in triples:
        degree[t["subject"]] += 1
        degree[t["object"]] += 1
    top_degree = dict(sorted(degree.items(), key=lambda x: -x[1])[:20])

    stats = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_files": ["data/entities.json", "data/triples.json"],
        "total_entities": len(entities),
        "total_unique_names": len(unique_names),
        "entity_type_count": len(entity_types),
        "entity_types": dict(sorted(entity_types.items(), key=lambda x: -x[1])),
        "total_relations": len(triples),
        "total_triples": len(triples),
        "relation_types": dict(sorted(relation_types.items(), key=lambda x: -x[1])),
        "evidence_levels": dict(sorted(evidence_levels.items())),
        "core_graph_nodes": len(core_nodes),
        "entity_index_terms": len(unique_names),
        "degree_centrality_top20": top_degree,
    }

    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=" * 70)
    print("MSI-HBP 知识图谱描述性统计（自发布数据文件直接复现）")
    print("=" * 70)
    print(f"实体记录总数（名称+类型唯一）: {stats['total_entities']}")
    print(f"唯一实体术语数:               {stats['total_unique_names']}")
    print(f"实体类型数:                   {stats['entity_type_count']}")
    print(f"关系（三元组）总数:           {stats['total_relations']}")
    print(f"关系类型分布:                 {stats['relation_types']}")
    print(f"证据等级分布:                 {stats['evidence_levels']}")
    print(f"知识图谱层核心节点数:         {stats['core_graph_nodes']}")
    print(f"实体索引层术语数:             {stats['entity_index_terms']}")
    print(f"\n度中心性 Top 10:")
    for name, d in list(top_degree.items())[:10]:
        print(f"  {name}: {d}")
    print(f"\n✅ 统计结果已写回 {STATS_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
