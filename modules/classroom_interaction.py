"""
课中互动模块
实时弹幕互动与AI总结
"""

import streamlit as st
from datetime import datetime
from openai import OpenAI
from streamlit_autorefresh import st_autorefresh
from config.settings import *

def check_neo4j_available():
    """检查Neo4j是否可用"""
    from modules.auth import check_neo4j_available as auth_check
    return auth_check()

def get_neo4j_driver():
    """获取Neo4j连接（复用auth模块的缓存连接）"""
    from modules.auth import get_neo4j_driver as auth_get_driver
    return auth_get_driver()

def get_current_student():
    """获取当前学生信息"""
    if st.session_state.get('user_role') == 'student':
        return st.session_state.get('student_id')
    return None

def log_interaction_activity(activity_type, content_id=None, content_name=None, details=None):
    """记录课中互动活动"""
    student_id = get_current_student()
    if not student_id:
        return
    
    from modules.auth import log_activity
    log_activity(
        student_id=student_id,
        activity_type=activity_type,
        module_name="课中互动",
        content_id=content_id,
        content_name=content_name,
        details=details
    )

def create_question(question_text):
    """教师创建问题"""
    if not check_neo4j_available():
        return None
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # 先关闭所有活跃问题
            session.run("MATCH (q:yzbx_Question {status: 'active'}) SET q.status = 'closed'")
            
            # 创建新问题
            result = session.run("""
                CREATE (q:yzbx_Question {
                    id: randomUUID(),
                    text: $text,
                    created_at: datetime(),
                    status: 'active'
                })
                RETURN q.id as id
            """, text=question_text)
            
            question_id = result.single()['id']
        
        return question_id
    except Exception:
        return None

def get_active_question():
    """获取当前活跃问题"""
    if not check_neo4j_available():
        return None
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run("""
                MATCH (q:yzbx_Question {status: 'active'})
                RETURN q.id as id, q.text as text, q.created_at as created_at
                ORDER BY q.created_at DESC
                LIMIT 1
            """)
            
            record = result.single()
            question = dict(record) if record else None
        
        return question
    except Exception:
        return None

def submit_reply(question_id, student_name, content):
    """学生提交回复"""
    if not check_neo4j_available():
        return
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            session.run("""
                MATCH (q:yzbx_Question {id: $question_id})
                MERGE (s:yzbx_Student {name: $student_name})
                CREATE (s)-[:REPLIED {
                    content: $content,
                    timestamp: datetime(),
                    length: size($content)
                }]->(q)
            """, question_id=question_id, student_name=student_name, content=content)
    except Exception:
        pass

def get_recent_replies(question_id, limit=20):
    """获取最新回复"""
    if not check_neo4j_available():
        return []
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run("""
                MATCH (s:yzbx_Student)-[r:REPLIED]->(q:yzbx_Question {id: $question_id})
                RETURN s.name as student_name, r.content as content, r.timestamp as timestamp
                ORDER BY r.timestamp DESC
                LIMIT $limit
            """, question_id=question_id, limit=limit)
            
            replies = [dict(record) for record in result]
        
        return replies
    except Exception:
        return []

def summarize_replies_with_ai(question_text, replies):
    """使用AI总结学生回复"""
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    
    replies_text = '\n'.join([f"- {r['content']}" for r in replies])
    
    prompt = f"""
课堂问题：{question_text}

学生回复（共{len(replies)}条）：
{replies_text}

请完成以下任务：
1. **核心观点总结**：归纳学生回复中的主要观点（分点列出）
2. **正确理解**：指出哪些回复体现了对知识点的正确理解
3. **常见误区**：识别学生的误解或知识盲点
4. **补充说明**：针对学生的理解，给出教师应补充的要点

请用简洁、专业的语言，帮助教师快速掌握学生的学习情况。
"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    
    return response.choices[0].message.content

def render_classroom_interaction():
    """渲染课中互动页面"""
    st.title("💬 课中互动")
    
    # 记录进入课中互动
    log_interaction_activity("进入模块", details="访问课中互动")
    
    # 根据登录角色自动选择
    user_role = st.session_state.get('user_role', 'student')
    
    if user_role == "teacher":
        role = "教师"
    else:
        role = st.radio("选择角色", ["学生", "教师"], horizontal=True)
    
    if role == "教师":
        st.subheader("📝 教师端")
        
        # 发布问题
        question = st.text_area("输入课堂问题")
        if st.button("发布提问"):
            if question:
                question_id = create_question(question)
                st.success("✅ 问题已发布！")
                st.rerun()
            else:
                st.warning("请输入问题内容")
        
        # 显示当前问题和回复
        current_q = get_active_question()
        if current_q:
            st.divider()
            st.markdown(f"### 当前问题")
            st.info(current_q['text'])
            
            # 自动刷新
            count = st_autorefresh(interval=3000, key="teacher_refresh")
            
            st.markdown("### 学生回复（实时弹幕）")
            replies = get_recent_replies(current_q['id'])
            
            if replies:
                for reply in replies:
                    timestamp = reply['timestamp'].strftime("%H:%M:%S") if hasattr(reply['timestamp'], 'strftime') else str(reply['timestamp'])
                    st.markdown(f"""
                    <div style="background: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 5px;">
                        <strong>{reply['student_name']}</strong>: {reply['content']}
                        <span style="float: right; color: gray; font-size: 0.9em;">{timestamp}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # AI总结
                st.divider()
                if st.button("🤖 AI总结回复"):
                    with st.spinner("AI正在分析..."):
                        try:
                            summary = summarize_replies_with_ai(current_q['text'], replies)
                            st.markdown("### AI总结")
                            st.success(summary)
                        except Exception as e:
                            st.error(f"AI总结失败: {str(e)}")
            else:
                st.info("暂无学生回复")
        else:
            st.info("当前没有活跃的问题")
    
    else:  # 学生端
        st.subheader("✍️ 学生端")
        
        # 使用登录的学生姓名
        student_name = st.session_state.get('student_name', '')
        if not student_name:
            student_name = st.text_input("📝 输入你的姓名", value="", placeholder="请输入姓名后才能参与互动")
            if student_name:
                st.session_state['student_name'] = student_name
        else:
            st.success(f"👋 欢迎, {student_name}!")
        
        # 显示当前问题
        current_q = get_active_question()
        if current_q:
            st.markdown("### 📢 当前问题")
            st.info(current_q['text'])
            
            # 回答问题 - 使用text_area更醒目
            st.markdown("### ✍️ 你的回答")
            answer = st.text_area(
                "输入你对这个问题的理解和回答", 
                height=100,
                placeholder="请在这里输入你的回答，然后点击提交按钮...",
                key="student_answer"
            )
            
            if st.button("📤 提交回答", type="primary"):
                if answer and student_name:
                    submit_reply(current_q['id'], student_name, answer)
                    # 记录回答活动
                    log_interaction_activity("提交回答", content_id=current_q['id'], 
                                           content_name=current_q['text'][:30], 
                                           details=f"回答内容: {answer[:50]}")
                    st.success("✅ 回答已提交！")
                    st.rerun()
                elif not student_name:
                    st.warning("⚠️ 请先在上方输入姓名")
                else:
                    st.warning("⚠️ 请输入回答内容")
            
            # 自动刷新显示其他同学的回复
            count = st_autorefresh(interval=3000, key="student_refresh")
            
            st.divider()
            st.markdown("### 💬 同学们的回复")
            replies = get_recent_replies(current_q['id'], limit=10)
            
            if replies:
                for reply in replies:
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 3px solid #4ECDC4;">
                        <strong>{reply['student_name']}</strong>: {reply['content']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无同学回复，快来做第一个回答者吧！")
        else:
            st.warning("📭 当前没有活跃的问题，请等待老师发布问题")
            
            # 提供模拟问题供练习
            st.markdown("---")
            st.markdown("### 💡 练习模式")
            st.markdown("当老师还没有发布问题时，你可以先练习回答以下问题：")
            
            practice_questions = [
                "牙周病的主要致病因素是什么？",
                "慢性牙周炎和侵袭性牙周炎的区别是什么？",
                "牙周基础治疗包括哪些内容？"
            ]
            
            selected_practice = st.selectbox("选择练习题目", practice_questions)
            
            practice_answer = st.text_area(
                "练习回答",
                height=80,
                placeholder="输入你的练习回答...",
                key="practice_answer"
            )
            
            if st.button("💾 保存练习"):
                if practice_answer:
                    log_interaction_activity("练习回答", content_name=selected_practice[:30], 
                                           details=f"练习内容: {practice_answer[:50]}")
                    st.success("✅ 练习已保存！")
                else:
                    st.warning("请输入练习内容")
