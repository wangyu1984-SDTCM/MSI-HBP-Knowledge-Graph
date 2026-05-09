"""
MSI-HBP 知识图谱可视化和问答系统 - Web界面
使用 Streamlit 构建
"""
import sys
from pathlib import Path
import json
from datetime import datetime
import streamlit.components.v1 as components

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    import streamlit as st
except ImportError:
    print("❌ 请先安装 streamlit: pip install streamlit")
    sys.exit(1)

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False
    print("⚠️  pyvis未安装，图谱可视化功能不可用")

from src.qa.qa_system import QASystem
from src.utils.config import config


# 页面配置
st.set_page_config(
    page_title="MSI-HBP 知识图谱",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
    .knowledge-item {
        background-color: #f8f9fa;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #1f77b4;
        border-radius: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_qa_system():
    """加载问答系统（缓存）"""
    return QASystem(use_neo4j=False)


@st.cache_data
def load_statistics():
    """加载统计信息（缓存）"""
    json_file = config.PROCESSED_DATA_DIR / "fused_knowledge" / "msi_hbp_fused.json"
    
    if not json_file.exists():
        json_file = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('statistics', {})
    return {}


def main():
    # 标题
    st.markdown('<div class="main-header">🏥 MSI-HBP 中医知识图谱系统</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("📋 系统信息")
        
        # 加载统计信息
        stats = load_statistics()
        
        if stats:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{stats.get('total_entities', 0)}</div>
                <div class="stat-label">实体总数</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{stats.get('total_triples', 0)}</div>
                <div class="stat-label">三元组总数</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 实体类型分布
            if stats.get('entity_types'):
                st.subheader("📊 实体类型分布")
                entity_types = stats['entity_types']
                for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:6]:
                    st.write(f"**{entity_type}**: {count}")
        
        st.markdown("---")
        st.subheader("💡 功能模块")
        page = st.radio(
            "选择功能",
            ["🤖 智能问答", "📊 知识浏览", "🕸️ 图谱可视化", "📈 统计分析", "📥 数据导出"],
            label_visibility="collapsed"
        )
    
    # 主内容区
    if page == "🤖 智能问答":
        show_qa_page()
    elif page == "📊 知识浏览":
        show_knowledge_page()
    elif page == "🕸️ 图谱可视化":
        show_graph_visualization_page()
    elif page == "📈 统计分析":
        show_statistics_page()
    elif page == "📥 数据导出":
        show_export_page()


def show_qa_page():
    """智能问答页面"""
    st.header("🤖 智能问答系统")
    st.write("基于知识图谱的中医智能问答，输入您的问题获取专业解答。")
    
    # 扩展的示例问题
    with st.expander("💡 查看示例问题（已扩展）"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**症状相关**")
            st.write("- 精神应激性高血压有什么症状？")
            st.write("- 肝阳上亢的表现是什么？")
            st.write("- 心肾不交会出现哪些症状？")
            st.write("- 失眠多梦是什么原因？")
            
            st.markdown("**治疗相关**")
            st.write("- 肝阳上亢怎么治疗？")
            st.write("- 平肝潜阳的方法有哪些？")
            st.write("- 如何疏肝解郁？")
            st.write("- 交通心肾的治法有哪些？")
            
            st.markdown("**方剂相关**")
            st.write("- 天麻钩藤饮的作用是什么？")
            st.write("- 逍遥散由什么组成？")
            st.write("- 半夏白术天麻汤治疗什么？")
            st.write("- 柴胡疏肝散的功效是什么？")
        
        with col2:
            st.markdown("**中药相关**")
            st.write("- 什么中药可以治疗焦虑？")
            st.write("- 天麻有什么功效？")
            st.write("- 钩藤的作用是什么？")
            st.write("- 酸枣仁能治疗失眠吗？")
            
            st.markdown("**病机相关**")
            st.write("- 高血压的病机是什么？")
            st.write("- 肝郁气滞是怎么形成的？")
            st.write("- 痰浊中阻的表现有哪些？")
            st.write("- 阴虚阳亢是什么意思？")
            
            st.markdown("**关系相关**")
            st.write("- 失眠和高血压有什么关系？")
            st.write("- 焦虑会导致高血压吗？")
            st.write("- 精神应激和高血压的关系？")
            st.write("- 情志失调如何影响血压？")
    
    # 问题输入
    question = st.text_input(
        "请输入您的问题：",
        value=st.session_state.current_question,
        placeholder="例如：精神应激性高血压有什么症状？",
        key="question_input"
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        ask_button = st.button("🔍 提问", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ 清空", use_container_width=True)
    with col3:
        if st.session_state.qa_history:
            show_history = st.button("📜 历史", use_container_width=True)
        else:
            show_history = False
    
    if clear_button:
        st.session_state.current_question = ""
        st.rerun()
    
    if ask_button and question:
        with st.spinner("🤔 正在思考..."):
            # 加载问答系统
            qa = load_qa_system()
            
            # 获取答案
            result = qa.answer(question)
            
            # 保存到历史记录
            st.session_state.qa_history.insert(0, {
                'question': question,
                'answer': result['answer'],
                'entities': result['entities'],
                'knowledge': result['knowledge'][:5],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 限制历史记录数量
            if len(st.session_state.qa_history) > 20:
                st.session_state.qa_history = st.session_state.qa_history[:20]
            
            # 显示答案
            st.markdown("### 💬 答案")
            st.success(result['answer'])
            
            # 显示识别的实体
            if result['entities']:
                st.markdown("### 🏷️ 识别的实体")
                entity_tags = " ".join([f"`{e}`" for e in result['entities']])
                st.markdown(entity_tags)
            
            # 显示相关知识
            if result['knowledge']:
                st.markdown("### 📚 相关知识")
                for i, k in enumerate(result['knowledge'][:10], 1):
                    st.markdown(f"""
                    <div class="knowledge-item">
                        {i}. <strong>{k['subject']}</strong> 
                        <span style="color: #1f77b4;">-[{k['relation']}]-></span> 
                        <strong>{k['object']}</strong>
                    </div>
                    """, unsafe_allow_html=True)
    
    # 显示历史记录
    if show_history and st.session_state.qa_history:
        st.markdown("---")
        st.markdown("### 📜 问答历史")
        
        for i, item in enumerate(st.session_state.qa_history[:10], 1):
            with st.expander(f"{i}. {item['question']} ({item['timestamp']})"):
                st.markdown(f"**答案**: {item['answer']}")
                if item['entities']:
                    st.markdown(f"**实体**: {', '.join(item['entities'])}")
                if item['knowledge']:
                    st.markdown("**相关知识**:")
                    for k in item['knowledge']:
                        st.write(f"- {k['subject']} -[{k['relation']}]-> {k['object']}")
        
        if st.button("🗑️ 清空历史"):
            st.session_state.qa_history = []
            st.rerun()


def show_knowledge_page():
    """知识浏览页面"""
    st.header("📊 知识浏览")
    st.write("浏览知识图谱中的实体和关系")
    
    # 加载数据
    json_file = config.PROCESSED_DATA_DIR / "fused_knowledge" / "msi_hbp_fused.json"
    if not json_file.exists():
        json_file = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    
    if not json_file.exists():
        st.error("❌ 未找到知识文件")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data.get('entities', [])
    triples = data.get('triples', [])
    
    # 选择浏览类型
    browse_type = st.radio(
        "选择浏览类型",
        ["实体", "三元组"],
        horizontal=True
    )
    
    if browse_type == "实体":
        # 实体类型筛选
        entity_types = list(set([e['type'] for e in entities]))
        selected_type = st.selectbox("选择实体类型", ["全部"] + entity_types)
        
        # 筛选实体
        if selected_type == "全部":
            filtered_entities = entities
        else:
            filtered_entities = [e for e in entities if e['type'] == selected_type]
        
        # 搜索
        search = st.text_input("搜索实体", placeholder="输入实体名称...")
        if search:
            filtered_entities = [e for e in filtered_entities if search in e['name']]
        
        # 显示实体
        st.write(f"共 {len(filtered_entities)} 个实体")
        
        # 分页显示
        page_size = 20
        total_pages = (len(filtered_entities) + page_size - 1) // page_size
        page = st.number_input("页码", min_value=1, max_value=max(1, total_pages), value=1)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        for i, entity in enumerate(filtered_entities[start_idx:end_idx], start_idx + 1):
            st.markdown(f"{i}. **{entity['name']}** ({entity['type']})")
    
    else:  # 三元组
        # 关系类型筛选
        relation_types = list(set([t['relation'] for t in triples]))
        selected_relation = st.selectbox("选择关系类型", ["全部"] + relation_types)
        
        # 筛选三元组
        if selected_relation == "全部":
            filtered_triples = triples
        else:
            filtered_triples = [t for t in triples if t['relation'] == selected_relation]
        
        # 搜索
        search = st.text_input("搜索三元组", placeholder="输入实体名称...")
        if search:
            filtered_triples = [
                t for t in filtered_triples 
                if search in t['subject'] or search in t['object']
            ]
        
        # 显示三元组
        st.write(f"共 {len(filtered_triples)} 个三元组")
        
        # 分页显示
        page_size = 20
        total_pages = (len(filtered_triples) + page_size - 1) // page_size
        page = st.number_input("页码", min_value=1, max_value=max(1, total_pages), value=1)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        for i, triple in enumerate(filtered_triples[start_idx:end_idx], start_idx + 1):
            st.markdown(f"""
            <div class="knowledge-item">
                {i}. <strong>{triple['subject']}</strong> 
                <span style="color: #1f77b4;">-[{triple['relation']}]-></span> 
                <strong>{triple['object']}</strong>
            </div>
            """, unsafe_allow_html=True)


def show_statistics_page():
    """统计分析页面"""
    st.header("📈 统计分析")
    st.write("知识图谱的统计信息和分析结果")
    
    # 加载统计信息
    stats = load_statistics()
    
    if not stats:
        st.error("❌ 未找到统计信息")
        return
    
    # 基本统计
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 基本统计")
        st.metric("实体总数", stats.get('total_entities', 0))
        st.metric("三元组总数", stats.get('total_triples', 0))
    
    with col2:
        st.subheader("📈 类型分布")
        
        # 实体类型分布
        if stats.get('entity_types'):
            st.write("**实体类型分布**")
            entity_types = stats['entity_types']
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                st.write(f"- {entity_type}: {count}")
    
    # 关系类型分布
    if stats.get('relation_types'):
        st.subheader("🔗 关系类型分布")
        relation_types = stats['relation_types']
        for relation_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- {relation_type}: {count}")
    
    # 挖掘结果
    mining_file = config.PROJECT_ROOT / "knowledge_mining_results" / "network_analysis.json"
    if mining_file.exists():
        st.subheader("🔍 知识挖掘结果")
        
        with open(mining_file, 'r', encoding='utf-8') as f:
            mining_data = json.load(f)
        
        # 核心实体
        if mining_data.get('top_degree_centrality'):
            st.write("**核心实体（度中心性Top 10）**")
            for item in mining_data['top_degree_centrality']:
                st.write(f"- {item['node']}: {item['centrality']:.4f}")


def show_graph_visualization_page():
    """图谱可视化页面"""
    st.header("🕸️ 知识图谱可视化")
    st.write("交互式知识图谱可视化，探索实体之间的关系")
    
    # 初始化全屏状态
    if 'fullscreen_mode' not in st.session_state:
        st.session_state.fullscreen_mode = False
    
    if not PYVIS_AVAILABLE:
        st.error("❌ pyvis未安装，请运行: pip install pyvis")
        return
    
    # 加载数据
    json_file = config.PROCESSED_DATA_DIR / "fused_knowledge" / "msi_hbp_fused.json"
    if not json_file.exists():
        json_file = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    
    if not json_file.exists():
        st.error("❌ 未找到知识文件")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = {e['name']: e for e in data.get('entities', [])}
    triples = data.get('triples', [])
    
    # 可视化选项
    if not st.session_state.fullscreen_mode:
        st.subheader("⚙️ 可视化设置")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 实体类型筛选
            entity_types = list(set([e['type'] for e in entities.values()]))
            selected_types = st.multiselect(
                "选择实体类型",
                entity_types,
                default=entity_types[:3] if len(entity_types) > 3 else entity_types
            )
        
        with col2:
            # 关系类型筛选
            relation_types = list(set([t['relation'] for t in triples]))
            selected_relations = st.multiselect(
                "选择关系类型",
                relation_types,
                default=relation_types
            )
        
        with col3:
            # 节点数量限制
            max_nodes = st.slider("最大节点数", 10, 200, 50)
        
        # 中心实体选择
        center_entity = st.selectbox(
            "选择中心实体（可选）",
            ["无"] + list(entities.keys())[:100],
            help="选择一个实体作为中心，显示其周围的关系"
        )
        
        # 生成按钮和全屏按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
        with col_btn1:
            generate_button = st.button("🎨 生成图谱", type="primary", use_container_width=True)
        with col_btn2:
            fullscreen_button = st.button("🖥️ 全屏模式", use_container_width=True)
    else:
        # 全屏模式下使用之前的设置
        if 'last_settings' in st.session_state:
            selected_types = st.session_state.last_settings['selected_types']
            selected_relations = st.session_state.last_settings['selected_relations']
            max_nodes = st.session_state.last_settings['max_nodes']
            center_entity = st.session_state.last_settings['center_entity']
        else:
            # 默认设置
            entity_types = list(set([e['type'] for e in entities.values()]))
            selected_types = entity_types[:3] if len(entity_types) > 3 else entity_types
            relation_types = list(set([t['relation'] for t in triples]))
            selected_relations = relation_types
            max_nodes = 50
            center_entity = "无"
        
        generate_button = True
        fullscreen_button = False
        
        # 全屏模式控制栏
        st.markdown("### 🖥️ 全屏模式")
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("❌ 退出全屏", use_container_width=True):
                st.session_state.fullscreen_mode = False
                st.rerun()
        with col2:
            if st.button("⚙️ 重新设置", use_container_width=True):
                st.session_state.fullscreen_mode = False
                st.rerun()
    
    if fullscreen_button:
        # 保存当前设置
        st.session_state.last_settings = {
            'selected_types': selected_types,
            'selected_relations': selected_relations,
            'max_nodes': max_nodes,
            'center_entity': center_entity
        }
        st.session_state.fullscreen_mode = True
        st.rerun()
    
    if generate_button:
        with st.spinner("正在生成图谱..."):
            # 筛选三元组
            filtered_triples = [
                t for t in triples
                if t['relation'] in selected_relations
                and entities.get(t['subject'], {}).get('type') in selected_types
                and entities.get(t['object'], {}).get('type') in selected_types
            ]
            
            # 如果选择了中心实体，只显示相关的三元组
            if center_entity != "无":
                filtered_triples = [
                    t for t in filtered_triples
                    if t['subject'] == center_entity or t['object'] == center_entity
                ]
            
            # 限制数量
            filtered_triples = filtered_triples[:max_nodes]
            
            if not filtered_triples:
                st.warning("⚠️ 没有符合条件的三元组")
                return
            
            # 创建网络图
            net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
            net.barnes_hut()
            
            # 实体类型颜色映射
            type_colors = {
                '疾病': '#e74c3c',
                '症状': '#f39c12',
                '病机': '#9b59b6',
                '中药': '#27ae60',
                '方剂': '#3498db',
                '治则治法': '#1abc9c'
            }
            
            # 添加节点和边
            added_nodes = set()
            for triple in filtered_triples:
                subject = triple['subject']
                obj = triple['object']
                relation = triple['relation']
                
                # 添加主体节点
                if subject not in added_nodes:
                    subject_type = entities.get(subject, {}).get('type', '未知')
                    color = type_colors.get(subject_type, '#95a5a6')
                    net.add_node(subject, label=subject, color=color, title=f"{subject}\n类型: {subject_type}")
                    added_nodes.add(subject)
                
                # 添加客体节点
                if obj not in added_nodes:
                    obj_type = entities.get(obj, {}).get('type', '未知')
                    color = type_colors.get(obj_type, '#95a5a6')
                    net.add_node(obj, label=obj, color=color, title=f"{obj}\n类型: {obj_type}")
                    added_nodes.add(obj)
                
                # 添加边
                net.add_edge(subject, obj, label=relation, title=relation)
            
            # 设置物理引擎
            net.set_options("""
            {
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -8000,
                        "centralGravity": 0.3,
                        "springLength": 95,
                        "springConstant": 0.04
                    },
                    "minVelocity": 0.75
                }
            }
            """)
            
            # 保存并显示
            html_file = config.PROJECT_ROOT / "graph_visualization.html"
            net.save_graph(str(html_file))
            
            # 读取HTML并显示
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 根据模式选择显示高度
            if st.session_state.fullscreen_mode:
                display_height = 900  # 全屏模式更高
                st.markdown("---")
            else:
                display_height = 600  # 普通模式
            
            components.html(html_content, height=display_height, scrolling=True)
            
            st.success(f"✅ 已生成图谱，包含 {len(added_nodes)} 个节点，{len(filtered_triples)} 条边")
            
            # 全屏模式提示
            if st.session_state.fullscreen_mode:
                st.info("💡 提示：图谱已放大显示，可以更清晰地查看节点和关系。点击'退出全屏'返回设置界面。")
            
            # 图例
            st.markdown("### 📌 图例")
            cols = st.columns(len(type_colors))
            for i, (entity_type, color) in enumerate(type_colors.items()):
                with cols[i]:
                    st.markdown(f'<span style="color: {color};">●</span> {entity_type}', unsafe_allow_html=True)
            
            # 操作提示
            if not st.session_state.fullscreen_mode:
                st.markdown("---")
                st.markdown("### 💡 操作提示")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**鼠标操作**")
                    st.write("- 🖱️ 拖拽节点：移动位置")
                    st.write("- 🔍 滚轮：缩放图谱")
                    st.write("- 👆 悬停：查看详情")
                with col2:
                    st.write("**显示模式**")
                    st.write("- 🎨 生成图谱：创建新图谱")
                    st.write("- 🖥️ 全屏模式：放大显示")
                    st.write("- ⚙️ 重新设置：修改参数")
    
    # 如果没有生成图谱，显示使用说明
    if not generate_button and not st.session_state.fullscreen_mode:
        st.markdown("---")
        st.markdown("### 📖 使用说明")
        
        st.write("**步骤1：选择筛选条件**")
        st.write("- 选择要显示的实体类型（疾病、症状、病机、中药、方剂、治则治法）")
        st.write("- 选择要显示的关系类型（治疗、引起、由...组成、使用）")
        st.write("- 设置最大节点数（建议50-100个）")
        
        st.write("**步骤2：选择中心实体（可选）**")
        st.write("- 如果想查看某个实体的周围关系，可以选择中心实体")
        st.write("- 例如：选择'高血压'查看与高血压相关的所有知识")
        
        st.write("**步骤3：生成图谱**")
        st.write("- 点击'🎨 生成图谱'按钮创建可视化")
        st.write("- 点击'🖥️ 全屏模式'放大显示")
        
        st.write("**步骤4：交互探索**")
        st.write("- 拖拽节点调整布局")
        st.write("- 滚轮缩放查看细节")
        st.write("- 鼠标悬停查看实体信息")


def show_export_page():
    """数据导出页面"""
    st.header("📥 数据导出")
    st.write("导出知识图谱数据为不同格式")
    
    # 加载数据
    json_file = config.PROCESSED_DATA_DIR / "fused_knowledge" / "msi_hbp_fused.json"
    if not json_file.exists():
        json_file = config.PROCESSED_DATA_DIR / "extracted_triples" / "msi_hbp_triples.json"
    
    if not json_file.exists():
        st.error("❌ 未找到知识文件")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data.get('entities', [])
    triples = data.get('triples', [])
    
    st.subheader("📊 数据概览")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("实体数量", len(entities))
    with col2:
        st.metric("三元组数量", len(triples))
    
    st.markdown("---")
    
    # 导出选项
    st.subheader("📤 导出格式")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON格式
        st.markdown("### 1. JSON格式")
        st.write("完整的知识图谱数据（JSON格式）")
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下载JSON",
            data=json_data,
            file_name="msi_hbp_knowledge_graph.json",
            mime="application/json",
            use_container_width=True
        )
        
        # CSV格式 - 实体
        st.markdown("### 2. CSV格式 - 实体")
        st.write("实体列表（CSV格式）")
        
        csv_entities = "名称,类型\n"
        for e in entities:
            csv_entities += f"{e['name']},{e['type']}\n"
        
        st.download_button(
            label="📥 下载实体CSV",
            data=csv_entities.encode('utf-8-sig'),
            file_name="msi_hbp_entities.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # CSV格式 - 三元组
        st.markdown("### 3. CSV格式 - 三元组")
        st.write("三元组列表（CSV格式）")
        
        csv_triples = "主体,关系,客体\n"
        for t in triples:
            csv_triples += f"{t['subject']},{t['relation']},{t['object']}\n"
        
        st.download_button(
            label="📥 下载三元组CSV",
            data=csv_triples.encode('utf-8-sig'),
            file_name="msi_hbp_triples.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Markdown格式
        st.markdown("### 4. Markdown格式")
        st.write("知识图谱报告（Markdown格式）")
        
        md_content = f"""# MSI-HBP 知识图谱报告

## 数据统计

- **实体总数**: {len(entities)}
- **三元组总数**: {len(triples)}

## 实体类型分布

"""
        entity_types = {}
        for e in entities:
            entity_types[e['type']] = entity_types.get(e['type'], 0) + 1
        
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            md_content += f"- {entity_type}: {count}\n"
        
        md_content += "\n## 关系类型分布\n\n"
        
        relation_types = {}
        for t in triples:
            relation_types[t['relation']] = relation_types.get(t['relation'], 0) + 1
        
        for relation_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            md_content += f"- {relation_type}: {count}\n"
        
        md_content += f"\n## 示例三元组\n\n"
        for i, t in enumerate(triples[:20], 1):
            md_content += f"{i}. {t['subject']} -[{t['relation']}]-> {t['object']}\n"
        
        st.download_button(
            label="📥 下载Markdown报告",
            data=md_content.encode('utf-8'),
            file_name="msi_hbp_report.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Neo4j Cypher导出
    st.subheader("🔧 Neo4j Cypher脚本")
    st.write("生成用于导入Neo4j的Cypher脚本")
    
    if st.button("生成Cypher脚本"):
        cypher_script = "// MSI-HBP 知识图谱 - Neo4j导入脚本\n\n"
        cypher_script += "// 创建实体\n"
        
        for e in entities[:100]:  # 限制数量
            cypher_script += f"CREATE (:{e['type']} {{name: '{e['name']}', project: 'MSI-HBP'}});\n"
        
        cypher_script += "\n// 创建关系\n"
        
        for t in triples[:100]:  # 限制数量
            relation = t['relation'].replace('-', '_').replace('...', '')
            cypher_script += f"MATCH (a {{name: '{t['subject']}'}}), (b {{name: '{t['object']}'}}) CREATE (a)-[:{relation}]->(b);\n"
        
        st.code(cypher_script, language="cypher")
        
        st.download_button(
            label="📥 下载Cypher脚本",
            data=cypher_script.encode('utf-8'),
            file_name="msi_hbp_neo4j_import.cypher",
            mime="text/plain",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
