"""
Elasticsearch初始化脚本
创建索引并同步Neo4j的病例数据
"""

import json
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
    
    print("🚀 开始初始化Elasticsearch...")
    
    try:
        # 1. 删除旧索引（如果存在）
        index_name = "yzbx_cases"
        if es.indices.exists(index=index_name):
            print(f"📌 删除旧索引 {index_name}...")
            es.indices.delete(index=index_name)
        
        # 2. 创建新索引
        print(f"📌 创建索引 {index_name}...")
        es.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "chief_complaint": {"type": "text", "analyzer": "standard"},
                        "symptoms": {"type": "text", "analyzer": "standard"},
                        "diagnosis": {"type": "text", "analyzer": "standard"},
                        "difficulty": {"type": "keyword"},
                        "treatment_plan": {"type": "text", "analyzer": "standard"},
                        "related_knowledge": {"type": "keyword"}
                    }
                }
            }
        )
        
        # 3. 读取病例数据并索引
        print("📌 索引病例数据...")
        with open('data/cases.json', 'r', encoding='utf-8') as f:
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
                "related_knowledge": case['related_knowledge']
            }
            
            es.index(index=index_name, id=case['id'], document=doc)
            print(f"  ✓ 索引病例: {case['id']}")
        
        # 4. 刷新索引
        es.indices.refresh(index=index_name)
        
        # 5. 验证
        count = es.count(index=index_name)['count']
        print(f"\n📊 索引统计:")
        print(f"  病例总数: {count}")
        
        print("\n✅ Elasticsearch初始化完成！")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        raise
    finally:
        es.close()

if __name__ == "__main__":
    init_elasticsearch()
