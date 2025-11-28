# 연도별 종가 비교 API 문서

## 📊 개요
- **국내 주식(KOSPI/KOSDAQ)**: `pykrx` 라이브러리만 사용해 일별 OHLCV를 수집합니다. pykrx에서 데이터가 없으면 요청을 실패로 처리하며, 다른 공급자를 사용하지 않습니다.
- **그 외 자산(해외 주식, 지수, 원자재 등)**: 기본적으로 `yfinance` 월봉을 사용하고, 실패 시 `Stooq` CSV를 폴백으로 호출합니다.
- **비트코인**: 달러 가격은 `Yahoo Finance`(`BTC-USD`)에서, 원화 가격은 `Upbit` 월봉 데이터를 사용합니다. 원화 표시에선 환율 변환이 아니라 업비트 실가격을 그대로 노출합니다.

## 🆕 API 엔드포인트
- **경로**: `POST /api/finance/yearly-closing-prices`
- **용도**: 프론트엔드 `연도별 종가 비교` 테이블/툴팁에서 실데이터를 보여주기 위한 경량 API

### 요청 구조
| 필드 | 타입 | 설명 |
|------|------|------|
| `start_year` | number | (선택) 조회 시작 연도. 생략 시 서버 기본값 적용 |
| `end_year` | number | (선택) 조회 종료 연도. 기본값은 현재 연도 |
| `assets` | array | `{id, label, unit, category}` 객체 배열. 최소 1개 필수 |

```json
{
  "start_year": 2016,
  "end_year": 2024,
  "assets": [
    { "id": "bitcoin", "label": "비트코인" },
    { "id": "005930.KS", "label": "삼성전자(005930)", "unit": "KRW", "category": "국내 주식" }
  ]
}
```

### 응답 예시
```json
{
  "ok": true,
  "start_year": 2016,
  "end_year": 2024,
  "data": [
    {
      "id": "bitcoin",
      "label": "비트코인",
      "unit": "USD",
      "category": "디지털 자산",
      "source": "yahoo",
      "requested_id": "BTC-USD",
      "aliases": ["bitcoin", "BTC-USD", "btc_usd"],
      "prices": [
        { "year": 2016, "value": 995.0 },
        { "year": 2017, "value": 13060.0 }
      ],
      "alt_prices": {
        "krw": [
          { "year": 2016, "value": 1357000.0 },
          { "year": 2017, "value": 19995000.0 }
        ]
      },
      "alt_sources": {
        "krw": "upbit"
      }
    },
    {
      "id": "005930.KS",
      "label": "삼성전자(005930)",
      "unit": "KRW",
      "category": "국내 주식",
      "source": "pykrx",
      "requested_id": "005930.KS",
      "aliases": ["삼성전자", "005930.KS", "005930"],
      "prices": [
        { "year": 2016, "value": 160800.0 },
        { "year": 2017, "value": 241500.0 }
      ]
    }
  ],
  "errors": []
}
```

> `requested_id`는 프런트엔드가 보낸 자산 ID를 그대로 반환해 매칭에 사용합니다. `aliases`는 동일 자산을 다른 이름으로 부를 때 매핑하는 데 활용하고, `alt_prices`/`alt_sources`는 통화별(예: KRW) 대체 시세를 명시합니다. `errors` 배열은 부분 실패 시 한글 메시지를 포함합니다. `ok`가 `false`인 경우 전체 요청이 실패한 것이므로 프론트엔드는 즉시 오류를 표기하면 됩니다.

## 🔄 국내 주식 데이터 플로우
```
사용자 요청 (예: 삼성전자)
    ↓
Ticker: 005930.KS
    ↓
┌─────────────────────────────────────┐
│ pykrx 호출                         │
│ - 005930.KS → 005930 (숫자코드)     │
│ - stock.get_market_ohlcv_by_date   │
│ - 성공 시: 일별 종가/거래량 확보   │
└─────────────────────────────────────┘
    ↓
연도별로 마지막 거래일 종가 선택 → 프론트 표시
```

> ⚠️ pykrx가 실패하면 해당 자산은 바로 오류 처리되며, 다른 공급자로 폴백하지 않습니다.

## ⚙️ 주요 데이터 소스
### 1. pykrx (국내 주식 전용)
- 리포지토리: https://github.com/sharebook-kr/pykrx
- 함수 사용 예시:

```python
from pykrx import stock

def fetch_ohlcv(code, start, end):
    df = stock.get_market_ohlcv_by_date(start, end, code)
    return df[['시가', '고가', '저가', '종가', '거래량']]
```

- 프로젝트 내 테스트: `python3 test_pykrx_api.py --ticker 005930 --days 5`
- 의존성: `backend/requirements.txt`에 `pykrx>=1.0.48` 명시

### 2. yfinance + Stooq (해외/기타 자산)
- `yfinance`에서 월봉(`interval='1mo'`)을 먼저 시도하고, 실패 시 Stooq CSV(`i=m` → 필요 시 `i=d`)로 보강합니다.
- `_fetch_stooq_history()`에서 HTTP GET + `csv.DictReader`를 사용합니다.
- 심볼은 자산 ID에서 `stooq_symbol`을 우선 사용하고, 없을 경우 `_guess_stooq_symbol()`로 변환합니다.

### 3. Yahoo Finance + Upbit (비트코인 전용)
- `yfinance`를 통해 `BTC-USD` 티커의 월봉(`interval='1mo'`) 데이터를 가져옵니다.
- 실패 시 Stooq(`btc_usd`)로 폴백하여 데이터 안정성을 확보합니다.
- `Upbit` `v1/candles/months` API로 KRW 월봉을 가져오고, 부족하면 과거로 반복 조회합니다. 응답의 `trade_price`를 연도별 마지막 값으로 사용합니다.
- `_fetch_coingecko_history()`, `_fetch_upbit_monthly_history()`, `_build_bitcoin_price_payload()`가 이 역할을 담당하며, 원화 표시는 환율 변환 없이 업비트 데이터를 그대로 씁니다.

## 🧩 백엔드 코드 맵
| 함수 | 위치 (backend/blocks/views.py) | 설명 |
|------|--------------------------------|------|
| `_fetch_pykrx_history` | 약 1905~1954 | pykrx에서 일별 OHLCV 수집 및 정규화 |
| `_fetch_korean_stock_history` | 약 2019~2040 | 한국 주식 진입점 (pykrx만 호출) |
| `_fetch_stooq_history` | 약 2056~2126 | Stooq CSV를 통해 월별/일별 종가 수집 |
| `_fetch_upbit_monthly_history` | 약 2176~2209 | 비트코인 KRW 월봉 데이터 수집 |
| `_build_bitcoin_price_payload` | 약 2220~2238 | USD/ KRW 연도별 종가 페이로드 구성 |
| `_fetch_yearly_closing_prices` | 약 2241~2274 | pykrx/Stooq/비트코인 소스별 연도 데이터를 구성 |
| `finance_yearly_closing_prices_view` | 약 3216~3288 | 새 API 엔드포인트. 요청 파싱, 자산 매칭, 가격 응답 |

핵심 로직:
```python
if _is_bitcoin_config(cfg):
    payload = _build_bitcoin_price_payload(...)
elif is_korean_stock and ticker:
    history = _fetch_korean_stock_history(...)
    source = 'pykrx'
else:
    symbol = _guess_stooq_symbol(ticker)
    history = _fetch_stooq_history(symbol, ...)
    source = 'stooq'

prices = _build_yearly_closing_points(history, start_year, end_year)
```

## 🧪 테스트 스크립트
| 스크립트 | 목적 |
|----------|------|
| `test_pykrx_api.py` | pykrx로 최근 시세를 가져오는 CLI 스모크 테스트 |
| `test_full_flow.py` | Finance API 전체 흐름 테스트 (KR 요청 시 pykrx만 사용) |
| `test_stooq_api.py` | Stooq CSV 응답 확인 (참고용, 국내 주식에 사용하지 않음) |
| `test_stooq.py`, `test_krx_api.py` 등 | 레거시 실험 스크립트 |

## 📈 데이터 처리
1. pykrx 일별 데이터 → 정렬 후 각 연도 마지막 거래일 추출
2. `SAFE_ASSETS`/프리셋 구성 요소에 따라 연도별 raw value 생성
3. 연평균 수익률/배수 계산 로직은 기존과 동일
4. 스케일링
   - pykrx/국내: 원화 그대로 (scale 1)
   - Stooq: 응답 통화(USD, index 등) 그대로 사용
5. 비트코인은 Yahoo Finance USD 데이터를 기준으로 수익률을 계산하고, 연도별 KRW 표시는 업비트 월봉 데이터를 별도로 보관하여 프론트엔드가 통화별로 선택할 수 있게 합니다.

## 🖥️ 프론트엔드 표시
- `frontend/src/pages/FinancePage.vue`에서 `selectedContextKey === 'kr_equity'`일 때 데이터 출처로 pykrx 링크만 노출
- 종가 테이블 셀은 네이버 금융 링크(연도 무관)로 유지하여 사용자가 참고 데이터를 열람 가능

## 🔧 트러블슈팅
1. **pykrx 미설치/ImportError**
   - `pip install -r backend/requirements.txt`
   - 시스템에 pandas/numpy 의존성이 설치되어야 합니다.
2. **KR 요청 실패**
   - 백엔드 로그에서 `[종목] pykrx에서 데이터 가져오기 시도` 메시지 확인
   - KRX 코드(6자리)가 올바른지 확인 (`005930.KS` → `005930`)
3. **해외/비트코인 자산 오류**
   - Stooq CSV 응답 상태/내용을 확인하세요. 심볼 인코딩이 올바른지 재검증합니다.
   - 비트코인이라면 Upbit API 제한을 먼저 확인한 뒤 재시도합니다. Yahoo Finance 데이터는 yfinance 라이브러리를 통해 수집됩니다.

## 📚 참고 자료
- pykrx: https://github.com/sharebook-kr/pykrx
- yfinance: https://pypi.org/project/yfinance/ (BTC-USD 포함)
- Stooq CSV: https://stooq.com
- Upbit Open API: https://docs.upbit.com/
- 네이버 금융: https://finance.naver.com

## 📝 변경 이력
- **2025-01-06**: `finance/yearly-closing-prices` API 추가. 해외 자산은 yfinance→Stooq 순으로 조회하고, 비트코인은 Yahoo Finance(USD)/Upbit(KRW) 가격을 병행 지원하도록 백엔드·프론트·문서를 갱신.
- **2025-11-27**: 국내 주식 데이터 공급자를 pykrx 단일 소스로 고정, Yahoo/Stooq 폴백 제거. UI/문서/요건 업데이트.
- **2024-12-30**: 초기 버전 문서화, 네이버 링크 추가 등.
