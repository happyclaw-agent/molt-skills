"""
Tests for Discovery Skill (simplified)
"""

import pytest


class TestSkill:
    """Tests for Skill dataclass"""
    
    def test_creation(self):
        """Test creating a skill"""
        from trustyclaw.skills.discovery import Skill
        
        skill = Skill(
            skill_id="test",
            agent_address="addr",
            name="Test Skill",
            category="code-generation",
            description="A test skill",
            price_per_task=1000000,
            estimated_duration_hours=2,
        )
        
        assert skill.skill_id == "test"
        assert skill.rating == 0.0
        assert skill.review_count == 0
    
    def test_to_dict(self):
        """Test serialization"""
        from trustyclaw.skills.discovery import Skill
        
        skill = Skill(
            skill_id="s",
            agent_address="a",
            name="n",
            category="c",
            description="d",
            price_per_task=100,
            estimated_duration_hours=1,
        )
        
        data = skill.to_dict()
        
        assert data["skill_id"] == "s"


class TestAgent:
    """Tests for Agent dataclass"""
    
    def test_creation(self):
        """Test creating an agent"""
        from trustyclaw.skills.discovery import Agent
        
        agent = Agent(
            address="test-addr",
            name="TestAgent",
            bio="Test bio",
            skills=[],
            rating=4.5,
            total_reviews=100,
            completed_tasks=150,
            status="available",
            languages=["English"],
        )
        
        assert agent.address == "test-addr"
        assert agent.rating == 4.5


class TestDiscoverySkill:
    """Tests for DiscoverySkill class"""
    
    def test_initialization(self):
        """Test skill initialization"""
        from trustyclaw.skills.discovery import DiscoverySkill
        
        skill = DiscoverySkill()
        assert skill is not None
        assert hasattr(skill, '_agents')
        assert hasattr(skill, '_skills')
    
    def test_search(self):
        """Test basic search"""
        from trustyclaw.skills.discovery import DiscoverySkill
        
        skill = DiscoverySkill()
        results = skill.search_agents(query="test")
        assert isinstance(results, list)


class TestSearchFilters:
    """Tests for SearchFilters dataclass"""
    
    def test_default_values(self):
        """Test default filter values"""
        from trustyclaw.skills.discovery import SearchFilters
        
        filters = SearchFilters()
        
        assert filters.category is None
        assert filters.min_rating == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
