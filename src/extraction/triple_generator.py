"""
三元组生成模块
从文本中抽取知识三元组（实体+关系）
"""
import json
from typing import List, Dict, Set, Tuple
from pathlib import Path
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import config
from src.utils.llm_client import llm_client


class TripleGenerator:
    """三元组生成器类"""
    
    def __init__(self):
        """初始化三元组生成器"""
        self.llm = llm_client
        self.entity_types = config.ENTITY_TYPES
        self.relation_types = config.RELATION_TYPES
        self.relation_definitions = config.RELATION_DEFINITIONS
    
    def create_extraction_prompt(self, text: str) -> str:
        """
        创建知识抽取的提示词
        
        Args:
            text: 输入文本
        
        Returns:
            提示词
        """
        prompt = f"""你是一个中医知识图谱构建专家。请从以下文本中抽取关于精神应激性高血压（MSI-HBP）的中医知识三元组。

文本内容：
{text[:3000]}

请按照以下规则抽取：

1. **实体类型**（6种）：
   - 疾病：如精神应激性高血压、高血压、头痛等
   - 症状：如头痛、失眠、焦虑、心悸、眩晕等
   - 病机：如肝阳上亢、心肾不交、肝郁气滞、痰浊上扰等
   - 中药：如黄芪、当归、天麻、钩藤、石决明等
   - 方剂：如天麻钩藤饮、逍遥散、六味地黄丸等
   - 治则治法：如平肝潜阳、疏肝解郁、滋阴降火、化痰降浊等

2. **关系类型**（4种）：
   - 使用：治则治法/病机 -> 中药/方剂/治则治法
   - 治疗：中药/方剂/治则治法 -> 疾病/症状/病机
   - 由...组成：方剂 -> 中药
   - 引起：病机 -> 疾病/症状

3. **输出格式**（JSON）：
{{
  "entities": [
    {{"name": "实体名称", "type": "实体类型"}},
    ...
  ],
  "triples": [
    {{"subject": "主体实体", "relation": "关系类型", "object": "客体实体"}},
    ...
  ]
}}

**重要规则**：
- 实体名称要标准化（如"平肝潜阳"和"平抑肝阳"统一为"平肝潜阳"）
- 关系必须符合定义的主客体类型
- 只抽取明确提到的知识，不要推理
- 确保三元组中的实体都在entities列表中

请直接输出JSON，不要其他说明文字。"""
        return prompt
    
    def extract_from_text(self, text: str) -> Dict[str, List]:
        """
        从文本中抽取知识三元组
        
        Args:
            text: 输入文本
        
        Returns:
            包含entities和triples的字典
        """
        prompt = self.create_extraction_prompt(text)
        
        try:
            result = self.llm.extract_json(prompt)
            
            # 验证结果格式
            if "entities" not in result:
                result["entities"] = []
            if "triples" not in result:
                result["triples"] = []
            
            return result
        except Exception as e:
            print(f"抽取失败: {e}")
            return {"entities": [], "triples": []}
    
    def extract_from_file(
        self,
        file_path: str,
        chunk_size: int = 3000,
        overlap: int = 200
    ) -> Dict[str, any]:
        """
        从文件中抽取知识三元组
        
        Args:
            file_path: 文本文件路径
            chunk_size: 每块文本的大小（字符数）
            overlap: 块之间的重叠大小
        
        Returns:
            抽取结果
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分块处理
        chunks = self._split_text(text, chunk_size, overlap)
        
        all_entities = []
        all_triples = []
        seen_entities: Set[Tuple[str, str]] = set()
        seen_triples: Set[Tuple[str, str, str]] = set()
        
        for chunk in tqdm(chunks, desc=f"处理 {Path(file_path).name}"):
            result = self.extract_from_text(chunk)
            
            # 去重实体
            for entity in result.get("entities", []):
                entity_key = (entity.get("name"), entity.get("type"))
                if entity_key not in seen_entities and entity_key[0]:
                    seen_entities.add(entity_key)
                    all_entities.append(entity)
            
            # 去重三元组
            for triple in result.get("triples", []):
                triple_key = (
                    triple.get("subject"),
                    triple.get("relation"),
                    triple.get("object")
                )
                if triple_key not in seen_triples and all(triple_key):
                    seen_triples.add(triple_key)
                    all_triples.append(triple)
        
        return {
            "entities": all_entities,
            "triples": all_triples,
            "source_file": file_path
        }
    
    def extract_from_directory(
        self,
        directory: str,
        output_path: str = None,
        pattern: str = "*.txt"
    ) -> Dict[str, any]:
        """
        从目录中的所有文件抽取知识三元组
        
        Args:
            directory: 文本文件目录
            output_path: 输出JSON文件路径
            pattern: 文件匹配模式
        
        Returns:
            合并后的抽取结果
        """
        dir_path = Path(directory)
        txt_files = list(dir_path.glob(pattern))
        
        if not txt_files:
            print(f"在目录 {directory} 中未找到文本文件")
            return {"entities": [], "triples": []}
        
        print(f"找到 {len(txt_files)} 个文本文件")
        
        all_results = []
        for txt_file in txt_files:
            result = self.extract_from_file(str(txt_file))
            all_results.append(result)
        
        # 合并所有结果
        merged = self._merge_results(all_results)
        
        # 保存结果
        if output_path:
            self._save_results(merged, output_path)
        
        return merged
    
    def _split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        分割文本为块
        
        Args:
            text: 输入文本
            chunk_size: 块大小
            overlap: 重叠大小
        
        Returns:
            文本块列表
        """
        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _merge_results(self, results: List[Dict]) -> Dict[str, any]:
        """
        合并多个抽取结果
        
        Args:
            results: 结果列表
        
        Returns:
            合并后的结果
        """
        merged_entities = []
        merged_triples = []
        seen_entities: Set[Tuple[str, str]] = set()
        seen_triples: Set[Tuple[str, str, str]] = set()
        
        for result in results:
            for entity in result.get("entities", []):
                key = (entity.get("name"), entity.get("type"))
                if key not in seen_entities and key[0]:
                    seen_entities.add(key)
                    merged_entities.append(entity)
            
            for triple in result.get("triples", []):
                key = (
                    triple.get("subject"),
                    triple.get("relation"),
                    triple.get("object")
                )
                if key not in seen_triples and all(key):
                    seen_triples.add(key)
                    merged_triples.append(triple)
        
        return {
            "project": config.PROJECT_NAME,
            "entities": merged_entities,
            "triples": merged_triples,
            "statistics": {
                "total_entities": len(merged_entities),
                "total_triples": len(merged_triples),
                "entity_types": self._count_by_type(merged_entities, "type"),
                "relation_types": self._count_by_type(merged_triples, "relation")
            }
        }
    
    def _count_by_type(self, items: List[Dict], key: str) -> Dict[str, int]:
        """统计各类型的数量"""
        counts = {}
        for item in items:
            item_type = item.get(key, "未知")
            counts[item_type] = counts.get(item_type, 0) + 1
        return counts
    
    def _save_results(self, results: Dict, output_path: str):
        """保存结果到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n知识抽取完成！")
        print(f"实体总数: {results['statistics']['total_entities']}")
        print(f"三元组总数: {results['statistics']['total_triples']}")
        print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    # 测试三元组生成
    generator = TripleGenerator()
    
    # 从文献目录抽取
    literature_dir = config.RAW_DATA_DIR / "literature"
    output_path = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    
    results = generator.extract_from_directory(
        str(literature_dir),
        str(output_path)
    )
