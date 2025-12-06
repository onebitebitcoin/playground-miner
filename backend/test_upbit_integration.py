"""
Test Upbit integration for Bitcoin KRW pricing
"""
import os
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import IntentClassifierAgent, PriceRetrieverAgent, CalculatorAgent


def test_korean_stock_comparison():
    """Test that Bitcoin uses Upbit when comparing with Korean stocks"""

    print("=" * 100)
    print("테스트: 비트코인 + 한국 주식 비교 (Upbit KRW 사용)")
    print("=" * 100)

    prompt = "비트코인과 삼성전자의 연도별 연말 가격을 비교해줘"

    print(f"\n프롬프트: {prompt}\n")

    # Step 1: Intent Classification
    print("[Step 1] IntentClassifierAgent 실행...")
    classifier = IntentClassifierAgent()
    intent_result, intent_logs = classifier.run(prompt, [])

    for log in intent_logs:
        print(f"  {log}")

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"\n결과:")
    print(f"  - 계산 방식: {calculation_method}")
    print(f"  - 자산 수: {len(assets)}")
    for asset in assets:
        print(f"    • {asset['label']} (id: {asset['id']})")

    # Step 2: Price Retrieval
    print("\n" + "=" * 100)
    print("[Step 2] PriceRetrieverAgent 실행...")
    print("=" * 100)

    retriever = PriceRetrieverAgent()
    price_data_map, retriever_logs = retriever.run(assets, 2020, 2024)

    for log in retriever_logs:
        print(f"  {log}")

    print(f"\n결과:")
    print(f"  - 수집된 자산: {len(price_data_map)}개")

    for asset_id, data in price_data_map.items():
        source = data.get('source', 'Unknown')
        config = data.get('config', {})
        unit = config.get('unit', 'N/A')
        prefer_krw = config.get('prefer_krw', False)
        history_len = len(data.get('history', []))

        print(f"\n  자산: {config.get('label', asset_id)}")
        print(f"    - 데이터 소스: {source}")
        print(f"    - 통화 단위: {unit}")
        print(f"    - prefer_krw: {prefer_krw}")
        print(f"    - 데이터 포인트: {history_len}개")

        # Check if Bitcoin used Upbit
        if asset_id == 'bitcoin':
            if source == 'Upbit' and unit == 'KRW':
                print(f"    ✅ 비트코인이 Upbit(KRW)에서 가져와짐")
            else:
                print(f"    ❌ 비트코인이 {source}({unit})에서 가져와짐 (예상: Upbit/KRW)")
                return False

        # Check if Samsung Electronics used pykrx
        if '005930' in asset_id or '삼성전자' in config.get('label', ''):
            if source == 'pykrx' and unit == 'KRW':
                print(f"    ✅ 삼성전자가 pykrx(KRW)에서 가져와짐")
            else:
                print(f"    ❌ 삼성전자가 {source}({unit})에서 가져와짐 (예상: pykrx/KRW)")
                return False

    print("\n" + "=" * 100)
    print("✅ 테스트 통과: 한국 주식 비교 시 비트코인이 Upbit(KRW) 사용")
    print("=" * 100)
    return True


def test_us_stock_comparison():
    """Test that Bitcoin uses Yahoo Finance when comparing with US stocks"""

    print("\n\n")
    print("=" * 100)
    print("테스트: 비트코인 + 미국 주식 비교 (Yahoo Finance USD 사용)")
    print("=" * 100)

    prompt = "비트코인과 애플의 연도별 연말 가격을 비교해줘"

    print(f"\n프롬프트: {prompt}\n")

    # Step 1: Intent Classification
    print("[Step 1] IntentClassifierAgent 실행...")
    classifier = IntentClassifierAgent()
    intent_result, intent_logs = classifier.run(prompt, [])

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"  - 계산 방식: {calculation_method}")
    print(f"  - 자산 수: {len(assets)}")

    # Step 2: Price Retrieval
    print("\n[Step 2] PriceRetrieverAgent 실행...")

    retriever = PriceRetrieverAgent()
    price_data_map, retriever_logs = retriever.run(assets, 2020, 2024)

    for log in retriever_logs:
        if '한국 주식' in log or 'KRW' in log:
            print(f"  {log}")

    print(f"\n결과:")
    for asset_id, data in price_data_map.items():
        source = data.get('source', 'Unknown')
        config = data.get('config', {})
        unit = config.get('unit', 'N/A')
        prefer_krw = config.get('prefer_krw', False)

        if asset_id == 'bitcoin':
            print(f"\n  비트코인:")
            print(f"    - 데이터 소스: {source}")
            print(f"    - 통화 단위: {unit}")
            print(f"    - prefer_krw: {prefer_krw}")

            if source == 'Yahoo Finance' and unit == 'USD':
                print(f"    ✅ 비트코인이 Yahoo Finance(USD)에서 가져와짐")
            else:
                print(f"    ❌ 비트코인이 {source}({unit})에서 가져와짐 (예상: Yahoo Finance/USD)")
                return False

    print("\n" + "=" * 100)
    print("✅ 테스트 통과: 미국 주식 비교 시 비트코인이 Yahoo Finance(USD) 사용")
    print("=" * 100)
    return True


if __name__ == "__main__":
    print("\n\n")
    print("비트코인 데이터 소스 선택 로직 테스트")
    print("=" * 100)
    print("목표:")
    print("  1. 한국 주식 비교 시 → Upbit(KRW)")
    print("  2. 미국 주식 비교 시 → Yahoo Finance(USD)")
    print("=" * 100)

    test1_passed = test_korean_stock_comparison()
    test2_passed = test_us_stock_comparison()

    print("\n\n" + "=" * 100)
    print("전체 테스트 결과")
    print("=" * 100)
    print(f"1. 한국 주식 비교 테스트: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"2. 미국 주식 비교 테스트: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("=" * 100)

    if test1_passed and test2_passed:
        print("✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)
