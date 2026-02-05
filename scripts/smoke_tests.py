"""
Smoke Tests for SDK Core Modules

Purpose:
    Simple smoke tests that can run without pytest.
    These verify basic functionality without complex mocking.
    
Usage:
    python scripts/smoke_tests.py
"""

import asyncio
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from clawtrust.sdk.client import SolanaClient, ClientConfig, Network
from clawtrust.sdk.identity import AgentIdentity, IdentityManager, IdentityStatus
from clawtrust.sdk.reputation import ReputationEngine, Review
from clawtrust.sdk.escrow import (
    EscrowClient, EscrowTerms, EscrowState, EscrowAccount
)


def test_imports():
    """Verify all modules import correctly"""
    print("Testing imports...")
    try:
        from clawtrust.sdk.client import SolanaClient, ClientConfig, Network
        from clawtrust.sdk.identity import AgentIdentity, IdentityManager
        from clawtrust.sdk.reputation import ReputationEngine, Review
        from clawtrust.sdk.escrow import EscrowClient, EscrowTerms, EscrowState
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_identity():
    """Test identity creation and management"""
    print("\nTesting Identity...")
    try:
        # Create identity
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
            email="test@example.com",
        )
        assert identity.name == "TestAgent"
        assert identity.status == IdentityStatus.ACTIVE
        
        # Test serialization
        data = identity.to_dict()
        assert data["name"] == "TestAgent"
        
        # Test deserialization
        restored = AgentIdentity.from_dict(data)
        assert restored.name == identity.name
        
        print("  ✓ Identity creation and serialization")
        return True
    except Exception as e:
        print(f"  ✗ Identity test failed: {e}")
        return False


def test_identity_manager():
    """Test identity manager"""
    print("\nTesting IdentityManager...")
    try:
        manager = IdentityManager()
        
        # Create and register
        identity = AgentIdentity(
            name="SmokeTestAgent",
            wallet_address="smoke-test.sol",
            public_key="smoke-pubkey",
        )
        manager.register(identity)
        
        # Query
        retrieved = manager.get_by_wallet("smoke-test.sol")
        assert retrieved is not None
        assert retrieved.name == "SmokeTestAgent"
        
        # List
        all_ids = manager.list_identities()
        assert len(all_ids) >= 1
        
        print("  ✓ IdentityManager operations")
        return True
    except Exception as e:
        print(f"  ✗ IdentityManager test failed: {e}")
        return False


def test_reputation():
    """Test reputation engine"""
    print("\nTesting Reputation...")
    try:
        engine = ReputationEngine()
        
        # Create review
        review = Review(
            provider="test-agent",
            renter="renter-agent",
            skill="test-skill",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Great work!",
        )
        assert review.validate()
        
        # Add review
        score = engine.add_review("test-agent", review)
        assert score.total_reviews == 1
        assert score.average_rating == 5.0
        
        # Get score
        value = engine.get_score_value("test-agent")
        assert value > 0
        
        # Top agents
        top = engine.get_top_agents(n=5)
        assert len(top) >= 1
        
        print("  ✓ Reputation engine operations")
        return True
    except Exception as e:
        print(f"  ✗ Reputation test failed: {e}")
        return False


def test_escrow_terms():
    """Test escrow terms"""
    print("\nTesting EscrowTerms...")
    try:
        terms = EscrowTerms(
            skill_name="image-generation",
            price_usdc=10000,
            duration_seconds=3600,
        )
        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 10000
        
        # Serialization
        data = terms.to_dict()
        assert data["skill_name"] == "image-generation"
        
        print("  ✓ EscrowTerms creation and serialization")
        return True
    except Exception as e:
        print(f"  ✗ EscrowTerms test failed: {e}")
        return False


async def test_escrow_state_machine():
    """Test complete escrow state machine"""
    print("\nTesting Escrow State Machine...")
    try:
        client = EscrowClient()
        
        # Create terms
        terms = EscrowTerms(
            skill_name="test-skill",
            price_usdc=10000,
            duration_seconds=3600,
        )
        
        # 1. Initialize
        init_tx = await client.initialize(
            provider="provider-agent",
            mint=client.USDC_MINT,
            terms=terms,
        )
        assert init_tx.success
        escrow_addr = init_tx.escrow_address
        
        # Verify Created state
        state = await client.get_state(escrow_addr)
        assert state == EscrowState.CREATED
        
        # 2. Accept/Fund
        accept_tx = await client.accept(
            escrow_address=escrow_addr,
            renter="renter-agent",
            amount=10000,
        )
        assert accept_tx.success
        
        # Verify Funded state
        state = await client.get_state(escrow_addr)
        assert state == EscrowState.FUNDED
        
        # 3. Complete
        complete_tx = await client.complete(
            escrow_address=escrow_addr,
            authority="anyone",
        )
        assert complete_tx.success
        
        # Verify Completed state
        state = await client.get_state(escrow_addr)
        assert state == EscrowState.COMPLETED
        
        print("  ✓ Escrow state machine (Created → Funded → Completed)")
        return True
    except Exception as e:
        print(f"  ✗ Escrow state machine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_escrow_cancel():
    """Test escrow cancellation flow"""
    print("\nTesting Escrow Cancellation...")
    try:
        client = EscrowClient()
        
        terms = EscrowTerms(
            skill_name="cancel-test",
            price_usdc=5000,
            duration_seconds=1800,
        )
        
        # Initialize and fund
        init_tx = await client.initialize(
            provider="provider",
            mint=client.USDC_MINT,
            terms=terms,
        )
        await client.accept(init_tx.escrow_address, "renter", 5000)
        
        # Cancel
        cancel_tx = await client.cancel(
            escrow_address=init_tx.escrow_address,
            authority="provider",
        )
        assert cancel_tx.success
        
        # Verify Cancelled state
        state = await client.get_state(init_tx.escrow_address)
        assert state == EscrowState.CANCELLED
        
        print("  ✓ Escrow cancellation (Created → Funded → Cancelled)")
        return True
    except Exception as e:
        print(f"  ✗ Escrow cancel test failed: {e}")
        return False


async def run_async_tests():
    """Run all async tests"""
    results = []
    
    results.append(await test_escrow_state_machine())
    results.append(await test_escrow_cancel())
    
    return all(results)


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("ClawTrust SDK Smoke Tests")
    print("=" * 60)
    
    results = []
    
    # Sync tests
    results.append(test_imports())
    results.append(test_identity())
    results.append(test_identity_manager())
    results.append(test_reputation())
    results.append(test_escrow_terms())
    
    # Async tests
    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ All smoke tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
