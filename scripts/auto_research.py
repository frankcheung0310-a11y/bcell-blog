import os
import feedparser
import requests
import json
import time # 导入时间模块
from datetime import datetime, timedelta # 导入 timedelta 处理三天跨度
from pathlib import Path

# --- 配置 ---
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def fetch_multi_source():
    sources = [
        "https://connect.biorxiv.org/relate/feed/123",
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5"
        "https://arxiv.org/rss/q-bio.BM"
    ]
    found_papers = []
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr"]
    
    # 核心修改：定义 3 天的时间阈值
    three_days_ago = datetime.now() - timedelta(days=3)
    
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 解析发布时间（如果解析失败则跳过时间过滤）
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                # 过滤条件：包含关键词 且 发布于 3 天内
                if any(kw in (entry.title + entry.summary).lower() for kw in keywords):
                    if published_time is None or published_time > three_days_ago:
                        found_papers.append(entry)
                
                if len(found_papers) >= 5: break # 稍微多拿几篇，给 AI 更多选择空间
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
title = f"B-cell & AI Research Roundup (3-Day Edition): {datetime.now().strftime('%Y-%m-%d')}"

# 核心修改：优化 Prompt 提升差异化
context_data = ""
if papers:
    for i, p in enumerate(papers):
        context_data += f"Paper {i+1}:\nTitle: {p.title}\nSummary: {p.summary}\n\n"
else:
    context_data = "No new major papers in the last 3 days."

full_prompt = f"""
请根据以下 B 细胞领域最近 3 天的研究内容，生成一篇 Jekyll 博客文章。
要求：
1. 使用 Markdown 格式。
2. 包含 YAML Front Matter（title, layout: post, author）。
3. 不要只是翻译摘要。请分析这些研究之间的内在联系，或者它们对 AI 辅助药物研发的意义。
4. 如果内容较少，请深入探讨该领域的一个前沿趋势。
5. 自动为文章生成 3 个相关的英文标签（tags）。

研究内容：
{context_data}
"""

print("📝 正在生成深度报告...")
final_content = generate_with_http(full_prompt)

# 如果 AI 生成失败，至少保留一个带标题的骨架
if not final_content:
    final_content = f"---\nlayout: post\ntitle: \"{title}\"\nauthor: \"BCellAI-Bot\"\n---\n\n{context_data}"

workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
posts_dir = Path(workspace) / "_posts"
posts_dir.mkdir(exist_ok=True)

filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-report.md"
file_path = posts_dir / filename

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"✅ 文件已写入: {file_path}")
