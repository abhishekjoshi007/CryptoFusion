import os, time, csv, requests
from typing import List, Dict, Optional

API_URL = "https://api.coingecko.com/api/v3"
# Raw ticker list from user (with -USD suffix)
RAW_TICKERS = "BTC-USDETH-USDUSDT-USDBNB-USDXRP-USDUSDC-USDSOL-USDSTETH-USDADA-USDDOGE-USDTRX-USDTON-USDLINK-USDAVAX-USDMATIC-USDDOT-USDWBTC-USDDAI-USDLTC-USDSHIB-USDBCH-USDUNI-USDLEO-USDOKB-USDTUSD-USDXLM-USDXMR-USDKAS-USDETC-USDATOM-USDCRO-USDLDO-USDFIL-USDHBAR-USDAPT-USDICP-USDNEAR-USDBUSD-USDRUNE-USDOP-USDVET-USDMNT-USDQNT-USDAAVE-USDMKR-USDINJ-USDARB-USDRNDR-USDRETH-USDSNX-USDEGLD-USDALGO-USDFLOW-USDTHETA-USDBSV-USDSTX-USDFTM-USDTIA-USDSAND-USDWBT-USDAXS-USDBGB-USDEOS-USDNEO-USDMANA-USDUSDD-USDKCS-USDXTZ-USDKAVA-USDXDC-USDFDUSD-USDFRAX-USDGALA-USDKLAY-USDPYTH-USDMINA-USDETHDYDX-USDXRD-USDILV-USDFRXETH-USDTKX-USDGT-USDCHEEL-USDWEMIX-USDBLUR-USDFET-USDCAKE-USDXEC-USDRPL-USDIOTA-USDAPE-USDFXS-USDSUI-USDCFX-USDAR-USDCRV-USDRLB-USDGNO-USDCHZ-USDGAS-USDXAUT-USDGMX-USDTWT-USDHT-USDPAXG-USDUSDP-USDORDI-USDSFRXETH-USDCWBTC-USDBTT-USDLUNC-USDCBETH-USDNEXO-USDKUJI-USDZEC-USDOSMO-USDWOO-USDBEAM-USDCSPR-USDAKT-USD1INCH-USDAGIX-USDAZERO-USDROSE-USDZIL-USDASTR-USDDASH-USDMSOL-USDFLOKI-USDHBTC-USDSEI-USDQTUM-USDFLR-USDXEM-USDNFT-USDHNT-USDBAT-USDWLD-USDMX-USDCVX-USDBDX-USDSKL-USDBTG-USDARK-USDCORGIAI-USDSFP-USDJST-USDTFUEL-USDYFI-USDENJ-USDHOT-USDCELO-USDOKT-USDLRC-USDFTN-USDSTSOL-USDJASMY-USDANKR-USDXCH-USDGLM-USDICX-USDSC-USDTRB-USDELG-USDDCR-USDPRIME-USDDFI-USDENS-USDELF-USDIOTX-USDKSM-USDLUSD-USDANT-USDAUDIO-USDSUSHI-USDWAXP-USDBORG-USDWAVES-USDOCEAN-USDFNSA-USDRVN-USDMEME-USDSXP-USDLPT-USDGLMR-USDTEL-USDBAND-USDDEXE-USDOHM-USD"

# Extract ticker symbols by splitting on "-USD"
TICKERS = [ticker for ticker in RAW_TICKERS.split("-USD") if ticker]
BASE_DIR = "C:/Users/FrontDesk/Desktop/GA/Crypto_Categories_Data"
HEADERS = {"Accept": "application/json"}
RATE_LIMIT_DELAY = 6  # seconds between requests for free tier

# Manual mappings for common tickers to CoinGecko IDs
TICKER_TO_ID = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    'MATIC': 'matic-network',
    'SOL': 'solana',
    'DOT': 'polkadot',
    'LTC': 'litecoin',
    'USDT': 'tether',
    'USDC': 'usd-coin',
    'STETH': 'staked-ether',
    'WBTC': 'wrapped-bitcoin',
    'TRX': 'tron',
    'TON': 'toncoin',
    'LINK': 'chainlink',
    'AVAX': 'avalanche-2',
    'DAI': 'dai',
    'SHIB': 'shiba-inu',
    'BCH': 'bitcoin-cash',
    'UNI': 'uniswap',
    'LEO': 'leo-token',
    'OKB': 'okb',
    'XLM': 'stellar',
    'XMR': 'monero',
    'ETC': 'ethereum-classic',
    'ATOM': 'cosmos',
    'CRO': 'crypto-com-chain',
    'LDO': 'lido-dao',
    'FIL': 'filecoin',
    'HBAR': 'hedera-hashgraph',
    'APT': 'aptos',
    'ICP': 'internet-computer',
    'NEAR': 'near',
    'OP': 'optimism',
    'VET': 'vechain',
    'AAVE': 'aave',
    'MKR': 'maker',
    'INJ': 'injective-protocol',
    'ARB': 'arbitrum',
    'RNDR': 'render-token',
    'TUSD': 'trueusd',
    'KAS': 'kaspa',
    'MNT': 'mantle',
    'QNT': 'quant-network',
    'RETH': 'rocket-pool-eth',
    'SNX': 'havven',
    'EGLD': 'elrond-erd-2',
    'ALGO': 'algorand',
    'FLOW': 'flow',
    'THETA': 'theta-token',
    'BSV': 'bitcoin-sv',
    'STX': 'blockstack',
    'FTM': 'fantom',
    'TIA': 'celestia',
    'SAND': 'the-sandbox',
    'WBT': 'whitebit',
    'AXS': 'axie-infinity',
    'BGB': 'bitget-token',
    'EOS': 'eos',
    'NEO': 'neo',
    'MANA': 'decentraland',
    'USDD': 'usdd',
    'KCS': 'kucoin-shares',
    'XTZ': 'tezos',
    'KAVA': 'kava',
    'XDC': 'xdce-crowd-sale',
    'FDUSD': 'first-digital-usd',
    'FRAX': 'frax',
    'GALA': 'gala',
    'KLAY': 'klaytn',
    'PYTH': 'pyth-network',
    'MINA': 'mina-protocol',
    'DYDX': 'dydx',
    'XRD': 'radix',
    'ILV': 'illuvium',
    'FRXETH': 'frax-ether',
    'TKX': 'tokenize-xchange',
    'GT': 'gatechain-token',
    'CHEEL': 'cheelee',
    'WEMIX': 'wemix-token',
    'BLUR': 'blur',
    'FET': 'fetch-ai',
    'CAKE': 'pancakeswap-token',
    'XEC': 'ecash',
    'RPL': 'rocket-pool',
    'IOTA': 'iota',
    'APE': 'apecoin',
    'FXS': 'frax-share',
    'SUI': 'sui',
    'CFX': 'conflux-token',
    'AR': 'arweave',
    'CRV': 'curve-dao-token',
    'RLB': 'rollbit-coin',
    'GNO': 'gnosis',
    'CHZ': 'chiliz',
    'GAS': 'gas',
    'XAUT': 'tether-gold',
    'GMX': 'gmx',
    'TWT': 'trust-wallet-token',
    'HT': 'huobi-token',
    'PAXG': 'pax-gold',
    'USDP': 'paxos-standard',
    'ORDI': 'ordinals',
    'SFRXETH': 'staked-frax-ether',
    'CWBTC': 'wrapped-bitcoin-celo',
    'BTT': 'bittorrent',
    'LUNC': 'terra-luna-classic',
    'CBETH': 'coinbase-wrapped-staked-eth',
    'NEXO': 'nexo',
    'KUJI': 'kujira',
    'ZEC': 'zcash',
    'OSMO': 'osmosis',
    'WOO': 'woo-token',
    'BEAM': 'beam',
    'CSPR': 'casper-network',
    'AKT': 'akash-network',
    '1INCH': '1inch',
    'AGIX': 'singularitynet',
    'AZERO': 'aleph-zero',
    'ROSE': 'oasis-network',
    'ZIL': 'zilliqa',
    'ASTR': 'astar',
    'DASH': 'dash',
    'MSOL': 'marinade-staked-sol',
    'FLOKI': 'floki',
    'HBTC': 'huobi-btc',
    'SEI': 'sei-network',
    'QTUM': 'qtum',
    'FLR': 'flare-networks',
    'XEM': 'nem',
    'NFT': 'apenft',
    'HNT': 'helium',
    'BAT': 'basic-attention-token',
    'WLD': 'worldcoin-wld',
    'CVX': 'convex-finance',
    'BDX': 'beldex',
    'SKL': 'skale',
    'BTG': 'bitcoin-gold',
    'ARK': 'ark',
    'CORGIAI': 'corgiiai',
    'SFP': 'safpal',
    'JST': 'just',
    'TFUEL': 'theta-fuel',
    'YFI': 'yearn-finance',
    'ENJ': 'enjincoin',
    'HOT': 'holo',
    'CELO': 'celo',
    'OKT': 'okt-chain',
    'LRC': 'loopring',
    'FTN': 'fasttoken',
    'STSOL': 'lido-staked-sol',
    'JASMY': 'jasmycoin',
    'ANKR': 'ankr',
    'XCH': 'chia',
    'GLM': 'golem',
    'ICX': 'icon',
    'SC': 'siacoin',
    'TRB': 'tellor',
    'ELG': 'escoin-token',
    'DCR': 'decred',
    'PRIME': 'echelon-prime',
    'DFI': 'defichain',
    'ENS': 'ethereum-name-service',
    'ELF': 'aelf',
    'IOTX': 'iotex',
    'KSM': 'kusama',
    'LUSD': 'liquity-usd',
    'ANT': 'aragon',
    'AUDIO': 'audius',
    'SUSHI': 'sushi',
    'WAXP': 'wax',
    'BORG': 'swissborg',
    'WAVES': 'waves',
    'OCEAN': 'ocean-protocol',
    'FNSA': 'finschia',
    'RVN': 'ravencoin',
    'MEME': 'memecoin',
    'SXP': 'swipe',
    'LPT': 'livepeer',
    'GLMR': 'moonbeam',
    'TEL': 'telcoin',
    'BAND': 'band-protocol',
    'DEXE': 'dexe',
    'OHM': 'olympus'
}

def get_coin_id(ticker: str) -> Optional[str]:
    """Get CoinGecko coin ID for a ticker symbol"""
    # First check manual mappings
    if ticker.upper() in TICKER_TO_ID:
        return TICKER_TO_ID[ticker.upper()]
    
    # If not found, search via API
    try:
        url = f"{API_URL}/coins/list"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        coins = resp.json()
        
        for coin in coins:
            if coin['symbol'].upper() == ticker.upper():
                return coin['id']
                
    except Exception as e:
        print(f"Error searching for {ticker}: {e}")
    
    return None

def fetch_categories_for_ticker(ticker: str) -> List[Dict[str, str]]:
    """Fetch category/sector data for a cryptocurrency ticker"""
    rows: List[Dict[str, str]] = []
    
    try:
        # Get coin ID
        coin_id = get_coin_id(ticker)
        if not coin_id:
            print(f"Could not find CoinGecko ID for {ticker}")
            return rows
        
        print(f"Found coin ID '{coin_id}' for {ticker}")
        
        # Fetch coin data with categories
        url = f"{API_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "false",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract categories
        categories = data.get('categories', [])
        coin_name = data.get('name', ticker)
        symbol = data.get('symbol', ticker).upper()
        description = data.get('description', {}).get('en', '')[:200] + '...' if data.get('description', {}).get('en') else ''
        
        if categories:
            for i, category in enumerate(categories):
                if category:  # Skip None values
                    rows.append({
                        "Ticker": symbol,
                        "Coin Name": coin_name,
                        "CoinGecko ID": coin_id,
                        "Category": category,
                        "Category Rank": i + 1,  # 1 = primary category
                        "Description": description if i == 0 else "",  # Only include description once
                        "All Categories": "; ".join([cat for cat in categories if cat])
                    })
            print(f"Found {len(categories)} categories for {ticker}: {', '.join([cat for cat in categories if cat])}")
        else:
            # No categories found, add row with unknown
            rows.append({
                "Ticker": symbol,
                "Coin Name": coin_name,
                "CoinGecko ID": coin_id,
                "Category": "Unknown",
                "Category Rank": 1,
                "Description": description,
                "All Categories": "Unknown"
            })
            print(f"No categories found for {ticker}")
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            return fetch_categories_for_ticker(ticker)  # Retry
        else:
            print(f"HTTP Error fetching {ticker}: {e}")
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    
    return rows

def save_to_csv(ticker: str, rows: List[Dict[str, str]]) -> None:
    """Save category data to CSV file"""
    out_dir = os.path.join(BASE_DIR, ticker)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{ticker}_categories.csv")
    
    fieldnames = ["Ticker", "Coin Name", "CoinGecko ID", "Category", "Category Rank", "Description", "All Categories"]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Saved {len(rows)} rows to {path}")

def save_combined_csv(all_data: List[Dict[str, str]]) -> None:
    """Save all data to a single combined CSV file"""
    os.makedirs(BASE_DIR, exist_ok=True)
    path = os.path.join(BASE_DIR, "all_crypto_categories.csv")
    
    fieldnames = ["Ticker", "Coin Name", "CoinGecko ID", "Category", "Category Rank", "Description", "All Categories"]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"Saved combined data ({len(all_data)} rows) to {path}")

def print_summary(all_data: List[Dict[str, str]]) -> None:
    """Print summary statistics"""
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    total_coins = len(set(row['Ticker'] for row in all_data))
    total_categories = len(all_data)
    unique_categories = len(set(row['Category'] for row in all_data if row['Category'] != 'Unknown'))
    
    print(f"Total coins processed: {total_coins}")
    print(f"Total category entries: {total_categories}")
    print(f"Unique categories found: {unique_categories}")
    
    # Count categories
    category_counts = {}
    for row in all_data:
        cat = row['Category']
        if cat != 'Unknown':
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    if category_counts:
        print(f"\nTop 10 categories:")
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for category, count in sorted_cats:
            print(f"  {category}: {count} coins")

def main():
    """Main function to fetch categories for all tickers"""
    print("Starting crypto categories extraction...")
    print(f"Processing {len(TICKERS)} tickers: {', '.join(TICKERS)}")
    print("This may take a few minutes due to API rate limits.\n")
    
    all_data = []
    
    for i, ticker in enumerate(TICKERS, 1):
        print(f"\n[{i}/{len(TICKERS)}] Processing {ticker}...")
        
        categories_data = fetch_categories_for_ticker(ticker)
        if categories_data:
            save_to_csv(ticker, categories_data)
            all_data.extend(categories_data)
        else:
            print(f"No data found for {ticker}")
        
        # Rate limiting between tickers
        if i < len(TICKERS):
            print(f"Waiting {RATE_LIMIT_DELAY} seconds before next request...")
            time.sleep(RATE_LIMIT_DELAY)
    
    # Save combined results
    if all_data:
        save_combined_csv(all_data)
        print_summary(all_data)
    
    print(f"\nCompleted! Processed {len(TICKERS)} tickers.")

if __name__ == "__main__":
    main()