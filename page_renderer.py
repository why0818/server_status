# page_renderer.py
"""页面渲染模块"""

import streamlit as st
import psutil
import time
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from system_monitor import SystemMonitor
from data_analyzer import DataAnalyzer
from data_manager import DataManager
from config import MONITOR_PATHS, REFRESH_INTERVAL

class PageRenderer:
    """页面渲染类"""
    
    @staticmethod
    def render_current_status(current_data):
        """渲染当前状态页面"""
        st.header("🟢 当前状态")
        
        # GPU状态
        PageRenderer._render_gpu_status(current_data)
        
        # CPU状态
        PageRenderer._render_cpu_status()
        
        # 自动刷新
        PageRenderer._render_auto_refresh()
    
    @staticmethod
    def render_storage_status():
        """渲染存储状态页面"""
        st.header("💾 存储状态")
        
        # 磁盘使用情况
        PageRenderer._render_disk_usage()
        
        # 可以添加更多存储相关的信息
        st.info("📝 存储信息每5分钟自动刷新，或点击刷新按钮手动更新")
    
    @staticmethod
    def _render_disk_usage():
        """渲染磁盘使用情况"""
        st.subheader("💽 磁盘使用情况")
        
        # 添加手动刷新按钮
        if st.button("🔄 刷新存储信息", key="refresh_storage"):
            # 强制刷新磁盘数据
            st.session_state.force_disk_refresh = True
            st.rerun()
        
        # 获取磁盘数据
        disk_data = {}
        for path in MONITOR_PATHS:
            info = SystemMonitor.get_disk_usage(path)
            if 'error' not in info:
                disk_data[path] = {
                    'percent': info['percent'],
                    'used': info['used'],
                    'total': info['total']
                }
        
        # 显示磁盘信息
        cols = st.columns(len(MONITOR_PATHS))
        for i, path in enumerate(MONITOR_PATHS):
            with cols[i]:
                st.markdown(f"**`{path}`**")
                if path in disk_data:
                    info = disk_data[path]
                    st.metric("使用率", f"{info['percent']:.1f}%")
                    st.write(f"已用: {info['used']} GB / {info['total']} GB")
                    
                    # 添加进度条
                    st.progress(info['percent'] / 100)
                    
                    # 添加警告信息
                    if info['percent'] > 90:
                        st.error("⚠️ 空间不足")
                    elif info['percent'] > 80:
                        st.warning("⚠️ 空间紧张")
                else:
                    st.error("❌ 无法访问")
    
    @staticmethod
    def _render_gpu_status(current_data):
        """渲染GPU状态"""
        st.subheader("🎮 GPU 状态")
        
        gpus = SystemMonitor.get_gpu_info()
        
        if len(gpus) > 0 and 'error' not in gpus[0]:
            # 显示GPU基本信息
            cols = st.columns(min(len(gpus), 4))
            for i, gpu in enumerate(gpus):
                with cols[i % 4]:
                    with st.expander(f"GPU {gpu['id']} - {gpu['name']}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("利用率", f"{gpu['util']}%", "GPU-Util")
                        col2.metric("温度", f"{gpu['temp']}°C", "Temp")
                        col3.metric("显存", f"{gpu['mem_used']} / {gpu['mem_total']} GB", "Memory")
                        
                        # 进度条显示
                        st.progress(gpu['util'] / 100)
                        st.progress(gpu['mem_used'] / gpu['mem_total'] if gpu['mem_total'] > 0 else 0)
            
            # 显示正在使用GPU的用户和进程
            gpu_processes = current_data.get('gpu_processes', [])
            if gpu_processes:
                st.subheader("👥 当前使用GPU的用户和进程")
                
                # 准备详细信息
                detailed_processes = []
                for proc in gpu_processes:
                    # 获取工作目录（简化显示）
                    try:
                        if os.path.exists(f"/proc/{proc['pid']}/cwd"):
                            cwd = os.readlink(f"/proc/{proc['pid']}/cwd")
                            # 只显示最后两层目录
                            cwd_parts = cwd.split('/')
                            if len(cwd_parts) > 2:
                                short_cwd = '/'.join(cwd_parts[-2:])
                            else:
                                short_cwd = cwd
                        else:
                            short_cwd = "unknown"
                    except:
                        short_cwd = "unknown"
                    
                    detailed_processes.append({
                        '用户': proc.get('username', 'unknown'),
                        'PID': proc.get('pid', 'unknown'),
                        '工作目录': short_cwd,
                        '进程名': proc.get('process_name', 'unknown'),
                        '显存(MB)': proc.get('used_memory', 'unknown'),
                        '启动时间': proc.get('start_time', 'unknown'),
                        '脚本': (proc.get('cmdline', 'unknown')[:80] + '...') if len(proc.get('cmdline', '')) > 80 else proc.get('cmdline', 'unknown')
                    })
                
                process_df = pd.DataFrame(detailed_processes)
                st.dataframe(process_df, use_container_width=True, hide_index=True)
                
                # 显示用户统计
                users = list(set([proc.get('username', 'unknown') for proc in gpu_processes]))
                st.success(f"当前使用GPU的用户: {', '.join(users)}")
            else:
                st.info("当前没有进程使用GPU")
        else:
            # 显示调试信息
            if st.session_state.get('show_debug', False) and len(gpus) > 0:
                st.error(f"⚠️ 无法获取 GPU 信息: {gpus[0].get('error', 'Unknown error')}")
            else:
                st.error("⚠️ 无法获取 GPU 信息，请确认已安装 nvidia-smi")
    
    @staticmethod
    def _render_cpu_status():
        """渲染CPU状态"""
        st.subheader("⚙️ CPU 状态")
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU 使用率", f"{cpu_percent}%")
        col2.metric("物理核心数", cpu_count)
        col3.metric("逻辑核心数", cpu_count_logical)
        
        # CPU使用率进度条
        st.progress(cpu_percent / 100)
    
    @staticmethod
    def _render_auto_refresh():
        """渲染自动刷新"""
        st.write(f"🔄 页面每{REFRESH_INTERVAL}秒自动刷新...")
        time.sleep(REFRESH_INTERVAL)
        st.rerun()
    
    @staticmethod
    def render_daily_view():
        """渲染日视图页面"""
        st.header("📅 日视图")
        
        history_data = DataManager.load_history_data()
        
        if not history_data:
            st.warning("暂无历史数据")
            return
        
        # GPU利用率趋势图
        gpu_fig = DataAnalyzer.create_gpu_utilization_chart(history_data, days=1)
        if gpu_fig:
            st.plotly_chart(gpu_fig, use_container_width=True)
        else:
            st.warning("无法生成GPU趋势图")
        
        # CPU利用率趋势图
        cpu_fig = DataAnalyzer.create_cpu_utilization_chart(history_data, days=1)
        if cpu_fig:
            st.plotly_chart(cpu_fig, use_container_width=True)
        else:
            st.warning("无法生成CPU趋势图")
        
        # 用户使用统计
        PageRenderer._render_user_stats(history_data, period='daily', title="今日")
    
    @staticmethod
    def render_weekly_view():
        """渲染周视图页面"""
        st.header("📆 周视图")
        
        history_data = DataManager.load_history_data()
        
        if not history_data:
            st.warning("暂无历史数据")
            return
        
        # GPU利用率趋势图（最近7天）
        gpu_fig = DataAnalyzer.create_gpu_utilization_chart(history_data, days=7)
        if gpu_fig:
            st.plotly_chart(gpu_fig, use_container_width=True)
        else:
            st.warning("无法生成GPU趋势图")
        
        # CPU利用率趋势图（最近7天）
        cpu_fig = DataAnalyzer.create_cpu_utilization_chart(history_data, days=7)
        if cpu_fig:
            st.plotly_chart(cpu_fig, use_container_width=True)
        else:
            st.warning("无法生成CPU趋势图")
        
        # 用户使用统计
        PageRenderer._render_user_stats(history_data, period='weekly', title="本周")
        
        # 显示历史周统计
        PageRenderer._render_historical_weekly_stats(history_data)
    
    @staticmethod
    def _render_user_stats(history_data, period='daily', title=""):
        """渲染用户使用统计"""
        st.subheader(f"👥 用户使用统计 ({title})")
        user_stats = DataAnalyzer.create_user_usage_stats(history_data, period=period)
        if user_stats is not None and not user_stats.empty:
            # 筛选记录
            if period == 'daily':
                target_date = datetime.now().date()
                filtered_stats = user_stats[user_stats['period'] == target_date]
            else:  # weekly
                current_week = pd.Period(datetime.now(), 'W').start_time
                filtered_stats = user_stats[user_stats['period'] == current_week]
            
            if not filtered_stats.empty:
                # 按使用时长排序
                filtered_stats = filtered_stats.sort_values('usage_minutes', ascending=False)
                
                st.dataframe(filtered_stats[['user', 'avg_gpu_util', 'avg_cpu_util', 'usage_minutes']].rename(columns={
                    'user': '用户',
                    'avg_gpu_util': '平均GPU利用率(%)',
                    'avg_cpu_util': '平均CPU利用率(%)',
                    'usage_minutes': '使用时长(分钟)'
                }), hide_index=True)
                
                # 找出使用时间最长的用户
                top_user = filtered_stats.iloc[0]
                st.success(f"🏆 {title}使用时间最长用户: {top_user['user']} ({top_user['usage_minutes']:.1f} 分钟)")
            else:
                st.info(f"{title}暂无用户使用记录")
        else:
            st.warning("无法生成用户统计")
    
    @staticmethod
    def _render_historical_weekly_stats(history_data):
        """渲染历史周统计"""
        st.subheader("📊 历史周统计")
        user_stats = DataAnalyzer.create_user_usage_stats(history_data, period='weekly')
        if user_stats is not None and len(user_stats) > 1:
            # 按周期分组，找出每个周期使用时间最长的用户
            weekly_top_users = user_stats.loc[user_stats.groupby('period')['usage_minutes'].idxmax()]
            weekly_top_users = weekly_top_users.sort_values('period', ascending=False)
            
            st.dataframe(weekly_top_users[['period', 'user', 'usage_minutes']].rename(columns={
                'period': '周期',
                'user': '用户',
                'usage_minutes': '使用时长(分钟)'
            }), hide_index=True)