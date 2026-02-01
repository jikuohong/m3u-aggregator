#!/usr/bin/env python3
import os
import re
import time
import threading
from datetime import datetime, timedelta

import requests
from flask import Flask, Response

# ================== 基础路径 ==================
BASE = "/iptv"
SRC = f"{BASE}/config/m3u-sources.txt"
OUT = f"{BASE}/output/iptv.m3u"
FAIL_DB = f"{BASE}/output/fail.db"

FAIL_LIMIT = 3
TIMEOUT = 8

app = Flask(__name__)

# ================== GEO 屏蔽关键词 ==================
GEO_KEYWORDS = [
    "geo", "blocked", "限制", "仅限", "地区", "region",
    "版权", "not available", "unavailable"
]

# ================== 失败源管理 ==================
def load_db():
    if not os.path.exists(FAIL_DB):
        return {}
    db = {}
    with open(FAIL_DB) as f:
        for line in f:
            if "|" in line:
                k, v = line.strip().split("|", 1)
                db[k] = int(v)
    return db

def save_db(db):
    with open(FAIL_DB, "w") as f:
        for k, v in db.items():
            f.write(f"{k}|{v}\n")

fail_db = load_db()

# ================== 分组顺序 ==================
GROUP_ORDER = {
    "中国大陆 | 央视": 1,
    "中国大陆 | 卫视": 2,
    "中国大陆 | 综艺": 3,
    "中国大陆 | 新闻": 4,
    "中国大陆 | 体育": 5,
    "中国大陆 | 影视": 6,
    "中国大陆 | 浙江": 7,
    "中国大陆 | 游戏": 8,
    "中国大陆 | 其他": 99,

    "中国香港 | 综合": 20,
    "中国香港 | 新闻": 21,
    "中国香港 | 影视": 22,
    "中国香港 | 体育": 23,
    "中国香港 | 综艺": 24,

    "中国台湾 | 综合": 30,
    "中国台湾 | 新闻": 31,
    "中国台湾 | 影视": 32,
    "中国台湾 | 体育": 33,
    "中国台湾 | 综艺": 34,

    "国际频道 | 新闻": 40,
    "国际频道 | 体育": 41,
    "国际频道 | 综合": 42,
    "国际频道 | 影视": 43,
    "国际频道 | 音乐": 44,
}

CCTV_ORDER = [
    "CCTV-1","CCTV-2","CCTV-3","CCTV-4","CCTV-5","CCTV-6",
    "CCTV-7","CCTV-8","CCTV-9","CCTV-10","CCTV-11",
    "CCTV-12","CCTV-13","CCTV-14","CCTV-15"
]

# ================== 分组识别 ==================
def detect_group(region, name):
    n = name.lower()

    if region == "中国大陆":
        if "cctv" in n:
            if "体育" in name or "5" in n:
                return "中国大陆 | 体育"
            if "新闻" in name:
                return "中国大陆 | 新闻"
            return "中国大陆 | 央视"
        if "卫视" in name:
            return "中国大陆 | 卫视"
        if any(x in name for x in ["浙江", "杭州", "宁波", "温州"]):
            return "中国大陆 | 浙江"
        if any(x in name for x in ["游戏", "电竞"]):
            return "中国大陆 | 游戏"
        if "综艺" in name:
            return "中国大陆 | 综艺"
        if "新闻" in name:
            return "中国大陆 | 新闻"
        if "体育" in name:
            return "中国大陆 | 体育"
        if any(x in name for x in ["电影", "影视"]):
            return "中国大陆 | 影视"
        return "中国大陆 | 其他"

    if region == "中国香港":
        if "新闻" in name:
            return "中国香港 | 新闻"
        if "体育" in n:
            return "中国香港 | 体育"
        if any(x in name for x in ["电影", "影视"]):
            return "中国香港 | 影视"
        if "综艺" in name:
            return "中国香港 | 综艺"
        return "中国香港 | 综合"

    if region == "中国台湾":
        if "新闻" in name:
            return "中国台湾 | 新闻"
        if "体育" in n:
            return "中国台湾 | 体育"
        if any(x in name for x in ["电影", "影视"]):
            return "中国台湾 | 影视"
        if "综艺" in name:
            return "中国台湾 | 综艺"
        return "中国台湾 | 综合"

    if region == "国际频道":
        if "sport" in n:
            return "国际频道 | 体育"
        if "music" in n:
            return "国际频道 | 音乐"
        if any(x in n for x in ["movie", "film"]):
            return "国际频道 | 影视"
        return "国际频道 | 综合"

    return None

# ================== M3U 解析 ==================
def parse_m3u(text):
    result = []
    name = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF"):
            m = re.search(r",(.*)", line)
            if m:
                name = m.group(1).strip()
        elif line.startswith("http") and name:
            if not any(k in name.lower() for k in GEO_KEYWORDS):
                result.append((name, line))
            name = None
    return result

# ================== 构建 IPTV ==================
def build():
    print("[BUILD] 开始构建 IPTV")
    channels = {}

    with open(SRC) as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue

            parts = raw.split(maxsplit=1)
            if len(parts) != 2:
                continue

            url, region = parts

            if fail_db.get(url, 0) >= FAIL_LIMIT:
                continue

            try:
                resp = requests.get(url, timeout=TIMEOUT)
                resp.raise_for_status()
                text = resp.text
            except Exception as e:
                fail_db[url] = fail_db.get(url, 0) + 1
                print(f"[FAIL] {url} 拉取失败")
                continue

            for name, link in parse_m3u(text):
                group = detect_group(region, name)
                if not group:
                    continue
                key = (group, name)
                channels.setdefault(key, set()).add(link)

    save_db(fail_db)

    def sort_key(item):
        (group, name), _ = item
        g = GROUP_ORDER.get(group, 50)
        if group == "中国大陆 | 央视":
            try:
                return (g, CCTV_ORDER.index(name))
            except ValueError:
                return (g, 99)
        return (g, name)

    items = sorted(channels.items(), key=sort_key)

    with open(OUT, "w") as f:
        f.write("#EXTM3U\n")
        for (group, name), urls in items:
            for u in urls:
                f.write(f'#EXTINF:-1 group-title="{group}",{name}\n{u}\n')

    print("[BUILD] IPTV 构建完成")

# ================== 定时任务 ==================
def schedule_daily(hour=2):
    def loop():
        while True:
            now = datetime.now()
            nxt = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
            time.sleep((nxt - now).total_seconds())
            build()
    threading.Thread(target=loop, daemon=True).start()

# ================== Flask ==================
@app.route("/iptv.m3u")
def serve():
    return Response(open(OUT).read(), mimetype="audio/x-mpegurl")

# ================== 启动 ==================
build()
schedule_daily(2)
app.run(host="0.0.0.0", port=50087)
