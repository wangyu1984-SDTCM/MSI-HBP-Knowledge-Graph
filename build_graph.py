"""
构建Neo4j知识图谱
"""
import sys
import json
from pathlib import Path
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.utils.config import config
from src.utils.neo4j_client import Neo4jClient


def main():
    print("\n" + "=" * 70)
    print("构建MSI-HBP知识图谱")
    print("=" * 70)
    
    # 测试Neo4j连接
    print("\n正在测试Neo4j连接...")
    client = Neo4jClient()
    
    if not client.test_connection():
        print("\n❌ Neo4j连接失败！")
        print("\n请确保:")
        print("  1. Neo4j已启动")
        print("  2. 端口7687可访问")
        print("  3. 用户名密码正确（neo4j/123456）")
        return
    
    print("✅ Neo4j连接成功！")
    
    # 读取合并后的知识图谱数据
    merged_file = config.FINAL_GRAPH_FILE
    
    if not merged_file.exists():
        print(f"\n❌ 合并数据文件不存在: {merged_file}")
        print(f"请先运行: python merge_and_deduplicate_data.py")
        return
    
    print(f"\n正在读取合并后的知识图谱数据...")
    with open(merged_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data.get('entities', [])
    relations = data.get('relations', [])
    
    print(f"\n数据版本: {data.get('version', 'N/A')}")
    print(f"数据描述: {data.get('description', 'N/A')}")
    
    print(f"  实体数: {len(entities)}")
    print(f"  关系数: {len(relations)}")
    
    # 显示统计信息
    stats = data.get('statistics', {})
    if stats:
        print(f"\n实体类型分布（Top 10）:")
        entity_types = stats.get('entity_types', {})
        for entity_type, count in sorted(entity_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  - {entity_type}: {count}")
        
        print(f"\n关系类型分布:")
        relation_types = stats.get('relation_types', {})
        for rel_type, count in sorted(relation_types.items(), key=lambda x: -x[1]):
            print(f"  - {rel_type}: {count}")
    
    # 询问是否清空现有数据
    print(f"\n⚠️  是否清空现有的MSI-HBP数据？")
    choice = input("  输入 'yes' 清空，其他键跳过: ")
    
    if choice.lower() == 'yes':
        print("\n正在清空现有数据...")
        client.clear_project_data(config.PROJECT_NAME)
        print("✅ 清空完成")
    
    # 创建节点
    print(f"\n正在创建节点...")
    
    # 实体类型映射
    entity_type_map = config.ENTITY_TYPE_MAP
    
    node_queries = []
    
    for entity in tqdm(entities, desc="准备节点"):
        entity_type = entity.get('type', '未知')
        entity_name = entity.get('name', '')
        
        if not entity_name:
            continue
        
        label = entity_type_map.get(entity_type, entity_type).replace('`', '')
        query = f"""
        MERGE (n:`{label}` {{name: $name, project: $project}})
        """
        
        params = {
            'name': entity_name,
            'project': config.PROJECT_NAME
        }
        
        node_queries.append((query, params))
    
    # 批量执行
    print(f"\n正在批量创建 {len(node_queries)} 个节点...")
    client.run_batch_cypher(node_queries, show_progress=True)
    print("✅ 节点创建完成")
    
    # 创建关系
    print(f"\n正在创建关系...")
    
    relation_queries = []
    for relation in tqdm(relations, desc="准备关系"):
        subject = relation.get('subject', '')
        predicate = relation.get('predicate', '')
        obj = relation.get('object', '')
        subject_type = relation.get('subject_type', '')
        object_type = relation.get('object_type', '')
        
        if not (subject and predicate and obj and subject_type and object_type):
            continue
        
        # 清理关系类型（Neo4j不允许某些字符）
        predicate_clean = predicate.replace('...', '_').replace('.', '_').replace(' ', '_')
        subject_label = entity_type_map.get(subject_type, subject_type).replace('`', '')
        object_label = entity_type_map.get(object_type, object_type).replace('`', '')
        
        query = f"""
        MATCH (a:`{subject_label}` {{name: $subject, project: $project}})
        MATCH (b:`{object_label}` {{name: $object, project: $project}})
        MERGE (a)-[r:`{predicate_clean}`]->(b)
        SET r.source = $source
        SET r.evidence_level = $evidence_level
        """

        params = {
            'subject': subject,
            'object': obj,
            'project': config.PROJECT_NAME,
            'source': relation.get('source', ''),
            'evidence_level': relation.get('evidence_level', '')
        }
        
        relation_queries.append((query, params))
    
    # 批量执行
    print(f"\n正在批量创建 {len(relation_queries)} 个关系...")
    client.run_batch_cypher(relation_queries, show_progress=True)
    print("✅ 关系创建完成")
    
    # 获取统计信息
    print(f"\n正在获取图谱统计...")
    stats = client.get_graph_statistics(config.PROJECT_NAME)
    
    print(f"\n" + "=" * 70)
    print("🎉 知识图谱构建完成！")
    print("=" * 70)
    
    print(f"\n图谱统计:")
    print(f"  节点总数: {stats.get('total_nodes', 0)}")
    print(f"  关系总数: {stats.get('total_relationships', 0)}")
    
    if stats.get('node_types'):
        print(f"\n  节点类型分布:")
        for node_type, count in sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {node_type}: {count}")
    
    if stats.get('relationship_types'):
        print(f"\n  关系类型分布:")
        for rel_type, count in sorted(stats['relationship_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {rel_type}: {count}")
    
    print(f"\n💡 下一步:")
    print(f"  1. 访问 Neo4j 浏览器: http://localhost:7474")
    print(f"  2. 用户名: neo4j")
    print(f"  3. 密码: 123456")
    print(f"\n  示例查询:")
    print(f"  MATCH (n {{project: 'MSI-HBP'}}) RETURN n LIMIT 25")
    print(f"  MATCH (a {{project: 'MSI-HBP'}})-[r]->(b) RETURN a, r, b LIMIT 25")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
