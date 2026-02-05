"""
Mandate Skill for TrustyClaw

Skill rental agreement management.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json


class MandateStatus(Enum):
    """Mandate lifecycle status"""
    DRAFT = "draft"
    PENDING = "pending"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXTENDED = "extended"


class MandateError(Exception):
    """Mandate operation error"""
    pass


@dataclass
class MandateTerms:
    """Terms of the mandate agreement"""
    skill_id: str
    amount: int  # USDC lamports
    duration_hours: int
    deliverables: List[str]
    requirements: List[str] = field(default_factory=list)
    revisions: int = 0  # Number of free revisions
    exclusivity: bool = False  # Exclusive use during mandate
    confidentiality: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "amount": self.amount,
            "duration_hours": self.duration_hours,
            "deliverables": self.deliverables,
            "requirements": self.requirements,
            "revisions": self.revisions,
            "exclusivity": self.exclusivity,
            "confidentiality": self.confidentiality,
        }


@dataclass
class Mandate:
    """Complete mandate record"""
    mandate_id: str
    provider: str
    renter: str
    terms: MandateTerms
    status: MandateStatus = MandateStatus.DRAFT
    escrow_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    accepted_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    extended_deadline: Optional[str] = None
    revision_count: int = 0
    deliverable_hash: Optional[str] = None
    renter_rating: Optional[int] = None
    provider_rating: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mandate_id": self.mandate_id,
            "provider": self.provider,
            "renter": self.renter,
            "terms": self.terms.to_dict(),
            "status": self.status.value,
            "escrow_id": self.escrow_id,
            "created_at": self.created_at,
            "accepted_at": self.accepted_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "deadline": self.deadline,
            "extended_deadline": self.extended_deadline,
            "revision_count": self.revision_count,
            "deliverable_hash": self.deliverable_hash,
            "renter_rating": self.renter_rating,
            "provider_rating": self.provider_rating,
        }


class MandateSkill:
    """
    Skill for managing rental agreements between providers and renters.
    
    Features:
    - Create mandates with detailed terms
    - Accept/decline mandates
    - Track progress and deadlines
    - Manage revisions
    - Complete with deliverables
    """
    
    def __init__(self):
        self._mandates: Dict[str, Mandate] = {}
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock mandates"""
        terms = MandateTerms(
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverables=["5 images", "1024x1024", "PNG"],
            requirements=["High quality", "Original content"],
        )
        
        mandate = Mandate(
            mandate_id="mandate-demo-1",
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            terms=terms,
            status=MandateStatus.ACCEPTED,
            accepted_at=datetime.utcnow().isoformat(),
            started_at=datetime.utcnow().isoformat(),
            deadline=(datetime.utcnow() + timedelta(hours=24)).isoformat(),
        )
        self._mandates[mandate.mandate_id] = mandate
    
    # ============ CRUD Operations ============
    
    def create_mandate(
        self,
        provider: str,
        renter: str,
        skill_id: str,
        amount: int,
        duration_hours: int,
        deliverables: List[str],
        requirements: List[str] = None,
        revisions: int = 0,
        exclusivity: bool = False,
        confidentiality: bool = True,
    ) -> Mandate:
        """
        Create a new mandate (rental agreement).
        
        Args:
            provider: Provider wallet address
            renter: Renter wallet address
            skill_id: Skill being rented
            amount: USDC amount
            duration_hours: Max duration
            deliverables: List of expected deliverables
            requirements: Additional requirements
            revisions: Number of free revisions
            exclusivity: Exclusive use during mandate
            confidentiality: Confidential work
            
        Returns:
            Created Mandate
        """
        mandate_id = f"mandate-{uuid.uuid4().hex[:12]}"
        
        terms = MandateTerms(
            skill_id=skill_id,
            amount=amount,
            duration_hours=duration_hours,
            deliverables=deliverables,
            requirements=requirements or [],
            revisions=revisions,
            exclusivity=exclusivity,
            confidentiality=confidentiality,
        )
        
        deadline = datetime.utcnow() + timedelta(hours=duration_hours)
        
        mandate = Mandate(
            mandate_id=mandate_id,
            provider=provider,
            renter=renter,
            terms=terms,
            status=MandateStatus.DRAFT,
            deadline=deadline.isoformat(),
        )
        
        self._mandates[mandate_id] = mandate
        return mandate
    
    def get_mandate(self, mandate_id: str) -> Optional[Mandate]:
        """Get mandate by ID"""
        return self._mandates.get(mandate_id)
    
    def get_mandates_by_participant(
        self,
        address: str,
        status: Optional[MandateStatus] = None,
    ) -> List[Mandate]:
        """Get all mandates for a participant"""
        mandates = [
            m for m in self._mandates.values()
            if m.provider == address or m.renter == address
        ]
        
        if status:
            mandates = [m for m in mandates if m.status == status]
        
        return sorted(mandates, key=lambda m: m.created_at, reverse=True)
    
    # ============ Lifecycle Operations ============
    
    def submit_mandate(self, mandate_id: str) -> Mandate:
        """
        Submit mandate for provider acceptance.
        
        Args:
            mandate_id: Mandate to submit
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.DRAFT:
            raise MandateError(f"Mandate {mandate_id} is not in DRAFT state")
        
        mandate.status = MandateStatus.PENDING
        return mandate
    
    def accept_mandate(self, mandate_id: str) -> Mandate:
        """
        Accept a pending mandate (provider).
        
        Args:
            mandate_id: Mandate to accept
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.PENDING:
            raise MandateError(f"Mandate {mandate_id} is not in PENDING state")
        
        mandate.status = MandateStatus.ACCEPTED
        mandate.accepted_at = datetime.utcnow().isoformat()
        
        # Auto-start if escrow is funded
        if mandate.escrow_id:
            mandate.status = MandateStatus.ACTIVE
            mandate.started_at = datetime.utcnow().isoformat()
        
        return mandate
    
    def decline_mandate(self, mandate_id: str, reason: str = None) -> Mandate:
        """
        Decline a pending mandate (provider).
        
        Args:
            mandate_id: Mandate to decline
            reason: Decline reason
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.PENDING:
            raise MandateError(f"Mandate {mandate_id} is not in PENDING state")
        
        mandate.status = MandateStatus.CANCELLED
        return mandate
    
    def start_mandate(self, mandate_id: str) -> Mandate:
        """
        Start work on an accepted mandate.
        
        Args:
            mandate_id: Mandate to start
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.ACCEPTED:
            raise MandateError(f"Mandate {mandate_id} is not in ACCEPTED state")
        
        mandate.status = MandateStatus.ACTIVE
        mandate.started_at = datetime.utcnow().isoformat()
        
        return mandate
    
    def request_revision(
        self,
        mandate_id: str,
        notes: str,
    ) -> Mandate:
        """
        Request a revision (renter).
        
        Args:
            mandate_id: Mandate to revise
            notes: Revision notes
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.ACTIVE:
            raise MandateError(f"Mandate {mandate_id} is not in ACTIVE state")
        
        if mandate.revision_count >= mandate.terms.revisions:
            raise MandateError(
                f"Mandate {mandate_id} has exceeded revision limit"
            )
        
        mandate.revision_count += 1
        return mandate
    
    def complete_mandate(
        self,
        mandate_id: str,
        deliverable_hash: str,
    ) -> Mandate:
        """
        Mark mandate as complete (provider).
        
        Args:
            mandate_id: Mandate to complete
            deliverable_hash: SHA256 hash of deliverables
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.ACTIVE:
            raise MandateError(f"Mandate {mandate_id} is not in ACTIVE state")
        
        mandate.status = MandateStatus.COMPLETED
        mandate.completed_at = datetime.utcnow().isoformat()
        mandate.deliverable_hash = deliverable_hash
        
        return mandate
    
    def extend_deadline(
        self,
        mandate_id: str,
        additional_hours: int,
    ) -> Mandate:
        """
        Request deadline extension.
        
        Args:
            mandate_id: Mandate to extend
            additional_hours: Hours to add
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status not in [MandateStatus.ACTIVE, MandateStatus.ACCEPTED]:
            raise MandateError(
                f"Mandate {mandate_id} cannot be extended from {mandate.status.value} state"
            )
        
        current_deadline = datetime.fromisoformat(mandate.deadline)
        new_deadline = current_deadline + timedelta(hours=additional_hours)
        
        mandate.deadline = new_deadline.isoformat()
        mandate.extended_deadline = new_deadline.isoformat()
        mandate.status = MandateStatus.EXTENDED
        
        return mandate
    
    def cancel_mandate(self, mandate_id: str) -> Mandate:
        """
        Cancel a mandate.
        
        Args:
            mandate_id: Mandate to cancel
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status not in [MandateStatus.DRAFT, MandateStatus.PENDING]:
            raise MandateError(
                f"Mandate {mandate_id} can only be cancelled from DRAFT or PENDING state"
            )
        
        mandate.status = MandateStatus.CANCELLED
        return mandate
    
    # ============ Rating Operations ============
    
    def rate_mandate(
        self,
        mandate_id: str,
        renter_rating: int = None,
        provider_rating: int = None,
    ) -> Mandate:
        """
        Rate a completed mandate.
        
        Args:
            mandate_id: Completed mandate
            renter_rating: Rating for renter (1-5)
            provider_rating: Rating for provider (1-5)
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        
        if mandate.status != MandateStatus.COMPLETED:
            raise MandateError(f"Mandate {mandate_id} is not COMPLETED")
        
        if renter_rating:
            if not 1 <= renter_rating <= 5:
                raise MandateError("Rating must be 1-5")
            mandate.renter_rating = renter_rating
        
        if provider_rating:
            if not 1 <= provider_rating <= 5:
                raise MandateError("Rating must be 1-5")
            mandate.provider_rating = provider_rating
        
        return mandate
    
    # ============ Escrow Integration ============
    
    def link_escrow(self, mandate_id: str, escrow_id: str) -> Mandate:
        """
        Link an escrow to a mandate.
        
        Args:
            mandate_id: Mandate to link
            escrow_id: Escrow ID
            
        Returns:
            Updated Mandate
        """
        mandate = self._get_mandate(mandate_id)
        mandate.escrow_id = escrow_id
        
        # Auto-start if escrow is funded
        if mandate.status == MandateStatus.ACCEPTED:
            mandate.status = MandateStatus.ACTIVE
            mandate.started_at = datetime.utcnow().isoformat()
        
        return mandate
    
    # ============ Helpers ============
    
    def _get_mandate(self, mandate_id: str) -> Mandate:
        """Get mandate or raise error"""
        if mandate_id not in self._mandates:
            raise MandateError(f"Mandate {mandate_id} not found")
        return self._mandates[mandate_id]
    
    def export_mandates_json(self, address: str = None) -> str:
        """Export mandates as JSON"""
        if address:
            mandates = self.get_mandates_by_participant(address)
        else:
            mandates = list(self._mandates.values())
        
        return json.dumps(
            [m.to_dict() for m in mandates],
            indent=2,
        )


def get_mandate_skill() -> MandateSkill:
    """
    Get a MandateSkill instance.
    
    Returns:
        Configured MandateSkill
    """
    return MandateSkill()
