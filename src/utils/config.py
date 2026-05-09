"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """项目配置类"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # 数据目录
    DATA_DIR = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    EXTERNAL_DATA_DIR = DATA_DIR / "external"
    
    # LLM配置
    MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
    MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
    
    # Neo4j配置
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    
    # 嵌入模型配置
    EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "./models/embeddings")
    
    # 知识图谱Schema
    ENTITY_TYPES = [
        "疾病",      # Disease
        "症状",      # Symptom
        "病机",      # Pathogenesis
        "中药",      # Herb
        "方剂",      # Formula
        "治则治法"   # TreatmentMethod
    ]
    
    RELATION_TYPES = [
        "使用",          # USE
        "治疗",          # TREAT
        "由...组成",     # COMPOSED_OF
        "引起"           # CAUSE
    ]
    
    # 实体类型映射（中英文）
    ENTITY_TYPE_MAP = {
        "疾病": "Disease",
        "症状": "Symptom",
        "病机": "Pathogenesis",
        "病因病机": "Pathomechanism",
        "病性": "PathogenicNature",
        "中药": "Herb",
        "方剂": "Formula",
        "治则治法": "TreatmentMethod"
    }
    
    # 关系类型映射
    RELATION_TYPE_MAP = {
        "使用": "USE",
        "治疗": "TREAT",
        "由...组成": "COMPOSED_OF",
        "引起": "CAUSE"
    }
    
    # 关系定义（根据GB/T38324-2019标准）
    RELATION_DEFINITIONS = {
        "使用": {
            "subject": ["治则治法", "病机"],
            "object": ["中药", "方剂", "治则治法"],
            "description": "在某种活动或过程中被利用"
        },
        "治疗": {
            "subject": ["中药", "方剂", "治则治法"],
            "object": ["疾病", "症状", "病机"],
            "description": "提供治愈或改善的方法"
        },
        "由...组成": {
            "subject": ["方剂"],
            "object": ["中药"],
            "description": "由某些材料或物质的结构性组成"
        },
        "引起": {
            "subject": ["病机"],
            "object": ["疾病", "症状"],
            "description": "导致某种状态或结果"
        }
    }
    
    # 项目标识
    PROJECT_NAME = "MSI-HBP"
    PROJECT_DESCRIPTION = "精神应激性高血压中医知识图谱"
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        errors = []
        
        if not cls.MODEL_API_KEY:
            errors.append("MODEL_API_KEY未配置")
        
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD未配置")
        
        if errors:
            raise ValueError(f"配置错误: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_data_path(cls, *paths):
        """获取数据路径"""
        return cls.DATA_DIR.joinpath(*paths)
    
    @classmethod
    def ensure_dirs(cls):
        """确保所有必要的目录存在"""
        dirs = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.EXTERNAL_DATA_DIR,
            cls.RAW_DATA_DIR / "literature",
            cls.RAW_DATA_DIR / "guidelines",
            cls.RAW_DATA_DIR / "medical_records",
            cls.PROCESSED_DATA_DIR / "extracted_triples",
            cls.PROCESSED_DATA_DIR / "fused_knowledge",
            cls.EXTERNAL_DATA_DIR / "tcm_database"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置
    print(f"项目根目录: {config.PROJECT_ROOT}")
    print(f"数据目录: {config.DATA_DIR}")
    print(f"LLM模型: {config.MODEL_NAME}")
    print(f"Neo4j URI: {config.NEO4J_URI}")
    
    # 确保目录存在
    config.ensure_dirs()
    print("\n所有目录已创建")
