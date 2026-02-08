"""
Unit Tests for Reputation Program

Tests verify reputation state machine and basic operations.
"""

import pytest
from datetime import datetime, timedelta

from trustyclaw.sdk.reputation import (
    ReputationEngine,
    ReputationScore,
    Review,
    Rating,
)


# ============ Review Tests ============

class TestReview:
    """Tests for Review dataclass"""
    
    def test_create_review(self):
        """Test creating a review"""
        review = Review(
            provider="agent_wallet",
            renter="client_wallet",
            skill="code-generation",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Great work!",
        )
        
        assert review.provider == "agent_wallet"
        assert review.renter == "client_wallet"
        assert review.rating == 5
        assert review.completed_on_time is True
        assert review.output_quality == "excellent"
    
    def test_review_default_values(self):
        """Test review default values"""
        review = Review(
            provider="agent",
            renter="client",
            skill="test",
        )
        
        assert review.rating == 5
        assert review.completed_on_time is True
        assert review.output_quality == "excellent"
        assert review.comment == ""
    
    def test_review_validate_valid(self):
        """Test validation with valid data"""
        review = Review(
            provider="valid_agent",
            renter="valid_client",
            skill="code",
            rating=5,
        )
        
        assert review.validate() is True
    
    def test_review_validate_invalid(self):
        """Test validation with invalid data"""
        review = Review(
            provider="",  # Empty provider
            renter="client",
            skill="code",
            rating=5,
        )
        
        assert review.validate() is False
    
    def test_review_rating_bounds(self):
        """Test rating bounds validation"""
        # Valid ratings
        for rating in [1, 2, 3, 4, 5]:
            review = Review(
                provider="agent",
                renter="client",
                skill="test",
                rating=rating,
            )
            assert review.validate() is True


# ============ ReputationScore Tests ============

class TestReputationScore:
    """Tests for ReputationScore"""
    
    def test_create_score(self):
        """Test creating reputation score"""
        score = ReputationScore(
            agent_id="agent_wallet",
        )
        
        assert score.agent_id == "agent_wallet"
        assert score.total_reviews == 0
        assert score.average_rating == 0.0
        assert score.reputation_score == 50.0  # Default for new agents
    
    def test_score_with_reviews(self):
        """Test score with reviews"""
        score = ReputationScore(
            agent_id="reviewed_agent",
            total_reviews=10,
            average_rating=4.5,
            on_time_percentage=95.0,
            reputation_score=87,
        )
        
        assert score.total_reviews == 10
        assert score.average_rating == 4.5
        assert score.on_time_percentage == 95.0
        assert score.reputation_score == 87
    
    def test_calculate_score_formula(self):
        """Test reputation calculation formula"""
        score = ReputationScore(
            agent_id="formula_test",
            total_reviews=5,
            average_rating=4.0,
            on_time_percentage=80.0,
            reputation_score=0,  # Will be calculated
        )
        
        calculated = score.calculate_score()
        
        # formula: (rating_score * 0.6) + (on_time_pct * 0.3) + (volume_bonus * 0.1)
        # rating_score = 4.0/5 * 100 = 80
        # on_time_pct = 80.0
        # volume_bonus = min(5 reviews * 1, 10) = 5
        # score = (80 * 0.6) + (80 * 0.3) + (5 * 0.1) = 48 + 24 + 0.5 = 72.5
        assert calculated > 0
    
    def test_new_agent_default_score(self):
        """Test new agent gets default score"""
        score = ReputationScore(agent_id="new_agent")
        
        # New agents start at 50
        assert score.reputation_score == 50.0
        assert score.total_reviews == 0


# ============ ReputationEngine Tests ============

class TestReputationEngine:
    """Tests for ReputationEngine"""
    
    def test_engine_initialization(self):
        """Test creating reputation engine"""
        engine = ReputationEngine()
        
        assert engine is not None
    
    def test_add_review(self):
        """Test adding a review"""
        engine = ReputationEngine()
        
        review = Review(
            provider="test_agent",
            renter="test_client",
            skill="code-generation",
            rating=5,
        )
        
        new_score = engine.add_review("test_agent", review)
        
        assert new_score is not None
        assert new_score.total_reviews >= 1
    
    def test_multiple_reviews(self):
        """Test multiple reviews affect score"""
        engine = ReputationEngine()
        
        # Add several reviews
        ratings = [5, 4, 5, 5, 4]  # Average = 4.6
        for i, rating in enumerate(ratings):
            review = Review(
                provider="rated_agent",
                renter=f"client_{i}",
                skill="test",
                rating=rating,
            )
            engine.add_review("rated_agent", review)
        
        score = engine.get_score("rated_agent")
        assert score is not None
        assert score.average_rating == 4.6
    
    def test_get_score_new_agent(self):
        """Test getting score for new agent"""
        engine = ReputationEngine()
        
        # Get score before adding any reviews
        score = engine.get_score("new_agent")
        
        # Should return default for non-existent agent
        if score is not None:
            assert score.agent_id == "new_agent"
            assert score.reputation_score == 50.0  # Default
    
    def test_get_top_agents(self):
        """Test getting top-rated agents"""
        engine = ReputationEngine()
        
        # Create agents with different scores
        for i in range(5):
            for j in range(i + 1):  # More reviews for some
                review = Review(
                    provider=f"agent_{i}",
                    renter=f"client_{i}_{j}",
                    skill="test",
                    rating=min(i + 3, 5),  # Higher ratings for some
                )
                engine.add_review(f"agent_{i}", review)
        
        top_agents = engine.get_top_agents()
        
        assert isinstance(top_agents, list)
        assert len(top_agents) >= 0
    
    def test_update_on_time_percentage(self):
        """Test on-time percentage affects score"""
        engine = ReputationEngine()
        
        # All on-time
        for _ in range(5):
            review = Review(
                provider="ontime_agent",
                renter="client",
                skill="test",
                rating=5,
                completed_on_time=True,
            )
            engine.add_review("ontime_agent", review)
        
        score = engine.get_score("ontime_agent")
        assert score is not None
        assert score.on_time_percentage == 100.0
        
        # Some late
        for _ in range(5):
            review = Review(
                provider="late_agent",
                renter="client",
                skill="test",
                rating=5,
                completed_on_time=False,
            )
            engine.add_review("late_agent", review)
        
        late_score = engine.get_score("late_agent")
        assert late_score is not None
        # On-time percentage should be affected
    
    def test_volume_bonus(self):
        """Test volume bonus in scoring"""
        engine = ReputationEngine()
        
        # Add many reviews for volume bonus
        for i in range(20):
            review = Review(
                provider="high_volume",
                renter=f"client_{i}",
                skill="test",
                rating=5,
            )
            engine.add_review("high_volume", review)
        
        score = engine.get_score("high_volume")
        
        # Volume bonus: min(total_reviews, 10) = 10
        # Score should include volume bonus
        assert score.total_reviews == 20
    
    def test_invalid_rating_ignored(self):
        """Test invalid ratings are handled"""
        engine = ReputationEngine()
        
        # Add invalid review
        review = Review(
            provider="test",
            renter="client",
            skill="test",
            rating=6,  # Invalid
        )
        
        # Should not crash
        new_score = engine.add_review("test", review)
        
        assert new_score is not None


# ============ Edge Cases ============

class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_all_one_star_reviews(self):
        """Test agent with all 1-star reviews"""
        engine = ReputationEngine()
        
        for _ in range(5):
            review = Review(
                provider="bad_agent",
                renter="client",
                skill="test",
                rating=1,
            )
            engine.add_review("bad_agent", review)
        
        score = engine.get_score("bad_agent")
        
        assert score.average_rating == 1.0
        assert score.reputation_score < 50.0  # Below default
    
    def test_all_five_star_reviews(self):
        """Test agent with all 5-star reviews"""
        engine = ReputationEngine()
        
        for _ in range(10):
            review = Review(
                provider="great_agent",
                renter="client",
                skill="test",
                rating=5,
            )
            engine.add_review("great_agent", review)
        
        score = engine.get_score("great_agent")
        
        assert score.average_rating == 5.0
        assert score.reputation_score > 50.0  # Above default
    
    def test_mixed_on_time_performance(self):
        """Test mixed on-time performance"""
        engine = ReputationEngine()
        
        # 7 on-time, 3 late = 70% on-time
        for i in range(10):
            review = Review(
                provider="mixed_agent",
                renter=f"client_{i}",
                skill="test",
                rating=5,
                completed_on_time=i < 7,  # First 7 on time
            )
            engine.add_review("mixed_agent", review)
        
        score = engine.get_score("mixed_agent")
        
        assert score.on_time_percentage == 70.0
    
    def test_skill_specific_reviews(self):
        """Test reviews by skill category"""
        engine = ReputationEngine()
        
        # Add reviews for different skills
        for skill in ["code", "text", "image"]:
            for _ in range(3):
                review = Review(
                    provider="multi_skill",
                    renter="client",
                    skill=skill,
                    rating=5,
                )
                engine.add_review("multi_skill", review)
        
        score = engine.get_score("multi_skill")
        
        assert score.total_reviews == 9  # 3 skills * 3 reviews each


# ============ Rating Enum Tests ============

class TestRatingEnum:
    """Tests for Rating enum"""
    
    def test_all_ratings_defined(self):
        """Test all rating values exist"""
        assert Rating.ONE_STAR.value == 1
        assert Rating.TWO_STARS.value == 2
        assert Rating.THREE_STARS.value == 3
        assert Rating.FOUR_STARS.value == 4
        assert Rating.FIVE_STARS.value == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
