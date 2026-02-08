"""
Tests for Reputation Skill (simplified)
"""

import pytest


class TestReputationMetrics:
    """Tests for ReputationMetrics dataclass"""
    
    def test_creation(self):
        """Test creating reputation metrics"""
        from trustyclaw.skills.reputation import ReputationMetrics
        
        metrics = ReputationMetrics(
            agent_address="addr",
            reputation_score=85.0,
            average_rating=4.5,
            total_reviews=100,
        )
        
        assert metrics.agent_address == "addr"
        assert metrics.reputation_score == 85.0
    
    def test_to_dict(self):
        """Test serialization"""
        from trustyclaw.skills.reputation import ReputationMetrics
        
        metrics = ReputationMetrics(
            agent_address="a",
            reputation_score=80.0,
            average_rating=4.0,
            total_reviews=50,
        )
        
        data = metrics.to_dict()
        
        assert data["agent_address"] == "a"


class TestReputationSkill:
    """Tests for ReputationSkill class"""
    
    def test_initialization(self):
        """Test skill initialization"""
        from trustyclaw.skills.reputation import ReputationSkill
        
        skill = ReputationSkill()
        assert skill is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
