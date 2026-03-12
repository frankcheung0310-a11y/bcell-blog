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
    
    # 稍微优化一下 Prompt，确保 AI 生成 Jekyll 需要的 Front Matter 格式
    prompt = f"""
Summarize this B-cell AI paper for a professional blog: {paper.title}. 
Abstract: {paper.summary}

Requirements:
1. Start with Jekyll Front Matter (layout: post, title, author: BCellAI-Bot).
2. Content in English, focus on B-cell and AI.
"""
    
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
        # --- 核心路径逻辑修改开始 ---
        # 1. 找到脚本所在文件夹的上一级（即仓库根目录）
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_script_dir)
        
        # 2. 强制指定根目录下的 _posts 文件夹
        posts_dir = os.path.join(root_dir, "_posts")
        os.makedirs(posts_dir, exist_ok=True)
        
        # 3. 生成文件名
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_title = "".join([c for c in paper.title[:30] if c.isalnum() or c==' ']).strip().replace(' ', '-')
        file_path = os.path.join(posts_dir, f"{date_str}-{safe_title}.md")
        # --- 核心路径逻辑修改结束 ---
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(post_content)
            
        print(f"Success! Created: {file_path}")
        print(f"Absolute Path: {os.path.abspath(file_path)}")
