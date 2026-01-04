"""修复学生数据：删除重复节点，创建缺失学生"""
from modules.auth import get_neo4j_driver

driver = get_neo4j_driver()

# 1. 查找重复的学生节点
print("检查重复的学生节点...")
records, _, _ = driver.execute_query('''
    MATCH (s:yzbx_Student)
    WITH s.student_id as student_id, collect(s) as nodes
    WHERE size(nodes) > 1
    RETURN student_id, size(nodes) as count
''')

if records:
    print(f"发现 {len(records)} 个重复的学生ID:")
    for r in records:
        print(f"  学生 {r['student_id']}: {r['count']} 个节点")
    
    # 删除重复节点，保留一个
    print("\n删除重复节点...")
    for r in records:
        student_id = r['student_id']
        driver.execute_query('''
            MATCH (s:yzbx_Student {student_id: $student_id})
            WITH s, s.login_count as login_count
            ORDER BY login_count DESC
            WITH collect(s) as nodes
            FOREACH (n in tail(nodes) | DETACH DELETE n)
        ''', student_id=student_id)
        print(f"  已清理学生 {student_id} 的重复节点")
else:
    print("没有发现重复节点")

# 2. 创建缺失的学生节点（1-38）
print("\n检查并创建缺失的学生节点...")
existing_ids, _, _ = driver.execute_query(
    'MATCH (s:yzbx_Student) RETURN s.student_id as student_id'
)
existing_set = set(r['student_id'] for r in existing_ids)

missing_ids = []
for i in range(1, 39):
    if str(i) not in existing_set:
        missing_ids.append(str(i))

if missing_ids:
    print(f"需要创建 {len(missing_ids)} 个学生节点: {', '.join(missing_ids)}")
    for student_id in missing_ids:
        driver.execute_query('''
            MERGE (s:yzbx_Student {student_id: $student_id})
            ON CREATE SET s.name = $student_id, s.last_login = datetime(), s.login_count = 0
        ''', student_id=student_id)
    print("学生节点创建完成")
else:
    print("所有学生节点已存在")

# 3. 验证结果
print("\n验证结果:")
records, _, _ = driver.execute_query('''
    MATCH (s:yzbx_Student)
    RETURN count(s) as total_students
''')
total = records[0]['total_students']
print(f"当前学生总数: {total}")

# 显示所有学生
records, _, _ = driver.execute_query('''
    MATCH (s:yzbx_Student)
    OPTIONAL MATCH (s)-[:PERFORMED]->(a:yzbx_Activity)
    RETURN s.student_id as student_id, count(a) as activity_count
    ORDER BY toInteger(s.student_id)
''')
print("\n所有学生列表:")
for r in records:
    print(f"  学生 {r['student_id']}: {r['activity_count']} 条活动")

print("\n修复完成！")
