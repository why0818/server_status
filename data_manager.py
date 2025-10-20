# data_manager.py
"""数据管理模块"""

import json
import os
from datetime import datetime, timedelta
import streamlit as st
from config import DATA_DIR, HISTORY_FILE, USER_STATS_FILE, DATA_RETENTION_DAYS

class DataManager:
    """数据管理类"""
    
    @staticmethod
    def init_data_dir():
        """初始化数据目录"""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    @staticmethod
    def save_history_data(data):
        """保存历史数据"""
        try:
            DataManager.init_data_dir()
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(data)
            
            # 只保留最近指定天数的数据
            cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
            history = [record for record in history 
                      if datetime.fromisoformat(record['timestamp']) > cutoff_date]
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            st.warning(f"保存历史数据失败: {e}")
    
    @staticmethod
    def load_history_data():
        """加载历史数据"""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            st.warning(f"加载历史数据失败: {e}")
            return []
    
    @staticmethod
    def save_user_stats(stats):
        """保存用户统计"""
        try:
            DataManager.init_data_dir()
            with open(USER_STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            st.warning(f"保存用户统计失败: {e}")
    
    @staticmethod
    def load_user_stats():
        """加载用户统计"""
        try:
            if os.path.exists(USER_STATS_FILE):
                with open(USER_STATS_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.warning(f"加载用户统计失败: {e}")
            return {}