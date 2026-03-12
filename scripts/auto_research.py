import os
import feedparser
import requests
import json
from datetime import datetime
from pathlib import Path

# --- 配置 ---
API_KEY = os.getenv("GEMINI_API_KEY")
# 强制尝试 v1beta 路径，这通常是 Free Tier 最稳的路径
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def fetch_multi_source():
    sources = [
        "https://connect.biorxiv.org/relate/feed/123",
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5"
    ]
    found_papers = []
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr"]
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if any(kw in (entry.title + entry.summary).lower() for kw in keywords):
                    found_papers.append(entry)
                if len(found_papers) >= 3: break
        except: continue
    return found_papers[:3]

def generate_with_http(prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        if "candidates" in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return None
    return None

# --- 执行 ---
papers = fetch_multi_source()
title = f"B-cell & AI Research Roundup: {datetime.now().strftime('%Y-%m-%d')}"
context = ""
if papers:
    for i, p in enumerate(papers):
        context += f"### {p.title}\n{p.summary}\n\n"
else:
    context = "AI review on B-cell antibody discovery trends."

full_prompt = f"---\nlayout: post\ntitle: \"{title}\"\nauthor: \"BCellAI-Bot\"\n---\n\n{context}"

print("📝 正在生成报告...")
final_content = generate_with_http(full_prompt) or full_prompt

# --- 核心修改：确保路径绝对正确 ---
# 获取 GitHub Action 的工作根目录
workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
posts_dir = Path(workspace) / "_posts"
posts_dir.mkdir(exist_ok=True)

filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-report.md"
file_path = posts_dir / filename

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"✅ 文件已写入: {file_path}")
