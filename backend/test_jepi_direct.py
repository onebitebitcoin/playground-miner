from blocks.models import AssetPriceCache
from blocks import views
import json
from unittest.mock import Mock

print("=" * 80)
print("JEPI Direct Function Test - Dividend Reinvestment Issue")
print("=" * 80)

# Clear cache
print("\n[1] Clearing JEPI cache...")
deleted_count = AssetPriceCache.objects.filter(asset_id='JEPI').delete()[0]
print(f"   Deleted {deleted_count} cache entries")

# Test parameters
asset_id = 'JEPI'
start_year = 2020
end_year = 2025

def create_mock_request(payload):
    request = Mock()
    request.method = 'POST'
    request.body = json.dumps(payload).encode('utf-8')
    request.content_type = 'application/json'
    return request

# Test WITHOUT dividend reinvestment
print("\n[2] Testing WITHOUT dividend reinvestment...")
payload_no_div = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': False
}

request_no_div = create_mock_request(payload_no_div)
response_no_div = views.finance_add_single_asset_view(request_no_div)
data_no_div = json.loads(response_no_div.content.decode())

if data_no_div.get('ok'):
    series_no_div = data_no_div['series']
    print(f"   ✓ Success")
    print(f"   Label: {series_no_div['label']}")
    print(f"   CAGR: {series_no_div['annualized_cagr_pct']:.2f}%")
    print(f"   Multiple: {series_no_div['multiple_from_start']:.3f}x")
    print(f"   Dividends Reinvested: {series_no_div.get('dividends_reinvested', False)}")
else:
    print(f"   ❌ Error: {data_no_div.get('error')}")

# Clear cache again
print("\n[3] Clearing JEPI cache again...")
AssetPriceCache.objects.filter(asset_id='JEPI').delete()

# Test WITH dividend reinvestment
print("\n[4] Testing WITH dividend reinvestment...")
payload_with_div = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': True
}

request_with_div = create_mock_request(payload_with_div)
response_with_div = views.finance_add_single_asset_view(request_with_div)
data_with_div = json.loads(response_with_div.content.decode())

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

# Summary
print("\n" + "=" * 80)
print("RESULTS SUMMARY:")
print("=" * 80)
if data_no_div.get('ok') and data_with_div.get('ok'):
    cagr_no_div = series_no_div['annualized_cagr_pct']
    cagr_with_div = series_with_div['annualized_cagr_pct']

    print(f"WITHOUT dividends: {cagr_no_div:.2f}%")
    print(f"WITH dividends:    {cagr_with_div:.2f}%")
    difference = cagr_with_div - cagr_no_div
    print(f"Difference:        {difference:.2f}%")
    print()

    if cagr_with_div > 15:
        print("❌ PROBLEM: CAGR with dividends is TOO HIGH (>15%)!")
        print("   This suggests dividends are being applied twice.")
        print("   Expected: ~9-10% with dividends")
    elif cagr_with_div < 5:
        print("❌ PROBLEM: CAGR with dividends is TOO LOW (<5%)!")
        print("   This suggests dividends are NOT being applied.")
    elif 8 <= cagr_with_div <= 11:
        print("✓ SUCCESS: CAGR with dividends is in expected range (8-11%)!")
        print("   The dividend reinvestment is working correctly.")
    else:
        print("⚠ WARNING: CAGR with dividends is outside expected range (8-11%)")
else:
    print("❌ One or both tests failed")
print("=" * 80)
