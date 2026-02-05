"""
Tests for Reputation Skill
"""

import pytest


class TestReputationMetrics:
    """Tests for ReputationMetrics dataclass"""
    
    def test_creation(self):
        """Test creating reputation metrics"""
        from src.trustyclaw.skills.reputation import ReputationMetrics
        
        metrics = ReputationMetrics(
            agent_address="addr",
            reputation_score=85.0,
            average_rating=4.5,
            total_reviews=100,
            on_time_percentage=90.0,
            completed_tasks=120,
        )
        
        assert metrics.agent_address == "addr"
        assert metrics.reputation_score == 85.0
        assert metrics.positive_reviews == 0  # default
    
    def test_to_dict(self):
        """Test serialization"""
        from src.trustyclaw.skills.reputation import ReputationMetrics
        
        metrics = ReputationMetrics(
            agent_address="a",
            reputation_score=80.0,
            average_rating=4.0,
            total_reviews=50,
        )
        
        data = metrics.to_dict()
        
        assert data["agent_address"] == "a"
        assert data["reputation_score"] == 80.0


class TestReputationBreakdown:
    """Tests for ReputationBreakdown dataclass"""
    
    def test_creation(self):
        """Test creating breakdown"""
        from src.trustyclaw.skills.reputation import ReputationBreakdown
        
        breakdown = ReputationBreakdown(
            agent_address="addr",
            quality_score=90.0,
            reliability_score=85.0,
            communication_score=80.0,
            value_score=88.0,
            overall_score=85.0,
        )
        
        assert breakdown.quality_score == 90.0
        assert breakdown.overall_score == 85.0


class TestReputationSkill:
    """Tests for ReputationSkill"""
    
    @pytest.fixture
    def skill(self):
        """Create a fresh skill with mock data"""
        from src.trustyclaw.skills.reputation import ReputationSkill
        return ReputationSkill(mock=True)
    
    def test_get_agent_reputation(self, skill):
        """Test getting agent reputation"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        rep = skill.get_agent_reputation(addr)
        
        assert rep is not None
        assert rep.agent_address == addr
        assert rep.reputation_score > 0
    
    def test_get_reputation_breakdown(self, skill):
        """Test getting breakdown"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        bd = skill.get_reputation_breakdown(addr)
        
        assert bd is not None
        assert "quality_score" in bd.to_dict()
    
    def test_get_reputation_score(self, skill):
        """Test getting simple score"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        score = skill.get_reputation_score(addr)
        
        assert score is not None
        assert 0 <= score <= 100
    
    def test_get_average_rating(self, skill):
        """Test getting average rating"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        rating = skill.get_average_rating(addr)
        
        assert rating is not None
        assert 0 <= rating <= 5
    
    def test_get_on_time_rate(self, skill):
        """Test getting on-time rate"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        rate = skill.get_on_time_rate(addr)
        
        assert rate is not None
        assert 0 <= rate <= 100
    
    def test_get_reputation_tier_elite(self, skill):
        """Test elite tier detection"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        tier = skill.get_reputation_tier(addr)
        
        assert tier == "elite"
    
    def test_get_reputation_tier_trusted(self, skill):
        """Test trusted tier detection"""
        addr = "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B"
        tier = skill.get_reputation_tier(addr)
        
        assert tier == "trusted"
    
    def test_get_reputation_tier_unknown(self, skill):
        """Test unknown tier for missing agent"""
        tier = skill.get_reputation_tier("unknown-addr")
        
        assert tier == "unknown"
    
    def test_get_top_reputed_agents(self, skill):
        """Test getting top agents"""
        top = skill.get_top_reputed_agents(limit=5)
        
        assert len(top) <= 5
        for i in range(len(top) - 1):
            assert top[i].reputation_score >= top[i + 1].reputation_score
    
    def test_calculate_trust_score_default(self, skill):
        """Test trust score calculation with defaults"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        trust = skill.calculate_trust_score(addr)
        
        assert trust is not None
        assert 0 <= trust <= 100
    
    def test_calculate_trust_score_custom_weights(self, skill):
        """Test trust score with custom weights"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        trust = skill.calculate_trust_score(
            addr,
            weights={"rating": 1.0, "on_time": 0.0, "volume": 0.0, "positivity": 0.0}
        )
        
        # Should be based purely on rating
        expected = (skill.get_average_rating(addr) / 5.0) * 100
        assert trust == expected
    
    def test_get_review_history(self, skill):
        """Test getting review history"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        reviews = skill.get_review_history(addr, limit=10)
        
        assert len(reviews) <= 10
        for r in reviews:
            assert "rating" in r
            assert "comment" in r
    
    def test_get_reputation_history(self, skill):
        """Test getting historical data"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        history = skill.get_reputation_history(addr, months=6)
        
        assert len(history) <= 6
        for h in history:
            assert hasattr(h, 'reputation_score')
            assert hasattr(h, 'average_rating')
    
    def test_verify_reputation_claim_valid(self, skill):
        """Test verifying valid claim"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        result = skill.verify_reputation_claim(addr, 92.0, tolerance=5.0)
        
        assert result["verified"] is True
        assert result["actual_score"] is not None
    
    def test_verify_reputation_claim_invalid(self, skill):
        """Test verifying invalid claim"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        result = skill.verify_reputation_claim(addr, 50.0, tolerance=5.0)
        
        assert result["verified"] is False
        assert result["difference"] > 5
    
    def test_compare_agents(self, skill):
        """Test comparing two agents"""
        result = skill.compare_agents(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        )
        
        assert "comparison" in result
        assert "reputation_score" in result["comparison"]
        assert "winner" in result["comparison"]["reputation_score"]
    
    def test_get_reputation_stats(self, skill):
        """Test getting statistics"""
        stats = skill.get_reputation_stats()
        
        assert "total_agents" in stats
        assert "avg_score" in stats
        assert "elite_count" in stats
        assert stats["total_agents"] >= 1
    
    def test_export_reputation_json(self, skill):
        """Test exporting as JSON"""
        json_str = skill.export_reputation_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) >= 1


class TestReputationTier:
    """Tests for ReputationTier enum"""
    
    def test_all_tiers_exist(self):
        """Test all expected tiers exist"""
        from src.trustyclaw.skills.reputation import ReputationTier
        
        assert ReputationTier.ELITE.value == "elite"
        assert ReputationTier.TRUSTED.value == "trusted"
        assert ReputationTier.VERIFIED.value == "verified"
        assert ReputationTier.NEW.value == "new"
        assert ReputationTier.UNKNOWN.value == "unknown"


class TestGetReputationSkill:
    """Tests for get_reputation_skill function"""
    
    def test_get_skill_mock(self):
        """Test getting skill with mock data"""
        from src.trustyclaw.skills.reputation import get_reputation_skill
        
        skill = get_reputation_skill(mock=True)
        assert skill.mock is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
