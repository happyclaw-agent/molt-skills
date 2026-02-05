"""
Escrow Contract for TrustyClaw

Secure payment escrow for agent skill rentals using USDC.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import json

try:
    from solana.rpc.api import Client as SolanaClient
    from solana.rpc.commitment import Confirmed, Finalized
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
    from solana.transaction import Transaction
    from solana.system_program import create_account, CreateAccountParams
    HAS_SOLANA = True
except ImportError:
    HAS_SOLANA = False


class EscrowState(Enum):
    """Escrow lifecycle state"""
    CREATED = "created"
    FUNDED = "funded"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    RELEASED = "released"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class EscrowError(Exception):
    """Escrow operation error"""
    pass


@dataclass
class EscrowTerms:
    """Terms of the escrow agreement"""
    renter: str  # Renter wallet
    provider: str  # Provider wallet
    skill_id: str  # Skill being rented
    amount: int  # USDC amount (lamports-like, 6 decimals)
    duration_hours: int  # Max duration in hours
    deliverable_hash: str  # SHA256 of expected deliverable
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = field(default_factory=lambda: (
        datetime.utcnow() + timedelta(hours=24)
    ).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "renter": self.renter,
            "provider": self.provider,
            "skill_id": self.skill_id,
            "amount": self.amount,
            "duration_hours": self.duration_hours,
            "deliverable_hash": self.deliverable_hash,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


@dataclass
class Escrow:
    """Complete escrow record"""
    escrow_id: str
    terms: EscrowTerms
    state: EscrowState = EscrowState.CREATED
    funded_at: Optional[str] = None
    completed_at: Optional[str] = None
    released_at: Optional[str] = None
    refunded_at: Optional[str] = None
    dispute_reason: Optional[str] = None
    dispute_resolved_at: Optional[str] = None
    dispute_resolution: Optional[str] = None  # "released", "refunded", "split"
    actual_deliverable_hash: Optional[str] = None
    provider_signature: Optional[str] = None
    renter_signature: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "escrow_id": self.escrow_id,
            "terms": self.terms.to_dict(),
            "state": self.state.value,
            "funded_at": self.funded_at,
            "completed_at": self.completed_at,
            "released_at": self.released_at,
            "refunded_at": self.refunded_at,
            "dispute_reason": self.dispute_reason,
            "dispute_resolved_at": self.dispute_resolved_at,
            "dispute_resolution": self.dispute_resolution,
            "actual_deliverable_hash": self.actual_deliverable_hash,
            "created_at": self.created_at,
        }


@dataclass
class EscrowPDAData:
    """On-chain escrow account data"""
    escrow_id: str
    renter: str
    provider: str
    amount: int
    state: int  # 0=created, 1=funded, 2=active, 3=completed, 4=disputed, 5=released, 6=refunded
    deliverable_hash: str
    created_at: int
    expires_at: int
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes"""
        return (
            self.escrow_id.encode('utf-8')[:32].ljust(32, b'\0') +
            self.renter.encode('utf-8')[:32].ljust(32, b'\0') +
            self.provider.encode('utf-8')[:32].ljust(32, b'\0') +
            self.amount.to_bytes(8, 'little') +
            self.state.to_bytes(1, 'little') +
            self.deliverable_hash.encode('utf-8')[:32].ljust(32, b'\0') +
            self.created_at.to_bytes(8, 'little') +
            self.expires_at.to_bytes(8, 'little')
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'EscrowPDAData':
        """Deserialize from bytes"""
        return cls(
            escrow_id=data[0:32].decode('utf-8').rstrip('\0'),
            renter=data[32:64].decode('utf-8').rstrip('\0'),
            provider=data[64:96].decode('utf-8').rstrip('\0'),
            amount=int.from_bytes(data[96:104], 'little'),
            state=int.from_bytes(data[104:105], 'little'),
            deliverable_hash=data[105:137].decode('utf-8').rstrip('\0'),
            created_at=int.from_bytes(data[137:145], 'little'),
            expires_at=int.from_bytes(data[145:153], 'little'),
        )


class EscrowClient:
    """
    Escrow contract client for managing secure payments.
    
    Features:
    - Create escrows with terms
    - Fund with USDC
    - Complete and release
    - Dispute resolution
    - Refunds for non-delivery
    """
    
    ESCROW_SEED = b"trustyclaw-escrow"
    ESCROW_SIZE = 256
    
    def __init__(
        self,
        network: str = "devnet",
        usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        program_id: Optional[str] = None,
        mock: bool = True,
    ):
        self.network = network
        self.usdc_mint = usdc_mint
        self.program_id = program_id or self._derive_program_id()
        self.mock = mock
        
        if HAS_SOLANA and not mock:
            self.client = SolanaClient(
                f"https://api.{network}.solana.com"
            )
        else:
            self.client = None
        
        self._escrows: Dict[str, Escrow] = {}
        self._init_mock_data()
    
    def _derive_program_id(self) -> str:
        """Derive program ID (placeholder)"""
        return "11111111111111111111111111111111"
    
    def _init_mock_data(self):
        """Initialize mock escrows for demo"""
        if not self.mock:
            return
        
        # Add a sample escrow
        terms = EscrowTerms(
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="image-generation",
            amount=1000000,  # 1 USDC
            duration_hours=24,
            deliverable_hash=hashlib.sha256(b"test-image.png").hexdigest()[:32],
        )
        
        escrow = Escrow(
            escrow_id="escrow-demo-1",
            terms=terms,
            state=EscrowState.FUNDED,
            funded_at=datetime.utcnow().isoformat(),
        )
        self._escrows[escrow.escrow_id] = escrow
    
    # ============ Escrow Operations ============
    
    def create_escrow(
        self,
        renter: str,
        provider: str,
        skill_id: str,
        amount: int,
        duration_hours: int,
        deliverable_hash: str,
    ) -> Escrow:
        """
        Create a new escrow with terms.
        
        Args:
            renter: Renter wallet
            provider: Provider wallet
            skill_id: Skill being rented
            amount: USDC amount (6 decimals)
            duration_hours: Max duration
            deliverable_hash: Expected deliverable hash
            
        Returns:
            Created Escrow
            
        Raises:
            EscrowError: If creation fails
        """
        escrow_id = f"escrow-{uuid.uuid4().hex[:12]}"
        
        terms = EscrowTerms(
            renter=renter,
            provider=provider,
            skill_id=skill_id,
            amount=amount,
            duration_hours=duration_hours,
            deliverable_hash=deliverable_hash,
        )
        
        escrow = Escrow(
            escrow_id=escrow_id,
            terms=terms,
            state=EscrowState.CREATED,
        )
        
        self._escrows[escrow_id] = escrow
        return escrow
    
    def get_escrow(self, escrow_id: str) -> Optional[Escrow]:
        """Get escrow by ID"""
        return self._escrows.get(escrow_id)
    
    def get_escrows_by_participant(
        self,
        address: str,
        states: Optional[List[EscrowState]] = None,
    ) -> List[Escrow]:
        """Get all escrows for a participant"""
        escrows = [
            e for e in self._escrows.values()
            if e.terms.renter == address or e.terms.provider == address
        ]
        
        if states:
            escrows = [e for e in escrows if e.state in states]
        
        return sorted(escrows, key=lambda e: e.created_at, reverse=True)
    
    # ============ Funding Operations ============
    
    def fund_escrow(self, escrow_id: str) -> Escrow:
        """
        Fund an escrow (renter deposits USDC).
        
        Args:
            escrow_id: Escrow to fund
            
        Returns:
            Updated Escrow
            
        Raises:
            EscrowError: If escrow not found or already funded
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state != EscrowState.CREATED:
            raise EscrowError(f"Escrow {escrow_id} is not in CREATED state")
        
        escrow.state = EscrowState.FUNDED
        escrow.funded_at = datetime.utcnow().isoformat()
        
        return escrow
    
    def activate_escrow(self, escrow_id: str) -> Escrow:
        """
        Activate a funded escrow (provider starts work).
        
        Args:
            escrow_id: Escrow to activate
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state != EscrowState.FUNDED:
            raise EscrowError(f"Escrow {escrow_id} is not in FUNDED state")
        
        escrow.state = EscrowState.ACTIVE
        return escrow
    
    # ============ Completion Operations ============
    
    def complete_escrow(
        self,
        escrow_id: str,
        deliverable_hash: str,
    ) -> Escrow:
        """
        Mark escrow as completed (provider delivered).
        
        Args:
            escrow_id: Escrow to complete
            deliverable_hash: Hash of actual deliverable
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state != EscrowState.ACTIVE:
            raise EscrowError(f"Escrow {escrow_id} is not in ACTIVE state")
        
        escrow.state = EscrowState.COMPLETED
        escrow.completed_at = datetime.utcnow().isoformat()
        escrow.actual_deliverable_hash = deliverable_hash
        
        return escrow
    
    def verify_deliverable(
        self,
        escrow_id: str,
        expected_hash: str,
    ) -> Dict[str, Any]:
        """
        Verify deliverable matches expected.
        
        Args:
            escrow_id: Escrow to check
            expected_hash: Expected deliverable hash
            
        Returns:
            Verification result
        """
        escrow = self.get_escrow(escrow_id)
        
        if not escrow:
            return {"valid": False, "error": "Escrow not found"}
        
        if not escrow.actual_deliverable_hash:
            return {"valid": False, "error": "No deliverable submitted"}
        
        matches = escrow.actual_deliverable_hash == expected_hash
        
        return {
            "valid": matches,
            "expected": expected_hash,
            "actual": escrow.actual_deliverable_hash,
        }
    
    # ============ Release Operations ============
    
    def release_escrow(self, escrow_id: str) -> Escrow:
        """
        Release funds to provider (renter approves).
        
        Args:
            escrow_id: Escrow to release
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state not in [EscrowState.COMPLETED, EscrowState.ACTIVE]:
            raise EscrowError(
                f"Escrow {escrow_id} cannot be released from {escrow.state.value} state"
            )
        
        escrow.state = EscrowState.RELEASED
        escrow.released_at = datetime.utcnow().isoformat()
        
        return escrow
    
    def release_amount_for_escrow(self, escrow_id: str) -> int:
        """Calculate release amount (full amount)"""
        escrow = self.get_escrow(escrow_id)
        if escrow:
            return escrow.terms.amount
        return 0
    
    # ============ Refund Operations ============
    
    def refund_escrow(self, escrow_id: str) -> Escrow:
        """
        Refund funds to renter (provider failed to deliver).
        
        Args:
            escrow_id: Escrow to refund
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state not in [EscrowState.FUNDED, EscrowState.ACTIVE]:
            raise EscrowError(
                f"Escrow {escrow_id} cannot be refunded from {escrow.state.value} state"
            )
        
        escrow.state = EscrowState.REFUNDED
        escrow.refunded_at = datetime.utcnow().isoformat()
        
        return escrow
    
    def refund_amount_for_escrow(self, escrow_id: str) -> int:
        """Calculate refund amount (full amount minus fees)"""
        escrow = self.get_escrow(escrow_id)
        if escrow:
            # 99% refund (1% platform fee)
            return int(escrow.terms.amount * 0.99)
        return 0
    
    # ============ Dispute Operations ============
    
    def dispute_escrow(self, escrow_id: str, reason: str) -> Escrow:
        """
        File a dispute on an escrow.
        
        Args:
            escrow_id: Escrow to dispute
            reason: Why it's disputed
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state not in [EscrowState.ACTIVE, EscrowState.COMPLETED]:
            raise EscrowError(
                f"Escrow {escrow_id} cannot be disputed from {escrow.state.value} state"
            )
        
        escrow.state = EscrowState.DISPUTED
        escrow.dispute_reason = reason
        
        return escrow
    
    def resolve_dispute(
        self,
        escrow_id: str,
        resolution: str,  # "released", "refunded", "split"
        split_percentage: int = 50,  # Provider gets X%
    ) -> Escrow:
        """
        Resolve an escrow dispute.
        
        Args:
            escrow_id: Escrow to resolve
            resolution: How to resolve
            split_percentage: Provider share for split resolution
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state != EscrowState.DISPUTED:
            raise EscrowError(f"Escrow {escrow_id} is not in DISPUTED state")
        
        if resolution == "released":
            escrow.state = EscrowState.RELEASED
            escrow.released_at = datetime.utcnow().isoformat()
        elif resolution == "refunded":
            escrow.state = EscrowState.REFUNDED
            escrow.refunded_at = datetime.utcnow().isoformat()
        elif resolution == "split":
            escrow.state = EscrowState.RELEASED
            escrow.released_at = datetime.utcnow().isoformat()
            # Mark as partial in notes
        
        escrow.dispute_resolved_at = datetime.utcnow().isoformat()
        escrow.dispute_resolution = resolution
        
        return escrow
    
    # ============ Cancellation ============
    
    def cancel_escrow(self, escrow_id: str) -> Escrow:
        """
        Cancel an unfunded escrow.
        
        Args:
            escrow_id: Escrow to cancel
            
        Returns:
            Updated Escrow
        """
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found")
        
        escrow = self._escrows[escrow_id]
        
        if escrow.state != EscrowState.CREATED:
            raise EscrowError(
                f"Only CREATED escrows can be cancelled (current: {escrow.state.value})"
            )
        
        escrow.state = EscrowState.CANCELLED
        return escrow
    
    # ============ Export ============
    
    def export_escrows_json(self, address: str = None) -> str:
        """Export escrows as JSON"""
        if address:
            escrows = self.get_escrows_by_participant(address)
        else:
            escrows = list(self._escrows.values())
        
        return json.dumps(
            [e.to_dict() for e in escrows],
            indent=2,
        )


def get_escrow_client(
    network: str = "devnet",
    usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    mock: bool = True,
) -> EscrowClient:
    """
    Get an EscrowClient instance.
    
    Args:
        network: Network name
        usdc_mint: USDC mint address
        mock: Use mock data
        
    Returns:
        Configured EscrowClient
    """
    return EscrowClient(
        network=network,
        usdc_mint=usdc_mint,
        mock=mock,
    )
