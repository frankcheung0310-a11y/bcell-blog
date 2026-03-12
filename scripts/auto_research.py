import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 1. 配置 API - 使用最稳健的经典库配置
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    # 尝试多个源，确保一定能抓到内容
    rss_urls = [
        "https://connect.biorxiv.org/relate/feed/123",
        "http://connect.biorxiv.org/biorxiv_xml.php?subject=immunology"
    ]
    
    for url in rss_urls:
        print(f"📡 正在尝试抓取源: {url}")
        feed = feedparser.parse(url)
        if feed.entries:
            print(f"✅ 成功发现 {len(feed.entries)} 篇文章")
            return feed.entries[:1]
    return None

def generate_post(paper):
    # 即使抓取失败，也准备好保底内容
    title = paper.title if paper else "Latest Trends in B-cell AI Research"
    abstract = paper.summary if paper else "Exploring how machine learning is transforming immunology."

    # 准备 Jekyll 格式的 Prompt
    prompt = f"""
---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
author: BCellAI-Bot
---

Analysis of the following research:
Title: {title}
Summary: {abstract}

Please write a detailed professional blog post in English.
"""

    # --- 双保险调用机制 ---
    # 尝试第一种路径：标准模型名
    models_to_try = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models_to_try:
        try:
            print(f"🤖 正在尝试调用模型: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 调用失败: {e}")
            continue # 如果失败，尝试下一个模型
            
    return None

# --- 执行主流程 ---
paper_list = fetch_papers()
paper = paper_list[0] if paper_list else None

print("📝 正在生成文章内容...")
content = generate_post(paper)

if content:
    # 获取根目录（GITHUB_WORKSPACE）
    repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
    posts_dir = repo_root / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    # 生成带时间戳的文件名，确保唯一性
    filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-bcell-post.md"
    file_path = posts_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"🔥 大功告成！文件已存入: {file_path}")
    print(f"📂 当前 _posts 目录文件列表: {os.listdir(posts_dir)}")
else:
    print("❌ 经过多次尝试，AI 仍无法生成内容。请检查 API Key 权限或余额。")
