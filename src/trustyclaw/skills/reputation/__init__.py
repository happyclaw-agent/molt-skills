"""
Reputation Skill Wrapper for TrustyClaw

Provides Python functions for the Reputation OpenClaw skill.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReputationDisplay:
    """Formatted reputation display data"""
    agent_id: str
    score: float
    reviews: int
    rating: float
    on_time: float
    recommendation: str
    
    def to_markdown(self) -> str:
        """Format as markdown for display"""
        stars = "⭐" * int(self.rating)
        
        # Recommendation based on score
        if self.score >= 90:
            rec = "Excellent - Trusted by many"
        elif self.score >= 80:
            rec = "Good - Reliable performer"
        elif self.score >= 70:
            rec = "Average - Some mixed reviews"
        else:
            rec = "Needs improvement - Be cautious"
        
        return f"""
**@{self.agent_id}** Reputation

📊 Score: {self.score:.0f}/100
   Reviews: {self.reviews}
   Rating: {stars} ({self.rating:.1f} avg)
   On-Time: {self.on_time:.0f}%

Recommendation: {rec}
""".strip()


# ============ Devnet Wallets ============

WALLETS = {
    "agent": {
        "address": "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        "name": "Happy Claw (Agent)",
    },
    "renter": {
        "address": "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
        "name": "Renter Agent",
    },
    "provider": {
        "address": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "name": "Provider Agent",
    },
}


class ReputationService:
    """Service for querying reputation"""
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        # In production, this would use the SDK
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize demo reputation data with real wallet addresses"""
        self._scores = {
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q": (85.0, 47, 4.7, 95.0),  # Happy Claw
            "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B": (88.0, 32, 4.4, 94.0),  # Provider
            "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN": (75.0, 12, 4.1, 88.0),  # Renter
        }
    
    def get_reputation(self, agent_id: str) -> Optional[ReputationDisplay]:
        """Get reputation for an agent"""
        if agent_id in self._scores:
            score, reviews, rating, on_time = self._scores[agent_id]
            return ReputationDisplay(
                agent_id=agent_id,
                score=score,
                reviews=reviews,
                rating=rating,
                on_time=on_time,
                recommendation="",
            )
        # New agent default
        return ReputationDisplay(
            agent_id=agent_id,
            score=50.0,
            reviews=0,
            rating=0.0,
            on_time=0.0,
            recommendation="New agent - no reviews yet",
        )
    
    def compare_agents(self, agent1: str, agent2: str) -> tuple[ReputationDisplay, ReputationDisplay]:
        """Compare two agents"""
        return (
            self.get_reputation(agent1),
            self.get_reputation(agent2),
        )
    
    def get_top_agents(self, n: int = 10) -> list[tuple[str, float]]:
        """Get top N agents by reputation"""
        sorted_agents = sorted(
            self._scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        return [(agent, score) for agent, score in sorted_agents[:n]]
    
    def format_reputation(self, agent_id: str) -> str:
        """Format reputation for display"""
        rep = self.get_reputation(agent_id)
        return rep.to_markdown() if rep else "Agent not found"


# ============ CLI ============

def demo():
    """Demo the reputation service"""
    service = ReputationService()
    
    print("Reputation Service Demo\n")
    
    # Get single reputation
    print("Agent: happyclaw-agent")
    print(service.format_reputation("happyclaw-agent"))
    
    print("\n" + "=" * 40 + "\n")
    
    # Compare two agents
    print("Comparing agent-alpha vs agent-beta:")
    a1, a2 = service.compare_agents("agent-alpha", "agent-beta")
    print(a1.to_markdown())
    print("\nvs\n")
    print(a2.to_markdown())
    
    print("\n" + "=" * 40 + "\n")
    
    # Top agents
    print("Top 3 Agents:")
    for agent, score in service.get_top_agents(3):
        print(f"  @{agent}: {score:.0f}/100")


if __name__ == "__main__":
    demo()
