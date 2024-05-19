FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y vim cron

# 设置工作目录
WORKDIR /app

# 复制文件到容器的/app目录
COPY app /app
RUN chmod +x /app/entrypoint.sh

# 安装python依赖
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 添加cron任务，每天0点运行cleanup.py脚本
RUN echo "0 0 * * * python /app/cleanup.py >> /var/log/cleanup.log 2>&1" | crontab -

# 启动应用
CMD ["bash", "/app/entrypoint.sh"]