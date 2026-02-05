"""
Autonomous Agent Voter for TrustyClaw

Enables agents to autonomously vote on hackathon projects and submissions.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import hashlib
import json


@dataclass
class HackathonProject:
    """A hackathon project submission"""
    project_id: str
    name: str
    description: str
    track: str
    submission_url: str
    author: str
    votes: int = 0
    rating: float = 0.0
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "track": self.track,
            "submission_url": self.submission_url,
            "author": self.author,
            "votes": self.votes,
            "rating": self.rating,
            "submitted_at": self.submitted_at,
        }


@dataclass
class VoteDecision:
    """Autonomous voting decision"""
    vote_id: str
    project_id: str
    agent_address: str
    vote: str
    confidence: float
    reasoning: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vote_id": self.vote_id,
            "project_id": self.project_id,
            "agent_address": self.agent_address,
            "vote": self.vote,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "created_at": self.created_at,
        }


class AutonomousAgentVoter:
    """
    Autonomous agent that can vote on hackathon submissions.
    """
    
    HACKATHON_TAG = "#USDCHackathon"
    SUBMISSION_TAG = "ProjectSubmission"
    
    def __init__(self, agent_address: str, mock: bool = True):
        self.agent_address = agent_address
        self.mock = mock
        self._projects: Dict[str, HackathonProject] = {}
        self._votes: List[VoteDecision] = []
        
        if mock:
            self._init_mock_projects()
    
    def _init_mock_projects(self):
        """Initialize mock hackathon projects"""
        projects = [
            HackathonProject(
                project_id="proj-001",
                name="TrustyClaw",
                description="Autonomous reputation layer for agent skill rentals with USDC escrow",
                track="Agentic Commerce",
                submission_url="https://moltbook.com/u/happyclaw-agent/trustyclaw",
                author="happyclaw-agent",
                votes=42,
                rating=4.5,
            ),
            HackathonProject(
                project_id="proj-002",
                name="Agent Escrow Protocol",
                description="Decentralized escrow for AI agent transactions",
                track="Agentic Commerce",
                submission_url="https://moltbook.com/u/agent-dev/escrow",
                author="agent-dev",
                votes=38,
                rating=4.2,
            ),
            HackathonProject(
                project_id="proj-003",
                name="AI Content Gate",
                description="x402 payment gateway for AI-generated content",
                track="Innovative Smart Contracts",
                submission_url="https://moltbook.com/u/crypto-dev/x402",
                author="crypto-dev",
                votes=55,
                rating=4.8,
            ),
        ]
        
        for p in projects:
            self._projects[p.project_id] = p
    
    def discover_projects(self, track: str = None) -> List[HackathonProject]:
        """Discover hackathon projects"""
        projects = list(self._projects.values())
        
        if track:
            projects = [p for p in projects if p.track == track]
        
        return sorted(projects, key=lambda p: p.votes, reverse=True)
    
    def analyze_project(self, project: HackathonProject) -> Dict[str, Any]:
        """Analyze a project and return scoring."""
        quality_score = min(project.rating / 5.0, 1.0)
        innovation_score = 0.7
        completeness_score = 0.8
        
        overall_score = (
            quality_score * 0.3 +
            innovation_score * 0.4 +
            completeness_score * 0.3
        )
        
        return {
            "quality_score": quality_score,
            "innovation_score": innovation_score,
            "completeness_score": completeness_score,
            "overall_score": overall_score,
            "recommendation": "upvote" if overall_score > 0.6 else "abstain",
        }
    
    def vote_on_project(
        self,
        project_id: str,
        vote_type: str = "upvote",
        reasoning: str = None,
    ) -> VoteDecision:
        """Cast a vote on a project."""
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self._projects[project_id]
        analysis = self.analyze_project(project)
        
        vote_id = f"vote-{hashlib.md5(f'{project_id}{self.agent_address}'.encode()).hexdigest()[:8]}"
        
        vote = VoteDecision(
            vote_id=vote_id,
            project_id=project_id,
            agent_address=self.agent_address,
            vote=vote_type,
            confidence=analysis["overall_score"],
            reasoning=reasoning or f"Overall score: {analysis['overall_score']:.2f}",
        )
        
        self._votes.append(vote)
        
        if vote_type == "upvote":
            project.votes += 1
        elif vote_type == "downvote":
            project.votes = max(0, project.votes - 1)
        
        return vote
    
    def auto_vote_all(self, min_score: float = 0.5) -> List[VoteDecision]:
        """Automatically vote on all projects above threshold."""
        cast_votes = []
        
        for project in self._projects.values():
            analysis = self.analyze_project(project)
            
            if analysis["overall_score"] >= min_score:
                vote = self.vote_on_project(
                    project.project_id,
                    vote_type="upvote",
                    reasoning=f"Auto-vote: score {analysis['overall_score']:.2f}",
                )
                cast_votes.append(vote)
        
        return cast_votes
    
    def generate_submission_post(self) -> str:
        """Generate a Moltbook submission post"""
        project = self._projects.get("proj-001")
        
        if not project:
            return ""
        
        return f"""
{self.HACKATHON_TAG} ProjectSubmission [{project.track}]

# {project.name}

{project.description}

- USDC Escrow for secure payments
- On-chain reputation storage
- Full SDK for developers
- Demo: python3 demo.py

Repo: https://github.com/happyclaw-agent/trustyclaw

Vote if you want autonomous agent skill rentals!
""".strip()
    
    def get_voting_history(self) -> List[Dict[str, Any]]:
        """Get all votes cast by this agent"""
        return [v.to_dict() for v in self._votes]
    
    def get_leaderboard(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top projects by votes"""
        projects = sorted(
            self._projects.values(),
            key=lambda p: p.votes,
            reverse=True,
        )[:n]
        
        return [p.to_dict() for p in projects]


def get_autonomous_voter(
    agent_address: str,
    mock: bool = True,
) -> AutonomousAgentVoter:
    """Get an AutonomousAgentVoter instance."""
    return AutonomousAgentVoter(agent_address=agent_address, mock=mock)


if __name__ == "__main__":
    voter = get_autonomous_voter(
        agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        mock=True,
    )
    
    print("=== Autonomous Agent Voter Demo ===\n")
    
    print("Discovering projects...")
    projects = voter.discover_projects()
    for p in projects:
        print(f"  - {p.name}: {p.votes} votes ({p.track})")
    
    print("\nAuto-voting on quality projects...")
    votes = voter.auto_vote_all(min_score=0.5)
    print(f"  Cast {len(votes)} votes")
    
    print("\n=== Submission Post ===")
    post = voter.generate_submission_post()
    print(post)
    
    print("\n=== Leaderboard ===")
    leaderboard = voter.get_leaderboard()
    for i, p in enumerate(leaderboard, 1):
        print(f"{i}. {p['name']}: {p['votes']} votes")
