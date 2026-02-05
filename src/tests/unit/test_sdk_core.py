"""
Unit Tests for SDK Core Modules

Purpose:
    Simple synchronous unit tests for SDK modules.
    Tests verify basic functionality without complex mocking.
    
Usage:
    pytest src/tests/unit/test_sdk_core.py -v
"""

import pytest
from datetime import datetime

from src.trustyclaw.sdk.identity import AgentIdentity, IdentityManager, IdentityStatus
from src.trustyclaw.sdk.reputation import ReputationEngine, Review
from src.trustyclaw.sdk.escrow import (
    EscrowClient, EscrowTerms, EscrowState, EscrowAccount
)


# ============ Identity Tests ============

class TestAgentIdentity:
    """Tests for AgentIdentity"""
    
    def test_create_identity(self):
        """Test creating an identity"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet-sol",
            public_key="test-pubkey-123",
            email="test@example.com",
        )
        assert identity.name == "TestAgent"
        assert identity.wallet_address == "test-wallet-sol"
        assert identity.status == IdentityStatus.ACTIVE
        assert identity.reputation_score == 0.0
    
    def test_identity_serialization(self, sample_identity):
        """Test serialization to dict"""
        data = sample_identity.to_dict()
        assert data["name"] == "TestAgent"
        assert data["wallet_address"] == "test-wallet-sol"
        assert "created_at" in data
        assert data["status"] == "active"
    
    def test_identity_deserialization(self, sample_identity):
        """Test deserialization from dict"""
        data = sample_identity.to_dict()
        restored = AgentIdentity.from_dict(data)
        assert restored.name == sample_identity.name
        assert restored.wallet_address == sample_identity.wallet_address
    
    def test_update_reputation(self, sample_identity):
        """Test reputation update"""
        sample_identity.update_reputation(95.0)
        assert sample_identity.reputation_score == 95.0
    
    def test_increment_rentals(self, sample_identity):
        """Test rental count increment"""
        initial = sample_identity.total_rentals
        sample_identity.increment_rentals(completed=True)
        assert sample_identity.total_rentals == initial + 1
        assert sample_identity.completed_rentals == 10


class TestIdentityManager:
    """Tests for IdentityManager"""
    
    def test_register_identity(self, demo_identities):
        """Test registering identities"""
        manager = IdentityManager()
        for identity in demo_identities:
            manager.register(identity)
        assert manager.check_exists("happyclaw.sol") is True
        assert manager.check_exists("alpha.sol") is True
        assert manager.check_exists("beta.sol") is True
    
    def test_get_by_wallet(self, demo_identities):
        """Test getting identity by wallet"""
        manager = IdentityManager()
        for identity in demo_identities:
            manager.register(identity)
        
        identity = manager.get_by_wallet("happyclaw.sol")
        assert identity is not None
        assert identity.name == "happyclaw-agent"
    
    def test_get_by_name(self, demo_identities):
        """Test getting identity by name"""
        manager = IdentityManager()
        for identity in demo_identities:
            manager.register(identity)
        
        identity = manager.get_by_name("agent-alpha")
        assert identity is not None
        assert identity.wallet_address == "alpha.sol"
    
    def test_list_identities(self, demo_identities):
        """Test listing all identities"""
        manager = IdentityManager()
        for identity in demo_identities:
            manager.register(identity)
        
        identities = manager.list_identities()
        assert len(identities) == 3
    
    def test_filter_by_reputation(self, demo_identities):
        """Test filtering by minimum reputation"""
        manager = IdentityManager()
        for identity in demo_identities:
            manager.register(identity)
        
        high_rep = manager.list_identities(min_reputation=90.0)
        assert len(high_rep) >= 1
        for identity in high_rep:
            assert identity.reputation_score >= 90.0


# ============ Reputation Tests ============

class TestReview:
    """Tests for Review"""
    
    def test_create_review(self, sample_review):
        """Test creating a review"""
        assert sample_review.provider == "agent-alpha"
        assert sample_review.rating == 5
        assert sample_review.validate() is True
    
    def test_validate_invalid_rating(self):
        """Test validation with invalid rating"""
        review = Review(
            provider="agent",
            renter="other",
            skill="test",
            rating=0,  # Invalid
        )
        assert review.validate() is False
    
    def test_validate_missing_provider(self):
        """Test validation with missing provider"""
        review = Review(
            provider="",
            renter="other",
            skill="test",
            rating=5,
        )
        assert review.validate() is False


class TestReputationEngine:
    """Tests for ReputationEngine"""
    
    def test_get_score(self):
        """Test getting reputation score"""
        engine = ReputationEngine()
        score = engine.get_score("test-agent")
        assert score is None  # New agent
    
    def test_add_review(self):
        """Test adding a review"""
        engine = ReputationEngine()
        
        review = Review(
            provider="new-agent",
            renter="renter",
            skill="test-skill",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Perfect!",
        )
        
        new_score = engine.add_review("new-agent", review)
        assert new_score.total_reviews == 1
        assert new_score.average_rating == 5.0
    
    def test_get_score_value(self):
        """Test getting score value"""
        engine = ReputationEngine()
        
        review = Review(
            provider="test-agent",
            renter="renter",
            skill="test",
            rating=4,
            completed_on_time=True,
        )
        engine.add_review("test-agent", review)
        
        value = engine.get_score_value("test-agent")
        assert value > 0
    
    def test_get_top_agents(self):
        """Test getting top agents"""
        engine = ReputationEngine()
        
        # Add reviews for multiple agents
        for i, (name, rating) in enumerate([
            ("agent-1", 3),
            ("agent-2", 5),
            ("agent-3", 4),
        ]):
            review = Review(
                provider=name,
                renter="test",
                skill="test",
                rating=rating,
                completed_on_time=True,
            )
            engine.add_review(name, review)
        
        top = engine.get_top_agents(n=2)
        assert len(top) <= 2
        # agent-2 should be first (highest rating)
        if len(top) == 2:
            assert top[0][0] == "agent-2"
    
    def test_get_reviews(self):
        """Test getting reviews for agent"""
        engine = ReputationEngine()
        
        review = Review(
            provider="test-agent",
            renter="renter-1",
            skill="test",
            rating=5,
            completed_on_time=True,
            comment="Great!",
        )
        engine.add_review("test-agent", review)
        
        reviews = engine.get_reviews("test-agent")
        assert len(reviews) == 1
        assert reviews[0].comment == "Great!"


# ============ Escrow Tests ============

class TestEscrowTerms:
    """Tests for EscrowTerms"""
    
    def test_create_terms(self):
        """Test creating escrow terms"""
        terms = EscrowTerms(
            skill_name="image-generation",
            price_usdc=10000,
            duration_seconds=3600,
        )
        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 10000
        assert terms.duration_seconds == 3600
    
    def test_terms_serialization(self):
        """Test terms serialization"""
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=5000,
            duration_seconds=1800,
        )
        data = terms.to_dict()
        assert data["skill_name"] == "test"
        assert data["price_usdc"] == 5000


class TestEscrowStateMachine:
    """Tests for Escrow state machine"""
    
    def test_escrow_state_enum(self):
        """Test EscrowState enum values"""
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.COMPLETED.value == "completed"
        assert EscrowState.CANCELLED.value == "cancelled"
    
    def test_escrow_account_created(self):
        """Test escrow in created state"""
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        escrow = EscrowAccount(
            address="test-escrow",
            provider="provider",
            renter="",
            terms=terms,
            state=EscrowState.CREATED,
            amount=0,
            created_at=datetime.utcnow().isoformat(),
        )
        assert escrow.state == EscrowState.CREATED
        assert escrow.amount == 0
        assert escrow.is_expired() is False
    
    def test_escrow_account_funded(self):
        """Test escrow in funded state"""
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        escrow = EscrowAccount(
            address="test-escrow",
            provider="provider",
            renter="renter",
            terms=terms,
            state=EscrowState.FUNDED,
            amount=10000,
            created_at=datetime.utcnow().isoformat(),
        )
        assert escrow.state == EscrowState.FUNDED
        assert escrow.amount == 10000
    
    def test_escrow_account_completed(self):
        """Test escrow in completed state"""
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        escrow = EscrowAccount(
            address="test-escrow",
            provider="provider",
            renter="renter",
            terms=terms,
            state=EscrowState.COMPLETED,
            amount=10000,
            created_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
        )
        assert escrow.state == EscrowState.COMPLETED
        assert escrow.completed_at is not None


class TestEscrowClient:
    """Tests for EscrowClient (sync methods)"""
    
    def test_client_init(self):
        """Test client initialization"""
        client = EscrowClient()
        assert client.network == "devnet"
        assert client.USDC_MINT == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    def test_create_escrow_terms_helper(self):
        """Test create_escrow_terms helper"""
        from src.trustyclaw.sdk.escrow import create_escrow_terms
        
        terms = create_escrow_terms(
            skill_name="code-review",
            price_usdc=0.05,
            duration_seconds=7200,
        )
        assert terms.skill_name == "code-review"
        assert terms.price_usdc == 50000  # 0.05 * 1_000_000
        assert terms.duration_seconds == 7200


# ============ Pytest Fixtures ============

@pytest.fixture
def sample_identity():
    """Create a sample identity for testing"""
    return AgentIdentity(
        id="test-agent-001",
        name="TestAgent",
        wallet_address="test-wallet-sol",
        public_key="test-pubkey-123",
        email="test@example.com",
        reputation_score=85.0,
        total_rentals=10,
        completed_rentals=9,
        status=IdentityStatus.ACTIVE,
    )


@pytest.fixture
def sample_review():
    """Create a sample review for testing"""
    return Review(
        provider="agent-alpha",
        renter="agent-beta",
        skill="image-generation",
        rating=5,
        completed_on_time=True,
        output_quality="excellent",
        comment="Great work!",
    )


@pytest.fixture
def demo_identities():
    """Create demo identities for testing"""
    return [
        AgentIdentity(
            name="happyclaw-agent",
            wallet_address="happyclaw.sol",
            public_key="happyclaw-pubkey",
            reputation_score=85.0,
            total_rentals=47,
            completed_rentals=45,
        ),
        AgentIdentity(
            name="agent-alpha",
            wallet_address="alpha.sol",
            public_key="alpha-pubkey",
            reputation_score=88.0,
            total_rentals=32,
            completed_rentals=30,
        ),
        AgentIdentity(
            name="agent-beta",
            wallet_address="beta.sol",
            public_key="beta-pubkey",
            reputation_score=91.0,
            total_rentals=28,
            completed_rentals=27,
        ),
    ]


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
