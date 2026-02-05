"""
Tests for Mandate Skill
"""

import pytest
from datetime import datetime, timedelta


class TestMandateTerms:
    """Tests for MandateTerms dataclass"""
    
    def test_creation(self):
        """Test creating mandate terms"""
        from src.trustyclaw.skills.mandate import MandateTerms
        
        terms = MandateTerms(
            skill_id="image-generation",
            amount=1000000,
            duration_hours=24,
            deliverables=["5 images"],
            requirements=["High quality"],
        )
        
        assert terms.skill_id == "image-generation"
        assert terms.amount == 1000000
        assert len(terms.deliverables) == 1
    
    def test_to_dict(self):
        """Test serialization"""
        from src.trustyclaw.skills.mandate import MandateTerms
        
        terms = MandateTerms(
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        data = terms.to_dict()
        
        assert data["skill_id"] == "s"
        assert data["amount"] == 100


class TestMandate:
    """Tests for Mandate dataclass"""
    
    def test_creation(self):
        """Test creating a mandate"""
        from src.trustyclaw.skills.mandate import Mandate, MandateTerms, MandateStatus
        
        terms = MandateTerms(
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        mandate = Mandate(
            mandate_id="test",
            provider="p",
            renter="r",
            terms=terms,
        )
        
        assert mandate.status == MandateStatus.DRAFT
        assert mandate.revision_count == 0
    
    def test_to_dict(self):
        """Test serialization"""
        from src.trustyclaw.skills.mandate import Mandate, MandateTerms
        
        terms = MandateTerms(skill_id="s", amount=100, duration_hours=1, deliverables=["d"])
        mandate = Mandate(mandate_id="test", provider="p", renter="r", terms=terms)
        
        data = mandate.to_dict()
        
        assert data["mandate_id"] == "test"
        assert data["status"] == "draft"


class TestMandateSkill:
    """Tests for MandateSkill"""
    
    @pytest.fixture
    def skill(self):
        """Create a fresh skill with mock data"""
        from src.trustyclaw.skills.mandate import MandateSkill
        return MandateSkill(mock=True)
    
    def test_create_mandate(self, skill):
        """Test creating a new mandate"""
        mandate = skill.create_mandate(
            provider="provider",
            renter="renter",
            skill_id="code-gen",
            amount=500000,
            duration_hours=12,
            deliverables=["code"],
            revisions=1,
        )
        
        assert mandate.mandate_id.startswith("mandate-")
        assert mandate.status.value == "draft"
        assert mandate.terms.amount == 500000
    
    def test_get_mandate(self, skill):
        """Test retrieving a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        retrieved = skill.get_mandate(mandate.mandate_id)
        
        assert retrieved is not None
        assert retrieved.mandate_id == mandate.mandate_id
    
    def test_submit_mandate(self, skill):
        """Test submitting a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        submitted = skill.submit_mandate(mandate.mandate_id)
        
        assert submitted.status.value == "pending"
    
    def test_accept_mandate(self, skill):
        """Test accepting a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        
        accepted = skill.accept_mandate(mandate.mandate_id)
        
        assert accepted.status.value == "accepted"
        assert accepted.accepted_at is not None
    
    def test_decline_mandate(self, skill):
        """Test declining a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        
        declined = skill.decline_mandate(mandate.mandate_id, "Not interested")
        
        assert declined.status.value == "cancelled"
    
    def test_start_mandate(self, skill):
        """Test starting a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        
        started = skill.start_mandate(mandate.mandate_id)
        
        assert started.status.value == "active"
        assert started.started_at is not None
    
    def test_request_revision(self, skill):
        """Test requesting a revision"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
            revisions=2,
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        skill.start_mandate(mandate.mandate_id)
        
        revised = skill.request_revision(mandate.mandate_id, "Add more detail")
        
        assert revised.revision_count == 1
    
    def test_complete_mandate(self, skill):
        """Test completing a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        skill.start_mandate(mandate.mandate_id)
        
        completed = skill.complete_mandate(mandate.mandate_id, "sha256hash")
        
        assert completed.status.value == "completed"
        assert completed.deliverable_hash == "sha256hash"
    
    def test_extend_deadline(self, skill):
        """Test extending deadline"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=24,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        skill.start_mandate(mandate.mandate_id)
        
        extended = skill.extend_deadline(mandate.mandate_id, 12)
        
        assert extended.status.value == "extended"
        assert extended.extended_deadline is not None
    
    def test_cancel_mandate(self, skill):
        """Test cancelling a mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        cancelled = skill.cancel_mandate(mandate.mandate_id)
        
        assert cancelled.status.value == "cancelled"
    
    def test_rate_mandate(self, skill):
        """Test rating a completed mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        skill.start_mandate(mandate.mandate_id)
        skill.complete_mandate(mandate.mandate_id, "hash")
        
        rated = skill.rate_mandate(
            mandate.mandate_id,
            renter_rating=5,
            provider_rating=4,
        )
        
        assert rated.renter_rating == 5
        assert rated.provider_rating == 4
    
    def test_link_escrow(self, skill):
        """Test linking escrow to mandate"""
        mandate = skill.create_mandate(
            provider="p",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        skill.submit_mandate(mandate.mandate_id)
        skill.accept_mandate(mandate.mandate_id)
        
        linked = skill.link_escrow(mandate.mandate_id, "escrow-123")
        
        assert linked.escrow_id == "escrow-123"
        assert linked.status.value == "active"
    
    def test_get_mandates_by_participant(self, skill):
        """Test getting mandates by participant"""
        mandate = skill.create_mandate(
            provider="search-provider",
            renter="r",
            skill_id="s",
            amount=100,
            duration_hours=1,
            deliverables=["d"],
        )
        
        mandates = skill.get_mandates_by_participant("search-provider")
        
        assert len(mandates) >= 1
        for m in mandates:
            assert m.provider == "search-provider" or m.renter == "search-provider"
    
    def test_export_mandates_json(self, skill):
        """Test exporting mandates as JSON"""
        json_str = skill.export_mandates_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)


class TestMandateStatus:
    """Tests for MandateStatus enum"""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist"""
        from src.trustyclaw.skills.mandate import MandateStatus
        
        assert MandateStatus.DRAFT.value == "draft"
        assert MandateStatus.PENDING.value == "pending"
        assert MandateStatus.ACCEPTED.value == "accepted"
        assert MandateStatus.ACTIVE.value == "active"
        assert MandateStatus.COMPLETED.value == "completed"
        assert MandateStatus.CANCELLED.value == "cancelled"
        assert MandateStatus.EXTENDED.value == "extended"


class TestGetMandateSkill:
    """Tests for get_mandate_skill function"""
    
    def test_get_skill_mock(self):
        """Test getting skill with mock data"""
        from src.trustyclaw.skills.mandate import get_mandate_skill
        
        skill = get_mandate_skill(mock=True)
        assert skill.mock is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
