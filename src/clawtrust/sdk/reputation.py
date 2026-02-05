"""
Reputation Engine

Purpose:
    Tracks and calculates reputation scores for ClawTrust agents.
    Scores are based on reviews, on-time delivery, and volume.
    
Capabilities:
    - Submit and aggregate reviews
    - Calculate weighted reputation scores
    - Query top-rated agents
    - Track review history
    
Scoring Formula:
    reputation = (rating_score * 0.6) + (on_time_pct * 0.3) + (volume_bonus * 0.1)
    
    - rating_score: Average rating normalized to 0-100
    - on_time_pct: Percentage of rentals completed on time
    - volume_bonus: Up to 10 points for high activity
    
Usage:
    >>> engine = ReputationEngine()
    >>> score = engine.get_score("agent-wallet")
    >>> print(f"Score: {score}")
    
    >>> # After rental
    >>> review = Review(rating=5, completed_on_time=True, ...)
    >>> new_score = engine.add_review("agent-wallet", review)
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Rating(Enum):
    """Rating values"""
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5


@dataclass
class Review:
    """
    A review from a completed rental.
    
    Attributes:
        provider: Agent being reviewed (wallet or name)
        renter: Reviewer (wallet or name)
        skill: Skill that was rented
        rating: Rating from 1-5
        completed_on_time: Whether task was on time
        output_quality: Quality assessment string
        comment: Optional review comment
    """
    provider: str
    renter: str
    skill: str
    rating: int = 5
    completed_on_time: bool = True
    output_quality: str = "excellent"
    comment: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def validate(self) -> bool:
        """
        Validate review data.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.provider:
            return False
        if not 1 <= self.rating <= 5:
            return False
        return True


@dataclass
class ReputationScore:
    """
    Reputation score for an agent.
    
    Contains all data needed to calculate and display reputation.
    """
    agent_id: str
    total_reviews: int = 0
    average_rating: float = 0.0
    on_time_percentage: float = 100.0
    reputation_score: float = 50.0  # Default for new agents
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reviews: list[Review] = field(default_factory=list)
    
    def calculate_score(self) -> float:
        """
        Calculate final reputation score.
        
        Uses weighted formula:
        - 60% from average rating
        - 30% from on-time percentage
        - 10% from volume (capped at 100 reviews)
        
        Returns:
            Calculated score (0-100)
        """
        if self.total_reviews == 0:
            self.reputation_score = 50.0
            return 50.0
        
        # Weight components
        rating_weight = 0.6
        ontime_weight = 0.3
        volume_weight = 0.1
        
        # Normalize rating (1-5 to 0-100)
        rating_score = (self.average_rating / 5.0) * 100
        
        # Volume bonus (cap at 100 reviews)
        volume_bonus = min(self.total_reviews / 100.0, 1.0) * 10
        
        # Calculate
        self.reputation_score = round(
            (rating_score * rating_weight +
             self.on_time_percentage * ontime_weight +
             volume_bonus * volume_weight),
            1
        )
        self.last_updated = datetime.utcnow().isoformat()
        
        return self.reputation_score


class ReputationEngine:
    """
    Manages reputation scores for ClawTrust agents.
    
    Provides methods to:
    - Add reviews
    - Query scores
    - Get top agents
    - Format reputation for display
    
    For MVP: In-memory storage.
    Production: On-chain storage with ZK proofs.
    
    Example:
        >>> engine = ReputationEngine()
        >>> score = engine.get_score("agent-wallet")
        >>> print(f"Score: {score}/100")
    """
    
    def __init__(self):
        """Initialize reputation engine with empty storage"""
        self._scores: dict[str, ReputationScore] = {}
        self._reviews: dict[str, list[Review]] = {}
    
    def get_score(self, agent_id: str) -> Optional[ReputationScore]:
        """
        Get reputation score for an agent.
        
        Args:
            agent_id: Agent's wallet or ID
            
        Returns:
            ReputationScore or None if not found
        """
        return self._scores.get(agent_id)
    
    def get_score_value(self, agent_id: str) -> float:
        """
        Get just the score value (0-100).
        
        Args:
            agent_id: Agent's wallet or ID
            
        Returns:
            Score (0-100), or 50 for new agents
        """
        score = self.get_score(agent_id)
        return score.reputation_score if score else 50.0
    
    def add_review(self, agent_id: str, review: Review) -> ReputationScore:
        """
        Add a review and update the agent's score.
        
        Args:
            agent_id: Agent's wallet or ID
            review: Review data
            
        Returns:
            Updated ReputationScore
        """
        # Get or create score
        if agent_id not in self._scores:
            self._scores[agent_id] = ReputationScore(agent_id=agent_id)
        
        score = self._scores[agent_id]
        
        # Add review
        if agent_id not in self._reviews:
            self._reviews[agent_id] = []
        self._reviews[agent_id].append(review)
        score.reviews.append(review)
        
        # Update counts
        score.total_reviews = len(score.reviews)
        
        # Calculate average rating
        if score.reviews:
            ratings = [r.rating for r in score.reviews]
            score.average_rating = sum(ratings) / len(ratings)
        
        # Calculate on-time percentage
        completed = [r for r in score.reviews if r.completed_on_time]
        if score.reviews:
            score.on_time_percentage = (len(completed) / len(score.reviews)) * 100
        
        # Recalculate final score
        score.calculate_score()
        
        return score
    
    def get_reviews(self, agent_id: str) -> list[Review]:
        """
        Get all reviews for an agent.
        
        Args:
            agent_id: Agent's wallet or ID
            
        Returns:
            List of reviews, newest first
        """
        reviews = self._reviews.get(agent_id, [])
        return sorted(reviews, key=lambda r: r.created_at, reverse=True)
    
    def get_top_agents(self, n: int = 10) -> list[tuple[str, float]]:
        """
        Get top N agents by reputation.
        
        Args:
            n: Number of agents to return
            
        Returns:
            List of (agent_id, score) tuples, sorted by score descending
        """
        sorted_agents = sorted(
            self._scores.items(),
            key=lambda x: x[1].reputation_score,
            reverse=True
        )
        return [(agent, score.reputation_score) for agent, score in sorted_agents[:n]]
    
    def format_score(self, agent_id: str) -> str:
        """
        Format reputation for human-readable display.
        
        Args:
            agent_id: Agent's wallet or ID
            
        Returns:
            Formatted string with score details
        """
        score = self.get_score(agent_id)
        if not score:
            return f"@{agent_id}: No reputation yet (50/100)"
        
        # Create score bar
        bar_length = 20
        filled = int(score.reputation_score / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        stars = "⭐" * int(score.average_rating)
        
        return f"""
**@{agent_id}** Reputation

{bar} {score.reputation_score}/100

📊 Stats:
   Reviews: {score.total_reviews}
   Average Rating: {score.average_rating:.1f} {stars}
   On-Time Delivery: {score.on_time_percentage:.0f}%

📝 Recent Reviews:
{self._format_recent_reviews(score)}
""".strip()
    
    def _format_recent_reviews(self, score: ReputationScore, n: int = 3) -> str:
        """Format recent reviews for display"""
        if not score.reviews:
            return "   (No reviews yet)"
        
        recent = sorted(
            score.reviews,
            key=lambda r: r.created_at,
            reverse=True
        )[:n]
        
        lines = []
        for r in recent:
            lines.append(f"   • \"{r.comment[:50]}\" - ⭐{r.rating}")
        
        return "\n".join(lines)


# ============ Factory Functions ============

def get_reputation(agent_id: str) -> float:
    """
    Get reputation score for an agent.
    
    Args:
        agent_id: Agent's wallet or ID
        
    Returns:
        Score (0-100)
    """
    engine = ReputationEngine()
    return engine.get_score_value(agent_id)


def add_review(agent_id: str, review: Review) -> float:
    """
    Add a review and return new score.
    
    Args:
        agent_id: Agent's wallet or ID
        review: Review data
        
    Returns:
        New score (0-100)
    """
    engine = ReputationEngine()
    return engine.add_review(agent_id, review).reputation_score


# ============ CLI ============

def demo():
    """Demo the reputation engine"""
    engine = ReputationEngine()
    
    # Create a review
    review = Review(
        provider="agent-alpha",
        renter="agent-beta",
        skill="image-generation",
        rating=5,
        completed_on_time=True,
        output_quality="excellent",
        comment="Amazing images! Fast delivery.",
    )
    
    engine.add_review("agent-alpha", review)
    
    # Check score
    print(engine.format_score("agent-alpha"))


if __name__ == "__main__":
    demo()
