"""
Alias creation and management.

Provides functions for creating independent and seed-derived aliases,
managing alias lifecycle, and ensuring cryptographic unlinkability.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import secrets

from zkidentity.exceptions import AliasError
from zkidentity.crypto import (
    generate_ed25519_keypair,
    hmac_sha256_key_derivation,
    derive_ed25519_keypair_from_seed,
    validate_alias_identifier,
)
from zkidentity.storage import get_default_storage, AliasStorage
from zkidentity.seed import MasterSeed
from zkidentity.proof import generate_proof, ZeroKnowledgeProof


@dataclass
class Alias:
    """An autonomous identity with its own cryptographic key pair."""
    alias_id: str
    public_key: bytes  # 32 bytes, Ed25519
    private_key: bytes  # 32 bytes, Ed25519 (never stored by system)
    is_revoked: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    revoked_at: Optional[str] = None
    master_seed_id: Optional[str] = None  # Reference if seed-derived
    
    def revoke(self) -> None:
        """Mark alias as revoked."""
        if self.is_revoked:
            raise AliasError(f"Alias '{self.alias_id}' is already revoked")
        self.is_revoked = True
        self.revoked_at = datetime.now().isoformat()
    
    def is_valid(self) -> bool:
        """Check if alias is not revoked."""
        return not self.is_revoked


# Track aliases in memory (private keys never stored)
_alias_registry: dict[str, Alias] = {}
_storage = get_default_storage()


def create_independent_alias(alias_id: str) -> Alias:
    """
    Create an alias with an independently generated key pair.
    
    Args:
        alias_id: User-chosen identifier, must be unique per user
    
    Returns:
        Alias object with generated key pair
    
    Raises:
        ValueError: If alias_id is empty, too long, or duplicate
        AliasError: If alias creation fails
    
    Requirements: FR-001, FR-004, FR-017, FR-018
    """
    # Validate alias identifier (FR-018)
    validate_alias_identifier(alias_id)
    
    # Check for duplicates in memory registry (FR-017)
    if alias_id in _alias_registry:
        raise ValueError(f"Alias '{alias_id}' already exists")
    
    # Check storage for existing alias (FR-017)
    existing = _storage.load_alias(alias_id)
    if existing:
        raise ValueError(f"Alias '{alias_id}' already exists in storage")
    
    # Generate random key pair
    private_key, public_key = generate_ed25519_keypair()
    
    # Create alias
    alias = Alias(
        alias_id=alias_id,
        public_key=public_key,
        private_key=private_key,
        is_revoked=False,
        master_seed_id=None
    )
    
    # Register in memory
    _alias_registry[alias_id] = alias
    
    # Save metadata to storage (public key only, never private key)
    _storage.save_alias(
        alias_id=alias_id,
        public_key=public_key.hex(),
        is_revoked=False,
        created_at=alias.created_at,
        master_seed_id=None
    )
    
    return alias


def derive_alias_from_seed(master_seed: MasterSeed, alias_id: str) -> Alias:
    """
    Derive an alias from a master seed using HMAC-SHA256.
    
    Args:
        master_seed: MasterSeed instance
        alias_id: User-chosen identifier, must be unique per seed
    
    Returns:
        Alias object with deterministically derived key pair
    
    Raises:
        ValueError: If seed is not 32 bytes, alias_id invalid, or duplicate
        AliasError: If derivation fails
    
    Requirements: FR-002, FR-003, FR-012, FR-017, FR-018
    """
    # Validate alias identifier (FR-018)
    validate_alias_identifier(alias_id)
    
    # Check for duplicates in memory registry (FR-017)
    if alias_id in _alias_registry:
        raise ValueError(f"Alias '{alias_id}' already exists")
    
    # Check storage for existing alias with same seed reference (FR-017)
    existing = _storage.load_alias(alias_id)
    if existing:
        # If exists with different seed reference, that's an error
        if existing.get('master_seed_id') != 'master-seed-001':
            raise ValueError(f"Alias '{alias_id}' already exists with different seed reference")
        raise ValueError(f"Alias '{alias_id}' already exists in storage")
    
    # Derive key pair deterministically
    private_key, public_key = master_seed.derive_key_pair(alias_id)
    
    # Create alias
    alias = Alias(
        alias_id=alias_id,
        public_key=public_key,
        private_key=private_key,
        is_revoked=False,
        master_seed_id='master-seed-001'  # Reference to seed
    )
    
    # Register in memory
    _alias_registry[alias_id] = alias
    
    # Save metadata to storage (public key only, never private key)
    _storage.save_alias(
        alias_id=alias_id,
        public_key=public_key.hex(),
        is_revoked=False,
        created_at=alias.created_at,
        master_seed_id=alias.master_seed_id
    )
    
    return alias


def revoke_alias(alias: Alias) -> None:
    """
    Revoke an alias, preventing future use.
    
    Args:
        alias: The alias to revoke
    
    Raises:
        AliasError: If alias is already revoked
    
    Requirements: FR-016
    """
    if alias.is_revoked:
        raise AliasError(f"Alias '{alias.alias_id}' is already revoked")
    
    alias.revoke()
    
    # Update storage
    _storage.update_alias(
        alias.alias_id,
        is_revoked=True,
        revoked_at=alias.revoked_at
    )


def get_alias(alias_id: str) -> Optional[Alias]:
    """
    Get alias by identifier.
    
    Args:
        alias_id: Alias identifier
    
    Returns:
        Alias object if found, None otherwise
    
    Note:
        Returns alias from memory registry. Private keys are not stored,
        so seed-derived aliases must be re-derived from master seed.
    """
    return _alias_registry.get(alias_id)


def list_aliases() -> List[Alias]:
    """
    List all aliases from storage.
    
    Returns:
        List of Alias objects (without private keys for independent aliases)
    
    Note:
        Returns aliases from persistent storage. Private keys are not available
        for independent aliases unless they were created in the current session.
        For seed-derived aliases, use load_alias_from_storage() with master_seed.
    """
    # Load all aliases from storage
    stored_aliases = _storage.list_aliases()
    result = []
    
    for stored in stored_aliases:
        # Check if we have it in memory (with private key)
        if stored['alias_id'] in _alias_registry:
            result.append(_alias_registry[stored['alias_id']])
        else:
            # Create alias from storage (without private key)
            alias = Alias(
                alias_id=stored['alias_id'],
                public_key=bytes.fromhex(stored['public_key']),
                private_key=b'',  # Not available for independent aliases
                is_revoked=stored.get('is_revoked', False),
                created_at=stored.get('created_at', datetime.now().isoformat()),
                revoked_at=stored.get('revoked_at'),
                master_seed_id=stored.get('master_seed_id')
            )
            result.append(alias)
    
    return result


def load_alias_from_storage(alias_id: str, master_seed: Optional[MasterSeed] = None) -> Optional[Alias]:
    """
    Load alias from storage and optionally re-derive private key from seed.
    
    Args:
        alias_id: Alias identifier
        master_seed: Master seed to re-derive private key (if seed-derived)
    
    Returns:
        Alias object if found, None otherwise
    
    Note:
        If alias is seed-derived and master_seed is provided, private key
        will be re-derived. Otherwise, only public key metadata is available.
    """
    stored = _storage.load_alias(alias_id)
    if not stored:
        return None
    
    # If seed-derived and seed provided, re-derive private key
    private_key = None
    if stored.get('master_seed_id') and master_seed:
        try:
            private_key, public_key = master_seed.derive_key_pair(alias_id)
            # Verify public key matches
            if public_key.hex() != stored['public_key']:
                raise AliasError(f"Public key mismatch for alias '{alias_id}'")
        except Exception as e:
            raise AliasError(f"Failed to derive private key: {e}")
    else:
        # For independent aliases or when seed not provided, we can't recover private key
        # Return alias with None private key (read-only)
        public_key = bytes.fromhex(stored['public_key'])
    
    alias = Alias(
        alias_id=stored['alias_id'],
        public_key=public_key,
        private_key=private_key or b'',  # Empty if not available
        is_revoked=stored.get('is_revoked', False),
        created_at=stored.get('created_at', datetime.now().isoformat()),
        revoked_at=stored.get('revoked_at'),
        master_seed_id=stored.get('master_seed_id')
    )
    
    return alias


def authenticate(alias: Alias, challenge: bytes) -> ZeroKnowledgeProof:
    """
    Authenticate using an alias identity with a zero-knowledge proof.
    
    This function combines alias public key presentation with proof generation
    to enable authentication flows. The user presents their public key to a
    service, receives a challenge, and generates a proof to authenticate.
    
    Args:
        alias: The alias to authenticate with (must have private key available)
        challenge: Challenge message/nonce from the service
    
    Returns:
        ZeroKnowledgeProof object containing the proof
    
    Raises:
        AliasError: If alias is revoked, invalid, or private key is not available
        ValueError: If challenge is invalid
    
    Requirements: FR-008, User Story 3
    
    Example:
        >>> alias = get_alias("my-identity")
        >>> challenge = service_challenge  # From service
        >>> proof = authenticate(alias, challenge)
        >>> # Send proof to service for verification
    """
    # Check alias has private key available
    if not alias.private_key:
        raise AliasError(
            f"Alias '{alias.alias_id}' private key is not available. "
            "For independent aliases, create the alias in this session to authenticate. "
            "For seed-derived aliases, use the master seed to re-derive the alias."
        )
    
    # Generate proof using the alias and challenge
    proof = generate_proof(alias, challenge)
    
    return proof


def create_authentication_request(alias: Alias) -> dict:
    """
    Create an authentication request with alias public key.
    
    This helper function prepares the initial authentication request
    that can be sent to a service. The service will respond
    with a challenge that can be used with authenticate().
    
    Args:
        alias: The alias to authenticate with
    
    Returns:
        Dictionary containing authentication request data
    
    Requirements: FR-008, User Story 3
    
    Example:
        >>> alias = get_alias("my-identity")
        >>> request = create_authentication_request(alias)
        >>> # Send request to service
        >>> # Service responds with challenge
        >>> proof = authenticate(alias, challenge)
    """
    return {
        "public_key": alias.public_key.hex(),
        "alias_id": alias.alias_id,
        "created_at": datetime.now().isoformat()
    }


def prepare_authentication_response(proof: ZeroKnowledgeProof) -> dict:
    """
    Prepare authentication response with proof for service.
    
    This helper function formats the proof for transmission to a service.
    The service can then verify the proof using verify_proof().
    
    Args:
        proof: The ZeroKnowledgeProof from authenticate()
    
    Returns:
        Dictionary containing proof data for service
    
    Requirements: FR-008, User Story 3
    
    Example:
        >>> proof = authenticate(alias, challenge)
        >>> response = prepare_authentication_response(proof)
        >>> # Send response to service
    """
    return {
        "proof_bytes": proof.proof_bytes.hex(),
        "public_key": proof.public_key.hex(),
        "challenge": proof.challenge.hex(),
        "created_at": proof.created_at
    }

