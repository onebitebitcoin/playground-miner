"""
Comprehensive test for Calculator Agent fix
Tests multiple scenarios to ensure all calculation methods work correctly
"""
import os
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import IntentClassifierAgent, PriceRetrieverAgent, CalculatorAgent


def test_scenario(name, prompt, expected_method, expected_label):
    """Test a single scenario"""
    print("\n" + "=" * 100)
    print(f"테스트: {name}")
    print("=" * 100)
    print(f"프롬프트: {prompt}")
    print(f"예상 방식: {expected_method}")
    print(f"예상 로그: {expected_label}")
    print("-" * 100)

    # Step 1: Intent Classification
    classifier = IntentClassifierAgent()
    intent_result, intent_logs = classifier.run(prompt, [])

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])
    is_allowed = intent_result.get('allowed', False)

    print(f"[1] IntentClassifierAgent:")
    print(f"    - 허용 여부: {is_allowed}")
    print(f"    - 감지된 방식: {calculation_method}")
    print(f"    - 자산 수: {len(assets)}")

    if not is_allowed:
        print(f"    ✗ 가드레일 차단: {intent_result.get('error')}")
        return False

    if calculation_method != expected_method:
        print(f"    ✗ 의도 분류 실패: 예상 '{expected_method}', 실제 '{calculation_method}'")
        return False

    print(f"    ✓ 의도 분류 성공")

    # Step 2: Price Retrieval (첫 2개만)
    if len(assets) == 0:
        print(f"    ✗ 자산이 추출되지 않음")
        return False

    retriever = PriceRetrieverAgent()
    price_data_map, _ = retriever.run(assets[:2], 2020, 2024)

    print(f"[2] PriceRetrieverAgent:")
    print(f"    - 수집된 자산: {len(price_data_map)}개")

    if len(price_data_map) == 0:
        print(f"    ✗ 데이터 수집 실패 (모든 자산 실패)")
        return False

    # Verify calculation_method preserved
    for asset_id, data in price_data_map.items():
        if data.get('calculation_method') != expected_method:
            print(f"    ✗ {asset_id}: calculation_method 불일치")
            return False

    print(f"    ✓ calculation_method 유지됨")

    # Step 3: Calculator
    calculator = CalculatorAgent()
    series_data, _, summary, calc_logs = calculator.run(
        price_data_map, 2020, 2024, calculation_method
    )

    print(f"[3] CalculatorAgent:")

    # Check method_label in logs
    if len(calc_logs) > 0:
        first_log = calc_logs[0]
        print(f"    - 첫 로그: {first_log}")

        if expected_label not in first_log:
            print(f"    ✗ 로그 레이블 불일치: '{expected_label}'이 없음")
            return False

        print(f"    ✓ 로그 레이블 정확")

    # Check series data
    if len(series_data) == 0:
        print(f"    ✗ 시리즈 생성 실패")
        return False

    for series in series_data:
        if series.get('calculation_method') != expected_method:
            print(f"    ✗ {series['label']}: calculation_method 불일치")
            return False

    print(f"    ✓ 시리즈 calculation_method 정확")
    print(f"    ✓ Summary: {summary[:80]}...")

    print("\n" + "=" * 100)
    print(f"✅ 테스트 통과: {name}")
    print("=" * 100)

    return True


def main():
    """Run all test scenarios"""
    print("\n\n")
    print("=" * 100)
    print("COMPREHENSIVE CALCULATOR AGENT FIX TEST")
    print("=" * 100)

    test_cases = [
        {
            "name": "가격(Price) 요청",
            "prompt": "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘",
            "expected_method": "price",
            "expected_label": "가격(Price)"
        },
        {
            "name": "CAGR 요청",
            "prompt": "비트코인과 금의 10년 연평균 수익률을 비교해줘",
            "expected_method": "cagr",
            "expected_label": "연평균 수익률(CAGR)"
        },
        {
            "name": "누적 수익률 요청",
            "prompt": "비트코인과 S&P 500의 누적 수익률을 비교해줘",
            "expected_method": "cumulative",
            "expected_label": "누적 상승률"
        },
        {
            "name": "전년 대비 증감률 요청",
            "prompt": "비트코인과 금의 전년 대비 증감률을 알려줘",
            "expected_method": "yearly_growth",
            "expected_label": "전년 대비 증감률(YoY)"
        }
    ]

    results = []
    for test_case in test_cases:
        try:
            passed = test_scenario(
                test_case["name"],
                test_case["prompt"],
                test_case["expected_method"],
                test_case["expected_label"]
            )
            results.append((test_case["name"], passed))
        except Exception as e:
            print(f"❌ 테스트 실패: {test_case['name']}")
            print(f"   오류: {e}")
            results.append((test_case["name"], False))

    # Summary
    print("\n\n" + "=" * 100)
    print("전체 테스트 결과")
    print("=" * 100)

    passed_count = sum(1 for _, passed in results if passed)
    failed_count = len(results) - passed_count

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print("=" * 100)
    print(f"총 {len(results)}개 테스트 중 {passed_count}개 통과, {failed_count}개 실패")
    print("=" * 100)

    if failed_count == 0:
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed_count}개 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
