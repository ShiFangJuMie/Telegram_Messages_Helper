FROM python:3.9-alpine

# 设置python环境变量，不生成pyc文件，不缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 复制文件到容器的/app目录
COPY app /app
RUN chmod +x /app/entrypoint.sh

# 安装python依赖
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 添加环境变量
ENV PATH="/usr/local/bin:$PATH"

# 启动应用
CMD ["sh", "/app/entrypoint.sh"]