from django.db import models
from .encryption import encrypt_mnemonic, decrypt_mnemonic, is_encrypted_mnemonic
import logging

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
            'created_at': self.created_at.isoformat(),
        }


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

    source = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='routes_to')
    route_type = models.CharField(max_length=30, choices=ROUTE_TYPE_CHOICES)
    fee_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)  # Percentage fee
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)  # Fixed BTC fee
    is_enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
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
                fee_str += f" + {self.fee_fixed} BTC"
            else:
                fee_str = f"{self.fee_fixed} BTC"
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
            'is_enabled': self.is_enabled,
            'description': self.description,
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
