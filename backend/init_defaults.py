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

from blocks.models import ExchangeRate, WithdrawalFee, LightningService, Mnemonic


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
        { 'exchange': 'binance', 'withdrawal_type': 'lightning', 'fee_btc': 0.00001, 'description': '바이낸스 라이트닝 출금 수수료' },
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
        { 'service': 'boltz',  'fee_rate': 0.5, 'is_kyc': False, 'description': 'Boltz 교환 수수료 (non-KYC)' },
        { 'service': 'coinos', 'fee_rate': 0.0, 'is_kyc': False, 'description': 'Coinos 라이트닝 간 거래수수료 0% (non-KYC)' },
        { 'service': 'walletofsatoshi', 'fee_rate': 0.0, 'is_kyc': False, 'description': '월렛오브사토시 라이트닝 간 거래수수료 0% (non-KYC)' },
        { 'service': 'strike', 'fee_rate': 0.0, 'is_kyc': True, 'description': 'Strike 라이트닝 간 거래수수료 0%, 온체인 출금수수료 0% (KYC)' },
    ]
    created = 0
    for d in defaults:
        obj, was_created = LightningService.objects.get_or_create(
            service=d['service'],
            defaults={
                'fee_rate': d['fee_rate'],
                'is_kyc': d['is_kyc'],
                'description': d['description'],
            },
        )
        created += 1 if was_created else 0
    return created


def seed_mnemonics(count=10):
    # limited list used in views for demo generation
    word_pool = [
        'abandon','ability','able','about','above','absent','absorb','abstract','absurd','abuse','access','accident',
        'account','accuse','achieve','acid','acoustic','acquire','across','act','action','actor','actress','actual',
        'adapt','add','addict','address','adjust','admit','adult','advance','advice','aerobic','affair','afford',
        'afraid','again','agent','agree','ahead','aim','air','airport','aisle','alarm','album','alcohol','alert',
        'alien','all','alley','allow','almost','alone','alpha','already','also','alter','always','amateur','amazing',
        'among','amount','amused','analyst','anchor','ancient','anger','angle','angry','animal','ankle','announce',
        'annual','another','answer','antenna','antique','anxiety','any','apart','apology','appear','apple','approve',
        'april','arch','arctic','area','arena','argue','arm','armed','armor','army','around','arrange','arrest',
        'arrive','arrow','art','article','artist','artwork','ask','aspect','assault','asset','assist','assume','asthma'
    ]
    created = 0
    for i in range(count):
        words = random.sample(word_pool, 12)
        mnemonic = ' '.join(words)
        # only create if there are no unassigned mnemonics at all
        if not Mnemonic.objects.filter(is_assigned=False).exists():
            Mnemonic.objects.create(username=f'seed-{i+1}', mnemonic=mnemonic, is_assigned=False)
            created += 1
        else:
            break
    return created


def main():
    created = 0
    created += seed_exchange_rates()
    created += seed_withdrawal_fees()
    created += seed_lightning_services()
    # Only seed mnemonics if none exist
    if Mnemonic.objects.count() == 0 or not Mnemonic.objects.filter(is_assigned=False).exists():
        created += seed_mnemonics()
    print(f"Seeding complete. Created/added entries: {created}")


if __name__ == '__main__':
    main()

