#!/bin/bash

SESSION_FILE="/app/data/${TELEGRAM_SESSION}.session"

# 检查会话文件是否存在
if [ -f "$SESSION_FILE" ]; then
    echo "INFO - Session file found. Attempting to start the bot..."
    
    # 启动服务
    python /app/main.py &
    python /app/script_scheduler.py &
    python /app/app.py

    # 等待后台进程结束
    wait $!
    
    # 检查Python脚本的退出状态
    if [ $? -eq 0 ]; then
        echo "INFO - Bot stopped gracefully."
        exit 0
    else
        echo "WARNING - Bot failed to start or stopped with an error, entering wait mode..."
        # 如果Python脚本发生错误，进入等待状态.
        tail -f /dev/null
    fi
else
    echo "WARNING - Session file not found. Please complete the manual authentication process."
    echo "WARNING - COMMAND: docker exec -it telegram_messages_helper python /app/setup.py"
    # 如果会话文件不存在，也进入等待状态
    tail -f /dev/null
fi