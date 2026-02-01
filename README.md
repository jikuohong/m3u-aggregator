📺 IPTV Merge Flask

单容器 · 自动更新 · 长期可订阅 IPTV 聚合服务

一个面向 TVBox / Kodi / Apple TV / iOS / Android 的
IPTV 订阅聚合、清洗、分类、排序、长期可用解决方案

✨ 项目简介

IPTV Merge Flask 是一个 基于 Python + Flask 的单容器 IPTV 聚合服务，用于：

聚合多个 IPTV / M3U / TXT 订阅源

自动去重、合并同名频道

剔除失效源与 GEO / 版权限制频道

自动分类分组 + 稳定排序

输出 长期不变的订阅地址

📌 目标只有一个：一键运行，长期订阅，不用天天修源

🚀 核心特性一览
✅ 单容器架构

无需多容器

无需数据库

Docker 一键运行

适合 OpenWrt / NAS / VPS

🔗 多源聚合

支持 M3U / M3U8 / TXT

支持 IPv4 / IPv6 / 混合源

支持本地源（路由器 / 局域网）

♻️ 同名频道自动合并

以 (分组 + 频道名) 为唯一键

同名频道只显示一次

内部保留 多条播放地址（多源）

客户端自动切换，稳定性更高

🧹 失败源自动剔除

拉取失败自动计数

连续 3 次失败的源自动剔除

剔除状态持久化（重启不丢失）

保证订阅长期干净稳定

🌍 GEO / 版权限制频道清理

自动删除以下频道：

实际访问失败的频道

频道名包含：

geo

blocked

地区限制

仅限

版权

unavailable

📌 确保 不会出现“刚订阅就大量失效”

📂 自动分组体系
🇨🇳 中国大陆

📺 央视（CCTV，固定顺序）

🛰️ 卫视

📰 新闻

🏀 体育

🎭 综艺

🎬 影视

🎮 游戏 / 电竞

📍 浙江地方频道

📦 其他（始终排在最后）

CCTV-1 ～ CCTV-15 顺序固定，永不乱序

🇭🇰 中国香港

综合

新闻

影视

体育

综艺

🇹🇼 中国台湾

综合

新闻

影视

体育

综艺

🌍 国际频道

新闻

体育

综合

影视

音乐

📊 排序与体验优化

分组顺序 完全可控

CCTV 固定顺序

同分组频道名称排序

不依赖原始源顺序

所有客户端显示一致

⏰ 自动更新机制

启动即生成一次 iptv.m3u

每日凌晨 2 点自动更新

更新过程 无需重启容器

订阅地址始终不变

🌐 订阅输出
📡 HTTP 订阅地址
http://服务器IP:50087/iptv.m3u


✔ 支持：

TVBox

Kodi

Apple TV（iPlayTV / APTV）

iOS / Android IPTV 客户端

🐳 Docker 部署
1️⃣ 目录结构
m3u-aggregator/
├── Dockerfile
├── docker-compose.yml
├── merge.py
├── config/
│   ├── sources.txt
│   └── blacklist.json
└── output/
    └── iptv.m3u

2️⃣ docker-compose.yml（示例）
services:
  iptv:
    build: .
    container_name: iptv-merge
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./config:/iptv/config
      - ./output:/iptv/output

3️⃣ 启动服务
docker compose up -d


Full 订阅 → http://<HOST_IP>:3566/full.m3u

Lite 订阅 → http://<HOST_IP>:3566/lite.m3u

CCTV+卫视 → http://<HOST_IP>:3566/cctv.m3u

📦 订阅源配置

编辑：

config/sources.txt


支持：

HTTP / HTTPS

M3U / TXT

🧠 适合人群

想要 长期可用 IPTV 订阅

不想每天修源、换链接

TVBox / Apple TV / 家庭 IPTV 用户

OpenWrt / Docker / NAS 玩家

⚠️ 免责声明

本项目仅用于 学习与技术研究

IPTV 内容版权归原始提供方所有

请在法律允许范围内使用

⭐ 推荐

如果你觉得这个项目对你有帮助：

⭐ Star 一下

🍴 Fork 自用

🐛 提 Issue / PR 一起完善
