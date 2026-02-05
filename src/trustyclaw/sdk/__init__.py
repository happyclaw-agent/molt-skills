"""
TrustyClaw SDK - Python SDK for interacting with TrustyClaw services

Modules:
- client: Solana RPC client wrapper
- identity: Agent identity management
- reputation: Reputation scoring engine
- escrow: Escrow contract interface
"""

from .client import SolanaClient
from .identity import AgentIdentity, IdentityManager
from .reputation import ReputationEngine
from .escrow import EscrowClient, EscrowTerms, EscrowState

__all__ = [
    "SolanaClient",
    "AgentIdentity",
    "IdentityManager", 
    "ReputationEngine",
    "EscrowClient",
    "EscrowTerms",
    "EscrowState",
]

__version__ = "0.1.0"
