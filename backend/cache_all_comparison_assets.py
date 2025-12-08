#!/usr/bin/env python3
"""
Script to cache price data for all assets in comparison groups
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.models import FinanceQuickCompareGroup, AssetPriceCache
from blocks.views import _cache_asset_prices

def cache_all_comparison_assets():
    print("=== Caching All Comparison Assets ===\n")

    # Get all comparison groups
    groups = FinanceQuickCompareGroup.objects.all().order_by('sort_order', 'id')
    print(f"Found {groups.count()} comparison groups\n")

    total_assets = 0
    cached_count = 0
    already_cached = 0
    failed_count = 0

    for group in groups:
        print(f"\n{'='*60}")
        print(f"Group: {group.label} ({group.key})")
        print(f"{'='*60}")

        resolved_assets = group.resolved_assets or []

        if not resolved_assets:
            print(f"  ⚠ No resolved assets found, skipping...")
            continue

        print(f"  Assets: {len(resolved_assets)}")

        for asset in resolved_assets:
            total_assets += 1
            asset_id = asset.get('ticker') or asset.get('id')
            asset_label = asset.get('label') or asset_id
            asset_category = asset.get('category')

            if not asset_id:
                print(f"  ✗ Skipping {asset_label}: No ticker/id")
                failed_count += 1
                continue

            # Check if already cached
            if AssetPriceCache.objects.filter(asset_id=asset_id).exists():
                print(f"  ✓ {asset_label} ({asset_id}): Already cached")
                already_cached += 1
                continue

            # Cache the asset
            print(f"  → Caching {asset_label} ({asset_id})...", end=' ')
            try:
                success = _cache_asset_prices(asset_id, asset_label, asset_category)
                if success:
                    print("✓ Success")
                    cached_count += 1
                else:
                    print("✗ Failed (no data)")
                    failed_count += 1
            except Exception as e:
                print(f"✗ Failed: {e}")
                failed_count += 1

    print(f"\n{'='*60}")
    print("=== Summary ===")
    print(f"{'='*60}")
    print(f"Total assets found:     {total_assets}")
    print(f"Already cached:         {already_cached}")
    print(f"Newly cached:           {cached_count}")
    print(f"Failed:                 {failed_count}")
    print(f"{'='*60}")

    # Show all cached assets
    all_cached = AssetPriceCache.objects.all().order_by('asset_id')
    print(f"\n=== All Cached Assets ({all_cached.count()}) ===")
    for cache in all_cached:
        years_count = len(cache.yearly_prices)
        print(f"  {cache.asset_id:20s} {cache.label:40s} ({cache.start_year}-{cache.end_year}, {years_count} years)")

if __name__ == '__main__':
    cache_all_comparison_assets()
