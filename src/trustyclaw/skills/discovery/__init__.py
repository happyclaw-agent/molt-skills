"""
Discovery Skill for TrustyClaw

Agent/skill marketplace discovery and browsing.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import uuid
import json


class SkillCategory(Enum):
    """Skill categories"""
    IMAGE_GENERATION = "image-generation"
    CODE_GENERATION = "code-generation"
    DATA_ANALYSIS = "data-analysis"
    WRITING = "writing"
    TRANSLATION = "translation"
    AUDIO = "audio"
    VIDEO = "video"
    RESEARCH = "research"
    OTHER = "other"


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    SUSPENDED = "suspended"


@dataclass
class Skill:
    """A skill offered by an agent"""
    skill_id: str
    agent_address: str
    name: str
    category: str
    description: str
    price_per_task: int  # USDC lamports
    estimated_duration_hours: int
    rating: float = 0.0
    review_count: int = 0
    completed_tasks: int = 0
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "agent_address": self.agent_address,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price_per_task": self.price_per_task,
            "estimated_duration_hours": self.estimated_duration_hours,
            "rating": self.rating,
            "review_count": self.review_count,
            "completed_tasks": self.completed_tasks,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
        }


@dataclass
class Agent:
    """An agent in the marketplace"""
    address: str
    name: str
    bio: str
    skills: List[Skill] = field(default_factory=list)
    rating: float = 0.0
    total_reviews: int = 0
    completed_tasks: int = 0
    member_since: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "available"
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "name": self.name,
            "bio": self.bio,
            "skills": [s.to_dict() for s in self.skills],
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "completed_tasks": self.completed_tasks,
            "member_since": self.member_since,
            "status": self.status,
            "avatar_url": self.avatar_url,
            "website": self.website,
            "languages": self.languages,
        }


@dataclass
class SearchFilters:
    """Filters for searching agents/skills"""
    category: Optional[str] = None
    min_rating: float = 0.0
    max_price: Optional[int] = None
    min_price: Optional[int] = None
    skills: List[str] = field(default_factory=list)
    availability: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    sort_by: str = "rating"  # rating, price, reviews, recent


class DiscoverySkill:
    """
    Skill for discovering agents and skills in the marketplace.
    
    Features:
    - Browse skills by category
    - Search agents by name/skill
    - Filter results
    - Get agent profiles
    - Trending/popular agents
    - Recommendations
    """
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        self._agents: Dict[str, Agent] = {}
        self._skills: Dict[str, Skill] = {}
        self._agent_by_skill: Dict[str, List[str]] = {}  # skill_id -> agent addresses
        
        if mock:
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with sample agents and skills"""
        # Create sample agents
        agents = [
            Agent(
                address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
                name="ImageGen Pro",
                bio="Professional AI image generation specialist",
                skills=[],
                rating=4.8,
                total_reviews=150,
                completed_tasks=200,
                status="available",
                languages=["English", "Spanish"],
            ),
            Agent(
                address="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
                name="CodeMaster",
                bio="Expert Python and Solidity developer",
                skills=[],
                rating=4.9,
                total_reviews=300,
                completed_tasks=450,
                status="available",
                languages=["English", "Chinese"],
            ),
            Agent(
                address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
                name="DataWhiz",
                bio="Data analysis and visualization expert",
                skills=[],
                rating=4.6,
                total_reviews=80,
                completed_tasks=95,
                status="busy",
                languages=["English"],
            ),
        ]
        
        for agent in agents:
            self._agents[agent.address] = agent
        
        # Create sample skills
        skills = [
            Skill(
                skill_id="img-gen-1",
                agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
                name="AI Image Generation",
                category="image-generation",
                description="High-quality AI image generation using latest models",
                price_per_task=500000,  # 0.5 USDC
                estimated_duration_hours=1,
                rating=4.8,
                review_count=120,
                completed_tasks=150,
                tags=["AI", "Images", "Art"],
                capabilities=["1024x1024", "Upscaling", "Variations"],
            ),
            Skill(
                skill_id="code-py-1",
                agent_address="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
                name="Python Development",
                category="code-generation",
                description="Full Python development services",
                price_per_task=1000000,  # 1 USDC
                estimated_duration_hours=4,
                rating=4.9,
                review_count=250,
                completed_tasks=350,
                tags=["Python", "Backend", "API"],
                capabilities=["Django", "FastAPI", "Data pipelines"],
            ),
            Skill(
                skill_id="data-1",
                agent_address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
                name="Data Analysis",
                category="data-analysis",
                description="Statistical analysis and visualization",
                price_per_task=750000,
                estimated_duration_hours=2,
                rating=4.6,
                review_count=60,
                completed_tasks=75,
                tags=["Data", "Analysis", "Charts"],
                capabilities=["Pandas", "Matplotlib", "SQL"],
            ),
        ]
        
        for skill in skills:
            self._skills[skill.skill_id] = skill
            self._agent_by_skill.setdefault(skill.category, []).append(skill.agent_address)
    
    # ============ Browse Skills ============
    
    def browse_skills(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Skill]:
        """
        Browse skills, optionally by category.
        
        Args:
            category: Filter by category
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of skills
        """
        skills = list(self._skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        return sorted(skills, key=lambda s: s.rating, reverse=True)[offset:offset+limit]
    
    def get_skill_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with skill counts"""
        categories = {}
        
        for skill in self._skills.values():
            cat = skill.category
            if cat not in categories:
                categories[cat] = {"category": cat, "count": 0, "avg_price": 0, "total_rating": 0}
            categories[cat]["count"] += 1
            categories[cat]["avg_price"] += skill.price_per_task
            categories[cat]["total_rating"] += skill.rating
        
        result = []
        for cat, data in categories.items():
            result.append({
                "category": cat,
                "skill_count": data["count"],
                "avg_price": data["avg_price"] // data["count"],
                "avg_rating": data["total_rating"] / data["count"],
            })
        
        return sorted(result, key=lambda x: x["skill_count"], reverse=True)
    
    # ============ Search Agents ============
    
    def search_agents(
        self,
        query: str = None,
        filters: SearchFilters = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Agent]:
        """
        Search for agents.
        
        Args:
            query: Search query (name, bio, tags)
            filters: Additional filters
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of matching agents
        """
        results = list(self._agents.values())
        
        # Text search
        if query:
            query_lower = query.lower()
            results = [
                a for a in results
                if query_lower in a.name.lower()
                or query_lower in a.bio.lower()
                or any(query_lower in s.name.lower() for s in a.skills)
            ]
        
        # Apply filters
        if filters:
            if filters.category:
                results = [
                    a for a in results
                    if any(s.category == filters.category for s in a.skills)
                ]
            if filters.min_rating > 0:
                results = [a for a in results if a.rating >= filters.min_rating]
            if filters.availability:
                results = [a for a in results if a.status == filters.availability]
            if filters.skills:
                results = [
                    a for a in results
                    if any(s.category in filters.skills for s in a.skills)
                ]
            
            # Sorting
            if filters.sort_by == "rating":
                results.sort(key=lambda a: a.rating, reverse=True)
            elif filters.sort_by == "reviews":
                results.sort(key=lambda a: a.total_reviews, reverse=True)
            elif filters.sort_by == "price":
                # Sort by lowest avg price
                results.sort(key=lambda a: min([s.price_per_task for s in a.skills] or [float('inf')]))
            elif filters.sort_by == "recent":
                results.sort(key=lambda a: a.member_since, reverse=True)
        
        return results[offset:offset+limit]
    
    def search_skills(
        self,
        query: str = None,
        category: str = None,
        min_rating: float = 0.0,
        max_price: int = None,
        limit: int = 20,
    ) -> List[Skill]:
        """
        Search for skills.
        
        Args:
            query: Search query
            category: Filter by category
            min_rating: Minimum rating
            max_price: Maximum price
            limit: Max results
            
        Returns:
            List of matching skills
        """
        skills = list(self._skills.values())
        
        if query:
            query_lower = query.lower()
            skills = [
                s for s in skills
                if query_lower in s.name.lower()
                or query_lower in s.description.lower()
                or any(query_lower in t.lower() for t in s.tags)
            ]
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if min_rating > 0:
            skills = [s for s in skills if s.rating >= min_rating]
        
        if max_price:
            skills = [s for s in skills if s.price_per_task <= max_price]
        
        return sorted(skills, key=lambda s: s.rating, reverse=True)[:limit]
    
    # ============ Agent Profiles ============
    
    def get_agent_profile(self, agent_address: str) -> Optional[Agent]:
        """Get detailed agent profile"""
        return self._agents.get(agent_address)
    
    def get_agent_skills(self, agent_address: str) -> List[Skill]:
        """Get all skills for an agent"""
        return [
            s for s in self._skills.values()
            if s.agent_address == agent_address
        ]
    
    def get_agent_availability(self, agent_address: str) -> Dict[str, Any]:
        """Get agent availability status"""
        agent = self._agents.get(agent_address)
        if not agent:
            return {"error": "Agent not found"}
        
        active_tasks = 0  # Would query active tasks
        
        return {
            "address": agent_address,
            "status": agent.status,
            "active_tasks": active_tasks,
            "available": agent.status == "available",
        }
    
    # ============ Top & Trending ============
    
    def get_top_rated_agents(self, limit: int = 10) -> List[Agent]:
        """Get top rated agents"""
        return sorted(
            list(self._agents.values()),
            key=lambda a: a.rating,
            reverse=True,
        )[:limit]
    
    def get_top_rated_skills(self, category: str = None, limit: int = 10) -> List[Skill]:
        """Get top rated skills"""
        skills = list(self._skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        return sorted(skills, key=lambda s: s.rating, reverse=True)[:limit]
    
    def get_most_active_agents(self, limit: int = 10) -> List[Agent]:
        """Get most active agents (most completed tasks)"""
        return sorted(
            list(self._agents.values()),
            key=lambda a: a.completed_tasks,
            reverse=True,
        )[:limit]
    
    def get_trending_skills(self, limit: int = 10) -> List[Skill]:
        """Get trending skills (recently popular)"""
        # Sort by recent review activity
        return sorted(
            list(self._skills.values()),
            key=lambda s: s.review_count,
            reverse=True,
        )[:limit]
    
    # ============ Recommendations ============
    
    def get_recommended_agents(
        self,
        user_preferences: Dict[str, Any],
        limit: int = 5,
    ) -> List[Agent]:
        """
        Get personalized agent recommendations.
        
        Args:
            user_preferences: User preferences (categories, budget, etc.)
            limit: Max results
            
        Returns:
            Recommended agents
        """
        preferences = user_preferences.get("categories", [])
        budget = user_preferences.get("max_budget", float('inf'))
        
        candidates = list(self._agents.values())
        
        if preferences:
            candidates = [
                a for a in candidates
                if any(s.category in preferences for s in a.skills)
            ]
        
        # Filter by budget
        candidates = [
            a for a in candidates
            if min([s.price_per_task for s in a.skills] or [float('inf')]) <= budget
        ]
        
        # Score by rating and activity
        scored = [
            (a, a.rating * 0.6 + min(a.completed_tasks / 100, 1.0) * 0.4)
            for a in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [a for a, _ in scored[:limit]]
    
    def get_similar_agents(self, agent_address: str, limit: int = 5) -> List[Agent]:
        """Get agents similar to a given agent"""
        agent = self._agents.get(agent_address)
        if not agent:
            return []
        
        agent_skills = set(s.category for s in agent.skills)
        
        # Find agents with overlapping skills
        similar = []
        for other in self._agents.values():
            if other.address == agent_address:
                continue
            
            other_skills = set(s.category for s in other.skills)
            overlap = len(agent_skills & other_skills)
            
            if overlap > 0:
                similar.append((other, overlap, other.rating))
        
        # Sort by overlap and rating
        similar.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [a for a, _, _ in similar[:limit]]
    
    # ============ Stats ============
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        agents = list(self._agents.values())
        skills = list(self._skills.values())
        
        return {
            "total_agents": len(agents),
            "total_skills": len(skills),
            "avg_agent_rating": sum(a.rating for a in agents) / len(agents) if agents else 0,
            "total_completed_tasks": sum(a.completed_tasks for a in agents),
            "available_agents": len([a for a in agents if a.status == "available"]),
            "categories": len(set(s.category for s in skills)),
        }
    
    # ============ Export ============
    
    def export_agents_json(self, agent_address: str = None) -> str:
        """Export agents as JSON"""
        if agent_address:
            agent = self._agents.get(agent_address)
            data = [agent.to_dict()] if agent else []
        else:
            data = [a.to_dict() for a in self._agents.values()]
        
        return json.dumps(data, indent=2)
    
    def export_skills_json(self, category: str = None) -> str:
        """Export skills as JSON"""
        skills = list(self._skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        return json.dumps([s.to_dict() for s in skills], indent=2)


def get_discovery_skill(mock: bool = True) -> DiscoverySkill:
    """
    Get a DiscoverySkill instance.
    
    Args:
        mock: Use mock data
        
    Returns:
        Configured DiscoverySkill
    """
    return DiscoverySkill(mock=mock)
