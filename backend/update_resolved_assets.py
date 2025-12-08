#!/usr/bin/env python3
"""
One-time script to populate resolved_assets for existing FinanceQuickCompareGroup entries
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.views import _resolve_assets
from blocks.models import FinanceQuickCompareGroup

def update_resolved_assets():
    groups = FinanceQuickCompareGroup.objects.all()
    print(f"Found {groups.count()} groups to update")

    for group in groups:
        if not group.assets:
            print(f"Skipping {group.key}: no assets")
            continue

        print(f"\nProcessing {group.key} with {len(group.assets)} assets...")
        resolved = _resolve_assets(group.assets)
        group.resolved_assets = resolved
        group.save()
        print(f"  ✓ Saved {len(resolved)} resolved assets")
        for asset in resolved:
            print(f"    - {asset.get('label')} ({asset.get('ticker')})")

    print(f"\n✓ Updated {groups.count()} groups")

if __name__ == '__main__':
    update_resolved_assets()
