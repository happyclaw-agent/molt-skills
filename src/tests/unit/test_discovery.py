"""
Tests for Discovery Skill
"""

import pytest


class TestSkill:
    """Tests for Skill dataclass"""
    
    def test_creation(self):
        """Test creating a skill"""
        from src.trustyclaw.skills.discovery import Skill
        
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
        from src.trustyclaw.skills.discovery import Skill
        
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
        assert data["price_per_task"] == 100


class TestAgent:
    """Tests for Agent dataclass"""
    
    def test_creation(self):
        """Test creating an agent"""
        from src.trustyclaw.skills.discovery import Agent
        
        agent = Agent(
            address="addr",
            name="Test Agent",
            bio="A test agent",
        )
        
        assert agent.address == "addr"
        assert agent.rating == 0.0
        assert len(agent.skills) == 0
    
    def test_to_dict(self):
        """Test serialization"""
        from src.trustyclaw.skills.discovery import Agent
        
        agent = Agent(
            address="a",
            name="n",
            bio="b",
        )
        
        data = agent.to_dict()
        
        assert data["address"] == "a"
        assert data["name"] == "n"


class TestDiscoverySkill:
    """Tests for DiscoverySkill"""
    
    @pytest.fixture
    def skill(self):
        """Create a fresh skill with mock data"""
        from src.trustyclaw.skills.discovery import DiscoverySkill
        return DiscoverySkill(mock=True)
    
    def test_browse_skills(self, skill):
        """Test browsing all skills"""
        skills = skill.browse_skills()
        
        assert len(skills) >= 1
        assert all(hasattr(s, 'skill_id') for s in skills)
    
    def test_browse_skills_by_category(self, skill):
        """Test browsing by category"""
        skills = skill.browse_skills(category="image-generation")
        
        assert len(skills) >= 1
        for s in skills:
            assert s.category == "image-generation"
    
    def test_get_skill_categories(self, skill):
        """Test getting categories with counts"""
        categories = skill.get_skill_categories()
        
        assert len(categories) >= 1
        for cat in categories:
            assert "category" in cat
            assert "skill_count" in cat
    
    def test_search_agents_by_query(self, skill):
        """Test searching agents by query"""
        agents = skill.search_agents(query="code")
        
        assert len(agents) >= 1
        for a in agents:
            assert "code" in a.name.lower() or "code" in a.bio.lower()
    
    def test_search_agents_by_filters(self, skill):
        """Test filtering agents"""
        from src.trustyclaw.skills.discovery import SearchFilters
        
        filters = SearchFilters(
            min_rating=4.5,
            availability="available",
        )
        
        agents = skill.search_agents(filters=filters)
        
        for a in agents:
            assert a.rating >= 4.5
            assert a.status == "available"
    
    def test_search_skills(self, skill):
        """Test searching skills"""
        skills = skill.search_skills(query="data")
        
        assert len(skills) >= 1
        for s in skills:
            assert "data" in s.name.lower() or "data" in s.description.lower()
    
    def test_search_skills_by_price(self, skill):
        """Test filtering skills by price"""
        skills = skill.search_skills(max_price=800000)
        
        for s in skills:
            assert s.price_per_task <= 800000
    
    def test_get_agent_profile(self, skill):
        """Test getting agent profile"""
        profile = skill.get_agent_profile(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        assert profile is not None
        assert hasattr(profile, 'name')
    
    def test_get_agent_skills(self, skill):
        """Test getting agent's skills"""
        skills = skill.get_agent_skills(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        assert len(skills) >= 1
        for s in skills:
            assert s.agent_address == "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
    
    def test_get_agent_availability(self, skill):
        """Test getting agent availability"""
        avail = skill.get_agent_availability(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        assert "status" in avail
        assert "available" in avail["status"] or "busy" in avail["status"]
    
    def test_get_top_rated_agents(self, skill):
        """Test getting top rated agents"""
        top = skill.get_top_rated_agents(limit=5)
        
        assert len(top) <= 5
        for i in range(len(top) - 1):
            assert top[i].rating >= top[i + 1].rating
    
    def test_get_top_rated_skills(self, skill):
        """Test getting top rated skills"""
        top = skill.get_top_rated_skills(limit=5)
        
        assert len(top) <= 5
        for i in range(len(top) - 1):
            assert top[i].rating >= top[i + 1].rating
    
    def test_get_most_active_agents(self, skill):
        """Test getting most active agents"""
        active = skill.get_most_active_agents(limit=5)
        
        assert len(active) <= 5
        for i in range(len(active) - 1):
            assert active[i].completed_tasks >= active[i + 1].completed_tasks
    
    def test_get_trending_skills(self, skill):
        """Test getting trending skills"""
        trending = skill.get_trending_skills(limit=5)
        
        assert len(trending) <= 5
    
    def test_get_recommended_agents(self, skill):
        """Test getting recommendations"""
        recs = skill.get_recommended_agents(
            {"categories": ["code-generation"]},
            limit=5,
        )
        
        # Some should have matching skills
        if len(recs) > 0:
            for r in recs:
                has_match = any(
                    s.category == "code-generation" for s in r.skills
                )
                assert has_match or r.rating > 4.0
    
    def test_get_similar_agents(self, skill):
        """Test getting similar agents"""
        similar = skill.get_similar_agents(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            limit=5,
        )
        
        # Should not include the original
        for a in similar:
            assert a.address != "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
    
    def test_get_marketplace_stats(self, skill):
        """Test marketplace statistics"""
        stats = skill.get_marketplace_stats()
        
        assert "total_agents" in stats
        assert "total_skills" in stats
        assert "avg_agent_rating" in stats
        assert "total_completed_tasks" in stats
        assert stats["total_agents"] >= 1
        assert stats["total_skills"] >= 1
    
    def test_export_agents_json(self, skill):
        """Test exporting agents as JSON"""
        json_str = skill.export_agents_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_export_skills_json(self, skill):
        """Test exporting skills as JSON"""
        json_str = skill.export_skills_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) >= 1


class TestSearchFilters:
    """Tests for SearchFilters dataclass"""
    
    def test_default_values(self):
        """Test default filter values"""
        from src.trustyclaw.skills.discovery import SearchFilters
        
        filters = SearchFilters()
        
        assert filters.category is None
        assert filters.min_rating == 0.0
        assert filters.sort_by == "rating"
    
    def test_custom_values(self):
        """Test custom filter values"""
        from src.trustyclaw.skills.discovery import SearchFilters
        
        filters = SearchFilters(
            category="image-generation",
            min_rating=4.0,
            max_price=1000000,
            sort_by="price",
        )
        
        assert filters.category == "image-generation"
        assert filters.min_rating == 4.0
        assert filters.max_price == 1000000
        assert filters.sort_by == "price"


class TestGetDiscoverySkill:
    """Tests for get_discovery_skill function"""
    
    def test_get_skill_mock(self):
        """Test getting skill with mock data"""
        from src.trustyclaw.skills.discovery import get_discovery_skill
        
        skill = get_discovery_skill(mock=True)
        assert skill.mock is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
