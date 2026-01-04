"""
牙周病学自适应学习系统 - 主应用
"""

import streamlit as st
import random
from modules.case_library import render_case_library
from modules.knowledge_graph import render_knowledge_graph
from modules.ability_recommender import render_ability_recommender
from modules.classroom_interaction import render_classroom_interaction
from modules.auth import render_login_page, check_login, get_current_user, logout
from modules.analytics import render_analytics_dashboard, render_module_analytics

# 页面配置
st.set_page_config(
    page_title="牙周病学自适应学习系统",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 高端现代化主题CSS
st.markdown("""
<style>
    /* 导入Google字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 全局字体 */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 隐藏Streamlit加载时的半透明蒙版 */
    div[data-testid="stAppViewBlockContainer"] > div:first-child > div:first-child {
        background: transparent !important;
    }
    
    /* 隐藏加载遮罩 */
    .stApp > div:first-child > div:first-child > div > div[style*="opacity"] {
        opacity: 1 !important;
    }
    
    /* 禁用加载动画的半透明效果 */
    [data-testid="stAppViewContainer"] > section > div {
        opacity: 1 !important;
        transition: none !important;
    }
    
    /* 禁用所有过渡动画减少闪烁 */
    * {
        transition: none !important;
        animation: none !important;
        animation-duration: 0s !important;
    }
    
    /* 禁止边框闪烁 */
    .stMetric, .stDataFrame, div[data-testid="stMetricValue"],
    div[data-testid="stDataFrame"], .stPlotlyChart {
        animation: none !important;
        border: none !important;
        outline: none !important;
    }
    
    /* 禁止图表容器边框动画 */
    .js-plotly-plot, .plotly, .plot-container {
        animation: none !important;
        transition: none !important;
    }
    
    /* 隐藏Streamlit的状态指示器 */
    .stStatusWidget,
    div[data-testid="stStatusWidget"],
    .stSpinner,
    .stProgress {
        display: none !important;
    }
    
    /* 禁止容器透明度变化 */
    .element-container,
    .stMarkdown,
    .stSelectbox,
    .stTabs {
        opacity: 1 !important;
    }
    
    /* 浅色渐变背景 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 50%, #f0f2f5 100%);
        min-height: 100vh;
    }
    
    /* 隐藏默认侧边栏 */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* 玻璃态效果容器 */
    .glass-container {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        padding: 30px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
    }
    
    /* 顶部导航栏 */
    .top-nav {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: none;
        padding: 15px 30px;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Logo区域 */
    .logo-section {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .logo-icon {
        font-size: 40px;
    }
    
    .logo-text {
        font-size: 24px;
        font-weight: 700;
        color: #fff;
        letter-spacing: -0.5px;
    }
    
    .logo-subtitle {
        font-size: 11px;
        color: rgba(255,255,255,0.8);
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* 用户信息 */
    .user-info {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 20px;
        background: rgba(255,255,255,0.2);
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(255,255,255,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    
    .user-name {
        color: #fff;
        font-weight: 500;
    }
    
    .user-role {
        color: rgba(255,255,255,0.8);
        font-size: 12px;
    }
    
    /* 功能卡片 */
    .feature-card {
        background: #fff;
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        padding: 30px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        height: 280px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        background: #fff;
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.25);
    }
    
    .feature-icon {
        font-size: 60px;
        margin-bottom: 20px;
        display: block;
    }
    
    .feature-title {
        color: #2d3748;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .feature-desc {
        color: #718096;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* 统计卡片 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: none;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .stat-number {
        font-size: 42px;
        font-weight: 700;
        color: #fff;
    }
    
    .stat-label {
        color: rgba(255,255,255,0.9);
        font-size: 14px;
        margin-top: 8px;
    }
    
    /* 页面标题 */
    .page-title {
        font-size: 32px;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .page-subtitle {
        color: #718096;
        font-size: 16px;
        margin-bottom: 30px;
    }
    
    /* 渐变文字 */
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 导航按钮样式 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
        font-size: 12px;
        white-space: nowrap;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }
    
    /* 输入框样式 - 完全覆盖所有边框 */
    .stTextInput>div>div>input, 
    .stTextInput>div>div>input:focus,
    .stTextInput>div>div>input:active,
    .stTextInput>div>div>input:focus-visible,
    .stTextArea>div>div>textarea,
    .stTextArea>div>div>textarea:focus,
    .stTextArea>div>div>textarea:active,
    .stTextArea>div>div>textarea:focus-visible {
        background: #fff !important;
        border: 2px solid #667eea !important;
        border-radius: 12px !important;
        color: #2d3748 !important;
        padding: 15px !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 未选中状态的边框 */
    .stTextInput>div>div>input:not(:focus),
    .stTextArea>div>div>textarea:not(:focus) {
        border: 2px solid rgba(102, 126, 234, 0.3) !important;
    }
    
    /* 移除所有可能的外层容器边框 */
    .stTextInput>div,
    .stTextInput>div>div,
    .stTextArea>div,
    .stTextArea>div>div {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 选择框样式 */
    .stSelectbox>div>div {
        background: #fff;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Radio按钮样式 */
    .stRadio>div {
        background: rgba(255,255,255,0.8);
        border-radius: 12px;
        padding: 15px;
    }
    
    .stRadio>div>div>label {
        color: #2d3748 !important;
    }
    
    /* 指标卡片 */
    [data-testid="metric-container"] {
        background: #fff;
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
    }
    
    [data-testid="metric-container"] label {
        color: #718096 !important;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #2d3748 !important;
    }
    
    /* 扩展器样式 */
    .streamlit-expanderHeader {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        color: #2d3748 !important;
    }
    
    /* 分隔线 */
    hr {
        border-color: rgba(102, 126, 234, 0.2);
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        padding: 5px;
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #718096;
        border-radius: 8px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff !important;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    /* 成功/警告/错误消息 */
    .stSuccess {
        background: rgba(46, 204, 113, 0.2) !important;
        border: 1px solid rgba(46, 204, 113, 0.5) !important;
        color: #2ecc71 !important;
        border-radius: 12px;
    }
    
    .stWarning {
        background: rgba(241, 196, 15, 0.2) !important;
        border: 1px solid rgba(241, 196, 15, 0.5) !important;
        color: #f1c40f !important;
        border-radius: 12px;
    }
    
    .stError {
        background: rgba(231, 76, 60, 0.2) !important;
        border: 1px solid rgba(231, 76, 60, 0.5) !important;
        color: #e74c3c !important;
        border-radius: 12px;
    }
    
    .stInfo {
        background: rgba(102, 126, 234, 0.2) !important;
        border: 1px solid rgba(102, 126, 234, 0.5) !important;
        color: #a8c0ff !important;
        border-radius: 12px;
    }
    
    /* Markdown文字颜色 */
    .stMarkdown p, .stMarkdown li {
        color: #4a5568;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #2d3748;
    }
    
    /* 隐藏Streamlit默认页脚 */
    footer {visibility: hidden;}
    
    /* 隐藏菜单按钮 */
    #MainMenu {visibility: hidden;}
    
    /* 隐藏顶部装饰线 */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* 欢迎横幅 */
    .welcome-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: none;
        padding: 40px;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .welcome-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .welcome-title {
        font-size: 32px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 10px;
    }
    
    .welcome-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 16px;
    }
    
    /* 动画效果 */
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
    
    /* 发光效果 */
    .glow {
        box-shadow: 0 0 40px rgba(102, 126, 234, 0.3);
    }
    
    /* 返回按钮 */
    .back-btn {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 10px;
        padding: 8px 20px;
        color: #667eea;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .back-btn:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    /* 模块页面标题 */
    .module-header {
        background: #fff;
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        padding: 20px 30px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
    }
    
    .module-title {
        font-size: 28px;
        font-weight: 700;
        color: #2d3748;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    /* 底部信息 */
    .footer-info {
        text-align: center;
        color: #718096;
        font-size: 12px;
        margin-top: 50px;
        padding: 20px;
    }
    
    /* Slider 样式 - 固定高度防止行距变化 */
    .stSlider [data-baseweb="slider"] {
        background: rgba(102, 126, 234, 0.2);
    }
    
    .stSlider {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    .stSlider > div {
        padding-top: 0 !important;
    }
    
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        display: none !important;
    }
    
    /* 能力选择区域固定行高 */
    [data-testid="column"] {
        min-height: auto !important;
    }
    
    /* DataFrame 样式 */
    .stDataFrame {
        background: #fff;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* 进度条 */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 检查登录状态
    if not check_login():
        render_login_page()
        return
    
    # 获取当前用户
    user = get_current_user()
    
    # 顶部导航栏
    st.markdown(f"""
    <div class="top-nav">
        <div class="logo-section">
            <span class="logo-icon">🦷</span>
            <div>
                <div class="logo-text">牙周病学自适应学习系统</div>
                <div class="logo-subtitle">PERIODONTAL AI LEARNING PLATFORM</div>
            </div>
        </div>
        <div class="user-info">
            <div class="user-avatar">{'👨‍🎓' if user['role'] == 'student' else '👨‍🏫'}</div>
            <div>
                <div class="user-name">{user.get('name', '教师')}</div>
                <div class="user-role">{'学生' if user['role'] == 'student' else '教师'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化当前页面状态
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # 导航按钮行
    if user['role'] == 'teacher':
        nav_cols = st.columns([1, 1, 1, 1, 1, 1, 1])
        with nav_cols[0]:
            if st.button("🏠 首页", key="nav_home_t", use_container_width=True):
                st.session_state.current_page = 'home'
        with nav_cols[1]:
            if st.button("📚 病例库数据", key="nav_case_t", use_container_width=True):
                st.session_state.current_page = 'case_analytics'
        with nav_cols[2]:
            if st.button("🗺️ 图谱数据", key="nav_graph_t", use_container_width=True):
                st.session_state.current_page = 'graph_analytics'
        with nav_cols[3]:
            if st.button("🎯 推荐数据", key="nav_ability_t", use_container_width=True):
                st.session_state.current_page = 'ability_analytics'
        with nav_cols[4]:
            if st.button("💬 互动数据", key="nav_int_t", use_container_width=True):
                st.session_state.current_page = 'interaction_analytics'
        with nav_cols[5]:
            if st.button("⚙️ 系统设置", key="nav_settings_t", use_container_width=True):
                st.session_state.current_page = 'system_settings'
        with nav_cols[6]:
            if st.button("🚪 退出登录", key="nav_logout_t", use_container_width=True):
                logout()
                st.rerun()
    else:
        nav_cols = st.columns([1, 1, 1, 1, 1, 1])
        with nav_cols[0]:
            if st.button("🏠 首页", key="nav_home", use_container_width=True):
                st.session_state.current_page = 'home'
        with nav_cols[1]:
            if st.button("📚 病例库", key="nav_case", use_container_width=True):
                st.session_state.current_page = 'case_library'
        with nav_cols[2]:
            if st.button("🗺️ 知识图谱", key="nav_graph", use_container_width=True):
                st.session_state.current_page = 'knowledge_graph'
        with nav_cols[3]:
            if st.button("🎯 能力推荐", key="nav_ability", use_container_width=True):
                st.session_state.current_page = 'ability_recommender'
        with nav_cols[4]:
            if st.button("💬 课中互动", key="nav_int", use_container_width=True):
                st.session_state.current_page = 'classroom'
        with nav_cols[5]:
            if st.button("🚪 退出登录", key="nav_logout", use_container_width=True):
                logout()
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 根据当前页面渲染内容
    current = st.session_state.current_page
    
    # 使用错误处理防止页面卡住
    try:
        # 教师端和学生端分开处理
        if user['role'] == 'teacher':
            # 教师端直接显示数据概览
            if current == 'home':
                render_teacher_dashboard()
            elif current == 'case_analytics':
                render_module_analytics("病例库")
            elif current == 'graph_analytics':
                render_module_analytics("知识图谱")
            elif current == 'ability_analytics':
                render_module_analytics("能力推荐")
            elif current == 'interaction_analytics':
                render_module_analytics("课中互动")
            elif current == 'system_settings':
                render_system_settings()
            else:
                render_teacher_dashboard()
        else:
            # 学生端
            if current == 'home':
                render_home_page(user)
            elif current == 'case_library':
                render_case_library()
            elif current == 'knowledge_graph':
                render_knowledge_graph()
            elif current == 'ability_recommender':
                render_ability_recommender()
            elif current == 'classroom':
                render_classroom_interaction()
            else:
                render_home_page(user)
    except Exception as e:
        st.error(f"⚠️ 页面加载出错：{str(e)}")
        st.info("请点击顶部导航按钮返回首页，或点击下方按钮重新尝试")
        if st.button("🏠 返回首页", type="primary"):
            st.session_state.current_page = 'home'
            st.rerun()

def render_teacher_dashboard():
    """渲染教师端数据概览首页"""
    import pandas as pd
    import plotly.express as px
    from modules.analytics import get_activity_summary, get_daily_activity_trend
    from modules.auth import check_neo4j_available, get_all_students
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 16px; margin-bottom: 30px;">
        <h2 style="margin: 0; color: white;">📊 教学数据概览</h2>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
            实时查看学生学习情况，掌握教学效果
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取真实数据
    has_neo4j = check_neo4j_available()
    
    # 获取数据
    summary = get_activity_summary()
    all_students = get_all_students() if has_neo4j else []
    
    # 计算统计数据
    total_students = summary.get('total_students', 0)
    today_active = summary.get('today_activities', 0)
    active_7d = summary.get('active_students', 0)
    total_acts = summary.get('total_activities', 0)
    
    # 调试信息（可以在终端看到）
    print(f"[教师端调试] Neo4j可用: {has_neo4j}")
    print(f"[教师端调试] 学生总数: {total_students}, 今日活跃: {today_active}, 7日活跃: {active_7d}, 总活动: {total_acts}")
    
    # 只在真正无数据时提示（避免本地开发时误报）
    if total_students == 0 and not has_neo4j:
        st.info("💡 提示：当前无学生数据。学生登录使用后即可在此查看学习统计。")
    
    # 核心数据指标 - 使用真实数据
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("👥 学生总数", str(total_students))
    with col2:
        st.metric("📚 今日活跃", str(today_active))
    with col3:
        st.metric("👨‍🎓 7日活跃学生", str(active_7d))
    with col4:
        if has_neo4j:
            completion_rate = int((active_7d / total_students * 100)) if total_students > 0 else 0
            st.metric("✅ 7日活跃率", f"{completion_rate}%")
        else:
            st.metric("✅ 7日活跃率", "0%")
    with col5:
        st.metric("📝 总学习记录", str(total_acts))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 四个模块数据概览 - 调用真实数据
    st.markdown("### 📈 各模块学习数据")
    
    modules = ["病例库", "知识图谱", "能力推荐", "课中互动"]
    module_cols = st.columns(4)
    
    if has_neo4j:
        from modules.auth import get_single_module_statistics
        
    for i, module in enumerate(modules):
        with module_cols[i]:
            if has_neo4j:
                stats = get_single_module_statistics(module)
                visit_count = stats.get('total_visits', 0)
                student_count = stats.get('unique_students', 0)
                completion = int((student_count / total_students * 100)) if total_students > 0 else 0
                print(f"[教师端调试] {module}: 访问{visit_count}次, 学生{student_count}人, 参与率{completion}%")
            else:
                visit_count = 0
                completion = 0
                print(f"[教师端调试] {module}: Neo4j不可用，显示0")
                
            st.markdown(f"""
            <div style="background: #fff; border-radius: 12px; padding: 20px; 
                        border: 1px solid rgba(102,126,234,0.2); text-align: center;">
                <h4 style="color: #667eea; margin-bottom: 15px;">{module}</h4>
                <div style="font-size: 24px; font-weight: 600; color: #333;">{visit_count}</div>
                <div style="color: #888; font-size: 13px;">学习人次</div>
                <hr style="margin: 15px 0; border: none; border-top: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span>学生参与率</span>
                    <span style="color: #667eea; font-weight: 600;">{completion}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 图表区域 - 使用真实数据
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 📊 近7天学习趋势")
        if has_neo4j:
            trend_data = get_daily_activity_trend(7)
            if trend_data:
                df = pd.DataFrame(trend_data)
                fig = px.line(df, x="date", y="count", markers=True, 
                            labels={"date": "日期", "count": "活动数"})
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无近7天数据")
        else:
            st.info("需要连接数据库查看趋势")
    
    with chart_col2:
        st.markdown("### 🥧 学生学习模块分布")
        if has_neo4j:
            # 统计每个模块的访问学生数
            module_data = []
            for module in modules:
                stats = get_single_module_statistics(module)
                module_data.append({
                    "模块": module,
                    "学生数": stats.get('unique_students', 0)
                })
            
            if any(m['学生数'] > 0 for m in module_data):
                progress_df = pd.DataFrame(module_data)
                fig = px.pie(progress_df, values="学生数", names="模块", 
                            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#4facfe'])
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无模块访问数据")
        else:
            st.info("需要连接数据库查看分布")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 学生排行榜 - 使用真实数据
    st.markdown("### 🏆 学习排行榜 (Top 10)")
    
    if has_neo4j:
        # 从数据库获取学生活动统计
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
                    LIMIT 10
                """)
                
                leaderboard = []
                for i, record in enumerate(result):
                    leaderboard.append({
                        "排名": "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else str(i+1))),
                        "学号": record['student_id'],
                        "姓名": record['name'] if record['name'] else "未设置",
                        "学习记录数": record['activity_count'],
                        "活跃天数": record['active_days']
                    })
                
                if leaderboard:
                    st.dataframe(pd.DataFrame(leaderboard), use_container_width=True, hide_index=True)
                else:
                    st.info("暂无学生学习数据")
        except Exception as e:
            st.error(f"获取排行榜数据失败: {e}")
    else:
        st.info("需要连接数据库查看学生排行榜")

def render_home_page(user):
    """渲染首页"""
    # 读取统计配置
    import json
    try:
        with open('config/stats_config.json', 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except:
        stats = {"case_count": 12, "knowledge_points": 45, "core_abilities": 10}
    
    # 欢迎横幅
    st.markdown(f"""
    <div class="welcome-banner">
        <div class="welcome-title">👋 欢迎回来，{user.get('name', '用户')}！</div>
        <div class="welcome-subtitle">今天想学习什么？选择下方功能模块开始你的学习之旅</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 统计卡片
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('case_count', 12)}</div>
            <div class="stat-label">📚 病例总数</div>
        </div>
        """, unsafe_allow_html=True)
    with stat_cols[1]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('knowledge_points', 45)}</div>
            <div class="stat-label">🧠 知识点</div>
        </div>
        """, unsafe_allow_html=True)
    with stat_cols[2]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('core_abilities', 10)}</div>
            <div class="stat-label">🎯 核心能力</div>
        </div>
        """, unsafe_allow_html=True)
    with stat_cols[3]:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">AI</div>
            <div class="stat-label">🤖 智能推荐</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 功能模块标题
    st.markdown("""
    <div class="page-title">
        <span>🚀</span> 
        <span class="gradient-text">功能模块</span>
    </div>
    <div class="page-subtitle">选择一个模块开始学习，AI将为你提供个性化的学习体验</div>
    """, unsafe_allow_html=True)
    
    # 功能模块卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card glow">
            <span class="feature-icon">📚</span>
            <div class="feature-title">智能病例库</div>
            <div class="feature-desc">真实临床病例学习<br>AI辅助诊断分析<br>掌握牙周病临床思维</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入病例库", key="btn_case", use_container_width=True):
            st.session_state.current_page = 'case_library'
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🗺️</span>
            <div class="feature-title">知识图谱</div>
            <div class="feature-desc">可视化知识网络<br>理清知识脉络<br>构建系统化知识体系</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入图谱", key="btn_graph", use_container_width=True):
            st.session_state.current_page = 'knowledge_graph'
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🎯</span>
            <div class="feature-title">AI能力推荐</div>
            <div class="feature-desc">基于能力自评<br>DeepSeek大模型<br>规划个性化学习路径</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入推荐", key="btn_ability", use_container_width=True):
            st.session_state.current_page = 'ability_recommender'
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">💬</span>
            <div class="feature-title">课中互动</div>
            <div class="feature-desc">实时投票弹幕<br>AI智能答疑<br>让课堂更加生动</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入互动", key="btn_class", use_container_width=True):
            st.session_state.current_page = 'classroom'
    
    # 技术栈展示
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="footer-info">
        <div style="margin-bottom: 15px;">
            <span style="padding: 8px 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border-radius: 20px; margin: 0 5px; display: inline-block;">🤖 DeepSeek AI</span>
            <span style="padding: 8px 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border-radius: 20px; margin: 0 5px; display: inline-block;">📊 Neo4j</span>
            <span style="padding: 8px 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border-radius: 20px; margin: 0 5px; display: inline-block;">🔍 Elasticsearch</span>
            <span style="padding: 8px 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border-radius: 20px; margin: 0 5px; display: inline-block;">⚡ Streamlit</span>
        </div>
        © 2026 牙周病学自适应学习系统 · Powered by AI Technology
    </div>
    """, unsafe_allow_html=True)

def render_module_analytics(module_name):
    """渲染教师端模块数据分析页面"""
    from modules.auth import check_neo4j_available, get_all_students, get_student_activities, get_single_module_statistics, get_neo4j_driver
    import pandas as pd
    
    has_neo4j = check_neo4j_available()
    
    # 调试信息面板
    with st.expander("🔧 调试信息（点击展开）", expanded=False):
        st.markdown("**连接状态检查：**")
        st.write(f"- Neo4j可用: `{has_neo4j}`")
        
        if has_neo4j:
            try:
                from modules.analytics import get_activity_summary
                summary = get_activity_summary()
                st.write(f"- 学生总数: `{summary.get('total_students', 0)}`")
                st.write(f"- 活动总数: `{summary.get('total_activities', 0)}`")
                
                all_students_debug = get_all_students()
                st.write(f"- get_all_students返回: `{len(all_students_debug)}` 条记录")
                
                stats = get_single_module_statistics(module_name)
                st.write(f"- {module_name}统计: `{stats}`")
            except Exception as e:
                st.error(f"查询出错: {e}")
        else:
            st.warning("Neo4j不可用，无法获取数据")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 16px; margin-bottom: 30px;">
        <h2 style="margin: 0; color: white;">📊 {module_name} - 数据分析</h2>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
            查看学生在该模块的学习情况和整体数据统计
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 选项卡：个人数据 / 整体数据
    tab1, tab2 = st.tabs(["👤 学生个人数据", "📈 整体统计数据"])
    
    with tab1:
        st.markdown("### 🔍 查询学生学习数据")
        
        # 获取真实学生列表
        all_students = get_all_students() if has_neo4j else []
        if not all_students:
            st.info("💡 当前暂无学生数据。学生注册登录后，数据会自动显示在此处。")
            # 不要return，让tab2可以继续显示
        else:
            student_options = {f"{s['student_id']} - {s.get('name', '未设置姓名')}": s['student_id'] 
                              for s in all_students}
            
            selected_display = st.selectbox("选择学生", list(student_options.keys()), key=f"select_{module_name}")
            selected_student_id = student_options[selected_display]
            
            if selected_student_id:
                # 获取该学生在该模块的活动记录
                activities = get_student_activities(selected_student_id, module_name)
            
                st.markdown(f"#### {selected_display.split(' - ')[1]} 的{module_name}学习数据")
                
                # 统计数据
                total_activities = len(activities)
                unique_days = len(set(a['date'] for a in activities)) if activities else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("学习记录数", str(total_activities))
                with col2:
                    st.metric("活跃天数", str(unique_days))
                with col3:
                    avg_per_day = round(total_activities / unique_days, 1) if unique_days > 0 else 0
                    st.metric("日均记录数", str(avg_per_day))
                
                # 学习记录列表
                if activities:
                    st.markdown("##### 📋 最近学习记录 (最新10条)")
                    records = []
                    for act in activities[:10]:
                        records.append({
                            "时间": act['timestamp'],
                            "活动类型": act['activity_type'],
                            "内容": act.get('content_name', '-'),
                            "详情": act.get('details', '-')
                        })
                    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
                else:
                    st.info(f"该学生暂无{module_name}学习记录")
    
    with tab2:
        st.markdown("### 📊 整体统计数据")
        
        # 获取模块统计数据
        stats = get_single_module_statistics(module_name)
        
        # 整体统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats.get('unique_students', 0)}</div>
                <div class="stat-label">👥 学习学生数</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_visits', 0)}</div>
                <div class="stat-label">📝 总访问次数</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats.get('avg_visits_per_student', 0)}</div>
                <div class="stat-label">📊 人均访问次数</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats.get('recent_7d_visits', 0)}</div>
                <div class="stat-label">🔥 近7日访问</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 显示活跃学生排行
        st.markdown(f"#### 🏆 {module_name}学习排行榜")
        try:
            driver = get_neo4j_driver()
            with driver.session() as session:
                result = session.run("""
                    MATCH (s:yzbx_Student)-[:PERFORMED]->(a:yzbx_Activity)
                    WHERE a.module_name = $module_name
                    RETURN s.student_id as student_id, 
                           s.name as name,
                           count(a) as activity_count
                    ORDER BY activity_count DESC
                    LIMIT 10
                """, module_name=module_name)
                
                ranking = []
                for i, record in enumerate(result):
                    ranking.append({
                        "排名": "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else str(i+1))),
                        "学号": record['student_id'],
                        "姓名": record['name'] if record['name'] else "未设置",
                        "学习记录数": record['activity_count']
                    })
                
                if ranking:
                    st.dataframe(pd.DataFrame(ranking), use_container_width=True, hide_index=True)
                else:
                    st.info(f"暂无{module_name}学习数据")
        except Exception as e:
            st.error(f"获取排行数据失败: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 图表展示
        import plotly.express as px
        import pandas as pd
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("##### 📈 近7天学习人数趋势")
            dates = [f"01-{i:02d}" for i in range(1, 8)]
            counts = [random.randint(20, 50) for _ in range(7)]
            df = pd.DataFrame({"日期": dates, "学习人数": counts})
            fig = px.line(df, x="日期", y="学习人数", markers=True)
            fig.update_traces(line_color='#667eea')
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            st.markdown("##### 🥧 学习进度分布")
            progress_data = pd.DataFrame({
                "进度": ["未开始", "进行中", "已完成"],
                "人数": [random.randint(10, 30), random.randint(40, 80), random.randint(50, 100)]
            })
            fig = px.pie(progress_data, values="人数", names="进度", 
                        color_discrete_sequence=['#e8eaf6', '#667eea', '#764ba2'])
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # 学生排行榜
        st.markdown("##### 🏆 学习排行榜 (Top 10)")
        leaderboard = []
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "郑九", "王十"]
        for i, name in enumerate(names):
            leaderboard.append({
                "排名": f"🥇" if i == 0 else (f"🥈" if i == 1 else (f"🥉" if i == 2 else f"{i+1}")),
                "学生": name,
                "学习时长(分)": random.randint(100, 300) - i * 15,
                "完成进度": f"{95 - i * 5}%",
                "正确率": f"{92 - i * 3}%"
            })
        st.dataframe(pd.DataFrame(leaderboard), use_container_width=True, hide_index=True)

def render_system_settings():
    """渲染系统设置页面（仅教师可用）"""
    st.title("⚙️ 系统设置")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 30px;">
        <h3 style="margin: 0; color: white;">📊 首页统计数据设置</h3>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
            设置首页展示的统计数据，这些数据将显示给所有学生
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 读取当前配置
    import json
    try:
        with open('config/stats_config.json', 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except:
        stats = {"case_count": 12, "knowledge_points": 45, "core_abilities": 10}
    
    # 编辑表单
    with st.form("stats_form"):
        st.markdown("### 📝 编辑统计数据")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            case_count = st.number_input(
                "📚 病例总数", 
                min_value=0, 
                value=stats.get("case_count", 12),
                step=1,
                help="设置系统中的病例总数"
            )
        
        with col2:
            knowledge_points = st.number_input(
                "🧠 知识点数量", 
                min_value=0, 
                value=stats.get("knowledge_points", 45),
                step=1,
                help="设置系统中的知识点数量"
            )
        
        with col3:
            core_abilities = st.number_input(
                "🎯 核心能力数", 
                min_value=0, 
                value=stats.get("core_abilities", 10),
                step=1,
                help="设置系统中的核心能力数量"
            )
        
        submitted = st.form_submit_button("💾 保存设置", use_container_width=True, type="primary")
        
        if submitted:
            new_stats = {
                "case_count": int(case_count),
                "knowledge_points": int(knowledge_points),
                "core_abilities": int(core_abilities)
            }
            
            try:
                with open('config/stats_config.json', 'w', encoding='utf-8') as f:
                    json.dump(new_stats, f, ensure_ascii=False, indent=4)
                st.success("✅ 设置已保存！学生在首页将看到更新后的数据。")
            except Exception as e:
                st.error(f"❌ 保存失败：{str(e)}")
    
    # 当前设置预览
    st.markdown("---")
    st.markdown("### 👀 当前设置预览")
    
    preview_cols = st.columns(3)
    with preview_cols[0]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('case_count', 12)}</div>
            <div class="stat-label">📚 病例总数</div>
        </div>
        """, unsafe_allow_html=True)
    with preview_cols[1]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('knowledge_points', 45)}</div>
            <div class="stat-label">🧠 知识点</div>
        </div>
        """, unsafe_allow_html=True)
    with preview_cols[2]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('core_abilities', 10)}</div>
            <div class="stat-label">🎯 核心能力</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
