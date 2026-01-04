"""
测试教师端数据显示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("测试教师端数据显示")
print("="*60)

# 1. 测试基础数据
print("\n1. 测试活动概况...")
from modules.analytics import get_activity_summary
summary = get_activity_summary()
print(f"   总学生数: {summary['total_students']}")
print(f"   总活动数: {summary['total_activities']}")
print(f"   今日活动: {summary['today_activities']}")
print(f"   活跃学生: {summary['active_students']}")

# 2. 测试模块统计
print("\n2. 测试各模块统计...")
from modules.auth import get_single_module_statistics

modules = ["病例库", "知识图谱", "能力推荐", "课中互动"]
for module in modules:
    stats = get_single_module_statistics(module)
    print(f"\n   【{module}】")
    print(f"   - 总访问次数: {stats.get('total_visits', 0)}")
    print(f"   - 参与学生数: {stats.get('unique_students', 0)}")
    print(f"   - 人均访问数: {stats.get('avg_visits_per_student', 0)}")
    print(f"   - 近7日访问: {stats.get('recent_7d_visits', 0)}")

# 3. 测试学生列表
print("\n3. 测试学生列表...")
from modules.auth import get_all_students
students = get_all_students()
print(f"   学生总数: {len(students)}")
if students:
    print(f"   前3个学生:")
    for s in students[:3]:
        print(f"   - {s['student_id']}: {s.get('name', '未设置')}")

# 4. 测试学生排行
print("\n4. 测试学生排行榜...")
from modules.auth import get_neo4j_driver
try:
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
            RETURN s.student_id as student_id, 
                   s.name as name,
                   count(a) as activity_count,
                   count(DISTINCT date(a.timestamp)) as active_days
            ORDER BY activity_count DESC
            LIMIT 5
        """)
        
        print("   Top 5学生:")
        for i, record in enumerate(result):
            print(f"   {i+1}. {record['student_id']} - {record['name']} - {record['activity_count']}条记录 - {record['active_days']}天活跃")
except Exception as e:
    print(f"   ❌ 排行榜查询失败: {e}")

# 5. 测试7天趋势
print("\n5. 测试7天活动趋势...")
from modules.analytics import get_daily_activity_trend
trend = get_daily_activity_trend(7)
if trend:
    print(f"   返回{len(trend)}天数据:")
    for day in trend[:3]:
        print(f"   - {day['date']}: {day['count']}条活动")
else:
    print("   ⚠️  无趋势数据")

# 6. 测试模块分析页面数据
print("\n6. 测试病例库模块分析数据...")
from modules.auth import get_student_activities
if students:
    test_student = students[0]['student_id']
    activities = get_student_activities(test_student, "病例库")
    print(f"   学生{test_student}的病例库活动: {len(activities)}条")
    if activities:
        print(f"   最近一条: {activities[0]}")

# 7. 测试模块排行
print("\n7. 测试病例库排行榜...")
try:
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
            WHERE a.module = $module_name
            RETURN s.student_id as student_id, 
                   s.name as name,
                   count(a) as activity_count
            ORDER BY activity_count DESC
            LIMIT 5
        """, module_name="病例库")
        
        ranking = list(result)
        print(f"   病例库Top学生: {len(ranking)}人")
        for i, record in enumerate(ranking[:3]):
            print(f"   {i+1}. {record['student_id']} - {record['activity_count']}条")
except Exception as e:
    print(f"   ❌ 模块排行查询失败: {e}")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
print("\n如果上面所有数据都正常，但教师端页面还是没有数据，")
print("请检查：")
print("1. 教师登录是否成功")
print("2. 浏览器是否有缓存")
print("3. Streamlit缓存是否需要清理")
