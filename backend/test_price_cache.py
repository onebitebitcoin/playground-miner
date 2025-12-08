#!/usr/bin/env python3
"""
Test script for price cache functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.views import _cache_asset_prices
from blocks.models import AssetPriceCache

def test_cache_price():
    print("=== Testing Price Cache ===\n")

    # Test 1: Cache AAPL prices
    print("Test 1: Caching AAPL prices...")
    success = _cache_asset_prices('AAPL', '애플(AAPL)', '미국 주식')
    print(f"  Result: {'✓ Success' if success else '✗ Failed'}\n")

    # Test 2: Verify cache entry
    print("Test 2: Verifying cache entry...")
    try:
        cache_entry = AssetPriceCache.objects.get(asset_id='AAPL')
        print(f"  ✓ Found cache entry")
        print(f"  - Label: {cache_entry.label}")
        print(f"  - Category: {cache_entry.category}")
        print(f"  - Source: {cache_entry.source}")
        print(f"  - Years: {cache_entry.start_year} - {cache_entry.end_year}")
        print(f"  - Data points: {len(cache_entry.yearly_prices)}")

        # Show sample data
        years = sorted(cache_entry.yearly_prices.keys())
        if years:
            sample_years = years[:3] + years[-3:]
            print(f"  - Sample prices:")
            for year in set(sample_years):
                price = cache_entry.yearly_prices[year]
                print(f"    {year}: ${price:,.2f}")
        print()

    except AssetPriceCache.DoesNotExist:
        print(f"  ✗ Cache entry not found\n")

    # Test 3: Cache another stock
    print("Test 3: Caching TSLA prices...")
    success = _cache_asset_prices('TSLA', '테슬라(TSLA)', '미국 주식')
    print(f"  Result: {'✓ Success' if success else '✗ Failed'}\n")

    # Summary
    print("=== Summary ===")
    total_cached = AssetPriceCache.objects.count()
    print(f"Total cached assets: {total_cached}")

    for entry in AssetPriceCache.objects.all():
        print(f"  - {entry.asset_id}: {entry.label} ({len(entry.yearly_prices)} years)")

if __name__ == '__main__':
    test_cache_price()
