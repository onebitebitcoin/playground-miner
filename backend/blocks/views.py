import csv
import io
import json
import logging
import re
import time
import threading
import hashlib
import uuid
import os
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse
from . import yahoo_finance
try:
    from pykrx import stock as pykrx_stock
except ImportError:  # pragma: no cover - optional dependency
    pykrx_stock = None
from django.db import transaction, OperationalError, ProgrammingError
from django.db.models import Max, Q
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Block,
    Nickname,
    Mnemonic,
    ExchangeRate,
    WithdrawalFee,
    LightningService,
    ServiceNode,
    Route,
    RoutingSnapshot,
    SidebarConfig,
    KingstoneWallet,
    FinanceQueryLog,
    FinanceQuickRequest,
    FinanceQuickCompareGroup,
    AssetPriceCache,
    CompatibilityAgentPrompt,
    CompatibilityAgentCache,
    CompatibilityAgentCache,
    CompatibilityQuickPreset,
    CompatibilityReportTemplate,
    TimeCapsule,
    TimeCapsuleBroadcastSetting,
)
from django.db import connection
from django.utils import timezone
from django.conf import settings
from .broadcast import broadcaster
from .finance_stream import finance_stream_manager
from .btc import (
    derive_bip84_addresses,
    fetch_blockstream_balances,
    calc_total_sats,
    derive_bip84_account_zpub,
    derive_master_fingerprint,
    _normalize_mnemonic,
    derive_bip84_private_key,
)
from mnemonic import Mnemonic as MnemonicValidator
from bitcoinlib.transactions import Transaction
from .prompts import (
    COMPATIBILITY_AGENT_DEFAULT_PROMPT,
    STORY_EXTRACTOR_AGENT_PROMPT,
    SAJU_AGENT_ANALYSIS_PROMPT,
    COMPATIBILITY_PAIR_AGENT_PROMPT,
    HIGHLIGHT_ANALYZER_PROMPT,
)

TIME_CAPSULE_MNEMONIC_USERNAME = 'timecapsule'
DUST_LIMIT = 294  # standard dust threshold for native segwit outputs (P2WPKH)
OP_RETURN_MAX_BYTES = 220  # Bitcoin Core allows up to 220 bytes for OP_RETURN (standard relay policy: 83 bytes, but most nodes accept more)
MIN_TIME_CAPSULE_FEE_RATE = 0.5
TIME_CAPSULE_GAP_LIMIT = 20
TIME_CAPSULE_MAX_SCAN_ADDRESSES = 1000
TIME_CAPSULE_SCAN_BATCH_SIZE = 50


def _get_block_explorer_base():
    """Return the base URL for explorer operations (UTXO lookup, broadcast, etc.)."""
    return (os.environ.get('BTC_EXPLORER_API') or 'https://blockstream.info/api').rstrip('/')


def _clean_cache_value(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_cache_profile(profile):
    if not isinstance(profile, dict):
        return ''
    name = _clean_cache_value(profile.get('name') or profile.get('label'))
    birthdate = _clean_cache_value(profile.get('birthdate') or profile.get('birth_date'))
    birth_time = _clean_cache_value(profile.get('birth_time') or profile.get('birthtime'))
    gender = _clean_cache_value(profile.get('gender'))
    zodiac = _clean_cache_value(profile.get('zodiac'))
    yin_yang = _clean_cache_value(profile.get('yin_yang') or profile.get('yinyang'))
    element = _clean_cache_value(profile.get('element'))
    return '|'.join([
        name.lower(),
        birthdate,
        birth_time or 'unknown',
        gender.lower(),
        zodiac.lower(),
        yin_yang.lower(),
        element.lower(),
    ])


def _resolve_cache_metadata(agent_key, cache_payload, context):
    if not cache_payload or not isinstance(cache_payload, dict) or not context:
        return None, None
    category = _clean_cache_value(cache_payload.get('category') or agent_key or 'compat')
    if not category:
        category = agent_key or 'compat'
    profile_signature = _normalize_cache_profile(cache_payload.get('profile'))
    target_signature = _normalize_cache_profile(cache_payload.get('target_profile'))
    scope = _clean_cache_value(
        cache_payload.get('scope')
        or cache_payload.get('role')
        or cache_payload.get('extra_scope')
        or (cache_payload.get('extra') or {}).get('scope')
    )
    base_components = [
        category.lower(),
        agent_key or '',
        profile_signature,
        target_signature,
        scope,
    ]
    context_hash = hashlib.sha256((context or '').encode('utf-8')).hexdigest()
    digest_source = '|'.join(filter(None, base_components + [context_hash]))
    cache_key = hashlib.sha256(digest_source.encode('utf-8')).hexdigest()
    cache_meta = {
        'cache_key': f"{category.lower()}:{cache_key}",
        'category': category,
        'profile_signature': profile_signature,
        'target_signature': target_signature,
        'context_hash': context_hash,
        'subject_name': _clean_cache_value((cache_payload.get('profile') or {}).get('name')),
        'target_name': _clean_cache_value((cache_payload.get('target_profile') or {}).get('name')),
        'payload': cache_payload,
    }
    try:
        cache_entry = CompatibilityAgentCache.objects.get(cache_key=cache_meta['cache_key'])
        cache_entry.hit_count += 1
        cache_entry.save(update_fields=['hit_count', 'updated_at'])
        return cache_meta, cache_entry
    except CompatibilityAgentCache.DoesNotExist:
        return cache_meta, None
    except (OperationalError, ProgrammingError):
        logger.warning('[Compatibility] Cache storage unavailable - skipping cache lookup')
        return None, None


def _store_cache_entry(agent_key, cache_meta, narrative, provider, model_used):
    if not cache_meta or not cache_meta.get('cache_key'):
        return
    try:
        metadata = {
            'provider': provider,
            'model': model_used,
            'context_hash': cache_meta.get('context_hash'),
        }
        CompatibilityAgentCache.objects.update_or_create(
            cache_key=cache_meta['cache_key'],
            defaults={
                'agent_key': agent_key,
                'category': cache_meta.get('category') or agent_key,
                'subject_name': cache_meta.get('subject_name', ''),
                'target_name': cache_meta.get('target_name', ''),
                'profile_signature': cache_meta.get('profile_signature', ''),
                'target_signature': cache_meta.get('target_signature', ''),
                'request_payload': cache_meta.get('payload') or {},
                'response_text': narrative,
                'metadata': metadata,
            }
        )
    except (OperationalError, ProgrammingError):
        logger.warning('[Compatibility] Cache storage unavailable - skipping cache save')


def _call_openai_chat_model(model_name, system_prompt, user_prompt, temperature=0.7, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0, max_tokens=None):
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OPENAI_API_KEY is not configured.')

    base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    resolved_model = model_name or getattr(settings, 'COMPATIBILITY_OPENAI_MODEL', getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'))

    # GPT-5 계열 모델은 Responses API 사용
    is_gpt5 = 'gpt-5' in resolved_model.lower()

    if is_gpt5:
        logger.info('[Compatibility][OpenAI] GPT-5 감지 - Responses API 사용 - model=%s', resolved_model)
    else:
        logger.info('[Compatibility][OpenAI] Chat Completions API 사용 - model=%s', resolved_model)

    try:
        if is_gpt5:
            # GPT-5: Responses API 사용
            # system_prompt와 user_prompt를 결합하여 input으로 전달
            combined_input = f"{system_prompt}\n\n{user_prompt}"

            # Responses API는 model과 input만 지원 (temperature, max_tokens 등 불지원)
            json_payload = {
                'model': resolved_model,
                'input': combined_input,
            }

            response = requests.post(
                f"{base_url}/responses",
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json=json_payload,
                timeout=90
            )
            response.raise_for_status()
            data = response.json()

            # Responses API 응답 형식 처리
            # 응답 구조: data['output'] 배열에서 type='message'인 항목의 content에서 text 추출
            if 'output' not in data:
                logger.error('[Compatibility][OpenAI][GPT-5] output 필드 없음: %s', data)
                raise ValueError('Responses API 응답에 output 필드가 없습니다.')

            # output 배열에서 message 타입 찾기
            message_output = None
            for item in data['output']:
                if item.get('type') == 'message':
                    message_output = item
                    break

            if not message_output:
                logger.error('[Compatibility][OpenAI][GPT-5] message 타입을 찾을 수 없음: %s', data)
                raise ValueError('Responses API 응답에서 message를 찾을 수 없습니다.')

            # content 배열에서 output_text 찾기
            content_text = None
            for content_item in message_output.get('content', []):
                if content_item.get('type') == 'output_text':
                    content_text = content_item.get('text', '')
                    break

            if content_text is None:
                logger.error('[Compatibility][OpenAI][GPT-5] output_text를 찾을 수 없음: %s', message_output)
                raise ValueError('Responses API 응답에서 텍스트를 찾을 수 없습니다.')

            actual_model = data.get('model', resolved_model)
            logger.info('[Compatibility][OpenAI][GPT-5] 응답 수신 - model=%s, tokens=%s', actual_model, data.get('usage'))
            return content_text.strip(), 'openai', actual_model
        else:
            # GPT-4 등 기존 모델: Chat Completions API 사용
            json_payload = {
                'model': resolved_model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': temperature,
                'top_p': top_p,
                'presence_penalty': presence_penalty,
                'frequency_penalty': frequency_penalty,
            }
            if max_tokens is not None:
                json_payload['max_tokens'] = max_tokens

            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json=json_payload,
                timeout=90
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get('choices') or []
            if not choices:
                logger.error('[Compatibility][OpenAI] 응답 choices 비어 있음: %s', data)
                raise ValueError('OpenAI 응답이 비어 있습니다.')
            logger.info('[Compatibility][OpenAI] 응답 수신 - tokens=%s', data.get('usage'))
            return choices[0]['message']['content'].strip(), 'openai', resolved_model
    except requests.HTTPError as exc:
        error_body = exc.response.text if exc.response else ''
        error_status = exc.response.status_code if exc.response else 'N/A'
        logger.exception('[Compatibility][OpenAI] HTTP 오류 status=%s body=%s', error_status, error_body)
        # 에러 메시지에 상세 정보 포함
        raise ValueError(f'OpenAI API 오류 ({error_status}): {error_body}') from exc
    except Exception:
        logger.exception('[Compatibility][OpenAI] 호출 실패')
        raise


def _call_gemini_chat_model(model_name, system_prompt, user_prompt, temperature=0.7, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0, max_tokens=None):
    """Call Google Gemini API for compatibility analysis."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise ValueError('GEMINI_API_KEY is not configured.')

    resolved_model = model_name or getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
    logger.info('[Compatibility][Gemini] 호출 준비 - model=%s', resolved_model)

    try:
        import google.generativeai as genai

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Initialize model
        model = genai.GenerativeModel(resolved_model)

        # Combine system prompt and user prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Generate content
        generation_config = {
            'temperature': temperature,
            'top_p': top_p,
        }
        if max_tokens is not None:
            generation_config['max_output_tokens'] = max_tokens
        
        # presence_penalty and frequency_penalty are not directly supported by Gemini's generation_config
        # and would require more complex mapping or safety settings.

        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )

        if not response.text:
            logger.error('[Compatibility][Gemini] 응답이 비어 있음')
            raise ValueError('Gemini 응답이 비어 있습니다.')

        logger.info('[Compatibility][Gemini] 응답 수신 - model=%s', resolved_model)
        return response.text.strip(), 'gemini', resolved_model

    except ImportError:
        logger.exception('[Compatibility][Gemini] google-generativeai 패키지가 설치되지 않음')
        raise ValueError('google-generativeai 패키지를 설치해야 합니다: pip install google-generativeai')
    except Exception as exc:
        logger.exception('[Compatibility][Gemini] 호출 실패: %s', str(exc))
        raise



MAX_NONCE = 100000
DIFFICULTY_BASE = 5000
KINGSTONE_WALLET_LIMIT = 3
FINANCE_DEFAULT_START_YEAR = 2015
FINANCE_YEAR_SPAN = 10
FINANCE_MAX_SERIES = 15
DIVIDEND_INFO_CACHE = {}
DIVIDEND_INFO_TTL = 3600  # seconds

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
        'label': '금 (GC=F)',
        'ticker': 'GC=F',
        'stooq_symbol': 'xauusd',
        'unit': 'USD',
        'category': '안전자산',
        'aliases': ['금', 'gold', '골드']
    },
    'us10y': {
        'label': '미국 10년물 국채 (^TNX)',
        'ticker': '^TNX',
        'stooq_symbol': None,  # Stooq doesn't have yield data, use Yahoo Finance only
        'unit': '%',
        'category': '채권',
        'aliases': ['미국 10년물 국채', '10년물 국채', 'us 10y', 'us10y', 'treasury', '미국 국채'],
        'yield_asset': True  # This is a yield (percentage), not a price
    },
    'silver': {
        'label': '은 (SI=F)',
        'ticker': 'SI=F',
        'stooq_symbol': 'xagusd',
        'unit': 'USD',
        'category': '안전자산',
        'aliases': ['은', 'silver']
    },
    'sp500': {
        'label': 'S&P 500 (^GSPC)',
        'ticker': '^GSPC',
        'stooq_symbol': 'spx',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['s&p 500', 'sp500', 's&p500', '에스앤피500']
    },
    'dow': {
        'label': '다우지수 (^DJI)',
        'ticker': '^DJI',
        'stooq_symbol': 'dji',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['다우', '다우지수', 'dow', 'dow jones']
    },
    'nasdaq100': {
        'label': '나스닥 100 (^NDX)',
        'ticker': '^NDX',
        'stooq_symbol': 'ndq',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['나스닥 100', '나스닥100', 'nasdaq 100', 'nasdaq100']
    },
    'kospi': {
        'label': '코스피 지수 (^KS11)',
        'ticker': '^KS11',
        'stooq_symbol': 'kospi',
        'unit': 'index',
        'category': '주식지수',
        'aliases': ['코스피', 'kospi', 'kospi composite', 'kospi composite index', '^ks11', 'ks11', '코스피 지수']
    },
    'soxx': {
        'label': 'iShares Semiconductor ETF (SOXX)',
        'ticker': 'SOXX',
        'stooq_symbol': 'soxx.us',
        'unit': 'USD',
        'category': 'ETF',
        'aliases': ['soxx', 'semiconductor etf', '반도체 etf', '아이셰어즈 반도체', 'ishares semiconductor']
    },
    'nvidia': {
        'label': '엔비디아 (NVDA)',
        'ticker': 'NVDA',
        'stooq_symbol': 'nvda.us',
        'unit': 'USD',
        'category': '미국 빅테크',
        'aliases': ['엔비디아', 'nvidia', 'nvda', '엔비디', 'nVIDIA']
    },
    'ief': {
        'label': 'iShares 7-10 Year Treasury Bond ETF (IEF)',
        'ticker': 'IEF',
        'stooq_symbol': 'ief.us',
        'unit': 'USD',
        'category': '채권 ETF',
        'aliases': ['ief', 'us 10y etf', '10년물 etf', '미국채 etf', '미국채 10년물', 'treasury etf']
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
    'cocacola': {
        'label': '코카콜라(KO)',
        'ticker': 'KO',
        'stooq_symbol': 'ko.us',
        'unit': 'USD',
        'category': '미국 소비재',
        'aliases': ['코카콜라', 'coca cola', 'coke', 'ko']
    },
    'berkshire_a': {
        'label': '버크셔해서웨이 클래스 A (BRK.A)',
        'ticker': 'BRK-A',
        'stooq_symbol': 'brk.a.us',
        'unit': 'USD',
        'category': '미국 주식',
        'aliases': [
            '버크셔해서웨이 클래스 a',
            '버크셔해서웨이 a',
            '버크셔 a',
            '버크셔해서웨이 inc a',
            '버크셔해서웨이 inc 클래스 a',
            'berkshire hathaway class a',
            'berkshire hathaway inc class a',
            'berkshire hathaway inc. class a',
            'berkshire hathaway inc a',
            'berkshire hathaway a',
            'berkshire hathaway inc class a shares',
            'brk.a',
            'brk-a'
        ]
    },
    'berkshire_b': {
        'label': '버크셔해서웨이 클래스 B (BRK.B)',
        'ticker': 'BRK-B',
        'stooq_symbol': 'brk.b.us',
        'unit': 'USD',
        'category': '미국 주식',
        'aliases': [
            '버크셔해서웨이',
            '버크셔해서웨이 클래스 b',
            '버크셔 b',
            '버크셔해서웨이 inc b',
            '버크셔해서웨이 inc 클래스 b',
            'berkshire hathaway',
            'berkshire hathaway class b',
            'berkshire hathaway inc class b',
            'berkshire hathaway inc. class b',
            'berkshire hathaway inc b',
            'brk.b',
            'brk-b'
        ]
    },
    'dxy': {
        'label': '달러지수(UUP)',
        'ticker': 'UUP',
        'stooq_symbol': 'uup.us',
        'unit': 'USD',
        'category': '통화',
        'aliases': ['달러지수', 'dxy', 'dollar index', '달러 인덱스']
    },
    'seoul_apartment': {
        'id': 'seoul_apartment',
        'label': '서울 아파트 평균 매매가격',
        'ticker': 'SEOUL_APT_KB',
        'stooq_symbol': None,
        'unit': 'KRW',
        'category': '부동산',
        'type': 'real_estate',
        'data_agent': 'seoul_apartment',
        'aliases': [
            '서울 아파트',
            '서울아파트',
            '서울 아파트 가격',
            '서울 지역 아파트',
            'seoul apartment',
            'seoul apt kb',
            'seoul_apt_kb',
            'seoul apt',
            'seoul_apartment',
            'seo ul apartment',
            'SEOUL_APT_KB'
        ]
    },
    'seoul_apartment_ltv50': {
        'id': 'seoul_apartment_ltv50',
        'label': '서울 아파트 (LTV 50%)',
        'ticker': 'SEOUL_APT_LTV50',
        'stooq_symbol': None,
        'unit': 'KRW',
        'category': '부동산',
        'type': 'real_estate',
        'base_asset_id': 'seoul_apartment',
        'ltv_ratio': 0.5,
        'allow_negative_prices': False,
        'aliases': [
            '서울 아파트 (LTV 50%)',
            '서울 아파트 LTV50',
            '서울 아파트 레버리지',
            '서울 아파트 ltv 50',
            '서울아파트 ltv50',
            '서울아파트 LTV 50%',
            'Seoul apartment LTV 50',
            'SEOUL_APT_LTV50'
        ]
    }
}

SAFE_ASSET_ALIASES = {}
for key, cfg in SAFE_ASSETS.items():
    for alias in cfg.get('aliases', []):
        SAFE_ASSET_ALIASES[alias.lower()] = key

DEFAULT_FINANCE_QUICK_REQUESTS = [
    {
        'label': '10년 전에 비트코인에 100만원 투자',
        'example': '10년 전에 비트코인에 100만원을 투자했다면 지금 얼마인지 알려주고, 비트코인과 S&P500, 나스닥100, 금, 은, 다우지수, 5년 전 시가총액 상위 5개 기업의 5년 전 대비 가격을 비교해줘',
        'quick_request': '비트코인에 100만원을 투자했다면 지금 얼마가 되었는지 계산해줘. 그리고 비트코인, S&P 500, 나스닥 100, 금, 은, 다우지수, 5년 전 시가총액 1~5위 기업들의 가격을 5년 전 대비 비교해줘. 각 자산의 5년 전과 현재 가격을 모두 가져와서 표로 정리해줘.',
        'context_key': 'safe_assets'
    }
]

DEFAULT_FINANCE_QUICK_COMPARE_GROUPS = [
    {
        'key': 'frequent',
        'label': '자주 찾는 종목',
        'sort_order': 0,
        'assets': [
            '서울 아파트',
            '서울 아파트 (LTV 50%)',
            '금',
            '미국 10년물 국채',
            'S&P 500',
            '코스피',
            '나스닥 100',
            '엔비디아',
            '코카콜라',
            '테슬라',
            '애플',
            '버크셔해서웨이',
        ],
    },
    {
        'key': 'us_bigtech',
        'label': '미국 빅테크',
        'sort_order': 10,
        'assets': ['애플', '엔비디아', '아마존', '메타', '구글', '마이크로소프트', '테슬라'],
    },
    {
        'key': 'kr_bluechips',
        'label': '국내 주요 주식',
        'sort_order': 20,
        'assets': ['삼성전자', 'SK 하이닉스', 'LG 에너지솔루션', '삼성 바이오로직스', '현대차', 'KB 금융', '카카오', '네이버'],
    },
    {
        'key': 'dividend_favorites',
        'label': '주요 배당주 TOP10',
        'sort_order': 99,
        'assets': [
            '삼성전자',
            'SK텔레콤',
            'KT&G',
            'KB 금융',
            '신한지주',
            '코카콜라',
            '프록터 앤 갬블',
            '존슨앤존슨',
            '맥도날드',
            'AT&T',
        ],
    },
]

SEOUL_APARTMENT_FALLBACK_DATA = [
    # Values aggregated from KB부동산 월간 KB주택가격동향 (세대당 평균 매매가격, KRW)
    {'year': 2010, 'avg_price_krw': 472_000_000},
    {'year': 2011, 'avg_price_krw': 478_000_000},
    {'year': 2012, 'avg_price_krw': 481_000_000},
    {'year': 2013, 'avg_price_krw': 505_000_000},
    {'year': 2014, 'avg_price_krw': 534_000_000},
    {'year': 2015, 'avg_price_krw': 575_000_000},
    {'year': 2016, 'avg_price_krw': 612_000_000},
    {'year': 2017, 'avg_price_krw': 667_000_000},
    {'year': 2018, 'avg_price_krw': 742_000_000},
    {'year': 2019, 'avg_price_krw': 826_000_000},
    {'year': 2020, 'avg_price_krw': 928_000_000},
    {'year': 2021, 'avg_price_krw': 1_082_000_000},
    {'year': 2022, 'avg_price_krw': 1_134_000_000},
    {'year': 2023, 'avg_price_krw': 1_072_000_000},
    {'year': 2024, 'avg_price_krw': 1_108_000_000},
]

_SEOUL_APARTMENT_HISTORY_CACHE = {}


def _ensure_default_finance_quick_requests():
    from .models import FinanceQuickRequest

    if FinanceQuickRequest.objects.exists():
        return False

    created = False
    for idx, entry in enumerate(DEFAULT_FINANCE_QUICK_REQUESTS):
        FinanceQuickRequest.objects.create(
            label=entry.get('label', f'요청 #{idx + 1}'),
            example=entry.get('example', ''),
            quick_request=entry.get('quick_request', ''),
            context_key=entry.get('context_key', ''),
            sort_order=idx
        )
        created = True

    return created


def _ensure_default_finance_quick_compare_groups():
    existing_keys = set(
        FinanceQuickCompareGroup.objects.values_list('key', flat=True)
    )
    created = False
    for idx, entry in enumerate(DEFAULT_FINANCE_QUICK_COMPARE_GROUPS):
        key = entry.get('key') or f'group_{idx + 1}'
        if key in existing_keys:
            continue

        assets = list(entry.get('assets') or [])
        resolved_assets = _resolve_assets(assets) if assets else []

        group = FinanceQuickCompareGroup.objects.create(
            key=key,
            label=entry.get('label', f'그룹 #{idx + 1}'),
            assets=assets,
            resolved_assets=resolved_assets,
            sort_order=entry.get('sort_order', idx),
            is_active=entry.get('is_active', True),
        )
        existing_keys.add(key)
        created = True

        # Warm cache entries for the default group immediately
        if resolved_assets:
            _ensure_assets_cached(resolved_assets, group_key=group.key)

    return created


def _ensure_assets_cached(resolved_assets, group_key=None):
    """
    Ensure a list of resolved asset dictionaries are persisted to the price cache.
    """
    for asset in resolved_assets or []:
        _ensure_asset_prices_cached(asset, group_key=group_key)


def _ensure_asset_prices_cached(asset, group_key=None):
    """
    Make sure a single asset has an entry inside AssetPriceCache.
    """
    try:
        asset_id = (asset.get('ticker') or asset.get('id') or '').strip()
        label = (asset.get('label') or asset_id).strip()
        category = asset.get('category')
        if not asset_id or not label:
            return False

        if AssetPriceCache.objects.filter(asset_id=asset_id).exists():
            return True

        return _cache_asset_prices(asset_id, label, category)
    except Exception as exc:
        logger.warning(
            "Failed to ensure cache for asset %s (group=%s): %s",
            asset.get('ticker') or asset.get('id'),
            group_key or 'n/a',
            exc
        )
        return False


def _ensure_quick_compare_groups_cached():
    """
    Ensure all quick compare groups have resolved assets and corresponding cache entries.
    """
    groups = FinanceQuickCompareGroup.objects.all()
    for group in groups:
        try:
            resolved_assets = list(group.resolved_assets or [])
            if not resolved_assets:
                asset_names = list(group.assets or [])
                if not asset_names:
                    continue
                resolved_assets = _resolve_assets(asset_names)
                group.resolved_assets = resolved_assets
                group.save(update_fields=['resolved_assets'])

            if resolved_assets:
                _ensure_assets_cached(resolved_assets, group_key=group.key)
        except Exception as exc:
            logger.warning("Failed to warm cache for quick compare group %s: %s", group.key, exc)
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

HISTORICAL_MARKET_CAP_GROUPS = [
    {
        'key': 'market_cap_top5_10y',
        'label': '2015년 글로벌 시가총액 Top 5',
        'match_phrases': ['10년 전', '10년전', '10년 전에', '2015년', '2014년'],
        'assets': [
            {'id': 'AAPL', 'label': '애플(AAPL)', 'type': 'us_stock', 'market_cap_usd': 750_000_000_000},
            {'id': 'MSFT', 'label': '마이크로소프트(MSFT)', 'type': 'us_stock', 'market_cap_usd': 340_000_000_000},
            {'id': 'GOOGL', 'label': '알파벳(GOOGL)', 'type': 'us_stock', 'market_cap_usd': 365_000_000_000},
            {'id': 'XOM', 'label': '엑슨모빌(XOM)', 'type': 'us_stock', 'market_cap_usd': 356_000_000_000},
            {'id': 'BRK.B', 'label': '버크셔해서웨이(BRK.B)', 'type': 'us_stock', 'market_cap_usd': 352_000_000_000},
        ],
    },
    {
        'key': 'market_cap_top5_5y',
        'label': '2020년 글로벌 시가총액 Top 5',
        'match_phrases': ['5년 전', '5년전', '5년 전에', '2020년', '2019년'],
        'assets': [
            {'id': 'AAPL', 'label': '애플(AAPL)', 'type': 'us_stock', 'market_cap_usd': 2_000_000_000_000},
            {'id': 'MSFT', 'label': '마이크로소프트(MSFT)', 'type': 'us_stock', 'market_cap_usd': 1_600_000_000_000},
            {'id': 'AMZN', 'label': '아마존(AMZN)', 'type': 'us_stock', 'market_cap_usd': 1_500_000_000_000},
            {'id': 'GOOGL', 'label': '알파벳(GOOGL)', 'type': 'us_stock', 'market_cap_usd': 1_200_000_000_000},
            {'id': 'META', 'label': '메타(META)', 'type': 'us_stock', 'market_cap_usd': 780_000_000_000},
        ],
    },
]

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
        # Save mnemonic directly (stored in plaintext for this project)
        mnemonic_obj = Mnemonic.objects.create(
            username=username,
            mnemonic=mnemonic,
            is_assigned=False
        )

        return JsonResponse({
            'ok': True,
            'id': mnemonic_obj.id,
            'message': 'Mnemonic이 저장되었습니다.'
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


def _parse_float(value, default=None):
    try:
        return float(value)
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
        count = max(1, min(int(request.GET.get('count', '1000')), 1000))
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

def _extract_username(request):
    """Best-effort extraction of username from query params, body, headers or cookies."""
    username = ''

    # Prefer explicit username in query/form params
    if request.method == 'GET':
        username = request.GET.get('username', '')
    else:
        username = request.POST.get('username', '')
        if not username:
            try:
                content_type = (request.META.get('CONTENT_TYPE') or '').lower()
                if 'application/json' in content_type:
                    if not hasattr(request, '_cached_body'):
                        request._cached_body = request.body
                    data = json.loads(request._cached_body.decode('utf-8') or '{}')
                    username = data.get('username', '')
            except Exception:
                username = ''

    # Allow custom headers for programmatic access
    if not username:
        username = request.META.get('HTTP_X_ADMIN_USERNAME', '') or request.META.get('HTTP_X_USERNAME', '')

    # Fall back to cookie
    if not username:
        username = request.COOKIES.get('username', '')

    return (username or '').strip()


def is_admin(request):
    """Check if user has admin privileges (supports JSON POST bodies and cookies)."""
    username = _extract_username(request)
    if username.lower() == 'admin':
        return True

    logger.warning(
        'Admin access denied for username=%s path=%s query=%s',
        username or '[empty]',
        request.path,
        request.META.get('QUERY_STRING', ''),
    )
    return False


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
                def ensure_route(source_node, destination_node, route_type, defaults):
                    if not source_node or not destination_node:
                        return
                    Route.objects.get_or_create(
                        source=source_node,
                        destination=destination_node,
                        route_type=route_type,
                        defaults=defaults,
                    )

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
                ensure_route(
                    bz_usdt,
                    bz_btc,
                    'trading',
                    {'fee_rate': 0.1, 'description': '바이낸스 USDT → 바이낸스 BTC', 'is_enabled': True},
                )
                ensure_route(
                    ok_usdt,
                    ok_btc,
                    'trading',
                    {'fee_rate': 0.1, 'description': 'OKX USDT → OKX BTC', 'is_enabled': True},
                )
                # Direct user -> exchange (splits) with trading fees
                special_user_pairs = []
                if up_usdt: special_user_pairs.append((user, up_usdt, 0.01, '사용자 → 업비트 USDT'))
                if up_btc:  special_user_pairs.append((user, up_btc,  0.05, '사용자 → 업비트 BTC'))
                if bi_usdt: special_user_pairs.append((user, bi_usdt, 0.04, '사용자 → 빗썸 USDT'))
                if bi_btc:  special_user_pairs.append((user, bi_btc,  0.04, '사용자 → 빗썸 BTC'))
                for (src, dst, fee_rate, desc) in special_user_pairs:
                    ensure_route(
                        src,
                        dst,
                        'trading',
                        {'fee_rate': fee_rate, 'description': desc, 'is_enabled': True},
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
                    ensure_route(
                        src,
                        dst,
                        'withdrawal_onchain',
                        {'fee_rate': None, 'fee_fixed': 0.0002, 'description': desc, 'is_enabled': True},
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

        # Fields for both create and update
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
        
        # Extract route_id for updates
        route_id = data.get('id')

        # Reject invalid user -> (binance|okx) paths
        if source.service == 'user' and destination.service in ['binance', 'okx']:
            return JsonResponse({'ok': False, 'error': '사용자에서 바로 바이낸스/OKX로 가는 경로는 유효하지 않습니다'}, status=400)

        # Reject invalid (upbit/bithumb) USDT -> (upbit/bithumb) BTC
        if source.service in ['upbit_usdt','bithumb_usdt'] and destination.service in ['upbit_btc','bithumb_btc']:
            return JsonResponse({'ok': False, 'error': 'USDT에서 동일 거래소 BTC로의 직접 전환 경로는 유효하지 않습니다'}, status=400)

        try:
            if route_id:
                # Update existing route by ID
                route = Route.objects.get(id=route_id)
                route.source = source
                route.destination = destination
                route.route_type = route_type
                route.fee_rate = fee_rate if fee_rate is not None else None
                route.fee_fixed = fee_fixed if fee_fixed is not None else None
                route.fee_fixed_currency = fee_fixed_currency
                route.is_enabled = bool(is_enabled)
                route.description = description
                route.is_event = bool(is_event)
                route.event_title = event_title
                route.event_description = event_description
                route.event_url = event_url
                route.save()
                created = False
            else:
                # Create new route using update_or_create (for cases where source, dest, route_type define uniqueness)
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

        except Route.DoesNotExist:
            return JsonResponse({'ok': False, 'error': f'라우트를 찾을 수 없습니다 (ID: {route_id})'}, status=404)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving route (ID: {route_id}, source: {source.service}, dest: {destination.service}): {e}")
            return JsonResponse({'ok': False, 'error': '라우트 저장 중 오류가 발생했습니다'}, status=500)

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

            if 'show_finance' not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN show_finance boolean DEFAULT false")
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
        'show_fee': True,
        'show_finance': False,
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
    if 'show_finance' in data:
        config.show_finance = bool(data['show_finance'])

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


def _build_fallback_seoul_apartment_history(start_year, end_year):
    """Return static KB average price data when the agent is unavailable."""
    target_year = max(end_year, datetime.utcnow().year)
    entries = []
    for item in SEOUL_APARTMENT_FALLBACK_DATA:
        year = item.get('year')
        price = _safe_float(item.get('avg_price_krw'))
        if year is None or price is None:
            continue
        try:
            year_int = int(year)
        except (TypeError, ValueError):
            continue
        if year_int < start_year or year_int > target_year:
            continue
        entries.append((datetime(year_int, 12, 31), price))
    entries.sort(key=lambda row: row[0])
    return _extend_history_to_year(entries, target_year)


def _extend_history_to_year(history, target_year):
    if not history:
        return history

    entries = list(history)
    entries.sort(key=lambda row: row[0])
    last_dt, last_price = entries[-1]
    if not isinstance(last_dt, datetime):
        return entries

    try:
        last_price_val = _safe_float(last_price)
    except Exception:
        last_price_val = None
    if last_price_val is None or last_price_val <= 0:
        return entries

    current_year = last_dt.year
    if target_year <= current_year:
        return entries

    for year in range(current_year + 1, target_year + 1):
        entries.append((datetime(year, 12, 31), last_price_val))

    return entries


def _call_seoul_apartment_data_agent(start_year, end_year):
    """Request structured Seoul apartment data from the price retriever agent."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        logger.info('[서울 아파트] OPENAI_API_KEY가 없어 Agent 호출을 건너뜁니다.')
        return [], None

    base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

    default_prompt = (
        "You are a data researcher that compiles verified South Korean real estate statistics. "
        "When asked for Seoul apartment prices, you must rely on KB부동산 리브온 (KB Housing Price Trend) "
        "or 한국부동산원 official releases. Return structured JSON, include evidence text, and never guess."
    )
    system_prompt = _get_agent_prompt('price_retriever', default_prompt)

    user_prompt = (
        f"서울특별시 아파트의 세대당 평균 매매가격을 {start_year}년부터 {end_year}년까지 연도별로 정리해 주세요.\n"
        "조건:\n"
        "1) KB부동산 리브온 KB주택가격동향 또는 한국부동산원 통계를 우선 사용하고 출처명을 source에 명시합니다.\n"
        "2) 각 연도 값은 해당 연도 12월(또는 연말) 기준 세대당 평균 매매가격이며 단위는 KRW 입니다.\n"
        "3) 금액에는 콤마/통화기호를 넣지 말고 숫자만 사용합니다 (예: 928000000).\n"
        "4) JSON만 반환하고 schema는 {\"source\": \"...\", \"unit\": \"KRW\", \"data\": [{\"year\": 2020, \"avg_price_krw\": 928000000, \"evidence\": \"자료명\"}] } 입니다.\n"
        "5) 요청된 연도 범위를 모두 포함하고, 사용할 수 없는 연도는 누락 이유를 evidence에 명시합니다."
    )

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
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.1,
                'max_tokens': 1200,
                'response_format': {'type': 'json_object'},
            },
            timeout=45
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get('choices') or []
        if not choices:
            raise RuntimeError('에이전트 응답이 비어 있습니다.')
        content = (choices[0]['message'] or {}).get('content', '').strip()
        if not content:
            raise RuntimeError('에이전트 응답을 파싱할 수 없습니다.')
        parsed = json.loads(content)
    except Exception as exc:
        raise RuntimeError(f'에이전트 호출 실패: {exc}') from exc

    rows = []
    for entry in parsed.get('data') or []:
        year = entry.get('year')
        price = (
            entry.get('avg_price_krw') or entry.get('average_price_krw') or
            entry.get('average_price') or entry.get('price_krw') or entry.get('price')
        )
        price_value = _safe_float(price)
        try:
            year_int = int(year)
        except (TypeError, ValueError):
            continue
        if price_value is None:
            continue
        if year_int < start_year or year_int > end_year:
            continue
        rows.append((datetime(year_int, 12, 31), price_value))

    rows.sort(key=lambda row: row[0])
    source_label = parsed.get('source') or 'KB부동산 (Agent)'
    if not rows:
        raise RuntimeError('에이전트가 유효한 연도별 데이터를 반환하지 않았습니다.')
    logger.info('[서울 아파트] Agent 데이터 %d개 수신 (source=%s)', len(rows), source_label)
    return rows, source_label


def _fetch_seoul_apartment_history(start_year, end_year):
    cache_key = (start_year, end_year)
    cached = _SEOUL_APARTMENT_HISTORY_CACHE.get(cache_key)
    if cached:
        return cached

    history = []
    source = 'KB부동산'
    target_year = max(end_year, datetime.utcnow().year)

    try:
        history, source = _call_seoul_apartment_data_agent(start_year, end_year)
    except Exception as exc:
        logger.warning('[서울 아파트] Agent 데이터를 가져오지 못했습니다: %s', exc)
        history = []

    if not history:
        history = _build_fallback_seoul_apartment_history(start_year, end_year)
        source = 'KB부동산 (정적)' if history else source
        if history:
            logger.info('[서울 아파트] Fallback KB 데이터를 사용합니다. (%d개)', len(history))

    history = _extend_history_to_year(history, target_year)

    if not history:
        raise RuntimeError('서울 아파트 평균 매매가격 데이터를 찾을 수 없습니다.')

    _SEOUL_APARTMENT_HISTORY_CACHE[cache_key] = (history, source)
    return history, source


def _build_ltv_equity_history(base_history, ltv_ratio):
    if not base_history:
        return []

    try:
        ratio = float(ltv_ratio)
    except (TypeError, ValueError):
        ratio = 0.5
    ratio = max(0.0, min(0.95, ratio))

    base_price = None
    loan_amount = None
    min_equity = 1.0
    adjusted = []
    for dt, raw_price in base_history:
        price_val = _safe_float(raw_price)
        if price_val is None or price_val <= 0:
            continue
        if base_price is None:
            base_price = price_val
            loan_amount = base_price * ratio
            min_equity = max(base_price * 0.001, 1.0)
        if loan_amount is None:
            continue
        equity_value = price_val - loan_amount
        if equity_value <= 0:
            equity_value = min_equity
        adjusted.append((dt, equity_value))

    return adjusted


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


def _fetch_yfinance_history(ticker, start_year, end_year, adjust_for_dividends=False):
    """Yahoo Finance 데이터를 yfinance 없이 직접 호출해 가져옵니다."""
    if not ticker:
        return []
    try:
        start_dt = datetime(start_year, 1, 1)
        end_dt = datetime(end_year, 12, 31)
        current_dt = datetime.utcnow()

        rows = yahoo_finance.fetch_price_history(
            ticker,
            start_dt,
            end_dt,
            interval='1mo',
            auto_adjust=adjust_for_dividends,
        )

        if not rows:
            return []

        if end_year == current_dt.year:
            last_dt = rows[-1][0]
            if last_dt.year < current_dt.year or last_dt.month < current_dt.month:
                current_month_start = datetime(current_dt.year, current_dt.month, 1)
                latest = yahoo_finance.fetch_latest_price_if_stale(
                    ticker,
                    start_dt=current_month_start,
                    end_dt=current_dt,
                    auto_adjust=adjust_for_dividends,
                )
                if latest:
                    rows.append(latest)
                    logger.info('[%s] 최신 일별 가격 추가: %s (%.2f)', ticker, latest[0].strftime('%Y-%m-%d'), latest[1])

        rows.sort(key=lambda item: item[0])
        log_suffix = ' (dividend-adjusted)' if adjust_for_dividends else ''
        logger.info('Yahoo Finance에서 %s 데이터 %d개 가져옴%s (%d-%d)', ticker, len(rows), log_suffix, start_year, end_year)
        return rows
    except Exception as exc:
        logger.warning('Yahoo Finance fetch failed for %s: %s', ticker, exc)
        raise


def _equity_like_asset(config):
    ticker = (config.get('ticker') or '').strip()
    if not ticker:
        return False
    upper = ticker.upper()
    if upper.startswith('^'):
        return False
    if '-' in upper or '=' in upper:
        return False
    category = (config.get('category') or '').lower()
    keywords = ['주식', 'etf', 'reit', '금융', '배당']
    if any(keyword in category for keyword in keywords):
        return True
    # Allow common Yahoo tickers such as BRK.B or Korean stocks (.KS/.KQ)
    normalized = upper.replace('.', '')
    if normalized.isalpha():
        return True
    if upper.endswith(('.KS', '.KQ', '.KL', '.US')):
        return True
    return False


def _cache_dividend_info(ticker, data):
    DIVIDEND_INFO_CACHE[ticker] = {
        'timestamp': time.time(),
        'data': data
    }


def _get_cached_dividend_info(ticker):
    record = DIVIDEND_INFO_CACHE.get(ticker)
    if not record:
        return False, None
    if time.time() - record['timestamp'] > DIVIDEND_INFO_TTL:
        return False, None
    return True, record['data']


def _fetch_dividend_profile(ticker):
    if not ticker:
        return None
    normalized = ticker.upper().strip()
    cached_hit, cached_data = _get_cached_dividend_info(normalized)
    if cached_hit:
        return cached_data

    yield_ratio = None
    try:
        yield_ratio = yahoo_finance.fetch_dividend_yield(normalized)

        if yield_ratio is None:
            _cache_dividend_info(normalized, None)
            return None

        if 0 < yield_ratio < 1:
            yield_pct = round(yield_ratio * 100, 2)
        else:
            yield_pct = round(float(yield_ratio), 2)

        profile = {
            'dividend_yield_pct': yield_pct,
            'dividend_yield_source': 'yfinance',
            'dividend_yield_updated_at': datetime.utcnow().strftime('%Y-%m-%d'),
            'is_dividend_stock': yield_pct > 0
        }
        _cache_dividend_info(normalized, profile)
        return profile
    except Exception as exc:
        logger.warning('[%s] Dividend yield fetch failed: %s', normalized, exc)
        _cache_dividend_info(normalized, None)
        return None


def _enrich_metadata_with_dividend_info(config, metadata):
    if not _equity_like_asset(config):
        return metadata
    ticker = (config.get('ticker') or '').strip()
    profile = _fetch_dividend_profile(ticker)
    if not profile:
        return metadata
    merged = dict(metadata)
    merged.update(profile)
    return merged


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

    result = _fetch_asset_history(cfg, start_year, end_year)
    if not result:
        raise RuntimeError('데이터를 가져오지 못했습니다.')

    history, source = result
    prices = _build_yearly_closing_points(history, start_year, end_year)

    response_unit = (cfg.get('unit') or '').upper()
    category = cfg.get('category') or ''
    ticker_upper = (cfg.get('ticker') or cfg.get('id') or '').upper()
    if category == '국내 주식' or ticker_upper.endswith(('.KS', '.KQ', '.KL', '.KR')):
        response_unit = 'KRW'

    return {
        'unit': response_unit,
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
    data_agent = cfg.get('data_agent')
    base_asset_id = cfg.get('base_asset_id')

    if data_agent == 'seoul_apartment':
        return _fetch_seoul_apartment_history(start_year, end_year)

    if base_asset_id:
        if base_asset_id == cfg.get('id'):
            raise RuntimeError('base_asset_id cannot reference itself')
        base_cfg = _find_known_asset_config(base_asset_id, base_asset_id)
        if not base_cfg:
            raise RuntimeError(f'기준 자산({base_asset_id})을 찾을 수 없습니다.')
        base_history, base_source = _fetch_asset_history(base_cfg, start_year, end_year)
        ltv_ratio = cfg.get('ltv_ratio') or cfg.get('ltv') or 0.5
        derived_history = _build_ltv_equity_history(base_history, ltv_ratio)
        if not derived_history:
            raise RuntimeError('기준 자산에서 유효한 데이터를 가져오지 못했습니다.')
        return derived_history, base_source

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
            'raw_value': adjusted_value,
            'multiple': round(multiple, 6)
        })

    if len(points) < 2:
        return None

    start_val = points[0]['multiple'] or 1.0
    end_val = points[-1]['multiple'] or start_val
    years_total = points[-1]['year'] - points[0]['year']

    # Always compute CAGR so it can be referenced in summaries regardless of the selected method
    if years_total > 0 and start_val > 0:
        try:
            cagr_return_pct = ((end_val / start_val) ** (1 / years_total) - 1) * 100
        except Exception:
            cagr_return_pct = 0.0
    else:
        cagr_return_pct = 0.0

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
        final_return_pct = cagr_return_pct

    return {
        'id': cfg.get('id') or asset_key,
        'label': cfg['label'],
        'ticker': cfg.get('ticker'),
        'category': cfg.get('category', '안전자산'),
        'unit': cfg.get('unit', ''),
        'points': points,
        'annualized_return_pct': round(final_return_pct, 2),  # Used for sorting
        'annualized_cagr_pct': round(cagr_return_pct, 2),
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
    # Explicit "X년 전" references (e.g., "5년 전 대비")
    match = re.search(r'(\d{1,3})\s*년\s*전(?:\s*대비)?', lowered)
    if match:
        try:
            span = int(match.group(1))
        except ValueError:
            span = None
        if span and 1 <= span <= 50:
            return span
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
        if span and 1 <= span <= 50:
            return span
    return None


def _derive_finance_year_window(year_hint, span_hint=None):
    current_year = datetime.utcnow().year
    min_year = 2010
    if span_hint and span_hint >= 1:
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


def _detect_historical_market_cap_assets(prompt_text):
    """
    Detect prompts asking for historical market-cap leaders (e.g., "10년 전 시가총액 상위 5개").
    Returns {'groups': [...], 'assets': [...]} or None.
    """
    if not prompt_text:
        return None

    text = str(prompt_text).lower()
    compact = text.replace(' ', '')

    market_cap_keywords = ['시가총액', 'market cap', 'marketcap', 'market capitalization']
    if not any(keyword in text for keyword in market_cap_keywords):
        return None

    has_rank_keyword = False
    if '상위' in text and ('5' in text or '다섯' in text):
        has_rank_keyword = True
    rank_variants = ['top 5', 'top5', 'top-five', 'topfive']
    if not has_rank_keyword:
        for variant in rank_variants:
            if variant.replace(' ', '') in compact or variant in text:
                has_rank_keyword = True
                break
    if not has_rank_keyword:
        return None

    detected_groups = []
    detected_assets = []
    seen_ids = set()

    for group in HISTORICAL_MARKET_CAP_GROUPS:
        match_found = False
        for phrase in group.get('match_phrases', []):
            phrase_lower = phrase.lower()
            if not phrase_lower:
                continue
            phrase_compact = phrase_lower.replace(' ', '')
            if phrase_lower in text or phrase_compact in compact:
                match_found = True
                break

        if not match_found:
            continue

        detected_groups.append(group.get('label', group.get('key', '시가총액 상위 그룹')))
        for idx, asset in enumerate(group.get('assets', []), start=1):
            asset_id = (asset.get('id') or '').strip()
            if not asset_id:
                continue
            norm_id = asset_id.lower()
            if norm_id in seen_ids:
                continue
            seen_ids.add(norm_id)
            metadata = {
                'market_cap_rank': idx,
                'market_cap_group': group.get('label') or group.get('key'),
                'market_cap_usd': asset.get('market_cap_usd'),
            }
            detected_assets.append({
                'id': asset_id,
                'label': asset.get('label') or asset_id,
                'type': asset.get('type', 'us_stock'),
                'metadata': metadata,
            })

    if not detected_assets:
        return None

    return {
        'groups': detected_groups,
        'assets': detected_assets,
    }


def _sanitize_custom_assets(raw_assets):
    if not isinstance(raw_assets, list):
        return []
    sanitized = []
    for item in raw_assets:
        if isinstance(item, str):
            name = item.strip()
            if name:
                sanitized.append(name)
    return sanitized


def _build_manual_assets(asset_names, calculation_method):
    manual_assets = []
    if not asset_names:
        return manual_assets

    for name in asset_names:
        label = (name or '').strip()
        if not label:
            continue

        known_config = _find_known_asset_config(label, label)
        if known_config:
            asset_id = known_config.get('id') or label
            asset_label = known_config.get('label') or asset_id
            asset_type = known_config.get('category', 'asset')
        else:
            asset_id = label
            asset_label = label
            asset_type = 'unknown'

        manual_assets.append({
            'id': asset_id,
            'label': asset_label,
            'type': asset_type,
            'calculation_method': calculation_method
        })

    return manual_assets


def _asset_identity_key(asset):
    if not asset:
        return ''
    asset_id = (asset.get('id') or '').strip().lower()
    if asset_id:
        return asset_id
    label_norm = _normalize_asset_label_text(asset.get('label'))
    return label_norm or ''


def _merge_asset_lists(original_assets, additional_assets):
    merged = []
    added = []
    seen = set()

    def _maybe_add(target_list, asset, track_added=False):
        key = _asset_identity_key(asset)
        if key and key in seen:
            return False
        if key:
            seen.add(key)
        target_list.append(asset)
        if track_added:
            added.append(asset)
        return True

    for asset in original_assets or []:
        _maybe_add(merged, asset)

    for asset in additional_assets or []:
        _maybe_add(merged, asset, track_added=True)

    return merged, added


RELATED_ASSET_SUGGESTIONS = [
    {
        'keywords': ['반도체', 'semiconductor', 'semi'],
        'asset_key': 'soxx'
    },
    {
        'keywords': ['미국채', '10년물', '10y', 'treasury'],
        'asset_key': 'ief'
    },
]


def _suggest_related_asset(text):
    """
    Recommend a closely-related asset when the exact ticker cannot be resolved.
    """
    normalized = _normalize_asset_label_text(text)
    if not normalized:
        return None

    for entry in RELATED_ASSET_SUGGESTIONS:
        for keyword in entry['keywords']:
            if keyword.lower() in normalized:
                asset_key = entry.get('asset_key')
                if asset_key and asset_key in SAFE_ASSETS:
                    return _clone_asset_config(SAFE_ASSETS[asset_key], asset_key)
    return None


def _contains_korean(text):
    if not text:
        return False
    return bool(re.search(r'[\uac00-\ud7a3]', str(text)))


def _translate_to_english_if_needed(text):
    """
    Translate Korean asset/company names for better ticker lookup accuracy.
    """
    cleaned = (text or '').strip()
    if not cleaned or not _contains_korean(cleaned):
        return cleaned

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return cleaned

    base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    system_prompt = (
        "You are a translator specializing in financial assets. "
        "Translate Korean company or asset names into the most likely official English names. "
        "Return concise English text only."
    )
    user_prompt = f"Korean name: {cleaned}"

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
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.0,
            },
            timeout=10
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        if content:
            return content
    except Exception as exc:
        logger.warning("Korean→English translation failed for '%s': %s", cleaned, exc)

    return cleaned


def _lookup_ticker_with_llm(asset_id, label):
    system_prompt = _get_agent_prompt('ticker_finder',
        "You are a financial data assistant. Your goal is to find the correct Yahoo Finance ticker symbol for a given asset name.\n"
        "Input: Asset Name / ID\n"
        "Output JSON: { \"found\": true, \"ticker\": \"SYMBOL\", \"label\": \"Official Name\", \"category\": \"Category\" }\n"
        "Rules:\n"
        "- For US Stocks: Use standard ticker (e.g., AAPL, TSLA, NVDA).\n"
        "- For Korean Stocks: Use 6-digit code with .KS (KOSPI) or .KQ (KOSDAQ) suffix (e.g., 005930.KS).\n"
        "- For Indices: Use Yahoo Finance symbol (e.g., ^GSPC for S&P 500, ^DJI for Dow).\n"
        "- For Crypto: Use BTC-USD, ETH-USD format.\n"
        "- If uncertain or not found, return { \"found\": false }.\n"
        "- BE PRECISE. Incorrect tickers cause errors."
    )

    resolved_name = (label or asset_id or '').strip()
    english_hint = _translate_to_english_if_needed(resolved_name or asset_id)
    user_content = f"Find ticker for: {resolved_name or asset_id} (ID: {asset_id})"
    if english_hint and english_hint.lower() != (resolved_name or '').lower():
        user_content += f"\nEnglish translation: {english_hint}"

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
            timeout=10
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        result = json.loads(content)

        if result.get('found') and result.get('ticker'):
            ticker = result['ticker'].strip().upper()
            found_label = (result.get('label') or label or ticker).strip()
            return {
                'id': ticker,
                'label': found_label,
                'ticker': ticker,
                'category': result.get('category')
            }

    except Exception as exc:
        logger.warning("LLM ticker lookup failed for %s (%s): %s", label, asset_id, exc)

    return None


# --- Agent Classes ---

class IntentClassifierAgent:
    """
    Responsible for extracting a list of assets to analyze.
    (Intent classification for method is now simplified to keyword-only or defaults).
    """
    def run(self, prompt, quick_requests):
        logs = []
        result = None
        for event in self.stream(prompt, quick_requests):
            if event['type'] == 'log':
                logs.append(event['message'])
            elif event['type'] == 'result':
                result = event['data']
        if result is None:
            result = {'allowed': False, 'error': '자산 추출 중 오류가 발생했습니다.'}
        return result, logs

    def stream(self, prompt, quick_requests):
        yield from self._run_generator(prompt, quick_requests)

    def _run_generator(self, prompt, quick_requests):
        yield {'type': 'log', 'message': "[의도 분석] 사용자 요청 분석 중..."}

        combined_prompt = f"{prompt} {' '.join(quick_requests)}" if quick_requests else prompt
        if not combined_prompt.strip():
            combined_prompt = "비트코인과 대표 자산의 과거 연평균 상승률을 비교해줘."

        time_keywords = ['년', '기간', '동안', '지난', '최근', '10년', '5년', '20년', 'year']
        has_time_period = any(keyword in combined_prompt.lower() for keyword in time_keywords)

        if not has_time_period:
            combined_prompt = f"{combined_prompt} (지난 10년간의 데이터)"
            yield {'type': 'log', 'message': "[의도 분석] 기본 기간 설정: 지난 10년"}

        try:
            allowed, reason = _check_prompt_intent(combined_prompt)
            if not allowed:
                yield {'type': 'log', 'message': f"[의도 분석] 요청 차단됨. 사유: {reason}"}
                yield {'type': 'result', 'data': {'allowed': False, 'error': '요청이 거부되었습니다. ' + reason}}
                return
            yield {'type': 'log', 'message': "[의도 분석] 보안 검사 통과"}
        except Exception as e:
            yield {'type': 'log', 'message': f"[의도 분석] 보안 검사 실패 ({e}). 계속 진행합니다."}

        prompt_lower = combined_prompt.lower()
        calculation_method = 'cagr'

        if any(k in prompt_lower for k in ['가격', '종가', 'price', 'value', 'year-end', '연말', '시세', '투자했다면', '투자', 'investment', '얼마', 'how much', '만원', '후']):
            calculation_method = 'price'
            yield {'type': 'log', 'message': "[의도 분석] 키워드 감지: '가격/투자(Price)' 분석 요청"}
        elif any(k in prompt_lower for k in ['증감률', 'growth', 'change', 'yoy', '전년', '성장률', '변동률']):
            calculation_method = 'yearly_growth'
            yield {'type': 'log', 'message': "[의도 분석] 키워드 감지: '증감률(YoY)' 분석 요청"}
        elif any(k in prompt_lower for k in ['누적', 'cumulative', 'total return', '총 수익률']):
            calculation_method = 'cumulative'
            yield {'type': 'log', 'message': "[의도 분석] 키워드 감지: '누적 수익률' 분석 요청"}
        else:
            yield {'type': 'log', 'message': "[의도 분석] 키워드 미감지: 기본값 '연평균 상승률(CAGR)' 적용"}

        system_prompt = _get_agent_prompt('intent_classifier',
            "You are a financial asset extractor. Your goal is to extract the target assets from the user's prompt.\n\n"
            "**IMPORTANT CONTEXT**: Unless otherwise specified, all analysis requests are for historical data from the past 10 years (지난 10년간의 데이터). "
            "This is the default time period for all financial comparisons and analysis.\n\n"
            "**STEP 1: Extract Assets**\n"
            "Identify all financial assets. Handle groups explicitly:\n"
            "- If '대표 자산' (Representative Assets) is found -> Expand to: Bitcoin, Gold, US 10Y Treasury, Silver, S&P 500.\n"
            "- If '미국 빅테크' or 'US Big Tech' or '미국 빅테크 10개 종목' -> Expand to ALL 10 companies: Apple, Microsoft, Alphabet, Amazon, Meta, Tesla, Nvidia, Netflix, Adobe, AMD.\n"
            "- If '국내 주식' or 'KR Equity' or '한국 주식 10개 종목' -> Expand to ALL 10 companies: Samsung Electronics, SK Hynix, NAVER, Kakao, LG Energy Solution, Hyundai Motor, Kia, Samsung Biologics, Samsung SDI, POSCO Holdings.\n"
            "- For Korean Stocks, MUST provide the Korean name in the 'label' field (e.g. '삼성전자' instead of 'Samsung Electronics').\n\n"
            "**CRITICAL**: When a group like '미국 빅테크 10개 종목' is mentioned, you MUST extract all 10 companies. Do not extract only a subset.\n\n"
            "**Output Format (JSON)**\n"
            "{\n"
            "  \"assets\": [ { \"id\": \"...\", \"label\": \"...\", \"type\": \"...\" }, ... ]\n"
            "}"
        )

        user_content = f"User Request: {combined_prompt}"

        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
            model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

            yield {'type': 'log', 'message': "[의도 분석] AI를 사용하여 자산 목록 추출 중..."}
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

            detected_market_cap = _detect_historical_market_cap_assets(combined_prompt)
            if detected_market_cap:
                added_assets = detected_market_cap.get('assets', [])
                asset_labels = ', '.join(a.get('label', a.get('id', '')) for a in added_assets if a.get('id'))
                group_names = ', '.join(detected_market_cap.get('groups', []))
                assets.extend(added_assets)
                yield {'type': 'log', 'message': f"[의도 분석] {group_names} 자동 감지 → {len(added_assets)}개 자산 추가: {asset_labels}"}

            clean_assets = []
            seen_ids = set()
            
            for a in assets:
                raw_id = (a.get('id') or '').strip()
                raw_label = (a.get('label') or raw_id).strip()
                
                if not raw_id and not raw_label:
                    continue

                known_config = _find_known_asset_config(raw_id, raw_label)
                
                if known_config:
                    final_id = known_config.get('id')
                    final_label = known_config.get('label') or final_id
                    asset_type = known_config.get('category', 'asset')
                else:
                    final_id = raw_id
                    final_label = raw_label or raw_id
                    asset_type = 'unknown'
                
                normalized_id = final_id.lower()
                if normalized_id in seen_ids:
                    continue
                seen_ids.add(normalized_id)

                asset_entry = {
                    'id': final_id,
                    'label': final_label,
                    'type': asset_type,
                    'calculation_method': calculation_method
                }
                clean_assets.append(asset_entry)

            if calculation_method == 'cumulative':
                method_label = '누적 수익률'
            elif calculation_method == 'yearly_growth':
                method_label = '전년 대비 증감률(YoY)'
            elif calculation_method == 'price':
                method_label = '가격(Price)'
            else:
                method_label = '연평균 상승률(CAGR)'

            yield {'type': 'log', 'message': f"[의도 분석] {len(clean_assets)}개 자산 추출 완료: {', '.join(a['label'] for a in clean_assets)}"}
            yield {'type': 'log', 'message': f"[의도 분석] 최종 계산 방식: {method_label}"}
            yield {'type': 'result', 'data': {'allowed': True, 'assets': clean_assets, 'calculation_method': calculation_method}}

        except Exception as e:
            yield {'type': 'log', 'message': f"[의도 분석] 자산 추출 실패: {e}"}
            yield {'type': 'result', 'data': {'allowed': False, 'error': '자산 추출 중 오류가 발생했습니다.'}}


class PriceRetrieverAgent:
    """
    Responsible for fetching historical price data for the requested assets.
    It uses the existing helper functions (_fetch_asset_history, etc.).
    Now includes cache-first lookup from internal DB.
    """
    def run(self, assets, start_year, end_year):
        logs = []
        price_data_map = {}
        for event in self.stream(assets, start_year, end_year):
            if event['type'] == 'log':
                logs.append(event['message'])
            elif event['type'] == 'result':
                price_data_map = event['data']
        return price_data_map, logs

    def stream(self, assets, start_year, end_year):
        yield from self._run_generator(assets, start_year, end_year)

    def _run_generator(self, assets, start_year, end_year):
        price_data_map = {}
        yield {'type': 'log', 'message': f"[데이터 수집] {len(assets)}개 자산의 {start_year}-{end_year} 데이터 가져오는 중..."}

        for asset in assets:
            asset_id = asset['id']
            label = asset['label']
            asset_type = asset.get('type', 'unknown')

            yield {'type': 'log', 'message': f"[데이터 수집] {label} 처리 중..."}

            cached_data = self._check_price_cache(asset_id, start_year, end_year)
            if cached_data:
                yield {'type': 'log', 'message': f"[데이터 수집] ✓ {label}: 캐시됨 (cache hit) - {len(cached_data['yearly_prices'])}개 데이터 포인트"}
                history = []
                for year_str, price in sorted(cached_data['yearly_prices'].items()):
                    year_int = int(year_str)
                    dt = datetime(year_int, 12, 31)
                    history.append((dt, float(price)))

                config = {
                    'id': asset_id,
                    'label': cached_data['label'],
                    'ticker': asset_id,
                    'category': cached_data['category'],
                    'unit': cached_data['unit']
                }

                base_metadata = dict(asset.get('metadata') or {})
                enriched_metadata = _enrich_metadata_with_dividend_info(config, base_metadata)
                price_data_map[asset_id] = {
                    'history': history,
                    'config': config,
                    'source': f"{cached_data['source']} (캐시됨)",
                    'calculation_method': asset.get('calculation_method', 'cagr'),
                    'metadata': enriched_metadata
                }
                continue

            yield {'type': 'log', 'message': f"[데이터 수집] {label}: 외부 API에서 조회 중..."}
            config = _find_known_asset_config(asset_id, label)

            if not config:
                is_korean_stock_ticker = bool(re.match(r'\d{6}\.(KS|KQ|KL)', asset_id))

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

                if not (asset_type == 'kr_stock' or is_korean_stock_ticker):
                    config['stooq_symbol'] = _guess_stooq_symbol(asset_id)

                yield {'type': 'log', 'message': f"[데이터 수집] {label}: 동적 config 생성 완료 (Category: {category}, Ticker: {asset_id})"}

            try:
                result = _fetch_asset_history(config, start_year, end_year)
                if result:
                    history, source = result
                    base_metadata = dict(asset.get('metadata') or {})
                    enriched_metadata = _enrich_metadata_with_dividend_info(config, base_metadata)
                    price_data_map[asset_id] = {
                        'history': history,
                        'config': config,
                        'source': source,
                        'calculation_method': asset.get('calculation_method', 'cagr'),
                        'metadata': enriched_metadata
                    }
                    ticker_info = config.get('ticker', asset_id)
                    category_info = config.get('category', '알 수 없음')
                    yield {'type': 'log', 'message': f"[데이터 수집] ✓ {label}: {source}에서 {len(history)}개 데이터 포인트 수집 완료 (Ticker: {ticker_info}, Category: {category_info})"}
                else:
                    yield {'type': 'log', 'message': f"[데이터 수집] ✗ {label}: 데이터 없음"}
            except Exception as e:
                yield {'type': 'log', 'message': f"[데이터 수집] ✗ {label} 실패: {e}"}

        yield {'type': 'result', 'data': price_data_map}

    def _check_price_cache(self, asset_id, start_year, end_year):
        """
        Check internal DB cache for price data.
        Returns cached data dict or None if not found.
        """
        from blocks.models import AssetPriceCache
        try:
            cache_entry = AssetPriceCache.objects.get(asset_id=asset_id)

            # Filter by year range
            yearly_prices = {}
            for year_str, price in cache_entry.yearly_prices.items():
                year = int(year_str)
                if year < start_year or year > end_year:
                    continue
                yearly_prices[year_str] = price

            if not yearly_prices:
                return None

            return {
                'asset_id': cache_entry.asset_id,
                'label': cache_entry.label,
                'category': cache_entry.category,
                'unit': cache_entry.unit,
                'source': cache_entry.source,
                'yearly_prices': yearly_prices,
            }
        except AssetPriceCache.DoesNotExist:
            return None
        except Exception as e:
            logger.warning(f"Error checking cache for {asset_id}: {e}")
            return None

    def _map_category(self, asset_type):
        mapping = {
            'crypto': '디지털 자산',
            'kr_stock': '국내 주식',
            'us_stock': '미국 주식',
            'index': '지수',
            'commodity': '원자재',
            'bond': '채권',
            'forex': '통화',
            'economic_indicator': '경제 지표',
            'real_estate': '부동산'
        }
        return mapping.get(asset_type, '기타')


class CalculatorAgent:
    """
    Responsible for processing raw price history into the standardized 'series' format
    required by the frontend (calculating CAGR or cumulative returns, normalizing to 1.0, etc.).
    Also prepares the yearly closing prices for the table.
    """
    def run(self, price_data_map, start_year, end_year, calculation_method='cagr', include_dividends=False):
        logs = []
        result_data = {'series': [], 'table': [], 'summary': ''}
        for event in self.stream(price_data_map, start_year, end_year, calculation_method, include_dividends=include_dividends):
            if event['type'] == 'log':
                logs.append(event['message'])
            elif event['type'] == 'result':
                result_data = event['data']
        return result_data['series'], result_data['table'], result_data['summary'], logs

    def stream(self, price_data_map, start_year, end_year, calculation_method='cagr', include_dividends=False):
        yield from self._run_generator(price_data_map, start_year, end_year, calculation_method, include_dividends)

    def _run_generator(self, price_data_map, start_year, end_year, calculation_method, include_dividends):
        if calculation_method == 'price':
            method_label = '가격(Price)'
        elif calculation_method == 'cumulative':
            method_label = '누적 상승률'
        elif calculation_method == 'yearly_growth':
            method_label = '전년 대비 증감률(YoY)'
        else:
            method_label = '연평균 상승률(CAGR)'

        yield {'type': 'log', 'message': f"[수익률 계산] {method_label} 계산 및 데이터 포맷팅 중..."}

        if include_dividends:
            adjusted = self._apply_dividend_reinvestment(price_data_map, start_year, end_year)
            if adjusted:
                yield {'type': 'log', 'message': f"[수익률 계산] 배당 재투자 적용: {len(adjusted)}개 자산"}
            else:
                yield {'type': 'log', 'message': "[수익률 계산] 배당 재투자 적용 대상이 없습니다."}

        series_list = []

        for asset_id, data in price_data_map.items():
            history = data['history']
            config = data['config']
            source = data.get('source', 'Unknown')

            asset_calc_method = data.get('calculation_method', calculation_method)

            try:
                series_obj = _build_asset_series(config['id'], config, history, start_year, end_year, asset_calc_method)
                if series_obj:
                    series_obj['id'] = config['id']
                    series_obj['calculation_method'] = asset_calc_method
                    series_obj['source'] = source
                    metadata = data.get('metadata') or {}
                    if metadata:
                        series_obj['metadata'] = metadata
                        for meta_key, meta_value in metadata.items():
                            if meta_key not in series_obj:
                                series_obj[meta_key] = meta_value
                    series_list.append(series_obj)
                else:
                    yield {'type': 'log', 'message': f"[수익률 계산] {config['label']}: 데이터 부족으로 시리즈 생성 불가"}
            except Exception as e:
                yield {'type': 'log', 'message': f"[수익률 계산] {config['label']} 시리즈 생성 오류: {e}"}

        series_list.sort(key=lambda x: x.get('annualized_return_pct', -999), reverse=True)
        chart_data_table = self._build_chart_data_table(series_list, calculation_method)
        yield {'type': 'log', 'message': f"[수익률 계산] {len(series_list)}개 시리즈 생성 완료"}

        summary = self._generate_summary(series_list, start_year, end_year)
        yield {'type': 'result', 'data': {'series': series_list, 'table': chart_data_table, 'summary': summary}}

    def _apply_dividend_reinvestment(self, price_data_map, start_year, end_year):
        """
        For Yahoo Finance assets, refetch dividend-adjusted history to simulate reinvestment.
        """
        adjusted_assets = []
        if not price_data_map:
            return adjusted_assets

        for asset_id, data in price_data_map.items():
            if not isinstance(data, dict):
                continue
            source = data.get('source')
            config = data.get('config') or {}
            ticker = (config.get('ticker') or '').strip()
            if source != 'Yahoo Finance' or not ticker:
                continue

            try:
                history = _fetch_yfinance_history(ticker, start_year, end_year, adjust_for_dividends=True)
                if history:
                    data['history'] = history
                    metadata = data.setdefault('metadata', {})
                    metadata['dividends_reinvested'] = True
                    adjusted_assets.append(config.get('label') or ticker)
                    logger.info('[%s] Dividend reinvestment 적용 (Adjusted Close 사용)', config.get('label', ticker))
            except Exception as exc:
                logger.warning('[%s] 배당 재투자 데이터 가져오기 실패: %s', config.get('label', ticker), exc)

        return adjusted_assets

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
                # Use raw_value if available (especially for price mode), otherwise value
                val = point.get('raw_value') if point.get('raw_value') is not None else point.get('value')
                
                if year is not None and val is not None:
                    yearly_values.append({
                        'year': year,
                        'value': val  # Use raw value for table display
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
            best_multiple = best.get('multiple_from_start')
            worst_multiple = worst.get('multiple_from_start')
            best_text = f"원금 대비 {best_multiple:.1f}배" if best_multiple is not None else "가장 크게 증가"
            worst_text = f"{worst_multiple:.1f}배" if worst_multiple is not None else "가장 낮은 수준"
            return (f"{start_year}년부터 {end_year}년까지 가격 비교 결과, "
                    f"{best['label']}이(가) {best_text}였으며, "
                    f"{worst['label']}은(는) {worst_text}에 그쳤습니다.")
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
        summary = "분석할 데이터가 없습니다."
        for event in self.stream(series_list, start_year, end_year, calculation_method, prompt):
            if event['type'] == 'log':
                logs.append(event['message'])
            elif event['type'] == 'result':
                summary = event['data']
        return summary, logs

    def stream(self, series_list, start_year, end_year, calculation_method, prompt):
        yield from self._run_generator(series_list, start_year, end_year, calculation_method, prompt)

    def _run_generator(self, series_list, start_year, end_year, calculation_method, prompt):
        yield {'type': 'log', 'message': "[분석 생성] 비트코인 중심 분석 리포트 생성 중..."}

        if not series_list:
            yield {'type': 'result', 'data': "분석할 데이터가 없습니다."}
            return

        bitcoin = None
        other_assets = []

        for series in series_list:
            label_lower = series.get('label', '').lower()
            if 'bitcoin' in label_lower or '비트코인' in label_lower or 'btc' in label_lower:
                bitcoin = series
            else:
                other_assets.append(series)

        if not bitcoin:
            yield {'type': 'log', 'message': "[분석 생성] 비트코인 데이터를 찾을 수 없어 일반 분석으로 대체"}
            yield {'type': 'result', 'data': self._generate_generic_analysis(series_list, start_year, end_year, calculation_method)}
            return

        try:
            analysis_text = self._generate_ai_analysis(bitcoin, other_assets, start_year, end_year, calculation_method, prompt)
            yield {'type': 'log', 'message': "[분석 생성] AI 분석 리포트 생성 완료"}
            yield {'type': 'result', 'data': analysis_text}
        except Exception as e:
            yield {'type': 'log', 'message': f"[분석 생성] AI 분석 실패: {e}, 기본 분석으로 대체"}
            yield {'type': 'result', 'data': self._generate_fallback_analysis(bitcoin, other_assets, start_year, end_year, calculation_method, prompt)}

    def _get_asset_cagr_pct(self, asset):
        """Return CAGR (연평균 상승률) for the asset if available."""
        if not asset:
            return None
        cagr_value = asset.get('annualized_cagr_pct')
        if isinstance(cagr_value, (int, float)):
            return cagr_value
        fallback = asset.get('annualized_return_pct')
        if isinstance(fallback, (int, float)):
            return fallback
        return None

    def _generate_ai_analysis(self, bitcoin, other_assets, start_year, end_year, calculation_method, prompt):
        """Generate narrative analysis using LLM"""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        base_url = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

        # Prepare data for LLM
        bitcoin_return = bitcoin.get('annualized_return_pct', 0)
        bitcoin_multiple = bitcoin.get('multiple_from_start', 1)
        investment_info = self._extract_investment_amount(prompt)

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
            "1. 비트코인의 핵심 수치를 먼저 강조하고, **3문장 이내**의 간결한 문단으로 설명합니다\n"
            "2. 비트코인 이외의 개별 자산명은 절대로 언급하지 않습니다 (엔비디아, 금 등 금지)\n"
            "3. 다른 자산을 언급해야 한다면 '다른 자산들의 성과는 아래에서 확인하세요'와 같이 일반 표현만 사용합니다\n"
            "4. 주요 수치(연도, 퍼센트, 배수)는 하이라이트 태그로 감싸고, 불필요한 수식어는 제거합니다\n"
            "5. 답변은 담백한 어조를 유지하며, 문장은 최대 20단어 내외로 유지합니다\n"
            "6. 다른 자산들의 세부 리스트는 시스템이 자동으로 생성하므로, HTML 리스트(<ul>, <ol>, <li>)는 출력하지 않습니다\n"
            "7. 리스트를 언급해야 할 경우, '다른 자산들의 성과는 시스템에서 이어서 제공합니다' 정도로 짧게 안내만 해주세요\n\n"
            "**하이라이트 규칙:**\n"
            "- 비트코인 관련 텍스트: <span class='bg-yellow-300 text-yellow-900 px-2 py-1 rounded font-bold text-lg'>비트코인</span>\n"
            "- 연도: <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>2015년</span>\n"
            "- 비트코인의 숫자(퍼센트, 배수): <span class='bg-yellow-200 text-yellow-900 px-2 py-1 rounded font-bold'>81.5%</span>\n\n"
            "**출력 형식:**\n"
            "1. 첫 문단: 비트코인의 성과 요약 (비트코인 단어를 크고 노란색으로 강조)\n"
            "2. HTML 리스트는 생성하지 말고 문단 단위의 설명만 작성하세요."
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
        cleaned_content = re.sub(r'<ul[\s\S]*?</ul>', '', content, flags=re.IGNORECASE).strip()
        bitcoin_focus_block = self._build_bitcoin_focus_block(bitcoin, start_year, end_year, metric_name, investment_info)
        final_sections = []
        if bitcoin_focus_block:
            final_sections.append(bitcoin_focus_block)
        return ''.join(final_sections)


    def _extract_investment_amount(self, prompt):
        if not prompt:
            return None
        text = str(prompt)
        patterns = [
            (r'(\d{1,3}(?:,\d{3})*)(?:\s*)(만원)', '만원', 10000),
            (r'(\d{1,3}(?:,\d{3})*)(?:\s*)(원)', '원', 1),
        ]
        for pattern, unit, unit_factor in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                amount_value = float(match.group(1).replace(',', ''))
            except ValueError:
                continue
            if amount_value <= 0:
                continue
            return {
                'unit': unit,
                'unit_factor': unit_factor,
                'amount': amount_value,
                'display_text': f"{match.group(1)}{unit}"
            }
        return None

    def _format_investment_result(self, value, unit, unit_factor=None):
        if value is None:
            return ''
        factor = unit_factor if unit_factor else (10000 if unit == '만원' else 1)
        amount_won = value * factor
        return self._format_korean_won(amount_won)

    def _format_korean_won(self, amount_won):
        try:
            amount_int = int(round(amount_won))
        except Exception:
            return "0 원"

        units = [
            (10 ** 12, '조'),
            (10 ** 8, '억'),
            (10 ** 4, '만'),
        ]

        parts = []
        remainder = amount_int

        for value, label in units:
            if remainder >= value:
                unit_amount = remainder // value
                parts.append(f"{unit_amount:,}{label}")
                remainder %= value

        if remainder >= 1000:
            parts.append(f"{remainder // 1000:,}천")
            remainder %= 1000

        if remainder > 0 or not parts:
            parts.append(f"{remainder:,}")

        return ' '.join(parts) + ' 원'

    def _format_market_cap_usd(self, amount_usd):
        if amount_usd is None:
            return ""
        try:
            amount = float(amount_usd)
        except (TypeError, ValueError):
            return ""
        if amount <= 0:
            return ""

        trillions = amount / 1_000_000_000_000
        if trillions >= 0.1:
            decimals = 1 if trillions >= 1 else 2
            formatted_value = format(trillions, f'.{decimals}f')
            return f"약 ${formatted_value}조 (USD)"

        return f"${amount:,.0f} (USD)"

    def _build_bitcoin_focus_block(self, bitcoin, start_year, end_year, metric_name, investment_info=None):
        """Return a large, simple paragraph highlighting Bitcoin performance."""
        if not bitcoin:
            return ""

        bitcoin_return = bitcoin.get('annualized_return_pct', 0) or 0
        bitcoin_multiple = bitcoin.get('multiple_from_start', 1) or 1
        period_years = max(1, end_year - start_year)

        base_text_class = "text-3xl font-black text-slate-900"
        block = (
            "<div class='mb-4 space-y-3'>"
            f"<p class='{base_text_class} leading-tight'>"
            f"<span class='{base_text_class}'>{start_year}년</span>부터 "
            f"<span class='{base_text_class}'>{end_year}년</span>까지 "
            f"<span class='{base_text_class}'>비트코인</span>은 "
            f"{period_years}년 동안 원금의 "
            f"<span class='bg-yellow-200 text-yellow-900 px-4 py-1 rounded font-black text-4xl'>{bitcoin_multiple:.1f}배</span>"
            "가 되었습니다."
            "</p>"
        )

        bitcoin_cagr = self._get_asset_cagr_pct(bitcoin)
        if isinstance(bitcoin_cagr, (int, float)):
            if metric_name == '연평균 상승률':
                prefix = "연평균 상승률은 "
            else:
                prefix = "같은 기간 연평균 상승률은 "
            highlight_span = (
                f"<span class='bg-yellow-200 text-yellow-900 px-4 py-1 rounded font-black text-3xl'>{bitcoin_cagr:.1f}%</span>"
            )
            block += (
                "<p class='text-3xl font-semibold text-slate-800 leading-snug'>"
                f"{prefix}{highlight_span}"
                "였습니다."
                "</p>"
            )

        if investment_info and bitcoin_multiple > 0:
            final_amount = investment_info['amount'] * bitcoin_multiple
            formatted_final = self._format_investment_result(
                final_amount,
                investment_info['unit'],
                investment_info.get('unit_factor')
            )
            block += (
                "<p class='text-3xl font-semibold text-slate-900 leading-snug'>"
                f"<span class='font-extrabold text-slate-900'>{investment_info['display_text']}</span>을 "
                f"<span class='{base_text_class}'>비트코인</span>에 투자했다면 "
                f"지금은 <span class='bg-green-100 text-green-900 px-3 py-1 rounded font-black text-3xl'>{formatted_final}</span> 정도입니다."
                "</p>"
            )

        block += "</div>"
        return block

    def _generate_fallback_analysis(self, bitcoin, other_assets, start_year, end_year, calculation_method, prompt=None):
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

        investment_info = self._extract_investment_amount(prompt)
        bitcoin_focus_block = self._build_bitcoin_focus_block(bitcoin, start_year, end_year, metric_name, investment_info)
        return bitcoin_focus_block or ""

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
    custom_assets = _sanitize_custom_assets(payload.get('custom_assets'))

    backend_logger.info("Prompt: %s", prompt)
    backend_logger.info("Quick Requests: %s", quick_requests)
    if custom_assets:
        backend_logger.info("Custom Assets: %s", custom_assets)

    context_key = (payload.get('context_key') or '').strip()
    backend_logger.info("Context Key: %s", context_key)
    _ensure_finance_cache_purged(context_key)
    include_dividends = bool(payload.get('include_dividends'))
    backend_logger.info("Include Dividends: %s", include_dividends)
    stream_channel = (payload.get('stream_channel') or '').strip()
    if stream_channel:
        finance_stream_manager.prepare_channel(stream_channel)

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
            _finance_analysis_stream(prompt, quick_requests, custom_assets, context_key, start_year, end_year, user_identifier, start_time, include_dividends),
            content_type='text/event-stream'
        )
    else:
        # Original non-streaming implementation
        all_logs = []

        def append_log(message):
            if not message:
                return
            all_logs.append(message)
            if stream_channel:
                finance_stream_manager.publish(stream_channel, {'type': 'log', 'message': message})

        def stream_error(message):
            if stream_channel and message:
                finance_stream_manager.publish(stream_channel, {'type': 'error', 'message': message})

        def stream_complete(status='ok'):
            if stream_channel:
                finance_stream_manager.publish(stream_channel, {'type': 'complete', 'status': status})

        def consume_agent_stream(generator):
            result_data = None
            for event in generator:
                event_type = event.get('type')
                if event_type == 'log':
                    append_log(event.get('message'))
                elif event_type == 'result':
                    result_data = event.get('data')
            return result_data

        append_log(f"시스템: {start_year}-{end_year} 멀티 에이전트 분석 시작")

        # --- Multi-Agent Workflow ---

        # Agent 1: Intent Classifier
        backend_logger.info("STEP 1: Running IntentClassifierAgent")
        intent_agent = IntentClassifierAgent()
        intent_result = consume_agent_stream(intent_agent.stream(prompt, quick_requests))
        if intent_result is None:
            intent_result = {'allowed': False, 'error': '자산 추출 중 오류가 발생했습니다.'}

        backend_logger.info("Intent Result: %s", intent_result)

        if not intent_result.get('allowed'):
            backend_logger.warning("Request blocked by guardrail")
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             intent_result.get('error', 'Request blocked'), 0, processing_time_ms)
            stream_error(intent_result.get('error', 'Request blocked'))
            stream_complete('error')
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
            stream_error('분석할 자산을 찾을 수 없습니다.')
            stream_complete('error')
            return JsonResponse({
                'ok': False,
                'error': '분석할 자산을 찾을 수 없습니다.',
                'logs': all_logs
            }, status=400)

        manual_assets = _build_manual_assets(custom_assets, calculation_method)
        if manual_assets:
            merged_assets, added_assets = _merge_asset_lists(assets, manual_assets)
            if added_assets:
                assets = merged_assets
                intent_result['assets'] = assets
                added_labels = ', '.join(a.get('label', a.get('id', '')) for a in added_assets)
                append_log(f"[의도 분석] 사용자 지정 자산 추가: {added_labels}")
        validated_assets = assets

        # Agent 2: Price Retriever
        backend_logger.info("STEP 2: Running PriceRetrieverAgent")
        retriever_agent = PriceRetrieverAgent()
        price_data_map = consume_agent_stream(retriever_agent.stream(validated_assets, start_year, end_year)) or {}

        backend_logger.info("Price Data Map Keys: %s", list(price_data_map.keys()) if price_data_map else "EMPTY")

        if not price_data_map:
            backend_logger.error("No price data retrieved - returning 502")
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '자산 데이터를 가져올 수 없습니다.', len(assets), processing_time_ms)
            stream_error('자산 데이터를 가져올 수 없습니다. (티커를 확인해주세요)')
            stream_complete('error')
            return JsonResponse({
                'ok': False,
                'error': '자산 데이터를 가져올 수 없습니다. (티커를 확인해주세요)',
                'logs': all_logs
            }, status=502)

        # Agent 3: Calculator
        backend_logger.info("STEP 3: Running CalculatorAgent with method: %s", calculation_method)
        calculator_agent = CalculatorAgent()
        calc_result = consume_agent_stream(
            calculator_agent.stream(price_data_map, start_year, end_year, calculation_method, include_dividends=include_dividends)
        ) or {}
        series_data = calc_result.get('series', [])
        chart_data_table = calc_result.get('table', [])
        summary = calc_result.get('summary', '')

        if not series_data:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '유효한 수익률 데이터를 계산할 수 없습니다.', len(assets), processing_time_ms)
            stream_error('유효한 수익률 데이터를 계산할 수 없습니다.')
            stream_complete('error')
            return JsonResponse({
                'ok': False,
                'error': '유효한 수익률 데이터를 계산할 수 없습니다.',
                'logs': all_logs
            }, status=502)

        # Agent 4: Analysis (Generate narrative summary)
        backend_logger.info("STEP 4: Running AnalysisAgent")
        analysis_agent = AnalysisAgent()
        combined_prompt_for_analysis = ' '.join(([prompt] if prompt else []) + quick_requests)
        analysis_summary = consume_agent_stream(
            analysis_agent.stream(series_data, start_year, end_year, calculation_method, combined_prompt_for_analysis)
        ) or ''

        # Cache Result (if context_key is present)
        usd_krw_rate = get_cached_usdkrw_rate()
        if context_key in ['safe_assets', 'us_bigtech']:
            _save_to_cache(context_key, start_year, end_year, series_data, usd_krw_rate)

        # Log successful query
        processing_time_ms = int((time.time() - start_time) * 1000)
        _log_finance_query(user_identifier, prompt, quick_requests, context_key, True,
                         '', len(assets), processing_time_ms)
        stream_complete('ok')

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
            'include_dividends': include_dividends,
        }

        return JsonResponse(response_payload)


def _finance_analysis_stream(prompt, quick_requests, custom_assets, context_key, start_year, end_year, user_identifier, start_time, include_dividends=False):
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
        intent_result = None
        for event in intent_agent.stream(prompt, quick_requests):
            if event['type'] == 'log':
                yield send_log(event['message'])
            elif event['type'] == 'result':
                intent_result = event['data']

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

        manual_assets = _build_manual_assets(custom_assets, calculation_method)
        if manual_assets:
            merged_assets, added_assets = _merge_asset_lists(assets, manual_assets)
            if added_assets:
                assets = merged_assets
                intent_result['assets'] = assets
                added_labels = ', '.join(a.get('label', a.get('id', '')) for a in added_assets)
                yield send_log(f"[의도 분석] 사용자 지정 자산 추가: {added_labels}")

        validated_assets = assets

        # Agent 2: Price Retriever
        retriever_agent = PriceRetrieverAgent()
        price_data_map = {}
        for event in retriever_agent.stream(validated_assets, start_year, end_year):
            if event['type'] == 'log':
                yield send_log(event['message'])
            elif event['type'] == 'result':
                price_data_map = event['data']

        if not price_data_map:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '자산 데이터를 가져올 수 없습니다.', len(assets), processing_time_ms)
            yield send_error('자산 데이터를 가져올 수 없습니다.')
            return

        # Agent 3: Calculator
        calculator_agent = CalculatorAgent()
        series_data = []
        chart_data_table = []
        summary = ''
        for event in calculator_agent.stream(price_data_map, start_year, end_year, calculation_method, include_dividends=include_dividends):
            if event['type'] == 'log':
                yield send_log(event['message'])
            elif event['type'] == 'result':
                result_payload = event['data']
                series_data = result_payload.get('series', [])
                chart_data_table = result_payload.get('table', [])
                summary = result_payload.get('summary', '')

        if not series_data:
            processing_time_ms = int((time.time() - start_time) * 1000)
            _log_finance_query(user_identifier, prompt, quick_requests, context_key, False,
                             '유효한 수익률 데이터를 계산할 수 없습니다.', len(assets), processing_time_ms)
            yield send_error('유효한 수익률 데이터를 계산할 수 없습니다.')
            return

        # Agent 4: Analysis (Generate narrative summary)
        analysis_agent = AnalysisAgent()
        combined_prompt_for_analysis = ' '.join(([prompt] if prompt else []) + quick_requests)
        analysis_summary = ''
        for event in analysis_agent.stream(series_data, start_year, end_year, calculation_method, combined_prompt_for_analysis):
            if event['type'] == 'log':
                yield send_log(event['message'])
            elif event['type'] == 'result':
                analysis_summary = event['data']

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
            'include_dividends': include_dividends,
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
def finance_resolve_custom_asset_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    name = (payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': '자산명을 입력해주세요.'}, status=400)

    config = _find_known_asset_config(name, name)
    if config:
        asset = {
            'id': config.get('id') or name,
            'label': config.get('label') or name,
            'ticker': config.get('ticker') or config.get('id') or name,
            'category': config.get('category'),
            'unit': config.get('unit')
        }
        _ensure_asset_prices_cached(asset)
        return JsonResponse({'ok': True, 'asset': asset})

    candidate = _lookup_ticker_with_llm(name, name)
    if candidate:
        asset = {
            'id': candidate.get('id') or name,
            'label': candidate.get('label') or name,
            'ticker': candidate.get('ticker') or candidate.get('id') or name,
            'category': candidate.get('category'),
            'unit': candidate.get('unit')
        }
        _ensure_asset_prices_cached(asset)
        return JsonResponse({'ok': True, 'asset': asset})

    suggestion = _suggest_related_asset(name)
    if suggestion:
        asset = {
            'id': suggestion.get('id') or name,
            'label': suggestion.get('label') or name,
            'ticker': suggestion.get('ticker') or suggestion.get('id') or name,
            'category': suggestion.get('category'),
            'unit': suggestion.get('unit')
        }
        _ensure_asset_prices_cached(asset)
        return JsonResponse({'ok': True, 'asset': asset})

    return JsonResponse({
        'ok': False,
        'error': f"'{name}'과(와) 관련된 티커나 대체 종목을 찾지 못했습니다."
    }, status=404)


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
        current_category = config.get('category') or entry.get('category') or ''
        current_unit = (config.get('unit') or entry.get('unit') or '').upper()
        ticker_upper = (config.get('ticker') or current_result_entry['id'] or '').upper()
        if current_category == '국내 주식' or ticker_upper.endswith(('.KS', '.KQ', '.KL', '.KR')):
            current_unit = 'KRW'
        current_result_entry['unit'] = current_unit
        current_result_entry['category'] = current_category
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

EXCLUDED_AGENT_PROMPT_TYPES = {
    # Intent classifier (asset extraction) prompt is no longer managed via admin UI.
    'intent_classifier',
}


def _cleanup_excluded_agent_prompts():
    """Remove agent prompts that should not be edited via the admin page."""
    if not EXCLUDED_AGENT_PROMPT_TYPES:
        return
    from .models import AgentPrompt
    AgentPrompt.objects.filter(agent_type__in=EXCLUDED_AGENT_PROMPT_TYPES).delete()


def _get_or_create_default_agent_prompts():
    """Initialize default agent prompts if they don't exist"""
    from .models import AgentPrompt

    _cleanup_excluded_agent_prompts()

    defaults = {
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

    _cleanup_excluded_agent_prompts()

    if request.method == 'GET':
        # Initialize defaults if empty
        if AgentPrompt.objects.count() == 0:
            _get_or_create_default_agent_prompts()

        prompts = AgentPrompt.objects.exclude(agent_type__in=EXCLUDED_AGENT_PROMPT_TYPES)
        return JsonResponse({
            'ok': True,
            'prompts': [p.as_dict() for p in prompts]
        })

    elif request.method == 'POST':
        # Initialize defaults
        created = _get_or_create_default_agent_prompts()
        prompts = AgentPrompt.objects.exclude(agent_type__in=EXCLUDED_AGENT_PROMPT_TYPES)
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
    if agent_type in EXCLUDED_AGENT_PROMPT_TYPES:
        return JsonResponse({
            'ok': False,
            'error': f'Agent prompt not supported: {agent_type}'
        }, status=404)

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

    elif request.method == 'DELETE':
        try:
            prompt = AgentPrompt.objects.get(agent_type=agent_type)
            prompt.delete()
            return JsonResponse({'ok': True})
        except AgentPrompt.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': f'Agent prompt not found: {agent_type}'
            }, status=404)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


DEFAULT_COMPATIBILITY_AGENT_KEY = 'saju_bitcoin'

DEFAULT_COMPATIBILITY_REPORT_TEMPLATES = [
    {
        'key': 'user_vs_bitcoin',
        'label': '개별 사용자와 비트코인의 궁합',
        'description': '',
        'sort_order': 1,
        'content': """{{SUBJECT_NAME}}의 사주와 비트코인 궁합을 분석하세요.{{SUBJECT_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 800~1000자. 시스템 프롬프트의 요구(비트코인 커리어·재물·인간관계·전략)를 빠짐없이 반영하고, 문단 사이 공백 없이 촘촘히 작성하세요.
2. **문체**: 모든 문장은 ‘~입니다’ 체로 작성하고, 각 항목의 핵심 문장은 **제목: 내용** 형태의 문장으로 시작하세요.

3. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 프로필 브리핑
     - 일간: …
     - 오행 핵심 기운: …
     - 직업/역할: …
   - ## 커리어 & 재물
     - 항목 2~3개로 비트코인 커리어와 재물 흐름 서술
   - ## 인간관계
     - 협업/대인관계 흐름과 리스크를 항목 2개로 정리
   - ## 비트코인 전략 체크리스트
     - 1. …
     - 2. …
     - 3. …

4. **근거 & 어휘**: 저장된 사주·스토리·오행 분포에서 최소 2가지 근거를 명시하고, 한자 대신 풀이형 표현을 사용하세요.

5. **금지 사항**: 인사말, 잡담, “모르겠다” 류 표현, 표 생략, 섹션 누락 금지.""",
    },
    {
        'key': 'team_vs_bitcoin',
        'label': '두 사용자의 비트코인 궁합',
        'description': '',
        'sort_order': 2,
        'content': """{{USER_NAME}}와(과) {{TARGET_NAME}}가 함께 비트코인 투자할 때의 두 사람 궁합을 분석하세요.{{TEAM_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 700~950자. 두 사람의 사주 핵심 기운, 투자 습관, 협업 흐름, 전략 포지셔닝을 모두 다루세요.
2. **문체**: 모든 문장을 ‘~입니다’ 체로 작성하고, 각 문단의 첫 문장은 '제목: 내용' 구조로 요약하세요.

3. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 두 사람 특성 & 호흡
     - 사용자 이름과 비교 대상 이름을 모두 언급하는 항목 2~3개
   - ## 커리어 & 재물 시너지
     - 항목 2개, 각 문장에 어느 사람이 어떤 역할을 맡는지 명시
   - ## 인간관계/커뮤니케이션
     - 항목 2개, 갈등 방지법 포함
   - ## 두 사람 비트코인 전략 체크리스트
     - 1. 역할 분담 규칙
     - 2. 의사결정 루틴
     - 3. 리스크 통제법

4. **근거**: 각 섹션에서 최소 한 번씩 두 사람의 사주 요약 또는 스토리에서 직접 언급한 특징을 인용하세요.

5. **금지 사항**: 인사말, 모호한 표현, 생략표, 섹션 누락 금지.""",
    },
]


def _resolve_openai_model_name():
    """Return the raw OpenAI model name (without provider prefix)."""
    value = getattr(settings, 'COMPATIBILITY_OPENAI_MODEL', 'gpt-5-mini')
    if ':' in value:
        _, value = value.split(':', 1)
    return value.strip()


def _get_default_compatibility_prompt_config(agent_key):
    normalized_key = (agent_key or DEFAULT_COMPATIBILITY_AGENT_KEY).strip()
    base_model = _resolve_openai_model_name()
    default_model_name = f'openai:{base_model}'
    defaults = {
        'saju_bitcoin': {
            'name': '비트코인 궁합 에이전트',
            'description': '비트코인을 디지털 금으로 바라보는 사주 분석 전문가',
            'system_prompt': COMPATIBILITY_AGENT_DEFAULT_PROMPT.strip(),
            'model_name': default_model_name,
            'is_active': True,
            'temperature': 0.2,
            'top_p': 0.9,
            'presence_penalty': 0.6,
            'frequency_penalty': 0.4,
            'max_tokens': 700,
        },
        'story_extractor': {
            'name': '스토리 추출 에이전트',
            'description': '선택된 인물의 알려진 행보와 특징을 서사형으로 정리합니다.',
            'system_prompt': STORY_EXTRACTOR_AGENT_PROMPT.strip(),
            'model_name': default_model_name,
            'is_active': True,
            'temperature': 0.6,
            'top_p': 0.9,
            'presence_penalty': 0.1,
            'frequency_penalty': 0.1,
            'max_tokens': 600,
        },
        'saju_analysis': {
            'name': '사주 추론 에이전트',
            'description': '인물 서사를 기반으로 투자 성향과 오행 핵심 기운을 추론합니다.',
            'system_prompt': SAJU_AGENT_ANALYSIS_PROMPT.strip(),
            'model_name': default_model_name,
            'is_active': True,
            'temperature': 0.4,
            'top_p': 0.85,
            'presence_penalty': 0.2,
            'frequency_penalty': 0.2,
            'max_tokens': 700,
        },
        'pair_compatibility': {
            'name': '두 사람 궁합 에이전트',
            'description': '두 명의 사주 요약을 비교해 관계 전략을 제시합니다.',
            'system_prompt': COMPATIBILITY_PAIR_AGENT_PROMPT.strip(),
            'model_name': default_model_name,
            'is_active': True,
            'temperature': 0.5,
            'top_p': 0.9,
            'presence_penalty': 0.3,
            'frequency_penalty': 0.3,
            'max_tokens': 800,
        },
        'highlight_story': {
            'name': '사주 하이라이트 에이전트',
            'description': '사주 분석 결과에서 핵심 구절만 형광펜으로 표시합니다.',
            'system_prompt': HIGHLIGHT_ANALYZER_PROMPT.strip(),
            'model_name': default_model_name,
            'is_active': True,
            'temperature': 0.3,
            'top_p': 0.8,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0,
            'max_tokens': 800,
        },
    }

    if normalized_key in defaults:
        return defaults[normalized_key]

    fallback = dict(defaults['saju_bitcoin'])
    fallback.update({
        'name': f'{normalized_key} 에이전트',
        'description': '사용자 정의 궁합 에이전트',
    })
    return fallback


def _get_or_create_compatibility_prompt(agent_key=None):
    """Ensure the requested compatibility agent prompt exists."""
    resolved_key = (agent_key or DEFAULT_COMPATIBILITY_AGENT_KEY).strip()
    prompt, _ = CompatibilityAgentPrompt.objects.get_or_create(
        agent_key=resolved_key,
        defaults=_get_default_compatibility_prompt_config(resolved_key)
    )
    _ensure_prompt_default_model(prompt)
    return prompt


def _ensure_prompt_default_model(prompt):
    """Force compatibility prompts to use the default OpenAI GPT-5 Mini model."""
    if not prompt:
        return
    desired_model = f'openai:{_resolve_openai_model_name()}'
    if prompt.model_name != desired_model:
        prompt.model_name = desired_model
        prompt.save(update_fields=['model_name', 'updated_at'])


def _ensure_default_report_templates():
    try:
        for template in DEFAULT_COMPATIBILITY_REPORT_TEMPLATES:
            CompatibilityReportTemplate.objects.get_or_create(
                key=template['key'],
                defaults=template,
            )
    except (OperationalError, ProgrammingError):
        logger.warning('[Compatibility] Report template table unavailable - default seeding skipped')


def _run_compatibility_agent(prompt, user_context, temperature=0.7):
    """Run compatibility agent with either OpenAI or Gemini based on configuration."""
    # Extract all parameters from the prompt object
    model_name_from_prompt = (prompt.model_name or '').strip()
    temperature_from_prompt = prompt.temperature
    top_p_from_prompt = prompt.top_p
    presence_penalty_from_prompt = prompt.presence_penalty
    frequency_penalty_from_prompt = prompt.frequency_penalty
    max_tokens_from_prompt = prompt.max_tokens

    # Use the temperature passed from frontend payload if available, otherwise use prompt's config
    # The 'temperature' argument to this function comes from payload.get('temperature', 0.7)
    resolved_temperature = temperature

    # Determine provider based on model_name_from_prompt
    default_provider = getattr(settings, 'COMPATIBILITY_DEFAULT_PROVIDER', 'openai').lower()
    provider = default_provider
    model_name = model_name_from_prompt # Use model name from prompt config
    
    if ':' in model_name:
        provider, model_name = model_name.split(':', 1)
        provider = provider.lower().strip()
        model_name = model_name.strip()

    # Validate model_name matches provider
    # If provider is gemini but model_name looks like an OpenAI model, clear it
    if provider == 'gemini' and model_name:
        openai_models = ['gpt-3.5', 'gpt-4', 'gpt-4o']
        if any(model_name.startswith(prefix) for prefix in openai_models):
            logger.warning('[Compatibility] Model "%s" is OpenAI model but provider is gemini, using default Gemini model', model_name)
            model_name = ''  # Use default Gemini model

    # If provider is openai but model_name looks like a Gemini model, clear it
    if provider == 'openai' and model_name:
        gemini_models = ['gemini-', 'gemma-']
        if any(model_name.startswith(prefix) for prefix in gemini_models):
            logger.warning('[Compatibility] Model "%s" is Gemini model but provider is openai, using default OpenAI model', model_name)
            model_name = ''  # Use default OpenAI model

    logger.info('[Compatibility] 에이전트 실행 - provider=%s, model_name=%s, temp=%.2f, top_p=%.2f, pres_p=%.2f, freq_p=%.2f, max_tokens=%s',
                provider, model_name, resolved_temperature, top_p_from_prompt,
                presence_penalty_from_prompt, frequency_penalty_from_prompt, max_tokens_from_prompt)

    # Call the appropriate API with fallback
    if provider == 'gemini':
        try:
            return _call_gemini_chat_model(
                model_name,
                prompt.system_prompt,
                user_context,
                temperature=resolved_temperature,
                top_p=top_p_from_prompt,
                max_tokens=max_tokens_from_prompt
            )
        except Exception as gemini_error:
            # Check if it's a quota/rate limit error
            error_str = str(gemini_error)
            if 'ResourceExhausted' in str(type(gemini_error)) or '429' in error_str or 'quota' in error_str.lower():
                logger.warning('[Compatibility] Gemini API quota exceeded, falling back to OpenAI')
                try:
                    fallback_openai_model = _resolve_openai_model_name()
                    return _call_openai_chat_model(
                        fallback_openai_model,
                        prompt.system_prompt,
                        user_context,
                        temperature=resolved_temperature,
                        top_p=top_p_from_prompt,
                        presence_penalty=presence_penalty_from_prompt,
                        frequency_penalty=frequency_penalty_from_prompt,
                        max_tokens=max_tokens_from_prompt
                    )
                except Exception as openai_error:
                    logger.error('[Compatibility] OpenAI fallback also failed: %s', openai_error)
                    # Re-raise the original Gemini error
                    raise gemini_error
            else:
                # Not a quota error, re-raise
                raise
    elif provider == 'openai':
        return _call_openai_chat_model(
            model_name,
            prompt.system_prompt,
            user_context,
            temperature=resolved_temperature,
            top_p=top_p_from_prompt,
            presence_penalty=presence_penalty_from_prompt,
            frequency_penalty=frequency_penalty_from_prompt,
            max_tokens=max_tokens_from_prompt
        )
    else:
        # Fallback to gemini as default
        logger.warning('[Compatibility] Unknown provider "%s", falling back to gemini', provider)
        try:
            return _call_gemini_chat_model(
                model_name,
                prompt.system_prompt,
                user_context,
                temperature=resolved_temperature,
                top_p=top_p_from_prompt,
                max_tokens=max_tokens_from_prompt
            )
        except Exception as gemini_error:
            error_str = str(gemini_error)
            if 'ResourceExhausted' in str(type(gemini_error)) or '429' in error_str or 'quota' in error_str.lower():
                logger.warning('[Compatibility] Gemini API quota exceeded, falling back to OpenAI')
                fallback_openai_model = _resolve_openai_model_name()
                return _call_openai_chat_model(
                    fallback_openai_model,
                    prompt.system_prompt,
                    user_context,
                    temperature=resolved_temperature,
                    top_p=top_p_from_prompt,
                    presence_penalty=presence_penalty_from_prompt,
                    frequency_penalty=frequency_penalty_from_prompt,
                    max_tokens=max_tokens_from_prompt
                )
            else:
                raise


@csrf_exempt
def compatibility_prompt_view(request):
    """Public endpoint to fetch the current compatibility agent prompt."""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    agent_key = request.GET.get('agent_key') or DEFAULT_COMPATIBILITY_AGENT_KEY
    prompt = _get_or_create_compatibility_prompt(agent_key)
    return JsonResponse({
        'ok': True,
        'prompt': prompt.as_dict()
    })


@csrf_exempt
def compatibility_admin_prompt_view(request):
    """Admin-only endpoint to view or update the compatibility agent prompt."""
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    base_agent_key = request.GET.get('agent_key') or DEFAULT_COMPATIBILITY_AGENT_KEY

    if request.method == 'GET':
        prompt = _get_or_create_compatibility_prompt(base_agent_key)
        return JsonResponse({'ok': True, 'prompt': prompt.as_dict()})

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    agent_key = payload.get('agent_key') or base_agent_key
    prompt = _get_or_create_compatibility_prompt(agent_key)

    if request.method in ['PUT', 'PATCH']:
        updated_fields = []
        if 'name' in payload:
            prompt.name = payload['name']
            updated_fields.append('name')
        if 'description' in payload:
            prompt.description = payload['description']
            updated_fields.append('description')
        if 'model_name' in payload:
            prompt.model_name = payload['model_name']
            updated_fields.append('model_name')
        if 'is_active' in payload:
            prompt.is_active = bool(payload['is_active'])
            updated_fields.append('is_active')
        if 'system_prompt' in payload:
            new_prompt = payload['system_prompt']
            if isinstance(new_prompt, str):
                new_prompt = new_prompt.strip('\ufeff')  # Remove accidental BOM
            if new_prompt != prompt.system_prompt:
                prompt.system_prompt = new_prompt
                prompt.version += 1
                updated_fields.extend(['system_prompt', 'version'])

        if updated_fields:
            fields = list({field for field in updated_fields})
            if 'updated_at' not in fields:
                fields.append('updated_at')
            prompt.save(update_fields=fields)

        return JsonResponse({'ok': True, 'prompt': prompt.as_dict()})

    if request.method == 'POST':
        action = (payload.get('action') or '').lower()
        if action == 'reset':
            defaults = _get_default_compatibility_prompt_config(agent_key)
            prompt.name = defaults['name']
            prompt.description = defaults['description']
            prompt.system_prompt = defaults['system_prompt']
            prompt.is_active = defaults['is_active']
            prompt.model_name = defaults['model_name']
            prompt.version += 1
            prompt.save(update_fields=['name', 'description', 'system_prompt', 'is_active', 'model_name', 'version', 'updated_at'])
            return JsonResponse({'ok': True, 'prompt': prompt.as_dict()})
        return JsonResponse({'ok': False, 'error': 'Unsupported action'}, status=400)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


from .saju_util import calculate_saju, analyze_elements

@csrf_exempt
def compatibility_agent_generate_view(request):
    """Call the compatibility agent (OpenAI or Gemini) to produce narrative text."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    payload = _load_json_body(request)
    if payload is None:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    agent_key = (payload.get('agent_key') or DEFAULT_COMPATIBILITY_AGENT_KEY).strip()

    # 1. Extract context or build it from structured data
    context = (payload.get('context') or '').strip()
    structured = payload.get('data')  # Expecting { 'birthdate': 'YYYY-MM-DD', 'birth_time': 'HH:MM', ... }

    if not context and structured:
        context = json.dumps(structured, ensure_ascii=False, indent=2)

    # 2. Perform explicit Saju calculation if requested for the Bitcoin agent
    if agent_key == 'saju_bitcoin' and structured and 'birthdate' in structured:
        try:
            bd_str = structured['birthdate']
            bt_str = structured.get('birth_time')

            bd = datetime.strptime(bd_str, '%Y-%m-%d').date()
            hour = None
            minute = None
            if bt_str:
                try:
                    bt = datetime.strptime(bt_str, '%H:%M').time()
                    hour = bt.hour
                    minute = bt.minute
                except ValueError:
                    pass

            pillars = calculate_saju(bd.year, bd.month, bd.day, hour, minute)
            elements = analyze_elements(pillars)

            saju_info = (
                f"\n\n[시스템 자동 계산된 사주 정보 - 이 정보를 최우선으로 신뢰하세요]\n"
                f"양력 생년월일: {bd_str} {bt_str if bt_str else ''}\n"
                f"년주(Year Pillar): {pillars['year_pillar']}\n"
                f"월주(Month Pillar): {pillars['month_pillar']}\n"
                f"일주(Day Pillar): {pillars['day_pillar']}\n"
                f"시주(Time Pillar): {pillars['time_pillar'] or '알 수 없음'}\n"
                f"오행 분포: 목({elements['wood']}) 화({elements['fire']}) 토({elements['earth']}) 금({elements['metal']}) 수({elements['water']})\n"
                f"일간(Day Master): {pillars['day_pillar'][0]} (이것이 본원입니다)\n"
            )

            if not context:
                context = json.dumps(structured, ensure_ascii=False, indent=2)

            context = saju_info + "\n" + context

        except Exception as e:
            logger.error(f"[Compatibility] Saju calculation failed: {e}")

    if not context:
        return JsonResponse({'ok': False, 'error': 'context is required'}, status=400)

    cache_payload = payload.get('cache')
    cache_meta = None
    cache_entry = None
    if cache_payload:
        cache_meta, cache_entry = _resolve_cache_metadata(agent_key, cache_payload, context)
        if cache_entry and cache_meta:
            logger.info('[Compatibility:%s] Cache hit - category=%s key=%s', agent_key, cache_meta.get('category'), cache_meta.get('cache_key'))
            cache_metadata = cache_entry.metadata or {}
            return JsonResponse({
                'ok': True,
                'narrative': cache_entry.response_text,
                'provider': cache_metadata.get('provider') or 'cache',
                'model': cache_metadata.get('model') or cache_entry.agent_key,
                'agent_key': agent_key,
                'cached': True,
                'cache_key': cache_entry.cache_key,
                'cache_category': cache_entry.category,
            })

    temp = payload.get('temperature', 0.7)
    try:
        temperature = float(temp)
    except (ValueError, TypeError):
        temperature = 0.7

    temperature = max(0, min(1.2, temperature))

    prompt = _get_or_create_compatibility_prompt(agent_key)
    if not prompt.is_active:
        return JsonResponse({'ok': False, 'error': 'Compatibility agent is inactive.'}, status=503)

    try:
        logger.info('[Compatibility:%s] 에이전트 요청 시작 - context_len=%d', agent_key, len(context))
        logger.info('[Compatibility:%s] System Prompt Preview: %s...', agent_key, prompt.system_prompt[:100].replace('\n', ' '))
        narrative, provider, model_used = _run_compatibility_agent(prompt, context, temperature)
    except ValueError as exc:
        logger.warning('[Compatibility:%s] 에이전트 입력 오류: %s', agent_key, exc)
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except Exception as exc:  # pragma: no cover - network failures
        logger.exception("[Compatibility:%s] Agent request failed", agent_key)
        error_msg = str(exc)
        # Gemini 할당량 초과 에러 처리
        if 'ResourceExhausted' in str(type(exc)) or '429' in error_msg or 'quota' in error_msg.lower():
            return JsonResponse({
                'ok': False,
                'error': 'API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.',
                'error_type': 'quota_exceeded'
            }, status=429)
        # OpenAI API key 미설정 에러 처리
        if 'OPENAI_API_KEY is not configured' in error_msg:
            return JsonResponse({
                'ok': False,
                'error': 'OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요.',
                'error_type': 'api_key_missing'
            }, status=503)
        return JsonResponse({'ok': False, 'error': 'Agent request failed'}, status=502)

    if cache_meta and narrative:
        _store_cache_entry(agent_key, cache_meta, narrative, provider, model_used)

    return JsonResponse({
        'ok': True,
        'narrative': narrative,
        'provider': provider,
        'model': model_used,
        'prompt_version': prompt.version,
        'agent_key': agent_key,
    })


@csrf_exempt
def compatibility_analysis_save_view(request):
    """Save a compatibility analysis result to the database"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST only'}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    required_fields = ['birthdate', 'element', 'zodiac', 'yin_yang', 'score', 'rating', 'narrative']
    for field in required_fields:
        if field not in payload:
            return JsonResponse({'ok': False, 'error': f'Missing required field: {field}'}, status=400)

    try:
        from datetime import datetime as dt
        from .models import CompatibilityAnalysis

        # Parse birthdate
        birthdate = dt.strptime(payload['birthdate'], '%Y-%m-%d').date()

        # Parse birth_time if provided
        birth_time = None
        if payload.get('birth_time'):
            birth_time = dt.strptime(payload['birth_time'], '%H:%M').time()

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user_ip = x_forwarded_for.split(',')[0]
        else:
            user_ip = request.META.get('REMOTE_ADDR')

        # Create the analysis record
        analysis = CompatibilityAnalysis.objects.create(
            birthdate=birthdate,
            birth_time=birth_time,
            gender=payload.get('gender', ''),
            element=payload['element'],
            zodiac=payload['zodiac'],
            yin_yang=payload['yin_yang'],
            score=int(payload['score']),
            rating=payload['rating'],
            narrative=payload['narrative'],
            user_ip=user_ip
        )

        return JsonResponse({'ok': True, 'id': analysis.id, 'analysis': analysis.as_dict()})

    except Exception as e:
        logger.exception("Error saving compatibility analysis")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@csrf_exempt
def compatibility_analysis_list_view(request):
    """List compatibility analysis results with pagination (admin only)"""
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    try:
        from django.core.paginator import Paginator
        from .models import CompatibilityAnalysis

        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        per_page = min(per_page, 100)  # Max 100 per page

        # Get all analyses ordered by creation time (newest first)
        analyses = CompatibilityAnalysis.objects.all()

        # Apply pagination
        paginator = Paginator(analyses, per_page)
        page_obj = paginator.get_page(page)

        return JsonResponse({
            'ok': True,
            'analyses': [analysis.as_dict() for analysis in page_obj.object_list],
            'pagination': {
                'page': page_obj.number,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    except Exception as e:
        logger.exception("Error listing compatibility analyses")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def _ensure_default_compatibility_presets():
    defaults = [
        {
            'label': '사용자',
            'description': '나만의 정보를 직접 입력해 궁합을 계산하세요.',
            'birthdate': None,
            'gender': '',
            'image_url': '',
            'sort_order': 0,
        },
        {
            'label': '마이클 세일러',
            'birthdate': datetime(1965, 2, 4).date(),
            'description': 'MicroStrategy CEO이자 비트코인 트리플 맥시.',
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Michael_Saylor_2016.jpg/640px-Michael_Saylor_2016.jpg',
            'sort_order': 1,
        },
        {
            'label': '도널드 트럼프',
            'birthdate': datetime(1946, 6, 14).date(),
            'description': '전 미 대통령으로 친비트코인 행보를 강화 중.',
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/640px-Donald_Trump_official_portrait.jpg',
            'sort_order': 2,
        },
        {
            'label': '래리 핑크',
            'birthdate': datetime(1952, 11, 2).date(),
            'description': '블랙록 CEO, 기관 비트코인 수요를 이끄는 인물.',
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Laurence_D._Fink.jpg/640px-Laurence_D._Fink.jpg',
            'sort_order': 3,
        },
        {
            'label': '제이미 다이먼',
            'birthdate': datetime(1956, 3, 13).date(),
            'description': 'JP모건 CEO, 비판과 도입을 오가는 상징적 인물.',
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Jamie_Dimon_2018.jpg/640px-Jamie_Dimon_2018.jpg',
            'sort_order': 4,
        },
        {
            'label': '비탈릭 부테린',
            'birthdate': datetime(1994, 1, 31).date(),
            'description': '이더리움 창시자이자 크립토 철학자.',
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg/640px-Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg',
            'sort_order': 5,
        },
    ]
    for preset in defaults:
        defaults_payload = preset.copy()
        obj, created = CompatibilityQuickPreset.objects.get_or_create(label=preset['label'], defaults=defaults_payload)
        if not created:
            update_fields = []
            if preset.get('description') and not obj.description:
                obj.description = preset['description']
                update_fields.append('description')
            if obj.sort_order is None:
                obj.sort_order = preset['sort_order']
                update_fields.append('sort_order')
            if preset.get('image_url') and not obj.image_url:
                obj.image_url = preset['image_url']
                update_fields.append('image_url')
            if update_fields:
                obj.save(update_fields=update_fields)


@csrf_exempt
def compatibility_report_templates_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    try:
        _ensure_default_report_templates()
        key_filter = (request.GET.get('key') or '').strip()
        templates = CompatibilityReportTemplate.objects.all().order_by('sort_order', 'id')
        if key_filter:
            templates = templates.filter(key=key_filter)

        payload = [template.as_dict() for template in templates]
    except (OperationalError, ProgrammingError):
        logger.warning('[Compatibility] Report template table missing - returning empty list')
        payload = []

    return JsonResponse({'ok': True, 'templates': payload})


@csrf_exempt
def compatibility_admin_report_template_detail_view(request, key):
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    try:
        _ensure_default_report_templates()
        template = CompatibilityReportTemplate.objects.get(key=key)
    except (OperationalError, ProgrammingError):
        return JsonResponse({'ok': False, 'error': 'Report template storage unavailable. Run migrations?'}, status=500)
    except CompatibilityReportTemplate.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Template not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'template': template.as_dict()})

    if request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        updated_fields = []
        if 'label' in payload and payload['label'] is not None:
            template.label = payload['label'].strip()
            updated_fields.append('label')
        if 'description' in payload and payload['description'] is not None:
            template.description = payload['description'].strip()
            updated_fields.append('description')
        if 'content' in payload and payload['content'] is not None:
            template.content = payload['content']
            updated_fields.append('content')
        if 'sort_order' in payload and payload['sort_order'] is not None:
            template.sort_order = int(payload['sort_order'])
            updated_fields.append('sort_order')

        if updated_fields:
            template.save(update_fields=updated_fields + ['updated_at'])
        return JsonResponse({'ok': True, 'template': template.as_dict()})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def compatibility_quick_presets_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)
    try:
        _ensure_default_compatibility_presets()
        presets = CompatibilityQuickPreset.objects.filter(is_active=True).order_by('sort_order', 'id')
        return JsonResponse({'ok': True, 'presets': [preset.as_dict() for preset in presets]})
    except Exception as e:
        logger.exception('[Compatibility] quick-presets view failed')
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@csrf_exempt
def compatibility_admin_quick_presets_view(request):
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)

    if request.method == 'GET':
        _ensure_default_compatibility_presets()
        presets = CompatibilityQuickPreset.objects.all().order_by('sort_order', 'id')
        return JsonResponse({'ok': True, 'presets': [preset.as_dict() for preset in presets]})

    if request.method == 'POST':
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        label = (payload.get('label') or '').strip()
        birthdate_str = (payload.get('birthdate') or '').strip()
        if not label or not birthdate_str:
            return JsonResponse({'ok': False, 'error': 'label과 birthdate는 필수입니다.'}, status=400)

        try:
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'birthdate 형식은 YYYY-MM-DD 이어야 합니다.'}, status=400)

        birth_time = None
        birth_time_str = (payload.get('birth_time') or '').strip()
        if birth_time_str:
            try:
                birth_time = datetime.strptime(birth_time_str, '%H:%M').time()
            except ValueError:
                return JsonResponse({'ok': False, 'error': 'birth_time 형식은 HH:MM 이어야 합니다.'}, status=400)

        sort_order = payload.get('sort_order')
        if sort_order is None:
            max_order = CompatibilityQuickPreset.objects.aggregate(max_order=Max('sort_order'))['max_order'] or 0
            sort_order = max_order + 1

        preset = CompatibilityQuickPreset.objects.create(
            label=label,
            description=(payload.get('description') or '').strip(),
            birthdate=birthdate,
            birth_time=birth_time,
            gender=(payload.get('gender') or '').strip(),
            image_url=(payload.get('image_url') or '').strip(),
            sort_order=int(sort_order),
            is_active=bool(payload.get('is_active', True)),
        )
        return JsonResponse({'ok': True, 'preset': preset.as_dict()}, status=201)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def compatibility_admin_quick_preset_detail_view(request, pk):
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    try:
        preset = CompatibilityQuickPreset.objects.get(pk=pk)
    except CompatibilityQuickPreset.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Preset not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'preset': preset.as_dict()})

    if request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        if 'label' in payload and payload['label'] is not None:
            preset.label = payload['label'].strip()
        if 'birthdate' in payload and payload['birthdate']:
            try:
                preset.birthdate = datetime.strptime(payload['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'ok': False, 'error': 'birthdate 형식은 YYYY-MM-DD 이어야 합니다.'}, status=400)
        if 'birth_time' in payload:
            birth_time_value = (payload.get('birth_time') or '').strip()
            if birth_time_value:
                try:
                    preset.birth_time = datetime.strptime(birth_time_value, '%H:%M').time()
                except ValueError:
                    return JsonResponse({'ok': False, 'error': 'birth_time 형식은 HH:MM 이어야 합니다.'}, status=400)
            else:
                preset.birth_time = None
        if 'gender' in payload and payload['gender'] is not None:
            preset.gender = payload['gender'].strip()
        if 'description' in payload and payload['description'] is not None:
            preset.description = payload['description'].strip()
        if 'image_url' in payload and payload['image_url'] is not None:
            preset.image_url = payload['image_url'].strip()
        if 'sort_order' in payload and payload['sort_order'] is not None:
            preset.sort_order = int(payload['sort_order'])
        if 'is_active' in payload:
            preset.is_active = bool(payload['is_active'])

        preset.save()
        return JsonResponse({'ok': True, 'preset': preset.as_dict()})

    if request.method == 'DELETE':
        preset_label = preset.label
        preset_id = preset.id
        preset.delete()
        print(f"[DELETE] Deleted preset: {preset_label} (ID: {preset_id})")
        return JsonResponse({'ok': True, 'deleted_id': preset_id, 'deleted_label': preset_label})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def compatibility_agent_cache_list_view(request):
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    search = (request.GET.get('search') or '').strip()
    category = (request.GET.get('category') or '').strip()
    limit = request.GET.get('limit')
    try:
        limit_value = int(limit) if limit else 50
    except ValueError:
        limit_value = 50
    limit_value = max(1, min(limit_value, 200))

    try:
        caches = CompatibilityAgentCache.objects.all().order_by('-updated_at', '-created_at')
        if category:
            caches = caches.filter(category=category)
        if search:
            caches = caches.filter(Q(subject_name__icontains=search) | Q(target_name__icontains=search))

        payload = [cache.as_dict() for cache in caches[:limit_value]]
        return JsonResponse({'ok': True, 'caches': payload, 'limit': limit_value})
    except (OperationalError, ProgrammingError):
        logger.exception('[Compatibility] Failed to load agent cache list')
        return JsonResponse({
            'ok': False,
            'caches': [],
            'limit': limit_value,
            'error': '궁합 캐시 저장소를 불러올 수 없습니다. backend/db 마이그레이션을 적용한 뒤 다시 시도해주세요.'
        })


@csrf_exempt
def compatibility_agent_cache_detail_view(request, pk):
    if not is_admin(request):
        return JsonResponse({'ok': False, 'error': 'Admin access required'}, status=403)
    try:
        cache_entry = CompatibilityAgentCache.objects.get(pk=pk)
    except CompatibilityAgentCache.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Cache entry not found'}, status=404)
    except (OperationalError, ProgrammingError):
        logger.exception('[Compatibility] Cache storage unavailable for detail request')
        return JsonResponse({'ok': False, 'error': '궁합 캐시 저장소가 준비되지 않았습니다. 마이그레이션을 다시 확인해주세요.'})

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'cache': cache_entry.as_dict()})

    if request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        updated_fields = []
        if 'response_text' in payload and payload['response_text'] is not None:
            cache_entry.response_text = payload['response_text']
            updated_fields.append('response_text')
        if 'category' in payload and payload['category'] is not None:
            cache_entry.category = (payload['category'] or cache_entry.category or '').strip()
            updated_fields.append('category')
        if 'subject_name' in payload and payload['subject_name'] is not None:
            cache_entry.subject_name = payload['subject_name']
            updated_fields.append('subject_name')
        if 'target_name' in payload and payload['target_name'] is not None:
            cache_entry.target_name = payload['target_name']
            updated_fields.append('target_name')
        if 'metadata' in payload and isinstance(payload['metadata'], dict):
            cache_entry.metadata = payload['metadata']
            updated_fields.append('metadata')

        if updated_fields:
            cache_entry.save(update_fields=list(set(updated_fields + ['updated_at'])))
        return JsonResponse({'ok': True, 'cache': cache_entry.as_dict()})

    if request.method == 'DELETE':
        cache_entry.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def finance_quick_requests_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    _ensure_default_finance_quick_requests()
    requests_qs = FinanceQuickRequest.objects.filter(is_active=True).order_by('sort_order', 'id')
    return JsonResponse({
        'ok': True,
        'requests': [qr.as_dict() for qr in requests_qs]
    })



@csrf_exempt
def admin_finance_quick_requests_view(request):
    if request.method == 'GET':
        _ensure_default_finance_quick_requests()
        requests_qs = FinanceQuickRequest.objects.all().order_by('sort_order', 'id')
        return JsonResponse({
            'ok': True,
            'requests': [qr.as_dict() for qr in requests_qs]
        })

    if request.method == 'POST':
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        label = (payload.get('label') or '').strip()
        quick_request_text = (payload.get('quick_request') or '').strip()
        if not label or not quick_request_text:
            return JsonResponse({'ok': False, 'error': 'label과 quick_request는 필수입니다.'}, status=400)

        sort_order = payload.get('sort_order')
        if sort_order is None:
            max_order = FinanceQuickRequest.objects.aggregate(max_order=Max('sort_order'))['max_order'] or 0
            sort_order = max_order + 1

        quick_request = FinanceQuickRequest.objects.create(
            label=label,
            example=payload.get('example', ''),
            quick_request=quick_request_text,
            context_key=(payload.get('context_key') or '').strip(),
            sort_order=sort_order,
            is_active=bool(payload.get('is_active', True))
        )

        return JsonResponse({'ok': True, 'request': quick_request.as_dict()}, status=201)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_finance_quick_request_detail_view(request, pk):
    try:
        quick_request = FinanceQuickRequest.objects.get(pk=pk)
    except FinanceQuickRequest.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Quick request not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'request': quick_request.as_dict()})

    if request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        if 'label' in payload and payload['label'] is not None:
            quick_request.label = payload['label']
        if 'example' in payload and payload['example'] is not None:
            quick_request.example = payload['example']
        if 'quick_request' in payload and payload['quick_request'] is not None:
            quick_request.quick_request = payload['quick_request']
        if 'context_key' in payload and payload['context_key'] is not None:
            quick_request.context_key = payload['context_key']

        if 'sort_order' in payload and payload['sort_order'] is not None:
            quick_request.sort_order = int(payload['sort_order'])
        if 'is_active' in payload:
            quick_request.is_active = bool(payload['is_active'])

        quick_request.save()
        return JsonResponse({'ok': True, 'request': quick_request.as_dict()})

    if request.method == 'DELETE':
        quick_request.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


def _sanitize_asset_names(asset_values):
    assets = []
    if isinstance(asset_values, (list, tuple)):
        for raw in asset_values:
            if isinstance(raw, str):
                name = raw.strip()
                if name:
                    assets.append(name)
    return assets


def _resolve_assets(asset_names):
    """
    Resolve asset names to {label, ticker, id, category} objects.
    Returns list of resolved asset dicts.
    """
    resolved = []
    for name in asset_names:
        name = (name or '').strip()
        if not name:
            continue

        # Try to find in known assets first
        config = _find_known_asset_config(name, name)
        if config:
            resolved.append({
                'id': config.get('id') or name,
                'label': config.get('label') or name,
                'ticker': config.get('ticker') or config.get('id') or name,
                'category': config.get('category'),
            })
            continue

        # Try LLM lookup
        candidate = _lookup_ticker_with_llm(name, name)
        if candidate:
            resolved.append({
                'id': candidate.get('id') or name,
                'label': candidate.get('label') or name,
                'ticker': candidate.get('ticker') or candidate.get('id') or name,
                'category': candidate.get('category'),
            })
            continue

        # Fallback: use name as-is
        resolved.append({
            'id': name,
            'label': name,
            'ticker': name,
            'category': None,
        })

    return resolved


def _cache_asset_prices(asset_id, label, category=None):
    """
    Fetch and cache historical price data for an asset from 2009 to present.
    Returns True if successful, False otherwise.
    """
    from blocks.models import AssetPriceCache
    from datetime import datetime

    try:
        current_year = datetime.now().year
        start_year = 2009

        # Find or create asset config
        config = _find_known_asset_config(asset_id, label)
        if not config:
            # Create dynamic config
            config = {
                'id': asset_id,
                'label': label,
                'ticker': asset_id,
                'category': category or '기타',
                'unit': 'USD'
            }

        # Fetch historical data
        result = _fetch_asset_history(config, start_year, current_year)
        if not result:
            logger.warning(f"Failed to fetch price data for {asset_id}")
            return False

        history, source = result
        logger.info(f"Fetched {len(history)} data points for {asset_id}, type: {type(history)}")

        # Convert history to yearly prices dict
        yearly_prices = {}
        for i, entry in enumerate(history):
            # entry might be a dict or tuple depending on data source
            if isinstance(entry, dict):
                year = entry.get('year')
                price = entry.get('close')
            elif isinstance(entry, (tuple, list)) and len(entry) >= 2:
                year = entry[0]
                price = entry[1]
            else:
                logger.warning(f"Unknown entry format for {asset_id}: {type(entry)}")
                continue

            # Extract year from various formats
            if year is not None:
                try:
                    # If year is already an integer
                    if isinstance(year, int):
                        year_int = year
                    # If year is a string, try to extract the year part
                    elif isinstance(year, str):
                        # Try to parse as datetime or extract year
                        year_int = int(year.split('-')[0])
                    # If year is a datetime object
                    elif hasattr(year, 'year'):
                        year_int = year.year
                    else:
                        logger.warning(f"Cannot parse year for {asset_id}: {year} (type: {type(year)})")
                        continue

                    if price is not None:
                        yearly_prices[str(year_int)] = float(price)
                except (ValueError, AttributeError, IndexError) as e:
                    logger.warning(f"Error parsing year/price for {asset_id}: {year}, {price} - {e}")
                    continue

        if not yearly_prices:
            logger.warning(f"No price data found for {asset_id}")
            return False

        # Get or create cache entry
        cache_entry, created = AssetPriceCache.objects.update_or_create(
            asset_id=asset_id,
            defaults={
                'label': label,
                'category': config.get('category', '기타'),
                'unit': config.get('unit', 'USD'),
                'source': source,
                'yearly_prices': yearly_prices,
                'start_year': min(int(y) for y in yearly_prices.keys()),
                'end_year': max(int(y) for y in yearly_prices.keys()),
            }
        )

        logger.info(f"{'Created' if created else 'Updated'} price cache for {asset_id}: {len(yearly_prices)} years")
        return True

    except Exception as e:
        logger.error(f"Error caching prices for {asset_id}: {e}")
        return False


@csrf_exempt
def finance_price_cache_view(request):
    """
    Internal API endpoint for PriceRetriever Agent to check cached prices.
    GET /api/finance/price-cache?asset_id=AAPL&start_year=2009&end_year=2024
    """
    from blocks.models import AssetPriceCache

    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    asset_id = request.GET.get('asset_id', '').strip()
    if not asset_id:
        return JsonResponse({'ok': False, 'error': 'asset_id is required'}, status=400)

    try:
        cache_entry = AssetPriceCache.objects.get(asset_id=asset_id)
    except AssetPriceCache.DoesNotExist:
        return JsonResponse({'ok': False, 'cache_hit': False, 'error': 'No cache found'}, status=404)

    # Filter by year range if provided
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')

    yearly_prices = cache_entry.yearly_prices
    if start_year or end_year:
        filtered_prices = {}
        for year_str, price in yearly_prices.items():
            year = int(year_str)
            if start_year and year < int(start_year):
                continue
            if end_year and year > int(end_year):
                continue
            filtered_prices[year_str] = price
        yearly_prices = filtered_prices

    return JsonResponse({
        'ok': True,
        'cache_hit': True,
        'asset_id': cache_entry.asset_id,
        'label': cache_entry.label,
        'category': cache_entry.category,
        'unit': cache_entry.unit,
        'source': cache_entry.source,
        'yearly_prices': yearly_prices,
        'start_year': cache_entry.start_year,
        'end_year': cache_entry.end_year,
    })


@csrf_exempt
def finance_quick_compare_groups_view(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'GET only'}, status=405)

    _ensure_default_finance_quick_compare_groups()
    _ensure_quick_compare_groups_cached()
    groups_qs = FinanceQuickCompareGroup.objects.filter(is_active=True).order_by('sort_order', 'id')
    return JsonResponse({'ok': True, 'groups': [group.as_dict() for group in groups_qs]})


@csrf_exempt
def admin_finance_quick_compare_groups_view(request):
    if request.method == 'GET':
        _ensure_default_finance_quick_compare_groups()
        _ensure_quick_compare_groups_cached()
        groups_qs = FinanceQuickCompareGroup.objects.all().order_by('sort_order', 'id')
        return JsonResponse({'ok': True, 'groups': [group.as_dict() for group in groups_qs]})

    if request.method == 'POST':
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        key = (payload.get('key') or '').strip()
        label = (payload.get('label') or '').strip()
        assets = _sanitize_asset_names(payload.get('assets'))

        if not key or not label:
            return JsonResponse({'ok': False, 'error': 'key와 label은 필수입니다.'}, status=400)
        if not assets:
            return JsonResponse({'ok': False, 'error': '최소 1개 이상의 비교 종목이 필요합니다.'}, status=400)

        # Resolve assets to get ticker and label
        resolved_assets = _resolve_assets(assets)

        # Cache price data for each resolved asset
        for asset in resolved_assets:
            asset_id = asset.get('ticker') or asset.get('id')
            asset_label = asset.get('label')
            asset_category = asset.get('category')
            if asset_id and asset_label:
                # Run in background to avoid blocking the request
                try:
                    _cache_asset_prices(asset_id, asset_label, asset_category)
                except Exception as e:
                    logger.warning(f"Failed to cache prices for {asset_id}: {e}")

        sort_order = payload.get('sort_order')
        if sort_order is None:
            max_order = FinanceQuickCompareGroup.objects.aggregate(max_order=Max('sort_order'))['max_order'] or 0
            sort_order = max_order + 1

        try:
            group = FinanceQuickCompareGroup.objects.create(
                key=key,
                label=label,
                assets=assets,
                resolved_assets=resolved_assets,
                sort_order=int(sort_order),
                is_active=bool(payload.get('is_active', True)),
            )
        except Exception as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

        return JsonResponse({'ok': True, 'group': group.as_dict()}, status=201)

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_finance_quick_compare_group_detail_view(request, pk):
    try:
        group = FinanceQuickCompareGroup.objects.get(pk=pk)
    except FinanceQuickCompareGroup.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Quick compare group not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'group': group.as_dict()})

    if request.method in ['PUT', 'PATCH']:
        payload = _load_json_body(request)
        if payload is None:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

        if 'key' in payload and payload['key'] is not None:
            key = str(payload['key']).strip()
            if not key:
                return JsonResponse({'ok': False, 'error': 'key는 비워둘 수 없습니다.'}, status=400)
            group.key = key
        if 'label' in payload and payload['label'] is not None:
            label = str(payload['label']).strip()
            if not label:
                return JsonResponse({'ok': False, 'error': 'label은 비워둘 수 없습니다.'}, status=400)
            group.label = label
        if 'assets' in payload:
            assets = _sanitize_asset_names(payload.get('assets'))
            if not assets:
                return JsonResponse({'ok': False, 'error': '최소 1개 이상의 비교 종목이 필요합니다.'}, status=400)
            group.assets = assets
            # Resolve assets to get ticker and label
            resolved_assets = _resolve_assets(assets)
            group.resolved_assets = resolved_assets

            # Cache price data for each resolved asset
            for asset in resolved_assets:
                asset_id = asset.get('ticker') or asset.get('id')
                asset_label = asset.get('label')
                asset_category = asset.get('category')
                if asset_id and asset_label:
                    try:
                        _cache_asset_prices(asset_id, asset_label, asset_category)
                    except Exception as e:
                        logger.warning(f"Failed to cache prices for {asset_id}: {e}")
        if 'sort_order' in payload and payload['sort_order'] is not None:
            group.sort_order = int(payload['sort_order'])
        if 'is_active' in payload:
            group.is_active = bool(payload['is_active'])

        try:
            group.save()
        except Exception as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

        return JsonResponse({'ok': True, 'group': group.as_dict()})

    if request.method == 'DELETE':
        group.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_price_cache_view(request):
    """
    Admin endpoint to manage price cache entries.
    GET: List all cached assets with pagination
    """
    from blocks.models import AssetPriceCache

    if request.method == 'GET':
        offset = max(0, int(request.GET.get('offset', 0)))
        limit = int(request.GET.get('limit', 10)) or 10
        limit = max(1, min(limit, 100))
        search_query = (request.GET.get('search') or '').strip()

        cache_qs = AssetPriceCache.objects.all()
        if search_query:
            cache_qs = cache_qs.filter(
                Q(label__icontains=search_query) | Q(asset_id__icontains=search_query)
            )

        total_count = cache_qs.count()
        cache_entries = cache_qs[offset:offset + limit]

        return JsonResponse({
            'ok': True,
            'cached_assets': [entry.as_dict() for entry in cache_entries],
            'total': total_count,
            'offset': offset,
            'limit': limit
        })

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def admin_price_cache_detail_view(request, pk):
    """
    Admin endpoint to manage individual price cache entry.
    GET: Retrieve cache entry
    DELETE: Remove cache entry
    """
    from blocks.models import AssetPriceCache

    try:
        cache_entry = AssetPriceCache.objects.get(pk=pk)
    except AssetPriceCache.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Cache entry not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'cache_entry': cache_entry.as_dict()})

    if request.method == 'DELETE':
        asset_id = cache_entry.asset_id
        cache_entry.delete()
        return JsonResponse({'ok': True, 'message': f'Cache for {asset_id} deleted'})

    return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)


# ------------------------------------------------------------------------------
# Time Capsule Views
# ------------------------------------------------------------------------------


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
        # Treat obviously invalid values (e.g., base64 blobs) as missing so admins can recreate.
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
    from django.core.cache import cache

    # 캐시 키 생성
    cache_key = f'utxo:{address}'

    # 캐시 확인 (30초 TTL)
    if use_cache:
        cached_utxos = cache.get(cache_key)
        if cached_utxos is not None:
            logger.debug(f'Cache HIT for address {address}')
            return cached_utxos

    logger.debug(f'Cache MISS for address {address}, fetching from API')

    base = (base_url or _get_block_explorer_base()).rstrip('/')
    url = f'{base}/address/{address}/utxo'

    try:
        resp = requests.get(url, timeout=5)  # 8초 → 5초로 단축
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        logger.error(f'Timeout fetching UTXOs for {address}')
        raise ValueError(f'주소 {address}의 UTXO 조회 시간이 초과되었습니다.')
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to fetch UTXOs for {address}: {e}')
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

    # 캐시 저장 (30초)
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

    # 실제 사용된 from 주소들 수집 (중복 제거)
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
        'from_address': primary_from_address,  # 주 출금 주소
        'from_addresses': used_from_addresses,  # 모든 출금 주소 (다중 UTXO 경우)
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

        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
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
    import time

    start_time = time.time()

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    payload = _load_json_body(request) or {}
    to_address = (payload.get('to_address') or '').strip()
    amount_sats = _parse_int(payload.get('amount_sats'))
    fee_rate = _parse_float(payload.get('fee_rate_sats_vb'))
    account = max(0, _parse_int(payload.get('account'), 0) or 0)
    from_address = (payload.get('from_address') or '').strip()
    memo_text = (payload.get('memo_text') or '').strip()

    logger.info(f'Building TX: to={to_address[:10]}..., from={from_address[:10] if from_address else "auto"}, amount={amount_sats}')

    mnemonic_obj = _get_time_capsule_mnemonic()
    if not mnemonic_obj:
        return JsonResponse({'ok': False, 'error': '타임캡슐 니모닉이 없습니다.'}, status=404)

    try:
        mnemonic_plain = mnemonic_obj.get_mnemonic()
    except Exception as e:
        logger.error(f'Failed to load mnemonic: {e}')
        return JsonResponse({'ok': False, 'error': '니모닉을 불러오지 못했습니다.'}, status=500)

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
        logger.info(f'Build TX SUCCESS in {elapsed:.2f}s: fee={details.get("fee_sats")} sats, vsize={details.get("vsize")} vB')

        return JsonResponse({'ok': True, **details})

    except ValueError as exc:
        elapsed = time.time() - start_time
        logger.warning(f'Build TX FAILED (ValueError) in {elapsed:.2f}s: {exc}')
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(f'Build TX FAILED (Exception) in {elapsed:.2f}s: {exc}', exc_info=True)
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

    stored_value, hostname, scheme, normalized_port = _parse_broadcast_target(host, port)

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
    stored_value, hostname, scheme, normalized_port = _parse_broadcast_target(
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

    response_data = {
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
    }
    return JsonResponse(response_data)


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
            # Addresses are only assigned by admins via the mnemonic-derived workflow.
            bitcoin_address='',
            user_info=user_info
        )

        return JsonResponse(capsule.as_dict())
    except Exception as e:
        logger.error(f"Error saving time capsule: {e}")
        return JsonResponse({'error': str(e)}, status=500)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@csrf_exempt
def admin_time_capsules_view(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    capsules = TimeCapsule.objects.all().order_by('-created_at')
    
    page_number = request.GET.get('page')
    if page_number:
        paginator = Paginator(capsules, 20)  # Show 20 contacts per page.
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
    else:
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
    except Exception as e:
        logger.error(f"Error updating time capsule: {e}")
        return JsonResponse({'error': str(e)}, status=500)


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
    except Exception as e:
        logger.error(f"Error deleting time capsule: {e}")
        return JsonResponse({'error': str(e)}, status=500)
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
