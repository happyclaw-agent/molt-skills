"""
Tests for OpenClaw Skills

Tests for Mandate, Discovery, and Reputation skills using actual Skill classes.
"""

import os

import pytest


def test_mandate_skill():
    """Test MandateSkill: create_mandate and get_mandate."""
    from trustyclaw.skills.mandate import get_mandate_skill, MandateStatus

    skill = get_mandate_skill(mock=True)
    m = skill.create_mandate(
        provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
        skill_id="image-generation",
        amount=500000,
        duration_hours=12,
        deliverables=["10 images"],
    )
    assert m is not None
    assert m.mandate_id.startswith("mandate-")
    assert m.status == MandateStatus.DRAFT
    assert m.terms.skill_id == "image-generation"
    assert m.terms.amount == 500000

    got = skill.get_mandate(m.mandate_id)
    assert got is not None
    assert got.mandate_id == m.mandate_id


def test_discovery_skill():
    """Test DiscoverySkill: browse_skills and search_agents."""
    from trustyclaw.skills.discovery import get_discovery_skill

    skill = get_discovery_skill(mock=True)
    skills = skill.browse_skills(category=None, limit=50)
    assert len(skills) >= 3

    skill_one = skill.browse_skills(category="image-generation", limit=5)
    assert len(skill_one) >= 1
    assert skill_one[0].category == "image-generation"

    agents = skill.search_agents(query="python", limit=10)
    assert isinstance(agents, list)


def test_reputation_skill():
    """Test ReputationSkill: get_agent_reputation and get_reputation_tier."""
    from trustyclaw.skills.reputation import get_reputation_skill

    skill = get_reputation_skill(network="devnet", mock=True)
    rep = skill.get_agent_reputation("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q")
    assert rep is not None
    assert hasattr(rep, "reputation_score")
    assert hasattr(rep, "average_rating")

    tier = skill.get_reputation_tier("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q")
    assert tier is not None
    assert isinstance(tier, str)


def test_skill_files_exist():
    """Test that SKILL.md and __init__.py exist in each skill package."""
    # Resolve path: tests/unit -> src -> trustyclaw/skills
    base = os.path.join(os.path.dirname(__file__), "..", "..", "trustyclaw", "skills")
    skill_dirs = ["mandate", "discovery", "reputation"]
    for name in skill_dirs:
        skill_dir = os.path.join(base, name)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        init_py = os.path.join(skill_dir, "__init__.py")
        assert os.path.exists(skill_md), f"SKILL.md missing in {skill_dir}"
        assert os.path.exists(init_py), f"__init__.py missing in {skill_dir}"


def test_getters_accept_mock():
    """Test that get_*_skill(mock=True) works (README API)."""
    from trustyclaw.skills.mandate import get_mandate_skill
    from trustyclaw.skills.discovery import get_discovery_skill
    from trustyclaw.skills.reputation import get_reputation_skill

    get_mandate_skill(mock=True)
    get_discovery_skill(mock=True)
    get_reputation_skill(mock=True)
