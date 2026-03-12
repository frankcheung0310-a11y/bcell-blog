import os
import feedparser
from google import genai
from datetime import datetime
from pathlib import Path

# 1. 配置 API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    # 换成 BioRxiv 免疫学大类源，内容非常多
    rss_urls = [
        "https://connect.biorxiv.org/relate/feed/123", # B-cell 专题
        "http://connect.biorxiv.org/biorxiv_xml.php?subject=immunology" # 免疫学大类（保底）
    ]
    
    for url in rss_urls:
        print(f"尝试抓取源: {url}")
        feed = feedparser.parse(url)
        if feed.entries:
            print(f"✅ 成功发现 {len(feed.entries)} 篇文章")
            return feed.entries[:1]
    return None

def generate_post(paper):
    # 哪怕没抓到，我们也让 AI 写点东西来验证流程是否通畅
    if not paper:
        title = "Weekly B-cell AI Research Landscape"
        abstract = "Periodic review of AI applications in B-cell immunology."
    else:
        title = paper.title
        abstract = paper.summary

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

Please write a detailed blog post in English.
"""
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"🚀 AI 报错: {e}")
        return None

# 执行主程序
paper_list = fetch_papers()
# 即使 paper_list 是空，我们也生成一篇“测试文章”来强行打通 GitHub 流程
paper = paper_list[0] if paper_list else None

print("正在生成文章内容...")
content = generate_post(paper)

if content:
    repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
    posts_dir = repo_root / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    # 文件名加上时间戳防止重复
    filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-bcell-post.md"
    file_path = posts_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"🔥 文件已成功生成并写入: {file_path}")
    print(f"📂 当前 _posts 目录: {os.listdir(posts_dir)}")
else:
    print("❌ 最终生成失败")
