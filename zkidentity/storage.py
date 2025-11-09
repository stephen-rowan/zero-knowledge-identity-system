"""
File-based storage for alias metadata.

Stores only public keys and metadata - never private keys or seeds.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from zkidentity.exceptions import AliasError


class AliasStorage:
    """
    File-based storage for alias metadata.
    
    Stores only public information: alias_id, public_key, is_revoked, timestamps.
    Never stores private keys or master seeds.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize storage.
        
        Args:
            storage_path: Path to storage file (default: ~/.zkidentity/aliases.json)
        """
        if storage_path is None:
            home = Path.home()
            storage_dir = home / ".zkidentity"
            storage_dir.mkdir(exist_ok=True)
            storage_path = str(storage_dir / "aliases.json")
        
        self.storage_path = Path(storage_path)
        self._aliases: Dict[str, Dict] = {}
        self._load()
    
    def _load(self) -> None:
        """Load aliases from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._aliases = data.get('aliases', {})
            except (json.JSONDecodeError, IOError) as e:
                raise AliasError(f"Failed to load storage: {e}")
        else:
            self._aliases = {}
    
    def _save(self) -> None:
        """Save aliases to storage file."""
        try:
            data = {
                'version': '1.0',
                'aliases': self._aliases
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            raise AliasError(f"Failed to save storage: {e}")
    
    def save_alias(self, alias_id: str, public_key: str, is_revoked: bool = False,
                   created_at: Optional[str] = None, revoked_at: Optional[str] = None,
                   master_seed_id: Optional[str] = None) -> None:
        """
        Save alias metadata (public key only, never private key).
        
        Args:
            alias_id: Alias identifier
            public_key: Public key as hex string
            is_revoked: Whether alias is revoked
            created_at: Creation timestamp (ISO format)
            revoked_at: Revocation timestamp (ISO format) if revoked
            master_seed_id: Reference to master seed if seed-derived
        """
        if created_at is None:
            created_at = datetime.now().isoformat()
        
        self._aliases[alias_id] = {
            'alias_id': alias_id,
            'public_key': public_key,
            'is_revoked': is_revoked,
            'created_at': created_at,
            'revoked_at': revoked_at,
            'master_seed_id': master_seed_id
        }
        self._save()
    
    def load_alias(self, alias_id: str) -> Optional[Dict]:
        """
        Load alias metadata by ID.
        
        Args:
            alias_id: Alias identifier
        
        Returns:
            Alias metadata dict or None if not found
        """
        return self._aliases.get(alias_id)
    
    def list_aliases(self) -> List[Dict]:
        """
        List all aliases.
        
        Returns:
            List of alias metadata dicts
        """
        return list(self._aliases.values())
    
    def update_alias(self, alias_id: str, **updates) -> None:
        """
        Update alias metadata.
        
        Args:
            alias_id: Alias identifier
            **updates: Fields to update
        """
        if alias_id not in self._aliases:
            raise AliasError(f"Alias '{alias_id}' not found")
        
        self._aliases[alias_id].update(updates)
        self._save()
    
    def delete_alias(self, alias_id: str) -> None:
        """
        Delete alias from storage.
        
        Args:
            alias_id: Alias identifier
        """
        if alias_id in self._aliases:
            del self._aliases[alias_id]
            self._save()


# Global storage instance
_default_storage: Optional[AliasStorage] = None


def get_default_storage() -> AliasStorage:
    """Get the default storage instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = AliasStorage()
    return _default_storage

