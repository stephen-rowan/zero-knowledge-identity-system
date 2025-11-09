# Research: Zero-Knowledge Identity System

**Date**: 2024-12-19  
**Feature**: Zero-Knowledge Identity System  
**Purpose**: Resolve technical unknowns identified in Technical Context

## Research Questions

### 1. Primary Dependencies - Cryptographic Libraries

**Question**: Which Python libraries provide HMAC-SHA256, Schnorr signatures, and Fiat-Shamir transformation?

**Decision**: 
- **`cryptography`** (PyCA) - Standard library for HMAC-SHA256 and general cryptographic primitives
- **`secp256k1`** (python-secp256k1) or **`ecdsa`** with secp256k1 curve - For Schnorr signatures on secp256k1
- **`pynacl`** (PyNaCl) - Alternative for Ed25519-based Schnorr signatures (simpler, modern)
- Custom Fiat-Shamir implementation or use library-provided challenge generation

**Rationale**: 
- `cryptography` is the de facto standard Python crypto library, well-maintained and secure
- Schnorr signatures: secp256k1 is Bitcoin-standard but complex; Ed25519 (via PyNaCl) is simpler and widely supported
- For zero-knowledge identity, Ed25519 with PyNaCl provides good performance and security
- Fiat-Shamir can be implemented using HMAC-SHA256 from `cryptography` library

**Alternatives Considered**:
- `pycryptodome` - More comprehensive but heavier; `cryptography` is preferred for production
- Pure Python implementations - Too slow for production use
- `libsecp256k1` bindings - More complex setup, better for Bitcoin-specific use cases

**Recommendation**: Use `cryptography` for HMAC-SHA256, `pynacl` for Ed25519-based Schnorr signatures (simpler than secp256k1), implement Fiat-Shamir using HMAC-SHA256.

---

### 2. W3C Verifiable Credentials Library

**Question**: Which Python library supports W3C Verifiable Credentials Data Model v1.1+?

**Decision**: 
- **`vc-issuer`** or **`pyld`** (JSON-LD processor) + custom VC implementation
- **`didkit`** Python bindings (if available) or **`vc-js`** port
- Custom implementation using `pyld` for JSON-LD processing

**Rationale**: 
- W3C VC support in Python is less mature than JavaScript
- `pyld` provides JSON-LD processing required for W3C VC
- May need custom implementation wrapping `pyld` for VC-specific operations
- Consider interoperability with existing VC ecosystems

**Alternatives Considered**:
- Full JavaScript stack with `vc-js` - Better library support but adds complexity
- Wait for mature Python VC library - Not viable for current project
- Minimal VC support - Acceptable for MVP, can enhance later

**Recommendation**: Use `pyld` for JSON-LD processing, implement custom W3C VC wrapper. For MVP, focus on core VC structure; full JSON-LD proof verification can be enhanced later.

---

### 3. Storage Requirements

**Question**: What storage is needed for alias metadata, revocation status, and credentials (given keys/seeds are user-managed)?

**Decision**: 
- **Option A**: In-memory only (stateless library) - No persistence, user manages all state
- **Option B**: Optional file-based storage (JSON/YAML) - User-controlled, simple
- **Option C**: Database integration (SQLite/PostgreSQL) - For production services

**Rationale**: 
- System does NOT store keys/seeds (FR-019) - user responsibility
- Need to track: alias identifiers, public keys, revocation status, associated credentials
- For library/CLI: File-based storage (JSON) is simplest and user-controlled
- For service: Database needed for scale (1B+ aliases)

**Alternatives Considered**:
- No storage - Too limiting, can't track revocation or credentials
- Cloud storage - Adds complexity and potential privacy concerns
- Encrypted local storage - Good for security but adds key management complexity

**Recommendation**: 
- **Library/CLI**: File-based JSON storage (user-controlled, simple)
- **Service**: SQLite for small deployments, PostgreSQL for scale
- Make storage pluggable/optional to support different use cases

---

### 4. Testing Framework

**Question**: Which testing framework for Python?

**Decision**: **`pytest`** - Standard Python testing framework

**Rationale**: 
- Industry standard for Python projects
- Excellent fixtures, parametrization, and plugin ecosystem
- Good integration with coverage tools
- Supports property-based testing (via `hypothesis`) for cryptographic correctness

**Alternatives Considered**:
- `unittest` - Standard library but less feature-rich
- `nose2` - Less popular, maintenance concerns

**Recommendation**: Use `pytest` with `hypothesis` for property-based testing of cryptographic operations.

---

### 5. Target Platform & Project Type

**Question**: Server-side library, CLI tool, or web service?

**Decision**: **Primary: Library with CLI interface** (can be used by services)

**Rationale**: 
- Core functionality (crypto operations) should be library-based for reusability
- CLI provides user-friendly interface for key/alias management
- Library can be imported by web services or other applications
- Matches "system provides tools" philosophy from spec

**Alternatives Considered**:
- Web service only - Too limiting, can't be used as library
- Library only - Less user-friendly for non-developers
- CLI only - Can't be integrated into other systems

**Recommendation**: 
- **Core**: Python library (`zkidentity` package)
- **CLI**: Command-line interface using `click` or `argparse`
- **Future**: Web service can be built on top of library if needed

---

## Additional Research Findings

### Performance Considerations

- Ed25519 signatures are fast (~100μs) - meets <500ms proof generation target easily
- HMAC-SHA256 is very fast - meets <1s alias creation target
- Verification is even faster - meets <200ms target
- For 1B+ aliases: Need efficient indexing (hash-based or B-tree)
- For 10K concurrent ops: Async I/O recommended (asyncio)

### Security Best Practices

- Never log or expose private keys or seeds (FR-011, SC-010)
- Use secure random number generation (`secrets` module for Python)
- Validate all inputs (alias identifiers, challenge messages)
- Use constant-time operations for cryptographic code
- Implement proper error handling that doesn't leak information

### Scalability Architecture

- Library design: Stateless operations, state managed externally
- For services: Horizontal scaling with load balancers
- Database: Partition aliases by user_id or use sharding
- Caching: Cache public keys and revocation status (Redis/Memcached)
- Async operations: Use asyncio for concurrent proof generation/verification

---

## Summary of Decisions

| Area | Decision | Library/Tool |
|------|----------|--------------|
| HMAC-SHA256 | `cryptography` (PyCA) | `cryptography` |
| Schnorr Signatures | Ed25519 via PyNaCl | `pynacl` |
| Fiat-Shamir | Custom using HMAC-SHA256 | `cryptography` |
| W3C VC | Custom wrapper over JSON-LD | `pyld` |
| Storage | File-based (JSON) or Database | JSON/SQLite/PostgreSQL |
| Testing | pytest | `pytest`, `hypothesis` |
| Project Type | Library + CLI | `click` for CLI |
| Platform | Python 3.11+ | Standard library + dependencies |

## Next Steps

1. Set up project structure (library + CLI)
2. Implement core cryptographic operations (key derivation, signatures)
3. Design data models for aliases, proofs, credentials
4. Create API contracts for library interface
5. Implement storage abstraction (file-based first, database later)

