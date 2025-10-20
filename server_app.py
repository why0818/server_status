# server_app.py
"""应用主类"""

import streamlit as st
from system_monitor import SystemMonitor
from data_manager import DataManager
from page_renderer import PageRenderer
from config import STREAMLIT_CONFIG

class ServerMonitorApp:
    """服务器监控应用主类"""
    
    def __init__(self):
        """初始化应用"""
        self._setup_sidebar()
    
    def _setup_sidebar(self):
        """设置侧边栏"""
        st.sidebar.title("导航")
        self.page = st.sidebar.radio("选择页面", [
            "当前状态", 
            "存储状态",
            "日视图", 
            "周视图"
        ])
        
        # 系统信息
        st.sidebar.subheader("系统信息")
        st.sidebar.info("用户自动检测")
        st.sidebar.caption("通过GPU进程自动识别用户")
        
        # 调试开关
        if st.sidebar.checkbox("显示调试信息"):
            st.session_state.show_debug = True
        else:
            st.session_state.show_debug = False
    
    def run(self):
        """运行应用"""
        st.set_page_config(**STREAMLIT_CONFIG)
        st.title("📊 服务器状态监控与分析")
        
        # 收集当前数据（自动检测用户）
        current_data = SystemMonitor.collect_current_data()
        
        # 保存当前数据到历史记录
        DataManager.save_history_data(current_data)
        
        # 根据页面选择渲染对应内容
        if self.page == "当前状态":
            PageRenderer.render_current_status(current_data)
        elif self.page == "存储状态":
            PageRenderer.render_storage_status()
        elif self.page == "日视图":
            PageRenderer.render_daily_view()
        elif self.page == "周视图":
            PageRenderer.render_weekly_view()