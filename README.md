# HTN-EC 高血压合并情志障碍中医知识图谱

<sub>Repository identifier: MSI-HBP-Knowledge-Graph (retained from the original project name)</sub>

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph?style=social)
![GitHub forks](https://img.shields.io/github/forks/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph?style=social)
![GitHub issues](https://img.shields.io/github/issues/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**高血压合并情志障碍中医知识图谱与问答系统**

*A Traditional Chinese Medicine Knowledge Graph for Hypertension With Emotional Comorbidity (HTN-EC-KG)*

简体中文

</div>

---

## 项目简介

本项目构建了**高血压合并情志障碍（Hypertension with Emotional Comorbidity, HTN-EC）**的中医知识资源与问答系统。语料为 419 条中文文献题录（题名、关键词、摘要），由 Qwen2.5-7B-Instruct 生成候选实体与关系，再由中医临床医师参照候选三元组、检索文献、标准教材和中医理论整理出最终关系集（LLM 辅助的专家策展）。

**题录计数说明**：419 为归档记录数，原导出标签为 Journal Article 321 条、Dissertation/Thesis 95 条、Journal 3 条，不代表 419 篇独立出版物。作者确认第 130/131、377/375、407/408 条为重复记录；编号按 `data/extracted/literature_records.json` 的从 1 开始的位置计算。原始记录及语料统计口径保留，书目核对说明见 [`data/extracted/bibliography_audit.csv`](data/extracted/bibliography_audit.csv)；附录 3 已注明对应关系，并按作者提供的题录补齐第 170 条会议论文的出处。

**关于命名**：本项目最初以「精神应激性高血压（MSI-HBP）」立项，仓库标识 `MSI-HBP-Knowledge-Graph` 予以保留。对语料的主题标注显示，419 条记录中 417 条（99.5%）涉及高血压合并焦虑、抑郁或失眠，仅 2 条（0.5%）提及精神应激；检索式为「高血压」合并「焦虑」，未包含应激相关词。因此本项目改用「高血压合并情志障碍」作为对语料范围的描述；这不是一个新定义的诊断亚型，也不意味着高血压由应激引起。详见论文 Introduction 与 Methods。

**当前定位**：文献导航原型，**不支持临床决策，请勿用于诊疗**。在 73 道由外部临床专家独立命题、双盲评分的问题上，固定生成模型（DeepSeek-V4-Pro）加入图谱检索后的严格正确率为 50/73（68%），不加图谱检索为 57/73（78%），配对 McNemar 检验 P=.09；该实验未能证明图谱检索提高严格正确率，也未建立等效性。评估材料见 [`evaluation/`](evaluation/README.md)。

### ✨ 核心特性

- 🧠 **大模型辅助候选抽取**: 从文献题录（题名、关键词、摘要）中抽取候选实体与关系
- 🔗 **专家策展**: 由中医临床医师参照候选三元组、标准教材与检索所得文献审定最终关系集；312 条最终关系中仅 38 条出现在融合后的抽取候选中，274 条来自专家补充
- 💾 **双存储表示**: JSON 知识库与 Neo4j 图数据库
- 💬 **问答系统**: 实体识别 → 关系检索 → 大模型答案合成
- 📊 **知识可视化**: 交互式知识图谱可视化展示
- 🏷️ **来源类别**: 每条关系标注来源类别（A 具体文献 171 条／B 教材《中医方剂学》84 条／C 中医理论 57 条）。类别只区分来源类型，不是临床证据强度分级；数据中的字段名 `evidence_level` 为历史保留
- 🔍 **可复算**: `rebuild_stats.py` 从发布数据重算资源构成统计（实体索引、图谱节点与关系、来源类别、度中心性）；`evaluation/retrieval_ablation.py` 重算失败分析所依据的图结构统计

### 📊 数据规模

- **实体索引**: 997 条记录（按「名称+类型」唯一，25 种类型），对应 956 个唯一实体名称；用于问题中的实体识别与术语归一
- **知识图谱**: 101 个节点、312 条关系（4 种谓词）；承担实际检索
- **端点有效性**: 312/312（100%），每条关系两端均在实体索引内（仅检查引用一致性）
- **来源类别**: A 类 171 条（可溯源至 46 篇具体文献）／B 类 84 条（《中医方剂学》）／C 类 57 条（中医病机、治法、治则理论）
- **专家确认**: 原 100 条均存在于抽样时的早期未公开本地图谱；后续整理删除其中 20 条，评审清单仍保留原 100 条，附录中的答案摘要则在删除之后用更新图谱补生成。原评审关系中，80 条存在于 v2.0 发布图谱；共识确认 79/80 条（98.8%，95% Wilson CI 93.3–99.8）。此结果描述早期评审集与最终图谱的交集，不是从最终 312 条重新抽取的分层样本。初始一致 77/80（96.3%），二次加权 Cohen κ = −0.02，Gwet AC1 = 0.96。原始 100 条评分与发布成员标记、复算方法见 [`evaluation/`](evaluation/README.md)。

> **注**：实体索引（956 词条）用于实体识别与术语归一；知识图谱（101 节点）承担实际检索。索引宽于图谱是有意设计。索引与图谱中「焦虑」「抑郁」「失眠」的类型为症状，「焦虑症」「抑郁症」为疾病；图谱中疾病节点仅「高血压」一个。详见论文 Methods。

---

## 🚀 快速开始

### 环境要求

- Python 3.12（NumPy 2.5 要求 Python ≥3.12；本次环境核对使用 3.12）
- Neo4j 5.x（可选；JSON 后端无需数据库）
- 8GB+ RAM

### 1. 克隆项目

```bash
git clone https://github.com/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph.git
cd MSI-HBP-Knowledge-Graph
```

### 2. 安装依赖

`v2.0.1` 删除了未被代码导入、且与 `langchain-core==1.4.8` 冲突的 `langchain==0.3.25` 元包；代码使用 `langchain_openai` 和 `langchain_core`。其余固定版本保留。历史 `v2.0` 的依赖文件未改写。

2026-10-29 已在独立的 Windows Python 3.12.14 环境完成实际安装，`pip check` 通过，问答、候选抽取、知识融合及主要依赖的离线导入通过。Q038 的实体识别实测返回“温胆汤”。这些检查不包含服务器部署或在线 LLM 请求。

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```env
# LLM配置
MODEL_BASE_URL=https://api.siliconflow.cn/v1
MODEL_API_KEY=your_api_key_here
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_TEMPERATURE=0.1

# Neo4j配置（使用 JSON 后端时可省略）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### 4. 启动Neo4j（可选）

**使用Docker（推荐）:**

```bash
export NEO4J_AUTH="neo4j/${NEO4J_PASSWORD:?Set your local Neo4j password first}"
docker run -d \
  --name neo4j \
  -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
  -e NEO4J_AUTH \
  neo4j:5
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
MSI-HBP-Knowledge-Graph/          # 仓库标识保留原名
├── 📂 evaluation/                # 独立评估材料（题集、评分细则、逐条评分、消融脚本）
├── 📂 data/                      # 数据目录
│   ├── entities.json            # 实体索引（997 条记录 / 956 个唯一名称）
│   ├── triples.json             # 最终关系集（312 条，含来源与来源类别）
│   ├── synonyms.json            # 同义词词典（28 组 / 66 个表面形式）
│   ├── prompts.py               # 实体识别、答案合成、三元组抽取提示词模板
│   ├── 📂 extracted/            # 419 条文献题录元数据及语料统计（当前文件不含摘要；历史提交未改写）
│   └── 📂 processed/            # 候选处理中间结果
│       ├── extracted_triples/   # 原始抽取（1004 实体记录 / 1290 候选三元组）
│       ├── fused_knowledge/     # 融合后（1002 / 1144）
│       └── merged/              # 最终资源的副本与统计
├── 📂 src/                       # 源代码
│   ├── 📂 crawler/              # 文献题录解析
│   ├── 📂 extraction/           # 候选实体-关系抽取
│   ├── 📂 fusion/               # 同义词归一与去重
│   ├── 📂 mining/               # 图谱层统计
│   ├── 📂 qa/                   # 问答系统（实体识别、JSON/Neo4j 检索、答案合成）
│   └── 📂 utils/                # 配置、LLM 客户端、Neo4j 客户端
├── 📂 deploy/                    # 部署脚本
├── 📂 lib/                       # 前端库（vis.js 等）
├── app.py                        # Web应用主程序（Streamlit）
├── chat.py                       # 命令行问答
├── build_graph.py                # 知识图谱构建（Neo4j）
├── merge_and_deduplicate_data.py # 数据合并去重
├── add_evidence_level.py         # 为关系补充来源类别字段（字段名 evidence_level 为历史保留）
├── rebuild_stats.py              # 资源构成统计复算
├── graph_visualization.html      # 筛选后的界面快照（38 节点、50 条边），非完整图谱
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明
```

---

## 🏗️ 知识图谱Schema

### 实体索引类型（25种）

| 类型 | 英文 | 数量 | 说明 |
|------|------|------|------|
| 治则治法 | Treatment Method | 159 | 治疗原则和方法 |
| 工具 | Tool | 153 | 指标、机制和检测工具 |
| 方剂 | Formula | 115 | 中药方剂及中成药 |
| 症状 | Symptom | 107 | 临床表现（含焦虑、抑郁、失眠） |
| 疾病 | Disease | 88 | 疾病名称（含高血压及其亚型、焦虑症、抑郁症） |
| 量表 | Scale | 69 | 临床评价量表 |
| 中药 | Herb | 66 | 中药材 |
| 病机 | Pathogenesis | 53 | 病因病机概念 |
| 其他 | Others | 187 | 其余 17 种类型（西药、证型、穴位、体质等） |

图谱节点（101 个）仅包含参与四种核心关系的词条：中药 52、方剂 18、症状 14、治则治法 8、病机 8（含 2 个病因病机）、疾病 1。

### 关系类型（4种）

| 关系 | 英文 | 数量 | 来源类别 | 说明 |
|------|------|------|------|------|
| 治疗 | TREATS | 171 | A（具体文献） | 中药/方剂/治则治法 → 疾病/症状/病机 |
| 组成 | COMPOSED_OF | 84 | B（《中医方剂学》） | 方剂 → 中药 |
| 引起 | CAUSES | 32 | C（中医病机理论） | 病机 → 疾病/症状 |
| 使用 | USES | 25 | C（中医治法/治则理论） | 病机 → 治则治法；治则治法 → 中药/方剂 |

谓词标签描述资源中记录的关联，不独立构成疗效或因果的证据。

---

## 🤖 技术架构

### 核心技术栈

- **后端框架**: Python 3.12（NumPy 2.5 要求 Python ≥3.12；本次环境核对使用 3.12）
- **图数据库**: Neo4j 5.x（可选）
- **Web框架**: Streamlit
- **LLM框架**: LangChain
- **大语言模型**: 候选抽取与默认问答使用 Qwen2.5-7B-Instruct（SiliconFlow）；论文中的六配置消融、生成模型比较与匹配对照实验使用 DeepSeek-V4-Pro
- **可视化**: Vis.js Network

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              Interface: Streamlit web UI / CLI          │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  Candidate     │  │   QA System  │  │  Visualization  │
│  Extraction    │  │ (retrieval + │  │   (Vis.js)      │
│  + Expert      │  │  generation) │  │                 │
│  Curation      │  └──────┬──────┘  └─────────────────┘
└───────┬────────┘         │
        │           ┌──────▼─────────┐
        │           │   LLM Client   │
        │           └────────────────┘
        │
┌───────▼────────────────────────────┐
│   JSON knowledge base / Neo4j      │
└────────────────────────────────────┘
```

---

## 💡 核心功能

### 1. 问答系统

```python
from src.qa.qa_system import QASystem

qa = QASystem(use_neo4j=False)   # JSON 后端；use_neo4j=True 使用 Neo4j
result = qa.answer("天麻钩藤饮由哪些中药组成？")
print(result['answer'])
```

**流程**:
- 先做同义词归一化和字符串匹配，未匹配到实体时才调用 LLM，返回最多 5 个候选实体
- 同义词归一化
- 按查询类型检索关系（JSON 过程或参数化 Cypher）
- 将最多 15 条检索到的三元组作为上下文交给生成模型合成 150–300 字回答

提供图谱上下文并不保证回答正确或无编造；见论文 Results 与 Limitations。

### 2. 知识图谱可视化

`app.py` 根据界面筛选条件生成 `graph_visualization.html`。仓库中保留的是一个含 38 个节点、50 条边的生成快照；完整图谱的 101 个节点和 312 条关系以 `data/triples.json` 为准。

- 实体搜索和过滤
- 关系类型筛选
- 动态图布局
- 节点详情查看

### 3. 数据管理

- 知识去重合并
- 同义词管理
- 资源构成统计复算（`python rebuild_stats.py`）

---

## 📊 评估

所有评估使用同一套 73 道问题（三位未参与系统构建的临床医师命题）与同一评分细则，由两位未参与命题的医师在不知条件的情况下独立评分，分歧取较保守档。各轮结果（分子/73）：

| 比较 | 条件 | 完全正确 | 正确或部分正确 |
|------|------|------|------|
| 初始三条件（Qwen2.5-7B-Instruct，无输出长度限制） | 完整系统 / 仅检索 / 仅模型 | 5 / 0 / 0 | 29 / 5 / 13 |
| 生成模型比较（图谱检索相同，6000 token 上限） | Qwen2.5-7B-Instruct / DeepSeek-V4-Pro | 9 / 26 | 35 / 59 |
| 六种检索配置（DeepSeek-V4-Pro） | A0 基线 … D4 | 25 … 14 | 47 … 26 |
| 匹配对照（DeepSeek-V4-Pro，同题同提示词） | 有图谱检索 / 无图谱检索 | **50 / 57**（P=.09） | 72 / 72 |

「正确或部分正确」仅是两档的合计，不代表临床可接受性；安全性标记与正确性分开记录。完整材料、各轮逐条评分与说明见 [`evaluation/README.md`](evaluation/README.md)。

---

## 📚 文档

- [评估材料说明](evaluation/README.md) - 题集、评分细则、逐条评分、消融脚本
- [部署文档](deploy/README.md) - 服务器部署指南
- 提示词模板：[`data/prompts.py`](data/prompts.py)

---

## 🚢 部署

### 本地部署

```bash
# 1. 启动Neo4j（可选）
export NEO4J_AUTH="neo4j/${NEO4J_PASSWORD:?Set your local Neo4j password first}"
docker run -d --name neo4j -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
  -e NEO4J_AUTH neo4j:5

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
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

- **项目负责人**: wangyu1984-SDTCM
- **技术支持**: HTN-EC-KG Research Team

---

## 📮 联系方式

- **GitHub Issues**: [提交问题](https://github.com/wangyu1984-SDTCM/MSI-HBP-Knowledge-Graph/issues)
- **Email**: wangyutcm.jinan@foxmail.com

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

## 发布与源文献说明

`v2.0.1` 汇集本轮说明修正、关系评审映射与复算材料、依赖修正及部署模板清理。图谱与评估评分数据相对 `v2.0` 未改变。组成题的方剂覆盖范围和融合计数可通过 `python evaluation/check_reported_counts.py` 重算；详见 `evaluation/README.md`。

当前发布文件 `data/extracted/literature_records.json` 提供题录元数据，不包含摘要或全文。早期 Git 历史仍保留包含摘要的版本；本次没有改写历史，因此不声称已从整个仓库历史中彻底清除摘要。源文本的获取和使用仍受相应数据库条款约束。

旧部署凭据已从当前文件移除；旧历史保留不等于凭据已失效。服务器端密码轮换和登录审计由管理员处理，具体见 `deploy/README.md`。
