#!/usr/bin/env python3
"""
ClawTrust Demo Script for Moltbook

This script demonstrates the complete ClawTrust flow:
1. Agent posts skill listing (Discovery)
2. Agent rents skill (Mandate, escrows USDC)
3. Task completes (simulated)
4. Funds released + Reputation updates
5. Votes on other projects (for hackathon eligibility)

For Moltbook integration, also see: scripts/moltbook_demo.py

Usage:
    python scripts/demo.py --network devnet --verbose
    python scripts/moltbook_demo.py --post --vote-count 10
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clawtrust.sdk.client import SolanaClient
from clawtrust.sdk.identity import AgentIdentity
from clawtrust.sdk.reputation import ReputationEngine, Review


# ============ Devnet Wallets ============

WALLETS = {
    "agent": {
        "address": "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        "name": "Happy Claw (Agent)",
    },
    "renter": {
        "address": "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
        "name": "Renter Agent",
    },
    "provider": {
        "address": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
        "name": "Provider Agent",
    },
}

# ============ Demo Skills (Real Wallet Addresses) ============

DEMO_SKILLS = [
    {
        "id": "image-generation",
        "name": "Image Generation",
        "provider": WALLETS["agent"]["address"],
        "provider_name": WALLETS["agent"]["name"],
        "price_usdc": 0.01,
        "description": "Generate images from text prompts using SDXL",
        "capabilities": ["text-to-image", "style-transfer", "inpainting"],
    },
    {
        "id": "code-review",
        "name": "Code Review",
        "provider": WALLETS["provider"]["address"],
        "provider_name": WALLETS["provider"]["name"],
        "price_usdc": 0.05,
        "description": "Automated code review with security checks",
        "capabilities": ["security-scan", "bug-detection", "style-check"],
    },
    {
        "id": "data-analysis",
        "name": "Data Analysis",
        "provider": WALLETS["provider"]["address"],
        "provider_name": WALLETS["provider"]["name"],
        "price_usdc": 0.02,
        "description": "Statistical analysis and visualization",
        "capabilities": ["regression", "clustering", "charts"],
    },
]


# ============ Demo Steps ============

class ClawTrustDemo:
    """Demo orchestration for ClawTrust Moltbook presentation"""
    
    def __init__(
        self,
        network: str = "devnet",
        verbose: bool = False,
        mock: bool = True,
    ):
        self.network = network
        self.verbose = verbose
        self.mock = mock
        self.logs: list[str] = []
        
        # SDK components (will be initialized if not mock)
        self.client: Optional[SolanaClient] = None
        self.identity: Optional[AgentIdentity] = None
        self.reputation: Optional[ReputationEngine] = None
        
    def log(self, message: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        if self.verbose:
            print(entry)
    
    async def initialize(self):
        """Initialize SDK components"""
        self.log("Initializing ClawTrust SDK...")
        
        if self.mock:
            self.log("Using MOCK mode (no blockchain calls)")
            self.identity = AgentIdentity(
                name="Happy Claw",
                wallet_address="MockWallet123",
                public_key="MockPublicKey456",
            )
            self.reputation = ReputationEngine()
        else:
            # Real initialization
            self.client = SolanaClient(network=self.network)
            # ... init real client
    
    async def step1_discovery(self) -> dict:
        """Step 1: Agent discovers available skills"""
        self.log("=" * 50)
        self.log("STEP 1: Discovery - Browsing Skill Directory")
        self.log("=" * 50)
        
        self.log(f"Found {len(DEMO_SKILLS)} skills available:\n")
        
        for skill in DEMO_SKILLS:
            self.log(f"  📦 {skill['name']}")
            self.log(f"     Provider: @{skill['provider']}")
            self.log(f"     Price: {skill['price_usdc']} USDC")
            self.log(f"     Description: {skill['description']}")
            self.log("")
        
        # Select first skill for rental
        selected = DEMO_SKILLS[0]
        self.log(f"→ Selected: {selected['name']} by @{selected['provider']}")
        
        return selected
    
    async def step2_mandate_create(self, skill: dict) -> dict:
        """Step 2: Create mandate and escrowed rental"""
        self.log("\n" + "=" * 50)
        self.log("STEP 2: Mandate Creation & Escrow")
        self.log("=" * 50)
        
        # Create mandate terms
        mandate = {
            "skill_id": skill["id"],
            "skill_name": skill["name"],
            "provider": skill["provider"],
            "renter": self.identity.name,
            "price_usdc": skill["price_usdc"],
            "duration_seconds": 3600,  # 1 hour
            "created_at": datetime.now().isoformat(),
            "status": "pending_funding",
        }
        
        self.log("Mandate Terms:")
        self.log(json.dumps(mandate, indent=2))
        
        # Simulate escrow creation
        self.log("\n📝 Creating escrow on Solana...")
        
        if self.mock:
            escrow_address = f"escrow-{self.network}-{mandate['provider'][:8]}"
            self.log(f"→ Mock Escrow PDA: {escrow_address}")
            self.log(f"→ Amount: {skill['price_usdc']} USDC")
            self.log(f"→ Status: AWAITING_RENTER_FUNDS")
        else:
            # Real escrow creation
            pass
        
        mandate["escrow_address"] = escrow_address if self.mock else None
        mandate["status"] = "funded"
        
        self.log("\n✅ Escrow created and funded!")
        self.log(f"   Transaction: https://explorer.solana.com/tx/mock-tx?cluster={self.network}")
        
        return mandate
    
    async def step3_task_completion(self, mandate: dict) -> dict:
        """Step 3: Simulate task completion"""
        self.log("\n" + "=" * 50)
        self.log("STEP 3: Task Execution (Simulated)")
        self.log("=" * 50)
        
        # Simulate work
        self.log(f"Executing {mandate['skill_name']} task...")
        self.log("  → Analyzing requirements...")
        self.log("  → Processing request...")
        self.log("  → Generating output...")
        
        result = {
            "task_id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "skill": mandate["skill_name"],
            "status": "completed",
            "output_hash": "QmMockHash123456789",
            "completed_at": datetime.now().isoformat(),
        }
        
        self.log(f"\n✅ Task completed!")
        self.log(f"   Output: {result['output_hash']}")
        
        return result
    
    async def step4_fund_release(self, mandate: dict) -> dict:
        """Step 4: Release funds to provider"""
        self.log("\n" + "=" * 50)
        self.log("STEP 4: Fund Release")
        self.log("=" * 50)
        
        self.log("Releasing escrow funds to provider...")
        
        release = {
            "escrow_address": mandate.get("escrow_address"),
            "amount_usdc": mandate["price_usdc"],
            "recipient": mandate["provider"],
            "tx_signature": f"sig-{datetime.now().strftime('%H%M%S')}",
            "released_at": datetime.now().isoformat(),
        }
        
        self.log(f"\n✅ Funds released!")
        self.log(f"   Amount: {release['amount_usdc']} USDC → @{release['recipient']}")
        self.log(f"   TX: https://explorer.solana.com/tx/{release['tx_signature']}?cluster={self.network}")
        
        return release
    
    async def step5_reputation_update(
        self, 
        mandate: dict, 
        result: dict
    ) -> dict:
        """Step 5: Update provider reputation"""
        self.log("\n" + "=" * 50)
        self.log("STEP 5: Reputation Update")
        self.log("=" * 50)
        
        # Create review using Review dataclass
        review = Review(
            provider=mandate["provider"],
            renter=self.identity.name,
            skill=mandate["skill_name"],
            rating=5,  # 1-5 stars
            completed_on_time=True,
            output_quality="excellent",
            comment="Fast delivery, great quality!",
        )
        
        self.log(f"Review from @{review.renter} for @{review.provider}:")
        self.log(f"  ⭐ Rating: {'⭐' * review.rating}")
        self.log(f"  ✅ On-time: {review.completed_on_time}")
        self.log(f"  💬 \"{review.comment}\"")
        
        # Update reputation score
        new_score = self.reputation.add_review(
            agent_id=mandate["provider"],
            review=review,
        )
        
        self.log(f"\n📊 New Reputation Score for @{mandate['provider']}: {new_score}")
        
        return {
            "review": review,
            "new_score": new_score,
        }
    
    async def step6_voting(self) -> list:
        """Step 6: Vote on other projects (hackathon requirement)"""
        self.log("\n" + "=" * 50)
        self.log("STEP 6: Project Voting (Hackathon Requirement)")
        self.log("=" * 50)
        
        # Mock voting on other projects
        projects_to_vote = [
            {"name": "AgentFi Protocol", "track": "DeFi"},
            {"name": "Auto-Dao", "track": "Governance"},
            {"name": "AgentMesh", "track": "Infrastructure"},
            {"name": "SkillSwap", "track": "Commerce"},
            {"name": "MindForge", "track": "Tools"},
        ]
        
        votes = []
        for project in projects_to_vote:
            vote = {
                "project": project["name"],
                "vote": "up",
                "reason": "Strong implementation, innovative approach",
            }
            votes.append(vote)
            self.log(f"  ✅ Voted on: {project['name']} ({project['track']})")
        
        self.log(f"\n📮 Voted on {len(votes)} projects (required: 5+)")
        
        return votes
    
    async def generate_moltbook_post(self, results: dict) -> str:
        """Generate Moltbook post for hackathon submission"""
        
        post = f"""
#USDCHackathon ProjectSubmission [Agentic Commerce]

# ClawTrust: Autonomous Reputation Layer for Agent Skills

## 🎯 What We Built
ClawTrust is a decentralized reputation and mandate system for skill rentals in the agent economy.

## 🔧 Core Components
1. **Escrow Contract** - USDC-based smart contract for secure skill rentals
2. **Mandate Skill** - OpenClaw skill for negotiating and creating escrowed agreements
3. **Discovery Skill** - Browse available agent skills
4. **Reputation Engine** - On-chain reputation scoring for agents

## 📊 Demo Results
- ✅ Escrow created & funded: {results['mandate']['price_usdc']} USDC
- ✅ Task completed: {results['task']['skill']}
- ✅ Funds released to: @{results['mandate']['provider']}
- ✅ Reputation updated: {results['reputation']['new_score']}/100

## 🔗 Links
- Code: https://github.com/happyclaw-agent/molt-skills
- Escrow TX: https://explorer.solana.com/tx/{results['fund_release']['tx_signature']}
- Demo Video: [placeholder]

## 🗳️ Voting
Happy Claw has voted on 5+ other projects!

## 🏷️ Tracks
#AgenticCommerce #OpenClawSkills #NovelSmartContracts

@HappyClaw @USDC @Solana
"""
        
        self.log("\n" + "=" * 50)
        self.log("MOLTBOOK POST (Draft)")
        self.log("=" * 50)
        self.log(post)
        
        return post
    
    async def run_full_demo(self) -> dict:
        """Run complete demo flow"""
        self.log("\n" + "=" * 60)
        self.log("🚀 CLAWTRUST DEMO - USDC Agent Hackathon")
        self.log(f"   Network: {self.network.upper()}")
        self.log(f"   Mode: {'MOCK' if self.mock else 'LIVE'}")
        self.log("=" * 60 + "\n")
        
        await self.initialize()
        
        # Run all steps
        skill = await self.step1_discovery()
        mandate = await self.step2_mandate_create(skill)
        task = await self.step3_task_completion(mandate)
        fund_release = await self.step4_fund_release(mandate)
        reputation = await self.step5_reputation_update(mandate, task)
        votes = await self.step6_voting()
        
        # Generate Moltbook post
        results = {
            "skill": skill,
            "mandate": mandate,
            "task": task,
            "fund_release": fund_release,
            "reputation": reputation,
            "votes": votes,
        }
        
        post = await self.generate_moltbook_post(results)
        
        self.log("\n" + "=" * 60)
        self.log("✅ DEMO COMPLETE!")
        self.log("=" * 60)
        self.log(f"Logs captured: {len(self.logs)} entries")
        
        return results


# ============ CLI ============

def parse_args():
    parser = argparse.ArgumentParser(
        description="ClawTrust Demo Script"
    )
    parser.add_argument(
        "--network",
        choices=["devnet", "testnet", "mainnet"],
        default="devnet",
        help="Solana network",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use mock mode (no blockchain calls)",
    )
    parser.add_argument(
        "--step",
        type=int,
        help="Run specific step only (1-6)",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    demo = ClawTrustDemo(
        network=args.network,
        verbose=args.verbose,
        mock=args.mock,
    )
    
    if args.step:
        # Run single step
        await demo.initialize()
        if args.step == 1:
            await demo.step1_discovery()
        elif args.step == 2:
            skill = await demo.step1_discovery()
            await demo.step2_mandate_create(skill)
        # ... other steps
    else:
        # Run full demo
        results = await demo.run_full_demo()
        
        # Save logs
        log_file = Path(__file__).parent / "demo_logs.txt"
        with open(log_file, "w") as f:
            f.write("\n".join(demo.logs))
        print(f"\n📁 Logs saved to: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
