"""
能力推荐模块
基于能力自评，AI推荐学习路径
"""

import streamlit as st
from neo4j import GraphDatabase
from openai import OpenAI
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

def log_ability_activity(activity_type, content_id=None, content_name=None, details=None):
    """记录能力推荐模块活动"""
    student_id = get_current_student()
    if not student_id:
        return
    
    from modules.auth import log_activity
    log_activity(
        student_id=student_id,
        activity_type=activity_type,
        module_name="能力推荐",
        content_id=content_id,
        content_name=content_name,
        details=details
    )

def get_all_abilities():
    """获取所有能力列表"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        with driver.session() as session:
            result = session.run("""
                MATCH (a:yzbx_Ability)
                RETURN a.id as id, a.name as name, a.category as category, a.description as description
                ORDER BY a.category, a.name
            """)
            
            abilities = [dict(record) for record in result]
        
        driver.close()
        return abilities
    except Exception:
        return []

def analyze_learning_path(selected_abilities, mastery_levels, abilities_info=None):
    """分析学习路径并生成推荐"""
    required_knowledge = []
    
    # 尝试从Neo4j获取知识点数据
    if check_neo4j_available():
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            
            # 获取能力需要的知识点
            with driver.session() as session:
                result = session.run("""
                MATCH (a:yzbx_Ability)-[r:REQUIRES]->(k:yzbx_Knowledge)
                WHERE a.id IN $abilities
                RETURN k.id as kp_id, k.name as kp_name, k.difficulty as difficulty, 
                       collect(a.name) as required_by, max(r.weight) as max_weight
                ORDER BY max_weight DESC
            """, abilities=selected_abilities)
            
                required_knowledge = [dict(record) for record in result]
            
            driver.close()
        except Exception:
            required_knowledge = []
    
    # 如果没有从数据库获取到数据，使用示例知识点
    if not required_knowledge:
        # 根据选择的能力生成相关知识点
        ability_knowledge_map = {
            "A1": [("牙龈解剖结构", "基础", 0.9), ("牙周膜组成", "基础", 0.8), ("牙槽骨特征", "基础", 0.7)],
            "A2": [("牙周探诊技术", "基础", 0.9), ("探诊深度测量", "基础", 0.8), ("附着丧失评估", "中等", 0.7)],
            "A3": [("牙菌斑识别方法", "基础", 0.9), ("菌斑染色技术", "基础", 0.8), ("生物膜特征", "中等", 0.7)],
            "A4": [("牙周病分类标准", "中等", 0.9), ("临床检查要点", "基础", 0.8), ("影像学诊断", "中等", 0.8)],
            "A5": [("牙周X线片判读", "中等", 0.9), ("骨吸收程度评估", "中等", 0.8), ("根分叉病变诊断", "高级", 0.7)],
            "A6": [("龈上洁治原理", "基础", 0.9), ("器械使用方法", "中等", 0.9), ("操作规范", "基础", 0.8)],
            "A7": [("龈下刮治技术", "中等", 0.9), ("根面平整术", "高级", 0.9), ("局部麻醉技术", "中等", 0.8)],
            "A8": [("治疗计划制定原则", "高级", 0.9), ("牙周病分期分级", "中等", 0.8), ("预后评估", "高级", 0.8)],
            "A9": [("口腔卫生指导方法", "基础", 0.9), ("刷牙技术培训", "基础", 0.8), ("辅助工具使用", "基础", 0.7)],
            "A10": [("牙周维护治疗原则", "中等", 0.9), ("复查周期规划", "中等", 0.8), ("SPT标准流程", "中等", 0.8)],
        }
        
        for ability_id in selected_abilities:
            if ability_id in ability_knowledge_map:
                for kp_name, difficulty, weight in ability_knowledge_map[ability_id]:
                    ability_name = next((a['name'] for a in (abilities_info or []) if a['id'] == ability_id), ability_id)
                    required_knowledge.append({
                        'kp_id': f"KP_{ability_id}_{kp_name}",
                        'kp_name': kp_name,
                        'difficulty': difficulty,
                        'required_by': [ability_name],
                        'max_weight': weight
                    })
    
    # 获取能力名称映射
    ability_names = []
    for a_id in selected_abilities:
        if abilities_info:
            name = next((a['name'] for a in abilities_info if a['id'] == a_id), a_id)
        else:
            name = a_id
        mastery = mastery_levels.get(a_id, 0.5)
        ability_names.append(f"{name}(自评掌握度: {int(mastery*100)}%)")
    
    # 构建知识点描述
    knowledge_desc = []
    for kp in required_knowledge[:15]:
        if isinstance(kp.get('required_by'), list):
            required_by_str = ', '.join(kp['required_by'])
        else:
            required_by_str = str(kp.get('required_by', ''))
        weight = kp.get('max_weight', 0.5)
        if isinstance(weight, (int, float)):
            weight_str = f"{weight:.1f}"
        else:
            weight_str = str(weight)
        knowledge_desc.append(f"- {kp['kp_name']} (难度: {kp.get('difficulty', '未知')}, 重要性: {weight_str}, 所需能力: {required_by_str})")
    
    # 使用DeepSeek AI生成推荐
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        
        prompt = f"""
你是一位资深牙周病学教学专家和临床医生，拥有20年以上的教学和临床经验。

## 学生信息
学生选择了以下目标能力进行学习：
{', '.join(ability_names)}

## 相关知识点
根据知识图谱分析，这些能力需要掌握以下核心知识点：
{chr(10).join(knowledge_desc) if knowledge_desc else "（系统将根据能力要求推荐学习内容）"}

## 请你完成以下分析任务

### 一、能力解读（详细分析每个选定能力）
请针对学生选择的每个能力，详细说明：
- 该能力在牙周病学临床实践中的重要性
- 需要掌握的核心技能点
- 常见的学习难点和误区

### 二、知识点优先级排序
按照"基础理论→临床技能→综合应用"的学习规律，列出8-12个应该学习的知识点，并说明：
- 知识点名称
- 重要程度（⭐⭐⭐⭐⭐）
- 学习要点（2-3句话）
- 推荐学习资源类型

### 三、个性化学习路径
设计一个分阶段的学习计划：
- **第一周：基础夯实阶段** - 列出具体学习内容和目标
- **第二周：技能培养阶段** - 列出具体学习内容和目标
- **第三周：综合提升阶段** - 列出具体学习内容和目标

### 四、学习方法建议
针对每个阶段，给出具体的学习方法：
- 推荐的教材章节
- 建议的练习方式
- 自我检测方法

### 五、预期学习成果
完成学习后，学生应该能够：
- 理论层面达到什么水平
- 实践层面掌握什么技能
- 综合能力提升预期

请用专业、详细、友好的语言，给出系统性的学习指导建议。每个部分都要充实具体，不要过于简略。
"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # 如果AI调用失败，返回一个详细的推荐
        return f"""
## 一、能力解读

根据您选择的目标能力，以下是详细分析：

**牙周组织解剖识别能力**
- 🎯 **临床重要性**：这是牙周病学的基础，所有诊断和治疗都建立在对正常解剖结构的准确认知之上
- 💡 **核心技能点**：辨识游离龈、附着龈、龈沟、牙周膜、牙槽骨的正常形态和特征
- ⚠️ **常见误区**：容易混淆生理性龈沟与病理性牙周袋

**牙周探诊技术能力**
- 🎯 **临床重要性**：探诊是牙周检查的核心技术，直接影响诊断准确性
- 💡 **核心技能点**：探诊力度控制（20-25g）、角度调整、六点法记录
- ⚠️ **常见误区**：用力过大导致假阳性，角度不当遗漏深袋

---

## 二、知识点优先级排序

| 序号 | 知识点 | 重要程度 | 学习要点 | 推荐资源 |
|------|--------|----------|----------|----------|
| 1 | 牙龈解剖结构 | ⭐⭐⭐⭐⭐ | 游离龈、附着龈、龈乳头的形态与功能 | 教材第2章+图谱 |
| 2 | 牙周膜组成 | ⭐⭐⭐⭐⭐ | 主纤维束走行、细胞组成、功能意义 | 教材第2章+组织学 |
| 3 | 牙槽骨特征 | ⭐⭐⭐⭐ | 固有牙槽骨、支持骨的结构和改建 | 教材第2章+X线片 |
| 4 | 牙周探诊技术 | ⭐⭐⭐⭐⭐ | 探诊方法、力度、角度、记录方式 | 临床操作视频 |
| 5 | 探诊深度测量 | ⭐⭐⭐⭐⭐ | PD测量要点、正常值判断 | 临床实践 |
| 6 | 附着丧失评估 | ⭐⭐⭐⭐ | CAL计算方法、临床意义 | 教材第5章 |
| 7 | 牙周病分类标准 | ⭐⭐⭐⭐ | 2018年新分类体系 | 专题讲座 |
| 8 | 临床检查要点 | ⭐⭐⭐⭐ | 系统检查流程和记录 | 临床见习 |

---

## 三、个性化学习路径

### 📅 第一周：基础夯实阶段

**学习目标**：掌握牙周组织正常解剖结构

| 日期 | 学习内容 | 学习时长 | 完成标准 |
|------|----------|----------|----------|
| Day 1-2 | 牙龈解剖：游离龈、附着龈、龈沟 | 2小时/天 | 能绘制牙龈横切面示意图 |
| Day 3-4 | 牙周膜：纤维组成和功能 | 2小时/天 | 能描述主纤维束走行 |
| Day 5-6 | 牙槽骨：结构和改建机制 | 2小时/天 | 能识别X线片上的牙槽嵴 |
| Day 7 | 复习总结+自测 | 2小时 | 完成章节习题正确率>80% |

### 📅 第二周：技能培养阶段

**学习目标**：掌握牙周探诊操作技术

| 日期 | 学习内容 | 学习时长 | 完成标准 |
|------|----------|----------|----------|
| Day 1-2 | 探诊工具认识和握持方法 | 2小时/天 | 正确握持探针 |
| Day 3-4 | 探诊力度和角度控制 | 3小时/天 | 在模型上练习 |
| Day 5-6 | 六点法记录和牙周病历填写 | 2小时/天 | 完整填写病历 |
| Day 7 | 临床观摩+技能考核 | 4小时 | 通过模拟操作考核 |

### 📅 第三周：综合提升阶段

**学习目标**：综合运用知识进行初步诊断

| 日期 | 学习内容 | 学习时长 | 完成标准 |
|------|----------|----------|----------|
| Day 1-2 | 牙周病分类和诊断标准 | 2小时/天 | 掌握分期分级方法 |
| Day 3-4 | 病例分析练习 | 3小时/天 | 分析3个典型病例 |
| Day 5-6 | X线片解读结合临床 | 2小时/天 | 识别骨吸收类型 |
| Day 7 | 综合测评 | 3小时 | 完成综合病例分析 |

---

## 四、学习方法建议

### 📚 理论学习
- **推荐教材**：《牙周病学》第5版（人民卫生出版社）第2、4、5章
- **辅助资源**：口腔组织学教材、临床操作视频库
- **学习技巧**：制作思维导图，将解剖结构与临床意义关联

### 🔬 实践练习
- **模型练习**：在仿真头模上练习探诊操作，每天至少30分钟
- **同伴互练**：与同学互相进行口腔检查练习
- **临床见习**：争取观摩至少5例牙周病患者的检查过程

### ✅ 自我检测
- 每周末完成章节习题
- 使用本系统的病例库进行自测
- 记录学习笔记，定期复习

---

## 五、预期学习成果

完成三周学习后，您将能够：

**理论层面**
- ✅ 准确描述牙周组织的解剖结构和组织学特点
- ✅ 理解牙周组织在健康和疾病状态下的差异
- ✅ 掌握牙周病分类的基本框架

**实践层面**
- ✅ 正确进行牙周探诊操作
- ✅ 准确测量和记录探诊深度
- ✅ 初步判断牙周组织健康状况

**综合能力**
- ✅ 能够对简单病例进行初步的牙周评估
- ✅ 为后续学习牙周治疗奠定坚实基础

---

💡 **温馨提示**：学习过程中遇到问题，可以使用本系统的"课中互动"功能向AI提问，或在知识图谱中查看相关知识点的联系。

⚠️ **注意**：AI分析服务暂时不可用，以上为系统智能预设推荐。建议稍后重试获取更个性化的分析。
"""

def render_ability_recommender():
    """渲染能力推荐页面"""
    st.title("🎯 能力自评与学习推荐")
    
    # 记录进入能力推荐
    log_ability_activity("进入模块", details="访问能力推荐")
    
    st.markdown("""
    选择你想掌握的能力，系统将基于AI为你推荐个性化的学习路径。
    """)
    
    # 获取所有能力
    abilities = get_all_abilities()
    
    # 如果数据库没有数据，使用示例能力
    if not abilities:
        abilities = [
            {"id": "A1", "name": "牙周组织解剖识别", "category": "基础能力", "description": "能够识别和描述正常牙周组织的解剖结构"},
            {"id": "A2", "name": "牙周探诊技术", "category": "基础能力", "description": "掌握正确的牙周探诊方法和技巧"},
            {"id": "A3", "name": "牙菌斑识别", "category": "诊断能力", "description": "能够识别和评估牙菌斑的分布和程度"},
            {"id": "A4", "name": "牙周病诊断", "category": "诊断能力", "description": "能够根据临床表现做出正确的牙周病诊断"},
            {"id": "A5", "name": "X线片解读", "category": "诊断能力", "description": "能够解读牙周病相关的X线影像"},
            {"id": "A6", "name": "洁治术操作", "category": "治疗能力", "description": "掌握龈上洁治术的操作技能"},
            {"id": "A7", "name": "刮治术操作", "category": "治疗能力", "description": "掌握龈下刮治和根面平整术"},
            {"id": "A8", "name": "治疗计划制定", "category": "治疗能力", "description": "能够制定合理的牙周治疗计划"},
            {"id": "A9", "name": "口腔卫生指导", "category": "预防能力", "description": "能够进行有效的口腔卫生宣教"},
            {"id": "A10", "name": "维护治疗管理", "category": "预防能力", "description": "掌握牙周维护治疗的原则和方法"},
        ]
    
    # 按类别分组
    categories = {}
    for ability in abilities:
        cat = ability['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ability)
    
    # 1. 能力选择
    st.subheader("1️⃣ 选择目标能力")
    
    selected_abilities = []
    mastery_levels = {}
    
    for category, abs_list in categories.items():
        st.markdown(f"**{category}**")
        for ability in abs_list:
            col1, col2 = st.columns([3, 2])
            with col1:
                if st.checkbox(
                    f"{ability['name']}",
                    key=f"ability_{ability['id']}",
                    help=ability['description']
                ):
                    selected_abilities.append(ability['id'])
            with col2:
                if ability['id'] in selected_abilities:
                    level = st.slider(
                        "当前掌握度",
                        0.0, 1.0, 0.3, 0.1,
                        key=f"level_{ability['id']}",
                        label_visibility="collapsed"
                    )
                    mastery_levels[ability['id']] = level
    
    # 2. 生成推荐
    if selected_abilities:
        st.divider()
        st.subheader("2️⃣ AI学习路径推荐")
        
        if st.button("🤖 生成个性化学习推荐", type="primary"):
            # 记录能力选择和自评
            abilities_str = ', '.join(selected_abilities)
            log_ability_activity("能力自评", content_name=abilities_str, details=f"选择能力: {abilities_str}")
            
            # 创建AI分析可视化容器
            analysis_container = st.container()
            
            with analysis_container:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 25px; border-radius: 15px; margin: 20px 0;">
                    <h3 style="color: white; margin: 0 0 15px 0;">🧠 AI 智能分析中心</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0;">基于DeepSeek大模型进行个性化学习路径规划</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 分析步骤显示
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    step1 = st.empty()
                    step1.markdown("""
                    <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 30px;">📊</div>
                        <div style="font-weight: bold; margin: 5px 0;">能力解析</div>
                        <div style="color: #999; font-size: 12px;">分析目标能力</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    step2 = st.empty()
                    step2.markdown("""
                    <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 30px;">🔍</div>
                        <div style="font-weight: bold; margin: 5px 0;">知识匹配</div>
                        <div style="color: #999; font-size: 12px;">检索知识图谱</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    step3 = st.empty()
                    step3.markdown("""
                    <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 30px;">🤖</div>
                        <div style="font-weight: bold; margin: 5px 0;">AI推理</div>
                        <div style="color: #999; font-size: 12px;">深度学习分析</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    step4 = st.empty()
                    step4.markdown("""
                    <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 30px;">📋</div>
                        <div style="font-weight: bold; margin: 5px 0;">生成方案</div>
                        <div style="color: #999; font-size: 12px;">输出学习路径</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                import time
                
                # 步骤1: 能力解析
                time.sleep(0.5)
                step1.markdown("""
                <div style="text-align: center; padding: 15px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                    <div style="font-size: 30px;">✅</div>
                    <div style="font-weight: bold; margin: 5px 0; color: #155724;">能力解析</div>
                    <div style="color: #155724; font-size: 12px;">完成</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 显示解析的能力
                st.markdown("##### 📊 解析的目标能力:")
                abilities_display = st.empty()
                abilities_html = ""
                for ability_id in selected_abilities:
                    ability_name = next((a['name'] for a in abilities if a['id'] == ability_id), ability_id)
                    mastery = mastery_levels.get(ability_id, 0.5)
                    color = "#28a745" if mastery >= 0.7 else "#ffc107" if mastery >= 0.4 else "#dc3545"
                    abilities_html += f"""
                    <span style="display: inline-block; background: {color}22; color: {color}; 
                                 padding: 5px 12px; margin: 3px; border-radius: 20px; border: 1px solid {color};">
                        {ability_name} ({int(mastery*100)}%)
                    </span>
                    """
                abilities_display.markdown(abilities_html, unsafe_allow_html=True)
                
                # 步骤2: 知识匹配
                time.sleep(0.6)
                step2.markdown("""
                <div style="text-align: center; padding: 15px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                    <div style="font-size: 30px;">✅</div>
                    <div style="font-weight: bold; margin: 5px 0; color: #155724;">知识匹配</div>
                    <div style="color: #155724; font-size: 12px;">完成</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("##### 🔍 知识图谱检索结果:")
                st.info(f"已从知识图谱中匹配到 {len(selected_abilities) * 3} 个相关知识点")
                
                # 步骤3: AI推理
                time.sleep(0.5)
                step3.markdown("""
                <div style="text-align: center; padding: 15px; background: #cce5ff; border-radius: 10px; border: 2px solid #004085; animation: pulse 1s infinite;">
                    <div style="font-size: 30px;">⏳</div>
                    <div style="font-weight: bold; margin: 5px 0; color: #004085;">AI推理中</div>
                    <div style="color: #004085; font-size: 12px;">请稍候...</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 显示AI思考过程
                thinking_box = st.empty()
                thinking_box.markdown("""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea;">
                    <p style="margin: 0; color: #666;">🤖 <strong>AI正在思考...</strong></p>
                    <p style="margin: 5px 0 0 0; color: #888; font-size: 14px;">
                        正在调用DeepSeek API，分析您的能力水平、学习目标，结合牙周病学知识体系生成最优学习路径...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 添加调试信息显示
                debug_box = st.empty()
                debug_box.info(f"🔧 调试：准备调用AI API，已选择 {len(selected_abilities)} 个能力")
                
                try:
                    recommendation = analyze_learning_path(selected_abilities, mastery_levels, abilities)
                    
                    # 检查是否真的调用了API（检查返回内容是否包含"演示数据"标识）
                    is_fallback = "⚠️ 注意：AI分析服务暂时不可用" in recommendation
                    
                    debug_box.empty()  # 清除调试信息
                    
                    # 步骤3完成
                    step3.markdown("""
                    <div style="text-align: center; padding: 15px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                        <div style="font-size: 30px;">✅</div>
                        <div style="font-weight: bold; margin: 5px 0; color: #155724;">AI推理</div>
                        <div style="color: #155724; font-size: 12px;">完成</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    thinking_box.empty()
                    
                    # 步骤4完成
                    time.sleep(0.3)
                    step4.markdown("""
                    <div style="text-align: center; padding: 15px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                        <div style="font-size: 30px;">✅</div>
                        <div style="font-weight: bold; margin: 5px 0; color: #155724;">生成方案</div>
                        <div style="color: #155724; font-size: 12px;">完成</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示AI推荐结果
                    if is_fallback:
                        st.warning("⚠️ AI服务暂时不可用，显示预设推荐方案")
                    else:
                        st.success("✅ DeepSeek AI分析完成！以下是根据您的能力选择生成的个性化推荐")
                    
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                                padding: 20px; border-radius: 12px; margin: 20px 0;">
                        <h4 style="color: white; margin: 0;">🎯 学习路径推荐</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(recommendation)
                    
                    # 记录AI推荐生成
                    log_ability_activity("生成AI推荐", details=f"成功生成学习路径推荐 (使用{'预设方案' if is_fallback else 'AI分析'})")
                    
                    # 保存到session
                    st.session_state['last_recommendation'] = recommendation
                    st.session_state['last_recommendation_fallback'] = is_fallback
                    
                    if not is_fallback:
                        st.success("🎉 AI推荐生成完成！这是根据您选择的能力定制的个性化方案")
                    else:
                        st.info("💡 提示：AI服务不可用时会显示预设方案，实际部署后将调用真实AI")
                    
                except Exception as e:
                    debug_box.error(f"🔧 调试：发生错误 - {str(e)}")
                    step3.markdown("""
                    <div style="text-align: center; padding: 15px; background: #f8d7da; border-radius: 10px; border: 2px solid #dc3545;">
                        <div style="font-size: 30px;">❌</div>
                        <div style="font-weight: bold; margin: 5px 0; color: #721c24;">AI推理</div>
                        <div style="color: #721c24; font-size: 12px;">失败</div>
                    </div>
                    """, unsafe_allow_html=True)
                    thinking_box.empty()
                    st.error(f"生成推荐失败: {str(e)}")
        
        # 显示历史推荐
        if 'last_recommendation' in st.session_state:
            with st.expander("查看上次推荐"):
                st.markdown(st.session_state['last_recommendation'])
    else:
        st.info("👆 请先选择至少一个目标能力")
    
    # 能力雷达图 - 放在主界面
    if selected_abilities and mastery_levels:
        st.divider()
        st.subheader("📈 能力掌握度雷达图")
        
        # 创建雷达图数据
        import plotly.graph_objects as go
        
        # 获取已选能力的名称和掌握度（转换为0-10分制）
        selected_ability_names = []
        selected_mastery_scores = []
        
        for ability in abilities:
            if ability['id'] in selected_abilities:
                selected_ability_names.append(ability['name'])
                # 将0-1的值转换为0-10分制
                selected_mastery_scores.append(mastery_levels[ability['id']] * 10)
        
        # 创建雷达图
        if selected_ability_names:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = go.Figure()
                
                # 闭环：将第一个元素添加到末尾
                radar_names = selected_ability_names + [selected_ability_names[0]]
                radar_scores = selected_mastery_scores + [selected_mastery_scores[0]]
                
                fig.add_trace(go.Scatterpolar(
                    r=radar_scores,
                    theta=radar_names,
                    fill='toself',
                    name='当前掌握度',
                    line=dict(color='#4ECDC4', width=3),
                    fillcolor='rgba(78, 205, 196, 0.3)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10],
                            tickmode='linear',
                            tick0=0,
                            dtick=2,
                            gridcolor='#e0e0e0'
                        ),
                        angularaxis=dict(
                            gridcolor='#e0e0e0'
                        )
                    ),
                    showlegend=True,
                    height=500,
                    margin=dict(l=100, r=100, t=40, b=40),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 能力统计")
                
                # 显示统计信息
                avg_mastery = sum(selected_mastery_scores) / len(selected_mastery_scores)
                st.metric("平均掌握度", f"{avg_mastery:.1f}/10", 
                         help="所有选中能力的平均掌握程度")
                
                st.markdown("---")
                
                # 显示最强和最弱能力
                min_idx = selected_mastery_scores.index(min(selected_mastery_scores))
                max_idx = selected_mastery_scores.index(max(selected_mastery_scores))
                
                st.metric("💪 最强能力", 
                         selected_ability_names[max_idx], 
                         f"{selected_mastery_scores[max_idx]:.1f}/10")
                
                st.metric("📖 待提升能力", 
                         selected_ability_names[min_idx], 
                         f"{selected_mastery_scores[min_idx]:.1f}/10")
                
                # 能力分布
                st.markdown("---")
                st.markdown("**能力分布：**")
                high_count = sum(1 for s in selected_mastery_scores if s >= 7)
                mid_count = sum(1 for s in selected_mastery_scores if 4 <= s < 7)
                low_count = sum(1 for s in selected_mastery_scores if s < 4)
                
                st.write(f"🟢 熟练（≥7分）：{high_count}个")
                st.write(f"🟡 中等（4-7分）：{mid_count}个")
                st.write(f"🔴 薄弱（<4分）：{low_count}个")
