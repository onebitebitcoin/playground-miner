import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from blocks import views

# Test JEPI with and without dividend reinvestment
asset_config = {
    'id': 'JEPI',
    'label': 'JPMorgan Equity Premium Income ETF',
    'ticker': 'JEPI',
    'unit': 'USD',
    'category': 'ETF'
}

print("Fetching JEPI data without dividend adjustment...")
history_no_div = views._fetch_yfinance_history('JEPI', 2020, 2025, adjust_for_dividends=False)
print(f"Got {len(history_no_div)} data points")
yearly_no_div = views._aggregate_to_yearly_prices(history_no_div, 'JEPI')
print("Yearly prices (no dividends):")
for year, price in sorted(yearly_no_div.items()):
    print(f"  {year}: ${price:.2f}")

print("\nFetching JEPI data WITH dividend adjustment...")
history_with_div = views._fetch_yfinance_history('JEPI', 2020, 2025, adjust_for_dividends=True)
print(f"Got {len(history_with_div)} data points")
yearly_with_div = views._aggregate_to_yearly_prices(history_with_div, 'JEPI')
print("Yearly prices (with dividends reinvested):")
for year, price in sorted(yearly_with_div.items()):
    print(f"  {year}: ${price:.2f}")

# Calculate CAGR
start_price_no_div = yearly_no_div[2020]
end_price_no_div = yearly_no_div[2025]
years = 2025 - 2020
cagr_no_div = ((end_price_no_div / start_price_no_div) ** (1 / years) - 1) * 100

start_price_with_div = yearly_with_div[2020]
end_price_with_div = yearly_with_div[2025]
cagr_with_div = ((end_price_with_div / start_price_with_div) ** (1 / years) - 1) * 100

print(f"\nCAGR without dividends: {cagr_no_div:.2f}%")
print(f"CAGR with dividends: {cagr_with_div:.2f}%")
print(f"Difference: {cagr_with_div - cagr_no_div:.2f}%")
