# HTN-EC 高血压合并情志障碍中医知识图谱

<sub>Repository identifier: MSI-HBP-Knowledge-Graph (retained from the original release)</sub>

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph?style=social)
![GitHub forks](https://img.shields.io/github/forks/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph?style=social)
![GitHub issues](https://img.shields.io/github/issues/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**高血压合并情志障碍中医知识图谱与问答系统**

*TCM Knowledge Graph for Hypertension with Emotional Comorbidity (HTN-EC)*

简体中文

</div>

---

## 项目简介

本项目构建了**高血压合并情志障碍（Hypertension with Emotional Comorbidity, HTN-EC）**的中医知识图谱与问答系统，语料为 419 条中文文献题录（题名、关键词、摘要），采用大模型辅助抽取加专家策展的方式构建。

**关于命名**：本项目最初以「精神应激性高血压（MSI-HBP）」立项，仓库标识 `MSI-HBP-Knowledge-Graph` 予以保留。对语料的主题标注显示，419 条记录中 417 条（99.5%）涉及高血压合并焦虑、抑郁或失眠，仅 2 条（0.5%）提及精神应激；检索式本身为「高血压」合并「焦虑」，未包含应激相关词。因此本项目改用与证据基础相符的「高血压合并情志障碍」表述，精神应激性高血压作为该范畴内证据尚不充分的亚型。详见论文 Introduction 与 Methods。

**当前定位**：早期文献导航原型。独立评估（73 道外部专家命题、双盲评分）显示，在论文所述配置下系统完整答对 12% 的临床问题、方向正确 48%。本系统不支持临床决策，请勿用于诊疗。评估材料见 `evaluation/` 目录。

### ✨ 核心特性

- 🧠 **智能知识抽取**: 从文献、指南、病历中自动抽取实体和关系
- 🔗 **多源知识融合**: 整合异构数据源，构建统一知识图谱
- 💾 **图数据库存储**: 基于Neo4j的高性能图存储
- 💬 **智能问答系统**: 基于LLM和知识图谱的中医问答
- 📊 **知识可视化**: 交互式知识图谱可视化展示
- 🎯 **高准确率**: 测试准确率达92.67%

### 📊 数据规模

- **实体记录**: 997条（按“名称+类型”唯一，25种类型）
- **唯一实体名称**: 956个
- **关系数量**: 312条（4种类型）
- **数据覆盖率**: 100%
- **测试准确率**: 92.67%

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Neo4j 5.x
- 8GB+ RAM

### 1. 克隆项目

```bash
git clone https://github.com/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph.git
cd MSI-HBP-Knowledge-Graph
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# LLM配置
MODEL_BASE_URL=https://api.siliconflow.cn/v1
MODEL_API_KEY=your_api_key_here
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_TEMPERATURE=0.1

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### 4. 启动Neo4j

**使用Docker（推荐）:**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

**或直接安装Neo4j:**

访问 [Neo4j下载页面](https://neo4j.com/download/)

### 5. 构建知识图谱

```bash
python build_graph.py
```

### 6. 启动Web应用

```bash
streamlit run app.py
```

访问 http://localhost:8080

---

## 📁 项目结构

```
MSI-HBP-Knowledge-Graph/   # 仓库标识保留原名
├── 📂 data/                      # 数据目录
│   ├── 📂 raw/                  # 原始数据（文献、指南、病历）
│   ├── 📂 processed/            # 处理后的数据
│   │   ├── extracted_triples/   # 抽取的三元组
│   │   ├── fused_knowledge/     # 融合后的知识
│   │   └── merged/              # 重分类、去重后的最终数据
│   ├── entities.json            # 附件实体数据（997条）
│   ├── 📂 external/             # 外部数据源
│   ├── synonyms.json            # 同义词映射
│   └── triples.json             # 知识三元组
├── 📂 src/                       # 源代码
│   ├── 📂 crawler/              # 数据爬取模块
│   ├── 📂 extraction/           # 知识抽取模块
│   ├── 📂 fusion/               # 知识融合模块
│   ├── 📂 qa/                   # 问答系统模块
│   └── 📂 utils/                # 工具函数
│       ├── config.py            # 配置管理
│       ├── llm_client.py        # LLM客户端
│       └── neo4j_client.py      # Neo4j客户端
├── 📂 deploy/                    # 部署脚本
├── 📂 lib/                       # 前端库
├── app.py                        # Web应用主程序
├── build_graph.py                # 知识图谱构建
├── chat.py                       # 聊天界面
├── merge_and_deduplicate_data.py # 数据合并去重
├── test_internal_dataset.py      # 测试脚本
├── requirements.txt              # Python依赖
├── 投稿信息文档.md               # 投稿信息
├── 测试改进方案.md               # 测试改进方案
└── README.md                     # 项目说明
```

---

## 🏗️ 知识图谱Schema

### 实体类型（25种）

| 类型 | 英文 | 数量 | 说明 |
|------|------|------|------|
| 治则治法 | TreatmentMethod | 159 | 治疗原则和方法 |
| 工具 | Tool | 153 | 指标、机制和检测工具 |
| 方剂 | Formula | 115 | 中药方剂及中成药 |
| 症状 | Symptom | 107 | 临床表现 |
| 疾病 | Disease | 88 | 疾病名称 |
| 量表 | Scale | 69 | 临床评价量表 |
| 中药 | Herb | 66 | 中药材 |
| 其他 | Others | 240 | 其余18种实体类型 |

### 关系类型（4种）

| 关系 | 英文 | 数量 | 说明 |
|------|------|------|------|
| 治疗 | TREATS | 171 | 治疗关系 |
| 组成 | COMPOSED_OF | 84 | 组成关系 |
| 引起 | CAUSES | 32 | 因果关系 |
| 使用 | USES | 25 | 使用关系 |

---

## 🤖 技术架构

### 核心技术栈

- **后端框架**: Python 3.8+
- **图数据库**: Neo4j 5.x
- **Web框架**: Streamlit
- **LLM框架**: LangChain
- **大语言模型**: Qwen2.5-7B-Instruct
- **可视化**: Vis.js Network

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     Web Interface                        │
│                    (Streamlit)                          │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  Knowledge     │  │   QA System  │  │  Visualization  │
│  Extraction    │  │   (LLM+KG)   │  │   (Vis.js)      │
└───────┬────────┘  └──────┬──────┘  └─────────────────┘
        │                   │
        │           ┌───────▼────────┐
        │           │   LLM Client   │
        │           │  (Qwen2.5-7B)  │
        │           └────────────────┘
        │
┌───────▼────────────────────────────┐
│        Neo4j Graph Database        │
│     (Entities + Relations)         │
└────────────────────────────────────┘
```

---

## � 核心功能

### 1. 智能问答系统

基于知识图谱和大语言模型的智能问答：

```python
from src.qa.qa_system import QASystem

qa = QASystem()
result = qa.answer("天麻钩藤饮由哪些中药组成？")
print(result['answer'])
```

**特点**:
- 混合实体识别（规则+LLM）
- 同义词归一化
- 多跳知识推理
- 自然语言生成

### 2. 知识图谱可视化

交互式知识图谱浏览：
- 实体搜索和过滤
- 关系类型筛选
- 动态图布局
- 节点详情查看

### 3. 数据管理

- 数据导入导出
- 知识去重合并
- 同义词管理
- 数据统计分析

---

## 📊 测试与评估

### 测试结果

基于150个测试案例的评估：

> 系统评测正在重新执行中，结果将在更新后发布。

### 运行测试

```bash
python test_internal_dataset.py
```

详细测试报告见：[测试改进方案.md](测试改进方案.md)

---

## 📚 文档

- [投稿信息文档](投稿信息文档.md) - LLM模型、提示词、数据清洗标准
- [测试改进方案](测试改进方案.md) - 测试结果分析和改进建议
- [改进总结](改进总结.md) - 项目改进总结
- [部署文档](deploy/README.md) - 服务器部署指南

---

## 🚢 部署

### 本地部署

```bash
# 1. 启动Neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456 neo4j:latest

# 2. 构建知识图谱
python build_graph.py

# 3. 启动应用
streamlit run app.py --server.port 8080
```

### 服务器部署

详见 [deploy/README.md](deploy/README.md)

---

## 🤝 贡献指南

欢迎贡献代码、提出问题和建议！

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发规范

- 遵循PEP 8代码规范
- 添加必要的注释和文档
- 编写单元测试
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## � 团队

- **项目负责人**: wangyu1984-SDTCM
- **技术支持**: HTN-EC-KG Research Team

---

## � 联系方式

- **GitHub Issues**: [提交问题](https://github.com/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph/   # 仓库标识保留原名issues)
- **Email**: wangyu1984@example.com

---

## 🙏 致谢

感谢以下开源项目：

- [Neo4j](https://neo4j.com/) - 图数据库
- [Streamlit](https://streamlit.io/) - Web框架
- [LangChain](https://www.langchain.com/) - LLM框架
- [Qwen](https://github.com/QwenLM/Qwen) - 大语言模型
- [Vis.js](https://visjs.org/) - 图可视化

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by HTN-EC-KG Research Team

</div>
