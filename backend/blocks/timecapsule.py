import json
import logging
import os
import time
from urllib.parse import urlparse

import requests
from bitcoinlib.transactions import Transaction
from django.core.cache import cache
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from mnemonic import Mnemonic as MnemonicValidator

from .api_helpers import _load_json_body, _parse_float, _parse_int
from .btc import (
    _normalize_mnemonic,
    calc_total_sats,
    derive_bip84_account_zpub,
    derive_bip84_addresses,
    derive_bip84_private_key,
    derive_master_fingerprint,
    fetch_blockstream_balances,
)
from .models import Mnemonic, TimeCapsule, TimeCapsuleBroadcastSetting

logger = logging.getLogger(__name__)

TIME_CAPSULE_MNEMONIC_USERNAME = 'timecapsule'
DUST_LIMIT = 294
OP_RETURN_MAX_BYTES = 220
MIN_TIME_CAPSULE_FEE_RATE = 0.5
TIME_CAPSULE_GAP_LIMIT = 20
TIME_CAPSULE_MAX_SCAN_ADDRESSES = 1000
TIME_CAPSULE_SCAN_BATCH_SIZE = 50

DEFAULT_BROADCAST_NODE = {
    'label': 'mempool.space',
    'host': 'https://mempool.space',
    'port': 443,
    'description': 'mempool.space에서 제공하는 공개 REST 풀노드 엔드포인트입니다.',
}

DEPRECATED_BROADCAST_HOSTS = {
    'https://blockstream.info',
    'blockstream.info',
    'https://coconutwallet.io',
    'coconutwallet.io',
    'https://nunchuk.io',
    'nunchuk.io',
    'https://mainnet.nunchuk.io',
    'mainnet.nunchuk.io',
}

RECOMMENDED_BROADCAST_NODES = [
    DEFAULT_BROADCAST_NODE,
]


def _get_block_explorer_base():
    """Return the base URL for explorer operations (UTXO lookup, broadcast, etc.)."""
    return (os.environ.get('BTC_EXPLORER_API') or 'https://blockstream.info/api').rstrip('/')


def _get_time_capsule_mnemonic():
    """Return the mnemonic reserved for admin time capsule operations."""
    mnemonic_obj = (
        Mnemonic.objects
        .filter(username=TIME_CAPSULE_MNEMONIC_USERNAME)
        .exclude(mnemonic__isnull=True)
        .exclude(mnemonic='')
        .order_by('-id')
        .first()
    )
    if mnemonic_obj:
        mnemonic_value = (mnemonic_obj.mnemonic or '').strip()
        if ' ' not in mnemonic_value:
            return None
    return mnemonic_obj


def _get_time_capsule_broadcast_setting():
    """Return the singleton broadcast setting row (creating it if needed)."""
    setting, _ = TimeCapsuleBroadcastSetting.objects.get_or_create(
        pk=1,
        defaults={
            'fullnode_host': DEFAULT_BROADCAST_NODE['host'],
            'fullnode_port': DEFAULT_BROADCAST_NODE['port'],
        }
    )
    normalized_host = (setting.fullnode_host or '').strip()
    if (
        not normalized_host
        or normalized_host in DEPRECATED_BROADCAST_HOSTS
        or not setting.fullnode_port
    ):
        setting.fullnode_host = DEFAULT_BROADCAST_NODE['host']
        setting.fullnode_port = DEFAULT_BROADCAST_NODE['port']
        setting.save(update_fields=['fullnode_host', 'fullnode_port', 'updated_at'])
    return setting


def _estimate_vbytes(num_inputs, num_outputs):
    """Rudimentary estimator for transaction weight in virtual bytes."""
    num_inputs = max(1, int(num_inputs))
    num_outputs = max(1, int(num_outputs))
    return 10 + num_inputs * 68 + num_outputs * 31


def _fetch_address_utxos(address, base_url=None, use_cache=True):
    """Fetch UTXOs for a single address via the configured explorer with caching."""
    cache_key = f'utxo:{address}'

    if use_cache:
        cached_utxos = cache.get(cache_key)
        if cached_utxos is not None:
            logger.debug('Cache HIT for address %s', address)
            return cached_utxos

    logger.debug('Cache MISS for address %s, fetching from API', address)

    base = (base_url or _get_block_explorer_base()).rstrip('/')
    url = f'{base}/address/{address}/utxo'

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.error('Timeout fetching UTXOs for %s', address)
        raise ValueError(f'주소 {address}의 UTXO 조회 시간이 초과되었습니다.')
    except requests.exceptions.RequestException as exc:
        logger.error('Failed to fetch UTXOs for %s: %s', address, exc)
        raise ValueError(f'주소 {address}의 UTXO를 가져올 수 없습니다.')

    utxos = []
    for item in data:
        txid = item.get('txid') or item.get('tx_hash') or ''
        if not txid:
            continue
        vout = item.get('vout')
        if vout is None:
            vout = item.get('output') or item.get('n') or 0
        utxos.append({
            'txid': txid,
            'vout': int(vout),
            'value': int(item.get('value') or 0),
            'status': item.get('status') or {},
        })

    if use_cache:
        cache.set(cache_key, utxos, timeout=30)

    return utxos


def _locate_time_capsule_address_path(mnemonic_obj, mnemonic_plain, target_address, account=0, scan_limit=200):
    """Return (change, index) tuple for a given address controlled by the mnemonic."""
    capsule = (
        TimeCapsule.objects
        .filter(bitcoin_address=target_address, mnemonic=mnemonic_obj)
        .only('address_index')
        .first()
    )
    if capsule and capsule.address_index is not None:
        return 0, int(capsule.address_index)

    normalized_target = (target_address or '').strip()
    if not normalized_target:
        return None, None

    scan_limit = max(1, int(scan_limit))
    for change in (0, 1):
        try:
            batch = derive_bip84_addresses(
                mnemonic_plain,
                account=account,
                change=change,
                start=0,
                count=scan_limit,
            )
        except Exception:
            break
        for idx, addr in enumerate(batch):
            if addr == normalized_target:
                return change, idx
    return None, None


def _build_op_return_script(memo_text):
    memo = (memo_text or '').strip()
    if not memo:
        raise ValueError('메모 내용을 입력하세요.')
    memo_bytes = memo.encode('utf-8')
    if len(memo_bytes) > OP_RETURN_MAX_BYTES:
        raise ValueError(f'메모는 최대 {OP_RETURN_MAX_BYTES}바이트까지 입력할 수 있습니다.')

    if len(memo_bytes) <= 75:
        return b'\x6a' + bytes([len(memo_bytes)]) + memo_bytes
    return b'\x6a\x4c' + bytes([len(memo_bytes)]) + memo_bytes


def _build_time_capsule_transaction(
    mnemonic_obj,
    mnemonic_plain,
    *,
    to_address,
    amount_sats,
    fee_rate,
    account=0,
    from_address='',
    scan_limit=50,
    memo_text='',
):
    to_address = (to_address or '').strip()
    if not to_address:
        raise ValueError('받는 주소를 입력하세요.')
    if amount_sats <= 0:
        raise ValueError('양수 금액을 입력하세요.')
    if fee_rate is None or fee_rate < MIN_TIME_CAPSULE_FEE_RATE:
        raise ValueError(f'수수료율은 최소 {MIN_TIME_CAPSULE_FEE_RATE} sats/vB 이상이어야 합니다.')
    memo_text = (memo_text or '').strip()

    candidate_utxos = []
    if from_address:
        change_chain, address_index = _locate_time_capsule_address_path(
            mnemonic_obj, mnemonic_plain, from_address, account=account
        )
        if address_index is None:
            raise ValueError('니모닉에서 해당 주소를 찾을 수 없습니다.')
        utxos = _fetch_address_utxos(from_address)
        for utxo in utxos:
            value = int(utxo.get('value') or 0)
            if value <= 0:
                continue
            candidate_utxos.append({
                'txid': utxo['txid'],
                'vout': int(utxo['vout']),
                'value': value,
                'address': from_address,
                'change': change_chain or 0,
                'index': address_index,
            })
    else:
        scan_limit = max(1, min(int(scan_limit), 200))
        for change_chain in (0, 1):
            try:
                addresses = derive_bip84_addresses(
                    mnemonic_plain,
                    account=account,
                    change=change_chain,
                    start=0,
                    count=scan_limit,
                )
            except Exception as exc:
                logger.error('Failed to derive addresses for change=%s: %s', change_chain, exc)
                continue

            for idx, address in enumerate(addresses):
                normalized = address.strip()
                if not normalized:
                    continue
                try:
                    utxos = _fetch_address_utxos(normalized)
                except Exception as exc:
                    logger.warning('Failed to fetch UTXOs for derived address %s: %s', normalized, exc)
                    continue
                if not utxos:
                    continue
                for utxo in utxos:
                    value = int(utxo.get('value') or 0)
                    if value <= 0:
                        continue
                    candidate_utxos.append({
                        'txid': utxo['txid'],
                        'vout': int(utxo['vout']),
                        'value': value,
                        'address': normalized,
                        'change': change_chain,
                        'index': idx,
                    })

    if not candidate_utxos:
        raise ValueError('사용 가능한 주소의 UTXO가 없습니다.')

    candidate_utxos.sort(key=lambda x: x['value'])
    selected = []
    total_in = 0
    for utxo in candidate_utxos:
        selected.append(utxo)
        total_in += utxo['value']
        est_fee = fee_rate * _estimate_vbytes(len(selected), 2)
        if total_in >= amount_sats + est_fee:
            break

    est_needed_fee = fee_rate * _estimate_vbytes(len(selected) or 1, 2)
    if total_in < amount_sats + est_needed_fee:
        raise ValueError('잔액이 부족합니다. (수수료 포함)')

    key_cache = {}
    tx = Transaction(network='bitcoin')
    for utxo in selected:
        cache_key = f"{utxo['change']}:{utxo['index']}"
        if cache_key not in key_cache:
            key_cache[cache_key] = derive_bip84_private_key(
                mnemonic_plain,
                account=account,
                change=utxo['change'] or 0,
                index=utxo['index'],
            )
        tx.add_input(
            bytes.fromhex(utxo['txid']),
            int(utxo['vout']),
            keys=[key_cache[cache_key]],
            value=int(utxo['value']),
            address=utxo['address'],
            script_type='sig_pubkey',
            witness_type='segwit',
        )

    tx.add_output(int(amount_sats), to_address)
    memo_output_index = None
    if memo_text:
        memo_output_index = tx.add_output(0, lock_script=_build_op_return_script(memo_text))
    provisional_change = total_in - amount_sats
    change_output_index = None
    change_address = selected[0]['address']
    if provisional_change > 0:
        change_output_index = tx.add_output(int(provisional_change), change_address, change=True)

    base_outputs = 1 + (1 if memo_output_index is not None else 0)
    num_outputs = base_outputs + (1 if change_output_index is not None else 0)
    estimated_size = _estimate_vbytes(len(selected), num_outputs)
    target_fee = fee_rate * estimated_size
    final_change = total_in - amount_sats - target_fee

    if final_change < 0:
        raise ValueError('잔액이 부족합니다. 수수료율을 낮춰주세요.')

    dust_burned_sats = 0
    if change_output_index is not None:
        if final_change <= 0:
            tx.outputs.pop(change_output_index)
            change_output_index = None
            num_outputs = base_outputs
        elif final_change < DUST_LIMIT:
            dust_burned_sats = int(final_change)
            tx.outputs.pop(change_output_index)
            change_output_index = None
            num_outputs = base_outputs
            final_change = 0
        else:
            tx.outputs[change_output_index].value = int(final_change)
    else:
        if final_change >= DUST_LIMIT:
            change_output_index = tx.add_output(int(final_change), change_address, change=True)
            num_outputs = base_outputs + 1
        elif final_change > 0:
            dust_burned_sats = int(final_change)
            final_change = 0

    tx.sign_and_update()
    tx.calc_weight_units()
    final_vsize = tx.vsize or _estimate_vbytes(len(selected), num_outputs)
    final_fee = total_in - sum(int(o.value) for o in tx.outputs)
    raw_tx = tx.raw_hex()

    outputs = []
    change_sats = 0
    for idx, out in enumerate(tx.outputs):
        if change_output_index == idx:
            change_sats = int(out.value)
        lock_script = getattr(out, 'lock_script', b'') or b''
        outputs.append({
            'address': out.address,
            'value': int(out.value),
            'is_change': change_output_index == idx,
            'is_memo': memo_output_index == idx or lock_script.startswith(b'\x6a'),
        })

    inputs_summary = [{
        'txid': utxo['txid'],
        'vout': utxo['vout'],
        'value': utxo['value'],
        'address': utxo['address'],
        'change': utxo['change'],
        'index': utxo['index'],
    } for utxo in selected]

    effective_fee_rate = fee_rate
    if final_vsize:
        effective_fee_rate = final_fee / final_vsize

    used_from_addresses = list(set(utxo['address'] for utxo in selected))
    primary_from_address = selected[0]['address'] if selected else ''

    metadata = {
        'inputs': inputs_summary,
        'outputs': outputs,
        'total_input_sats': total_in,
        'amount_sats': amount_sats,
        'change_sats': change_sats,
        'fee_sats': final_fee,
        'fee_rate_sats_vb': effective_fee_rate,
        'requested_fee_rate_sats_vb': fee_rate,
        'vsize': final_vsize,
        'raw_tx': raw_tx,
        'txid': tx.txid,
        'change_address': change_address if change_sats > 0 else '',
        'from_address': primary_from_address,
        'from_addresses': used_from_addresses,
        'dust_limit_sats': DUST_LIMIT,
        'dust_burned_sats': dust_burned_sats,
        'memo_text': memo_text,
    }

    return tx, metadata


@csrf_exempt
def admin_time_capsule_mnemonic_view(request):
    """Create or fetch the dedicated time capsule mnemonic."""
    if request.method == 'GET':
        mnemonic_obj = _get_time_capsule_mnemonic()
        if not mnemonic_obj:
            return JsonResponse({'ok': True, 'has_mnemonic': False})
        mnemonic_plain = mnemonic_obj.get_mnemonic()

        return JsonResponse({
            'ok': True,
            'has_mnemonic': True,
            'mnemonic_id': mnemonic_obj.id,
            'mnemonic': mnemonic_plain,
            'assigned_count': mnemonic_obj.time_capsules.count(),
            'next_address_index': int(mnemonic_obj.next_address_index or 0),
        })

    if request.method == 'POST':
        if _get_time_capsule_mnemonic():
            return JsonResponse({'ok': False, 'error': '이미 니모닉이 존재합니다.'}, status=400)
        try:
            generator = MnemonicValidator('english')
            mnemonic_plain = generator.generate(strength=128)
            mnemonic_obj = Mnemonic.objects.create(
                username=TIME_CAPSULE_MNEMONIC_USERNAME,
                mnemonic=mnemonic_plain,
                is_assigned=True,
                assigned_to='timecapsule',
                next_address_index=0,
            )
            return JsonResponse({
                'ok': True,
                'mnemonic_id': mnemonic_obj.id,
                'mnemonic': mnemonic_plain,
                'next_address_index': 0,
            })
        except Exception as exc:
            logger.error('Failed to generate time capsule mnemonic: %s', exc)
            return JsonResponse({'ok': False, 'error': '니모닉 생성에 실패했습니다.'}, status=500)

    if request.method in ('PUT', 'PATCH'):
        mnemonic_obj = _get_time_capsule_mnemonic()
        if not mnemonic_obj:
            return JsonResponse({'ok': False, 'error': '수정할 니모닉이 존재하지 않습니다.'}, status=404)

        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': '잘못된 JSON 데이터입니다.'}, status=400)

        new_mnemonic = (payload.get('mnemonic') or '').strip()
        if not new_mnemonic:
            return JsonResponse({'ok': False, 'error': '니모닉을 입력하세요.'}, status=400)

        try:
            normalized = _normalize_mnemonic(new_mnemonic)
            validator = MnemonicValidator('english')
            words = normalized.split()
            if len(words) not in (12, 15, 18, 21, 24):
                return JsonResponse({'ok': False, 'error': '유효한 단어 수의 니모닉을 입력하세요.'}, status=400)
            if not validator.check(normalized):
                return JsonResponse({'ok': False, 'error': '유효하지 않은 BIP39 니모닉입니다.'}, status=400)
        except Exception as exc:
            logger.error('Failed to validate updated mnemonic: %s', exc)
            return JsonResponse({'ok': False, 'error': '니모닉 검증에 실패했습니다.'}, status=400)

        update_fields = ['mnemonic']
        mnemonic_obj.mnemonic = normalized

        if payload.get('reset_address_index'):
            mnemonic_obj.next_address_index = 0
            update_fields.append('next_address_index')
        elif 'next_address_index' in payload:
            try:
                next_index = max(0, int(payload.get('next_address_index')))
            except (TypeError, ValueError):
                next_index = None
            if next_index is not None:
                mnemonic_obj.next_address_index = next_index
                update_fields.append('next_address_index')

        mnemonic_obj.save(update_fields=update_fields)

        return JsonResponse({
            'ok': True,
            'mnemonic_id': mnemonic_obj.id,
            'mnemonic': mnemonic_obj.get_mnemonic(),
            'has_mnemonic': True,
            'assigned_count': mnemonic_obj.time_capsules.count(),
            'next_address_index': int(mnemonic_obj.next_address_index or 0),
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_time_capsule_build_transaction_view(request):
    """Build a transaction and return details without broadcasting."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request) or {}
    to_address = (payload.get('to_address') or '').strip()
    amount_sats = _parse_int(payload.get('amount_sats'))
    fee_rate = _parse_float(payload.get('fee_rate_sats_vb'))
    account = max(0, _parse_int(payload.get('account'), 0) or 0)
    from_address = (payload.get('from_address') or '').strip()
    memo_text = (payload.get('memo_text') or '').strip()

    logger.info('Building TX: to=%s..., from=%s, amount=%s', to_address[:10], from_address[:10] if from_address else 'auto', amount_sats)

    mnemonic_obj = _get_time_capsule_mnemonic()
    if not mnemonic_obj:
        return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 없습니다.'}, status=404)

    try:
        mnemonic_plain = mnemonic_obj.get_mnemonic()
    except Exception as exc:
        logger.error('Failed to load mnemonic: %s', exc)
        return JsonResponse({'ok': False, 'error': '니모닉을 불러오지 못했습니다.'}, status=500)

    start_time = time.time()
    try:
        _, details = _build_time_capsule_transaction(
            mnemonic_obj,
            mnemonic_plain,
            to_address=to_address,
            amount_sats=amount_sats,
            fee_rate=fee_rate,
            account=account,
            from_address=from_address,
            memo_text=memo_text,
        )

        elapsed = time.time() - start_time
        logger.info('Build TX SUCCESS in %.2fs: fee=%s sats, vsize=%s vB', elapsed, details.get('fee_sats'), details.get('vsize'))

        return JsonResponse({'ok': True, **details})

    except ValueError as exc:
        elapsed = time.time() - start_time
        logger.warning('Build TX FAILED (ValueError) in %.2fs: %s', elapsed, exc)
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error('Build TX FAILED (Exception) in %.2fs: %s', elapsed, exc, exc_info=True)
        return JsonResponse({'ok': False, 'error': '트랜잭션 생성에 실패했습니다.'}, status=500)


@csrf_exempt
def admin_time_capsule_broadcast_settings_view(request):
    """Manage full node connection info used for time capsule broadcasting."""
    setting = _get_time_capsule_broadcast_setting()

    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'settings': setting.as_dict(),
            'recommended_nodes': RECOMMENDED_BROADCAST_NODES,
        })

    if request.method not in ['POST', 'PUT', 'PATCH']:
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    host = (payload.get('fullnode_host') or '').strip()
    port = payload.get('fullnode_port')

    stored_value, hostname, scheme, normalized_port = _parse_broadcast_target(host, port)

    if not hostname:
        return JsonResponse({'ok': False, 'error': '풀노드 IP 또는 호스트를 입력하세요.'}, status=400)
    if normalized_port is None or normalized_port <= 0 or normalized_port > 65535:
        return JsonResponse({'ok': False, 'error': '유효한 포트 번호를 입력하세요.'}, status=400)

    setting.fullnode_host = stored_value
    setting.fullnode_port = normalized_port
    setting.save(update_fields=['fullnode_host', 'fullnode_port', 'updated_at'])

    return JsonResponse({
        'ok': True,
        'settings': setting.as_dict(),
        'recommended_nodes': RECOMMENDED_BROADCAST_NODES,
        'scheme': scheme,
    })


@csrf_exempt
def admin_time_capsule_broadcast_test_view(request):
    """Test connectivity to the configured Bitcoin node via REST chain info."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request) or {}
    setting = _get_time_capsule_broadcast_setting()
    host = (payload.get('fullnode_host') or setting.fullnode_host or '').strip()
    port = payload.get('fullnode_port') or setting.fullnode_port

    _, hostname, scheme, normalized_port = _parse_broadcast_target(host, port)

    if not hostname or not normalized_port:
        logger.warning('Broadcast test rejected due to missing host/port (host=%s, port=%s)', host, port)
        return JsonResponse({'ok': False, 'error': '먼저 풀노드 IP와 포트를 설정하세요.'}, status=400)

    if normalized_port <= 0 or normalized_port > 65535:
        logger.warning('Broadcast test rejected due to invalid port: %s', normalized_port)
        return JsonResponse({'ok': False, 'error': '유효한 포트 번호를 입력하세요.'}, status=400)

    url = f"{scheme}://{hostname}:{normalized_port}/rest/chaininfo.json"
    logger.info('Attempting time capsule broadcast test via %s', url)
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        info = resp.json()
        height = info.get('blocks') or info.get('headers')
        logger.info('Broadcast test succeeded for %s (height=%s chain=%s)', url, height, info.get('chain'))
        return JsonResponse({
            'ok': True,
            'block_height': height,
            'chain': info.get('chain', ''),
            'raw': info,
        })
    except Exception as exc:
        logger.exception('Failed to reach time capsule full node at %s', url)
        return JsonResponse({'ok': False, 'error': f'연결 실패: {exc}'}, status=502)


@csrf_exempt
def admin_time_capsule_xpub_view(request):
    """Expose the BIP84 account xpub (zpub) for the time capsule mnemonic."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    mnemonic_obj = _get_time_capsule_mnemonic()
    if not mnemonic_obj:
        return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 없습니다.'}, status=404)

    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0

    try:
        mnemonic_plain = mnemonic_obj.get_mnemonic()
    except Exception as exc:
        logger.error('Failed to read time capsule mnemonic for xpub: %s', exc)
        return JsonResponse({'ok': False, 'error': '니모닉을 읽지 못했습니다.'}, status=500)

    try:
        zpub = derive_bip84_account_zpub(mnemonic_plain, account=account)
        try:
            master_fingerprint = derive_master_fingerprint(mnemonic_plain)
        except Exception:
            master_fingerprint = None
        return JsonResponse({
            'ok': True,
            'mnemonic_id': mnemonic_obj.id,
            'account': account,
            'xpub': zpub,
            'zpub': zpub,
            'master_fingerprint': master_fingerprint,
        })
    except Exception as exc:
        logger.error('Failed to derive time capsule xpub: %s', exc)
        return JsonResponse({'ok': False, 'error': 'xpub 생성에 실패했습니다.'}, status=500)


@csrf_exempt
def admin_time_capsule_xpub_balance_view(request):
    """Query explorer balances by deriving addresses from the time capsule xpub."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    mnemonic_obj = _get_time_capsule_mnemonic()
    if not mnemonic_obj:
        return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 없습니다.'}, status=404)

    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0
    include_mempool = str(request.GET.get('include_mempool', '1')).lower() in ('1', 'true', 'yes')
    both_chains = str(request.GET.get('both_chains', '1')).lower() in ('1', 'true', 'yes')
    assigned_capsules = list(
        TimeCapsule.objects.filter(mnemonic=mnemonic_obj).exclude(bitcoin_address='').values(
            'id', 'bitcoin_address', 'address_index', 'user_info'
        )
    )
    capsule_assignments = {
        c['bitcoin_address']: c
        for c in assigned_capsules
        if c.get('bitcoin_address')
    }
    try:
        mnemonic_plain = mnemonic_obj.get_mnemonic()
        zpub = derive_bip84_account_zpub(mnemonic_plain, account=account)
    except Exception as exc:
        logger.error('Failed to derive time capsule xpub for balance lookup: %s', exc)
        return JsonResponse({'ok': False, 'error': 'xpub 생성에 실패했습니다.'}, status=500)

    addresses = []
    address_set = set()
    by_address = {}
    scanned_counts = {0: 0, 1: 0}

    def add_address(addr):
        if addr in address_set:
            return False
        address_set.add(addr)
        addresses.append(addr)
        return True

    def scan_chain(change):
        idx = 0
        consecutive_empty = 0
        max_scan = TIME_CAPSULE_MAX_SCAN_ADDRESSES
        while idx < max_scan and consecutive_empty < TIME_CAPSULE_GAP_LIMIT:
            batch_count = min(TIME_CAPSULE_SCAN_BATCH_SIZE, max_scan - idx)
            try:
                derived = derive_bip84_addresses(
                    mnemonic_plain,
                    account=account,
                    change=change,
                    start=idx,
                    count=batch_count,
                )
            except Exception as exc:
                logger.error('Failed to derive addresses for change=%s: %s', change, exc)
                break
            idx += batch_count
            try:
                batch_balances = fetch_blockstream_balances(
                    derived,
                    include_mempool=include_mempool,
                )
            except Exception as exc:
                logger.error('Failed to fetch balances for derived addresses (change=%s): %s', change, exc)
                break

            for addr in derived:
                balance = int(batch_balances.get(addr) or 0)
                by_address[addr] = balance
                add_address(addr)
                scanned_counts[change] += 1
                if balance > 0:
                    consecutive_empty = 0
                else:
                    consecutive_empty += 1
            if consecutive_empty >= TIME_CAPSULE_GAP_LIMIT:
                break

    scan_chain(0)
    if both_chains:
        scan_chain(1)

    assigned_only_addresses = [
        addr for addr in capsule_assignments.keys()
        if addr and addr not in by_address
    ]
    if assigned_only_addresses:
        try:
            assigned_balances = fetch_blockstream_balances(
                assigned_only_addresses,
                include_mempool=include_mempool,
            )
        except Exception as exc:
            logger.error('Failed to fetch balances for assigned addresses: %s', exc)
            assigned_balances = {}
        for addr in assigned_only_addresses:
            balance = int(assigned_balances.get(addr) or 0)
            by_address[addr] = balance
            add_address(addr)

    total = calc_total_sats(by_address)

    address_details = []
    total_utxos = 0
    for addr in addresses:
        balance = int(by_address.get(addr) or 0)
        utxos = []
        if balance > 0:
            try:
                utxos = _fetch_address_utxos(addr)
            except Exception as exc:
                logger.warning('Failed to fetch UTXOs for %s: %s', addr, exc)
                utxos = []
        detail_utxos = []
        for item in utxos or []:
            try:
                detail_utxos.append({
                    'txid': item.get('txid'),
                    'vout': int(item.get('vout')),
                    'value': int(item.get('value') or 0),
                    'status': item.get('status') or {},
                })
            except Exception:
                continue
        total_utxos += len(detail_utxos)
        assigned = capsule_assignments.get(addr)
        address_details.append({
            'address': addr,
            'balance_sats': balance,
            'utxo_count': len(detail_utxos),
            'utxos': detail_utxos,
            'assigned_capsule_id': assigned['id'] if assigned else None,
            'assigned_user_info': assigned['user_info'] if assigned else '',
        })

    return JsonResponse({
        'ok': True,
        'xpub': zpub,
        'account': account,
        'balance_sats': max(0, total),
        'include_mempool': include_mempool,
        'both_chains': both_chains,
        'count_per_chain': scanned_counts,
        'address_count': len(addresses),
        'by_address': by_address,
        'address_details': address_details,
        'utxo_address_count': len(address_details),
        'total_utxo_count': total_utxos,
    })


@csrf_exempt
def admin_time_capsule_broadcast_transaction_view(request):
    """Construct and broadcast a transaction from the time capsule mnemonic."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request) or {}
    from_address = (payload.get('from_address') or '').strip()
    to_address = (payload.get('to_address') or '').strip()
    amount_sats = _parse_int(payload.get('amount_sats'))
    fee_rate = _parse_float(payload.get('fee_rate_sats_vb'))
    account = max(0, _parse_int(payload.get('account'), 0) or 0)
    raw_tx_payload = (payload.get('raw_tx') or '').strip()
    memo_text = (payload.get('memo_text') or '').strip()

    summary = {}
    tx = None
    if raw_tx_payload:
        try:
            tx = Transaction.parse_hex(raw_tx_payload, network='bitcoin')
            tx.calc_weight_units()
            summary = {
                'raw_tx': raw_tx_payload,
                'txid': tx.txid,
                'fee_sats': payload.get('fee_sats'),
                'fee_rate_sats_vb': fee_rate or payload.get('fee_rate_sats_vb'),
                'vsize': tx.vsize,
            }
        except Exception as exc:
            logger.error('Failed to parse provided raw transaction: %s', exc)
            return JsonResponse({'ok': False, 'error': '유효한 raw 트랜잭션이 아닙니다.'}, status=400)
    else:
        mnemonic_obj = _get_time_capsule_mnemonic()
        if not mnemonic_obj:
            return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 없습니다.'}, status=404)
        try:
            mnemonic_plain = mnemonic_obj.get_mnemonic()
        except Exception:
            return JsonResponse({'ok': False, 'error': '니모닉을 불러오지 못했습니다.'}, status=500)
        try:
            tx, summary = _build_time_capsule_transaction(
                mnemonic_obj,
                mnemonic_plain,
                to_address=to_address,
                amount_sats=amount_sats,
                fee_rate=fee_rate,
                account=account,
                from_address=from_address,
                memo_text=memo_text,
            )
        except ValueError as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
        except Exception as exc:
            logger.error('Failed to build transaction for broadcast: %s', exc)
            return JsonResponse({'ok': False, 'error': '트랜잭션 생성에 실패했습니다.'}, status=500)

    setting = _get_time_capsule_broadcast_setting()
    _, hostname, scheme, normalized_port = _parse_broadcast_target(
        setting.fullnode_host, setting.fullnode_port
    )
    broadcast_url = f"{scheme}://{hostname}:{normalized_port}/api/tx"
    try:
        resp = requests.post(
            broadcast_url,
            data=summary['raw_tx'],
            timeout=10,
            headers={'Content-Type': 'text/plain'},
        )
        resp.raise_for_status()
        broadcast_result = resp.text.strip()
    except Exception as exc:
        logger.error('Time capsule transaction broadcast failed via %s: %s', broadcast_url, exc)
        return JsonResponse({'ok': False, 'error': f'트랜잭션 전파에 실패했습니다. ({exc})'}, status=502)

    return JsonResponse({
        'ok': True,
        'txid': summary.get('txid'),
        'raw_tx': summary.get('raw_tx'),
        'fee_sats': summary.get('fee_sats'),
        'fee_rate_sats_vb': summary.get('fee_rate_sats_vb'),
        'vsize': summary.get('vsize'),
        'inputs': summary.get('inputs', []),
        'outputs': summary.get('outputs', []),
        'broadcast_url': broadcast_url,
        'broadcast_response': broadcast_result or summary.get('txid'),
    })


@csrf_exempt
def admin_time_capsule_fee_estimates_view(request):
    """Fetch current fee estimates from mempool.space."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    try:
        resp = requests.get('https://mempool.space/api/v1/fees/recommended', timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return JsonResponse({'ok': True, 'fees': data})
    except Exception as exc:
        logger.error('Failed to fetch mempool.space fees: %s', exc)
        return JsonResponse({'ok': False, 'error': '수수료 정보를 가져오지 못했습니다.'}, status=502)


@csrf_exempt
def admin_time_capsule_assign_address_view(request, pk):
    """Assign the next unused native SegWit address to a time capsule entry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    mnemonic_obj = _get_time_capsule_mnemonic()
    if not mnemonic_obj:
        return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 생성되지 않았습니다.'}, status=400)

    try:
        account = max(0, int(request.GET.get('account', '0')))
    except Exception:
        account = 0

    payload = _load_json_body(request) or {}
    preferred_address = (payload.get('address') or payload.get('preferred_address') or '').strip()

    try:
        with transaction.atomic():
            mnemonic_locked = Mnemonic.objects.select_for_update().get(pk=mnemonic_obj.pk)
            capsule = TimeCapsule.objects.select_for_update().get(pk=pk)

            if capsule.bitcoin_address:
                return JsonResponse({
                    'ok': True,
                    'address': capsule.bitcoin_address,
                    'already_assigned': True,
                    'capsule': capsule.as_dict(),
                })

            mnemonic_plain = mnemonic_locked.get_mnemonic()
            next_index = int(mnemonic_locked.next_address_index or 0)
            address = ''
            address_index = None

            if preferred_address:
                change_chain, derived_index = _locate_time_capsule_address_path(
                    mnemonic_locked,
                    mnemonic_plain,
                    preferred_address,
                    account=account,
                )
                if derived_index is None:
                    return JsonResponse({'ok': False, 'error': '니모닉에서 찾을 수 없는 주소입니다.'}, status=400)
                if change_chain not in (0, None):
                    return JsonResponse({'ok': False, 'error': '외부 체인 주소만 할당할 수 있습니다.'}, status=400)
                if TimeCapsule.objects.filter(bitcoin_address=preferred_address).exclude(pk=capsule.pk).exists():
                    return JsonResponse({'ok': False, 'error': '이미 다른 타임캡슐에 할당된 주소입니다.'}, status=400)
                address = preferred_address
                address_index = derived_index
                next_index = max(next_index, derived_index + 1)
            else:
                try:
                    address = derive_bip84_addresses(mnemonic_plain, change=0, start=next_index, count=1)[0]
                except Exception as exc:
                    logger.error('Failed to derive time capsule address: %s', exc)
                    raise
                address_index = next_index
                next_index += 1

            capsule.bitcoin_address = address
            capsule.mnemonic = mnemonic_locked
            capsule.address_index = address_index
            capsule.save(update_fields=['bitcoin_address', 'mnemonic', 'address_index'])

            mnemonic_locked.next_address_index = next_index
            mnemonic_locked.save(update_fields=['next_address_index'])

            return JsonResponse({
                'ok': True,
                'address': address,
                'address_index': address_index,
                'used_preferred_address': bool(preferred_address),
                'capsule': capsule.as_dict(),
            })
    except TimeCapsule.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '타임캡슐을 찾을 수 없습니다.'}, status=404)
    except Exception as exc:
        logger.error('Failed to assign bitcoin address to capsule %s: %s', pk, exc)
        return JsonResponse({'ok': False, 'error': '주소 할당에 실패했습니다.'}, status=500)


@csrf_exempt
def admin_time_capsule_unassign_address_view(request, pk):
    """Clear the assigned bitcoin address from a time capsule entry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        with transaction.atomic():
            capsule = TimeCapsule.objects.select_for_update().get(pk=pk)
            if not capsule.bitcoin_address and not capsule.mnemonic_id:
                return JsonResponse({
                    'ok': True,
                    'already_unassigned': True,
                    'capsule': capsule.as_dict(),
                })

            capsule.bitcoin_address = ''
            capsule.mnemonic = None
            capsule.address_index = None
            capsule.save(update_fields=['bitcoin_address', 'mnemonic', 'address_index'])

            return JsonResponse({
                'ok': True,
                'capsule': capsule.as_dict(),
            })
    except TimeCapsule.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '타임캡슐을 찾을 수 없습니다.'}, status=404)
    except Exception as exc:
        logger.error('Failed to unassign bitcoin address from capsule %s: %s', pk, exc)
        return JsonResponse({'ok': False, 'error': '주소 할당 해제에 실패했습니다.'}, status=500)


@csrf_exempt
def time_capsule_save_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        encrypted_message = data.get('encrypted_message')
        user_info = data.get('user_info', '')

        if not encrypted_message:
            return JsonResponse({'error': 'encrypted_message is required'}, status=400)

        capsule = TimeCapsule.objects.create(
            encrypted_message=encrypted_message,
            bitcoin_address='',
            user_info=user_info
        )

        return JsonResponse(capsule.as_dict())
    except Exception as exc:
        logger.error('Error saving time capsule: %s', exc)
        return JsonResponse({'error': str(exc)}, status=500)


@csrf_exempt
def admin_time_capsules_view(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    capsules = TimeCapsule.objects.all().order_by('-created_at')

    page_number = request.GET.get('page')
    if page_number:
        paginator = Paginator(capsules, 20)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {
            'results': [c.as_dict() for c in page_obj],
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        return JsonResponse(data)

    return JsonResponse([c.as_dict() for c in capsules], safe=False)


@csrf_exempt
def admin_time_capsule_update_coupon_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        capsule = TimeCapsule.objects.get(pk=pk)
        data = json.loads(request.body)
        is_coupon_used = data.get('is_coupon_used')

        if is_coupon_used is not None:
            capsule.is_coupon_used = bool(is_coupon_used)
            capsule.save()

        return JsonResponse(capsule.as_dict())
    except TimeCapsule.DoesNotExist:
        return JsonResponse({'error': 'Time capsule not found'}, status=404)
    except Exception as exc:
        logger.error('Error updating time capsule: %s', exc)
        return JsonResponse({'error': str(exc)}, status=500)


@csrf_exempt
def admin_time_capsule_record_broadcast_view(request, pk):
    if request.method not in ['POST', 'PUT', 'PATCH']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    txid = (payload.get('txid') or '').strip()
    if not txid:
        return JsonResponse({'error': 'txid is required'}, status=400)

    try:
        capsule = TimeCapsule.objects.get(pk=pk)
    except TimeCapsule.DoesNotExist:
        return JsonResponse({'error': 'Time capsule not found'}, status=404)

    capsule.broadcast_txid = txid
    capsule.broadcasted_at = timezone.now()
    capsule.save(update_fields=['broadcast_txid', 'broadcasted_at'])

    return JsonResponse({'ok': True, 'capsule': capsule.as_dict()})


@csrf_exempt
def admin_time_capsule_delete_view(request, pk):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        capsule = TimeCapsule.objects.get(pk=pk)
        capsule_id = capsule.id
        capsule.delete()

        return JsonResponse({'ok': True, 'deleted_id': capsule_id})
    except TimeCapsule.DoesNotExist:
        return JsonResponse({'error': 'Time capsule not found'}, status=404)
    except Exception as exc:
        logger.error('Error deleting time capsule: %s', exc)
        return JsonResponse({'error': str(exc)}, status=500)


def _parse_broadcast_target(host, port):
    """Return sanitized storage value, hostname, scheme, and port."""
    raw_host = (host or '').strip()
    scheme = None
    hostname = raw_host
    normalized_port = None

    if raw_host.startswith(('http://', 'https://')):
        parsed = urlparse(raw_host)
        scheme = parsed.scheme or 'http'
        hostname = parsed.hostname or ''
        if parsed.port:
            normalized_port = parsed.port
    else:
        hostname = raw_host

    if port is not None and port != '':
        try:
            normalized_port = int(port)
        except (TypeError, ValueError):
            normalized_port = None

    if normalized_port is None:
        normalized_port = 443 if scheme == 'https' else 8332

    if scheme is None:
        scheme = 'https' if normalized_port == 443 else 'http'

    stored_value = raw_host
    if scheme == 'https' and not raw_host.startswith(('http://', 'https://')) and hostname:
        stored_value = f'https://{hostname}'
    elif scheme == 'http' and raw_host.startswith('https://') and hostname:
        stored_value = f'http://{hostname}'
    elif not stored_value:
        stored_value = hostname

    return stored_value, hostname, scheme, normalized_port
