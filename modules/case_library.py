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
                "present_illness": """患者自述3个月前开始出现刷牙时牙龈出血，初期仅早晨刷牙时偶有血丝，未予重视。近1个月来出血加重，刷牙时牙膏泡沫常呈粉红色，偶尔进食硬物时也会出血。伴有口臭，晨起明显。无自发性出血，无牙龈疼痛。曾自行使用"消炎牙膏"无明显改善。

既往刷牙习惯：每日刷牙1次，约1分钟，不使用牙线或牙间隙刷。平时进食速度快，喜食软烂食物。5年前曾洁牙1次。

吸烟史：10支/天，20年。饮酒史：偶尔社交饮酒。""",
                "symptoms": ["牙龈红肿", "探诊出血", "牙周袋形成4-6mm", "牙槽骨水平吸收"],
                "diagnosis": "慢性牙周炎（III期B级）",
                "difficulty": "简单",
                "patient_info": {"age": 45, "gender": "男", "occupation": "教师"},
                "medical_history": """【既往史】高血压病史5年，规律服用氨氯地平5mg/日，血压控制在130/85mmHg左右。
【过敏史】否认药物及食物过敏史。
【家族史】父亲有糖尿病，母亲有高血压。
【个人史】吸烟20年，10支/日；偶尔饮酒。""",
                "treatment_plan": [
                    "【第一阶段：基础治疗】",
                    "1. 口腔卫生宣教：教授改良Bass刷牙法，建议每日刷牙2次，每次3分钟",
                    "2. 龈上洁治术：使用超声洁牙机去除龈上牙石和菌斑",
                    "3. 龈下刮治及根面平整术（SRP）：分2-4次完成全口治疗",
                    "4. 局部药物治疗：盐酸米诺环素软膏（派丽奥）置入深牙周袋",
                    "【第二阶段：再评估】",
                    "5. 4-6周后复查，评估治疗效果",
                    "6. 检查菌斑控制情况（目标：菌斑指数<20%）",
                    "7. 重新探诊，记录探诊深度和出血情况",
                    "【第三阶段：维护治疗】",
                    "8. 每3个月复查一次，进行SPT（支持性牙周治疗）",
                    "9. 强调戒烟的重要性，提供戒烟咨询"
                ],
                "key_points": [
                    "⚠️ 高血压患者注意事项：治疗前测量血压，避免使用含肾上腺素过高的麻药",
                    "📋 吸烟与牙周炎：吸烟是牙周炎的重要危险因素，会影响治疗效果和预后",
                    "🔄 长期随访：慢性牙周炎需要终身维护，强调定期复查的重要性",
                    "📝 菌斑控制记录：每次复查记录菌斑指数，评估患者依从性"
                ],
                "diagnosis_analysis": {
                    "clinical_exam": {
                        "title": "临床检查发现",
                        "items": [
                            "牙龈颜色：暗红色，质地松软，点彩消失",
                            "探诊深度：全口多数牙位4-6mm，16/26/36/46区最深达6mm",
                            "探诊出血：BOP阳性率约70%",
                            "附着丧失：3-4mm",
                            "牙齿松动度：36、46 I度松动",
                            "菌斑指数（PLI）：约65%",
                            "牙石情况：龈上牙石++，龈下牙石+"
                        ]
                    },
                    "radiographic": {
                        "title": "X线片分析",
                        "items": [
                            "全口曲面断层片示：牙槽骨呈水平型吸收",
                            "骨吸收量为根长的1/3-1/2",
                            "下颌磨牙根分叉区可见低密度影像，提示I度根分叉病变",
                            "牙周膜间隙增宽，部分牙位硬骨板不连续",
                            "无明显根尖周病变"
                        ]
                    },
                    "differential": {
                        "title": "鉴别诊断",
                        "items": [
                            "与侵袭性牙周炎鉴别：本例发病年龄较大（45岁），病程进展慢，破坏程度与菌斑量相符",
                            "与牙龈炎鉴别：已有牙槽骨吸收和附着丧失，非单纯牙龈炎",
                            "与创伤𬌗鉴别：咬合检查未发现明显早接触，磨耗不显著",
                            "与药物性牙龈增生鉴别：服用氨氯地平，但未见明显牙龈增生"
                        ]
                    },
                    "staging": {
                        "title": "分期分级依据（2018年新分类）",
                        "content": """【分期】III期（严重牙周炎）
• 附着丧失：3-4mm（复杂性因素：根分叉病变I度）
• 骨吸收：延伸至根中1/3-根尖1/3
• 失牙数：0颗（因牙周炎）

【分级】B级（中度进展）
• 直接证据：无5年以上的影像学资料对比
• 间接证据：骨丧失/年龄比值 = 4mm/45年 ≈ 0.09（<0.25提示A级，但考虑吸烟因素升级为B级）
• 危险因素：吸烟10支/日（重度吸烟者，为分级加重因素）"""
                    }
                }
            },
            {
                "id": "case2", 
                "title": "侵袭性牙周炎病例", 
                "chief_complaint": "前牙松动2周，自觉牙齿移位", 
                "present_illness": """患者2周前发现上前牙松动，并逐渐出现牙间隙增大，上前牙有"往外翘"的感觉。近日自觉咬合不适，进食时不敢用前牙咬断食物。偶有牙龈出血，但无明显疼痛。

患者初中时曾因"牙周病"在当地医院洁牙2次，之后未再复诊。近2年感觉多颗后牙咬物无力，但因无疼痛未就诊。

月经史：月经规律，无异常。婚育史：未婚未育。""",
                "symptoms": ["前牙扇形移位", "深牙周袋>7mm", "快速骨吸收", "探诊出血"],
                "diagnosis": "侵袭性牙周炎（IV期C级）",
                "difficulty": "困难",
                "patient_info": {"age": 28, "gender": "女", "occupation": "白领"},
                "medical_history": """【既往史】既往体健，否认高血压、糖尿病、心脏病等慢性病史。
【过敏史】青霉素过敏（皮疹）。
【家族史】母亲40岁时多数牙齿松动拔除，现佩戴全口义齿；外祖母也有早期失牙史。
【个人史】不吸烟，不饮酒。""",
                "treatment_plan": [
                    "【第一阶段：急症处理与全身治疗】",
                    "1. 松牙暂时性固定：使用光固化树脂夹板固定11-21",
                    "2. 全身抗生素：阿奇霉素500mg首剂，之后250mg/日×4天（青霉素过敏替代方案）",
                    "3. 联合甲硝唑400mg 3次/日×7天",
                    "【第二阶段：基础治疗】",
                    "4. 口腔卫生强化指导：强调牙间隙清洁，使用牙间刷",
                    "5. 全口龈下刮治及根面平整：分4次完成，局部麻醉下进行",
                    "6. 深牙周袋辅助治疗：盐酸米诺环素软膏袋内给药",
                    "【第三阶段：再评估与手术治疗】",
                    "7. 6-8周后复查评估",
                    "8. 必要时考虑牙周翻瓣术+引导组织再生术（GTR）",
                    "【第四阶段：长期维护】",
                    "9. 每2-3个月复查，严密监测",
                    "10. 考虑进行基因检测和免疫功能评估"
                ],
                "key_points": [
                    "🧬 家族史阳性：母系家族成员有早期失牙史，高度提示遗传易感性",
                    "⚠️ 年轻患者严重破坏：28岁即有严重骨吸收，需警惕侵袭性牙周炎",
                    "💊 抗生素选择：青霉素过敏，选用阿奇霉素替代阿莫西林",
                    "🔬 菌斑与破坏不成比例：口腔卫生尚可但破坏严重，是侵袭性牙周炎特点",
                    "📅 长期随访：需终身密切随访，复查间隔应短于慢性牙周炎"
                ],
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
        tab1, tab2, tab3, tab4 = st.tabs(["🩺 病史与症状", "🔬 诊断分析", "💊 治疗方案", "📝 学习要点"])
        
        with tab1:
            # 主诉
            st.markdown("#### 📢 主诉")
            st.info(selected_case['chief_complaint'])
            
            # 现病史
            if 'present_illness' in selected_case:
                st.markdown("#### 📖 现病史")
                st.markdown(f"""
                <div style="background: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800; white-space: pre-line;">
                {selected_case['present_illness']}
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📋 既往史与全身情况")
                medical_history = selected_case.get('medical_history', '患者既往体健，否认重大疾病史')
                st.markdown(f"""
                <div style="background: #fce4ec; padding: 15px; border-radius: 8px; border-left: 4px solid #e91e63; white-space: pre-line;">
                {medical_history}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### 🔍 主要临床表现")
                symptoms = selected_case['symptoms']
                if isinstance(symptoms, list):
                    for s in symptoms:
                        st.markdown(f"""
                        <div style="background: #e3f2fd; padding: 8px 12px; margin: 4px 0; border-radius: 5px; border-left: 3px solid #2196f3;">
                            • {s}
                        </div>
                        """, unsafe_allow_html=True)
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
            
            current_phase = None
            step_count = 0
            
            for step in treatment:
                # 检测是否是阶段标题（包含【】）
                if step.startswith('【') and '】' in step:
                    current_phase = step
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 12px 20px; margin: 15px 0 10px 0; border-radius: 8px;">
                        <strong>{step}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    step_count += 1
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 12px 15px; margin: 5px 0 5px 20px; 
                                border-radius: 8px; border-left: 4px solid #4ECDC4;">
                        {step}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 治疗注意事项
            st.markdown("#### ⚠️ 治疗注意事项")
            key_points = selected_case.get('key_points', ['注意病史采集', '仔细临床检查'])
            for point in key_points:
                st.markdown(f"""
                <div style="background: #fff8e1; padding: 10px 15px; margin: 5px 0; 
                            border-radius: 8px; border-left: 4px solid #ffc107;">
                    {point}
                </div>
                """, unsafe_allow_html=True)
        
        with tab4:
            st.markdown("#### 📝 学习要点总结")
            
            # 显示关键学习要点
            key_points = selected_case.get('key_points', ['注意病史采集', '仔细临床检查', '辅助检查分析'])
            for i, point in enumerate(key_points, 1):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                            padding: 12px 15px; margin: 8px 0; border-radius: 8px; 
                            border-left: 4px solid #4caf50;">
                    <strong>要点 {i}：</strong> {point}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown("#### ✏️ 我的学习笔记")
            notes = st.text_area(
                "记录你对这个病例的理解、疑问和思考",
                height=150,
                placeholder="例如：\n1. 这个病例的诊断依据是...\n2. 治疗方案的关键点是...\n3. 需要进一步学习的内容...",
                key=f"notes_{selected_case['id']}"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 保存笔记", type="primary", key=f"save_notes_{selected_case['id']}"):
                    if notes:
                        log_case_activity("保存笔记", case_id=selected_case['id'], 
                                        case_title=selected_case['title'], 
                                        details=f"笔记: {notes[:100]}")
                        st.success("✅ 笔记已保存！")
                    else:
                        st.warning("请先输入笔记内容")
            with col2:
                st.markdown("*笔记将保存到你的学习记录中*")
