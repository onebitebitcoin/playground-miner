import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import _detect_historical_market_cap_assets


def test_detects_10year_market_cap_group():
    prompt = "10년 전에 시가총액 상위 5개 기업과 비트코인을 비교해줘"
    result = _detect_historical_market_cap_assets(prompt)

    assert result is not None
    assert any('2015' in group for group in result['groups'])
    asset_ids = {asset['id'] for asset in result['assets']}
    for expected in {'AAPL', 'MSFT', 'GOOGL', 'XOM', 'BRK.B'}:
        assert expected in asset_ids
    ranks = {asset['id']: asset['metadata']['market_cap_rank'] for asset in result['assets']}
    assert ranks['AAPL'] == 1
    assert ranks['MSFT'] == 2
    apple = next(asset for asset in result['assets'] if asset['id'] == 'AAPL')
    assert apple['metadata']['market_cap_usd'] == 750_000_000_000


def test_detects_5year_market_cap_group():
    prompt = "5년 전 시가총액 상위 5개 기업의 연평균 수익률을 보여줘"
    result = _detect_historical_market_cap_assets(prompt)

    assert result is not None
    assert any('2020' in group for group in result['groups'])
    asset_ids = {asset['id'] for asset in result['assets']}
    for expected in {'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'}:
        assert expected in asset_ids
    ranks = {asset['id']: asset['metadata']['market_cap_rank'] for asset in result['assets']}
    assert ranks['AAPL'] == 1
    assert ranks['META'] == 5
    apple = next(asset for asset in result['assets'] if asset['id'] == 'AAPL')
    assert apple['metadata']['market_cap_usd'] == 2_000_000_000_000


def test_no_detection_without_market_cap_keywords():
    prompt = "비트코인과 금의 10년 수익률을 비교해줘"
    result = _detect_historical_market_cap_assets(prompt)
    assert result is None
