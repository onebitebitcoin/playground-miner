import csv
import io
import json
import logging
import re
import time
import threading
import hashlib
from datetime import datetime, timedelta
import requests
import yfinance as yf
try:
    from pykrx import stock as pykrx_stock
except ImportError:  # pragma: no cover - optional dependency
    pykrx_stock = None
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Block, Nickname, Mnemonic, ExchangeRate, WithdrawalFee, LightningService, ServiceNode, Route, RoutingSnapshot, SidebarConfig, KingstoneWallet, FinanceQueryLog
from django.db import connection
from django.conf import settings
from .broadcast import broadcaster
from .btc import derive_bip84_addresses, fetch_blockstream_balances, calc_total_sats, derive_bip84_account_zpub, derive_master_fingerprint, _normalize_mnemonic
from mnemonic import Mnemonic as MnemonicValidator



MAX_NONCE = 100000
DIFFICULTY_BASE = 5000
KINGSTONE_WALLET_LIMIT = 3
FINANCE_DEFAULT_START_YEAR = 2015
FINANCE_YEAR_SPAN = 10
FINANCE_MAX_SERIES = 15

SAFE_ASSETS = {
    'bitcoin': {
        'label': '비트코인',
        'ticker': 'BTC-USD',
        'stooq_symbol': 'btc_usd',
        'unit': 'USD',
        'category': '디지털 자산',
        'aliases': ['비트코인', 'bitcoin', 'btc']
    },
    'gold': {
        'label': '금',
        'ticker': 'GC=F',
        'stooq_symbol': 'xauusd',
        'unit': 'USD',
        'category': '안전자산',
        'aliases': ['금', 'gold', '골드']
    },
    'us10y': {
        'label': '미국 10년물 국채',
        'ticker': '^TNX',
        'stooq_symbol': None,  # Stooq doesn't have yield data, use Yahoo Finance only
        'unit': '%',
        'category': '채권',
        'aliases': ['미국 10년물 국채', '10년물 국채', 'us 10y', 'us10y', 'treasury', '미국 국채'],
        'yield_asset': True  # This is a yield (percentage), not a price
    },
    'silver': {
        'label': '은',
        'ticker': 'SI=F',
        'stooq_symbol': 'xagusd',
        'unit': 'USD',
        'category': '안전자산',
        'aliases': ['은', 'silver']
    },
    'sp500': {
        'label': 'S&P 500',
        'ticker': '^GSPC',
        'stooq_symbol': 'spx',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['s&p 500', 'sp500', 's&p500', '에스앤피500']
    },
    'dow': {
        'label': '다우지수',
        'ticker': '^DJI',
        'stooq_symbol': 'dji',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['다우', '다우지수', 'dow', 'dow jones']
    },
    'nasdaq100': {
        'label': '나스닥 100',
        'ticker': '^NDX',
        'stooq_symbol': 'ndq',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['나스닥 100', '나스닥100', 'nasdaq 100', 'nasdaq100']
    },
    'oil': {
        'label': '원유(USO)',
        'ticker': 'USO',
        'stooq_symbol': 'uso.us',
        'unit': 'USD',
        'category': '원자재',
        'aliases': ['원유', 'crude oil', 'oil', 'wti', '브렌트']
    },
    'copper': {
        'label': '구리(CPER)',
        'ticker': 'CPER',
        'stooq_symbol': 'cper.us',
        'unit': 'USD',
        'category': '원자재',
        'aliases': ['구리', 'copper']
    },
    'dxy': {
        'label': '달러지수(UUP)',
        'ticker': 'UUP',
        'stooq_symbol': 'uup.us',
        'unit': 'USD',
        'category': '통화',
        'aliases': ['달러지수', 'dxy', 'dollar index', '달러 인덱스']
    }
}

SAFE_ASSET_ALIASES = {}
for key, cfg in SAFE_ASSETS.items():
    for alias in cfg.get('aliases', []):
        SAFE_ASSET_ALIASES[alias.lower()] = key

PRESET_STOCK_GROUPS = {
    'us_bigtech': [
        {'id': 'AAPL', 'label': '애플(AAPL)', 'ticker': 'AAPL', 'stooq_symbol': 'aapl.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['apple', 'aapl']},
        {'id': 'MSFT', 'label': '마이크로소프트(MSFT)', 'ticker': 'MSFT', 'stooq_symbol': 'msft.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['microsoft', 'msft']},
        {'id': 'GOOGL', 'label': '알파벳(GOOGL)', 'ticker': 'GOOGL', 'stooq_symbol': 'googl.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['alphabet', 'google', 'googl', 'goog']},
        {'id': 'AMZN', 'label': '아마존(AMZN)', 'ticker': 'AMZN', 'stooq_symbol': 'amzn.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['amazon', 'amzn']},
        {'id': 'META', 'label': '메타(META)', 'ticker': 'META', 'stooq_symbol': 'meta.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['meta', 'facebook', 'fb']},
        {'id': 'TSLA', 'label': '테슬라(TSLA)', 'ticker': 'TSLA', 'stooq_symbol': 'tsla.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['tesla', 'tsla']},
        {'id': 'NVDA', 'label': '엔비디아(NVDA)', 'ticker': 'NVDA', 'stooq_symbol': 'nvda.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['nvidia', 'nvda']},
        {'id': 'NFLX', 'label': '넷플릭스(NFLX)', 'ticker': 'NFLX', 'stooq_symbol': 'nflx.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['netflix', 'nflx']},
        {'id': 'ADBE', 'label': '어도비(ADBE)', 'ticker': 'ADBE', 'stooq_symbol': 'adbe.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['adobe', 'adbe']},
        {'id': 'AMD', 'label': 'AMD(AMD)', 'ticker': 'AMD', 'stooq_symbol': 'amd.us', 'category': '미국 빅테크', 'unit': 'USD', 'aliases': ['amd']}
    ],
    'kr_equity': [
        {'id': '005930.KS', 'label': '삼성전자(005930)', 'ticker': '005930.KS', 'stooq_symbol': '005930.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['samsung electronics', '삼성전자', 'samsung', '005930']},
        {'id': '000660.KS', 'label': 'SK하이닉스(000660)', 'ticker': '000660.KS', 'stooq_symbol': '000660.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['sk hynix', 'sk하이닉스', 'hynix', '000660']},
        {'id': '035420.KS', 'label': 'NAVER(035420)', 'ticker': '035420.KS', 'stooq_symbol': '035420.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['naver', '네이버', '035420']},
        {'id': '035720.KS', 'label': '카카오(035720)', 'ticker': '035720.KS', 'stooq_symbol': '035720.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['kakao', '카카오', '035720']},
        {'id': '373220.KS', 'label': 'LG에너지솔루션(373220)', 'ticker': '373220.KS', 'stooq_symbol': '373220.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['lg energy solution', 'lg에너지솔루션', 'lg energy', '373220']},
        {'id': '005380.KS', 'label': '현대차(005380)', 'ticker': '005380.KS', 'stooq_symbol': '005380.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['hyundai motor', '현대차', 'hyundai', '005380']},
        {'id': '000270.KS', 'label': '기아(000270)', 'ticker': '000270.KS', 'stooq_symbol': '000270.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['kia', '기아', 'kia motors', '000270']},
        {'id': '207940.KS', 'label': '삼성바이오로직스(207940)', 'ticker': '207940.KS', 'stooq_symbol': '207940.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['samsung biologics', '삼성바이오로직스', 'samsung bio', '207940']},
        {'id': '006400.KS', 'label': '삼성SDI(006400)', 'ticker': '006400.KS', 'stooq_symbol': '006400.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['samsung sdi', '삼성sdi', '삼성에스디아이', '006400']},
        {'id': '005490.KS', 'label': '포스코홀딩스(005490)', 'ticker': '005490.KS', 'stooq_symbol': '005490.kr', 'category': '국내 주식', 'unit': 'KRW', 'aliases': ['posco holdings', '포스코홀딩스', 'posco', '005490']}
    ]
}

_guest_counter = 0
_guest_lock = threading.Lock()
_btc_usdt_cache = {'price': None, 'expires_at': 0.0}
_btc_usdt_lock = threading.Lock()
_usdkrw_cache = {'rate': None, 'expires_at': 0.0}
_usdkrw_lock = threading.Lock()
FINANCE_CACHE_PURGE_VERSIONS = {
    'safe_assets': 2,
}
_purged_finance_contexts = {}
_HTTP_DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; PlaygroundMiner/1.0; +https://playground-miner)'
}

logger = logging.getLogger(__name__)


def get_cached_btc_usdt_price():
    """Return cached BTC/USDT price, refreshing from Binance if needed."""
    now = time.time()
    cached_price = _btc_usdt_cache['price']
    if cached_price and now < _btc_usdt_cache['expires_at']:
        return cached_price
    with _btc_usdt_lock:
        cached_price = _btc_usdt_cache['price']
        if cached_price and now < _btc_usdt_cache['expires_at']:
            return cached_price
        try:
            resp = requests.get(
                'https://api.binance.com/api/v3/ticker/price',
                params={'symbol': 'BTCUSDT'},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            price = float(data.get('price'))
            if price <= 0:
                raise ValueError('invalid BTCUSDT price')
            _btc_usdt_cache['price'] = price
            _btc_usdt_cache['expires_at'] = time.time() + 60  # cache for 60s
            return price
        except Exception:
            return _btc_usdt_cache['price']


def get_cached_usdkrw_rate():
    now = time.time()
    if _usdkrw_cache['rate'] and now < _usdkrw_cache['expires_at']:
        return _usdkrw_cache['rate']
    with _usdkrw_lock:
        if _usdkrw_cache['rate'] and now < _usdkrw_cache['expires_at']:
            return _usdkrw_cache['rate']
        fetchers = []
        if getattr(settings, 'ECOS_API_KEY', ''):
            fetchers.append(('bok', _fetch_usdkrw_from_bok))
        fetchers.extend([
            ('exchangerate_host', _fetch_usdkrw_from_exchange_host),
            ('erapi', _fetch_usdkrw_from_erapi),
            ('jsdelivr', _fetch_usdkrw_from_jsdelivr),
        ])
        for source, fetcher in fetchers:
            try:
                quote = fetcher()
            except Exception as exc:
                logger.warning('Failed to fetch USD/KRW from %s: %s', source, exc)
                continue
            if quote and quote > 0:
                _usdkrw_cache['rate'] = quote
                _usdkrw_cache['expires_at'] = time.time() + 1800
                return quote
        return _usdkrw_cache['rate'] or 1300.0


def _fetch_usdkrw_from_bok():
    api_key = getattr(settings, 'ECOS_API_KEY', '') or ''
    if not api_key:
        raise ValueError('ECOS_API_KEY is not configured')
    now_kst = datetime.utcnow() + timedelta(hours=9)
    end_date = now_kst.strftime('%Y%m%d')
    start_date = (now_kst - timedelta(days=31)).strftime('%Y%m%d')
    url = (
        f'https://ecos.bok.or.kr/api/StatisticSearch/'
        f'{api_key}/json/kr/1/10/036Y001/D/{start_date}/{end_date}/USD'
    )
    resp = requests.get(url, timeout=10, headers=_HTTP_DEFAULT_HEADERS)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get('StatisticSearch')
    rows = None
    if isinstance(data, dict):
        rows = data.get('row')
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get('row'):
                rows = entry['row']
                break
    if not rows:
        return None

    def _row_time(row):
        return row.get('TIME') or row.get('TIME_PERIOD') or ''

    for row in sorted(rows, key=_row_time, reverse=True):
        value = _safe_float(row.get('DATA_VALUE') or row.get('data_value') or row.get('DATA'))
        if value:
            return value
    return None


def _fetch_usdkrw_from_exchange_host():
    resp = requests.get(
        'https://api.exchangerate.host/latest',
        params={'base': 'USD', 'symbols': 'KRW'},
        timeout=10
    )
    resp.raise_for_status()
    payload = resp.json()
    rate = (payload.get('rates') or {}).get('KRW')
    return _safe_float(rate)


def _fetch_usdkrw_from_erapi():
    resp = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    rate = (payload.get('rates') or {}).get('KRW')
    return _safe_float(rate)


def _fetch_usdkrw_from_jsdelivr():
    resp = requests.get(
        'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/krw.json',
        timeout=10
    )
    resp.raise_for_status()
    payload = resp.json()
    rate = payload.get('krw')
    return _safe_float(rate)


def calc_difficulty_for_height(height: int) -> int:
    # 10블록마다 절반씩 난이도(허용 최대값)를 낮춤
    # 높이 0(아직 블록 없음)일 때 현재 난이도는 10000
    step = height // 10
    d = DIFFICULTY_BASE // (2 ** step)
    return max(1, d)


def calc_reward_for_height(next_height: int) -> int:
    # 블록 보상: 100부터 시작, 20개 블록마다 절반으로
    step = (next_height - 1) // 20
    r = 100 // (2 ** step)
    return max(1, r)


def current_status():
    height = Block.objects.aggregate(m=Max('height'))['m'] or 0
    difficulty = calc_difficulty_for_height(height)
    reward = calc_reward_for_height(height + 1) if height >= 0 else 100
    return { 'height': height, 'difficulty': difficulty, 'reward': reward }


def status_view(_request):
    return JsonResponse(current_status())


def blocks_view(_request):
    qs = Block.objects.order_by('-height').values('height','nonce','miner','difficulty','reward','timestamp')[:200]
    data = list(qs)
    return JsonResponse({ 'blocks': data })


@csrf_exempt
def mine_view(request):
    if request.method != 'POST':
        return JsonResponse({ 'ok': False, 'error': 'POST만 허용됩니다.' }, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({ 'ok': False, 'error': '잘못된 JSON' }, status=400)

    miner = (payload.get('miner') or 'guest')[:64]
    try:
        nonce = int(payload.get('nonce'))
    except Exception:
        return JsonResponse({ 'ok': False, 'error': 'nonce가 필요합니다.' }, status=400)

    if not (1 <= nonce <= MAX_NONCE):
        return JsonResponse({ 'ok': False, 'error': 'nonce 범위(1~100000) 오류' }, status=400)

    # 현재 난이도 판단(다음 블록 높이에 대한 난이도)
    with transaction.atomic():
        height = Block.objects.select_for_update().count()
        difficulty = calc_difficulty_for_height(height)
        # 조건: 생성된 난수 ≤ 현재 난이도(허용 최대값)
        if nonce > difficulty:
            return JsonResponse({ 'ok': False, 'error': '난이도 조건 불만족' }, status=200)

        next_height = height + 1
        reward = calc_reward_for_height(next_height)
        block = Block.objects.create(
            height=next_height,
            nonce=nonce,
            miner=miner,
            difficulty=difficulty,
            reward=reward,
        )
        # no cache layer; nothing to invalidate

    # 방송
    status = current_status()
    notice = f"{miner} 님이 블록 #{block.height}를 채굴했습니다."
    broadcaster.publish({ 'type': 'block', 'block': block.as_dict(), 'status': status, 'notice': notice })
    return JsonResponse({ 'ok': True, 'block': block.as_dict(), 'status': status })


def stream_view(_request):
    global _guest_counter
    requested = _request.GET.get('nick')
    nickname = None
    if requested:
        try:
            if Nickname.objects.filter(name=requested[:64]).exists():
                nickname = requested[:64]
        except Exception:
            nickname = None
    if not nickname:
        with _guest_lock:
            _guest_counter += 1
            nickname = f"guest {_guest_counter}"
    q = broadcaster.add_listener({ 'nickname': nickname })
    # 새 접속자 목록을 모든 클라이언트에 즉시 방송(기존 클라이언트도 즉시 갱신)
    broadcaster.publish({ 'type': 'peers', 'peers': broadcaster.peers() })

    def event_stream():
        try:
            # Advise client to retry every 3s if disconnected
            yield "retry: 3000\n\n"
            # 초기 스냅샷 전송
            # Build snapshot directly (no cache) for freshness
            blocks_snapshot = list(Block.objects.order_by('-height').values('height','nonce','miner','difficulty','reward','timestamp')[:200])
            initial = {
                'type': 'snapshot',
                'blocks': blocks_snapshot,
                'status': current_status(),
                'me': { 'nickname': nickname },
                'peers': broadcaster.peers(),
            }
            yield f"data: {json.dumps(initial)}\n\n"

            # 하트비트 + 메시지 처리 루프
            last_heartbeat = time.time()
            while True:
                try:
                    data = q.get(timeout=1.0)
                    yield f"data: {data}\n\n"
                except Exception:
                    pass
                # 10초마다 하트비트
                if time.time() - last_heartbeat > 10:
                    hb = { 'type': 'status', 'status': current_status() }
                    yield f"data: {json.dumps(hb)}\n\n"
                    last_heartbeat = time.time()
        finally:
            broadcaster.remove_listener(q)
            # 접속자 목록 갱신 방송
            broadcaster.publish({ 'type': 'peers', 'peers': broadcaster.peers() })

    resp = StreamingHttpResponse(event_stream(), content_type='text/event-stream; charset=utf-8')
    resp['Cache-Control'] = 'no-cache'
    # For Nginx: disable proxy buffering to support SSE
    resp['X-Accel-Buffering'] = 'no'
    return resp


@csrf_exempt
def register_nick_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        nickname = (payload.get('nickname') or '').strip()[:64]
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    if not nickname:
        return JsonResponse({'ok': False, 'error': 'nickname required'}, status=400)
    try:
        obj, created = Nickname.objects.get_or_create(name=nickname)
        return JsonResponse({'ok': True, 'nickname': obj.name, 'created': created})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': 'db error'}, status=500)


def check_nick_view(request):
    nickname = (request.GET.get('nickname') or '').strip()[:64]
    if not nickname:
        return JsonResponse({'ok': False, 'error': 'nickname required'}, status=400)
    exists = Nickname.objects.filter(name=nickname).exists()
    return JsonResponse({'ok': True, 'exists': exists})


@csrf_exempt
def init_reset_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    # Simple protection using env token
    import os
    # Default password is '0000' unless overridden by INIT_TOKEN/ADMIN_TOKEN
    expected = os.environ.get('INIT_TOKEN') or os.environ.get('ADMIN_TOKEN') or '0000'
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = {}
    token = payload.get('token') or request.headers.get('X-Admin-Token')
    if expected and token != expected:
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)

    # Reset blocks and guest counter
    Block.objects.all().delete()
    global _guest_counter
    with _guest_lock:
        _guest_counter = 0
    # Broadcast updated status and peers
    broadcaster.publish({'type': 'status', 'status': current_status()})
    broadcaster.publish({'type': 'peers', 'peers': broadcaster.peers()})
    return JsonResponse({'ok': True, 'status': current_status()})


# Mnemonic API views
@csrf_exempt
def request_mnemonic_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    try:
        # Try to parse requester username (optional)
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            payload = {}
        requester = (payload.get('username') or '').strip()[:64]
        # Find an unassigned mnemonic
        mnemonic_obj = Mnemonic.objects.filter(is_assigned=False).first()
        if not mnemonic_obj:
            return JsonResponse({'ok': False, 'error': '사용 가능한 니모닉이 없습니다'}, status=200)

        # Mark as assigned
        mnemonic_obj.is_assigned = True
        if requester:
            mnemonic_obj.assigned_to = requester
        mnemonic_obj.save()

        # Return decrypted mnemonic
        return JsonResponse({
            'ok': True,
            'mnemonic': mnemonic_obj.get_mnemonic(),
            'id': mnemonic_obj.id
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in request_mnemonic_view: {e}")
        return JsonResponse({'ok': False, 'error': '니모닉 요청 처리 중 오류가 발생했습니다'}, status=500)


@csrf_exempt
def generate_mnemonic_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=128)  # 128 bits = 12 words
        return JsonResponse({'ok': True, 'mnemonic': mnemonic})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'failed to generate: {e}'}, status=500)


@csrf_exempt
def save_mnemonic_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        mnemonic = payload.get('mnemonic', '').strip()
        username = payload.get('username', '').strip()[:64]
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    if not mnemonic or not username:
        return JsonResponse({'ok': False, 'error': 'Mnemonic and username required'}, status=400)

    # Validate mnemonic is BIP39-valid (use same logic as validate_mnemonic_view)
    try:
        from .btc import _normalize_mnemonic
        from mnemonic import Mnemonic as MnemonicValidator
        mnorm = _normalize_mnemonic(mnemonic)
        words = [w for w in mnorm.split(' ') if w]
        if len(words) not in (12, 15, 18, 21, 24):
            return JsonResponse({'ok': False, 'error': 'Invalid BIP39 mnemonic (word count)'}, status=400)
        mnemo = MnemonicValidator('english')
        if not mnemo.check(mnorm):
            return JsonResponse({'ok': False, 'error': 'Invalid BIP39 mnemonic (checksum)'}, status=400)
        # Overwrite with normalized mnemonic to keep consistent
        mnemonic = mnorm
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Validation failed: {e}'}, status=400)

    try:
        # Save mnemonic - it will be encrypted automatically by the model
        mnemonic_obj = Mnemonic.objects.create(
            username=username,
            mnemonic=mnemonic,  # This will be encrypted by the model's save method
            is_assigned=False
        )

        return JsonResponse({
            'ok': True,
            'id': mnemonic_obj.id,
            'message': 'Mnemonic saved and encrypted successfully'
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving mnemonic for user {username}: {e}")
        return JsonResponse({'ok': False, 'error': '니모닉 저장 중 오류가 발생했습니다'}, status=500)


@csrf_exempt
def admin_mnemonics_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    # Simple admin check (in real app, use proper authentication)
    username = request.GET.get('username', '')
    if username != 'admin':
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    mnemonics = Mnemonic.objects.all().order_by('-created_at')
    mnemonic_list = [m.as_dict() for m in mnemonics]

    return JsonResponse({
        'ok': True,
        'mnemonics': mnemonic_list
    })


def _parse_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


@csrf_exempt
def mnemonic_balance_view(request):
    """Get balance (in sats) for a mnemonic by id."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    mid = _parse_int(request.GET.get('id'))
    if not mid:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)
    try:
        m = Mnemonic.objects.get(id=mid)
        return JsonResponse({'ok': True, 'id': m.id, 'balance_sats': int(m.balance_sats or 0)})
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)


@csrf_exempt
def admin_set_mnemonic_balance_view(request):
    """Admin endpoint to set balance for a mnemonic in sats."""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    mid = _parse_int(data.get('id'))
    balance_sats = _parse_int(data.get('balance_sats'))
    if not mid or balance_sats is None or balance_sats < 0:
        return JsonResponse({'ok': False, 'error': 'id and non-negative balance_sats required'}, status=400)
    try:
        m = Mnemonic.objects.get(id=mid)
        m.balance_sats = balance_sats
        m.save()
        return JsonResponse({'ok': True, 'mnemonic': m.as_dict()})
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)


@csrf_exempt
def mnemonic_onchain_balance_view(request):
    """
    Calculate on-chain balance for a mnemonic by deriving BIP84 addresses and querying
    a public explorer (Blockstream). Does not reveal the mnemonic over the wire.

    GET params:
      - id: mnemonic id (required)
      - count: number of addresses per chain from index 0 (default 20, max 100)
      - account: BIP84 account index (default 0)
      - include_mempool: '1' to include mempool deltas (default 1)
      - both_chains: '1' to check both external (0) and internal (1) chains (default 1)
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)
    try:
        mid = int(request.GET.get('id', '0'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)

    try:
        count = max(1, min(int(request.GET.get('count', '20')), 100))
    except Exception:
        count = 20
    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0

    # Check both external and internal chains by default (BIP44 standard)
    both_chains = str(request.GET.get('both_chains', '1')) in ('1', 'true', 'True')
    include_mempool = str(request.GET.get('include_mempool', '1')) in ('1', 'true', 'True')

    try:
        m = Mnemonic.objects.get(id=mid)
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)

    # Decrypt on server only
    try:
        mnemonic_plain = m.get_mnemonic()
    except Exception:
        return JsonResponse({'ok': False, 'error': 'decrypt failed'}, status=500)

    try:
        # Collect addresses from both chains
        all_addresses = []

        # External chain (receiving addresses)
        addresses_external = derive_bip84_addresses(
            mnemonic_plain, account=account, change=0, start=0, count=count
        )
        all_addresses.extend(addresses_external)

        # Internal chain (change addresses) - only if both_chains is True
        if both_chains:
            addresses_internal = derive_bip84_addresses(
                mnemonic_plain, account=account, change=1, start=0, count=count
            )
            all_addresses.extend(addresses_internal)

    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'address derivation failed: {e}'}, status=400)

    try:
        by_addr = fetch_blockstream_balances(all_addresses, include_mempool=include_mempool)
        total = calc_total_sats(by_addr)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Balance fetch failed for mnemonic {mid}: {e}")

        # Provide more specific error messages
        error_msg = str(e)
        if '429' in error_msg or 'rate limit' in error_msg.lower():
            return JsonResponse({
                'ok': False,
                'error': 'API 호출 제한에 도달했습니다. 잠시 후 다시 시도해주세요.',
                'error_type': 'rate_limit'
            }, status=429)
        elif 'timeout' in error_msg.lower():
            return JsonResponse({
                'ok': False,
                'error': 'Blockstream API 요청 시간이 초과되었습니다.',
                'error_type': 'timeout'
            }, status=504)
        elif '502' in error_msg or '503' in error_msg:
            return JsonResponse({
                'ok': False,
                'error': 'Blockstream API 서버가 일시적으로 응답하지 않습니다.',
                'error_type': 'service_unavailable'
            }, status=502)
        else:
            return JsonResponse({
                'ok': False,
                'error': f'블록체인 탐색기 오류: {e}',
                'error_type': 'explorer_error'
            }, status=502)

    return JsonResponse({
        'ok': True,
        'total_sats': total,
        'by_address': by_addr,
        'count': len(all_addresses),
        'external_count': len(addresses_external) if not both_chains else count,
        'internal_count': len(addresses_internal) if both_chains else 0
    })


@csrf_exempt
def admin_delete_mnemonic_view(request):
    """Admin: delete a mnemonic by id."""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'ok': False, 'error': 'POST or DELETE only'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    try:
        mid = int(data.get('id'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)
    deleted, _ = Mnemonic.objects.filter(id=mid).delete()
    return JsonResponse({'ok': True, 'deleted': deleted})


@csrf_exempt
def admin_unassign_mnemonic_view(request):
    """Admin: unassign a mnemonic by id (clear assigned_to and mark as not assigned)."""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    try:
        mid = int(data.get('id'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)
    try:
        m = Mnemonic.objects.get(id=mid)
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)
    m.is_assigned = False
    m.assigned_to = ''
    m.save(update_fields=['is_assigned', 'assigned_to'])
    return JsonResponse({'ok': True, 'mnemonic': m.as_dict()})


@csrf_exempt
def admin_mnemonic_xpub_view(request):
    """Admin: return BIP84 account zpub for a mnemonic id."""
    # Allow access to all users (was admin-only)
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)
    try:
        mid = int(request.GET.get('id', '0'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)
    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0
    try:
        m = Mnemonic.objects.get(id=mid)
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)
    try:
        mnemonic_plain = m.get_mnemonic()
        zpub = derive_bip84_account_zpub(mnemonic_plain, account=account)
        # Also calculate master fingerprint
        try:
            mfp = derive_master_fingerprint(mnemonic_plain)
        except Exception:
            mfp = None
        return JsonResponse({'ok': True, 'zpub': zpub, 'account': account, 'master_fingerprint': mfp})
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating zpub/mfp: {e}")
        return JsonResponse({'ok': False, 'error': 'zpub generation failed'}, status=400)


@csrf_exempt
def admin_mnemonic_address_view(request):
    """Admin: return a BIP84 bech32 receive address for a mnemonic id.
    Optional query params: index (default 0), account (default 0), change (default 0).
    """
    # Allow access to all users (was admin-only)
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    try:
        mid = int(request.GET.get('id', '0'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'id required'}, status=400)

    try:
        index = max(0, int(request.GET.get('index', '0')))
    except Exception:
        index = 0
    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0
    try:
        change = max(0, int(request.GET.get('change', '0')))
    except Exception:
        change = 0

    try:
        m = Mnemonic.objects.get(id=mid)
    except Mnemonic.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)

    try:
        addresses = derive_bip84_addresses(m.get_mnemonic(), account=account, change=change, start=index, count=1)
        if not addresses:
            return JsonResponse({'ok': False, 'error': 'address derivation failed'}, status=500)
        return JsonResponse({'ok': True, 'address': addresses[0], 'index': index, 'account': account, 'change': change})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'address derivation failed: {e}'}, status=400)


@csrf_exempt
def validate_mnemonic_view(request):
    """Validate a BIP39 mnemonic (English) and return a normalized form and details."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        mnemonic = (data.get('mnemonic') or '').strip()
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    mnorm = _normalize_mnemonic(mnemonic)
    words = [w for w in mnorm.split(' ') if w]

    # Initialize mnemonic validator
    mnemo = MnemonicValidator('english')

    # Check for unknown words
    unknown = [w for w in words if w not in mnemo.wordlist]

    if len(words) not in (12, 15, 18, 21, 24):
        return JsonResponse({'ok': False, 'valid': False, 'error': 'invalid_word_count', 'word_count': len(words), 'normalized': mnorm, 'unknown_words': unknown})

    try:
        # Use mnemonic library for validation
        valid = mnemo.check(mnorm)
        resp = {'ok': True, 'valid': bool(valid), 'word_count': len(words), 'normalized': mnorm, 'unknown_words': unknown}

        if not valid and len(unknown) == 0:
            # All words valid but checksum failed
            resp['error'] = 'checksum_failed'
        return JsonResponse(resp)
    except Exception:
        return JsonResponse({'ok': True, 'valid': False, 'word_count': len(words), 'normalized': mnorm, 'unknown_words': unknown})


def is_admin(request):
    """Check if user has admin privileges (supports JSON POST bodies and cookies)."""
    username = ''

    # Try to get username from cookie first
    username = request.COOKIES.get('username', '')

    # If not in cookie, try GET/POST parameters
    if not username:
        if request.method == 'GET':
            username = request.GET.get('username', '')
        else:
            # Try form-encoded first
            username = request.POST.get('username', '')
            # If missing and JSON body is used, parse it
            if not username:
                try:
                    content_type = (request.META.get('CONTENT_TYPE') or '').lower()
                    if 'application/json' in content_type:
                        data = json.loads(request.body.decode('utf-8') or '{}')
                        username = data.get('username', '')
                except Exception:
                    username = ''

    return username == 'admin'


@csrf_exempt
def exchange_rates_view(request):
    """Get all exchange rates"""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    rates = ExchangeRate.objects.all()
    rates_list = [rate.as_dict() for rate in rates]

    return JsonResponse({
        'ok': True,
        'rates': rates_list
    })


@csrf_exempt
def admin_exchange_rates_view(request):
    """Admin endpoint to manage exchange rates"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method == 'GET':
        # Get all exchange rates for admin panel
        rates = ExchangeRate.objects.all()
        rates_list = [rate.as_dict() for rate in rates]
        return JsonResponse({
            'ok': True,
            'rates': rates_list
        })

    elif request.method == 'POST':
        # Update exchange rate
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        exchange = data.get('exchange')
        fee_rate = data.get('fee_rate')
        is_event = data.get('is_event', False)
        description = data.get('description', '')
        event_details = data.get('event_details', '')

        if not exchange or fee_rate is None:
            return JsonResponse({'ok': False, 'error': 'Exchange and fee_rate required'}, status=400)

        try:
            fee_rate = float(fee_rate)
            if fee_rate < 0 or fee_rate > 100:
                return JsonResponse({'ok': False, 'error': 'Fee rate must be between 0 and 100'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'error': 'Invalid fee rate'}, status=400)

        try:
            # Update or create exchange rate
            exchange_rate, created = ExchangeRate.objects.update_or_create(
                exchange=exchange,
                defaults={
                    'fee_rate': fee_rate,
                    'is_event': is_event,
                    'description': description,
                    'event_details': event_details
                }
            )

            return JsonResponse({
                'ok': True,
                'rate': exchange_rate.as_dict(),
                'created': created
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating exchange rate {exchange}: {e}")
            return JsonResponse({'ok': False, 'error': '수수료 업데이트 중 오류가 발생했습니다'}, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def withdrawal_fees_view(request):
    """Get all withdrawal fees"""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    fees = WithdrawalFee.objects.all()
    fees_list = [fee.as_dict() for fee in fees]

    return JsonResponse({
        'ok': True,
        'fees': fees_list
    })


@csrf_exempt
def lightning_services_view(request):
    """Get all lightning services"""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    services = LightningService.objects.all()
    services_list = [service.as_dict() for service in services]

    return JsonResponse({
        'ok': True,
        'services': services_list
    })


@csrf_exempt
def admin_withdrawal_fees_view(request):
    """Admin endpoint to manage withdrawal fees"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method == 'GET':
        # Get all withdrawal fees for admin panel
        fees = WithdrawalFee.objects.all()
        fees_list = [fee.as_dict() for fee in fees]
        return JsonResponse({
            'ok': True,
            'fees': fees_list
        })

    elif request.method == 'POST':
        # Update withdrawal fee
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        exchange = data.get('exchange')
        withdrawal_type = data.get('withdrawal_type')
        fee_btc = data.get('fee_btc')
        description = data.get('description', '')

        if not exchange or not withdrawal_type or fee_btc is None:
            return JsonResponse({'ok': False, 'error': 'Exchange, withdrawal_type, and fee_btc required'}, status=400)

        try:
            fee_btc = float(fee_btc)
            if fee_btc < 0:
                return JsonResponse({'ok': False, 'error': 'Fee must be non-negative'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'error': 'Invalid fee amount'}, status=400)

        try:
            # Update or create withdrawal fee
            withdrawal_fee, created = WithdrawalFee.objects.update_or_create(
                exchange=exchange,
                withdrawal_type=withdrawal_type,
                defaults={
                    'fee_btc': fee_btc,
                    'description': description
                }
            )

            return JsonResponse({
                'ok': True,
                'fee': withdrawal_fee.as_dict(),
                'created': created
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating withdrawal fee {exchange}-{withdrawal_type}: {e}")
            return JsonResponse({'ok': False, 'error': '출금 수수료 업데이트 중 오류가 발생했습니다'}, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_lightning_services_view(request):
    """Admin endpoint to manage lightning services"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method == 'GET':
        # Get all lightning services for admin panel
        services = LightningService.objects.all()
        services_list = [service.as_dict() for service in services]
        return JsonResponse({
            'ok': True,
            'services': services_list
        })

    elif request.method == 'POST':
        # Update lightning service
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        service = data.get('service')
        fee_rate = data.get('fee_rate')
        is_kyc = data.get('is_kyc', False)  # Default to False if not provided
        is_custodial = data.get('is_custodial', True)  # Default to True if not provided
        description = data.get('description', '')

        if not service or fee_rate is None:
            return JsonResponse({'ok': False, 'error': 'Service and fee_rate required'}, status=400)

        try:
            fee_rate = float(fee_rate)
            if fee_rate < 0 or fee_rate > 100:
                return JsonResponse({'ok': False, 'error': 'Fee rate must be between 0 and 100'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'error': 'Invalid fee rate'}, status=400)

        try:
            # Update or create lightning service
            lightning_service, created = LightningService.objects.update_or_create(
                service=service,
                defaults={
                    'fee_rate': fee_rate,
                    'is_kyc': bool(is_kyc),
                    'is_custodial': bool(is_custodial),
                    'description': description
                }
            )

            return JsonResponse({
                'ok': True,
                'service': lightning_service.as_dict(),
                'created': created
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating lightning service {service}: {e}")
            return JsonResponse({'ok': False, 'error': '라이트닝 서비스 업데이트 중 오류가 발생했습니다'}, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


# New routing system views

@csrf_exempt
def admin_service_nodes_view(request):
    """Admin endpoint to manage service nodes. GET is public (read-only)."""
    if request.method == 'GET':
        # Ensure required service nodes exist (idempotent)
        try:
            required = [
                { 'service': 'user',            'display_name': '사용자',        'is_kyc': False, 'is_custodial': False, 'website_url': '', 'node_type': 'user' },
                { 'service': 'upbit_btc',       'display_name': '업비트 BTC',    'is_kyc': True,  'is_custodial': True,  'website_url': 'https://upbit.com',              'node_type': 'exchange' },
                { 'service': 'upbit_usdt',      'display_name': '업비트 USDT',   'is_kyc': True,  'is_custodial': True,  'website_url': 'https://upbit.com',              'node_type': 'exchange' },
                { 'service': 'bithumb_btc',     'display_name': '빗썸 BTC',      'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.bithumb.com',        'node_type': 'exchange' },
                { 'service': 'bithumb_usdt',    'display_name': '빗썸 USDT',     'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.bithumb.com',        'node_type': 'exchange' },
                { 'service': 'binance_usdt',    'display_name': '바이낸스 USDT', 'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.binance.com',        'node_type': 'exchange' },
                { 'service': 'binance_btc',     'display_name': '바이낸스 BTC',  'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.binance.com',        'node_type': 'exchange' },
                { 'service': 'okx_usdt',        'display_name': 'OKX USDT',      'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.okx.com',            'node_type': 'exchange' },
                { 'service': 'okx_btc',         'display_name': 'OKX BTC',       'is_kyc': True,  'is_custodial': True,  'website_url': 'https://www.okx.com',            'node_type': 'exchange' },
                { 'service': 'strike',          'display_name': 'Strike',        'is_kyc': True,  'is_custodial': True,  'website_url': 'https://strike.me',              'node_type': 'service' },
                { 'service': 'coinos',          'display_name': 'Coinos',        'is_kyc': False, 'is_custodial': True,  'website_url': 'https://coinos.io',              'node_type': 'service' },
                { 'service': 'walletofsatoshi', 'display_name': 'Wallet of Satoshi','is_kyc': False,'is_custodial': True,  'website_url': 'https://walletofsatoshi.com', 'node_type': 'service' },
                { 'service': 'boltz',           'display_name': 'Boltz Exchange','is_kyc': False, 'is_custodial': False, 'website_url': 'https://boltz.exchange',        'node_type': 'service' },
                { 'service': 'personal_wallet', 'display_name': '개인지갑',      'is_kyc': False, 'is_custodial': False, 'website_url': '',                               'node_type': 'wallet' },
            ]
            for d in required:
                ServiceNode.objects.get_or_create(
                    service=d['service'],
                    defaults={
                        'display_name': d['display_name'],
                        'node_type': d.get('node_type', 'service'),
                        'is_kyc': d['is_kyc'],
                        'is_custodial': d['is_custodial'],
                        'website_url': d['website_url'],
                        'description': f"{d['display_name']} 서비스",
                        'is_enabled': True,
                    },
                )
            # Remove plain exchange umbrella nodes if they exist
            ServiceNode.objects.filter(service__in=['upbit','bithumb','binance','okx']).delete()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error seeding default service nodes: {e}")

        nodes = ServiceNode.objects.all()
        nodes_list = [node.as_dict() for node in nodes]
        return JsonResponse({'ok': True, 'nodes': nodes_list})

    elif request.method == 'POST':
        if not is_admin(request):
            return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        service = data.get('service')
        display_name = data.get('display_name')
        is_kyc = data.get('is_kyc', False)
        is_custodial = data.get('is_custodial', True)
        is_enabled = data.get('is_enabled', True)
        description = data.get('description', '')
        website_url = data.get('website_url', '')
        node_type = data.get('node_type', 'service')

        if not service or not display_name:
            return JsonResponse({'ok': False, 'error': 'Service and display_name required'}, status=400)

        valid_types = {choice[0] for choice in ServiceNode.NODE_TYPE_CHOICES}
        if node_type not in valid_types:
            node_type = 'service'

        try:
            node, created = ServiceNode.objects.update_or_create(
                service=service,
                defaults={
                    'display_name': display_name,
                    'node_type': node_type,
                    'is_kyc': bool(is_kyc),
                    'is_custodial': bool(is_custodial),
                    'is_enabled': bool(is_enabled),
                    'description': description,
                    'website_url': website_url
                }
            )

            return JsonResponse({
                'ok': True,
                'node': node.as_dict(),
                'created': created
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating service node {service}: {e}")
            return JsonResponse({'ok': False, 'error': '서비스 노드 업데이트 중 오류가 발생했습니다'}, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_routes_view(request):
    """Admin endpoint to manage routes. GET is public (read-only)."""
    if request.method == 'GET':
        # Seed/ensure a richer default graph based on requested reference
        try:
            user = ServiceNode.objects.filter(service='user').first()
            # Only use split nodes; plain umbrella nodes are deprecated
            wos = ServiceNode.objects.filter(service='walletofsatoshi').first()
            coinos = ServiceNode.objects.filter(service='coinos').first()
            boltz = ServiceNode.objects.filter(service='boltz').first()
            personal_wallet = ServiceNode.objects.filter(service='personal_wallet').first()

            if user:
                # Trading edges (deposits and exchange to exchange)
                trading_pairs = []
                # 사용자 → 업비트/빗썸 원화
                # Split nodes
                up_krw = ServiceNode.objects.filter(service='upbit_krw').first()
                up_usdt = ServiceNode.objects.filter(service='upbit_usdt').first()
                up_btc = ServiceNode.objects.filter(service='upbit_btc').first()
                bi_krw = ServiceNode.objects.filter(service='bithumb_krw').first()
                bi_usdt = ServiceNode.objects.filter(service='bithumb_usdt').first()
                bi_btc = ServiceNode.objects.filter(service='bithumb_btc').first()
                bz_usdt = ServiceNode.objects.filter(service='binance_usdt').first()
                bz_btc  = ServiceNode.objects.filter(service='binance_btc').first()
                ok_usdt = ServiceNode.objects.filter(service='okx_usdt').first()
                ok_btc  = ServiceNode.objects.filter(service='okx_btc').first()
                # User deposits to KRW entries
                if up_krw: trading_pairs.append((user, up_krw, '업비트 원화 입금'))
                if bi_krw: trading_pairs.append((user, bi_krw, '빗썸 원화 입금'))
                # Internal exchange conversions
                if up_krw and up_usdt: trading_pairs.append((up_krw, up_usdt, '업비트 원화 → 업비트 USDT'))
                # 업비트/빗썸에서 USDT → BTC 직접 전환은 유효하지 않음 (삭제/차단)
                if bi_krw and bi_usdt: trading_pairs.append((bi_krw, bi_usdt, '빗썸 원화 → 빗썸 USDT'))
                # 거래소 내부 USDT → BTC (바이낸스/OKX) - 수수료 0.1%
                if bz_usdt and bz_btc:
                    Route.objects.update_or_create(
                        source=bz_usdt, destination=bz_btc, route_type='trading',
                        defaults={'fee_rate': 0.1, 'description': '바이낸스 USDT → 바이낸스 BTC', 'is_enabled': True},
                    )
                if ok_usdt and ok_btc:
                    Route.objects.update_or_create(
                        source=ok_usdt, destination=ok_btc, route_type='trading',
                        defaults={'fee_rate': 0.1, 'description': 'OKX USDT → OKX BTC', 'is_enabled': True},
                    )
                # Direct user -> exchange (splits) with trading fees
                special_user_pairs = []
                if up_usdt: special_user_pairs.append((user, up_usdt, 0.01, '사용자 → 업비트 USDT'))
                if up_btc:  special_user_pairs.append((user, up_btc,  0.05, '사용자 → 업비트 BTC'))
                if bi_usdt: special_user_pairs.append((user, bi_usdt, 0.04, '사용자 → 빗썸 USDT'))
                if bi_btc:  special_user_pairs.append((user, bi_btc,  0.04, '사용자 → 빗썸 BTC'))
                for (src, dst, fee_rate, desc) in special_user_pairs:
                    Route.objects.update_or_create(
                        source=src, destination=dst, route_type='trading',
                        defaults={'fee_rate': fee_rate, 'description': desc, 'is_enabled': True},
                    )
                # Cross-exchange USDT 온체인 경로는 생성하지 않음 (업비트 USDT 포함)

                # BTC cross-exchange onchain 0.0002 BTC
                btc_onchain_pairs = []
                if up_btc and bz_btc:
                    btc_onchain_pairs.append((up_btc, bz_btc, '업비트 BTC → 바이낸스 BTC 온체인'))
                if up_btc and ok_btc:
                    btc_onchain_pairs.append((up_btc, ok_btc, '업비트 BTC → OKX BTC 온체인'))
                if bi_btc and bz_btc:
                    btc_onchain_pairs.append((bi_btc, bz_btc, '빗썸 BTC → 바이낸스 BTC 온체인'))
                if bi_btc and ok_btc:
                    btc_onchain_pairs.append((bi_btc, ok_btc, '빗썸 BTC → OKX BTC 온체인'))
                for (src, dst, desc) in btc_onchain_pairs:
                    Route.objects.update_or_create(
                        source=src, destination=dst, route_type='withdrawal_onchain',
                        defaults={'fee_rate': None, 'fee_fixed': 0.0002, 'description': desc, 'is_enabled': True},
                    )
                for (src, dst, desc) in trading_pairs:
                    Route.objects.get_or_create(
                        source=src, destination=dst, route_type='trading',
                        defaults={'fee_rate': 0.0, 'description': desc, 'is_enabled': True},
                    )

                # Lightning withdrawals from exchanges (BTC) to LN services
                # - Binance BTC -> WoS/Strike/Coinos at 0.000001 BTC
                # - OKX BTC -> WoS/Coinos at 0.00001 BTC (unchanged)
                if bz_btc:
                    for dst, name in [(wos, 'Wallet of Satoshi'), (ServiceNode.objects.filter(service='strike').first(), 'Strike'), (coinos, 'Coinos')]:
                        if dst:
                            Route.objects.get_or_create(
                                source=bz_btc, destination=dst, route_type='withdrawal_lightning',
                                defaults={'fee_fixed': 0.000001, 'description': f"바이낸스 BTC → {name} 라이트닝", 'is_enabled': True},
                            )
                if ok_btc:
                    for dst, name in [(wos, 'Wallet of Satoshi'), (coinos, 'Coinos')]:
                        if dst:
                            Route.objects.get_or_create(
                                source=ok_btc, destination=dst, route_type='withdrawal_lightning',
                                defaults={'fee_fixed': 0.00001, 'description': f"OKX BTC → {name} 라이트닝", 'is_enabled': True},
                            )

                # LN services → Boltz (lightning, 0%/0 BTC)
                if boltz:
                    for src in [wos, ServiceNode.objects.filter(service='strike').first(), coinos]:
                        if src:
                            Route.objects.get_or_create(
                                source=src, destination=boltz, route_type='withdrawal_lightning',
                                defaults={'fee_fixed': 0.0, 'fee_rate': 0.0, 'description': f"{src.display_name} → Boltz 라이트닝", 'is_enabled': True},
                            )

                # On-chain direct withdrawals from exchange BTC to personal wallet
                if bz_btc and personal_wallet:
                    Route.objects.get_or_create(
                        source=bz_btc,
                        destination=personal_wallet,
                        route_type='withdrawal_onchain',
                        defaults={'fee_rate': None, 'fee_fixed': 0.00003, 'description': '바이낸스 BTC → 개인지갑 온체인', 'is_enabled': True},
                    )
                if ok_btc and personal_wallet:
                    Route.objects.get_or_create(
                        source=ok_btc,
                        destination=personal_wallet,
                        route_type='withdrawal_onchain',
                        defaults={'fee_rate': None, 'fee_fixed': 0.00001, 'description': 'OKX BTC → 개인지갑 온체인', 'is_enabled': True},
                    )

                # On-chain withdrawals to personal wallet
                for src in [wos, coinos, boltz, binance, okx]:
                    if src and personal_wallet:
                        Route.objects.get_or_create(
                            source=src, destination=personal_wallet, route_type='withdrawal_onchain',
                            defaults={'fee_rate': 0.0, 'description': f"{src.display_name} → 개인지갑", 'is_enabled': True},
                        )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error seeding default routes: {e}")

        # Cleanup invalid routes: user -> (binance|okx) umbrellas
        try:
            Route.objects.filter(source=user, destination__service__in=['binance', 'okx']).delete()
        except Exception:
            pass

        # Cleanup invalid: (binance|okx and their splits) -> boltz (lightning)
        try:
            Route.objects.filter(source__service__in=['binance', 'okx', 'binance_usdt', 'binance_btc', 'okx_usdt', 'okx_btc'], destination__service='boltz', route_type='withdrawal_lightning').delete()
        except Exception:
            pass

        # Remove any routes still referencing umbrella nodes on either side
        try:
            Route.objects.filter(source__service__in=['upbit','bithumb','binance','okx']).delete()
            Route.objects.filter(destination__service__in=['upbit','bithumb','binance','okx']).delete()
        except Exception:
            pass

        # Cleanup invalid: (업비트/빗썸) USDT -> (업비트/빗썸) BTC (어떤 유형이든 제거)
        try:
            Route.objects.filter(source__service__in=['upbit_usdt','bithumb_usdt'], destination__service__in=['upbit_btc','bithumb_btc']).delete()
        except Exception:
            pass

        # Cleanup invalid: 업비트 BTC -> 빗썸 BTC (요청에 따라 제거)
        try:
            Route.objects.filter(source__service='upbit_btc', destination__service='bithumb_btc').delete()
        except Exception:
            pass

        # Cleanup: 빗썸 USDT -> (바이낸스/OKX) USDT 온체인 경로 제거
        try:
            bi_usdt = ServiceNode.objects.filter(service='bithumb_usdt').first()
            bz_usdt = ServiceNode.objects.filter(service='binance_usdt').first()
            ok_usdt = ServiceNode.objects.filter(service='okx_usdt').first()
            for dst in [bz_usdt, ok_usdt]:
                if bi_usdt and dst:
                    Route.objects.filter(
                        source=bi_usdt,
                        destination=dst,
                        route_type='withdrawal_onchain',
                    ).delete()
        except Exception:
            pass

        # Cleanup: 업비트 USDT -> (바이낸스/OKX) USDT 온체인 경로 제거
        try:
            up_usdt = ServiceNode.objects.filter(service='upbit_usdt').first()
            bz_usdt = ServiceNode.objects.filter(service='binance_usdt').first()
            ok_usdt = ServiceNode.objects.filter(service='okx_usdt').first()
            for dst in [bz_usdt, ok_usdt]:
                if up_usdt and dst:
                    Route.objects.filter(
                        source=up_usdt,
                        destination=dst,
                        route_type='withdrawal_onchain',
                    ).delete()
        except Exception:
            pass

        # Note: Keep OKX USDT → OKX BTC trading route (0.1%) as requested

        routes = Route.objects.select_related('source', 'destination').all()
        routes_list = [route.as_dict() for route in routes]
        return JsonResponse({'ok': True, 'routes': routes_list})

    elif request.method == 'POST':
        if not is_admin(request):
            return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        source_id = data.get('source_id')
        destination_id = data.get('destination_id')
        route_type = data.get('route_type')
        fee_rate = data.get('fee_rate')
        fee_fixed = data.get('fee_fixed')
        fee_fixed_currency = (data.get('fee_fixed_currency') or 'BTC').upper()
        is_enabled = data.get('is_enabled', True)
        description = data.get('description', '')
        is_event = data.get('is_event', False)
        event_title = data.get('event_title', '')
        event_description = data.get('event_description', '')
        event_url = data.get('event_url', '')

        valid_fee_currencies = {choice[0] for choice in Route.FEE_CURRENCY_CHOICES}
        if fee_fixed_currency not in valid_fee_currencies:
            fee_fixed_currency = 'BTC'

        if not source_id or not destination_id or not route_type:
            return JsonResponse({'ok': False, 'error': 'Source, destination, and route_type required'}, status=400)

        try:
            source = ServiceNode.objects.get(id=source_id)
            destination = ServiceNode.objects.get(id=destination_id)
        except ServiceNode.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Invalid source or destination'}, status=400)

        # Reject invalid user -> (binance|okx) paths
        if source.service == 'user' and destination.service in ['binance', 'okx']:
            return JsonResponse({'ok': False, 'error': '사용자에서 바로 바이낸스/OKX로 가는 경로는 유효하지 않습니다'}, status=400)

        # Reject invalid (upbit/bithumb) USDT -> (upbit/bithumb) BTC
        if source.service in ['upbit_usdt','bithumb_usdt'] and destination.service in ['upbit_btc','bithumb_btc']:
            return JsonResponse({'ok': False, 'error': 'USDT에서 동일 거래소 BTC로의 직접 전환 경로는 유효하지 않습니다'}, status=400)

        try:
            route, created = Route.objects.update_or_create(
                source=source,
                destination=destination,
                route_type=route_type,
                defaults={
                    'fee_rate': fee_rate if fee_rate is not None else None,
                    'fee_fixed': fee_fixed if fee_fixed is not None else None,
                    'fee_fixed_currency': fee_fixed_currency,
                    'is_enabled': bool(is_enabled),
                    'description': description,
                    'is_event': bool(is_event),
                    'event_title': event_title,
                    'event_description': event_description,
                    'event_url': event_url,
                }
            )

            return JsonResponse({
                'ok': True,
                'route': route.as_dict(),
                'created': created
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating route {source.service} -> {destination.service}: {e}")
            return JsonResponse({'ok': False, 'error': '라우트 업데이트 중 오류가 발생했습니다'}, status=500)

    elif request.method == 'DELETE':
        if not is_admin(request):
            return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
        try:
            data = json.loads(request.body)
            route_id = data.get('id')
            if not route_id:
                return JsonResponse({'ok': False, 'error': 'Route ID required'}, status=400)

            Route.objects.filter(id=route_id).delete()
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


def get_optimal_paths_view(request):
    """Get optimal paths from user to personal wallet"""
    try:
        user = ServiceNode.objects.get(service='user')
        personal_wallet = ServiceNode.objects.get(service='personal_wallet')

        # Allow clients to request more paths; clamp to avoid explosion
        try:
            max_paths = int(request.GET.get('max_paths', '300'))
        except (TypeError, ValueError):
            max_paths = 300
        max_paths = max(1, min(max_paths, 1000))

        paths = find_optimal_paths(user, personal_wallet, max_paths=max_paths)

        return JsonResponse({
            'ok': True,
            'paths': [path_to_dict(path) for path in paths]
        })

    except ServiceNode.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Required service nodes not found'}, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error finding optimal paths: {e}")
        return JsonResponse({'ok': False, 'error': '경로 찾기 중 오류가 발생했습니다'}, status=500)


# Path finding algorithm
def find_optimal_paths(start_node, end_node, max_paths=10):
    """Find optimal paths between two nodes using Dijkstra-like algorithm"""
    from collections import defaultdict, deque
    import heapq

    # Get all enabled routes
    routes = Route.objects.filter(is_enabled=True).select_related('source', 'destination')

    # Build adjacency list
    graph = defaultdict(list)
    for route in routes:
        graph[route.source.id].append(route)

    # Priority queue: (total_cost, tie_breaker, path_routes, current_node_id)
    from itertools import count
    _tie = count()
    pq = [(0.0, next(_tie), [], start_node.id)]
    completed_paths = []
    visited_paths = set()

    while pq and len(completed_paths) < max_paths:
        current_cost, _seq, path_routes, current_node_id = heapq.heappop(pq)

        # Create path signature to avoid duplicates
        path_signature = tuple(route.id for route in path_routes)
        if path_signature in visited_paths:
            continue
        visited_paths.add(path_signature)

        # If we reached the destination
        if current_node_id == end_node.id:
            completed_paths.append({
                'routes': path_routes,
                'total_cost': current_cost,
                'path_signature': path_signature
            })
            continue

        # Explore neighbors
        for route in graph[current_node_id]:
            # Avoid cycles (don't go back to nodes already in path)
            nodes_in_path = {start_node.id} | {r.destination.id for r in path_routes}
            if route.destination.id in nodes_in_path:
                continue

            # Calculate route cost
            route_cost = calculate_route_cost(route)
            new_cost = current_cost + route_cost
            new_path = path_routes + [route]

            heapq.heappush(pq, (new_cost, next(_tie), new_path, route.destination.id))

    return completed_paths


def calculate_route_cost(route):
    """Calculate the cost of a single route"""
    cost = 0.0
    if route.fee_rate:
        cost += float(route.fee_rate)  # Percentage cost
    if route.fee_fixed:
        fixed_amount = float(route.fee_fixed)
        currency = (route.fee_fixed_currency or 'BTC').upper()
        if currency == 'USDT':
            btc_usdt_price = get_cached_btc_usdt_price()
            if btc_usdt_price:
                fixed_amount = fixed_amount / btc_usdt_price
        cost += fixed_amount * 100000000  # Convert BTC to satoshis for comparison
    return cost


def path_to_dict(path):
    """Convert path data to dictionary format"""
    return {
        'routes': [route.as_dict() for route in path['routes']],
        'total_cost': path['total_cost'],
        'path_signature': path['path_signature']
    }


@csrf_exempt
def routing_snapshot_view(request):
    """Save and reset routing graph snapshot (service nodes + routes)."""
    if request.method == 'GET':
        try:
            snap = RoutingSnapshot.objects.filter(name='default').first()
            if not snap:
                return JsonResponse({'ok': True, 'has_snapshot': False})
            return JsonResponse({
                'ok': True,
                'has_snapshot': True,
                'updated_at': snap.updated_at.isoformat(),
                'counts': {
                    'nodes': len(snap.nodes_json or []),
                    'routes': len(snap.routes_json or []),
                }
            })
        except Exception as e:
            return JsonResponse({'ok': False, 'error': f'라우팅 스냅샷을 불러오는 중 오류: {e}'}, status=500)

    if request.method == 'POST':
        if not is_admin(request):
            return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            data = {}
        action = (data.get('action') or '').lower()

        if action == 'save':
            try:
                nodes = list(ServiceNode.objects.all().values(
                    'service', 'display_name', 'node_type', 'is_kyc', 'is_custodial', 'is_enabled', 'description', 'website_url'
                ))
                routes_qs = Route.objects.select_related('source', 'destination').all()
                routes = []
                for r in routes_qs:
                    routes.append({
                        'source': r.source.service,
                        'destination': r.destination.service,
                        'route_type': r.route_type,
                        'fee_rate': float(r.fee_rate) if r.fee_rate is not None else None,
                        'fee_fixed': float(r.fee_fixed) if r.fee_fixed is not None else None,
                        'fee_fixed_currency': r.fee_fixed_currency,
                        'is_enabled': bool(r.is_enabled),
                        'description': r.description or '',
                        'is_event': bool(r.is_event),
                        'event_title': r.event_title or '',
                        'event_description': r.event_description or '',
                        'event_url': r.event_url or '',
                    })
                snap, _ = RoutingSnapshot.objects.update_or_create(
                    name='default',
                    defaults={'nodes_json': nodes, 'routes_json': routes}
                )
                return JsonResponse({'ok': True, 'updated_at': snap.updated_at.isoformat(), 'counts': {'nodes': len(nodes), 'routes': len(routes)}})
            except Exception as e:
                return JsonResponse({'ok': False, 'error': f'스냅샷 저장 중 오류: {e}'}, status=500)

        if action == 'reset':
            try:
                snap = RoutingSnapshot.objects.filter(name='default').first()
                if not snap:
                    return JsonResponse({'ok': False, 'error': '저장된 스냅샷이 없습니다'}, status=400)
                nodes = snap.nodes_json or []
                routes = snap.routes_json or []
                # Clear and restore
                Route.objects.all().delete()
                ServiceNode.objects.all().delete()
                service_to_node = {}
                valid_fee_currencies = {choice[0] for choice in Route.FEE_CURRENCY_CHOICES}
                for n in nodes:
                    node = ServiceNode.objects.create(
                        service=n['service'],
                        display_name=n.get('display_name') or n['service'],
                        node_type=n.get('node_type', 'service'),
                        is_kyc=bool(n.get('is_kyc', False)),
                        is_custodial=bool(n.get('is_custodial', True)),
                        is_enabled=bool(n.get('is_enabled', True)),
                        description=n.get('description', ''),
                        website_url=n.get('website_url', ''),
                    )
                    service_to_node[n['service']] = node
                created = 0
                for r in routes:
                    src = service_to_node.get(r['source'])
                    dst = service_to_node.get(r['destination'])
                    if not src or not dst:
                        continue
                    currency = (r.get('fee_fixed_currency') or 'BTC').upper()
                    if currency not in valid_fee_currencies:
                        currency = 'BTC'
                    Route.objects.create(
                        source=src,
                        destination=dst,
                        route_type=r['route_type'],
                        fee_rate=r.get('fee_rate', None),
                        fee_fixed=r.get('fee_fixed', None),
                        fee_fixed_currency=currency,
                        is_enabled=bool(r.get('is_enabled', True)),
                        description=r.get('description', ''),
                        is_event=bool(r.get('is_event', False)),
                        event_title=r.get('event_title', ''),
                        event_description=r.get('event_description', ''),
                        event_url=r.get('event_url', ''),
                    )
                    created += 1
                return JsonResponse({'ok': True, 'restored_nodes': len(service_to_node), 'restored_routes': created})
            except Exception as e:
                return JsonResponse({'ok': False, 'error': f'스냅샷 초기화 중 오류: {e}'}, status=500)

        return JsonResponse({'ok': False, 'error': 'Invalid action'}, status=400)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


def _ensure_sidebar_schema():
    """Best-effort: add missing columns for SidebarConfig if migrations not applied.
    Avoids 500s when the DB wasn't migrated yet."""
    table = SidebarConfig._meta.db_table
    try:
        with connection.cursor() as cur:
            vendor = connection.vendor
            existing = set()
            if vendor == 'sqlite':
                cur.execute(f"PRAGMA table_info({table})")
                existing = {row[1] for row in cur.fetchall()}
            elif vendor == 'postgresql':
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", [table])
                existing = {r[0] for r in cur.fetchall()}
            else:
                # mysql and others
                cur.execute(f"SHOW COLUMNS FROM {table}")
                existing = {r[0] for r in cur.fetchall()}

            if 'wallet_password_hash' not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN wallet_password_hash varchar(128) DEFAULT ''")
            if 'wallet_password_plain' not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN wallet_password_plain varchar(128) DEFAULT ''")
    except Exception:
        # Silently ignore to avoid breaking
        pass


def sidebar_config_view(request):
    _ensure_sidebar_schema()
    """Get current sidebar configuration"""
    config, _ = SidebarConfig.objects.get_or_create(id=1, defaults={
        'show_mining': True,
        'show_utxo': True,
        'show_wallet': True,
        'show_fee': True
    })
    return JsonResponse({'ok': True, 'config': config.as_dict()})


@csrf_exempt
def admin_update_sidebar_config_view(request):
    _ensure_sidebar_schema()
    """Admin: update sidebar configuration"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    config, _ = SidebarConfig.objects.get_or_create(id=1)

    if 'show_mining' in data:
        config.show_mining = bool(data['show_mining'])
    if 'show_utxo' in data:
        config.show_utxo = bool(data['show_utxo'])
    if 'show_wallet' in data:
        config.show_wallet = bool(data['show_wallet'])
    if 'show_fee' in data:
        config.show_fee = bool(data['show_fee'])

    config.save()
    return JsonResponse({'ok': True, 'config': config.as_dict()})


@csrf_exempt
def admin_finance_logs_view(request):
    """Admin: get finance query logs"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    # Get query parameters
    limit = int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    success_filter = request.GET.get('success')  # 'true', 'false', or None (all)

    # Build query
    query = FinanceQueryLog.objects.all()

    if success_filter == 'true':
        query = query.filter(success=True)
    elif success_filter == 'false':
        query = query.filter(success=False)

    # Get total count before pagination
    total_count = query.count()

    # Apply pagination
    logs = query[offset:offset + limit]

    # Serialize logs
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'user_identifier': log.user_identifier,
            'prompt': log.prompt,
            'quick_requests': log.quick_requests,
            'context_key': log.context_key,
            'success': log.success,
            'error_message': log.error_message,
            'assets_count': log.assets_count,
            'processing_time_ms': log.processing_time_ms,
            'created_at': log.created_at.isoformat(),
        })

    return JsonResponse({
        'ok': True,
        'logs': logs_data,
        'total': total_count,
        'offset': offset,
        'limit': limit,
    })


@csrf_exempt
def admin_finance_stats_view(request):
    """Admin: get finance query statistics"""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    from django.db.models import Count, Avg
    from datetime import datetime, timedelta

    # Get stats
    total_queries = FinanceQueryLog.objects.count()
    successful_queries = FinanceQueryLog.objects.filter(success=True).count()
    failed_queries = FinanceQueryLog.objects.filter(success=False).count()

    # Average processing time for successful queries
    avg_processing_time = FinanceQueryLog.objects.filter(
        success=True,
        processing_time_ms__isnull=False
    ).aggregate(Avg('processing_time_ms'))['processing_time_ms__avg']

    # Queries in the last 24 hours
    last_24h = datetime.now() - timedelta(hours=24)
    queries_24h = FinanceQueryLog.objects.filter(created_at__gte=last_24h).count()

    # Top users by query count
    top_users = list(FinanceQueryLog.objects.values('user_identifier').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    # Most common context keys
    top_contexts = list(FinanceQueryLog.objects.exclude(context_key='').values('context_key').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    return JsonResponse({
        'ok': True,
        'stats': {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'success_rate': round(successful_queries / total_queries * 100, 2) if total_queries > 0 else 0,
            'avg_processing_time_ms': round(avg_processing_time, 2) if avg_processing_time else 0,
            'queries_last_24h': queries_24h,
            'top_users': top_users,
            'top_contexts': top_contexts,
        }
    })


def _load_json_body(request):
    try:
        body = request.body
    except Exception:
        body = b''

    if isinstance(body, (bytes, bytearray)):
        try:
            raw = body.decode('utf-8')
        except UnicodeDecodeError:
            return None
    else:
        raw = body

    if isinstance(raw, str):
        raw = raw.strip()

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _get_client_identifier(request):
    """Get client IP address or identifier from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def _log_finance_query(user_identifier, prompt, quick_requests, context_key, success, error_message='', assets_count=0, processing_time_ms=None):
    """Log finance query to database"""
    try:
        FinanceQueryLog.objects.create(
            user_identifier=user_identifier,
            prompt=prompt,
            quick_requests=quick_requests if isinstance(quick_requests, list) else [],
            context_key=context_key,
            success=success,
            error_message=error_message,
            assets_count=assets_count,
            processing_time_ms=processing_time_ms
        )
    except Exception as e:
        logger.error(f"Failed to log finance query: {e}")


def _safe_float(value, allow_negative=False):
    """
    안전하게 float로 변환합니다.
    allow_negative=False인 경우 음수 값은 None을 반환합니다.
    """
    try:
        result = float(value)
        if not allow_negative and result < 0:
            return None
        return result
    except (TypeError, ValueError):
        return None


def _normalize_korean_stock_code(ticker):
    if not ticker:
        return None
    symbol = ticker.strip()
    if '.' in symbol:
        symbol = symbol.split('.')[0]
    symbol = symbol.replace('-', '').strip()
    digits = ''.join(ch for ch in symbol if ch.isdigit())
    return digits or symbol


def _fetch_pykrx_history(ticker, start_year, end_year):
    if not ticker:
        return []
    if pykrx_stock is None:
        raise RuntimeError('pykrx 패키지가 설치되어 있지 않습니다.')

    stock_code = _normalize_korean_stock_code(ticker)
    if not stock_code:
        raise ValueError('유효한 한국 종목 코드를 찾을 수 없습니다.')

    start_dt = datetime(start_year, 1, 1)
    end_dt = datetime(end_year, 12, 31)
    current_dt = datetime.utcnow()
    if end_dt > current_dt:
        end_dt = current_dt

    start_str = start_dt.strftime('%Y%m%d')
    end_str = end_dt.strftime('%Y%m%d')

    try:
        df = pykrx_stock.get_market_ohlcv_by_date(start_str, end_str, stock_code)
    except Exception as exc:
        logger.warning('[%s] pykrx 데이터 가져오기 실패: %s', stock_code, exc)
        raise

    if df is None or df.empty:
        logger.info('[%s] pykrx 데이터가 비어 있습니다.', stock_code)
        return []

    rows = []
    for index, row in df.iterrows():
        close_price = row.get('종가') or row.get('close') or row.get('Close')
        price = _safe_float(close_price, allow_negative=False)
        if price is None or price <= 0:
            continue
        if hasattr(index, 'to_pydatetime'):
            dt = index.to_pydatetime()
        else:
            index_str = str(index)
            try:
                dt = datetime.strptime(index_str[:10], '%Y-%m-%d')
            except ValueError:
                continue
        if dt < start_dt or dt > end_dt:
            continue
        rows.append((dt, price))

    rows.sort(key=lambda item: item[0])
    logger.info('[%s] pykrx에서 데이터 %d개 가져옴 (%d-%d)', stock_code, len(rows), start_year, end_year)
    return rows


def _detect_safe_assets(prompt, quick_requests):
    texts = [prompt or '']
    texts.extend(quick_requests or [])
    haystack = ' '.join(texts).lower()
    matched = set()
    for alias, key in SAFE_ASSET_ALIASES.items():
        if alias in haystack:
            matched.add(key)
    return matched


def _fetch_yfinance_history(ticker, start_year, end_year):
    """Yahoo Finance를 통해 데이터를 가져옵니다."""
    if not ticker:
        return []
    try:
        start_dt = datetime(start_year, 1, 1)
        end_dt = datetime(end_year, 12, 31)
        current_dt = datetime.utcnow()

        stock = yf.Ticker(ticker)
        df = stock.history(start=start_dt, end=end_dt, interval='1mo')

        if df.empty:
            return []

        rows = []
        for index, row in df.iterrows():
            close_price = row.get('Close')
            if close_price is None or close_price <= 0:
                continue
            # index는 pandas Timestamp 객체
            dt = index.to_pydatetime()
            rows.append((dt, float(close_price)))

        # 현재 연도의 현재 월 데이터가 누락되었을 경우, 일별 데이터로 최신 가격 추가
        if end_year == current_dt.year and rows:
            last_row_dt = rows[-1][0]
            # 마지막 데이터가 현재 월보다 이전이면 최신 데이터 추가
            if last_row_dt.year < current_dt.year or last_row_dt.month < current_dt.month:
                try:
                    # 현재 월의 일별 데이터 가져오기
                    current_month_start = datetime(current_dt.year, current_dt.month, 1)
                    df_daily = stock.history(start=current_month_start, end=current_dt, interval='1d')
                    if not df_daily.empty:
                        # 가장 최근 데이터 추가
                        latest_index = df_daily.index[-1]
                        latest_close = df_daily.iloc[-1]['Close']
                        if latest_close and latest_close > 0:
                            latest_dt = latest_index.to_pydatetime()
                            rows.append((latest_dt, float(latest_close)))
                            logger.info('[%s] 최신 가격 추가: %s (%.2f)', ticker, latest_dt.strftime('%Y-%m-%d'), latest_close)
                except Exception as e:
                    logger.warning('[%s] 최신 가격 가져오기 실패: %s', ticker, e)

        logger.info('Yahoo Finance에서 %s 데이터 %d개 가져옴 (%d-%d)', ticker, len(rows), start_year, end_year)
        return rows
    except Exception as exc:
        logger.warning('Yahoo Finance fetch failed for %s: %s', ticker, exc)
        raise


def _fetch_korean_stock_history(ticker, start_year, end_year):
    """
    pykrx만 사용하여 한국 주식 데이터를 가져옵니다.
    ticker 형식: 005930.KS -> pykrx 코드: 005930
    """
    try:
        stock_code = _normalize_korean_stock_code(ticker)
        if not stock_code:
            raise ValueError('유효한 한국 종목 코드를 찾지 못했습니다.')
        if pykrx_stock is None:
            raise RuntimeError('pykrx 패키지가 설치되어 있지 않습니다.')

        logger.info('[%s] pykrx에서 데이터 가져오기 시도 (code: %s)', ticker, stock_code)
        history = _fetch_pykrx_history(stock_code, start_year, end_year)
        if history:
            logger.info('pykrx에서 %s 데이터 %d개 가져옴 (%d-%d)', ticker, len(history), start_year, end_year)
            return history

        raise RuntimeError(f'pykrx에서 {ticker} 데이터를 찾지 못했습니다.')

    except Exception as exc:
        logger.warning('한국 주식 데이터 fetch 실패 (%s): %s', ticker, exc)
        raise


def _fetch_upbit_btc_krw_history(start_year, end_year):
    """
    Upbit API를 사용하여 BTC/KRW 월별 데이터를 가져옵니다.
    """
    try:
        start_dt = datetime(start_year, 1, 1)
        end_dt = datetime(end_year, 12, 31)
        current_dt = datetime.utcnow()

        # Upbit API: 월봉 데이터 (최대 200개)
        url = 'https://api.upbit.com/v1/candles/months'
        params = {
            'market': 'KRW-BTC',
            'count': 200  # 최대 200개 월봉 (약 16년치)
        }

        logger.info('[비트코인] Upbit에서 KRW-BTC 데이터 가져오기 시도')
        response = requests.get(url, params=params, timeout=15, headers=_HTTP_DEFAULT_HEADERS)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.warning('[비트코인] Upbit에서 데이터를 찾지 못함')
            return []

        rows = []
        for candle in data:
            # Upbit 캔들 데이터 구조
            # candle_date_time_kst: "2024-11-01T00:00:00"
            # trade_price: 종가
            timestamp_str = candle.get('candle_date_time_kst')
            close_price = candle.get('trade_price')

            if not timestamp_str or close_price is None or close_price <= 0:
                continue

            try:
                # Parse timestamp
                dt = datetime.strptime(timestamp_str[:10], '%Y-%m-%d')
            except (ValueError, TypeError):
                continue

            # Filter by year range
            if dt < start_dt or dt > end_dt:
                continue

            rows.append((dt, float(close_price)))

        # Sort by date (Upbit returns newest first)
        rows.sort(key=lambda x: x[0])

        logger.info('Upbit에서 KRW-BTC 데이터 %d개 가져옴 (%d-%d)', len(rows), start_year, end_year)
        return rows

    except Exception as exc:
        logger.warning('Upbit fetch failed for BTC/KRW: %s', exc)
        raise


def _fetch_stooq_history(symbol, start_year, end_year):
    if not symbol:
        return []
    start_dt = datetime(start_year, 1, 1)
    end_dt = datetime(end_year, 12, 31) + timedelta(days=1)
    current_dt = datetime.utcnow()

    # 월별 데이터 가져오기
    params = {'s': symbol.lower(), 'i': 'm'}
    resp = requests.get('https://stooq.com/q/d/l/', params=params, timeout=15, headers=_HTTP_DEFAULT_HEADERS)
    resp.raise_for_status()
    content = resp.text
    rows = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        date_str = row.get('Date') or row.get('date')
        price = row.get('Close') or row.get('close')
        if not date_str or price in (None, '', 'null'):
            continue
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            continue
        if dt < start_dt or dt > end_dt:
            continue
        value = _safe_float(price, allow_negative=False)
        if value is None or value <= 0:
            continue
        rows.append((dt, value))

    # 현재 연도의 현재 월 데이터가 누락되었을 경우, 일별 데이터로 최신 가격 추가
    if end_year == current_dt.year and rows:
        last_row_dt = rows[-1][0]
        # 마지막 데이터가 현재 월보다 이전이면 최신 데이터 추가
        if last_row_dt.year < current_dt.year or last_row_dt.month < current_dt.month:
            try:
                # 일별 데이터 가져오기
                params_daily = {'s': symbol.lower(), 'i': 'd'}
                resp_daily = requests.get('https://stooq.com/q/d/l/', params=params_daily, timeout=15, headers=_HTTP_DEFAULT_HEADERS)
                resp_daily.raise_for_status()
                content_daily = resp_daily.text
                reader_daily = csv.DictReader(io.StringIO(content_daily))
                daily_rows = []
                for row in reader_daily:
                    date_str = row.get('Date') or row.get('date')
                    price = row.get('Close') or row.get('close')
                    if not date_str or price in (None, '', 'null'):
                        continue
                    try:
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        continue
                    # 현재 월의 데이터만
                    if dt.year == current_dt.year and dt.month == current_dt.month:
                        value = _safe_float(price, allow_negative=False)
                        if value is not None and value > 0:
                            daily_rows.append((dt, value))

                # 가장 최근 데이터 추가
                if daily_rows:
                    daily_rows.sort(key=lambda x: x[0])
                    latest_dt, latest_price = daily_rows[-1]
                    rows.append((latest_dt, latest_price))
                    logger.info('[%s] 최신 가격 추가 (Stooq): %s (%.2f)', symbol, latest_dt.strftime('%Y-%m-%d'), latest_price)
            except Exception as e:
                logger.warning('[%s] Stooq 최신 가격 가져오기 실패: %s', symbol, e)

    logger.info('Stooq에서 %s 데이터 %d개 가져옴 (%d-%d)', symbol, len(rows), start_year, end_year)
    return rows


def _guess_stooq_symbol(ticker: str):
    if not ticker:
        return None
    symbol = ticker.strip().lower()
    index_map = {
        '^gspc': 'spx',
        '^dji': 'dji',
        '^ndx': 'ndq',
        '^tnx': 'us10y',
    }
    if symbol in index_map:
        return index_map[symbol]
    if symbol.endswith('.ks') or symbol.endswith('.kq'):
        return symbol.split('.')[0] + '.kr'
    if symbol.endswith('.to'):
        return symbol.replace('.to', '.ca')
    if symbol.endswith('.ax'):
        return symbol.replace('.ax', '.au')
    if symbol.endswith('=f'):
        return symbol.replace('=f', '')
    if '-' in symbol:
        symbol = symbol.replace('-', '_')
    if symbol.isalpha():
        return f"{symbol}.us"
    return symbol


def _normalize_asset_label_text(label):
    if not label:
        return ''
    normalized = re.sub(r'\([^)]*\)', '', str(label))
    return normalized.strip().lower()


_BITCOIN_KEYWORDS = {
    'bitcoin', 'btc', 'btc usd', 'btc-usd', 'btc_usd', 'btc-krw', 'btc krw', 'btcusd', 'btcusdt'
}


def _is_bitcoin_config(cfg):
    asset_id = _normalize_asset_label_text(cfg.get('id'))
    label = _normalize_asset_label_text(cfg.get('label'))
    ticker = _normalize_asset_label_text(cfg.get('ticker'))
    if asset_id in _BITCOIN_KEYWORDS:
        return True
    if label in _BITCOIN_KEYWORDS:
        return True
    if ticker.replace('.', '') in _BITCOIN_KEYWORDS:
        return True
    return False



def _parse_upbit_datetime(value):
    if not value:
        return None
    cleaned = value.replace('Z', '')
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def _fetch_upbit_monthly_history(start_year, end_year):
    url = 'https://api.upbit.com/v1/candles/months'
    cursor = datetime(end_year, 12, 31, 15, 0)
    rows = []
    while True:
        params = {'market': 'KRW-BTC', 'count': 200}
        if cursor:
            params['to'] = cursor.strftime('%Y-%m-%d %H:%M:%S')
        resp = requests.get(url, params=params, timeout=15, headers=_HTTP_DEFAULT_HEADERS)
        resp.raise_for_status()
        data = resp.json() or []
        if not data:
            break
        for candle in data:
            dt = _parse_upbit_datetime(candle.get('candle_date_time_utc') or candle.get('candle_date_time_kst'))
            value = _safe_float(candle.get('trade_price'), allow_negative=False)
            if not dt or value is None or value <= 0:
                continue
            rows.append((dt, value))
        last_dt = _parse_upbit_datetime(data[-1].get('candle_date_time_utc') or data[-1].get('candle_date_time_kst'))
        if not last_dt or last_dt.year <= start_year:
            break
        cursor = last_dt - timedelta(days=1)
        if cursor.year < start_year:
            break
    rows.sort(key=lambda item: item[0])
    logger.info('Upbit에서 BTC KRW 데이터 %d개 가져옴 (%d-%d)', len(rows), start_year, end_year)
    return rows


def _collect_asset_aliases(cfg, requested_id):
    aliases = set()
    for candidate in [cfg.get('id'), requested_id, cfg.get('ticker'), cfg.get('stooq_symbol')]:
        if candidate:
            aliases.add(str(candidate))
    label = cfg.get('label')
    if label:
        aliases.add(str(label))
        normalized_label = _normalize_asset_label_text(label)
        if normalized_label:
            aliases.add(normalized_label)
    for alias in cfg.get('aliases', []):
        aliases.add(alias)
    normalized = set()
    for alias in aliases:
        normalized.add(alias)
        normalized.add(alias.lower())
    return sorted(a for a in normalized if a)


def _build_bitcoin_price_payload(start_year, end_year):
    # Use standard fetcher for USD history (Yahoo -> Stooq)
    usd_source = 'Yahoo Finance'  # default
    try:
        usd_history, usd_source = _fetch_asset_history(SAFE_ASSETS['bitcoin'], start_year, end_year)
    except Exception:
        usd_history = []

    usd_prices = _build_yearly_closing_points(usd_history, start_year, end_year)
    krw_history = _fetch_upbit_monthly_history(start_year, end_year)
    krw_prices = _build_yearly_closing_points(krw_history, start_year, end_year)
    payload = {
        'unit': 'USD',
        'source': usd_source,
        'prices': usd_prices,
    }
    if krw_prices:
        payload['alt_prices'] = {'krw': krw_prices}
        payload['alt_sources'] = {'krw': 'Upbit'}
    return payload


def _clone_asset_config(cfg, fallback_id=None):
    if not cfg:
        return None
    cloned = dict(cfg)
    if fallback_id and not cloned.get('id'):
        cloned['id'] = fallback_id
    return cloned


def _find_known_asset_config(asset_id=None, label=None):
    asset_id = (asset_id or '').strip()
    normalized_id = asset_id.lower()
    normalized_label = _normalize_asset_label_text(label)
    normalized_asset_text = _normalize_asset_label_text(asset_id)

    if normalized_id and normalized_id in SAFE_ASSETS:
        return _clone_asset_config(SAFE_ASSETS[normalized_id], normalized_id)

    alias_candidates = [normalized_id, normalized_asset_text, normalized_label]
    for candidate in alias_candidates:
        if not candidate:
            continue
        alias_key = SAFE_ASSET_ALIASES.get(candidate)
        if alias_key and alias_key in SAFE_ASSETS:
            return _clone_asset_config(SAFE_ASSETS[alias_key], alias_key)

    for key, cfg in SAFE_ASSETS.items():
        ticker = (cfg.get('ticker') or '').strip().lower()
        stooq_symbol = (cfg.get('stooq_symbol') or '').strip().lower()
        label_norm = _normalize_asset_label_text(cfg.get('label'))
        if normalized_id and normalized_id in {ticker, stooq_symbol}:
            return _clone_asset_config(cfg, key)
        if normalized_label and label_norm == normalized_label:
            return _clone_asset_config(cfg, key)

    for configs in PRESET_STOCK_GROUPS.values():
        for cfg in configs:
            cfg_id = (cfg.get('id') or cfg.get('ticker') or '').strip()
            cfg_id_normalized = cfg_id.lower()
            ticker = (cfg.get('ticker') or '').strip().lower()
            stooq_symbol = (cfg.get('stooq_symbol') or '').strip().lower()
            label_norm = _normalize_asset_label_text(cfg.get('label'))
            if normalized_id and normalized_id in {cfg_id_normalized, ticker, stooq_symbol}:
                return _clone_asset_config(cfg, cfg_id or normalized_id)
            if normalized_label and label_norm == normalized_label:
                return _clone_asset_config(cfg, cfg_id or label_norm)

    # Fallback: Check if the asset_id or label looks like a Korean stock ticker (e.g. 005930.KS)
    candidates = [asset_id, label]
    for cand in candidates:
        if not cand:
            continue
        # Normalize candidate
        cand_upper = cand.strip().upper()
        # Check for 6-digit code with optional suffix .KS, .KQ, .KL
        # Regex: Starts with 6 digits, optionally followed by .KS/KQ/KL/KR
        if re.match(r'^\d{6}(\.(KS|KQ|KL|KR))?$', cand_upper):
            # If it's just digits, assume .KS for safety or pass as-is (pykrx usually handles just digits)
            # But providing a suffix helps is_korean_stock detection downstream.
            final_ticker = cand_upper
            if re.match(r'^\d{6}$', cand_upper):
                final_ticker = f"{cand_upper}.KS"
            
            return {
                'id': final_ticker,
                'ticker': final_ticker,
                'label': label or final_ticker,
                'category': '국내 주식',
                'unit': 'KRW',
                'stooq_symbol': f"{final_ticker[:6]}.KR" # Fallback for stooq if needed, though pykrx is preferred
            }

    return None


def _build_yearly_closing_points(history, start_year, end_year):
    if not history:
        return []
    
    current_year = datetime.utcnow().year
    # Allow current year data even if end_year < current_year
    # This ensures we always show the latest available price for the current year (YTD/Current)
    effective_end_year = max(end_year, current_year)
    
    yearly = {}
    for dt, price in history:
        if not dt or price in (None, 0):
            continue
        year = getattr(dt, 'year', None)
        if not isinstance(year, int):
            continue
            
        # We still respect the start_year, but allow up to effective_end_year
        if year < start_year or year > effective_end_year:
            continue
            
        prev = yearly.get(year)
        # Keep the latest date's price for the year
        if not prev or dt > prev[0]:
            yearly[year] = (dt, price)
            
    ordered = []
    for year in sorted(yearly.keys()):
        value = _safe_float(yearly[year][1], allow_negative=False)
        if value is None or value <= 0:
            continue
        ordered.append({'year': year, 'value': round(value, 6)})
    return ordered


def _fetch_yearly_closing_prices(cfg, start_year, end_year):
    if _is_bitcoin_config(cfg):
        return _build_bitcoin_price_payload(start_year, end_year)

    ticker = (cfg.get('ticker') or '').strip()
    stooq_symbol = (cfg.get('stooq_symbol') or '').strip()
    category = cfg.get('category', '')
    unit = (cfg.get('unit') or '').upper()

    is_korean_stock = (
        category == '국내 주식' or
        unit == 'KRW' or
        (ticker and ticker.upper().endswith(('.KS', '.KQ', '.KL')))
    )

    if is_korean_stock:
        if not ticker:
            raise ValueError('국내 주식은 종목 코드가 필요합니다.')
        history = _fetch_korean_stock_history(ticker, start_year, end_year)
        source = 'pykrx'
    else:
        symbol = stooq_symbol or _guess_stooq_symbol(ticker)
        if not symbol:
            raise ValueError('Stooq 심볼을 찾을 수 없습니다.')
        history = _fetch_stooq_history(symbol, start_year, end_year)
        source = 'stooq'

    prices = _build_yearly_closing_points(history, start_year, end_year)
    return {
        'unit': cfg.get('unit') or '',
        'source': source,
        'prices': prices,
    }


def _fetch_m2_money_supply_history(ticker, start_year, end_year):
    """
    M2 통화량 데이터를 가져옵니다.

    - US: FRED API (M2SL)
    - Korea: ECOS API (한국은행 광의통화 M2, 통계코드: 101Y002)
    """
    from datetime import datetime
    import requests

    # Determine data source based on ticker
    if 'US' in ticker.upper():
        return _fetch_us_m2_from_fred(start_year, end_year)
    elif 'KR' in ticker.upper():
        return _fetch_korea_m2_from_ecos(start_year, end_year)
    else:
        logger.warning(f"Unknown M2 ticker: {ticker}")
        return []


def _fetch_us_m2_from_fred(start_year, end_year):
    """FRED API를 통해 미국 M2 데이터를 가져옵니다."""
    from datetime import datetime
    import requests

    label = "US M2"
    series_id = 'M2SL'

    try:
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"

        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': getattr(settings, 'FRED_API_KEY', 'demo'),
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'frequency': 'a',  # Annual frequency
            'aggregation_method': 'eop',  # End of period
        }

        logger.info(f"[{label}] FRED API에서 데이터 가져오기 시도: {series_id}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        observations = data.get('observations', [])

        if not observations:
            logger.warning(f"[{label}] FRED API에서 데이터를 찾지 못함")
            return []

        history = []
        for obs in observations:
            date_str = obs.get('date')
            value_str = obs.get('value')

            if not value_str or value_str == '.':
                continue

            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                value = float(value_str)
                history.append((date, value))
            except (ValueError, TypeError) as e:
                logger.warning(f"[{label}] 데이터 파싱 오류: {e}")
                continue

        logger.info(f"[{label}] FRED API에서 데이터 {len(history)}개 가져옴 ({start_year}-{end_year})")
        return history

    except Exception as exc:
        logger.error(f"[{label}] FRED API 요청 실패: {exc}")
        raise RuntimeError(f"FRED API에서 {label} 데이터를 가져오는데 실패했습니다.")


def _fetch_korea_m2_from_ecos(start_year, end_year):
    """ECOS API를 통해 한국 M2 데이터를 가져옵니다."""
    from datetime import datetime
    import requests

    label = "Korean M2"
    api_key = getattr(settings, 'ECOS_API_KEY', '')

    if not api_key:
        logger.error(f"[{label}] ECOS_API_KEY가 설정되지 않음")
        raise RuntimeError("ECOS_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    try:
        # ECOS API 통계표: 101Y001 (M2 말잔, 계절조정계열)
        # 데이터가 많아서 페이징 필요 - 연도별로 나눠서 요청
        all_rows = []

        # 연도별로 요청하여 페이징 문제 회피
        for year in range(start_year, end_year + 1):
            year_start = f"{year}01"
            year_end = f"{year}12"

            url = (
                f"https://ecos.bok.or.kr/api/StatisticSearch/"
                f"{api_key}/json/kr/1/100/101Y001/M/{year_start}/{year_end}"
            )

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'StatisticSearch' in data:
                rows = data['StatisticSearch'].get('row', [])
                all_rows.extend(rows)

        if not all_rows:
            logger.warning(f"[{label}] ECOS API에서 데이터를 찾지 못함")
            return []

        # M2 총액 데이터만 필터링 (ITEM_NAME1이 "M2(말잔, 계절조정계열)"인 것)
        # 각 연도의 마지막 사용 가능한 월 데이터 추출
        m2_data_by_year = {}
        for row in all_rows:
            time_str = row.get('TIME')  # YYYYMM 형식
            value_str = row.get('DATA_VALUE')
            item_name = row.get('ITEM_NAME1', '')

            if not time_str or not value_str:
                continue

            # M2 총액만 선택 (다른 항목 제외)
            if not item_name.startswith('M2('):
                continue

            try:
                year = int(time_str[:4])
                month = int(time_str[4:6])
                value = float(value_str)

                # 각 연도의 최신 월 데이터 저장
                if year not in m2_data_by_year or month > m2_data_by_year[year]['month']:
                    m2_data_by_year[year] = {
                        'month': month,
                        'value': value
                    }
            except (ValueError, TypeError) as e:
                logger.warning(f"[{label}] 데이터 파싱 오류: {e}")
                continue

        # 연도별 데이터를 히스토리로 변환
        history = []
        for year in sorted(m2_data_by_year.keys()):
            data = m2_data_by_year[year]
            month = data['month']
            value = data['value']
            # 해당 월의 마지막 날로 설정
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            date = datetime(year, month, last_day)
            history.append((date, value))

        logger.info(f"[{label}] ECOS API에서 데이터 {len(history)}개 가져옴 ({start_year}-{end_year})")
        return history

    except Exception as exc:
        logger.error(f"[{label}] ECOS API 요청 실패: {exc}")
        raise RuntimeError(f"ECOS API에서 {label} 데이터를 가져오는데 실패했습니다.")


def _fetch_asset_history(cfg, start_year, end_year):
    """
    여러 데이터 소스를 순서대로 시도하여 자산 가격 이력을 가져옵니다.

    Returns:
        tuple: (history, source) where source is the name of the data provider

    비트코인:
      - prefer_krw 플래그가 True면 Upbit (KRW) 사용
      - 그 외에는 Yahoo Finance (USD) 사용

    한국 주식(.KS, .KQ):
      - pykrx에서만 데이터를 가져옴

    경제 지표 (M2 등):
      - ECOS (한국) 또는 FRED (미국)

    기타 자산:
      - 우선순위: Yahoo Finance > Stooq
    """
    errors = []
    label = cfg.get('label', 'Unknown')
    ticker = cfg.get('ticker')
    stooq_symbol = cfg.get('stooq_symbol') or _guess_stooq_symbol(ticker)
    category = cfg.get('category', '')
    prefer_krw = cfg.get('prefer_krw', False)  # 한국 원화 시세 우선 사용 여부

    # 비트코인 여부 확인 (id가 'bitcoin'이거나 ticker가 'BTC'로 시작)
    is_bitcoin = (
        cfg.get('id') == 'bitcoin' or
        (ticker and ticker.upper().startswith('BTC'))
    )

    # 비트코인이고 prefer_krw가 True면 Upbit 사용
    if is_bitcoin and prefer_krw:
        try:
            history = _fetch_upbit_btc_krw_history(start_year, end_year)
            if history:
                return history, 'Upbit'
            errors.append('Upbit: 데이터 없음')
        except Exception as exc:
            errors.append(f'Upbit: {exc}')
            logger.warning('[%s] Upbit 가져오기 실패, Yahoo Finance로 폴백: %s', label, exc)

    # M2 통화량 지표 여부 확인
    is_m2_indicator = ticker and ('M2-' in ticker.upper() or ticker.upper().startswith('M2'))
    if is_m2_indicator:
        try:
            history = _fetch_m2_money_supply_history(ticker, start_year, end_year)
            if history:
                # Determine source based on ticker
                source = 'ECOS' if 'KR' in ticker.upper() else 'FRED'
                return history, source
            errors.append('M2 데이터: 데이터 없음')
        except Exception as exc:
            errors.append(f'M2 데이터: {exc}')
            logger.error('[%s] M2 데이터 가져오기 실패: %s', label, exc)

    # 한국 주식 여부 확인
    is_korean_stock = (
        category == '국내 주식' or
        (ticker and (ticker.endswith('.KS') or ticker.endswith('.KQ') or ticker.endswith('.KL')))
    )

    # 한국 주식은 pykrx만 사용
    if is_korean_stock and ticker:
        logger.info('[%s] 한국 주식 감지 (Category: %s, Ticker: %s) → pykrx 사용', label, category, ticker)
        try:
            history = _fetch_korean_stock_history(ticker, start_year, end_year)
            if history:
                logger.info('[%s] pykrx에서 데이터 가져오기 성공: %d개', label, len(history))
                return history, 'pykrx'
            errors.append('pykrx: 데이터 없음')
            logger.warning('[%s] pykrx에서 데이터를 찾지 못함', label)
        except Exception as exc:
            errors.append(f'pykrx: {exc}')
            logger.error('[%s] pykrx 실패: %s', label, exc)
        error_msg = '; '.join(errors) if errors else 'pykrx 데이터를 가져올 수 없습니다.'
        logger.error('[%s] 한국 주식 데이터 가져오기 실패: %s', label, error_msg)
        raise RuntimeError(error_msg)

    # 1. Yahoo Finance 시도
    if ticker and not is_korean_stock:
        try:
            logger.info('[%s] Yahoo Finance에서 데이터 가져오기 시도: %s', label, ticker)
            history = _fetch_yfinance_history(ticker, start_year, end_year)
            if history:
                logger.info('[%s] Yahoo Finance에서 데이터 가져오기 성공: %d개', label, len(history))
                return history, 'Yahoo Finance'
            else:
                errors.append('Yahoo Finance: 데이터 없음')
                logger.warning('[%s] Yahoo Finance에서 데이터를 찾지 못함', label)
        except Exception as exc:
            errors.append(f'Yahoo Finance: {exc}')
            logger.warning('[%s] Yahoo Finance 실패: %s', label, exc)

    # 2. Stooq 시도 (한국 주식 제외)
    if stooq_symbol:
        try:
            logger.info('[%s] Stooq에서 데이터 가져오기 시도: %s', label, stooq_symbol)
            history = _fetch_stooq_history(stooq_symbol, start_year, end_year)
            if history:
                logger.info('[%s] Stooq에서 데이터 가져오기 성공: %d개', label, len(history))
                return history, 'Stooq'
            else:
                errors.append('Stooq: 데이터 없음')
                logger.warning('[%s] Stooq에서 데이터를 찾지 못함', label)
        except Exception as exc:
            errors.append(f'Stooq: {exc}')
            logger.warning('[%s] Stooq 실패: %s', label, exc)

    # 모든 소스 실패
    error_msg = '; '.join(errors) if errors else '지원되는 시세 제공처가 없습니다.'
    logger.error('[%s] 모든 데이터 소스에서 가져오기 실패: %s', label, error_msg)
    raise RuntimeError(error_msg)


def _build_asset_series(asset_key, cfg, history, start_year, end_year, calculation_method='cagr'):
    """
    Build asset series for charting.

    Args:
        calculation_method: 'cagr' (연평균 상승률) or 'cumulative' (누적 상승률)
    """
    if not history:
        return None

    current_year = datetime.utcnow().year
    # Allow current year data even if end_year < current_year
    # This ensures we render the chart up to the latest available point
    effective_end_year = max(end_year, current_year)

    yearly_prices = {}
    for dt, value in history:
        year = dt.year
        # Use effective_end_year to include current year data
        if year < start_year or year > effective_end_year:
            continue
        prev = yearly_prices.get(year)
        if not prev or dt > prev[0]:
            yearly_prices[year] = (dt, value)
    if len(yearly_prices) < 2:
        return None
    ordered_years = sorted(yearly_prices.keys())
    base_year = ordered_years[0]
    is_yield_asset = bool(cfg.get('yield_asset'))
    adjusted_series = []
    pseudo_price = 1.0

    # KRW 주식의 경우 스케일 팩터 적용 여부 결정
    unit = (cfg.get('unit') or '').upper()
    category = cfg.get('category', '')
    ticker = cfg.get('ticker', '')
    is_krw_asset = unit == 'KRW' or category == '국내 주식'
    scale_factor = 1.0

    # 데이터 소스 판별을 위한 플래그
    # Stooq는 원화 그대로 제공
    # Yahoo Finance는 100원 단위로 제공
    if is_krw_asset and history:
        is_korean_stock = (
            ticker.endswith('.KS') or
            ticker.endswith('.KQ') or
            ticker.endswith('.KL') or
            category == '국내 주식'
        )

        if is_korean_stock:
            sample_prices = [v for _, v in history if v and v > 0]
            if sample_prices:
                recent_prices = sample_prices[-min(3, len(sample_prices)):]
                avg_price = sum(recent_prices) / len(recent_prices)

                # 가격 범위로 데이터 소스 판별
                # Stooq: 10,000원 이상 (원화 그대로)
                # Yahoo Finance: 1,000원 미만 (100원 단위)
                if avg_price < 10000:
                    # Yahoo Finance 데이터로 추정 - 100배 스케일 필요
                    scale_factor = 100.0
                    logger.info('[%s] 한국 주식 스케일 팩터 100x 적용 (Yahoo Finance: %.2f → %.2f원)',
                               cfg.get('label', 'Unknown'), avg_price, avg_price * scale_factor)
                else:
                    # Stooq 데이터로 추정 - 스케일 불필요
                    scale_factor = 1.0
                    logger.info('[%s] 한국 주식 스케일 팩터 적용 안함 (Stooq: %.2f원)',
                               cfg.get('label', 'Unknown'), avg_price)

    for index, year in enumerate(ordered_years):
        price = yearly_prices[year][1]
        if price is None:
            continue

        if is_yield_asset:
            rate_pct = _safe_float(price, allow_negative=True)  # 수익률은 음수 가능
            if rate_pct is None:
                continue
            if index == 0:
                pseudo_price = 1.0
            else:
                rate_decimal = max(rate_pct / 100.0, 0.0)
                pseudo_price *= (1 + rate_decimal)
            adjusted_value = pseudo_price
            adjusted_series.append((year, adjusted_value))
        else:
            price_val = _safe_float(price, allow_negative=False)  # 가격은 음수 불가
            if price_val is None or price_val <= 0:
                logger.warning('[%s] 유효하지 않은 가격 데이터 발견 (연도: %d, 가격: %s)',
                             cfg.get('label', 'Unknown'), year, price)
                continue
            # 스케일 팩터 적용
            adjusted_value = price_val * scale_factor
            if adjusted_value <= 0:
                logger.warning('[%s] 스케일 팩터 적용 후 유효하지 않은 가격 (연도: %d, 가격: %.2f)',
                               cfg.get('label', 'Unknown'), year, adjusted_value)
                continue

            adjusted_series.append((year, adjusted_value))

    if len(adjusted_series) < 2:
        return None

    base_value = adjusted_series[0][1]
    if not base_value or base_value <= 0:
        return None

    points = []
    for idx, (year, adjusted_value) in enumerate(adjusted_series):
        multiple = adjusted_value / base_value

        if calculation_method == 'price':
            # 실제 가격 표시 (Price mode shows actual prices)
            return_pct = adjusted_value
        elif calculation_method == 'cumulative':
            # 누적 상승률: (현재값 / 시작값 - 1) * 100
            return_pct = (multiple - 1) * 100
        elif calculation_method == 'yearly_growth':
            # 전년 대비 증감률 (YoY)
            if idx == 0:
                return_pct = 0.0
            else:
                prev_val = adjusted_series[idx-1][1]
                if prev_val > 0:
                    return_pct = (adjusted_value - prev_val) / prev_val * 100
                else:
                    return_pct = 0.0
        else:
            # CAGR: 연평균 상승률
            if year == base_year:
                return_pct = 0.0
            else:
                years_elapsed = year - base_year
                if years_elapsed <= 0:
                    return_pct = 0.0
                else:
                    try:
                        return_pct = ((adjusted_value / base_value) ** (1 / years_elapsed) - 1) * 100
                    except Exception:
                        return_pct = 0.0

        points.append({
            'year': year,
            'value': round(return_pct, 3),
            'multiple': round(multiple, 6)
        })

    if len(points) < 2:
        return None

    start_val = points[0]['multiple'] or 1.0
    end_val = points[-1]['multiple'] or start_val
    years_total = points[-1]['year'] - points[0]['year']

    # Calculate final return metric for legend/sorting
    if calculation_method == 'price':
        # 가격 모드: 누적 상승률을 정렬용 메트릭으로 사용
        final_return_pct = (end_val / start_val - 1) * 100 if start_val else 0.0
    elif calculation_method == 'cumulative':
        # 누적 상승률
        final_return_pct = (end_val / start_val - 1) * 100 if start_val else 0.0
    elif calculation_method == 'yearly_growth':
        # 증감률의 경우 마지막 해 증감률 또는 평균 증감률을 사용? 
        # 여기서는 '마지막 해 증감률'을 표시하거나, 전체 기간 단순 평균을 표시
        # 단순 평균으로 결정
        growth_sum = sum(p['value'] for p in points[1:]) # 첫해 제외
        count = len(points) - 1
        final_return_pct = growth_sum / count if count > 0 else 0.0
    else:
        # CAGR
        if years_total > 0 and start_val > 0:
            final_return_pct = ((end_val / start_val) ** (1 / years_total) - 1) * 100
        else:
            final_return_pct = 0.0

    return {
        'id': cfg.get('id') or asset_key,
        'label': cfg['label'],
        'category': cfg.get('category', '안전자산'),
        'unit': cfg.get('unit', ''),
        'points': points,
        'annualized_return_pct': round(final_return_pct, 2),  # Used for sorting
        'multiple_from_start': round(end_val / start_val, 3) if start_val else 0.0,
        'calculation_method': calculation_method,
    }


def _fetch_safe_asset_series(asset_keys, start_year, end_year):
    results = []
    errors = []
    for key in asset_keys:
        cfg = SAFE_ASSETS.get(key)
        if not cfg:
            continue
        try:
            history = _fetch_asset_history(cfg, start_year, end_year)
            series = _build_asset_series(key, cfg, history, start_year, end_year)
            if series:
                results.append(series)
            else:
                errors.append(f"{cfg.get('label')} 데이터가 부족합니다.")
        except Exception as exc:
            logger.warning('Failed to fetch safe asset %s: %s', key, exc)
            errors.append(f"{cfg.get('label')} 오류: {exc}")
    return results, errors


def _fetch_preset_group(group_name, start_year, end_year):
    configs = PRESET_STOCK_GROUPS.get(group_name) or []
    results = []
    errors = []
    for cfg in configs[:FINANCE_MAX_SERIES]:
        try:
            history = _fetch_asset_history(cfg, start_year, end_year)
            series = _build_asset_series(cfg.get('id'), cfg, history, start_year, end_year)
            if series:
                results.append(series)
            else:
                errors.append(f"{cfg.get('label')} 데이터가 부족합니다.")
        except Exception as exc:
            logger.warning('Failed to fetch preset asset %s: %s', cfg.get('label'), exc)
            errors.append(f"{cfg.get('label')} 오류: {exc}")
    return results, errors


def _extract_start_year_from_prompt(prompt):
    if not prompt:
        return None
    years = []
    for match in re.findall(r'(?:19|20)\d{2}', prompt):
        try:
            year = int(match)
        except ValueError:
            continue
        if 1900 <= year <= 2100:
            years.append(year)
    return min(years) if years else None


def _extract_year_span_from_prompt(prompt):
    if not prompt:
        return None
    lowered = prompt.lower()
    match = re.search(r'지난\s*(\d{1,3})\s*년', lowered)
    if not match:
        match = re.search(r'(\d{1,3})\s*년\s*(?:간|동안)', lowered)
    if not match:
        # "10년 연평균", "10년 수익률" etc.
        match = re.search(r'(\d{1,3})\s*년\s+(?:연평균|수익률|상승률|전년|증감)', lowered)
    if match:
        try:
            span = int(match.group(1))
        except ValueError:
            span = None
        if span and 2 <= span <= 50:
            return span
    return None


def _derive_finance_year_window(year_hint, span_hint=None):
    current_year = datetime.utcnow().year
    min_year = 2010
    if span_hint and span_hint >= 2:
        end_year = current_year
        # Calculate start year: e.g., 2025 - 10 = 2015 (Range: 2015-2025)
        start_year = max(min_year, end_year - span_hint)
    else:
        base_year = year_hint or FINANCE_DEFAULT_START_YEAR
        start_year = max(min_year, base_year)
        if start_year > current_year:
            start_year = max(min_year, current_year - FINANCE_YEAR_SPAN + 1)
        end_year = min(start_year + FINANCE_YEAR_SPAN - 1, current_year)
        if end_year - start_year < 1:
            start_year = max(min_year, end_year - FINANCE_YEAR_SPAN + 1)
    return start_year, end_year
        


def _get_agent_prompt(agent_type, default_prompt=''):
    """
    Get agent prompt from database or return default
    """
    from .models import AgentPrompt
    try:
        agent = AgentPrompt.objects.get(agent_type=agent_type, is_active=True)
        return agent.system_prompt
    except AgentPrompt.DoesNotExist:
        return default_prompt


def _check_prompt_intent(prompt):
    """
    LLM을 사용하여 프롬프트의 의도를 분류하고 허용 여부를 판단
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OpenAI API 키가 설정되지 않았습니다.')
    base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

    # Get guardrail prompt from DB
    guardrail_system_prompt = _get_agent_prompt('guardrail',
        "당신은 사용자 요청의 의도를 분류하는 전문가입니다.\n\n"
        "주어진 사용자 요청이 다음 중 어디에 해당하는지 판단하세요:\n\n"
        "1. **금융 분석 요청** (allowed=true): 자산의 과거 데이터 분석을 원하는 경우\n"
        "   - 과거 수익률, 가격 변동, 비교 분석 (예: '비트코인 수익률', '삼성전자 주가')\n"
        "   - 연도별/연말 가격 조회 (예: '연말 가격을 알려줘', '2020년부터 2024년까지 가격')\n"
        "   - 가격 비교 (예: '비트코인과 금 비교', '미국 빅테크 기업들의 가격')\n"
        "   - **과거 가정 투자 분석** (예: '10년 전에 100만원을 투자했다면', 'X년 전에 투자했으면 지금 얼마일까')\n"
        "   - **중요**: '연말 가격', '연도별 가격', '과거 투자 수익'은 과거 데이터 요청이므로 allowed=true\n\n"
        "2. **부적절한 요청** (allowed=false): 다음과 같은 경우만 거부\n"
        "   - 금융 분석과 완전히 무관한 요청 (예: '날씨 알려줘', '게임 추천')\n"
        "   - 개인정보 요구 (예: '사용자 비밀번호', '계좌번호')\n"
        "   - 시스템 악용 시도\n"
        "   - **실제 미래 예측 요청** (예: '내일 비트코인 가격 예측', '2025년 주가 전망', '다음 달 어떻게 될까')\n\n"
        "**주의사항**:\n"
        "- '투자했다면', '넣었으면', 'X년 후'라는 표현이 있어도, 과거 특정 시점을 기준으로 한다면 과거 분석입니다.\n"
        "- 예: '10년 전에 투자했다면 지금은?' -> 과거 데이터 분석 (allowed=true)\n"
        "- 예: '지금 투자하면 10년 후에는?' -> 미래 예측 (allowed=false)\n\n"
        "응답 형식 (JSON만 반환):\n"
        "{\n"
        '  "allowed": true 또는 false,\n'
        '  "reason": "거부 사유 (allowed가 false일 때만)"\n'
        "}\n\n"
    )

    guardrail_prompt = f'사용자 요청: "{prompt}"'

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [
                    {"role": "system", "content": guardrail_system_prompt},
                    {"role": "user", "content": guardrail_prompt}
                ],
                'temperature': 0.1,
                'response_format': {
                    'type': 'json_object'
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get('choices') or []
        if not choices or 'message' not in choices[0]:
            logger.warning('Guardrail check failed, allowing request by default')
            return True, '의도 분류 실패'

        content = choices[0]['message'].get('content')
        if not content:
            return True, '의도 분류 실패'

        result = json.loads(content)
        allowed = result.get('allowed', True)
        reason = result.get('reason', '')

        return allowed, reason

    except Exception as exc:
        logger.warning(f'Guardrail check error: {exc}, allowing request by default')
        return True, '의도 분류 오류'








def _generate_cache_key(context_key, start_year, end_year):
    """Generate cache key for a query"""
    import hashlib
    key_str = f"{context_key}:{start_year}:{end_year}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_cached_finance_data(context_key, start_year, end_year):
    """Get cached finance data if available and not expired"""
    from datetime import datetime, timezone
    from .models import FinanceQueryCache

    if not context_key:
        return None

    cache_key = _generate_cache_key(context_key, start_year, end_year)

    try:
        cache_entry = FinanceQueryCache.objects.get(
            query_key=cache_key,
            expires_at__gt=datetime.now(timezone.utc)
        )
        cache_entry.increment_hit()
        logger.info(f"Cache hit for {context_key} ({start_year}-{end_year}), hit_count={cache_entry.hit_count}")
        return cache_entry.as_dict()
    except FinanceQueryCache.DoesNotExist:
        return None


def _save_to_cache(context_key, start_year, end_year, series_data, fx_rate):
    """Save finance data to cache"""
    from datetime import datetime, timedelta, timezone
    from .models import FinanceQueryCache

    if not context_key:
        return

    cache_key = _generate_cache_key(context_key, start_year, end_year)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # 24시간 캐시

    try:
        FinanceQueryCache.objects.update_or_create(
            query_key=cache_key,
            defaults={
                'context_key': context_key,
                'start_year': start_year,
                'end_year': end_year,
                'series_data': series_data,
                'fx_rate': fx_rate,
                'expires_at': expires_at,
            }
        )
        logger.info(f"Saved to cache: {context_key} ({start_year}-{end_year})")
    except Exception as exc:
        logger.error(f"Failed to save cache: {exc}")


def _purge_finance_cache(context_key):
    """Delete cached finance data for a specific context key."""
    if not context_key:
        return
    from .models import FinanceQueryCache
    try:
        deleted, _ = FinanceQueryCache.objects.filter(context_key=context_key).delete()
        if deleted:
            logger.info(f"Purged {deleted} cache entries for context {context_key}")
    except Exception as exc:
        logger.error(f"Failed to purge cache for {context_key}: {exc}")


def _ensure_finance_cache_purged(context_key):
    if not context_key:
        return
    version = FINANCE_CACHE_PURGE_VERSIONS.get(context_key)
    if not version:
        return
    if _purged_finance_contexts.get(context_key) == version:
        return
    _purge_finance_cache(context_key)
    _purged_finance_contexts[context_key] = version


# --- Agent Classes ---

class IntentClassifierAgent:
    """
    Responsible for understanding the user's request, checking guardrails,
    and extracting a list of assets to analyze.
    """
    def run(self, prompt, quick_requests):
        logs = []
        logs.append("[의도 분석] 사용자 요청 분석 중...")

        # Combine prompt and quick requests
        # If no explicit time period mentioned, add "지난 10년" context
        combined_prompt = f"{prompt} {' '.join(quick_requests)}" if quick_requests else prompt
        if not combined_prompt.strip():
            combined_prompt = "비트코인과 대표 자산의 과거 연평균 상승률을 비교해줘."

        # Add default time period if not mentioned
        time_keywords = ['년', '기간', '동안', '지난', '최근', '10년', '5년', '20년', 'year']
        has_time_period = any(keyword in combined_prompt.lower() for keyword in time_keywords)

        if not has_time_period:
            combined_prompt = f"{combined_prompt} (지난 10년간의 데이터)"
            logs.append("[의도 분석] 기본 기간 설정: 지난 10년")

        # 1. Guardrail Check
        try:
            allowed, reason = _check_prompt_intent(combined_prompt)
            if not allowed:
                logs.append(f"[의도 분석] 요청 차단됨. 사유: {reason}")
                return {'allowed': False, 'error': '요청이 거부되었습니다. ' + reason}, logs
            logs.append("[의도 분석] 보안 검사 통과")
        except Exception as e:
            logs.append(f"[의도 분석] 보안 검사 실패 ({e}). 계속 진행합니다.")

        # 2. Hybrid Step 1: Keyword-based Pre-classification
        prompt_lower = combined_prompt.lower()
        keyword_method = None

        # Check for specific keywords
        # PRIORITY 1: Explicit CAGR requests (highest priority for annualized returns)
        if any(k in prompt_lower for k in ['연평균', 'cagr', 'annualized', '평균 수익률', '평균 상승률']):
            keyword_method = 'cagr'
            logs.append("[의도 분석] 키워드 감지: '연평균 상승률(CAGR)' 분석 요청")

        # PRIORITY 2: Year-over-Year Growth
        elif not keyword_method and any(k in prompt_lower for k in ['증감률', 'growth', 'change', 'yoy', '전년', '성장률', '변동률']):
            keyword_method = 'yearly_growth'
            logs.append("[의도 분석] 키워드 감지: '증감률(YoY)' 분석 요청")

        # PRIORITY 3: Cumulative Returns
        elif not keyword_method and any(k in prompt_lower for k in ['누적', 'cumulative', 'total return', '총 수익률']):
            keyword_method = 'cumulative'
            logs.append("[의도 분석] 키워드 감지: '누적 수익률' 분석 요청")

        # PRIORITY 4: Investment/Return questions (need price data to calculate returns)
        elif not keyword_method and any(k in prompt_lower for k in ['투자했다면', '투자', 'investment', '얼마', 'how much', '만원', '후']):
            keyword_method = 'price'
            logs.append("[의도 분석] 키워드 감지: '투자 수익 계산(Price 데이터 필요)' 분석 요청")

        # PRIORITY 5: Explicit Price Requests
        elif not keyword_method and any(k in prompt_lower for k in ['가격', '종가', 'price', 'value', 'year-end', '연말', '시세']):
            keyword_method = 'price'
            logs.append("[의도 분석] 키워드 감지: '가격(Price)' 분석 요청")

        # 3. Call LLM (Asset Extraction + Fallback Method)
        system_prompt = _get_agent_prompt('intent_classifier',
            "You are a financial intent classifier. Your goal is to extract the user's intent and target assets.\n\n"
            "**IMPORTANT CONTEXT**: Unless otherwise specified, all analysis requests are for historical data from the past 10 years (지난 10년간의 데이터). "
            "This is the default time period for all financial comparisons and analysis.\n\n"
            "**STEP 1: Determine Calculation Method**\n"
            "Check for keywords in the user's request in this order:\n\n"
            "**PRIORITY 1: Investment Return Questions (ALWAYS 'price')**\n"
            "IF the prompt asks about investment returns or final values (e.g., '100만원을 투자했다면', 'if I invested X', '투자 수익', 'X년 후 얼마', 'how much would it be'):\n"
            "  -> Set method = 'price'\n"
            "  -> We need actual price data to calculate investment returns accurately\n"
            "  -> Examples: '10년 전에 비트코인에 100만원을 투자했다면', '100만원을 넣었으면 10년 후에는 얼마일까'\n\n"
            "**PRIORITY 2: Year-over-Year Growth**\n"
            "IF prompt contains '증감률', 'growth', 'change', 'YoY', '전년 대비', '성장률', '변동률':\n"
            "  -> Set method = 'yearly_growth'\n\n"
            "**PRIORITY 3: Cumulative Returns**\n"
            "IF prompt contains '누적', 'cumulative', 'total return', '총 수익률':\n"
            "  -> Set method = 'cumulative'\n\n"
            "**PRIORITY 4: Annualized Returns**\n"
            "IF prompt contains '연평균', 'cagr', 'annualized', '평균 수익률', '평균 상승률':\n"
            "  -> Set method = 'cagr'\n\n"
            "**PRIORITY 5: Explicit Price Requests**\n"
            "IF prompt explicitly asks for prices/values:\n"
            "  - Contains: '가격', '종가', 'price', 'closing price', 'year-end price', '연말 가격', '시세'\n"
            "  -> Set method = 'price'\n\n"
            "**DEFAULT**: If none of the above match -> Set method = 'price'\n\n"
            "**STEP 2: Extract Assets**\n"
            "Identify all financial assets. Handle groups explicitly:\n"
            "- If '대표 자산' (Representative Assets) is found -> Expand to: Bitcoin, Gold, US 10Y Treasury, Silver, S&P 500.\n"
            "- If '미국 빅테크' or 'US Big Tech' or '미국 빅테크 10개 종목' -> Expand to ALL 10 companies: Apple, Microsoft, Alphabet, Amazon, Meta, Tesla, Nvidia, Netflix, Adobe, AMD.\n"

            "- If '국내 주식' or 'KR Equity' or '한국 주식 10개 종목' -> Expand to ALL 10 companies: Samsung Electronics, SK Hynix, NAVER, Kakao, LG Energy Solution, Hyundai Motor, Kia, Samsung Biologics, Samsung SDI, POSCO Holdings.\n\n"
            "**CRITICAL**: When a group like '미국 빅테크 10개 종목' is mentioned, you MUST extract all 10 companies. Do not extract only a subset.\n\n"
            "**Output Format (JSON)**\n"
            "{\n"
            "  \"reasoning\": \"Step-by-step logic used\",\n"
            "  \"calculation_method\": \"cagr\" | \"cumulative\" | \"yearly_growth\" | \"price\",\n"
            "  \"assets\": [ { \"id\": \"...\", \"label\": \"...\", \"type\": \"...\" }, ... ]\n"
            "}"
        )

        user_content = f"User Request: {combined_prompt}"

        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
            model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

            logs.append("[의도 분석] AI를 사용하여 자산 목록 추출 중...")
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}

                    ],
                    'temperature': 0.0,
                    'response_format': {'type': 'json_object'},
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']

            parsed = json.loads(content)
            assets = parsed.get('assets', [])
            llm_method = parsed.get('calculation_method', 'cagr')

            # 4. Hybrid Decision (Step 2)
            if keyword_method:
                calculation_method = keyword_method
                if keyword_method != llm_method:
                    logs.append(f"[의도 분석] AI 분류('{llm_method}')를 키워드 기반('{keyword_method}')으로 보정함.")
            else:
                calculation_method = llm_method
                logs.append(f"[의도 분석] 키워드 매칭 실패, AI 분류 사용: {calculation_method}")

            # 5. Strict Validation
            valid_methods = ['cagr', 'cumulative', 'yearly_growth', 'price']
            if calculation_method not in valid_methods:
                logs.append(f"[의도 분석] 실패: 알 수 없는 계산 방식 '{calculation_method}'")
                return {'allowed': False, 'error': f"계산 방식을 이해할 수 없습니다. ({calculation_method})"}, logs

            # Basic validation/cleanup
            clean_assets = []
            for a in assets:
                if a.get('id'):
                    # Add calculation_method to each asset
                    a['calculation_method'] = calculation_method

                    clean_assets.append(a)

            # Logging for UI
            if calculation_method == 'cumulative':
                method_label = '누적 수익률'
            elif calculation_method == 'yearly_growth':
                method_label = '전년 대비 증감률(YoY)'
            elif calculation_method == 'price':
                method_label = '가격(Price)'
            else:
                method_label = '연평균 상승률(CAGR)'

            logs.append(f"[의도 분석] {len(clean_assets)}개 자산 추출 완료: {', '.join(a['label'] for a in clean_assets)}")
            logs.append(f"[의도 분석] 최종 계산 방식: {method_label}")
            return {'allowed': True, 'assets': clean_assets, 'calculation_method': calculation_method}, logs

        except Exception as e:
            logs.append(f"[의도 분석] 자산 추출 실패: {e}")
            return {'allowed': False, 'error': '자산 추출 중 오류가 발생했습니다.'}, logs


class ValidationAgent:
    """
    Validates if the classified intent and extracted data match the user's original prompt.
    """
    def run(self, prompt, intent_result):
        logs = []
        logs.append("[검증] 분석 결과 유효성 검사 중...")

        classified_method = intent_result.get('calculation_method', 'unknown')
        assets = intent_result.get('assets', [])
        asset_names = ", ".join([a.get('label', 'unknown') for a in assets])

        # Validate classification method
        system_prompt = _get_agent_prompt('validation_agent',
            "You are a Quality Assurance auditor for a financial analysis AI. "
            "Your job is to verify if the system's classification matches the user's request.\n\n"
            "Input:\n"
            "1. User Request\n"
            "2. Classified Method (cagr, cumulative, yearly_growth, price)\n"
            "3. Extracted Assets\n\n"
            "Rules:\n"
            "- If User asks for 'Price', 'Value', 'Level', 'Close', 'Year-end', the Method MUST be 'price'. "
            "  (System deciding 'cagr' or 'cumulative' for a price request is a CRITICAL ERROR).\n"
            "- If User asks for 'Growth', 'Change', 'YoY', the Method MUST be 'yearly_growth'.\n"
            "- If User asks for 'Return', 'Profit', 'Performance', 'CAGR' is acceptable.\n"
            "- If comparison is implied without specific metric, 'cagr' is acceptable.\n\n"
            "Output JSON:\n"
            "{\n"
            "  \"valid\": true/false,\n"
            "  \"reason\": \"Short explanation if invalid\"\n"
            "}"
        )

        user_content = (
            f"User Request: {prompt}\n"
            f"Classified Method: {classified_method}\n"
            f"Extracted Assets: {asset_names}"
        )

        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
            model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    'temperature': 0.0,
                    'response_format': {'type': 'json_object'},
                },
                timeout=15,
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            result = json.loads(content)

            valid = result.get('valid', True)
            reason = result.get('reason', '')

            if not valid:
                logs.append(f"[검증] 실패: {reason}")
                return {'valid': False, 'error': reason}, logs

            logs.append("[검증] 통과: 의도와 분석 방식이 일치합니다.")

        except Exception as e:
            logs.append(f"[검증] 오류 발생 (패스): {e}")

        logs.append(f"[검증] 완료: {len(assets)}개 자산 검증됨")
        return {'valid': True}, logs


class TickerConversionAgent:
    """
    Converts asset names to proper ticker symbols/codes (e.g., "Tesla" -> "TSLA", "삼성전자" -> "005930").
    """
    def run(self, assets):
        logs = []
        logs.append(f"[티커 변환] {len(assets)}개 자산의 티커/코드 변환 중...")

        converted_assets = []

        for asset in assets:
            original_id = asset.get('id', '')
            original_label = asset.get('label', '')
            asset_type = asset.get('type', '')

            # Convert to proper ticker/code
            converted, reason = self._convert_to_ticker(original_id, original_label, asset_type)

            if converted:
                converted_assets.append({
                    **asset,
                    'id': converted['id'],
                    'label': converted['label'],
                    'ticker': converted.get('ticker'),
                    'original_id': original_id,
                    'original_label': original_label
                })
                ticker_info = converted.get('ticker', converted['id'])
                if converted['id'] != original_id:
                    logs.append(f"[티커 변환] ✓ {original_label} → {converted['id']} (Ticker: {ticker_info})")
                else:
                    logs.append(f"[티커 변환] ✓ {original_label}: 이미 올바른 형식 (Ticker: {ticker_info})")
            else:
                # Keep original if conversion fails
                converted_assets.append(asset)
                logs.append(f"[티커 변환] ✗ {original_label}: {reason}")

        logs.append(f"[티커 변환] 완료: {len(converted_assets)}개 자산 변환됨")
        return {'assets': converted_assets}, logs

    def _convert_to_ticker(self, asset_id, label, asset_type):
        """
        Convert asset name to proper ticker/code.
        Returns (dict with id, label, ticker, reason string).
        If conversion fails, returns (None, reason).
        """
        # Normalize inputs (replace underscores with spaces for better matching)
        normalized_id = (asset_id or '').strip().lower().replace('_', ' ')
        normalized_label = _normalize_asset_label_text(label)

        if not normalized_id and not normalized_label:
            return None, "자산 ID와 라벨이 모두 비어있음"

        # Bitcoin - keep as is
        if normalized_id in ['bitcoin', 'btc'] or normalized_label in ['비트코인', 'bitcoin', 'btc']:
            return {'id': 'bitcoin', 'label': '비트코인', 'ticker': 'BTC-USD'}, None

        # Check SAFE_ASSETS first
        for key, cfg in SAFE_ASSETS.items():
            ticker = (cfg.get('ticker') or '').strip().lower()
            stooq_symbol = (cfg.get('stooq_symbol') or '').strip().lower()
            cfg_label_norm = _normalize_asset_label_text(cfg.get('label'))
            cfg_aliases = [a.lower() for a in cfg.get('aliases', [])]

            if normalized_id in {key.lower(), ticker, stooq_symbol} or normalized_id in cfg_aliases:
                return {'id': key, 'label': cfg.get('label'), 'ticker': cfg.get('ticker')}, None
            if normalized_label and normalized_label in {cfg_label_norm} | set(cfg_aliases):
                return {'id': key, 'label': cfg.get('label'), 'ticker': cfg.get('ticker')}, None

        # Check PRESET_STOCK_GROUPS
        for configs in PRESET_STOCK_GROUPS.values():
            for cfg in configs:
                cfg_id = (cfg.get('id') or '').strip()
                ticker = (cfg.get('ticker') or '').strip().lower()
                stooq_symbol = (cfg.get('stooq_symbol') or '').strip().lower()
                cfg_label_norm = _normalize_asset_label_text(cfg.get('label'))
                cfg_aliases = [a.lower() for a in cfg.get('aliases', [])]

                if normalized_id in {cfg_id.lower(), ticker, stooq_symbol} or normalized_id in cfg_aliases:
                    return {'id': cfg_id, 'label': cfg.get('label'), 'ticker': cfg.get('ticker')}, None
                if normalized_label and (normalized_label == cfg_label_norm or normalized_label in cfg_aliases):
                    return {'id': cfg_id, 'label': cfg.get('label'), 'ticker': cfg.get('ticker')}, None

        # Korean stock pattern (6-digit code)
        for cand in [asset_id, label]:
            if not cand:
                continue
            cand_upper = cand.strip().upper()
            if re.match(r'^\d{6}(\.(KS|KQ|KL|KR))?$', cand_upper):
                final_ticker = cand_upper if '.' in cand_upper else f"{cand_upper}.KS"
                return {'id': final_ticker, 'label': label or final_ticker, 'ticker': final_ticker}, None

        # Not found - return None with reason
        return None, f"매칭되는 티커를 찾을 수 없음 (ID: {asset_id}, Label: {label}, Type: {asset_type})"


class PriceRetrieverAgent:
    """
    Responsible for fetching historical price data for the requested assets.
    It uses the existing helper functions (_fetch_asset_history, etc.).
    """
    def run(self, assets, start_year, end_year):
        logs = []
        logs.append(f"[데이터 수집] {len(assets)}개 자산의 {start_year}-{end_year} 데이터 가져오는 중...")

        # 한국 주식이 포함되어 있는지 확인
        def is_korean_stock_asset(asset):
            asset_id = asset.get('id', '')
            asset_type = asset.get('type', '')
            label = asset.get('label', '')

            # Type이 kr_stock인 경우
            if asset_type == 'kr_stock':
                return True

            # ID가 .KS, .KQ, .KL로 끝나는 경우
            if asset_id.endswith('.KS') or asset_id.endswith('.KQ') or asset_id.endswith('.KL'):
                return True

            # 라벨이나 ID에 한국 기업명이 포함된 경우 (대표적인 예시)
            korean_companies = [
                '삼성전자', 'SK하이닉스', 'NAVER', '네이버', '카카오',
                'LG에너지솔루션', '현대차', '기아', '삼성바이오로직스',
                '삼성SDI', '포스코홀딩스', 'Samsung Electronics', 'SK Hynix',
                'Hyundai', 'Kia'
            ]
            for company in korean_companies:
                if company.lower() in label.lower() or company.lower() in asset_id.lower():
                    return True

            return False

        has_korean_stock = any(is_korean_stock_asset(asset) for asset in assets)

        if has_korean_stock:
            logs.append(f"[데이터 수집] 한국 주식 감지 → 비트코인 원화(KRW) 시세 사용")

        price_data_map = {}

        for asset in assets:
            asset_id = asset['id']
            label = asset['label']
            asset_type = asset.get('type', 'unknown')

            logs.append(f"[데이터 수집] {label} 처리 중...")

            # 1. Map to internal config structure
            # We try to find an existing config or create a dynamic one
            config = _find_known_asset_config(asset_id, label)

            # 비트코인이고 한국 주식이 포함되어 있으면 prefer_krw 플래그 설정
            is_bitcoin = (asset_id == 'bitcoin' or label in ['비트코인', 'Bitcoin', 'BTC'])
            if config and is_bitcoin and has_korean_stock:
                config = config.copy()  # 기존 config를 수정하지 않도록 복사
                config['prefer_krw'] = True
                config['unit'] = 'KRW'  # 원화 단위로 변경

            if not config:
                # If not found in presets, construct a config based on the Agent 1 output
                # This is crucial for the new dynamic behavior

                # Determine if this is a Korean stock based on ticker pattern
                is_korean_stock_ticker = bool(re.match(r'\d{6}\.(KS|KQ|KL)', asset_id))

                # Set category: force '국내 주식' if ticker ends with .KS/.KQ/.KL
                if asset_type == 'kr_stock' or is_korean_stock_ticker:
                    category = '국내 주식'
                    unit = 'KRW'
                else:
                    category = self._map_category(asset_type)
                    unit = 'USD'

                config = {
                    'id': asset_id,
                    'label': label,
                    'ticker': asset_id,
                    'category': category,
                    'unit': unit
                }

                # Try to guess stooq symbol if not Korean stock
                if not (asset_type == 'kr_stock' or is_korean_stock_ticker):
                    config['stooq_symbol'] = _guess_stooq_symbol(asset_id)

                logs.append(f"[데이터 수집] {label}: 동적 config 생성 완료 (Category: {category}, Ticker: {asset_id})")

            # 2. Fetch History
            try:
                result = _fetch_asset_history(config, start_year, end_year)
                if result:
                    history, source = result
                    price_data_map[asset_id] = {
                        'history': history,
                        'config': config,
                        'source': source,
                        'calculation_method': asset.get('calculation_method', 'cagr')
                    }
                    # Show detailed info including ticker and category
                    ticker_info = config.get('ticker', asset_id)
                    category_info = config.get('category', '알 수 없음')
                    logs.append(f"[데이터 수집] ✓ {label}: {source}에서 {len(history)}개 데이터 포인트 수집 완료 (Ticker: {ticker_info}, Category: {category_info})")
                else:
                    logs.append(f"[데이터 수집] ✗ {label}: 데이터 없음")
            except Exception as e:
                logs.append(f"[데이터 수집] ✗ {label} 실패: {e}")
        
        return price_data_map, logs

    def _map_category(self, asset_type):
        mapping = {
            'crypto': '디지털 자산',
            'kr_stock': '국내 주식',
            'us_stock': '미국 주식',
            'index': '지수',
            'commodity': '원자재',
            'bond': '채권',
            'forex': '통화',
            'economic_indicator': '경제 지표'
        }
        return mapping.get(asset_type, '기타')


class CalculatorAgent:
    """
    Responsible for processing raw price history into the standardized 'series' format
    required by the frontend (calculating CAGR or cumulative returns, normalizing to 1.0, etc.).
    Also prepares the yearly closing prices for the table.
    """
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
            method_label = '연평균 상승률(CAGR)'

        logs.append(f"[수익률 계산] {method_label} 계산 및 데이터 포맷팅 중...")

        series_list = []

        for asset_id, data in price_data_map.items():
            history = data['history']
            config = data['config']
            source = data.get('source', 'Unknown')

            # Get calculation method for this specific asset (or use default)
            asset_calc_method = data.get('calculation_method', calculation_method)

            # Build Series for Chart (includes points data)
            try:
                series_obj = _build_asset_series(config['id'], config, history, start_year, end_year, asset_calc_method)
                if series_obj:
                    series_obj['id'] = config['id']
                    series_obj['calculation_method'] = asset_calc_method
                    series_obj['source'] = source  # Add data source to series
                    series_list.append(series_obj)
                else:
                     logs.append(f"[수익률 계산] {config['label']}: 데이터 부족으로 시리즈 생성 불가")
            except Exception as e:
                logs.append(f"[수익률 계산] {config['label']} 시리즈 생성 오류: {e}")

        # Sort by return metric descending (CAGR/Cumulative/YoY/Price change)
        series_list.sort(key=lambda x: x.get('annualized_return_pct', -999), reverse=True)

        # Convert series points to table format for display below legend
        chart_data_table = self._build_chart_data_table(series_list, calculation_method)

        logs.append(f"[수익률 계산] {len(series_list)}개 시리즈 생성 완료")

        summary = self._generate_summary(series_list, start_year, end_year)

        return series_list, chart_data_table, summary, logs

    def _build_chart_data_table(self, series_list, calculation_method):
        """
        Convert chart points data to table format for display below legend.
        Shows the actual values that are rendered in the chart.
        """
        if not series_list:
            return []

        table_data = []

        # Determine value label based on calculation method
        if calculation_method == 'price':
            value_label = '가격'
        elif calculation_method == 'cumulative':
            value_label = '누적 수익률 (%)'
        elif calculation_method == 'yearly_growth':
            value_label = '전년 대비 증감률 (%)'
        else:  # cagr
            value_label = '연평균 상승률 (%)'

        for series in series_list:
            asset_id = series.get('id', '')
            label = series.get('label', '')
            points = series.get('points', [])
            source = series.get('source', 'Unknown')
            unit = series.get('unit', '')

            if not points:
                continue

            # Convert points to year->value mapping
            yearly_values = []
            for point in points:
                year = point.get('year')
                value = point.get('value')
                if year is not None and value is not None:
                    yearly_values.append({
                        'year': year,
                        'value': round(value, 2)
                    })

            table_data.append({
                'id': asset_id,
                'label': label,
                'unit': unit,
                'source': source,
                'value_label': value_label,
                'values': yearly_values,
                'calculation_method': calculation_method
            })

        return table_data

    def _generate_summary(self, series_list, start_year, end_year):
        if not series_list:
            return "데이터가 없습니다."

        best = series_list[0]
        worst = series_list[-1]

        method = best.get('calculation_method', 'cagr')

        if method == 'price':
            # 가격 비교 모드: 가격 상승률로 표현
            return (f"{start_year}년부터 {end_year}년까지 가격 비교 결과, "
                    f"{best['label']}의 가격 상승률이 {best['annualized_return_pct']}%로 가장 높았으며, "
                    f"{worst['label']}은(는) {worst['annualized_return_pct']}%를 기록했습니다.")
        elif method == 'cumulative':
            unit = "누적 수익률"
        elif method == 'yearly_growth':
            unit = "평균 증감률"
        else:
            unit = "연평균 상승률"

        return (f"{start_year}년부터 {end_year}년까지 분석 결과, "
                f"{best['label']}이(가) {unit} {best['annualized_return_pct']}%로 가장 높은 성과를 보였으며, "
                f"{worst['label']}은(는) {worst['annualized_return_pct']}%를 기록했습니다.")


class AnalysisAgent:
    """
    Analyzes the calculation results and generates a narrative summary
    focusing on Bitcoin's performance and comparing other assets against it.
    """
    def run(self, series_list, start_year, end_year, calculation_method, prompt):
        logs = []
        logs.append("[분석 생성] 비트코인 중심 분석 리포트 생성 중...")

        if not series_list:
            return "분석할 데이터가 없습니다.", logs

        # Find Bitcoin in the series
        bitcoin = None
        other_assets = []

        for series in series_list:
            label_lower = series.get('label', '').lower()
            if 'bitcoin' in label_lower or '비트코인' in label_lower or 'btc' in label_lower:
                bitcoin = series
            else:
                other_assets.append(series)

        if not bitcoin:
            # If no Bitcoin found, fall back to generic analysis
            logs.append("[분석 생성] 비트코인 데이터를 찾을 수 없어 일반 분석으로 대체")
            return self._generate_generic_analysis(series_list, start_year, end_year, calculation_method), logs

        # Generate Bitcoin-focused analysis using LLM
        try:
            analysis_text = self._generate_ai_analysis(bitcoin, other_assets, start_year, end_year, calculation_method, prompt)
            logs.append("[분석 생성] AI 분석 리포트 생성 완료")
            return analysis_text, logs
        except Exception as e:
            logs.append(f"[분석 생성] AI 분석 실패: {e}, 기본 분석으로 대체")
            return self._generate_fallback_analysis(bitcoin, other_assets, start_year, end_year, calculation_method), logs

    def _generate_ai_analysis(self, bitcoin, other_assets, start_year, end_year, calculation_method, prompt):
        """Generate narrative analysis using LLM"""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

        # Prepare data for LLM
        bitcoin_return = bitcoin.get('annualized_return_pct', 0)
        bitcoin_multiple = bitcoin.get('multiple_from_start', 1)

        # Get method-specific terminology
        if calculation_method == 'price':
            metric_name = "가격 상승률"
        elif calculation_method == 'cumulative':
            metric_name = "누적 수익률"
        elif calculation_method == 'yearly_growth':
            metric_name = "평균 증감률"
        else:
            metric_name = "연평균 상승률"

        # Build comparison data - include ALL assets
        comparison_data = []
        for asset in other_assets:  # Include all assets, not just top 10
            asset_return = asset.get('annualized_return_pct', 0)
            asset_multiple = asset.get('multiple_from_start', 1)
            performance_vs_btc = (asset_multiple / bitcoin_multiple * 100) if bitcoin_multiple > 0 else 0

            comparison_data.append({
                'name': asset.get('label', ''),
                'return': round(asset_return, 1),
                'multiple': round(asset_multiple, 1),
                'vs_bitcoin': round(performance_vs_btc, 1)
            })

        # Sort by performance
        comparison_data.sort(key=lambda x: x['return'], reverse=True)

        system_prompt = _get_agent_prompt('analysis_generator',
            "당신은 금융 데이터 분석 전문가입니다. 비트코인을 중심으로 자산 성과를 분석하고 서술형 리포트를 작성합니다.\n\n"
            "**작성 원칙:**\n"
            "1. 비트코인의 성과를 먼저 강조하고, **제공된 모든 자산들**과 비교합니다\n"
            "2. 구체적인 수치를 포함하되, 자연스러운 문장으로 작성합니다\n"
            "3. 주요 수치(연도, 퍼센트, 배수)는 하이라이트 태그로 감쌉니다\n"
            "4. 비트코인 대비 성과가 좋은 자산과 낮은 자산을 구분하여 언급합니다\n"
            "5. **중요: 제공된 모든 자산을 리스트 형태로 나열하여 누락 없이 표시합니다**\n\n"
            "**색상 코딩 규칙 (매우 중요!):**\n"
            "- '비트코인 대비' 값은 (자산의 원금 대비 / 비트코인의 원금 대비 × 100)으로 계산됩니다\n"
            "- **이 값이 100보다 크면** → 비트코인보다 성과가 좋음 → **빨간색 (bg-red-200 text-red-900)**\n"
            "- **이 값이 100보다 작거나 같으면** → 비트코인보다 성과가 나쁨 → **파란색 (bg-blue-200 text-blue-900)**\n\n"
            "**구체적인 예시:**\n"
            "1. 엔비디아의 비트코인 대비 값이 220.6% (> 100) → 빨간색\n"
            "   <li><span class='bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold'>엔비디아(NVDA)</span>: 연평균 상승률 <span class='bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold'>129.7%</span>, 원금 대비 <span class='bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold'>12.1배</span> (비트코인 대비 <span class='bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold'>220.6%</span>)</li>\n\n"
            "2. 금의 비트코인 대비 값이 12.5% (< 100) → 파란색\n"
            "   <li><span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>금</span>: 연평균 상승률 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>8.2%</span>, 원금 대비 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>2.1배</span> (비트코인 대비 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>12.5%</span>)</li>\n\n"
            "3. 은의 비트코인 대비 값이 43.0% (< 100) → 파란색\n"
            "   <li><span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>은</span>: 연평균 상승률 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>33.2%</span>, 원금 대비 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>2.4배</span> (비트코인 대비 <span class='bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold'>43.0%</span>)</li>\n\n"
            "**하이라이트 규칙:**\n"
            "- 비트코인 관련 텍스트: <span class='bg-yellow-300 text-yellow-900 px-2 py-1 rounded font-bold text-lg'>비트코인</span>\n"
            "- 연도: <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>2015년</span>\n"
            "- 비트코인의 숫자(퍼센트, 배수): <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>81.5%</span>\n\n"
            "**출력 형식:**\n"
            "1. 첫 문단: 비트코인의 성과 요약 (비트코인 단어를 크고 노란색으로 강조)\n"
            "2. 두 번째 문단: '다른 자산들의 성과는 다음과 같습니다:'\n"
            "3. 불릿 리스트(<ul><li>): 제공된 모든 자산을 성과 순으로 나열하되, 각 자산의 '비트코인 대비' 값을 확인하여:\n"
            "   - 값이 100보다 크면 (>100): bg-red-200 text-red-900 (빨간색)\n"
            "   - 값이 100보다 작거나 같으면 (≤100): bg-blue-200 text-blue-900 (파란색)\n"
            "   자산명과 모든 수치에 동일한 색상을 적용하세요."
        )

        user_content = (
            f"사용자 요청: {prompt}\n\n"
            f"분석 기간: {start_year}년 ~ {end_year}년\n"
            f"계산 방식: {metric_name}\n\n"
            f"비트코인 성과:\n"
            f"- {metric_name}: {bitcoin_return:.1f}%\n"
            f"- 원금 대비: {bitcoin_multiple:.1f}배\n\n"
            f"다른 자산들 (비트코인 대비 상대 성과 포함):\n"
        )

        for asset in comparison_data:
            user_content += (
                f"- {asset['name']}: {metric_name} {asset['return']}%, "
                f"원금 대비 {asset['multiple']}배, "
                f"비트코인 대비 {asset['vs_bitcoin']}%\n"
            )

        user_content += "\n위 데이터를 바탕으로 비트코인을 중심으로 한 분석 리포트를 작성해주세요."

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                'temperature': 0.7,
                'max_tokens': 1000,
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']

        return content.strip()

    def _generate_fallback_analysis(self, bitcoin, other_assets, start_year, end_year, calculation_method):
        """Generate basic narrative analysis without LLM - shows all assets"""
        bitcoin_return = bitcoin.get('annualized_return_pct', 0)
        bitcoin_multiple = bitcoin.get('multiple_from_start', 1)

        if calculation_method == 'price':
            metric_name = "가격 상승률"
        elif calculation_method == 'cumulative':
            metric_name = "누적 수익률"
        elif calculation_method == 'yearly_growth':
            metric_name = "평균 증감률"
        else:
            metric_name = "연평균 상승률"

        period_years = end_year - start_year

        analysis = (
            f"<p><span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>{start_year}년</span>부터 "
            f"<span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>{end_year}년</span>까지 "
            f"<span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>{period_years}년</span> 동안, "
            f"<span class='bg-yellow-300 text-yellow-900 px-2 py-1 rounded font-bold text-lg'>비트코인</span>은 {metric_name} <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>{bitcoin_return:.1f}%</span>를 기록하며 "
            f"원금의 <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>{bitcoin_multiple:.1f}배</span>로 성장했습니다.</p>"
        )

        # Compare with ALL other assets
        if other_assets:
            # Sort other assets by performance
            sorted_others = sorted(other_assets, key=lambda x: x.get('annualized_return_pct', 0), reverse=True)

            analysis += "<p class='mt-4'>다른 자산들의 성과는 다음과 같습니다:</p>"
            analysis += "<ul class='list-disc pl-6 space-y-2 mt-2'>"

            for asset in sorted_others:
                asset_return = asset.get('annualized_return_pct', 0)
                asset_multiple = asset.get('multiple_from_start', 1)
                perf = (asset_multiple / bitcoin_multiple * 100) if bitcoin_multiple > 0 else 0

                # Apply color based on performance vs Bitcoin
                if perf > 100:
                    asset_style = "bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold"
                    number_style = "bg-red-200 text-red-900 px-2 py-0.5 rounded font-bold"
                else:
                    asset_style = "bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold"
                    number_style = "bg-blue-200 text-blue-900 px-2 py-0.5 rounded font-semibold"

                analysis += (
                    f"<li><span class='{asset_style}'>{asset.get('label')}</span>: "
                    f"{metric_name} <span class='{number_style}'>{asset_return:.1f}%</span>, "
                    f"원금 대비 <span class='{number_style}'>{asset_multiple:.1f}배</span> "
                    f"(비트코인 대비 <span class='{number_style}'>{perf:.1f}%</span>)</li>"
                )

            analysis += "</ul>"

        return analysis

    def _generate_generic_analysis(self, series_list, start_year, end_year, calculation_method):
        """Fallback when Bitcoin is not in the data - shows all assets"""
        if not series_list:
            return "<p>분석할 데이터가 없습니다.</p>"

        # Sort by performance
        sorted_assets = sorted(series_list, key=lambda x: x.get('annualized_return_pct', 0), reverse=True)

        best = sorted_assets[0]
        worst = sorted_assets[-1]

        if calculation_method == 'price':
            metric_name = "가격 상승률"
        elif calculation_method == 'cumulative':
            metric_name = "누적 수익률"
        elif calculation_method == 'yearly_growth':
            metric_name = "평균 증감률"
        else:
            metric_name = "연평균 상승률"

        period_years = end_year - start_year

        # Start with overview
        analysis = (
            f"<p><span class='highlight-year'>{start_year}년</span>부터 "
            f"<span class='highlight-year'>{end_year}년</span>까지 "
            f"<span class='highlight-number'>{period_years}년</span> 동안, "
            f"{best.get('label')}이(가) {metric_name} "
            f"<span class='highlight-number'>{best.get('annualized_return_pct', 0):.1f}%</span>로 "
            f"가장 높은 성과를 보였습니다.</p>"
        )

        # List all assets with their performance
        if len(sorted_assets) > 1:
            analysis += "<p class='mt-4'>전체 자산별 성과는 다음과 같습니다:</p>"
            analysis += "<ul class='list-disc pl-6 space-y-2 mt-2'>"

            for asset in sorted_assets:
                asset_return = asset.get('annualized_return_pct', 0)
                asset_multiple = asset.get('multiple_from_start', 1)
                analysis += (
                    f"<li><span class='font-semibold'>{asset.get('label')}</span>: "
                    f"{metric_name} <span class='highlight-number'>{asset_return:.1f}%</span>, "
                    f"원금 대비 <span class='highlight-number'>{asset_multiple:.1f}배</span></li>"
                )

            analysis += "</ul>"

        return analysis


@csrf_exempt
def finance_historical_returns_view(request):
    """
    Finance analysis endpoint with streaming log support.
    Use ?stream=1 to enable Server-Sent Events streaming.
    """
    import logging
    import time
    backend_logger = logging.getLogger('backend')
    backend_logger.info("=" * 80)
    backend_logger.info("NEW REQUEST: finance_historical_returns_view")

    # Get client identifier for logging
    user_identifier = _get_client_identifier(request)
    start_time = time.time()

    if request.method != 'POST':
        backend_logger.warning("Method not allowed: %s", request.method)
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        backend_logger.error("Invalid JSON payload")
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    # Check if streaming is requested
    use_streaming = request.GET.get('stream') == '1'

    # 1. Parse Inputs
    prompt = (payload.get('prompt') or '').strip()
    quick_requests = payload.get('quick_requests') or []
    if isinstance(quick_requests, str):
        quick_requests = [quick_requests]

    backend_logger.info("Prompt: %s", prompt)
    backend_logger.info("Quick Requests: %s", quick_requests)

    context_key = (payload.get('context_key') or '').strip()
    backend_logger.info("Context Key: %s", context_key)
    _ensure_finance_cache_purged(context_key)

    # Derive years (reusing existing logic helpers)
    start_hint = payload.get('start_year')
    try:
        start_hint = int(start_hint)
    except (TypeError, ValueError):
        start_hint = None
    prompt_year = _extract_start_year_from_prompt(prompt)
    combined_prompt_text = ' '.join(([prompt] if prompt else []) + quick_requests)
    span_hint = _extract_year_span_from_prompt(combined_prompt_text or prompt)
    start_year, end_year = _derive_finance_year_window(start_hint or prompt_year, span_hint)

    backend_logger.info("Year Range: %s - %s", start_year, end_year)

    if use_streaming:
        # Return a streaming response (logging handled in stream generator)
        return StreamingHttpResponse(
            _finance_analysis_stream(prompt, quick_requests, context_key, start_year, end_year, user_identifier, start_time),
            content_type='text/event-stream'
        )
    else:
        # Original non-streaming implementation
        all_logs = []
        all_logs.append(f"시스템: {start_year}-{end_year} 멀티 에이전트 분석 시작")

        # --- Multi-Agent Workflow ---

        # Agent 1: Intent Classifier
        backend_logger.info("STEP 1: Running IntentClassifierAgent")
        intent_agent = IntentClassifierAgent()
        intent_result, intent_logs = intent_agent.run(prompt, quick_requests)
        all_logs.extend(intent_logs)

        backend_logger.info("Intent Result: %s", intent_result)

        if not intent_result.get('allowed'):
            backend_logger.warning("Request blocked by guardrail")
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             intent_result.get('error', 'Request blocked'), 0, processing_time_ms)
            return JsonResponse({
                'ok': False,
                'error': intent_result.get('error', 'Request blocked'),
                'logs': all_logs
            }, status=400)

        assets = intent_result.get('assets', [])
        calculation_method = intent_result.get('calculation_method', 'cagr')
        backend_logger.info("Extracted Assets (%d): %s", len(assets), assets)
        backend_logger.info("Calculation Method: %s", calculation_method)

        if not assets:
            backend_logger.error("No assets found - returning 400")
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '분석할 자산을 찾을 수 없습니다.', 0, processing_time_ms)
            return JsonResponse({
                'ok': False,
                'error': '분석할 자산을 찾을 수 없습니다.',
                'logs': all_logs
            }, status=400)

        # Agent 1.5: Validation Agent
        backend_logger.info("STEP 1.5: Running ValidationAgent")
        validation_agent = ValidationAgent()
        # Use original prompts for validation context
        combined_prompt_text = ' '.join(([prompt] if prompt else []) + quick_requests)
        val_res, val_logs = validation_agent.run(combined_prompt_text, intent_result)
        all_logs.extend(val_logs)

        if not val_res.get('valid'):
            backend_logger.warning("Validation failed: %s", val_res.get('error'))
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"요청 분석 오류: {val_res.get('error')}"
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             error_msg, len(assets), processing_time_ms)
            return JsonResponse({
                'ok': False,
                'error': error_msg,
                'logs': all_logs
            }, status=400)

        # Agent 1.6: Ticker Conversion Agent
        backend_logger.info("STEP 1.6: Running TickerConversionAgent")
        ticker_agent = TickerConversionAgent()
        ticker_res, ticker_logs = ticker_agent.run(assets)
        all_logs.extend(ticker_logs)

        # Use converted assets with proper tickers/codes
        validated_assets = ticker_res.get('assets', assets)
        backend_logger.info("Converted Assets: %s", validated_assets)

        # Agent 2: Price Retriever
        backend_logger.info("STEP 2: Running PriceRetrieverAgent")
        retriever_agent = PriceRetrieverAgent()
        price_data_map, retriever_logs = retriever_agent.run(validated_assets, start_year, end_year)
        all_logs.extend(retriever_logs)

        backend_logger.info("Price Data Map Keys: %s", list(price_data_map.keys()) if price_data_map else "EMPTY")

        if not price_data_map:
            backend_logger.error("No price data retrieved - returning 502")
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '자산 데이터를 가져올 수 없습니다.', len(assets), processing_time_ms)
            return JsonResponse({
                'ok': False,
                'error': '자산 데이터를 가져올 수 없습니다. (티커를 확인해주세요)',
                'logs': all_logs
            }, status=502)

        # Agent 3: Calculator
        backend_logger.info("STEP 3: Running CalculatorAgent with method: %s", calculation_method)
        calculator_agent = CalculatorAgent()
        series_data, chart_data_table, summary, calculator_logs = calculator_agent.run(price_data_map, start_year, end_year, calculation_method)
        all_logs.extend(calculator_logs)

        if not series_data:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '유효한 수익률 데이터를 계산할 수 없습니다.', len(assets), processing_time_ms)
            return JsonResponse({
                'ok': False,
                'error': '유효한 수익률 데이터를 계산할 수 없습니다.',
                'logs': all_logs
            }, status=502)

        # Agent 4: Analysis (Generate narrative summary)
        backend_logger.info("STEP 4: Running AnalysisAgent")
        analysis_agent = AnalysisAgent()
        combined_prompt_for_analysis = ' '.join(([prompt] if prompt else []) + quick_requests)
        analysis_summary, analysis_logs = analysis_agent.run(series_data, start_year, end_year, calculation_method, combined_prompt_for_analysis)
        all_logs.extend(analysis_logs)

        # Cache Result (if context_key is present)
        usd_krw_rate = get_cached_usdkrw_rate()
        if context_key in ['safe_assets', 'us_bigtech']:
            _save_to_cache(context_key, start_year, end_year, series_data, usd_krw_rate)

        # Log successful query
        processing_time_ms = int((time.time() - start_time) * 1000)
        _log_finance_query(user_identifier, prompt, quick_requests, context_key, True,
                         '', len(assets), processing_time_ms)

        # Construct Response
        response_payload = {
            'ok': True,
            'series': series_data,
            'chart_data_table': chart_data_table,  # Chart values as table (replaces yearly_prices)
            'analysis_summary': analysis_summary,  # AI-generated narrative analysis
            'start_year': start_year,
            'end_year': end_year,
            'summary': summary,
            'notes': "본 분석은 AI 에이전트가 실시간 데이터를 수집하여 계산했습니다.",
            'fx_rate': usd_krw_rate,
            'logs': all_logs,
            'prompt': prompt,
            'quick_requests': quick_requests,
            'calculation_method': calculation_method,
        }

        return JsonResponse(response_payload)


def _finance_analysis_stream(prompt, quick_requests, context_key, start_year, end_year, user_identifier, start_time):
    """Generator function for streaming finance analysis logs."""
    import logging
    import time
    backend_logger = logging.getLogger('backend')

    def send_log(message):
        """Helper to send a log message as SSE."""
        return f"data: {json.dumps({'type': 'log', 'message': message})}\n\n"

    def send_error(error_message):
        """Helper to send an error as SSE."""
        return f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"

    def send_result(data):
        """Helper to send final result as SSE."""
        return f"data: {json.dumps({'type': 'result', 'data': data})}\n\n"

    try:
        yield send_log(f"시스템: {start_year}-{end_year} 멀티 에이전트 분석 시작")

        # Agent 1: Intent Classifier
        intent_agent = IntentClassifierAgent()
        intent_result, intent_logs = intent_agent.run(prompt, quick_requests)

        for log in intent_logs:
            yield send_log(log)

        if not intent_result.get('allowed'):
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             intent_result.get('error', 'Request blocked'), 0, processing_time_ms)
            yield send_error(intent_result.get('error', 'Request blocked'))
            return

        assets = intent_result.get('assets', [])
        calculation_method = intent_result.get('calculation_method', 'cagr')
        if not assets:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '분석할 자산을 찾을 수 없습니다.', 0, processing_time_ms)
            yield send_error('분석할 자산을 찾을 수 없습니다.')
            return

        # Agent 1.5: Validation Agent
        validation_agent = ValidationAgent()
        combined_prompt_text = ' '.join(([prompt] if prompt else []) + quick_requests)
        val_res, val_logs = validation_agent.run(combined_prompt_text, intent_result)

        for log in val_logs:
            yield send_log(log)

        if not val_res.get('valid'):
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"요청 분석 오류: {val_res.get('error')}"
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             error_msg, len(assets), processing_time_ms)
            yield send_error(error_msg)
            return

        # Agent 1.6: Ticker Conversion Agent
        ticker_agent = TickerConversionAgent()
        ticker_res, ticker_logs = ticker_agent.run(assets)

        for log in ticker_logs:
            yield send_log(log)

        # Use converted assets with proper tickers/codes
        validated_assets = ticker_res.get('assets', assets)

        # Agent 2: Price Retriever
        retriever_agent = PriceRetrieverAgent()
        price_data_map, retriever_logs = retriever_agent.run(validated_assets, start_year, end_year)

        for log in retriever_logs:
            yield send_log(log)

        if not price_data_map:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '자산 데이터를 가져올 수 없습니다.', len(assets), processing_time_ms)
            yield send_error('자산 데이터를 가져올 수 없습니다.')
            return

        # Agent 3: Calculator
        calculator_agent = CalculatorAgent()
        series_data, chart_data_table, summary, calculator_logs = calculator_agent.run(price_data_map, start_year, end_year, calculation_method)

        for log in calculator_logs:
            yield send_log(log)

        if not series_data:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '유효한 수익률 데이터를 계산할 수 없습니다.', len(assets), processing_time_ms)
            yield send_error('유효한 수익률 데이터를 계산할 수 없습니다.')
            return

        # Agent 4: Analysis (Generate narrative summary)
        analysis_agent = AnalysisAgent()
        combined_prompt_for_analysis = ' '.join(([prompt] if prompt else []) + quick_requests)
        analysis_summary, analysis_logs = analysis_agent.run(series_data, start_year, end_year, calculation_method, combined_prompt_for_analysis)

        for log in analysis_logs:
            yield send_log(log)

        # Cache and send final result
        usd_krw_rate = get_cached_usdkrw_rate()
        if context_key in ['safe_assets', 'us_bigtech']:
            _save_to_cache(context_key, start_year, end_year, series_data, usd_krw_rate)

        # Log successful query
        processing_time_ms = int((time.time() - start_time) * 1000)
        _log_finance_query(user_identifier, prompt, quick_requests, context_key, True,
                         '', len(assets), processing_time_ms)

        result_payload = {
            'ok': True,
            'series': series_data,
            'chart_data_table': chart_data_table,  # Chart values as table (replaces yearly_prices)
            'analysis_summary': analysis_summary,  # AI-generated narrative analysis
            'start_year': start_year,
            'end_year': end_year,
            'summary': summary,
            'notes': "본 분석은 AI 에이전트가 실시간 데이터를 수집하여 계산했습니다.",
            'fx_rate': usd_krw_rate,
            'prompt': prompt,
            'quick_requests': quick_requests,
            'calculation_method': calculation_method,
        }

        yield send_result(result_payload)

    except Exception as e:
        backend_logger.error(f"Stream error: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                         f"분석 중 오류: {str(e)}", 0, processing_time_ms)
        yield send_error(f"분석 중 오류가 발생했습니다: {str(e)}")


@csrf_exempt
def finance_yearly_closing_prices_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    assets = payload.get('assets')
    if not isinstance(assets, list) or not assets:
        return JsonResponse({'ok': False, 'error': 'assets must be a non-empty list'}, status=400)

    try:
        start_year = int(payload.get('start_year') or FINANCE_DEFAULT_START_YEAR)
    except (TypeError, ValueError):
        start_year = FINANCE_DEFAULT_START_YEAR
    try:
        end_year = int(payload.get('end_year') or datetime.utcnow().year)
    except (TypeError, ValueError):
        end_year = datetime.utcnow().year
    if end_year < start_year:
        end_year = start_year

    results = []
    global_errors = [] # Collected for overall response

    seen_ids = set() # To prevent duplicate processing if same ID appears multiple times in request

    for entry in assets:
        if not isinstance(entry, dict):
            global_errors.append(f"유효하지 않은 자산 형식: {entry}")
            continue

        asset_id = (str(entry.get('id') or entry.get('ticker') or '')).strip()
        label = (entry.get('label') or '').strip()
        context_label = label or asset_id or '알 수 없는 자산'

        current_result_entry = {
            'id': asset_id, # Default to requested ID
            'requested_id': asset_id,
            'label': label,
            'unit': entry.get('unit') or '',
            'category': entry.get('category') or '',
            'source': '',
            'prices': [],
            'aliases': [],
            'status': 'failed', # Default status
            'error_message': None,
            'alt_prices': {},
            'alt_sources': {},
        }

        # Check for duplicates in the request payload
        if asset_id in seen_ids:
            continue
        seen_ids.add(asset_id)

        config = _find_known_asset_config(asset_id, label)
        
        if not config:
            current_result_entry['error_message'] = f"{context_label}: 지원되지 않는 자산입니다."
            global_errors.append(current_result_entry['error_message'])
            results.append(current_result_entry)
            continue
        
        # Override with canonical config info (e.g. if '삼성전자' maps to '005930.KS')
        current_result_entry['id'] = config.get('id') or asset_id
        current_result_entry['label'] = config.get('label') or label or current_result_entry['id']
        current_result_entry['unit'] = config.get('unit') or entry.get('unit') or ''
        current_result_entry['category'] = config.get('category') or entry.get('category') or ''
        current_result_entry['aliases'] = _collect_asset_aliases(config, asset_id)

        try:
            price_payload = _fetch_yearly_closing_prices(config, start_year, end_year)
            prices = (price_payload or {}).get('prices') or []

            if not prices:
                current_result_entry['error_message'] = f"{current_result_entry['label']}: 데이터가 없습니다."
                global_errors.append(current_result_entry['error_message'])
            else:
                current_result_entry['prices'] = prices
                current_result_entry['source'] = price_payload.get('source') or ''
                current_result_entry['status'] = 'success'

                alt_prices = price_payload.get('alt_prices') or {}
                alt_sources = price_payload.get('alt_sources') or {}
                if alt_prices:
                    current_result_entry['alt_prices'] = alt_prices
                if alt_sources:
                    current_result_entry['alt_sources'] = alt_sources

        except Exception as exc:
            logger.warning('Failed to fetch yearly closing prices for %s: %s', context_label, exc)
            current_result_entry['error_message'] = f"{current_result_entry['label']}: {exc}"
            global_errors.append(current_result_entry['error_message'])

        results.append(current_result_entry)

    if not results and not global_errors: # If no assets were processed and no errors occurred
         return JsonResponse({'ok': True, 'start_year': start_year, 'end_year': end_year, 'data': [], 'errors': []})

    if not results: # All assets failed and no results
        status_code = 400 if global_errors else 502
        return JsonResponse({'ok': False, 'error': '연도별 종가 데이터를 가져올 수 없습니다.', 'errors': global_errors}, status=status_code)

    return JsonResponse({
        'ok': True,
        'start_year': start_year,
        'end_year': end_year,
        'data': results,
        'errors': global_errors, # Still include for overall context if needed
    })


# Kingstone wallet endpoints
@csrf_exempt
def kingstone_wallets_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    username = (request.GET.get('username') or '').strip()
    if not username:
        return JsonResponse({'ok': False, 'error': 'username required'}, status=400)

    wallets = KingstoneWallet.objects.filter(username=username).order_by('index', 'created_at')
    return JsonResponse({
        'ok': True,
        'wallets': [w.as_dict() for w in wallets],
        'count': wallets.count(),
        'limit': KINGSTONE_WALLET_LIMIT,
    })


@csrf_exempt
def kingstone_verify_pin_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    data = _load_json_body(request)
    if data is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    username = (data.get('username') or '').strip()
    pin = (str(data.get('pin') or '').strip())

    if not username:
        return JsonResponse({'ok': False, 'error': 'username required'}, status=400)
    if not pin:
        return JsonResponse({'ok': False, 'error': 'pin required'}, status=400)

    wallets = list(KingstoneWallet.objects.filter(username=username))
    if not wallets:
        return JsonResponse({'ok': False, 'code': 'no_pins', 'error': '등록된 핀번호가 없습니다. 새 핀번호를 등록하세요.'})

    for wallet in wallets:
        if wallet.check_pin(pin):
            return JsonResponse({'ok': True, 'wallet': wallet.as_dict()})

    return JsonResponse({'ok': False, 'code': 'invalid_pin', 'error': '핀번호가 올바르지 않습니다. 새 핀번호를 등록하세요.'})


@csrf_exempt
def kingstone_register_pin_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    data = _load_json_body(request)
    if data is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    username = (data.get('username') or '').strip()
    pin = (str(data.get('pin') or '').strip())
    requested_name = (data.get('wallet_name') or '').strip()
    mnemonic_override = (data.get('mnemonic') or '').strip()

    if not username:
        return JsonResponse({'ok': False, 'error': 'username required'}, status=400)
    if not pin:
        return JsonResponse({'ok': False, 'error': 'pin required'}, status=400)

    if not pin.isdigit() or len(pin) != 6:
        return JsonResponse({'ok': False, 'error': '핀번호는 6자리 숫자여야 합니다.'}, status=400)

    existing_wallets = list(KingstoneWallet.objects.filter(username=username).order_by('index'))
    if len(existing_wallets) >= KINGSTONE_WALLET_LIMIT:
        return JsonResponse({'ok': False, 'code': 'limit_reached', 'error': f'핀번호는 최대 {KINGSTONE_WALLET_LIMIT}개까지 등록할 수 있습니다.'}, status=400)

    for wallet in existing_wallets:
        if wallet.check_pin(pin):
            return JsonResponse({'ok': False, 'code': 'duplicate_pin', 'error': '이미 등록된 핀번호입니다.'}, status=400)

    used_indexes = {wallet.index for wallet in existing_wallets if wallet.index is not None}
    next_index = None
    for candidate in range(1, KINGSTONE_WALLET_LIMIT + 1):
        if candidate not in used_indexes:
            next_index = candidate
            break

    if not next_index:
        # Fallback just in case
        next_index = len(existing_wallets) + 1

    wallet_name = requested_name or f"지갑{next_index}"

    wallet = KingstoneWallet(username=username, index=next_index, wallet_name=wallet_name)
    if mnemonic_override:
        wallet.mnemonic = mnemonic_override
    wallet.set_pin(pin)
    wallet.save()

    return JsonResponse({'ok': True, 'wallet': wallet.as_dict(), 'limit': KINGSTONE_WALLET_LIMIT})


@csrf_exempt
def kingstone_delete_wallet_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    data = _load_json_body(request)
    if data is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    username = (data.get('username') or '').strip()
    wallet_id = (data.get('wallet_id') or '').strip()

    if not username:
        return JsonResponse({'ok': False, 'error': 'username required'}, status=400)
    if not wallet_id:
        return JsonResponse({'ok': False, 'error': 'wallet_id required'}, status=400)

    try:
        if username == 'admin':
            wallet = KingstoneWallet.objects.get(wallet_id=wallet_id)
        else:
            wallet = KingstoneWallet.objects.get(username=username, wallet_id=wallet_id)
        wallet.delete()
        return JsonResponse({'ok': True, 'message': '지갑이 삭제되었습니다'})
    except KingstoneWallet.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '지갑을 찾을 수 없습니다'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'삭제 실패: {str(e)}'}, status=500)


@csrf_exempt
def kingstone_wallet_address_view(request):
    """Get BIP84 address for a Kingstone wallet by wallet_id and index."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    username = (request.GET.get('username') or '').strip()
    wallet_id = (request.GET.get('wallet_id') or '').strip()

    if not username:
        return JsonResponse({'ok': False, 'error': 'username required'}, status=400)
    if not wallet_id:
        return JsonResponse({'ok': False, 'error': 'wallet_id required'}, status=400)

    try:
        index = max(0, int(request.GET.get('index', '0')))
    except Exception:
        index = 0
    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0
    try:
        change = max(0, int(request.GET.get('change', '0')))
    except Exception:
        change = 0

    try:
        wallet = KingstoneWallet.objects.get(username=username, wallet_id=wallet_id)
    except KingstoneWallet.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '지갑을 찾을 수 없습니다'}, status=404)

    if not wallet.mnemonic:
        return JsonResponse({'ok': False, 'error': '지갑에 니모닉이 없습니다'}, status=400)

    try:
        addresses = derive_bip84_addresses(wallet.mnemonic, account=account, change=change, start=index, count=1)
        if not addresses:
            return JsonResponse({'ok': False, 'error': 'address derivation failed'}, status=500)
        return JsonResponse({'ok': True, 'address': addresses[0], 'index': index, 'account': account, 'change': change})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deriving address for wallet {wallet_id}: {e}")
        return JsonResponse({'ok': False, 'error': f'address derivation failed: {e}'}, status=400)


@csrf_exempt
def admin_kingstone_wallets_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    wallets = KingstoneWallet.objects.all().order_by('-created_at')
    results = []
    for wallet in wallets:
        pin_plain = wallet.get_pin_plain()
        results.append({
            'id': wallet.id,
            'wallet_id': wallet.wallet_id,
            'wallet_name': wallet.wallet_name,
            'username': wallet.username,
            'created_at': wallet.created_at.isoformat(),
            'pin': pin_plain,
        })

    return JsonResponse({'ok': True, 'wallets': results})


# Wallet password endpoints
@csrf_exempt
def admin_set_wallet_password_view(request):
    _ensure_sidebar_schema()
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = {}
    password = (payload.get('password') or '').strip()
    if not password:
        # Clear password
        h = ''
        plain = ''
    else:
        h = hashlib.sha256(password.encode('utf-8')).hexdigest()
        plain = password
    config, _ = SidebarConfig.objects.get_or_create(id=1)
    config.wallet_password_hash = h
    config.wallet_password_plain = plain
    config.save()
    return JsonResponse({'ok': True, 'wallet_password_set': bool(h)})


@csrf_exempt
def wallet_password_check_view(request):
    _ensure_sidebar_schema()
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = {}
    password = (payload.get('password') or '').strip()
    config, _ = SidebarConfig.objects.get_or_create(id=1)
    h = hashlib.sha256(password.encode('utf-8')).hexdigest() if password else ''
    if not config.wallet_password_hash:
        return JsonResponse({'ok': False, 'error': 'not_set'})
    if h and h == config.wallet_password_hash:
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'invalid'})


@csrf_exempt
def admin_get_wallet_password_view(request):
    _ensure_sidebar_schema()
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)
    config, _ = SidebarConfig.objects.get_or_create(id=1)
    return JsonResponse({'ok': True, 'password': config.wallet_password_plain or ''})


# ============================================================
# Agent Prompt Management
# ============================================================

def _get_or_create_default_agent_prompts():
    """Initialize default agent prompts if they don't exist"""
    from .models import AgentPrompt

    defaults = {
        'intent_classifier': {
            'name': '의도 분석 Agent',
            'description': '사용자 요청을 분석하여 자산 목록을 추출하고 계산 방식을 결정합니다.',
            'system_prompt': (
                "You are a financial intent classifier. "
                "Extract a list of financial assets or economic indicators mentioned in the user's request. "
                "For each asset/indicator, provide the following fields: "
                "- 'id': The ticker symbol (e.g., 'AAPL', 'BTC-USD'), Korean stock code (e.g., '005930.KS'), or indicator code (e.g., 'M2-US', 'M2-KR'). "
                "  **CRITICAL**: For Korean stocks, you MUST provide the 6-digit code followed by '.KS' or '.KQ'. "
                "  (e.g., Samsung Electronics -> '005930.KS', Kakao -> '035720.KS'). "
                "  For economic indicators like M2 money supply, use 'M2-US' for US M2, 'M2-KR' for Korean M2. "
                "- 'label': The display name (e.g., 'Samsung Electronics', 'Bitcoin', 'US M2 Money Supply'). "
                "- 'type': One of 'crypto', 'kr_stock', 'us_stock', 'index', 'commodity', 'forex', 'bond', 'economic_indicator'. "
                "- 'calculation_method': REQUIRED. Determine from user's request:\n"
                "  * 'cagr' (default): If user asks for '연평균', 'CAGR', 'annualized', '평균 수익률'\n"
                "  * 'cumulative': If user asks for '누적', 'total return', '총 상승률', '전체 상승률'\n"
                "  * If unclear, use 'cagr' as default.\n"
                "If the user asks for a group (e.g., 'US Big Tech'), expand it into individual representative stocks (max 10). "
                "IMPORTANT: The 'calculation_method' should be the SAME for all assets unless the user specifically requests different methods for different assets. "
                "Return ONLY a JSON object with keys 'assets' (list) and 'calculation_method' (string: 'cagr' or 'cumulative')."
            ),
        },
        'guardrail': {
            'name': '가드레일 Agent',
            'description': '부적절한 요청을 필터링하고 안전성을 검사합니다.',
            'system_prompt': (
                "당신은 사용자 요청의 의도를 분류하는 전문가입니다.\n\n"
                "주어진 사용자 요청이 다음 중 어디에 해당하는지 판단하세요:\n\n"
                "1. **금융 분석 요청**: 자산(예: 비트코인, 삼성전자, S&P 500 등)의 수익률, 가격 변동, 비교 분석 등을 원하는 경우.\n"
                "   - 이런 경우 'allowed': true를 반환하세요.\n\n"
                "2. **부적절한 요청**: 금융 분석과 무관하거나, 개인정보를 요구하거나, 시스템 악용을 시도하는 경우.\n"
                "   - 이런 경우 'allowed': false를 반환하고, 'reason'에 거부 사유를 간단히 설명하세요.\n\n"
                "응답 형식 (JSON만 반환):\n"
                "{\n"
                '  "allowed": true 또는 false,\n'
                '  "reason": "거부 사유 (allowed가 false일 때만)"\n'
                "}\n\n"
            ),
        },
    }

    created = []
    for agent_type, data in defaults.items():
        agent, is_new = AgentPrompt.objects.get_or_create(
            agent_type=agent_type,
            defaults=data
        )
        if is_new:
            created.append(agent.name)

    return created


@csrf_exempt
def admin_agent_prompts_view(request):
    """
    GET: List all agent prompts
    POST: Create or initialize default agent prompts
    """
    from .models import AgentPrompt

    if request.method == 'GET':
        # Initialize defaults if empty
        if AgentPrompt.objects.count() == 0:
            _get_or_create_default_agent_prompts()

        prompts = AgentPrompt.objects.all()
        return JsonResponse({
            'ok': True,
            'prompts': [p.as_dict() for p in prompts]
        })

    elif request.method == 'POST':
        # Initialize defaults
        created = _get_or_create_default_agent_prompts()
        prompts = AgentPrompt.objects.all()
        return JsonResponse({
            'ok': True,
            'created': created,
            'prompts': [p.as_dict() for p in prompts]
        })

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_agent_prompt_detail_view(request, agent_type):
    """
    GET: Get specific agent prompt
    PUT/PATCH: Update agent prompt
    """
    from .models import AgentPrompt

    if request.method == 'GET':
        try:
            prompt = AgentPrompt.objects.get(agent_type=agent_type)
            return JsonResponse({
                'ok': True,
                'prompt': prompt.as_dict()
            })
        except AgentPrompt.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': f'Agent prompt not found: {agent_type}'
            }, status=404)

    elif request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        try:
            prompt = AgentPrompt.objects.get(agent_type=agent_type)

            # Update fields
            if 'name' in payload:
                prompt.name = payload['name']
            if 'description' in payload:
                prompt.description = payload['description']
            if 'system_prompt' in payload:
                prompt.system_prompt = payload['system_prompt']
                # Increment version when prompt changes
                prompt.version += 1
            if 'is_active' in payload:
                prompt.is_active = payload['is_active']

            prompt.save()

            return JsonResponse({
                'ok': True,
                'prompt': prompt.as_dict()
            })
        except AgentPrompt.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': f'Agent prompt not found: {agent_type}'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)
