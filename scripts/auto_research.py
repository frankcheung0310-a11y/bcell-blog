import os
import feedparser
import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# --- 配置 ---
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={API_KEY}"
HISTORY_FILE = "published_history.txt"  # 用于记录已发布的文章摘要，防止重复

def fetch_multi_source():
    # 加入了 arXiv 的生物分子频道
    sources = [
        "https://connect.biorxiv.org/relate/feed/123",
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5",
        "https://arxiv.org/rss/q-bio.BM" 
    ]
    found_papers = []
    # 扩展了关键词，涵盖 AI 辅助设计
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr", "protein design", "epitope"]
    
    three_days_ago = datetime.now() - timedelta(days=3)
    
    # 读取历史记录
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = f.read().splitlines()

    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 1. 时间过滤
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                if published_time and published_time < three_days_ago:
                    continue

                # 2. 关键词过滤
                content_to_check = (entry.title + entry.summary).lower()
                if any(kw in content_to_check for kw in keywords):
                    # 3. 重复性过滤 (通过标题的 MD5 哈希值)
                    entry_hash = hashlib.md5(entry.title.encode('utf-8')).hexdigest()
                    if entry_hash not in history:
                        found_papers.append({'entry': entry, 'hash': entry_hash})
                
                if len(found_papers) >= 5: break
        except:
            continue
    
    return found_papers

def generate_with_http(prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        # --- 增加这一行打印，看看 Google 到底回了什么 ---
        print(f"DEBUG: API Response: {res_json}") 
        
        if "candidates" in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"DEBUG: Error: {e}")
        return None
    return None

# --- 执行 ---
new_papers_data = fetch_multi_source()

# 核心逻辑：如果没有新文章，直接退出程序
if not new_papers_data:
    print("📢 经过比对，近 3 天内没有发现新的相关科研文章。跳过本次更新。")
    exit()

# 提取文章对象用于后续处理
papers = [item['entry'] for item in new_papers_data]
new_hashes = [item['hash'] for item in new_papers_data]

print(f"🚀 发现 {len(papers)} 篇新文章，正在准备生成深度报告...")

context_data = ""
for i, p in enumerate(papers):
    context_data += f"Paper {i+1}:\nTitle: {p.title}\nSummary: {p.summary}\n\n"

full_prompt = f"""
请根据以下 B 细胞与抗体 AI 领域最近的新研究内容，生成一篇 Jekyll 博客文章。
要求：
1. 使用 Markdown 格式。
2. 包含 YAML Front Matter（title, layout: post, author, tags）。
3. 语言风格：专业、硬核但易于理解。
4. 重点分析：这些研究如何利用 AI 技术（如机器学习、结构预测）加速 B 细胞研究或疫苗设计。
5. 自动生成 3 个相关的英文标签。

研究内容：
{context_data}
"""

final_content = generate_with_http(full_prompt)

if final_content:
    workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    posts_dir = Path(workspace) / "_posts"
    posts_dir.mkdir(exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d')}-bcell-report.md"
    file_path = posts_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    # 更新历史记录文件，防止下次重复
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        for h in new_hashes:
            f.write(h + "\n")

    print(f"✅ 深度报告已生成并写入: {file_path}")
else:
    print("❌ AI 生成内容失败。")
