"""
Neo4j连接和数据调试工具
用于检查Neo4j连接状态和数据库中的数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules.auth import check_neo4j_available, get_neo4j_driver, get_all_students
from modules.analytics import get_activity_summary

print("=" * 60)
print("Neo4j 连接和数据检查")
print("=" * 60)

# 1. 检查连接
print("\n1. 检查Neo4j连接...")
is_available = check_neo4j_available()
print(f"   Neo4j可用: {is_available}")

if not is_available:
    print("\n❌ Neo4j连接失败！请检查：")
    print("   - Neo4j服务是否启动")
    print("   - config/settings.py中的连接信息是否正确")
    print("   - 网络连接是否正常")
    sys.exit(1)

print("   ✅ Neo4j连接正常")

# 2. 获取driver并测试
print("\n2. 获取Neo4j driver...")
driver = get_neo4j_driver()
if driver:
    print("   ✅ Driver获取成功")
else:
    print("   ❌ Driver获取失败")
    sys.exit(1)

# 3. 查询学生数据
print("\n3. 查询学生数据...")
try:
    with driver.session() as session:
        result = session.run("MATCH (s:yzbx_Student) RETURN count(s) as count")
        student_count = result.single()['count']
        print(f"   学生总数: {student_count}")
        
        if student_count > 0:
            result = session.run("""
                MATCH (s:yzbx_Student) 
                RETURN s.student_id as id, s.name as name, s.login_count as logins
                LIMIT 5
            """)
            print("\n   前5个学生:")
            for record in result:
                print(f"   - {record['id']} | {record['name']} | 登录{record['logins']}次")
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

# 4. 查询活动数据
print("\n4. 查询活动记录...")
try:
    with driver.session() as session:
        result = session.run("MATCH (a:yzbx_Activity) RETURN count(a) as count")
        activity_count = result.single()['count']
        print(f"   活动记录总数: {activity_count}")
        
        if activity_count > 0:
            result = session.run("""
                MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
                RETURN s.student_id as student, a.type as type, a.module as module, a.timestamp as time
                ORDER BY a.timestamp DESC
                LIMIT 10
            """)
            print("\n   最近10条活动:")
            for record in result:
                print(f"   - {record['student']} | {record['module']} | {record['type']} | {record['time']}")
        else:
            print("\n   ⚠️  没有活动记录！这说明：")
            print("      - 学生访问时没有记录到数据库")
            print("      - 或者 check_neo4j_available() 返回False导致跳过记录")
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

# 5. 测试活动记录函数
print("\n5. 测试活动记录功能...")
from modules.auth import log_activity
try:
    log_activity(
        student_id="test_debug",
        activity_type="测试活动",
        module_name="调试模块",
        content_id="debug_001",
        content_name="调试测试",
        details="这是一条测试记录"
    )
    print("   ✅ 记录测试活动成功")
    
    # 验证是否记录成功
    with driver.session() as session:
        result = session.run("""
            MATCH (s:yzbx_Student {student_id: 'test_debug'})-[:PERFORMED]->(a:yzbx_Activity)
            RETURN count(a) as count
        """)
        test_count = result.single()['count']
        print(f"   测试学生的活动记录数: {test_count}")
        
        # 清理测试数据
        session.run("MATCH (s:yzbx_Student {student_id: 'test_debug'})-[r:PERFORMED]->(a:yzbx_Activity) DELETE r, a")
        session.run("MATCH (s:yzbx_Student {student_id: 'test_debug'}) DELETE s")
        print("   ✅ 测试数据已清理")
except Exception as e:
    print(f"   ❌ 测试失败: {e}")

# 6. 使用analytics函数查询
print("\n6. 测试analytics统计函数...")
try:
    summary = get_activity_summary()
    print(f"   总学生数: {summary['total_students']}")
    print(f"   总活动数: {summary['total_activities']}")
    print(f"   今日活动: {summary['today_activities']}")
    print(f"   活跃学生: {summary['active_students']}")
except Exception as e:
    print(f"   ❌ 统计失败: {e}")

# 7. 检查各模块的活动记录
print("\n7. 检查各模块活动分布...")
modules = ["病例库", "知识图谱", "能力推荐", "课中互动"]
try:
    with driver.session() as session:
        for module in modules:
            result = session.run("""
                MATCH (a:yzbx_Activity {module: $module})
                RETURN count(a) as count
            """, module=module)
            count = result.single()['count']
            print(f"   {module}: {count} 条记录")
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

print("\n" + "=" * 60)
print("检查完成！")
print("=" * 60)
