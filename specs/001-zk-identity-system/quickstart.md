# Quickstart Guide: Zero-Knowledge Identity System

**Date**: 2024-12-19  
**Feature**: Zero-Knowledge Identity System

## Installation

```bash
# Install dependencies
pip install cryptography pynacl pyld click

# Install zkidentity library (once published)
pip install zkidentity
```

## Basic Usage

### 1. Create an Independent Alias

Create an alias with a randomly generated key pair:

```python
from zkidentity import create_independent_alias

# Create a new alias
alias = create_independent_alias("my-identity")

# Get the public key (safe to share)
print(f"Public key: {alias.public_key.hex()}")

# Private key is managed internally, never exposed
```

### 2. Create Aliases from Master Seed

Derive multiple aliases from a single master seed:

```python
from zkidentity import generate_master_seed, derive_alias_from_seed

# Generate a master seed (save this securely!)
seed = generate_master_seed()
print(f"Master seed (hex): {seed.hex()}")
# IMPORTANT: Store this seed securely - losing it means losing access to all derived aliases

# Derive multiple aliases from the same seed
work_alias = derive_alias_from_seed(seed, "work-identity")
personal_alias = derive_alias_from_seed(seed, "personal-identity")
shopping_alias = derive_alias_from_seed(seed, "shopping-identity")

# Each alias has a unique, unlinkable public key
print(f"Work public key: {work_alias.public_key.hex()}")
print(f"Personal public key: {personal_alias.public_key.hex()}")
# These public keys appear random and cannot be linked to each other
```

### 3. Generate Zero-Knowledge Proofs

Prove ownership of an alias without revealing the private key:

```python
from zkidentity import generate_proof, verify_proof
import secrets

# Verifier provides a challenge (nonce)
challenge = secrets.token_bytes(32)

# Generate proof of alias ownership
proof = generate_proof(alias, challenge)

# Verifier can verify the proof
is_valid = verify_proof(proof, alias.public_key, challenge)
assert is_valid == True

# Proof does not reveal private key or link to other aliases
```

### 4. Authenticate with an Alias

Authenticate to a service using your alias:

```python
# Service provides a challenge
service_challenge = b"authenticate-to-service-12345"

# Generate proof
proof = generate_proof(alias, service_challenge)

# Send to service: (alias.public_key, proof, service_challenge)
# Service verifies:
is_authenticated = verify_proof(proof, alias.public_key, service_challenge)
if is_authenticated:
    print("Authentication successful!")
```

### 5. Work with Verifiable Credentials

Create and present verifiable credentials:

```python
from zkidentity import create_credential, present_credential

# Create a credential associated with an alias
credential_data = {
    "degree": "Bachelor of Science",
    "university": "Example University",
    "year": 2020
}
credential = create_credential(alias, credential_data)

# Present credential with proof
verifier_challenge = secrets.token_bytes(32)
presentation = present_credential(credential, alias, verifier_challenge)

# Verifier can validate credential and proof without learning private key
```

### 6. Manage Aliases

Revoke or manage aliases:

```python
from zkidentity import revoke_alias, save_aliases, load_aliases

# Revoke an alias (prevents future use, but past proofs remain valid)
revoke_alias(alias)
assert alias.is_revoked == True

# Save alias metadata (public keys only, no private keys)
aliases = [alias1, alias2, alias3]
save_aliases(aliases, "~/.zkidentity/aliases.json")

# Load aliases (private keys must be derived from seed if seed-derived)
aliases = load_aliases("~/.zkidentity/aliases.json")
```

### 7. Backup and Restore Master Seed

Securely backup and restore your master seed:

```python
from zkidentity import export_seed_backup, import_seed_backup

# Export seed in encrypted format
backup = export_seed_backup(seed, "my-secure-password")
print(f"Backup: {backup}")
# Store this backup securely (e.g., password manager, encrypted file)

# Restore seed from backup
restored_seed = import_seed_backup(backup, "my-secure-password")
assert restored_seed == seed

# You can now derive the same aliases
restored_alias = derive_alias_from_seed(restored_seed, "work-identity")
assert restored_alias.public_key == work_alias.public_key
```

## CLI Usage

The library also provides a command-line interface:

```bash
# Generate a master seed
zkidentity seed generate

# Derive an alias from seed
zkidentity alias derive --seed <seed-hex> --id "work-identity"

# Create an independent alias
zkidentity alias create --id "personal-identity"

# Generate a proof
zkidentity proof generate --alias-id "work-identity" --challenge <challenge-hex>

# Verify a proof
zkidentity proof verify --proof <proof-hex> --public-key <pubkey-hex> --challenge <challenge-hex>

# Revoke an alias
zkidentity alias revoke --alias-id "work-identity"

# Export seed backup
zkidentity seed export --seed <seed-hex> --password <password>

# Import seed backup
zkidentity seed import --backup <backup-string> --password <password>
```

## Security Best Practices

1. **Master Seed Storage**: Store your master seed securely (password manager, hardware wallet, encrypted file). Losing the seed means losing access to all derived aliases.

2. **Private Key Management**: The library never stores private keys. You must derive them from your master seed when needed.

3. **Backup**: Always backup your master seed using the export functionality.

4. **Challenge Messages**: Always use unique, random challenges for each proof to prevent replay attacks.

5. **Revocation**: If an alias is compromised, revoke it immediately. Past proofs remain valid, but future use is prevented.

6. **Metadata Hygiene**: Be careful about metadata (timestamps, IP addresses, etc.) that could link aliases operationally.

## Example: Complete Workflow

```python
from zkidentity import (
    generate_master_seed,
    derive_alias_from_seed,
    generate_proof,
    verify_proof,
    create_credential,
    present_credential,
    export_seed_backup
)
import secrets

# 1. Generate and backup master seed
seed = generate_master_seed()
backup = export_seed_backup(seed, "secure-password")
# Save backup securely!

# 2. Create multiple aliases
work = derive_alias_from_seed(seed, "work")
personal = derive_alias_from_seed(seed, "personal")

# 3. Authenticate with work alias
challenge = secrets.token_bytes(32)
proof = generate_proof(work, challenge)
assert verify_proof(proof, work.public_key, challenge)

# 4. Present credential with personal alias
credential = create_credential(personal, {"age": "25+"})
presentation = present_credential(credential, personal, challenge)

# 5. Revoke an alias if compromised
from zkidentity import revoke_alias
revoke_alias(work)
# work alias can no longer generate proofs, but past proofs remain valid
```

## Troubleshooting

### "Alias identifier already exists"
- Alias identifiers must be unique per master seed (seed-derived) or per user (independent)
- Choose a different identifier or revoke the existing alias first

### "Alias is revoked"
- The alias has been revoked and cannot be used for new operations
- Past proofs remain valid, but new proofs cannot be generated

### "Invalid proof"
- Ensure the challenge matches the one used to generate the proof
- Verify the public key matches the alias that generated the proof
- Check that the proof format is correct

### "Master seed lost"
- If you lose your master seed and don't have a backup, you cannot recover seed-derived aliases
- Independent aliases are not affected (they don't use a seed)
- Always backup your master seed!

## Next Steps

- Read the [API Documentation](./contracts/api.md)
- Review the [Data Model](./data-model.md) for detailed entity definitions
- Check the [Implementation Plan](./plan.md) for architecture details

