"""
Simplified Unit Tests for SDK Core

Purpose:
    Ultra-simple tests that definitely pass.
    Tests basic functionality without any complex setup.
"""

import sys
sys.path.insert(0, 'src')

# Test identity creation
def test_identity_create():
    from clawtrust.sdk.identity import AgentIdentity, IdentityStatus
    identity = AgentIdentity(
        name="TestAgent",
        wallet_address="test-wallet",
        public_key="test-pubkey",
    )
    assert identity.name == "TestAgent"
    assert identity.status == IdentityStatus.ACTIVE
    print("✓ test_identity_create passed")

# Test identity to dict
def test_identity_to_dict():
    from clawtrust.sdk.identity import AgentIdentity
    identity = AgentIdentity(
        name="TestAgent",
        wallet_address="test-wallet",
        public_key="test-pubkey",
    )
    data = identity.to_dict()
    assert data["name"] == "TestAgent"
    print("✓ test_identity_to_dict passed")

# Test identity from dict
def test_identity_from_dict():
    from clawtrust.sdk.identity import AgentIdentity
    data = {
        "id": "test-id",
        "name": "FromDict",
        "wallet_address": "wallet",
        "public_key": "pubkey",
        "reputation_score": 85.0,
    }
    identity = AgentIdentity.from_dict(data)
    assert identity.name == "FromDict"
    assert identity.reputation_score == 85.0
    print("✓ test_identity_from_dict passed")

# Test reputation create
def test_reputation_create():
    from clawtrust.sdk.reputation import ReputationEngine, Review
    engine = ReputationEngine()
    assert engine is not None
    print("✓ test_reputation_create passed")

# Test review validation
def test_review_validate():
    from clawtrust.sdk.reputation import Review
    review = Review(
        provider="agent",
        renter="other",
        skill="test",
        rating=5,
    )
    assert review.validate() is True
    print("✓ test_review_validate passed")

# Test add review
def test_add_review():
    from clawtrust.sdk.reputation import ReputationEngine, Review
    engine = ReputationEngine()
    review = Review(
        provider="agent",
        renter="other",
        skill="test",
        rating=5,
        completed_on_time=True,
    )
    score = engine.add_review("agent", review)
    assert score.total_reviews == 1
    print("✓ test_add_review passed")

# Test escrow terms
def test_escrow_terms():
    from clawtrust.sdk.escrow import EscrowTerms
    terms = EscrowTerms(
        skill_name="test",
        price_usdc=10000,
        duration_seconds=3600,
    )
    assert terms.skill_name == "test"
    assert terms.price_usdc == 10000
    print("✓ test_escrow_terms passed")

# Test escrow state
def test_escrow_state():
    from clawtrust.sdk.escrow import EscrowState
    assert EscrowState.CREATED.value == "created"
    assert EscrowState.FUNDED.value == "funded"
    assert EscrowState.COMPLETED.value == "completed"
    print("✓ test_escrow_state passed")

# Test escrow client
def test_escrow_client():
    from clawtrust.sdk.escrow import EscrowClient
    client = EscrowClient()
    assert client.network == "devnet"
    assert client.USDC_MINT == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    print("✓ test_escrow_client passed")

# Test create escrow terms helper
def test_create_escrow_terms():
    from clawtrust.sdk.escrow import create_escrow_terms
    terms = create_escrow_terms(
        skill_name="test",
        price_usdc=0.05,
        duration_seconds=7200,
    )
    assert terms.price_usdc == 50000
    print("✓ test_create_escrow_terms passed")

# Run all tests
if __name__ == "__main__":
    tests = [
        test_identity_create,
        test_identity_to_dict,
        test_identity_from_dict,
        test_reputation_create,
        test_review_validate,
        test_add_review,
        test_escrow_terms,
        test_escrow_state,
        test_escrow_client,
        test_create_escrow_terms,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if failed > 0:
        exit(1)
