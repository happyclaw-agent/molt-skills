"""
Unit Tests for Reputation Program
Tests verify reputation state machine and basic operations.
"""
import pytest
from trustyclaw.sdk.reputation import (
    ReputationEngine, ReputationScore, Review, Rating,
)

class TestReview:
    def test_create_review(self):
        review = Review(provider="agent_wallet", renter="client_wallet", skill="code-generation", rating=5, completed_on_time=True, output_quality="excellent", comment="Great work!")
        assert review.provider == "agent_wallet"
        assert review.rating == 5

    def test_review_validate_valid(self):
        review = Review(provider="valid_agent", renter="valid_client", skill="code", rating=5)
        assert review.validate() is True

    def test_review_validate_invalid(self):
        review = Review(provider="", renter="client", skill="code", rating=5)
        assert review.validate() is False

class TestReputationScore:
    def test_create_score(self):
        score = ReputationScore(agent_id="agent_wallet")
        assert score.agent_id == "agent_wallet"
        assert score.reputation_score == 50.0

    def test_score_with_reviews(self):
        score = ReputationScore(agent_id="reviewed_agent", total_reviews=10, average_rating=4.5, on_time_percentage=95.0, reputation_score=87)
        assert score.total_reviews == 10

    def test_calculate_score_formula(self):
        score = ReputationScore(agent_id="formula_test", total_reviews=5, average_rating=4.0, on_time_percentage=80.0, reputation_score=0)
        calculated = score.calculate_score()
        assert calculated > 0

class TestReputationEngine:
    def test_engine_initialization(self):
        engine = ReputationEngine()
        assert engine is not None

    def test_add_review(self):
        engine = ReputationEngine()
        review = Review(provider="test_agent", renter="test_client", skill="code-generation", rating=5)
        new_score = engine.add_review("test_agent", review)
        assert new_score is not None

    def test_multiple_reviews(self):
        engine = ReputationEngine()
        for i, rating in enumerate([5, 4, 5, 5, 4]):
            review = Review(provider="rated_agent", renter=f"client_{i}", skill="test", rating=rating)
            engine.add_review("rated_agent", review)
        score = engine.get_score("rated_agent")
        assert score is not None

    def test_get_top_agents(self):
        engine = ReputationEngine()
        for i in range(5):
            for j in range(i + 1):
                review = Review(provider=f"agent_{i}", renter=f"client_{i}_{j}", skill="test", rating=min(i + 3, 5))
                engine.add_review(f"agent_{i}", review)
        top_agents = engine.get_top_agents()
        assert isinstance(top_agents, list)

    def test_invalid_rating_ignored(self):
        engine = ReputationEngine()
        review = Review(provider="test", renter="client", skill="test", rating=6)
        new_score = engine.add_review("test", review)
        assert new_score is not None

class TestEdgeCases:
    def test_all_one_star_reviews(self):
        engine = ReputationEngine()
        for _ in range(5):
            review = Review(provider="bad_agent", renter="client", skill="test", rating=1)
            engine.add_review("bad_agent", review)
        score = engine.get_score("bad_agent")
        assert score.average_rating == 1.0
        assert score.reputation_score < 50.0

    def test_all_five_star_reviews(self):
        engine = ReputationEngine()
        for _ in range(10):
            review = Review(provider="great_agent", renter="client", skill="test", rating=5)
            engine.add_review("great_agent", review)
        score = engine.get_score("great_agent")
        assert score.average_rating == 5.0
        assert score.reputation_score > 50.0

class TestRatingEnum:
    def test_all_ratings_defined(self):
        assert Rating.ONE_STAR.value == 1
        assert Rating.TWO_STARS.value == 2
        assert Rating.THREE_STARS.value == 3
        assert Rating.FOUR_STARS.value == 4
        assert Rating.FIVE_STARS.value == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
