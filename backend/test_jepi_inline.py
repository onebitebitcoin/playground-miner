from blocks import views
from blocks.models import AssetPriceCache
from datetime import datetime

print("=" * 80)
print("JEPI Single Asset Test - Dividend Reinvestment Issue")
print("=" * 80)

# Clear any existing cache
print("\n[1] Clearing JEPI cache...")
deleted_count = AssetPriceCache.objects.filter(asset_id='JEPI').delete()[0]
print(f"   Deleted {deleted_count} cache entries")

# Test parameters
asset_id = 'JEPI'
ticker = 'JEPI'
start_year = 2020
end_year = 2025
calculation_method = 'cagr'

print(f"\n[2] Fetching JEPI data ({start_year}-{end_year})...")

# Test WITHOUT dividend reinvestment
print("\n--- Test A: Without Dividend Reinvestment ---")
history_no_div = views._fetch_yfinance_history(ticker, start_year, end_year, adjust_for_dividends=False)
print(f"   Fetched {len(history_no_div)} data points")

yearly_no_div = views._aggregate_to_yearly_prices(history_no_div, ticker)
print("   Yearly prices (Close):")
for year in sorted(yearly_no_div.keys()):
    print(f"      {year}: ${yearly_no_div[year]:.2f}")

# Calculate CAGR manually
start_price_no_div = yearly_no_div[start_year]
end_price_no_div = yearly_no_div[end_year]
years = end_year - start_year
cagr_no_div = ((end_price_no_div / start_price_no_div) ** (1 / years) - 1) * 100
print(f"   Manual CAGR (Close): {cagr_no_div:.2f}%")

# Test WITH dividend reinvestment (Adjusted Close)
print("\n--- Test B: With Dividend Reinvestment (Adjusted Close) ---")
history_with_div = views._fetch_yfinance_history(ticker, start_year, end_year, adjust_for_dividends=True)
print(f"   Fetched {len(history_with_div)} data points")

yearly_with_div = views._aggregate_to_yearly_prices(history_with_div, ticker)
print("   Yearly prices (Adjusted Close):")
for year in sorted(yearly_with_div.keys()):
    print(f"      {year}: ${yearly_with_div[year]:.2f}")

start_price_with_div = yearly_with_div[start_year]
end_price_with_div = yearly_with_div[end_year]
cagr_with_div = ((end_price_with_div / start_price_with_div) ** (1 / years) - 1) * 100
print(f"   Manual CAGR (Adjusted Close): {cagr_with_div:.2f}%")

# Test the single asset endpoint logic
print("\n--- Test C: Single Asset Endpoint Logic ---")

cfg = {
    'id': asset_id,
    'label': 'JEPI',
    'ticker': ticker,
    'unit': 'USD',
    'category': 'ETF'
}

# Simulate the endpoint logic WITH dividend reinvestment
print("\n   Simulating endpoint with include_dividends=True:")
include_dividends = True
source = 'Yahoo Finance'

# This mimics the logic in finance_add_single_asset_view
dividends_reinvested = False
if include_dividends and 'yahoo finance' in source.lower() and cfg.get('ticker'):
    print(f"      Fetching Adjusted Close for {ticker}...")
    adjusted_history = views._fetch_yfinance_history(ticker, start_year, end_year, adjust_for_dividends=True)
    if adjusted_history:
        history = adjusted_history
        dividends_reinvested = True
        print(f"      ✓ Using Adjusted Close ({len(adjusted_history)} points)")
else:
    history = history_no_div
    print(f"      Using regular Close ({len(history)} points)")

# Build yearly dividend map (should be None if using Adjusted Close)
yearly_dividends = None if dividends_reinvested else views._build_yearly_dividend_map(cfg, start_year, end_year)
print(f"      yearly_dividends = {yearly_dividends}")
print(f"      dividends_reinvested = {dividends_reinvested}")

# Build series (this should NOT apply dividends again)
print(f"      Calling _build_asset_series with include_dividends=False...")
series = views._build_asset_series(
    asset_id, cfg, history, start_year, end_year, calculation_method,
    source=source,
    include_dividends=False,  # Should be False when using Adjusted Close
    dividend_map=yearly_dividends
)

if series:
    print(f"\n   Series Result:")
    print(f"      Label: {series['label']}")
    print(f"      Annualized Return: {series['annualized_return_pct']:.2f}%")
    print(f"      Annualized CAGR: {series['annualized_cagr_pct']:.2f}%")
    print(f"      Multiple: {series['multiple_from_start']:.3f}x")
    print(f"      Dividends Reinvested: {series.get('dividends_reinvested', False)}")
    print(f"\n   Points:")
    for point in series['points']:
        print(f"      {point['year']}: {point['value']:.2f}% (multiple: {point['multiple']:.4f})")
else:
    print("   ❌ Failed to build series")

# Expected results
print("\n" + "=" * 80)
print("EXPECTED RESULTS:")
print("=" * 80)
print(f"Without dividends (Close):         ~{cagr_no_div:.2f}%")
print(f"With dividends (Adjusted Close):   ~{cagr_with_div:.2f}%")
print(f"Difference:                         ~{cagr_with_div - cagr_no_div:.2f}%")
print("\nThe single asset endpoint should show:")
print(f"  - With include_dividends=True:  ~{cagr_with_div:.2f}% (NOT 18.9%)")
print(f"  - With include_dividends=False: ~{cagr_no_div:.2f}%")
print("=" * 80)
