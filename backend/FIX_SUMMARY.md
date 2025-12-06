# Calculator Agent 수정 완료 보고서

## 📋 문제 요약

### 사용자 보고 문제
**프롬프트**: "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"

**증상**:
- 의도 분류는 `price`로 정확히 감지됨
- 하지만 CalculatorAgent 로그에 "연평균 수익률(CAGR) 계산 및 데이터 포맷팅 중..."으로 표시됨
- 실제 계산은 CAGR 방식으로 수행되는 것처럼 보임

---

## 🔍 근본 원인 분석

### 발견된 문제 2가지

#### 1️⃣ **CalculatorAgent의 method_label 로직 누락**

**위치**: `backend/blocks/views.py:3529`

**문제 코드**:
```python
def run(self, price_data_map, start_year, end_year, calculation_method='cagr'):
    logs = []
    method_label = '누적 상승률' if calculation_method == 'cumulative' else '연평균 수익률(CAGR)'
    logs.append(f"[수익률 계산] {method_label} 계산 및 데이터 포맷팅 중...")
```

**문제점**:
- `price`와 `yearly_growth` 케이스가 처리되지 않음
- `price` 요청 시 else 문으로 빠져서 "연평균 수익률(CAGR)"로 표시됨
- 실제 계산은 올바르게 수행되지만, 로그 메시지가 부정확함

#### 2️⃣ **Guardrail이 가격 요청을 차단**

**위치**: `backend/blocks/views.py:3075-3087`

**문제 코드**:
```python
guardrail_system_prompt = _get_agent_prompt('guardrail',
    "당신은 사용자 요청의 의도를 분류하는 전문가입니다.\n\n"
    "주어진 사용자 요청이 다음 중 어디에 해당하는지 판단하세요:\n\n"
    "1. **금융 분석 요청**: 자산(예: 비트코인, 삼성전자, S&P 500 등)의 수익률, 가격 변동, 비교 분석 등을 원하는 경우.\n"
    "   - 이런 경우 'allowed': true를 반환하세요.\n\n"
    "2. **부적절한 요청**: 금융 분석과 무관하거나, 개인정보를 요구하거나, 시스템 악용을 시도하는 경우.\n"
    "   - 이런 경우 'allowed': false를 반환하고, 'reason'에 거부 사유를 간단히 설명하세요.\n\n"
)
```

**문제점**:
- "연말 가격을 알려줘"라는 표현이 모호함
- Guardrail LLM이 이를 미래 예측으로 오인
- 차단 사유: "미래의 가격 예측은 불가능하며, 요청이 금융 분석의 범위를 벗어남"
- 실제로는 과거 데이터 조회 요청이지만 명시적 설명이 없어 오인

---

## 🔧 적용한 수정사항

### 수정 1: CalculatorAgent method_label 완전 구현

**파일**: `backend/blocks/views.py:3527-3540`

**수정 전**:
```python
def run(self, price_data_map, start_year, end_year, calculation_method='cagr'):
    logs = []
    method_label = '누적 상승률' if calculation_method == 'cumulative' else '연평균 수익률(CAGR)'
    logs.append(f"[수익률 계산] {method_label} 계산 및 데이터 포맷팅 중...")
```

**수정 후**:
```python
def run(self, price_data_map, start_year, end_year, calculation_method='cagr'):
    logs = []

    # Determine method label based on calculation_method
    if calculation_method == 'price':
        method_label = '가격(Price)'
    elif calculation_method == 'cumulative':
        method_label = '누적 상승률'
    elif calculation_method == 'yearly_growth':
        method_label = '전년 대비 증감률(YoY)'
    else:
        method_label = '연평균 수익률(CAGR)'

    logs.append(f"[수익률 계산] {method_label} 계산 및 데이터 포맷팅 중...")
```

**효과**:
- ✅ `price` 요청 시: "가격(Price) 계산 및 데이터 포맷팅 중..."
- ✅ `cagr` 요청 시: "연평균 수익률(CAGR) 계산 및 데이터 포맷팅 중..."
- ✅ `cumulative` 요청 시: "누적 상승률 계산 및 데이터 포맷팅 중..."
- ✅ `yearly_growth` 요청 시: "전년 대비 증감률(YoY) 계산 및 데이터 포맷팅 중..."

### 수정 2: Guardrail 프롬프트 강화

**파일**: `backend/blocks/views.py:3075-3094`

**수정 후**:
```python
guardrail_system_prompt = _get_agent_prompt('guardrail',
    "당신은 사용자 요청의 의도를 분류하는 전문가입니다.\n\n"
    "주어진 사용자 요청이 다음 중 어디에 해당하는지 판단하세요:\n\n"
    "1. **금융 분석 요청** (allowed=true): 자산의 과거 데이터 분석을 원하는 경우\n"
    "   - 과거 수익률, 가격 변동, 비교 분석 (예: '비트코인 수익률', '삼성전자 주가')\n"
    "   - 연도별/연말 가격 조회 (예: '연말 가격을 알려줘', '2020년부터 2024년까지 가격')\n"
    "   - 가격 비교 (예: '비트코인과 금 비교', '미국 빅테크 기업들의 가격')\n"
    "   - **중요**: '연말 가격', '연도별 가격'은 과거 데이터 요청이므로 allowed=true\n\n"
    "2. **부적절한 요청** (allowed=false): 다음과 같은 경우만 거부\n"
    "   - 금융 분석과 완전히 무관한 요청 (예: '날씨 알려줘', '게임 추천')\n"
    "   - 개인정보 요구 (예: '사용자 비밀번호', '계좌번호')\n"
    "   - 시스템 악용 시도\n"
    "   - **미래 예측 요청** (예: '내일 비트코인 가격 예측', '2025년 주가 전망')\n\n"
    "**주의**: 단순히 '가격'이라는 단어가 있다고 거부하지 마세요. 과거 가격 조회는 정상적인 금융 분석입니다.\n\n"
)
```

**개선 사항**:
- ✅ "연말 가격", "연도별 가격" 명시적 예시 추가
- ✅ 과거 가격 조회와 미래 예측 명확히 구분
- ✅ 가격 요청이 정상적인 금융 분석임을 강조
- ✅ "주의" 섹션으로 LLM에게 명확한 가이드 제공

### 수정 3: 차트 데이터 및 Summary (이전 수정)

**이미 적용된 수정사항**:

1. **실제 가격 표시** (`views.py:2889-2894`)
   ```python
   if calculation_method == 'price':
       return_pct = adjusted_value  # 실제 가격
   elif calculation_method == 'cumulative':
       return_pct = (multiple - 1) * 100  # 누적 상승률
   ```

2. **Summary 메시지 개선** (`views.py:3607-3611`)
   ```python
   if method == 'price':
       return (f"{start_year}년부터 {end_year}년까지 가격 비교 결과, "
               f"{best['label']}의 가격 상승률이 {best['annualized_return_pct']}%로 가장 높았으며...")
   ```

---

## ✅ 테스트 결과

### 종합 테스트 (4개 시나리오)

```
====================================================================================================
전체 테스트 결과
====================================================================================================
✅ PASS: 가격(Price) 요청
✅ PASS: CAGR 요청
✅ PASS: 누적 수익률 요청
✅ PASS: 전년 대비 증감률 요청
====================================================================================================
총 4개 테스트 중 4개 통과, 0개 실패
====================================================================================================
🎉 모든 테스트 통과!
```

### 실제 사용자 프롬프트 테스트

**프롬프트**: "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"

#### 수정 전
```
[의도 분석] 요청 차단됨. 사유: 미래의 가격 예측은 불가능하며, 요청이 금융 분석의 범위를 벗어남
[수익률 계산] 연평균 수익률(CAGR) 계산 및 데이터 포맷팅 중...  ← 잘못된 레이블
```

#### 수정 후
```
[의도 분석] 보안 검사 통과  ✓
[의도 분석] 키워드 감지: '가격(Price)' 분석 요청  ✓
[의도 분석] 8개 자산 추출 완료: Bitcoin, Apple, Microsoft, Alphabet, Amazon, Meta, Tesla, Nvidia  ✓
[의도 분석] 최종 계산 방식: 가격(Price)  ✓
[수익률 계산] 가격(Price) 계산 및 데이터 포맷팅 중...  ✓
Summary: 2020년부터 2024년까지 가격 비교 결과, 비트코인의 가격 상승률이 222.15%로 가장 높았으며...  ✓
차트 데이터: 2020: $29,001.72 → 2024: $93,429.20  ✓
```

### 상세 검증 결과

| 테스트 항목 | 수정 전 | 수정 후 |
|-----------|---------|---------|
| **Guardrail 통과** | ✗ 차단 | ✅ 통과 |
| **의도 분류** | N/A (차단됨) | ✅ price |
| **Calculator 로그** | ✗ "CAGR 계산..." | ✅ "가격(Price) 계산..." |
| **차트 데이터** | N/A | ✅ 실제 가격 ($29K → $93K) |
| **Summary** | N/A | ✅ "가격 비교 결과..." |
| **CAGR 모드 (회귀)** | ✅ 정상 | ✅ 정상 (영향 없음) |

---

## 📊 수정 전후 비교

### 시나리오 1: "연말 가격을 알려줘"

| 단계 | 수정 전 | 수정 후 |
|-----|---------|---------|
| **Guardrail** | ✗ 차단 ("미래 예측") | ✅ 통과 ("과거 데이터 조회") |
| **IntentClassifier** | - | ✅ method='price' |
| **Calculator 로그** | - | ✅ "가격(Price) 계산..." |
| **차트** | - | ✅ 실제 가격 표시 |

### 시나리오 2: "연평균 수익률 비교"

| 단계 | 수정 전 | 수정 후 |
|-----|---------|---------|
| **Guardrail** | ✅ 통과 | ✅ 통과 |
| **IntentClassifier** | ✅ method='cagr' | ✅ method='cagr' |
| **Calculator 로그** | ✅ "CAGR 계산..." | ✅ "연평균 수익률(CAGR) 계산..." |
| **차트** | ✅ CAGR % | ✅ CAGR % (동일) |

---

## 🎯 해결된 문제 목록

### ✅ 주요 문제
1. ✅ Guardrail이 "연말 가격" 요청을 미래 예측으로 오인하여 차단
2. ✅ CalculatorAgent 로그가 항상 "CAGR 계산..."으로 표시되는 문제
3. ✅ Price 모드에서 차트에 누적 상승률 대신 실제 가격 표시
4. ✅ Summary 메시지가 가격 요청에 맞지 않는 문제

### ✅ 부가 개선
5. ✅ `yearly_growth` 모드 로그 레이블 추가
6. ✅ 정렬 주석 명확화
7. ✅ Price와 Cumulative 명시적 분리

---

## 📝 생성된 테스트 파일

1. **`backend/test_real_prompt.py`**
   - 실제 사용자 프롬프트로 전체 플로우 테스트
   - Guardrail, IntentClassifier, PriceRetriever, Calculator 순차 검증

2. **`backend/test_comprehensive_fix.py`**
   - 4가지 calculation_method 모두 테스트
   - Price, CAGR, Cumulative, YoY 각각 검증

3. **`backend/test_price_calculation.py`**
   - Price와 CAGR 계산 비교 테스트
   - 회귀 테스트 포함

4. **`backend/test_intent_validation_agent.py`**
   - 10개 Quick Request 테스트
   - 의도 분류 정확도 검증

5. **`backend/ISSUE_ANALYSIS_calculator_agent.md`**
   - 상세 문제 분석 리포트
   - 코드 흐름 추적

---

## 🚀 변경 파일 요약

### `backend/blocks/views.py`

#### 1. Guardrail 프롬프트 강화 (라인 3075-3094)
- "연말 가격", "연도별 가격"을 과거 데이터 조회로 명시
- 미래 예측과 명확히 구분

#### 2. CalculatorAgent method_label 완전 구현 (라인 3527-3540)
- `price` → "가격(Price)"
- `cumulative` → "누적 상승률"
- `yearly_growth` → "전년 대비 증감률(YoY)"
- `cagr` → "연평균 수익률(CAGR)"

#### 3. 차트 데이터 계산 분리 (라인 2889-2894)
- `price`: 실제 가격 표시
- `cumulative`: 누적 상승률 (%)

#### 4. 최종 수익률 계산 명확화 (라인 2933-2938)
- `price`와 `cumulative` 명시적 분리

#### 5. Summary 메시지 개선 (라인 3607-3611)
- `price`: "가격 비교 결과..."
- 기타: 기존 로직 유지

#### 6. 정렬 주석 수정 (라인 3589)
- "Sort by CAGR" → "Sort by return metric (CAGR/Cumulative/YoY/Price change)"

---

## 💡 핵심 개선 사항

### Before (문제)
```
사용자: "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"
시스템: ✗ 차단됨 - "미래의 가격 예측은 불가능"
```

### After (해결)
```
사용자: "비트코인과 미국 빅테크 기업의 연말 가격을 알려줘"
시스템: ✓ 보안 검사 통과
       ✓ 키워드 감지: '가격(Price)' 분석 요청
       ✓ 8개 자산 추출 완료
       ✓ 가격(Price) 계산 및 데이터 포맷팅 중...
       ✓ 차트: 실제 가격 ($29K → $93K)
       ✓ Summary: "가격 비교 결과, 비트코인의 가격 상승률이 222.15%..."
```

---

## ✅ 최종 검증

### 모든 Calculation Method 정상 작동 확인

| Method | Guardrail | Intent | Calculator 로그 | 차트 데이터 | Summary | 상태 |
|--------|-----------|--------|----------------|-----------|---------|------|
| **price** | ✅ 통과 | ✅ price | ✅ "가격(Price)" | ✅ 실제 가격 | ✅ "가격 비교" | ✅ |
| **cagr** | ✅ 통과 | ✅ cagr | ✅ "CAGR" | ✅ CAGR % | ✅ "연평균 수익률" | ✅ |
| **cumulative** | ✅ 통과 | ✅ cumulative | ✅ "누적 상승률" | ✅ 누적 % | ✅ "누적 수익률" | ✅ |
| **yearly_growth** | ✅ 통과 | ✅ yearly_growth | ✅ "YoY" | ✅ YoY % | ✅ "평균 증감률" | ✅ |

---

## 🎉 결론

**모든 문제가 완전히 해결되었습니다!**

1. ✅ Guardrail이 과거 가격 조회를 정상적으로 허용
2. ✅ CalculatorAgent 로그가 정확한 calculation_method 표시
3. ✅ Price 모드에서 실제 가격 값 표시
4. ✅ Summary 메시지가 의도에 맞게 생성
5. ✅ 모든 calculation_method (price, cagr, cumulative, yearly_growth) 정상 작동
6. ✅ 회귀 테스트 통과 - 기존 기능에 영향 없음

### 테스트 실행 방법

```bash
# 실제 프롬프트 테스트
python3 backend/test_real_prompt.py

# 종합 테스트 (4가지 시나리오)
python3 backend/test_comprehensive_fix.py

# 가격 vs CAGR 비교
python3 backend/test_price_calculation.py

# 의도 분류 검증 (10개 케이스)
python3 backend/test_intent_validation_agent.py
```

---

**수정 완료일**: 2025-11-28
**테스트 통과율**: 100% (4/4 종합 테스트)
