import os
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. 配置 Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 定义抓取函数 (以 bioRxiv 的免疫学/生物信息学分类为例)
def fetch_papers():
    # 这里的 URL 是 bioRxiv 的 RSS 订阅地址
    rss_url = "https://connect.biorxiv.org/relate/feed/123" 
    feed = feedparser.parse(rss_url)
    return feed.entries[:1] # 每天只取最新的一篇，保证质量

# 3. 让 AI 生成内容
def generate_post(paper):
    prompt = f"""
    You are a PhD expert in B-cell immunology and AI. 
    Summarize the following research paper into a high-quality blog post.
    
    Requirements:
    1. Language: English.
    2. Length: 500-800 words.
    3. Focus: Experimental results, data benchmarks, and AI architectures used.
    4. Format: Jekyll Markdown with Front Matter.
    
    Paper Title: {paper.title}
    Abstract: {paper.summary}
    Link: {paper.link}
    
    Output must start with --- layout: post --- and include 'author: BCellAI-Bot'.
    """
    response = model.generate_content(prompt)
    return response.text

# 4. 执行流程
papers = fetch_papers()
if papers:
    paper = papers[0]
    post_content = generate_post(paper)
    
    # 生成合规的文件名
    date_str = datetime.now().strftime('%Y-%m-%d')
    safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).replace(' ', '-')
    file_path = f"_posts/{date_str}-{safe_title}.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(post_content)
    print(f"Post created: {file_path}")
