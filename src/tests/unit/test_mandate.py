"""
Tests for Mandate Skill (simplified)
"""

import pytest


class TestMandateTerms:
    """Tests for MandateTerms dataclass"""
    
    def test_creation(self):
        """Test creating mandate terms"""
        from trustyclaw.skills.mandate import MandateTerms
        
        terms = MandateTerms(
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverables=["5 images"],
        )
        
        assert terms.skill_id == "image-generation"
        assert terms.amount == 1000000
    
    def test_to_dict(self):
        """Test serialization"""
        from trustyclaw.skills.mandate import MandateTerms
        
        terms = MandateTerms(
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        data = terms.to_dict()
        
        assert data["skill_id"] == "s"
        assert data["amount"] == 100


class TestMandateStatus:
    """Tests for MandateStatus enum"""
    
    def test_values(self):
        """Test status values"""
        from trustyclaw.skills.mandate import MandateStatus
        
        assert MandateStatus.PENDING.value == "pending"
        assert MandateStatus.ACCEPTED.value == "accepted"


class TestMandateSkill:
    """Tests for MandateSkill class"""
    
    def test_initialization(self):
        """Test skill initialization"""
        from trustyclaw.skills.mandate import MandateSkill
        
        skill = MandateSkill()
        assert skill is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
