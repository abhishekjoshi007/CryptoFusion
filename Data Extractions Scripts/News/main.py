#!/usr/bin/env python3

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
from tqdm import tqdm

# ─── CONFIG ───
API_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
API_KEY = os.getenv("NYT_API_KEY", "SGGWyPzdW8s0fI1NnGGQsWgPIgrwYw2j")
BEGIN_DATE, END_DATE = "20240801", "20241101"
SORT = "oldest"
SECTIONS = [ "Technology","Business"]
PAGES_TO_FETCH, ARTICLES_PER_PAGE = 100, 10
SCRAPE_BODY = True
HEADLESS = True
SEL_TIMEOUT = 15
OUTPUT_DIR = "News"

TICKERS = [
    "PagerDuty Inc NASDAQ: PD",
    "Turtle Beach NASDAQ: HEAR",
    "Apple Inc NASDAQ: AAPL",
    "Palo Alto Networks NASDAQ: PANW",
    "Array Technologies NASDAQ: ARRY",
    "TE Connectivity NASDAQ: TEL",
    "Arqit Quantum Inc NASDAQ: ARQQ",
    "Arista Networks NASDAQ: ANET",
    "Ubiquiti Inc NASDAQ: UI",
    "Zoom Video Communications NASDAQ: ZM",
    "Agilysys Inc NASDAQ: AGYS",
    "First Solar NASDAQ: FSLR",
    "Innodata Inc NASDAQ: INOD",
    "Uber Technologies NASDAQ: UBER",
    "Synopsys Inc NASDAQ: SNPS",
    "Analog Devices NASDAQ: ADI",
    "FormFactor Inc NASDAQ: FORM",
    "Palantir Technologies NASDAQ: PLTR",
    "Block Inc NASDAQ: SQ",
    "Richardson Electronics NASDAQ: RELL",
    "Amkor Technology NASDAQ: AMKR",
    "Canadian Solar NASDAQ: CSIQ",
    "Kyndryl Holdings NASDAQ: KD",
    "BlackLine Inc NASDAQ: BL",
    "Texas Instruments NASDAQ: TXN",
    "KLA Corporation NASDAQ: KLAC",
    "Intel Corporation NASDAQ: INTC",
    "AppLovin Corporation NASDAQ: APP",
    "Bill.com Holdings NASDAQ: BILL",
    "Remitly Global NASDAQ: RELY",
    "Cadence Design Systems NASDAQ: CDNS",
    "Micron Technology NASDAQ: MU",
    "Applied Digital Corporation NASDAQ: APLD",
    "Fidelity National Information Services NASDAQ: FIS",
    "Toast Inc NASDAQ: TOST",
    "Datadog Inc NASDAQ: DDOG",
    "Applied Materials NASDAQ: AMAT",
    "Payoneer Global NASDAQ: PAYO",
    "NetApp Inc NASDAQ: NTAP",
    "Fair Isaac Corporation NASDAQ: FICO",
    "The Trade Desk NASDAQ: TTD",
    "Atomera Incorporated NASDAQ: ATOM",
    "Digimarc Corporation NASDAQ: DMRC",
    "Enphase Energy NASDAQ: ENPH",
    "Twilio Inc NASDAQ: TWLO",
    "Badger Meter NASDAQ: BMI",
    "Bumble Inc NASDAQ: BMBL",
    "MicroStrategy NASDAQ: MSTR",
    "Universal Display Corporation NASDAQ: OLED",
    "CrowdStrike Holdings NASDAQ: CRWD",
    "SoundHound AI NASDAQ: SOUN",
    "Lyft Inc NASDAQ: LYFT",
    "UiPath Inc NASDAQ: PATH",
    "Qualcomm NASDAQ: QCOM",
    "Bandwidth Inc NASDAQ: BAND",
    "Rumble Inc NASDAQ: RUM",
    "Elastic N.V. NASDAQ: ESTC",
    "DocuSign Inc NASDAQ: DOCU",
    "Unity Software Inc NASDAQ: U",
    "SolarEdge Technologies NASDAQ: SEDG",
    "Microsoft Corporation NASDAQ: MSFT",
    "Hewlett Packard Enterprise NASDAQ: HPE",
    "Coherent Corp NASDAQ: COHR",
    "Methode Electronics NASDAQ: MEI",
    "Onto Innovation NASDAQ: ONTO",
    "Accenture plc NASDAQ: ACN",
    "Workiva Inc NASDAQ: WK",
    "HP Inc NASDAQ: HPQ",
    "SentinelOne NASDAQ: S",
    "Gen Digital NASDAQ: GEN",
    "Oracle Corporation NASDAQ: ORCL",
    "Ouster Inc NASDAQ: OUST",
    "Dell Technologies NASDAQ: DELL",
    "Astera Labs NASDAQ: ALAB",
    "Oddity Tech Ltd NASDAQ: ODD",
    "International Business Machines NASDAQ: IBM",
    "Automatic Data Processing NASDAQ: ADP",
    "Advanced Micro Devices NASDAQ: AMD",
    "Wolfspeed Inc NASDAQ: WOLF",
    "Lam Research Corporation NASDAQ: LRCX",
    "Impinj Inc NASDAQ: PI",
    "Super Micro Computer NASDAQ: SMCI",
    "PagSeguro Digital NASDAQ: PAGS",
    "StoneCo Ltd NASDAQ: STNE",
    "Nextracker Inc NASDAQ: NXT",
    "Zscaler Inc NASDAQ: ZS",
    "Workday Inc NASDAQ: WDAY",
    "HubSpot Inc NASDAQ: HUBS",
    "Bitdeer Technologies Group NASDAQ: BTDR",
    "ServiceNow Inc NASDAQ: NOW",
    "C3.ai Inc NASDAQ: AI",
    "Affirm Holdings NASDAQ: AFRM",
    "Nutanix Inc NASDAQ: NTNX",
    "Core Scientific NASDAQ: CORZ",
    "Knowles Corporation NASDAQ: KN",
    "Intuit Inc NASDAQ: INTU",
    "Western Digital Corporation NASDAQ: WDC",
    "TaskUs Inc NASDAQ: TASK",
    "ACM Research NASDAQ: ACMR",
    "Amphenol Corporation NASDAQ: APH",
    "Okta Inc NASDAQ: OKTA",
    "Neonode Inc NASDAQ: NEON",
    "Amdocs Ltd NASDAQ: DOX",
    "Aehr Test Systems NASDAQ: AEHR",
    "Cisco Systems NASDAQ: CSCO",
    "Nova Ltd NASDAQ: NVMI",
    "Corsair Gaming NASDAQ: CRSR",
    "Semtech Corporation NASDAQ: SMTC",
    "Keysight Technologies NASDAQ: KEYS",
    "Broadcom Inc NASDAQ: AVGO",
    "Ostin Technology Group NASDAQ: OS",
    "LiveRamp Holdings NASDAQ: RAMP",
    "nCino Inc NASDAQ: NCNO",
    "Inseego Corp NASDAQ: INSG",
    "Koss Corporation NASDAQ: KOSS",
    "Applied Optoelectronics NASDAQ: AAOI",
    "Snowflake Inc NASDAQ: SNOW",
    "Autodesk Inc NASDAQ: ADSK",
    "Paysafe Ltd NASDAQ: PSFE",
    "Sunrun Inc NASDAQ: RUN",
    "Unisys Corporation NASDAQ: UIS",
    "AST SpaceMobile NASDAQ: ASTS",
    "ON Semiconductor NASDAQ: ON",
    "Katapult Holdings NASDAQ: KPLT",
    "Adobe Inc NASDAQ: ADBE",
    "Flex Ltd NASDAQ: FLEX",
    "Camtek Ltd NASDAQ: CAMT",
    "QXO Inc NASDAQ: QXO",
    "Arteris Inc NASDAQ: AIP",
    "Viasat Inc NASDAQ: VSAT",
    "Couchbase Inc NASDAQ: BASE",
    "Maxeon Solar Technologies NASDAQ: MAXN",
    "Pagaya Technologies NASDAQ: PGY",
    "Teledyne Technologies NASDAQ: TDY",
    "PAR Technology NASDAQ: PAR",
    "Marvell Technology NASDAQ: MRVL",
    "ePlus inc. NASDAQ: PLUS",
    "GigaCloud Technology NASDAQ: GCT",
    "BlackSky Technology NASDAQ: BKSY",
    "Shift4 Payments NASDAQ: FOUR"
]

# ─── Requests session ───
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
session.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502])))

# ─── Selenium ───
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

# ─── Helpers ───
def _join_ps(ps): return " ".join(p.get_text(" ", strip=True) for p in ps)
def _extract_paragraphs(c: BeautifulSoup) -> str: return _join_ps(c.find_all("p"))
def _clean_body(text: str) -> str:
    return re.sub(r"We are having trouble retrieving.*?Subscribe\s*\.", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

def _from_next_data(soup: BeautifulSoup) -> str:
    node = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not node: return ""
    try:
        data = js.loads(node.string)
        stack: List[Any] = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                art = cur.get("article")
                if isinstance(art, dict):
                    body = art.get("body") or art.get("articleBody")
                    if body:
                        return BeautifulSoup(body, "html.parser").get_text(" ", strip=True)
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
    except Exception:
        pass
    return ""

def _scrape_static(url: str) -> str:
    try:
        r = session.get(url, timeout=10); r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        for tag in [
            {"data-testid": "article-body"}, {"id": "article-body"},
            {"class": re.compile(r"meteredContent")},
            {"name": "articleBody"}
        ]:
            sec = soup.find("section", tag)
            if sec:
                return _extract_paragraphs(sec)

        css_block = soup.find("div", class_=re.compile(r"css-[a-z0-9]+"))
        if css_block and css_block.find("p"):
            return _extract_paragraphs(css_block)

        paras = soup.find_all("p", {"data-testid": "paragraph"})
        if paras:
            return _join_ps(paras)

        next_data = _from_next_data(soup)
        if next_data:
            return next_data

        fallback = soup.find("article") or soup.find("main") or soup
        return _extract_paragraphs(fallback)
    except Exception:
        return ""

def _scrape_with_selenium(url: str) -> str:
    try:
        driver.get(url)
        WebDriverWait(driver, SEL_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article p"))
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

def build_params(company_query: str, page: int, with_filter: bool) -> Dict:
    p = {
        "q": f"{company_query}",
        "begin_date": BEGIN_DATE,
        "end_date": END_DATE,
        "sort": SORT,
        "api-key": API_KEY,
        "page": page,
        "type_of_material": "Article"
    }
    if with_filter and SECTIONS:
        quoted = " ".join(f'"{s}"' for s in SECTIONS)
        p["fq"] = f'(section_name:({quoted}) OR news_desk:({quoted}))'
    return p

# ─── Fetch for one ticker ───
def fetch_articles_for_ticker(company_query: str) -> List[Dict]:
    collected, seen = [], set()
    for use_filter in (True, False if SECTIONS else False):
        r0 = session.get(API_URL, params=build_params(company_query, 0, use_filter), timeout=10)
        r0.raise_for_status()
        resp = r0.json()["response"]
        hits = (resp.get("meta") or resp.get("metadata", {})).get("hits", 0)
        docs0 = resp.get("docs") or []
        if hits == 0 or not docs0:
            if use_filter: continue
            return []
        perpg = len(docs0)
        pages = min(PAGES_TO_FETCH, -(-hits // perpg))
        page_bar = tqdm(range(pages), desc=f"  ↪ Pages for {company_query}", leave=False, unit="page")

        for pg in page_bar:
            r = session.get(API_URL, params=build_params(company_query, pg, use_filter), timeout=10)
            if r.status_code == 429:
                time.sleep(10)
                r = session.get(API_URL, params=build_params(company_query, pg, use_filter), timeout=10)
            r.raise_for_status()
            for d in r.json()["response"]["docs"][:ARTICLES_PER_PAGE]:
                url = d.get("web_url", "")
                if not url or url in seen: continue
                seen.add(url)
                section = d.get("section_name") or d.get("news_desk", "")
                if section not in SECTIONS:
                    continue
                pub = d.get("pub_date") or ""
                date_str = datetime.strptime(pub, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d") if pub else ""
                collected.append({
                    "url": url,
                    "published_date": date_str,
                    "section": section,
                    "headline": d.get("headline", {}).get("main", ""),
                    "abstract": d.get("abstract", ""),
                    "body": get_body(url),
                })
            time.sleep(2)
        break
    return collected

# ─── Main loop with tqdm ───
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for company_query in tqdm(TICKERS, desc="🔍 Processing Tickers", unit="ticker"):
        try:
            articles = fetch_articles_for_ticker(company_query)
            # Use only ticker symbol for filename
            ticker_symbol = company_query.split(":")[-1].strip()
            out_path = os.path.join(OUTPUT_DIR, f"{ticker_symbol}_news.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            tqdm.write(f"✅ {company_query}: Saved {len(articles)} articles → {out_path}")
        except Exception as e:
            tqdm.write(f"❌ Failed for {company_query}: {e}")
    driver.quit()
