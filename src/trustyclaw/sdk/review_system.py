"""
Review System for TrustyClaw

Full review lifecycle: create, dispute, resolve, and aggregation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import uuid
import hashlib
import json


class ReviewStatus(Enum):
    """Review lifecycle status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    DISPUTED = "disputed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class DisputeResolution(Enum):
    """How a dispute was resolved"""
    APPROVED = "approved"  # Review stands
    REJECTED = "rejected"  # Review removed
    MODIFIED = "modified"  # Rating adjusted
    ESCALATED = "escalated"  # Sent to arbitration


@dataclass
class Review:
    """A complete review with full lifecycle tracking"""
    review_id: str
    provider: str
    renter: str
    skill_id: str
    rating: int  # 1-5
    completed_on_time: bool
    output_quality: str  # "excellent", "good", "fair", "poor"
    comment: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: ReviewStatus = ReviewStatus.PENDING
    dispute_reason: Optional[str] = None
    dispute_resolved_at: Optional[str] = None
    resolution: Optional[DisputeResolution] = None
    dispute_comments: List[str] = field(default_factory=list)
    helpful_votes: int = 0
    unhelpful_votes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "review_id": self.review_id,
            "provider": self.provider,
            "renter": self.renter,
            "skill_id": self.skill_id,
            "rating": self.rating,
            "completed_on_time": self.completed_on_time,
            "output_quality": self.output_quality,
            "comment": self.comment,
            "created_at": self.created_at,
            "status": self.status.value,
            "dispute_reason": self.dispute_reason,
            "dispute_resolved_at": self.dispute_resolved_at,
            "resolution": self.resolution.value if self.resolution else None,
            "dispute_comments": self.dispute_comments,
            "helpful_votes": self.helpful_votes,
            "unhelpful_votes": self.unhelpful_votes,
        }


@dataclass
class ReviewDispute:
    """A dispute filed against a review"""
    dispute_id: str
    review_id: str
    filed_by: str
    reason: str
    evidence: List[str]  # Links to evidence
    filed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False
    resolution: Optional[DisputeResolution] = None
    resolver_comments: Optional[str] = None
    resolved_at: Optional[str] = None


@dataclass
class ReviewVote:
    """A vote on whether a review is helpful"""
    vote_id: str
    review_id: str
    voter: str
    helpful: bool
    voted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ReviewService:
    """
    Complete review management service.
    
    Provides:
    - Review creation and submission
    - Dispute filing and resolution
    - Vote tracking
    - Rating aggregation
    """
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        self._reviews: Dict[str, Review] = {}
        self._disputes: Dict[str, ReviewDispute] = {}
        self._votes: Dict[str, ReviewVote] = {}
        self._review_ids_by_agent: Dict[str, List[str]] = {}
        
        if mock:
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with sample reviews"""
        # Add some mock reviews for demo
        mock_reviews = [
            Review(
                review_id="mock-review-1",
                provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
                renter="renter-1",
                skill_id="image-generation",
                rating=5,
                completed_on_time=True,
                output_quality="excellent",
                comment="Amazing work! Generated exactly what I needed.",
                status=ReviewStatus.SUBMITTED,
            ),
            Review(
                review_id="mock-review-2",
                provider="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
                renter="renter-2",
                skill_id="code-review",
                rating=4,
                completed_on_time=True,
                output_quality="good",
                comment="Good code review, found a few issues.",
                status=ReviewStatus.SUBMITTED,
            ),
        ]
        
        for review in mock_reviews:
            self._reviews[review.review_id] = review
            self._review_ids_by_agent.setdefault(review.provider, []).append(review.review_id)
    
    # ============ Review Operations ============
    
    def create_review(
        self,
        provider: str,
        renter: str,
        skill_id: str,
        rating: int,
        completed_on_time: bool,
        output_quality: str,
        comment: str,
    ) -> Review:
        """
        Create a new review (not yet submitted).
        
        Args:
            provider: Provider's wallet address
            renter: Renter's wallet address
            skill_id: Skill that was rented
            rating: Rating (1-5)
            completed_on_time: Whether task was on time
            output_quality: Quality assessment
            comment: Review comment
            
        Returns:
            Created Review
        """
        review_id = f"review-{uuid.uuid4().hex[:8]}"
        
        review = Review(
            review_id=review_id,
            provider=provider,
            renter=renter,
            skill_id=skill_id,
            rating=rating,
            completed_on_time=completed_on_time,
            output_quality=output_quality,
            comment=comment,
            status=ReviewStatus.PENDING,
        )
        
        self._reviews[review_id] = review
        return review
    
    def submit_review(self, review_id: str) -> Review:
        """
        Submit a pending review.
        
        Args:
            review_id: Review to submit
            
        Returns:
            Updated Review
        """
        if review_id not in self._reviews:
            raise ValueError(f"Review {review_id} not found")
        
        review = self._reviews[review_id]
        review.status = ReviewStatus.SUBMITTED
        
        # Add to agent's review list
        self._review_ids_by_agent.setdefault(review.provider, []).append(review_id)
        
        return review
    
    def get_review(self, review_id: str) -> Optional[Review]:
        """Get a review by ID"""
        return self._reviews.get(review_id)
    
    def get_agent_reviews(
        self,
        agent_address: str,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
    ) -> List[Review]:
        """
        Get all reviews for an agent.
        
        Args:
            agent_address: Agent's wallet address
            status: Filter by status
            limit: Max reviews to return
            
        Returns:
            List of reviews
        """
        review_ids = self._review_ids_by_agent.get(agent_address, [])
        
        reviews = []
        for rid in review_ids:
            review = self._reviews.get(rid)
            if review:
                if status is None or review.status == status:
                    reviews.append(review)
        
        return sorted(reviews, key=lambda r: r.created_at, reverse=True)[:limit]
    
    # ============ Dispute Operations ============
    
    def file_dispute(
        self,
        review_id: str,
        filed_by: str,
        reason: str,
        evidence: List[str] = None,
    ) -> ReviewDispute:
        """
        File a dispute against a review.
        
        Args:
            review_id: Review to dispute
            filed_by: Who is filing (provider or renter)
            reason: Why the review is being disputed
            evidence: Links to evidence
            
        Returns:
            Created Dispute
        """
        if review_id not in self._reviews:
            raise ValueError(f"Review {review_id} not found")
        
        review = self._reviews[review_id]
        
        if review.status != ReviewStatus.SUBMITTED:
            raise ValueError("Can only dispute submitted reviews")
        
        dispute = ReviewDispute(
            dispute_id=f"dispute-{uuid.uuid4().hex[:8]}",
            review_id=review_id,
            filed_by=filed_by,
            reason=reason,
            evidence=evidence or [],
        )
        
        self._disputes[dispute.dispute_id] = dispute
        
        # Update review status
        review.status = ReviewStatus.DISPUTED
        review.dispute_reason = reason
        
        return dispute
    
    def resolve_dispute(
        self,
        dispute_id: str,
        resolution: DisputeResolution,
        resolver_comments: str = None,
    ) -> Review:
        """
        Resolve a dispute.
        
        Args:
            dispute_id: Dispute to resolve
            resolution: How it was resolved
            resolver_comments: Notes on resolution
            
        Returns:
            Updated Review
        """
        if dispute_id not in self._disputes:
            raise ValueError(f"Dispute {dispute_id} not found")
        
        dispute = self._disputes[dispute_id]
        
        if dispute.resolved:
            raise ValueError("Dispute already resolved")
        
        dispute.resolved = True
        dispute.resolution = resolution
        dispute.resolver_comments = resolver_comments
        dispute.resolved_at = datetime.utcnow().isoformat()
        
        # Update review
        review = self._reviews[dispute.review_id]
        review.status = ReviewStatus.RESOLVED
        review.resolution = resolution
        review.dispute_resolved_at = dispute.resolved_at
        review.dispute_comments.append(resolver_comments or "")
        
        return review
    
    def get_dispute(self, dispute_id: str) -> Optional[ReviewDispute]:
        """Get a dispute by ID"""
        return self._disputes.get(dispute_id)
    
    def get_review_disputes(self, review_id: str) -> List[ReviewDispute]:
        """Get all disputes for a review"""
        return [
            d for d in self._disputes.values()
            if d.review_id == review_id
        ]
    
    # ============ Voting Operations ============
    
    def vote_review(
        self,
        review_id: str,
        voter: str,
        helpful: bool,
    ) -> ReviewVote:
        """
        Vote on whether a review is helpful.
        
        Args:
            review_id: Review to vote on
            voter: Who is voting
            helpful: Is the review helpful
            
        Returns:
            Created Vote
        """
        if review_id not in self._reviews:
            raise ValueError(f"Review {review_id} not found")
        
        vote = ReviewVote(
            vote_id=f"vote-{uuid.uuid4().hex[:8]}",
            review_id=review_id,
            voter=voter,
            helpful=helpful,
        )
        
        self._votes[vote.vote_id] = vote
        
        # Update review vote counts
        review = self._reviews[review_id]
        if helpful:
            review.helpful_votes += 1
        else:
            review.unhelpful_votes += 1
        
        return vote
    
    def get_review_votes(self, review_id: str) -> Dict[str, int]:
        """Get vote summary for a review"""
        votes = [v for v in self._votes.values() if v.review_id == review_id]
        
        helpful = sum(1 for v in votes if v.helpful)
        unhelpful = sum(1 for v in votes if not v.helpful)
        
        return {"helpful": helpful, "unhelpful": unhelpful}
    
    # ============ Aggregation Operations ============
    
    def calculate_agent_rating(
        self,
        agent_address: str,
        min_reviews: int = 1,
    ) -> Dict[str, Any]:
        """
        Calculate aggregated rating for an agent.
        
        Args:
            agent_address: Agent's wallet address
            min_reviews: Minimum reviews needed
            
        Returns:
            Rating summary dict
        """
        reviews = self.get_agent_reviews(
            agent_address,
            status=ReviewStatus.SUBMITTED,
        )
        
        if len(reviews) < min_reviews:
            return {
                "agent": agent_address,
                "total_reviews": len(reviews),
                "average_rating": 0,
                "on_time_rate": 0,
                "quality_breakdown": {},
                "rating": "insufficient_reviews",
            }
        
        # Calculate averages
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        on_time_rate = sum(1 for r in reviews if r.completed_on_time) / len(reviews) * 100
        
        # Quality breakdown
        quality_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for r in reviews:
            quality_counts[r.output_quality] = quality_counts.get(r.output_quality, 0) + 1
        
        # Calculate helpful rate
        total_votes = sum(r.helpful_votes + r.unhelpful_votes for r in reviews)
        helpful_rate = 0
        if total_votes > 0:
            helpful_votes = sum(r.helpful_votes for r in reviews)
            helpful_rate = helpful_votes / total_votes * 100
        
        # Determine rating tier
        if avg_rating >= 4.5:
            rating = "excellent"
        elif avg_rating >= 3.5:
            rating = "good"
        elif avg_rating >= 2.5:
            rating = "average"
        else:
            rating = "needs_work"
        
        return {
            "agent": agent_address,
            "total_reviews": len(reviews),
            "average_rating": round(avg_rating, 2),
            "on_time_rate": round(on_time_rate, 1),
            "helpful_rate": round(helpful_rate, 1),
            "quality_breakdown": quality_counts,
            "rating": rating,
        }
    
    def get_top_agents(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top agents by rating.
        
        Args:
            n: Number of agents to return
            
        Returns:
            List of agent rating summaries
        """
        all_providers = set()
        for review in self._reviews.values():
            all_providers.add(review.provider)
        
        agents = []
        for provider in all_providers:
            rating = self.calculate_agent_rating(provider)
            agents.append(rating)
        
        # Sort by average rating
        sorted_agents = sorted(
            agents,
            key=lambda a: a["average_rating"],
            reverse=True,
        )
        
        return sorted_agents[:n]
    
    def export_reviews_json(self, agent_address: str = None) -> str:
        """
        Export reviews as JSON.
        
        Args:
            agent_address: Filter by agent (None = all)
            
        Returns:
            JSON string
        """
        if agent_address:
            reviews = self.get_agent_reviews(agent_address)
        else:
            reviews = list(self._reviews.values())
        
        return json.dumps(
            [r.to_dict() for r in reviews],
            indent=2,
        )


def get_review_service(mock: bool = True) -> ReviewService:
    """
    Get a ReviewService instance.
    
    Args:
        mock: Use mock data
        
    Returns:
        Configured ReviewService
    """
    return ReviewService(mock=mock)
