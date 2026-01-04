"""
Neo4j数据库初始化脚本
执行Cypher脚本，创建知识图谱、能力图谱和病例数据
"""

import json
from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def init_neo4j():
    """初始化Neo4j数据库"""
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    print("🚀 开始初始化Neo4j数据库...")
    
    try:
        with driver.session() as session:
            # 1. 清空yzbx标签的所有数据（可选，首次运行可注释）
            print("📌 清空旧数据...")
            session.run("""
                MATCH (n)
                WHERE any(label IN labels(n) WHERE label STARTS WITH 'yzbx')
                DETACH DELETE n
            """)
            
            # 2. 读取并执行Cypher初始化脚本
            print("📌 创建知识图谱...")
            with open('data/neo4j_init.cypher', 'r', encoding='utf-8') as f:
                cypher_script = f.read()
                
            # 分割多个语句并执行
            statements = [s.strip() for s in cypher_script.split('\n\n') if s.strip() and not s.strip().startswith('//')]
            
            for i, statement in enumerate(statements):
                if statement and not statement.startswith('//'):
                    try:
                        session.run(statement)
                        print(f"  ✓ 执行语句 {i+1}/{len(statements)}")
                    except Exception as e:
                        print(f"  ✗ 语句执行失败: {str(e)[:100]}")
            
            # 3. 创建病例节点
            print("📌 创建病例数据...")
            with open('data/cases.json', 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            for case in cases:
                session.run("""
                    CREATE (c:yzbx_Case {
                        id: $id,
                        title: $title,
                        chief_complaint: $chief_complaint,
                        patient_age: $patient_age,
                        patient_gender: $patient_gender,
                        diagnosis: $diagnosis,
                        difficulty: $difficulty,
                        symptoms: $symptoms,
                        treatment_plan: $treatment_plan
                    })
                """, 
                    id=case['id'],
                    title=case['title'],
                    chief_complaint=case['chief_complaint'],
                    patient_age=case['patient_info']['age'],
                    patient_gender=case['patient_info']['gender'],
                    diagnosis=case['diagnosis'],
                    difficulty=case['difficulty'],
                    symptoms=case['symptoms'],
                    treatment_plan=case['treatment_plan']
                )
                
                # 创建病例与知识点的关联
                for kp_id in case['related_knowledge']:
                    session.run("""
                        MATCH (c:yzbx_Case {id: $case_id})
                        MATCH (k:yzbx_Knowledge {id: $kp_id})
                        CREATE (c)-[:RELATES_TO {weight: 0.8}]->(k)
                    """, case_id=case['id'], kp_id=kp_id)
            
            print(f"  ✓ 创建了 {len(cases)} 个病例")
            
            # 4. 验证数据
            print("\n📊 数据统计:")
            result = session.run("MATCH (n:yzbx_Module) RETURN count(n) as count")
            print(f"  模块数: {result.single()['count']}")
            
            result = session.run("MATCH (n:yzbx_Chapter) RETURN count(n) as count")
            print(f"  章节数: {result.single()['count']}")
            
            result = session.run("MATCH (n:yzbx_Knowledge) RETURN count(n) as count")
            print(f"  知识点数: {result.single()['count']}")
            
            result = session.run("MATCH (n:yzbx_Case) RETURN count(n) as count")
            print(f"  病例数: {result.single()['count']}")
            
            result = session.run("MATCH (n:yzbx_Ability) RETURN count(n) as count")
            print(f"  能力数: {result.single()['count']}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            print(f"  关系数: {result.single()['count']}")
            
        print("\n✅ Neo4j初始化完成！")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        raise
    finally:
        driver.close()

if __name__ == "__main__":
    init_neo4j()
