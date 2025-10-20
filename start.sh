#!/bin/bash

# Streamlit应用启动脚本
# 端口: 8501
# 支持日期时间格式日志: app_20250917_201022.log

# 设置变量
APP_FILE="app.py"
PORT=8501
PID_FILE="streamlit.pid"
CONDA_ENV="unet-env"

# 生成带日期时间格式的日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="app_${TIMESTAMP}.log"

# 检查应用文件是否存在
if [ ! -f "$APP_FILE" ]; then
    echo "错误: 应用文件 $APP_FILE 不存在"
    exit 1
fi

# 检查conda是否可用
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda命令"
    exit 1
fi

# 检查conda环境是否存在
if ! conda env list | grep -q "^$CONDA_ENV "; then
    echo "错误: conda环境 '$CONDA_ENV' 不存在"
    echo "请先创建环境: conda create -n $CONDA_ENV python=3.8"
    exit 1
fi

# 检查是否已经运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "Streamlit应用已经在运行 (PID: $PID)"
        echo "日志文件: $(ls app_*.log 2>/dev/null | tail -1)"
        exit 1
    else
        # 清理旧的PID文件
        rm -f "$PID_FILE"
    fi
fi

# 启动Streamlit应用
echo "正在启动Streamlit应用..."
echo "应用文件: $APP_FILE"
echo "端口: $PORT"
echo "日志文件: $LOG_FILE"
echo "Conda环境: $CONDA_ENV"

# 使用conda环境启动应用
nohup bash -c "
    source \$(conda info --base)/etc/profile.d/conda.sh
    conda activate $CONDA_ENV
    streamlit run '$APP_FILE' \
        --server.port $PORT \
        --server.address 0.0.0.0
" > "$LOG_FILE" 2>&1 &

# 保存进程ID
echo $! > "$PID_FILE"

# 等待几秒检查是否启动成功
echo "等待应用启动..."
sleep 1

if ps -p $(cat "$PID_FILE") > /dev/null; then
    echo "✅ Streamlit应用启动成功!"
    echo "PID: $(cat "$PID_FILE")"
    echo "访问地址: http://localhost:$PORT"
    echo "日志文件: $LOG_FILE"
else
    echo "❌ 启动失败，请检查日志文件: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi