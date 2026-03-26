import os
import feedparser
import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

# ✅ 修复一：去重记忆文件
SEEN_FILE = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd())) / "seen_papers.json"

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_multi_source():
    sources = [
        "https://connect.biorxiv.org/relate/feed/123",
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5",
        "https://arxiv.org/rss/q-bio.BM",
    ]
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr"]
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # ✅ 修复一：加载已处理过的论文ID
    seen = load_seen()
    found_papers = []

    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # ✅ 用link或id作为唯一标识
                paper_id = getattr(entry, 'link', getattr(entry, 'id', entry.title))
                
                # ✅ 跳过已处理的论文
                if paper_id in seen:
                    continue

                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                if any(kw in (entry.title + entry.summary).lower() for kw in keywords):
                    if published_time is None or published_time > seven_days_ago:
                        found_papers.append((paper_id, entry))

        except:
            continue
        
        # ✅ 修复二：break放在外层
        if len(found_papers) >= 5:
            break

    # ✅ 更新seen记录
    new_seen = seen | {pid for pid, _ in found_papers}
    save_seen(new_seen)
    
    return [entry for _, entry in found_papers[:3]]

def generate_with_http(prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        # ✅ 打印返回内容，方便排查
        print(f"API状态码: {response.status_code}")
        print(f"API返回: {response.text[:500]}")
        res_json = response.json()
        if "candidates" in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"API调用异常: {e}")
        return None
    return None

# --- 执行 ---
papers = fetch_multi_source()

if not papers:
    print("⏭️ 没有新论文，跳过本次生成")
    exit(0)  # ✅ 修复三：没有新内容就直接退出，不生成重复文章

title = f"B-cell & AI Research Roundup: {datetime.now().strftime('%Y-%m-%d')}"
context_data = ""
for i, p in enumerate(papers):
    context_data += f"Paper {i+1}:\nTitle: {p.title}\nSummary: {p.summary}\n\n"

full_prompt = f"""
请根据以下 B 细胞领域最新研究内容，生成一篇 Jekyll 博客文章。
要求：
1. 使用 Markdown 格式。
2. 包含 YAML Front Matter（title, layout: post, author, date: {datetime.now().strftime('%Y-%m-%d')}）。
3. 不要翻译摘要，分析研究之间的内在联系和对AI辅助药物研发的意义。
用中文写一篇简短的B细胞AI研究摘要，300字以内，面向普通读者。
不要用学术语言，结尾一句话说明对普通人的意义。
研究内容：
{context_data}
"""

print("📝 正在生成深度报告...")
final_content = generate_with_http(full_prompt)

if not final_content:
    print("❌ AI生成失败")
    exit(1)

workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
posts_dir = Path(workspace) / "_posts"
posts_dir.mkdir(exist_ok=True)

# ✅ 修复三：文件名加时间戳避免覆盖
filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-bcell-report.md"
file_path = posts_dir / filename

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"✅ 文件已写入: {file_path}")
