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
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Block, Nickname, Mnemonic, ExchangeRate, WithdrawalFee, LightningService, ServiceNode, Route, RoutingSnapshot, SidebarConfig, KingstoneWallet
from django.db import connection
from django.conf import settings
from .broadcast import broadcaster
from .btc import derive_bip84_addresses, fetch_blockstream_balances, calc_total_sats, derive_bip84_account_zpub, derive_master_fingerprint, _normalize_mnemonic
from mnemonic import Mnemonic as MnemonicValidator


MAX_NONCE = 100000
DIFFICULTY_BASE = 5000
KINGSTONE_WALLET_LIMIT = 3
FINANCE_DEFAULT_START_YEAR = 2016
FINANCE_YEAR_SPAN = 10
FINANCE_MAX_SERIES = 10

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
        'stooq_symbol': 'us10y',
        'unit': '%',
        'category': '채권',
        'aliases': ['미국 10년물 국채', '10년물 국채', 'us 10y', 'us10y', 'treasury']
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
    }
}

SAFE_ASSET_ALIASES = {}
for key, cfg in SAFE_ASSETS.items():
    for alias in cfg.get('aliases', []):
        SAFE_ASSET_ALIASES[alias.lower()] = key

PRESET_STOCK_GROUPS = {
    'us_bigtech': [
        {'id': 'AAPL', 'label': '애플(AAPL)', 'ticker': 'AAPL', 'stooq_symbol': 'aapl.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'MSFT', 'label': '마이크로소프트(MSFT)', 'ticker': 'MSFT', 'stooq_symbol': 'msft.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'GOOGL', 'label': '알파벳(GOOGL)', 'ticker': 'GOOGL', 'stooq_symbol': 'googl.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'AMZN', 'label': '아마존(AMZN)', 'ticker': 'AMZN', 'stooq_symbol': 'amzn.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'META', 'label': '메타(META)', 'ticker': 'META', 'stooq_symbol': 'meta.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'TSLA', 'label': '테슬라(TSLA)', 'ticker': 'TSLA', 'stooq_symbol': 'tsla.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'NVDA', 'label': '엔비디아(NVDA)', 'ticker': 'NVDA', 'stooq_symbol': 'nvda.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'NFLX', 'label': '넷플릭스(NFLX)', 'ticker': 'NFLX', 'stooq_symbol': 'nflx.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'ADBE', 'label': '어도비(ADBE)', 'ticker': 'ADBE', 'stooq_symbol': 'adbe.us', 'category': '미국 빅테크', 'unit': 'USD'},
        {'id': 'AMD', 'label': 'AMD(AMD)', 'ticker': 'AMD', 'stooq_symbol': 'amd.us', 'category': '미국 빅테크', 'unit': 'USD'}
    ],
    'kr_equity': [
        {'id': '005930.KS', 'label': '삼성전자(005930)', 'ticker': '005930.KS', 'stooq_symbol': '005930.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '000660.KS', 'label': 'SK하이닉스(000660)', 'ticker': '000660.KS', 'stooq_symbol': '000660.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '035420.KS', 'label': 'NAVER(035420)', 'ticker': '035420.KS', 'stooq_symbol': '035420.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '051910.KS', 'label': 'LG화학(051910)', 'ticker': '051910.KS', 'stooq_symbol': '051910.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '005380.KS', 'label': '현대차(005380)', 'ticker': '005380.KS', 'stooq_symbol': '005380.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '207940.KS', 'label': '삼성바이오로직스(207940)', 'ticker': '207940.KS', 'stooq_symbol': '207940.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '006400.KS', 'label': '삼성SDI(006400)', 'ticker': '006400.KS', 'stooq_symbol': '006400.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '028260.KS', 'label': '삼성물산(028260)', 'ticker': '028260.KS', 'stooq_symbol': '028260.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '105560.KS', 'label': 'KB금융(105560)', 'ticker': '105560.KS', 'stooq_symbol': '105560.kr', 'category': '국내 주식', 'unit': 'KRW'},
        {'id': '055550.KS', 'label': '신한지주(055550)', 'ticker': '055550.KS', 'stooq_symbol': '055550.kr', 'category': '국내 주식', 'unit': 'KRW'}
    ]
}

_guest_counter = 0
_guest_lock = threading.Lock()
_btc_usdt_cache = {'price': None, 'expires_at': 0.0}
_btc_usdt_lock = threading.Lock()
_usdkrw_cache = {'rate': None, 'expires_at': 0.0}
_usdkrw_lock = threading.Lock()
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
    """Check if user has admin privileges (supports JSON POST bodies)."""
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


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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

        logger.info('Yahoo Finance에서 %s 데이터 %d개 가져옴 (%d-%d)', ticker, len(rows), start_year, end_year)
        return rows
    except Exception as exc:
        logger.warning('Yahoo Finance fetch failed for %s: %s', ticker, exc)
        raise


def _fetch_stooq_history(symbol, start_year, end_year):
    if not symbol:
        return []
    start_dt = datetime(start_year, 1, 1)
    end_dt = datetime(end_year, 12, 31) + timedelta(days=1)
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
        value = _safe_float(price)
        if value is None:
            continue
        rows.append((dt, value))
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


def _fetch_asset_history(cfg, start_year, end_year):
    """
    여러 데이터 소스를 순서대로 시도하여 자산 가격 이력을 가져옵니다.
    우선순위: Yahoo Finance > Stooq
    """
    errors = []
    label = cfg.get('label', 'Unknown')
    ticker = cfg.get('ticker')
    stooq_symbol = cfg.get('stooq_symbol') or _guess_stooq_symbol(ticker)

    # 1. Yahoo Finance 시도
    if ticker:
        try:
            logger.info('[%s] Yahoo Finance에서 데이터 가져오기 시도: %s', label, ticker)
            history = _fetch_yfinance_history(ticker, start_year, end_year)
            if history:
                logger.info('[%s] Yahoo Finance에서 데이터 가져오기 성공: %d개', label, len(history))
                return history
            else:
                errors.append('Yahoo Finance: 데이터 없음')
                logger.warning('[%s] Yahoo Finance에서 데이터를 찾지 못함', label)
        except Exception as exc:
            errors.append(f'Yahoo Finance: {exc}')
            logger.warning('[%s] Yahoo Finance 실패: %s', label, exc)

    # 2. Stooq 시도
    if stooq_symbol:
        try:
            logger.info('[%s] Stooq에서 데이터 가져오기 시도: %s', label, stooq_symbol)
            history = _fetch_stooq_history(stooq_symbol, start_year, end_year)
            if history:
                logger.info('[%s] Stooq에서 데이터 가져오기 성공: %d개', label, len(history))
                return history
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


def _build_asset_series(asset_key, cfg, history, start_year, end_year):
    if not history:
        return None
    yearly_prices = {}
    for dt, value in history:
        year = dt.year
        if year < start_year or year > end_year:
            continue
        prev = yearly_prices.get(year)
        if not prev or dt > prev[0]:
            yearly_prices[year] = (dt, value)
    if len(yearly_prices) < 2:
        return None
    ordered_years = sorted(yearly_prices.keys())
    base_year = ordered_years[0]
    base_value = yearly_prices[base_year][1]
    if not base_value or base_value <= 0:
        return None

    points = []
    for year in ordered_years:
        price = yearly_prices[year][1]
        if price is None or price <= 0:
            continue
        multiple = price / base_value
        if year == base_year:
            annualized_pct = 0.0
        else:
            years_elapsed = year - base_year
            if years_elapsed <= 0:
                annualized_pct = 0.0
            else:
                annualized_pct = ((price / base_value) ** (1 / years_elapsed) - 1) * 100
        points.append({
            'year': year,
            'value': round(annualized_pct, 3),
            'multiple': round(multiple, 6),
            'raw_value': round(price, 6)
        })
    if len(points) < 2:
        return None

    start_val = points[0]['multiple'] or 1.0
    end_val = points[-1]['multiple'] or start_val
    years_total = points[-1]['year'] - points[0]['year']
    if years_total > 0 and start_val > 0:
        agg = (end_val / start_val) ** (1 / years_total) - 1
    else:
        agg = 0.0

    return {
        'id': cfg.get('id') or asset_key,
        'label': cfg['label'],
        'category': cfg.get('category', '안전자산'),
        'unit': cfg.get('unit', ''),
        'points': points,
        'annualized_return_pct': round(agg * 100, 2),
        'multiple_from_start': round(end_val / start_val, 3) if start_val else 0.0,
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


def _derive_finance_year_window(year_hint):
    current_year = datetime.utcnow().year
    min_year = 2010
    base_year = year_hint or FINANCE_DEFAULT_START_YEAR
    start_year = max(min_year, base_year)
    if start_year > current_year:
        start_year = max(min_year, current_year - FINANCE_YEAR_SPAN + 1)
    end_year = min(start_year + FINANCE_YEAR_SPAN - 1, current_year)
    if end_year - start_year < 1:
        start_year = max(min_year, end_year - FINANCE_YEAR_SPAN + 1)
    return start_year, end_year


def _build_finance_messages(user_prompt, start_year, end_year, quick_requests):
    preferred_assets = ', '.join(quick_requests) if quick_requests else ''
    quick_text = f"\n선호 비교 대상: {preferred_assets}" if preferred_assets else ''
    user_content = (
        f"사용자 요청: {user_prompt or '비트코인과 다른 자산의 연평균 수익률을 비교'}\n"
        f"데이터 구간: {start_year}년부터 {end_year}년까지 연 단위 연평균(연율환산) 수익률.\n"
        "항상 비트코인은 포함하고, 각 연도 말 기준의 누적 배수(시작 연도=1.0)와 연평균 수익률을 함께 제공하세요."
        f"{quick_text}\n"
        f"최대 {FINANCE_MAX_SERIES}개의 자산만 포함하고 의미 없는 자산은 제외하세요.\n"
        "multiple 값이 없으면 시작 연도 대비 배수를 계산해서 채우세요."
    )
    system_prompt = (
        "너는 한국어로 설명하는 재무 데이터 분석가이다. "
        "반드시 순수한 JSON만 반환하며 최상위 키는 series(필수), summary(필수), notes(선택)이다. "
        "series는 최대 10개의 객체 배열이고 각 객체는 {id, label, category, unit, benchmark, points}를 가진다. "
        "points는 연도별 데이터 배열이며 각 항목은 {\"year\": 2016, \"value\": 12.3, \"multiple\": 1.0, \"note\": \"\"} 형식을 따른다. "
        "value 필드는 해당 연도까지의 연평균 수익률(%)이고 multiple은 시작 연도 대비 누적 배수이다. "
        "JSON 외의 텍스트를 추가하지 말고, summary/notes는 간결한 한국어 문장으로 작성한다."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]


def _call_openai_finance(messages):
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OpenAI API 키가 설정되지 않았습니다.')
    base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.2,
                'top_p': 0.9,
                'response_format': {
                    'type': 'json_object'
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get('choices') or []
        if not choices or 'message' not in choices[0]:
            raise ValueError('OpenAI 응답에 message가 없습니다.')
        content = choices[0]['message'].get('content')
        if not content:
            raise ValueError('OpenAI 응답 본문이 비어 있습니다.')
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error('Failed to parse OpenAI response: %s', exc)
        raise
    except requests.HTTPError as exc:
        detail = ''
        if exc.response is not None:
            try:
                detail = exc.response.text
            except Exception:
                detail = ''
        logger.error('OpenAI request failed (%s): %s', getattr(exc.response, 'status_code', 'unknown'), detail)
        raise
    except requests.RequestException as exc:
        logger.error('OpenAI request failed: %s', exc)
        raise


def _normalize_finance_series(raw_series, start_year, end_year):
    normalized = []
    if not isinstance(raw_series, list):
        return normalized

    for idx, entry in enumerate(raw_series[:FINANCE_MAX_SERIES]):
        points = entry.get('points') if isinstance(entry, dict) else None
        if not isinstance(points, list):
            continue
        cleaned = []
        seen_years = set()
        base_value = None

        for point in points:
            year = point.get('year')
            if not isinstance(year, int):
                continue
            if year < start_year or year > end_year:
                continue
            if year in seen_years:
                continue
            seen_years.add(year)
            value = _safe_float(point.get('value'))
            multiple = _safe_float(point.get('multiple'))
            if base_value is None and value not in (None, 0):
                base_value = value
            cleaned.append({
                'year': year,
                'value': value,
                'multiple': multiple,
            })

        if len(cleaned) < 2:
            continue

        cleaned.sort(key=lambda p: p['year'])
        base_multiple = cleaned[0]['multiple']
        if base_multiple is None or base_multiple <= 0:
            base_multiple = 1.0
        if base_value in (None, 0):
            first_value = next((p['value'] for p in cleaned if p['value'] not in (None, 0)), 1.0)
            base_value = first_value or 1.0

        prev_multiple = 1.0
        rebased_points = []
        for p in cleaned:
            mul = p['multiple']
            if mul is None:
                if p['value'] is not None and base_value:
                    mul = p['value'] / base_value
                else:
                    mul = prev_multiple
            if mul is None or mul <= 0:
                mul = prev_multiple if prev_multiple > 0 else 1.0
            rebased = mul / base_multiple if base_multiple not in (0, 1.0) else mul
            rebased = max(rebased, 0.0001)
            rebased = round(float(rebased), 6)
            years_elapsed = p['year'] - cleaned[0]['year']
            if years_elapsed > 0:
                try:
                    annualized_pct = (rebased ** (1 / years_elapsed) - 1) * 100
                except Exception:
                    annualized_pct = 0.0
            else:
                annualized_pct = 0.0
            rebased_points.append({
                'year': p['year'],
                'multiple': rebased,
                'raw_value': p['value'],
                'value': round(annualized_pct, 3)
            })
            prev_multiple = rebased

        if len(rebased_points) < 2:
            continue

        start_val = rebased_points[0]['multiple']
        end_val = rebased_points[-1]['multiple']
        years = rebased_points[-1]['year'] - rebased_points[0]['year']
        annualized = 0.0
        if years > 0 and start_val > 0:
            try:
                annualized = (end_val / start_val) ** (1 / years) - 1
            except Exception:
                annualized = 0.0

        normalized.append({
            'id': entry.get('id') or entry.get('label') or f'series_{idx + 1}',
            'label': entry.get('label') or entry.get('id') or f'자산 {idx + 1}',
            'category': entry.get('category') or entry.get('benchmark') or '',
            'unit': entry.get('unit') or entry.get('currency') or 'USD',
            'points': rebased_points,
            'annualized_return_pct': round(annualized * 100, 2),
            'multiple_from_start': round(end_val / start_val, 3) if start_val else 0.0,
        })

    return normalized


@csrf_exempt
def finance_historical_returns_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    prompt = (payload.get('prompt') or '').strip()
    quick_requests = payload.get('quick_requests') or []
    if isinstance(quick_requests, str):
        quick_requests = [quick_requests]
    quick_requests = [str(q).strip() for q in quick_requests if str(q).strip()]

    start_hint = payload.get('start_year')
    try:
        start_hint = int(start_hint)
    except (TypeError, ValueError):
        start_hint = None

    prompt_year = _extract_start_year_from_prompt(prompt)
    start_year, end_year = _derive_finance_year_window(start_hint or prompt_year)
    debug_logs = []
    debug_logs.append(f"Prompt: {prompt or '기본 프롬프트'}")
    debug_logs.append(f"Quick requests: {', '.join(quick_requests) if quick_requests else '없음'}")
    debug_logs.append(f"Year window: {start_year}~{end_year}")

    safe_asset_keys = _detect_safe_assets(prompt, quick_requests)
    debug_logs.append(f"Detected safe assets: {', '.join(sorted(safe_asset_keys)) if safe_asset_keys else '없음'}")
    safe_series, safe_errors = _fetch_safe_asset_series(safe_asset_keys, start_year, end_year)
    if safe_series:
        debug_logs.append(f"Loaded safe asset series: {len(safe_series)}개")
    else:
        debug_logs.append("Loaded safe asset series: 없음")
    for err in safe_errors:
        debug_logs.append(f"Safe asset error: {err}")
    context_key = (payload.get('context_key') or '').strip()
    preset_series = []
    preset_errors = []
    if context_key == 'us_bigtech':
        preset_series, preset_errors = _fetch_preset_group('us_bigtech', start_year, end_year)
    elif context_key == 'kr_equity':
        preset_series, preset_errors = _fetch_preset_group('kr_equity', start_year, end_year)
    if context_key:
        debug_logs.append(f"Context key: {context_key} (series {len(preset_series)})")
    else:
        debug_logs.append("Context key: 없음")
    for err in preset_errors:
        debug_logs.append(f"Preset error: {err}")
    usd_krw_rate = get_cached_usdkrw_rate()

    if not prompt and not quick_requests:
        prompt = '비트코인과 대표 자산의 과거 연평균 수익률을 비교해줘.'

    try:
        messages = _build_finance_messages(prompt, start_year, end_year, quick_requests)
        llm_data = _call_openai_finance(messages)
        series = _normalize_finance_series(llm_data.get('series'), start_year, end_year)
        debug_logs.append(f"OpenAI series count: {len(series)}")
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except requests.RequestException:
        return JsonResponse({'ok': False, 'error': 'OpenAI API 호출에 실패했습니다.'}, status=502)
    except Exception as exc:
        logger.exception('finance_historical_returns_view error: %s', exc)
        return JsonResponse({'ok': False, 'error': '데이터 생성 중 오류가 발생했습니다.'}, status=500)

    if not series and not safe_series and not preset_series:
        return JsonResponse({'ok': False, 'error': 'LLM 데이터가 비어 있습니다.'}, status=502)

    # ID와 정규화된 label로 중복 체크
    def normalize_label(label):
        """종목코드와 괄호를 제거하고 핵심 이름만 추출"""
        import re
        # "삼성전자(005930)" -> "삼성전자"
        normalized = re.sub(r'\([^)]*\)', '', label).strip()
        # "삼성전자" -> "삼성전자"
        return normalized.lower()

    existing_ids = set()
    existing_normalized_labels = set()
    merged_series = []

    # Safe assets 추가
    for s in (safe_series or []):
        merged_series.append(s)
        existing_ids.add(s['id'])
        existing_normalized_labels.add(normalize_label(s['label']))

    # Preset series 추가 (중복 체크)
    if preset_series:
        for ps in preset_series:
            ps_id = ps['id']
            ps_norm_label = normalize_label(ps['label'])
            if ps_id in existing_ids or ps_norm_label in existing_normalized_labels:
                continue
            merged_series.append(ps)
            existing_ids.add(ps_id)
            existing_normalized_labels.add(ps_norm_label)

    # OpenAI series 추가 (중복 체크)
    for item in series:
        item_id = item['id']
        item_norm_label = normalize_label(item['label'])
        if item_id in existing_ids or item_norm_label in existing_normalized_labels:
            continue
        merged_series.append(item)
        existing_ids.add(item_id)
        existing_normalized_labels.add(item_norm_label)

    base_notes = (llm_data or {}).get('notes', '')
    notes_parts = []
    if base_notes:
        notes_parts.append(base_notes)
    if safe_series:
        safe_labels = ', '.join(s['label'] for s in safe_series)
        notes_parts.append(f"{safe_labels} 데이터는 외부 시세 제공처(Stooq 등)의 월별 종가/수익률을 기반으로 계산했습니다.")
    if preset_series:
        preset_labels = ', '.join(s['label'] for s in preset_series)
        notes_parts.append(f"{preset_labels} 주가는 외부 시세 제공처(Stooq 등) 데이터를 활용해 연평균 수익률로 환산했습니다.")
    notes = ' '.join(notes_parts).strip()
    debug_logs.append(f"Final merged series: {len(merged_series)}")

    return JsonResponse({
        'ok': True,
        'series': merged_series,
        'start_year': start_year,
        'end_year': end_year,
        'summary': (llm_data or {}).get('summary', ''),
        'notes': notes,
        'fx_rate': usd_krw_rate,
        'logs': debug_logs,
        'prompt': prompt,
        'quick_requests': quick_requests,
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
