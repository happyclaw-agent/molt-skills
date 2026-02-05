"""
Mandate Skill Wrapper for TrustyClaw

This module provides Python functions for the Mandate OpenClaw skill.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MandateStatus(Enum):
    """Status of a mandate"""
    PENDING = "pending"
    FUNDED = "funded"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class MandateTerms:
    """Terms of a skill rental mandate"""
    skill_name: str
    provider: str
    renter: str
    price_usdc: int  # microUSDC
    duration_seconds: int
    metadata_uri: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class Mandate:
    """A skill rental mandate"""
    id: str
    terms: MandateTerms
    escrow_address: str = ""
    status: MandateStatus = MandateStatus.PENDING
    tx_signature: str = ""
    completed_at: str = ""


# ============ Devnet Wallets ============
# Configured for Solana Devnet testing
# Fund these at: https://faucet.circle.com/

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
    "image-generation": {
        "name": "Image Generation",
        "provider": "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        "wallet": "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        "price_usdc": 10000,
        "description": "Generate images from text prompts using SDXL",
        "capabilities": ["text-to-image", "style-transfer", "inpainting"],
    },
    "code-review": {
        "name": "Code Review", 
        "provider": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "wallet": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "price_usdc": 50000,
        "description": "Automated code review with security checks",
        "capabilities": ["security-scan", "bug-detection", "style-check"],
    },
    "data-analysis": {
        "name": "Data Analysis",
        "provider": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "wallet": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "price_usdc": 20000,
        "description": "Statistical analysis and visualization",
        "capabilities": ["regression", "clustering", "charts"],
    },
}


class MandateService:
    """Service for creating and managing mandates"""
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        self._mandates: dict[str, Mandate] = {}
    
    def create_terms(
        self,
        skill_name: str,
        provider: str,
        renter: str,
        price_usdc: int,
        duration_seconds: int = 3600,
        metadata_uri: str = "",
    ) -> MandateTerms:
        """Create mandate terms"""
        return MandateTerms(
            skill_name=skill_name,
            provider=provider,
            renter=renter,
            price_usdc=price_usdc,
            duration_seconds=duration_seconds,
            metadata_uri=metadata_uri,
        )
    
    def create_mandate(self, terms: MandateTerms) -> Mandate:
        """Create a new mandate"""
        import uuid
        mandate_id = f"mandate-{uuid.uuid4().hex[:8]}"
        
        mandate = Mandate(
            id=mandate_id,
            terms=terms,
            status=MandateStatus.PENDING,
        )
        
        self._mandates[mandate_id] = mandate
        return mandate
    
    def get_mandate(self, mandate_id: str) -> Optional[Mandate]:
        """Get a mandate by ID"""
        return self._mandates.get(mandate_id)
    
    def list_mandates(self, status: Optional[MandateStatus] = None) -> list[Mandate]:
        """List all mandates, optionally filtered by status"""
        mandates = list(self._mandates.values())
        if status:
            mandates = [m for m in mandates if m.status == status]
        return mandates
    
    def format_terms(self, terms: MandateTerms) -> str:
        """Format mandate terms for display"""
        price_usd = terms.price_usdc / 1_000_000
        duration_min = terms.duration_seconds // 60
        
        return f"""
**Mandate Terms**
- Skill: {terms.skill_name}
- Provider: @{terms.provider}
- Renter: @{terms.renter}
- Price: ${price_usd:.2f} USDC ({terms.price_usdc:,} microUSDC)
- Duration: {duration_min} minutes
- Created: {terms.created_at}
""".strip()
    
    def format_mandate(self, mandate: Mandate) -> str:
        """Format mandate for display"""
        status_emoji = {
            MandateStatus.PENDING: "⏳",
            MandateStatus.FUNDED: "💰",
            MandateStatus.COMPLETED: "✅",
            MandateStatus.CANCELLED: "❌",
        }
        
        price_usd = mandate.terms.price_usdc / 1_000_000
        
        return f"""
{status_emoji.get(mandate.status, '')} **Mandate #{mandate.id}**

{self.format_terms(mandate.terms)}

- Status: {mandate.status.value}
- Escrow: {mandate.escrow_address or 'Not created'}
- TX: {mandate.tx_signature or 'Pending'}
""".strip()


# ============ CLI ============

def demo():
    """Demo the mandate service"""
    service = MandateService(mock=True)
    
    # Create terms
    terms = service.create_terms(
        skill_name="image-generation",
        provider="agent-alpha",
        renter="happyclaw-agent",
        price_usdc=10000,  # 0.01 USDC
        duration_seconds=3600,
    )
    
    print(service.format_terms(terms))
    
    # Create mandate
    mandate = service.create_mandate(terms)
    print("\n" + service.format_mandate(mandate))
    
    # Update status
    mandate.status = MandateStatus.FUNDED
    mandate.escrow_address = "escrow-7nYHz..."
    print("\n" + service.format_mandate(mandate))


if __name__ == "__main__":
    demo()
