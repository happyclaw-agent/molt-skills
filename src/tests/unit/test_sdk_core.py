"""
Unit Tests for SDK Core Modules

Purpose:
    Unit tests for client.py, identity.py, and reputation.py.
    Tests use mocked data to verify behavior without network calls.
    
Fixtures:
    - test_client: SolanaClient with mocked HTTP responses
    - test_identity: AgentIdentity with sample data
    - test_reputation: ReputationEngine with demo data
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.clawtrust.sdk.client import SolanaClient, ClientConfig, Network
from src.clawtrust.sdk.identity import AgentIdentity, IdentityManager, IdentityStatus
from src.clawtrust.sdk.reputation import ReputationEngine, Review, ReputationScore


# ============ Mock Fixtures ============

@pytest.fixture
def mock_http_response(self):
    """Create a mock HTTP response"""
    def _create(json_data: dict, status: int = 200):
        response = MagicMock()
        response.json.return_value = json_data
        response.raise_for_status = MagicMock()
        response.status_code = status
        return response
    return _create


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


@pytest.fixture
def demo_reviews():
    """Create demo reviews for testing"""
    return [
        Review(
            provider="agent-alpha",
            renter="agent-beta",
            skill="code-review",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Excellent code review!",
        ),
        Review(
            provider="agent-alpha",
            renter="agent-gamma",
            skill="security-scan",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Found all vulnerabilities.",
        ),
    ]


# ============ Client Tests ============

class TestSolanaClient:
    """Tests for SolanaClient"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return SolanaClient(ClientConfig(network=Network.DEVNET))
    
    @pytest.mark.asyncio
    async def test_get_balance(self, client, mock_http_response):
        """Test getting balance with mock response"""
        mock_response = mock_http_response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"value": {"lamports": 1000000000}},
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            balance = await client.get_balance("test-address")
            assert balance == 1000000000
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, client, mock_http_response):
        """Test getting account info with mock response"""
        mock_response = mock_http_response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": {
                    "lamports": 500000000,
                    "owner": "Program111111111111111111111111111111111",
                    "executable": False,
                }
            },
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            info = await client.get_account_info("test-address")
            assert info["lamports"] == 500000000
    
    @pytest.mark.asyncio
    async def test_get_latest_blockhash(self, client, mock_http_response):
        """Test getting blockhash with mock response"""
        mock_response = mock_http_response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": {
                    "blockhash": "abc123...xyz789",
                    "lastValidBlockHeight": 1000,
                }
            },
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            blockhash = await client.get_latest_blockhash()
            assert blockhash == "abc123...xyz789"
    
    def test_derive_pda(self, client):
        """Test PDA derivation"""
        address, bump = client.derive_pda(
            [b"escrow", b"provider123"],
            "ESCRW1111111111111111111111111111111111111",
        )
        assert address is not None
        assert len(address) == 64  # hex string
        assert bump == 255
    
    def test_get_rpc_url(self, client):
        """Test RPC URL retrieval"""
        url = client.get_rpc_url()
        assert "devnet" in url or "solana.com" in url
    
    def test_get_network(self, client):
        """Test network enum retrieval"""
        network = client.get_network()
        assert network == Network.DEVNET
    
    @pytest.mark.asyncio
    async def test_send_transaction(self, client, mock_http_response):
        """Test sending transaction with mock response"""
        mock_response = mock_http_response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": "tx-abc123",
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            tx_sig = await client.send_transaction(b"test-tx", ["sig1"])
            assert tx_sig == "tx-abc123"


# ============ Identity Tests ============

class TestAgentIdentity:
    """Tests for AgentIdentity"""
    
    def test_create_identity(self, sample_identity):
        """Test creating an identity"""
        assert sample_identity.name == "TestAgent"
        assert sample_identity.wallet_address == "test-wallet-sol"
        assert sample_identity.status == IdentityStatus.ACTIVE
        assert sample_identity.reputation_score == 85.0
    
    def test_to_dict(self, sample_identity):
        """Test serialization"""
        data = sample_identity.to_dict()
        
        assert data["name"] == "TestAgent"
        assert data["wallet_address"] == "test-wallet-sol"
        assert "created_at" in data
        assert data["status"] == "active"
    
    def test_from_dict(self, sample_identity):
        """Test deserialization"""
        data = sample_identity.to_dict()
        restored = AgentIdentity.from_dict(data)
        
        assert restored.name == sample_identity.name
        assert restored.wallet_address == sample_identity.wallet_address
        assert restored.reputation_score == sample_identity.reputation_score
    
    def test_update_reputation(self, sample_identity):
        """Test reputation update"""
        sample_identity.update_reputation(95.0)
        assert sample_identity.reputation_score == 95.0
    
    def test_increment_rentals(self, sample_identity):
        """Test rental count increment"""
        sample_identity.increment_rentals(completed=True)
        assert sample_identity.total_rentals == 11
        assert sample_identity.completed_rentals == 10
        
        sample_identity.increment_rentals(completed=False)
        assert sample_identity.total_rentals == 12
        assert sample_identity.completed_rentals == 10
    
    def test_to_short_str(self, sample_identity):
        """Test short string representation"""
        short = sample_identity.to_short_str()
        assert "@TestAgent" in short
        assert "85" in short


class TestIdentityManager:
    """Tests for IdentityManager"""
    
    @pytest.fixture
    def manager(self, demo_identities):
        """Create manager with demo identities"""
        mgr = IdentityManager()
        for identity in demo_identities:
            mgr.register(identity)
        return mgr
    
    def test_register_identity(self, manager, sample_identity):
        """Test registering a new identity"""
        # sample_identity already registered via fixture
        assert manager.check_exists(sample_identity.wallet_address) is True
    
    def test_get_by_wallet(self, manager):
        """Test getting by wallet"""
        identity = manager.get_by_wallet("happyclaw.sol")
        assert identity is not None
        assert identity.name == "happyclaw-agent"
    
    def test_get_by_name(self, manager):
        """Test getting by name"""
        identity = manager.get_by_name("agent-alpha")
        assert identity is not None
        assert identity.wallet_address == "alpha.sol"
    
    def test_list_identities(self, manager):
        """Test listing all identities"""
        identities = manager.list_identities()
        assert len(identities) >= 3
    
    def test_filter_by_status(self, manager):
        """Test filtering by status"""
        identities = manager.list_identities(status=IdentityStatus.ACTIVE)
        assert len(identities) >= 3
    
    def test_filter_by_reputation(self, manager):
        """Test filtering by minimum reputation"""
        identities = manager.list_identities(min_reputation=90.0)
        assert len(identities) >= 1
        for identity in identities:
            assert identity.reputation_score >= 90.0
    
    def test_update_reputation(self, manager):
        """Test reputation update"""
        score = manager.update_reputation("alpha.sol", 95.0)
        assert score is not None
        assert score.reputation_score == 95.0
    
    def test_check_exists(self, manager):
        """Test checking if identity exists"""
        assert manager.check_exists("happyclaw.sol") is True
        assert manager.check_exists("nonexistent.sol") is False
    
    def test_duplicate_wallet_error(self, manager, sample_identity):
        """Test that registering duplicate wallet raises error"""
        with pytest.raises(ValueError, match="already registered"):
            manager.register(sample_identity)


# ============ Reputation Tests ============

class TestReview:
    """Tests for Review"""
    
    def test_create_review(self, sample_review):
        """Test creating a review"""
        assert sample_review.provider == "agent-alpha"
        assert sample_review.rating == 5
        assert sample_review.validate() is True
    
    def test_validate_invalid(self):
        """Test validation failure with invalid data"""
        review = Review(
            provider="",  # Invalid - required
            renter="agent-beta",
            rating=5,
        )
        assert review.validate() is False
    
    def test_validate_rating_bounds(self):
        """Test rating must be 1-5"""
        # Valid
        review = Review(provider="agent", renter="other", skill="test", rating=1)
        assert review.validate() is True
        
        review = Review(provider="agent", renter="other", skill="test", rating=5)
        assert review.validate() is True
        
        # Invalid
        review = Review(provider="agent", renter="other", skill="test", rating=0)
        assert review.validate() is False
        
        review = Review(provider="agent", renter="other", skill="test", rating=6)
        assert review.validate() is False


class TestReputationScore:
    """Tests for ReputationScore"""
    
    def test_calculate_new_agent(self):
        """Test calculating score for new agent (no reviews)"""
        score = ReputationScore(agent_id="new-agent")
        calculated = score.calculate_score()
        
        assert calculated == 50.0  # Default for no reviews
    
    def test_calculate_with_reviews(self):
        """Test calculating score with reviews"""
        score = ReputationScore(
            agent_id="test-agent",
            total_reviews=5,
            average_rating=4.5,
            on_time_percentage=90.0,
        )
        
        calculated = score.calculate_score()
        
        assert calculated > 0
        assert calculated <= 100
    
    def test_calculate_perfect_score(self):
        """Test perfect score calculation"""
        score = ReputationScore(
            agent_id="perfect-agent",
            total_reviews=100,
            average_rating=5.0,
            on_time_percentage=100.0,
        )
        
        calculated = score.calculate_score()
        
        # Should be close to 100
        assert calculated >= 90


class TestReputationEngine:
    """Tests for ReputationEngine"""
    
    @pytest.fixture
    def engine(self, demo_reviews):
        """Create engine with demo reviews"""
        eng = ReputationEngine()
        for review in demo_reviews:
            eng.add_review(review.provider, review)
        return eng
    
    def test_get_score(self, engine):
        """Test getting score"""
        score = engine.get_score("agent-alpha")
        assert score is not None
        assert score.total_reviews >= 2
    
    def test_get_score_value(self, engine):
        """Test getting score value"""
        value = engine.get_score_value("agent-alpha")
        assert value > 0
    
    def test_add_review(self):
        """Test adding a review"""
        engine = ReputationEngine()
        
        review = Review(
            provider="new-agent",
            renter="test-renter",
            skill="test-skill",
            rating=5,
            completed_on_time=True,
            comment="Excellent!",
        )
        
        new_score = engine.add_review("new-agent", review)
        
        assert new_score.total_reviews == 1
        assert new_score.average_rating == 5.0
    
    def test_get_reviews(self, engine):
        """Test getting reviews"""
        reviews = engine.get_reviews("agent-alpha")
        assert isinstance(reviews, list)
        assert len(reviews) >= 2
    
    def test_get_top_agents(self, engine):
        """Test getting top agents"""
        top = engine.get_top_agents(n=3)
        
        assert len(top) <= 3
        assert len(top) > 0
        # Should be sorted by score descending
        if len(top) >= 2:
            assert top[0][1] >= top[1][1]
    
    def test_format_score(self, engine):
        """Test formatting score for display"""
        formatted = engine.format_score("agent-alpha")
        
        assert "agent-alpha" in formatted
        assert "Reputation" in formatted
        assert "📊" in formatted


# ============ Integration Tests ============

class TestIdentityReputationIntegration:
    """Integration tests for identity + reputation"""
    
    def test_identity_and_reputation_link(self):
        """Test that identity and reputation can be linked"""
        # Create identity
        identity = AgentIdentity(
            name="test-agent",
            wallet_address="test.sol",
            public_key="test-pubkey",
        )
        
        # Create reputation
        engine = ReputationEngine()
        
        # Add review
        review = Review(
            provider="test.sol",  # Use wallet as ID
            renter="renter.sol",
            skill="test-skill",
            rating=5,
            completed_on_time=True,
            comment="Perfect!",
        )
        engine.add_review("test.sol", review)
        
        # Verify
        score = engine.get_score("test.sol")
        assert score is not None
        assert score.average_rating == 5.0


# ============ Pytest Configuration ==========

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ========== Run Tests ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
