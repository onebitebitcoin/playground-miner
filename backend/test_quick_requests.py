import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.views import IntentClassifierAgent

# Quick Requests from FinancePage.vue
test_cases = [
    {
        "name": "1. Safe Assets - CAGR",
        "prompt": "비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 원유, 구리의 10년 연평균 수익률을 비교해줘",
        "expected_method": "cagr"
    },
    {
        "name": "2. US Tech - CAGR",
        "prompt": "비트코인과 미국 빅테크 10개 종목(애플, 마이크로소프트, 알파벳, 아마존, 메타, 테슬라, 엔비디아, 넷플릭스, 어도비, AMD)의 10년 연평균 수익률을 비교해줘",
        "expected_method": "cagr"
    },
    {
        "name": "3. KR Equity - CAGR",
        "prompt": "비트코인과 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 현대차, 기아, 삼성바이오로직스, 삼성SDI, 포스코홀딩스의 10년 연평균 수익률을 비교해줘",
        "expected_method": "cagr"
    },
    {
        "name": "4. Safe Assets - Price",
        "prompt": "비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 원유, 구리의 연도별 연말 가격을 알려줘",
        "expected_method": "price"
    },
    {
        "name": "5. US Tech - Price",
        "prompt": "비트코인과 미국 빅테크 10개 종목의 연도별 연말 가격을 알려줘",
        "expected_method": "price"
    },
    {
        "name": "6. KR Equity - Price",
        "prompt": "비트코인과 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 현대차, 기아, 삼성바이오로직스, 삼성SDI, 포스코홀딩스의 연도별 연말 가격을 알려줘",
        "expected_method": "price"
    },
    {
        "name": "7. Safe Assets - YoY",
        "prompt": "비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 원유, 구리의 전년 대비 증감률을 비교해줘",
        "expected_method": "yearly_growth"
    },
    {
        "name": "8. US Tech - YoY",
        "prompt": "비트코인과 미국 빅테크 10개 종목의 전년 대비 증감률을 비교해줘",
        "expected_method": "yearly_growth"
    },
    {
        "name": "9. KR Equity - YoY",
        "prompt": "비트코인과 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 현대차, 기아, 삼성바이오로직스, 삼성SDI, 포스코홀딩스의 전년 대비 증감률을 비교해줘",
        "expected_method": "yearly_growth"
    },
    {
        "name": "10. M2 Compare - CAGR",
        "prompt": "지난 10년간 미국의 M2 통화량 연평균 상승률과 한국의 M2 연평균 상승률, 비트코인을 비교해줘",
        "expected_method": "cagr"
    }
]

classifier = IntentClassifierAgent()

passed_count = 0
failed_count = 0

print(f"Running tests for {len(test_cases)} Quick Requests...\n")

for case in test_cases:
    print(f"--- {case['name']} ---")
    print(f"Prompt: {case['prompt'][:60]}...")
    
    # 1. Run Intent Classifier
    intent_result, _ = classifier.run(case['prompt'], [])
    detected_method = intent_result.get('calculation_method')
    
    # Check
    method_match = detected_method == case['expected_method']
    final_pass = method_match
    
    if final_pass:
        passed_count += 1
        print("RESULT: [PASS]")
    else:
        failed_count += 1
        print("RESULT: [FAIL]")
        print(f"  - Expected Method: {case['expected_method']}")
        print(f"  - Detected Method: {detected_method}")
    print("")

print(f"Summary: {passed_count} Passed, {failed_count} Failed")

if failed_count > 0:
    sys.exit(1)
else:
    sys.exit(0)
