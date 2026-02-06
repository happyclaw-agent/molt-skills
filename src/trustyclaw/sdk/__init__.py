"""
TrustyClaw SDK - Python SDK for interacting with TrustyClaw services

Modules:
- client: Solana RPC client wrapper
- identity: Agent identity management
- reputation: Reputation scoring engine
- escrow: Escrow contract interface
- solana: Real Solana blockchain integration
- usdc: USDC SPL Token integration
- cross_chain: Cross-chain bridge service
- unified_balance: Unified balance API
- reputation_chain: On-chain reputation storage
- review_system: Full review lifecycle management
- escrow_contract: Secure payment escrow
"""

from .client import SolanaClient
from .identity import AgentIdentity, IdentityManager
from .reputation import ReputationEngine, Review, ReputationScore
from .escrow import EscrowClient, EscrowTerms, EscrowState
from .solana import SolanaRPCClient, WalletInfo, TransactionInfo, get_client
from .usdc import USDCClient, TokenAccount, TransferResult, get_usdc_client
from .cross_chain import (
    CrossChainBridge,
    BridgeTransaction,
    BridgeStatus,
    BridgeQuote,
    Chain,
    get_bridge_client,
)
from .unified_balance import (
    UnifiedBalance,
    UnionWallet,
    ChainBalance,
    AggregatedBalance,
    Chain,
    Token,
    get_unified_balance,
)
from .reputation_chain import (
    ReputationPDAProgram,
    ReputationScoreData,
    ReviewData,
    get_reputation_program,
)
from .review_system import (
    ReviewService,
    Review,
    ReviewStatus,
    ReviewDispute,
    ReviewVote,
    get_review_service,
)
from .escrow_contract import (
    EscrowClient as EscrowContractClient,
    Escrow,
    EscrowTerms,
    EscrowState,
    get_escrow_client,
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
    "CrossChainBridge",
    "BridgeTransaction",
    "BridgeStatus",
    "BridgeQuote",
    "Chain",
    "get_bridge_client",
    "UnifiedBalance",
    "UnionWallet",
    "ChainBalance",
    "AggregatedBalance",
    "Token",
    "get_unified_balance",
    "ReputationPDAProgram",
    "ReputationScoreData",
    "ReviewData",
    "get_reputation_program",
    "ReviewService",
    "Review",
    "ReviewStatus",
    "ReviewDispute",
    "ReviewVote",
    "get_review_service",
    "EscrowContractClient",
    "Escrow",
    "EscrowTerms",
    "EscrowState",
    "get_escrow_client",
]

__version__ = "0.1.0"
