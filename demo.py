#!/usr/bin/env python3
"""
TrustyClaw Demo Application

End-to-end demonstration of TrustyClaw features with real USDC operations.
"""

import sys
import json
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, 'src')

from trustyclaw.sdk.solana import get_client
from trustyclaw.sdk.usdc import get_usdc_client
from trustyclaw.sdk.escrow_contract import get_escrow_client
from trustyclaw.sdk.reputation_chain import get_reputation_chain
from trustyclaw.sdk.review_system import get_review_service
from trustyclaw.skills.mandate import get_mandate_skill
from trustyclaw.skills.discovery import get_discovery_skill
from trustyclaw.skills.reputation import get_reputation_skill


def print_header(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a subsection header"""
    print(f"\n--- {title} ---")


# Demo wallets
PROVIDER_WALLET = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
RENTER_WALLET = "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # Not used directly


def demo_solana():
    """Demo Solana integration"""
    print_header("SOLANA INTEGRATION")
    
    client = get_client("devnet")
    
    print_section("Network Info")
    print(f"Network: {client.network}")
    print(f"Endpoint: https://api.{client.network}.solana.com")
    
    print_section("Wallet Balances")
    print(f"Provider: {PROVIDER_WALLET[:16]}...")
    balance = client.get_balance(str(PROVIDER_WALLET))
    print(f"Balance: {balance.lamports:,} lamports ({balance.sol_balance:.4f} SOL)")
    
    print(f"\nRenter: {RENTER_WALLET[:16]}...")
    balance = client.get_balance(RENTER_WALLET)
    print(f"Balance: {balance.lamports:,} lamports ({balance.sol_balance:.4f} SOL)")


def demo_usdc():
    """Demo USDC integration with real signing"""
    print_header("USDC TOKEN INTEGRATION (REAL SIGNING)")
    
    usdc = get_usdc_client("devnet")
    
    print_section("Token Info")
    print(f"Network: {usdc.network}")
    print(f"USDC Mint: {usdc.mint[:16]}...")
    print(f"Endpoint: {usdc.endpoint}")
    
    print_section("Client Status")
    if usdc._keypair:
        print(f"Keypair Loaded: Yes ({usdc.address[:16]}...)")
    else:
        print("Keypair Loaded: No (using mock mode)")
        print("Set SOLANA_KEYPAIR_PATH for real transactions")
    
    print_section("Provider USDC Balance")
    balance = usdc.get_balance(str(PROVIDER_WALLET))
    print(f"Balance: {balance:,.2f} USDC")
    
    print_section("Renter USDC Balance")
    balance = usdc.get_balance(RENTER_WALLET)
    print(f"Balance: {balance:,.2f} USDC")
    
    print_section("Token Account Discovery")
    provider_ata = usdc.find_associated_token_account(PROVIDER_WALLET)
    print(f"Provider ATA: {provider_ata or 'None'}")
    
    renter_ata = usdc.find_associated_token_account(RENTER_WALLET)
    print(f"Renter ATA: {renter_ata or 'None'}")
    
    # Real transfer demo (only if keypair available)
    if usdc._keypair:
        print_section("Real USDC Transfer")
        print("Signing with loaded keypair...")
        
        result = usdc.transfer(
            from_wallet=PROVIDER_WALLET,
            to_wallet=RENTER_WALLET,
            amount=0.01,  # Small amount for demo
        )
        
        print(f"Transaction Signature: {result.signature}")
        print(f"Status: {result.status.value}")
        print(f"Explorer: {result.explorer_url}")
        print(f"Amount: {result.amount} USDC")
        print(f"From: {result.source_account[:16]}...")
        print(f"To: {result.destination_account[:16]}...")
    else:
        print_section("Transfer Demo (Mock Mode)")
        print("Set SOLANA_KEYPAIR_PATH to enable real transfers")
        
        result = usdc.transfer(
            from_wallet=PROVIDER_WALLET,
            to_wallet=RENTER_WALLET,
            amount=1.0,
        )
        
        print(f"Transaction Signature: {result.signature}")
        print(f"Status: {result.status.value}")
        print(f"Explorer: {result.explorer_url}")


def demo_escrow():
    """Demo escrow contract"""
    print_header("ESCROW CONTRACT")
    
    escrow = get_escrow_client("devnet")
    
    print_section("Create Escrow")
    new_escrow = escrow.create_escrow(
        renter=RENTER_WALLET,
        provider=PROVIDER_WALLET,
        skill_id="image-generation",
        amount=1000000,  # 1 USDC
        duration_hours=24,
        deliverable_hash="abc123def456789",
    )
    print(f"Created: {new_escrow.escrow_id}")
    print(f"State: {new_escrow.state.value}")
    print(f"Amount: {new_escrow.terms.amount:,} USDC")
    
    print_section("Fund Escrow")
    funded = escrow.fund_escrow(new_escrow.escrow_id)
    print(f"State: {funded.state.value}")
    
    print_section("Activate Escrow")
    active = escrow.activate_escrow(new_escrow.escrow_id)
    print(f"State: {active.state.value}")
    
    print_section("Complete Escrow")
    completed = escrow.complete_escrow(
        new_escrow.escrow_id,
        "completed-deliverable-hash"
    )
    print(f"State: {completed.state.value}")
    
    print_section("Release Funds")
    released = escrow.release_escrow(new_escrow.escrow_id)
    print(f"State: {released.state.value}")
    print(f"Released Amount: {escrow.release_amount_for_escrow(new_escrow.escrow_id):,} USDC")


def demo_reviews():
    """Demo review system"""
    print_header("REVIEW SYSTEM")
    
    reviews = get_review_service()
    
    print_section("Create Review")
    review = reviews.create_review(
        provider=PROVIDER_WALLET,
        renter=RENTER_WALLET,
        skill_id="image-generation",
        rating=5,
        completed_on_time=True,
        output_quality="excellent",
        comment="Amazing work! Generated perfect images exactly as requested.",
    )
    print(f"Created: {review.review_id}")
    print(f"Rating: {'⭐'*review.rating}")
    
    print_section("Submit Review")
    submitted = reviews.submit_review(review.review_id)
    print(f"State: {submitted.status.value}")
    
    print_section("Calculate Agent Rating")
    rating = reviews.calculate_agent_rating(PROVIDER_WALLET)
    print(f"Average Rating: {rating['average_rating']}/5")
    print(f"Total Reviews: {rating['total_reviews']}")
    print(f"On-Time Rate: {rating['on_time_rate']}%")
    print(f"Reputation Tier: {rating['rating']}")
    
    print_section("Top Agents")
    top = reviews.get_top_agents(3)
    for i, agent in enumerate(top, 1):
        print(f"{i}. {agent['agent'][:16]}... - {agent['average_rating']}/5")


def demo_mandate():
    """Demo mandate skill"""
    print_header("MANDATE SKILL")
    
    mandate = get_mandate_skill()
    
    print_section("Create Mandate")
    new_mandate = mandate.create_mandate(
        provider=PROVIDER_WALLET,
        renter=RENTER_WALLET,
        skill_id="image-generation",
        amount=500000,  # 0.5 USDC
        duration_hours=12,
        deliverables=["10 images", "1024x1024", "PNG format"],
        revisions=1,
    )
    print(f"Created: {new_mandate.mandate_id}")
    print(f"Status: {new_mandate.status.value}")
    
    print_section("Submit Mandate")
    submitted = mandate.submit_mandate(new_mandate.mandate_id)
    print(f"Status: {submitted.status.value}")
    
    print_section("Accept Mandate")
    accepted = mandate.accept_mandate(new_mandate.mandate_id)
    print(f"Status: {accepted.status.value}")
    
    print_section("Start Mandate")
    started = mandate.start_mandate(new_mandate.mandate_id)
    print(f"Status: {started.status.value}")
    
    print_section("Complete Mandate")
    completed = mandate.complete_mandate(new_mandate.mandate_id, "final-hash")
    print(f"Status: {completed.status.value}")
    
    print_section("Rate Mandate")
    rated = mandate.rate_mandate(
        new_mandate.mandate_id,
        renter_rating=5,
        provider_rating=5,
    )
    print(f"Provider Rating: {rated.provider_rating}/5")


def demo_discovery():
    """Demo discovery skill"""
    print_header("DISCOVERY SKILL")
    
    discovery = get_discovery_skill()
    
    print_section("Browse Skills")
    skills = discovery.browse_skills()
    print(f"Found {len(skills)} skills")
    for s in skills[:3]:
        print(f"  - {s.name}: {s.rating}⭐ ({s.price_per_task/1000000:.2f} USDC)")
    
    print_section("Search Agents")
    agents = discovery.search_agents(query="image")
    print(f"Found {len(agents)} agents")
    for a in agents[:3]:
        print(f"  - {a.name}: {a.rating}⭐")
    
    print_section("Categories")
    categories = discovery.get_skill_categories()
    for c in categories[:5]:
        print(f"  - {c['category']}: {c['skill_count']} skills")
    
    print_section("Top Agents")
    top = discovery.get_top_rated_agents(3)
    for i, a in enumerate(top, 1):
        print(f"{i}. {a.name}: {a.rating}⭐ ({a.total_reviews} reviews)")
    
    print_section("Marketplace Stats")
    stats = discovery.get_marketplace_stats()
    print(f"Total Agents: {stats['total_agents']}")
    print(f"Total Skills: {stats['total_skills']}")
    print(f"Avg Rating: {stats['avg_agent_rating']:.2f}")


def demo_reputation():
    """Demo reputation skill"""
    print_header("REPUTATION SKILL")
    
    reputation = get_reputation_skill()
    
    print_section("Agent Reputation")
    rep = reputation.get_agent_reputation(PROVIDER_WALLET)
    print(f"Reputation Score: {rep.reputation_score}/100")
    print(f"Average Rating: {rep.average_rating}/5")
    print(f"On-Time Rate: {rep.on_time_percentage}%")
    print(f"Completed Tasks: {rep.completed_tasks}")
    
    print_section("Reputation Tier")
    tier = reputation.get_reputation_tier(PROVIDER_WALLET)
    print(f"Tier: {tier.upper()}")
    
    print_section("Trust Score")
    trust = reputation.calculate_trust_score(PROVIDER_WALLET)
    print(f"Trust Score: {trust}/100")
    
    print_section("Reputation Breakdown")
    bd = reputation.get_reputation_breakdown(PROVIDER_WALLET)
    print(f"Quality: {bd.quality_score:.1f}")
    print(f"Reliability: {bd.reliability_score:.1f}")
    print(f"Communication: {bd.communication_score:.1f}")
    print(f"Value: {bd.value_score:.1f}")
    
    print_section("Top Reputed Agents")
    top = reputation.get_top_reputed_agents(3)
    for i, a in enumerate(top, 1):
        print(f"{i}. {a.agent_address[:16]}... - {a.reputation_score}/100")


def demo_reputation_chain():
    """Demo on-chain reputation storage"""
    print_header("ON-CHAIN REPUTATION")
    
    program = get_reputation_chain("devnet")
    
    print_section("Reputation PDA")
    pda = program.derive_reputation_pda(PROVIDER_WALLET)
    print(f"PDA: {pda}")
    
    print_section("Get On-Chain Reputation")
    rep = program.get_reputation(PROVIDER_WALLET)
    if rep:
        print(f"On-Chain Score: {rep.reputation_score}")
        print(f"Reviews: {rep.total_reviews}")
        print(f"Rating: {rep.average_rating}")
    
    print_section("Calculate Score")
    score = program.calculate_score(
        average_rating=4.8,
        on_time_pct=95.0,
        total_reviews=150,
    )
    print(f"Calculated Score: {score}/100")


def main():
    """Run all demos"""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print("  TRUSTYCLAW DEMO APPLICATION")
    print(f"  {now.isoformat()}")
    print(f"{'='*60}")
    
    # Check for keypair
    import os
    if os.environ.get("SOLANA_KEYPAIR_PATH"):
        print("\n✓ Real USDC signing enabled (SOLANA_KEYPAIR_PATH set)")
    else:
        print("\n⚠ Mock mode - Set SOLANA_KEYPAIR_PATH for real transactions")
    
    # Run all demos
    demo_solana()
    demo_usdc()
    demo_escrow()
    demo_reviews()
    demo_mandate()
    demo_discovery()
    demo_reputation()
    demo_reputation_chain()
    
    print(f"\n{'='*60}")
    print("  DEMO COMPLETE!")
    print(f"{'='*60}\n")
    
    print("TrustyClaw Features Demonstrated:")
    print("  ✓ Solana blockchain integration")
    print("  ✓ USDC token handling with real signing")
    print("  ✓ Escrow contract management")
    print("  ✓ Review submission and aggregation")
    print("  ✓ Mandate lifecycle")
    print("  ✓ Agent/skill discovery")
    print("  ✓ Reputation queries")
    print("  ✓ On-chain reputation storage")
    
    print("\nRepository: https://github.com/happyclaw-agent/trustyclaw")


if __name__ == "__main__":
    main()
