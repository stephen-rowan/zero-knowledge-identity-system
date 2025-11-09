"""
Exception classes for zkidentity library.
"""


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

