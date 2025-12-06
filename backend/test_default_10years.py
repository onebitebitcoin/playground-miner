"""
Test default 10 years period addition
"""
import os
import sys

# Setup Django environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')

# Force bitcoinlib data directory to workspace-local path
local_bitcoinlib_dir = os.path.join(CURRENT_DIR, '.bitcoinlib')
os.environ.setdefault('BCL_DATA_DIR', local_bitcoinlib_dir)
os.makedirs(local_bitcoinlib_dir, exist_ok=True)

import django
django.setup()

from blocks.views import IntentClassifierAgent


def test_default_period():
    """Test that prompts without time period get '지난 10년' added"""

    test_cases = [
        {
            "name": "기간 없음 - 기본 10년 추가되어야 함",
            "prompt": "비트코인과 금의 수익률을 비교해줘",
            "should_add_period": True
        },
        {
            "name": "기간 명시 (10년) - 추가 안됨",
            "prompt": "비트코인과 금의 10년 수익률을 비교해줘",
            "should_add_period": False
        },
        {
            "name": "기간 명시 (5년) - 추가 안됨",
            "prompt": "비트코인과 금의 5년간 수익률을 비교해줘",
            "should_add_period": False
        },
        {
            "name": "기간 명시 (5년 전 대비) - 추가 안됨",
            "prompt": "비트코인과 S&P500의 5년 전 대비 가격을 비교해줘",
            "should_add_period": False
        },
        {
            "name": "기간 명시 (1년 전) - 추가 안됨",
            "prompt": "비트코인에 100만원을 투자했다면 1년 전에 얼마였고 지금은 얼마인지 비교해줘",
            "should_add_period": False
        },
        {
            "name": "기간 명시 (최근) - 추가 안됨",
            "prompt": "비트코인과 금의 최근 수익률을 비교해줘",
            "should_add_period": False
        },
        {
            "name": "연도 명시 - 추가 안됨",
            "prompt": "2020년부터 2024년까지 비트코인 가격",
            "should_add_period": False
        },
        {
            "name": "기간 없음 (가격) - 기본 10년 추가",
            "prompt": "비트코인과 애플의 연말 가격을 알려줘",
            "should_add_period": True
        }
    ]

    print("=" * 100)
    print("기본 10년 기간 설정 테스트")
    print("=" * 100)

    classifier = IntentClassifierAgent()
    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n테스트: {test['name']}")
        print(f"프롬프트: {test['prompt']}")

        intent_result, logs = classifier.run(test['prompt'], [])

        # Check if period was added
        period_added = any("기본 기간 설정" in log for log in logs)

        print(f"기간 추가 여부: {period_added}")
        print(f"예상: {test['should_add_period']}")

        if period_added == test['should_add_period']:
            print("✅ 통과")
            passed += 1
        else:
            print("❌ 실패")
            failed += 1

        # Show relevant logs
        for log in logs:
            if "기본 기간" in log or "의도 분석" in log:
                print(f"  - {log}")

    print("\n" + "=" * 100)
    print(f"결과: {passed}개 통과, {failed}개 실패")
    print("=" * 100)

    return failed == 0


if __name__ == "__main__":
    success = test_default_period()
    sys.exit(0 if success else 1)
