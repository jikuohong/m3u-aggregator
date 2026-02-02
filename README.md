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

支持本地源（路由器 / 局域网）# m3u-aggregator

> IPTV 聚合工具，自动抓取多个 M3U 源，分类整理频道，支持长期订阅与多种订阅模式。

---

## 功能概览

- 从多源 M3U 订阅抓取频道
- 自动合并同名频道（仅对 CCTV 系列进行标准化，如 CCTV1 / CCTV-1 / CCTV1高清 → CCTV-1，CCTV-5+ 保留特殊处理）
- 自动去除不可长期订阅的频道（GEO 限制 / 广告站 / 特定关键词）
- 支持失败源管理（连续 5 次失败自动跳过）
- 自动分类分组：
  - 中国大陆：央视、卫视、体育、新闻、影视、综艺、其他
  - 中国香港：综合、新闻、影视、体育、综艺
  - 中国台湾：综合、新闻、影视、体育、综艺
  - 国际频道：综合、新闻、影视、体育、音乐、游戏
- 三种订阅模式：
  - `Full`：全部频道
  - `Lite`：仅核心频道（央视 + 卫视 + 港台综合）
  - `CCTV+卫视`：仅央视和卫视频道
- 输出两种格式：`.m3u` 与 `.txt`
- 提供 Flask API：
  - `/full.m3u`、`/lite.m3u`、`/cctv.m3u`  
  - `/status`：查看频道数量、源状态  
  - `/rebuild`：手动重建订阅
- Docker 化，支持单容器部署，一键运行
- 配合 OpenWRT 或计划任务，可实现每日自动更新

---

## 文件结构

m3u-aggregator/
├─ config/
│  └─ m3u-sources.txt   # M3U 源列表 (URL + 区域)
├─ output/
│  ├─ iptv_full.m3u
│  ├─ iptv_lite.m3u
│  ├─ iptv_cctv_ws.m3u
│  ├─ fail.db           # 失败源数据库
│  └─ *.txt             # 对应 TXT 输出
├─ merge.py             # 核心生成脚本
├─ docker-compose.yml
├─ Dockerfile
└─ README.md
安装与运行
1. 克隆仓库
git clone https://github.com/jikuohong/m3u-aggregator.git
cd m3u-aggregator
2. 编辑 M3U 源
在 config/m3u-sources.txt 中添加你的源，每行格式：

<URL> <区域>
示例：

https://epg.pw/test_channels.m3u 中国大陆
http://go8.myartsonline.com/zx/0/港澳4Gtv.txt 中国香港
https://iptv-org.github.io/iptv/countries/tw.m3u 中国台湾
3. 启动容器
docker compose up -d
首次启动会自动生成 .m3u 和 .txt 文件。

4. 访问订阅
Full      : http://<HOST>:50087/full.m3u
Lite      : http://<HOST>:50087/lite.m3u
CCTV+卫视 : http://<HOST>:50087/cctv.m3u
Status    : http://<HOST>:50087/status
Rebuild   : http://<HOST>:50087/rebuild
Flask API
路径	功能
/full.m3u	获取 Full 订阅
/lite.m3u	获取 Lite 订阅
/cctv.m3u	获取 CCTV+卫视 订阅
/status	查看源状态、频道数量、失败源统计
/rebuild	手动触发订阅重建
频道管理
标准化 CCTV 名称：CCTV1 / CCTV-1 / CCTV1高清 → CCTV-1

保留特殊：CCTV-5+

自动剔除 GEO / 广告频道，包含关键词：

geo, block, restricted, 版权, 地区, 区域, 仅限, 海外, 港澳限定, 台灣限定
失败源管理：连续 5 次失败自动跳过

输出说明
所有输出保存在 output/：

.m3u：标准 IPTV 订阅

.txt：频道名 + URL，对应 .m3u 内容

排序规则：

CCTV 固定顺序

其他按照分组 + 字母顺序

中国大陆其他频道放最后

定时更新
可通过 OpenWRT 计划任务 或 Linux cron 每日重启容器，实现每日自动更新。

Flask API /rebuild 可随时触发重建

Docker Compose 示例
version: "3"
services:
  m3u-flask:
    container_name: m3u-flask
    image: python:3.11-slim
    volumes:
      - ./config:/iptv/config
      - ./output:/iptv/output
    working_dir: /iptv
    command: python3 merge.py
    ports:
      - "50087:50087"
注意事项
确保 M3U 源可以被容器网络访问，海外源可能存在延迟或 GEO 限制。

merge.py 会自动管理失败源，减少无效请求。

建议在 config/m3u-sources.txt 中避免重复源，以提高效率。

CCTV-5+ 为特殊处理频道，保持不被标准化。

License
MIT License

⚡ 本项目仅用于个人 IPTV 订阅整理学习使用，请勿用于商业分发。

如果你觉得这个项目对你有帮助：

⭐ Star 一下

🍴 Fork 自用

🐛 提 Issue / PR 一起完善
