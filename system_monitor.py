# system_monitor.py
"""系统监控模块"""

import subprocess
import psutil
import streamlit as st
from datetime import datetime
from config import MONITOR_PATHS
import getpass
import time
import json
import os

class SystemMonitor:
    """系统监控类"""
    
    # 磁盘缓存文件
    DISK_CACHE_FILE = "disk_cache.json"
    CACHE_EXPIRY_SECONDS = 300  # 5分钟缓存
    
    @staticmethod
    def _load_disk_cache():
        """加载磁盘缓存"""
        try:
            if os.path.exists(SystemMonitor.DISK_CACHE_FILE):
                with open(SystemMonitor.DISK_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    # 检查缓存是否过期
                    cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01T00:00:00'))
                    if (datetime.now() - cache_time).total_seconds() < SystemMonitor.CACHE_EXPIRY_SECONDS:
                        return cache_data.get('disk_data', {})
        except Exception:
            pass
        return None
    
    @staticmethod
    def _save_disk_cache(disk_data):
        """保存磁盘缓存"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'disk_data': disk_data
            }
            with open(SystemMonitor.DISK_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
        except Exception:
            pass
    
    @staticmethod
    def get_disk_usage(path):
        """获取磁盘使用情况"""
        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total // (1024**3),  # GB
                'used': usage.used // (1024**3),
                'free': usage.free // (1024**3),
                'percent': usage.percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_gpu_processes():
        """获取使用GPU的进程信息"""
        try:
            start_time = time.time()
            
            # 检查 nvidia-smi 是否可用
            result = subprocess.run(['which', 'nvidia-smi'], capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return []
            
            # 增加超时时间到10秒
            result = subprocess.run(
                ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory,gpu_uuid', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=10
            )
            
            end_time = time.time()
            
            if st.session_state.get('show_debug', False):
                st.sidebar.write(f"GPU进程查询耗时: {end_time - start_time:.2f}s")
                st.sidebar.write(f"进程查询返回码: {result.returncode}")
                if result.stdout:
                    st.sidebar.write(f"进程查询输出行数: {len(result.stdout.strip().split(chr(10)))}")
            
            if result.returncode != 0:
                return []
            
            gpu_processes = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('No running processes found'):
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        pid = parts[0]
                        process_name = parts[1]
                        used_memory = parts[2]
                        gpu_uuid = parts[3]
                        
                        try:
                            process = psutil.Process(int(pid))
                            username = process.username()
                            cmdline = ' '.join(process.cmdline()) if process.cmdline() else process_name
                            create_time = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')
                        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                            username = "unknown"
                            cmdline = process_name
                            create_time = "unknown"
                        except Exception:
                            username = "unknown"
                            cmdline = process_name
                            create_time = "unknown"
                        
                        gpu_processes.append({
                            'pid': pid,
                            'process_name': process_name,
                            'used_memory': used_memory,
                            'gpu_uuid': gpu_uuid,
                            'username': username,
                            'cmdline': cmdline,
                            'start_time': create_time
                        })
            
            return gpu_processes
        except subprocess.TimeoutExpired:
            if st.session_state.get('show_debug', False):
                st.sidebar.warning("GPU进程查询超时(10秒)")
            return []
        except FileNotFoundError:
            return []
        except Exception as e:
            if st.session_state.get('show_debug', False):
                st.sidebar.warning(f"GPU进程查询异常: {str(e)[:100]}")
            return []
    
    @staticmethod
    def get_gpu_info():
        """获取GPU信息"""
        try:
            start_time = time.time()
            
            # 检查 nvidia-smi 是否可用
            which_result = subprocess.run(['which', 'nvidia-smi'], capture_output=True, text=True, timeout=3)
            if which_result.returncode != 0:
                return [{'error': 'nvidia-smi not found in PATH'}]
            
            # 测试基本 nvidia-smi 命令
            test_result = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True, timeout=5)
            if test_result.returncode != 0:
                return [{'error': f'nvidia-smi test failed'}]
            
            # 执行查询命令 - 增加超时时间到15秒
            query_result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=15
            )
            
            end_time = time.time()
            
            # 调试信息
            if st.session_state.get('show_debug', False):
                st.sidebar.write(f"GPU信息查询耗时: {end_time - start_time:.2f}s")
                st.sidebar.write(f"查询返回码: {query_result.returncode}")
                if query_result.stdout:
                    st.sidebar.write(f"查询输出: {query_result.stdout[:200]}")
            
            if query_result.returncode != 0:
                error_msg = query_result.stderr[:200] if query_result.stderr else "Unknown error"
                return [{'error': f'nvidia-smi query failed: {error_msg}'}]
            
            # 解析输出
            gpus = []
            lines = query_result.stdout.strip().split('\n')
            
            if st.session_state.get('show_debug', False):
                st.sidebar.write(f"解析行数: {len(lines)}")
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                parts = [part.strip() for part in line.split(',')]
                if st.session_state.get('show_debug', False):
                    st.sidebar.write(f"第{i}行数据: {line}")
                    
                if len(parts) >= 6:
                    try:
                        gpus.append({
                            'id': int(parts[0]),
                            'name': parts[1],
                            'temp': int(parts[2]),
                            'util': int(parts[3]),
                            'mem_used': int(parts[4]) // 1024,
                            'mem_total': int(parts[5]) // 1024
                        })
                    except ValueError as e:
                        if st.session_state.get('show_debug', False):
                            st.sidebar.warning(f"解析第{i}行时出错: {line}, 错误: {str(e)}")
                        continue
            
            if not gpus:
                if st.session_state.get('show_debug', False):
                    st.sidebar.warning(f"未解析到GPU数据，原始输出: {query_result.stdout[:300]}")
                return [{'error': 'no gpus parsed'}]
                
            return gpus
        except subprocess.TimeoutExpired:
            if st.session_state.get('show_debug', False):
                st.sidebar.warning("GPU信息查询超时(15秒)")
            return [{'error': 'timeout - nvidia-smi took too long'}]
        except FileNotFoundError:
            return [{'error': 'nvidia-smi command not found'}]
        except Exception as e:
            if st.session_state.get('show_debug', False):
                st.sidebar.warning(f"GPU信息查询异常: {str(e)}")
            return [{'error': f'exception in get_gpu_info: {str(e)}'}]
    
    @staticmethod
    def get_cpu_info():
        """快速获取CPU信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            return cpu_percent, cpu_count, cpu_count_logical
        except Exception as e:
            if st.session_state.get('show_debug', False):
                st.sidebar.warning(f"获取CPU信息失败: {str(e)}")
            return 0, 0, 0
    
    @staticmethod
    def collect_current_data(use_disk_cache=True):
        """收集当前系统数据"""
        timestamp = datetime.now().isoformat()
        
        start_time = time.time()
        
        # 收集GPU数据
        gpus = SystemMonitor.get_gpu_info()
        gpu_data = []
        
        if len(gpus) > 0 and 'error' not in gpus[0]:
            for gpu in gpus:
                if 'id' in gpu:  # 确保是有效数据
                    gpu_data.append({
                        'id': gpu['id'],
                        'util': gpu['util'],
                        'temp': gpu['temp'],
                        'mem_used': gpu['mem_used'],
                        'mem_total': gpu['mem_total']
                    })
        else:
            # 显示具体错误信息
            if gpus and len(gpus) > 0 and 'error' in gpus[0]:
                if st.session_state.get('show_debug', False):
                    st.sidebar.warning(f"GPU错误详情: {gpus[0]['error']}")
        
        # 快速收集CPU数据
        cpu_percent, cpu_count, cpu_count_logical = SystemMonitor.get_cpu_info()
        
        # 收集磁盘数据（支持缓存）
        disk_data = {}
        if use_disk_cache:
            # 尝试从缓存加载
            cached_disk_data = SystemMonitor._load_disk_cache()
            if cached_disk_data:
                disk_data = cached_disk_data
            else:
                # 缓存未命中，重新收集并保存
                for path in MONITOR_PATHS:
                    info = SystemMonitor.get_disk_usage(path)
                    if 'error' not in info:
                        disk_data[path] = {
                            'percent': info['percent'],
                            'used': info['used'],
                            'total': info['total']
                        }
                # 保存到缓存
                SystemMonitor._save_disk_cache(disk_data)
        else:
            # 强制刷新磁盘数据
            for path in MONITOR_PATHS:
                info = SystemMonitor.get_disk_usage(path)
                if 'error' not in info:
                    disk_data[path] = {
                        'percent': info['percent'],
                        'used': info['used'],
                        'total': info['total']
                    }
            # 保存到缓存
            SystemMonitor._save_disk_cache(disk_data)
        
        # 获取GPU进程信息用于用户检测
        gpu_processes = SystemMonitor.get_gpu_processes()
        
        # 自动检测使用GPU的用户
        gpu_users = list(set([proc.get('username', 'unknown') for proc in gpu_processes if proc.get('username')]))
        if gpu_users and 'unknown' not in gpu_users:
            active_users = ', '.join(gpu_users)
        else:
            active_users = getpass.getuser()
        
        end_time = time.time()
        if st.session_state.get('show_debug', False):
            st.sidebar.caption(f"总数据收集耗时: {end_time - start_time:.2f}秒")
        
        data = {
            'timestamp': timestamp,
            'user': active_users,
            'gpu': gpu_data,
            'gpu_processes': gpu_processes,
            'cpu': {
                'util': cpu_percent,
                'physical_cores': cpu_count,
                'logical_cores': cpu_count_logical
            },
            'disk': disk_data
        }
        
        return data