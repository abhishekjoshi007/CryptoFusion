#This code works for both stock and crypto

import yfinance as yf
import pandas as pd
import os

def handle_failed_ticker(ticker, csv_path, base_folder_name):
    """
    Identifies tickers with failed data extraction, prevents subdirectory creation,
    and removes the ticker from the input CSV file.
    
    Args:
        ticker (str): The ticker symbol that failed data extraction
        csv_path (str): Path to the input CSV file containing tickers
        base_folder_name (str): Path to the base folder for data storage
    """
    print(f"Handling failed ticker: {ticker}")
    
    # Check if subdirectory exists for the ticker and remove it if it does
    ticker_folder = os.path.join(base_folder_name, ticker)
    if os.path.exists(ticker_folder):
        try:
            os.rmdir(ticker_folder)
            print(f"Removed empty subdirectory for {ticker} at {ticker_folder}")
        except OSError as e:
            print(f"Failed to remove subdirectory for {ticker}: {e}")
    
    # Remove the ticker from the CSV file
    try:
        # Read the current CSV
        tickers_df = pd.read_csv(csv_path)
        
        # Filter out the failed ticker
        updated_df = tickers_df[tickers_df["Ticker"] != ticker]
        
        # Save the updated CSV back to the original file
        updated_df.to_csv(csv_path, index=False)
        print(f"Removed {ticker} from {csv_path}")
    except Exception as e:
        print(f"Error updating CSV file {csv_path} for {ticker}: {e}")

# 1) READ TICKERS FROM CSV
#    Replace "coin_tickers.csv" with your actual filename/path
tickers_df = pd.read_csv("C:/Users/Pushkarsikharam/Desktop/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction-main/CSV/Crypto.csv")  # CSV has columns like "Coin Name,Ticker,..."
# 2) CONFIGURATION
start_date = "2023-06-01"
end_date   = "2025-06-01"
base_folder_name = "C:/Users/Pushkarsikharam/Desktop/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction-main/Combined Data/Historic Data Cry"  # Main folder

# Create base folder if it doesn't exist
if not os.path.exists(base_folder_name):
    os.makedirs(base_folder_name)

# 3) LOOP OVER EACH ROW, DOWNLOAD & SAVE DATA
for idx, row in tickers_df.iterrows():
    # Grab the ticker symbol from the CSV row
    ticker = row["Ticker"]  # e.g. "BTC-USD"

    print(f"Processing {ticker}...")

    # 3a) Download Data
    raw_data = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        group_by="ticker",   # multi-index columns under ticker name
        auto_adjust=False    # includes both "Close" (raw) and "Adj Close"
    )

    # If nothing returned (e.g. invalid ticker or no data), skip
    if raw_data.empty:
        print(f"No data returned for {ticker}. Skipping.")
        handle_failed_ticker(ticker, "C:/Users/Pushkarsikharam/Desktop/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction-main/CSV/Crypto.csv", base_folder_name)
        continue

    # 3b) Flatten multi-index columns for single ticker
    #     Typically columns are: "Open", "High", "Low", "Close", "Adj Close", "Volume"
    try:
        data = raw_data[ticker].copy()  # If multi-index
    except KeyError:
        # If yfinance returns single-level columns
        data = raw_data.copy()

    # 3c) Convert Date from index to a normal column
    data.reset_index(inplace=True)

    # 3d) Rename "Adj Close" → "Price"
    if "Adj Close" in data.columns:
        data.rename(columns={"Adj Close": "Adj Close"}, inplace=True)

    # 3e) Insert a "Ticker" column
    if "Ticker" not in data.columns:
        data.insert(1, "Ticker", ticker)

    # 3f) Reorder columns: Date, Ticker, Open, High, Low, Close, Adj Close, Volume
    desired_order = ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    missing_cols = [col for col in desired_order if col not in data.columns]
    if missing_cols:
        print(f"Missing columns {missing_cols} for {ticker}. Skipping.")
        continue

    data = data[desired_order]

    # 4) SAVE TO SUBFOLDER NAMED AFTER THE TICKER
    #    e.g. "Historic DATA/BTC-USD/BTC-USD.csv"
    ticker_folder = os.path.join(base_folder_name, ticker)  # e.g. "Historic DATA/BTC-USD"
    os.makedirs(ticker_folder, exist_ok=True)

    # Filename = TICKER.csv (e.g. "BTC-USD.csv")
    filename = f"{ticker}.csv"
    filepath = os.path.join(ticker_folder, filename)
    data.to_csv(filepath, index=False)

    print(f"Saved {ticker} data to {filepath}")

print("Done!")
