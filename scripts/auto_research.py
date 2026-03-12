import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 1. 配置 API
# 尝试使用最稳定的配置
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    url = "https://connect.biorxiv.org/relate/feed/123"
    print(f"📡 正在抓取: {url}")
    feed = feedparser.parse(url)
    if feed.entries:
        print(f"✅ 发现 {len(feed.entries)} 篇文章")
        return feed.entries[:1]
    return None

def generate_post(paper):
    title = paper.title if paper else "B-cell AI Research Daily"
    abstract = paper.summary if paper else "Latest updates in immunology and AI."
    
    prompt = f"Summarize this research for a blog post. Title: {title}. Abstract: {abstract}"

    # --- 核心修改：模型名称轮询列表 ---
    # 我们按稳定性排序：gemini-pro 是最不可能报 404 的
    model_names = ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.0-pro']
    
    for name in model_names:
        try:
            print(f"🤖 尝试调用模型: {name}...")
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"⚠️ 模型 {name} 失败: {e}")
            continue
    
    # --- 最终保底：如果 AI 真的坏了，生成一个固定模版，不让 Workflow 失败 ---
    print("📢 AI 调用全线失败，启动保底模版...")
    return f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
---
This is an automated research update.
Research Title: {title}
Abstract: {abstract}
(Note: AI summary service temporarily unavailable)"""

# 执行
paper_list = fetch_papers()
paper = paper_list[0] if paper_list else None

print("📝 正在准备文章内容...")
content = generate_post(paper)

if content:
    repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
    posts_dir = repo_root / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    filename = f"{datetime.now().strftime('%Y-%m-%d')}-update.md"
    file_path = posts_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"🔥 成功！文件已存入: {file_path}")
    print(f"📂 目录现状: {os.listdir(posts_dir)}")
