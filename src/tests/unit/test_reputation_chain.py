"""
Tests for On-Chain Reputation Storage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestReputationScoreData:
    """Tests for ReputationScoreData serialization"""
    
    def test_serialization_roundtrip(self):
        """Test bytes serialization and deserialization"""
        from src.trustyclaw.sdk.reputation_chain import ReputationScoreData
        
        original = ReputationScoreData(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            total_reviews=25,
            average_rating=4.5,
            on_time_percentage=95.0,
            reputation_score=87.5,
            last_updated=1707158400,
        )
        
        # Serialize and deserialize
        bytes_data = original.to_bytes()
        restored = ReputationScoreData.from_bytes(bytes_data)
        
        assert restored.agent_address == original.agent_address
        assert restored.total_reviews == original.total_reviews
        assert restored.average_rating == original.average_rating
        assert restored.on_time_percentage == original.on_time_percentage
        assert restored.reputation_score == original.reputation_score
        assert restored.last_updated == original.last_updated
    
    def test_default_values(self):
        """Test default values"""
        from src.trustyclaw.sdk.reputation_chain import ReputationScoreData
        
        score = ReputationScoreData(agent_address="test")
        
        assert score.total_reviews == 0
        assert score.average_rating == 0.0
        assert score.on_time_percentage == 100.0
        assert score.reputation_score == 50.0
        assert score.last_updated == 0


class TestReviewData:
    """Tests for ReviewData serialization"""
    
    def test_serialization_roundtrip(self):
        """Test bytes serialization and deserialization"""
        from src.trustyclaw.sdk.reputation_chain import ReviewData
        
        original = ReviewData(
            review_id="review-123",
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            skill_id="image-generation",
            rating=5,
            completed_on_time=True,
            comment_hash="abc123def456",
            timestamp=1707158400,
            positive_votes=10,
            negative_votes=1,
        )
        
        bytes_data = original.to_bytes()
        restored = ReviewData.from_bytes(bytes_data)
        
        assert restored.review_id == original.review_id
        assert restored.provider == original.provider
        assert restored.renter == original.renter
        assert restored.skill_id == original.skill_id
        assert restored.rating == original.rating
        assert restored.completed_on_time == original.completed_on_time
        assert restored.comment_hash == original.comment_hash
        assert restored.timestamp == original.timestamp
    
    def test_rating_bounds(self):
        """Test rating is stored correctly"""
        from src.trustyclaw.sdk.reputation_chain import ReviewData
        
        for rating in [1, 3, 5]:
            review = ReviewData(
                review_id="test",
                provider="test",
                renter="test",
                skill_id="test",
                rating=rating,
                completed_on_time=True,
                comment_hash="test",
                timestamp=0,
            )
            assert review.rating == rating


class TestReputationPDAProgram:
    """Tests for ReputationPDAProgram"""
    
    @pytest.fixture
    def program(self):
        """Create program with mock"""
        with patch('src.trustyclaw.sdk.reputation_chain.HAS_SOLANA', False):
            from src.trustyclaw.sdk.reputation_chain import ReputationPDAProgram
            return ReputationPDAProgram(network="devnet")
    
    def test_derive_reputation_pda(self, program):
        """Test PDA derivation"""
        pda = program.derive_reputation_pda(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        assert pda is not None
        assert "rep-" in pda
    
    def test_derive_pda_deterministic(self, program):
        """Test same address produces same PDA"""
        addr = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        pda1 = program.derive_reputation_pda(addr)
        pda2 = program.derive_reputation_pda(addr)
        assert pda1 == pda2
    
    def test_derive_different_pdas(self, program):
        """Test different addresses produce different PDAs"""
        pda1 = program.derive_reputation_pda("addr1")
        pda2 = program.derive_reputation_pda("addr2")
        assert pda1 != pda2
    
    def test_get_reputation_mock(self, program):
        """Test getting reputation returns mock data"""
        reputation = program.get_reputation(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        assert reputation is not None
        assert reputation.agent_address == "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        assert 0 <= reputation.reputation_score <= 100
        assert 0 <= reputation.average_rating <= 5
    
    def test_create_reputation_account(self, program):
        """Test creating reputation account"""
        result = program.create_reputation_account(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            payer_address="payer",
        )
        assert result["success"] is True
        assert "pda" in result
        assert "signature" in result
    
    def test_update_reputation(self, program):
        """Test updating reputation"""
        result = program.update_reputation(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            new_score=90.0,
            new_reviews=30,
            new_rating=4.8,
            on_time_pct=98.0,
        )
        assert result["success"] is True
        assert result["score"] == 90.0
    
    def test_submit_review(self, program):
        """Test submitting review"""
        result = program.submit_review(
            review_id="review-123",
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            skill_id="image-generation",
            rating=5,
            completed_on_time=True,
            comment="Great work!",
        )
        assert result["success"] is True
        assert result["review_id"] == "review-123"
    
    def test_get_agent_reviews(self, program):
        """Test getting agent reviews"""
        reviews = program.get_agent_reviews(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            limit=5,
        )
        assert len(reviews) > 0
        assert len(reviews) <= 5
        for review in reviews:
            assert isinstance(review, type(program._mock_reviews("", 1)[0]))
    
    def test_calculate_score_perfect(self, program):
        """Test score calculation for perfect agent"""
        score = program.calculate_score(
            average_rating=5.0,
            on_time_pct=100.0,
            total_reviews=100,
        )
        assert score >= 90.0  # Should be very high
    
    def test_calculate_score_new_agent(self, program):
        """Test score calculation for new agent"""
        score = program.calculate_score(
            average_rating=3.0,
            on_time_pct=50.0,
            total_reviews=1,
        )
        assert 0 <= score <= 100
        # New agent with poor metrics should have low score
        assert score < 50.0
    
    def test_calculate_score_volume_bonus(self, program):
        """Test that more reviews boost score"""
        low_score = program.calculate_score(
            average_rating=4.0,
            on_time_pct=80.0,
            total_reviews=1,
        )
        high_score = program.calculate_score(
            average_rating=4.0,
            on_time_pct=80.0,
            total_reviews=100,
        )
        # More reviews should give higher score
        assert high_score >= low_score


class TestGetReputationProgram:
    """Tests for get_reputation_program function"""
    
    def test_get_program_devnet(self):
        """Test getting program for devnet"""
        with patch('src.trustyclaw.sdk.reputation_chain.HAS_SOLANA', False):
            from src.trustyclaw.sdk.reputation_chain import get_reputation_program
            
            program = get_reputation_program("devnet")
            assert program.network == "devnet"
    
    def test_get_program_mainnet(self):
        """Test getting program for mainnet"""
        with patch('src.trustyclaw.sdk.reputation_chain.HAS_SOLANA', False):
            from src.trustyclaw.sdk.reputation_chain import get_reputation_program
            
            program = get_reputation_program("mainnet")
            assert program.network == "mainnet"


class TestReputationError:
    """Tests for ReputationError"""
    
    def test_raise_error(self):
        """Test raising reputation error"""
        from src.trustyclaw.sdk.reputation_chain import ReputationError
        
        with pytest.raises(ReputationError):
            raise ReputationError("Test error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
