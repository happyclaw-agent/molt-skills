"""
Tests for USDC Payment Service (simplified)
"""

import pytest


class TestPaymentIntent:
    """Tests for PaymentIntent dataclass"""
    
    def test_amount_usd_property(self):
        """Test amount USD conversion"""
        from trustyclaw.sdk.usdc_payment import PaymentIntent, PaymentStatus
        
        intent = PaymentIntent(
            intent_id="pi-test-1",
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            amount=1_000_000,
            description="Test payment",
        )
        
        assert intent.amount_usd == 1.0
    
    def test_to_dict(self):
        """Test intent to dictionary conversion"""
        from trustyclaw.sdk.usdc_payment import PaymentIntent
        
        intent = PaymentIntent(
            intent_id="pi-test-1",
            from_wallet="wallet-1",
            to_wallet="wallet-2",
            amount=500_000,
            description="Test payment",
        )
        
        result = intent.to_dict()
        
        assert result["intent_id"] == "pi-test-1"


class TestEscrowPayment:
    """Tests for EscrowPayment dataclass"""
    
    def test_amount_usd_property(self):
        """Test amount USD conversion"""
        from trustyclaw.sdk.usdc_payment import EscrowPayment
        
        payment = EscrowPayment(
            escrow_id="escrow-1",
            payment_intent_id="pi-1",
            amount=2_000_000,
            from_wallet="renter",
            to_wallet="provider",
        )
        
        assert payment.amount_usd == 2.0
    
    def test_to_dict(self):
        """Test payment to dictionary conversion"""
        from trustyclaw.sdk.usdc_payment import EscrowPayment
        
        payment = EscrowPayment(
            escrow_id="escrow-1",
            payment_intent_id="pi-1",
            amount=1_000_000,
            from_wallet="renter",
            to_wallet="provider",
        )
        
        result = payment.to_dict()
        
        assert result["escrow_id"] == "escrow-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
