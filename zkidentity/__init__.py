"""
Zero-Knowledge Identity System

A library for creating and managing multiple cryptographically unlinkable alias identities.
"""

__version__ = "0.1.0"
__author__ = "Zero-Knowledge Identity System"

# Core modules
from zkidentity.exceptions import (
    ZKIdentityError,
    AliasError,
    ProofError,
    CredentialError,
)

# Crypto
from zkidentity.crypto import KeyPair

# Alias functions
from zkidentity.alias import (
    create_independent_alias,
    derive_alias_from_seed,
    revoke_alias,
    get_alias,
    list_aliases,
    Alias,
)

# Seed functions
from zkidentity.seed import (
    generate_master_seed,
    export_seed_backup,
    import_seed_backup,
    MasterSeed,
)

# Proof functions
from zkidentity.proof import (
    generate_proof,
    verify_proof,
    ZeroKnowledgeProof,
    generate_challenge,
)

__all__ = [
    # Exceptions
    "ZKIdentityError",
    "AliasError",
    "ProofError",
    "CredentialError",
    # Alias functions
    "create_independent_alias",
    "derive_alias_from_seed",
    "revoke_alias",
    "get_alias",
    "list_aliases",
    "Alias",
    "KeyPair",
    # Seed functions
    "generate_master_seed",
    "export_seed_backup",
    "import_seed_backup",
    "MasterSeed",
    # Proof functions
    "generate_proof",
    "verify_proof",
    "ZeroKnowledgeProof",
    "generate_challenge",
]

