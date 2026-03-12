import os
import feedparser
import requests
import json
from datetime import datetime
from pathlib import Path

# --- 配置区 ---
API_KEY = os.getenv("GEMINI_API_KEY")
# 直接使用官方 V1 接口，绕过 SDK 默认的 v1beta 路径
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def fetch_multi_source():
    """从多个生物医学源抓取包含 B-cell 和 AI 筛选的文章"""
    sources = [
        # 源 1: BioRxiv (B-cell 专题)
        "https://connect.biorxiv.org/relate/feed/123",
        # 源 2: PubMed (关键词检索: B-cell + AI / Antibody / Vaccine)
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5",
        # 源 3: BioRxiv (免疫学大类)
        "http://connect.biorxiv.org/biorxiv_xml.php?subject=immunology"
    ]
    
    found_papers = []
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr"]
    
    for url in sources:
        try:
            print(f"📡 正在扫描源: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                text = (entry.title + entry.summary).lower()
                # 筛选逻辑：必须包含 B 细胞相关词汇
                if any(kw in text for kw in keywords):
                    found_papers.append(entry)
                if len(found_papers) >= 3: break
        except Exception as e:
            print(f"⚠️ 抓取失败 {url}: {e}")
            
    return found_papers[:3]

def generate_with_http(prompt):
    """使用原生 HTTP 请求调用 Gemini，解决 SDK 404 报错问题"""
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        # 解析返回内容
        if "candidates" in res_json:
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            return text.replace('```markdown', '').replace('```', '').strip()
        else:
            print(f"❌ API 响应异常: {res_json}")
            return None
    except Exception as e:
        print(f"❌ HTTP 请求失败: {e}")
        return None

# --- 主程序执行 ---
papers = fetch_multi_source()
print(f"📚 成功筛选出 {len(papers)} 篇相关文献")

# 构造 Prompt
if papers:
    title = f"Daily B-cell Research Roundup: {datetime.now().strftime('%Y-%m-%d')}"
    context = "Please analyze the following papers separately:\n\n"
    for i, p in enumerate(papers):
        context += f"### Paper {i+1}: {p.title}\nAbstract: {p.summary}\n\n"
else:
    title = "Insights into AI-Driven Antibody Discovery"
    context = "No new papers today. Please write a professional review on how AI assists in B-cell screening and antibody engineering."

full_prompt = f"""
---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
author: "BCellAI-Bot"
categories: [B-cell, AI, Immunology]
---

## Overview
This report summarizes the latest advancements in B-cell immunology and AI-assisted research.

{context}

---
**Technical Note:** Analysis focused on B-cell screening, antibody discovery, and vaccine development.
"""

print("📝 正在通过原生接口生成报告...")
final_content = generate_with_http(full_prompt)

# 如果 API 彻底挂了，使用极简保底内容
if not final_content:
    print("📢 使用本地保底模版...")
    final_content = f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
author: "BCellAI-Bot"
---
## Daily Summary
Research indicates ongoing progress in B-cell screening and AI model integration for antibody discovery.
"""

# 写入文件
repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
posts_dir = repo_root / "_posts"
posts_dir.mkdir(exist_ok=True)
filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-ai-report.md"
file_path = posts_dir / filename

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"🔥 大功告成！报告已生成: {file_path}")
