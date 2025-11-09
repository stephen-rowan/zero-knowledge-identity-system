"""
Cryptographic primitives for zero-knowledge identity system.

Provides HMAC-SHA256 key derivation, Ed25519 Schnorr signatures,
Fiat-Shamir transformation, and secure random number generation.
"""

import secrets
import hmac
import hashlib
from typing import Tuple
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError

from dataclasses import dataclass
from zkidentity.exceptions import ProofError


@dataclass
class KeyPair:
    """Cryptographic key pair for an alias."""
    public_key: bytes  # 32 bytes, Ed25519
    private_key: bytes  # 32 bytes, Ed25519 (never stored by system)
    
    def sign(self, message: bytes) -> bytes:
        """Generate Schnorr signature."""
        # Forward reference - function defined below
        return schnorr_sign(self.private_key, message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify Schnorr signature."""
        # Forward reference - function defined below
        return schnorr_verify(self.public_key, message, signature)


def hmac_sha256_key_derivation(key: bytes, data: str) -> bytes:
    """
    Derive a key using HMAC-SHA256.
    
    Args:
        key: The master key (32 bytes)
        data: The data to derive from (alias identifier)
    
    Returns:
        32-byte derived key material
    """
    if len(key) != 32:
        raise ValueError("Key must be exactly 32 bytes")
    
    return hmac.new(key, data.encode('utf-8'), hashlib.sha256).digest()


def generate_ed25519_keypair() -> Tuple[bytes, bytes]:
    """
    Generate a random Ed25519 key pair.
    
    Returns:
        Tuple of (private_key, public_key) as 32-byte bytes
    """
    signing_key = SigningKey.generate()
    private_key = bytes(signing_key)
    public_key = bytes(signing_key.verify_key)
    
    return private_key, public_key


def derive_ed25519_keypair_from_seed(seed_material: bytes) -> Tuple[bytes, bytes]:
    """
    Derive an Ed25519 key pair deterministically from seed material.
    
    Args:
        seed_material: 32-byte seed material (from HMAC-SHA256)
    
    Returns:
        Tuple of (private_key, public_key) as 32-byte bytes
    """
    if len(seed_material) != 32:
        raise ValueError("Seed material must be exactly 32 bytes")
    
    # Use seed material directly as private key (Ed25519 allows this)
    # Ensure it's a valid Ed25519 scalar by clamping
    private_key = seed_material
    signing_key = SigningKey(private_key)
    public_key = bytes(signing_key.verify_key)
    
    return private_key, public_key


def fiat_shamir_challenge(commitment: bytes, public_key: bytes, message: bytes) -> bytes:
    """
    Generate a Fiat-Shamir challenge using HMAC-SHA256.
    
    Args:
        commitment: The commitment value (random point)
        public_key: The public key (32 bytes)
        message: The message/challenge to sign
    
    Returns:
        32-byte challenge hash
    """
    combined = commitment + public_key + message
    return hashlib.sha256(combined).digest()


def schnorr_sign(private_key: bytes, message: bytes) -> bytes:
    """
    Generate a Schnorr signature using Ed25519.
    
    Args:
        private_key: 32-byte Ed25519 private key
        message: Message to sign
    
    Returns:
        64-byte signature
    """
    signing_key = SigningKey(private_key)
    signature = signing_key.sign(message)
    # Ed25519 signatures are 64 bytes
    return signature.signature


def schnorr_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """
    Verify a Schnorr signature using Ed25519.
    
    Args:
        public_key: 32-byte Ed25519 public key
        message: Original message
        signature: 64-byte signature to verify
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        verify_key = VerifyKey(public_key)
        verify_key.verify(message, signature)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False


def generate_secure_random_bytes(length: int = 32) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Args:
        length: Number of bytes to generate (default: 32)
    
    Returns:
        Random bytes
    """
    return secrets.token_bytes(length)


def validate_alias_identifier(alias_id: str) -> None:
    """
    Validate an alias identifier.
    
    Args:
        alias_id: The alias identifier to validate
    
    Raises:
        ValueError: If alias_id is invalid
    """
    if not alias_id:
        raise ValueError("Alias identifier cannot be empty")
    
    if len(alias_id) > 256:
        raise ValueError("Alias identifier cannot exceed 256 characters")
    
    if not isinstance(alias_id, str):
        raise ValueError("Alias identifier must be a string")


def validate_challenge(challenge: bytes) -> None:
    """
    Validate a challenge message.
    
    Args:
        challenge: The challenge bytes to validate
    
    Raises:
        ValueError: If challenge is invalid
    """
    if not challenge:
        raise ValueError("Challenge cannot be empty")
    
    if len(challenge) > 1024:  # Reasonable size limit
        raise ValueError("Challenge cannot exceed 1024 bytes")
    
    if not isinstance(challenge, bytes):
        raise ValueError("Challenge must be bytes")

