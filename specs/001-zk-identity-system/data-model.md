# Data Model: Zero-Knowledge Identity System

**Date**: 2024-12-19  
**Feature**: Zero-Knowledge Identity System  
**Based on**: [spec.md](./spec.md)

## Overview

This document defines the data structures, entities, and relationships for the zero-knowledge identity system. The system manages alias identities, cryptographic key pairs, zero-knowledge proofs, and verifiable credentials.

## Core Entities

### MasterSeed

A secret value used to deterministically derive multiple alias key pairs.

**Attributes**:
- `seed_bytes` (bytes, 32 bytes): The master seed value (never stored by system, user-managed)
- `derived_aliases` (list[str]): List of alias identifiers derived from this seed (metadata only)

**Constraints**:
- Must be 32 bytes (256 bits) for security
- Never exposed in logs, errors, or system outputs (FR-011, SC-010)
- User is responsible for secure storage (FR-019)

**Operations**:
- `derive_key_pair(alias_id: str) -> KeyPair`: Deterministic key derivation using HMAC-SHA256
- `export_backup() -> str`: Export seed in secure format for backup (FR-020)

---

### Alias

An autonomous identity with its own cryptographic key pair.

**Attributes**:
- `alias_id` (str): User-chosen identifier, unique per master seed (seed-derived) or per user (independent)
- `public_key` (bytes, 32 bytes): Ed25519 public key
- `private_key` (bytes, 32 bytes): Ed25519 private key (never stored by system, user-managed)
- `is_revoked` (bool): Revocation status (default: False)
- `created_at` (datetime): Creation timestamp
- `revoked_at` (datetime, optional): Revocation timestamp if revoked
- `master_seed_id` (str, optional): Reference to master seed if seed-derived, None if independent

**Constraints**:
- `alias_id` must be unique per master seed (seed-derived) or per user (independent) (FR-017)
- `alias_id` is user-chosen string with reasonable length limits (FR-018)
- Public keys must appear random and unlinkable to other aliases (FR-003, FR-004)
- Revocation prevents future use but past proofs remain valid (FR-016)

**State Transitions**:
1. **Created**: `is_revoked=False`, `revoked_at=None`
2. **Revoked**: `is_revoked=True`, `revoked_at=timestamp`
3. **Deleted**: Removed from storage (but past proofs remain valid)

**Operations**:
- `generate_proof(challenge: bytes) -> ZeroKnowledgeProof`: Generate Schnorr signature proof
- `revoke()`: Mark alias as revoked (FR-016)
- `is_valid() -> bool`: Check if alias is not revoked

---

### KeyPair

A cryptographic public/private key pair associated with an alias.

**Attributes**:
- `public_key` (bytes, 32 bytes): Ed25519 public key
- `private_key` (bytes, 32 bytes): Ed25519 private key (never stored by system)

**Constraints**:
- Ed25519 curve (via PyNaCl)
- Private key never exposed (FR-011)
- Deterministic generation for seed-derived aliases (FR-012)

**Operations**:
- `sign(message: bytes) -> bytes`: Generate Schnorr signature
- `verify(message: bytes, signature: bytes) -> bool`: Verify signature

**Key Derivation** (for seed-derived aliases):
```
key_material = HMAC-SHA256(seed_bytes, alias_id)
private_key = Ed25519_derive_private_key(key_material)
public_key = Ed25519_derive_public_key(private_key)
```

---

### ZeroKnowledgeProof

A non-interactive proof (Schnorr signature with Fiat-Shamir) demonstrating possession of a private key.

**Attributes**:
- `proof_bytes` (bytes): The Schnorr signature proof
- `challenge` (bytes): The challenge message/nonce used in proof
- `public_key` (bytes, 32 bytes): The alias public key this proof is for
- `created_at` (datetime): Proof generation timestamp

**Constraints**:
- Proofs for different aliases must be cryptographically unlinkable (FR-007)
- Private key never revealed in proof (FR-005)
- Challenge must be provided by verifier to prevent replay attacks

**Operations**:
- `verify(public_key: bytes, challenge: bytes) -> bool`: Verify proof validity (FR-006)
- `is_valid() -> bool`: Check proof structure and format (FR-013)

**Fiat-Shamir Transformation**:
```
commitment = random_point()
challenge = HMAC-SHA256(commitment || public_key || message)
response = private_key * challenge + nonce
proof = (commitment, response)
```

---

### VerifiableCredential

A credential or claim associated with an alias following W3C Verifiable Credentials Data Model v1.1+.

**Attributes**:
- `credential_id` (str): Unique identifier for the credential
- `credential_subject` (dict): The credential claims/attributes (JSON-LD format)
- `issuer` (str): Issuer identifier (DID or alias public key)
- `alias_public_key` (bytes, 32 bytes): The alias this credential is associated with
- `credential_json` (dict): Full W3C VC JSON structure
- `created_at` (datetime): Credential issuance timestamp
- `expires_at` (datetime, optional): Credential expiration if applicable

**Constraints**:
- Must follow W3C Verifiable Credentials Data Model v1.1+ standard
- Credential presentations must be unlinkable across different aliases (FR-010)
- Can be presented with zero-knowledge proof (FR-009)

**Operations**:
- `present(proof: ZeroKnowledgeProof) -> CredentialPresentation`: Create presentation with proof
- `validate() -> bool`: Validate credential structure and JSON-LD

---

### CredentialPresentation

A verifiable credential presented with a zero-knowledge proof.

**Attributes**:
- `credential` (VerifiableCredential): The credential being presented
- `proof` (ZeroKnowledgeProof): The zero-knowledge proof of alias ownership
- `presented_at` (datetime): Presentation timestamp

**Constraints**:
- Presentations from different aliases must be unlinkable (FR-010)
- Proof must validate against credential's alias public key

---

### ChallengeMessage

A message or nonce provided by a verifier for proof generation.

**Attributes**:
- `challenge_bytes` (bytes): The challenge nonce/message
- `created_at` (datetime): Challenge generation timestamp
- `expires_at` (datetime, optional): Challenge expiration for freshness

**Constraints**:
- Must be included in zero-knowledge proof to prevent replay attacks
- Should be unique per verification request
- Reasonable size limits (FR-014)

---

## Relationships

```
MasterSeed (1) ──< (many) Alias (seed-derived)
User (1) ──< (many) Alias (independent)
Alias (1) ──< (many) ZeroKnowledgeProof
Alias (1) ──< (many) VerifiableCredential
VerifiableCredential (1) ──< (many) CredentialPresentation
CredentialPresentation (1) ──> (1) ZeroKnowledgeProof
```

## Storage Schema (File-based JSON)

For library/CLI use, aliases and metadata stored in JSON format:

```json
{
  "version": "1.0",
  "aliases": [
    {
      "alias_id": "work-identity",
      "public_key": "<base64-encoded>",
      "is_revoked": false,
      "created_at": "2024-12-19T10:00:00Z",
      "master_seed_id": "seed-001"
    }
  ],
  "credentials": [
    {
      "credential_id": "cred-001",
      "alias_public_key": "<base64-encoded>",
      "credential_json": { /* W3C VC structure */ }
    }
  ]
}
```

**Note**: Private keys and master seeds are NEVER stored in this file (FR-019). Users manage keys separately.

## Validation Rules

### Alias Identifier
- Type: string
- Length: 1-256 characters (reasonable limit)
- Uniqueness: Per master seed (seed-derived) or per user (independent) (FR-017)
- Format: User-chosen, no special validation beyond length

### Public Key
- Type: bytes (32 bytes for Ed25519)
- Format: Ed25519 public key
- Uniqueness: Not enforced (collisions extremely unlikely)

### Private Key
- Type: bytes (32 bytes for Ed25519)
- Never stored or exposed (FR-011, SC-010)

### Zero-Knowledge Proof
- Must validate against public key and challenge (FR-006)
- Must be correctly formed (FR-013)
- Invalid proofs rejected with appropriate error handling (FR-014)

## State Management

### Alias Lifecycle
1. **Creation**: Generate key pair (independent or seed-derived), create Alias entity
2. **Active**: Alias can generate proofs, present credentials
3. **Revoked**: `is_revoked=True`, future operations rejected, past proofs remain valid
4. **Deleted**: Removed from storage, past proofs remain cryptographically valid

### Revocation
- Revocation prevents future authentication and proof generation (FR-016)
- Past proofs remain valid (cannot be retroactively invalidated)
- Revocation status stored in alias metadata

## Performance Considerations

- Alias creation: <1s (SC-001) - Key generation is fast
- Proof generation: <500ms (SC-002) - Ed25519 signatures are ~100μs
- Proof verification: <200ms (SC-003) - Ed25519 verification is ~50μs
- Scale: 10K aliases per user, 1B+ total aliases (SC-004, SC-012)

## Security Constraints

- Zero exposure of private keys or master seeds (FR-011, SC-010)
- Cryptographic unlinkability between aliases (FR-003, FR-004, FR-007)
- Deterministic key derivation for seed-based aliases (FR-012)
- Proper input validation and error handling (FR-013, FR-014)

