"""
模拟测试教师端页面加载
检查render_teacher_dashboard函数是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 模拟streamlit环境
class MockStreamlit:
    def metric(self, label, value, delta=None):
        print(f"   📊 {label}: {value}" + (f" ({delta})" if delta else ""))
    
    def markdown(self, text, unsafe_allow_html=False):
        if "教学数据概览" in text:
            print("\n📊 教学数据概览页面加载")
        elif "各模块学习数据" in text:
            print("\n📈 各模块学习数据")
    
    def columns(self, n):
        return [self] * n
    
    def info(self, text):
        print(f"ℹ️  {text}")
    
    def warning(self, text):
        print(f"⚠️  {text}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

sys.modules['streamlit'] = MockStreamlit()
import streamlit as st

print("="*60)
print("测试教师端render_teacher_dashboard函数")
print("="*60)

# 导入必要的函数
from modules.analytics import get_activity_summary, get_daily_activity_trend
from modules.auth import check_neo4j_available, get_all_students, get_single_module_statistics, get_neo4j_driver
import pandas as pd
import plotly.express as px

print("\n1. 检查Neo4j连接...")
has_neo4j = check_neo4j_available()
print(f"   Neo4j可用: {has_neo4j}")

print("\n2. 获取活动概况...")
summary = get_activity_summary()
all_students = get_all_students() if has_neo4j else []

total_students = summary.get('total_students', 0)
today_active = summary.get('today_activities', 0)
active_7d = summary.get('active_students', 0)
total_acts = summary.get('total_activities', 0)

print(f"   总学生数: {total_students}")
print(f"   今日活动: {today_active}")
print(f"   7日活跃: {active_7d}")
print(f"   总活动数: {total_acts}")

print("\n3. 渲染核心指标...")
mock_st = MockStreamlit()
col1, col2, col3, col4, col5 = [mock_st] * 5

col1.metric("👥 学生总数", str(total_students))
col2.metric("📚 今日活跃", str(today_active))
col3.metric("👨‍🎓 7日活跃学生", str(active_7d))
if has_neo4j:
    completion_rate = int((active_7d / total_students * 100)) if total_students > 0 else 0
    col4.metric("✅ 7日活跃率", f"{completion_rate}%")
else:
    col4.metric("✅ 7日活跃率", "0%")
col5.metric("📝 总学习记录", str(total_acts))

print("\n4. 获取各模块数据...")
modules = ["病例库", "知识图谱", "能力推荐", "课中互动"]

for module in modules:
    if has_neo4j:
        stats = get_single_module_statistics(module)
        visit_count = stats.get('total_visits', 0)
        student_count = stats.get('unique_students', 0)
        completion = int((student_count / total_students * 100)) if total_students > 0 else 0
        print(f"   {module}: {visit_count}次访问, {student_count}个学生, {completion}%参与率")
    else:
        print(f"   {module}: Neo4j不可用")

print("\n5. 测试排行榜查询...")
if has_neo4j:
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
            
            print("   Top 5 学生:")
            for i, record in enumerate(result):
                name = record['name'] if record['name'] else "未设置"
                print(f"   {i+1}. {record['student_id']} ({name}): {record['activity_count']}条记录")
    except Exception as e:
        print(f"   ❌ 排行榜查询失败: {e}")
else:
    print("   ⚠️  Neo4j不可用，跳过排行榜")

print("\n" + "="*60)
print("✅ 测试完成！")
print("="*60)
print("\n结论:")
if has_neo4j and total_students > 0:
    print("✅ 所有数据正常，教师端应该能显示数据")
    print("   如果页面还是没有数据，可能是:")
    print("   1. Streamlit缓存问题 - 清理缓存")
    print("   2. 浏览器缓存 - 强制刷新(Ctrl+Shift+R)")
    print("   3. 代码没有重新加载 - 重启Streamlit")
else:
    print("❌ 数据获取有问题:")
    if not has_neo4j:
        print("   - Neo4j连接失败")
    if total_students == 0:
        print("   - 没有学生数据")
