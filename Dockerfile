# 使用官方 Python 轻量镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /iptv

# 安装依赖
RUN pip install --no-cache-dir flask requests

# 复制配置和脚本
COPY config/ ./config/
COPY merge.py ./merge.py

# 输出目录
RUN mkdir -p ./output

# 暴露端口
EXPOSE 50087

# 启动 Flask
CMD ["python", "merge.py"]
