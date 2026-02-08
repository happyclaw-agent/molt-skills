"""
Tests for On-Chain Reputation Storage (simplified)
"""

import pytest


class TestReputationScoreData:
    """Tests for ReputationScoreData"""
    
    def test_creation(self):
        """Test creating score data"""
        from trustyclaw.sdk.reputation_chain import ReputationScoreData
        
        score = ReputationScoreData(
            agent_address="test-addr",
            total_reviews=25,
            average_rating=4.5,
            reputation_score=87.5,
        )
        
        assert score.agent_address == "test-addr"
        assert score.total_reviews == 25
    
    def test_defaults(self):
        """Test default values"""
        from trustyclaw.sdk.reputation_chain import ReputationScoreData
        
        score = ReputationScoreData(agent_address="test")
        
        assert score.total_reviews == 0
        assert score.average_rating == 0.0
        assert score.reputation_score == 50.0


class TestReviewData:
    """Tests for ReviewData"""
    
    def test_creation(self):
        """Test creating review data"""
        from trustyclaw.sdk.reputation_chain import ReviewData
        
        review = ReviewData(
            review_id="review-123",
            provider="test-addr",
            reviewer="reviewer-addr",
            rating=5,
            completed_on_time=True,
            comment_hash="abc123",
        )
        
        assert review.review_id == "review-123"
        assert review.rating == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
