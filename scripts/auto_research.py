import os
import feedparser
from google import genai
from datetime import datetime

# 1. 配置新的 Gemini SDK
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. 定义抓取函数
def fetch_papers():
    rss_url = "https://connect.biorxiv.org/relate/feed/123" 
    feed = feedparser.parse(rss_url)
    return feed.entries[:1]

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
    # 使用最新的 generate 方法
    response = client.models.generate_content(
        model="models/gemini-1.5-flash",
        contents=prompt
    )
    return response.text

# 4. 执行流程
papers = fetch_papers()
if papers:
    paper = papers[0]
    post_content = generate_post(paper)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).replace(' ', '-')
    file_path = f"_posts/{date_str}-{safe_title}.md"
    
    # 确保文件夹存在（防止路径错误）
    os.makedirs("_posts", exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(post_content)
    print(f"Post created: {file_path}")
