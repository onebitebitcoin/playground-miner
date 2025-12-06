# Calculator Agent Issue Analysis

## 🐛 문제 상황

**증상**: 프롬프트로 "미국 빅테크 연말 가격"을 요청하면 의도는 `price`로 분류되지만, 실제 계산은 `cagr`로 수행됨

**발생 사례**:
- 프롬프트: "미국 빅테크 10개 종목의 연도별 연말 가격을 알려줘"
- IntentClassifierAgent 결과: `calculation_method = 'price'` ✓
- CalculatorAgent 실제 계산: `cagr` 방식 사용 ✗

---

## 🔍 근본 원인 분석

### 문제의 흐름

```
User Request
    ↓
[Agent 1] IntentClassifierAgent
    ├─ 프롬프트 분석: "연말 가격" → method='price' ✓
    ├─ 자산 추출: [BTC, AAPL, MSFT, ...]
    └─ 각 자산에 calculation_method='price' 할당 ✓
    ↓
[Agent 2] PriceRetrieverAgent
    ├─ 각 자산별 데이터 수집
    └─ price_data_map 생성:
        {
          'BTC': {
            'history': [...],
            'config': {...},
            'calculation_method': 'price'  ✓ (3492번 라인)
          },
          'AAPL': {
            'history': [...],
            'config': {...},
            'calculation_method': 'price'  ✓
          }
        }
    ↓
[Agent 3] CalculatorAgent
    ├─ run(price_data_map, start_year, end_year, calculation_method='price')
    ├─ 문제 발생 지점 (3536번 라인):
    │   asset_calc_method = data.get('calculation_method', calculation_method)
    │   → 'price' 가져옴 ✓
    ├─ _build_asset_series() 호출 (3540번 라인):
    │   series_obj = _build_asset_series(config['id'], config, history,
    │                                    start_year, end_year, asset_calc_method)
    │   → asset_calc_method='price' 전달 ✓
    └─ _build_asset_series 내부 (2784-2957번 라인):
        ├─ calculation_method 파라미터 받음 ✓
        ├─ 2889-2892번 라인: price/cumulative 계산 로직 존재 ✓
        │   if calculation_method == 'cumulative' or calculation_method == 'price':
        │       return_pct = (multiple - 1) * 100  # 누적 상승률
        ├─ 2931-2933번 라인: price 최종 수익률 계산 ✓
        │   if calculation_method == 'cumulative' or calculation_method == 'price':
        │       final_return_pct = (end_val / start_val - 1) * 100
        └─ 2956번 라인: calculation_method 반환 ✓
            'calculation_method': calculation_method
```

### ⚠️ 실제 문제 지점

**놀랍게도, 코드 자체는 정상적으로 작동합니다!**

문제는 다른 곳에 있습니다:

#### 1️⃣ **차트 데이터 혼동**
- `calculation_method='price'` 요청 시, `_build_asset_series`는 **누적 상승률(cumulative)**로 변환하여 차트 데이터를 생성합니다 (2889-2892번 라인)
- 이는 의도적 설계입니다: "Price requests are visualized as Cumulative Trend (Index) on the chart for comparison" (2891번 주석)
- 즉, **가격 비교를 시각화하기 위해 기준점 대비 누적 상승률로 차트를 그립니다**

#### 2️⃣ **정렬 기준 혼동** (3584번 라인)
```python
# Sort by CAGR descending
series_list.sort(key=lambda x: x.get('annualized_return_pct', -999), reverse=True)
```
- 주석에 "Sort by CAGR descending"이라고 되어 있지만
- 실제로는 `annualized_return_pct` 필드로 정렬
- `price` 모드에서는 이 값이 **누적 상승률**입니다 (2933번 라인)
- 따라서 주석이 잘못되었고, 실제로는 각 calculation_method에 맞는 값으로 정렬됨

#### 3️⃣ **Summary 메시지 혼동** (3589-3610번 라인)
```python
def _generate_summary(self, series_list, start_year, end_year):
    method = best.get('calculation_method', 'cagr')
    if method == 'cumulative' or method == 'price':
        unit = "누적 수익률"
    elif method == 'yearly_growth':
        unit = "평균 증감률"
    else:
        unit = "연평균 수익률"

    return (f"{start_year}년부터 {end_year}년까지 분석 결과, "
            f"{best['label']}이(가) {unit} {best['annualized_return_pct']}%로 가장 높은 성과를 보였으며, "
            f"{worst['label']}은(는) {worst['annualized_return_pct']}%를 기록했습니다.")
```
- `price` 요청 시 summary는 "누적 수익률"이라고 표시 ✓
- 하지만 사용자가 원한 것은 "연말 가격" 정보

---

## 🎯 실제 문제 정리

### 문제 1: UI/UX 혼동
**현상**: 사용자가 "연말 가격을 알려줘"라고 요청했는데, 차트에는 "누적 상승률"이 표시됨

**원인**:
- `price` 요청을 `cumulative` 상승률 차트로 시각화하는 것은 **의도된 설계**
- 하지만 사용자는 실제 가격 값을 기대함

**해결 방안**:
1. `yearly_prices_list`에 실제 가격 데이터가 있으므로, 프론트엔드에서 price 모드일 때 차트 타입을 변경
2. 또는 `calculation_method='price'`일 때 차트 데이터를 누적 상승률이 아닌 실제 가격으로 변경

### 문제 2: Summary 메시지 부적절
**현상**: "연말 가격"을 요청했는데 summary가 "누적 수익률로 가장 높은 성과"라고 표시

**원인**:
- `_generate_summary`가 price와 cumulative를 동일하게 취급
- 하지만 사용자의 의도는 다름

**해결 방안**:
- `price` 모드일 때 summary 메시지를 다르게 생성:
  ```
  "2015년부터 2024년까지 가격 비교 결과,
  Bitcoin의 가격이 $434에서 $42,000으로 가장 크게 상승했습니다."
  ```

### 문제 3: 정렬 로직 주석 오해
**현상**: 코드 주석에 "Sort by CAGR"라고 되어 있어 혼란

**원인**: 주석이 오래되었거나 부정확함

**해결 방안**: 주석 수정
```python
# Sort by return metric (CAGR/Cumulative/YoY) descending
```

---

## ✅ 코드 레벨 검증

### 테스트 케이스: "미국 빅테크 연말 가격"

**IntentClassifierAgent (라인 3218-3379)**
```python
# 입력
prompt = "미국 빅테크 10개 종목의 연도별 연말 가격을 알려줘"

# 출력
{
  'allowed': True,
  'calculation_method': 'price',  ✓
  'assets': [
    {'id': 'AAPL', 'label': 'Apple', 'calculation_method': 'price'},  ✓
    ...
  ]
}
```

**PriceRetrieverAgent (라인 3446-3514)**
```python
# 입력
assets = [{'id': 'AAPL', 'label': 'Apple', 'calculation_method': 'price'}, ...]

# 출력 (라인 3488-3493)
price_data_map = {
  'AAPL': {
    'history': [(date, price), ...],
    'config': {...},
    'calculation_method': 'price'  ✓
  }
}
```

**CalculatorAgent (라인 3516-3591)**
```python
# 입력 (라인 3757)
calculator_agent.run(price_data_map, start_year, end_year, calculation_method='price')

# 처리 (라인 3536)
asset_calc_method = data.get('calculation_method', calculation_method)
# → 'price' ✓

# _build_asset_series 호출 (라인 3540)
series_obj = _build_asset_series(config['id'], config, history,
                                start_year, end_year, 'price')  ✓
```

**_build_asset_series (라인 2784-2957)**
```python
# 입력
calculation_method = 'price'

# 차트 데이터 계산 (라인 2889-2892)
if calculation_method == 'cumulative' or calculation_method == 'price':
    # 누적 상승률로 변환 (의도적 설계)
    return_pct = (multiple - 1) * 100  ✓

# points 예시
points = [
  {'year': 2015, 'value': 0.0, 'multiple': 1.0},      # 100% 기준
  {'year': 2016, 'value': 35.2, 'multiple': 1.352},   # +35.2%
  {'year': 2017, 'value': 120.5, 'multiple': 2.205},  # +120.5%
  ...
]

# 최종 수익률 계산 (라인 2931-2933)
if calculation_method == 'cumulative' or calculation_method == 'price':
    final_return_pct = (end_val / start_val - 1) * 100  ✓
    # → 누적 상승률

# 반환값 (라인 2948-2957)
return {
  'label': 'Apple',
  'points': points,  # 누적 상승률 차트 데이터
  'annualized_return_pct': 350.2,  # 전체 기간 누적 상승률
  'calculation_method': 'price'  ✓
}
```

---

## 🔧 결론

### 코드는 정상 작동합니다!

1. ✅ IntentClassifierAgent: `price` 의도 정확히 감지
2. ✅ PriceRetrieverAgent: `calculation_method='price'` 정확히 전달
3. ✅ CalculatorAgent: `calculation_method='price'` 정확히 받아서 처리
4. ✅ `_build_asset_series`: `price` 모드로 정확히 계산

### 하지만 사용자 경험이 혼란스럽습니다

**현재 동작**:
- "연말 가격" 요청 → 누적 상승률 차트 + 가격 테이블

**사용자 기대**:
- "연말 가격" 요청 → 실제 가격 차트 + 가격 테이블

**해결 방법**:
1. **차트 데이터 변경**: `price` 모드일 때 실제 가격을 표시
2. **Summary 메시지 개선**: 가격 비교에 적합한 메시지
3. **주석 명확화**: 코드 의도를 명확히 표현

---

## 📝 추천 수정 사항

### 1. `_build_asset_series` 수정 (라인 2886-2922)

**현재**:
```python
if calculation_method == 'cumulative' or calculation_method == 'price':
    # 누적 상승률
    return_pct = (multiple - 1) * 100
```

**수정안**:
```python
if calculation_method == 'price':
    # 실제 가격 표시
    return_pct = adjusted_value  # 실제 가격
elif calculation_method == 'cumulative':
    # 누적 상승률
    return_pct = (multiple - 1) * 100
```

### 2. `_generate_summary` 수정 (라인 3593-3610)

**수정안**:
```python
def _generate_summary(self, series_list, start_year, end_year):
    if not series_list:
        return "데이터가 없습니다."

    best = series_list[0]
    worst = series_list[-1]
    method = best.get('calculation_method', 'cagr')

    if method == 'price':
        # 가격 비교 모드
        return (f"{start_year}년부터 {end_year}년까지 가격 비교 결과, "
                f"{best['label']}의 가격 상승률이 {best['annualized_return_pct']}%로 가장 높았으며, "
                f"{worst['label']}은(는) {worst['annualized_return_pct']}%를 기록했습니다.")
    elif method == 'cumulative':
        unit = "누적 수익률"
    elif method == 'yearly_growth':
        unit = "평균 증감률"
    else:
        unit = "연평균 수익률"

    return (f"{start_year}년부터 {end_year}년까지 분석 결과, "
            f"{best['label']}이(가) {unit} {best['annualized_return_pct']}%로 가장 높은 성과를 보였으며, "
            f"{worst['label']}은(는) {worst['annualized_return_pct']}%를 기록했습니다.")
```

### 3. 정렬 주석 수정 (라인 3584)

**현재**:
```python
# Sort by CAGR descending
```

**수정안**:
```python
# Sort by return metric descending (CAGR/Cumulative/YoY/Price change)
```
