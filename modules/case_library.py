"""
病例库模块
提供病例浏览、搜索和详情查看功能
"""

import streamlit as st
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
from config.settings import *

def check_neo4j_available():
    """检查Neo4j是否可用"""
    from modules.auth import check_neo4j_available as auth_check
    return auth_check()

def get_current_student():
    """获取当前学生信息"""
    if st.session_state.get('user_role') == 'student':
        return st.session_state.get('student_id')
    return None

def log_case_activity(activity_type, case_id=None, case_title=None, details=None):
    """记录病例库活动"""
    student_id = get_current_student()
    if not student_id:
        return
    
    from modules.auth import log_activity
    log_activity(
        student_id=student_id,
        activity_type=activity_type,
        module_name="病例库",
        content_id=case_id,
        content_name=case_title,
        details=details
    )

def search_cases(query="", difficulty=None):
    """搜索病例"""
    try:
        es = Elasticsearch(
            cloud_id=ELASTICSEARCH_CLOUD_ID,
            basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
        )
        
        # 构建搜索查询
        if query:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "symptoms", "diagnosis", "chief_complaint"]
                    }
                }
            }
        else:
            search_body = {"query": {"match_all": {}}}
        
        # 添加难度过滤
        if difficulty:
            search_body["query"] = {
                "bool": {
                    "must": [search_body["query"]],
                    "filter": [{"term": {"difficulty": difficulty}}]
                }
            }
        
        result = es.search(index="yzbx_cases", body=search_body, size=10)
        es.close()
        
        return [hit["_source"] for hit in result["hits"]["hits"]]
    except Exception:
        return []

def get_case_detail(case_id):
    """从Neo4j获取病例详情"""
    if not check_neo4j_available():
        return None
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # 获取病例基本信息
            result = session.run("""
                MATCH (c:yzbx_Case {id: $case_id})
                RETURN c
            """, case_id=case_id)
            
            case = result.single()
            if not case:
                driver.close()
                return None
            
            case_data = dict(case['c'])
            
            # 获取关联的知识点
            result = session.run("""
                MATCH (c:yzbx_Case {id: $case_id})-[:RELATES_TO]->(k:yzbx_Knowledge)
                RETURN k.id as id, k.name as name
            """, case_id=case_id)
            
            case_data['knowledge_points'] = [dict(record) for record in result]
        
        driver.close()
        return case_data
    except Exception:
        return None

def render_case_library():
    """渲染病例库页面"""
    st.title("📚 临床病例学习中心")
    
    # 记录进入病例库
    log_case_activity("进入模块", details="访问病例库")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0; color: white;">🏥 牙周病学临床病例库</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">通过真实临床病例学习，掌握牙周病诊断与治疗的核心技能</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有病例供选择
    all_cases = search_cases("", None)
    
    if not all_cases:
        # 使用丰富的示例数据 - 包含详细诊断分析
        all_cases = [
            {
                "id": "case1", 
                "title": "慢性牙周炎典型病例", 
                "chief_complaint": "牙龈出血3个月，刷牙时加重", 
                "symptoms": ["牙龈红肿", "探诊出血", "牙周袋形成4-6mm", "牙槽骨水平吸收"],
                "diagnosis": "慢性牙周炎（III期B级）",
                "difficulty": "简单",
                "patient_info": {"age": 45, "gender": "男", "occupation": "教师"},
                "medical_history": "高血压病史5年，规律服药控制良好",
                "treatment_plan": ["口腔卫生指导", "龈上洁治", "龈下刮治及根面平整", "3个月后复查"],
                "key_points": ["注意询问全身病史", "关注菌斑控制情况", "制定个性化维护计划"],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "牙龈颜色：暗红色，质地松软",
                            "探诊深度：全口多数牙位4-6mm，后牙区为主",
                            "探诊出血：BOP阳性率约70%",
                            "附着丧失：3-4mm",
                            "牙齿松动度：个别后牙I度松动"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "牙槽骨呈水平型吸收",
                            "骨吸收量为根长的1/3-1/2",
                            "根分叉病变：下颌磨牙I度病变",
                            "牙周膜间隙增宽"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "与侵袭性牙周炎鉴别：本例发病年龄较大，病程进展慢，与菌斑量相符",
                            "与牙龈炎鉴别：已有牙槽骨吸收和附着丧失，非单纯牙龈炎",
                            "与创伤𬌗鉴别：咬合检查未发现明显早接触"
                        ]
                    },
                    "staging": {
                        "title": "分期分级依据",
                        "content": "根据2018年牙周病新分类：III期（严重）——附着丧失≥5mm或骨吸收延伸至根中1/3；B级（中度进展）——年骨丧失/年龄比值0.25-1.0，无明显加重因素"
                    }
                }
            },
            {
                "id": "case2", 
                "title": "侵袭性牙周炎病例", 
                "chief_complaint": "前牙松动2周，自觉牙齿移位", 
                "symptoms": ["前牙扇形移位", "深牙周袋>7mm", "快速骨吸收", "探诊出血"],
                "diagnosis": "侵袭性牙周炎（IV期C级）",
                "difficulty": "困难",
                "patient_info": {"age": 28, "gender": "女", "occupation": "白领"},
                "medical_history": "既往体健，母亲有早期失牙史",
                "treatment_plan": ["系统性抗生素治疗", "全口龈下刮治", "松牙固定", "定期维护"],
                "key_points": ["注意家族史询问", "年轻患者骨破坏严重需警惕", "强调长期维护重要性"],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "上颌切牙唇向扇形移位，牙间隙增大",
                            "第一磨牙和切牙区牙周破坏最严重",
                            "探诊深度：前牙区和第一磨牙达8-10mm",
                            "菌斑量与组织破坏程度不成比例——菌斑少但破坏严重",
                            "牙齿松动II-III度"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "第一磨牙垂直型骨吸收，呈典型'弧形吸收'",
                            "切牙区骨吸收达根长1/2以上",
                            "骨吸收范围局限于第一磨牙和切牙——'门牙-磨牙型'",
                            "磨牙根分叉病变明显"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "与慢性牙周炎鉴别：发病年龄轻，进展快速，破坏与菌斑不成比例",
                            "排除系统性疾病：需检查血常规、血糖，排除白血病等",
                            "家族史阳性支持诊断：母亲有早期失牙史"
                        ]
                    },
                    "staging": {
                        "title": "分期分级依据",
                        "content": "IV期（晚期）——需要复杂治疗，存在咬合功能障碍；C级（快速进展）——直接证据：1年内有快速进展史，间接证据：年轻患者严重破坏，无明确风险因素"
                    }
                }
            },
            {
                "id": "case3", 
                "title": "牙周-牙髓联合病变", 
                "chief_complaint": "右下后牙持续性疼痛1周", 
                "symptoms": ["牙齿叩痛(+)", "牙龈窦道", "深牙周袋达根尖", "根尖暗影"],
                "diagnosis": "牙周-牙髓联合病变（真性联合病变）",
                "difficulty": "困难",
                "patient_info": {"age": 52, "gender": "男", "occupation": "工程师"},
                "medical_history": "糖尿病史8年，血糖控制一般",
                "treatment_plan": ["先行根管治疗", "炎症控制后牙周治疗", "必要时行牙周手术", "密切随访"],
                "key_points": ["鉴别原发病灶", "关注糖尿病对愈合的影响", "多学科联合治疗"],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "46牙冠大面积充填体",
                            "叩痛(++)，冷热测无反应",
                            "牙龈近中可见窦道，探针可通向根尖",
                            "颊侧牙周袋深达根尖部（12mm）",
                            "牙齿松动II度"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "根尖区低密度影像（直径约5mm）",
                            "近中骨吸收从冠方延伸至根尖",
                            "形成连续的'J'形透射影",
                            "根分叉区可见透射影像"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "原发性牙髓病变：活力测无反应+根尖病变，提示牙髓坏死",
                            "原发性牙周病变：深牙周袋从冠方延伸，提示牙周破坏",
                            "真性联合病变：两者同时存在，形成交通",
                            "判断预后：糖尿病患者愈合能力下降，需严格控糖"
                        ]
                    },
                    "staging": {
                        "title": "治疗策略分析",
                        "content": "因同时存在牙髓和牙周病变，需联合治疗。先行根管治疗控制根尖感染，2-3个月后评估牙周愈合情况，再决定是否需要牙周手术。糖尿病患者需控制空腹血糖<7.0mmol/L后进行有创操作。"
                    }
                }
            },
            {
                "id": "case4", 
                "title": "药物性牙龈增生", 
                "chief_complaint": "服用降压药后牙龈逐渐增大1年", 
                "symptoms": ["牙龈弥漫性增生", "质地较韧", "覆盖牙面1/3-1/2", "菌斑堆积"],
                "diagnosis": "药物性牙龈增生（硝苯地平相关）",
                "difficulty": "中等",
                "patient_info": {"age": 58, "gender": "女", "occupation": "退休"},
                "medical_history": "高血压10年，服用硝苯地平",
                "treatment_plan": ["口腔卫生强化", "建议替换降压药", "牙龈切除术", "定期维护"],
                "key_points": ["详细药物史询问", "与心内科医生沟通", "术后可能复发需告知"],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "全口牙龈弥漫性增生，前牙区明显",
                            "龈乳头圆钝肥大，覆盖牙面1/3-1/2",
                            "牙龈质地较韧，颜色淡粉色",
                            "菌斑指数偏高，局部牙石沉积",
                            "探诊深度4-6mm（假性牙周袋）"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "牙槽骨未见明显吸收",
                            "牙周膜间隙正常",
                            "提示增生为软组织改变，非牙周破坏"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "与遗传性牙龈纤维瘤病鉴别：有明确用药史，非自幼发病",
                            "与白血病性牙龈增生鉴别：血常规正常，质地较韧而非松软",
                            "与慢性牙周炎鉴别：X线无骨吸收，为假性牙周袋",
                            "药物相关性：硝苯地平是二氢吡啶类钙通道阻滞剂，为常见致病药物"
                        ]
                    },
                    "staging": {
                        "title": "发病机制说明",
                        "content": "钙通道阻滞剂（硝苯地平、氨氯地平等）可抑制成纤维细胞胶原酶活性，导致胶原过度沉积。发生率约20-30%，多在用药后3-6个月出现。菌斑是重要的协同因素——良好口腔卫生可减轻增生程度。"
                    }
                }
            },
            {
                "id": "case5", 
                "title": "坏死性溃疡性牙龈炎", 
                "chief_complaint": "牙龈疼痛出血3天，伴口臭", 
                "symptoms": ["龈乳头坏死", "灰白色假膜", "自发性出血", "剧烈疼痛"],
                "diagnosis": "坏死性溃疡性牙龈炎（NUG）",
                "difficulty": "中等",
                "patient_info": {"age": 23, "gender": "男", "occupation": "大学生"},
                "medical_history": "近期熬夜备考，压力大，吸烟",
                "treatment_plan": ["局部清创冲洗", "甲硝唑含漱", "全身抗感染", "改善生活方式"],
                "key_points": ["询问诱发因素", "排除HIV感染", "强调戒烟和作息调整"],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "龈乳头顶端坏死，呈'火山口状'凹陷",
                            "坏死区覆盖灰白色假膜",
                            "假膜擦除后基底红、糜烂、易出血",
                            "剧烈疼痛，影响进食",
                            "口腔恶臭明显",
                            "可伴有低热、颌下淋巴结肿大"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "急性期X线无明显改变",
                            "反复发作可见龈乳头间牙槽骨吸收（骨嵴呈截平状）"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "与急性疱疹性龈口炎鉴别：NUG主要累及龈乳头，无水疱史",
                            "与急性白血病鉴别：需查血常规排除",
                            "与艾滋病相关牙周炎鉴别：NUG可为HIV感染首发症状，高危人群需排查",
                            "与剥脱性龈炎鉴别：NUG有典型坏死假膜"
                        ]
                    },
                    "staging": {
                        "title": "发病机制与诱因",
                        "content": "NUG是机会性感染，由梭形杆菌和螺旋体共同致病。主要诱因包括：精神压力、睡眠不足、吸烟、营养不良、免疫抑制等。本例患者有熬夜、压力大、吸烟等多个诱因。治疗后需强调生活方式改善以防复发。"
                    }
                }
            },
        ]
    
    # 病例选择区
    st.markdown("### 📂 选择学习病例")
    
    case_options = {f"🏥 {c['title']}": c for c in all_cases}
    selected_case_name = st.selectbox(
        "选择病例进行学习",
        options=list(case_options.keys()),
        index=0,
        label_visibility="collapsed",
        help="从下拉列表中选择一个病例进行深入学习"
    )
    
    selected_case = case_options.get(selected_case_name)
    
    if selected_case:
        # 记录查看病例
        log_case_activity("查看病例", case_id=selected_case['id'], case_title=selected_case['title'])
        
        st.divider()
        
        # 病例头部信息卡片
        difficulty_colors = {"简单": "#28a745", "中等": "#ffc107", "困难": "#dc3545"}
        diff_color = difficulty_colors.get(selected_case['difficulty'], "#6c757d")
        
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {diff_color};">
            <h2 style="margin: 0 0 10px 0;">📋 {selected_case['title']}</h2>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <span style="background: {diff_color}; color: white; padding: 5px 15px; border-radius: 20px;">
                    难度: {selected_case['difficulty']}
                </span>
                <span style="background: #17a2b8; color: white; padding: 5px 15px; border-radius: 20px;">
                    诊断: {selected_case['diagnosis']}
                </span>
                <span style="background: #6c757d; color: white; padding: 5px 15px; border-radius: 20px;">
                    ID: {selected_case['id']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # 患者信息
        if 'patient_info' in selected_case:
            patient = selected_case['patient_info']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**👤 年龄：** {patient.get('age', '-')}岁")
            with col2:
                st.markdown(f"**⚥ 性别：** {patient.get('gender', '-')}")
            with col3:
                st.markdown(f"**💼 职业：** {patient.get('occupation', '-')}")
            with col4:
                st.markdown(f"**📋 病历号：** {selected_case['id']}")
        
        # 使用选项卡组织内容
        tab1, tab2, tab3, tab4 = st.tabs(["🩺 病史与症状", "🔬 诊断分析", "💊 治疗方案", "📝 学习笔记"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📢 主诉")
                st.info(selected_case['chief_complaint'])
                
                st.markdown("#### 📋 既往史")
                st.warning(selected_case.get('medical_history', '患者既往体健，否认重大疾病史'))
            
            with col2:
                st.markdown("#### 🔍 临床表现")
                symptoms = selected_case['symptoms']
                if isinstance(symptoms, list):
                    for s in symptoms:
                        st.markdown(f"• {s}")
                else:
                    st.markdown(symptoms)
        
        with tab2:
            st.markdown("#### 🏥 临床诊断")
            st.success(f"**{selected_case['diagnosis']}**")
            
            # 详细诊断分析
            diagnosis_analysis = selected_case.get('diagnosis_analysis', {})
            
            if diagnosis_analysis:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 临床检查发现
                    if 'clinical_exam' in diagnosis_analysis:
                        exam = diagnosis_analysis['clinical_exam']
                        st.markdown(f"#### 🔍 {exam['title']}")
                        for item in exam['items']:
                            st.markdown(f"""
                            <div style="background: #e8f5e9; padding: 8px 12px; margin: 4px 0; border-radius: 5px; border-left: 3px solid #4caf50;">
                                ✓ {item}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # X线片分析
                    if 'radiographic' in diagnosis_analysis:
                        st.markdown("")
                        xray = diagnosis_analysis['radiographic']
                        st.markdown(f"#### 📷 {xray['title']}")
                        for item in xray['items']:
                            st.markdown(f"""
                            <div style="background: #e3f2fd; padding: 8px 12px; margin: 4px 0; border-radius: 5px; border-left: 3px solid #2196f3;">
                                📋 {item}
                            </div>
                            """, unsafe_allow_html=True)
                
                with col2:
                    # 鉴别诊断
                    if 'differential' in diagnosis_analysis:
                        diff = diagnosis_analysis['differential']
                        st.markdown(f"#### ⚖️ {diff['title']}")
                        for item in diff['items']:
                            st.markdown(f"""
                            <div style="background: #fff3e0; padding: 8px 12px; margin: 4px 0; border-radius: 5px; border-left: 3px solid #ff9800;">
                                💭 {item}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 分期分级依据
                    if 'staging' in diagnosis_analysis:
                        st.markdown("")
                        staging = diagnosis_analysis['staging']
                        st.markdown(f"#### 📊 {staging['title']}")
                        st.markdown(f"""
                        <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; border: 1px solid #9c27b0;">
                            <p style="margin: 0; line-height: 1.6;">{staging['content']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # 如果没有详细分析，显示简要诊断要点
                st.markdown("#### 💡 诊断要点")
                key_points = selected_case.get('key_points', ['注意病史采集', '仔细临床检查', '辅助检查分析'])
                for i, point in enumerate(key_points, 1):
                    st.markdown(f"""
                    <div style="background: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #0066cc;">
                        <strong>{i}.</strong> {point}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 诊断要点提醒
            st.markdown("")
            st.markdown("#### 💡 学习要点")
            key_points = selected_case.get('key_points', ['注意病史采集', '仔细临床检查', '辅助检查分析'])
            cols = st.columns(len(key_points))
            for i, (col, point) in enumerate(zip(cols, key_points)):
                with col:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 12px; border-radius: 8px; text-align: center; height: 100%;">
                        <strong>要点 {i+1}</strong><br>
                        <span style="font-size: 13px;">{point}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("#### 💊 治疗计划")
            treatment = selected_case.get('treatment_plan', ['口腔卫生指导', '基础治疗', '定期复查'])
            for i, step in enumerate(treatment, 1):
                st.markdown(f"""
                <div style="background: #f0f0f0; padding: 12px; margin: 8px 0; border-radius: 8px;">
                    <span style="background: #4ECDC4; color: white; padding: 3px 10px; border-radius: 15px; margin-right: 10px;">
                        第{i}步
                    </span>
                    {step}
                </div>
                """, unsafe_allow_html=True)
        
        with tab4:
            st.markdown("#### ✏️ 我的学习笔记")
            notes = st.text_area(
                "记录你对这个病例的理解、疑问和思考",
                height=150,
                placeholder="例如：\n1. 这个病例的诊断依据是...\n2. 治疗方案的关键点是...\n3. 需要进一步学习的内容..."
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 保存笔记", type="primary"):
                    if notes:
                        log_case_activity("保存笔记", case_id=selected_case['id'], 
                                        case_title=selected_case['title'], 
                                        details=f"笔记: {notes[:100]}")
                        st.success("✅ 笔记已保存！")
                    else:
                        st.warning("请先输入笔记内容")
            with col2:
                st.markdown("*笔记将保存到你的学习记录中*")
