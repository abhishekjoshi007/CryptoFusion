#!/usr/bin/env python3
"""
NYT Article‑Search + Hybrid Scraper (v2.2)
────────────────────────────────────────────────────────────────────────
• Queries NYT Article‑Search API with a date range and optional section filter
• Uses requests + BeautifulSoup for static content and Selenium fallback for JS-rendered pages
• Cleans boilerplate such as NYT paywall prompts from article body
• Outputs: url · published_date · section · headline · abstract · body
"""

import json, time, os, re, requests, json as js
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─── CONFIG ───
API_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
API_KEY = os.getenv("NYT_API_KEY", "SGGWyPzdW8s0fI1NnGGQsWgPIgrwYw2j")
QUERY = "NVDA Stock"
BEGIN_DATE, END_DATE = "20240801", "20240802"
SORT = "oldest"
SECTIONS = ["Business", "Technology"]
PAGES_TO_FETCH, ARTICLES_PER_PAGE = 9, 10
SCRAPE_BODY = True
HEADLESS = True
SEL_TIMEOUT = 15

# ─── Session with retry ───
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5, backoff_factor=2,
            status_forcelist=[429, 500, 502], allowed_methods=["GET"]
        )
    ),
)

# ─── Selenium driver ───
def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=opts)

driver = make_driver(HEADLESS)

# ─── Body scraping helpers ───
def _join_ps(ps):
    return " ".join(p.get_text(" ", strip=True) for p in ps)

def _extract_paragraphs(container: BeautifulSoup) -> str:
    return _join_ps(container.find_all("p"))

def _clean_body(text: str) -> str:
    """Removes boilerplate, paywall notices, and subscription prompts."""
    return re.sub(
        r"We are having trouble retrieving.*?Subscribe\s*\.",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

def _from_next_data(soup: BeautifulSoup) -> str:
    node = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not node:
        return ""
    try:
        data = js.loads(node.string)
        stack: List[Any] = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if "article" in cur and isinstance(cur["article"], dict):
                    body = cur["article"].get("body") or cur["article"].get("articleBody")
                    if body and isinstance(body, str):
                        return BeautifulSoup(body, "html.parser").get_text(" ", strip=True)
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
    except Exception:
        pass
    return ""

def _scrape_static(url: str) -> str:
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        sec = soup.find("section", {"data-testid": "article-body"}) or \
              soup.find("section", {"id": "article-body"})
        if sec:
            return _extract_paragraphs(sec)

        sec = soup.find("section", class_=re.compile(r"meteredContent"))
        if sec:
            return _extract_paragraphs(sec)

        sec = soup.find("div", class_=re.compile(r"css-[a-z0-9]+"))
        if sec and sec.find("p"):
            return _extract_paragraphs(sec)

        sec = soup.find("section", {"name": "articleBody"})
        if sec:
            return _extract_paragraphs(sec)

        paras = soup.find_all("p", {"data-testid": "paragraph"})
        if paras:
            return _join_ps(paras)

        body = _from_next_data(soup)
        if body:
            return body

        container = soup.find("article") or soup.find("main") or soup
        return _extract_paragraphs(container)
    except Exception:
        return ""

def _scrape_with_selenium(url: str) -> str:
    try:
        driver.get(url)
        WebDriverWait(driver, SEL_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "section[data-testid='article-body'], section#article-body, article p")
            )
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        container = soup.find("section", {"data-testid": "article-body"}) or \
                    soup.find("section", {"id": "article-body"}) or \
                    soup.find("article") or soup.find("main") or soup
        return _extract_paragraphs(container)
    except Exception:
        return ""

def get_body(url: str) -> str:
    if not SCRAPE_BODY:
        return ""
    text = _scrape_static(url)
    if not text:
        text = _scrape_with_selenium(url)
    return _clean_body(text)

# ─── API helpers ───
def build_params(page: int, with_filter: bool) -> Dict:
    p = {
        "q": QUERY, "begin_date": BEGIN_DATE, "end_date": END_DATE,
        "sort": SORT, "api-key": API_KEY, "page": page,
    }
    if with_filter and SECTIONS:
        quoted = " ".join(f'"{s}"' for s in SECTIONS)
        p["fq"] = f'(section_name:({quoted}) OR news_desk:({quoted}))'
    return p

# ─── Fetch routine ───
def fetch_articles() -> List[Dict]:
    collected, seen = [], set()
    for use_filter in (True, False if SECTIONS else False):
        probe = session.get(API_URL, params=build_params(0, use_filter), timeout=10)
        probe.raise_for_status()
        resp = probe.json()["response"]
        hits = (resp.get("meta") or resp.get("metadata", {})).get("hits", 0)
        docs0 = resp.get("docs") or []
        if hits == 0 or not docs0:
            if use_filter:
                print("0 hits with section filter → retrying without it …")
                continue
            print("No articles found.")
            return []
        pages = min(PAGES_TO_FETCH, -(-hits // len(docs0)))
        print(f"Fetching {pages} page(s) (hits={hits}, server_filter={use_filter})")

        for pg in range(pages):
            r = session.get(API_URL, params=build_params(pg, use_filter), timeout=10)
            if r.status_code == 429:
                print("Rate‑limit 429 → sleeping 10 s"); time.sleep(10)
                r = session.get(API_URL, params=build_params(pg, use_filter), timeout=10)
            r.raise_for_status()
            for d in r.json()["response"]["docs"][:ARTICLES_PER_PAGE]:
                url = d.get("web_url", "")
                if not url or url in seen: continue
                seen.add(url)
                if not use_filter and SECTIONS:
                    if d.get("section_name") not in SECTIONS and d.get("news_desk") not in SECTIONS:
                        continue

                pub = d.get("pub_date") or ""
                date_str = datetime.strptime(pub, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d") if pub else ""
                collected.append({
                    "url": url,
                    "published_date": date_str,
                    "section": d.get("section_name") or d.get("news_desk", ""),
                    "headline": d.get("headline", {}).get("main", ""),
                    "abstract": d.get("abstract", ""),
                    "body": get_body(url),
                })
            print(f" • Page {pg+1}/{pages} done; total {len(collected)}")
            time.sleep(2)
        break
    return collected

# ─── Run & save ───
if __name__ == "__main__":
    try:
        arts = fetch_articles()
        out = datetime.now().strftime("nyt_%Y%m%d_%H%M%S.json")
        with open(out, "w", encoding="utf-8") as fp:
            json.dump(arts, fp, indent=2, ensure_ascii=False)
        print(f"Done — wrote {len(arts)} articles to {out}")
    finally:
        driver.quit()
