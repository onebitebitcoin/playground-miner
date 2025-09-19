#!/usr/bin/env python3
"""
Initialize default exchange rates
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.models import ExchangeRate

def init_exchange_rates():
    """Initialize default exchange rates"""

    rates = [
        {
            'exchange': 'upbit_btc',
            'fee_rate': 0.05,
            'is_event': False,
            'description': '업비트 비트코인 일반 거래 수수료'
        },
        {
            'exchange': 'upbit_usdt',
            'fee_rate': 0.01,
            'is_event': True,
            'description': '업비트 USDT 한시적 이벤트 수수료'
        },
        {
            'exchange': 'bithumb',
            'fee_rate': 0.04,
            'is_event': False,
            'description': '빗썸 거래 수수료 (쿠폰 적용 필수)'
        },
        {
            'exchange': 'okx',
            'fee_rate': 0.1,
            'is_event': False,
            'description': 'OKX 거래 수수료'
        },
        {
            'exchange': 'binance',
            'fee_rate': 0.1,
            'is_event': False,
            'description': '바이낸스 거래 수수료'
        }
    ]

    for rate_data in rates:
        exchange_rate, created = ExchangeRate.objects.get_or_create(
            exchange=rate_data['exchange'],
            defaults={
                'fee_rate': rate_data['fee_rate'],
                'is_event': rate_data['is_event'],
                'description': rate_data['description']
            }
        )

        if created:
            print(f"Created: {exchange_rate}")
        else:
            print(f"Already exists: {exchange_rate}")

if __name__ == "__main__":
    init_exchange_rates()
    print("Exchange rates initialization completed!")