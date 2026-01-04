"""
病例库模块
提供病例浏览、搜索和详情查看功能
"""

import streamlit as st

# 可选导入Elasticsearch（仅本地开发需要）
try:
    from elasticsearch import Elasticsearch
    HAS_ELASTICSEARCH = True
except ImportError:
    HAS_ELASTICSEARCH = False
    Elasticsearch = None

try:
    from config.settings import ELASTICSEARCH_CLOUD_ID, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD
except (ImportError, AttributeError):
    ELASTICSEARCH_CLOUD_ID = None
    ELASTICSEARCH_USERNAME = None
    ELASTICSEARCH_PASSWORD = None

def ensure_list(value, default=None):
    """确保值是列表格式，如果是字符串则分割"""
    if default is None:
        default = []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # 如果是字符串，按换行符分割
        return [line.strip() for line in value.split('\n') if line.strip()]
    return default

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
    """搜索病例（仅本地开发可用，云端返回None）"""
    # 云端部署时跳过Elasticsearch
    if not HAS_ELASTICSEARCH or not ELASTICSEARCH_CLOUD_ID:
        return None
    
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
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 获取病例基本信息
            result = session.run("""
                MATCH (c:yzbx_Case {id: $case_id})
                RETURN c
            """, case_id=case_id)
            
            case = result.single()
            if not case:
                return None
            
            case_data = dict(case['c'])
            
            # 获取关联的知识点
            result = session.run("""
                MATCH (c:yzbx_Case {id: $case_id})-[:RELATES_TO]->(k:yzbx_Knowledge)
                RETURN k.id as id, k.name as name
            """, case_id=case_id)
            
            case_data['knowledge_points'] = [dict(record) for record in result]
        
        return case_data
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_all_sample_cases():
    """获取所有病例数据（带缓存）"""
    # 暂时禁用Elasticsearch，使用本地丰富的示例数据
    # TODO: 后续需要将丰富的数据同步到Elasticsearch
    # try:
    #     cases = search_cases("", None)
    #     if cases:
    #         return cases
    # except:
    #     pass
    
    # 返回示例数据
    return [
        {
            "id": "case1", 
            "title": "慢性牙周炎典型病例", 
            "chief_complaint": "患者因\"刷牙出血反复发作3个月余，近2周加重伴口腔异味\"就诊。自述每日晨起刷牙时牙龈出血明显，牙膏泡沫呈粉红色，漱口后出血可自行停止；进食苹果等硬物时亦可见牙龈出血，伴有明显口臭，影响社交，自觉牙齿有\"变长\"感，咬物略感无力。", 
            "present_illness": """现病史：患者3个月前无明显诱因出现刷牙时牙龈出血，初期仅早晨偶发，未予重视。近2周来出血频率和量均明显增加，每日刷牙必出血，持续时间延长，进食时也易出血。伴有晨起口臭加重，家属也反映能闻到异味。感觉多颗牙齿较前"变长"，牙缝变大，下前牙排列似有轻度移位。咬较硬食物时感牙齿酸软无力。无牙龈自发痛，无明显牙齿松动感，无发热等全身不适。曾自购"云南白药牙膏"使用2周，效果不明显。

既往口腔诊疗史：5年前曾在某诊所洁牙1次，之后未再进行牙周维护。否认正畸治疗史。否认颌面部外伤史。""",
            "symptoms": ["牙龈红肿", "探诊出血", "牙周袋形成4-6mm", "牙槽骨水平吸收", "口腔异味"],
            "diagnosis": "慢性牙周炎（III期B级）",
            "difficulty": "简单",
            "patient_info": {"age": 45, "gender": "男", "occupation": "教师"},
            "medical_history": """【既往史】高血压病史5年，长期规律服用苯磺酸氨氯地平片5mg每日1次，血压控制在130-135/80-85mmHg，未见明显降压药相关牙龈增生。否认糖尿病、冠心病、脑血管病等。否认肝炎、结核等传染病史。否认手术、外伤史。否认输血史。
【过敏史】否认青霉素、磺胺类等药物过敏史。否认食物及接触物过敏史。
【家族史】父亲65岁时因"牙齿松动"拔除多颗牙，具体诊断不详；母亲有高血压病史，牙齿保存尚可。兄弟姐妹口腔情况不详。否认家族遗传病史。
【个人史】吸烟20年，每日10-15支，多次尝试戒烟未成功；偶尔社交饮酒，量不多。睡眠、饮食一般。工作压力中等。""",
            "clinical_manifestation": """口腔检查：全口牙龈色暗红，龈缘圆钝肥厚，质地松软，点彩消失；龈乳头充血肿胀；探诊后普遍出血；可见龈上牙石（++），龈缘处菌斑堆积明显；探诊深度4-6mm，下颌磨牙区最深达6mm；全口菌斑指数（PLI）约65%；探诊出血指数（BOP）约70%阳性；36、46牙I度松动；口腔有异味。""",
            "auxiliary_examination": """【影像学检查】全口曲面体层片示：全口牙槽骨呈水平型吸收，骨吸收量约为根长的1/3-1/2；下颌第一磨牙根分叉区可见低密度影像，提示I度根分叉病变；硬骨板部分不连续，牙周膜间隙增宽；未见明显根尖周病变及埋伏牙。
【实验室检查】（如有）血常规、凝血功能均正常。""",
            "treatment_plan": [
                "【基础治疗阶段】口腔卫生宣教，教授改良Bass刷牙法，每日2次，每次3分钟；推荐使用牙线或牙间隙刷清洁邻面。全口龈上洁治术，超声波洁牙机配合手工洁治器彻底去除龈上牙石及菌斑。分区龈下刮治及根面平整术（SRP），建议分2-4次完成全口治疗，局部麻醉下进行。深牙周袋局部药物治疗，盐酸米诺环素软膏（派丽奥）缓释剂袋内给药。",
                "【再评估阶段】基础治疗完成4-6周后复诊，重新进行全口牙周检查，记录探诊深度、附着水平、出血指数等，评估治疗效果。若残留探诊深度>5mm、骨内袋或根分叉病变未改善者，考虑牙周手术治疗。",
                "【维护治疗阶段】建立终身牙周支持治疗计划，每3个月复诊一次进行SPT，包括菌斑控制评估、专业清洁及强化宣教。强调戒烟的必要性，吸烟严重影响牙周治疗效果及长期预后。监测血压控制情况，与心内科保持沟通。"
            ],
            "treatment_notes": "治疗注意事项：①高血压患者每次就诊前测量血压，血压>180/110mmHg时暂缓操作；②局麻药选择肾上腺素浓度不超过1:100000；③吸烟者应书面告知吸烟对牙周治疗的不良影响；④预约复诊时间充足，避免患者等候时间过长导致焦虑。",
            "key_points": [
                "⚠️ 高血压患者注意事项：治疗前测量血压，控制在160/100mmHg以下方可操作，避免使用高浓度肾上腺素",
                "📋 吸烟与牙周炎：吸烟是牙周炎的重要危险因素，显著降低治疗效果，需强调戒烟",
                "🔄 长期随访：慢性牙周炎需要终身维护治疗，复查间隔不超过3个月",
                "📝 菌斑控制是关键：每次复查记录菌斑指数，目标<20%，评估患者依从性"
            ],
            "diagnosis_analysis": {
                "clinical_exam": {
                    "title": "临床检查发现",
                    "items": [
                        "牙龈状态：全口牙龈色暗红，龈缘圆钝肥厚，质地松软，正常点彩结构消失，龈乳头充血水肿",
                        "探诊检查：全口探诊深度普遍4-6mm，16、26、36、46牙位最深达6mm；探诊出血阳性率约70%",
                        "附着丧失：临床附着丧失约3-4mm，龈退缩不明显，以袋内吸收为主",
                        "牙齿松动：36、46牙I度松动，余牙未见明显松动",
                        "菌斑牙石：龈上牙石（++），龈缘及邻面菌斑堆积明显，菌斑指数约65%",
                        "根分叉病变：下颌第一磨牙探及I度根分叉病变"
                    ]
                },
                "radiographic": {
                    "title": "X线片分析",
                    "items": [
                        "全口曲面断层片显示全口牙槽骨呈水平型吸收为主",
                        "骨吸收量为根长的1/3-1/2，符合中重度骨丧失",
                        "下颌磨牙根分叉区可见低密度透射影，提示I度根分叉病变",
                        "牙周膜间隙轻度增宽，硬骨板部分区域不连续",
                        "未见明显根尖周病变，无牙根外吸收征象"
                    ]
                },
                "differential": {
                    "title": "鉴别诊断",
                    "items": [
                        "与侵袭性牙周炎鉴别：本例发病年龄45岁，病程进展缓慢，破坏程度与菌斑量相符，临床附着丧失与年龄比值在正常范围，符合慢性牙周炎特点",
                        "与牙龈炎鉴别：本例已有明确牙槽骨吸收和临床附着丧失，超越了龈炎范畴，可排除单纯牙龈炎诊断",
                        "与创伤性咬合鉴别：咬合检查未见明显早接触及干扰，磨耗程度与年龄相符，无扇形移位",
                        "与药物性牙龈增生鉴别：虽服用氨氯地平，但临床检查牙龈以炎症水肿为主，非纤维性增生"
                    ]
                },
                "staging": {
                    "title": "分期分级依据（2018年新分类）",
                    "content": """【分期诊断】III期（严重牙周炎）
依据：①附着丧失：最大附着丧失3-4mm；②影像学表现：骨吸收延伸至根中1/3-根尖1/3；③复杂性因素：存在I度根分叉病变，需纳入复杂治疗考量；④失牙：因牙周炎失牙0颗。符合III期诊断标准。

【分级诊断】B级（中度进展）
依据：①直接证据：无5年以上的影像学资料用于纵向对比；②间接证据：骨丧失(mm)/年龄(岁)比值=4/45≈0.09，提示A级，但存在吸烟危险因素（10支/日属中重度吸烟）；③风险因素修正：吸烟使分级由A升至B级。最终诊断为III期B级慢性牙周炎。"""
                }
            }
        },
        {
            "id": "case2", 
            "title": "侵袭性牙周炎病例", 
            "chief_complaint": "患者因\"上前牙逐渐外翻、牙缝变大2周，咬物无力\"就诊。自述2周前偶然照镜子时发现上门牙较前明显外突，且牙齿之间出现缝隙，用舌头顶牙齿感觉有松动。近日咬馒头等软食时上前牙感觉酸软无力，不敢用前牙切断食物。偶有牙龈出血，无明显疼痛。", 
            "present_illness": """现病史：患者2周前无意中发现上前牙"往外翘"，牙间隙逐渐增大，前牙咬合关系改变，闭口时上下牙接触与以前不同。同期感觉上前牙松动，用舌头舔压时有晃动感。进食软食时上前牙酸软无力，不敢咬东西。刷牙偶有牙龈出血，量不多。无牙龈明显红肿疼痛，无自发性出血。未曾就诊治疗。

患者初中时（约14岁）曾因"牙龈出血"在当地诊所洁牙2次，医生曾说"牙周有问题"，建议定期检查，但之后未再复诊。近2年感觉多颗后牙咬物略感无力，咀嚼效率下降，但因无疼痛未予重视。

月经生育史：月经规律，14岁初潮，周期28-30天，经量中等，无痛经。未婚未育。""",
            "symptoms": ["前牙扇形移位", "深牙周袋>7mm", "快速骨吸收", "探诊出血", "牙齿松动"],
            "diagnosis": "侵袭性牙周炎（IV期C级，广泛型）",
            "difficulty": "困难",
            "patient_info": {"age": 28, "gender": "女", "occupation": "公司职员"},
            "medical_history": """【既往史】平素体健，否认高血压、糖尿病、心脏病、血液系统疾病等慢性病史。否认肝炎、结核等传染病史。否认手术史及住院史。否认外伤史。否认输血史。
【过敏史】青霉素过敏（既往使用后全身皮疹），否认其他药物过敏。否认食物及接触物过敏史。
【家族史】母亲40岁左右时因"牙齿松动"拔除多颗牙齿，50岁时上下牙全部脱落，现佩戴全口义齿；外祖母据说也是"年纪不大就掉光了牙"。父亲现年55岁，牙齿保存尚可。无其他家族遗传病史。
【个人史】不吸烟，偶尔聚会饮酒。睡眠尚可，无明显精神压力。饮食习惯良好，体型适中。""",
            "clinical_manifestation": """口腔检查：11、21牙唇向扇形移位，牙间隙明显增大约2-3mm；上颌切牙区牙龈退缩，根面部分暴露；全口牙龈轻度红肿，但菌斑附着量与组织破坏程度明显不成比例；探诊深度：11、21、16、26、36、46牙位达8-10mm，余牙3-4mm；11、21牙II-III度松动，16、26、36、46牙I-II度松动；探诊出血阳性；咬合检查示前牙区咬合关系改变。""",
            "auxiliary_examination": """【影像学检查】全口曲面体层片及根尖片示：第一磨牙区牙槽骨呈典型"弧形"或"壶底状"垂直型吸收，切牙区骨吸收达根长1/2-2/3；呈现典型"门牙-磨牙型"分布特点——破坏主要集中于第一恒磨牙和切牙区；磨牙根分叉病变明显，达II-III度；余牙骨吸收程度较轻。
【实验室检查】血常规正常，排除血液系统疾病；空腹血糖5.2mmol/L，正常。建议完善免疫功能及遗传易感性相关检测。""",
            "treatment_plan": [
                "【急症处理与全身辅助治疗】松动前牙暂时性固定，光固化树脂夹板固定11-21牙稳定咬合功能。全身抗生素辅助治疗：因青霉素过敏，选用阿奇霉素500mg首剂，后250mg/日×4天，联合甲硝唑400mg每日3次共7天，针对侵袭性牙周炎特征性致病菌（伴放线放线杆菌Aa）。",
                "【系统基础治疗】全口龈下刮治及根面平整术，分4次完成，局部麻醉下操作，重点处理深牙周袋区域。深袋辅助药物治疗，盐酸米诺环素软膏局部缓释给药。强化口腔卫生指导，强调牙间隙清洁，推荐使用牙间隙刷。",
                "【手术治疗阶段】基础治疗后6-8周再评估，对残留深袋、骨下袋行牙周翻瓣术，条件适合者考虑引导组织再生术（GTR）或植骨术，争取部分骨再生。16、26、36、46牙根分叉病变行隧道成形术或截根术评估。",
                "【长期维护与监测】建立严密随访计划，每2-3个月复查一次，周期短于慢性牙周炎患者。考虑建议患者直系亲属进行牙周筛查（遗传易感性）。可建议完善基因检测和免疫功能评估，用于预后判断。"
            ],
            "treatment_notes": "治疗注意事项：①青霉素过敏，严禁使用阿莫西林，选择大环内酯类替代；②年轻女性患者需关注心理状态，前牙美观问题可能造成心理负担，必要时转诊心理咨询；③家族史阳性，建议家族成员进行牙周筛查；④抗生素使用期间避免饮酒。",
            "key_points": [
                "🧬 家族史高度阳性：母系家族成员有早期失牙史，高度提示遗传易感性，是诊断侵袭性牙周炎的重要线索",
                "⚠️ 年轻患者严重破坏：28岁即出现严重骨吸收和牙齿松动，与年龄严重不符，需高度警惕侵袭性牙周炎",
                "💊 抗生素选择：青霉素过敏患者不能使用阿莫西林，大环内酯类（阿奇霉素）是有效替代",
                "🔬 菌斑与破坏不成比例：口腔卫生状况尚可但组织破坏严重，是侵袭性牙周炎的典型特征",
                "📅 密切随访：侵袭性牙周炎复查间隔应为2-3个月，需终身严密监测"
            ],
            "diagnosis_analysis": {
                "clinical_exam": {
                    "title": "临床检查发现",
                    "items": [
                        "前牙移位：11、21牙明显唇向扇形移位，牙间隙增大2-3mm，影响美观及咬合功能",
                        "特征性分布：第一磨牙(16、26、36、46)和切牙区破坏最严重，呈典型'门牙-磨牙型'",
                        "深牙周袋：第一磨牙及切牙区探诊深度达8-10mm，远超一般慢性牙周炎",
                        "菌斑-破坏不符：菌斑附着量较少（菌斑指数约30%），但组织破坏程度严重，明显不成比例",
                        "牙齿松动：11、21牙II-III度松动，16、26、36、46牙I-II度松动，功能受损明显",
                        "年龄因素：患者仅28岁，严重程度与年龄明显不匹配"
                    ]
                },
                "radiographic": {
                    "title": "X线片分析",
                    "items": [
                        "第一磨牙呈典型'弧形'或'壶底状'垂直骨吸收，是侵袭性牙周炎特征性表现",
                        "切牙区牙槽骨吸收严重，达根长的1/2-2/3",
                        "破坏呈'门牙-磨牙型'特征分布，非全口均匀分布",
                        "磨牙根分叉区透射影明显，根分叉病变达II-III度",
                        "余牙骨吸收程度相对较轻，对比明显"
                    ]
                },
                "differential": {
                    "title": "鉴别诊断",
                    "items": [
                        "与慢性牙周炎鉴别：本例发病年龄轻（28岁），进展迅速，破坏严重程度与菌斑量不成比例，分布呈门牙-磨牙型特征，家族史阳性，均符合侵袭性牙周炎而非慢性牙周炎",
                        "排除血液系统疾病：需完善血常规检查排除白血病、再生障碍性贫血等导致的牙周组织破坏，本例血常规正常",
                        "排除糖尿病：需排除未诊断的糖尿病导致的严重牙周破坏，本例空腹血糖正常",
                        "家族史支持：母亲早期多牙脱落、外祖母也有类似病史，高度支持遗传易感性相关的侵袭性牙周炎诊断"
                    ]
                },
                "staging": {
                    "title": "分期分级依据（2018年新分类）",
                    "content": """【分期诊断】IV期（晚期牙周炎伴咬合功能障碍）
依据：①附着丧失≥5mm；②骨吸收延伸至根中1/3至根尖1/3；③存在继发表现：前牙扇形移位、咬合关系改变、咀嚼功能明显受损；④根分叉病变达II-III度；⑤符合IV期的复杂治疗需求。

【分级诊断】C级（快速进展）
依据：①直接证据：病史提示1-2年内有明显进展，初中时即有牙周问题；②间接证据：年轻患者（28岁）即出现与其年龄严重不符的广泛破坏，骨丧失/年龄比值远超1.0；③分布特征：符合原"侵袭性牙周炎"的门牙-磨牙型分布特点；④危险因素：无吸烟等传统危险因素，但有明确家族史。

【诊断转换说明】按2018年新分类，原"侵袭性牙周炎"已纳入牙周炎的分期分级系统，诊断为IV期C级牙周炎（原侵袭性牙周炎，广泛型）。"""
                }
            }
        },
        {
            "id": "case3", 
            "title": "牙周-牙髓联合病变", 
            "chief_complaint": """患者因"右下后牙持续性疼痛1周，牙龈反复起脓包3天"就诊。自述1周前右下后牙开始出现持续性隐痛，夜间尤其明显，严重时影响睡眠。疼痛呈钝痛，无明显冷热刺激痛，咬合时略有不适。3天前右下后牙牙龈侧面出现一黄白色"脓包"，挤压后有少量脓液流出，排脓后疼痛稍缓解，但次日"脓包"再次出现。""", 
            "present_illness": """现病史：患者1周前无明显诱因出现右下后牙区（疑为46牙）持续性隐痛，呈钝痛，无明显阵发性加重，但夜间平卧后疼痛感加重，曾影响睡眠。冷热水漱口无明显刺激痛或刺激痛缓解，咬合时该牙有"浮起感"和不适。3天前发现该牙牙龈颊侧近根尖处出现一个约黄豆大小的黄白色"脓包"，稍有触痛，用手挤压可有少量黄白色脓液流出，流脓后疼痛减轻。但次日"脓包"再次出现，反复如此。曾自服"阿莫西林"3天，效果不明显。

患者回忆该牙约3-4年前因龋坏在当地诊所行大面积充填治疗，使用银汞合金充填。之后2年偶有咬物不适，但可忍受，未予处理。半年前开始发现该牙牙龈处反复"起脓包"，约2-3个月发作一次，每次挤脓后自行好转，但始终未根治。本次发作疼痛较前明显，故来就诊。

血糖情况：患者近期在社区医院体检发现血糖偏高，空腹血糖8.5-9.2mmol/L，餐后2小时血糖12-14mmol/L，目前服药调整中。""",
            "symptoms": ["牙齿叩痛(+)", "牙龈窦道", "深牙周袋达根尖", "根尖暗影", "牙齿松动"],
            "diagnosis": "牙周-牙髓联合病变（真性联合病变）",
            "difficulty": "困难",
            "patient_info": {"age": 52, "gender": "男", "occupation": "工程师"},
            "medical_history": """【既往史】2型糖尿病确诊8年，目前口服二甲双胍850mg每日2次联合格列美脲2mg每日1次，血糖控制欠佳（空腹8.5-9.2mmol/L，餐后2h 12-14mmol/L），近期正在调整方案。否认高血压、冠心病、脑血管病等。否认肝炎、结核等传染病史。4年前曾行阑尾切除术，恢复好。否认其他手术史。
【过敏史】否认青霉素、磺胺类等药物过敏史。否认食物及接触物过敏史。
【家族史】父母均有2型糖尿病病史。否认家族遗传性疾病。
【个人史】不吸烟，偶尔应酬饮酒。近1年工作压力较大，饮食作息不规律，体重较前增加约5kg。睡眠质量一般。""",
            "clinical_manifestation": """口腔检查：46牙冠可见大面积银汞合金充填体，充填体边缘密合性尚可；叩诊（++）不适明显，冷热测无反应，牙髓电活力测试无反应（提示牙髓坏死）；颊侧龈粘膜近根尖处可见一窦道口，轻压有少量脓性分泌物溢出，窦道探针探查可通向根尖区；46牙颊侧探诊，牙周袋从冠方延伸至根尖部，最深达12mm，形成连续性通道；牙齿松动II度；邻牙未见明显异常。""",
            "auxiliary_examination": """【影像学检查】46牙根尖片及CBCT示：46牙远中根根尖区可见椭圆形低密度透射影，直径约5mm，边界尚清；近中骨吸收从冠方延伸至根尖区域，形成典型"J"形连续透射影像，牙周-根尖病变相互交通；根分叉区亦可见透射影，提示II度根分叉病变；牙周膜间隙明显增宽。
【实验室检查】血常规大致正常；空腹血糖8.8mmol/L，糖化血红蛋白（HbA1c）8.2%，提示近3个月血糖控制欠佳。""",
            "treatment_plan": [
                "【急症处理与感染控制】开髓引流：局麻下行46牙开髓术，打开髓腔，解除髓腔压力，建立冠方引流通道。根管预备：完成根管预备，彻底清除坏死牙髓组织，大量冲洗（次氯酸钠+EDTA），根管内封氢氧化钙糊剂2周。疼痛管理：必要时口服布洛芬400mg每日3次。血糖控制：与内分泌科沟通，建议调整降糖方案，目标空腹血糖<7.0mmol/L。",
                "【根管治疗完成】复诊观察窦道是否闭合，若闭合良好则完成根管充填（热牙胶垂直加压技术）。冠部严密封闭，临时冠修复，观察1-2个月。定期复查根尖愈合情况。",
                "【牙周状态再评估】根管治疗完成后2-3个月复查，评估牙周组织愈合情况，重新探诊记录牙周袋深度变化。若牙周袋持续较深（>5mm），待血糖控制稳定后（空腹<7.0mmol/L、HbA1c<7%）考虑行牙周翻瓣术联合植骨术。根分叉病变的处理：评估是否行隧道成形术或截根术。",
                "【修复与长期维护】牙周稳定后行全冠修复保护患牙，选择高强度材料。每3个月复查牙周及根尖状态，持续监测。同步监测血糖控制情况，强调代谢控制对牙周愈合的重要性。与内分泌科保持沟通协作。"
            ],
            "treatment_notes": "治疗注意事项：①糖尿病患者感染控制较差，血糖控制欠佳时暂缓有创操作，待空腹血糖<7.0mmol/L后进行；②手术当日正常进食和服用降糖药，术前监测血糖防止低血糖；③围术期可预防性使用抗生素；④糖尿病患者创口愈合延迟，术后严密随访；⑤多学科协作，与内分泌科医师保持沟通。",
            "key_points": [
                "🔍 鉴别原发病灶：真性联合病变需判断病变来源，本例牙髓坏死（活力测试阴性）合并牙周破坏（深袋达根尖），两个途径同时存在并相交通",
                "🩸 糖尿病影响治疗：高血糖状态影响愈合和感染控制能力，需与内分泌科协同管理，控制血糖是治疗成功的前提",
                "👥 多学科协作：本病例涉及牙体牙髓科、牙周科、修复科及内分泌科，需多专业协作制定治疗方案",
                "📅 序贯治疗原则：先控制急性感染（开髓引流、抗感染），再行根管治疗，最后评估是否需要牙周手术",
                "⏰ 预后评估：真性联合病变因同时存在两种病变来源，预后较单纯牙髓病或牙周病差，需充分知情"
            ],
            "diagnosis_analysis": {
                "clinical_exam": {
                    "title": "临床检查发现",
                    "items": [
                        "牙冠情况：46牙可见大面积银汞充填体，提示既往深龋病史，充填体边缘密合性尚可",
                        "牙髓活力：叩诊（++），冷热测无反应，电活力测试无反应，综合判断牙髓已坏死",
                        "窦道检查：颊侧近根尖处可见窦道口，探针可通向根尖区，提示根尖周感染引流通道形成",
                        "牙周探诊：颊侧牙周袋从冠方延伸至根尖区域，最深达12mm，形成连续通道，牙周与根尖病变相交通",
                        "牙齿松动：II度松动，提示牙周支持组织大量丧失",
                        "根分叉探查：可探及根分叉区病变"
                    ]
                },
                "radiographic": {
                    "title": "X线片分析",
                    "items": [
                        "根尖区可见直径约5mm的类圆形低密度透射影，边界尚清，提示慢性根尖周炎",
                        "近中骨吸收从冠方沿牙周膜间隙延伸至根尖区，形成典型J形透射影",
                        "牙周-根尖病变通过共同通道连通，符合真性联合病变影像学特征",
                        "根分叉区透射影像提示II度根分叉病变",
                        "牙周膜间隙弥漫性增宽"
                    ]
                },
                "differential": {
                    "title": "鉴别诊断",
                    "items": [
                        "原发性牙髓病变继发牙周病变：牙髓坏死在先（深龋史），根尖感染后沿根面向冠方蔓延，形成逆行性牙周袋；牙髓活力测试阴性、根尖病变支持此途径",
                        "原发性牙周病变继发牙髓病变：牙周袋进展至根尖或侧支根管，感染逆行进入髓腔导致牙髓坏死；深牙周袋支持此途径",
                        "真性联合病变（最终诊断）：本例既有明确的牙髓源性（深龋、活力丧失、根尖病变），又有牙周源性（深牙周袋从冠方延伸），两者相互交通形成联合病变",
                        "糖尿病因素：糖尿病患者感染风险增高、愈合能力下降，是本例病情反复的重要因素"
                    ]
                },
                "staging": {
                    "title": "联合病变分类与预后分析",
                    "content": """【联合病变分类】真性联合病变（True Combined Lesion）
本例符合真性联合病变诊断：①明确的牙髓坏死证据（活力测试阴性、根尖病变）提示存在牙髓源性感染；②深牙周袋从冠方延伸至根尖、根分叉病变提示存在原发性牙周破坏；③两者通过根尖区或侧支根管相交通，形成典型"J"形影像。

【预后评估】中等偏差
预后影响因素：①糖尿病控制欠佳影响愈合；②存在根分叉病变增加治疗难度；③真性联合病变预后较单纯病变差；④需评估患牙在全口中的战略价值决定是否保留。若经规范治疗（血糖控制+根管治疗+必要的牙周手术）病变仍无法控制，需考虑拔除。"""
                }
            }
        },
        {
            "id": "case4", 
            "title": "药物性牙龈增生", 
            "chief_complaint": "患者因\"服用降压药后牙龈逐渐增大1年余，影响美观和进食\"就诊。自述约1年前开始发现牙龈逐渐增大，最初仅上前牙区龈乳头稍显饱满，未在意。近半年增生明显加重，牙龈已覆盖部分牙面，进食时经常咬到牙龈导致出血和疼痛，且牙缝处食物嵌塞难以清理，影响美观，社交时感到尴尬。", 
            "present_illness": """现病史：患者约1年前无明显诱因开始出现牙龈增大，起初仅上颌前牙区龈乳头较前饱满，色粉红，质地略韧，未予重视。之后增生逐渐加重并波及全口，尤以上下前牙区和磨牙区龈乳头处明显。近半年来牙龈已覆盖牙冠约1/3-1/2，部分区域接近牙冠切缘。进食时常咬到增生的牙龈导致出血和疼痛，牙缝处食物嵌塞难以清理。因牙龈增大影响美观，患者社交时感到不自信。

询问病史，患者10余年前确诊原发性高血压，最初服用卡托普利，后因干咳副作用于5年前改为硝苯地平缓释片（拜新同）30mg每日1次，血压控制在130-140/80-90mmHg。患者回忆牙龈增大似乎是在更换降压药后约6个月开始出现，之后逐渐加重。

口腔卫生情况：既往每日刷牙1次，约2分钟。牙龈增大后因刷牙容易出血而不敢用力，刷牙时间缩短，清洁效果更差。""",
            "symptoms": ["牙龈弥漫性增生", "质地较韧", "覆盖牙面1/3-1/2", "菌斑堆积明显", "假性牙周袋"],
            "diagnosis": "药物性牙龈增生（硝苯地平相关）",
            "difficulty": "中等",
            "patient_info": {"age": 58, "gender": "女", "occupation": "退休教师"},
            "medical_history": """【既往史】原发性高血压病史10余年，目前服用硝苯地平缓释片（拜新同）30mg每日1次，血压控制在130-140/80-90mmHg。否认糖尿病、冠心病、脑血管疾病等。否认癫痫病史（排除苯妥英钠服用史）。否认器官移植史（排除环孢素服用史）。否认肝炎、结核等传染病史。5年前因子宫肌瘤行子宫切除术，恢复好。
【过敏史】否认青霉素、磺胺类等药物过敏史。否认食物过敏史。
【家族史】父亲有高血压病史，母亲有2型糖尿病病史。否认家族遗传病史。
【个人史】不吸烟不饮酒。已绝经5年，未行激素替代治疗。睡眠饮食一般。退休后生活规律，无明显精神压力。""",
            "clinical_manifestation": """口腔检查：全口牙龈弥漫性增生，上下颌前牙区及磨牙区尤为明显；龈乳头圆钝肥大，相邻牙的龈乳头融合，覆盖牙冠约1/3-1/2；增生牙龈颜色淡粉红，质地较韧实，表面可见浅分叶；龈缘及牙间隙处菌斑堆积明显；探诊深度4-6mm，但主要为假性牙周袋（龈缘向冠方增生所致）；探诊出血率约50%；牙齿无明显松动。""",
            "auxiliary_examination": """【影像学检查】全口曲面体层片示：全口牙槽骨未见明显吸收，牙槽嵴顶位于釉牙骨质界下方1-2mm正常范围；硬骨板连续，牙周膜间隙正常；无根尖周病变征象。影像学检查提示为单纯软组织增生，无骨组织破坏（真性牙周袋）。
【实验室检查】血常规正常，排除白血病等血液系统疾病导致的牙龈肿大。空腹血糖正常。""",
            "treatment_plan": [
                "【病因控制与内科协调】首先与心内科/全科医师沟通，说明硝苯地平与牙龈增生的相关性，建议尝试更换其他类型降压药物。可选替代方案：ACEI类（贝那普利、培哚普利，注意干咳副作用）、ARB类（缬沙坦、厄贝沙坦）、β受体阻滞剂（美托洛尔）等，均不引起牙龈增生。换药后需密切监测血压变化。",
                "【口腔卫生宣教与基础治疗】口腔卫生强化指导，教授改良Bass刷牙法，强调龈缘和龈乳头区清洁，推荐使用软毛牙刷。配合牙间隙刷或牙线清理增生牙龈间隙内菌斑。全口龈上洁治术，彻底去除菌斑牙石。局部使用0.12%氯己定含漱液辅助菌斑控制。换药后观察2-3个月，评估牙龈增生消退情况。",
                "【手术治疗（如有需要）】若换药后2-3个月增生未消退或消退不完全，需行牙龈切除术。手术方式：传统手术刀或电刀切除增生牙龈，恢复正常牙龈外形；条件允许可使用激光辅助，减少出血。术后牙周塞治剂保护创面约1周，术后1周拆除观察愈合。",
                "【长期维护与复发预防】术后每月复查，监测有无复发。若患者无法换药，需书面告知复发风险较高，需定期维护治疗。长期保持良好口腔卫生是预防复发的关键。每3-6个月进行专业清洁，定期随访。"
            ],
            "treatment_notes": "治疗注意事项：①换药需心内科医师配合，不可擅自停用降压药；②换药后需监测血压至少2-4周确保平稳；③手术时机选择在换药观察期后进行；④术前需排除凝血功能异常；⑤充分告知患者：若无法换药则术后复发可能性较大。",
            "key_points": [
                "💊 详细药物史询问：钙通道阻滞剂（硝苯地平、氨氯地平等）、苯妥英钠（抗癫痫药）、环孢素（免疫抑制剂）是三类常见致病药物，需仔细询问服药史",
                "👨‍⚕️ 多学科协作：需与心内科/全科医师沟通换药可能性，不可擅自停药",
                "🧹 菌斑控制是关键：良好口腔卫生可减轻增生程度、延缓进展，是治疗的重要组成部分",
                "🔄 复发风险评估：不换药则术后复发率高（约40-50%），需充分告知并做好长期维护计划",
                "⏳ 换药后观察期：更换药物后一般需2-6个月观察牙龈消退情况，轻症可能不需手术"
            ],
            "diagnosis_analysis": {
                "clinical_exam": {
                    "title": "临床检查发现",
                    "items": [
                        "增生范围：全口牙龈弥漫性增生，上下颌前牙区及磨牙区龈乳头处最明显",
                        "增生形态：龈乳头圆钝肥大，相邻牙龈乳头可相互融合，覆盖牙冠1/3-1/2",
                        "组织质地：增生牙龈颜色淡粉红，质地较韧实，表面可见浅分叶，非炎症性水肿",
                        "菌斑情况：龈缘及增生牙龈间隙处菌斑堆积明显（菌斑指数约60%），加重增生",
                        "探诊检查：探诊深度4-6mm，但为假性牙周袋（龈缘向冠方增生所致，并非附着丧失）",
                        "牙齿情况：牙齿无明显松动，咬合关系正常"
                    ]
                },
                "radiographic": {
                    "title": "X线片分析",
                    "items": [
                        "全口曲面断层片示牙槽骨未见明显吸收，牙槽嵴顶位于正常位置",
                        "硬骨板连续完整，牙周膜间隙正常，无骨下袋形成",
                        "影像学表现与临床假性牙周袋相符——单纯软组织增生，非真性牙周破坏",
                        "无根尖周病变及其他牙源性病变",
                        "影像学检查有助于鉴别药物性牙龈增生与伴骨吸收的牙周炎"
                    ]
                },
                "differential": {
                    "title": "鉴别诊断",
                    "items": [
                        "与遗传性牙龈纤维瘤病鉴别：本例有明确的硝苯地平用药史，牙龈增大在换药后出现，且无家族史，可排除遗传性牙龈纤维瘤病",
                        "与白血病性牙龈增生鉴别：白血病时牙龈肿大多较松软、易出血、常伴紫红色，血常规可见白细胞明显异常；本例牙龈质韧、色淡粉、血常规正常，可排除",
                        "与慢性牙周炎鉴别：慢性牙周炎有真性牙周袋（附着丧失）和牙槽骨吸收；本例为假性牙周袋，X线无骨吸收，为单纯软组织增生",
                        "硝苯地平相关性确认：硝苯地平属二氢吡啶类钙通道阻滞剂，是常见的致牙龈增生药物，发生率约20-30%，症状出现与用药时间相符"
                    ]
                },
                "staging": {
                    "title": "发病机制与分级评估",
                    "content": """【发病机制】
钙通道阻滞剂（硝苯地平、氨氯地平等）导致牙龈增生的机制：①抑制成纤维细胞内钙离子通道，影响细胞代谢；②导致胶原酶活性降低，胶原降解减少；③同时刺激成纤维细胞增殖，导致胶原过度沉积；④菌斑是重要的协同因素——牙龈炎症可促进增生，良好口腔卫生可减轻增生程度。

【严重程度分级】中度
依据：①牙龈覆盖牙冠约1/3-1/2（轻度<1/3，中度1/3-2/3，重度>2/3）；②影响美观和功能；③需考虑手术治疗。

【预后评估】若能换药且加强口腔卫生，预后较好；若无法换药，术后复发风险高，需终身维护。"""
                }
            }
        },
        {
            "id": "case5", 
            "title": "坏死性溃疡性牙龈炎", 
            "chief_complaint": "患者因\"牙龈剧烈疼痛3天，伴自发性出血和严重口臭\"急诊就诊。自述3天前突然出现牙龈剧烈疼痛，起初仅上颌前牙区，很快蔓延至全口。疼痛呈持续性，进食和刷牙时明显加重，目前几乎无法正常刷牙和进食。牙龈有自发性出血，枕头上可见血迹。口腔内有明显腐臭味，自己和周围人都能闻到，严重影响社交。", 
            "present_illness": """现病史：患者3天前突然出现牙龈剧烈疼痛，最初仅累及上颌前牙区龈乳头，表现为尖锐刺痛，触之更甚。1天内疼痛迅速蔓延至全口多个区域，呈持续性，进食时明显加重，无法咀嚼，仅能进食流质。刷牙时疼痛剧烈，已基本放弃刷牙。牙龈有自发性出血，夜间枕头上可见血迹，白天说话时也会有血丝。口腔内有极其明显的腐臭味，说话时周围人可闻到，患者因此不敢与人近距离交流。

全身症状：感觉低热、畏寒（自测腋温37.8℃），颌下可触及肿大淋巴结，有压痛，全身乏力、食欲下降。

诱因分析：患者是大学四年级学生，近2周正在全力准备考研考试，每日学习15-16小时，睡眠仅4-5小时，饮食极不规律以外卖和方便食品为主。平时有吸烟习惯（约15支/日），近期因压力增加至20支/日以上。精神高度紧张，自觉免疫力下降。

口腔卫生情况：平时刷牙不规律，约每日1次或隔日1次，近2周因忙于复习几乎没有刷牙。""",
            "symptoms": ["龈乳头坏死", "灰白色假膜", "自发性出血", "剧烈疼痛", "口腔恶臭"],
            "diagnosis": "坏死性溃疡性牙龈炎（NUG）",
            "difficulty": "中等",
            "patient_info": {"age": 23, "gender": "男", "occupation": "大学生"},
            "medical_history": """【既往史】平素体健，否认高血压、糖尿病、心脏病、血液系统疾病等慢性病史。否认肝炎、结核等传染病史。否认HIV检测史。否认手术、外伤及住院史。
【过敏史】否认青霉素、磺胺类等药物过敏史。否认食物过敏史。
【家族史】父母体健。否认家族遗传病史。
【个人史】吸烟史5年，平时15支/日，近期增加至20支/日以上。偶尔饮酒。否认吸毒史及不安全性行为史（评估HIV感染风险）。近2周严重熬夜（每日睡眠4-5小时），精神压力极大，饮食不规律。""",
            "clinical_manifestation": """口腔检查：上下颌多处龈乳头顶端坏死，呈典型"火山口状"或"虫蚀状"凹陷缺损；坏死区表面覆盖灰白色或灰黄色坏死假膜，边界较清楚；假膜擦除后基底呈鲜红色、糜烂、极易出血；触及牙龈引起剧烈疼痛，患者拒绝检查；探诊因疼痛无法完成，可见龈缘处菌斑堆积明显；口腔内有强烈腐臭味（特征性"坏死臭"）；颌下淋巴结肿大、压痛。体温37.8℃。""",
            "auxiliary_examination": """【影像学检查】急性期一般不必进行X线检查。若反复发作病史，全口曲面断层片可能显示龈乳头间骨吸收，牙槽嵴顶呈"截平状"或"凹陷状"改变。本例为首次发作，未行影像学检查。
【实验室检查】血常规：白细胞计数轻度升高（11.2×10^9/L），中性粒细胞比例偏高；血红蛋白、血小板正常。C反应蛋白轻度升高。建议完善HIV抗体筛查（告知患者后）。""",
            "treatment_plan": [
                "【急症处理（首诊）】局部清创：用棉签蘸3%过氧化氢溶液轻柔擦拭去除表面坏死组织和假膜，注意动作轻柔避免加重疼痛。0.12%氯己定溶液局部冲洗。患者带回：甲硝唑含漱液（0.5%）每日含漱3-4次。全身抗生素：甲硝唑片400mg每日3次口服，疗程5-7天（针对厌氧菌混合感染）。疼痛管理：布洛芬400mg必要时服用。",
                "【72小时后复诊】评估急性症状缓解情况，通常治疗24-48小时后疼痛明显减轻。若症状缓解，可轻柔进行龈上洁治，去除菌斑牙石。继续氯己定含漱控制菌斑。指导患者恢复刷牙，使用极软毛牙刷轻柔刷洗。",
                "【1-2周后随访】完善龈上洁治。口腔卫生指导：改良Bass刷牙法培训。评估龈乳头恢复情况，告知可能遗留龈乳头缺失（黑三角），影响美观。若龈乳头缺损严重，后期可考虑龈乳头再生术或修复方法改善美观。",
                "【生活方式指导与病因控制】强调戒烟的紧迫性：吸烟是NUG发生的重要诱因，继续吸烟会增加复发风险。睡眠和饮食调整：规律作息，每日睡眠7-8小时，均衡营养。压力管理：建议心理疏导，合理安排学习时间。HIV筛查：向患者说明NUG可能与免疫功能相关，建议进行HIV抗体检测（知情同意后）。每3个月复查，预防复发。"
            ],
            "treatment_notes": "治疗注意事项：①急性期清创操作需轻柔，避免过度刺激造成疼痛和出血加重；②甲硝唑服药期间禁止饮酒（双硫仑样反应）；③首诊时避免进行龈下操作；④告知患者24-48小时症状应有改善，若无改善需复诊排除其他疾病；⑤关注患者心理状态，考研压力大需给予人文关怀。",
            "key_points": [
                "🚨 急性发病特征：发病急骤，进展迅速，疼痛剧烈，是牙周病中少数引起明显疼痛的疾病",
                "🔬 病原学特征：梭形杆菌（Fusobacterium）与螺旋体（Treponema）混合感染，属于机会性感染，发生在宿主抵抗力下降时",
                "⚠️ 危险因素识别：精神压力、严重睡眠不足、吸烟、营养不良、免疫抑制等因素共同作用",
                "🩺 HIV筛查建议：NUG可能是HIV感染的首发口腔表现，对高危人群或反复发作者应建议HIV检测",
                "🚭 戒烟至关重要：吸烟既是诱发因素也是复发危险因素，需在治疗中反复强调戒烟",
                "📋 远期后遗症：龈乳头坏死后可能永久性缺失，遗留『黑三角』影响美观，需提前告知患者"
            ],
            "diagnosis_analysis": {
                "clinical_exam": {
                    "title": "临床检查发现",
                    "items": [
                        "龈乳头坏死：多处龈乳头顶端坏死缺损，呈典型『火山口状』或『虫蚀状』凹陷，是NUG最具特征性的表现",
                        "灰白色假膜：坏死区表面覆盖灰白色或灰黄色坏死膜，由坏死组织、纤维素、细菌构成，边界较清",
                        "易出血特征：假膜擦除后基底面鲜红、糜烂、极易出血",
                        "剧烈疼痛：触碰牙龈即引起剧痛，患者常因疼痛拒绝口腔检查，是NUG区别于其他牙周病的重要特点",
                        "特征性口臭：口腔有极其强烈的腐臭味（『坏死臭』），是厌氧菌感染和组织坏死的典型表现",
                        "全身症状：可伴低热、乏力、颌下淋巴结肿大压痛等"
                    ]
                },
                "radiographic": {
                    "title": "X线片分析",
                    "items": [
                        "急性期X线片一般无明显特征性改变，不必急于拍片",
                        "反复发作者可见龈乳头间区牙槽骨吸收",
                        "牙槽嵴顶呈『截平状』或『凹陷状』，而非正常的尖锐外形",
                        "本例为首次发作，影像学检查非必需，待急性期控制后再评估"
                    ]
                },
                "differential": {
                    "title": "鉴别诊断",
                    "items": [
                        "与急性疱疹性龈口炎鉴别：疱疹性龈口炎有水疱、溃疡病史，主要累及附着龈和口腔粘膜，龈乳头非主要受累部位；NUG特征性累及龈乳头顶端，形成坏死凹陷",
                        "与急性白血病鉴别：白血病性牙龈病变多为弥漫性肿大、质软、紫红色、易出血，常伴贫血、出血倾向等全身症状；血常规可明确诊断。本例血常规仅轻度白细胞升高，可排除",
                        "与HIV相关牙周病鉴别：NUG可为HIV感染的首发口腔表现，尤其反复发作者应高度警惕；建议HIV筛查",
                        "与坏死性溃疡性牙周炎（NUP）鉴别：NUG限于牙龈，NUP进展至牙周组织伴骨吸收；本例尚无骨吸收证据，诊断为NUG"
                    ]
                },
                "staging": {
                    "title": "病因分析与预后评估",
                    "content": """【病因学分析】
坏死性溃疡性牙龈炎（NUG）是一种机会性感染，由梭形杆菌和螺旋体共同致病。致病条件需宿主抵抗力下降：
• 本例诱发因素：①考研压力（精神高度紧张）；②严重睡眠不足（每日4-5小时）；③饮食不规律、营养不良；④大量吸烟（近期增至20支/日以上）；⑤口腔卫生极差（近2周几乎未刷牙）
• 这些因素共同导致局部和全身抵抗力下降，口腔内潜伏的致病菌趁机大量繁殖，引发急性坏死性感染。

【预后评估】
• 短期预后：经规范治疗24-48小时后疼痛即可明显缓解，1-2周急性期控制；
• 远期预后：龈乳头坏死区可能永久性缺失形成"黑三角"，影响美观；
• 复发风险：若不纠正诱发因素（尤其戒烟、改善作息），复发可能性大；
• 进展风险：若不及时治疗可进展为坏死性溃疡性牙周炎（NUP），造成骨组织破坏。"""
                }
            }
        }
    ]

def render_case_library():
    """渲染病例库页面"""
    st.title("📚 临床病例学习中心")
    
    # 初始化session_state以减少刷新
    if 'case_library_initialized' not in st.session_state:
        st.session_state.case_library_initialized = True
        st.session_state.selected_case_index = 0
    
    # 记录进入病例库（只记录一次）
    if 'case_activity_logged' not in st.session_state:
        log_case_activity("进入模块", details="访问病例库")
        st.session_state.case_activity_logged = True
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0; color: white;">🏥 牙周病学临床病例库</h3>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">通过真实临床病例学习，掌握牙周病诊断与治疗的核心技能</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有病例供选择（使用缓存数据）
    all_cases = get_all_sample_cases()
    
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
                st.markdown("#### 🔍 主要症状")
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
            
            # 临床表现（新增）
            if 'clinical_manifestation' in selected_case:
                st.markdown("#### 🔬 临床表现")
                st.markdown(f"""
                <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; border-left: 4px solid #9c27b0; white-space: pre-line;">
                {selected_case['clinical_manifestation']}
                </div>
                """, unsafe_allow_html=True)
            
            # 辅助检查（新增）
            if 'auxiliary_examination' in selected_case:
                st.markdown("#### 🩻 辅助检查")
                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50; white-space: pre-line;">
                {selected_case['auxiliary_examination']}
                </div>
                """, unsafe_allow_html=True)
        
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
                        # 使用white-space: pre-line保留换行格式
                        st.markdown(f"""
                        <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; border: 1px solid #9c27b0; white-space: pre-line; line-height: 1.8;">
                            {staging['content']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # 如果没有详细分析，显示简要诊断要点
                st.markdown("#### 💡 诊断要点")
                key_points = ensure_list(
                    selected_case.get('key_points'),
                    ['注意病史采集', '仔细临床检查', '辅助检查分析']
                )
                for i, point in enumerate(key_points, 1):
                    st.markdown(f"""
                    <div style="background: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #0066cc;">
                        <strong>{i}.</strong> {point}
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab3:
            st.markdown("#### 💊 治疗计划")
            treatment = ensure_list(
                selected_case.get('treatment_plan'), 
                ['口腔卫生指导', '基础治疗', '定期复查']
            )
            
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
            
            # 治疗注意事项（新增字段）
            if 'treatment_notes' in selected_case:
                st.markdown("#### ⚠️ 治疗注意事项")
                st.markdown(f"""
                <div style="background: #fff8e1; padding: 15px; margin: 10px 0; 
                            border-radius: 8px; border-left: 4px solid #ffc107; white-space: pre-line;">
                    {selected_case['treatment_notes']}
                </div>
                """, unsafe_allow_html=True)
        
        with tab4:
            st.markdown("#### 📝 学习要点总结")
            
            # 显示关键学习要点
            key_points = ensure_list(
                selected_case.get('key_points'),
                ['注意病史采集', '仔细临床检查', '辅助检查分析']
            )
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
