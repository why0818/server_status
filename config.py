# config.py
"""配置文件"""

import os
from datetime import datetime, timedelta

# Streamlit配置
STREAMLIT_CONFIG = {
    "page_title": "服务器状态监控",
    "layout": "wide",
    "page_icon": "📊"
}

# 数据配置
DATA_DIR = "monitor_data"
HISTORY_FILE = os.path.join(DATA_DIR, "usage_history.json")
USER_STATS_FILE = os.path.join(DATA_DIR, "user_stats.json")

# 监控路径
MONITOR_PATHS = ["/data01", "/data02", "/home", "/"]

# 数据保留时间
DATA_RETENTION_DAYS = 30

# 刷新间隔（秒）
REFRESH_INTERVAL = 30