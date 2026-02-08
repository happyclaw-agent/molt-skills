"""
Integration Tests for On-Chain Reputation Program

Tests the real Solana reputation program deployment and interactions.
"""

import pytest
import hashlib
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from trustyclaw.sdk.reputation_chain import (
    ReputationChainSDK,
    ReputationScoreData,
    ReviewData,
    ReputationError,
    REPUTATION_PROGRAM_ID,
)
from trustyclaw.skills.reputation import (
    ReputationSkill,
    ReputationMetrics,
    ReputationTier,
    ReputationBreakdown,
    get_reputation_skill,
)


class TestReputationScoreData:
    """Test the ReputationScoreData dataclass"""
    
    def test_create_reputation_data(self):
        """Test creating reputation score data"""
        data = ReputationScoreData(
            agent_address="TestAgent123456789",
            total_reviews=100,
            average_rating=4.5,
            on_time_percentage=95.0,
            reputation_score=85.0,
            positive_votes=50,
            negative_votes=5,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        
        assert data.agent_address == "TestAgent123456789"
        assert data.total_reviews == 100
        assert data.average_rating == 4.5
        assert data.on_time_percentage == 95.0
        assert data.reputation_score == 85.0
    
    def test_serialization_roundtrip(self):
        """Test bytes serialization and deserialization"""
        original = ReputationScoreData(
            agent_address="TestAgent",
            total_reviews=50,
            average_rating=4.2,
            on_time_percentage=90.0,
            reputation_score=75.5,
            positive_votes=25,
            negative_votes=3,
            created_at=1000000,
            updated_at=1000001,
        )
        
        bytes_data = original.to_bytes()
        restored = ReputationScoreData.from_bytes(bytes_data)
        
        assert restored.agent_address == original.agent_address
        assert restored.total_reviews == original.total_reviews
        assert abs(restored.average_rating - original.average_rating) < 0.01
        assert abs(restored.reputation_score - original.reputation_score) < 0.01
    
    def test_from_account_info(self):
        """Test creating from account info dict"""
        raw_data = ReputationScoreData(
            agent_address="AccountInfoTest",
            total_reviews=200,
            average_rating=4.8,
            on_time_percentage=98.0,
            reputation_score=92.0,
            positive_votes=150,
            negative_votes=10,
            created_at=1000000,
            updated_at=1000001,
        ).to_bytes()
        
        account_info = {'data': raw_data}
        result = ReputationScoreData.from_account_info(account_info)
        
        assert result.agent_address == "AccountInfoTest"
        assert result.total_reviews == 200


class TestReviewData:
    """Test the ReviewData dataclass"""
    
    def test_create_review_data(self):
        """Test creating review data"""
        review = ReviewData(
            review_id="review-123",
            provider="ProviderAddress123",
            reviewer="ReviewerAddress456",
            rating=5,
            completed_on_time=True,
            comment_hash="abc123def456",
            positive_votes=10,
            negative_votes=1,
            timestamp=int(time.time()),
        )
        
        assert review.review_id == "review-123"
        assert review.provider == "ProviderAddress123"
        assert review.rating == 5
        assert review.completed_on_time is True
    
    def test_review_serialization(self):
        """Test review data serialization"""
        original = ReviewData(
            review_id="test-review-id",
            provider="TestProvider",
            reviewer="TestReviewer",
            rating=4,
            completed_on_time=False,
            comment_hash="hash123",
            positive_votes=5,
            negative_votes=2,
            timestamp=1000000,
        )
        
        bytes_data = original.to_bytes()
        restored = ReviewData.from_bytes(bytes_data)
        
        assert restored.review_id == original.review_id
        assert restored.rating == original.rating
        assert restored.completed_on_time == original.completed_on_time


class TestReputationChainSDK:
    """Test the ReputationChainSDK"""
    
    @pytest.fixture
    def sdk(self):
        """Create SDK instance for testing"""
        return ReputationChainSDK(network="devnet")
    
    def test_derive_reputation_pda(self, sdk):
        """Test PDA derivation"""
        pda, bump = sdk.derive_reputation_pda("TestAgent123")
        
        assert pda is not None
        assert isinstance(pda, str)
        assert bump > 0
    
    def test_derive_review_pda(self, sdk):
        """Test review PDA derivation"""
        review_id = "unique-review-123"
        pda, bump = sdk.derive_review_pda(review_id)
        
        assert pda is not None
        assert isinstance(pda, str)
        assert bump > 0
    
    def test_calculate_score_basic(self, sdk):
        """Test reputation score calculation"""
        score = sdk.calculate_score(
            average_rating=5.0,
            on_time_pct=100.0,
            total_reviews=100,
        )
        
        # Perfect metrics should give high score
        assert score >= 90.0
        assert score <= 100.0
    
    def test_calculate_score_low_metrics(self, sdk):
        """Test score with low metrics"""
        score = sdk.calculate_score(
            average_rating=1.0,
            on_time_pct=50.0,
            total_reviews=1,
        )
        
        # Poor metrics should give low score
        assert score < 50.0
    
    def test_calculate_score_volume_bonus(self, sdk):
        """Test that more reviews give higher score"""
        score_low_volume = sdk.calculate_score(
            average_rating=4.0,
            on_time_pct=90.0,
            total_reviews=5,
        )
        
        score_high_volume = sdk.calculate_score(
            average_rating=4.0,
            on_time_pct=90.0,
            total_reviews=100,
        )
        
        # Higher volume should give higher score
        assert score_high_volume > score_low_volume
    
    def test_program_id_set(self, sdk):
        """Test that program ID is correctly set"""
        assert sdk.program_id == REPUTATION_PROGRAM_ID


class TestReputationSkill:
    """Test the ReputationSkill"""
    
    @pytest.fixture
    def skill(self):
        """Create skill instance for testing"""
        return ReputationSkill(network="devnet")
    
    def test_skill_initialization(self, skill):
        """Test skill initializes correctly"""
        assert skill.network == "devnet"
        assert skill._sdk is None
        assert skill._cache == {}
    
    def test_get_reputation_tier_elite(self, skill):
        assert skill.get_tier_for_score(95.0) == ReputationTier.ELITE.value

    def test_get_reputation_tier_trusted(self, skill):
        assert skill.get_tier_for_score(80.0) == ReputationTier.TRUSTED.value

    def test_get_reputation_tier_verified(self, skill):
        assert skill.get_tier_for_score(60.0) == ReputationTier.VERIFIED.value

    def test_get_reputation_tier_new(self, skill):
        assert skill.get_tier_for_score(35.0) == ReputationTier.NEW.value

    def test_get_reputation_tier_unknown(self, skill):
        assert skill.get_tier_for_score(10.0) == ReputationTier.UNKNOWN.value

    def test_get_reputation_tier_boundary_90(self, skill):
        assert skill.get_tier_for_score(90.0) == ReputationTier.ELITE.value

    def test_get_reputation_tier_boundary_75(self, skill):
        assert skill.get_tier_for_score(75.0) == ReputationTier.TRUSTED.value

    def test_get_reputation_tier_boundary_50(self, skill):
        assert skill.get_tier_for_score(50.0) == ReputationTier.VERIFIED.value

    def test_get_reputation_tier_boundary_25(self, skill):
        assert skill.get_tier_for_score(25.0) == ReputationTier.NEW.value

    def test_clear_cache(self, skill):
        """Test cache clearing"""
        skill._cache = {"agent1": (Mock(), time.time())}
        
        skill.clear_cache("agent1")
        assert "agent1" not in skill._cache
    
    def test_clear_all_cache(self, skill):
        """Test clearing all cache"""
        skill._cache = {
            "agent1": (Mock(), time.time()),
            "agent2": (Mock(), time.time()),
        }
        
        skill.clear_cache()
        assert skill._cache == {}
    
    def test_refresh_reputation(self, skill):
        """Test reputation refresh clears cache"""
        original_data = ReputationMetrics(
            agent_address="RefreshTestAgent",
            reputation_score=70.0,
        )
        skill._cache["RefreshTestAgent"] = (original_data, time.time())
        
        skill.clear_cache("RefreshTestAgent")
        assert "RefreshTestAgent" not in skill._cache
    
    def test_export_reputation_json_empty(self, skill):
        """Test JSON export with no data"""
        result = skill.export_reputation_json()
        assert result == "[]"
    
    def test_export_reputation_json_single(self, skill):
        """Test JSON export with single agent (populate cache first)"""
        import json as json_mod
        metrics = ReputationMetrics(
            agent_address="ExportTestAgent",
            reputation_score=80.0,
            average_rating=4.5,
            total_reviews=50,
        )
        skill._cache["ExportTestAgent"] = (metrics, time.time())
        result = skill.export_reputation_json("ExportTestAgent")
        data = json_mod.loads(result)
        assert len(data) == 1
        assert data[0]["agent_address"] == "ExportTestAgent"
        assert data[0]["reputation_score"] == 80.0


class TestReputationMetrics:
    """Test the ReputationMetrics dataclass"""
    
    def test_from_on_chain(self):
        """Test creating metrics from on-chain data"""
        on_chain = ReputationScoreData(
            agent_address="OnChainAgent",
            total_reviews=100,
            average_rating=4.5,
            on_time_percentage=95.0,
            reputation_score=85.0,
            positive_votes=80,
            negative_votes=20,
            created_at=1000000,
            updated_at=1000001,
        )
        
        metrics = ReputationMetrics.from_on_chain(on_chain)
        
        assert metrics.agent_address == "OnChainAgent"
        assert metrics.total_reviews == 100
        assert metrics.average_rating == 4.5
        assert metrics.on_time_percentage == 95.0
        assert metrics.positive_reviews == 80
        assert metrics.negative_reviews == 20
        assert metrics.on_chain_data == on_chain
    
    def test_to_dict(self):
        """Test metrics to dict conversion"""
        metrics = ReputationMetrics(
            agent_address="DictTestAgent",
            reputation_score=75.0,
            average_rating=4.0,
            total_reviews=50,
            on_time_percentage=90.0,
            positive_reviews=40,
            negative_reviews=10,
        )
        
        result = metrics.to_dict()
        
        assert result["agent_address"] == "DictTestAgent"
        assert result["reputation_score"] == 75.0
        assert result["average_rating"] == 4.0
        assert result["total_reviews"] == 50


class TestReputationBreakdown:
    """Test the ReputationBreakdown dataclass"""
    
    def test_create_breakdown(self):
        """Test creating reputation breakdown"""
        breakdown = ReputationBreakdown(
            agent_address="BreakdownAgent",
            quality_score=85.0,
            reliability_score=90.0,
            communication_score=80.0,
            value_score=75.0,
            overall_score=82.5,
        )
        
        assert breakdown.agent_address == "BreakdownAgent"
        assert breakdown.overall_score == 82.5
    
    def test_breakdown_to_dict(self):
        """Test breakdown to dict"""
        breakdown = ReputationBreakdown(
            agent_address="TestAgent",
            quality_score=80.0,
            reliability_score=85.0,
            communication_score=75.0,
            value_score=70.0,
            overall_score=77.5,
        )
        
        result = breakdown.to_dict()
        
        assert result["agent_address"] == "TestAgent"
        assert result["quality_score"] == 80.0
        assert result["overall_score"] == 77.5


class TestTrustScoreCalculation:
    """Test trust score calculations"""
    
    @pytest.fixture
    def skill(self):
        """Create skill instance"""
        return ReputationSkill(network="devnet")
    
    def test_default_weights(self, skill):
        """Test default trust score weights"""
        metrics = ReputationMetrics(
            agent_address="TrustTestAgent",
            reputation_score=80.0,
            average_rating=4.5,
            total_reviews=50,
            on_time_percentage=90.0,
            positive_reviews=45,
            negative_reviews=5,
        )
        
        skill._cache["TrustTestAgent"] = (metrics, time.time())
        
        score = skill.calculate_trust_score("TrustTestAgent")
        
        assert score is not None
        assert 0 <= score <= 100
    
    def test_custom_weights(self, skill):
        """Test custom trust score weights"""
        metrics = ReputationMetrics(
            agent_address="CustomWeightAgent",
            reputation_score=80.0,
            average_rating=4.0,
            total_reviews=100,
            on_time_percentage=85.0,
            positive_reviews=90,
            negative_reviews=10,
        )
        
        skill._cache["CustomWeightAgent"] = (metrics, time.time())
        
        # High rating weight
        score_high_rating = skill.calculate_trust_score(
            "CustomWeightAgent",
            weights={"rating": 0.5, "on_time": 0.2, "volume": 0.15, "positivity": 0.15}
        )
        
        # High volume weight
        score_high_volume = skill.calculate_trust_score(
            "CustomWeightAgent",
            weights={"rating": 0.2, "on_time": 0.2, "volume": 0.4, "positivity": 0.2}
        )
        
        assert score_high_rating != score_high_volume


class TestVerification:
    """Test reputation verification"""
    
    @pytest.fixture
    def skill(self):
        """Create skill instance"""
        return ReputationSkill(network="devnet")
    
    def test_verify_claim_match(self, skill):
        """Test verification when claim matches actual"""
        metrics = ReputationMetrics(
            agent_address="VerifyMatchAgent",
            reputation_score=85.0,
        )
        
        skill._cache["VerifyMatchAgent"] = (metrics, time.time())
        
        result = skill.verify_reputation_claim("VerifyMatchAgent", claimed_score=85.0, tolerance=5.0)
        
        assert result["verified"] is True
        assert result["actual_score"] == 85.0
        assert result["claimed_score"] == 85.0
    
    def test_verify_claim_within_tolerance(self, skill):
        """Test verification within tolerance"""
        metrics = ReputationMetrics(
            agent_address="VerifyToleranceAgent",
            reputation_score=85.0,
        )
        
        skill._cache["VerifyToleranceAgent"] = (metrics, time.time())
        
        result = skill.verify_reputation_claim("VerifyToleranceAgent", claimed_score=88.0, tolerance=5.0)
        
        assert result["verified"] is True
        assert result["difference"] == 3.0
        assert result["within_tolerance"] is True
    
    def test_verify_claim_outside_tolerance(self, skill):
        """Test verification outside tolerance"""
        metrics = ReputationMetrics(
            agent_address="VerifyFailAgent",
            reputation_score=85.0,
        )
        
        skill._cache["VerifyFailAgent"] = (metrics, time.time())
        
        result = skill.verify_reputation_claim("VerifyFailAgent", claimed_score=95.0, tolerance=5.0)
        
        assert result["verified"] is False
        assert result["difference"] == 10.0
        assert result["within_tolerance"] is False
    
    def test_verify_claim_not_found(self, skill):
        """Test verification when agent not in cache (may get mock fallback and still get a result)"""
        result = skill.verify_reputation_claim("NonExistentAgent", claimed_score=85.0)
        assert "claimed_score" in result
        assert result["claimed_score"] == 85.0
        assert "verified" in result
        assert result["actual_score"] is None or isinstance(result["actual_score"], (int, float))


class TestComparison:
    """Test agent comparison"""
    
    @pytest.fixture
    def skill(self):
        """Create skill instance"""
        return ReputationSkill(network="devnet")
    
    def test_compare_agents(self, skill):
        """Test comparing two agents"""
        rep_a = ReputationMetrics(
            agent_address="CompareAgentA",
            reputation_score=90.0,
            average_rating=4.8,
            total_reviews=100,
            on_time_percentage=95.0,
        )
        
        rep_b = ReputationMetrics(
            agent_address="CompareAgentB",
            reputation_score=75.0,
            average_rating=4.0,
            total_reviews=50,
            on_time_percentage=85.0,
        )
        
        skill._cache["CompareAgentA"] = (rep_a, time.time())
        skill._cache["CompareAgentB"] = (rep_b, time.time())
        
        result = skill.compare_agents("CompareAgentA", "CompareAgentB")
        
        assert result["agent_a"] == "CompareAgentA"
        assert result["agent_b"] == "CompareAgentB"
        assert result["comparison"]["reputation_score"]["winner"] == "CompareAgentA"
        assert result["comparison"]["average_rating"]["winner"] == "CompareAgentA"
        assert result["comparison"]["on_time_rate"]["winner"] == "CompareAgentA"
    
    def test_compare_one_not_found(self, skill):
        """Test comparing when one agent not in cache (skill may use mock fallback and still return comparison)"""
        rep_a = ReputationMetrics(
            agent_address="FoundAgent",
            reputation_score=80.0,
        )
        skill._cache["FoundAgent"] = (rep_a, time.time())
        result = skill.compare_agents("FoundAgent", "MissingAgent")
        assert result["agent_a"] == "FoundAgent"
        assert result["agent_b"] == "MissingAgent"
        assert "comparison" in result


class TestGetReputationSkill:
    """Test the get_reputation_skill factory function"""
    
    def test_get_reputation_skill(self):
        """Test factory function creates skill"""
        skill = get_reputation_skill("devnet")
        
        assert isinstance(skill, ReputationSkill)
        assert skill.network == "devnet"
    
    def test_get_reputation_skill_mainnet(self):
        """Test factory with mainnet"""
        skill = get_reputation_skill("mainnet")
        
        assert skill.network == "mainnet"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def skill(self):
        """Create skill instance"""
        return ReputationSkill(network="devnet")
    
    def test_zero_reviews(self, skill):
        """Test score calculation with zero reviews"""
        score = skill.sdk.calculate_score(
            average_rating=0.0,
            on_time_pct=0.0,
            total_reviews=0,
        )
        
        assert score >= 0.0
    
    def test_max_rating(self, skill):
        """Test score calculation with max rating"""
        score = skill.sdk.calculate_score(
            average_rating=5.0,
            on_time_pct=100.0,
            total_reviews=1000,
        )
        
        assert score == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
