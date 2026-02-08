"""
Tests for Escrow Contract (simplified)
"""

import pytest


class TestEscrowTerms:
    """Tests for EscrowTerms dataclass"""
    
    def test_creation(self):
        """Test creating escrow terms"""
        from trustyclaw.sdk.escrow_contract import EscrowTerms
        
        terms = EscrowTerms(
            skill_name="image-generation",
            duration_seconds=86400,
            price_usdc=1000000,
            metadata_uri="https://example.com/metadata.json",
        )
        
        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 1000000


class TestEscrowClient:
    """Tests for EscrowClient class"""
    
    def test_initialization(self):
        """Test client initialization"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient()
        assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
