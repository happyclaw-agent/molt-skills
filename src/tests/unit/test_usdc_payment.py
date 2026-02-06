"""
Tests for USDC Payment Service

Comprehensive tests for USDC payment integration including:
- Payment intent creation and execution
- Escrow payment flow
- Balance notifications
- Multi-signature support
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json


class TestPaymentIntent:
    """Tests for PaymentIntent dataclass"""
    
    def test_amount_usd_property(self):
        """Test amount USD conversion"""
        from src.trustyclaw.sdk.usdc_payment import PaymentIntent, PaymentStatus
        
        intent = PaymentIntent(
            intent_id="pi-test-1",
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            amount=1_000_000,
            description="Test payment",
            status=PaymentStatus.PENDING,
        )
        
        assert intent.amount_usd == 1.0
    
    def test_to_dict(self):
        """Test intent to dictionary conversion"""
        from src.trustyclaw.sdk.usdc_payment import PaymentIntent, PaymentStatus
        
        intent = PaymentIntent(
            intent_id="pi-test-1",
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            amount=500_000,
            description="Test payment",
        )
        
        result = intent.to_dict()
        
        assert result["intent_id"] == "pi-test-1"
        assert result["amount"] == 500_000
        assert result["amount_usd"] == 0.5
        assert result["status"] == "pending"


class TestEscrowPayment:
    """Tests for EscrowPayment dataclass"""
    
    def test_amount_usd_property(self):
        """Test amount USD conversion"""
        from src.trustyclaw.sdk.usdc_payment import EscrowPayment, EscrowPaymentStatus
        
        payment = EscrowPayment(
            escrow_id="escrow-1",
            payment_intent_id="pi-1",
            amount=2_000_000,
            from_wallet="renter",
            to_wallet="provider",
        )
        
        assert payment.amount_usd == 2.0
    
    def test_is_fully_signed(self):
        """Test multisig signature checking"""
        from src.trustyclaw.sdk.usdc_payment import EscrowPayment
        
        payment = EscrowPayment(
            escrow_id="escrow-1",
            payment_intent_id="pi-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
            signatures={"signer1": "sig1"},
        )
        
        assert payment.is_fully_signed is False
        
        payment.signatures["signer2"] = "sig2"
        assert payment.is_fully_signed is True
    
    def test_to_dict(self):
        """Test payment to dictionary conversion"""
        from src.trustyclaw.sdk.usdc_payment import EscrowPayment
        
        payment = EscrowPayment(
            escrow_id="escrow-1",
            payment_intent_id="pi-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
        )
        
        result = payment.to_dict()
        
        assert result["escrow_id"] == "escrow-1"
        assert result["amount"] == 1_000_000
        assert result["amount_usd"] == 1.0


class TestUSDCPaymentService:
    """Tests for USDCPaymentService"""
    
    @pytest.fixture
    def service(self):
        """Create payment service with mocked USDC client"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient'):
            from src.trustyclaw.sdk.usdc_payment import USDCPaymentService
            return USDCPaymentService(network="devnet")
    
    def test_create_payment_intent_basic(self, service):
        """Test basic payment intent creation"""
        intent = service.create_payment_intent(
            amount=1_000_000,
            from_wallet="renter123",
            to_wallet="provider456",
            description="Image generation service",
        )
        
        assert intent is not None
        assert intent.from_wallet == "renter123"
        assert intent.to_wallet == "provider456"
        assert intent.amount == 1_000_000
        assert intent.status.value == "pending"
        assert intent.intent_id.startswith("pi-")
    
    def test_create_payment_intent_with_metadata(self, service):
        """Test payment intent with metadata"""
        metadata = {"skill_id": "image-gen", "order_id": "order-123"}
        
        intent = service.create_payment_intent(
            amount=500_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Payment with metadata",
            metadata=metadata,
        )
        
        assert intent.metadata == metadata
    
    def test_create_payment_intent_invalid_amount(self, service):
        """Test payment intent with invalid amount"""
        from src.trustyclaw.sdk.usdc_payment import PaymentError
        
        with pytest.raises(PaymentError):
            service.create_payment_intent(
                amount=-100,
                from_wallet="wallet-1",
                to_wallet="wallet-2",
                description="Invalid payment",
            )
    
    def test_create_payment_intent_below_minimum(self, service):
        """Test payment intent below minimum amount"""
        from src.trustyclaw.sdk.usdc_payment import PaymentError
        
        with pytest.raises(PaymentError):
            service.create_payment_intent(
                amount=100,
                from_wallet="wallet-1",
                to_wallet="wallet-2",
                description="Below minimum",
            )
    
    def test_get_payment_intent(self, service):
        """Test retrieving a payment intent"""
        created = service.create_payment_intent(
            amount=1_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Test payment",
        )
        
        retrieved = service.get_payment_intent(created.intent_id)
        
        assert retrieved is not None
        assert retrieved.intent_id == created.intent_id
    
    def test_get_nonexistent_intent(self, service):
        """Test retrieving non-existent intent"""
        result = service.get_payment_intent("pi-nonexistent")
        assert result is None
    
    def test_cancel_payment_intent_pending(self, service):
        """Test cancelling a pending payment intent"""
        intent = service.create_payment_intent(
            amount=1_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Test payment",
        )
        
        result = service.cancel_payment_intent(intent.intent_id)
        
        assert result.success is True
        assert result.status.value == "cancelled"
        
        updated = service.get_payment_intent(intent.intent_id)
        assert updated.status.value == "cancelled"


class TestEscrowPayments:
    """Tests for escrow payment functionality"""
    
    @pytest.fixture
    def service(self):
        """Create payment service"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient'):
            from src.trustyclaw.sdk.usdc_payment import USDCPaymentService
            return USDCPaymentService(network="devnet")
    
    def test_execute_escrow_payment(self, service):
        """Test executing an escrow payment"""
        escrow = service.execute_escrow_payment(
            escrow_id="escrow-hackathon-1",
            amount=5_000_000,
            from_wallet="renter-wallet",
            to_wallet="provider-wallet",
            description="Hackathon project payment",
        )
        
        assert escrow is not None
        assert escrow.escrow_id == "escrow-hackathon-1"
        assert escrow.amount == 5_000_000
        assert escrow.status.value == "pending"
        assert escrow.payment_intent_id.startswith("pi-")
    
    def test_fund_escrow_payment(self, service):
        """Test funding an escrow payment"""
        escrow = service.execute_escrow_payment(
            escrow_id="escrow-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
            description="Test escrow",
        )
        
        result = service.fund_escrow_payment(escrow.escrow_id)
        
        assert result.success is True
        assert result.signature is not None
        
        updated = service.get_escrow_payment(escrow.escrow_id)
        assert updated.status.value == "funded"
        assert updated.funded_at is not None
    
    def test_release_escrow_payment(self, service):
        """Test releasing escrow funds"""
        escrow = service.execute_escrow_payment(
            escrow_id="escrow-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
            description="Test escrow",
        )
        
        service.fund_escrow_payment(escrow.escrow_id)
        
        result = service.release_escrow_payment(
            escrow_id=escrow.escrow_id,
            authority="renter",
        )
        
        assert result.success is True
        
        updated = service.get_escrow_payment(escrow.escrow_id)
        assert updated.status.value == "released"
        assert updated.released_at is not None
    
    def test_refund_escrow_payment(self, service):
        """Test refunding escrow funds"""
        escrow = service.execute_escrow_payment(
            escrow_id="escrow-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
            description="Test escrow",
        )
        
        service.fund_escrow_payment(escrow.escrow_id)
        
        result = service.refund_escrow_payment(escrow.escrow_id)
        
        assert result.success is True
        
        updated = service.get_escrow_payment(escrow.escrow_id)
        assert updated.status.value == "refunded"
        assert updated.refunded_at is not None


class TestPaymentHistory:
    """Tests for payment history functionality"""
    
    @pytest.fixture
    def service(self):
        """Create payment service"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient'):
            from src.trustyclaw.sdk.usdc_payment import USDCPaymentService
            return USDCPaymentService(network="devnet")
    
    def test_get_payment_history_empty(self, service):
        """Test getting payment history when empty"""
        history = service.get_payment_history("wallet-1")
        
        assert history == []
    
    def test_get_payment_history_with_payments(self, service):
        """Test getting payment history with payments"""
        intent = service.create_payment_intent(
            amount=1_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Payment 1",
        )
        service.execute_payment_intent(intent.intent_id)
        
        intent2 = service.create_payment_intent(
            amount=2_000_000,
            from_wallet="wallet-2",
            to_wallet="wallet-3",
            description="Payment 2",
        )
        service.execute_payment_intent(intent2.intent_id)
        
        history = service.get_payment_history("wallet-1")
        
        assert len(history) == 1
        assert history[0].from_wallet == "wallet-1"
    
    def test_get_payment_history_with_limit(self, service):
        """Test payment history with limit"""
        for i in range(5):
            intent = service.create_payment_intent(
                amount=1_000_000,
                from_wallet=f"wallet-{i}",
                to_wallet="wallet-dest",
                description=f"Payment {i}",
            )
            service.execute_payment_intent(intent.intent_id)
        
        history = service.get_payment_history("wallet-dest", limit=3)
        
        assert len(history) == 3


class TestBalanceNotifications:
    """Tests for balance notification functionality"""
    
    @pytest.fixture
    def service(self):
        """Create payment service with mocked USDC client"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient') as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_balance.return_value = 5.0
            
            from src.trustyclaw.sdk.usdc_payment import USDCPaymentService
            service = USDCPaymentService(network="devnet")
            service.usdc_client = mock_client
            return service
    
    def test_register_balance_notification(self, service):
        """Test registering a balance notification"""
        notification = service.register_balance_notification(
            wallet_address="wallet-1",
            threshold_usd=10.0,
            callback_url="https://example.com/webhook",
            auto_reload=True,
            auto_reload_amount=100_000_000,
        )
        
        assert notification is not None
        assert notification.wallet_address == "wallet-1"
        assert notification.threshold_usd == 10.0
        assert notification.auto_reload_enabled is True
    
    def test_check_balance_below_threshold(self, service):
        """Test balance check when below threshold"""
        service.register_balance_notification(
            wallet_address="wallet-1",
            threshold_usd=10.0,
        )
        
        result = service.check_balance_and_notify("wallet-1")
        
        assert result["alert_sent"] is True
        assert result["current_balance"] == 5.0
        assert result["threshold"] == 10.0
    
    def test_check_balance_above_threshold(self, service):
        """Test balance check when above threshold"""
        service.usdc_client.get_balance.return_value = 100.0
        
        service.register_balance_notification(
            wallet_address="wallet-1",
            threshold_usd=10.0,
        )
        
        result = service.check_balance_and_notify("wallet-1")
        
        assert result["alert_sent"] is False
        assert "above threshold" in result["reason"]
    
    def test_unregistered_wallet_check(self, service):
        """Test checking balance for unregistered wallet"""
        result = service.check_balance_and_notify("unregistered-wallet")
        
        assert result["alert_sent"] is False
        assert "No notification registered" in result["reason"]


class TestMultisigSupport:
    """Tests for multi-signature support"""
    
    @pytest.fixture
    def service(self):
        """Create payment service with multisig config"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient'):
            from src.trustyclaw.sdk.usdc_payment import (
                USDCPaymentService,
                MultisigConfig,
            )
            
            service = USDCPaymentService(network="devnet")
            service.set_multisig_config(MultisigConfig(
                threshold_usd=100.0,
                required_signers=["signer1", "signer2", "signer3"],
                required_count=2,
                recovery_signer="recovery-wallet",
            ))
            return service
    
    def test_multisig_payment_creation(self, service):
        """Test creating payment above threshold requires multisig"""
        intent = service.create_payment_intent(
            amount=200_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Large payment",
        )
        
        assert intent.metadata.get("requires_multisig") is True
        assert intent.metadata["signers_required"] == ["signer1", "signer2", "signer3"]
    
    def test_small_payment_no_multisig(self, service):
        """Test payment below threshold doesn't require multisig"""
        intent = service.create_payment_intent(
            amount=50_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Small payment",
        )
        
        assert intent.metadata.get("requires_multisig") is not True
    
    def test_collect_multisig_signature(self, service):
        """Test collecting signatures for multisig"""
        intent = service.create_payment_intent(
            amount=200_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Multisig payment",
        )
        
        result1 = service.collect_multisig_signature(
            intent.intent_id,
            signer="signer1",
            signature="signature-1",
        )
        
        assert result1["success"] is True
        assert result1["multisig_complete"] is False
        assert result1["signatures_needed"] == 1
        
        result2 = service.collect_multisig_signature(
            intent.intent_id,
            signer="signer2",
            signature="signature-2",
        )
        
        assert result2["multisig_complete"] is True
    
    def test_unauthorized_signer(self, service):
        """Test collecting signature from unauthorized signer"""
        intent = service.create_payment_intent(
            amount=200_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Multisig payment",
        )
        
        result = service.collect_multisig_signature(
            intent.intent_id,
            signer="unauthorized-signer",
            signature="fake-sig",
        )
        
        assert result["success"] is False
        assert "not authorized" in result["error"]
    
    def test_initiate_recovery(self, service):
        """Test initiating payment recovery"""
        intent = service.create_payment_intent(
            amount=200_000_000,
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            description="Stuck payment",
        )
        
        result = service.initiate_recovery(
            intent_id=intent.intent_id,
            recovery_wallet="recovery-wallet",
            reason="Payment stuck in processing",
        )
        
        assert result["success"] is True
        assert result["recovery_initiated"] is True


class TestPaymentResult:
    """Tests for PaymentResult dataclass"""
    
    def test_successful_result(self):
        """Test successful payment result"""
        from src.trustyclaw.sdk.usdc_payment import PaymentResult, PaymentStatus
        
        result = PaymentResult(
            success=True,
            payment_intent_id="pi-test",
            signature="sig-123",
            status=PaymentStatus.CONFIRMED,
            explorer_url="https://explorer.solana.com/tx/sig-123",
        )
        
        assert result.success is True
        assert result.error is None
    
    def test_failed_result(self):
        """Test failed payment result"""
        from src.trustyclaw.sdk.usdc_payment import PaymentResult
        
        result = PaymentResult(
            success=False,
            error="Insufficient funds",
        )
        
        assert result.success is False
        assert result.error == "Insufficient funds"
    
    def test_to_dict(self):
        """Test result to dictionary conversion"""
        from src.trustyclaw.sdk.usdc_payment import PaymentResult, PaymentStatus
        
        result = PaymentResult(
            success=True,
            payment_intent_id="pi-test",
            signature="sig-123",
            status=PaymentStatus.CONFIRMED,
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["payment_intent_id"] == "pi-test"
        assert data["status"] == "confirmed"


class TestGetPaymentService:
    """Tests for factory function"""
    
    def test_get_usdc_payment_service(self):
        """Test getting payment service via factory"""
        with patch('src.trustyclaw.sdk.usdc_payment.USDCClient'):
            from src.trustyclaw.sdk.usdc_payment import get_usdc_payment_service
            
            service = get_usdc_payment_service(
                network="mainnet",
                multisig_threshold_usd=500.0,
                recovery_wallet="recovery123",
            )
            
            assert service.network == "mainnet"
            assert service.multisig_config.threshold_usd == 500.0
            assert service.multisig_config.recovery_signer == "recovery123"


class TestBalanceNotificationDataclass:
    """Tests for BalanceNotification dataclass"""
    
    def test_threshold_micro_conversion(self):
        """Test threshold USD to microUSDC conversion"""
        from src.trustyclaw.sdk.usdc_payment import BalanceNotification
        
        notification = BalanceNotification(
            wallet_address="wallet-1",
            threshold_usd=25.50,
        )
        
        assert notification.threshold_micro == 25_500_000
    
    def test_defaults(self):
        """Test default values"""
        from src.trustyclaw.sdk.usdc_payment import BalanceNotification
        
        notification = BalanceNotification(
            wallet_address="wallet-1",
            threshold_usd=10.0,
        )
        
        assert notification.auto_reload_enabled is False
        assert notification.auto_reload_amount == 100_000_000
        assert notification.reload_count_today == 0


class TestPaymentDataclass:
    """Tests for Payment historical record"""
    
    def test_amount_usd_property(self):
        """Test USD conversion"""
        from src.trustyclaw.sdk.usdc_payment import Payment, PaymentStatus
        
        payment = Payment(
            payment_id="pay-123",
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            amount=1_500_000,
            description="Service payment",
            status=PaymentStatus.CONFIRMED,
            signature="sig-123",
            created_at="2024-01-01T00:00:00",
            confirmed_at="2024-01-01T00:01:00",
        )
        
        assert payment.amount_usd == 1.5


class TestPaymentStatusEnum:
    """Tests for PaymentStatus enum"""
    
    def test_all_statuses(self):
        """Test all payment statuses exist"""
        from src.trustyclaw.sdk.usdc_payment import PaymentStatus
        
        statuses = [
            "pending",
            "processing",
            "confirmed",
            "finalized",
            "failed",
            "cancelled",
        ]
        
        for status in statuses:
            assert hasattr(PaymentStatus, status.upper())


class TestEscrowPaymentStatusEnum:
    """Tests for EscrowPaymentStatus enum"""
    
    def test_all_statuses(self):
        """Test all escrow payment statuses exist"""
        from src.trustyclaw.sdk.usdc_payment import EscrowPaymentStatus
        
        statuses = [
            "pending",
            "funded",
            "released",
            "refunded",
            "disputed",
        ]
        
        for status in statuses:
            assert hasattr(EscrowPaymentStatus, status.upper())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
