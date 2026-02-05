"""
Agent Identity Management

Purpose:
    Provides wallet-based identity management for ClawTrust agents.
    Each agent is identified by their Solana wallet address.
    
Capabilities:
    - Create and register agent identities
    - Query identities by ID, wallet, or name
    - Track reputation and rental history
    - Update identity metadata
    
Usage:
    >>> manager = IdentityManager()
    >>> identity = manager.get_by_wallet("wallet-address")
    >>> print(identity.name)
    
Storage:
    - For MVP: In-memory storage
    - Production: On-chain registry (ERC-8004 inspired) or database
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class IdentityStatus(Enum):
    """Status of an agent identity"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class AgentIdentity:
    """
    Represents an agent's identity in ClawTrust.
    
    Each identity is tied to a Solana wallet address.
    Reputation scores track the agent's trustworthiness.
    
    Attributes:
        name: Human-readable name (e.g., "@happyclaw-agent")
        wallet_address: Solana wallet address (primary identifier)
        public_key: Associated public key
        email: Optional contact email
        reputation_score: Score from 0-100
        total_rentals: Total rentals participated in
        completed_rentals: Successfully completed rentals
        status: Identity status (active, suspended, etc.)
    """
    name: str
    wallet_address: str
    public_key: str
    id: str = field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:8]}")
    email: Optional[str] = None
    reputation_score: float = 0.0
    total_rentals: int = 0
    completed_rentals: int = 0
    status: IdentityStatus = IdentityStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """
        Convert identity to dictionary for serialization.
        
        Returns:
            Dictionary representation of the identity
        """
        return {
            "id": self.id,
            "name": self.name,
            "wallet_address": self.wallet_address,
            "public_key": self.public_key,
            "email": self.email,
            "reputation_score": self.reputation_score,
            "total_rentals": self.total_rentals,
            "completed_rentals": self.completed_rentals,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentIdentity":
        """
        Create identity from dictionary.
        
        Args:
            data: Dictionary with identity fields
            
        Returns:
            AgentIdentity instance
        """
        status = IdentityStatus(data.get("status", "active"))
        return cls(
            id=data.get("id", f"agent-{uuid.uuid4().hex[:8]}"),
            name=data["name"],
            wallet_address=data["wallet_address"],
            public_key=data["public_key"],
            email=data.get("email"),
            reputation_score=data.get("reputation_score", 0.0),
            total_rentals=data.get("total_rentals", 0),
            completed_rentals=data.get("completed_rentals", 0),
            status=status,
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )
    
    def update_reputation(self, score: float):
        """
        Update the reputation score.
        
        Args:
            score: New score (0-100)
        """
        self.reputation_score = score
        self.updated_at = datetime.utcnow().isoformat()
    
    def increment_rentals(self, completed: bool = False):
        """
        Increment rental count.
        
        Args:
            completed: Whether the rental was completed successfully
        """
        self.total_rentals += 1
        if completed:
            self.completed_rentals += 1
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_short_str(self) -> str:
        """Short string representation for display"""
        return f"@{self.name} ({self.reputation_score:.0f}/100)"


class IdentityManager:
    """
    Manages agent identities.
    
    Provides CRUD operations for agent identities.
    For MVP: In-memory storage.
    Production: Use on-chain registry or database.
    
    Example:
        >>> manager = IdentityManager()
        >>> agents = manager.list_identities()
        >>> for agent in agents:
        ...     print(agent.name)
    """
    
    def __init__(self):
        """Initialize identity manager with empty storage"""
        self._identities: dict[str, AgentIdentity] = {}
        self._wallets: dict[str, AgentIdentity] = {}
    
    def register(self, identity: AgentIdentity) -> AgentIdentity:
        """
        Register a new identity.
        
        Args:
            identity: AgentIdentity to register
            
        Returns:
            The registered identity
            
        Raises:
            ValueError: If wallet already registered
        """
        if identity.wallet_address.lower() in self._wallets:
            raise ValueError(f"Wallet {identity.wallet_address} already registered")
        
        self._identities[identity.id] = identity
        self._wallets[identity.wallet_address.lower()] = identity
        return identity
    
    def get_by_id(self, id: str) -> Optional[AgentIdentity]:
        """
        Get identity by ID.
        
        Args:
            id: Agent ID
            
        Returns:
            AgentIdentity or None if not found
        """
        return self._identities.get(id)
    
    def get_by_wallet(self, wallet: str) -> Optional[AgentIdentity]:
        """
        Get identity by wallet address.
        
        Args:
            wallet: Wallet address
            
        Returns:
            AgentIdentity or None if not found
        """
        return self._wallets.get(wallet.lower())
    
    def get_by_name(self, name: str) -> Optional[AgentIdentity]:
        """
        Get identity by name.
        
        Args:
            name: Agent name (without @)
            
        Returns:
            AgentIdentity or None if not found
        """
        for identity in self._identities.values():
            if identity.name.lower() == name.lower():
                return identity
        return None
    
    def list_identities(
        self,
        status: Optional[IdentityStatus] = None,
        min_reputation: Optional[float] = None,
    ) -> list[AgentIdentity]:
        """
        List all identities with optional filters.
        
        Args:
            status: Filter by status
            min_reputation: Filter by minimum reputation score
            
        Returns:
            List of matching identities
        """
        identities = list(self._identities.values())
        
        if status:
            identities = [i for i in identities if i.status == status]
        
        if min_reputation is not None:
            identities = [
                i for i in identities
                if i.reputation_score >= min_reputation
            ]
        
        return identities
    
    def update_reputation(
        self,
        wallet: str,
        score: float,
    ) -> Optional[AgentIdentity]:
        """
        Update reputation for an identity.
        
        Args:
            wallet: Wallet address
            score: New reputation score
            
        Returns:
            Updated identity or None if not found
        """
        identity = self.get_by_wallet(wallet)
        if identity:
            identity.update_reputation(score)
        return identity
    
    def check_exists(self, wallet: str) -> bool:
        """
        Check if identity exists for wallet.
        
        Args:
            wallet: Wallet address
            
        Returns:
            True if exists, False otherwise
        """
        return wallet.lower() in self._wallets


# ============ Factory Functions ============

def create_identity(
    name: str,
    wallet_address: str,
    public_key: str,
    email: Optional[str] = None,
) -> AgentIdentity:
    """
    Create a new agent identity.
    
    Args:
        name: Agent name
        wallet_address: Solana wallet address
        public_key: Associated public key
        email: Optional email
        
    Returns:
        New AgentIdentity
    """
    return AgentIdentity(
        name=name,
        wallet_address=wallet_address,
        public_key=public_key,
        email=email,
    )


def load_identity(wallet: str) -> Optional[AgentIdentity]:
    """
    Load identity from storage.
    
    Args:
        wallet: Wallet address
        
    Returns:
        AgentIdentity or None if not found
    """
    manager = IdentityManager()
    return manager.get_by_wallet(wallet)


# ============ CLI ============

def demo():
    """Demo identity management"""
    manager = IdentityManager()
    
    # Create an identity
    identity = create_identity(
        name="happyclaw-agent",
        wallet_address="happyclaw.sol",
        public_key="happyclaw-pubkey",
        email="happytreeiot@gmail.com",
    )
    identity.reputation_score = 85.0
    
    manager.register(identity)
    
    # Query it
    retrieved = manager.get_by_wallet("happyclaw.sol")
    print(f"Name: {retrieved.name}")
    print(f"Reputation: {retrieved.reputation_score}")


if __name__ == "__main__":
    demo()
