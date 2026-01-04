"""
数据分析模块
教师查看、分析和管理学生学习数据
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from modules.auth import (
    get_all_students, get_student_activities, get_module_statistics,
    delete_student_data, delete_all_activities, check_neo4j_available,
    get_single_module_statistics
)
from config.settings import *

def get_neo4j_driver():
    """获取Neo4j连接"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def get_activity_summary():
    """获取活动概况"""
    if not check_neo4j_available():
        return {
            'total_students': 0,
            'total_activities': 0,
            'today_activities': 0,
            'active_students': 0
        }
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 总学生数
            result = session.run("MATCH (s:yzbx_Student) RETURN count(s) as count")
            total_students = result.single()['count']
            
            # 总活动数
            result = session.run("MATCH (a:yzbx_Activity) RETURN count(a) as count")
            total_activities = result.single()['count']
            
            # 今日活动数
            result = session.run("""
                MATCH (a:yzbx_Activity)
                WHERE date(a.timestamp) = date()
                RETURN count(a) as count
            """)
            today_activities = result.single()['count']
            
            # 活跃学生数（7天内）
            result = session.run("""
                MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
                WHERE a.timestamp > datetime() - duration('P7D')
                RETURN count(DISTINCT s) as count
            """)
            active_students = result.single()['count']
        
        driver.close()
        return {
            'total_students': total_students,
            'total_activities': total_activities,
            'today_activities': today_activities,
            'active_students': active_students
        }
    except Exception:
        return {
            'total_students': 0,
            'total_activities': 0,
            'today_activities': 0,
            'active_students': 0
        }

def get_daily_activity_trend(days=7):
    """获取每日活动趋势"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run("""
                MATCH (a:yzbx_Activity)
                WHERE a.timestamp > datetime() - duration('P' + $days + 'D')
                RETURN date(a.timestamp) as date, count(*) as count
                ORDER BY date
            """, days=str(days))
            
            trend = [dict(record) for record in result]
        
        driver.close()
        return trend
    except Exception:
        return []

def get_module_usage():
    """获取各模块使用情况"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run("""
                MATCH (a:yzbx_Activity)
                RETURN a.module as module, count(*) as count
                ORDER BY count DESC
            """)
            
            usage = [dict(record) for record in result]
        
        driver.close()
        return usage
    except Exception:
        return []

def get_popular_content(module=None, limit=10):
    """获取热门学习内容"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            query = """
                MATCH (a:yzbx_Activity)
                WHERE a.content_name IS NOT NULL
            """
            params = {"limit": limit}
            
            if module:
                query += " AND a.module = $module"
                params["module"] = module
            
            query += """
                RETURN a.module as module,
                       a.content_name as content_name,
                       count(*) as view_count,
                       count(DISTINCT a.content_id) as unique_views
                ORDER BY view_count DESC
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            content = [dict(record) for record in result]
        
        driver.close()
        return content
    except Exception:
        return []

def get_student_learning_profile(student_id):
    """获取学生学习画像"""
    if not check_neo4j_available():
        return None
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 基本信息
            result = session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})
                RETURN s.name as name, s.last_login as last_login, s.login_count as login_count
            """, student_id=student_id)
            
            student_info = dict(result.single()) if result.peek() else None
            
            if not student_info:
                driver.close()
                return None
            
            # 各模块活动统计
            result = session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})-[:PERFORMED]->(a:yzbx_Activity)
                RETURN a.module as module, count(*) as count
                ORDER BY count DESC
            """, student_id=student_id)
            
            module_stats = [dict(record) for record in result]
            
            # 学习时间分布
            result = session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})-[:PERFORMED]->(a:yzbx_Activity)
                RETURN a.timestamp.hour as hour, count(*) as count
                ORDER BY hour
            """, student_id=student_id)
            
            time_distribution = [dict(record) for record in result]
            
            # 查看的内容
            result = session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})-[:PERFORMED]->(a:yzbx_Activity)
                WHERE a.content_name IS NOT NULL
                RETURN a.module as module, a.content_name as content, a.timestamp as time
                ORDER BY a.timestamp DESC
                LIMIT 20
            """, student_id=student_id)
            
            recent_content = [dict(record) for record in result]
        
        driver.close()
        
        return {
            'info': student_info,
            'module_stats': module_stats,
            'time_distribution': time_distribution,
            'recent_content': recent_content
        }
    except Exception:
        return None

def get_classroom_interaction_stats():
    """获取课中互动统计"""
    if not check_neo4j_available():
        return {'questions': [], 'participation': []}
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 问题统计
            result = session.run("""
                MATCH (q:yzbx_Question)
                OPTIONAL MATCH (s:yzbx_Student)-[r:REPLIED]->(q)
                RETURN q.id as question_id,
                       q.text as question_text,
                       q.created_at as created_at,
                       q.status as status,
                       count(r) as reply_count
                ORDER BY q.created_at DESC
                LIMIT 20
            """)
            
            questions = [dict(record) for record in result]
            
            # 学生参与度
            result = session.run("""
                MATCH (s:yzbx_Student)-[r:REPLIED]->(q:yzbx_Question)
                RETURN s.name as student_name,
                       s.student_id as student_id,
                       count(r) as reply_count
                ORDER BY reply_count DESC
                LIMIT 20
            """)
            
            participation = [dict(record) for record in result]
        
        driver.close()
        
        return {
            'questions': questions,
            'participation': participation
        }
    except Exception:
        return {'questions': [], 'participation': []}

def render_analytics_dashboard():
    """渲染数据分析面板"""
    st.title("📊 学习数据分析")
    
    # 概况卡片
    summary = get_activity_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 总学生数", summary['total_students'])
    with col2:
        st.metric("📝 总活动记录", summary['total_activities'])
    with col3:
        st.metric("📅 今日活动", summary['today_activities'])
    with col4:
        st.metric("🔥 活跃学生(7天)", summary['active_students'])
    
    st.divider()
    
    # 标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 总体趋势", "👥 学生列表", "📖 个人画像", "💬 课堂互动", "🗑️ 数据管理"
    ])
    
    with tab1:
        render_overall_trends()
    
    with tab2:
        render_student_list()
    
    with tab3:
        render_student_profile()
    
    with tab4:
        render_classroom_stats()
    
    with tab5:
        render_data_management()

def render_overall_trends():
    """渲染总体趋势"""
    st.subheader("📈 学习活动趋势")
    
    # 日期范围选择
    days = st.selectbox("时间范围", [7, 14, 30], format_func=lambda x: f"最近{x}天")
    
    # 每日活动趋势图
    trend_data = get_daily_activity_trend(days)
    if trend_data:
        df = pd.DataFrame(trend_data)
        fig = px.line(df, x='date', y='count', title='每日学习活动趋势',
                      labels={'date': '日期', 'count': '活动次数'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无活动数据")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 模块使用饼图
        st.subheader("📊 模块使用分布")
        usage_data = get_module_usage()
        if usage_data:
            df = pd.DataFrame(usage_data)
            fig = px.pie(df, values='count', names='module', title='各模块使用占比')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")
    
    with col2:
        # 热门内容
        st.subheader("🔥 热门学习内容")
        popular = get_popular_content(limit=10)
        if popular:
            df = pd.DataFrame(popular)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据")

def render_student_list():
    """渲染学生列表"""
    st.subheader("👥 学生学习记录")
    
    students = get_all_students()
    
    if students:
        df = pd.DataFrame(students)
        
        # 格式化显示
        df_display = df.copy()
        df_display['last_login'] = df_display['last_login'].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M') if hasattr(x, 'strftime') else str(x) if x else '-'
        )
        
        st.dataframe(
            df_display,
            column_config={
                "student_id": "学号",
                "name": "姓名",
                "last_login": "最后登录",
                "login_count": "登录次数",
                "activity_count": "活动次数"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # 导出按钮
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 导出学生列表CSV",
            data=csv,
            file_name=f"学生列表_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("暂无学生数据")

def render_student_profile():
    """渲染学生个人画像"""
    st.subheader("📖 学生学习画像")
    
    students = get_all_students()
    if not students:
        st.info("暂无学生数据")
        return
    
    # 选择学生
    student_options = {f"{s['student_id']} - {s['name']}": s['student_id'] for s in students}
    selected = st.selectbox("选择学生", list(student_options.keys()))
    
    if selected:
        student_id = student_options[selected]
        profile = get_student_learning_profile(student_id)
        
        if profile:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("姓名", profile['info']['name'])
            with col2:
                st.metric("登录次数", profile['info']['login_count'] or 0)
            with col3:
                last_login = profile['info']['last_login']
                if hasattr(last_login, 'strftime'):
                    last_login = last_login.strftime('%Y-%m-%d %H:%M')
                st.metric("最后登录", last_login or '-')
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 模块活动统计
                if profile['module_stats']:
                    df = pd.DataFrame(profile['module_stats'])
                    fig = px.bar(df, x='module', y='count', title='各模块学习次数',
                                labels={'module': '模块', 'count': '次数'})
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 学习时间分布
                if profile['time_distribution']:
                    df = pd.DataFrame(profile['time_distribution'])
                    fig = px.bar(df, x='hour', y='count', title='学习时间分布',
                                labels={'hour': '小时', 'count': '次数'})
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            
            # 最近学习内容
            st.subheader("📚 最近学习内容")
            if profile['recent_content']:
                df = pd.DataFrame(profile['recent_content'])
                df['time'] = df['time'].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M') if hasattr(x, 'strftime') else str(x)
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无学习记录")
            
            # 导出个人数据
            activities = get_student_activities(student_id=student_id)
            if activities:
                df = pd.DataFrame(activities)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 导出该学生学习记录",
                    data=csv,
                    file_name=f"学习记录_{student_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

def render_classroom_stats():
    """渲染课堂互动统计"""
    st.subheader("💬 课堂互动数据")
    
    stats = get_classroom_interaction_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 问题统计")
        if stats['questions']:
            for q in stats['questions'][:10]:
                status_emoji = "🟢" if q['status'] == 'active' else "🔴"
                created = q['created_at'].strftime('%m-%d %H:%M') if hasattr(q['created_at'], 'strftime') else str(q['created_at'])[:10]
                st.markdown(f"""
                {status_emoji} **{q['question_text'][:30]}...**
                - 回复数: {q['reply_count']} | 时间: {created}
                """)
        else:
            st.info("暂无问题数据")
    
    with col2:
        st.markdown("### 学生参与度排行")
        if stats['participation']:
            df = pd.DataFrame(stats['participation'])
            fig = px.bar(df.head(10), x='student_name', y='reply_count', 
                        title='回答次数Top10',
                        labels={'student_name': '学生', 'reply_count': '回答次数'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无参与数据")

def render_data_management():
    """渲染数据管理"""
    st.subheader("🗑️ 数据管理")
    
    st.warning("⚠️ 以下操作不可撤销，请谨慎操作！")
    
    # 删除特定学生数据
    st.markdown("### 删除学生数据")
    students = get_all_students()
    if students:
        student_options = {f"{s['student_id']} - {s['name']}": s['student_id'] for s in students}
        selected = st.selectbox("选择要删除的学生", list(student_options.keys()), key="delete_student")
        
        if st.button("🗑️ 删除该学生数据", type="secondary"):
            student_id = student_options[selected]
            delete_student_data(student_id)
            st.success(f"已删除学生 {selected} 的所有数据")
            st.rerun()
    
    st.divider()
    
    # 清空所有活动记录
    st.markdown("### 清空活动记录")
    if st.button("🗑️ 清空所有活动记录", type="secondary"):
        confirm = st.checkbox("确认清空所有活动记录（不删除学生账号）")
        if confirm:
            delete_all_activities()
            st.success("已清空所有活动记录")
            st.rerun()
    
    st.divider()
    
    # 导出所有数据
    st.markdown("### 导出数据")
    col1, col2 = st.columns(2)
    
    with col1:
        activities = get_student_activities(limit=1000)
        if activities:
            df = pd.DataFrame(activities)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出所有活动记录",
                data=csv,
                file_name=f"全部活动记录_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if students:
            df = pd.DataFrame(students)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 导出学生名单",
                data=csv,
                file_name=f"学生名单_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

def render_module_analytics(module_name):
    """渲染特定模块的数据分析页面"""
    st.title(f"📊 {module_name} - 学习数据分析")
    
    # 获取该模块的独立统计数据
    module_data = get_single_module_statistics(module_name)
    
    # 如果数据库没有数据，尝试从活动记录中计算
    if not module_data:
        activities = get_student_activities(limit=1000)
        module_activities = [a for a in activities if a.get('module') == module_name]
        unique_students = len(set(a.get('student_id') for a in module_activities if a.get('student_id')))
        today = datetime.now().strftime('%Y-%m-%d')
        today_activities = [a for a in module_activities if str(a.get('timestamp', ''))[:10] == today]
        
        module_data = {
            'module': module_name,
            'total_activities': len(module_activities),
            'unique_students': unique_students,
            'today_count': len(today_activities)
        }
    
    # 概览卡片
    col1, col2, col3, col4 = st.columns(4)
    
    total = module_data.get('total_activities', 0) or 0
    students = module_data.get('unique_students', 0) or 0
    today_count = module_data.get('today_count', 0) or 0
    
    with col1:
        st.metric("📊 总访问次数", total)
    with col2:
        st.metric("👥 访问学生数", students)
    with col3:
        avg_per_student = total / max(students, 1)
        st.metric("📈 人均访问", f"{avg_per_student:.1f}次")
    with col4:
        st.metric("📅 今日访问", today_count)
    
    st.divider()
    
    # 选项卡
    tab1, tab2, tab3 = st.tabs(["📈 整体数据", "👤 个人数据", "🗑️ 数据管理"])
    
    with tab1:
        render_module_overview(module_name)
    
    with tab2:
        render_module_student_detail(module_name)
    
    with tab3:
        render_data_management()

def render_module_overview(module_name):
    """渲染模块整体数据"""
    st.subheader(f"📈 {module_name} - 整体学习数据")
    
    # 获取该模块的活动数据 - 使用module参数筛选
    activities = get_student_activities(module=module_name, limit=500)
    module_activities = activities  # 已经是该模块的数据
    
    if not module_activities:
        # 使用该模块特定的示例数据
        st.info(f"📊 {module_name}暂无实际学习数据，以下为示例展示")
        
        # 根据模块名称生成不同的示例数据
        example_data = {
            "病例库": [
                {"student_name": "张三", "activity_type": "查看病例", "timestamp": "2026-01-03 10:30", "content_name": "慢性牙周炎病例"},
                {"student_name": "李四", "activity_type": "查看病例", "timestamp": "2026-01-03 11:15", "content_name": "侵袭性牙周炎病例"},
                {"student_name": "王五", "activity_type": "保存笔记", "timestamp": "2026-01-03 14:20", "content_name": "牙周-牙髓联合病变"},
                {"student_name": "张三", "activity_type": "查看病例", "timestamp": "2026-01-03 15:45", "content_name": "药物性牙龈增生"},
                {"student_name": "赵六", "activity_type": "进入模块", "timestamp": "2026-01-03 16:00", "content_name": None},
            ],
            "知识图谱": [
                {"student_name": "张三", "activity_type": "查看模块", "timestamp": "2026-01-03 09:20", "content_name": "M1-生物学基础"},
                {"student_name": "李四", "activity_type": "查看模块", "timestamp": "2026-01-03 10:00", "content_name": "M2-病因与发病机制"},
                {"student_name": "王五", "activity_type": "点击节点", "timestamp": "2026-01-03 11:30", "content_name": "牙周组织解剖"},
                {"student_name": "赵六", "activity_type": "查看模块", "timestamp": "2026-01-03 14:00", "content_name": "M3-诊断与分类"},
                {"student_name": "张三", "activity_type": "进入模块", "timestamp": "2026-01-03 16:30", "content_name": None},
            ],
            "能力推荐": [
                {"student_name": "张三", "activity_type": "能力自评", "timestamp": "2026-01-03 10:00", "content_name": "牙周探诊技术"},
                {"student_name": "李四", "activity_type": "能力自评", "timestamp": "2026-01-03 11:00", "content_name": "牙周病诊断"},
                {"student_name": "王五", "activity_type": "生成AI推荐", "timestamp": "2026-01-03 13:00", "content_name": "学习路径"},
                {"student_name": "赵六", "activity_type": "能力自评", "timestamp": "2026-01-03 15:00", "content_name": "洁治术操作"},
                {"student_name": "张三", "activity_type": "进入模块", "timestamp": "2026-01-03 16:00", "content_name": None},
            ],
            "课中互动": [
                {"student_name": "张三", "activity_type": "回答问题", "timestamp": "2026-01-03 08:30", "content_name": "牙周探诊深度正常值"},
                {"student_name": "李四", "activity_type": "回答问题", "timestamp": "2026-01-03 08:35", "content_name": "牙周探诊深度正常值"},
                {"student_name": "王五", "activity_type": "提交练习", "timestamp": "2026-01-03 09:00", "content_name": "探诊练习"},
                {"student_name": "赵六", "activity_type": "回答问题", "timestamp": "2026-01-03 14:00", "content_name": "牙周病分类"},
                {"student_name": "张三", "activity_type": "进入模块", "timestamp": "2026-01-03 08:00", "content_name": None},
            ],
        }
        
        module_activities = example_data.get(module_name, example_data["病例库"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 活动类型分布
        st.markdown("#### 📊 学习行为分布")
        activity_types = {}
        for a in module_activities:
            t = a.get('activity_type', '其他')
            activity_types[t] = activity_types.get(t, 0) + 1
        
        if activity_types:
            fig = px.pie(
                values=list(activity_types.values()),
                names=list(activity_types.keys()),
                title=f'{module_name} - 学习行为类型分布'
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 热门内容
        st.markdown("#### 🔥 热门学习内容")
        content_counts = {}
        for a in module_activities:
            c = a.get('content_name')
            if c:
                content_counts[c] = content_counts.get(c, 0) + 1
        
        if content_counts:
            sorted_content = sorted(content_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (name, count) in enumerate(sorted_content, 1):
                st.markdown(f"**{i}. {name}** - {count}次访问")
        else:
            st.info("暂无内容访问记录")
    
    # 最近活动记录
    st.markdown(f"#### 📝 {module_name} - 最近学习记录")
    if module_activities:
        df = pd.DataFrame(module_activities[:20])
        display_cols = ['student_name', 'activity_type', 'content_name', 'timestamp']
        display_cols = [c for c in display_cols if c in df.columns]
        if display_cols:
            df_display = df[display_cols].copy()
            df_display.columns = ['学生', '行为', '内容', '时间'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

def render_module_student_detail(module_name):
    """渲染模块个人数据"""
    st.subheader(f"👤 {module_name}模块 - 学生个人数据")
    
    # 获取学生列表
    students = get_all_students()
    
    if not students:
        # 使用示例学生
        students = [
            {"student_id": "2024001", "name": "张三", "login_count": 5},
            {"student_id": "2024002", "name": "李四", "login_count": 3},
            {"student_id": "2024003", "name": "王五", "login_count": 8},
        ]
    
    # 学生选择
    student_options = {f"{s.get('student_id', '')} - {s.get('name', '')}": s for s in students}
    selected = st.selectbox("选择学生", list(student_options.keys()))
    
    if selected:
        student = student_options[selected]
        student_id = student.get('student_id', '')
        
        # 获取该学生在此模块的活动 - 使用module参数
        student_module_activities = get_student_activities(student_id=student_id, module=module_name, limit=100)
        
        if not student_module_activities:
            # 根据模块名称生成不同的示例数据
            example_data = {
                "病例库": [
                    {"activity_type": "进入模块", "timestamp": "2026-01-03 09:00", "content_name": None, "details": "访问病例库"},
                    {"activity_type": "查看病例", "timestamp": "2026-01-03 09:05", "content_name": "慢性牙周炎病例", "details": None},
                    {"activity_type": "保存笔记", "timestamp": "2026-01-03 09:15", "content_name": "慢性牙周炎病例", "details": "笔记内容..."},
                ],
                "知识图谱": [
                    {"activity_type": "进入模块", "timestamp": "2026-01-03 10:00", "content_name": None, "details": "访问知识图谱"},
                    {"activity_type": "查看模块", "timestamp": "2026-01-03 10:05", "content_name": "M1-生物学基础", "details": None},
                    {"activity_type": "点击节点", "timestamp": "2026-01-03 10:10", "content_name": "牙周组织解剖", "details": "查看详情"},
                ],
                "能力推荐": [
                    {"activity_type": "进入模块", "timestamp": "2026-01-03 11:00", "content_name": None, "details": "访问能力推荐"},
                    {"activity_type": "能力自评", "timestamp": "2026-01-03 11:05", "content_name": "牙周探诊技术", "details": "掌握度50%"},
                    {"activity_type": "生成AI推荐", "timestamp": "2026-01-03 11:10", "content_name": "学习路径", "details": "成功生成"},
                ],
                "课中互动": [
                    {"activity_type": "进入模块", "timestamp": "2026-01-03 08:00", "content_name": None, "details": "访问课中互动"},
                    {"activity_type": "回答问题", "timestamp": "2026-01-03 08:30", "content_name": "牙周探诊深度", "details": "回答正确"},
                    {"activity_type": "提交练习", "timestamp": "2026-01-03 08:45", "content_name": "探诊练习", "details": "完成练习"},
                ],
            }
            student_module_activities = example_data.get(module_name, example_data["病例库"])
        
        # 学生数据卡片
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"📊 {module_name}访问次数", len(student_module_activities))
        with col2:
            content_viewed = len(set(a.get('content_name') for a in student_module_activities if a.get('content_name')))
            st.metric("📚 学习内容数", content_viewed)
        with col3:
            st.metric("🔑 总登录次数", student.get('login_count', 0))
        
        # 活动时间线
        st.markdown(f"#### 📅 {module_name} - 学习时间线")
        
        # 根据模块设置不同的图标
        icon_map = {
            "病例库": {"查看病例": "📋", "保存笔记": "✍️", "进入模块": "👁️"},
            "知识图谱": {"查看模块": "🗺️", "点击节点": "📍", "进入模块": "👁️"},
            "能力推荐": {"能力自评": "📊", "生成AI推荐": "🤖", "进入模块": "👁️"},
            "课中互动": {"回答问题": "💬", "提交练习": "📝", "进入模块": "👁️"},
        }
        module_icons = icon_map.get(module_name, {"default": "📖"})
        
        for activity in student_module_activities[:10]:
            action = activity.get('activity_type', '')
            icon = module_icons.get(action, "👁️")
            content = activity.get('content_name', '')
            time = activity.get('timestamp', '')
            
            st.markdown(f"""
            <div style="padding: 10px; margin: 5px 0; background: #f8f9fa; border-left: 3px solid #4ECDC4; border-radius: 5px;">
                {icon} <strong>{action}</strong> {f'- {content}' if content else ''}
                <span style="float: right; color: gray;">{time}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 导出该学生数据
        if student_module_activities:
            df = pd.DataFrame(student_module_activities)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 导出{student.get('name', '')}的{module_name}学习记录",
                data=csv,
                file_name=f"{student.get('name', 'student')}_{module_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
