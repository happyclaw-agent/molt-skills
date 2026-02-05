"""
Integration Tests for TrustyClaw SDK

Tests real blockchain integration and SDK workflows.
"""

import sys
import unittest
sys.path.insert(0, 'src')


class TestSolanaIntegration(unittest.TestCase):
    """Test Solana SDK integration"""
    
    def test_solana_client_creation(self):
        """Test client creation for different networks"""
        from trustyclaw.sdk.solana import get_client, Network
        
        # Devnet client
        client = get_client("devnet")
        self.assertEqual(client.network, Network.DEVNET)
        
        # Testnet client
        client = get_client("testnet")
        self.assertEqual(client.network, Network.TESTNET)
        
        # Mainnet client
        client = get_client("mainnet")
        self.assertEqual(client.network, Network.MAINNET)
    
    def test_wallet_info(self):
        """Test wallet info dataclass"""
        from trustyclaw.sdk.solana import WalletInfo
        
        wallet = WalletInfo(
            address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            lamports=1000000000,
            usdc_balance=100.0,
        )
        
        self.assertEqual(wallet.sol_balance, 1.0)  # 1e9 lamports = 1 SOL
        self.assertIn("GFeyFZL", wallet.address)
    
    def test_get_balance(self):
        """Test balance retrieval"""
        from trustyclaw.sdk.solana import get_client, WalletInfo
        
        client = get_client("devnet")
        balance = client.get_balance(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        self.assertIsInstance(balance, WalletInfo)
        self.assertGreater(balance.lamports, 0)
        self.assertGreaterEqual(balance.usdc_balance, 0)
    
    def test_escrow_pda_derivation(self):
        """Test escrow PDA derivation"""
        from trustyclaw.sdk.solana import get_client
        
        client = get_client("devnet")
        pda = client.derive_escrow_pda(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="image-generation",
        )
        
        self.assertIsInstance(pda, str)
        self.assertTrue(len(pda) > 0)
    
    def test_transaction_info(self):
        """Test transaction info dataclass"""
        from trustyclaw.sdk.solana import TransactionInfo
        
        tx = TransactionInfo(
            signature="abc123" * 8,
            slot=100,
            status="confirmed",
        )
        
        self.assertIn("explorer", tx.explorer_url)
        self.assertIn("abc123", tx.signature)


class TestUSDCIntegration(unittest.TestCase):
    """Test USDC SDK integration"""
    
    def test_usdc_client_creation(self):
        """Test USDC client creation"""
        from trustyclaw.sdk.usdc import get_usdc_client
        
        client = get_usdc_client("devnet")
        self.assertEqual(client.network, "devnet")
        self.assertIn("EPjFWdd", client.mint)
    
    def test_get_usdc_balance(self):
        """Test USDC balance retrieval"""
        from trustyclaw.sdk.usdc import get_usdc_client
        
        client = get_usdc_client("devnet")
        balance = client.get_balance(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        self.assertIsInstance(balance, float)
        self.assertGreaterEqual(balance, 0)
    
    def test_transfer_simulation(self):
        """Test transfer simulation"""
        from trustyclaw.sdk.usdc import get_usdc_client
        
        client = get_usdc_client("devnet")
        
        # Check that transfer would work (mock)
        result = client.transfer(
            from_wallet="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            to_wallet="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            amount=1000000,
        )
        
        # TransferResult has status attribute, not success
        self.assertTrue(hasattr(result, 'status'))
        self.assertEqual(str(result.status), 'TransferStatus.CONFIRMED')
        self.assertTrue(hasattr(result, 'signature'))
        self.assertIn("mock-transfer", result.signature)


class TestEscrowIntegration(unittest.TestCase):
    """Test Escrow contract integration"""
    
    def test_escrow_creation(self):
        """Test escrow creation workflow"""
        from trustyclaw.sdk.escrow_contract import get_escrow_client
        
        escrow = get_escrow_client("devnet")
        
        # Create escrow
        e = escrow.create_escrow(
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="abc123def456789",
        )
        
        self.assertIsNotNone(e.escrow_id)
        self.assertEqual(e.terms.amount, 1000000)
    
    def test_escrow_lifecycle(self):
        """Test full escrow lifecycle"""
        from trustyclaw.sdk.escrow_contract import get_escrow_client, EscrowState
        
        escrow = get_escrow_client("devnet")
        
        # Create
        e = escrow.create_escrow(
            renter="renter",
            provider="provider",
            skill_id="test",
            amount=500000,
            duration_hours=12,
            deliverable_hash="hash",
        )
        self.assertEqual(e.state, EscrowState.CREATED)
        
        # Fund
        e = escrow.fund_escrow(e.escrow_id)
        self.assertEqual(e.state, EscrowState.FUNDED)
        
        # Activate
        e = escrow.activate_escrow(e.escrow_id)
        self.assertEqual(e.state, EscrowState.ACTIVE)
        
        # Complete
        e = escrow.complete_escrow(e.escrow_id, "deliverable-hash")
        self.assertEqual(e.state, EscrowState.COMPLETED)
        
        # Release
        e = escrow.release_escrow(e.escrow_id)
        self.assertEqual(e.state, EscrowState.RELEASED)
    
    def test_dispute_flow(self):
        """Test dispute and resolution"""
        from trustyclaw.sdk.escrow_contract import get_escrow_client, EscrowState
        
        escrow = get_escrow_client("devnet")
        
        # Create and fund
        e = escrow.create_escrow(
            renter="renter",
            provider="provider",
            skill_id="test",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="hash",
        )
        escrow.fund_escrow(e.escrow_id)
        escrow.activate_escrow(e.escrow_id)
        
        # Dispute
        e = escrow.dispute_escrow(e.escrow_id, "Quality issues")
        self.assertEqual(e.state, EscrowState.DISPUTED)
        
        # Resolve - release
        e = escrow.resolve_dispute(e.escrow_id, "released")
        self.assertEqual(e.state, EscrowState.RELEASED)
    
    def test_refund_flow(self):
        """Test refund workflow"""
        from trustyclaw.sdk.escrow_contract import get_escrow_client, EscrowState
        
        escrow = get_escrow_client("devnet")
        
        e = escrow.create_escrow(
            renter="renter",
            provider="provider",
            skill_id="test",
            amount=1000000,
            duration_hours=24,
            deliverable_hash="hash",
        )
        escrow.fund_escrow(e.escrow_id)
        
        # Refund
        e = escrow.refund_escrow(e.escrow_id)
        self.assertEqual(e.state, EscrowState.REFUNDED)
        
        # Check refund amount (99%)
        amount = escrow.refund_amount_for_escrow(e.escrow_id)
        self.assertEqual(amount, 990000)


class TestReviewIntegration(unittest.TestCase):
    """Test Review system integration"""
    
    def test_review_creation(self):
        """Test review creation"""
        from trustyclaw.sdk.review_system import get_review_service
        
        service = get_review_service(mock=True)
        
        review = service.create_review(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            skill_id="image-generation",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Amazing work!",
        )
        
        self.assertIsNotNone(review.review_id)
        self.assertEqual(review.rating, 5)
    
    def test_review_submission(self):
        """Test review submission"""
        from trustyclaw.sdk.review_system import get_review_service, ReviewStatus
        
        service = get_review_service(mock=True)
        
        review = service.create_review(
            provider="provider",
            renter="renter",
            skill_id="test",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Good work",
        )
        
        service.submit_review(review.review_id)
        self.assertEqual(review.status, ReviewStatus.SUBMITTED)
    
    def test_rating_calculation(self):
        """Test agent rating calculation"""
        from trustyclaw.sdk.review_system import get_review_service
        
        service = get_review_service(mock=True)
        
        rating = service.calculate_agent_rating(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        self.assertIn("average_rating", rating)
        self.assertIn("total_reviews", rating)
        self.assertGreaterEqual(rating["average_rating"], 0)
    
    def test_dispute_flow(self):
        """Test dispute filing and resolution"""
        from trustyclaw.sdk.review_system import get_review_service, ReviewStatus
        
        service = get_review_service(mock=True)
        
        review = service.create_review(
            provider="provider",
            renter="renter",
            skill_id="test",
            rating=1,
            completed_on_time=False,
            output_quality="poor",
            comment="Bad work",
        )
        service.submit_review(review.review_id)
        
        # File dispute
        dispute = service.file_dispute(
            review.review_id,
            filed_by="provider",
            reason="Unfair rating",
        )
        
        self.assertIsNotNone(dispute.dispute_id)
        
        # Resolve dispute
        service.resolve_dispute(dispute.dispute_id, "approved", "Valid review")
        self.assertEqual(review.status, ReviewStatus.RESOLVED)


class TestMandateIntegration(unittest.TestCase):
    """Test Mandate skill integration"""
    
    def test_mandate_creation(self):
        """Test mandate creation"""
        from trustyclaw.skills.mandate import get_mandate_skill
        
        skill = get_mandate_skill(mock=True)
        
        mandate = skill.create_mandate(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            skill_id="image-generation",
            amount=500000,
            duration_hours=12,
            deliverables=["10 images", "1024x1024"],
            revisions=2,
        )
        
        self.assertIsNotNone(mandate.mandate_id)
        self.assertEqual(mandate.terms.amount, 500000)
    
    def test_mandate_lifecycle(self):
        """Test full mandate lifecycle"""
        from trustyclaw.skills.mandate import get_mandate_skill, MandateStatus
        
        skill = get_mandate_skill(mock=True)
        
        m = skill.create_mandate(
            provider="provider",
            renter="renter",
            skill_id="test",
            amount=100000,
            duration_hours=24,
            deliverables=["deliverable"],
        )
        
        # Submit
        skill.submit_mandate(m.mandate_id)
        self.assertEqual(m.status, MandateStatus.PENDING)
        
        # Accept
        skill.accept_mandate(m.mandate_id)
        self.assertEqual(m.status, MandateStatus.ACCEPTED)
        
        # Start
        skill.start_mandate(m.mandate_id)
        self.assertEqual(m.status, MandateStatus.ACTIVE)
        
        # Complete
        skill.complete_mandate(m.mandate_id, "final-hash")
        self.assertEqual(m.status, MandateStatus.COMPLETED)
    
    def test_rating(self):
        """Test mandate rating"""
        from trustyclaw.skills.mandate import get_mandate_skill
        
        skill = get_mandate_skill(mock=True)
        
        m = skill.create_mandate(
            provider="provider",
            renter="renter",
            skill_id="test",
            amount=100000,
            duration_hours=24,
            deliverables=["test"],
        )
        
        # Complete and rate
        skill.submit_mandate(m.mandate_id)
        skill.accept_mandate(m.mandate_id)
        skill.start_mandate(m.mandate_id)
        skill.complete_mandate(m.mandate_id, "hash")
        
        rated = skill.rate_mandate(
            m.mandate_id,
            renter_rating=5,
            provider_rating=4,
        )
        
        self.assertEqual(rated.renter_rating, 5)
        self.assertEqual(rated.provider_rating, 4)


class TestDiscoveryIntegration(unittest.TestCase):
    """Test Discovery skill integration"""
    
    def test_browse_skills(self):
        """Test browsing skills"""
        from trustyclaw.skills.discovery import get_discovery_skill
        
        discovery = get_discovery_skill(mock=True)
        skills = discovery.browse_skills()
        
        self.assertGreater(len(skills), 0)
        for s in skills:
            self.assertTrue(hasattr(s, 'skill_id'))
    
    def test_search_agents(self):
        """Test agent search"""
        from trustyclaw.skills.discovery import get_discovery_skill
        
        discovery = get_discovery_skill(mock=True)
        agents = discovery.search_agents(query="code")
        
        self.assertGreater(len(agents), 0)
    
    def test_get_agent_profile(self):
        """Test agent profile retrieval"""
        from trustyclaw.skills.discovery import get_discovery_skill
        
        discovery = get_discovery_skill(mock=True)
        profile = discovery.get_agent_profile(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        self.assertIsNotNone(profile)
        self.assertTrue(hasattr(profile, 'name'))
        self.assertTrue(hasattr(profile, 'rating'))
    
    def test_top_rated(self):
        """Test top rated agents"""
        from trustyclaw.skills.discovery import get_discovery_skill
        
        discovery = get_discovery_skill(mock=True)
        top = discovery.get_top_rated_agents(limit=5)
        
        self.assertLessEqual(len(top), 5)
        for i in range(len(top) - 1):
            self.assertGreaterEqual(top[i].rating, top[i + 1].rating)
    
    def test_marketplace_stats(self):
        """Test marketplace statistics"""
        from trustyclaw.skills.discovery import get_discovery_skill
        
        discovery = get_discovery_skill(mock=True)
        stats = discovery.get_marketplace_stats()
        
        self.assertIn("total_agents", stats)
        self.assertIn("total_skills", stats)
        self.assertGreater(stats["total_agents"], 0)


class TestReputationIntegration(unittest.TestCase):
    """Test Reputation skill integration"""
    
    def test_reputation_query(self):
        """Test reputation query"""
        from trustyclaw.skills.reputation import get_reputation_skill
        
        reputation = get_reputation_skill(mock=True)
        rep = reputation.get_agent_reputation("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q")
        
        self.assertIsNotNone(rep)
        self.assertIn("reputation_score", rep.to_dict())
    
    def test_reputation_tier(self):
        """Test reputation tier detection"""
        from trustyclaw.skills.reputation import get_reputation_skill
        
        reputation = get_reputation_skill(mock=True)
        
        # Elite tier
        tier = reputation.get_reputation_tier(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        self.assertEqual(tier, "elite")
    
    def test_trust_score(self):
        """Test trust score calculation"""
        from trustyclaw.skills.reputation import get_reputation_skill
        
        reputation = get_reputation_skill(mock=True)
        trust = reputation.calculate_trust_score(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        self.assertIsNotNone(trust)
        self.assertGreaterEqual(trust, 0)
        self.assertLessEqual(trust, 100)
    
    def test_verify_claim(self):
        """Test reputation claim verification"""
        from trustyclaw.skills.reputation import get_reputation_skill
        
        reputation = get_reputation_skill(mock=True)
        
        # Valid claim
        result = reputation.verify_reputation_claim(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            claimed_score=92.0,
            tolerance=5.0,
        )
        
        self.assertTrue(result["verified"])
    
    def test_compare_agents(self):
        """Test agent comparison"""
        from trustyclaw.skills.reputation import get_reputation_skill
        
        reputation = get_reputation_skill(mock=True)
        result = reputation.compare_agents(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        )
        
        self.assertIn("comparison", result)


class TestFullWorkflow(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def test_complete_rental_workflow(self):
        """Test complete rental: discovery -> mandate -> escrow -> review"""
        from trustyclaw.skills.discovery import get_discovery_skill
        from trustyclaw.skills.mandate import get_mandate_skill
        from trustyclaw.sdk.escrow_contract import get_escrow_client
        from trustyclaw.sdk.review_system import get_review_service
        
        # Step 1: Discover agent
        discovery = get_discovery_skill(mock=True)
        agent = discovery.get_agent_profile(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        self.assertIsNotNone(agent)
        
        # Step 2: Create mandate
        mandate_skill = get_mandate_skill(mock=True)
        mandate = mandate_skill.create_mandate(
            provider=agent.address,
            renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverables=["5 images"],
        )
        
        # Step 3: Create escrow using mandate's own provider/renter
        escrow = get_escrow_client("devnet")
        escrow_contract = escrow.create_escrow(
            renter=mandate.renter,
            provider=mandate.provider,
            skill_id=mandate.terms.skill_id,
            amount=mandate.terms.amount,
            duration_hours=mandate.terms.duration_hours,
            deliverable_hash="expected-hash",
        )
        
        # Link escrow to mandate
        mandate_skill.link_escrow(mandate.mandate_id, escrow_contract.escrow_id)
        
        # Step 4: Complete workflow (proper lifecycle)
        escrow.fund_escrow(escrow_contract.escrow_id)
        escrow.activate_escrow(escrow_contract.escrow_id)
        escrow.complete_escrow(escrow_contract.escrow_id, "deliverable-hash")
        escrow.release_escrow(escrow_contract.escrow_id)
        
        # Step 5: Leave review
        reviews = get_review_service(mock=True)
        review = reviews.create_review(
            provider=mandate.provider,
            renter=mandate.renter,
            skill_id=mandate.terms.skill_id,
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Perfect images!",
        )
        
        self.assertEqual(review.rating, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
