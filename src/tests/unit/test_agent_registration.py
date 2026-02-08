"""
Tests for Agent Registration Skill

Tests for agent registration, capability management, 
and auto-negotiation rules.
"""

import sys
sys.path.insert(0, 'src')


def test_agent_registration():
    """Test agent registration"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register a new agent
    registration = skill.register_agent(
        name="TestAgent",
        bio="A test autonomous agent",
        capabilities=[
            SkillCapability.CODE_GENERATION,
            SkillCapability.TEXT_GENERATION,
        ],
        pricing={
            "code-generation": 2000000,  # 2 USDC
            "text-generation": 500000,  # 0.5 USDC
        },
        auto_accept=False,
        max_mandate_value=5000000,  # 5 USDC
        agent_address="test-agent-001",
    )
    
    assert registration is not None
    assert registration.agent_address == "test-agent-001"
    assert registration.status == "active"
    assert len(registration.capabilities.skills) == 2
    
    # Verify skills were created
    skill_ids = [s.skill_id for s in registration.capabilities.skills]
    assert len(skill_ids) == 2
    
    print("✓ test_agent_registration passed")
    return True


def test_get_registration():
    """Test getting registration by address"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register an agent
    skill.register_agent(
        name="GetTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.DATA_ANALYSIS],
        pricing={"data-analysis": 1000000},
        agent_address="get-test-agent",
    )
    
    # Get registration
    registration = skill.get_registration("get-test-agent")
    assert registration is not None
    assert registration.agent_address == "get-test-agent"
    
    # Test non-existent agent
    missing = skill.get_registration("non-existent")
    assert missing is None
    
    print("✓ test_get_registration passed")
    return True


def test_update_capabilities():
    """Test updating agent capabilities"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="UpdateTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="update-test-agent",
    )
    
    # Update capabilities
    updated = skill.update_capabilities(
        "update-test-agent",
        capabilities=[
            SkillCapability.CODE_GENERATION,
            SkillCapability.IMAGE_GENERATION,
        ],
        pricing={
            "code-generation": 1500000,
            "image-generation": 2000000,
        },
    )
    
    assert len(updated.capabilities.skills) == 2
    
    # Verify original agent still works
    registration = skill.get_registration("update-test-agent")
    assert len(registration.capabilities.skills) == 2
    
    print("✓ test_update_capabilities passed")
    return True


def test_add_remove_skills():
    """Test adding and removing skills"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="SkillTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="skill-test-agent",
    )
    
    # Add a skill
    new_skill = skill.add_skill(
        "skill-test-agent",
        SkillCapability.DATA_ANALYSIS,
        "Data Analysis",
        "Professional data analysis",
        1500000,
        estimated_hours=3.0,
    )
    
    assert new_skill is not None
    assert new_skill.skill_id.startswith("skill_")
    
    # Verify skill was added
    registration = skill.get_registration("skill-test-agent")
    assert len(registration.capabilities.skills) == 2
    
    # Remove the skill
    removed = skill.remove_skill("skill-test-agent", new_skill.skill_id)
    assert removed is True
    
    # Verify skill was removed
    registration = skill.get_registration("skill-test-agent")
    assert len(registration.capabilities.skills) == 1
    
    # Try to remove non-existent skill
    removed = skill.remove_skill("skill-test-agent", "non-existent")
    assert removed is False
    
    print("✓ test_add_remove_skills passed")
    return True


def test_auto_negotiation_rules():
    """Test auto-negotiation rules"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    from trustyclaw.models.negotiation import (
        NegotiationRules,
        NegotiationStrategy,
        AutoAcceptCriteria,
        PriceNegotiationRules,
        PriceRange,
        DeliveryPreferences,
        DeliveryPreference,
    )
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="AutoNegTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="autoneg-test-agent",
    )
    
    # Set auto-negotiation rules
    rules = NegotiationRules(
        strategy=NegotiationStrategy.AUTO_ACCEPT,
        auto_accept=AutoAcceptCriteria(
            min_price_usdc=500000,
            max_price_usdc=5000000,
            require_escrow=True,
            require_deposit=True,
        ),
        price_rules=PriceNegotiationRules(
            strategy=PriceRange.FLEXIBLE_10_PERCENT,
            min_counter_offers=1,
            max_counter_offers=3,
        ),
        delivery_preferences=DeliveryPreferences(
            preference=DeliveryPreference.STANDARD,
            preferred_duration_seconds=14400,
        ),
    )
    
    updated = skill.set_auto_negotiation("autoneg-test-agent", rules)
    
    assert updated.negotiation_rules is not None
    assert updated.negotiation_rules.strategy == NegotiationStrategy.AUTO_ACCEPT
    assert updated.capabilities.auto_negotiation is True
    
    print("✓ test_auto_negotiation_rules passed")
    return True


def test_enable_disable_auto_accept():
    """Test enabling and disabling auto-accept"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="AutoAcceptTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="autoaccept-test-agent",
    )
    
    # Enable auto-accept
    enabled = skill.enable_auto_accept(
        "autoaccept-test-agent",
        min_price_usdc=100000,
        max_price_usdc=3000000,
    )
    
    assert enabled.negotiation_rules is not None
    assert enabled.negotiation_rules.auto_accept.min_price_usdc == 100000
    assert enabled.negotiation_rules.auto_accept.max_price_usdc == 3000000
    
    # Disable auto-negotiation
    disabled = skill.disable_auto_negotiation("autoaccept-test-agent")
    
    assert disabled.capabilities.auto_negotiation is False
    assert disabled.negotiation_rules.strategy.value == "manual-review"
    
    print("✓ test_enable_disable_auto_accept passed")
    return True


def test_price_negotiation_config():
    """Test price negotiation configuration"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    from trustyclaw.models.negotiation import PriceRange
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="PriceNegTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="priceneg-test-agent",
    )
    
    # Configure price negotiation
    updated = skill.configure_price_negotiation(
        "priceneg-test-agent",
        strategy=PriceRange.FLEXIBLE_20_PERCENT,
        min_counter_offers=2,
        max_counter_offers=5,
    )
    
    assert updated.negotiation_rules is not None
    assert updated.negotiation_rules.price_rules.strategy == PriceRange.FLEXIBLE_20_PERCENT
    assert updated.negotiation_rules.price_rules.min_counter_offers == 2
    assert updated.negotiation_rules.price_rules.max_counter_offers == 5
    
    print("✓ test_price_negotiation_config passed")
    return True


def test_negotiation_sessions():
    """Test negotiation sessions"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    from trustyclaw.models.negotiation import NegotiationSession
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="NegSessionTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="negsession-test-agent",
    )
    
    # Start negotiation
    session = skill.start_negotiation(
        agent_address="negsession-test-agent",
        client_address="client-001",
        skill_id="skill-001",
        initial_price=1000000,
        duration_seconds=3600,
    )
    
    assert session is not None
    assert session.session_id.startswith("neg_")
    assert session.status == "active"
    assert session.agent_offer == 1000000
    
    # Get negotiation
    retrieved = skill.get_negotiation(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    
    # Accept offer
    accepted = skill.accept_offer(
        session.session_id,
        offerer="client",
        price=900000,
        duration=7200,
        duration_seconds=7200,
    )
    
    assert accepted.status == "accepted"
    assert accepted.counter_number == 1
    
    # Get agent negotiations
    agent_negs = skill.get_agent_negotiations("negsession-test-agent")
    assert len(agent_negs) >= 1
    
    # Reject negotiation
    skill.register_agent(
        name="RejectTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="reject-test-agent",
    )
    
    reject_session = skill.start_negotiation(
        agent_address="reject-test-agent",
        client_address="client-002",
        skill_id="skill-002",
        initial_price=1000000,
        duration_seconds=3600,
    )
    
    rejected = skill.reject_negotiation(reject_session.session_id)
    assert rejected.status == "rejected"
    
    print("✓ test_negotiation_sessions passed")
    return True


def test_agent_status():
    """Test agent status management"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="StatusTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="status-test-agent",
    )
    
    # Initially active
    registration = skill.get_registration("status-test-agent")
    assert registration.status == "active"
    
    # Suspend agent
    suspended = skill.suspend_agent("status-test-agent")
    assert suspended.status == "suspended"
    
    # Activate agent
    activated = skill.activate_agent("status-test-agent")
    assert activated.status == "active"
    
    # Delete registration
    deleted = skill.delete_registration("status-test-agent")
    assert deleted is True
    
    # Verify deleted
    missing = skill.get_registration("status-test-agent")
    assert missing is None
    
    print("✓ test_agent_status passed")
    return True


def test_statistics():
    """Test registration statistics"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Get initial stats
    stats = skill.get_statistics()
    assert "total_registrations" in stats
    assert "active_agents" in stats
    assert "auto_negotiating_agents" in stats
    
    # Register some agents
    for i in range(3):
        skill.register_agent(
            name=f"StatsTestAgent{i}",
            bio="Test agent",
            capabilities=[SkillCapability.CODE_GENERATION],
            pricing={"code-generation": 1000000},
            agent_address=f"stats-test-agent-{i}",
        )
    
    # Get updated stats
    new_stats = skill.get_statistics()
    assert new_stats["total_registrations"] >= 3
    
    print("✓ test_statistics passed")
    return True


def test_list_registrations():
    """Test listing registrations"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    
    skill = AgentRegistrationSkill()
    
    # Register agents
    for i in range(3):
        skill.register_agent(
            name=f"ListTestAgent{i}",
            bio="Test agent",
            capabilities=[SkillCapability.CODE_GENERATION],
            pricing={"code-generation": 1000000},
            agent_address=f"list-test-agent-{i}",
        )
    
    # List all
    all_regs = skill.list_registrations()
    assert len(all_regs) >= 3
    
    # List by status
    active_regs = skill.list_registrations(status="active")
    assert len(active_regs) >= 3
    
    # List with limit
    limited = skill.list_registrations(limit=2)
    assert len(limited) == 2
    
    print("✓ test_list_registrations passed")
    return True


def test_export_registration():
    """Test exporting registration as JSON"""
    from trustyclaw.skills.agent_registration import AgentRegistrationSkill
    from trustyclaw.models.skill import SkillCapability
    import json
    
    skill = AgentRegistrationSkill()
    
    # Register agent
    skill.register_agent(
        name="ExportTestAgent",
        bio="Test agent",
        capabilities=[SkillCapability.CODE_GENERATION],
        pricing={"code-generation": 1000000},
        agent_address="export-test-agent",
    )
    
    # Export single
    json_single = skill.export_registration_json("export-test-agent")
    data = json.loads(json_single)
    assert len(data) == 1
    assert data[0]["agent_address"] == "export-test-agent"
    
    # Export all
    json_all = skill.export_registration_json()
    data = json.loads(json_all)
    assert len(data) >= 1
    
    print("✓ test_export_registration passed")
    return True


def test_negotiation_criteria():
    """Test auto-accept criteria evaluation"""
    from trustyclaw.models.negotiation import AutoAcceptCriteria
    
    criteria = AutoAcceptCriteria(
        min_price_usdc=500000,
        max_price_usdc=5000000,
        require_escrow=True,
        require_deposit=True,
        blocked_clients=["blocked-client"],
        trusted_clients=["trusted-client"],
    )
    
    # Should accept - meets criteria
    should_accept = criteria.should_accept(
        price_usdc=1000000,
        duration_seconds=3600,
        client_rating=4.5,
        client_address="any-client",
        has_escrow=True,
        has_deposit=True,
    )
    assert should_accept is True
    
    # Should reject - price too low
    too_low = criteria.should_accept(
        price_usdc=100000,
        duration_seconds=3600,
        client_rating=4.5,
        client_address="any-client",
        has_escrow=True,
        has_deposit=True,
    )
    assert too_low is False
    
    # Should reject - blocked client
    blocked = criteria.should_accept(
        price_usdc=1000000,
        duration_seconds=3600,
        client_rating=4.5,
        client_address="blocked-client",
        has_escrow=True,
        has_deposit=True,
    )
    assert blocked is False
    
    # Should accept - trusted client overrides
    trusted = criteria.should_accept(
        price_usdc=100000,  # Below minimum
        duration_seconds=3600,
        client_rating=4.5,
        client_address="trusted-client",
        has_escrow=True,
        has_deposit=True,
    )
    assert trusted is True
    
    # Should reject - missing escrow
    no_escrow = criteria.should_accept(
        price_usdc=1000000,
        duration_seconds=3600,
        client_rating=4.5,
        client_address="any-client",
        has_escrow=False,
        has_deposit=True,
    )
    assert no_escrow is False
    
    print("✓ test_negotiation_criteria passed")
    return True


def test_price_negotiation_rules():
    """Test price negotiation rules"""
    from trustyclaw.models.negotiation import PriceNegotiationRules, PriceRange
    
    rules = PriceNegotiationRules(
        strategy=PriceRange.FLEXIBLE_10_PERCENT,
        min_counter_offers=1,
        max_counter_offers=3,
    )
    
    # Test acceptable range
    min_price, max_price = rules.get_acceptable_range(1000000)  # 1 USDC
    assert min_price == 900000  # 10% below
    assert max_price == 1100000  # 10% above
    
    # Test fixed price
    fixed_rules = PriceNegotiationRules(strategy=PriceRange.FIXED)
    fixed_min, fixed_max = fixed_rules.get_acceptable_range(1000000)
    assert fixed_min == 1000000
    assert fixed_max == 1000000
    
    # Test counter acceptability (counters 0, 1, 2 are valid with max_counter_offers=3)
    assert rules.is_counter_acceptable(1000000, 950000, 0) is True  # First counter
    assert rules.is_counter_acceptable(1000000, 800000, 0) is False  # Below minimum
    assert rules.is_counter_acceptable(1000000, 950000, 2) is True  # Third counter (valid)
    assert rules.is_counter_acceptable(1000000, 950000, 3) is False  # Fourth counter (too many)
    # Test counter acceptability
    assert rules.is_counter_acceptable(1000000, 950000, 0) is True  # Within range
    assert rules.is_counter_acceptable(1000000, 800000, 0) is False  # Below minimum
    assert rules.is_counter_acceptable(1000000, 950000, 3) is False  # Too many counters
    
    print("✓ test_price_negotiation_rules passed")
    return True


def test_delivery_preferences():
    """Test delivery preferences"""
    from trustyclaw.models.negotiation import DeliveryPreferences, DeliveryPreference
    
    prefs = DeliveryPreferences(
        preference=DeliveryPreference.EXPRESS,
        preferred_duration_seconds=14400,  # 4 hours
        max_duration_seconds=86400,  # 24 hours
        express_multiplier=1.5,
    )
    
    # Standard delivery at preferred time
    price, duration = prefs.get_adjusted_price(1000000, 14400)
    assert price == 1000000
    assert duration == 14400
    
    # Express delivery
    express_price, express_duration = prefs.get_adjusted_price(1000000, 14400)
    assert express_price == 1500000  # 1.5x multiplier
    assert express_duration == 14400
    
    # Test flexible delivery
    flexible_prefs = DeliveryPreferences(
        preference=DeliveryPreference.FLEXIBLE,
        min_duration_seconds=7200,  # 2 hours
        max_duration_seconds=28800,  # 8 hours
    )
    
    flexible_price, flexible_duration = flexible_prefs.get_adjusted_price(1000000, 14400)
    assert flexible_price == 1000000
    assert flexible_duration == 14400
    
    print("✓ test_delivery_preferences passed")
    return True


def test_all():
    """Run all tests"""
    tests = [
        test_agent_registration,
        test_get_registration,
        test_update_capabilities,
        test_add_remove_skills,
        test_auto_negotiation_rules,
        test_enable_disable_auto_accept,
        test_price_negotiation_config,
        test_negotiation_sessions,
        test_agent_status,
        test_statistics,
        test_list_registrations,
        test_export_registration,
        test_negotiation_criteria,
        test_price_negotiation_rules,
        test_delivery_preferences,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed}/{passed + failed} tests passed")
    return failed == 0


if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
