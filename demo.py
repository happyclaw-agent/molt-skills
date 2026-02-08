#!/usr/bin/env python3
"""
TrustyClaw Demo Application

End-to-end demonstration of TrustyClaw features with real USDC operations.

Usage:
    python3 demo.py              # Run with mock mode (default)
    python3 demo.py --onchain   # Run with real on-chain contracts (REQUIRES deployment)
    python3 demo.py --mock      # Run with mock mode explicitly
"""

import sys
import argparse
import os
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description='TrustyClaw Demo', allow_abbrev=True)
parser.add_argument('--mock', action='store_true', default=False, help='Use mock mode explicitly')
parser.add_argument('--onchain', action='store_true', default=False, help='Use real on-chain contracts (REQUIRES anchor programs deployed)')

USE_MOCK = True  # default when imported (e.g. by tests); overridden in __main__

def check_anchor_deployed() -> bool:
    """Check if Anchor programs are deployed"""
    idl_dir = os.path.join(os.path.dirname(__file__), "target", "idl")
    escrow_idl_exists = os.path.exists(os.path.join(idl_dir, "escrow.json"))
    reputation_idl_exists = os.path.exists(os.path.join(idl_dir, "reputation.json"))
    return escrow_idl_exists or reputation_idl_exists

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
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


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
    print_header("USDC TOKEN INTEGRATION")
    
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


def demo_escrow():
    """Demo escrow contract"""
    print_header("ESCROW CONTRACT")
    
    escrow = get_escrow_client("devnet")
    
    print_section("Create Escrow")
    new_escrow = escrow.create_escrow(
        renter=RENTER_WALLET,
        provider=PROVIDER_WALLET,
        skill_id="image-generation",
        amount=1000000,
        duration_hours=24,
        deliverable_hash="abc123def456789",
    )
    print(f"Created: {new_escrow.escrow_id}")
    print(f"State: {new_escrow.state.value}")
    
    print_section("Fund Escrow")
    funded = escrow.fund_escrow(new_escrow.escrow_id)
    print(f"State: {funded.state.value}")
    
    print_section("Activate Escrow")
    active = escrow.activate_escrow(new_escrow.escrow_id)
    print(f"State: {active.state.value}")
    
    print_section("Complete Escrow")
    completed = escrow.complete_escrow(new_escrow.escrow_id, "final-hash")
    print(f"State: {completed.state.value}")
    
    print_section("Release Funds")
    released = escrow.release_escrow(new_escrow.escrow_id)
    print(f"State: {released.state.value}")


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
        comment="Amazing work!",
    )
    print(f"Created: {review.review_id}")
    print(f"Rating: {'⭐'*review.rating}")
    
    print_section("Calculate Agent Rating")
    rating = reviews.calculate_agent_rating(PROVIDER_WALLET)
    print(f"Average Rating: {rating['average_rating']}/5")
    print(f"Total Reviews: {rating['total_reviews']}")


def demo_mandate():
    """Demo mandate skill"""
    print_header("MANDATE SKILL")
    
    mandate = get_mandate_skill()
    
    print_section("Create Mandate")
    new_mandate = mandate.create_mandate(
        provider=PROVIDER_WALLET,
        renter=RENTER_WALLET,
        skill_id="image-generation",
        amount=500000,
        duration_hours=12,
        deliverables=["10 images", "1024x1024"],
        revisions=1,
    )
    print(f"Created: {new_mandate.mandate_id}")
    print(f"Status: {new_mandate.status.value}")
    
    print_section("Submit & Accept")
    mandate.submit_mandate(new_mandate.mandate_id)
    mandate.accept_mandate(new_mandate.mandate_id)
    print("Status: submitted → accepted")


def demo_discovery():
    """Demo discovery skill"""
    print_header("DISCOVERY SKILL")
    
    discovery = get_discovery_skill()
    
    print_section("Browse Skills")
    skills = discovery.browse_skills()
    print(f"Found {len(skills)} skills")
    
    print_section("Top Agents")
    top = discovery.get_top_rated_agents(3)
    for i, a in enumerate(top, 1):
        print(f"{i}. {a.name}: {a.rating}⭐")
    
    print_section("Marketplace Stats")
    stats = discovery.get_marketplace_stats()
    print(f"Total Agents: {stats['total_agents']}")
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
    
    print_section("Reputation Tier")
    tier = reputation.get_reputation_tier(PROVIDER_WALLET)
    print(f"Tier: {tier.upper()}")


def demo_reputation_chain():
    """Demo on-chain reputation storage"""
    print_header("ON-CHAIN REPUTATION")
    
    program = get_reputation_chain("devnet")
    
    print_section("Reputation PDA")
    pda = program.derive_reputation_pda(PROVIDER_WALLET)
    print(f"PDA: {pda}")
    
    print_section("Get Reputation")
    try:
        rep = program.get_reputation(PROVIDER_WALLET)
        print(f"On-Chain Score: {rep.reputation_score}")
    except Exception as e:
        print(f"No on-chain reputation: {str(e)[:50]}...")


def main():
    """Run all demos"""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print("  TRUSTYCLAW DEMO APPLICATION")
    print(f"  {now.isoformat()}")
    print(f"{'='*60}")
    
    mode = "ON-CHAIN" if not USE_MOCK else "MOCK"
    print(f"\nMode: {mode}")
    
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
    
    print("Repository: https://github.com/happyclaw-agent/trustyclaw")
    print("Hackathon: Colosseum Agent Hackathon (Feb 2-12, 2026)")


if __name__ == "__main__":
    args = parser.parse_args()
    USE_MOCK = args.mock or not args.onchain  # Mock by default, --onchain overrides
    if USE_MOCK:
        print("⚠ Mock mode - Run with --onchain for real on-chain operations")
        print("   (Requires: anchor build && anchor deploy)")
    else:
        if not check_anchor_deployed():
            print("❌ ERROR: --onchain mode requires Anchor programs to be deployed!")
            print()
            print("   Programs NOT deployed. Run these commands on your LOCAL machine:")
            print("   # 1. Install dependencies")
            print("   curl -sSfL https://release.solana.com/v1.18.22/install | sh")
            print("   cargo install --git https://github.com/coral-xyz/anchor anchor-cli --locked")
            print("   rustup install 1.75.0 && rustup default 1.75.0")
            print("   # 2. Deploy: anchor build && anchor deploy --provider.cluster devnet")
            print("   # 3. export ESCROW_PROGRAM_ID=... REPUTATION_PROGRAM_ID=...")
            print("   Then run: python3 demo.py --onchain")
            sys.exit(1)
        print("✓ On-chain mode - Anchor programs detected")
        print(f"   Escrow Program: {os.environ.get('ESCROW_PROGRAM_ID', 'default')[:16]}...")
        print(f"   Reputation Program: {os.environ.get('REPUTATION_PROGRAM_ID', 'default')[:16]}...")
    main()
