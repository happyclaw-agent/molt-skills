"""
Solana Keypair Manager for TrustyClaw

Secure keypair loading and management for Solana transactions.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from pathlib import Path
import os
import base64
import json
import hashlib

from solders.keypair import Keypair
from solders.pubkey import Pubkey


class KeypairError(Exception):
    """Keypair operation error"""
    pass


@dataclass
class WalletInfo:
    """Wallet information for display"""
    address: str
    name: str
    network: str
    
    @property
    def short_address(self) -> str:
        """Shortened address for display"""
        return f"{self.address[:8]}...{self.address[-8:]}"


class KeypairManager:
    """
    Secure keypair manager for Solana operations.
    
    Handles loading, validation, and secure storage of keypairs
    for transaction signing.
    """
    
    DEFAULT_KEY_DIR = "~/.config/solana"
    
    def __init__(
        self,
        key_dir: Optional[str] = None,
        master_password: Optional[str] = None,
    ):
        self._keypairs: Dict[str, Keypair] = {}
        self._wallet_info: Dict[str, WalletInfo] = {}
        
        # Resolve key directory
        if key_dir:
            self._key_dir = Path(key_dir)
        else:
            self._key_dir = Path(os.path.expanduser(self.DEFAULT_KEY_DIR))
        
        self._master_password = master_password
        
        # Auto-load default keypair if env var set
        self._auto_load_default()
    
    def _auto_load_default(self) -> None:
        """Auto-load default keypair from environment"""
        keypair_path = os.environ.get("SOLANA_KEYPAIR_PATH")
        if keypair_path and os.path.exists(keypair_path):
            self.load_keypair(keypair_path, name="default")
    
    def load_keypair(
        self,
        path: str,
        name: Optional[str] = None,
    ) -> str:
        """
        Load a keypair from file.
        
        Args:
            path: Path to keypair file (JSON, base64, or raw bytes)
            name: Optional name for the wallet
            
        Returns:
            Address of loaded keypair
            
        Raises:
            KeypairError: If keypair cannot be loaded
        """
        path = Path(path)
        
        if not path.exists():
            raise KeypairError(f"Keypair file not found: {path}")
        
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            # Try JSON format first
            try:
                json_data = json.loads(data)
                if isinstance(json_data, dict) and 'secret_key' in json_data:
                    # JSON format with secret_key
                    secret_key = bytes(json_data['secret_key'])
                else:
                    # Array format
                    secret_key = bytes(json_data)
            except (json.JSONDecodeError, TypeError):
                # Try base64
                try:
                    secret_key = base64.b64decode(data)
                except Exception:
                    # Raw bytes
                    secret_key = data
            
            # Validate key length
            if len(secret_key) != 64:
                raise KeypairError(
                    f"Invalid keypair: expected 64 bytes, got {len(secret_key)}"
                )
            
            keypair = Keypair.from_bytes(secret_key)
            address = str(keypair.pubkey())
            
            # Use filename as name if not provided
            if not name:
                name = path.stem
            
            self._keypairs[address] = keypair
            self._wallet_info[address] = WalletInfo(
                address=address,
                name=name,
                network=self._get_network_from_path(path),
            )
            
            return address
            
        except Exception as e:
            raise KeypairError(f"Failed to load keypair: {e}")
    
    def _get_network_from_path(self, path: Path) -> str:
        """Infer network from path"""
        path_str = str(path).lower()
        if "devnet" in path_str:
            return "devnet"
        elif "testnet" in path_str:
            return "testnet"
        elif "mainnet" in path_str or "main" in path_str:
            return "mainnet"
        return "unknown"
    
    def get_keypair(self, address: str) -> Keypair:
        """
        Get a loaded keypair by address.
        
        Args:
            address: Wallet address
            
        Returns:
            Keypair for signing
            
        Raises:
            KeypairError: If keypair not found
        """
        if address not in self._keypairs:
            raise KeypairError(f"Keypair not loaded: {address}")
        return self._keypairs[address]
    
    def get_address(self, name: str) -> Optional[str]:
        """Get address by wallet name"""
        for info in self._wallet_info.values():
            if info.name == name:
                return info.address
        return None
    
    def list_wallets(self) -> List[WalletInfo]:
        """List all loaded wallets"""
        return list(self._wallet_info.values())
    
    def has_keypair(self, address: str) -> bool:
        """Check if a keypair is loaded"""
        return address in self._keypairs
    
    def remove_keypair(self, address: str) -> None:
        """Remove a loaded keypair"""
        if address in self._keypairs:
            del self._keypairs[address]
        if address in self._wallet_info:
            del self._wallet_info[address]
    
    def clear(self) -> None:
        """Clear all loaded keypairs"""
        self._keypairs.clear()
        self._wallet_info.clear()
    
    def validate_keypair(self, address: str) -> bool:
        """Validate that an address matches a loaded keypair"""
        if address not in self._keypairs:
            return False
        
        keypair = self._keypairs[address]
        return str(keypair.pubkey()) == address
    
    def sign_message(self, address: str, message: bytes) -> bytes:
        """
        Sign a message with a keypair.
        
        Args:
            address: Wallet address
            message: Message bytes to sign
            
        Returns:
            Signature bytes
        """
        keypair = self.get_keypair(address)
        return keypair.sign_message(message)
    
    def __enter__(self) -> "KeypairManager":
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - clears keypairs for security"""
        self.clear()


def get_keypair_manager(
    key_dir: Optional[str] = None,
) -> KeypairManager:
    """
    Get the default keypair manager.
    
    Creates a singleton manager with auto-loading from SOLANA_KEYPAIR_PATH.
    """
    return KeypairManager(key_dir=key_dir)
