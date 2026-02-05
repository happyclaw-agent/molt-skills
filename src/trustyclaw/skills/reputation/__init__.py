"""
Reputation Skill for TrustyClaw

On-chain reputation queries and aggregation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import json


class ReputationTier(Enum):
    """Reputation tiers"""
    ELITE = "elite"      # 90+
    TRUSTED = "trusted"  # 75-89
    VERIFIED = "verified"  # 50-74
    NEW = "new"          # 25-49
    UNKNOWN = "unknown"   # 0-24


@dataclass
class ReputationMetrics:
    """Complete reputation metrics for an agent"""
    agent_address: str
    reputation_score: float = 50.0
    average_rating: float = 0.0
    total_reviews: int = 0
    on_time_percentage: float = 100.0
    completed_tasks: int = 0
    positive_reviews: int = 0
    negative_reviews: int = 0
    average_response_time_hours: float = 24.0
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address,
            "reputation_score": self.reputation_score,
            "average_rating": self.average_rating,
            "total_reviews": self.total_reviews,
            "on_time_percentage": self.on_time_percentage,
            "completed_tasks": self.completed_tasks,
            "positive_reviews": self.positive_reviews,
            "negative_reviews": self.negative_reviews,
            "average_response_time_hours": self.average_response_time_hours,
            "last_updated": self.last_updated,
        }


@dataclass
class ReputationBreakdown:
    """Breakdown of reputation by category"""
    agent_address: str
    quality_score: float = 50.0
    reliability_score: float = 50.0
    communication_score: float = 50.0
    value_score: float = 50.0
    overall_score: float = 50.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address,
            "quality_score": self.quality_score,
            "reliability_score": self.reliability_score,
            "communication_score": self.communication_score,
            "value_score": self.value_score,
            "overall_score": self.overall_score,
        }


@dataclass
class ReputationHistory:
    """Historical reputation data point"""
    timestamp: str
    reputation_score: float
    average_rating: float
    total_reviews: int


class ReputationSkill:
    """
    Skill for querying and analyzing on-chain reputation.
    
    Features:
    - Query agent reputation from PDAs
    - Get review history
    - Calculate composite trust scores
    - Track reputation trends
    - Verify reputation claims
    """
    
    def __init__(self):
        self._reputations: Dict[str, ReputationMetrics] = {}
        self._breakdowns: Dict[str, ReputationBreakdown] = {}
        self._history: Dict[str, List[ReputationHistory]] = {}
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with sample reputation data"""
        # Sample agents with varying reputations
        agents = [
            ("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q", 92.5, 4.8, 150, 95.0, 200),
            ("HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B", 87.3, 4.6, 300, 92.0, 450),
            ("3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN", 65.0, 3.8, 80, 85.0, 95),
        ]
        
        for addr, score, rating, reviews, on_time, completed in agents:
            metrics = ReputationMetrics(
                agent_address=addr,
                reputation_score=score,
                average_rating=rating,
                total_reviews=reviews,
                on_time_percentage=on_time,
                completed_tasks=completed,
                positive_reviews=int(reviews * 0.85),
                negative_reviews=int(reviews * 0.15),
                last_updated=datetime.utcnow().isoformat(),
            )
            self._reputations[addr] = metrics
            
            # Create breakdown
            breakdown = ReputationBreakdown(
                agent_address=addr,
                quality_score=score * 0.9,
                reliability_score=on_time,
                communication_score=score * 0.85,
                value_score=score * 0.95,
                overall_score=score,
            )
            self._breakdowns[addr] = breakdown
            
            # Create history
            history = []
            for i in range(12):  # 12 months
                history.append(ReputationHistory(
                    timestamp=(datetime.utcnow() - 
                              __import__('datetime').timedelta(days=i * 30)).isoformat(),
                    reputation_score=score - (i * 0.5),
                    average_rating=rating - (i * 0.02),
                    total_reviews=reviews - (i * 10),
                ))
            self._history[addr] = history
    
    # ============ Query Operations ============
    
    def get_agent_reputation(self, agent_address: str) -> Optional[ReputationMetrics]:
        """
        Get complete reputation metrics for an agent.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationMetrics or None
        """
        return self._reputations.get(agent_address)
    
    def get_reputation_breakdown(self, agent_address: str) -> Optional[ReputationBreakdown]:
        """
        Get detailed reputation breakdown by category.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationBreakdown or None
        """
        return self._breakdowns.get(agent_address)
    
    def get_reputation_score(self, agent_address: str) -> Optional[float]:
        """
        Get simple reputation score (0-100).
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Score or None
        """
        rep = self._reputations.get(agent_address)
        return rep.reputation_score if rep else None
    
    def get_average_rating(self, agent_address: str) -> Optional[float]:
        """
        Get agent's average rating (1-5).
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Rating or None
        """
        rep = self._reputations.get(agent_address)
        return rep.average_rating if rep else None
    
    def get_on_time_rate(self, agent_address: str) -> Optional[float]:
        """
        Get agent's on-time completion rate.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Percentage or None
        """
        rep = self._reputations.get(agent_address)
        return rep.on_time_percentage if rep else None
    
    # ============ Tier Operations ============
    
    def get_reputation_tier(self, agent_address: str) -> str:
        """
        Get agent's reputation tier.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Tier name
        """
        score = self.get_reputation_score(agent_address)
        
        if score is None:
            return ReputationTier.UNKNOWN.value
        elif score >= 90:
            return ReputationTier.ELITE.value
        elif score >= 75:
            return ReputationTier.TRUSTED.value
        elif score >= 50:
            return ReputationTier.VERIFIED.value
        elif score >= 25:
            return ReputationTier.NEW.value
        else:
            return ReputationTier.UNKNOWN.value
    
    def get_top_reputed_agents(self, limit: int = 10) -> List[ReputationMetrics]:
        """
        Get agents with highest reputation.
        
        Args:
            limit: Max results
            
        Returns:
            List of top agents
        """
        sorted_reps = sorted(
            self._reputations.values(),
            key=lambda r: r.reputation_score,
            reverse=True,
        )
        return sorted_reps[:limit]
    
    # ============ Trust Score ============
    
    def calculate_trust_score(
        self,
        agent_address: str,
        weights: Dict[str, float] = None,
    ) -> Optional[float]:
        """
        Calculate composite trust score.
        
        Args:
            agent_address: Agent's wallet address
            weights: Custom weights for calculation
            
        Returns:
            Trust score (0-100)
        """
        rep = self._reputations.get(agent_address)
        if not rep:
            return None
        
        # Default weights
        if weights is None:
            weights = {
                "rating": 0.35,
                "on_time": 0.25,
                "volume": 0.20,
                "positivity": 0.20,
            }
        
        # Normalize metrics
        rating_norm = rep.average_rating / 5.0  # 0-1
        on_time_norm = rep.on_time_percentage / 100.0  # 0-1
        
        # Volume bonus (diminishing returns)
        volume_norm = min(rep.completed_tasks / 100.0, 1.0)
        
        # Positivity ratio
        total = rep.positive_reviews + rep.negative_reviews
        positivity = rep.positive_reviews / total if total > 0 else 0.5
        
        # Calculate weighted score
        trust = (
            rating_norm * weights["rating"] +
            on_time_norm * weights["on_time"] +
            volume_norm * weights["volume"] +
            positivity * weights["positivity"]
        ) * 100
        
        return round(trust, 1)
    
    # ============ Review History ============
    
    def get_review_history(
        self,
        agent_address: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get agent's review history.
        
        Args:
            agent_address: Agent's wallet address
            limit: Max reviews
            
        Returns:
            List of review data
        """
        rep = self._reputations.get(agent_address)
        if not rep:
            return []
        
        # Generate mock reviews based on metrics
        reviews = []
        for i in range(min(limit, rep.total_reviews)):
            reviews.append({
                "review_id": f"review-{i}",
                "rating": rep.average_rating + (0.5 - (i % 10) * 0.1),
                "comment": "Great agent!" if i % 3 == 0 else "Good work.",
                "on_time": i % 5 != 0,
                "timestamp": f"2025-{11 - (i % 12):02d}-{(i % 28) + 1:02d}",
            })
        
        return reviews[:limit]
    
    def get_reputation_history(
        self,
        agent_address: str,
        months: int = 12,
    ) -> List[ReputationHistory]:
        """
        Get historical reputation data.
        
        Args:
            agent_address: Agent's wallet address
            months: Number of months of history
            
        Returns:
            List of historical data points
        """
        return self._history.get(agent_address, [])[:months]
    
    # ============ Verification ============
    
    def verify_reputation_claim(
        self,
        agent_address: str,
        claimed_score: float,
        tolerance: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Verify an agent's claimed reputation score.
        
        Args:
            agent_address: Agent's wallet address
            claimed_score: Score claimed by agent
            tolerance: Acceptable variance
            
        Returns:
            Verification result
        """
        actual_score = self.get_reputation_score(agent_address)
        
        if actual_score is None:
            return {
                "verified": False,
                "reason": "No reputation data found",
                "actual_score": None,
            }
        
        diff = abs(actual_score - claimed_score)
        
        return {
            "verified": diff <= tolerance,
            "claimed_score": claimed_score,
            "actual_score": actual_score,
            "difference": diff,
            "within_tolerance": diff <= tolerance,
        }
    
    def compare_agents(
        self,
        agent_a: str,
        agent_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two agents' reputations.
        
        Args:
            agent_a: First agent
            agent_b: Second agent
            
        Returns:
            Comparison result
        """
        rep_a = self._reputations.get(agent_a)
        rep_b = self._reputations.get(agent_b)
        
        if not rep_a or not rep_b:
            return {"error": "One or both agents not found"}
        
        return {
            "agent_a": agent_a,
            "agent_b": agent_b,
            "comparison": {
                "reputation_score": {
                    "a": rep_a.reputation_score,
                    "b": rep_b.reputation_score,
                    "winner": agent_a if rep_a.reputation_score > rep_b.reputation_score else agent_b,
                },
                "average_rating": {
                    "a": rep_a.average_rating,
                    "b": rep_b.average_rating,
                    "winner": agent_a if rep_a.average_rating > rep_b.average_rating else agent_b,
                },
                "on_time_rate": {
                    "a": rep_a.on_time_percentage,
                    "b": rep_b.on_time_percentage,
                    "winner": agent_a if rep_a.on_time_percentage > rep_b.on_time_percentage else agent_b,
                },
                "completed_tasks": {
                    "a": rep_a.completed_tasks,
                    "b": rep_b.completed_tasks,
                    "winner": agent_a if rep_a.completed_tasks > rep_b.completed_tasks else agent_b,
                },
            },
        }
    
    # ============ Statistics ============
    
    def get_reputation_stats(self) -> Dict[str, Any]:
        """Get overall reputation statistics"""
        reps = list(self._reputations.values())
        
        if not reps:
            return {
                "total_agents": 0,
                "avg_score": 0,
                "avg_rating": 0,
            }
        
        return {
            "total_agents": len(reps),
            "avg_score": sum(r.reputation_score for r in reps) / len(reps),
            "avg_rating": sum(r.average_rating for r in reps) / len(reps),
            "avg_on_time": sum(r.on_time_percentage for r in reps) / len(reps),
            "elite_count": len([r for r in reps if r.reputation_score >= 90]),
            "trusted_count": len([r for r in reps if r.reputation_score >= 75]),
            "new_count": len([r for r in reps if r.reputation_score < 50]),
        }
    
    # ============ Export ============
    
    def export_reputation_json(self, agent_address: str = None) -> str:
        """Export reputation data as JSON"""
        if agent_address:
            rep = self._reputations.get(agent_address)
            data = [rep.to_dict()] if rep else []
        else:
            data = [r.to_dict() for r in self._reputations.values()]
        
        return json.dumps(data, indent=2)


def get_reputation_skill() -> ReputationSkill:
    """
    Get a ReputationSkill instance.
    
    Returns:
        Configured ReputationSkill
    """
    return ReputationSkill()
