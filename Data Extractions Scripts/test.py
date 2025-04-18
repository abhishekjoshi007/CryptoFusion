import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_fin_news(ticker: str) -> pd.DataFrame:
    """Fetch and parse Finviz news for a given ticker into a DataFrame."""
    # be polite to the server
    time.sleep(5)
    
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    
    # parse the news table
    soup = BeautifulSoup(resp.text, "lxml")
    news_table = soup.find(id="news-table")
    df = pd.read_html(str(news_table))[0]
    df.columns = ["datetime_str", "News"]
    
    # split into date vs. time
    split_dt = df["datetime_str"].str.split(" ", n=1, expand=True)
    df["date_part"] = split_dt[0].where(~split_dt[0].str.contains(":"), None)
    df["time_part"] = split_dt[1].fillna(split_dt[0])
    
    # map relative dates to absolute
    today = datetime.now()
    mapping = {
        "Today": today.strftime("%b-%d-%y"),
        "Yesterday": (today - timedelta(days=1)).strftime("%b-%d-%y")
    }
    df["date_part"] = df["date_part"].replace(mapping).ffill()
    
    # build real timestamps
    df["Date"] = pd.to_datetime(
        df["date_part"] + " " + df["time_part"],
        format="%b-%d-%y %I:%M%p"
    )
    
    df["Ticker"] = ticker
    return df[["Date", "News", "Ticker"]]

if __name__ == "__main__":
    # 1) List the tickers you want to scrape
    tickers = ["AAPL", "ZM", "GOOG"]
    
    # 2) Fetch each and collect
    all_news = []
    for t in tickers:
        print(f"Fetching news for {t}…")
        df = get_fin_news(t)
        all_news.append(df)
    
    # 3) Combine into one DataFrame
    full_df = pd.concat(all_news, ignore_index=True)
    
    # 4) Save to CSV
    full_df.to_csv("multi_ticker_news.csv", index=False)
    print("Saved all news to multi_ticker_news.csv")
    
    # 5) Print summaries
    print("\nFirst 5 rows:")
    print(full_df.head(), "\n")
    
    print("Last 5 rows:")
    print(full_df.tail(), "\n")
    
    print(f"Total headlines fetched: {full_df.shape[0]}")
