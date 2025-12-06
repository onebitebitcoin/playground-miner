"""
Test with real user prompt: "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"
"""
import os
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import IntentClassifierAgent, PriceRetrieverAgent, CalculatorAgent


def test_real_prompt():
    """Test with the exact user prompt"""

    prompt = "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"

    print("=" * 100)
    print(f"프롬프트: {prompt}")
    print("=" * 100)

    # Step 1: Intent Classification
    print("\n[Step 1] IntentClassifierAgent 실행...")
    print("-" * 100)
    classifier = IntentClassifierAgent()
    intent_result, intent_logs = classifier.run(prompt, [])

    for log in intent_logs:
        print(f"  {log}")

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"\n결과:")
    print(f"  - 감지된 계산 방식: {calculation_method}")
    print(f"  - 감지된 자산 수: {len(assets)}")
    print(f"  - 자산 목록:")
    for asset in assets:
        print(f"    • {asset['label']} (id: {asset['id']}, method: {asset.get('calculation_method', 'N/A')})")

    if calculation_method != 'price':
        print(f"\n  ⚠️  문제 발견: 예상 'price', 실제 '{calculation_method}'")
    else:
        print(f"\n  ✓ 의도 분류 정확: price")

    # Step 2: Price Retrieval
    print("\n" + "=" * 100)
    print("[Step 2] PriceRetrieverAgent 실행...")
    print("-" * 100)
    retriever = PriceRetrieverAgent()
    price_data_map, retriever_logs = retriever.run(assets[:3], 2020, 2024)  # 처음 3개만 테스트

    for log in retriever_logs:
        print(f"  {log}")

    print(f"\n결과:")
    print(f"  - 수집된 자산: {len(price_data_map)}개")
    for asset_id, data in price_data_map.items():
        method = data.get('calculation_method', 'N/A')
        print(f"    • {asset_id}: calculation_method={method}")

    # Step 3: Calculator
    print("\n" + "=" * 100)
    print("[Step 3] CalculatorAgent 실행...")
    print("-" * 100)
    print(f"  입력 calculation_method: {calculation_method}")

    calculator = CalculatorAgent()
    series_data, yearly_prices, summary, calc_logs = calculator.run(
        price_data_map, 2020, 2024, calculation_method
    )

    for log in calc_logs:
        print(f"  {log}")

    print(f"\n결과:")
    print(f"  - 생성된 시리즈: {len(series_data)}개")
    print(f"  - Summary: {summary}")

    # Check method_label in logs
    method_label_log = None
    for log in calc_logs:
        if "계산 및 데이터 포맷팅" in log:
            method_label_log = log
            break

    if method_label_log:
        print(f"\n  첫 번째 로그: {method_label_log}")
        if "연평균 수익률(CAGR)" in method_label_log and calculation_method == 'price':
            print(f"  ⚠️  문제 발견: method_label이 CAGR로 표시됨 (예상: 가격)")

    # Verify series data
    print("\n" + "=" * 100)
    print("[Step 4] 시리즈 데이터 검증...")
    print("-" * 100)

    for series in series_data:
        label = series['label']
        method = series.get('calculation_method', 'N/A')
        points = series.get('points', [])

        print(f"\n  {label}:")
        print(f"    - calculation_method: {method}")

        if len(points) >= 2:
            first = points[0]
            last = points[-1]
            print(f"    - {first['year']}: {first['value']:.2f}")
            print(f"    - {last['year']}: {last['value']:.2f}")

            if method == 'price':
                if first['value'] > 100:
                    print(f"    ✓ 실제 가격 값이 표시됨")
                else:
                    print(f"    ⚠️  가격 값이 너무 작음 (퍼센트처럼 보임)")
            elif method == 'cagr':
                if abs(first['value']) < 100:
                    print(f"    ✓ CAGR % 값이 표시됨")
                else:
                    print(f"    ⚠️  CAGR 값이 너무 큼 (가격처럼 보임)")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    test_real_prompt()
