import feedparser
import requests
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

SEEN_FILE = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd())) / "seen_papers.json"

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_full_text(url):
    """尝试抓取全文，失败则返回None"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; BCellBot/1.0)'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')

        # arxiv全文
        if 'arxiv.org' in url:
            abs_url = url.replace('/abs/', '/html/')
            resp2 = requests.get(abs_url, headers=headers, timeout=10)
            if resp2.status_code == 200:
                soup2 = BeautifulSoup(resp2.text, 'html.parser')
                body = soup2.find('div', class_='ltx_page_content')
                if body:
                    return body.get_text(separator='\n', strip=True)[:5000]

        # biorxiv全文
        if 'biorxiv.org' in url or 'medrxiv.org' in url:
            full_url = url + '.full'
            resp2 = requests.get(full_url, headers=headers, timeout=10)
            if resp2.status_code == 200:
                soup2 = BeautifulSoup(resp2.text, 'html.parser')
                body = soup2.find('div', class_='article-text')
                if body:
                    return body.get_text(separator='\n', strip=True)[:5000]

        # PubMed Central开放全文
        if 'pubmed' in url:
            pmcid = url.split('/')[-1].strip('/')
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            resp2 = requests.get(pmc_url, headers=headers, timeout=10)
            if resp2.status_code == 200:
                soup2 = BeautifulSoup(resp2.text, 'html.parser')
                body = soup2.find('div', class_='jig-ncbiinpagenav-content')
                if body:
                    return body.get_text(separator='\n', strip=True)[:5000]

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

    keywords = [
        "b cell", "b-cell", "antibody", "antigen", "bcr",
        "t cell", "t-cell", "car-t", "car t",
        "mrna vaccine", "mrna therapy", "immunotherapy",
        "lymphocyte", "immune", "immunology",
        "cell therapy", "therapeutic antibody", "monoclonal"
    ]

    seven_days_ago = datetime.now() - timedelta(days=7)
    seen = load_seen()
    found = []

    for url in sources:
        try:
            feed = feedparser.parse(url)
            print(f"📡 {url} → {len(feed.entries)} 条")
            for entry in feed.entries:
                paper_id = getattr(entry, 'link', getattr(entry, 'id', entry.title))
                if paper_id in seen:
                    continue

                published_time = None
                if hasattr(entry, 'published_parsed'):
                    try:
                        published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except:
                        pass

                summary = getattr(entry, 'summary', '')
                text = (entry.title + " " + summary).lower()

                if any(kw in text for kw in keywords):
                    if published_time is None or published_time > seven_days_ago:
                        found.append((paper_id, entry))
                        print(f"  ✅ 收录: {entry.title[:60]}")

        except Exception as e:
            print(f"❌ 抓取失败 {url}: {e}")
            continue

        if len(found) >= 15:
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
        f.write(f"共收录论文：{len(papers)} 篇\n")
        f.write("="*60 + "\n\n")

        for i, p in enumerate(papers):
            link = getattr(p, 'link', 'N/A')
            summary = getattr(p, 'summary', '无摘要')

            f.write(f"【论文 {i+1}】\n")
            f.write(f"标题：{p.title}\n")
            f.write(f"链接：{link}\n")
            f.write(f"摘要：{summary}\n\n")

            # 尝试抓取全文
            print(f"🔍 尝试抓取全文: {p.title[:50]}")
            full_text = fetch_full_text(link)
            if full_text:
                f.write(f"全文节选：\n{full_text}\n")
                print(f"  ✅ 全文抓取成功")
            else:
                f.write("全文：暂无（付费墙或格式不支持）\n")
                print(f"  ⚠️ 全文不可用，仅保留摘要")

            f.write("\n" + "-"*40 + "\n\n")

    print(f"✅ 已保存：{file_path}")
