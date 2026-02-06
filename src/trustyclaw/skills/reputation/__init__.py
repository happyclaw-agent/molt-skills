"""
Reputation Skill for TrustyClaw

On-chain reputation queries and aggregation.
Connects to real Solana reputation program.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from trustyclaw.sdk.reputation_chain import (
    get_reputation_chain,
    ReputationChainSDK,
    ReputationScoreData,
    ReviewData,
    ReputationError,
)


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
    on_chain_data: Optional[ReputationScoreData] = None
    
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
    
    @classmethod
    def from_on_chain(cls, data: ReputationScoreData) -> 'ReputationMetrics':
        """Create from on-chain data"""
        return cls(
            agent_address=data.agent_address,
            reputation_score=data.reputation_score,
            average_rating=data.average_rating,
            total_reviews=data.total_reviews,
            on_time_percentage=data.on_time_percentage,
            positive_reviews=data.positive_votes,
            negative_reviews=data.negative_votes,
            last_updated=datetime.fromtimestamp(data.updated_at).isoformat() if data.updated_at > 0 else None,
            on_chain_data=data,
        )


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
    - Query agent reputation from on-chain PDAs
    - Get review history from real data
    - Calculate composite trust scores
    - Track reputation trends
    - Verify reputation claims
    
    Note: No mock fallbacks - all data comes from on-chain or returns None
    """
    
    def __init__(self, network: str = "devnet"):
        """
        Initialize the reputation skill.
        
        Args:
            network: Solana network (devnet, mainnet)
        """
        self.network = network
        self._sdk: Optional[ReputationChainSDK] = None
        self._cache: Dict[str, Tuple[ReputationMetrics, float]] = {}
        self._cache_ttl = 30  # 30 seconds cache
    
    @property
    def sdk(self) -> ReputationChainSDK:
        """Get or create the reputation SDK"""
        if self._sdk is None:
            self._sdk = get_reputation_chain(self.network)
        return self._sdk
    
    def _get_cached_or_fetch(self, agent_address: str) -> Optional[ReputationMetrics]:
        """
        Get from cache or fetch from chain.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationMetrics or None
        """
        now = time.time()
        
        # Check cache
        if agent_address in self._cache:
            metrics, timestamp = self._cache[agent_address]
            if now - timestamp < self._cache_ttl:
                return metrics
        
        # Fetch from chain
        try:
            on_chain_data = self.sdk.get_reputation(agent_address)
            if on_chain_data:
                metrics = ReputationMetrics.from_on_chain(on_chain_data)
                self._cache[agent_address] = (metrics, now)
                return metrics
        except ReputationError:
            pass
        
        # Not found - don't cache negative result
        return None
    
    # ============ Query Operations ============
    
    def get_agent_reputation(self, agent_address: str) -> Optional[ReputationMetrics]:
        """
        Get complete reputation metrics for an agent from on-chain.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationMetrics or None if not found
        """
        return self._get_cached_or_fetch(agent_address)
    
    def get_reputation_breakdown(self, agent_address: str) -> Optional[ReputationBreakdown]:
        """
        Get detailed reputation breakdown by category.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationBreakdown or None if not found
        """
        metrics = self._get_cached_or_fetch(agent_address)
        if not metrics:
            return None
        
        # Calculate breakdown from metrics
        return ReputationBreakdown(
            agent_address=agent_address,
            quality_score=metrics.average_rating * 20,  # Scale 1-5 to 0-100
            reliability_score=metrics.on_time_percentage,
            communication_score=metrics.reputation_score * 0.9,
            value_score=metrics.reputation_score * 0.95,
            overall_score=metrics.reputation_score,
        )
    
    def get_reputation_score(self, agent_address: str) -> Optional[float]:
        """
        Get simple reputation score (0-100).
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Score or None if not found
        """
        metrics = self._get_cached_or_fetch(agent_address)
        return metrics.reputation_score if metrics else None
    
    def get_average_rating(self, agent_address: str) -> Optional[float]:
        """
        Get agent's average rating (1-5).
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Rating or None if not found
        """
        metrics = self._get_cached_or_fetch(agent_address)
        return metrics.average_rating if metrics else None
    
    def get_on_time_rate(self, agent_address: str) -> Optional[float]:
        """
        Get agent's on-time completion rate.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Percentage or None if not found
        """
        metrics = self._get_cached_or_fetch(agent_address)
        return metrics.on_time_percentage if metrics else None
    
    # ============ Tier Operations ============
    
    def get_reputation_tier(self, agent_address: str) -> str:
        """
        Get agent's reputation tier.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Tier name (unknown if not found)
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
            List of top agents (empty if not available)
        """
        try:
            all_reps = self.sdk.get_all_reputations(limit * 2)
            if all_reps:
                metrics_list = [ReputationMetrics.from_on_chain(r) for r in all_reps]
                return sorted(metrics_list, key=lambda r: r.reputation_score, reverse=True)[:limit]
        except ReputationError:
            pass
        
        return []
    
    # ============ Review Operations ============
    
    def get_agent_reviews(
        self,
        agent_address: str,
        limit: int = 10,
    ) -> List[ReviewData]:
        """
        Get reviews for an agent from on-chain.
        
        Args:
            agent_address: Agent's wallet address
            limit: Max reviews to return
            
        Returns:
            List of ReviewData (empty if not available)
        """
        # In production, this would fetch from on-chain review accounts
        # For now, return empty list
        return []
    
    def get_review(self, review_id: str) -> Optional[ReviewData]:
        """
        Get a specific review.
        
        Args:
            review_id: Review ID
            
        Returns:
            ReviewData or None
        """
        try:
            return self.sdk.get_review(review_id)
        except ReputationError:
            return None
    
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
            Trust score (0-100) or None if not found
        """
        metrics = self._get_cached_or_fetch(agent_address)
        if not metrics:
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
        rating_norm = metrics.average_rating / 5.0  # 0-1
        on_time_norm = metrics.on_time_percentage / 100.0  # 0-1
        
        # Volume bonus (diminishing returns)
        volume_norm = min(metrics.total_reviews / 100.0, 1.0)
        
        # Positivity ratio
        total = metrics.positive_reviews + metrics.negative_reviews
        positivity = metrics.positive_reviews / total if total > 0 else 0.5
        
        # Calculate weighted score
        trust = (
            rating_norm * weights["rating"] +
            on_time_norm * weights["on_time"] +
            volume_norm * weights["volume"] +
            positivity * weights["positivity"]
        ) * 100
        
        return round(trust, 1)
    
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
            Verification result dict
        """
        actual_score = self.get_reputation_score(agent_address)
        
        if actual_score is None:
            return {
                "verified": False,
                "reason": "No reputation data found on-chain",
                "actual_score": None,
                "claimed_score": claimed_score,
            }
        
        diff = abs(actual_score - claimed_score)
        
        return {
            "verified": diff <= tolerance,
            "claimed_score": claimed_score,
            "actual_score": actual_score,
            "difference": round(diff, 2),
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
            Comparison result dict
        """
        rep_a = self._get_cached_or_fetch(agent_a)
        rep_b = self._get_cached_or_fetch(agent_b)
        
        if not rep_a or not rep_b:
            missing = []
            if not rep_a:
                missing.append(agent_a)
            if not rep_b:
                missing.append(agent_b)
            return {
                "error": f"No on-chain data for: {', '.join(missing)}",
                "agent_a_found": rep_a is not None,
                "agent_b_found": rep_b is not None,
            }
        
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
                    "a": rep_a.total_reviews,
                    "b": rep_b.total_reviews,
                    "winner": agent_a if rep_a.total_reviews > rep_b.total_reviews else agent_b,
                },
            },
        }
    
    # ============ Statistics ============
    
    def get_reputation_stats(self) -> Dict[str, Any]:
        """Get overall reputation statistics (from on-chain)"""
        # In production, this would aggregate from all reputation accounts
        return {
            "total_agents": 0,
            "avg_score": 0.0,
            "avg_rating": 0.0,
            "message": "Full stats require indexed on-chain data",
        }
    
    # ============ Cache Management ============
    
    def clear_cache(self, agent_address: str = None):
        """
        Clear the reputation cache.
        
        Args:
            agent_address: Specific agent to clear, or None for all
        """
        if agent_address:
            self._cache.pop(agent_address, None)
        else:
            self._cache.clear()
    
    def refresh_reputation(self, agent_address: str) -> Optional[ReputationMetrics]:
        """
        Force refresh reputation from chain.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Fresh ReputationMetrics or None
        """
        self.clear_cache(agent_address)
        return self._get_cached_or_fetch(agent_address)
    
    # ============ Export ============
    
    def export_reputation_json(self, agent_address: str = None) -> str:
        """Export reputation data as JSON"""
        if agent_address:
            rep = self._get_cached_or_fetch(agent_address)
            data = [rep.to_dict()] if rep else []
        else:
            data = [m.to_dict() for m in self._cache.values()]
        
        return json.dumps(data, indent=2)


def get_reputation_skill(network: str = "devnet") -> ReputationSkill:
    """
    Get a ReputationSkill instance.
    
    Args:
        network: Network name (devnet, mainnet)
        
    Returns:
        Configured ReputationSkill
    """
    return ReputationSkill(network)
