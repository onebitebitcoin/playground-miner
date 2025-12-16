from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .encryption import encrypt_mnemonic, decrypt_mnemonic, is_encrypted_mnemonic
import logging
import uuid
import random

logger = logging.getLogger(__name__)


class Block(models.Model):
    height = models.PositiveIntegerField(unique=True)
    nonce = models.PositiveIntegerField()
    miner = models.CharField(max_length=64)
    difficulty = models.PositiveIntegerField()
    reward = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-height']

    def as_dict(self):
        return {
            'height': self.height,
            'nonce': self.nonce,
            'miner': self.miner,
            'difficulty': self.difficulty,
            'reward': self.reward,
            'timestamp': self.timestamp.isoformat(),
        }


class Nickname(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Mnemonic(models.Model):
    username = models.CharField(max_length=64)
    mnemonic = models.TextField()  # Stores encrypted mnemonic
    is_assigned = models.BooleanField(default=False)
    # Username of the user to whom this mnemonic has been assigned (if any)
    assigned_to = models.CharField(max_length=64, blank=True, null=True)
    balance_sats = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Override save to encrypt mnemonic before storing"""
        if self.mnemonic and not is_encrypted_mnemonic(self.mnemonic):
            try:
                self.mnemonic = encrypt_mnemonic(self.mnemonic)
                logger.info(f"Encrypted mnemonic for user: {self.username}")
            except Exception as e:
                logger.error(f"Failed to encrypt mnemonic for user {self.username}: {e}")
                raise ValueError("Failed to encrypt mnemonic")

        super().save(*args, **kwargs)

    def get_mnemonic(self):
        """Get the decrypted mnemonic"""
        try:
            if self.mnemonic and is_encrypted_mnemonic(self.mnemonic):
                return decrypt_mnemonic(self.mnemonic)
            return self.mnemonic  # Return as-is if not encrypted (for migration compatibility)
        except Exception as e:
            logger.error(f"Failed to decrypt mnemonic for user {self.username}: {e}")
            raise ValueError("Failed to decrypt mnemonic")

    def set_mnemonic(self, plaintext_mnemonic):
        """Set a new mnemonic (will be encrypted on save)"""
        self.mnemonic = plaintext_mnemonic

    def __str__(self):
        try:
            mnemonic_preview = self.get_mnemonic()[:20] + "..." if len(self.get_mnemonic()) > 20 else self.get_mnemonic()
            return f"{self.username} - {mnemonic_preview}"
        except:
            return f"{self.username} - [encrypted]"

    def as_dict(self):
        """Return dictionary representation with decrypted mnemonic"""
        try:
            decrypted_mnemonic = self.get_mnemonic()
        except Exception as e:
            logger.error(f"Failed to decrypt mnemonic in as_dict for user {self.username}: {e}")
            # For admin purposes, show that it's encrypted
            decrypted_mnemonic = "[ENCRYPTION_ERROR]"

        return {
            'id': self.id,
            'username': self.username,
            'mnemonic': decrypted_mnemonic,
            'is_assigned': self.is_assigned,
            'assigned_to': self.assigned_to or '',
            'balance_sats': int(self.balance_sats or 0),
            'created_at': self.created_at.isoformat(),
        }


class KingstoneWallet(models.Model):
    """PIN-protected Kingstone wallets mapped per user"""

    username = models.CharField(max_length=64)
    pin_hash = models.CharField(max_length=256)
    pin_encrypted = models.CharField(max_length=256, blank=True, default='')
    wallet_id = models.CharField(max_length=64, unique=True)
    wallet_name = models.CharField(max_length=64)
    index = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    mnemonic = models.CharField(max_length=512, blank=True, default='')

    class Meta:
        unique_together = (
            ('username', 'index'),
        )
        indexes = [
            models.Index(fields=['username']),
        ]

    def set_pin(self, pin: str):
        if not pin:
            raise ValueError('PIN must not be empty')
        self.pin_hash = make_password(pin)
        try:
            self.pin_encrypted = encrypt_mnemonic(pin)
        except Exception:
            # Encryption failures should not block hashing; fall back to empty storage.
            self.pin_encrypted = ''

    def check_pin(self, pin: str) -> bool:
        if not self.pin_hash:
            return False
        return check_password(pin, self.pin_hash)

    def ensure_defaults(self):
        """Ensure wallet_id and wallet_name are populated before saving."""
        if not self.wallet_id:
            self.wallet_id = uuid.uuid4().hex
        if not self.wallet_name:
            self.wallet_name = f"지갑{self.index}"
        if not self.mnemonic:
            self.mnemonic = self.generate_mock_mnemonic()

    def save(self, *args, **kwargs):
        self.ensure_defaults()
        super().save(*args, **kwargs)

    def as_dict(self):
        from .btc import derive_bip84_account_zpub
        zpub = None
        try:
            if self.mnemonic:
                zpub = derive_bip84_account_zpub(self.mnemonic, account=0)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to derive zpub for wallet {self.wallet_id}: {e}")

        return {
            'id': self.id,
            'username': self.username,
            'wallet_id': self.wallet_id,
            'wallet_name': self.wallet_name,
            'index': self.index,
            'created_at': self.created_at.isoformat(),
            'mnemonic': self.mnemonic,
            'zpub': zpub,
        }

    @staticmethod
    def generate_mock_mnemonic(word_count: int = 12) -> str:
        words = [
            'apple', 'balance', 'candle', 'delta', 'ember', 'forest', 'globe', 'harbor',
            'island', 'jungle', 'king', 'lantern', 'magnet', 'nebula', 'ocean', 'prairie',
            'quantum', 'rocket', 'saturn', 'timber', 'utopia', 'victory', 'willow', 'zenith'
        ]
        if not words:
            return uuid.uuid4().hex
        return ' '.join(random.choice(words) for _ in range(max(1, word_count)))

    def get_pin_plain(self) -> str:
        """Return stored PIN in plaintext for admin-only contexts."""
        if not self.pin_encrypted:
            return ''
        try:
            return decrypt_mnemonic(self.pin_encrypted)
        except Exception:
            return ''


class ExchangeRate(models.Model):
    """Exchange fee rates for different trading platforms"""
    EXCHANGE_CHOICES = [
        ('upbit_btc', '업비트 비트코인'),
        ('upbit_usdt', '업비트 USDT'),
        ('bithumb', '빗썸'),
        ('okx', 'OKX'),
        ('binance', '바이낸스'),
    ]

    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES, unique=True)
    fee_rate = models.DecimalField(max_digits=6, decimal_places=4)  # Support up to 99.9999%
    is_event = models.BooleanField(default=False)  # Mark if this is a temporary event rate
    description = models.TextField(blank=True, null=True)  # Additional notes
    event_details = models.TextField(blank=True, null=True)  # Detailed event information
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exchange']

    def __str__(self):
        event_indicator = " (이벤트)" if self.is_event else ""
        return f"{self.get_exchange_display()}: {self.fee_rate}%{event_indicator}"

    def as_dict(self):
        return {
            'exchange': self.exchange,
            'exchange_name': self.get_exchange_display(),
            'fee_rate': float(self.fee_rate),
            'is_event': self.is_event,
            'description': self.description,
            'event_details': self.event_details,
            'updated_at': self.updated_at.isoformat(),
        }


class WithdrawalFee(models.Model):
    """Withdrawal fees for different exchanges and methods"""
    EXCHANGE_CHOICES = [
        ('okx', 'OKX'),
        ('binance', '바이낸스'),
    ]

    WITHDRAWAL_TYPE_CHOICES = [
        ('onchain', '온체인'),
        ('lightning', '라이트닝'),
    ]

    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES)
    withdrawal_type = models.CharField(max_length=20, choices=WITHDRAWAL_TYPE_CHOICES)
    fee_btc = models.DecimalField(max_digits=10, decimal_places=8)  # Fee in BTC
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exchange', 'withdrawal_type')
        ordering = ['exchange', 'withdrawal_type']

    def __str__(self):
        return f"{self.get_exchange_display()} {self.get_withdrawal_type_display()}: {self.fee_btc} BTC"

    def as_dict(self):
        return {
            'exchange': self.exchange,
            'exchange_name': self.get_exchange_display(),
            'withdrawal_type': self.withdrawal_type,
            'withdrawal_type_name': self.get_withdrawal_type_display(),
            'fee_btc': float(self.fee_btc),
            'description': self.description,
            'updated_at': self.updated_at.isoformat(),
        }


class ServiceNode(models.Model):
    """Service nodes for routing system"""
    NODE_TYPE_CHOICES = [
        ('user', '사용자'),
        ('exchange', '거래소'),
        ('service', '서비스'),
        ('wallet', '지갑'),
    ]

    SERVICE_CHOICES = [
        ('user', '사용자'),
        ('upbit', '업비트'),
        ('upbit_krw', '업비트 원화'),
        ('upbit_btc', '업비트 BTC'),
        ('upbit_usdt', '업비트 USDT'),
        ('bithumb', '빗썸'),
        ('bithumb_krw', '빗썸 원화'),
        ('bithumb_btc', '빗썸 BTC'),
        ('bithumb_usdt', '빗썸 USDT'),
        ('binance', '바이낸스'),
        ('binance_usdt', '바이낸스 USDT'),
        ('binance_btc', '바이낸스 BTC'),
        ('okx', 'OKX'),
        ('okx_usdt', 'OKX USDT'),
        ('okx_btc', 'OKX BTC'),
        ('strike', 'Strike'),
        ('walletofsatoshi', '월렛오브사토시'),
        ('coinos', 'Coinos'),
        ('boltz', 'Boltz Exchange'),
        ('personal_wallet', '개인지갑'),
    ]

    service = models.CharField(max_length=30, choices=SERVICE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='service')
    is_kyc = models.BooleanField(default=False)
    is_custodial = models.BooleanField(default=True)
    is_enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['service']

    def __str__(self):
        kyc_indicator = " (KYC)" if self.is_kyc else " (non-KYC)"
        custodial_indicator = " 수탁형" if self.is_custodial else " 비수탁형"
        return f"{self.display_name}{kyc_indicator}{custodial_indicator}"

    def as_dict(self):
        return {
            'id': self.id,
            'service': self.service,
            'display_name': self.display_name,
            'node_type': self.node_type,
            'is_kyc': self.is_kyc,
            'is_custodial': self.is_custodial,
            'is_enabled': self.is_enabled,
            'description': self.description,
            'website_url': self.website_url,
            'updated_at': self.updated_at.isoformat(),
        }


class Route(models.Model):
    """Routes between service nodes"""
    ROUTE_TYPE_CHOICES = [
        ('trading', '거래수수료'),
        ('withdrawal_lightning', '라이트닝 출금'),
        ('withdrawal_onchain', '온체인 출금'),
    ]
    FEE_CURRENCY_CHOICES = [
        ('BTC', 'BTC'),
        ('USDT', 'USDT'),
    ]

    source = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='routes_to')
    route_type = models.CharField(max_length=30, choices=ROUTE_TYPE_CHOICES)
    fee_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)  # Percentage fee
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)  # Fixed fee amount
    fee_fixed_currency = models.CharField(max_length=10, choices=FEE_CURRENCY_CHOICES, default='BTC')
    is_enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    is_event = models.BooleanField(default=False)
    event_title = models.CharField(max_length=255, blank=True, default='')
    event_description = models.TextField(blank=True, default='')
    event_url = models.URLField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source', 'destination', 'route_type')
        ordering = ['source', 'destination', 'route_type']

    def __str__(self):
        fee_str = ""
        if self.fee_rate:
            fee_str += f"{self.fee_rate}%"
        if self.fee_fixed:
            if fee_str:
                fee_str += f" + {self.fee_fixed} {self.fee_fixed_currency}"
            else:
                fee_str = f"{self.fee_fixed} {self.fee_fixed_currency}"
        return f"{self.source.display_name} → {self.destination.display_name} ({self.get_route_type_display()}): {fee_str}"

    def as_dict(self):
        return {
            'id': self.id,
            'source': self.source.as_dict(),
            'destination': self.destination.as_dict(),
            'route_type': self.route_type,
            'route_type_display': self.get_route_type_display(),
            'fee_rate': float(self.fee_rate) if self.fee_rate else None,
            'fee_fixed': float(self.fee_fixed) if self.fee_fixed else None,
            'fee_fixed_currency': self.fee_fixed_currency,
            'is_enabled': self.is_enabled,
            'description': self.description,
            'is_event': self.is_event,
            'event_title': self.event_title or '',
            'event_description': self.event_description or '',
            'event_url': self.event_url or '',
            'updated_at': self.updated_at.isoformat(),
        }


class LightningService(models.Model):
    """Lightning network service fees - DEPRECATED, use ServiceNode and Route instead"""
    SERVICE_CHOICES = [
        ('boltz', 'Boltz Exchange'),
        ('coinos', 'Coinos'),
        ('walletofsatoshi', '월렛오브사토시'),
        ('strike', 'Strike'),
    ]

    service = models.CharField(max_length=30, choices=SERVICE_CHOICES, unique=True)
    fee_rate = models.DecimalField(max_digits=6, decimal_places=4)  # Fee rate as percentage
    is_kyc = models.BooleanField(default=False)  # KYC required or not
    is_custodial = models.BooleanField(default=True)  # Custodial or non-custodial service
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['service']

    def __str__(self):
        kyc_indicator = " (KYC)" if self.is_kyc else " (non-KYC)"
        custodial_indicator = " 수탁형" if self.is_custodial else " 비수탁형"
        return f"{self.get_service_display()}: {self.fee_rate}%{kyc_indicator}{custodial_indicator}"

    def as_dict(self):
        return {
            'service': self.service,
            'service_name': self.get_service_display(),
            'fee_rate': float(self.fee_rate),
            'is_kyc': self.is_kyc,
            'is_custodial': self.is_custodial,
            'description': self.description,
            'updated_at': self.updated_at.isoformat(),
        }


class RoutingSnapshot(models.Model):
    """Persisted snapshot of routing graph (service nodes + routes) for reset."""
    name = models.CharField(max_length=100, unique=True)
    nodes_json = models.JSONField()
    routes_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"RoutingSnapshot<{self.name}> updated={self.updated_at.isoformat()}"


class SidebarConfig(models.Model):
    """Configuration for sidebar menu visibility"""
    show_mining = models.BooleanField(default=True)
    show_utxo = models.BooleanField(default=True)
    show_wallet = models.BooleanField(default=True)
    show_fee = models.BooleanField(default=True)
    show_finance = models.BooleanField(default=False)
    # Optional wallet password protection (stored as SHA256 hex)
    wallet_password_hash = models.CharField(max_length=128, blank=True, default='')
    # For admin visibility (demo purpose): store plaintext as well
    wallet_password_plain = models.CharField(max_length=128, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Only allow one config row
        db_table = 'blocks_sidebar_config'

    def __str__(self):
        return (
            f"SidebarConfig (mining={self.show_mining}, utxo={self.show_utxo}, "
            f"wallet={self.show_wallet}, fee={self.show_fee}, finance={self.show_finance})"
        )

    def as_dict(self):
        return {
            'show_mining': self.show_mining,
            'show_utxo': self.show_utxo,
            'show_wallet': self.show_wallet,
            'show_fee': self.show_fee,
            'show_finance': self.show_finance,
            'wallet_password_set': bool(self.wallet_password_hash),
            'updated_at': self.updated_at.isoformat(),
        }


class FinanceQueryCache(models.Model):
    """Cache for frequently used finance queries"""
    query_key = models.CharField(max_length=255, unique=True, db_index=True)
    context_key = models.CharField(max_length=50, blank=True, default='')  # e.g., 'us_bigtech', 'kr_equity'
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    series_data = models.JSONField()  # Cached series with pre-calculated CAGR
    fx_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1300)
    hit_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()  # Cache expiration

    class Meta:
        ordering = ['-hit_count', '-updated_at']
        indexes = [
            models.Index(fields=['query_key']),
            models.Index(fields=['context_key']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Cache<{self.context_key}> {self.start_year}-{self.end_year} (hits: {self.hit_count})"

    def as_dict(self):
        return {
            'start_year': self.start_year,
            'end_year': self.end_year,
            'series': self.series_data,
            'fx_rate': float(self.fx_rate),
        }

    def increment_hit(self):
        """Increment hit count"""
        self.hit_count += 1
        self.save(update_fields=['hit_count', 'updated_at'])


class FinanceQueryLog(models.Model):
    """Log for finance query requests"""
    user_identifier = models.CharField(max_length=255, blank=True, default='')  # IP or username
    prompt = models.TextField()  # User's prompt
    quick_requests = models.JSONField(default=list, blank=True)  # Quick request buttons
    context_key = models.CharField(max_length=50, blank=True, default='')  # e.g., 'us_bigtech', 'kr_equity'
    success = models.BooleanField(default=False)  # Whether query succeeded
    error_message = models.TextField(blank=True, default='')  # Error if failed
    assets_count = models.PositiveSmallIntegerField(default=0)  # Number of assets analyzed
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)  # Processing time in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user_identifier']),
            models.Index(fields=['success']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} [{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.user_identifier}: {self.prompt[:50]}"


class FinanceQuickRequest(models.Model):
    label = models.CharField(max_length=150)
    example = models.TextField(blank=True, default='')
    quick_request = models.TextField()
    context_key = models.CharField(max_length=50, blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"QuickRequest<{self.label}>"

    def as_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'example': self.example,
            'quick_request': self.quick_request,
            'context_key': self.context_key,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


class FinanceQuickCompareGroup(models.Model):
    key = models.CharField(max_length=50, unique=True, db_index=True)
    label = models.CharField(max_length=150)
    assets = models.JSONField(default=list, blank=True)
    resolved_assets = models.JSONField(default=list, blank=True, help_text='Pre-resolved asset information with label, ticker, id, category')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"QuickCompare<{self.label}>"

    def as_dict(self):
        # Enrich resolved_assets with cache status
        resolved_assets_with_cache = []
        for asset in (self.resolved_assets or []):
            asset_copy = dict(asset)
            # Check if this asset has cached price data
            asset_id = asset.get('ticker') or asset.get('id')
            if asset_id:
                has_cache = AssetPriceCache.objects.filter(asset_id=asset_id).exists()
                asset_copy['has_cache'] = has_cache
            else:
                asset_copy['has_cache'] = False
            resolved_assets_with_cache.append(asset_copy)

        return {
            'id': self.id,
            'key': self.key,
            'label': self.label,
            'assets': list(self.assets or []),
            'resolved_assets': resolved_assets_with_cache,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


class AssetPriceCache(models.Model):
    """Cache for asset historical price data (2009-present)"""
    asset_id = models.CharField(max_length=100, db_index=True, help_text='Asset ticker or identifier')
    label = models.CharField(max_length=200, help_text='Human-readable asset name')
    category = models.CharField(max_length=100, blank=True, help_text='Asset category')
    unit = models.CharField(max_length=10, default='USD', help_text='Price unit (USD, KRW, etc)')
    source = models.CharField(max_length=100, blank=True, help_text='Data source')

    # Store yearly price data as JSON: {year: price}
    yearly_prices = models.JSONField(default=dict, help_text='Yearly closing prices from 2009 onwards')

    # Metadata
    start_year = models.IntegerField(default=2009, help_text='First year of data')
    end_year = models.IntegerField(help_text='Last year of data')
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['asset_id']),
            models.Index(fields=['last_updated']),
        ]
        unique_together = [['asset_id']]

    def __str__(self):
        return f"PriceCache<{self.asset_id}: {self.label}>"

    def as_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'label': self.label,
            'category': self.category,
            'unit': self.unit,
            'source': self.source,
            'yearly_prices': self.yearly_prices,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


class AgentPrompt(models.Model):
    """Agent system prompts for finance analysis"""
    AGENT_CHOICES = [
        ('intent_classifier', 'Intent Classifier Agent'),
        ('price_retriever', 'Price Retriever Agent'),
        ('calculator', 'Calculator Agent'),
        ('guardrail', 'Guardrail Agent'),
    ]

    agent_type = models.CharField(max_length=50, choices=AGENT_CHOICES, unique=True, db_index=True)
    name = models.CharField(max_length=100)  # Display name in Korean/English
    description = models.TextField(blank=True, default='')  # Agent description
    system_prompt = models.TextField()  # System prompt for the agent
    is_active = models.BooleanField(default=True)  # Whether this agent is active
    version = models.PositiveIntegerField(default=1)  # Version tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['agent_type']
        indexes = [
            models.Index(fields=['agent_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def as_dict(self):
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class CompatibilityAgentPrompt(models.Model):
    """System prompt configuration for the compatibility agent."""

    agent_key = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    system_prompt = models.TextField()
    model_name = models.CharField(max_length=100, default='openai:gpt-5-mini')
    is_active = models.BooleanField(default=True)
    temperature = models.FloatField(default=0.2)
    top_p = models.FloatField(default=0.9)
    presence_penalty = models.FloatField(default=0.6)
    frequency_penalty = models.FloatField(default=0.4)
    max_tokens = models.IntegerField(default=700)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['agent_key']
        indexes = [
            models.Index(fields=['agent_key']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} (compat v{self.version})"

    def as_dict(self):
        return {
            'id': self.id,
            'agent_key': self.agent_key,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model_name': self.model_name,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class CompatibilityAnalysis(models.Model):
    """Stores Bitcoin compatibility analysis results"""
    birthdate = models.DateField()
    birth_time = models.TimeField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)  # 'male', 'female', or empty

    # Calculated saju properties
    element = models.CharField(max_length=10)  # e.g., '목(木)', '금(金)', etc.
    zodiac = models.CharField(max_length=20)  # e.g., '자(쥐)', '축(소)', etc.
    yin_yang = models.CharField(max_length=5)  # '음' or '양'

    # Compatibility results
    score = models.IntegerField()  # Compatibility score (0-100)
    rating = models.CharField(max_length=50)  # e.g., '찰떡궁합', '균형 잡힌 합', etc.
    narrative = models.TextField()  # AI-generated story/analysis

    # Metadata
    user_ip = models.GenericIPAddressField(null=True, blank=True)  # For tracking unique users
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user_ip']),
        ]

    def __str__(self):
        return f"{self.birthdate} - {self.element} ({self.score}점)"

    def as_dict(self):
        return {
            'id': self.id,
            'birthdate': self.birthdate.isoformat(),
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'gender': self.gender,
            'element': self.element,
            'zodiac': self.zodiac,
            'yin_yang': self.yin_yang,
            'score': self.score,
            'rating': self.rating,
            'narrative': self.narrative,
            'user_ip': self.user_ip,
            'created_at': self.created_at.isoformat(),
        }


class CompatibilityQuickPreset(models.Model):
    """Preconfigured saju inputs that appear as quick presets on the compatibility page."""

    label = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, default='')
    birthdate = models.DateField(null=True, blank=True)
    birth_time = models.TimeField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, default='')  # 'male', 'female', etc.
    image_url = models.URLField(blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        birthdate_display = self.birthdate.isoformat() if self.birthdate else '정보 없음'
        return f"{self.label} ({birthdate_display})"

    def as_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'description': self.description,
            'birthdate': self.birthdate.isoformat() if self.birthdate else None,
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'gender': self.gender,
            'image_url': self.image_url,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class TimeCapsule(models.Model):
    """Stores encrypted time capsule messages and associated metadata"""
    encrypted_message = models.TextField()
    bitcoin_address = models.CharField(max_length=100)
    user_info = models.TextField(blank=True, default='')  # Can store JSON or simple string
    is_coupon_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TimeCapsule {self.id} ({self.created_at.strftime('%Y-%m-%d')})"

    def as_dict(self):
        return {
            'id': self.id,
            'encrypted_message': self.encrypted_message,
            'bitcoin_address': self.bitcoin_address,
            'user_info': self.user_info,
            'is_coupon_used': self.is_coupon_used,
            'created_at': self.created_at.isoformat(),
        }
