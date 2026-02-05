"""
TrustyClaw SDK - Python SDK for interacting with TrustyClaw services

Modules:
- client: Solana RPC client wrapper
- identity: Agent identity management
- reputation: Reputation scoring engine
- escrow: Escrow contract interface
- solana: Real Solana blockchain integration
- usdc: USDC SPL Token integration
- reputation_chain: On-chain reputation storage
"""

from .client import SolanaClient
from .identity import AgentIdentity, IdentityManager
from .reputation import ReputationEngine, Review, ReputationScore
from .escrow import EscrowClient, EscrowTerms, EscrowState
from .solana import SolanaRPCClient, WalletInfo, TransactionInfo, get_client
from .usdc import USDCClient, TokenAccount, TransferResult, get_usdc_client
from .reputation_chain import (
    ReputationPDAProgram,
    ReputationScoreData,
    ReviewData,
    get_reputation_program,
)

__all__ = [
    "SolanaClient",
    "AgentIdentity",
    "IdentityManager", 
    "ReputationEngine",
    "Review",
    "ReputationScore",
    "EscrowClient",
    "EscrowTerms",
    "EscrowState",
    "SolanaRPCClient",
    "WalletInfo",
    "TransactionInfo",
    "get_client",
    "USDCClient",
    "TokenAccount",
    "TransferResult",
    "get_usdc_client",
    "ReputationPDAProgram",
    "ReputationScoreData",
    "ReviewData",
    "get_reputation_program",
]

__version__ = "0.1.0"
