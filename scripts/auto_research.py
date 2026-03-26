import feedparser
import requests
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

# 自动适配 GitHub 环境或本地环境
workspace = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd()))
SEEN_FILE = workspace / "seen_papers.json"
RAW_DIR = workspace / "raw_papers"

def load_seen():
    if SEEN_FILE.exists():
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

def fetch_full_text(url):
    """尝试抓取全文，失败则返回None"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # Arxiv 转换逻辑
        if 'arxiv.org' in url:
            abs_url = url.replace('/abs/', '/html/')
            resp = requests.get(abs_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                body = soup.find('div', class_='ltx_page_content')
                return body.get_text(separator='\n', strip=True)[:5000] if body else None
        
        # BioRxiv 转换逻辑
        if 'biorxiv.org' in url:
            full_url = url + '.full'
            resp = requests.get(full_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                body = soup.find('div', class_='article-text')
                return body.get_text(separator='\n', strip=True)[:5000] if body else None

        return None
    except:
        return None

def fetch_papers():
    sources = [
        "https://pubmed.ncbi.nlm.nih.gov/rss/search/1y0yS_XvO2fQfX4p-B-cell-AI/?limit=20",
        "https://arxiv.org/rss/q-bio.QM",
        "https://arxiv.org/rss/q-bio.BM",
        "https://connect.biorxiv.org/relate/feed/181",
        "https://connect.biorxiv.org/relate/feed/123",
        "https://www.nature.com/ni.rss",
        "https://www.cell.com/immunity/rss.xml",
    ]

    keywords = ["b cell", "b-cell", "antibody", "antigen", "bcr", "immunology", "vaccine", "immunotherapy"]
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    seen = load_seen()
    found = []

    print(f"开始扫描 {len(sources)} 个源...")
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                paper_id = getattr(entry, 'link', entry.title)
                if paper_id in seen:
                    continue

                title = entry.title
                summary = getattr(entry, 'summary', '')
                text = (title + " " + summary).lower()

                if any(kw in text for kw in keywords):
                    found.append((paper_id, entry))
                    print(f"  ✅ 发现新论文: {title[:50]}...")
                
                if len(found) >= 15: break
        except Exception as e:
            print(f"❌ 抓取失败 {url}: {e}")
        if len(found) >= 15: break

    return found, seen

# --- 主执行程序 ---
if __name__ == "__main__":
    RAW_DIR.mkdir(exist_ok=True)
    new_papers, seen_set = fetch_papers()

    if not new_papers:
        print("⏭️ 本次运行没有发现新论文。")
    else:
        # 生成 TXT 文件
        timestamp = datetime.now().strftime('%Y-%m-%d')
        file_path = RAW_DIR / f"{timestamp}-raw.txt"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"B-Cell AI Research Intelligence ({timestamp})\n")
            f.write(f"Total New Papers: {len(new_papers)}\n")
            f.write("="*60 + "\n\n")

            new_ids = set()
            for i, (pid, p) in enumerate(new_papers):
                new_ids.add(pid)
                f.write(f"【Paper {i+1}】\n")
                f.write(f"Title: {p.title}\n")
                f.write(f"Link: {p.link}\n")
                f.write(f"Summary: {getattr(p, 'summary', 'No summary available.')}\n")
                
                # 尝试抓取全文
                print(f"🔍 尝试抓取全文: {p.title[:30]}")
                content = fetch_full_text(p.link)
                if content:
                    f.write(f"\n[Full Text Snippet]:\n{content}\n")
                
                f.write("\n" + "-"*40 + "\n\n")
        
        # 更新已读列表
        save_seen(seen_set | new_ids)
        print(f"✅ 任务完成！素材已保存至: {file_path}")
