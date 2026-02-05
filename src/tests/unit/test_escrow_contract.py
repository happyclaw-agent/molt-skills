"""
Tests for Escrow Contract
"""

import pytest


class TestEscrowTerms:
    """Tests for EscrowTerms dataclass"""
    
    def test_escrow_terms_creation(self):
        """Test creating escrow terms"""
        from src.trustyclaw.sdk.escrow_contract import EscrowTerms
        
        terms = EscrowTerms(
            renter="renter-addr",
            provider="provider-addr",
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="abc123def456",
        )
        
        assert terms.renter == "renter-addr"
        assert terms.provider == "provider-addr"
        assert terms.amount == 1000000
        assert terms.duration_hours == 24
    
    def test_escrow_terms_to_dict(self):
        """Test serialization"""
        from src.trustyclaw.sdk.escrow_contract import EscrowTerms
        
        terms = EscrowTerms(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        
        data = terms.to_dict()
        
        assert data["renter"] == "r"
        assert data["amount"] == 100


class TestEscrow:
    """Tests for Escrow dataclass"""
    
    def test_escrow_creation(self):
        """Test creating an escrow"""
        from src.trustyclaw.sdk.escrow_contract import Escrow, EscrowTerms, EscrowState
        
        terms = EscrowTerms(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="hash",
        )
        
        escrow = Escrow(
            escrow_id="test-escrow",
            terms=terms,
        )
        
        assert escrow.escrow_id == "test-escrow"
        assert escrow.state == EscrowState.CREATED
        assert escrow.funded_at is None
    
    def test_escrow_to_dict(self):
        """Test escrow serialization"""
        from src.trustyclaw.sdk.escrow_contract import Escrow, EscrowTerms
        
        terms = EscrowTerms(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        
        escrow = Escrow(escrow_id="test", terms=terms)
        data = escrow.to_dict()
        
        assert data["escrow_id"] == "test"
        assert data["state"] == "created"
        assert data["terms"]["amount"] == 100


class TestEscrowClient:
    """Tests for EscrowClient"""
    
    @pytest.fixture
    def client(self):
        """Create a fresh client with mock data"""
        from src.trustyclaw.sdk.escrow_contract import EscrowClient
        return EscrowClient(mock=True)
    
    def test_create_escrow(self, client):
        """Test creating a new escrow"""
        escrow = client.create_escrow(
            renter="renter-new",
            provider="provider-new",
            skill_id="code-gen",
            amount=500000,
            duration_hours=12,
            deliverable_hash="newhash",
        )
        
        assert escrow.escrow_id.startswith("escrow-")
        assert escrow.state.value == "created"
        assert escrow.terms.renter == "renter-new"
    
    def test_get_escrow(self, client):
        """Test retrieving an escrow"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        
        retrieved = client.get_escrow(escrow.escrow_id)
        
        assert retrieved is not None
        assert retrieved.escrow_id == escrow.escrow_id
    
    def test_fund_escrow(self, client):
        """Test funding an escrow"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        
        funded = client.fund_escrow(escrow.escrow_id)
        
        assert funded.state.value == "funded"
        assert funded.funded_at is not None
    
    def test_activate_escrow(self, client):
        """Test activating an escrow"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        
        active = client.activate_escrow(escrow.escrow_id)
        
        assert active.state.value == "active"
    
    def test_complete_escrow(self, client):
        """Test completing an escrow"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        
        completed = client.complete_escrow(escrow.escrow_id, "deliverable-hash")
        
        assert completed.state.value == "completed"
        assert completed.actual_deliverable_hash == "deliverable-hash"
    
    def test_verify_deliverable_match(self, client):
        """Test deliverable verification - match"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="expected-hash",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.complete_escrow(escrow.escrow_id, "expected-hash")
        
        result = client.verify_deliverable(escrow.escrow_id, "expected-hash")
        
        assert result["valid"] is True
    
    def test_verify_deliverable_mismatch(self, client):
        """Test deliverable verification - mismatch"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="expected",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.complete_escrow(escrow.escrow_id, "wrong-hash")
        
        result = client.verify_deliverable(escrow.escrow_id, "expected")
        
        assert result["valid"] is False
    
    def test_release_escrow(self, client):
        """Test releasing escrow to provider"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.complete_escrow(escrow.escrow_id, "h")
        
        released = client.release_escrow(escrow.escrow_id)
        
        assert released.state.value == "released"
        assert released.released_at is not None
    
    def test_release_amount(self, client):
        """Test release amount is full amount"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.complete_escrow(escrow.escrow_id, "h")
        client.release_escrow(escrow.escrow_id)
        
        amount = client.release_amount_for_escrow(escrow.escrow_id)
        
        assert amount == 1000000
    
    def test_refund_escrow(self, client):
        """Test refunding escrow to renter"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        
        refunded = client.refund_escrow(escrow.escrow_id)
        
        assert refunded.state.value == "refunded"
        assert refunded.refunded_at is not None
    
    def test_refund_amount_with_fee(self, client):
        """Test refund amount includes platform fee"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.refund_escrow(escrow.escrow_id)
        
        amount = client.refund_amount_for_escrow(escrow.escrow_id)
        
        assert amount == 990000  # 99%
    
    def test_dispute_escrow(self, client):
        """Test filing a dispute"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        
        disputed = client.dispute_escrow(escrow.escrow_id, "Poor quality work")
        
        assert disputed.state.value == "disputed"
        assert disputed.dispute_reason == "Poor quality work"
    
    def test_resolve_dispute_released(self, client):
        """Test resolving dispute - release to provider"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.dispute_escrow(escrow.escrow_id, "reason")
        
        resolved = client.resolve_dispute(escrow.escrow_id, "released")
        
        assert resolved.state.value == "released"
        assert resolved.dispute_resolution == "released"
    
    def test_resolve_dispute_refunded(self, client):
        """Test resolving dispute - refund to renter"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        client.fund_escrow(escrow.escrow_id)
        client.activate_escrow(escrow.escrow_id)
        client.dispute_escrow(escrow.escrow_id, "reason")
        
        resolved = client.resolve_dispute(escrow.escrow_id, "refunded")
        
        assert resolved.state.value == "refunded"
        assert resolved.dispute_resolution == "refunded"
    
    def test_cancel_escrow(self, client):
        """Test cancelling an unfunded escrow"""
        escrow = client.create_escrow(
            renter="r",
            provider="p",
            skill_id="s",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="h",
        )
        
        cancelled = client.cancel_escrow(escrow.escrow_id)
        
        assert cancelled.state.value == "cancelled"
    
    def test_get_escrows_by_participant(self, client):
        """Test getting escrows by participant"""
        client.create_escrow(
            renter="renter-search",
            provider="provider",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverable_hash="h",
        )
        
        escrows = client.get_escrows_by_participant("renter-search")
        
        assert len(escrows) >= 1
        for e in escrows:
            assert e.terms.renter == "renter-search" or e.terms.provider == "renter-search"
    
    def test_export_escrows_json(self, client):
        """Test exporting escrows as JSON"""
        json_str = client.export_escrows_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) > 0


class TestEscrowState:
    """Tests for EscrowState enum"""
    
    def test_all_states_exist(self):
        """Test all expected states exist"""
        from src.trustyclaw.sdk.escrow_contract import EscrowState
        
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.ACTIVE.value == "active"
        assert EscrowState.COMPLETED.value == "completed"
        assert EscrowState.DISPUTED.value == "disputed"
        assert EscrowState.RELEASED.value == "released"
        assert EscrowState.REFUNDED.value == "refunded"
        assert EscrowState.CANCELLED.value == "cancelled"


class TestGetEscrowClient:
    """Tests for get_escrow_client function"""
    
    def test_get_client_mock(self):
        """Test getting client with mock data"""
        from src.trustyclaw.sdk.escrow_contract import get_escrow_client
        
        client = get_escrow_client(mock=True)
        assert client.mock is True
    
    def test_get_client_mainnet(self):
        """Test getting client for mainnet"""
        from src.trustyclaw.sdk.escrow_contract import get_escrow_client
        
        client = get_escrow_client(network="mainnet", mock=False)
        assert client.network == "mainnet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
