"""
Tests for OpenClaw Skills

Tests for Mandate, Discovery, and Reputation skills.
"""

import sys
sys.path.insert(0, 'src')


def test_mandate_service():
    """Test mandate skill wrapper"""
    from clawtrust.skills.mandate import MandateService, MandateStatus
    
    service = MandateService()
    
    # Create terms
    terms = service.create_terms(
        skill_name="image-generation",
        provider="agent-alpha",
        renter="happyclaw-agent",
        price_usdc=10000,
        duration_seconds=3600,
    )
    
    assert terms.skill_name == "image-generation"
    assert terms.price_usdc == 10000
    
    # Create mandate
    mandate = service.create_mandate(terms)
    assert mandate.status == MandateStatus.PENDING
    
    print("✓ test_mandate_service passed")
    return True


def test_discovery_service():
    """Test discovery skill wrapper"""
    from clawtrust.skills.discovery import DiscoveryService
    
    service = DiscoveryService()
    
    # List all skills
    skills = service.list_skills()
    assert len(skills) >= 3
    
    # Get specific skill
    skill = service.get_skill("image-generation")
    assert skill is not None
    assert skill.provider == "happyclaw-agent"
    
    # Filter by price
    affordable = service.list_skills(max_price=20000)
    assert len(affordable) >= 1
    
    print("✓ test_discovery_service passed")
    return True


def test_reputation_service():
    """Test reputation skill wrapper"""
    from clawtrust.skills.reputation import ReputationService
    
    service = ReputationService()
    
    # Get reputation
    rep = service.get_reputation("happyclaw-agent")
    assert rep is not None
    assert rep.score == 85.0
    assert rep.reviews == 47
    
    # Get new agent
    new_rep = service.get_reputation("new-agent")
    assert new_rep.score == 50.0  # Default for new
    assert new_rep.reviews == 0
    
    # Top agents
    top = service.get_top_agents(3)
    assert len(top) <= 3
    assert top[0][1] >= top[1][1]  # Sorted descending
    
    print("✓ test_reputation_service passed")
    return True


def test_skill_files_exist():
    """Test that SKILL.md files exist"""
    import os
    
    skill_dirs = [
        "src/clawtrust/skills/mandate",
        "src/clawtrust/skills/discovery",
        "src/clawtrust/skills/reputation",
    ]
    
    for skill_dir in skill_dirs:
        skill_md = os.path.join(skill_dir, "SKILL.md")
        assert os.path.exists(skill_md), f"SKILL.md missing in {skill_dir}"
        assert os.path.exists(os.path.join(skill_dir, "__init__.py")), f"__init__.py missing in {skill_dir}"
    
    print("✓ test_skill_files_exist passed")
    return True


def test_all():
    """Run all tests"""
    tests = [
        test_mandate_service,
        test_discovery_service,
        test_reputation_service,
        test_skill_files_exist,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{passed}/{passed + failed} tests passed")
    return failed == 0


if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
