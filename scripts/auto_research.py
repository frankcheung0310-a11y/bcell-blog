import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 1. 配置 API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_multi_source():
    """从多个生物医学源抓取文章"""
    sources = [
        # 源 1: BioRxiv (B-cell 专题)
        "https://connect.biorxiv.org/relate/feed/123",
        # 源 2: PubMed (B-cell 与 AI 关键词搜索结果)
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5",
        # 源 3: BioRxiv (免疫学大类)
        "http://connect.biorxiv.org/biorxiv_xml.php?subject=immunology"
    ]
    
    all_papers = []
    
    for url in sources:
        try:
            print(f"📡 正在尝试抓取: {url}")
            feed = feedparser.parse(url)
            if feed.entries:
                # 过滤出和 B 细胞相关的文章（如果源比较杂）
                for entry in feed.entries:
                    title_summary = (entry.title + entry.summary).lower()
                    if "b cell" in title_summary or "b-cell" in title_summary or "antibody" in title_summary:
                        all_papers.append(entry)
                    if len(all_papers) >= 3: break # 每个源或总体取前 3 篇即可
        except Exception as e:
            print(f"⚠️ 抓取 {url} 失败: {e}")
            
    return all_papers[:3] # 最终取前 2-3 篇

def generate_combined_post(papers):
    """汇聚多篇文章生成一份深度报告"""
    
    if not papers:
        # 保底逻辑：如果没有搜到新文章，AI 撰写领域动态
        context = "Currently no new papers found on RSS. Please provide a daily insight on AI applications in Antibody discovery and B-cell engineering."
        title = "Daily Insight: AI in Antibody & B-cell Engineering"
    else:
        title = f"Daily B-cell & AI Research Roundup: {len(papers)} New Highlights"
        context = "I have found the following research papers. Please summarize them separately in one blog post:\n\n"
        for i, p in enumerate(papers):
            context += f"Paper {i+1}:\nTitle: {p.title}\nAbstract: {p.summary}\n\n"

    prompt = f"""
---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
author: "BCellAI-Bot"
categories: [Research, B-cell]
---

Please act as a senior Bio-AI scientist. Write a professional daily report based on the following input:

{context}

Requirements:
1. Separate each paper or topic with a clear Heading (##).
2. For each part, describe the core findings and specifically explain its impact on B-cell research, antibody discovery, or vaccine development.
3. If AI was used (machine learning, screening models, etc.), highlight the methodology.
4. Language: English (Professional Scientific Style).
5. Do not include any AI-generated metadata like '```markdown'.
"""

    model_names = ['gemini-pro', 'gemini-1.5-flash']
    for name in model_names:
        try:
            print(f"🤖 正在使用 {name} 生成汇编报告...")
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.replace('```markdown', '').replace('```', '').strip()
        except Exception as e:
            print(f"⚠️ {name} 调用失败: {e}")
            continue
    return None

# --- 执行主流程 ---
papers = fetch_multi_source()
print(f"📚 共筛选出 {len(papers)} 篇相关文献")

content = generate_combined_post(papers)

if content:
    repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
    posts_dir = repo_root / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-ai-report.md"
    file_path = posts_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"🔥 报告已汇总并存入: {file_path}")
