#!/usr/bin/env python3
import os
import re
import requests
from flask import Flask, Response, jsonify

from collections import defaultdict

BASE = "/iptv"
SRC = f"{BASE}/config/m3u-sources.txt"
OUT_DIR = f"{BASE}/output"
FAIL_DB = f"{OUT_DIR}/fail.db"

TIMEOUT = 8
FAIL_LIMIT = 5

os.makedirs(OUT_DIR, exist_ok=True)
app = Flask(__name__)

# =========================
# GEO / 不可长期订阅关键词
# =========================
GEO_KEYWORDS = [
    "geo", "block", "restricted", "版权", "地区", "区域",
    "仅限", "海外", "港澳限定", "台灣限定"
]

def is_geo_blocked(name, url):
    text = (name + url).lower()
    return any(k.lower() in text for k in GEO_KEYWORDS)

# =========================
# CCTV 名称标准化
# =========================
def normalize_name(name: str) -> str:
    n = name.upper().strip()
    # 只处理 CCTV
    if "CCTV" in n:
        n = re.sub(r"CCTV[-\s]*0*([0-9]{1,2})", r"CCTV-\1", n)
        if "CCTV-5" in n and "+" in name:
            return "CCTV-5+"
    return name

# =========================
# 失败源管理（每条 URL）
# =========================
def load_db():
    if not os.path.exists(FAIL_DB):
        return {}
    db = {}
    with open(FAIL_DB) as f:
        for l in f:
            k, v = l.strip().split("|")
            db[k] = int(v)
    return db

def save_db(db):
    with open(FAIL_DB, "w") as f:
        for k, v in db.items():
            f.write(f"{k}|{v}\n")

fail_db = load_db()

# =========================
# 排序规则
# =========================
CCTV_ORDER = [
    "CCTV-1","CCTV-2","CCTV-3","CCTV-4","CCTV-5","CCTV-5+",
    "CCTV-6","CCTV-7","CCTV-8","CCTV-9","CCTV-10","CCTV-11",
    "CCTV-12","CCTV-13","CCTV-14","CCTV-15","CCTV-16","CCTV-17"
]

GROUP_ORDER = {
    "中国大陆 | 央视": 1,
    "中国大陆 | 卫视": 2,
    "中国大陆 | 体育": 3,
    "中国大陆 | 新闻": 4,
    "中国大陆 | 影视": 5,
    "中国大陆 | 综艺": 6,
    "中国大陆 | 其他": 99,

    "中国香港 | 综合": 10,
    "中国香港 | 新闻": 11,
    "中国香港 | 影视": 12,
    "中国香港 | 体育": 13,
    "中国香港 | 综艺": 14,

    "中国台湾 | 综合": 20,
    "中国台湾 | 新闻": 21,
    "中国台湾 | 影视": 22,
    "中国台湾 | 体育": 23,
    "中国台湾 | 综艺": 24,

    "国际频道 | 综合": 30,
    "国际频道 | 新闻": 31,
    "国际频道 | 影视": 32,
    "国际频道 | 体育": 33,
    "国际频道 | 音乐": 34,
    "国际频道 | 游戏": 35
}

# =========================
# 分组识别
# =========================
def detect_group(region, name):
    up = name.upper()

    if region == "中国大陆":
        if "CCTV" in up:
            if "5" in up or "体育" in name:
                return "中国大陆 | 体育"
            return "中国大陆 | 央视"
        if "卫视" in name: return "中国大陆 | 卫视"
        if "新闻" in name: return "中国大陆 | 新闻"
        if "体育" in name: return "中国大陆 | 体育"
        if any(x in name for x in ["电影","影视"]): return "中国大陆 | 影视"
        if "综艺" in name: return "中国大陆 | 综艺"
        return "中国大陆 | 其他"

    if region == "中国香港":
        if "新闻" in name: return "中国香港 | 新闻"
        if "体育" in name: return "中国香港 | 体育"
        if "综艺" in name: return "中国香港 | 综艺"
        if any(x in name for x in ["电影","影视"]): return "中国香港 | 影视"
        return "中国香港 | 综合"

    if region == "中国台湾":
        if "新闻" in name: return "中国台湾 | 新闻"
        if "体育" in name: return "中国台湾 | 体育"
        if "综艺" in name: return "中国台湾 | 综艺"
        if any(x in name for x in ["电影","影视"]): return "中国台湾 | 影视"
        return "中国台湾 | 综合"

    if region == "国际频道":
        if "SPORT" in up: return "国际频道 | 体育"
        if "MUSIC" in up: return "国际频道 | 音乐"
        if "GAME" in up or "电竞" in name: return "国际频道 | 游戏"
        if any(x in up for x in ["MOVIE","FILM"]): return "国际频道 | 影视"
        return "国际频道 | 综合"
    return None

# =========================
# M3U 解析
# =========================
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
            result.append((name, line))
            name = None
    return result

# =========================
# 构建频道池（每条URL独立失败统计）
# =========================
def build_channels():
    channels = {}
    for line in open(SRC, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            url, region = line.split(maxsplit=1)
        except ValueError:
            continue

        try:
            text = requests.get(url, timeout=TIMEOUT).text
        except Exception:
            # 整个源失败不影响其他源
            continue

        for raw_name, link in parse_m3u(text):
            if is_geo_blocked(raw_name, link):
                continue

            group = detect_group(region, raw_name)
            if not group:
                continue

            name = normalize_name(raw_name)
            key = (group, name)
            channels.setdefault(key, {})

            # 失败计数下沉到单条 URL
            if fail_db.get(link, 0) < FAIL_LIMIT:
                channels[key][link] = fail_db.get(link, 0)

    return channels

# =========================
# 输出订阅
# =========================
def output_playlist(name, filter_fn):
    channels = build_channels()
    items = [(k, v) for k, v in channels.items() if filter_fn(k)]

    def sort_key(item):
        (group, cname), _ = item
        if group == "中国大陆 | 央视" and cname in CCTV_ORDER:
            return (GROUP_ORDER[group], CCTV_ORDER.index(cname))
        return (GROUP_ORDER.get(group, 50), cname)

    items.sort(key=sort_key)

    m3u_file = f"{OUT_DIR}/{name}.m3u"
    txt_file = f"{OUT_DIR}/{name}.txt"

    with open(m3u_file, "w", encoding="utf-8") as fm, open(txt_file, "w", encoding="utf-8") as ft:
        fm.write("#EXTM3U\n")
        for (group, cname), urls_dict in items:
            for u in urls_dict:
                fm.write(f'#EXTINF:-1 group-title="{group}",{cname}\n{u}\n')
                ft.write(f"{cname},{u}\n")

# =========================
# 三种订阅
# =========================
def generate_all():
    output_playlist("iptv_full", lambda k: True)
    output_playlist(
        "iptv_lite",
        lambda k: k[0] in (
            "中国大陆 | 央视",
            "中国大陆 | 卫视",
            "中国香港 | 综合",
            "中国台湾 | 综合"
        )
    )
    output_playlist(
        "iptv_cctv_ws",
        lambda k: k[0] in (
            "中国大陆 | 央视",
            "中国大陆 | 卫视"
        )
    )

# =========================
# 状态接口
# =========================
@app.route("/status")
def status():
    channels = build_channels()
    stats = {f"{g} - {n}": len(urls) for (g, n), urls in channels.items()}
    return jsonify(stats)

@app.route("/rebuild")
def rebuild():
    generate_all()
    return "Rebuild complete"

# =========================
# 三种订阅接口
# =========================
@app.route("/full.m3u")
def full():
    path = f"{OUT_DIR}/iptv_full.m3u"
    if not os.path.exists(path):
        generate_all()
    return Response(open(path, encoding="utf-8").read(), mimetype="audio/x-mpegurl")

@app.route("/lite.m3u")
def lite():
    path = f"{OUT_DIR}/iptv_lite.m3u"
    if not os.path.exists(path):
        generate_all()
    return Response(open(path, encoding="utf-8").read(), mimetype="audio/x-mpegurl")

@app.route("/cctv.m3u")
def cctv():
    path = f"{OUT_DIR}/iptv_cctv_ws.m3u"
    if not os.path.exists(path):
        generate_all()
    return Response(open(path, encoding="utf-8").read(), mimetype="audio/x-mpegurl")

# =========================
# 首次生成
# =========================
generate_all()

# =========================
# 启动 Flask
# =========================
app.run(host="0.0.0.0", port=50087)
