"""
Neo4j客户端模块
封装Neo4j图数据库操作
"""
import json
from typing import List, Dict, Any, Tuple, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError
from tqdm import tqdm
from .config import config


class Neo4jClient:
    """Neo4j客户端类"""
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None
    ):
        """
        初始化Neo4j客户端
        
        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
        """
        self.uri = uri or config.NEO4J_URI
        self.user = user or config.NEO4J_USER
        self.password = password or config.NEO4J_PASSWORD
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                return result.single()["test"] == 1
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    
    def run_cypher(
        self,
        query: str,
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行单条Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
        
        Returns:
            查询结果列表
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def run_batch_cypher(
        self,
        queries_with_params: List[Tuple[str, Dict]],
        show_progress: bool = True
    ):
        """
        批量执行Cypher语句（使用事务）
        
        Args:
            queries_with_params: 查询和参数的列表
            show_progress: 是否显示进度条
        """
        with self.driver.session() as session:
            def transaction_logic(tx):
                iterator = queries_with_params
                if show_progress:
                    iterator = tqdm(iterator, desc="执行Cypher语句")
                
                for query, params in iterator:
                    tx.run(query, params or {})
            
            session.execute_write(transaction_logic)
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        project: str = None
    ) -> Dict[str, Any]:
        """
        创建节点
        
        Args:
            label: 节点标签
            properties: 节点属性
            project: 项目标识
        
        Returns:
            创建的节点信息
        """
        if project:
            properties["project"] = project
        
        query = f"""
        CREATE (n:{label} $properties)
        RETURN n
        """
        
        result = self.run_cypher(query, {"properties": properties})
        return result[0] if result else {}
    
    def create_relationship(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        to_label: str,
        to_property: str,
        to_value: Any,
        rel_type: str,
        rel_properties: Dict[str, Any] = None
    ):
        """
        创建关系
        
        Args:
            from_label: 起始节点标签
            from_property: 起始节点匹配属性
            from_value: 起始节点匹配值
            to_label: 终止节点标签
            to_property: 终止节点匹配属性
            to_value: 终止节点匹配值
            rel_type: 关系类型
            rel_properties: 关系属性
        """
        query = f"""
        MATCH (a:{from_label} {{{from_property}: $from_value}})
        MATCH (b:{to_label} {{{to_property}: $to_value}})
        MERGE (a)-[r:{rel_type}]->(b)
        """
        
        if rel_properties:
            query += "\nSET r += $rel_properties"
        
        query += "\nRETURN r"
        
        params = {
            "from_value": from_value,
            "to_value": to_value
        }
        
        if rel_properties:
            params["rel_properties"] = rel_properties
        
        self.run_cypher(query, params)
    
    def get_nodes_by_label(
        self,
        label: str,
        project: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        根据标签获取节点
        
        Args:
            label: 节点标签
            project: 项目标识
            limit: 限制数量
        
        Returns:
            节点列表
        """
        query = f"MATCH (n:{label})"
        
        if project:
            query += f" WHERE n.project = '{project}'"
        
        query += " RETURN n"
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.run_cypher(query)
        return [record["n"] for record in result]
    
    def get_relationships_by_type(
        self,
        rel_type: str,
        project: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        根据类型获取关系
        
        Args:
            rel_type: 关系类型
            project: 项目标识
            limit: 限制数量
        
        Returns:
            关系列表
        """
        query = f"MATCH (a)-[r:{rel_type}]->(b)"
        
        if project:
            query += f" WHERE a.project = '{project}'"
        
        query += " RETURN a, r, b"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.run_cypher(query)
    
    def clear_project_data(self, project: str):
        """
        清除项目数据
        
        Args:
            project: 项目标识
        """
        query = """
        MATCH (n {project: $project})
        DETACH DELETE n
        """
        self.run_cypher(query, {"project": project})
        print(f"已清除项目 {project} 的所有数据")
    
    def get_graph_statistics(self, project: str = None) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        Args:
            project: 项目标识
        
        Returns:
            统计信息
        """
        stats = {}
        
        # 节点总数
        query = "MATCH (n)"
        if project:
            query += f" WHERE n.project = '{project}'"
        query += " RETURN count(n) AS count"
        
        result = self.run_cypher(query)
        stats["total_nodes"] = result[0]["count"] if result else 0
        
        # 关系总数
        query = "MATCH (a)-[r]->(b)"
        if project:
            query += f" WHERE a.project = '{project}'"
        query += " RETURN count(r) AS count"
        
        result = self.run_cypher(query)
        stats["total_relationships"] = result[0]["count"] if result else 0
        
        # 各类型节点数量
        query = "MATCH (n)"
        if project:
            query += f" WHERE n.project = '{project}'"
        query += """
        UNWIND labels(n) AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """
        
        result = self.run_cypher(query)
        stats["node_types"] = {r["label"]: r["count"] for r in result}
        
        # 各类型关系数量
        query = "MATCH (a)-[r]->(b)"
        if project:
            query += f" WHERE a.project = '{project}'"
        query += """
        RETURN type(r) AS rel_type, count(*) AS count
        ORDER BY count DESC
        """
        
        result = self.run_cypher(query)
        stats["relationship_types"] = {r["rel_type"]: r["count"] for r in result}
        
        return stats
    
    def export_metadata(
        self,
        project: str,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        导出图谱元数据
        
        Args:
            project: 项目标识
            output_path: 输出文件路径
        
        Returns:
            元数据字典
        """
        metadata = {
            "project": project,
            "labels": [],
            "relationships": [],
            "triples": []
        }
        
        # 获取所有标签
        query = f"""
        MATCH (n {{project: '{project}'}})
        UNWIND labels(n) AS label
        RETURN DISTINCT label
        """
        labels = [r["label"] for r in self.run_cypher(query)]
        
        # 获取每个标签的属性
        for label in labels:
            query = f"""
            MATCH (n:{label} {{project: '{project}'}})
            UNWIND keys(n) AS prop
            RETURN DISTINCT prop
            """
            props = [r["prop"] for r in self.run_cypher(query) if r["prop"] != "project"]
            
            metadata["labels"].append({
                "name": label,
                "properties": [{"name": p, "description": ""} for p in props]
            })
        
        # 获取所有关系类型
        query = f"""
        MATCH (a {{project: '{project}'}})-[r]->(b)
        RETURN DISTINCT type(r) AS rel_type
        """
        rel_types = [r["rel_type"] for r in self.run_cypher(query)]
        
        # 获取每个关系的属性
        for rel_type in rel_types:
            query = f"""
            MATCH (a {{project: '{project}'}})-[r:{rel_type}]->(b)
            UNWIND keys(r) AS prop
            RETURN DISTINCT prop
            """
            props = [r["prop"] for r in self.run_cypher(query)]
            
            metadata["relationships"].append({
                "type": rel_type,
                "properties": [{"name": p, "description": ""} for p in props]
            })
        
        # 获取三元组结构
        query = f"""
        MATCH (a {{project: '{project}'}})-[r]->(b)
        WITH head(labels(a)) AS from_label, type(r) AS rel_type, head(labels(b)) AS to_label
        RETURN DISTINCT from_label, rel_type, to_label
        """
        triples = self.run_cypher(query)
        metadata["triples"] = [
            {
                "from": t["from_label"],
                "rel_type": t["rel_type"],
                "to": t["to_label"],
                "description": ""
            }
            for t in triples
        ]
        
        # 保存到文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"元数据已导出到: {output_path}")
        
        return metadata
    
    def __del__(self):
        """析构函数"""
        self.close()


# 创建全局Neo4j客户端实例
neo4j_client = Neo4jClient()


if __name__ == "__main__":
    # 测试Neo4j客户端
    client = Neo4jClient()
    
    # 测试连接
    if client.test_connection():
        print("✓ Neo4j连接成功")
    else:
        print("✗ Neo4j连接失败")
    
    # 获取统计信息
    stats = client.get_graph_statistics(config.PROJECT_NAME)
    print(f"\n图谱统计信息:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
