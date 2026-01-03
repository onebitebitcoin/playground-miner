from blocks.models import AssetPriceCache
from blocks import views
import json
from unittest.mock import Mock

print("=" * 80)
print("배당소득세 차감 기능 테스트")
print("=" * 80)

# Clear cache
print("\n[1] JEPI 캐시 삭제...")
deleted_count = AssetPriceCache.objects.filter(asset_id='JEPI').delete()[0]
print(f"   삭제: {deleted_count}개")

def create_mock_request(payload):
    request = Mock()
    request.method = 'POST'
    request.body = json.dumps(payload).encode('utf-8')
    request.content_type = 'application/json'
    return request

asset_id = 'JEPI'
start_year = 2020
end_year = 2025

# Test 1: 배당 재투자 없음
print("\n[2] Test 1: 배당 재투자 없음")
payload_no_div = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': False,
    'include_tax': False
}

request_no_div = create_mock_request(payload_no_div)
response_no_div = views.finance_add_single_asset_view(request_no_div)
data_no_div = json.loads(response_no_div.content.decode())

if data_no_div.get('ok'):
    series_no_div = data_no_div['series']
    print(f"   ✓ 성공")
    print(f"   CAGR: {series_no_div['annualized_cagr_pct']:.2f}%")
    print(f"   배수: {series_no_div['multiple_from_start']:.3f}x")
else:
    print(f"   ❌ 실패: {data_no_div.get('error')}")

# Clear cache
AssetPriceCache.objects.filter(asset_id='JEPI').delete()

# Test 2: 세전 배당 재투자 (Adjusted Close)
print("\n[3] Test 2: 세전 배당 재투자 (Adjusted Close)")
payload_with_div_no_tax = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': True,
    'include_tax': False
}

request_with_div_no_tax = create_mock_request(payload_with_div_no_tax)
response_with_div_no_tax = views.finance_add_single_asset_view(request_with_div_no_tax)
data_with_div_no_tax = json.loads(response_with_div_no_tax.content.decode())

if data_with_div_no_tax.get('ok'):
    series_with_div_no_tax = data_with_div_no_tax['series']
    print(f"   ✓ 성공")
    print(f"   CAGR: {series_with_div_no_tax['annualized_cagr_pct']:.2f}%")
    print(f"   배수: {series_with_div_no_tax['multiple_from_start']:.3f}x")
    print(f"   배당 재투자: {series_with_div_no_tax.get('dividends_reinvested', False)}")
else:
    print(f"   ❌ 실패: {data_with_div_no_tax.get('error')}")

# Clear cache
AssetPriceCache.objects.filter(asset_id='JEPI').delete()

# Test 3: 세후 배당 재투자 (세금 15% 차감)
print("\n[4] Test 3: 세후 배당 재투자 (세금 15% 차감)")
payload_with_div_with_tax = {
    'asset_id': asset_id,
    'start_year': start_year,
    'end_year': end_year,
    'calculation_method': 'cagr',
    'include_dividends': True,
    'include_tax': True
}

request_with_div_with_tax = create_mock_request(payload_with_div_with_tax)
response_with_div_with_tax = views.finance_add_single_asset_view(request_with_div_with_tax)
data_with_div_with_tax = json.loads(response_with_div_with_tax.content.decode())

if data_with_div_with_tax.get('ok'):
    series_with_div_with_tax = data_with_div_with_tax['series']
    print(f"   ✓ 성공")
    print(f"   CAGR: {series_with_div_with_tax['annualized_cagr_pct']:.2f}%")
    print(f"   배수: {series_with_div_with_tax['multiple_from_start']:.3f}x")
    print(f"   배당 재투자: {series_with_div_with_tax.get('dividends_reinvested', False)}")
    metadata = series_with_div_with_tax.get('metadata', {})
    if metadata.get('dividend_yield_pct'):
        print(f"   배당률: {metadata['dividend_yield_pct']:.2f}%")
else:
    print(f"   ❌ 실패: {data_with_div_with_tax.get('error')}")

# Summary
print("\n" + "=" * 80)
print("결과 요약:")
print("=" * 80)

if data_no_div.get('ok') and data_with_div_no_tax.get('ok') and data_with_div_with_tax.get('ok'):
    cagr_no_div = series_no_div['annualized_cagr_pct']
    cagr_pretax = series_with_div_no_tax['annualized_cagr_pct']
    cagr_aftertax = series_with_div_with_tax['annualized_cagr_pct']

    print(f"1. 배당 재투자 없음:        {cagr_no_div:.2f}%")
    print(f"2. 세전 배당 재투자:        {cagr_pretax:.2f}%")
    print(f"3. 세후 배당 재투자 (15%):  {cagr_aftertax:.2f}%")
    print()
    print(f"세전 vs 배당 없음 차이:     +{cagr_pretax - cagr_no_div:.2f}%")
    print(f"세후 vs 배당 없음 차이:     +{cagr_aftertax - cagr_no_div:.2f}%")
    print(f"세전 vs 세후 차이:          {cagr_pretax - cagr_aftertax:.2f}%")
    print()

    # 검증
    print("검증 결과:")
    if cagr_aftertax < cagr_pretax:
        print(f"   ✓ 세후 CAGR ({cagr_aftertax:.2f}%) < 세전 CAGR ({cagr_pretax:.2f}%)")
        tax_impact = cagr_pretax - cagr_aftertax
        print(f"   ✓ 세금으로 인한 수익률 감소: {tax_impact:.2f}%p")
    else:
        print(f"   ❌ 문제: 세후 CAGR이 세전보다 높거나 같음!")

    if cagr_aftertax > cagr_no_div:
        print(f"   ✓ 세후 배당 재투자 ({cagr_aftertax:.2f}%) > 배당 없음 ({cagr_no_div:.2f}%)")
    else:
        print(f"   ⚠ 경고: 세후 배당 재투자가 배당 없음보다 낮음")

else:
    print("❌ 일부 테스트 실패")

print("=" * 80)
