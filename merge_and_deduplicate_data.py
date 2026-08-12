"""Build the canonical MSI-HBP knowledge graph files."""

import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
MERGED_DIR = PROJECT_ROOT / "data" / "processed" / "merged"
SOURCE_ENTITIES_FILE = MERGED_DIR / "entities_cleaned.json"
SOURCE_RELATIONS_FILE = MERGED_DIR / "relations.json"
FINAL_ENTITIES_FILE = MERGED_DIR / "entities.json"
ATTACHMENT_ENTITIES_FILE = PROJECT_ROOT / "data" / "entities.json"
FINAL_GRAPH_FILE = MERGED_DIR / "msi_hbp_merged.json"
STATISTICS_FILE = MERGED_DIR / "statistics.json"


RELATION_TYPE_PREFERENCES = {
    "组成": {
        "subject": ["方剂"],
        "object": ["中药"],
    },
    "使用": {
        "subject": ["治则治法", "病机", "病因病机"],
        "object": ["方剂", "中药", "治则治法", "病机", "病因病机"],
    },
    "治疗": {
        "subject": ["中药", "方剂", "治则治法"],
        "object": ["疾病", "症状", "病机", "病因病机"],
    },
    "引起": {
        "subject": ["病机", "病因病机"],
        "object": ["疾病", "症状"],
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def deduplicate_entities(entities):
    seen = set()
    result = []

    for entity in entities:
        name = entity.get("name", "").strip()
        entity_type = entity.get("type", "").strip()
        key = (name, entity_type)
        if not all(key) or key in seen:
            continue
        seen.add(key)
        result.append({"name": name, "type": entity_type})

    return result


def choose_endpoint_type(name, original_type, relation, side, entity_types_by_name):
    available_types = entity_types_by_name.get(name, [])
    if original_type in available_types:
        return original_type

    preferences = RELATION_TYPE_PREFERENCES.get(relation, {}).get(side, [])
    for entity_type in preferences:
        if entity_type in available_types:
            return entity_type

    if available_types:
        return available_types[0]

    raise ValueError(f"Relation endpoint is missing from entities: {name}")


def normalize_relations(relations, entities):
    entity_types_by_name = defaultdict(list)
    for entity in entities:
        entity_types_by_name[entity["name"]].append(entity["type"])

    seen = set()
    normalized = []
    for relation in relations:
        subject = relation.get("subject", "").strip()
        predicate = relation.get("predicate", relation.get("relation", "")).strip()
        obj = relation.get("object", "").strip()
        if not (subject and predicate and obj):
            continue

        subject_type = choose_endpoint_type(
            subject,
            relation.get("subject_type", "").strip(),
            predicate,
            "subject",
            entity_types_by_name,
        )
        object_type = choose_endpoint_type(
            obj,
            relation.get("object_type", "").strip(),
            predicate,
            "object",
            entity_types_by_name,
        )

        key = (subject, predicate, obj)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "subject": subject,
                "subject_type": subject_type,
                "predicate": predicate,
                "object": obj,
                "object_type": object_type,
                "source": relation.get("source", ""),
            }
        )

    return normalized


def validate_graph(entities, relations) -> None:
    entity_keys = {(entity["name"], entity["type"]) for entity in entities}
    if len(entity_keys) != len(entities):
        raise ValueError("Duplicate name/type entity records remain")

    relation_keys = set()
    for relation in relations:
        subject_key = (relation["subject"], relation["subject_type"])
        object_key = (relation["object"], relation["object_type"])
        if subject_key not in entity_keys or object_key not in entity_keys:
            raise ValueError(f"Invalid relation endpoints: {relation}")

        relation_key = (
            relation["subject"],
            relation["predicate"],
            relation["object"],
        )
        if relation_key in relation_keys:
            raise ValueError(f"Duplicate relation remains: {relation_key}")
        relation_keys.add(relation_key)


def build_statistics(entities, relations):
    entity_types = Counter(entity["type"] for entity in entities)
    relation_types = Counter(relation["predicate"] for relation in relations)
    return {
        "total_entities": len(entities),
        "total_unique_names": len({entity["name"] for entity in entities}),
        "total_relations": len(relations),
        "total_triples": len(relations),
        "entity_types": dict(sorted(entity_types.items())),
        "relation_types": dict(sorted(relation_types.items())),
    }


def main() -> None:
    source_entities = load_json(SOURCE_ENTITIES_FILE)
    source_relations = load_json(SOURCE_RELATIONS_FILE)

    entities = deduplicate_entities(source_entities)
    relations = normalize_relations(source_relations, entities)
    validate_graph(entities, relations)
    statistics = build_statistics(entities, relations)

    triples = [
        {
            "subject": relation["subject"],
            "subject_type": relation["subject_type"],
            "relation": relation["predicate"],
            "object": relation["object"],
            "object_type": relation["object_type"],
            "source": relation["source"],
        }
        for relation in relations
    ]
    graph = {
        "project": "MSI-HBP",
        "version": "3.0",
        "description": "精神应激性高血压知识图谱 - 重分类与唯一性约束版",
        "statistics": statistics,
        "entities": entities,
        "relations": relations,
        "triples": triples,
    }

    write_json(SOURCE_ENTITIES_FILE, entities)
    write_json(FINAL_ENTITIES_FILE, entities)
    write_json(ATTACHMENT_ENTITIES_FILE, entities)
    write_json(SOURCE_RELATIONS_FILE, relations)
    write_json(PROJECT_ROOT / "data" / "triples.json", relations)
    write_json(FINAL_GRAPH_FILE, graph)
    write_json(STATISTICS_FILE, statistics)

    removed_duplicates = len(source_entities) - len(entities)
    print(f"Entity records: {len(source_entities)} -> {len(entities)}")
    print(f"Removed duplicate records: {removed_duplicates}")
    print(f"Unique entity names: {statistics['total_unique_names']}")
    print(f"Relations: {len(relations)}")


if __name__ == "__main__":
    main()
