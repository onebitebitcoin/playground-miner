"""
Price Calculation Test
Tests that price intent is correctly calculated (not as CAGR)
"""
import os
import sys
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import IntentClassifierAgent, PriceRetrieverAgent, CalculatorAgent


def test_price_calculation():
    """Test that price intent results in actual price values, not CAGR"""

    print("=" * 80)
    print("Testing Price Calculation Fix")
    print("=" * 80)

    # Test Case: "미국 빅테크 연말 가격"
    prompt = "비트코인과 애플, 마이크로소프트의 연도별 연말 가격을 알려줘"

    print(f"\n프롬프트: {prompt}\n")

    # Step 1: Intent Classification
    print("[Step 1] IntentClassifierAgent 실행...")
    classifier = IntentClassifierAgent()
    intent_result, intent_logs = classifier.run(prompt, [])

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"  ✓ 감지된 계산 방식: {calculation_method}")
    print(f"  ✓ 감지된 자산 수: {len(assets)}")

    if calculation_method != 'price':
        print(f"  ✗ 오류: 예상 'price', 실제 '{calculation_method}'")
        return False

    print(f"  ✓ 의도 분류 성공: price")

    # Step 2: Price Retrieval
    print(f"\n[Step 2] PriceRetrieverAgent 실행...")
    retriever = PriceRetrieverAgent()
    price_data_map, retriever_logs = retriever.run(assets, 2020, 2024)

    print(f"  ✓ 수집된 자산 데이터: {len(price_data_map)}개")

    # Check that calculation_method is preserved
    for asset_id, data in price_data_map.items():
        asset_method = data.get('calculation_method')
        if asset_method != 'price':
            print(f"  ✗ 오류: {asset_id}의 calculation_method가 '{asset_method}'로 변경됨")
            return False

    print(f"  ✓ 모든 자산의 calculation_method='price' 유지됨")

    # Step 3: Calculator
    print(f"\n[Step 3] CalculatorAgent 실행...")
    calculator = CalculatorAgent()
    series_data, yearly_prices, summary, calc_logs = calculator.run(
        price_data_map, 2020, 2024, calculation_method='price'
    )

    print(f"  ✓ 생성된 시리즈: {len(series_data)}개")
    print(f"  ✓ Summary: {summary}")

    # Verify that chart data contains actual prices, not CAGR percentages
    print(f"\n[Step 4] 차트 데이터 검증...")

    passed = True
    for series in series_data:
        asset_label = series['label']
        asset_method = series.get('calculation_method')
        points = series.get('points', [])

        print(f"\n  자산: {asset_label}")
        print(f"    - calculation_method: {asset_method}")

        if asset_method != 'price':
            print(f"    ✗ 오류: calculation_method가 '{asset_method}'")
            passed = False
            continue

        if len(points) > 0:
            # Check first and last point
            first_point = points[0]
            last_point = points[-1]

            print(f"    - {first_point['year']}: {first_point['value']:.2f}")
            print(f"    - {last_point['year']}: {last_point['value']:.2f}")

            # For price mode, values should be actual prices (likely > 100 for stocks)
            # not percentage returns (which would be close to 0 for first year)
            if first_point['value'] < 1.0 and last_point['value'] < 100.0:
                # This looks like percentage returns, not prices
                print(f"    ⚠️  경고: 값이 가격이 아닌 퍼센트처럼 보임")
                print(f"    ⚠️  예상: 실제 가격 (예: $150, $2000)")
                print(f"    ⚠️  실제: {first_point['value']}, {last_point['value']}")
                passed = False
            else:
                print(f"    ✓ 실제 가격 값이 표시됨")

    print("\n" + "=" * 80)
    if passed:
        print("✅ 테스트 통과: Price 의도가 올바르게 계산됨")
        print("=" * 80)
        return True
    else:
        print("❌ 테스트 실패: Price 의도가 CAGR로 계산됨")
        print("=" * 80)
        return False


def test_cagr_still_works():
    """Verify that CAGR mode still works correctly"""

    print("\n" + "=" * 80)
    print("Testing CAGR Calculation (Regression Test)")
    print("=" * 80)

    prompt = "비트코인과 애플의 연평균 수익률을 비교해줘"

    print(f"\n프롬프트: {prompt}\n")

    # Step 1: Intent Classification
    print("[Step 1] IntentClassifierAgent 실행...")
    classifier = IntentClassifierAgent()
    intent_result, _ = classifier.run(prompt, [])

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"  ✓ 감지된 계산 방식: {calculation_method}")

    if calculation_method != 'cagr':
        print(f"  ✗ 오류: 예상 'cagr', 실제 '{calculation_method}'")
        return False

    # Step 2 & 3: Quick test
    retriever = PriceRetrieverAgent()
    price_data_map, _ = retriever.run(assets, 2020, 2024)

    calculator = CalculatorAgent()
    series_data, _, summary, _ = calculator.run(
        price_data_map, 2020, 2024, calculation_method='cagr'
    )

    print(f"  ✓ Summary: {summary}")

    # Verify CAGR values are percentages
    for series in series_data:
        points = series.get('points', [])
        if len(points) > 0:
            last_point = points[-1]
            # CAGR should be a reasonable percentage (-50% to +200%)
            if abs(last_point['value']) > 500:
                print(f"  ✗ {series['label']}: CAGR 값이 이상함 ({last_point['value']}%)")
                return False

    print(f"  ✓ CAGR 계산 정상 작동")

    print("=" * 80)
    print("✅ CAGR 모드 정상 작동 (회귀 테스트 통과)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    print("\n\n")

    # Test 1: Price calculation
    test1_passed = test_price_calculation()

    # Test 2: CAGR still works
    test2_passed = test_cagr_still_works()

    print("\n\n" + "=" * 80)
    print("전체 테스트 결과")
    print("=" * 80)
    print(f"1. Price 계산 테스트: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"2. CAGR 회귀 테스트: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("=" * 80)

    if test1_passed and test2_passed:
        print("✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)
