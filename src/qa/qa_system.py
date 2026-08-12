"""
知识图谱问答系统
基于Neo4j和LLM的智能问答
"""
import json
from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import config
from src.utils.llm_client import llm_client
from src.utils.neo4j_client import Neo4jClient


class QASystem:
    """知识图谱问答系统"""
    
    def __init__(self, use_neo4j: bool = True):
        """
        初始化问答系统
        
        Args:
            use_neo4j: 是否使用Neo4j（如果False，则使用JSON文件）
        """
        self.llm = llm_client
        self.use_neo4j = use_neo4j
        
        # 始终加载实体列表（用于实体识别）
        self.load_entities()
        
        if use_neo4j:
            try:
                self.neo4j_client = Neo4jClient()
                if not self.neo4j_client.test_connection():
                    print("⚠️  Neo4j连接失败，将使用JSON文件模式")
                    self.use_neo4j = False
                    self.load_knowledge_from_json()
            except:
                print("⚠️  Neo4j不可用，将使用JSON文件模式")
                self.use_neo4j = False
                self.load_knowledge_from_json()
        else:
            self.load_knowledge_from_json()
    
    def load_entities(self):
        """加载实体列表（用于实体识别）"""
        json_file = config.FINAL_ENTITIES_FILE
        
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果是entities.json，直接是列表
            if isinstance(data, list):
                self.entities = {e['name']: e for e in data}
            else:
                # 如果是完整的知识图谱文件
                self.entities = {e['name']: e for e in data.get('entities', [])}
            
            print(f"✅ 已加载 {len(self.entities)} 个实体用于识别")
        else:
            print("❌ 未找到实体文件")
            self.entities = {}
        
        # 加载同义词
        self.load_synonyms()
    
    def load_synonyms(self):
        """加载同义词映射"""
        synonyms_file = Path(config.DATA_DIR) / "synonyms.json"
        self.synonym_map = {}  # 同义词 -> 标准词
        
        if synonyms_file.exists():
            with open(synonyms_file, 'r', encoding='utf-8') as f:
                synonyms_data = json.load(f)
            
            # 构建同义词映射
            for category, synonym_groups in synonyms_data.items():
                for group in synonym_groups:
                    # 第一个词作为标准词
                    standard_term = group[0]
                    for synonym in group:
                        self.synonym_map[synonym] = standard_term
            
            print(f"✅ 已加载 {len(self.synonym_map)} 个同义词映射")
        else:
            print("⚠️  未找到同义词文件")
    
    def load_knowledge_from_json(self):
        """从JSON文件加载知识（仅JSON模式需要）"""
        json_file = config.FINAL_GRAPH_FILE
        
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取三元组/关系
            self.triples = data.get('triples', data.get('relations', []))
            
            # 构建索引
            self.entity_to_triples = {}
            for triple in self.triples:
                subject = triple.get('subject', '')
                obj = triple.get('object', '')
                
                if subject not in self.entity_to_triples:
                    self.entity_to_triples[subject] = []
                self.entity_to_triples[subject].append(triple)
                
                if obj not in self.entity_to_triples:
                    self.entity_to_triples[obj] = []
                self.entity_to_triples[obj].append(triple)
            
            print(f"✅ 已加载 {len(self.triples)} 个三元组")
        else:
            print("❌ 未找到知识文件")
            self.triples = []
            self.entity_to_triples = {}
    
    def extract_entities_from_question(self, question: str) -> List[str]:
        """
        从问题中提取实体（使用同义词+LLM智能识别）
        
        Args:
            question: 用户问题
        
        Returns:
            提取的实体列表
        """
        found_entities = []
        
        # 1. 先用同义词映射进行替换
        normalized_question = question
        for synonym, standard in self.synonym_map.items():
            if synonym in question:
                normalized_question = normalized_question.replace(synonym, standard)
        
        # 2. 在标准化后的问题中匹配实体
        for entity_name in self.entities.keys():
            if entity_name in normalized_question:
                found_entities.append(entity_name)
        
        # 如果找到了实体，直接返回
        if found_entities:
            found_entities.sort(key=len, reverse=True)
            return found_entities[:5]
        
        # 3. 如果还没找到，使用LLM进行智能识别
        try:
            # 按类型分组实体
            entity_by_type = {}
            for name, entity in self.entities.items():
                entity_type = entity.get('type', '未知')
                if entity_type not in entity_by_type:
                    entity_by_type[entity_type] = []
                entity_by_type[entity_type].append(name)
            
            # 构建实体列表（每个类型取前20个）
            entity_list_text = ""
            for entity_type, names in entity_by_type.items():
                entity_list_text += f"\n【{entity_type}】\n"
                entity_list_text += "、".join(names[:20])
                if len(names) > 20:
                    entity_list_text += f"...等{len(names)}个"
            
            prompt = f"""你是一个中医知识图谱的实体识别专家。请从用户问题中识别出相关的实体。

【用户问题】
{question}

【知识图谱中的实体】
{entity_list_text}

【识别要求】
1. 识别问题中提到的疾病、症状、中药、方剂、治疗方法、病机等实体
2. 考虑同义词和近义词（如"头疼"对应"头痛"）
3. 考虑部分匹配（如"精神应激性"可能指"精神应激性高血压"）
4. 如果问题很模糊，尝试推断用户可能关心的实体
5. 最多返回5个最相关的实体

【输出格式】
只输出实体名称，用逗号分隔，不要有其他解释。如果没有找到相关实体，输出"无"。

示例：
- 问题："头疼怎么办" → 头痛
- 问题："精神应激性有什么症状" → 精神应激性高血压
- 问题："钩藤的作用" → 钩藤
- 问题："失眠和高血压的关系" → 失眠,高血压

请开始识别："""
            
            response = self.llm.chat([{"role": "user", "content": prompt}])
            
            # 解析LLM返回的实体
            if response and response.strip() and response.strip() != "无":
                entities_text = response.strip()
                # 分割实体
                potential_entities = [e.strip() for e in entities_text.replace('、', ',').split(',')]
                
                # 验证实体是否在知识库中
                for entity in potential_entities:
                    if entity in self.entities:
                        found_entities.append(entity)
                    else:
                        # 模糊匹配
                        for entity_name in self.entities.keys():
                            if entity in entity_name or entity_name in entity:
                                found_entities.append(entity_name)
                                break
                
                if found_entities:
                    return found_entities[:5]
        
        except Exception as e:
            print(f"⚠️  LLM实体识别失败: {e}")
        
        return found_entities[:5]
    
    def query_neo4j(self, question: str, entities: List[str]) -> List[Dict]:
        """
        查询Neo4j获取相关知识
        
        Args:
            question: 用户问题
            entities: 提取的实体
        
        Returns:
            查询结果
        """
        if not self.use_neo4j or not entities:
            return []
        
        results = []
        seen = set()  # 去重
        
        for entity in entities:
            # 查询与该实体相关的三元组（出边）
            query = """
            MATCH (a {name: $entity, project: $project})-[r]->(b)
            RETURN a.name AS subject, type(r) AS relation, b.name AS object, 
                   labels(a)[0] AS subject_type, labels(b)[0] AS object_type
            LIMIT 30
            """
            
            try:
                result = self.neo4j_client.run_cypher(query, {
                    'entity': entity,
                    'project': config.PROJECT_NAME
                })
                for item in result:
                    key = f"{item['subject']}-{item['relation']}-{item['object']}"
                    if key not in seen:
                        results.append(item)
                        seen.add(key)
            except Exception as e:
                print(f"⚠️  查询出边失败: {e}")
            
            # 反向查询（入边）
            query = """
            MATCH (a)-[r]->(b {name: $entity, project: $project})
            RETURN a.name AS subject, type(r) AS relation, b.name AS object, 
                   labels(a)[0] AS subject_type, labels(b)[0] AS object_type
            LIMIT 30
            """
            
            try:
                result = self.neo4j_client.run_cypher(query, {
                    'entity': entity,
                    'project': config.PROJECT_NAME
                })
                for item in result:
                    key = f"{item['subject']}-{item['relation']}-{item['object']}"
                    if key not in seen:
                        results.append(item)
                        seen.add(key)
            except Exception as e:
                print(f"⚠️  查询入边失败: {e}")
        
        # 如果结果太少，尝试扩展查询（2跳）
        if len(results) < 5 and entities:
            for entity in entities[:2]:  # 只对前2个实体做2跳查询
                query = """
                MATCH (a {name: $entity, project: $project})-[r1]->(b)-[r2]->(c)
                WHERE b.project = $project AND c.project = $project
                RETURN b.name AS subject, type(r2) AS relation, c.name AS object,
                       labels(b)[0] AS subject_type, labels(c)[0] AS object_type
                LIMIT 20
                """
                
                try:
                    result = self.neo4j_client.run_cypher(query, {
                        'entity': entity,
                        'project': config.PROJECT_NAME
                    })
                    for item in result:
                        key = f"{item['subject']}-{item['relation']}-{item['object']}"
                        if key not in seen:
                            results.append(item)
                            seen.add(key)
                except Exception as e:
                    print(f"⚠️  2跳查询失败: {e}")
        
        return results
    
    def query_json(self, entities: List[str]) -> List[Dict]:
        """
        从JSON数据查询相关知识
        
        Args:
            entities: 提取的实体
        
        Returns:
            查询结果
        """
        results = []
        
        for entity in entities:
            if entity in self.entity_to_triples:
                triples = self.entity_to_triples[entity]
                for triple in triples[:20]:  # 限制数量
                    results.append({
                        'subject': triple.get('subject', ''),
                        'relation': triple.get('relation', ''),
                        'object': triple.get('object', ''),
                        'subject_type': self.entities.get(triple.get('subject', ''), {}).get('type', ''),
                        'object_type': self.entities.get(triple.get('object', ''), {}).get('type', '')
                    })
        
        return results
    
    def generate_answer(self, question: str, knowledge: List[Dict]) -> str:
        """
        基于知识生成答案
        
        Args:
            question: 用户问题
            knowledge: 相关知识
        
        Returns:
            生成的答案
        """
        if not knowledge:
            return "抱歉，我在知识库中没有找到相关信息。您可以尝试：\n1. 使用更具体的中医术语\n2. 查看示例问题了解提问方式\n3. 在知识浏览中查看可用的实体"
        
        # 构建知识上下文
        knowledge_text = "相关知识：\n"
        for i, item in enumerate(knowledge[:15], 1):  # 限制15条
            knowledge_text += f"{i}. {item['subject']} -[{item['relation']}]-> {item['object']}\n"
        
        # 优化的提示词
        prompt = f"""你是一个专业的中医知识图谱问答助手，专门回答关于精神应激性高血压（MSI-HBP）的问题。

【用户问题】
{question}

【知识图谱中的相关知识】
{knowledge_text}

【回答要求】
1. 基于上述知识图谱中的信息回答问题
2. 使用专业的中医术语，但要通俗易懂
3. 回答要有逻辑性和条理性
4. 如果知识不足以完整回答，请说明已知的部分
5. 可以适当解释中医概念，帮助理解
6. 回答长度控制在150-300字之间
7. 如果涉及多个方面，可以分点说明

【回答格式】
- 直接回答问题，不要重复问题
- 使用自然流畅的语言
- 重要的实体和概念可以加粗
- 如有多个要点，使用序号或分段

请开始回答："""
        
        try:
            answer = self.llm.chat([
                {"role": "user", "content": prompt}
            ])
            return answer
        except Exception as e:
            return f"生成答案时出错: {e}\n\n相关知识：\n" + "\n".join([f"- {k['subject']} -[{k['relation']}]-> {k['object']}" for k in knowledge[:5]])
    
    def answer(self, question: str) -> Dict:
        """
        回答用户问题
        
        Args:
            question: 用户问题
        
        Returns:
            包含答案和相关知识的字典
        """
        print(f"\n问题: {question}")
        
        # 1. 提取实体
        entities = self.extract_entities_from_question(question)
        print(f"识别实体: {entities}")
        
        # 2. 查询知识
        if self.use_neo4j:
            knowledge = self.query_neo4j(question, entities)
        else:
            knowledge = self.query_json(entities)
        
        print(f"找到 {len(knowledge)} 条相关知识")
        
        # 3. 生成答案
        answer = self.generate_answer(question, knowledge)
        
        return {
            'question': question,
            'entities': entities,
            'knowledge': knowledge[:10],  # 返回前10条
            'answer': answer
        }
    
    def batch_answer(self, questions: List[str]) -> List[Dict]:
        """
        批量回答问题
        
        Args:
            questions: 问题列表
        
        Returns:
            答案列表
        """
        results = []
        for question in questions:
            result = self.answer(question)
            results.append(result)
        return results


if __name__ == "__main__":
    # 测试问答系统
    qa = QASystem(use_neo4j=False)
    
    # 测试问题
    test_questions = [
        "精神应激性高血压有什么症状？",
        "肝阳上亢怎么治疗？",
        "天麻钩藤饮的作用是什么？",
        "失眠和高血压有什么关系？"
    ]
    
    print("\n" + "=" * 70)
    print("知识图谱问答系统测试")
    print("=" * 70)
    
    for question in test_questions:
        result = qa.answer(question)
        print(f"\n答案: {result['answer']}")
        print("-" * 70)
