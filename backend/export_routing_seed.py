#!/usr/bin/env python3
"""
Export current routing management data (ServiceNode + Route) to a JSON seed
file so production can initialize with the same data.

Usage:
  python backend/export_routing_seed.py [output_path]

Defaults:
  Writes to backend/blocks/initial_data/routing.json
"""
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(BASE_DIR, 'blocks', 'initial_data', 'routing.json')

def setup_django():
    sys.path.append(BASE_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
    import django
    django.setup()

def main(argv):
    setup_django()
    from blocks.models import ServiceNode, Route

    out_path = argv[1] if len(argv) > 1 else DEFAULT_OUT
    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)

    nodes = list(ServiceNode.objects.all().values(
        'service', 'display_name', 'node_type', 'is_kyc', 'is_custodial', 'is_enabled', 'description', 'website_url'
    ))

    routes_list = []
    qs = Route.objects.select_related('source', 'destination').all()
    for r in qs:
        routes_list.append({
            'source': r.source.service,
            'destination': r.destination.service,
            'route_type': r.route_type,
            'fee_rate': float(r.fee_rate) if r.fee_rate is not None else None,
            'fee_fixed': float(r.fee_fixed) if r.fee_fixed is not None else None,
            'is_enabled': bool(r.is_enabled),
            'description': r.description or '',
            'is_event': bool(r.is_event),
            'event_title': r.event_title or '',
            'event_description': r.event_description or '',
        })

    payload = { 'nodes': nodes, 'routes': routes_list }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Exported routing seed to: {out_path}")

if __name__ == '__main__':
    main(sys.argv)
