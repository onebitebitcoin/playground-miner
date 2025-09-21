import json
import time
import threading
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Block, Nickname, Mnemonic, ExchangeRate, WithdrawalFee, LightningService
from .broadcast import broadcaster


MAX_NONCE = 100000
DIFFICULTY_BASE = 5000

_guest_counter = 0
_guest_lock = threading.Lock()


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
        # Find an unassigned mnemonic
        mnemonic_obj = Mnemonic.objects.filter(is_assigned=False).first()
        if not mnemonic_obj:
            return JsonResponse({'ok': False, 'error': '사용 가능한 니모닉이 없습니다'}, status=200)

        # Mark as assigned
        mnemonic_obj.is_assigned = True
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

    import random

    # BIP39 word list sample (limited for demo)
    bip39_words = [
        'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
        'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
        'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
        'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
        'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'agent', 'agree',
        'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album', 'alcohol',
        'alert', 'alien', 'all', 'alley', 'allow', 'almost', 'alone', 'alpha',
        'already', 'also', 'alter', 'always', 'amateur', 'amazing', 'among', 'amount',
        'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle', 'angry', 'animal',
        'ankle', 'announce', 'annual', 'another', 'answer', 'antenna', 'antique', 'anxiety',
        'any', 'apart', 'apology', 'appear', 'apple', 'approve', 'april', 'arch',
        'arctic', 'area', 'arena', 'argue', 'arm', 'armed', 'armor', 'army',
        'around', 'arrange', 'arrest', 'arrive', 'arrow', 'art', 'article', 'artist',
        'artwork', 'ask', 'aspect', 'assault', 'asset', 'assist', 'assume', 'asthma',
        'athlete', 'atom', 'attack', 'attend', 'attitude', 'attract', 'auction', 'audit',
        'august', 'aunt', 'author', 'auto', 'autumn', 'average', 'avocado', 'avoid',
        'awake', 'aware', 'away', 'awesome', 'awful', 'awkward', 'axis', 'baby',
        'bachelor', 'bacon', 'badge', 'bag', 'balance', 'balcony', 'ball', 'bamboo',
        'banana', 'banner', 'bar', 'barely', 'bargain', 'barrel', 'base', 'basic',
        'basket', 'battle', 'beach', 'bean', 'beauty', 'because', 'become', 'beef',
        'before', 'begin', 'behave', 'behind', 'believe', 'below', 'belt', 'bench',
        'benefit', 'best', 'betray', 'better', 'between', 'beyond', 'bicycle', 'bid',
        'bike', 'bind', 'biology', 'bird', 'birth', 'bitter', 'black', 'blade',
        'blame', 'blanket', 'blast', 'bleak', 'bless', 'blind', 'blood', 'blossom',
        'blow', 'blue', 'blur', 'blush', 'board', 'boat', 'body', 'boil',
        'bomb', 'bone', 'bonus', 'book', 'boost', 'border', 'boring', 'borrow',
        'boss', 'bottom', 'bounce', 'box', 'boy', 'bracket', 'brain', 'brand',
        'brass', 'brave', 'bread', 'breeze', 'brick', 'bridge', 'brief', 'bright',
        'bring', 'brisk', 'broccoli', 'broken', 'bronze', 'broom', 'brother', 'brown',
        'brush', 'bubble', 'buddy', 'budget', 'buffalo', 'build', 'bulb', 'bulk',
        'bullet', 'bundle', 'bunker', 'burden', 'burger', 'burst', 'bus', 'business',
        'busy', 'butter', 'buyer', 'buzz', 'cabbage', 'cabin', 'cable', 'cactus'
    ]

    # Generate 12 random words
    mnemonic_words = random.sample(bip39_words, 12)
    mnemonic = ' '.join(mnemonic_words)

    return JsonResponse({
        'ok': True,
        'mnemonic': mnemonic
    })


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

    # Validate mnemonic (12 words)
    words = mnemonic.split()
    if len(words) != 12:
        return JsonResponse({'ok': False, 'error': 'Mnemonic must contain exactly 12 words'}, status=400)

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
