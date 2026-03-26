import feedparser
import time
from datetime import datetime, timedelta
from pathlib import Path
import os
import json

SEEN_FILE = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd())) / "seen_papers.json"

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_papers():
    sources = [
        "https://connect.biorxiv.org/relate/feed/123",
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=5",
        "https://arxiv.org/rss/q-bio.BM",
    ]
    keywords = ["b cell", "b-cell", "antibody", "vaccine", "antigen", "bcr"]
    seven_days_ago = datetime.now() - timedelta(days=7)
    seen = load_seen()
    found = []

    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                paper_id = getattr(entry, 'link', getattr(entry, 'id', entry.title))
                if paper_id in seen:
                    continue
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                text = (entry.title + " " + getattr(entry, 'summary', '')).lower()
                if any(kw in text for kw in keywords):
                    if published_time is None or published_time > seven_days_ago:
                        found.append((paper_id, entry))
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            continue
        if len(found) >= 10:
            break

    save_seen(seen | {pid for pid, _ in found})
    return [entry for _, entry in found]

# --- 执行 ---
papers = fetch_papers()

workspace = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
raw_dir = workspace / "raw_papers"
raw_dir.mkdir(exist_ok=True)

if not papers:
    print("⏭️ 本周没有新论文")
else:
    filename = f"{datetime.now().strftime('%Y-%m-%d')}-raw.txt"
    file_path = raw_dir / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"共抓取论文：{len(papers)} 篇\n")
        f.write("="*60 + "\n\n")
        for i, p in enumerate(papers):
            f.write(f"【论文 {i+1}】\n")
            f.write(f"标题：{p.title}\n")
            f.write(f"链接：{getattr(p, 'link', 'N/A')}\n")
            f.write(f"摘要：{getattr(p, 'summary', 'N/A')}\n")
            f.write("\n" + "-"*40 + "\n\n")
    print(f"✅ 已保存：{file_path}")
