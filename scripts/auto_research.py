import os
import feedparser
from google import genai  # 使用新版导入方式
from datetime import datetime
from pathlib import Path

# 1. 配置 API (新版 SDK 自动识别模型路径)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_papers():
    # 使用一个非常稳的 RSS 源
    rss_url = "https://pubmed.ncbi.nlm.nih.gov/rss/search/18yG_7JbI78V6_9_W7z/?limit=5"
    feed = feedparser.parse(rss_url)
    return feed.entries[:1]

def generate_post(paper):
    prompt = f"""
    Write a Jekyll blog post about this B-cell research:
    Title: {paper.title}
    Abstract: {paper.summary}
    
    Format: Include Jekyll Front Matter (layout: post, title).
    """
    
    try:
        # 新版 SDK 的调用方式，直接写模型名，不再有 v1beta 的烦恼
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"🚀 新版 SDK 报错详情: {e}")
        return None

# 执行主程序
papers = fetch_papers()
if papers:
    paper = papers[0]
    print(f"✅ Found paper: {paper.title}")
    
    content = generate_post(paper)
    
    if content:
        # 强制定位到 _posts 文件夹
        repo_root = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
        posts_dir = repo_root / "_posts"
        posts_dir.mkdir(exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-update.md"
        file_path = posts_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"🔥 文件已成功存入: {file_path}")
    else:
        print("❌ AI 生成内容为空")
else:
    print("❌ 未抓取到文章")
