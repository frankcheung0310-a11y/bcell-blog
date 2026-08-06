import feedparser, requests, json, os
from datetime import datetime, timedelta
from pathlib import Path

# 环境适配
ws = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
SEEN_FILE = ws / "seen_papers.json"
OUT_DIR = ws / "raw_papers"

def main():
    OUT_DIR.mkdir(exist_ok=True)
    # 加载已读记录
    seen = set()
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f: seen = set(json.load(f))

    sources = [
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/",
        "https://arxiv.org/rss/q-bio.QM",
        "https://connect.biorxiv.org/relate/feed/181"
    ]
    
    found = []
    # 只要标题里含这些词就抓取
    keywords = ["b cell", "antibody", "antigen", "immunology", "vaccine"]

    for url in sources:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if e.link in seen: continue
            if any(k in e.title.lower() for k in keywords):
                found.append(f"Title: {e.title}\nLink: {e.link}\nSummary: {getattr(e, 'summary', 'No summary.')}\n")
                seen.add(e.link)
            if len(found) >= 15: break

    if found:
        # 存入 TXT 供你手动丢给 AI
        date_str = datetime.now().strftime('%Y-%m-%d')
        with open(OUT_DIR / f"{date_str}-raw.txt", "w", encoding="utf-8") as f:
            f.write(f"--- B-Cell Research Materials {date_str} ---\n\n")
            f.write("\n\n".join(found))
        # 更新已读
        with open(SEEN_FILE, "w") as f: json.dump(list(seen), f)
        print(f"Captured {len(found)} papers.")
    else:
        print("Everything is up to date.")

if __name__ == "__main__":
    main()
