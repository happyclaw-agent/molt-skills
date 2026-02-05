"""
Unit Tests for Escrow Contract Interface

Purpose:
    Simple synchronous unit tests for escrow module.
    Tests verify escrow state machine and basic operations.
    
Usage:
    pytest src/tests/unit/test_escrow.py -v
"""

import pytest
from datetime import datetime, timedelta

from src.clawtrust.sdk.escrow import (
    EscrowClient,
    EscrowTerms,
    EscrowState,
    EscrowAccount,
    EscrowTransaction,
    ESCROW_PROGRAM_ID,
    USDC_MINT,
)


# ============ EscrowTerms Tests ============

class TestEscrowTerms:
    """Tests for EscrowTerms"""
    
    def test_create_terms(self):
        """Test creating escrow terms"""
        terms = EscrowTerms(
            skill_name="image-generation",
            price_usdc=10000,  # 0.01 USDC
            duration_seconds=3600,
        )
        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 10000
        assert terms.duration_seconds == 3600
    
    def test_terms_serialization(self):
        """Test terms to dict"""
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=5000,
            duration_seconds=1800,
            metadata_uri="ipfs://QmTest",
        )
        data = terms.to_dict()
        assert data["skill_name"] == "test"
        assert data["price_usdc"] == 5000
        assert data["duration_seconds"] == 1800
        assert data["metadata_uri"] == "ipfs://QmTest"
    
    def test_price_conversion(self):
        """Test USD to microUSDC conversion"""
        # 0.01 USDC = 10,000 microUSDC
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        assert terms.price_usdc == 10000


# ============ EscrowAccount Tests ============

class TestEscrowAccount:
    """Tests for EscrowAccount"""
    
    def test_created_state(self, created_escrow):
        """Test escrow in CREATED state"""
        assert created_escrow.state == EscrowState.CREATED
        assert created_escrow.amount == 0
        assert created_escrow.renter == ""
    
    def test_funded_state(self, funded_escrow):
        """Test escrow in FUNDED state"""
        assert funded_escrow.state == EscrowState.FUNDED
        assert funded_escrow.amount == 10000
        assert funded_escrow.renter == "agent-alpha"
    
    def test_completed_state(self, completed_escrow):
        """Test escrow in COMPLETED state"""
        assert completed_escrow.state == EscrowState.COMPLETED
        assert completed_escrow.amount == 10000
        assert completed_escrow.completed_at is not None
    
    def test_not_expired_just_created(self, created_escrow):
        """Test escrow is not expired when just created"""
        assert created_escrow.is_expired() is False
    
    def test_expired_after_duration(self, funded_escrow):
        """Test escrow is expired after duration passes"""
        # Set created 2 hours ago with 1 hour duration
        funded_escrow.created_at = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        assert funded_escrow.is_expired() is True
    
    def test_not_expired_within_duration(self, funded_escrow):
        """Test escrow is not expired within duration"""
        funded_escrow.created_at = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        assert funded_escrow.is_expired() is False
    
    def test_account_to_dict(self, created_escrow):
        """Test account serialization"""
        data = created_escrow.to_dict()
        assert data["address"] == "test-escrow-123"
        assert data["provider"] == "happyclaw-agent"
        assert data["state"] == "created"
        assert data["amount"] == 0


# ============ EscrowState Tests ============

class TestEscrowState:
    """Tests for EscrowState enum"""
    
    def test_all_states_defined(self):
        """Verify all expected states exist"""
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.COMPLETED.value == "completed"
        assert EscrowState.CANCELLED.value == "cancelled"
    
    def test_state_order(self):
        """Test state transitions are distinct"""
        assert EscrowState.CREATED != EscrowState.FUNDED
        assert EscrowState.FUNDED != EscrowState.COMPLETED
        assert EscrowState.COMPLETED != EscrowState.CANCELLED


# ============ EscrowTransaction Tests ============

class TestEscrowTransaction:
    """Tests for EscrowTransaction"""
    
    def test_successful_transaction(self):
        """Test successful transaction"""
        tx = EscrowTransaction(
            tx_signature="tx-abc123",
            escrow_address="escrow-xyz",
            success=True,
        )
        assert tx.success is True
        assert tx.tx_signature == "tx-abc123"
        assert tx.escrow_address == "escrow-xyz"
        assert tx.error is None
    
    def test_failed_transaction(self):
        """Test failed transaction"""
        tx = EscrowTransaction(
            tx_signature="",
            success=False,
            error="Escrow not found",
        )
        assert tx.success is False
        assert "not found" in tx.error


# ============ EscrowClient Tests ============

class TestEscrowClient:
    """Tests for EscrowClient (sync methods)"""
    
    def test_client_init(self):
        """Test client initialization"""
        client = EscrowClient()
        assert client.network == "devnet"
        assert client.USDC_MINT == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    def test_client_mainnet(self):
        """Test client on mainnet"""
        client = EscrowClient(network="mainnet")
        assert client.network == "mainnet"
    
    def test_create_escrow_terms_helper(self):
        """Test create_escrow_terms helper function"""
        from src.clawtrust.sdk.escrow import create_escrow_terms
        
        terms = create_escrow_terms(
            skill_name="code-review",
            price_usdc=0.05,  # 0.05 USDC
            duration_seconds=7200,
        )
        assert terms.skill_name == "code-review"
        assert terms.price_usdc == 50000  # 0.05 * 1_000_000
        assert terms.duration_seconds == 7200
    
    def test_format_escrow(self, funded_escrow):
        """Test escrow formatting"""
        client = EscrowClient()
        formatted = client.format_escrow(funded_escrow)
        
        assert "Escrow" in formatted
        assert "happyclaw-agent" in formatted
        assert "agent-alpha" in formatted
        assert "💰" in formatted  # Status emoji for FUNDED


# ============ Integration Tests ============

class TestEscrowStateMachine:
    """Integration tests for escrow state machine"""
    
    def test_full_escrow_state_transitions(self):
        """Test complete escrow lifecycle (sync parts only)"""
        # Create terms
        terms = EscrowTerms(
            skill_name="data-analysis",
            price_usdc=20000,
            duration_seconds=3600,
        )
        
        # Create account
        escrow = EscrowAccount(
            address="lifecycle-test",
            provider="provider-agent",
            renter="",
            terms=terms,
            state=EscrowState.CREATED,
            amount=0,
            created_at=datetime.utcnow().isoformat(),
        )
        
        # Verify initial state
        assert escrow.state == EscrowState.CREATED
        assert escrow.amount == 0
        
        # Simulate funding
        escrow.renter = "renter-agent"
        escrow.amount = 20000
        escrow.state = EscrowState.FUNDED
        
        assert escrow.state == EscrowState.FUNDED
        assert escrow.renter == "renter-agent"
        assert escrow.amount == 20000
        
        # Simulate completion
        escrow.state = EscrowState.COMPLETED
        escrow.completed_at = datetime.utcnow().isoformat()
        
        assert escrow.state == EscrowState.COMPLETED
        assert escrow.completed_at is not None


# ============ Pytest Fixtures ============

@pytest.fixture
def sample_terms():
    """Create sample escrow terms"""
    return EscrowTerms(
        skill_name="image-generation",
        price_usdc=10000,
        duration_seconds=3600,
        metadata_uri="ipfs://QmTest...",
    )


@pytest.fixture
def created_escrow(sample_terms):
    """Create an escrow in CREATED state"""
    return EscrowAccount(
        address="test-escrow-123",
        provider="happyclaw-agent",
        renter="",
        terms=sample_terms,
        state=EscrowState.CREATED,
        amount=0,
        created_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def funded_escrow(sample_terms):
    """Create an escrow in FUNDED state"""
    return EscrowAccount(
        address="test-escrow-123",
        provider="happyclaw-agent",
        renter="agent-alpha",
        terms=sample_terms,
        state=EscrowState.FUNDED,
        amount=10000,
        created_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def completed_escrow(sample_terms):
    """Create an escrow in COMPLETED state"""
    return EscrowAccount(
        address="test-escrow-123",
        provider="happyclaw-agent",
        renter="agent-alpha",
        terms=sample_terms,
        state=EscrowState.COMPLETED,
        amount=10000,
        created_at=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
        completed_at=datetime.utcnow().isoformat(),
    )


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
