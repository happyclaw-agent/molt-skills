"""
Solana RPC Client for TrustyClaw

Real Solana blockchain integration for escrow operations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import os
import base64

from solana.rpc.api import Client as SolanaClient
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts, TokenAccountOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey


class Network(Enum):
    """Solana network environments"""
    DEVNET = "https://api.devnet.solana.com"
    TESTNET = "https://api.testnet.solana.com"
    MAINNET = "https://api.mainnet-beta.solana.com"


@dataclass
class WalletInfo:
    """Wallet information"""
    address: str
    lamports: int
    usdc_balance: float = 0.0
    
    @property
    def sol_balance(self) -> float:
        """Balance in SOL"""
        return self.lamports / 1_000_000_000


@dataclass
class TransactionInfo:
    """Transaction information"""
    signature: str
    slot: int
    status: str
    block_time: Optional[int] = None
    
    @property
    def explorer_url(self) -> str:
        """Solana Explorer URL"""
        return f"https://explorer.solana.com/tx/{self.signature}?cluster=devnet"


class SolanaRPCClient:
    """Real Solana RPC client for TrustyClaw operations"""
    
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    ESCROW_SEED = "trustyclaw-escrow"
    
    def __init__(
        self,
        network: Network = Network.DEVNET,
        keypair_path: Optional[str] = None,
        commitment: str = "confirmed",
    ):
        self.network = network
        self.commitment = commitment
        self.client = SolanaClient(str(network.value))
        
        self._keypair: Optional[Keypair] = None
        if keypair_path and os.path.exists(keypair_path):
            self.load_keypair(keypair_path)
    
    def load_keypair(self, path: str) -> None:
        """Load a keypair from file"""
        with open(path, 'rb') as f:
            keypair_data = f.read()
        
        try:
            self._keypair = Keypair.from_bytes(keypair_data)
        except Exception:
            secret = base64.b64decode(keypair_data)
            self._keypair = Keypair.from_bytes(secret)
    
    @property
    def address(self) -> Optional[str]:
        """Get loaded keypair address"""
        if self._keypair:
            return str(self._keypair.pubkey())
        return None
    
    def get_balance(self, address: str) -> WalletInfo:
        """Get SOL and USDC balance for an address"""
        pubkey = Pubkey.from_string(address) if isinstance(address, str) else address
        resp = self.client.get_balance(pubkey, commitment=self.commitment)
        lamports = resp.value if hasattr(resp, 'value') else 0
        usdc_balance = 0.0  # TODO: Fix token balance RPC call
        
        return WalletInfo(
            address=address,
            lamports=lamports,
            usdc_balance=usdc_balance,
        )
    
    def get_token_balance(self, address: str, mint: str) -> float:
        """Get token balance for a specific mint"""
        pubkey = Pubkey.from_string(address)
        mint_pubkey = Pubkey.from_string(mint)
        
        opts = TokenAccountOpts(mint=mint_pubkey)
        resp = self.client.get_token_accounts_by_owner(
            pubkey,
            opts,
            commitment=self.commitment,
        )
        
        if resp.value and len(resp.value) > 0:
            account_data = resp.value[0].account.data
            if hasattr(account_data, 'parsed') and hasattr(account_data.parsed, 'info'):
                return float(account_data.parsed.info.tokenAmount.uiAmount)
        
        return 0.0
    
    def get_transaction(self, signature: str) -> Optional[TransactionInfo]:
        """Get transaction details"""
        resp = self.client.get_transaction(
            signature,
            encoding="jsonParsed",
            commitment=self.commitment,
        )
        
        if resp.value:
            return TransactionInfo(
                signature=signature,
                slot=resp.value.slot,
                status="confirmed",
                block_time=resp.value.block_time,
            )
        return None
    
    def derive_escrow_pda(self, provider: str, skill_id: str) -> str:
        """Derive a PDA for an escrow account (provider is base58 pubkey string)."""
        provider_pubkey = Pubkey.from_string(provider)
        provider_bytes = bytes(provider_pubkey)
        seed_bytes = skill_id.encode()[:32]
        program_id_str = os.environ.get("ESCROW_PROGRAM_ID", "11111111111111111111111111111111")
        program_pubkey = Pubkey.from_string(program_id_str)
        pda, _bump = Pubkey.find_program_address(
            [self.ESCROW_SEED.encode(), provider_bytes, seed_bytes],
            program_pubkey,
        )
        return str(pda)
    
    def get_recent_blockhash(self) -> str:
        """Get recent blockhash for transaction building"""
        resp = self.client.get_recent_blockhash()
        return resp.value.blockhash if hasattr(resp.value, 'blockhash') else resp.value
    
    def request_airdrop(self, address: str, lamports: int = 1000000000) -> str:
        """Request SOL airdrop (devnet/testnet only)"""
        if self.network != Network.DEVNET:
            raise ValueError("Airdrop only available on devnet")
        
        resp = self.client.request_airdrop(address, lamports, commitment=self.commitment)
        return resp.value if hasattr(resp, 'value') else str(resp)


def get_client(network: str = "devnet") -> SolanaRPCClient:
    """Get a Solana RPC client"""
    network_map = {
        "devnet": Network.DEVNET,
        "testnet": Network.TESTNET,
        "mainnet": Network.MAINNET,
    }
    
    net = network_map.get(network.lower(), Network.DEVNET)
    keypair_path = os.environ.get("SOLANA_KEYPAIR_PATH")
    
    return SolanaRPCClient(
        network=net,
        keypair_path=keypair_path,
        commitment="confirmed",
    )
