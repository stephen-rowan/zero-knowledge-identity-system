"""
Master seed generation and backup functionality.

Users are responsible for secure storage - system never stores seeds.
"""

import secrets
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from zkidentity.exceptions import AliasError
from zkidentity.crypto import hmac_sha256_key_derivation, derive_ed25519_keypair_from_seed


class MasterSeed:
    """
    Master seed for deterministic alias key derivation.
    
    The seed is never stored by the system - users must manage it securely.
    """
    
    SEED_SIZE = 32  # 256 bits
    
    def __init__(self, seed_bytes: bytes):
        """
        Initialize master seed.
        
        Args:
            seed_bytes: 32-byte seed value
        
        Raises:
            ValueError: If seed is not 32 bytes
        """
        if len(seed_bytes) != self.SEED_SIZE:
            raise ValueError(f"Seed must be exactly {self.SEED_SIZE} bytes")
        self.seed_bytes = seed_bytes
    
    def derive_key_pair(self, alias_id: str) -> tuple[bytes, bytes]:
        """
        Derive a key pair deterministically from this seed and alias identifier.
        
        Args:
            alias_id: Unique alias identifier
        
        Returns:
            Tuple of (private_key, public_key) as 32-byte bytes
        """
        # Derive key material using HMAC-SHA256
        key_material = hmac_sha256_key_derivation(self.seed_bytes, alias_id)
        
        # Derive Ed25519 key pair from material
        private_key, public_key = derive_ed25519_keypair_from_seed(key_material)
        
        return private_key, public_key
    
    def export_backup(self, password: str) -> str:
        """
        Export seed in encrypted backup format.
        
        Args:
            password: Password for encryption
        
        Returns:
            Encrypted backup string (base64-encoded)
        """
        # Derive encryption key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'zkidentity_seed_backup',  # Fixed salt for deterministic backup
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        # Encrypt seed
        encrypted = fernet.encrypt(self.seed_bytes)
        return base64.b64encode(encrypted).decode('ascii')
    
    @classmethod
    def import_backup(cls, backup: str, password: str) -> 'MasterSeed':
        """
        Import seed from encrypted backup.
        
        Args:
            backup: Encrypted backup string
            password: Password for decryption
        
        Returns:
            MasterSeed instance
        
        Raises:
            AliasError: If backup format is invalid or password is incorrect
        """
        try:
            # Derive encryption key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'zkidentity_seed_backup',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)
            
            # Decrypt seed
            encrypted = base64.b64decode(backup)
            seed_bytes = fernet.decrypt(encrypted)
            
            return cls(seed_bytes)
        except Exception as e:
            raise AliasError(f"Failed to import seed backup: {e}. Check password and backup format.")


def generate_master_seed() -> MasterSeed:
    """
    Generate a new 32-byte master seed.
    
    Returns:
        MasterSeed instance
    
    Warning:
        Store this seed securely - losing it means losing access to all seed-derived aliases.
    """
    seed_bytes = secrets.token_bytes(32)
    return MasterSeed(seed_bytes)


def export_seed_backup(seed: MasterSeed, password: str) -> str:
    """
    Export master seed in encrypted backup format.
    
    Args:
        seed: MasterSeed instance
        password: Password for encryption
    
    Returns:
        Encrypted backup string
    
    Warning:
        Store this backup securely. Losing both the seed and backup means permanent loss of access.
    """
    return seed.export_backup(password)


def import_seed_backup(backup: str, password: str) -> MasterSeed:
    """
    Import master seed from encrypted backup.
    
    Args:
        backup: Encrypted backup string
        password: Password for decryption
    
    Returns:
        MasterSeed instance
    
    Raises:
        AliasError: If backup format is invalid or password is incorrect
    """
    return MasterSeed.import_backup(backup, password)


def warn_seed_loss() -> str:
    """
    Get warning message about seed loss consequences.
    
    Returns:
        Warning message
    """
    return """
    ⚠️  WARNING: Master Seed Security
    
    - Losing your master seed means PERMANENT loss of access to all seed-derived aliases
    - The system CANNOT recover lost seeds - you must maintain your own backups
    - Store seeds securely: password manager, hardware wallet, or encrypted file
    - Never share your master seed with anyone
    - Consider creating multiple secure backups in different locations
    """

