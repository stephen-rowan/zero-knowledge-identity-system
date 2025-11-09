# Authentication Flow: Zero-Knowledge Identity System

**Date**: 2024-12-19  
**Feature**: User Story 3 - Authenticate Using Alias Identity  
**Requirements**: FR-008

## Overview

This document describes the authentication flow for services using alias identities with zero-knowledge proofs. The system enables users to authenticate to services without revealing their private keys or linking to other aliases.

## Authentication Flow

### 1. User Initiates Authentication

The user presents their alias public key to the service. The public key serves as the user's identity identifier.

```python
from zkidentity import get_alias

alias = get_alias("my-identity")
public_key = alias.public_key.hex()  # Present to service
```

### 2. Service Generates Challenge

The service generates a unique, random challenge (nonce) for this authentication session. This prevents replay attacks and ensures proof freshness.

```python
from zkidentity.proof import generate_challenge

challenge = generate_challenge()  # Service generates this
# Send challenge to user
```

**Best Practices**:
- Use cryptographically secure random generation
- Include timestamp or session identifier in challenge
- Store challenge temporarily to verify later
- Reject reused challenges

### 3. User Generates Zero-Knowledge Proof

The user generates a zero-knowledge proof (Schnorr signature) using their alias's private key and the service's challenge.

```python
from zkidentity import generate_proof

proof = generate_proof(alias, challenge)
# Send proof to service
```

**Security Guarantees**:
- Private key is never revealed
- Proof is cryptographically unlinkable to other aliases
- Proof is specific to this challenge (cannot be reused)

### 4. Service Verifies Proof

The service verifies the proof against the user's public key and the challenge.

```python
from zkidentity import verify_proof

is_valid = verify_proof(
    proof=proof,
    public_key=bytes.fromhex(public_key),
    challenge=challenge
)

if is_valid:
    # Authentication successful
    grant_access()
else:
    # Authentication failed
    reject_access()
```

### 5. Service Grants Access

If verification succeeds, the service grants access to the user. The service should:

- **Not store** the private key or any key material
- **Optionally store** the public key for future authentication
- **Maintain session state** if needed (but be aware of metadata linkage)
- **Respect revocation** - check if alias is revoked before granting access

## Complete Example

### User Side (Client)

```python
from zkidentity import get_alias, generate_proof

# 1. Get alias
alias = get_alias("work-identity")

# 2. Present public key to service
public_key_hex = alias.public_key.hex()
# Send public_key_hex to service

# 3. Receive challenge from service
challenge_bytes = bytes.fromhex(service_challenge_hex)

# 4. Generate proof
proof = generate_proof(alias, challenge_bytes)

# 5. Send proof to service
proof_data = {
    "proof_bytes": proof.proof_bytes.hex(),
    "public_key": proof.public_key.hex(),
    "challenge": proof.challenge.hex(),
    "created_at": proof.created_at
}
# Send proof_data to service
```

### Service Side (Server)

```python
from zkidentity.proof import generate_challenge, verify_proof
from zkidentity import ZeroKnowledgeProof
from datetime import datetime

# 1. Receive public key from user
user_public_key_hex = request.json["public_key"]
user_public_key = bytes.fromhex(user_public_key_hex)

# 2. Generate challenge
challenge = generate_challenge()
challenge_hex = challenge.hex()
# Send challenge_hex to user

# 3. Store challenge temporarily (with expiration)
challenge_store[challenge_hex] = {
    "public_key": user_public_key_hex,
    "created_at": datetime.now(),
    "expires_at": datetime.now() + timedelta(minutes=5)
}

# 4. Receive proof from user
proof_data = request.json["proof"]
proof = ZeroKnowledgeProof(
    proof_bytes=bytes.fromhex(proof_data["proof_bytes"]),
    challenge=bytes.fromhex(proof_data["challenge"]),
    public_key=bytes.fromhex(proof_data["public_key"]),
    created_at=proof_data["created_at"]
)

# 5. Verify challenge matches
stored_challenge = challenge_store.get(proof_data["challenge"].hex())
if not stored_challenge:
    return {"error": "Invalid or expired challenge"}, 401

if stored_challenge["public_key"] != proof_data["public_key"]:
    return {"error": "Public key mismatch"}, 401

# 6. Verify proof
is_valid = verify_proof(
    proof=proof,
    public_key=user_public_key,
    challenge=challenge
)

if is_valid:
    # 7. Grant access
    del challenge_store[proof_data["challenge"].hex()]  # Clean up
    return {"status": "authenticated", "public_key": user_public_key_hex}, 200
else:
    return {"error": "Invalid proof"}, 401
```

## Session Unlinkability

**Requirement**: FR-008, User Story 3 Acceptance Scenario 2

Each authentication session should appear as a new, unlinkable session. To achieve this:

1. **Use fresh challenges**: Each authentication should use a unique challenge
2. **Don't link sessions**: Avoid storing session identifiers that link multiple authentications
3. **Metadata hygiene**: Be careful with timestamps, IP addresses, and other metadata that could link sessions
4. **Separate public keys**: If a user authenticates with multiple aliases, treat them as separate identities

### Best Practices for Services

- **Challenge expiration**: Challenges should expire after a short time (e.g., 5 minutes)
- **One-time use**: Each challenge should be used only once
- **No session linking**: Don't create session identifiers that link multiple authentications from the same user
- **Metadata minimization**: Collect only necessary metadata, avoid storing IP addresses or other linking data

## Error Handling

### Invalid Proof

```python
try:
    is_valid = verify_proof(proof, public_key, challenge)
except ProofError as e:
    # Proof format is invalid
    return {"error": "Invalid proof format"}, 400
except ValueError as e:
    # Input validation failed
    return {"error": "Invalid input"}, 400
```

### Revoked Alias

```python
from zkidentity import get_alias

alias = get_alias(alias_id)
if alias.is_revoked:
    return {"error": "Alias is revoked"}, 403
```

### Expired Challenge

```python
if challenge_expired(challenge):
    return {"error": "Challenge expired"}, 401
```

## Security Considerations

1. **Never expose private keys**: Private keys are never sent to the service
2. **Challenge freshness**: Always use fresh, random challenges
3. **Proof validation**: Always validate proof format before verification
4. **Revocation checking**: Check if alias is revoked before granting access
5. **Metadata hygiene**: Minimize metadata collection to prevent operational linkage

## Metadata Hygiene for Authentication

**Requirement**: FR-015, User Story 3

Metadata hygiene is critical for maintaining privacy and preventing operational linkage between authentication sessions. While the cryptographic system ensures proofs are unlinkable, operational metadata can still create linkage.

### What is Metadata?

Metadata includes any information about an authentication session that is not part of the cryptographic proof itself:

- **Timestamps**: When the authentication occurred
- **IP addresses**: Network location of the user
- **User agents**: Browser or client information
- **Session identifiers**: Service-created session tokens
- **Request patterns**: Frequency, timing, or sequence of authentications
- **Device fingerprints**: Hardware or software characteristics

### Metadata Hygiene Best Practices

#### For Services (Verifiers)

1. **Minimize Collection**
   - Only collect metadata necessary for your service operation
   - Avoid collecting IP addresses unless required for security
   - Don't store detailed request headers or user agents

2. **Separate Storage**
   - Store authentication records separately from user profiles
   - Don't create database relationships that link multiple authentications
   - Use separate tables or databases for authentication logs

3. **Avoid Linkage Patterns**
   - Don't create session identifiers that persist across authentications
   - Avoid storing authentication history that could reveal patterns
   - Don't correlate authentications based on timing or frequency

4. **Time-based Anonymization**
   - Round timestamps to reduce precision (e.g., round to nearest minute)
   - Don't store exact timestamps if approximate times are sufficient
   - Consider time-based data retention policies

5. **Network Privacy**
   - Don't log IP addresses unless necessary for security
   - Use IP address anonymization if logging is required
   - Consider using VPN-friendly architectures

#### For Users (Provers)

1. **Use Different Aliases**
   - Use separate aliases for different services
   - Don't reuse the same alias across multiple services
   - Create service-specific aliases when possible

2. **Vary Timing**
   - Avoid predictable authentication patterns
   - Don't authenticate at the same time every day
   - Vary the timing of authentications

3. **Network Privacy**
   - Use VPNs or Tor when possible
   - Be aware that IP addresses can create linkage
   - Consider using different networks for different aliases

4. **Client Diversity**
   - Use different devices or browsers for different aliases
   - Avoid using the same user agent across aliases
   - Consider using privacy-focused browsers

### Operational Linkage Risks

Even with perfect cryptographic unlinkability, operational metadata can create linkage:

1. **Timing Correlation**: Multiple authentications at the same time
2. **IP Address Matching**: Same IP address across authentications
3. **Pattern Recognition**: Similar authentication patterns or frequencies
4. **Session Tracking**: Service-created session identifiers
5. **Device Fingerprinting**: Hardware or software characteristics

### Mitigation Strategies

1. **Cryptographic Unlinkability**: The system provides cryptographic guarantees (FR-007)
2. **Metadata Minimization**: Collect only necessary metadata
3. **Separate Storage**: Don't create linkage in data storage
4. **Time Randomization**: Vary authentication timing
5. **Network Privacy**: Use VPNs, Tor, or different networks
6. **Alias Separation**: Use different aliases for different purposes

### Example: Good vs. Bad Metadata Practices

**❌ Bad Practice**:
```python
# Storing detailed metadata that creates linkage
auth_record = {
    "public_key": proof.public_key.hex(),
    "ip_address": request.remote_addr,  # Creates linkage
    "user_agent": request.headers["User-Agent"],  # Creates linkage
    "timestamp": datetime.now(),  # Exact timestamp
    "session_id": session.id,  # Links to other authentications
    "previous_auth_time": last_auth_time  # Creates pattern
}
```

**✅ Good Practice**:
```python
# Minimal metadata, no linkage
auth_record = {
    "public_key": proof.public_key.hex(),
    "authenticated": True,
    "timestamp_rounded": round_to_minute(datetime.now())  # Reduced precision
    # No IP address, user agent, or session linking
}
```

### Compliance and Privacy

- **GDPR**: Minimize personal data collection
- **Privacy by Design**: Build privacy into authentication flows
- **Data Minimization**: Collect only what's necessary
- **Purpose Limitation**: Use authentication data only for authentication

### Tools and Resources

- Use privacy-focused authentication libraries
- Implement metadata anonymization tools
- Use time-based data retention policies
- Consider privacy-preserving authentication protocols

## Integration with Existing Systems

### REST API Integration

```python
# POST /auth/initiate
# Request: {"public_key": "hex_string"}
# Response: {"challenge": "hex_string"}

# POST /auth/authenticate
# Request: {"proof": {...proof_data...}}
# Response: {"status": "authenticated", "token": "session_token"}
```

### WebSocket Integration

```python
# Client sends: {"type": "auth_init", "public_key": "hex_string"}
# Server sends: {"type": "challenge", "challenge": "hex_string"}
# Client sends: {"type": "proof", "proof": {...proof_data...}}
# Server sends: {"type": "authenticated", "session_id": "..."}
```

## Performance Requirements

- Challenge generation: <10ms (SC-002)
- Proof generation: <500ms (SC-002)
- Proof verification: <200ms (SC-003)
- Authentication success rate: 99.9% (SC-008)

## References

- **Functional Requirements**: FR-008 (Authentication flows)
- **User Story**: User Story 3 - Authenticate Using Alias Identity
- **Success Criteria**: SC-002, SC-003, SC-008
- **Related Documentation**: [API Contracts](./api.md), [Quickstart Guide](../specs/001-zk-identity-system/quickstart.md)

