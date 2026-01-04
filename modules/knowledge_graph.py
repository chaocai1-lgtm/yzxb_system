"""
知识图谱模块
可视化展示五模块知识图谱
"""

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from config.settings import *

def check_neo4j_available():
    """检查Neo4j是否可用"""
    from modules.auth import check_neo4j_available as auth_check
    return auth_check()

def get_neo4j_driver():
    """获取Neo4j连接（复用auth模块的缓存连接）"""
    from modules.auth import get_neo4j_driver as auth_get_driver
    return auth_get_driver()

def get_current_student():
    """获取当前学生信息"""
    if st.session_state.get('user_role') == 'student':
        return st.session_state.get('student_id')
    return None

def log_graph_activity(activity_type, content_id=None, content_name=None, details=None):
    """记录知识图谱活动"""
    student_id = get_current_student()
    if not student_id:
        return
    
    from modules.auth import log_activity
    log_activity(
        student_id=student_id,
        activity_type=activity_type,
        module_name="知识图谱",
        content_id=content_id,
        content_name=content_name,
        details=details
    )

def get_knowledge_graph_data(module_id=None):
    """从Neo4j获取知识图谱数据"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            if module_id:
                # 获取特定模块的知识图谱
                result = session.run("""
                    MATCH path = (m:yzbx_Module {id: $module_id})-[:CONTAINS]->(c:yzbx_Chapter)-[:CONTAINS]->(k:yzbx_Knowledge)
                    OPTIONAL MATCH (k)-[r:PREREQUISITE]->(k2:yzbx_Knowledge)
                    RETURN m, c, k, r, k2
                """, module_id=module_id)
            else:
                # 获取所有模块
                result = session.run("""
                    MATCH (m:yzbx_Module)-[:CONTAINS]->(c:yzbx_Chapter)-[:CONTAINS]->(k:yzbx_Knowledge)
                    RETURN m, c, k
                    LIMIT 50
                """)
            
            data = [dict(record) for record in result]
        
        # 不关闭driver，保持连接池复用
        return data
    except Exception:
        return []

def create_knowledge_graph_viz(module_id=None):
    """创建知识图谱可视化"""
    # 使用浅色背景
    net = Network(height="1100px", width="100%", bgcolor="#ffffff", font_color="#333333")
    
    # 配置物理引擎 - 优化布局，使用直线，减少交叠
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -35000,
                "centralGravity": 0.1,
                "springLength": 250,
                "springConstant": 0.02,
                "damping": 0.5,
                "avoidOverlap": 1
            },
            "stabilization": {
                "enabled": true,
                "iterations": 200,
                "fit": true
            },
            "minVelocity": 0.75
        },
        "layout": {
            "improvedLayout": true,
            "randomSeed": 42,
            "hierarchical": false
        },
        "edges": {
            "smooth": false,
            "font": {
                "size": 20,
                "color": "#000000",
                "strokeWidth": 0,
                "align": "middle",
                "bold": true
            },
            "color": {
                "inherit": false
            },
            "width": 2.5,
            "chosen": {
                "edge": true
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.8
                }
            }
        },
        "nodes": {
            "font": {
                "size": 50,
                "face": "Arial",
                "strokeWidth": 3,
                "strokeColor": "#ffffff",
                "color": "#000000",
                "bold": true,
                "align": "top",
                "vadjust": -140
            },
            "shadow": {
                "enabled": true,
                "size": 8,
                "x": 2,
                "y": 2
            },
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "chosen": {
                "node": true
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    # 获取数据
    data = get_knowledge_graph_data(module_id)
    
    # 知识点详细信息（用于tooltip显示）
    knowledge_details = {
        "牙龈结构": "包括游离龈、附着龈和龈乳头三部分。游离龈形成龈沟，正常深度0.5-3mm。",
        "牙周膜组成": "主要由胶原纤维束、细胞成分和基质组成。纤维束分为6组，提供牙齿支持。",
        "牙槽骨特征": "分为固有牙槽骨和支持骨。X线上固有牙槽骨呈硬骨板（骨白线）。",
        "牙骨质类型": "分为无细胞纤维性牙骨质（颈1/3）和有细胞纤维性牙骨质（根尖1/3）。",
        "龈沟液功能": "含有免疫球蛋白、补体、白细胞等，具有冲洗和抗菌防御作用。",
        "牙周韧带力学": "可承受咀嚼力，具有本体感觉，调节咬合力大小。",
        "骨改建机制": "成骨细胞与破骨细胞平衡，受机械力和炎症因子调控。",
        "菌斑形成过程": "获得性膜形成→早期定植菌黏附→共聚集→成熟生物膜，约需7-14天。",
        "致病菌种类": "主要包括牙龈卟啉单胞菌(Pg)、放线聚集杆菌(Aa)、福赛坦氏菌(Tf)等红色复合体。",
        "生物膜结构": "由细菌、胞外多糖基质、水通道组成，具有抗生素耐药性。",
        "牙石形成": "菌斑矿化形成，龈上牙石主要来自唾液，龈下牙石来自龈沟液。",
        "食物嵌塞": "分为垂直型和水平型，可导致局部牙周破坏，需去除病因。",
        "不良修复体": "悬突、边缘不密合等导致菌斑滞留，需重新修复。",
        "探诊技术": "使用牙周探针，力度20-25g，记录6个位点探诊深度。",
        "附着丧失测量": "CAL=探诊深度-釉牙骨质界到龈缘距离，反映累积破坏。",
        "牙周图表制作": "记录探诊深度、出血、松动度等，便于治疗计划和随访。",
        "牙龈炎分类": "包括菌斑性和非菌斑性牙龈病，前者最常见。",
        "牙周炎分期": "2018新分类采用分期(I-IV)和分级(A-C)系统。",
        "新分类标准": "基于附着丧失、骨吸收、失牙数分期；基于进展速率分级。",
        "龈上洁治": "去除龈上牙石和菌斑，使用超声或手工器械。",
        "龈下刮治": "深入牙周袋清除龈下牙石和感染牙骨质。",
        "根面平整": "使刮治后根面光滑，利于牙周组织再附着。",
        "翻瓣术": "切开牙龈、翻瓣暴露病变区进行清创，常见改良Widman翻瓣术。",
        "植骨术": "在骨缺损区填入骨替代材料，促进骨再生。",
        "引导再生": "使用屏障膜引导牙周组织选择性再生。",
        "口腔卫生宣教": "教授Bass刷牙法，使用牙线/牙间刷，定期专业维护。",
        "刷牙方法": "推荐Bass法或改良Bass法，每天2次，每次2分钟。",
        "辅助工具": "包括牙线、牙间刷、冲牙器等，根据牙间隙选择。",
        "复查周期": "牙周炎患者建议3-6个月复查一次，高危患者更频繁。",
        "SPT原则": "支持性牙周治疗，终身维护，定期评估和必要的再治疗。",
        "长期管理": "监测探诊深度、出血指数，及时发现复发。"
    }
    
    # 如果没有数据，创建示例数据
    if not data:
        # 创建示例知识图谱 - 更丰富的内容，添加知识点间的关联
        example_modules = {
            "M1": {
                "name": "生物学基础", 
                "description": "牙周组织的解剖结构和生理功能基础",
                "chapters": {
                    "牙周组织解剖": ["牙龈结构", "牙周膜组成", "牙槽骨特征", "牙骨质类型"],
                    "牙周组织生理": ["龈沟液功能", "牙周韧带力学", "骨改建机制"]
                }
            },
            "M2": {
                "name": "病因与发病机制", 
                "description": "牙周病的致病因素和发生发展机制",
                "chapters": {
                    "牙菌斑生物膜": ["菌斑形成过程", "致病菌种类", "生物膜结构"],
                    "局部促进因素": ["牙石形成", "食物嵌塞", "不良修复体"]
                }
            },
            "M3": {
                "name": "诊断与分类", 
                "description": "牙周病的检查方法和分类标准",
                "chapters": {
                    "牙周检查": ["探诊技术", "附着丧失测量", "牙周图表制作"],
                    "牙周病分类": ["牙龈炎分类", "牙周炎分期", "新分类标准"]
                }
            },
            "M4": {
                "name": "治疗", 
                "description": "牙周病的各种治疗方法",
                "chapters": {
                    "牙周基础治疗": ["龈上洁治", "龈下刮治", "根面平整"],
                    "牙周手术治疗": ["翻瓣术", "植骨术", "引导再生"]
                }
            },
            "M5": {
                "name": "预防与维护", 
                "description": "牙周病的预防措施和长期维护治疗",
                "chapters": {
                    "牙周病预防": ["口腔卫生宣教", "刷牙方法", "辅助工具"],
                    "牙周维护治疗": ["复查周期", "SPT原则", "长期管理"]
                }
            }
        }
        
        # 知识点之间的关联关系
        knowledge_links = [
            ("牙龈结构", "龈沟液功能", "产生"),
            ("牙周膜组成", "牙周韧带力学", "决定"),
            ("牙槽骨特征", "骨改建机制", "遵循"),
            ("菌斑形成过程", "致病菌种类", "涉及"),
            ("菌斑形成过程", "牙石形成", "导致"),
            ("致病菌种类", "生物膜结构", "构成"),
            ("探诊技术", "附着丧失测量", "用于"),
            ("牙周炎分期", "新分类标准", "依据"),
            ("龈上洁治", "龈下刮治", "先于"),
            ("龈下刮治", "根面平整", "配合"),
            ("翻瓣术", "植骨术", "结合"),
            ("刷牙方法", "口腔卫生宣教", "包含"),
            ("SPT原则", "复查周期", "规定"),
            # 跨模块关联
            ("致病菌种类", "探诊技术", "指导"),
            ("骨改建机制", "植骨术", "原理"),
            ("龈沟液功能", "探诊技术", "评估"),
        ]
        
        # 根据模块ID筛选
        if module_id and module_id in example_modules:
            modules_to_show = {module_id: example_modules[module_id]}
        else:
            modules_to_show = example_modules
        
        # 收集所有知识点ID用于建立关联
        all_knowledge_ids = {}
        
        for m_id, m_info in modules_to_show.items():
            # 添加模块节点 - 核心节点
            module_desc = m_info.get('description', '')
            net.add_node(m_id, 
                        label=m_info['name'], 
                        color='#FF6B6B', 
                        size=120, 
                        title=f"📚 {m_info['name']}\n\n{module_desc}\n\n💡 这是牙周病学的核心模块之一，包含重要的理论知识和临床技能",
                        shape='dot', 
                        borderWidth=4)
            
            for chapter, knowledge_points in m_info['chapters'].items():
                c_id = f"{m_id}_{chapter}"
                
                # 章节解读
                chapter_descriptions = {
                    "牙周组织解剖": "牙周组织包括牙龈、牙周膜、牙槽骨和牙骨质四部分，是牙齿的支持组织。理解其解剖结构是学习牙周病学的基础。",
                    "牙周组织生理": "牙周组织具有保护、支持、感觉和修复再生功能。龈沟液、牙周膜等的生理功能对维持口腔健康至关重要。",
                    "牙菌斑生物膜": "牙菌斑是牙周病的始动因子，以生物膜形式存在，对抗生素有耐药性。理解其形成过程和结构对防治牙周病很重要。",
                    "局部促进因素": "牙石、食物嵌塞、不良修复体等局部因素会促进菌斑堆积和牙周破坏，临床上需要识别并去除这些因素。",
                    "牙周检查": "牙周检查是诊断的基础，包括探诊、附着丧失测量等，需要掌握标准化的检查方法和记录方式。",
                    "牙周病分类": "2018年新分类采用分期分级系统，更科学地评估疾病严重程度和进展风险，指导治疗计划制定。",
                    "牙周基础治疗": "包括龈上洁治、龈下刮治和根面平整，是所有牙周治疗的基础，约80%的牙周炎患者可通过基础治疗控制。",
                    "牙周手术治疗": "用于基础治疗后仍存在深袋或骨缺损的患者，包括翻瓣术、植骨术、引导组织再生等。",
                    "牙周病预防": "预防是最经济有效的策略，通过正确的口腔卫生习惯可预防大部分牙周病，重点是菌斑控制。",
                    "牙周维护治疗": "牙周炎是慢性病，需要终身维护。SPT（支持性牙周治疗）对防止复发至关重要，复查周期一般3-6个月。",
                }
                chapter_desc = chapter_descriptions.get(chapter, f"本章节介绍{chapter}相关内容")
                
                # 添加章节节点
                net.add_node(c_id, 
                            label=chapter, 
                            color='#4ECDC4', 
                            size=120,
                            title=f"📖 {chapter}\n\n{chapter_desc}\n\n包含知识点：{len(knowledge_points)}个",
                            shape='dot', 
                            borderWidth=4)
                net.add_edge(m_id, c_id, label="包含", title="模块包含章节", width=3, color="#888888", smooth=False)
                
                # 添加知识点
                for k_name in knowledge_points:
                    k_id = f"{c_id}_{k_name}"
                    all_knowledge_ids[k_name] = k_id
                    
                    # 获取知识点详细说明
                    detail = knowledge_details.get(k_name, f"{k_name}是{chapter}中的重要知识点，需要重点掌握。")
                    
                    net.add_node(k_id, 
                                label=k_name, 
                                color='#95E1D3', 
                                size=120,
                                title=f"📝 {k_name}\n\n{detail}\n\n所属章节：{chapter}",
                                shape='dot', 
                                borderWidth=4)
                    net.add_edge(c_id, k_id, label="涵盖", title="章节涵盖知识点", width=2, color="#aaaaaa", smooth=False)
        
        # 添加知识点之间的关联边 - 所有边都有标签
        for source, target, relation in knowledge_links:
            source_id = all_knowledge_ids.get(source)
            target_id = all_knowledge_ids.get(target)
            if source_id and target_id:
                net.add_edge(source_id, target_id, 
                           label=relation,
                           color="#e91e63", 
                           width=2.5, 
                           dashes=True,
                           arrows={'to': {'enabled': True, 'scaleFactor': 0.8}},
                           title=f"知识关联：{source} {relation} {target}",
                           smooth=False)
    else:
        nodes_added = set()
        
        for record in data:
            # 添加模块节点
            if 'm' in record and record['m'] and record['m']['id'] not in nodes_added:
                m = record['m']
                desc = m.get('description', '牙周病学核心知识模块')
                net.add_node(
                    m['id'],
                    label=m['name'],
                    color='#FF6B6B',
                    size=120,
                    title=f"📚 {m['name']}\n\n{desc}",
                    shape='dot',
                    borderWidth=4
                )
                nodes_added.add(m['id'])
            
            # 添加章节节点
            if 'c' in record and record['c'] and record['c']['id'] not in nodes_added:
                c = record['c']
                net.add_node(
                    c['id'],
                    label=c['name'],
                    color='#4ECDC4',
                    size=120,
                    title=f"📖 {c['name']}\n\n本章节包含多个相关知识点，构成完整的知识体系。",
                    shape='dot',
                    borderWidth=4
                )
                nodes_added.add(c['id'])
                if 'm' in record and record['m']:
                    net.add_edge(record['m']['id'], c['id'], 
                               label="包含", 
                               title="模块包含章节",
                               width=3, 
                               color="#888888",
                               smooth=False)
            
            # 添加知识点节点
            if 'k' in record and record['k'] and record['k']['id'] not in nodes_added:
                k = record['k']
                k_name = k['name']
                k_desc = knowledge_details.get(k_name, f"{k_name}的详细内容和学习要点")
                difficulty = k.get('difficulty', '未知')
                
                net.add_node(
                    k['id'],
                    label=k_name,
                    color='#95E1D3',
                    size=120,
                    title=f"📝 {k_name}\n\n{k_desc}\n\n难度：{difficulty}",
                    shape='dot',
                    borderWidth=4
                )
                nodes_added.add(k['id'])
                if 'c' in record and record['c']:
                    net.add_edge(record['c']['id'], k['id'], 
                               label="涵盖", 
                               title="章节涵盖知识点",
                               width=2, 
                               color="#aaaaaa",
                               smooth=False)
            
            # 添加知识点前置关系 - 确保有标签
            if 'k2' in record and record['k2']:
                k2 = record['k2']
                if k2['id'] not in nodes_added:
                    k2_name = k2['name']
                    k2_desc = knowledge_details.get(k2_name, f"{k2_name}的详细内容和学习要点")
                    
                    net.add_node(
                        k2['id'],
                        label=k2_name,
                        color='#95E1D3',
                        size=120,
                        title=f"📝 {k2_name}\n\n{k2_desc}",
                        shape='dot',
                        borderWidth=4
                    )
                    nodes_added.add(k2['id'])
                if 'k' in record and record['k']:
                    net.add_edge(record['k']['id'], k2['id'], 
                               label="前置", 
                               title=f"前置关系：需要先掌握 {k2['name']}",
                               arrows='to', 
                               dashes=True, 
                               color="#ff9999", 
                               width=2.5,
                               smooth=False)
    
    # 保存并返回HTML
    try:
        net.save_graph("temp_graph.html")
        with open("temp_graph.html", 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except Exception:
        return "<div style='padding:20px;text-align:center;'>知识图谱生成中...</div>"

def render_knowledge_graph():
    """渲染知识图谱页面"""
    st.title("🗺️ 章节知识图谱")
    
    # 记录进入知识图谱
    log_graph_activity("进入模块", details="访问知识图谱")
    
    st.markdown("""
    可视化展示牙周病学五模块知识结构，帮助你建立系统的知识网络。
    - 🔴 **红色节点**：教学模块
    - 🔵 **蓝色节点**：章节
    - 🟢 **绿色节点**：知识点
    - **虚线箭头**：前置关系
    """)
    
    # 模块选择
    modules = [
        ("全部", None),
        ("M1 - 生物学基础", "M1"),
        ("M2 - 病因与发病机制", "M2"),
        ("M3 - 诊断与分类", "M3"),
        ("M4 - 治疗", "M4"),
        ("M5 - 预防与维护", "M5")
    ]
    
    selected = st.selectbox(
        "选择要查看的模块",
        options=[m[0] for m in modules],
        index=0
    )
    
    module_id = next((m[1] for m in modules if m[0] == selected), None)
    
    # 记录查看模块
    if module_id:
        log_graph_activity("查看模块", content_id=module_id, content_name=selected)
    
    # 生成并显示图谱
    with st.spinner("生成知识图谱中..."):
        html_content = create_knowledge_graph_viz(module_id)
        components.html(html_content, height=1200)
    
    # 学习进度标记
    st.sidebar.title("📊 学习进度")
    st.sidebar.info("未来功能：标记已掌握的知识点")
