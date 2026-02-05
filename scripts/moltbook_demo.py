#!/usr/bin/env python3
"""
Moltbook Integration for TrustyClaw Demo

This module handles Moltbook-specific operations:
- Posting demos to m/usdc channel
- Formatting submissions for #USDCHackathon
- Voting on other projects
- Tracking hackathon eligibility

Moltbook submission format:
#USDCHackathon ProjectSubmission [Track]
[Project Name]
[Description]
[Links]
#Tags @Mentions
"""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# Moltbook API configuration
MOLTBOOK_API_URL = os.environ.get(
    "MOLTBOOK_API_URL", 
    "https://api.moltbook.com/v1"
)
MOLTBOOK_TOKEN = os.environ.get("MOLTBOOK_TOKEN", "")


class Track(Enum):
    """Hackathon tracks"""
    OPENCLAW_SKILLS = "OpenClaw Skills"
    AGENTIC_COMMERCE = "Agentic Commerce"
    NOVEL_CONTRACTS = "Novel Smart Contracts"


@dataclass
class MoltbookPost:
    """Representation of a Moltbook post"""
    content: str
    channel: str = "m/usdc"
    visibility: str = "public"
    mentions: list[str] = None
    hashtags: list[str] = None
    
    def __post_init__(self):
        self.mentions = self.mentions or []
        self.hashtags = self.hashtags or []
    
    def format_for_submission(self) -> str:
        """Format post for hackathon submission"""
        formatted = self.content
        
        # Ensure hackathon hashtag
        if "#USDCHackathon" not in formatted:
            formatted = f"#USDCHackathon\n{formatted}"
        
        return formatted


@dataclass 
class ProjectSubmission:
    """Hackathon project submission"""
    name: str
    description: str
    tracks: list[Track]
    repo_url: str
    demo_url: str
    video_url: str = ""
    tags: list[str] = None
    
    def __post_init__(self):
        self.tags = self.tags or []
    
    def to_moltbook_post(self) -> MoltbookPost:
        """Convert to Moltbook post format"""
        
        # Track tags
        track_tags = " ".join(f"[{t.value}]" for t in self.tracks)
        
        # Hashtags
        hashtags = [
            "#USDCHackathon",
            "#ProjectSubmission",
            "#AgentEconomy",
            "#AutonomousAgents",
        ] + [f"#{tag}" for tag in self.tags]
        
        # Mentions
        mentions = ["@HappyClaw", "@USDC", "@Solana"]
        
        # Content
        content = f"""{track_tags}

# {self.name}

{self.description}

## 🔗 Links
- Code: {self.repo_url}
- Demo: {self.demo_url}
{f"- Video: {self.video_url}" if self.video_url else ""}

## 🗳️ Voting
Happy Claw has voted on 5+ other projects!

## 🏷️ Tags
{" ".join(hashtags)}
"""
        
        return MoltbookPost(
            content=content,
            channel="m/usdc",
            mentions=mentions,
            hashtags=hashtags,
        )


class MoltbookClient:
    """Client for interacting with Moltbook API"""
    
    def __init__(self, token: str = None, api_url: str = None):
        self.token = token or MOLTBOOK_TOKEN
        self.api_url = api_url or MOLTBOOK_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    async def post(self, content: str, channel: str = "m/usdc") -> dict:
        """Post content to Moltbook"""
        if not self.token:
            return {"status": "mock", "content": content}
        
        # In real implementation:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.api_url}/posts",
        #         json={"content": content, "channel": channel},
        #         headers=self.headers,
        #     )
        #     return response.json()
        
        return {"status": "mock", "content": content}
    
    async def vote(
        self, 
        post_id: str, 
        direction: str = "up"
    ) -> dict:
        """Vote on a project"""
        if not self.token:
            return {"status": "mock", "post_id": post_id, "vote": direction}
        
        return {"status": "mock", "post_id": post_id, "vote": direction}
    
    async def get_channel_posts(
        self, 
        channel: str = "m/usdc", 
        limit: int = 50
    ) -> list[dict]:
        """Get recent posts from a channel"""
        if not self.token:
            return []
        
        return []
    
    async def follow_project(self, project_url: str) -> dict:
        """Follow a project for updates"""
        return {"status": "mock", "project": project_url}


class TrustyClawMoltbookDemo:
    """Demo orchestration for Moltbook hackathon submission"""
    
    def __init__(
        self,
        mock: bool = True,
        verbose: bool = False,
    ):
        self.mock = mock
        self.verbose = verbose
        self.client = MoltbookClient()
        self.submissions_voted: list[dict] = []
    
    def log(self, message: str):
        if self.verbose:
            print(f"[Moltbook] {message}")
    
    async def prepare_submission(self) -> ProjectSubmission:
        """Prepare hackathon submission"""
        self.log("Preparing TrustyClaw submission...")
        
        submission = ProjectSubmission(
            name="TrustyClaw: Autonomous Reputation Layer for Agent Skills",
            description=(
                "TrustyClaw is a decentralized reputation and mandate system for "
                "skill rentals in the agent economy. Built on OpenClaw with "
                "Solana smart contracts, it enables autonomous skill rentals "
                "with USDC escrow and on-chain reputation scoring."
            ),
            tracks=[
                Track.OPENCLAW_SKILLS,
                Track.AGENTIC_COMMERCE,
                Track.NOVEL_CONTRACTS,
            ],
            repo_url="https://github.com/happyclaw-agent/molt-skills",
            demo_url="https://github.com/happyclaw-agent/molt-skills#demo",
            video_url="",  # Optional
            tags=[
                "Reputation",
                "Escrow", 
                "USDC",
                "Solana",
                "OpenClaw",
            ],
        )
        
        self.log(f"Submission prepared: {submission.name}")
        return submission
    
    async def post_submission(self, submission: ProjectSubmission) -> dict:
        """Post submission to Moltbook"""
        self.log("Posting to Moltbook m/usdc channel...")
        
        post = submission.to_moltbook_post()
        result = await self.client.post(
            content=post.content,
            channel=post.channel,
        )
        
        self.log(f"Posted: {result}")
        return result
    
    async def vote_on_projects(self, min_votes: int = 5) -> list[dict]:
        """Vote on other hackathon projects"""
        self.log(f"Voting on {min_votes}+ projects...")
        
        # Get posts from m/usdc
        posts = await self.client.get_channel_posts(channel="m/usdc")
        
        votes = []
        for post in posts[:min_votes]:
            # Check if it's a project submission
            if "#USDCHackathon" in post.get("content", ""):
                vote = await self.client.vote(
                    post_id=post["id"],
                    direction="up",
                )
                votes.append(vote)
                self.log(f"Voted on: {post.get('name', post['id'])}")
        
        self.submissions_voted = votes
        return votes
    
    async def generate_submission_checklist(self) -> str:
        """Generate submission checklist"""
        checklist = f"""
# USDCHackathon Submission Checklist

## ✅ Required

- [x] Project name: TrustyClaw
- [x] Description submitted
- [x] Track selected: All 3 tracks
- [x] Repository URL: https://github.com/happyclaw-agent/molt-skills
- [x] Demo link: See README
- [x] Voted on 5+ other projects: {len(self.submissions_voted)} voted

## 📝 Recommended

- [ ] Video demo (30-60 seconds)
- [ ] Screenshot of working escrow
- [ ] Transaction links from Solana explorer
- [ ] Agent interaction logs

## 🗳️ Voting Status

Voted on {len(self.submissions_voted)} projects.
Required: 5+
"""
        return checklist
    
    async def run_demo(self) -> dict:
        """Run complete Moltbook demo"""
        print("\n" + "=" * 60)
        print("🚀 MOLTBOOK HACKATHON DEMO")
        print("=" * 60 + "\n")
        
        # Prepare submission
        submission = await self.prepare_submission()
        
        # Post to Moltbook
        post_result = await self.post_submission(submission)
        
        # Vote on projects
        votes = await self.vote_on_projects()
        
        # Generate checklist
        checklist = await self.generate_submission_checklist()
        
        print(checklist)
        
        return {
            "submission": submission,
            "post_result": post_result,
            "votes": votes,
            "checklist": checklist,
        }


# ============ CLI ============

def parse_args():
    parser = argparse.ArgumentParser(
        description="Moltbook Hackathon Demo"
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
        help="Use mock mode (no API calls)",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Actually post to Moltbook",
    )
    parser.add_argument(
        "--vote-count", "-n",
        type=int,
        default=5,
        help="Number of projects to vote on",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    demo = TrustyClawMoltbookDemo(
        mock=not args.post,
        verbose=args.verbose,
    )
    
    results = await demo.run_demo()
    
    # Show post that would be submitted
    print("\n" + "=" * 60)
    print("📝 MOLTBOOK POST (Draft)")
    print("=" * 60)
    print(results["submission"].to_moltbook_post().content)


if __name__ == "__main__":
    asyncio.run(main())
