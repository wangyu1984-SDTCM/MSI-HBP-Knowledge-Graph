"""
知识融合模块
实现实体对齐、实体消歧、知识去重等功能
"""
import json
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import config


class KnowledgeFusion:
    """知识融合类"""
    
    def __init__(self):
        """初始化知识融合器"""
        self.entity_types = config.ENTITY_TYPES
        self.relation_types = config.RELATION_TYPES
        
        # 实体别名映射（可扩展）
        self.entity_aliases = {
            "精神应激性高血压": ["MSI-HBP", "应激性高血压", "精神性高血压"],
            "高血压": ["高血压病", "原发性高血压"],
            "肝阳上亢": ["肝阳亢盛", "肝阳偏亢"],
            "心肾不交": ["心肾失交", "心肾不济"],
            "天麻钩藤饮": ["天麻钩藤汤"],
            "逍遥散": ["逍遥丸"],
        }
        
        # 反向映射
        self.alias_to_standard = {}
        for standard, aliases in self.entity_aliases.items():
            for alias in aliases:
                self.alias_to_standard[alias] = standard
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
        
        Returns:
            相似度（0-1）
        """
        return SequenceMatcher(None, str1, str2).ratio()
    
    def normalize_entity_name(self, name: str) -> str:
        """
        标准化实体名称
        
        Args:
            name: 实体名称
        
        Returns:
            标准化后的名称
        """
        # 去除空格和特殊字符
        name = name.strip()
        
        # 检查是否有别名映射
        if name in self.alias_to_standard:
            return self.alias_to_standard[name]
        
        return name
    
    def align_entities(self, entities: List[Dict]) -> Tuple[List[Dict], Dict[str, str]]:
        """
        实体对齐：将相似的实体合并
        
        Args:
            entities: 实体列表
        
        Returns:
            (对齐后的实体列表, 实体映射字典)
        """
        print("\n正在进行实体对齐...")
        
        # 按类型分组
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get('type', '未知')
            entity_name = entity.get('name', '')
            if entity_name:
                entities_by_type[entity_type].append(entity_name)
        
        aligned_entities = []
        entity_mapping = {}  # 原名称 -> 标准名称
        
        for entity_type, names in entities_by_type.items():
            # 对每种类型的实体进行对齐
            seen_names = set()  # 已处理的标准名称
            
            for name in names:
                # 标准化名称
                normalized_name = self.normalize_entity_name(name)
                
                # 检查是否已存在
                if normalized_name in seen_names:
                    # 已存在，直接映射
                    entity_mapping[name] = normalized_name
                else:
                    # 检查是否有高度相似的实体
                    found_similar = False
                    
                    for existing_name in seen_names:
                        # 只对长度相近的实体进行相似度比较（避免误合并）
                        len_diff = abs(len(normalized_name) - len(existing_name))
                        if len_diff <= 2:
                            similarity = self.calculate_similarity(normalized_name, existing_name)
                            
                            # 相似度阈值0.95（非常严格）
                            if similarity > 0.95:
                                entity_mapping[name] = existing_name
                                found_similar = True
                                break
                    
                    if not found_similar:
                        # 新实体
                        entity_mapping[name] = normalized_name
                        seen_names.add(normalized_name)
                        aligned_entities.append({
                            'name': normalized_name,
                            'type': entity_type
                        })
        
        print(f"  原始实体数: {len(entities)}")
        print(f"  对齐后实体数: {len(aligned_entities)}")
        print(f"  合并了 {len(entities) - len(aligned_entities)} 个重复实体")
        
        return aligned_entities, entity_mapping
    
    def deduplicate_triples(
        self,
        triples: List[Dict],
        entity_mapping: Dict[str, str]
    ) -> List[Dict]:
        """
        三元组去重
        
        Args:
            triples: 三元组列表
            entity_mapping: 实体映射字典
        
        Returns:
            去重后的三元组列表
        """
        print("\n正在进行三元组去重...")
        
        seen_triples = set()
        deduplicated_triples = []
        
        for triple in triples:
            subject = triple.get('subject', '')
            relation = triple.get('relation', '')
            obj = triple.get('object', '')
            
            if not (subject and relation and obj):
                continue
            
            # 使用映射后的实体名称
            mapped_subject = entity_mapping.get(subject, subject)
            mapped_object = entity_mapping.get(obj, obj)
            
            # 创建三元组键
            triple_key = (mapped_subject, relation, mapped_object)
            
            if triple_key not in seen_triples:
                seen_triples.add(triple_key)
                deduplicated_triples.append({
                    'subject': mapped_subject,
                    'relation': relation,
                    'object': mapped_object
                })
        
        print(f"  原始三元组数: {len(triples)}")
        print(f"  去重后三元组数: {len(deduplicated_triples)}")
        print(f"  去除了 {len(triples) - len(deduplicated_triples)} 个重复三元组")
        
        return deduplicated_triples
    
    def validate_triples(self, triples: List[Dict], entities: List[Dict]) -> List[Dict]:
        """
        验证三元组的有效性
        
        Args:
            triples: 三元组列表
            entities: 实体列表
        
        Returns:
            有效的三元组列表
        """
        print("\n正在验证三元组...")
        
        # 构建实体名称集合
        entity_names = {entity['name'] for entity in entities}
        
        valid_triples = []
        invalid_count = 0
        
        for triple in triples:
            subject = triple.get('subject', '')
            obj = triple.get('object', '')
            
            # 检查主体和客体是否都存在于实体列表中
            if subject in entity_names and obj in entity_names:
                valid_triples.append(triple)
            else:
                invalid_count += 1
        
        print(f"  有效三元组: {len(valid_triples)}")
        print(f"  无效三元组: {invalid_count}")
        
        return valid_triples
    
    def fuse_knowledge(
        self,
        input_file: str,
        output_file: str = None
    ) -> Dict:
        """
        执行完整的知识融合流程
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
        
        Returns:
            融合后的知识
        """
        print("\n" + "=" * 70)
        print("知识融合")
        print("=" * 70)
        
        # 读取输入文件
        print(f"\n正在读取输入文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        triples = data.get('triples', [])
        
        print(f"  原始实体数: {len(entities)}")
        print(f"  原始三元组数: {len(triples)}")
        
        # 1. 实体对齐
        aligned_entities, entity_mapping = self.align_entities(entities)
        
        # 2. 三元组去重
        deduplicated_triples = self.deduplicate_triples(triples, entity_mapping)
        
        # 3. 验证三元组
        valid_triples = self.validate_triples(deduplicated_triples, aligned_entities)
        
        # 4. 统计信息
        entity_type_counts = defaultdict(int)
        for entity in aligned_entities:
            entity_type_counts[entity['type']] += 1
        
        relation_type_counts = defaultdict(int)
        for triple in valid_triples:
            relation_type_counts[triple['relation']] += 1
        
        # 构建结果
        result = {
            'project': config.PROJECT_NAME,
            'entities': aligned_entities,
            'triples': valid_triples,
            'statistics': {
                'total_entities': len(aligned_entities),
                'total_triples': len(valid_triples),
                'entity_types': dict(entity_type_counts),
                'relation_types': dict(relation_type_counts)
            },
            'fusion_info': {
                'original_entities': len(entities),
                'original_triples': len(triples),
                'merged_entities': len(entities) - len(aligned_entities),
                'removed_triples': len(triples) - len(valid_triples)
            }
        }
        
        # 保存结果
        if output_file:
            print(f"\n正在保存融合结果...")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  结果已保存到: {output_file}")
        
        print("\n" + "=" * 70)
        print("✅ 知识融合完成！")
        print("=" * 70)
        
        print(f"\n融合统计:")
        print(f"  最终实体数: {result['statistics']['total_entities']}")
        print(f"  最终三元组数: {result['statistics']['total_triples']}")
        print(f"  合并实体数: {result['fusion_info']['merged_entities']}")
        print(f"  去除三元组数: {result['fusion_info']['removed_triples']}")
        
        return result


if __name__ == "__main__":
    # 测试知识融合
    fusion = KnowledgeFusion()
    
    input_file = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    output_file = config.PROCESSED_DATA_DIR / "fused_knowledge" / "msi_hbp_fused.json"
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    result = fusion.fuse_knowledge(str(input_file), str(output_file))
