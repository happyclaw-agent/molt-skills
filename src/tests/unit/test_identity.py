"""Tests for Identity Module"""

import pytest
from pydantic import ValidationError

from trustyclaw.sdk.identity import (
    AgentIdentity,
    IdentityStatus,
    create_identity,
)


class TestAgentIdentity:
    """Test cases for AgentIdentity class"""

    def test_create_valid_identity(self):
        """Test creating a valid agent identity"""
        identity = create_identity(
            name="TestAgent",
            wallet_address="0x1234567890abcdef",
            public_key="0xabcdef1234567890",
            email="test@example.com",
        )

        assert identity.name == "TestAgent"
        assert identity.email == "test@example.com"
        assert identity.status == IdentityStatus.ACTIVE
        assert identity.reputation_score == 0.0
        assert identity.total_rentals == 0

    def test_identity_to_dict(self):
        """Test identity serialization"""
        identity = create_identity(
            name="TestAgent",
            wallet_address="0x1234567890abcdef",
            public_key="0xabcdef1234567890",
            email="test@example.com",
        )

        data = identity.__dict__

        assert data["name"] == "TestAgent"
        assert data["email"] == "test@example.com"
        assert data["status"] == IdentityStatus.ACTIVE
        assert "created_at" in data
        assert "updated_at" in data

    def test_identity_from_dict(self):
        """Test identity deserialization"""
        data = {
            "id": "agent-123",
            "name": "TestAgent",
            "wallet_address": "0x1234567890abcdef",
            "public_key": "0xabcdef1234567890",
            "email": "test@example.com",
            "status": "active",
            "reputation_score": 85.5,
            "total_rentals": 10,
            "created_at": "2026-02-05T00:00:00Z",
            "updated_at": "2026-02-05T00:00:00Z",
        }

        identity = AgentIdentity(**data)

        assert identity.id == "agent-123"
        assert identity.reputation_score == 85.5
        assert identity.total_rentals == 10

    def test_reputation_update(self):
        """Test reputation score updates"""
        identity = create_identity(
            name="TestAgent",
            wallet_address="0x1234567890abcdef",
            public_key="0xabcdef1234567890",
            email="test@example.com",
        )

        # Simulate reputation update
        identity.reputation_score = 90.0
        identity.total_rentals = 5

        assert identity.reputation_score == 90.0
        assert identity.total_rentals == 5

    def test_identity_status_transitions(self):
        """Test identity status transitions"""
        identity = create_identity(
            name="TestAgent",
            wallet_address="0x1234567890abcdef",
            public_key="0xabcdef1234567890",
            email="test@example.com",
        )

        # Active by default
        assert identity.status == IdentityStatus.ACTIVE

        # Suspend
        identity.status = IdentityStatus.SUSPENDED
        assert identity.status == IdentityStatus.SUSPENDED

        # Reactivate
        identity.status = IdentityStatus.ACTIVE
        assert identity.status == IdentityStatus.ACTIVE


class TestIdentityStatus:
    """Test cases for IdentityStatus enum"""

    def test_all_statuses_defined(self):
        """Verify all expected statuses exist"""
        assert IdentityStatus.ACTIVE.value == "active"
        assert IdentityStatus.SUSPENDED.value == "suspended"
        assert IdentityStatus.REVOKED.value == "revoked"
        assert IdentityStatus.PENDING.value == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
