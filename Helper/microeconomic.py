import pandas as pd
import requests
from datetime import datetime
import time
import pandas.api.types as ptypes

class MacroeconomicDataExtractor:
    def __init__(self):
        self.fred_api_key = "ec1b10b7bfeff1f12e8538633a26ad51"
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.start_date = "2023-06-01"
        self.end_date = "2025-06-01"

        # FRED macroeconomic indicators by frequency
        self.fred_series_quarterly = {
            'GDP_Growth_Rate': 'A191RL1Q225SBEA',  # Real GDP Growth Rate (QoQ)
            'GDP_Annual_Growth_Rate': 'A191RO1Q156NBEA',  # Real GDP Annual Growth Rate
            'Current_Account': 'NETFI',  # Current Account Balance (Billions USD)
            'Current_Account_to_GDP': 'IEABCA',  # Current Account to GDP
            'Government_Debt_to_GDP': 'GGGDTAUSA188N',  # Government Debt to GDP
            'Government_Budget': 'M318501Q027NBEA'  # Government Budget as % of GDP
        }

        self.fred_series_monthly = {
            'Unemployment_Rate': 'UNRATE',  # Unemployment Rate
            'Non_Farm_Payrolls': 'PAYEMS',  # Nonfarm Payroll Employment (Thousands)
            'Inflation_Rate': 'CPIAUCSL',  # CPI, used for annual inflation rate
            'Inflation_Rate_MoM': 'CPIAUCNS',  # CPI Month-over-Month
            'Interest_Rate': 'FEDFUNDS',  # Effective Federal Funds Rate
            'Balance_of_Trade': 'BOPGSTB',  # Balance of Trade (Billions USD)
            'Business_Confidence': 'BSCICP03USM665S',  # Business Confidence Index
            'Manufacturing_PMI': 'MANPM',  # ISM Manufacturing PMI
            'Non_Manufacturing_PMI': 'NMFCI',  # ISM Non-Manufacturing PMI
            'Services_PMI': 'SRVPRD',  # Services PMI
            'Consumer_Confidence': 'UMCSENT',  # Consumer Sentiment Index
            'Retail_Sales_MoM': 'RSXFS',  # Retail Sales Month-over-Month
            'Building_Permits': 'PERMIT'  # Building Permits (Thousands)
        }

                # Note: Currency, Stock Market, Corporate Tax Rate, and Personal Income Tax Rate are not available in FRED.
        # These could be sourced from other APIs (e.g., Alpha Vantage for Stock Market, IMF/OECD for tax rates).

    def get_fred_data(self, series_id, series_name, frequency='m'):
        params = {
            'series_id': series_id,
            'api_key': self.fred_api_key,
            'file_type': 'json',
            'observation_start': self.start_date,
            'observation_end': self.end_date,
            'frequency': frequency
        }

        try:
            response = requests.get(self.fred_base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'observations' in data:
                df = pd.DataFrame(data['observations'])
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna()
                df = df.rename(columns={'value': series_name})
                print(f"✅ FRED data retrieved for {series_name}")
                return df[['date', series_name]]
            else:
                print(f"No data found for {series_id} ({series_name}) on FRED")
                return None
        except Exception as e:
            print(f"Error fetching {series_id} ({series_name}) from FRED: {e}")
            return None

    def extract_all_data(self):
        print("Starting macroeconomic data extraction...")
        dataframes = []

        # Fetch quarterly data
        for name, series_id in self.fred_series_quarterly.items():
            print(f"Fetching quarterly: {name}...")
            df = self.get_fred_data(series_id, name, frequency='q')
            if df is not None:
                dataframes.append(df)
            time.sleep(0.1)

        # Fetch monthly data
        for name, series_id in self.fred_series_monthly.items():
            print(f"Fetching monthly: {name}...")
            df = self.get_fred_data(series_id, name, frequency='m')
            if df is not None:
                dataframes.append(df)
            time.sleep(0.1)

        
        if dataframes:
            # Merge all on 'date'
            merged_df = dataframes[0]
            for df in dataframes[1:]:
                merged_df = pd.merge(merged_df, df, on='date', how='outer')

            merged_df = merged_df.sort_values('date')
            merged_df = merged_df.ffill()

            # Format date
            merged_df['Date'] = merged_df['date'].dt.strftime('%m/%d/%Y')
            merged_df = merged_df.drop(columns=['date'])

            # Round and format
            for col in merged_df.columns:
                if col != 'Date' and ptypes.is_numeric_dtype(merged_df[col]):
                    if col in ['Non_Farm_Payrolls', 'Building_Permits']:
                        merged_df[col] = merged_df[col].round(0)  # Thousands, no decimals
                    elif col in ['Balance_of_Trade', 'Current_Account']:
                        merged_df[col] = merged_df[col].round(2)  # Billions USD
                    elif col in ['GDP_Growth_Rate', 'GDP_Annual_Growth_Rate', 'Unemployment_Rate',
                                 'Interest_Rate', 'Ten_Year_Yield', 'Current_Account_to_GDP',
                                 'Government_Debt_to_GDP', 'Government_Budget']:
                        merged_df[col] = merged_df[col].round(1)  # Percentages
                    elif col in ['Inflation_Rate', 'Inflation_Rate_MoM']:
                        merged_df[col] = merged_df[col].round(2)  # CPI-based inflation
                    elif col in ['Business_Confidence', 'Manufacturing_PMI', 'Non_Manufacturing_PMI',
                                 'Services_PMI', 'Consumer_Confidence']:
                        merged_df[col] = merged_df[col].round(2)  # Index values
                    else:
                        merged_df[col] = merged_df[col].round(6)  # Default precision

            return merged_df
        else:
            print("No data was fetched.")
            return None

    def save_data(self, df, filename="macroeconomic_indicators.csv"):
        if df is not None:
            df.to_csv(filename, index=False, float_format='%.4f')
            print(f"\nSaved to {filename}")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {df.shape[0]}")
            print("\nSample:")
            print(df.head(3).to_string(index=False, float_format='%.4f'))
        else:
            print("No data to save.")

def main():
    extractor = MacroeconomicDataExtractor()
    print("=== MACROECONOMIC DATA EXTRACTION ===")

    df = extractor.extract_all_data()
    if df is not None:
        extractor.save_data(df)
    else:
        print("Extraction failed.")

if __name__ == "__main__":
    main()