# API Contracts: Zero-Knowledge Identity System

**Date**: 2024-12-19  
**Feature**: Zero-Knowledge Identity System  
**Type**: Python Library API

## Overview

This document defines the Python API contracts for the `zkidentity` library. The library provides functionality for creating and managing alias identities, generating zero-knowledge proofs, and working with verifiable credentials.

## Core Module: `zkidentity.alias`

### `create_independent_alias(alias_id: str) -> Alias`

Create an alias with an independently generated key pair.

**Parameters**:
- `alias_id` (str): User-chosen identifier, must be unique per user

**Returns**: `Alias` object with generated key pair

**Raises**:
- `ValueError`: If `alias_id` is empty, too long, or duplicate
- `AliasError`: If alias creation fails

**Example**:
```python
from zkidentity import create_independent_alias

alias = create_independent_alias("work-identity")
print(alias.public_key.hex())
```

**Requirements**: FR-001, FR-004

---

### `derive_alias_from_seed(master_seed: bytes, alias_id: str) -> Alias`

Derive an alias from a master seed using HMAC-SHA256.

**Parameters**:
- `master_seed` (bytes): 32-byte master seed
- `alias_id` (str): User-chosen identifier, must be unique per seed

**Returns**: `Alias` object with deterministically derived key pair

**Raises**:
- `ValueError`: If seed is not 32 bytes, alias_id invalid, or duplicate
- `AliasError`: If derivation fails

**Example**:
```python
from zkidentity import derive_alias_from_seed
import secrets

seed = secrets.token_bytes(32)
alias = derive_alias_from_seed(seed, "personal-identity")
```

**Requirements**: FR-002, FR-003, FR-012

---

### `revoke_alias(alias: Alias) -> None`

Revoke an alias, preventing future use.

**Parameters**:
- `alias` (Alias): The alias to revoke

**Returns**: None

**Raises**:
- `AliasError`: If alias is already revoked

**Example**:
```python
from zkidentity import revoke_alias

revoke_alias(alias)
assert alias.is_revoked == True
```

**Requirements**: FR-016

---

## Core Module: `zkidentity.proof`

### `generate_proof(alias: Alias, challenge: bytes) -> ZeroKnowledgeProof`

Generate a zero-knowledge proof (Schnorr signature) for alias ownership.

**Parameters**:
- `alias` (Alias): The alias to prove ownership of
- `challenge` (bytes): Challenge message/nonce from verifier

**Returns**: `ZeroKnowledgeProof` object

**Raises**:
- `AliasError`: If alias is revoked
- `ValueError`: If challenge is empty or invalid

**Example**:
```python
from zkidentity import generate_proof
import secrets

challenge = secrets.token_bytes(32)
proof = generate_proof(alias, challenge)
```

**Requirements**: FR-005, FR-007

---

### `verify_proof(proof: ZeroKnowledgeProof, public_key: bytes, challenge: bytes) -> bool`

Verify a zero-knowledge proof against a public key and challenge.

**Parameters**:
- `proof` (ZeroKnowledgeProof): The proof to verify
- `public_key` (bytes): The alias public key (32 bytes)
- `challenge` (bytes): The challenge message used in proof

**Returns**: `bool` - True if proof is valid, False otherwise

**Raises**:
- `ValueError`: If proof format is invalid
- `ProofError`: If proof is malformed

**Example**:
```python
from zkidentity import verify_proof

is_valid = verify_proof(proof, alias.public_key, challenge)
assert is_valid == True
```

**Requirements**: FR-006, FR-013, FR-014

---

## Core Module: `zkidentity.credential`

### `create_credential(alias: Alias, credential_data: dict) -> VerifiableCredential`

Create a W3C Verifiable Credential associated with an alias.

**Parameters**:
- `alias` (Alias): The alias to associate the credential with
- `credential_data` (dict): Credential subject data (will be wrapped in W3C VC format)

**Returns**: `VerifiableCredential` object

**Raises**:
- `ValueError`: If credential_data is invalid
- `CredentialError`: If credential creation fails

**Example**:
```python
from zkidentity import create_credential

cred_data = {
    "degree": "Bachelor of Science",
    "university": "Example University"
}
credential = create_credential(alias, cred_data)
```

**Requirements**: FR-009

---

### `present_credential(credential: VerifiableCredential, alias: Alias, challenge: bytes) -> CredentialPresentation`

Present a verifiable credential with a zero-knowledge proof.

**Parameters**:
- `credential` (VerifiableCredential): The credential to present
- `alias` (Alias): The alias presenting the credential
- `challenge` (bytes): Challenge from verifier

**Returns**: `CredentialPresentation` object

**Raises**:
- `AliasError`: If alias is revoked or doesn't match credential
- `CredentialError`: If credential is invalid

**Example**:
```python
from zkidentity import present_credential
import secrets

challenge = secrets.token_bytes(32)
presentation = present_credential(credential, alias, challenge)
```

**Requirements**: FR-009, FR-010

---

## Core Module: `zkidentity.storage`

### `save_aliases(aliases: list[Alias], filepath: str) -> None`

Save alias metadata to JSON file (public keys only, no private keys).

**Parameters**:
- `aliases` (list[Alias]): List of aliases to save
- `filepath` (str): Path to JSON file

**Raises**:
- `IOError`: If file write fails
- `ValueError`: If aliases data is invalid

**Example**:
```python
from zkidentity import save_aliases

aliases = [alias1, alias2, alias3]
save_aliases(aliases, "~/.zkidentity/aliases.json")
```

**Requirements**: FR-019 (does not store private keys)

---

### `load_aliases(filepath: str) -> list[Alias]`

Load alias metadata from JSON file.

**Parameters**:
- `filepath` (str): Path to JSON file

**Returns**: `list[Alias]` with public keys and metadata (private keys must be derived separately)

**Raises**:
- `IOError`: If file read fails
- `ValueError`: If file format is invalid

**Example**:
```python
from zkidentity import load_aliases

aliases = load_aliases("~/.zkidentity/aliases.json")
# Note: Private keys must be derived from master seed if seed-derived
```

---

## Core Module: `zkidentity.seed`

### `generate_master_seed() -> bytes`

Generate a new 32-byte master seed.

**Returns**: `bytes` - 32-byte secure random seed

**Example**:
```python
from zkidentity import generate_master_seed

seed = generate_master_seed()
# User must store this securely
```

**Requirements**: Secure random generation

---

### `export_seed_backup(seed: bytes, password: str) -> str`

Export master seed in encrypted backup format.

**Parameters**:
- `seed` (bytes): The master seed to export
- `password` (str): Password for encryption

**Returns**: `str` - Encrypted backup string (e.g., base64-encoded)

**Raises**:
- `ValueError`: If seed is invalid

**Example**:
```python
from zkidentity import export_seed_backup

backup = export_seed_backup(seed, "user-password")
# Save backup securely
```

**Requirements**: FR-020

---

### `import_seed_backup(backup: str, password: str) -> bytes`

Import master seed from encrypted backup.

**Parameters**:
- `backup` (str): Encrypted backup string
- `password` (str): Password for decryption

**Returns**: `bytes` - The master seed

**Raises**:
- `ValueError`: If backup format is invalid or password is incorrect

**Example**:
```python
from zkidentity import import_seed_backup

seed = import_seed_backup(backup_string, "user-password")
```

---

## Data Classes

### `Alias`

```python
@dataclass
class Alias:
    alias_id: str
    public_key: bytes  # 32 bytes, Ed25519
    is_revoked: bool
    created_at: datetime
    revoked_at: Optional[datetime]
    master_seed_id: Optional[str]
    
    def generate_proof(self, challenge: bytes) -> ZeroKnowledgeProof: ...
    def revoke(self) -> None: ...
    def is_valid(self) -> bool: ...
```

### `ZeroKnowledgeProof`

```python
@dataclass
class ZeroKnowledgeProof:
    proof_bytes: bytes
    challenge: bytes
    public_key: bytes  # 32 bytes
    created_at: datetime
    
    def verify(self, public_key: bytes, challenge: bytes) -> bool: ...
    def is_valid(self) -> bool: ...
```

### `VerifiableCredential`

```python
@dataclass
class VerifiableCredential:
    credential_id: str
    credential_subject: dict
    issuer: str
    alias_public_key: bytes
    credential_json: dict  # Full W3C VC structure
    created_at: datetime
    expires_at: Optional[datetime]
    
    def present(self, proof: ZeroKnowledgeProof) -> CredentialPresentation: ...
    def validate(self) -> bool: ...
```

---

## Error Classes

```python
class ZKIdentityError(Exception):
    """Base exception for zkidentity library"""
    pass

class AliasError(ZKIdentityError):
    """Alias-related errors"""
    pass

class ProofError(ZKIdentityError):
    """Proof-related errors"""
    pass

class CredentialError(ZKIdentityError):
    """Credential-related errors"""
    pass
```

---

## Security Guarantees

1. **No Key Exposure**: Private keys and master seeds are never returned, logged, or exposed (FR-011, SC-010)
2. **Input Validation**: All inputs are validated; invalid inputs raise `ValueError`
3. **Error Handling**: Errors do not leak sensitive information
4. **Cryptographic Correctness**: All operations use secure cryptographic primitives

---

## Performance Requirements

- `create_independent_alias`: <1s (SC-001)
- `derive_alias_from_seed`: <1s (SC-001)
- `generate_proof`: <500ms (SC-002)
- `verify_proof`: <200ms (SC-003)

