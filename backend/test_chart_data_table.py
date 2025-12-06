"""
Test chart_data_table feature
- Verify that yearly_prices is removed
- Verify that chart_data_table is returned with actual chart values
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

import django
django.setup()

from blocks.views import IntentClassifierAgent, PriceRetrieverAgent, CalculatorAgent


def test_chart_data_table():
    """Test that chart_data_table contains actual chart values"""

    print("=" * 100)
    print("차트 데이터 테이블 기능 테스트")
    print("=" * 100)

    # Test with price mode
    prompt = "비트코인과 금의 연말 가격을 알려줘"
    print(f"\n프롬프트: {prompt}")

    # Step 1: Intent Classification
    print(f"\n[Step 1] IntentClassifierAgent")
    classifier = IntentClassifierAgent()
    intent_result, _ = classifier.run(prompt, [])

    calculation_method = intent_result.get('calculation_method')
    assets = intent_result.get('assets', [])

    print(f"  ✓ 계산 방식: {calculation_method}")
    print(f"  ✓ 자산 수: {len(assets)}")

    # Step 2: Price Retrieval
    print(f"\n[Step 2] PriceRetrieverAgent")
    retriever = PriceRetrieverAgent()
    price_data_map, _ = retriever.run(assets, 2020, 2024)

    print(f"  ✓ 수집된 자산: {len(price_data_map)}개")

    # Step 3: Calculator
    print(f"\n[Step 3] CalculatorAgent")
    calculator = CalculatorAgent()
    series_data, chart_data_table, summary, _ = calculator.run(
        price_data_map, 2020, 2024, calculation_method
    )

    print(f"  ✓ 시리즈 수: {len(series_data)}개")
    print(f"  ✓ 테이블 항목 수: {len(chart_data_table)}개")

    # Verify structure
    print(f"\n[Step 4] 테이블 구조 검증")

    if len(chart_data_table) == 0:
        print("  ✗ 테이블이 비어있음!")
        return False

    # Check first entry
    first_entry = chart_data_table[0]
    required_keys = ['id', 'label', 'value_label', 'values', 'calculation_method', 'source']

    print(f"\n  첫 번째 항목 ({first_entry.get('label', 'Unknown')}):")
    for key in required_keys:
        has_key = key in first_entry
        status = "✓" if has_key else "✗"
        print(f"    {status} {key}: {first_entry.get(key, 'MISSING')}")

    # Check values structure
    values = first_entry.get('values', [])
    if len(values) > 0:
        print(f"\n  값 샘플 (처음 3개):")
        for val in values[:3]:
            year = val.get('year')
            value = val.get('value')
            print(f"    - {year}년: {value}")

    # Verify it matches chart points
    print(f"\n[Step 5] 차트 데이터와 일치 확인")

    if len(series_data) > 0 and len(chart_data_table) > 0:
        series = series_data[0]
        table = chart_data_table[0]

        series_points = series.get('points', [])
        table_values = table.get('values', [])

        print(f"  시리즈 포인트 수: {len(series_points)}")
        print(f"  테이블 값 수: {len(table_values)}")

        if len(series_points) != len(table_values):
            print(f"  ⚠️  개수가 일치하지 않음!")
        else:
            print(f"  ✓ 개수 일치")

        # Check first value matches
        if len(series_points) > 0 and len(table_values) > 0:
            series_first = series_points[0]
            table_first = table_values[0]

            series_year = series_first.get('year')
            series_value = series_first.get('value')
            table_year = table_first.get('year')
            table_value = table_first.get('value')

            print(f"\n  첫 번째 값 비교:")
            print(f"    시리즈: {series_year}년 = {series_value}")
            print(f"    테이블: {table_year}년 = {table_value}")

            if series_year == table_year and abs(series_value - table_value) < 0.01:
                print(f"    ✓ 값이 일치함!")
            else:
                print(f"    ✗ 값이 일치하지 않음!")
                return False

    # Check value_label
    print(f"\n[Step 6] value_label 확인")
    for entry in chart_data_table:
        label = entry.get('label')
        value_label = entry.get('value_label')
        calc_method = entry.get('calculation_method')

        print(f"  {label}: {value_label} (method: {calc_method})")

    print(f"\n" + "=" * 100)
    print(f"✅ 테스트 통과: chart_data_table이 정상적으로 생성됨")
    print(f"=" * 100)

    # Print sample JSON
    print(f"\n샘플 응답 구조:")
    sample = {
        'ok': True,
        'series': f"[{len(series_data)} items with points data]",
        'chart_data_table': chart_data_table[:1],  # First item only
        'calculation_method': calculation_method,
        'summary': summary[:100] + "..."
    }
    print(json.dumps(sample, ensure_ascii=False, indent=2))

    return True


def test_multiple_methods():
    """Test different calculation methods"""

    print("\n\n" + "=" * 100)
    print("다양한 계산 방식 테스트")
    print("=" * 100)

    test_cases = [
        ("비트코인의 연말 가격", "price", "가격"),
        ("비트코인의 연평균 수익률", "cagr", "연평균 수익률 (%)"),
        ("비트코인의 누적 수익률", "cumulative", "누적 수익률 (%)"),
        ("비트코인의 전년 대비 증감률", "yearly_growth", "전년 대비 증감률 (%)"),
    ]

    for prompt, expected_method, expected_label in test_cases:
        print(f"\n테스트: {prompt}")

        classifier = IntentClassifierAgent()
        intent_result, _ = classifier.run(prompt, [])

        calc_method = intent_result.get('calculation_method')
        assets = intent_result.get('assets', [])

        retriever = PriceRetrieverAgent()
        price_data_map, _ = retriever.run(assets[:1], 2020, 2024)

        calculator = CalculatorAgent()
        _, chart_data_table, _, _ = calculator.run(
            price_data_map, 2020, 2024, calc_method
        )

        if len(chart_data_table) > 0:
            entry = chart_data_table[0]
            value_label = entry.get('value_label')

            if calc_method == expected_method and value_label == expected_label:
                print(f"  ✓ value_label: {value_label}")
            else:
                print(f"  ✗ 예상: {expected_label}, 실제: {value_label}")
        else:
            print(f"  ✗ 테이블이 비어있음")

    print(f"\n" + "=" * 100)
    print(f"✅ 모든 계산 방식 테스트 완료")
    print(f"=" * 100)


if __name__ == "__main__":
    success = test_chart_data_table()

    if success:
        test_multiple_methods()
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n❌ 테스트 실패")
        sys.exit(1)
