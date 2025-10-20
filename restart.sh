#!/bin/bash

# Streamlit应用重启脚本

echo "=================================="
echo "🔄 Streamlit应用重启脚本"
echo "=================================="

# 先停止应用
echo "1. 停止当前运行的应用..."
if [ -f "streamlit.pid" ]; then
    ./stop.sh
    if [ $? -eq 0 ]; then
        echo "✅ 应用已停止"
    else
        echo "⚠️ 停止应用时出现问题"
    fi
else
    echo "ℹ️ 应用未运行"
fi

# 等待几秒确保完全停止
echo "2. 等待应用完全停止..."
sleep 1

# 启动应用
echo "3. 启动应用..."
./start.sh

if [ $? -eq 0 ]; then
    echo "✅ 应用重启成功!"
    
    # 显示最新的日志文件
    LATEST_LOG=$(ls app_*.log 2>/dev/null | sort | tail -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo "📝 最新日志文件: $LATEST_LOG"
    fi
    
else
    echo "❌ 应用重启失败!"
    exit 1
fi

echo "=================================="
echo "重启完成!"
echo "=================================="