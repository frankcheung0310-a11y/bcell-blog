import os
import feedparser
import google.generativeai as genai
from datetime import datetime

# 配置 API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    # 抓取相关文章
    rss_url = "https://connect.biorxiv.org/relate/feed/123" 
    feed = feedparser.parse(rss_url)
    return feed.entries[:1]

def generate_post(paper):
    # 使用最经典的 1.5-flash 引用方式
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"Summarize this B-cell AI paper for a professional blog: {paper.title}. Abstract: {paper.summary}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# 执行
papers = fetch_papers()
if papers:
    paper = papers[0]
    print(f"Processing: {paper.title}")
    
    post_content = generate_post(paper)
    
    if post_content:
        os.makedirs("_posts", exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).strip().replace(' ', '-')
        file_path = f"_posts/{date_str}-{safe_title}.md"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(post_content)
        print(f"Success! Created {file_path}")
