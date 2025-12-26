#!/usr/bin/env python3
"""
Seed initial data for production if tables are empty or missing entries.
 - ExchangeRate (defaults)
 - WithdrawalFee (OKX/Binance onchain+lightning)
 - LightningService (Boltz/Coinos)
 - Mnemonic (a few unassigned demo mnemonics)
"""
import os
import sys
import django
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.models import ExchangeRate, WithdrawalFee, LightningService, Mnemonic, ServiceNode, Route
import json

# Optional routing seed file (exported from dev) to sync to prod
ROUTING_SEED_FILE = os.environ.get(
    'ROUTING_SEED_FILE',
    os.path.join(os.path.dirname(__file__), 'blocks', 'initial_data', 'routing.json')
)


def seed_exchange_rates():
    defaults = [
        { 'exchange': 'upbit_btc', 'fee_rate': 0.05, 'is_event': False, 'description': '업비트 비트코인 일반 거래 수수료' },
        { 'exchange': 'upbit_usdt', 'fee_rate': 0.01, 'is_event': True,  'description': '업비트 USDT 한시적 이벤트 수수료' },
        { 'exchange': 'bithumb',   'fee_rate': 0.04, 'is_event': False, 'description': '빗썸 거래 수수료 (쿠폰 적용 필수)' },
        { 'exchange': 'okx',       'fee_rate': 0.1,  'is_event': False, 'description': 'OKX 거래 수수료' },
        { 'exchange': 'binance',   'fee_rate': 0.1,  'is_event': False, 'description': '바이낸스 거래 수수료' },
    ]
    created = 0
    for d in defaults:
        obj, was_created = ExchangeRate.objects.get_or_create(
            exchange=d['exchange'],
            defaults={
                'fee_rate': d['fee_rate'],
                'is_event': d['is_event'],
                'description': d['description'],
            },
        )
        created += 1 if was_created else 0
    return created


def seed_withdrawal_fees():
    defaults = [
        { 'exchange': 'okx',     'withdrawal_type': 'onchain',   'fee_btc': 0.00001, 'description': 'OKX 온체인 개인지갑 출금 수수료' },
        { 'exchange': 'okx',     'withdrawal_type': 'lightning', 'fee_btc': 0.00001, 'description': 'OKX 라이트닝 출금 수수료' },
        { 'exchange': 'binance', 'withdrawal_type': 'onchain',   'fee_btc': 0.00003, 'description': '바이낸스 온체인 개인지갑 출금 수수료' },
        { 'exchange': 'binance', 'withdrawal_type': 'lightning', 'fee_btc': 0.000001, 'description': '바이낸스 라이트닝 출금 수수료' },
    ]
    created = 0
    for d in defaults:
        obj, was_created = WithdrawalFee.objects.get_or_create(
            exchange=d['exchange'],
            withdrawal_type=d['withdrawal_type'],
            defaults={
                'fee_btc': d['fee_btc'],
                'description': d['description'],
            },
        )
        created += 1 if was_created else 0
    return created


def seed_lightning_services():
    defaults = [
        { 'service': 'boltz',  'fee_rate': 0.5, 'is_kyc': False, 'is_custodial': False, 'description': 'Boltz 교환 수수료 (non-KYC, 비수탁형)' },
        { 'service': 'coinos', 'fee_rate': 0.0, 'is_kyc': False, 'is_custodial': True, 'description': 'Coinos 라이트닝 간 거래수수료 0% (non-KYC, 수탁형)' },
        { 'service': 'walletofsatoshi', 'fee_rate': 0.0, 'is_kyc': False, 'is_custodial': True, 'description': '월렛오브사토시 라이트닝 간 거래수수료 0% (non-KYC, 수탁형)' },
        { 'service': 'strike', 'fee_rate': 0.0, 'is_kyc': True, 'is_custodial': True, 'description': 'Strike 라이트닝 간 거래수수료 0%, 온체인 출금수수료 0% (KYC, 수탁형)' },
    ]
    created = 0
    for d in defaults:
        obj, was_created = LightningService.objects.get_or_create(
            service=d['service'],
            defaults={
                'fee_rate': d['fee_rate'],
                'is_kyc': d['is_kyc'],
                'is_custodial': d['is_custodial'],
                'description': d['description'],
            },
        )
        created += 1 if was_created else 0
    return created


def seed_mnemonics(count=10):
    """Seed valid BIP39 mnemonics for the pool (12-word)."""
    try:
        from mnemonic import Mnemonic as MnemonicGenerator
    except Exception:
        # If mnemonic library is not available, skip
        return 0
    created = 0
    # only create if there are no unassigned mnemonics at all
    if Mnemonic.objects.filter(is_assigned=False).exists():
        return 0
    mnemo = MnemonicGenerator("english")
    for i in range(int(count)):
        m = mnemo.generate(strength=128)  # 128 bits = 12 words
        Mnemonic.objects.create(username=f'seed-{i+1}', mnemonic=m, is_assigned=False)
        created += 1
    return created


def seed_service_nodes():
    """Seed service nodes for the new routing system"""
    # If a routing seed file exists, prefer using it for initial nodes
    if os.path.isfile(ROUTING_SEED_FILE):
        try:
            with open(ROUTING_SEED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nodes = data.get('nodes', [])
            created = 0
            for n in nodes:
                obj, was_created = ServiceNode.objects.update_or_create(
                    service=n['service'],
                    defaults={
                        'display_name': n.get('display_name') or n['service'],
                        'node_type': n.get('node_type', 'service'),
                        'is_kyc': bool(n.get('is_kyc', False)),
                        'is_custodial': bool(n.get('is_custodial', True)),
                        'is_enabled': bool(n.get('is_enabled', True)),
                        'website_url': n.get('website_url') or '',
                        'description': n.get('description') or '',
                    }
                )
                created += 1 if was_created else 0
            return created
        except Exception as e:
            print(f"Failed to load routing seed file for nodes: {e}. Falling back to built-in defaults.")

    nodes = [
        {'service': 'user', 'display_name': '사용자', 'is_kyc': False, 'is_custodial': False, 'website_url': '', 'node_type': 'user'},
        {'service': 'upbit', 'display_name': '업비트', 'is_kyc': True, 'is_custodial': True, 'website_url': 'https://upbit.com', 'node_type': 'exchange'},
        {'service': 'bithumb', 'display_name': '빗썸', 'is_kyc': True, 'is_custodial': True, 'website_url': 'https://www.bithumb.com', 'node_type': 'exchange'},
        {'service': 'binance', 'display_name': '바이낸스', 'is_kyc': True, 'is_custodial': True, 'website_url': 'https://www.binance.com', 'node_type': 'exchange'},
        {'service': 'okx', 'display_name': 'OKX', 'is_kyc': True, 'is_custodial': True, 'website_url': 'https://www.okx.com', 'node_type': 'exchange'},
        {'service': 'strike', 'display_name': 'Strike', 'is_kyc': True, 'is_custodial': True, 'website_url': 'https://strike.me', 'node_type': 'service'},
        {'service': 'walletofsatoshi', 'display_name': '월렛오브사토시', 'is_kyc': False, 'is_custodial': True, 'website_url': 'https://walletofsatoshi.com', 'node_type': 'service'},
        {'service': 'coinos', 'display_name': 'Coinos', 'is_kyc': False, 'is_custodial': True, 'website_url': 'https://coinos.io', 'node_type': 'service'},
        {'service': 'boltz', 'display_name': 'Boltz Exchange', 'is_kyc': False, 'is_custodial': False, 'website_url': 'https://boltz.exchange', 'node_type': 'service'},
        {'service': 'personal_wallet', 'display_name': '개인지갑', 'is_kyc': False, 'is_custodial': False, 'website_url': '', 'node_type': 'wallet'},
    ]

    created = 0
    for node_data in nodes:
        obj, was_created = ServiceNode.objects.get_or_create(
            service=node_data['service'],
            defaults={
                'display_name': node_data['display_name'],
                'node_type': node_data.get('node_type', 'service'),
                'is_kyc': node_data['is_kyc'],
                'is_custodial': node_data['is_custodial'],
                'website_url': node_data['website_url'],
                'description': f"{node_data['display_name']} 서비스"
            }
        )
        created += 1 if was_created else 0
    return created


def seed_default_routes():
    """Seed default routes based on existing data"""
    created = 0

    # If a routing seed file exists, prefer using it for initial routes
    if os.path.isfile(ROUTING_SEED_FILE):
        try:
            with open(ROUTING_SEED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            routes = data.get('routes', [])

            # Build lookup for ServiceNode by service code
            service_to_node = {s.service: s for s in ServiceNode.objects.all()}
            for r in routes:
                src = service_to_node.get(r['source'])
                dst = service_to_node.get(r['destination'])
                if not src or not dst:
                    continue

                obj, was_created = Route.objects.get_or_create(
                    source=src,
                    destination=dst,
                    route_type=r['route_type'],
                    defaults={
                        'fee_rate': r.get('fee_rate', None),
                        'fee_fixed': r.get('fee_fixed', None),
                        'is_enabled': bool(r.get('is_enabled', True)),
                        'description': r.get('description', ''),
                    }
                )
                created += 1 if was_created else 0
            return created
        except Exception as e:
            print(f"Failed to load routing seed file for routes: {e}. Falling back to built-in defaults.")

    # Get service nodes
    try:
        user = ServiceNode.objects.get(service='user')
        upbit = ServiceNode.objects.get(service='upbit')
        binance = ServiceNode.objects.get(service='binance')
        okx = ServiceNode.objects.get(service='okx')
        strike = ServiceNode.objects.get(service='strike')
        coinos = ServiceNode.objects.get(service='coinos')
        personal_wallet = ServiceNode.objects.get(service='personal_wallet')

        # Trading fee routes (거래수수료)
        trading_routes = [
            # User to exchanges (no fee - just entry point)
            {'source': user, 'dest': upbit, 'fee_rate': 0.0, 'desc': '업비트 입금'},
            {'source': user, 'dest': binance, 'fee_rate': 0.0, 'desc': '바이낸스 입금'},
            {'source': user, 'dest': okx, 'fee_rate': 0.0, 'desc': 'OKX 입금'},
        ]

        for route in trading_routes:
            obj, was_created = Route.objects.get_or_create(
                source=route['source'],
                destination=route['dest'],
                route_type='trading',
                defaults={
                    'fee_rate': route['fee_rate'],
                    'description': route['desc']
                }
            )
            created += 1 if was_created else 0

        # Lightning withdrawal routes
        lightning_routes = [
            {'source': binance, 'dest': strike, 'fee_fixed': 0.000001, 'desc': '바이낸스 → Strike 라이트닝'},
            {'source': binance, 'dest': ServiceNode.objects.get(service='walletofsatoshi'), 'fee_fixed': 0.000001, 'desc': '바이낸스 → 월렛오브사토시 라이트닝'},
            {'source': binance, 'dest': coinos, 'fee_fixed': 0.000001, 'desc': '바이낸스 → Coinos 라이트닝'},
            {'source': okx, 'dest': strike, 'fee_fixed': 0.00001, 'desc': 'OKX → Strike 라이트닝'},
            {'source': okx, 'dest': coinos, 'fee_fixed': 0.00001, 'desc': 'OKX → Coinos 라이트닝'},
        ]

        for route in lightning_routes:
            obj, was_created = Route.objects.get_or_create(
                source=route['source'],
                destination=route['dest'],
                route_type='withdrawal_lightning',
                defaults={
                    'fee_fixed': route['fee_fixed'],
                    'description': route['desc']
                }
            )
            created += 1 if was_created else 0

        # Service fee routes (라이트닝 서비스 수수료)
        service_routes = [
            {'source': strike, 'dest': personal_wallet, 'fee_rate': 0.0, 'desc': 'Strike → 개인지갑'},
            {'source': coinos, 'dest': personal_wallet, 'fee_rate': 0.0, 'desc': 'Coinos → 개인지갑'},
        ]

        for route in service_routes:
            obj, was_created = Route.objects.get_or_create(
                source=route['source'],
                destination=route['dest'],
                route_type='withdrawal_onchain',
                defaults={
                    'fee_rate': route['fee_rate'],
                    'description': route['desc']
                }
            )
            created += 1 if was_created else 0

        # On-chain direct withdrawals from exchanges to personal wallet (fixed BTC fees)
        try:
            direct_onchain = [
                {'source': binance, 'fee_fixed': 0.00003, 'desc': '바이낸스 BTC → 개인지갑 온체인'},
                {'source': okx,     'fee_fixed': 0.00001, 'desc': 'OKX BTC → 개인지갑 온체인'},
            ]
            for item in direct_onchain:
                if item['source'] and personal_wallet:
                    obj, was_created = Route.objects.get_or_create(
                        source=item['source'], destination=personal_wallet, route_type='withdrawal_onchain',
                        defaults={'fee_rate': None, 'fee_fixed': item['fee_fixed'], 'description': item['desc']}
                    )
                    created += 1 if was_created else 0
        except Exception:
            pass

    except ServiceNode.DoesNotExist as e:
        print(f"Service node not found: {e}")
        return 0

    return created


def main():
    created = 0
    created += seed_exchange_rates()
    created += seed_withdrawal_fees()
    created += seed_lightning_services()

    # Seed new routing system
    created += seed_service_nodes()
    created += seed_default_routes()

    # Only seed mnemonics if none exist
    if Mnemonic.objects.count() == 0 or not Mnemonic.objects.filter(is_assigned=False).exists():
        created += seed_mnemonics()
    print(f"Seeding complete. Created/added entries: {created}")


if __name__ == '__main__':
    main()
