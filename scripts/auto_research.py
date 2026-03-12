import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 1. 配置 API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    rss_url = "https://connect.biorxiv.org/relate/feed/123" 
    feed = feedparser.parse(rss_url)
    return feed.entries[:1]

def generate_post(paper):
    # 重点：去掉 models/ 前缀，直接写名字，或者尝试 gemini-pro
    # 有些旧版本的库对 1.5-flash 的路径识别有误
    try:
        # 方案 A: 尝试最标准的名字
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
---
layout: post
title: "{paper.title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
author: BCellAI-Bot
---

Summarize this B-cell AI research: {paper.title}. 
Abstract: {paper.summary}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# 执行主程序
papers = fetch_papers()
if papers:
    paper = papers[0]
    print(f"✅ Found: {paper.title}")
    
    post_content = generate_post(paper)
    
    if post_content:
        # --- 这里的逻辑最关键：使用 GitHub 环境变量定位根目录 ---
        # GITHUB_WORKSPACE 是 GitHub 官方提供的根目录绝对路径
        repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        posts_dir = os.path.join(repo_root, "_posts")
        
        # 确保文件夹存在
        if not os.path.exists(posts_dir):
            os.makedirs(posts_dir)
            print(f"📁 Created folder: {posts_dir}")
        
        # 生成文件名
        date_str = datetime.now().strftime('%Y-%m-%d')
        # 只保留字母数字，防止文件名非法导致保存失败
        safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).strip().replace(' ', '-')
        file_path = os.path.join(posts_dir, f"{date_str}-{safe_title}.md")
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(post_content)
        
        print(f"🚀 Success! File saved at: {file_path}")
        # 列出 _posts 目录内容，用于在日志里验证文件是否真的存在
        print(f"Contents of _posts: {os.listdir(posts_dir)}")
    else:
        print("❌ AI failed to generate content.")
else:
    print("❌ No papers found.")
