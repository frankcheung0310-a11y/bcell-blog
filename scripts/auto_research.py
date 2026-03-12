import os
import feedparser
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 配置 API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    rss_url = "https://connect.biorxiv.org/relate/feed/123" 
    feed = feedparser.parse(rss_url)
    return feed.entries[:1]

def generate_post(paper):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Create a Jekyll blog post for this research: {paper.title}. Abstract: {paper.summary}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

papers = fetch_papers()
if papers:
    paper = papers[0]
    post_content = generate_post(paper)
    
    if post_content:
        # 定位到仓库根目录下的 _posts
        script_path = Path(__file__).resolve()
        repo_root = script_path.parent.parent
        posts_dir = repo_root / "_posts"
        posts_dir.mkdir(exist_ok=True)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).strip().replace(' ', '-')
        file_path = posts_dir / f"{date_str}-{safe_title}.md"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(post_content)
        print(f"🚀 Success! File saved at: {file_path}")
