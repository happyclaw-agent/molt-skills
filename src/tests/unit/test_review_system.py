"""
Tests for Review System
"""

import pytest


class TestReview:
    """Tests for Review dataclass"""
    
    def test_review_creation(self):
        """Test creating a basic review"""
        from src.trustyclaw.sdk.review_system import Review, ReviewStatus
        
        review = Review(
            review_id="test-review",
            provider="provider-addr",
            renter="renter-addr",
            skill_id="image-generation",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Great work!",
        )
        
        assert review.review_id == "test-review"
        assert review.rating == 5
        assert review.status == ReviewStatus.PENDING
        assert review.helpful_votes == 0
    
    def test_review_to_dict(self):
        """Test review serialization"""
        from src.trustyclaw.sdk.review_system import Review
        
        review = Review(
            review_id="test",
            provider="p",
            renter="r",
            skill_id="s",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Nice",
        )
        
        data = review.to_dict()
        
        assert data["review_id"] == "test"
        assert data["rating"] == 4
        assert data["status"] == "pending"


class TestReviewService:
    """Tests for ReviewService"""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service with mock data"""
        from src.trustyclaw.sdk.review_system import ReviewService
        return ReviewService(mock=True)
    
    def test_create_review(self, service):
        """Test creating a new review"""
        review = service.create_review(
            provider="new-provider",
            renter="renter-1",
            skill_id="code-generation",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Amazing code!",
        )
        
        assert review.review_id.startswith("review-")
        assert review.provider == "new-provider"
        assert review.status.value == "pending"
    
    def test_submit_review(self, service):
        """Test submitting a pending review"""
        review = service.create_review(
            provider="provider",
            renter="renter",
            skill_id="test",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Good",
        )
        
        submitted = service.submit_review(review.review_id)
        
        assert submitted.status.value == "submitted"
        assert review.status.value == "submitted"
    
    def test_get_review(self, service):
        """Test retrieving a specific review"""
        review = service.create_review(
            provider="p",
            renter="r",
            skill_id="s",
            rating=3,
            completed_on_time=False,
            output_quality="fair",
            comment="Ok",
        )
        
        retrieved = service.get_review(review.review_id)
        
        assert retrieved is not None
        assert retrieved.review_id == review.review_id
    
    def test_get_agent_reviews(self, service):
        """Test getting reviews for an agent"""
        reviews = service.get_agent_reviews(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        
        assert len(reviews) >= 1
        for r in reviews:
            assert r.provider == "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
    
    def test_file_dispute(self, service):
        """Test filing a dispute"""
        review = service.create_review(
            provider="p",
            renter="r",
            skill_id="s",
            rating=1,
            completed_on_time=False,
            output_quality="poor",
            comment="Terrible",
        )
        service.submit_review(review.review_id)
        
        dispute = service.file_dispute(
            review.review_id,
            filed_by="provider",
            reason="Unfair rating",
            evidence=["link1", "link2"],
        )
        
        assert dispute.dispute_id.startswith("dispute-")
        assert dispute.reason == "Unfair rating"
        assert review.status.value == "disputed"
    
    def test_resolve_dispute(self, service):
        """Test resolving a dispute"""
        review = service.create_review(
            provider="p",
            renter="r",
            skill_id="s",
            rating=2,
            completed_on_time=False,
            output_quality="fair",
            comment="Bad",
        )
        service.submit_review(review.review_id)
        dispute = service.file_dispute(review.review_id, "provider", "Reason")
        
        resolved = service.resolve_dispute(
            dispute.dispute_id,
            "approved",
            "Review is valid",
        )
        
        assert resolved.status.value == "resolved"
        assert resolved.resolution.value == "approved"
    
    def test_vote_review(self, service):
        """Test voting on a review"""
        review = service.create_review(
            provider="p",
            renter="r",
            skill_id="s",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Nice",
        )
        service.submit_review(review.review_id)
        
        vote = service.vote_review(review.review_id, "voter-1", helpful=True)
        
        assert vote.helpful is True
        assert review.helpful_votes == 1
    
    def test_get_review_votes(self, service):
        """Test getting vote summary"""
        review = service.create_review(
            provider="p",
            renter="r",
            skill_id="s",
            rating=4,
            completed_on_time=True,
            output_quality="good",
            comment="Nice",
        )
        service.submit_review(review.review_id)
        
        service.vote_review(review.review_id, "v1", helpful=True)
        service.vote_review(review.review_id, "v2", helpful=True)
        service.vote_review(review.review_id, "v3", helpful=False)
        
        votes = service.get_review_votes(review.review_id)
        
        assert votes["helpful"] == 2
        assert votes["unhelpful"] == 1
    
    def test_calculate_agent_rating_new_agent(self, service):
        """Test rating calculation for agent with reviews"""
        review = service.create_review(
            provider="test-agent",
            renter="r",
            skill_id="s",
            rating=5,
            completed_on_time=True,
            output_quality="excellent",
            comment="Perfect",
        )
        service.submit_review(review.review_id)
        
        rating = service.calculate_agent_rating("test-agent")
        
        assert rating["total_reviews"] == 1
        assert rating["average_rating"] == 5.0
        assert rating["rating"] == "excellent"
    
    def test_calculate_agent_rating_insufficient_reviews(self, service):
        """Test rating for agent with no reviews"""
        rating = service.calculate_agent_rating("unknown-agent", min_reviews=10)
        
        assert rating["rating"] == "insufficient_reviews"
        assert rating["total_reviews"] == 0
    
    def test_get_top_agents(self, service):
        """Test getting top rated agents"""
        top = service.get_top_agents(5)
        
        assert len(top) <= 5
        # Should be sorted by rating
        for i in range(len(top) - 1):
            assert top[i]["average_rating"] >= top[i + 1]["average_rating"]
    
    def test_export_reviews_json(self, service):
        """Test exporting reviews as JSON"""
        json_str = service.export_reviews_json()
        
        import json
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) > 0


class TestReviewStatus:
    """Tests for ReviewStatus enum"""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist"""
        from src.trustyclaw.sdk.review_system import ReviewStatus
        
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.SUBMITTED.value == "submitted"
        assert ReviewStatus.DISPUTED.value == "disputed"
        assert ReviewStatus.RESOLVED.value == "resolved"
        assert ReviewStatus.ARCHIVED.value == "archived"


class TestDisputeResolution:
    """Tests for DisputeResolution enum"""
    
    def test_all_resolutions_exist(self):
        """Test all resolution types exist"""
        from src.trustyclaw.sdk.review_system import DisputeResolution
        
        assert DisputeResolution.APPROVED.value == "approved"
        assert DisputeResolution.REJECTED.value == "rejected"
        assert DisputeResolution.MODIFIED.value == "modified"
        assert DisputeResolution.ESCALATED.value == "escalated"


class TestGetReviewService:
    """Tests for get_review_service function"""
    
    def test_get_service_mock(self):
        """Test getting service with mock data"""
        from src.trustyclaw.sdk.review_system import get_review_service
        
        service = get_review_service(mock=True)
        assert service.mock is True
    
    def test_get_service_no_mock(self):
        """Test getting service without mock data"""
        from src.trustyclaw.sdk.review_system import get_review_service
        
        service = get_review_service(mock=False)
        assert service.mock is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
