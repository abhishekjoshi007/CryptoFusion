import os, time, math, csv, requests
from datetime import datetime
from typing import List, Dict

API_URL    = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
API_KEY    = "OYUirWyf1UZwehhxIQQFHTkgQ4DWOutK"
TICKERS    = ["AAPL"]
BASE_DIR   = "/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/News"
HEADERS    = {"Accept": "application/json"}
BEGIN_DATE = "20240801"
END_DATE   = "20241031"
SORT       = "oldest"

def fetch_data_for_ticker(ticker: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    params = {
        "q":          f"{ticker} Stock",
        "begin_date": BEGIN_DATE,
        "end_date":   END_DATE,
        "sort":       SORT,
        "api-key":    API_KEY,
        "page":       0
    }

    try:
        # initial request
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # drill into metadata
        meta = data["response"]["metadata"]
        total_hits = meta.get("hits", 0)
        docs = data["response"].get("docs", [])
        per_page = len(docs)
        if total_hits == 0 or per_page == 0:
            print("No articles found for", ticker)
            return rows

        total_pages = math.ceil(total_hits / per_page)
        print(f"→ {total_hits} hits over {total_pages} pages")

        for page in range(total_pages):
            params["page"] = page
            resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            docs = data["response"].get("docs", [])

            for doc in docs:
                pub_date = doc.get("pub_date", "")
                date_str = ""
                if pub_date:
                    date_str = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S%z")\
                                      .strftime("%Y-%m-%d")

                rows.append({
                    "Date":          date_str,
                    "URL":           doc.get("web_url", ""),
                    "News Title":    doc.get("headline", {}).get("main", ""),
                    "News Abstract": doc.get("abstract", ""),
                    "News Content":  doc.get("snippet", "")     # <<< use snippet here
                })

            print(f"‣ Page {page+1}/{total_pages} fetched ({len(docs)} articles)")
            time.sleep(1)

    except Exception as e:
        print("Error fetching", ticker, ":", e)

    return rows

def save_to_csv(ticker: str, rows: List[Dict[str, str]]) -> None:
    out_dir = os.path.join(BASE_DIR, ticker); os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{ticker}_news_url.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date","URL","News Title","News Abstract","News Content"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} rows to {path}")

def main():
    for t in TICKERS:
        articles = fetch_data_for_ticker(t)
        save_to_csv(t, articles)

if __name__ == "__main__":
    main()
