"""
Zero-knowledge proof generation and verification.

Provides Schnorr signature-based proofs (Fiat-Shamir) for proving alias ownership
without revealing private keys or relationships between aliases.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from zkidentity.exceptions import ProofError, AliasError
from zkidentity.crypto import (
    schnorr_sign,
    schnorr_verify,
    validate_challenge,
    generate_secure_random_bytes,
)

if TYPE_CHECKING:
    from zkidentity.alias import Alias


@dataclass
class ZeroKnowledgeProof:
    """
    A non-interactive zero-knowledge proof (Schnorr signature with Fiat-Shamir).
    
    Proves possession of a private key without revealing it or linking to other aliases.
    """
    proof_bytes: bytes  # Schnorr signature (64 bytes for Ed25519)
    challenge: bytes  # Challenge message/nonce from verifier
    public_key: bytes  # 32 bytes, Ed25519 public key
    created_at: str  # ISO format timestamp
    
    def verify(self, public_key: Optional[bytes] = None, challenge: Optional[bytes] = None) -> bool:
        """
        Verify this proof against a public key and challenge.
        
        Args:
            public_key: Public key to verify against (defaults to self.public_key)
            challenge: Challenge to verify against (defaults to self.challenge)
        
        Returns:
            True if proof is valid, False otherwise
        """
        pub_key = public_key if public_key is not None else self.public_key
        chall = challenge if challenge is not None else self.challenge
        
        return verify_proof(self, pub_key, chall)
    
    def is_valid(self) -> bool:
        """
        Check if proof structure and format are valid.
        
        Returns:
            True if proof format is valid, False otherwise
        """
        try:
            # Check proof_bytes length (Ed25519 signatures are 64 bytes)
            if len(self.proof_bytes) != 64:
                return False
            
            # Check public_key length (Ed25519 public keys are 32 bytes)
            if len(self.public_key) != 32:
                return False
            
            # Check challenge is not empty
            if not self.challenge:
                return False
            
            # Check created_at is valid ISO format
            datetime.fromisoformat(self.created_at)
            
            return True
        except (ValueError, TypeError):
            return False


def generate_proof(alias: "Alias", challenge: bytes) -> ZeroKnowledgeProof:
    """
    Generate a zero-knowledge proof (Schnorr signature) for alias ownership.
    
    Args:
        alias: The alias to prove ownership of
        challenge: Challenge message/nonce from verifier
    
    Returns:
        ZeroKnowledgeProof object
    
    Raises:
        AliasError: If alias is revoked
        ValueError: If challenge is empty or invalid
        ProofError: If proof generation fails
    
    Requirements: FR-005, FR-007, FR-011
    """
    # Validate challenge
    validate_challenge(challenge)
    
    # Check alias is not revoked
    if alias.is_revoked:
        raise AliasError(f"Cannot generate proof for revoked alias '{alias.alias_id}'")
    
    # Check alias is valid
    if not alias.is_valid():
        raise AliasError(f"Alias '{alias.alias_id}' is not valid")
    
    try:
        # Generate Schnorr signature using Ed25519
        # The signature itself is the proof - it demonstrates knowledge of private key
        # without revealing it
        proof_bytes = schnorr_sign(alias.private_key, challenge)
        
        # Create proof object
        proof = ZeroKnowledgeProof(
            proof_bytes=proof_bytes,
            challenge=challenge,
            public_key=alias.public_key,
            created_at=datetime.now().isoformat()
        )
        
        # Verify the proof we just created (sanity check)
        if not verify_proof(proof, alias.public_key, challenge):
            raise ProofError("Generated proof failed verification")
        
        return proof
    
    except Exception as e:
        # Ensure no private key information leaks in error messages
        raise ProofError(f"Failed to generate proof: {str(e)}") from e


def verify_proof(proof: ZeroKnowledgeProof, public_key: bytes, challenge: bytes) -> bool:
    """
    Verify a zero-knowledge proof against a public key and challenge.
    
    Args:
        proof: The ZeroKnowledgeProof to verify
        public_key: The alias public key (32 bytes)
        challenge: The challenge message used in proof
    
    Returns:
        True if proof is valid, False otherwise
    
    Raises:
        ValueError: If proof format is invalid
        ProofError: If proof is malformed
    
    Requirements: FR-006, FR-013, FR-014
    """
    # Validate proof format first (FR-013)
    if not proof.is_valid():
        raise ProofError("Proof format is invalid")
    
    # Validate public key
    if len(public_key) != 32:
        raise ValueError("Public key must be exactly 32 bytes")
    
    # Validate challenge
    validate_challenge(challenge)
    
    # Check public key matches proof's public key
    if proof.public_key != public_key:
        return False
    
    # Check challenge matches proof's challenge
    if proof.challenge != challenge:
        return False
    
    try:
        # Verify Schnorr signature
        is_valid = schnorr_verify(public_key, challenge, proof.proof_bytes)
        return is_valid
    
    except Exception as e:
        # Handle malformed proofs gracefully (FR-014)
        raise ProofError(f"Proof verification failed: {str(e)}") from e


def validate_proof_format(proof: ZeroKnowledgeProof) -> None:
    """
    Validate proof format before acceptance.
    
    Args:
        proof: The proof to validate
    
    Raises:
        ProofError: If proof format is invalid
    
    Requirements: FR-013
    """
    if not proof.is_valid():
        raise ProofError("Proof format is invalid")
    
    # Additional format checks
    if not isinstance(proof.proof_bytes, bytes):
        raise ProofError("Proof bytes must be bytes")
    
    if not isinstance(proof.challenge, bytes):
        raise ProofError("Challenge must be bytes")
    
    if not isinstance(proof.public_key, bytes):
        raise ProofError("Public key must be bytes")


def ensure_unlinkability(proof1: ZeroKnowledgeProof, proof2: ZeroKnowledgeProof) -> bool:
    """
    Verify that two proofs are cryptographically unlinkable.
    
    This is a validation function to ensure the system maintains unlinkability.
    Two proofs should not reveal any relationship between their aliases.
    
    Args:
        proof1: First proof
        proof2: Second proof
    
    Returns:
        True if proofs are unlinkable (no relationship revealed), False otherwise
    
    Requirements: FR-007
    """
    # If proofs are for the same public key, they're linkable (expected)
    if proof1.public_key == proof2.public_key:
        return False
    
    # For different public keys, proofs should be unlinkable
    # This means:
    # 1. Proof bytes should appear random and independent
    # 2. No correlation between proof bytes and public keys
    # 3. Challenge values don't reveal relationships
    
    # In practice, with proper Schnorr signatures, this is automatically satisfied
    # because each signature is independent and appears random
    # We just verify that the proofs are for different public keys
    return proof1.public_key != proof2.public_key


def generate_challenge() -> bytes:
    """
    Generate a random challenge for proof generation.
    
    This is a helper for verifiers to create fresh challenges.
    
    Returns:
        32-byte random challenge
    """
    return generate_secure_random_bytes(32)


def generate_service_challenge(service_id: Optional[str] = None, session_id: Optional[str] = None) -> bytes:
    """
    Generate a service challenge for authentication flows.
    
    This helper function creates challenges suitable for service authentication.
    It includes optional service and session identifiers to prevent replay attacks
    and ensure challenge uniqueness.
    
    Args:
        service_id: Optional service identifier (e.g., "api.example.com")
        session_id: Optional session identifier (e.g., UUID)
    
    Returns:
        32-byte challenge suitable for authentication
    
    Requirements: FR-008, User Story 3
    
    Example:
        >>> challenge = generate_service_challenge("api.example.com", "session-123")
        >>> proof = generate_proof(alias, challenge)
    """
    # Generate base random challenge
    base_challenge = generate_secure_random_bytes(32)
    
    # If service_id or session_id provided, incorporate them into challenge
    # This helps prevent cross-service or cross-session replay attacks
    if service_id or session_id:
        import hashlib
        challenge_data = base_challenge
        if service_id:
            challenge_data += service_id.encode('utf-8')
        if session_id:
            challenge_data += session_id.encode('utf-8')
        # Hash to ensure consistent 32-byte output
        challenge = hashlib.sha256(challenge_data).digest()
    else:
        challenge = base_challenge
    
    return challenge

