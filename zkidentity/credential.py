"""
Verifiable credential operations.

Provides functionality for creating and presenting W3C Verifiable Credentials
associated with alias identities using zero-knowledge proofs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
import json
import uuid

from zkidentity.exceptions import CredentialError, AliasError
from zkidentity.proof import generate_proof, ZeroKnowledgeProof
from zkidentity.storage import get_default_storage

if TYPE_CHECKING:
    from zkidentity.alias import Alias

try:
    from pyld import jsonld
except ImportError:
    try:
        import pyld
        jsonld = pyld.jsonld if hasattr(pyld, 'jsonld') else None
    except ImportError:
        jsonld = None  # Will raise error if used without pyld


@dataclass
class VerifiableCredential:
    """
    A verifiable credential following W3C Verifiable Credentials Data Model v1.1+.
    
    Associated with an alias identity and can be presented with zero-knowledge proofs.
    """
    credential_id: str
    credential_subject: dict  # The credential claims/attributes
    issuer: str  # Issuer identifier (DID or alias public key)
    alias_public_key: bytes  # 32 bytes, Ed25519 - the alias this credential is associated with
    credential_json: dict  # Full W3C VC JSON structure
    created_at: str  # ISO format timestamp
    expires_at: Optional[str] = None  # ISO format timestamp if applicable
    
    def present(self, proof: ZeroKnowledgeProof) -> "CredentialPresentation":
        """
        Create a credential presentation with a zero-knowledge proof.
        
        Args:
            proof: The zero-knowledge proof of alias ownership
        
        Returns:
            CredentialPresentation object
        
        Raises:
            CredentialError: If proof doesn't match credential's alias
        """
        # Verify proof is for this credential's alias
        if proof.public_key != self.alias_public_key:
            raise CredentialError(
                f"Proof public key does not match credential alias public key"
            )
        
        return CredentialPresentation(
            credential=self,
            proof=proof,
            presented_at=datetime.now().isoformat()
        )
    
    def validate(self) -> bool:
        """
        Validate credential structure and JSON-LD format.
        
        Returns:
            True if credential is valid, False otherwise
        
        Raises:
            CredentialError: If credential structure is invalid
        """
        # Check required fields
        if not self.credential_id:
            raise CredentialError("Credential ID is required")
        
        if not self.credential_subject:
            raise CredentialError("Credential subject is required")
        
        if not self.issuer:
            raise CredentialError("Issuer is required")
        
        if len(self.alias_public_key) != 32:
            raise CredentialError("Alias public key must be 32 bytes")
        
        # Validate W3C VC structure
        if not isinstance(self.credential_json, dict):
            raise CredentialError("Credential JSON must be a dictionary")
        
        # Check for required W3C VC fields
        required_fields = ["@context", "type", "credentialSubject", "issuer"]
        for field in required_fields:
            if field not in self.credential_json:
                raise CredentialError(f"Missing required W3C VC field: {field}")
        
        # Validate @context includes W3C VC context
        contexts = self.credential_json.get("@context", [])
        if isinstance(contexts, str):
            contexts = [contexts]
        
        vc_context = "https://www.w3.org/2018/credentials/v1"
        if vc_context not in contexts:
            raise CredentialError(f"Missing W3C VC context: {vc_context}")
        
        # Validate type includes VerifiableCredential
        types = self.credential_json.get("type", [])
        if isinstance(types, str):
            types = [types]
        
        if "VerifiableCredential" not in types:
            raise CredentialError("Type must include 'VerifiableCredential'")
        
        # If pyld is available, validate JSON-LD
        if jsonld is not None:
            try:
                # Expand JSON-LD to check for errors
                expanded = jsonld.expand(self.credential_json)
                if not expanded:
                    raise CredentialError("JSON-LD expansion failed")
            except Exception as e:
                raise CredentialError(f"JSON-LD validation failed: {e}")
        
        return True


@dataclass
class CredentialPresentation:
    """
    A verifiable credential presented with a zero-knowledge proof.
    
    Enables anonymous credential presentation without revealing identity
    or linking to other aliases.
    """
    credential: VerifiableCredential
    proof: ZeroKnowledgeProof
    presented_at: str  # ISO format timestamp
    
    def verify(self) -> bool:
        """
        Verify the credential presentation.
        
        This verifies:
        1. The credential structure is valid
        2. The proof is valid for the credential's alias public key
        3. The proof matches the credential's alias
        
        Returns:
            True if presentation is valid, False otherwise
        """
        # Validate credential
        try:
            self.credential.validate()
        except CredentialError:
            return False
        
        # Verify proof matches credential's alias
        if self.proof.public_key != self.credential.alias_public_key:
            return False
        
        # Verify the proof itself
        from zkidentity.proof import verify_proof
        return verify_proof(
            self.proof,
            self.credential.alias_public_key,
            self.proof.challenge
        )


def create_credential(
    alias: "Alias",
    credential_data: dict,
    issuer: Optional[str] = None,
    credential_type: Optional[str] = None,
    expires_at: Optional[str] = None
) -> VerifiableCredential:
    """
    Create a W3C Verifiable Credential associated with an alias.
    
    Args:
        alias: The alias to associate the credential with
        credential_data: Credential subject data (claims/attributes)
        issuer: Issuer identifier (defaults to alias public key as hex)
        credential_type: Additional credential type beyond VerifiableCredential
        expires_at: Expiration timestamp (ISO format) if applicable
    
    Returns:
        VerifiableCredential object
    
    Raises:
        AliasError: If alias is revoked or invalid
        ValueError: If credential_data is invalid
        CredentialError: If credential creation fails
    
    Requirements: FR-009
    """
    # Check alias is valid
    if alias.is_revoked:
        raise AliasError(f"Cannot create credential for revoked alias '{alias.alias_id}'")
    
    if not alias.is_valid():
        raise AliasError(f"Alias '{alias.alias_id}' is not valid")
    
    # Validate credential data
    if not isinstance(credential_data, dict):
        raise ValueError("Credential data must be a dictionary")
    
    if not credential_data:
        raise ValueError("Credential data cannot be empty")
    
    # Generate credential ID
    credential_id = f"cred-{uuid.uuid4().hex[:16]}"
    
    # Set issuer (default to alias public key)
    if issuer is None:
        issuer = f"did:zkidentity:{alias.public_key.hex()}"
    
    # Build credential type
    types = ["VerifiableCredential"]
    if credential_type:
        types.append(credential_type)
    
    # Build W3C VC JSON structure
    credential_json = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1"
        ],
        "id": f"urn:zkidentity:credential:{credential_id}",
        "type": types,
        "issuer": issuer,
        "issuanceDate": datetime.now().isoformat() + "Z",
        "credentialSubject": {
            "id": f"did:zkidentity:{alias.public_key.hex()}",
            **credential_data
        }
    }
    
    # Add expiration if provided
    if expires_at:
        credential_json["expirationDate"] = expires_at
    
    # Create credential object
    credential = VerifiableCredential(
        credential_id=credential_id,
        credential_subject=credential_data,
        issuer=issuer,
        alias_public_key=alias.public_key,
        credential_json=credential_json,
        created_at=datetime.now().isoformat(),
        expires_at=expires_at
    )
    
    # Validate credential
    try:
        credential.validate()
    except CredentialError as e:
        raise CredentialError(f"Created credential failed validation: {e}") from e
    
    # Save credential to storage
    storage = get_default_storage()
    storage.save_credential(
        credential_id=credential.credential_id,
        alias_public_key=alias.public_key.hex(),
        credential_json=credential.credential_json,
        created_at=credential.created_at,
        expires_at=credential.expires_at
    )
    
    return credential


def present_credential(
    credential: VerifiableCredential,
    alias: "Alias",
    challenge: bytes
) -> CredentialPresentation:
    """
    Present a verifiable credential with a zero-knowledge proof.
    
    Args:
        credential: The credential to present
        alias: The alias presenting the credential (must match credential's alias)
        challenge: Challenge from verifier
    
    Returns:
        CredentialPresentation object
    
    Raises:
        AliasError: If alias is revoked, invalid, or doesn't match credential
        CredentialError: If credential is invalid or alias mismatch
        ValueError: If challenge is invalid
    
    Requirements: FR-009, FR-010
    """
    # Check alias is valid
    if alias.is_revoked:
        raise AliasError(f"Cannot present credential with revoked alias '{alias.alias_id}'")
    
    if not alias.is_valid():
        raise AliasError(f"Alias '{alias.alias_id}' is not valid")
    
    # Verify alias matches credential
    if alias.public_key != credential.alias_public_key:
        raise AliasError(
            f"Alias public key does not match credential's alias public key"
        )
    
    # Check alias has private key available
    if not alias.private_key:
        raise AliasError(
            f"Alias '{alias.alias_id}' private key is not available. "
            "Cannot generate proof for credential presentation."
        )
    
    # Validate challenge
    if not challenge:
        raise ValueError("Challenge cannot be empty")
    
    # Validate credential
    try:
        credential.validate()
    except CredentialError as e:
        raise CredentialError(f"Credential validation failed: {e}") from e
    
    # Generate zero-knowledge proof
    proof = generate_proof(alias, challenge)
    
    # Create presentation
    presentation = credential.present(proof)
    
    return presentation


def ensure_presentation_unlinkability(
    presentation1: CredentialPresentation,
    presentation2: CredentialPresentation
) -> bool:
    """
    Verify that two credential presentations are unlinkable.
    
    Two presentations from different aliases should not reveal any
    relationship between their aliases or credentials.
    
    Args:
        presentation1: First credential presentation
        presentation2: Second credential presentation
    
    Returns:
        True if presentations are unlinkable, False otherwise
    
    Requirements: FR-010
    """
    # If presentations are for the same alias, they're linkable (expected)
    if presentation1.credential.alias_public_key == presentation2.credential.alias_public_key:
        return False
    
    # For different aliases, presentations should be unlinkable
    # This means:
    # 1. Proofs should be unlinkable (handled by proof system)
    # 2. Credentials should not reveal relationships
    # 3. No correlation between presentations
    
    # Verify proofs are unlinkable
    from zkidentity.proof import ensure_unlinkability
    proofs_unlinkable = ensure_unlinkability(presentation1.proof, presentation2.proof)
    
    # Credentials themselves should not reveal relationships
    # (they're associated with different public keys)
    credentials_unlinkable = (
        presentation1.credential.alias_public_key != presentation2.credential.alias_public_key
    )
    
    return proofs_unlinkable and credentials_unlinkable

