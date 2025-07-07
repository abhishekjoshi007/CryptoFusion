import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin, urlparse
import re
import csv

class CryptoRankScraper:
    def __init__(self, csv_file_path=None):
        self.base_url = "https://cryptorank.io"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Load cryptocurrencies from CSV file
        self.crypto_list = []
        if csv_file_path:
            self.load_crypto_from_csv(csv_file_path)
        
        # Define categories for fallback scraping
        self.categories = [
            'currency',
            'chain', 
            'stablecoin',
            'meme',
            'defi',
            'cefi',
            'blockchain-infrastructure',
            'blockchain-service',
            'gamefi',
            'nft',
            'social'
        ]
    
    def load_crypto_from_csv(self, csv_file_path):
        """Load cryptocurrency list from CSV file"""
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Extract ticker symbol (remove -USD suffix)
                    ticker = row['Ticker'].replace('-USD', '') if row['Ticker'].endswith('-USD') else row['Ticker']
                    
                    self.crypto_list.append({
                        'name': row['Coin Name'].strip(),
                        'ticker': ticker.strip(),
                        'original_ticker': row['Ticker'].strip()
                    })
            print(f"Loaded {len(self.crypto_list)} cryptocurrencies from {csv_file_path}")
        except FileNotFoundError:
            print(f"CSV file {csv_file_path} not found")
        except Exception as e:
            print(f"Error loading CSV: {e}")
    
    def get_crypto_url(self, ticker):
        """Generate URL for a specific cryptocurrency"""
        # Try different URL formats that CryptoRank might use
        possible_urls = [
            f"{self.base_url}/price/{ticker.lower()}",
            f"{self.base_url}/currencies/{ticker.lower()}",
            f"{self.base_url}/{ticker.lower()}",
        ]
        return possible_urls
    
    def search_crypto_by_name(self, name):
        """Search for cryptocurrency by name"""
        search_url = f"{self.base_url}/search"
        try:
            response = self.session.get(search_url, params={'q': name}, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for search results
                results = soup.find_all(['div', 'a'], class_=re.compile(r'search|result'))
                return results
        except Exception as e:
            print(f"Search error for {name}: {e}")
        return []
    
    def scrape_individual_crypto(self, crypto_info):
        """Scrape data for a specific cryptocurrency"""
        name = crypto_info['name']
        ticker = crypto_info['ticker']
        
        print(f"Scraping {name} ({ticker})")
        
        # Try different URL formats
        possible_urls = self.get_crypto_url(ticker)
        
        for url in possible_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract data from the page
                    crypto_data = self.extract_crypto_data_from_page(soup, name, ticker)
                    if crypto_data:
                        print(f"✓ Found data for {name}")
                        return crypto_data
                    
            except requests.RequestException as e:
                print(f"Error accessing {url}: {e}")
                continue
        
        # If direct URL doesn't work, try searching
        search_results = self.search_crypto_by_name(name)
        if search_results:
            # Try to extract data from search results
            for result in search_results[:3]:  # Try first 3 results
                try:
                    link = result.find('a')
                    if link and 'href' in link.attrs:
                        result_url = urljoin(self.base_url, link['href'])
                        response = self.session.get(result_url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            crypto_data = self.extract_crypto_data_from_page(soup, name, ticker)
                            if crypto_data:
                                print(f"✓ Found data for {name} via search")
                                return crypto_data
                except Exception as e:
                    continue
        
        print(f"✗ No data found for {name} ({ticker})")
        return None
    
    def extract_crypto_data_from_page(self, soup, name, ticker):
        """Extract cryptocurrency data from a page"""
        data = {
            'name': name,
            'ticker': ticker,
            'price': '',
            'market_cap': '',
            'volume_24h': '',
            'change_24h': '',
            'rank': '',
            'category': '',
            'circulating_supply': '',
            'total_supply': '',
            'max_supply': ''
        }
        
        # Extract price
        price_selectors = [
            'span[class*="price"]',
            'div[class*="price"]',
            '.price-value',
            '[data-testid="price"]',
            'span:contains("$")'
        ]
        
        for selector in price_selectors:
            try:
                price_elem = soup.select_one(selector)
                if price_elem and '
    
    def scrape_all_cryptos_from_list(self):
        """Scrape all cryptocurrencies from the loaded list"""
        if not self.crypto_list:
            print("No cryptocurrency list loaded. Please provide a CSV file.")
            return []
        
        all_data = []
        failed_cryptos = []
        
        print(f"Starting to scrape {len(self.crypto_list)} cryptocurrencies...")
        
        for i, crypto_info in enumerate(self.crypto_list, 1):
            print(f"\n[{i}/{len(self.crypto_list)}] ", end="")
            
            try:
                crypto_data = self.scrape_individual_crypto(crypto_info)
                if crypto_data:
                    all_data.append(crypto_data)
                else:
                    failed_cryptos.append(crypto_info)
                
                # Be respectful to the server
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing {crypto_info['name']}: {e}")
                failed_cryptos.append(crypto_info)
        
        print(f"\n\nScraping completed!")
        print(f"Successfully scraped: {len(all_data)} cryptocurrencies")
        print(f"Failed to scrape: {len(failed_cryptos)} cryptocurrencies")
        
        if failed_cryptos:
            print("\nFailed cryptocurrencies:")
            for crypto in failed_cryptos:
                print(f"  - {crypto['name']} ({crypto['ticker']})")
        
        return all_data
    
    def get_category_url(self, category):
        """Generate URL for a specific category"""
        return f"{self.base_url}/categories/{category}"
    
    def scrape_category_page(self, category):
        """Scrape data from a category page (fallback method)"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_extracted_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    # Initialize scraper with your CSV file
    scraper = CryptoRankScraper('Crypto.csv')
    
    # Scrape all cryptocurrencies from the CSV file
    print("Scraping cryptocurrencies from CSV file...")
    crypto_data = scraper.scrape_all_cryptos_from_list()
    
    # Save results
    if crypto_data:
        print(f"\nTotal cryptocurrencies scraped: {len(crypto_data)}")
        df = scraper.save_to_csv(crypto_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(crypto_data[:5]):
            print(f"{i+1}. {crypto['name']} ({crypto['ticker']})")
            print(f"   Price: {crypto['price']}")
            print(f"   Market Cap: {crypto['market_cap']}")
            print(f"   24h Volume: {crypto['volume_24h']}")
            print(f"   24h Change: {crypto['change_24h']}")
            print()
        
        # Show dataframe info
        if df is not None:
            print(f"DataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Show summary statistics
            print(f"\nSummary:")
            print(f"Total coins: {len(df)}")
            print(f"Coins with price data: {len(df[df['price'] != ''])}")
            print(f"Coins with market cap data: {len(df[df['market_cap'] != ''])}")
            print(f"Coins with volume data: {len(df[df['volume_24h'] != ''])}")
    else:
        print("No data found. Please check the website structure or network connection.")
    
    # Alternative: If you want to scrape categories instead
    # print("\nAlternative: Scraping by categories...")
    # scraper_categories = CryptoRankScraper()
    # category_data = scraper_categories.scrape_all_categories(['defi', 'chain', 'meme'])
    # if category_data:
    #     scraper_categories.save_to_csv(category_data, "cryptorank_categories_data.csv")
 in price_elem.get_text():
                    data['price'] = price_elem.get_text(strip=True)
                    break
            except:
                continue
        
        # Extract market cap
        market_cap_selectors = [
            'span[class*="market-cap"]',
            'div[class*="market-cap"]',
            'span:contains("Market Cap")',
            '[data-testid="market-cap"]'
        ]
        
        for selector in market_cap_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    # Look for the value in the same element or nearby
                    text = elem.get_text(strip=True)
                    if '
    
    def scrape_category_page(self, category):
        """Scrape data from a category page"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
    
    def extract_crypto_from_row(self, row, category):
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    scraper = CryptoRankScraper()
    
    # Example 1: Scrape all categories
    print("Scraping all categories...")
    all_data = scraper.scrape_all_categories()
    
    # Example 2: Scrape specific categories
    # specific_categories = ['chain', 'defi', 'meme']
    # print(f"Scraping specific categories: {specific_categories}")
    # all_data = scraper.scrape_all_categories(specific_categories)
    
    # Save results
    if all_data:
        print(f"Total cryptocurrencies found: {len(all_data)}")
        df = scraper.save_to_csv(all_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(all_data[:5]):
            print(f"{i+1}. {crypto}")
            
        # Show dataframe info
        if df is not None:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
    else:
        print("No data found. The website structure may have changed.")
    
    # Example 3: Scrape just one category
    # print("Scraping just DeFi category...")
    # defi_data = scraper.scrape_category_page('defi')
    # print(f"DeFi cryptos found: {len(defi_data)}")
 in text and any(suffix in text for suffix in ['B', 'M', 'K', 'T']):
                        data['market_cap'] = text
                        break
                    # Check parent or sibling elements
                    parent = elem.parent
                    if parent:
                        parent_text = parent.get_text(strip=True)
                        if '
    
    def scrape_category_page(self, category):
        """Scrape data from a category page"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
    
    def extract_crypto_from_row(self, row, category):
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    scraper = CryptoRankScraper()
    
    # Example 1: Scrape all categories
    print("Scraping all categories...")
    all_data = scraper.scrape_all_categories()
    
    # Example 2: Scrape specific categories
    # specific_categories = ['chain', 'defi', 'meme']
    # print(f"Scraping specific categories: {specific_categories}")
    # all_data = scraper.scrape_all_categories(specific_categories)
    
    # Save results
    if all_data:
        print(f"Total cryptocurrencies found: {len(all_data)}")
        df = scraper.save_to_csv(all_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(all_data[:5]):
            print(f"{i+1}. {crypto}")
            
        # Show dataframe info
        if df is not None:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
    else:
        print("No data found. The website structure may have changed.")
    
    # Example 3: Scrape just one category
    # print("Scraping just DeFi category...")
    # defi_data = scraper.scrape_category_page('defi')
    # print(f"DeFi cryptos found: {len(defi_data)}")
 in parent_text and any(suffix in parent_text for suffix in ['B', 'M', 'K', 'T']):
                            data['market_cap'] = parent_text
                            break
            except:
                continue
        
        # Extract volume
        volume_selectors = [
            'span[class*="volume"]',
            'div[class*="volume"]',
            'span:contains("Volume")',
            '[data-testid="volume"]'
        ]
        
        for selector in volume_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if '
    
    def scrape_category_page(self, category):
        """Scrape data from a category page"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
    
    def extract_crypto_from_row(self, row, category):
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    scraper = CryptoRankScraper()
    
    # Example 1: Scrape all categories
    print("Scraping all categories...")
    all_data = scraper.scrape_all_categories()
    
    # Example 2: Scrape specific categories
    # specific_categories = ['chain', 'defi', 'meme']
    # print(f"Scraping specific categories: {specific_categories}")
    # all_data = scraper.scrape_all_categories(specific_categories)
    
    # Save results
    if all_data:
        print(f"Total cryptocurrencies found: {len(all_data)}")
        df = scraper.save_to_csv(all_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(all_data[:5]):
            print(f"{i+1}. {crypto}")
            
        # Show dataframe info
        if df is not None:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
    else:
        print("No data found. The website structure may have changed.")
    
    # Example 3: Scrape just one category
    # print("Scraping just DeFi category...")
    # defi_data = scraper.scrape_category_page('defi')
    # print(f"DeFi cryptos found: {len(defi_data)}")
 in text and any(suffix in text for suffix in ['B', 'M', 'K', 'T']):
                        data['volume_24h'] = text
                        break
                    # Check parent or sibling elements
                    parent = elem.parent
                    if parent:
                        parent_text = parent.get_text(strip=True)
                        if '
    
    def scrape_category_page(self, category):
        """Scrape data from a category page"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
    
    def extract_crypto_from_row(self, row, category):
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    scraper = CryptoRankScraper()
    
    # Example 1: Scrape all categories
    print("Scraping all categories...")
    all_data = scraper.scrape_all_categories()
    
    # Example 2: Scrape specific categories
    # specific_categories = ['chain', 'defi', 'meme']
    # print(f"Scraping specific categories: {specific_categories}")
    # all_data = scraper.scrape_all_categories(specific_categories)
    
    # Save results
    if all_data:
        print(f"Total cryptocurrencies found: {len(all_data)}")
        df = scraper.save_to_csv(all_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(all_data[:5]):
            print(f"{i+1}. {crypto}")
            
        # Show dataframe info
        if df is not None:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
    else:
        print("No data found. The website structure may have changed.")
    
    # Example 3: Scrape just one category
    # print("Scraping just DeFi category...")
    # defi_data = scraper.scrape_category_page('defi')
    # print(f"DeFi cryptos found: {len(defi_data)}")
 in parent_text and any(suffix in parent_text for suffix in ['B', 'M', 'K', 'T']):
                            data['volume_24h'] = parent_text
                            break
            except:
                continue
        
        # Extract 24h change
        change_selectors = [
            'span[class*="change"]',
            'div[class*="change"]',
            'span:contains("%")',
            '[data-testid="change"]'
        ]
        
        for selector in change_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if '%' in text and ('+' in text or '-' in text):
                        data['change_24h'] = text
                        break
            except:
                continue
        
        # Extract rank
        rank_selectors = [
            'span[class*="rank"]',
            'div[class*="rank"]',
            'span:contains("#")',
            '[data-testid="rank"]'
        ]
        
        for selector in rank_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if '#' in text or 'rank' in text.lower():
                        data['rank'] = text
                        break
            except:
                continue
        
        # Return data if we found at least price
        if data['price']:
            return data
        
        return None
    
    def scrape_category_page(self, category):
        """Scrape data from a category page"""
        url = self.get_category_url(category)
        print(f"Scraping category: {category}")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cryptocurrency data in various possible formats
            cryptos = []
            
            # Method 1: Look for table rows
            table_rows = soup.find_all('tr')
            for row in table_rows:
                crypto_data = self.extract_crypto_from_row(row, category)
                if crypto_data:
                    cryptos.append(crypto_data)
            
            # Method 2: Look for card-style elements
            if not cryptos:
                cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|crypto|coin'))
                for card in cards:
                    crypto_data = self.extract_crypto_from_card(card, category)
                    if crypto_data:
                        cryptos.append(crypto_data)
            
            # Method 3: Look for JSON data in script tags
            if not cryptos:
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'props' in data:
                            cryptos.extend(self.extract_from_json(data, category))
                    except:
                        continue
            
            return cryptos
            
        except requests.RequestException as e:
            print(f"Error scraping {category}: {e}")
            return []
    
    def extract_crypto_from_row(self, row, category):
        """Extract cryptocurrency data from a table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # Look for name and symbol
        name_cell = cells[0] if cells else None
        symbol = ""
        name = ""
        
        if name_cell:
            # Try to find symbol (usually in parentheses or separate element)
            symbol_elem = name_cell.find(text=re.compile(r'\([A-Z]{2,10}\)'))
            if symbol_elem:
                symbol = symbol_elem.strip('()')
            else:
                # Look for symbol in separate elements
                symbol_elem = name_cell.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
                if symbol_elem:
                    symbol = symbol_elem.get_text(strip=True)
            
            # Get name
            name = name_cell.get_text(strip=True)
            # Remove symbol from name if present
            if symbol and symbol in name:
                name = name.replace(f"({symbol})", "").strip()
        
        # Extract other data
        price = self.extract_price(cells)
        market_cap = self.extract_market_cap(cells)
        volume = self.extract_volume(cells)
        change_24h = self.extract_change_24h(cells)
        
        if name and (symbol or name):
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume,
                'change_24h': change_24h
            }
        return None
    
    def extract_crypto_from_card(self, card, category):
        """Extract cryptocurrency data from a card element"""
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'], 
                             class_=re.compile(r'name|title'))
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Look for symbol
        symbol_elem = card.find(['span', 'div'], class_=re.compile(r'symbol|ticker'))
        symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price'))
        price = price_elem.get_text(strip=True) if price_elem else ""
        
        if name:
            return {
                'name': name,
                'symbol': symbol,
                'category': category,
                'price': price,
                'market_cap': '',
                'volume_24h': '',
                'change_24h': ''
            }
        return None
    
    def extract_from_json(self, data, category):
        """Extract cryptocurrency data from JSON"""
        cryptos = []
        # This would need to be customized based on the actual JSON structure
        # that CryptoRank uses
        return cryptos
    
    def extract_price(self, cells):
        """Extract price from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '$' in text and re.search(r'\d', text):
                return text
        return ""
    
    def extract_market_cap(self, cells):
        """Extract market cap from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if ('$' in text and ('B' in text or 'M' in text or 'K' in text)) or 'cap' in text.lower():
                return text
        return ""
    
    def extract_volume(self, cells):
        """Extract volume from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if 'volume' in text.lower() or ('$' in text and len(text) > 5):
                return text
        return ""
    
    def extract_change_24h(self, cells):
        """Extract 24h change from table cells"""
        for cell in cells:
            text = cell.get_text(strip=True)
            if '%' in text and ('+' in text or '-' in text):
                return text
        return ""
    
    def scrape_all_categories(self, target_categories=None):
        """Scrape all categories or specific ones"""
        if target_categories is None:
            target_categories = self.categories
        
        all_data = []
        
        for category in target_categories:
            if category.lower() in [c.lower() for c in self.categories]:
                category_data = self.scrape_category_page(category.lower())
                all_data.extend(category_data)
                time.sleep(2)  # Be respectful to the server
            else:
                print(f"Warning: '{category}' is not a valid category")
        
        return all_data
    
    def save_to_csv(self, data, filename="cryptorank_data.csv"):
        """Save scraped data to CSV"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
            return df
        else:
            print("No data to save")
            return None
    


# Example usage
if __name__ == "__main__":
    scraper = CryptoRankScraper()
    
    # Example 1: Scrape all categories
    print("Scraping all categories...")
    all_data = scraper.scrape_all_categories()
    
    # Example 2: Scrape specific categories
    # specific_categories = ['chain', 'defi', 'meme']
    # print(f"Scraping specific categories: {specific_categories}")
    # all_data = scraper.scrape_all_categories(specific_categories)
    
    # Save results
    if all_data:
        print(f"Total cryptocurrencies found: {len(all_data)}")
        df = scraper.save_to_csv(all_data)
        
        # Display first few results
        print("\nFirst 5 results:")
        for i, crypto in enumerate(all_data[:5]):
            print(f"{i+1}. {crypto}")
            
        # Show dataframe info
        if df is not None:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
    else:
        print("No data found. The website structure may have changed.")
    
    # Example 3: Scrape just one category
    # print("Scraping just DeFi category...")
    # defi_data = scraper.scrape_category_page('defi')
    # print(f"DeFi cryptos found: {len(defi_data)}")