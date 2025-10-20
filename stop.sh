#!/bin/bash

# Streamlit应用停止脚本

PID_FILE="streamlit.pid"
LOG_FILE="streamlit_app.log"

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "应用未运行或PID文件不存在"
    exit 1
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ps -p "$PID" > /dev/null; then
    echo "正在停止Streamlit应用 (PID: $PID)..."
    
    # 优雅地停止进程
    kill "$PID"
    
    # 等待进程结束
    TIMEOUT=30
    COUNT=0
    
    while ps -p "$PID" > /dev/null && [ $COUNT -lt $TIMEOUT ]; do
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    if ps -p "$PID" > /dev/null; then
        echo "进程未正常退出，强制终止..."
        kill -9 "$PID"
    fi
    
    # 清理文件
    rm -f "$PID_FILE"
    
    echo "Streamlit应用已停止"
else
    echo "进程不存在 (PID: $PID)"
    rm -f "$PID_FILE"
fi