import shutil
from pathlib import Path

def sync_news_articles(ticker_root: str, news_source: str, move: bool = False):
    """
    Syncs *_news.json files into respective ticker folders under ticker_root.

    Parameters:
    - ticker_root: Root folder containing ticker subfolders (e.g., Historic Data Cry 2).
    - news_source: Folder containing {TICKER}_news.json files.
    - move: If True, move files instead of copying.
    """
    ticker_root_path = Path(ticker_root)
    news_source_path = Path(news_source)

    for news_file in news_source_path.glob('*_news.json'):
        ticker_name = news_file.stem.replace('_news', '')
        ticker_folder = ticker_root_path / ticker_name

        if ticker_folder.exists():
            target_path = ticker_folder / news_file.name
            ticker_folder.mkdir(parents=True, exist_ok=True)
            if move:
                shutil.move(str(news_file), str(target_path))
            else:
                shutil.copy2(str(news_file), str(target_path))
            print(f"✓ {'Moved' if move else 'Copied'}: {news_file.name} → {ticker_folder}")
        else:
            print(f"⚠️ Folder not found for: {ticker_name}")

# Example usage
if __name__ == "__main__":
    sync_news_articles(
        ticker_root="/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/Historic Data Cry",
        news_source="/Users/abhishekjoshi/Documents/GitHub/Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/News Articles Json",
        move=False  # Set to True if you want to move instead of copy
    )
