# data_analyzer.py
"""数据分析模块"""

import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import streamlit as st

class DataAnalyzer:
    """数据分析类"""
    
    @staticmethod
    def create_gpu_utilization_chart(history_data, days=7):
        """创建GPU利用率图表"""
        if not history_data:
            return None
        
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_data = [record for record in history_data 
                        if datetime.fromisoformat(record['timestamp']) > cutoff_date]
        
        if not filtered_data:
            return None
        
        # 准备数据
        chart_data = []
        for record in filtered_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            user = record.get('user', 'unknown')
            if 'gpu' in record:
                for gpu in record['gpu']:
                    chart_data.append({
                        'timestamp': timestamp,
                        'user': user,
                        'gpu_id': gpu['id'],
                        'utilization': gpu['util']
                    })
        
        if not chart_data:
            return None
        
        df = pd.DataFrame(chart_data)
        df['hour'] = df['timestamp'].dt.floor('H')
        
        # 按小时和GPU聚合数据
        hourly_data = df.groupby(['hour', 'gpu_id']).agg({
            'utilization': 'mean',
            'user': lambda x: x.value_counts().index[0] if len(x.value_counts()) > 0 else 'unknown'
        }).reset_index()
        
        fig = px.line(hourly_data, x='hour', y='utilization', color='gpu_id',
                      title=f'GPU利用率趋势 (最近{days}天)',
                      labels={'utilization': '利用率 (%)', 'hour': '时间', 'gpu_id': 'GPU ID'})
        fig.update_layout(height=400)
        
        return fig
    
    @staticmethod
    def create_cpu_utilization_chart(history_data, days=7):
        """创建CPU利用率图表"""
        if not history_data:
            return None
        
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_data = [record for record in history_data 
                        if datetime.fromisoformat(record['timestamp']) > cutoff_date]
        
        if not filtered_data:
            return None
        
        # 准备数据
        chart_data = []
        for record in filtered_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            user = record.get('user', 'unknown')
            if 'cpu' in record:
                chart_data.append({
                    'timestamp': timestamp,
                    'user': user,
                    'utilization': record['cpu']['util']
                })
        
        if not chart_data:
            return None
        
        df = pd.DataFrame(chart_data)
        df['hour'] = df['timestamp'].dt.floor('H')
        
        # 按小时聚合数据
        hourly_data = df.groupby(['hour']).agg({
            'utilization': 'mean',
            'user': lambda x: x.value_counts().index[0] if len(x.value_counts()) > 0 else 'unknown'
        }).reset_index()
        
        fig = px.line(hourly_data, x='hour', y='utilization',
                      title=f'CPU利用率趋势 (最近{days}天)',
                      labels={'utilization': '利用率 (%)', 'hour': '时间'})
        fig.update_layout(height=400)
        
        return fig
    
    @staticmethod
    def create_user_usage_stats(history_data, period='daily'):
        """创建用户使用统计"""
        if not history_data:
            return None
        
        df_data = []
        for record in history_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            user = record.get('user', 'unknown')
            
            # 计算GPU总利用率
            gpu_util = 0
            if 'gpu' in record:
                gpu_util = sum(gpu['util'] for gpu in record['gpu']) / len(record['gpu']) if record['gpu'] else 0
            
            df_data.append({
                'timestamp': timestamp,
                'user': user,
                'gpu_util': gpu_util,
                'cpu_util': record['cpu']['util'] if 'cpu' in record else 0
            })
        
        if not df_data:
            return None
        
        df = pd.DataFrame(df_data)
        
        if period == 'daily':
            df['period'] = df['timestamp'].dt.date
        else:  # weekly
            df['period'] = df['timestamp'].dt.to_period('W').apply(lambda x: x.start_time)
        
        # 计算每个用户在每个周期的平均使用率和使用时间
        user_stats = df.groupby(['period', 'user']).agg({
            'gpu_util': 'mean',
            'cpu_util': 'mean',
            'timestamp': ['count', 'min', 'max']
        }).reset_index()
        
        user_stats.columns = ['period', 'user', 'avg_gpu_util', 'avg_cpu_util', 'record_count', 'first_record', 'last_record']
        
        # 计算使用时长（分钟）
        user_stats['usage_minutes'] = (user_stats['last_record'] - user_stats['first_record']).dt.total_seconds() / 60
        
        return user_stats