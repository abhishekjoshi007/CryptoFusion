import os
import csv
import glob

def combine_all_csvs():
    """Combine all individual ticker CSV files into one"""
    base_dir = "C:/Users/FrontDesk/Desktop/GA/Crypto_Categories_Data"
    all_data = []
    
    # Find all ticker directories
    ticker_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    print(f"Found {len(ticker_dirs)} ticker directories")
    
    csv_files = []
    for ticker_dir in ticker_dirs:
        # Look for CSV files in each ticker directory
        csv_pattern = os.path.join(base_dir, ticker_dir, f"{ticker_dir}_categories.csv")
        if os.path.exists(csv_pattern):
            csv_files.append(csv_pattern)
        else:
            # Fallback: look for any CSV file in the directory
            fallback_pattern = os.path.join(base_dir, ticker_dir, "*.csv")
            fallback_files = glob.glob(fallback_pattern)
            if fallback_files:
                csv_files.extend(fallback_files)
    
    print(f"Found {len(csv_files)} CSV files to combine")
    
    fieldnames = ["Ticker", "Coin Name", "CoinGecko ID", "Category", "Category Rank", "Description", "All Categories"]
    
    # Read all CSV files
    for csv_file in csv_files:
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)
            print(f"Read {csv_file}")
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    # Try to save combined file with different names if needed
    for attempt in range(5):
        try:
            filename = "all_crypto_categories.csv" if attempt == 0 else f"all_crypto_categories_{attempt}.csv"
            output_path = os.path.join(base_dir, filename)
            
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
            
            print(f"Successfully saved {len(all_data)} rows to {output_path}")
            
            # Print summary
            print(f"\nSUMMARY:")
            print(f"Total rows: {len(all_data)}")
            print(f"Unique tickers: {len(set(row['Ticker'] for row in all_data))}")
            print(f"Unique categories: {len(set(row['Category'] for row in all_data if row['Category'] != 'Unknown'))}")
            
            return
            
        except PermissionError:
            print(f"Permission denied for {filename}, trying alternative...")
            continue
        except Exception as e:
            print(f"Error: {e}")
            return
    
    print("Could not save file after 5 attempts. Please close any open Excel files and try again.")

if __name__ == "__main__":
    combine_all_csvs()