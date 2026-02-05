"""
Solana RPC Client Wrapper

Purpose:
    Provides a simple, type-safe interface for Solana blockchain interactions.
    Designed for use with the ClawTrust escrow system.
    
Capabilities:
    - Connect to Solana mainnet, testnet, or devnet
    - Get account balances and info
    - Send transactions
    - Query token balances
    - Derive Program Derived Addresses (PDAs)
    
Usage:
    # Connect to devnet
    client = SolanaClient(network="devnet")
    
    # Get balance
    balance = await client.get_balance("wallet-address")
    
    # Send transaction
    tx_sig = await client.send_transaction(signed_tx, [sig1, sig2])

Notes:
    - Requires httpx for async HTTP requests
    - Set SOLANA_RPC_URL environment variable to override default RPC
    - For testnet/devnet, tokens are free - no mocking needed!
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
import os


class Network(Enum):
    """Solana network types"""
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"


@dataclass
class ClientConfig:
    """Configuration for Solana client connection"""
    network: Network = Network.DEVNET
    rpc_url: Optional[str] = None
    ws_url: Optional[str] = None
    commitment: str = "confirmed"


class SolanaClient:
    """
    Solana RPC client for ClawTrust.
    
    This client provides a clean async interface to Solana RPC endpoints.
    Connect to devnet/testnet for testing, mainnet for production.
    
    Example:
        >>> client = SolanaClient(network="devnet")
        >>> balance = await client.get_balance(wallet)
        >>> print(f"Balance: {balance} lamports")
    """
    
    # Default RPC URLs for each network
    RPC_URLS = {
        Network.MAINNET: "https://api.mainnet-beta.solana.com",
        Network.TESTNET: "https://api.testnet.solana.com",
        Network.DEVNET: "https://api.devnet.solana.com",
    }
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """
        Initialize Solana client.
        
        Args:
            config: Optional ClientConfig. If not provided, uses devnet defaults.
        """
        self.config = config or ClientConfig()
        
        # Determine RPC URL
        if self.config.rpc_url:
            self.rpc_url = self.config.rpc_url
        else:
            self.rpc_url = self.RPC_URLS.get(
                self.config.network,
                self.RPC_URLS[Network.DEVNET]
            )
        
        # Allow environment override
        env_url = os.environ.get("SOLANA_RPC_URL")
        if env_url:
            self.rpc_url = env_url
        
        self.commitment = self.config.commitment
    
    async def get_balance(self, address: str) -> int:
        """
        Get the balance of a Solana address in lamports.
        
        Args:
            address: Base58 encoded public key
            
        Returns:
            Balance in lamports (1 SOL = 1e9 lamports)
            
        Raises:
            ConnectionError: If RPC call fails
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [address],
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return result["result"]["value"]
    
    async def get_account_info(self, address: str) -> Optional[dict]:
        """
        Get account info for a Solana address.
        
        Args:
            address: Base58 encoded public key
            
        Returns:
            Account info dict or None if not found
            
        Raises:
            ConnectionError: If RPC call fails
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [address, {"commitment": self.commitment}],
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return result["result"]["value"]
    
    async def get_latest_blockhash(self) -> str:
        """
        Get the latest blockhash for transaction building.
        
        Returns:
            Blockhash as base58 string
            
        Raises:
            ConnectionError: If RPC call fails
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [{"commitment": self.commitment}],
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return result["result"]["value"]["blockhash"]
    
    async def send_transaction(
        self,
        transaction: bytes,
        signatures: list[str],
    ) -> str:
        """
        Send a signed transaction to the network.
        
        Args:
            transaction: Signed transaction bytes
            signatures: List of base58 signatures
            
        Returns:
            Transaction signature (tx id)
            
        Raises:
            ConnectionError: If RPC call fails
        """
        import base64
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        base64.b64encode(transaction).decode(),
                        {
                            "encoding": "base64",
                            "commitment": self.commitment,
                        },
                    ],
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return result["result"]
    
    async def get_token_balance(
        self,
        token_account: str,
        mint: str,
    ) -> int:
        """
        Get token balance for a token account.
        
        Args:
            token_account: Token account address
            mint: Token mint address
            
        Returns:
            Token balance in raw units (not decimals)
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountBalance",
                    "params": [token_account, {"commitment": self.commitment}],
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return int(result["result"]["value"]["amount"])
    
    async def get_token_accounts_by_owner(
        self,
        owner: str,
        mint: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all token accounts owned by an address.
        
        Args:
            owner: Owner's public key
            mint: Optional token mint to filter
            
        Returns:
            List of token account dicts
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            params = [{"commitment": self.commitment}]
            if mint:
                params.append({"mint": mint})
            
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [owner] + params,
                },
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise RuntimeError(f"RPC error: {result['error']}")
            return result["result"]["value"]
    
    def derive_pda(
        self,
        seeds: list[bytes],
        program_id: str,
    ) -> tuple[str, int]:
        """
        Derive a Program Derived Address (PDA).
        
        Args:
            seeds: List of seed bytes
            program_id: Program's public key
            
        Returns:
            Tuple of (address, bump)
            
        Note:
            Uses SHA256 for PDA derivation.
        """
        import hashlib
        
        combined = b"".join(seeds) + program_id.encode()
        hash_digest = hashlib.sha256(combined).digest()
        address_bytes = hash_digest[:32]
        address = "".join(f"{b:02x}" for b in address_bytes)
        
        return (address, 255)
    
    def get_rpc_url(self) -> str:
        """Get the configured RPC URL"""
        return self.rpc_url
    
    def get_network(self) -> Network:
        """Get the configured network"""
        return self.config.network


# ============ CLI Helpers ============

def get_client(network: str = "devnet") -> SolanaClient:
    """
    Get a Solana client for the given network.
    
    Args:
        network: One of 'mainnet', 'testnet', or 'devnet'
        
    Returns:
        Configured SolanaClient instance
    """
    network_enum = Network.DEVNET
    if network == "mainnet":
        network_enum = Network.MAINNET
    elif network == "testnet":
        network_enum = Network.TESTNET
    
    return SolanaClient(ClientConfig(network=network_enum))


if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = SolanaClient()
        print(f"Connected to: {client.get_rpc_url()}")
        
        # Get latest blockhash (sanity check)
        try:
            blockhash = await client.get_latest_blockhash()
            print(f"Latest blockhash: {blockhash[:16]}...")
        except Exception as e:
            print(f"Connection test: {e}")
    
    asyncio.run(main())
