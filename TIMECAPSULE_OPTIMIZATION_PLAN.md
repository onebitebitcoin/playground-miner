# 타임캡슐 트랜잭션 생성 API 최적화 계획

## 현재 문제점

### 1. 성능 문제
- **블로킹 API 호출**: 최대 100번의 외부 API 호출 (각 8초 타임아웃)
- **최악 소요 시간**: 800초 (13분)
- **평균 소요 시간**: 2-5초 (UTXO가 빨리 발견될 경우)

### 2. 동시성 문제
- Django 동기 워커 블로킹
- Race condition: 같은 UTXO를 여러 사용자가 선택
- DB 트랜잭션 락 없음

### 3. 리소스 낭비
- 캐싱 없음
- 불필요한 전체 스캔

## 즉시 적용 가능한 해결책 (단계별)

### Phase 1: 긴급 핫픽스 (우선순위 높음) ⚡

#### 1.1. Rate Limiting 추가
```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# views.py에 추가
def rate_limit_build_tx(request):
    """동시 트랜잭션 생성 제한"""
    cache_key = 'building_tx_lock'
    if cache.get(cache_key):
        return JsonResponse({
            'ok': False,
            'error': '다른 트랜잭션이 생성 중입니다. 잠시 후 다시 시도해주세요.'
        }, status=429)

    # 30초 동안 락
    cache.set(cache_key, True, timeout=30)
    return None
```

#### 1.2. scan_limit 축소
```python
# Line 8108: 기본값 50 → 20으로 축소
scan_limit = max(1, min(int(scan_limit), 20))  # 기존: 200
```

#### 1.3. Early Exit 추가
```python
# Line 8122-8144에 추가
EARLY_EXIT_THRESHOLD = 10  # 10개 UTXO 찾으면 중단

total_utxos_found = 0
for change_chain in (0, 1):
    # ...
    for idx, address in enumerate(addresses):
        utxos = _fetch_address_utxos(normalized)
        if utxos:
            total_utxos_found += len(utxos)
            # Early exit
            if total_utxos_found >= EARLY_EXIT_THRESHOLD:
                break

    if total_utxos_found >= EARLY_EXIT_THRESHOLD:
        break
```

#### 1.4. 타임아웃 설정
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError("작업 시간 초과")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# admin_time_capsule_build_transaction_view에서:
try:
    with timeout(15):  # 15초 타임아웃
        _, details = _build_time_capsule_transaction(...)
except TimeoutError:
    return JsonResponse({
        'ok': False,
        'error': '트랜잭션 생성 시간이 초과되었습니다.'
    }, status=408)
```

### Phase 2: 중기 개선 (2-3일 소요) 🔧

#### 2.1. Redis 캐싱
```python
from django.core.cache import cache

def _fetch_address_utxos_cached(address, base_url=None):
    """UTXO 조회 결과 캐싱 (1분)"""
    cache_key = f'utxo:{address}'
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    utxos = _fetch_address_utxos(address, base_url)
    cache.set(cache_key, utxos, timeout=60)
    return utxos
```

#### 2.2. DB 락 추가
```python
from django.db import transaction

@transaction.atomic
def admin_time_capsule_build_transaction_view(request):
    # SELECT FOR UPDATE로 mnemonic 락
    mnemonic_obj = (
        Mnemonic.objects
        .select_for_update()
        .get(username=TIME_CAPSULE_MNEMONIC_USERNAME)
    )
    # ...
```

#### 2.3. 병렬 API 호출
```python
import concurrent.futures

def _fetch_multiple_utxos(addresses):
    """여러 주소의 UTXO를 병렬로 조회"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_fetch_address_utxos_cached, addr): addr
            for addr in addresses
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            addr = futures[future]
            try:
                results[addr] = future.result()
            except Exception as e:
                logger.warning(f'Failed to fetch {addr}: {e}')
                results[addr] = []

        return results
```

### Phase 3: 장기 아키텍처 개선 (1주 소요) 🏗️

#### 3.1. Celery 백그라운드 작업
```python
from celery import shared_task

@shared_task
def build_transaction_async(payload):
    """비동기로 트랜잭션 생성"""
    # 기존 로직
    return details

# View에서:
def admin_time_capsule_build_transaction_view(request):
    task = build_transaction_async.delay(payload)
    return JsonResponse({
        'ok': True,
        'task_id': task.id,
        'status': 'pending'
    })
```

#### 3.2. WebSocket 진행상황 알림
```python
# channels를 사용한 실시간 진행률 전송
async def build_tx_with_progress(channel_name):
    await channel_layer.send(channel_name, {
        'type': 'progress_update',
        'progress': 25,
        'message': 'UTXO 스캔 중...'
    })
```

#### 3.3. UTXO 인덱서 구축
```python
# 주기적으로 mnemonic 관련 주소의 UTXO를 미리 수집
@shared_task
def refresh_timecapsule_utxos():
    """5분마다 UTXO 캐시 갱신"""
    mnemonic_obj = _get_time_capsule_mnemonic()
    addresses = derive_all_used_addresses(mnemonic_obj)

    for addr in addresses:
        utxos = _fetch_address_utxos(addr)
        cache.set(f'utxo:{addr}', utxos, timeout=300)
```

## 권장 적용 순서

### 즉시 (오늘)
1. ✅ Rate limiting 추가
2. ✅ scan_limit 축소 (50 → 20)
3. ✅ 타임아웃 15초 설정

### 이번 주
4. ✅ Redis 캐싱 도입
5. ✅ DB 락 추가
6. ✅ Early exit 로직

### 다음 주
7. ✅ 병렬 API 호출
8. ✅ Celery 비동기 처리
9. ✅ 진행상황 UI 개선

## 예상 개선 효과

| 항목 | 현재 | Phase 1 | Phase 2 | Phase 3 |
|------|------|---------|---------|---------|
| 평균 응답 시간 | 3-5초 | 2-3초 | 1-2초 | <1초 |
| 최악 응답 시간 | 800초 | 15초 | 10초 | 5초 |
| 동시 처리 | 불가 | 1명 | 3-5명 | 무제한 |
| 캐시 적중률 | 0% | 0% | 80%+ | 95%+ |

## 모니터링 추가

```python
import time
import logging

logger = logging.getLogger(__name__)

def admin_time_capsule_build_transaction_view(request):
    start_time = time.time()

    try:
        # ... 기존 로직

        elapsed = time.time() - start_time
        logger.info(f'Build TX completed in {elapsed:.2f}s')

        return JsonResponse({'ok': True, **details})
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f'Build TX failed after {elapsed:.2f}s: {e}')
        raise
```

## 결론

현재 상태로는 **동시 사용자 2-3명만 접속해도 서버가 마비**될 수 있습니다.
최소한 Phase 1 (긴급 핫픽스)를 **즉시 적용**하는 것을 강력히 권장합니다.
