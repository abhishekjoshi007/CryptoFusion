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
base_dir = '/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Combined Data /Historic Data Cry'

# Configuration parameters
batch_size = 500         # Number of comments per batch (ensure API supports this)
max_batches = 1500        # Maximum number of batches to scan
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
    """
    Asynchronously fetch comments within the desired date range.
    The function launches multiple batch requests concurrently.
    """
    desired_start_obj = datetime.strptime(start_date, '%Y-%m-%d')
    desired_end_obj = datetime.strptime(end_date, '%Y-%m-%d')
    cleaned_comments = []
    batch_count = 0
    current_offset = payload["offset"]

    async with aiohttp.ClientSession() as session:
        while batch_count < max_batches:
            tasks = []
            # Prepare a group of concurrent batch requests
            for i in range(concurrency):
                batch_payload = payload.copy()
                batch_payload["offset"] = current_offset + i * batch_size
                batch_payload["count"] = batch_size
                tasks.append(fetch_batch(session, batch_payload, headers))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Process each response
            for r in responses:
                if r is None or isinstance(r, Exception):
                    continue
                batch_comments = r.get("conversation", {}).get("comments", [])
                if not batch_comments:
                    continue

                # Determine the batch's date range
                batch_newest = datetime.utcfromtimestamp(batch_comments[0]['written_at'])
                batch_oldest = datetime.utcfromtimestamp(batch_comments[-1]['written_at'])
                print(f"DEBUG: Batch date range: {batch_newest} to {batch_oldest}")

                # Hierarchical check: skip if entire batch is out-of-range
                if batch_newest.year > desired_end_obj.year:
                    print("DEBUG: Entire batch's year is newer than desired end year. Skipping batch.")
                    continue
                if batch_oldest.year < desired_start_obj.year:
                    print("DEBUG: Entire batch's year is older than desired start year. Ending fetch.")
                    return cleaned_comments

                # Month check (when on the boundary year)
                if batch_newest.year == desired_end_obj.year:
                    if batch_newest.month > desired_end_obj.month and batch_oldest.month > desired_end_obj.month:
                        print("DEBUG: Entire batch's month is newer than desired end month. Skipping batch.")
                        continue
                if batch_oldest.year == desired_start_obj.year:
                    if batch_newest.month < desired_start_obj.month and batch_oldest.month < desired_start_obj.month:
                        print("DEBUG: Entire batch's month is older than desired start month. Ending fetch.")
                        return cleaned_comments

                # Day check (when in the boundary month)
                if (batch_newest.year == desired_end_obj.year and batch_newest.month == desired_end_obj.month):
                    if batch_newest.day > desired_end_obj.day and batch_oldest.day > desired_end_obj.day:
                        print("DEBUG: Entire batch's day is newer than desired end day. Skipping batch.")
                        continue
                if (batch_oldest.year == desired_start_obj.year and batch_oldest.month == desired_start_obj.month):
                    if batch_newest.day < desired_start_obj.day and batch_oldest.day < desired_start_obj.day:
                        print("DEBUG: Entire batch's day is older than desired start day. Ending fetch.")
                        return cleaned_comments

                # Process individual comments in the batch that fall in range
                for comment in batch_comments:
                    if 'written_at' in comment:
                        comment_date = datetime.utcfromtimestamp(comment['written_at'])
                        print(f"DEBUG: Comment date: {comment_date}")
                        if desired_start_obj <= comment_date <= desired_end_obj:
                            cleaned_comments.append(clean_comment_data(comment))
                        elif comment_date < desired_start_obj:
                            print(f"DEBUG: Stopping fetch, comment date {comment_date} is before {start_date}.")
                            return cleaned_comments

            # Update the offset based on the number of concurrent batches processed
            batch_count += concurrency
            current_offset += concurrency * batch_size
            print(f"DEBUG: Fetched {len(cleaned_comments)} cleaned comments so far after {batch_count} batches.")
            await asyncio.sleep(1)  # Pause to respect rate limits

    return cleaned_comments

def main():
    data = pd.read_csv(csv_path)
    total_tickers = len(data)
    os.makedirs(base_dir, exist_ok=True)

    # Set desired date range
    start_date = '2024-08-01'
    end_date = '2024-11-01'

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
