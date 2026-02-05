"""
Discovery Skill Wrapper for ClawTrust

This module provides Python functions for the Discovery OpenClaw skill.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Skill:
    """A skill offered by an agent"""
    id: str
    name: str
    provider: str
    wallet: str
    price_usdc: int
    description: str
    capabilities: list[str]
    reputation_score: float = 85.0
    available: bool = True
    
    @property
    def price_usd(self) -> float:
        """Price in USDC (not micro)"""
        return self.price_usdc / 1_000_000


# ============ Devnet Wallets ============
# Configured for Solana Devnet testing

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

# ============ Demo Skills ============

DEMO_SKILLS = {
    "image-generation": Skill(
        id="image-generation",
        name="Image Generation",
        provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        wallet="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        price_usdc=10000,
        description="Generate images from text prompts using SDXL",
        capabilities=["text-to-image", "style-transfer", "inpainting"],
        reputation_score=85.0,
    ),
    "code-review": Skill(
        id="code-review",
        name="Code Review",
        provider="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        wallet="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        price_usdc=50000,
        description="Automated code review with security checks",
        capabilities=["security-scan", "bug-detection", "style-check"],
        reputation_score=88.0,
    ),
    "data-analysis": Skill(
        id="data-analysis",
        name="Data Analysis",
        provider="agent-beta",
        wallet="agent-beta.sol",
        price_usdc=20000,
        description="Statistical analysis and visualization",
        capabilities=["regression", "clustering", "charts"],
        reputation_score=91.0,
    ),
}


class DiscoveryService:
    """Service for discovering and browsing skills"""
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        self._skills = DEMO_SKILLS.copy()
    
    def list_skills(
        self,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_reputation: Optional[float] = None,
        capabilities: Optional[list[str]] = None,
        available_only: bool = True,
    ) -> list[Skill]:
        """List skills with optional filters"""
        skills = list(self._skills.values())
        
        if available_only:
            skills = [s for s in skills if s.available]
        
        if min_price is not None:
            skills = [s for s in skills if s.price_usdc >= min_price]
        
        if max_price is not None:
            skills = [s for s in skills if s.price_usdc <= max_price]
        
        if min_reputation is not None:
            skills = [s for s in skills if s.reputation_score >= min_reputation]
        
        if capabilities:
            skills = [
                s for s in skills
                if any(cap in s.capabilities for cap in capabilities)
            ]
        
        return skills
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID"""
        return self._skills.get(skill_id)
    
    def search_skills(self, query: str) -> list[Skill]:
        """Search skills by name or description"""
        query = query.lower()
        return [
            s for s in self._skills.values()
            if query in s.name.lower() or query in s.description.lower()
        ]
    
    def get_provider_skills(self, provider: str) -> list[Skill]:
        """Get all skills from a specific provider"""
        return [
            s for s in self._skills.values()
            if s.provider.lower() == provider.lower()
        ]
    
    def format_skill(self, skill: Skill, index: int = 0) -> str:
        """Format a skill for display"""
        price_usd = skill.price_usdc / 1_000_000
        rep_bar = "⭐" * int(skill.reputation_score // 20)
        
        return f"""
📦 **{skill.name}** (#{index + 1})
   Provider: @{skill.provider}
   Price: ${price_usd:.2f} USDC
   Reputation: {rep_bar} {skill.reputation_score:.0f}/100
   Description: {skill.description}
   Capabilities: {", ".join(skill.capabilities)}
""".strip()
    
    def format_skill_list(self, skills: list[Skill]) -> str:
        """Format a list of skills for display"""
        if not skills:
            return "No skills found matching your criteria."
        
        lines = [f"Found {len(skills)} skill(s):\n"]
        for i, skill in enumerate(skills):
            lines.append(self.format_skill(skill, i))
            lines.append("")
        
        return "\n".join(lines).strip()
    
    def get_recommendations(
        self,
        budget_usdc: float = 0.10,
        top_n: int = 3,
    ) -> list[Skill]:
        """Get top recommendations within budget"""
        skills = self.list_skills(max_price=int(budget_usdc * 1_000_000))
        skills.sort(key=lambda s: s.reputation_score, reverse=True)
        return skills[:top_n]


# ============ CLI ============

def demo():
    """Demo the discovery service"""
    service = DiscoveryService(mock=True)
    
    # List all
    print("All Skills:")
    print(service.format_skill_list(service.list_skills()))
    
    # Filter by price
    print("\n\nUnder $0.03:")
    under_30 = service.list_skills(max_price=30000)
    print(service.format_skill_list(under_30))
    
    # Search
    print("\n\nSearch 'code':")
    results = service.search_skills("code")
    print(service.format_skill_list(results))
    
    # Recommendations
    print("\n\nTop picks under $0.10:")
    recs = service.get_recommendations(budget_usdc=0.10)
    print(service.format_skill_list(recs))


if __name__ == "__main__":
    demo()
