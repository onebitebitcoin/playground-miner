import os
from typing import List, Dict
import requests
import unicodedata

from mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic as BtcLibMnemonic


def _normalize_mnemonic(m: str) -> str:
    """Normalize mnemonic per BIP39 (NFKD, collapse whitespace)."""
    m = unicodedata.normalize("NFKD", (m or "")).strip()
    # collapse all whitespace runs to single spaces and lower-case (BIP39 English wordlist is lower-case)
    return " ".join(m.split()).lower()


def derive_bip84_addresses(mnemonic: str, account: int = 0, change: int = 0, start: int = 0, count: int = 20) -> List[str]:
    """
    Derive BIP84 (P2WPKH bech32) Bitcoin mainnet addresses from a mnemonic.
    Path: m/84'/0'/account'/change/index
    Uses bip_utils (no DB, no side effects).
    """
    mnorm = _normalize_mnemonic(mnemonic)

    # Validate mnemonic first
    mnemo_validator = Mnemonic('english')
    if not mnemo_validator.check(mnorm):
        raise ValueError(f"Invalid mnemonic: {mnorm}")

    try:
        seed = BtcLibMnemonic().to_seed(mnorm)
        root = HDKey.from_seed(seed, network='bitcoin')
        base_path = f"m/84'/0'/{int(account)}'/{int(change)}"
        addrs: List[str] = []
        for i in range(int(start), int(start) + int(count)):
            k = root.subkey_for_path(f"{base_path}/{i}")
            # Native segwit P2WPKH bech32 address
            addrs.append(k.address(script_type='p2wpkh', encoding='bech32'))
        return addrs
    except Exception as e:
        raise ValueError(f"Failed to derive addresses: {str(e)}")


def fetch_blockstream_balances(addresses: List[str], base_url: str = None, include_mempool: bool = True, timeout: float = 8.0) -> Dict[str, int]:
    """
    Query Blockstream explorer for balances. Returns sats per address.
    """
    import time
    base = (base_url or os.environ.get('BTC_EXPLORER_API') or 'https://blockstream.info/api').rstrip('/')
    out: Dict[str, int] = {}
    sess = requests.Session()
    for i, addr in enumerate(addresses):
        try:
            # Add delay between requests to avoid rate limiting (max 1 req/sec to be safe)
            if i > 0:
                time.sleep(1.2)

            r = sess.get(f"{base}/address/{addr}", timeout=timeout)

            # Handle rate limiting
            if r.status_code == 429:
                # Wait longer and retry once
                time.sleep(5)
                r = sess.get(f"{base}/address/{addr}", timeout=timeout)

            r.raise_for_status()
            data = r.json()
            c = data.get('chain_stats', {})
            m = data.get('mempool_stats', {})
            bal = int(c.get('funded_txo_sum', 0)) - int(c.get('spent_txo_sum', 0))
            if include_mempool:
                bal += int(m.get('funded_txo_sum', 0)) - int(m.get('spent_txo_sum', 0))
            out[addr] = max(0, bal)
        except Exception as e:
            # Log the error but continue
            import logging
            logging.getLogger(__name__).warning(f"Failed to fetch balance for {addr}: {e}")
            out[addr] = 0
    return out


def calc_total_sats(addr_balances: Dict[str, int]) -> int:
    return sum(int(v or 0) for v in (addr_balances or {}).values())


def derive_master_fingerprint(mnemonic: str) -> str:
    """
    Derive master fingerprint (first 8 hex chars of HASH160 of master pubkey).
    This is the standard BIP32 fingerprint format.
    """
    mnorm = _normalize_mnemonic(mnemonic)

    # Validate mnemonic first
    mnemo_validator = Mnemonic('english')
    if not mnemo_validator.check(mnorm):
        raise ValueError(f"Invalid mnemonic: {mnorm}")

    try:
        seed = BtcLibMnemonic().to_seed(mnorm)
        root = HDKey.from_seed(seed, network='bitcoin')
        # Get fingerprint - bitcoinlib provides this directly
        # The fingerprint is the first 4 bytes (8 hex chars) of HASH160(pubkey)
        fingerprint = root.fingerprint.hex() if hasattr(root, 'fingerprint') else root.hash160[:4].hex()
        return fingerprint
    except Exception as e:
        raise ValueError(f"Failed to derive master fingerprint: {str(e)}")


def derive_bip84_account_zpub(mnemonic: str, account: int = 0) -> str:
    """Return BIP84 account public extended key (zpub) for m/84'/0'/account'.
    Uses bip_utils to avoid any DB usage.
    """
    mnorm = _normalize_mnemonic(mnemonic)

    # Validate mnemonic first
    mnemo_validator = Mnemonic('english')
    if not mnemo_validator.check(mnorm):
        raise ValueError(f"Invalid mnemonic: {mnorm}")

    try:
        seed = BtcLibMnemonic().to_seed(mnorm)
        root = HDKey.from_seed(seed, network='bitcoin')
        acc = root.subkey_for_path(f"m/84'/0'/{int(account)}'")
        # Return extended public key; bitcoinlib uses appropriate version bytes per network/purpose
        return acc.wif_public()
    except Exception as e:
        raise ValueError(f"Failed to derive zpub: {str(e)}")
