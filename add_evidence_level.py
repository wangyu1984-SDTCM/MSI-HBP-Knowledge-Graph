"""
为知识三元组补充 evidence_level 证据等级字段（v2.0）

分级规则（与论文大修说明一致）：
  A 级：可追溯至具体来源文献（source 以「文献:」开头）
  B 级：出自权威教材《方剂学》（source == 中医方剂学）
  C 级：来自公认中医基础理论（中医治法理论 / 中医病机理论 / 中医治则理论）

处理文件：
  data/triples.json
  data/processed/merged/relations.json
  data/processed/merged/msi_hbp_merged.json（relations 与 triples 两处）
"""
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

GRADE_B_SOURCES = {"中医方剂学"}
GRADE_C_SOURCES = {"中医治法理论", "中医病机理论", "中医治则理论"}


def grade_source(source: str) -> str:
    if source and source.startswith("文献"):
        return "A"
    if source in GRADE_B_SOURCES:
        return "B"
    if source in GRADE_C_SOURCES:
        return "C"
    raise ValueError(f"无法分级的 source: {source!r}")


def annotate(triples):
    for t in triples:
        t["evidence_level"] = grade_source(t.get("source", ""))
    return triples


def main():
    targets = [
        PROJECT_ROOT / "data" / "triples.json",
        PROJECT_ROOT / "data" / "processed" / "merged" / "relations.json",
        PROJECT_ROOT / "data" / "processed" / "merged" / "msi_hbp_merged.json",
    ]

    for path in targets:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        if isinstance(data, list):
            annotate(data)
            changed = True
        else:
            for key in ("relations", "triples"):
                if isinstance(data.get(key), list) and data[key]:
                    annotate(data[key])
                    changed = True
            # 同步更新统计块中的证据等级分布
            stats = data.get("statistics")
            if isinstance(stats, dict):
                rels = data.get("relations") or data.get("triples") or []
                if rels:
                    stats["evidence_levels"] = dict(
                        Counter(t["evidence_level"] for t in rels)
                    )

        if not changed:
            print(f"⚠️  {path} 中未找到三元组数据，跳过")
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已更新 {path.relative_to(PROJECT_ROOT)}")

    # 校验分布
    triples = json.load(open(targets[0], "r", encoding="utf-8"))
    dist = Counter(t["evidence_level"] for t in triples)
    print(f"\n证据等级分布: A={dist.get('A', 0)}, B={dist.get('B', 0)}, C={dist.get('C', 0)}")
    expected = {"A": 171, "B": 84, "C": 57}
    if {k: v for k, v in dist.items()} != expected:
        print(f"❌ 与论文声明不一致，期望 {expected}")
        sys.exit(1)
    print("✅ 与论文声明的 A=171 / B=84 / C=57 完全一致")


if __name__ == "__main__":
    main()
