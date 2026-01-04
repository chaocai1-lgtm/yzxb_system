"""
Elasticsearch初始化脚本
创建索引并同步病例数据和知识点数据
所有索引使用 yzbx_ 前缀
"""

import json
import os
from elasticsearch import Elasticsearch
from config.settings import (
    ELASTICSEARCH_CLOUD_ID,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD
)

def init_elasticsearch():
    """初始化Elasticsearch索引"""
    
    # 连接Elasticsearch
    es = Elasticsearch(
        cloud_id=ELASTICSEARCH_CLOUD_ID,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
    )
    
    print("🚀 开始初始化Elasticsearch（牙周病学）...")
    
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # ==================== 1. 病例索引 ====================
        index_cases = "yzbx_cases"
        if es.indices.exists(index=index_cases):
            print(f"📌 删除旧索引 {index_cases}...")
            es.indices.delete(index=index_cases)
        
        print(f"📌 创建索引 {index_cases}...")
        es.indices.create(
            index=index_cases,
            body={
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "standard"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "chief_complaint": {"type": "text", "analyzer": "standard"},
                        "symptoms": {"type": "text", "analyzer": "standard"},
                        "diagnosis": {"type": "text", "analyzer": "standard"},
                        "difficulty": {"type": "keyword"},
                        "treatment_plan": {"type": "text", "analyzer": "standard"},
                        "related_knowledge": {"type": "keyword"},
                        "patient_age": {"type": "integer"},
                        "patient_gender": {"type": "keyword"}
                    }
                }
            }
        )
        
        # 索引病例数据
        print("📌 索引病例数据...")
        cases_path = os.path.join(script_dir, 'data', 'cases.json')
        with open(cases_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        for case in cases:
            doc = {
                "id": case['id'],
                "title": case['title'],
                "chief_complaint": case['chief_complaint'],
                "symptoms": ' '.join(case['symptoms']),
                "diagnosis": case['diagnosis'],
                "difficulty": case['difficulty'],
                "treatment_plan": ' '.join(case['treatment_plan']),
                "related_knowledge": case.get('related_knowledge', []),
                "patient_age": case['patient_info']['age'],
                "patient_gender": case['patient_info']['gender']
            }
            es.index(index=index_cases, id=case['id'], document=doc)
        
        print(f"  ✓ 索引了 {len(cases)} 个病例")
        
        # ==================== 2. 知识点索引 ====================
        index_knowledge = "yzbx_knowledge"
        if es.indices.exists(index=index_knowledge):
            print(f"📌 删除旧索引 {index_knowledge}...")
            es.indices.delete(index=index_knowledge)
        
        print(f"📌 创建索引 {index_knowledge}...")
        es.indices.create(
            index=index_knowledge,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "chapter_id": {"type": "keyword"},
                        "module_id": {"type": "keyword"},
                        "importance": {"type": "keyword"}
                    }
                }
            }
        )
        
        # 知识点数据
        knowledge_points = [
            {"id": "KP_M1_C1_1", "name": "牙龈结构", "description": "包括游离龈、附着龈和龈乳头三部分。游离龈形成龈沟，正常深度0.5-3mm。", "chapter_id": "C1_1", "module_id": "M1", "importance": "high"},
            {"id": "KP_M1_C1_2", "name": "牙周膜组成", "description": "主要由胶原纤维束、细胞成分和基质组成。纤维束分为6组，提供牙齿支持。", "chapter_id": "C1_1", "module_id": "M1", "importance": "high"},
            {"id": "KP_M1_C1_3", "name": "牙槽骨特征", "description": "分为固有牙槽骨和支持骨。X线上固有牙槽骨呈硬骨板（骨白线）。", "chapter_id": "C1_1", "module_id": "M1", "importance": "high"},
            {"id": "KP_M1_C1_4", "name": "牙骨质类型", "description": "分为无细胞纤维性牙骨质（颈1/3）和有细胞纤维性牙骨质（根尖1/3）。", "chapter_id": "C1_1", "module_id": "M1", "importance": "medium"},
            {"id": "KP_M1_C2_1", "name": "龈沟液功能", "description": "含有免疫球蛋白、补体、白细胞等，具有冲洗和抗菌防御作用。", "chapter_id": "C1_2", "module_id": "M1", "importance": "high"},
            {"id": "KP_M1_C2_2", "name": "牙周韧带力学", "description": "可承受咀嚼力，具有本体感觉，调节咬合力大小。", "chapter_id": "C1_2", "module_id": "M1", "importance": "medium"},
            {"id": "KP_M1_C2_3", "name": "骨改建机制", "description": "成骨细胞与破骨细胞平衡，受机械力和炎症因子调控。", "chapter_id": "C1_2", "module_id": "M1", "importance": "high"},
            {"id": "KP_M2_C1_1", "name": "菌斑形成过程", "description": "获得性膜形成→早期定植菌黏附→共聚集→成熟生物膜，约需7-14天。", "chapter_id": "C2_1", "module_id": "M2", "importance": "high"},
            {"id": "KP_M2_C1_2", "name": "致病菌种类", "description": "主要包括牙龈卟啉单胞菌(Pg)、放线聚集杆菌(Aa)、福赛坦氏菌(Tf)等红色复合体。", "chapter_id": "C2_1", "module_id": "M2", "importance": "high"},
            {"id": "KP_M2_C1_3", "name": "生物膜结构", "description": "由细菌、胞外多糖基质、水通道组成，具有抗生素耐药性。", "chapter_id": "C2_1", "module_id": "M2", "importance": "medium"},
            {"id": "KP_M2_C2_1", "name": "牙石形成", "description": "菌斑矿化形成，龈上牙石主要来自唾液，龈下牙石来自龈沟液。", "chapter_id": "C2_2", "module_id": "M2", "importance": "high"},
            {"id": "KP_M2_C2_2", "name": "食物嵌塞", "description": "分为垂直型和水平型，可导致局部牙周破坏，需去除病因。", "chapter_id": "C2_2", "module_id": "M2", "importance": "medium"},
            {"id": "KP_M2_C2_3", "name": "不良修复体", "description": "悬突、边缘不密合等导致菌斑滞留，需重新修复。", "chapter_id": "C2_2", "module_id": "M2", "importance": "medium"},
            {"id": "KP_M3_C1_1", "name": "探诊技术", "description": "使用牙周探针，力度20-25g，记录6个位点探诊深度。", "chapter_id": "C3_1", "module_id": "M3", "importance": "high"},
            {"id": "KP_M3_C1_2", "name": "附着丧失测量", "description": "CAL=探诊深度-釉牙骨质界到龈缘距离，反映累积破坏。", "chapter_id": "C3_1", "module_id": "M3", "importance": "high"},
            {"id": "KP_M3_C1_3", "name": "牙周图表制作", "description": "记录探诊深度、出血、松动度等，便于治疗计划和随访。", "chapter_id": "C3_1", "module_id": "M3", "importance": "medium"},
            {"id": "KP_M3_C2_1", "name": "牙龈炎分类", "description": "包括菌斑性和非菌斑性牙龈病，前者最常见。", "chapter_id": "C3_2", "module_id": "M3", "importance": "high"},
            {"id": "KP_M3_C2_2", "name": "牙周炎分期", "description": "2018新分类采用分期(I-IV)和分级(A-C)系统。", "chapter_id": "C3_2", "module_id": "M3", "importance": "high"},
            {"id": "KP_M3_C2_3", "name": "新分类标准", "description": "基于附着丧失、骨吸收、失牙数分期；基于进展速率分级。", "chapter_id": "C3_2", "module_id": "M3", "importance": "high"},
            {"id": "KP_M4_C1_1", "name": "龈上洁治", "description": "去除龈上牙石和菌斑，使用超声或手工器械。", "chapter_id": "C4_1", "module_id": "M4", "importance": "high"},
            {"id": "KP_M4_C1_2", "name": "龈下刮治", "description": "深入牙周袋清除龈下牙石和感染牙骨质。", "chapter_id": "C4_1", "module_id": "M4", "importance": "high"},
            {"id": "KP_M4_C1_3", "name": "根面平整", "description": "使刮治后根面光滑，利于牙周组织再附着。", "chapter_id": "C4_1", "module_id": "M4", "importance": "high"},
            {"id": "KP_M4_C2_1", "name": "翻瓣术", "description": "切开牙龈、翻瓣暴露病变区进行清创，常见改良Widman翻瓣术。", "chapter_id": "C4_2", "module_id": "M4", "importance": "high"},
            {"id": "KP_M4_C2_2", "name": "植骨术", "description": "在骨缺损区填入骨替代材料，促进骨再生。", "chapter_id": "C4_2", "module_id": "M4", "importance": "medium"},
            {"id": "KP_M4_C2_3", "name": "引导再生", "description": "使用屏障膜引导牙周组织选择性再生。", "chapter_id": "C4_2", "module_id": "M4", "importance": "medium"},
            {"id": "KP_M5_C1_1", "name": "口腔卫生宣教", "description": "教授Bass刷牙法，使用牙线/牙间刷，定期专业维护。", "chapter_id": "C5_1", "module_id": "M5", "importance": "high"},
            {"id": "KP_M5_C1_2", "name": "刷牙方法", "description": "推荐Bass法或改良Bass法，每天2次，每次2分钟。", "chapter_id": "C5_1", "module_id": "M5", "importance": "high"},
            {"id": "KP_M5_C1_3", "name": "辅助工具", "description": "包括牙线、牙间刷、冲牙器等，根据牙间隙选择。", "chapter_id": "C5_1", "module_id": "M5", "importance": "medium"},
            {"id": "KP_M5_C2_1", "name": "复查周期", "description": "牙周炎患者建议3-6个月复查一次，高危患者更频繁。", "chapter_id": "C5_2", "module_id": "M5", "importance": "high"},
            {"id": "KP_M5_C2_2", "name": "SPT原则", "description": "支持性牙周治疗，终身维护，定期评估和必要的再治疗。", "chapter_id": "C5_2", "module_id": "M5", "importance": "high"},
            {"id": "KP_M5_C2_3", "name": "长期管理", "description": "监测探诊深度、出血指数，及时发现复发。", "chapter_id": "C5_2", "module_id": "M5", "importance": "medium"},
        ]
        
        for kp in knowledge_points:
            es.index(index=index_knowledge, id=kp['id'], document=kp)
        
        print(f"  ✓ 索引了 {len(knowledge_points)} 个知识点")
        
        # ==================== 3. 刷新索引 ====================
        es.indices.refresh(index=index_cases)
        es.indices.refresh(index=index_knowledge)
        
        # ==================== 4. 验证 ====================
        print("\n📊 索引统计:")
        print(f"  病例数: {es.count(index=index_cases)['count']}")
        print(f"  知识点数: {es.count(index=index_knowledge)['count']}")
        
        print("\n✅ Elasticsearch初始化完成！")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        raise
    finally:
        es.close()

if __name__ == "__main__":
    init_elasticsearch()
