from modules.auth import get_neo4j_driver

driver = get_neo4j_driver()
records, summary, keys = driver.execute_query(
    'MATCH (s:yzbx_Student) RETURN s.student_id as student_id ORDER BY toInteger(s.student_id)'
)

print(f'学生总数: {len(records)}')
print('\n学生ID列表:')
for r in records:
    print(f'  {r["student_id"]}')

# 检查是否有1-38的所有学生
all_ids = [r["student_id"] for r in records]
missing_ids = []
for i in range(1, 39):
    if str(i) not in all_ids:
        missing_ids.append(str(i))

if missing_ids:
    print(f'\n缺失的学生ID: {", ".join(missing_ids)}')
else:
    print('\n所有1-38号学生都存在')

# 统计每个学生的活动数
print('\n每个学生的活动数:')
records2, _, _ = driver.execute_query('''
    MATCH (s:yzbx_Student)
    OPTIONAL MATCH (s)-[:PERFORMED]->(a:yzbx_Activity)
    RETURN s.student_id as student_id, count(a) as activity_count
    ORDER BY toInteger(s.student_id)
''')
for r in records2:
    print(f'  学生 {r["student_id"]}: {r["activity_count"]} 条活动')
