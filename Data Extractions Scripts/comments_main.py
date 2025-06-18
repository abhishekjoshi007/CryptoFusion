import os
import asyncio
import aiohttp
import json
import time
from datetime import datetime
import pandas as pd
import re  # For cleaning HTML tags

api_url = "https://api-2-0.spot.im/v1.0.0/conversation/read"
csv_path = '/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/CSV/Crypto.csv'
base_dir = '/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Historic Data Cry'

# Configuration parameters
batch_size = 800         # Number of comments per batch (ensure API supports this)
max_batches = 9500        # Maximum number of batches to scan
concurrency = 5          # Number of concurrent requests
jump_multiplier = 5      # (Not used directly here but could be used for dynamic offset jumps)

def convert_timestamp(unix_timestamp):
    """Convert Unix timestamp to human-readable date."""
    try:
        return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d')
    except Exception as e:
        print(f"DEBUG: Invalid timestamp {unix_timestamp} - {e}")
        return None

def clean_html_tags(text):
    """Remove HTML tags like <p>, <br>, etc., from a string."""
    clean_text = re.sub(r'<[^>]*>', '', text)
    return clean_text.strip()

def clean_comment_data(comment):
    """Clean the comment data into the desired format."""
    cleaned_data = {
        "time": convert_timestamp(comment.get("time")),
        "replies_count": comment.get("replies_count", 0),
        "rank": {
            "ranks_up": comment.get("rank", {}).get("ranks_up", 0),
            "ranks_down": comment.get("rank", {}).get("ranks_down", 0),
            "ranked_by_current_user": comment.get("rank", {}).get("ranked_by_current_user", 0)
        },
        "replies": [],
        "content": [],
        "best_score": comment.get("best_score", 0),
        "total_replies_count": comment.get("total_replies_count", 0),
        "user_reputation": comment.get("user_reputation", 0),
        "additional_data": comment.get("additional_data", {})
    }

    # Process replies recursively
    if "replies" in comment and comment["replies"]:
        for reply in comment["replies"]:
            cleaned_data["replies"].append(clean_comment_data(reply))

    # Process main content
    if "content" in comment and comment["content"]:
        for content_item in comment["content"]:
            cleaned_data["content"].append({"text": clean_html_tags(content_item.get("text", ""))})

    return cleaned_data

async def fetch_batch(session, payload, headers):
    """Fetch a single batch with the given offset."""
    async with session.post(api_url, json=payload, headers=headers) as response:
        if response.status != 200:
            print(f"Failed to fetch data: Status code {response.status}")
            return None
        return await response.json()

async def fetch_comments_within_date_range_async(payload, headers, start_date, end_date):
    """Fetch all comments dated start_date … end_date (inclusive)."""
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt   = datetime.strptime(end_date,   '%Y-%m-%d')
    cleaned, batches, offset = [], 0, payload["offset"]

    async with aiohttp.ClientSession() as session:
        while batches < max_batches:
            # -------- launch CONCURRENCY parallel requests -------------
            tasks = [
                fetch_batch(
                    session,
                    dict(payload, offset=offset + i*batch_size, count=batch_size),
                    headers
                )
                for i in range(concurrency)
            ]
            responses = await asyncio.gather(*tasks)
            empty = True

            # -------- handle every response ----------------------------
            for res in responses:
                if not res or isinstance(res, Exception):
                    continue
                comments = res.get("conversation", {}).get("comments", [])
                if not comments:
                    continue
                empty = False

                newest = datetime.utcfromtimestamp(comments[0]['written_at'])
                oldest = datetime.utcfromtimestamp(comments[-1]['written_at'])
                print(f"DEBUG: {newest} … {oldest}")

                # (a) batch wholly AFTER window  → skip
                if newest > end_dt and oldest > end_dt:
                    continue
                # (b) batch wholly BEFORE window → done
                if newest < start_dt and oldest < start_dt:
                    return cleaned

                # (c) overlap → copy in-range comments
                for c in comments:
                    t = datetime.utcfromtimestamp(c['written_at'])
                    if start_dt <= t <= end_dt:
                        cleaned.append(clean_comment_data(c))

            # if every page was empty the thread is exhausted
            if empty:
                break

            offset   += concurrency * batch_size
            batches  += concurrency
            print(f"DEBUG: kept {len(cleaned)} comments after {batches} batches")
            await asyncio.sleep(1)   # gentle rate-limit pause

    return cleaned

def main():
    data = pd.read_csv(csv_path)
    total_tickers = len(data)
    os.makedirs(base_dir, exist_ok=True)

    # Set desired date range
    start_date = '2023-06-01'
    end_date = '2025-06-01'

    for idx, row in data.iterrows():
        payload = {
            "conversation_id": row['Conversation Id'],
            "count": batch_size,
            "offset": 0,
            "sort_by": "newest",
        }
        api_headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "x-spot-id": row['X-Spot-Id'],
            "x-post-id": row['X-Post-Id'],
        }

        print(f"\nProcessing {idx + 1}/{total_tickers}: {row['Ticker']} ({row['Coin Name']})")
        # Run the asynchronous batch fetching
        cleaned_comments = asyncio.run(fetch_comments_within_date_range_async(payload, api_headers, start_date, end_date))

        ticker_dir = os.path.join(base_dir, row['Ticker'])
        os.makedirs(ticker_dir, exist_ok=True)
        filename = os.path.join(ticker_dir, f"{row['Ticker']}_comments.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_comments, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(cleaned_comments)} cleaned comments for {row['Ticker']} to {filename}")

if __name__ == "__main__":
    main()
