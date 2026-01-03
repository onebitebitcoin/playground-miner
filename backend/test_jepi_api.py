from blocks.models import AssetPriceCache
import json
from django.test import Client

print("=" * 80)
print("JEPI API Test - Dividend Reinvestment Issue")
print("=" * 80)

# Clear cache
print("\n[1] Clearing JEPI cache...")
deleted_count = AssetPriceCache.objects.filter(asset_id='JEPI').delete()[0]
print(f"   Deleted {deleted_count} cache entries")

# Create test client
client = Client()

# Test parameters
asset_id = 'JEPI'
start_year = 2020
end_year = 2025

# Test WITHOUT dividend reinvestment
print("\n[2] Testing API WITHOUT dividend reinvestment...")
payload_no_div = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': False
}

response_no_div = client.post(
    '/api/finance/add-single-asset',
    data=json.dumps(payload_no_div),
    content_type='application/json'
)

if response_no_div.status_code == 200:
    data_no_div = response_no_div.json()
    if data_no_div.get('ok'):
        series_no_div = data_no_div['series']
        print(f"   ✓ Success")
        print(f"   Label: {series_no_div['label']}")
        print(f"   CAGR: {series_no_div['annualized_cagr_pct']:.2f}%")
        print(f"   Multiple: {series_no_div['multiple_from_start']:.3f}x")
        print(f"   Dividends Reinvested: {series_no_div.get('dividends_reinvested', False)}")
    else:
        print(f"   ❌ Error: {data_no_div.get('error')}")
else:
    print(f"   ❌ HTTP {response_no_div.status_code}")
    try:
        error_data = response_no_div.json()
        print(f"   Error: {error_data.get('error', 'Unknown error')}")
    except:
        print(f"   Response: {response_no_div.content.decode()[:200]}")

# Clear cache again
print("\n[3] Clearing JEPI cache again...")
AssetPriceCache.objects.filter(asset_id='JEPI').delete()

# Test WITH dividend reinvestment
print("\n[4] Testing API WITH dividend reinvestment...")
payload_with_div = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': True
}

response_with_div = client.post(
    '/api/finance/add-single-asset',
    data=json.dumps(payload_with_div),
    content_type='application/json'
)

if response_with_div.status_code == 200:
    data_with_div = response_with_div.json()
    if data_with_div.get('ok'):
        series_with_div = data_with_div['series']
        print(f"   ✓ Success")
        print(f"   Label: {series_with_div['label']}")
        print(f"   CAGR: {series_with_div['annualized_cagr_pct']:.2f}%")
        print(f"   Multiple: {series_with_div['multiple_from_start']:.3f}x")
        print(f"   Dividends Reinvested: {series_with_div.get('dividends_reinvested', False)}")

        # Check if dividend info is present
        metadata = series_with_div.get('metadata', {})
        if metadata.get('dividend_yield_pct'):
            print(f"   Dividend Yield: {metadata['dividend_yield_pct']:.2f}%")
    else:
        print(f"   ❌ Error: {data_with_div.get('error')}")
else:
    print(f"   ❌ HTTP {response_with_div.status_code}")
    try:
        error_data = response_with_div.json()
        print(f"   Error: {error_data.get('error', 'Unknown error')}")
    except:
        print(f"   Response: {response_with_div.content.decode()[:200]}")

# Summary
print("\n" + "=" * 80)
print("RESULTS SUMMARY:")
print("=" * 80)
if response_no_div.status_code == 200 and data_no_div.get('ok'):
    print(f"WITHOUT dividends: {series_no_div['annualized_cagr_pct']:.2f}%")
if response_with_div.status_code == 200 and data_with_div.get('ok'):
    print(f"WITH dividends:    {series_with_div['annualized_cagr_pct']:.2f}%")
    difference = series_with_div['annualized_cagr_pct'] - series_no_div['annualized_cagr_pct']
    print(f"Difference:        {difference:.2f}%")
    print()
    if series_with_div['annualized_cagr_pct'] > 15:
        print("❌ PROBLEM: CAGR with dividends is TOO HIGH (>15%)!")
        print("   This suggests dividends are being applied twice.")
    elif series_with_div['annualized_cagr_pct'] < 5:
        print("❌ PROBLEM: CAGR with dividends is TOO LOW (<5%)!")
        print("   This suggests dividends are NOT being applied.")
    elif 8 <= series_with_div['annualized_cagr_pct'] <= 11:
        print("✓ SUCCESS: CAGR with dividends is in expected range (8-11%)!")
    else:
        print("⚠ WARNING: CAGR with dividends is outside expected range (8-11%)")
print("=" * 80)
