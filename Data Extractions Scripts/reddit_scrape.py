#!pip install praw pandas unidecode
import os
import time
import json
import praw
import prawcore
import re
import random  # Added this import
from unidecode import unidecode
import pandas as pd
from datetime import datetime

# Reddit API credentials
CLIENT_ID = "qMC5FCxaIkKR1of9AzkYgg"
CLIENT_SECRET = "2gVN2nq-gibv8cHAQghN1UXV4nbYGQ"
USER_AGENT = "stock-analysis-v1"

# Search parameters
SUBREDDITS = ["stocks", "investing", "wallstreetbets", "crypto", "cryptocurrency"]
START_DATE = datetime(2024, 8, 1)
END_DATE = datetime(2024, 10, 31)

# Load the CSV file containing tickers (stocks or crypto)
file_path = "/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/CSV/Crypto.csv"  
df = pd.read_csv(file_path)
tickers = df['Ticker'].tolist()

# Initialize Reddit instance
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
)

def clean_text(text):
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"[^\w\s,.!?]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def to_unix_timestamp(date):
    return int(date.timestamp())

start_timestamp = to_unix_timestamp(START_DATE)
end_timestamp = to_unix_timestamp(END_DATE)

def scrape_ticker(ticker):
    print(f"Scraping data for ticker: {ticker}...")
    data = []
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.search(ticker, sort="new", time_filter="all", limit=50):
            submission_date = datetime.utcfromtimestamp(submission.created_utc)
            if START_DATE <= submission_date <= END_DATE:
                try:
                    submission.comments.replace_more(limit=None)
                    replies = []
                    for comment in submission.comments.list():
                        cleaned_body = clean_text(unidecode(comment.body))
                        if cleaned_body:
                            replies.append({"text": cleaned_body})
                    user_reputation = 0
                    if submission.author:
                        try:
                            user_reputation = getattr(submission.author, "link_karma", 0)
                        except AttributeError:
                            user_reputation = 0
                    data.append({
                        "time": submission_date.strftime('%Y-%m-%d'),
                        "replies_count": len(replies),
                        "rank": {
                            "ranks_up": submission.ups,
                            "ranks_down": submission.downs,
                            "ranked_by_current_user": submission.score,
                        },
                        "replies": replies,
                        "content": [{
                            "text": clean_text(unidecode(submission.title))
                        }],
                        "best_score": submission.score,
                        "total_replies_count": len(replies),
                        "user_reputation": user_reputation,
                        "additional_data": {
                            "labels": {
                                "ids": ["BULLISH"],  # Placeholder label
                                "section": "stock"
                            }
                        }
                    })
                except Exception as e:
                    print(f"Error fetching comments for submission in {ticker}: {e}")
            # Sleep to respect rate limits
            time.sleep(random.uniform(2, 5))
    return data

def main():
    # Main output folder
    base_output_dir = "/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Combined Data /Data Cry"
    os.makedirs(base_output_dir, exist_ok=True)

    for ticker in tickers:
        try:
            scraped_data = scrape_ticker(ticker)
            # Create a subfolder for this ticker
            ticker_folder = os.path.join(base_output_dir, ticker)
            os.makedirs(ticker_folder, exist_ok=True)
            output_file = os.path.join(
                ticker_folder,
                f"{ticker}_reddit_comments.json"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(scraped_data, f, ensure_ascii=False, indent=4)
            print(f"Data for {ticker} saved to {output_file}.")
        except prawcore.exceptions.TooManyRequests:
            print(f"Rate limit hit for {ticker}. Waiting for 60 seconds...")
            time.sleep(60)
        except Exception as e:
            print(f"An error occurred with {ticker}: {e}")

if __name__ == "__main__":
    main()
