"""
知识挖掘模块
实现网络分析、社区发现、模式挖掘等功能
"""
import json
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import networkx as nx
from networkx.algorithms import community

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import config


class KnowledgeMining:
    """知识挖掘类"""
    
    def __init__(self):
        """初始化知识挖掘器"""
        self.graph = nx.DiGraph()
        self.entity_types = config.ENTITY_TYPES
        self.relation_types = config.RELATION_TYPES
    
    def build_graph(self, entities: List[Dict], triples: List[Dict]):
        """
        构建NetworkX图
        
        Args:
            entities: 实体列表
            triples: 三元组列表
        """
        print("\n正在构建知识图谱...")
        
        # 添加节点
        for entity in entities:
            name = entity.get('name', '')
            entity_type = entity.get('type', '未知')
            
            if name:
                self.graph.add_node(name, type=entity_type)
        
        # 添加边
        for triple in triples:
            subject = triple.get('subject', '')
            relation = triple.get('relation', '')
            obj = triple.get('object', '')
            
            if subject and obj:
                self.graph.add_edge(subject, obj, relation=relation)
        
        print(f"  节点数: {self.graph.number_of_nodes()}")
        print(f"  边数: {self.graph.number_of_edges()}")
    
    def analyze_network(self) -> Dict:
        """
        网络分析
        
        Returns:
            网络分析结果
        """
        print("\n正在进行网络分析...")
        
        results = {}
        
        # 1. 基本统计
        results['basic_stats'] = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph)
        }
        
        # 2. 度中心性（Top 10）
        degree_centrality = nx.degree_centrality(self.graph)
        top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        results['top_degree_centrality'] = [
            {'node': node, 'centrality': round(cent, 4)}
            for node, cent in top_degree
        ]
        
        # 3. 介数中心性（Top 10）
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        results['top_betweenness_centrality'] = [
            {'node': node, 'centrality': round(cent, 4)}
            for node, cent in top_betweenness
        ]
        
        # 4. PageRank（Top 10）
        pagerank = nx.pagerank(self.graph)
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        results['top_pagerank'] = [
            {'node': node, 'score': round(score, 4)}
            for node, score in top_pagerank
        ]
        
        print(f"  网络密度: {results['basic_stats']['density']:.4f}")
        print(f"  是否连通: {results['basic_stats']['is_connected']}")
        
        return results
    
    def detect_communities(self) -> Dict:
        """
        社区发现
        
        Returns:
            社区发现结果
        """
        print("\n正在进行社区发现...")
        
        # 转换为无向图（社区发现算法需要）
        undirected_graph = self.graph.to_undirected()
        
        # 使用Louvain算法进行社区发现
        communities = community.louvain_communities(undirected_graph)
        
        results = {
            'num_communities': len(communities),
            'communities': []
        }
        
        # 整理社区信息
        for i, comm in enumerate(communities, 1):
            if len(comm) >= 3:  # 只保留至少3个节点的社区
                # 统计社区中的实体类型
                type_counts = Counter()
                for node in comm:
                    node_type = self.graph.nodes[node].get('type', '未知')
                    type_counts[node_type] += 1
                
                results['communities'].append({
                    'id': i,
                    'size': len(comm),
                    'nodes': list(comm)[:10],  # 只保留前10个节点
                    'type_distribution': dict(type_counts)
                })
        
        print(f"  发现社区数: {len(communities)}")
        print(f"  有效社区数（≥3节点）: {len(results['communities'])}")
        
        return results
    
    def find_patterns(self, triples: List[Dict]) -> Dict:
        """
        模式挖掘
        
        Args:
            triples: 三元组列表
        
        Returns:
            模式挖掘结果
        """
        print("\n正在进行模式挖掘...")
        
        results = {}
        
        # 1. 关系模式统计
        relation_patterns = defaultdict(int)
        for triple in triples:
            relation = triple.get('relation', '')
            if relation:
                relation_patterns[relation] += 1
        
        results['relation_patterns'] = [
            {'relation': rel, 'count': count}
            for rel, count in sorted(relation_patterns.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # 2. 实体-关系模式（主体类型-关系-客体类型）
        entity_relation_patterns = defaultdict(int)
        for triple in triples:
            subject = triple.get('subject', '')
            relation = triple.get('relation', '')
            obj = triple.get('object', '')
            
            if subject in self.graph.nodes and obj in self.graph.nodes:
                subject_type = self.graph.nodes[subject].get('type', '未知')
                object_type = self.graph.nodes[obj].get('type', '未知')
                
                pattern = f"{subject_type} -[{relation}]-> {object_type}"
                entity_relation_patterns[pattern] += 1
        
        results['entity_relation_patterns'] = [
            {'pattern': pattern, 'count': count}
            for pattern, count in sorted(entity_relation_patterns.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
        
        # 3. 高频实体对
        entity_pairs = defaultdict(int)
        for triple in triples:
            subject = triple.get('subject', '')
            obj = triple.get('object', '')
            
            if subject and obj:
                pair = (subject, obj)
                entity_pairs[pair] += 1
        
        results['frequent_entity_pairs'] = [
            {'subject': subj, 'object': obj, 'count': count}
            for (subj, obj), count in sorted(entity_pairs.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
        
        print(f"  关系模式数: {len(results['relation_patterns'])}")
        print(f"  实体-关系模式数: {len(results['entity_relation_patterns'])}")
        
        return results
    
    def mine_knowledge(
        self,
        input_file: str,
        output_dir: str = None
    ) -> Dict:
        """
        执行完整的知识挖掘流程
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录路径
        
        Returns:
            挖掘结果
        """
        print("\n" + "=" * 70)
        print("知识挖掘")
        print("=" * 70)
        
        # 读取输入文件
        print(f"\n正在读取输入文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        triples = data.get('triples', [])
        
        print(f"  实体数: {len(entities)}")
        print(f"  三元组数: {len(triples)}")
        
        # 1. 构建图
        self.build_graph(entities, triples)
        
        # 2. 网络分析
        network_analysis = self.analyze_network()
        
        # 3. 社区发现
        communities = self.detect_communities()
        
        # 4. 模式挖掘
        patterns = self.find_patterns(triples)
        
        # 整合结果
        results = {
            'project': config.PROJECT_NAME,
            'network_analysis': network_analysis,
            'communities': communities,
            'patterns': patterns
        }
        
        # 保存结果
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n正在保存挖掘结果...")
            
            # 保存完整结果
            with open(output_dir / "mining_results.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 保存网络分析结果
            with open(output_dir / "network_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(network_analysis, f, ensure_ascii=False, indent=2)
            
            # 保存社区发现结果
            with open(output_dir / "communities.json", 'w', encoding='utf-8') as f:
                json.dump(communities, f, ensure_ascii=False, indent=2)
            
            # 保存模式挖掘结果
            with open(output_dir / "patterns.json", 'w', encoding='utf-8') as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            
            print(f"  结果已保存到: {output_dir}")
        
        print("\n" + "=" * 70)
        print("✅ 知识挖掘完成！")
        print("=" * 70)
        
        # 打印关键发现
        print(f"\n关键发现:")
        print(f"\n1. 核心实体（度中心性Top 5）:")
        for item in network_analysis['top_degree_centrality'][:5]:
            print(f"   - {item['node']}: {item['centrality']:.4f}")
        
        print(f"\n2. 重要实体（PageRank Top 5）:")
        for item in network_analysis['top_pagerank'][:5]:
            print(f"   - {item['node']}: {item['score']:.4f}")
        
        print(f"\n3. 主要社区:")
        for comm in communities['communities'][:3]:
            print(f"   - 社区{comm['id']}: {comm['size']}个节点")
            print(f"     类型分布: {comm['type_distribution']}")
        
        print(f"\n4. 高频关系模式（Top 5）:")
        for item in patterns['relation_patterns'][:5]:
            print(f"   - {item['relation']}: {item['count']}次")
        
        return results


if __name__ == "__main__":
    # 测试知识挖掘
    mining = KnowledgeMining()
    
    # 使用重分类、去重后的最终知识图谱
    input_file = config.FINAL_GRAPH_FILE
    output_dir = config.PROJECT_ROOT / "knowledge_mining_results"
    
    result = mining.mine_knowledge(str(input_file), str(output_dir))
