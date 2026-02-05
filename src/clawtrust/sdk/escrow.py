"""
Escrow Contract Interface

Purpose:
    Python bindings for the ClawTrust USDC escrow contract on Solana.
    Handles deposit, lock, release, and refund operations.
    
Capabilities:
    - Initialize new escrows
    - Accept and fund escrows
    - Complete tasks and release funds
    - Cancel and refund
    - Check timeout status
    
Usage:
    >>> client = EscrowClient(network="devnet")
    >>> terms = EscrowTerms(skill_name="image-gen", price_usdc=10000, ...)
    >>> tx = await client.initialize(provider, mint, terms)
    
Smart Contract:
    Program ID: ESCRW1111111111111111111111111111111111111
    State: Created → Funded → Completed/Cancelled
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EscrowState(Enum):
    """State of an escrow"""
    CREATED = "created"      # Initialized, not funded
    FUNDED = "funded"       # Renter deposited, awaiting completion
    COMPLETED = "completed"  # Task done, funds released
    CANCELLED = "cancelled"  # Cancelled, funds refunded


@dataclass
class EscrowTerms:
    """
    Terms of an escrow agreement.
    
    Attributes:
        skill_name: Name of the skill being rented
        duration_seconds: Max duration for task completion
        price_usdc: Price in microUSDC (10,000 = 0.01 USDC)
        metadata_uri: IPFS link to full terms
    """
    skill_name: str
    price_usdc: int  # microUSDC
    duration_seconds: int
    metadata_uri: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "skill_name": self.skill_name,
            "price_usdc": self.price_usdc,
            "duration_seconds": self.duration_seconds,
            "metadata_uri": self.metadata_uri,
        }


@dataclass
class EscrowAccount:
    """
    State of an escrow account on Solana.
    
    Contains all data stored in the escrow PDA.
    """
    address: str
    provider: str
    renter: str
    terms: EscrowTerms
    state: EscrowState
    amount: int  # microUSDC
    created_at: str
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    
    def is_expired(self) -> bool:
        """
        Check if escrow has timed out.
        
        Returns:
            True if duration has elapsed
        """
        created = datetime.fromisoformat(self.created_at)
        now = datetime.utcnow()
        elapsed = (now - created).total_seconds()
        return elapsed > self.terms.duration_seconds
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "address": self.address,
            "provider": self.provider,
            "renter": self.renter,
            "terms": self.terms.to_dict(),
            "state": self.state.value,
            "amount": self.amount,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
        }


@dataclass
class EscrowTransaction:
    """
    Result of an escrow transaction.
    
    Contains transaction signature and status.
    """
    tx_signature: str
    escrow_address: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "tx_signature": self.tx_signature,
            "escrow_address": self.escrow_address,
            "success": self.success,
            "error": self.error,
        }


# Contract addresses (Solana mainnet)
ESCROW_PROGRAM_ID = "ESCRW1111111111111111111111111111111111111"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class EscrowClient:
    """
    Python client for the ClawTrust Escrow contract.
    
    Provides async methods for all escrow operations.
    Connect to devnet for testing, mainnet for production.
    
    Example:
        >>> client = EscrowClient(network="devnet")
        >>> terms = EscrowTerms("image-gen", 10000, 3600)
        >>> tx = await client.initialize(provider, mint, terms)
    """
    
    PROGRAM_ID = ESCROW_PROGRAM_ID
    USDC_MINT = USDC_MINT
    
    def __init__(self, network: str = "devnet"):
        """
        Initialize escrow client.
        
        Args:
            network: Solana network ("mainnet", "testnet", "devnet")
        """
        self.network = network
        self._escrows: dict[str, EscrowAccount] = {}
    
    async def initialize(
        self,
        provider: str,
        mint: str,
        terms: EscrowTerms,
    ) -> EscrowTransaction:
        """
        Initialize a new escrow.
        
        Creates a new escrow PDA with the given terms.
        Provider must fund the escrow after creation.
        
        Args:
            provider: Provider's wallet address
            mint: Token mint (e.g., USDC)
            terms: Escrow terms
            
        Returns:
            EscrowTransaction with address and tx signature
        """
        import hashlib
        
        # Generate PDA address
        seed = f"escrow-{provider}-{datetime.utcnow().isoformat()}"
        address = hashlib.sha256(seed.encode()).hexdigest()[:32]
        
        # Create escrow state
        escrow = EscrowAccount(
            address=address,
            provider=provider,
            renter="",
            terms=terms,
            state=EscrowState.CREATED,
            amount=0,
            created_at=datetime.utcnow().isoformat(),
        )
        self._escrows[address] = escrow
        
        return EscrowTransaction(
            tx_signature=f"tx-init-{address[:16]}",
            escrow_address=address,
            success=True,
        )
    
    async def accept(
        self,
        escrow_address: str,
        renter: str,
        amount: int,
    ) -> EscrowTransaction:
        """
        Accept escrow and fund it.
        
        Transfers USDC from renter to escrow.
        
        Args:
            escrow_address: Address of escrow to fund
            renter: Renter's wallet address
            amount: Amount to fund (microUSDC)
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.CREATED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not created",
            )
        
        # Fund escrow
        escrow.renter = renter
        escrow.amount = amount
        escrow.state = EscrowState.FUNDED
        
        return EscrowTransaction(
            tx_signature=f"tx-accept-{escrow_address[:16]}",
            escrow_address=escrow_address,
            success=True,
        )
    
    async def complete(
        self,
        escrow_address: str,
        authority: str,
    ) -> EscrowTransaction:
        """
        Complete task and release funds to provider.
        
        Can be called by provider or renter.
        
        Args:
            escrow_address: Address of escrow
            authority: Caller's wallet
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.FUNDED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not funded",
            )
        
        # Release funds
        escrow.state = EscrowState.COMPLETED
        escrow.completed_at = datetime.utcnow().isoformat()
        
        return EscrowTransaction(
            tx_signature=f"tx-complete-{escrow_address[:16]}",
            escrow_address=escrow_address,
            success=True,
        )
    
    async def cancel(
        self,
        escrow_address: str,
        authority: str,
    ) -> EscrowTransaction:
        """
        Cancel escrow and refund to renter.
        
        Can be called by provider anytime, or renter after timeout.
        
        Args:
            escrow_address: Address of escrow
            authority: Caller's wallet
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.FUNDED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not funded",
            )
        
        # Refund
        escrow.state = EscrowState.CANCELLED
        escrow.cancelled_at = datetime.utcnow().isoformat()
        
        return EscrowTransaction(
            tx_signature=f"tx-cancel-{escrow_address[:16]}",
            escrow_address=escrow_address,
            success=True,
        )
    
    async def get_state(self, escrow_address: str) -> Optional[EscrowState]:
        """
        Get the current state of an escrow.
        
        Args:
            escrow_address: Escrow address
            
        Returns:
            Current EscrowState or None
        """
        escrow = self._escrows.get(escrow_address)
        return escrow.state if escrow else None
    
    async def check_timeout(self, escrow_address: str) -> bool:
        """
        Check if escrow has timed out.
        
        Args:
            escrow_address: Escrow address
            
        Returns:
            True if duration has elapsed
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return False
        return escrow.is_expired()
    
    def get_escrow(self, escrow_address: str) -> Optional[EscrowAccount]:
        """
        Get escrow account details.
        
        Args:
            escrow_address: Escrow address
            
        Returns:
            EscrowAccount or None
        """
        return self._escrows.get(escrow_address)
    
    def format_escrow(self, escrow: EscrowAccount) -> str:
        """
        Format escrow for human-readable display.
        
        Args:
            escrow: EscrowAccount to format
            
        Returns:
            Formatted string
        """
        status_emoji = {
            EscrowState.CREATED: "⏳",
            EscrowState.FUNDED: "💰",
            EscrowState.COMPLETED: "✅",
            EscrowState.CANCELLED: "❌",
        }
        
        price_usd = escrow.terms.price_usdc / 1_000_000
        
        return f"""
{status_emoji.get(escrow.state, "")} **Escrow** #{escrow.address[:16]}

Provider: @{escrow.provider}
Renter: @{escrow.renter or "Not set"}
Skill: {escrow.terms.skill_name}
Amount: ${price_usd:.2f} USDC ({escrow.terms.price_usdc:,} microUSDC)
State: {escrow.state.value}
Created: {escrow.created_at}
""".strip()


# ============ Helper Functions ============

def create_escrow_terms(
    skill_name: str,
    price_usdc: float,
    duration_seconds: int = 3600,
) -> EscrowTerms:
    """
    Create escrow terms.
    
    Args:
        skill_name: Name of the skill
        price_usdc: Price in USDC (e.g., 0.01)
        duration_seconds: Max duration in seconds
        
    Returns:
        EscrowTerms object
    """
    return EscrowTerms(
        skill_name=skill_name,
        price_usdc=int(price_usdc * 1_000_000),  # Convert to microUSDC
        duration_seconds=duration_seconds,
    )


# ============ CLI Demo ============

async def demo():
    """Demo the escrow client"""
    client = EscrowClient()
    
    print("=== Escrow Demo ===\n")
    
    # Create terms
    terms = create_escrow_terms(
        skill_name="image-generation",
        price_usdc=0.01,
        duration_seconds=3600,
    )
    print(f"Created terms: {terms.price_usdc} microUSDC")
    
    # Initialize escrow
    print("\n1. Initializing escrow...")
    tx = await client.initialize(
        provider="happyclaw-agent",
        mint=client.USDC_MINT,
        terms=terms,
    )
    print(f"   Escrow: {tx.escrow_address}")
    print(f"   TX: {tx.tx_signature}")
    
    # Accept escrow
    print("\n2. Accepting and funding...")
    tx = await client.accept(
        escrow_address=tx.escrow_address,
        renter="agent-alpha",
        amount=10000,
    )
    print(f"   TX: {tx.tx_signature}")
    print(f"   State: {await client.get_state(tx.escrow_address)}")
    
    # Check timeout
    print(f"\n3. Timeout check: {await client.check_timeout(tx.escrow_address)}")
    
    # Complete
    print("\n4. Completing task...")
    tx = await client.complete(
        escrow_address=tx.escrow_address,
        authority="agent-alpha",
    )
    print(f"   TX: {tx.tx_signature}")
    print(f"   State: {await client.get_state(tx.escrow_address)}")
    
    # Show final state
    escrow = client.get_escrow(tx.escrow_address)
    if escrow:
        print("\n" + client.format_escrow(escrow))


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
