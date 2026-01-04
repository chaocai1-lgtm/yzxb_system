"""
认证模块
处理学生登录和教师登录验证
"""

import streamlit as st
from datetime import datetime

# 可选导入Neo4j（仅本地开发需要）
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    GraphDatabase = None

try:
    from config.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
except (ImportError, AttributeError):
    NEO4J_URI = None
    NEO4J_USERNAME = None
    NEO4J_PASSWORD = None

# 教师密码
TEACHER_PASSWORD = "admin888"

# 全局缓存的Neo4j驱动（避免重复创建连接）
_cached_driver = None

def get_neo4j_driver():
    """获取Neo4j连接（使用缓存避免重复连接）"""
    global _cached_driver
    
    # 云端部署时跳过Neo4j
    if not HAS_NEO4J or not NEO4J_URI:
        return None
    
    # 如果已有缓存的driver，直接返回
    if _cached_driver is not None:
        try:
            # 验证连接是否仍然有效
            _cached_driver.verify_connectivity()
            return _cached_driver
        except:
            # 连接失效，重新创建
            try:
                _cached_driver.close()
            except:
                pass
            _cached_driver = None
    
    # 创建新的driver
    try:
        _cached_driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            max_connection_lifetime=300,  # 5分钟
            connection_timeout=10,
            max_connection_pool_size=10
        )
        return _cached_driver
    except Exception as e:
        print(f"Neo4j连接创建失败: {e}")
        return None

# 全局变量：标记Neo4j是否可用
_neo4j_available = None

def check_neo4j_available():
    """检查Neo4j是否可用"""
    global _neo4j_available
    if _neo4j_available is not None:
        return _neo4j_available
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            session.run("RETURN 1")
        # 不关闭driver，保持连接池复用
        _neo4j_available = True
    except:
        _neo4j_available = False
    return _neo4j_available

def register_student(student_id, student_name):
    """注册或更新学生信息"""
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            session.run("""
                MERGE (s:yzbx_Student {student_id: $student_id})
                SET s.name = $name,
                    s.last_login = datetime(),
                    s.login_count = COALESCE(s.login_count, 0) + 1
            """, student_id=student_id, name=student_name)
        
        # 不关闭driver，保持连接池复用
    except Exception as e:
        print(f"Neo4j连接失败，跳过学生注册: {e}")
        pass

def log_activity(student_id, activity_type, module_name, content_id=None, content_name=None, details=None):
    """记录学生学习活动"""
    # 如果Neo4j不可用，直接跳过
    if not check_neo4j_available():
        return
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            session.run("""
                MERGE (s:yzbx_Student {student_id: $student_id})
                CREATE (a:yzbx_Activity {
                    id: randomUUID(),
                    type: $activity_type,
                    module: $module_name,
                    content_id: $content_id,
                    content_name: $content_name,
                    details: $details,
                    timestamp: datetime()
                })
                CREATE (s)-[:PERFORMED]->(a)
            """, student_id=student_id, activity_type=activity_type, 
                module_name=module_name, content_id=content_id,
                content_name=content_name, details=details)
    except Exception as e:
        pass

def get_all_students():
    """获取所有学生列表"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run("""
                MATCH (s:yzbx_Student)
                OPTIONAL MATCH (s)-[:PERFORMED]->(a:yzbx_Activity)
                RETURN s.student_id as student_id, 
                       s.name as name,
                       s.last_login as last_login,
                       s.login_count as login_count,
                       count(a) as activity_count
                ORDER BY s.last_login DESC
            """)
            
            students = [dict(record) for record in result]
        
        return students
    except:
        return []

def get_student_activities(student_id=None, module=None, limit=100):
    """获取学生活动记录"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            query = """
                MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
                WHERE 1=1
            """
            params = {"limit": limit}
            
            if student_id:
                query += " AND s.student_id = $student_id"
                params["student_id"] = student_id
            
            if module:
                query += " AND a.module = $module"
                params["module"] = module
            
            query += """
                RETURN s.student_id as student_id,
                       s.name as student_name,
                       a.type as activity_type,
                       a.module as module,
                       a.content_id as content_id,
                       a.content_name as content_name,
                       a.details as details,
                       a.timestamp as timestamp
                ORDER BY a.timestamp DESC
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            activities = [dict(record) for record in result]
        
        return activities
    except:
        return []

def get_module_statistics():
    """获取各模块使用统计"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 获取每个模块的详细统计
            result = session.run("""
                MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
                WITH a.module as module, 
                     count(a) as total_activities,
                     count(DISTINCT s) as unique_students,
                     collect(DISTINCT s.student_id) as student_ids
                OPTIONAL MATCH (a2:yzbx_Activity {module: module})
                WHERE date(a2.timestamp) = date()
                WITH module, total_activities, unique_students, student_ids, count(a2) as today_count
                RETURN module, total_activities, unique_students, today_count
                ORDER BY total_activities DESC
            """)
            
            stats = [dict(record) for record in result]
        
        return stats
    except:
        return []

def get_single_module_statistics(module_name):
    """获取单个模块的详细统计"""
    if not check_neo4j_available():
        return {
            'module': module_name,
            'total_visits': 0,
            'unique_students': 0,
            'avg_visits_per_student': 0,
            'recent_7d_visits': 0
        }
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 总访问次数和学生数
            result = session.run("""
                MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity {module: $module})
                RETURN count(a) as total_activities,
                       count(DISTINCT s) as unique_students
            """, module=module_name)
            
            record = result.single()
            total_activities = record['total_activities'] if record else 0
            unique_students = record['unique_students'] if record else 0
            
            # 计算人均访问次数
            avg_visits = round(total_activities / unique_students, 1) if unique_students > 0 else 0
            
            # 近7天访问
            result = session.run("""
                MATCH (a:yzbx_Activity {module: $module})
                WHERE a.timestamp > datetime() - duration('P7D')
                RETURN count(a) as recent_count
            """, module=module_name)
            
            record = result.single()
            recent_count = record['recent_count'] if record else 0
        
        return {
            'module': module_name,
            'total_visits': total_activities,
            'unique_students': unique_students,
            'avg_visits_per_student': avg_visits,
            'recent_7d_visits': recent_count
        }
    except Exception as e:
        print(f"获取模块统计失败 {module_name}: {e}")
        return {
            'module': module_name,
            'total_visits': 0,
            'unique_students': 0,
            'avg_visits_per_student': 0,
            'recent_7d_visits': 0
        }

def delete_student_data(student_id):
    """删除学生及其所有活动数据"""
    if not check_neo4j_available():
        return
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 删除活动记录
            session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})-[:PERFORMED]->(a:yzbx_Activity)
                DETACH DELETE a
            """, student_id=student_id)
            
            # 删除学生节点
            session.run("""
                MATCH (s:yzbx_Student {student_id: $student_id})
                DETACH DELETE s
            """, student_id=student_id)
    except:
        pass

def delete_all_activities():
    """删除所有活动记录"""
    if not check_neo4j_available():
        return
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            session.run("MATCH (a:yzbx_Activity) DETACH DELETE a")
    except:
        pass

def render_login_page():
    """渲染登录页面"""
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1>🦷 牙周病学自适应学习系统</h1>
        <p style="font-size: 1.2em; color: #666;">请选择您的身份登录</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        login_type = st.radio("选择身份", ["学生", "教师"], horizontal=True)
        
        st.markdown("---")
        
        if login_type == "学生":
            st.subheader("🎓 学生登录")
            student_input = st.text_input("学号或姓名", placeholder="请输入学号或姓名")
            
            if st.button("登录", type="primary", use_container_width=True):
                if student_input:
                    # 使用输入作为学生ID和姓名
                    student_id = student_input
                    student_name = student_input
                    
                    # 保存到session（不连接数据库，直接登录）
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = 'student'
                    st.session_state['student_id'] = student_id
                    st.session_state['student_name'] = student_name
                    
                    st.success(f"欢迎，{student_name}！")
                    st.rerun()
                else:
                    st.error("请输入学号或姓名")
        
        else:  # 教师登录
            st.subheader("👨‍🏫 教师登录")
            password = st.text_input("密码", type="password", placeholder="请输入教师密码")
            
            if st.button("登录", type="primary", use_container_width=True):
                if password == TEACHER_PASSWORD:
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = 'teacher'
                    st.session_state['teacher_name'] = "教师"
                    
                    st.success("教师登录成功！")
                    st.rerun()
                else:
                    st.error("密码错误")

def check_login():
    """检查用户是否已登录"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """获取当前用户信息"""
    if st.session_state.get('user_role') == 'student':
        return {
            'role': 'student',
            'student_id': st.session_state.get('student_id'),
            'name': st.session_state.get('student_name')
        }
    elif st.session_state.get('user_role') == 'teacher':
        return {
            'role': 'teacher',
            'name': st.session_state.get('teacher_name', '教师')
        }
    return None

def logout():
    """登出 - 清除所有session状态"""
    # 清除所有session_state，确保完全登出
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        del st.session_state[key]
    
    # 重置Neo4j可用性检查
    global _neo4j_available
    _neo4j_available = None
